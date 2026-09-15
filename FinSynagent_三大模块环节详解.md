# Fin Synagent · 三大核心模块「环节级」详解

> **本文档定位**：逐节点、逐环节拆解 **智能咨询（Consult）**、**智能荐股（Screen）**、**RAG 知识库** 三个模块。
> 每个环节都标注了**真实代码位置**、**输入依赖**、**提示词**、**产出**、**失败降级行为**，可以直接对着源码核对。
>
> 代码地图：
> - `agent_graph.py` — Consult 智能咨询的 LangGraph 状态图（7 节点）
> - `screen_graph.py` — Screen 智能荐股的 LangGraph 状态图（12 节点）
> - `kb.py` — 知识库加载 / 检索 / 诊断（独立模块，不依赖 Streamlit）
> - `app.py` — 单文件 UI（含真实行情、情绪分析、评分、DeepSeek 调用等实现）
> - `build_kb/` — 离线建库与评测脚本（不进应用包）

---

# 第一部分 · 智能咨询（Consult）

## 1.1 整体结构：一张 7 节点状态图

```
                    ┌──────────────────────────────────────────┐
                    ▼                                          │
[用户提问] → 👔leader → 📚retrieve → 🎓expert → 🧐critic ──┐    │
                                                │          │    │
                                     verdict=revise        │    │
                                    且 loop < max_loop    ▼    │
                                                    ✍️revise ───┘
                                                │
                                     verdict=pass
                                                ▼
                                          🔎verify → 📋summarize → END
```

- **节点定义**：`agent_graph.py` L195–201
- **边与条件边**：L203–211
- **条件路由函数**：`_route_after_critic` L182–186 → `verdict=="revise" and loop < max_loop` 则回 `revise`，否则去 `verify`
- **回环上限**：`max_loop` 默认 2；线上调用时显式传 `max_loop=2`（`app.py` L1509）

### 状态（State）怎么设计

`ConsultState`（L37–63）刻意分成三类：

| 类别 | 字段 | 说明 |
|---|---|---|
| **输入/配置**（图内只读） | `query` `decomp_level` `rag_key` `kb_tag` `real` `max_loop` `loop` `script` | 由调用方注入；`script` 是演示模式的兜底脚本 |
| **依赖注入** | `llm_text` `rag_fn` `on_step` | 让编排与"具体用哪个模型/哪个知识库/怎么渲染"解耦，便于注入 mock 做测试 |
| **各智能体产出** | `leader` `expert` `critic` `verdict` `expert_revise` `verify` `summary` `rag_hits` `rag_ctx` | 图内累积 |
| **可观测轨迹** | `trace: Annotated[list, operator.add]` | 用 `operator.add` 作 reducer，每个节点返回的单条 list 会被**追加**而非覆盖 —— 这是渲染"逐节点点亮"的数据基础 |

> ⭐ **设计要点**：`trace` 用 `Annotated[list, operator.add]` 是 LangGraph 的标准写法。若不写 reducer，后一个节点返回的 `trace` 会**覆盖**前一个节点的，UI 就只剩最后一步了。

---

## 1.2 环节 ① 👔 Leader 领导智能体 · 任务拆解

| 项 | 内容 |
|---|---|
| **代码** | `leader_node` L80–91 |
| **触发** | 图的入口（`set_entry_point("leader")`） |
| **输入** | `state["query"]`（用户问题）、`state["decomp_level"]`（拆解粒度，默认 3） |
| **System Prompt** | 「你是 Fin 智能投顾系统的 Leader 领导智能体。负责把用户的投资咨询问题拆解为若干子任务并分配专家。请只输出纯文本 Markdown 列表：每行一个「- 子任务：<名称>」，最后一行「- 分配专家：<专家名>」。不要添加额外解释。」 |
| **User Prompt** | `用户问题：{query}` + `拆解粒度：{decomp_level} 级（粒度越高，子任务越细）。请给出子任务列表与分配的专家。` |
| **产出** | `state["leader"]`；一条 trace：`👔 Leader 领导智能体 · 任务拆解` |
| **演示模式兜底** | `script["subtasks"]` → 逐行 `- 子任务：xxx`；`script["experts"]` → `- 分配专家：A、B` |

**为什么要有粒度参数？** `decomp_level` 是"人机协同"的入口：UI 上是一个滑块（`app.py` L1609「⚙️ 任务设置 · 任务分解程度」），用户能决定 Leader 拆得多细。粒度越高 → 子任务越多 → 后续专家要覆盖的面越广。

**输出格式为什么写死？** 因为下游（UI）要按固定格式渲染。用「行级模板 + 禁止额外解释」替代 JSON，是为了在**流式输出**时也能逐步解析、不会因为 JSON 未闭合而渲染失败。

---

## 1.3 环节 ② 📚 RAG 知识库检索

| 项 | 内容 |
|---|---|
| **代码** | `retrieve_node` L94–117 |
| **输入** | `state["rag_key"]`（行业路由键）、`state["query"]`、可选注入的 `state["rag_fn"]` |
| **产出** | `state["rag_hits"]`（命中列表）、`state["rag_ctx"]`（拼好的上下文字符串）；trace `📚 知识库检索（RAG）` |
| **上下文格式** | 每条命中拼成 `【{source} · p{page}】{text}`，用换行连接 |
| **无命中文案** | `（知识库未加载，以下为通用分析）` |

**这个节点有一段极重要的设计注释（L95–96）**：

```
# 直接 import 检索函数，避免依赖注入在云端（langgraph 版本差异）失效导致静默空结果；
# 同时保留 rag_fn 注入作为可测试入口，若注入可用则优先使用。
```

**三级取数顺序**（这是踩坑后的加固）：

1. 优先用注入的 `rag_fn(rag_key, query)`（单测时可传 mock）；
2. 若注入不可用 / 抛异常 / 返回空 → **直接 `from kb import get_rag_hits`** 兜底调用；
3. 若两条路都失败 → 打印 stderr 诊断日志（`[agent_graph] retrieve_node ... failed`），并让 `rag_ctx` 退化为"通用分析"文案。

> ⭐ **踩坑原文**：最初完全依赖 `state["rag_fn"]` 注入，本地正常，云端却是空结果——因为 LangGraph 的 StateGraph **channel schema 对 `Callable` 类型在不同版本下不一定传播**，云端 `state["rag_fn"]` 拿到的是 `None`，于是静默走了空分支。**结论：不要把框架当依赖注入通道**，共享逻辑抽成独立纯模块、节点内直接 import 才是稳的。

`rag_key` 怎么来的？在 `app.py` L1490：

```python
rag_key = next((k for k in ["白酒", "红利", "贵金属"] if k in query), "default")
kb_tag = "宏观" if rag_key == "default" else rag_key
```

即**关键词命中式行业路由**：问题里出现"白酒/红利/贵金属"就路由到对应库，都没命中则 `default` → 映射到 `宏观` 库。

---

## 1.4 环节 ③ 🎓 专家智能体 · 生成回答

| 项 | 内容 |
|---|---|
| **代码** | `expert_node` L120–128 |
| **输入** | `query` + `rag_ctx`（上一步的检索片段） |
| **System Prompt** | 「你是 Fin 智能投顾系统的行业专家智能体（金融领域资深分析师）。请基于【知识库检索片段】与用户问题，输出专业、数据驱动、可追溯的投资分析。要求：使用 Markdown，分点论述，关键结论加粗，必要时给出风险提示。语言为中文。」 |
| **User Prompt** | `用户问题：{query}\n\n【知识库检索片段】\n{rag_ctx}\n\n请基于以上信息给出专业回答。` |
| **产出** | `state["expert"]`；trace `🎓 专家智能体（DeepSeek-Chat）· 生成回答` |
| **兜底** | `script["expert_answer"]` |

**这段 prompt 的四个约束各有目的**：
- **「基于【知识库检索片段】」** → 强制开卷答题，是抑幻觉的第一道闸；
- **「数据驱动、可追溯」** → 要求引用具体数字与出处；
- **「关键结论加粗」** → 让 UI 上用户一眼看到结论；
- **「必要时给出风险提示」** → 合规留痕（金融场景硬要求）。

---

## 1.5 环节 ④ 🧐 评论家智能体 · 审查

| 项 | 内容 |
|---|---|
| **代码** | `critic_node` L131–145 |
| **输入** | `query` + `state["expert"]`（待审的专家回答） |
| **System Prompt** | 「你是 Fin 智能投顾系统的评论家智能体。请审查专家回答，指出遗漏、逻辑漏洞、数据存疑之处，并给出改进建议。用中文 Markdown 要点输出。」 |
| **产出** | `state["critic"]`（批评文本）+ `state["verdict"]`（`revise` / `pass`）；trace `🧐 评论家智能体 · 审查` |

### verdict（是否返工）怎么判？

两条完全不同的判定路径：

```python
if state.get("real"):                                     # 真实模式：看文本信号
    _pass_kw = ["无需修改","无需修订","分析充分","无需补充",
                "无需完善","已较完整","通过","无需返工"]
    verdict = "pass" if any(k in crit for k in _pass_kw) else "revise"
else:                                                     # 演示模式：保证必有一次回环
    verdict = "revise" if state.get("loop", 0) == 0 else "pass"
```

- **真实模式**用**关键词信号判定**——这是"用自然语言当结构化输出"的轻量做法：不额外让 LLM 输出 JSON，而是让它在批评里自然写出"无需修改"这类词，代码做子串匹配。好处是省一次 LLM 往返；坏处是有误判空间（比如模型写"并非无需修改"也会命中）。
- **演示模式**强制 `loop==0` 时必返工一次 —— **保证观众一定能看到"批评—修订"回环**，不会因为模型这次心情好直接通过而演示不到核心机制。

---

## 1.6 环节 ⑤ ✍️ 专家智能体 · 完善回答（回环节点）

| 项 | 内容 |
|---|---|
| **代码** | `revise_node` L148–155 |
| **输入** | `query` + `expert`（原回答）+ `critic`（批评意见） |
| **System Prompt** | 「你是 Fin 智能投顾系统的专家智能体。请根据评论家的批评意见，完善并修订你的回答，输出修订后的完整要点。中文 Markdown。」 |
| **产出** | `state["expert_revise"]`；**同时 `state["loop"] + 1`**；trace `✍️ 专家智能体 · 完善回答` |

### ⚠️ 全项目最关键的一个工程细节：循环计数放在哪

```python
return {"expert_revise": rev, "loop": state.get("loop", 0) + 1, ...}
```

**计数必须放在回环中会被重新执行的节点里（这里是 `revise`），且只在"需要返工"时递增。**

为什么？

- 如果放在**条件边的起点**（`critic_node`）里自增，LangGraph 会在**执行 `add_conditional_edges` 的路由函数之前**就已经消费掉这次自增 → 路由函数读到的 `loop` 已经是自增后的值 → 条件 `loop < max_loop` 立刻不成立 → **回环只跑一次**（甚至一次都不跑）。
- 这种 bug **不报错、不抛异常**，只是"感觉系统好像没反思"，极其隐蔽。

> 📌 这条规律在 `screen_graph.py` 里被写成了注释警告（L233–234），是同一个坑的复现与防复发。

**回环终止保证**：`critic_node` 里 `verdict = "revise" if loop < max_loop else "pass"` —— 即使批评始终不通过，`loop` 累计到 `max_loop`（默认 2）后必然变 `pass`，图一定终止。

---

## 1.7 环节 ⑥ 🔎 搜索与求证智能体 · 验证

| 项 | 内容 |
|---|---|
| **代码** | `verify_node` L158–168 |
| **输入** | `query` + **`state["expert_revise"]`**（注意：用的是修订后的版本，不是初版） |
| **System Prompt** | 「你是 Fin 智能投顾系统的搜索与求证智能体。请针对分析中的关键数据与结论，列出可溯源的信息来源（研究报告/数据/新闻），并判断是否可能存在幻觉。中文 Markdown 列表。」 |
| **产出** | `state["verify"]`；trace `🔎 搜索与求证智能体 · 验证` |
| **兜底文案** | 「已检索知识库与互联网，交叉验证关键数据，未发现幻觉内容。信息源如下：」+ `script["verify"]` 逐条列出 |

**这一环的作用**：把"答案对不对"从"专家自己说了算"变成"第三方复核"。它是幻觉抑制的**最后一道闸**，也是产品上"信源可溯"承诺的兑现点。

---

## 1.8 环节 ⑦ 📋 总结领导 · 最终建议

| 项 | 内容 |
|---|---|
| **代码** | `summarize_node` L171–178 |
| **输入** | `query` + `expert_revise` + `verify` |
| **System Prompt** | 「你是 Fin 智能投顾系统的总结领导。请基于以上全流程（任务拆解、专家分析、评论家审查、修订、求证），给出最终投资建议与可执行结论。中文 Markdown，简明有力。」 |
| **产出** | `state["summary"]`；trace `📋 总结领导 · 最终建议`，随后 `add_edge("summarize", END)` 结束 |

注意 prompt 里显式列举了**全流程四段**（拆解/分析/审查修订/求证）——这是在提示模型"你是在做结案陈词，不是重新分析"，避免它把前面几轮的中间态混进来。

---

## 1.9 Consult 的运行模式与 UI 渲染链路

### 两种运行模式

| 模式 | LLM 实现 | 特点 |
|---|---|---|
| **真实模式** | `_ds_client()` + `_ds_text()` / `_ds_stream_into()`（`app.py` L827/865/886）→ 走 DeepSeek API | 真实推理；用户可自带 Key（只存浏览器会话） |
| **演示模式** | 每个节点返回内置 `script[...]` 兜底文本 | **断网可跑**，演示现场保险 |

每个节点的 `llm_text(system, user, fallback)` 签名统一为"三个参数进、一段文本出"——`fallback` 就是演示模式的答案。这样真实/演示的切换**完全收敛在一个函数里**，编排层无感知。

### UI 渲染链路：`on_step` 回调

```
节点内 _emit(state, agent, title, content)
      ├─ 构造 step = {"agent","title","content"}
      ├─ 若 state["on_step"] 可调用 → cb(state, step)   ← 立即推给 UI
      └─ return [step]                                   ← 交给 state["trace"] 累加
```

`app.py` 的 `_consult_on_step`（L1463）在回调里用 `st.status(step["title"], expanded=True)` 现场开一个折叠块并写入内容 —— **这就是"六个智能体卡片依次点亮、思维链逐段展开"的实现原理**。回调整体包在 `try/except` 里（L72–75），保证 UI 报错不会污染图执行。

### 无 LangGraph 时的降级

`agent_graph.py` 顶部用 `try: from langgraph.graph import ... except: StateGraph = None`。若环境没装 LangGraph，`app.py` 还有一份**手写顺序编排版** `_run_workflow_inline`（L1321）——每个节点用 `st.status` 串行执行，语义与状态图一致。**保证页面永远可用**。

---

# 第二部分 · 智能荐股（Screen）

## 2.1 整体结构：筛选树 12 节点

```
📡fetch_data
   ↓
🧭planner            ← 意图解析（口语 → 结构化 JSON）
   ↓
🏗️build_pool         ← 行业过滤 + 基础过滤
   ↓
🌐fetch_comments     ← 并发爬股吧评论（仅真实模式）
   ↓
💰feat_fundamental ─┐
📈feat_technical   ─┤  四维特征（树状分支）
💬feat_sentiment   ─┤
🏭feat_industry    ─┘
   ↓
🧬synthesize         ← 四分支收束为单一特征向量
   ↓
⚖️scorer             ← 加权打分 → Top-3
   ↓
🤖reasoner  ←─────────┐
   ↓                  │
🧐critic ─────────────┘  回环（verdict=revise 且 loop<max_loop）
   ↓
  END
```

- **节点注册**：`screen_graph.py` L256–259（用 `globals()[n + "_node"]` 按名字批量注册，节点名与函数名一一对应）
- **边与条件边**：L260–272
- **回环上限**：`max_loop` 默认 1；线上传 `max_loop=1`（`app.py` L2261）

### 状态设计：一个"全依赖注入"的图

`ScreenState`（L46–82）最特别的地方是**把 8 个函数也塞进 state 当依赖**：

| 注入项 | 签名 | 作用 |
|---|---|---|
| `fetch_rt_fn` | `(codes) -> (rt, src)` | 实时行情 |
| `fetch_kline_fn` | `(code, days) -> kline` | 日 K 线 |
| `fetch_comments_fn` | `(code, name, n) -> list` | 个股评论 |
| `sentiment_fn` | `(pool, industry, risk, rt, klines, allow_real, comments) -> dict` | 情绪面 |
| `score_fn` | `(pool, rt, klines) -> None` | 评分（写回 `real_score`） |
| `analyst_fn` | `(industry, risk, feat, pool, allow_real) -> str` | 行业分析师观点 |
| `reason_fn` | `(stk, industry, risk, allow_real) -> str` | 单只推荐理由 |
| `tech_fn` | `(close_list) -> dict` | 技术指标计算 |

> 为什么这次敢用注入？（对比 1.3 节的教训）
> 因为 `ScreenState` 的注入是**同一个 Python 进程内构造初始 state 时直接塞进去的**（`build_initial_state` L284–301），不依赖 LangGraph 的 channel schema 传播；而且每个节点里都做了 `try/except` 降级。**与 Consult 的 `rag_fn` 跨模块注入风险不同**。这个对比本身就是很好的工程判断素材。

---

## 2.2 环节 ① 📡 实时行情获取

| 项 | 内容 |
|---|---|
| **代码** | `fetch_data_node` L104–115 |
| **输入** | `candidates[industry]` ∪ `stocks[industry]` 的全部股票代码（`sorted(set)` 去重） |
| **真实模式** | `fetch_rt_fn(codes)` 拉实时报价 → `rt, src`；再对每只 `fetch_kline_fn(code, 120)` 拉 120 日日 K |
| **演示模式** | `rt = {}`、`src = "demo"`、`klines = {}` |
| **产出** | `codes` / `rt` / `klines` / `rt_src`（展示为"内置示例"或真实来源）；trace `📡 实时行情获取` |

**为什么先把所有代码收齐再拉？** 因为后续 4 个特征节点都要用行情数据，统一次拉取避免重复请求。代码集合是 `候选池 ∪ 展示池` 的并集——**候选池用于打分排序，展示池用于生成推荐理由**，两者可能不完全重合（比如分析师观点里要提一只没进候选的行业龙头）。

真实行情实现有好几路兜底：`_em_realtime_one`（东方财富）、`_yh_realtime_one`（同花顺）等（`app.py` L1005–1084）。

---

## 2.3 环节 ② 🧭 Screen Agent 意图解析

| 项 | 内容 |
|---|---|
| **代码** | `planner_node` L118–126 |
| **输入** | `state["risk"]`（保守型/稳健型/积极型）、`state["industry"]` |
| **产出** | `state["intent"]` 结构化 JSON |

```python
rp = {"保守型": "low", "稳健型": "medium", "积极型": "high"}[state["risk"]]
intent = {
    "sector": state["industry"],
    "risk_preference": rp,
    "objective": "capital_appreciation" if state["risk"] == "积极型" else "stable_income",
    "source": "qstock 行情 / 财务报告 / 时讯新闻",
}
```

**这一环的意义是"把口语需求翻译成机器能用的结构化条件"**：用户点的是「行业=白酒、风险=稳健」这种 UI 控件，系统据此落成 `sector / risk_preference / objective` 三个枚举字段 —— 这就是通常说的 **Intent → Structured Query**（口语 → 结构化查询）。之后所有筛选、打分都以这份 JSON 为准，不再回看原始口语，避免歧义漂移。

---

## 2.4 环节 ③ 🏗️ 股票池构建

| 项 | 内容 |
|---|---|
| **代码** | `build_pool_node` L129–133 |
| **输入** | `candidates[industry]` |
| **产出** | `state["pool"]`（用 `copy.deepcopy` 深拷贝，避免污染全局候选字典） |
| **筛选规则文案** | 「行业过滤 + 基础过滤（市值>500亿、非ST）→ 候选池 N 支」 |

**两级过滤的逻辑**：
1. **行业过滤**：只在本行业候选池里选（白酒/红利/贵金属三选一）；
2. **基础过滤**：**市值 > 500 亿**（保证流动性、避免小盘操纵）、**非 ST**（排除退市风险股）。

`deepcopy` 不是可有可无的细节——`candidates` 是模块级全局常量，后面 `feat_sentiment` 和 `score_fn` 会往 pool 的元素里回写 `sent` / `real_score` / `score_break`。不深拷贝就会**把演示数据改脏**，第二次运行结果就不一样了。

---

## 2.5 环节 ④ 🌐 个股评论抓取

| 项 | 内容 |
|---|---|
| **代码** | `fetch_comments_node` L136–161 |
| **真实模式** | `ThreadPoolExecutor(max_workers=min(9, len(pool)))` 并发，对每只标的抓 **15 条**股吧评论 |
| **演示模式** | 直接返回 `{}`，trace 文案「🟠 演示模式跳过实时评论抓取。」 |
| **产出** | `state["stock_news"]` = `{code: [评论, ...]}`；trace 汇报总条数 |
| **降级** | 线程池整体异常 → 退化为**串行 for 循环**逐只抓，单只失败则该只记 `[]` |

```python
def _one(c):
    try:
        return c["code"], state["fetch_comments_fn"](c["code"], c.get("name", ""), 15)
    except Exception as e:
        return c["code"], []          # 单只失败不影响整体
```

**并发 + 单点失败隔离**是这一环的核心：抓评论是最容易失败的外部 IO（反爬、超时），所以每只标的独立 try/except，把"失败"降级为"这只没有评论"，而不是整条流水线崩掉。UI 上还有个「🔍 评论抓取诊断（各标的 · 各源失败原因）」展开面板（`app.py` L2443）——**把失败原因摊开给用户看**，而不是静默吞掉。

评论抓取实现：`_guba_em_comments`（东方财富股吧，`app.py` L1936）等。

---

## 2.6 环节 ⑤⑥⑦⑧ 四维特征提取（树状分支）

这四个节点构成树的四条分支，最终由 `synthesize` 收束。

### ⑤ 💰 基本面特征

| 项 | 内容 |
|---|---|
| **代码** | `feat_fundamental_node` L164–166 |
| **指标** | **PE（市盈率）/ PB（市净率）/ ROE（净资产收益率）/ 营收增速** |
| **筛选逻辑文案** | 「低估值 + 高 ROE + 稳定增长」 |

### ⑥ 📈 技术面特征

| 项 | 内容 |
|---|---|
| **代码** | `feat_technical_node` L169–171 |
| **指标** | **趋势 / 均线形态 / 波动率 / MACD** |
| **真实模式** | 由真实日 K 计算 **MA20 / MA60 与 MACD** |

技术指标计算实现：`_compute_tech` / `_tech_detail` / `_tech_score`（`app.py` L1138/1167/1192）。

### ⑦ 💬 情绪面特征

| 项 | 内容 |
|---|---|
| **代码** | `feat_sentiment_node` L174–183 |
| **核心调用** | `sentiment_fn(pool, industry, risk, rt, klines, allow_real, comments)` |
| **输入** | 真实模式下额外传入 `stock_news`（逐条评论） |
| **产出** | `state["sent_res"]`；`sentiment_fn` 内部把 `sent` / `sent_score` / `comment_labels` **写回 pool 的每个元素**；节点随后显式回写 `pool` 引用确保 state 持有更新后的池 |
| **实现** | `_screen_sentiment`（`app.py` L1833）—— **FinBERT / DeepSeek 三分类 + 本地词库混合** |

**情绪面的双层设计**：
1. **股票级**：FinBERT / DeepSeek 给出「正面/中性/负面」三分类概率；
2. **评论级**：逐条股吧评论单独打情绪标签（`comment_labels`），再聚合成带符号均值 `sent_score ∈ [-1, 1]`。

**中性覆盖策略**：当 DeepSeek 判为"中性"时，若本地 `_POS/_NEG_WORDS` 词库对该文本有明显倾向，则**用词库结论覆盖 DS 结论（×0.92 权重）**。理由：财经股吧的口语表达（"yyds"、"回本了"、"割肉"）DS 常保守判中性，而词库反而更敏感。中性只保留给**纯数据播报、跨吧 spam、真模糊标题**。

### ⑧ 🏭 行业面特征

| 项 | 内容 |
|---|---|
| **代码** | `feat_industry_node` L186–191 |
| **输入** | `industry_feature[industry]` 的 `macro` 与 `industry` 两个列表 |
| **产出** | trace 里拼接展示：`宏观特征：A；B` / `行业特征：C；D` |

这一维是**自上而下**的：宏观（利率、政策、经济周期）+ 行业景气（供需、价格、竞争格局），给个股提供"大环境是否配合"的判断。

---

## 2.7 环节 ⑨ 🧬 四维特征汇聚

| 项 | 内容 |
|---|---|
| **代码** | `synthesize_node` L194–196 |
| **产出** | 仅一条 trace：「基本面 / 技术面 / 情绪面 / 行业面四分支特征合成，送入 LLM 加权评分。」 |

**这一环是"树"的收束点**：四条并列分支在这里合并成一条主干。工程上它是个**语义标记节点**（没有自己的计算），价值在于让"筛选树"的拓扑在 trace 与 UI 上清晰可见 —— **可观测性优先于代码行数**。

---

## 2.8 环节 ⑩ ⚖️ LLM 综合评分

| 项 | 内容 |
|---|---|
| **代码** | `scorer_node` L199–206 |
| **触发条件** | `if state.get("rt"): score_fn(pool, rt, klines)` —— 只有当有真实行情时才重算评分 |
| **排序** | 按 `_score_of(c)`（优先 `real_score`，回退 `score`）降序取前 3 |
| **trace** | 「加权收敛（0.30×动量 + 0.30×技术面 + 0.25×质量 + 0.15×情绪），Top-3 已锁定：**A, B, C**。」 |

### 打分明细（`app.py` `_screen_score` L1198–1221）

| 分项 | 权重 | 公式 | 含义 |
|---|---|---|---|
| **动量 mom** | 0.30 | `clamp(55 + 涨跌幅% × 7, 15, 95)` | 涨跌幅 ×7 放大后以 55 为中枢，上下限夹逼防极端值 |
| **技术 tech** | 0.30 | `_tech_score(收盘价序列)`；不足 60 日给 60 | 均线/MACD 综合技术分 |
| **质量 qual** | 0.25 | `clamp(ROE × 2.6, 20, 98)` | ROE 越高越好（15% → 39 分，35% → 91 分） |
| **情绪 sent** | 0.15 | `50 + sent_score × 50`（无 `sent_score` 时回退 `30 + 正面占比 × 60`） | -1→0 分，0→50 分，+1→100 分 |

```
real_score = 0.30×mom + 0.30×tech + 0.25×qual + 0.15×sent      # 0~100
```

同时把四项写回 `c["score_break"]`（`{mom, tech, qual, sent}`）——UI 上「🧮 维度得分计算明细」展开面板（`app.py` L2620）就是读这个字段，**让每个分数都能被拆解核对**。

> ⭐ **权重设计意图**：动量与技术面各占 0.30（短中期价格行为权重最高），质量 0.25（基本面托底），情绪 0.15（辅助信号、且噪声最大所以权重最低）。**这是"可解释打分"而非"LLM 拍板"**：LLM 负责把结构化分数转成人话观点，分数本身是确定性公式算出来的。

---

## 2.9 环节 ⑪ 🤖 分析师观点与推荐理由

| 项 | 内容 |
|---|---|
| **代码** | `reasoner_node` L209–222 |
| **两件事** | ① `analyst_fn(industry, risk, feat, pool, allow_real)` → 行业层面分析师观点 `analyst_view`；② 对 `stocks[industry]` 里每只标的 `reason_fn(merged, ...)` → 单只推荐理由 `reasons` |
| **合并策略** | `merged = {**cand, **stk}` —— 先用候选池里带评分的 `cand`，再被 `stocks` 里的展示字段覆盖（后者优先） |
| **loop 计数** | `_loop = state.get("loop", 0) + (1 if state.get("verdict") == "revise" else 0)` |

**这是第二次出现"计数放在回环节点"的设计**（`screen_graph.py` L219–220），注释写得很直白：

```
# loop 计数：仅当因 critic 判定 revise 而回环进入本节点时才 +1（首次生成保持 0）
```

首次进入时 `verdict` 还是空串 → 不 +1 → `loop=0`；只有被 critic 打回后**再次进入 reasoner** 时才 +1。**第一次生成计 0，这样 `critic` 里的 `loop < max_loop` 判定才能正确允许一次回环。** 若写成"每次进 reasoner 都 +1"，首次就会变成 1，`max_loop=1` 时回环直接被卡死。

---

## 2.10 环节 ⑫ 🧐 校验与反思

| 项 | 内容 |
|---|---|
| **代码** | `critic_node` L225–239 |
| **结构完整性校验** | `ok = (reasons 数量 == pool 数量) and bool(analyst_view) and all(每只评分 > 0)` |
| **verdict** | `"revise" if loop < max_loop else "pass"` |
| **关键注释** | 「注意：loop 计数由 reasoner 节点在进入回环时递增（见 reasoner_node），本节点只做判定、不修改 loop，否则条件边读到的是已自增的值，回环将无法触发。」 |

**有意思的产品取舍**（L230–231 注释）：

```
# 结构完整也至少触发一次反思回环（演示 / 真实一致），以体现 Critic 机制；
# 结构不完整时同样修订一次，但仍受 max_loop 上限保护，保证终止。
```

即：**即使 `ok == True`（结构完全没问题），也照样触发一次回环**。这是刻意的产品选择——目的是让"Critic 反思"这个核心机制在演示中必然被看到。`ok` 变量的计算结果当前主要用于 semantic 校验与日志，回环本身由 `loop < max_loop` 驱动。**这是一个"演示可见性 > 计算最优性"的取舍，讲的时候应该主动承认。**

**终止保证**：`loop` 每次都经 reasoner 递增（仅回环时），到 `max_loop`（线上=1）后 verdict 必为 `pass` → 路由到 END。

---

## 2.11 Screen 的降级与 UI

### 无 LangGraph 时的降级（`run_screen` L304–322）

```python
g = get_graph()
if g is not None:
    return g.invoke(initial_state)          # 正常路径
s = dict(initial_state)
for fn in [fetch_data_node, planner_node, ..., scorer_node]:   # 手动顺序编排
    s.update(fn(s))
while True:                                  # 手动回环
    s.update(reasoner_node(s)); s.update(critic_node(s))
    if s.get("verdict") != "revise" or s.get("loop",0) >= s.get("max_loop",1):
        break
return s
```

**手写版与状态图版语义完全一致**（同样的节点顺序、同样的回环条件），保证部署端没装 LangGraph 也能跑完整条筛选树。

### UI 渲染

- **状态图版**：`_run_screen_graph`（L2243）→ `_screen_on_step`（L2235）回调驱动 `st.status` 与进度；
- **手写版**：`_run_screen_inline`（L2269）—— 每个节点一个 `st.status` 现场展开；
- **四维特征用 4 个 Tab 展示**（L2449）：`💰基本面 / 📈技术面 / 💬情绪面（FinBERT）/ 🏭行业面`；
- **评分明细可展开**（L2620）、**评论抓取诊断可展开**（L2443）、**推荐理由可展开**（L2696）—— 全部围绕"可核对"设计。

---

# 第三部分 · RAG 知识库

RAG = **Retrieval-Augmented Generation（检索增强生成）**。一句话：**先翻资料，再写答案**。
它分成完全解耦的两端：**离线建库（Offline）** 和 **在线查询（Online）**。

---

## 3.1 离线建库：五个步骤

### 步骤 ① 语料收集

| 项 | 内容 |
|---|---|
| **规模** | **152 份权威 PDF**，按 4 个行业分目录归集 |
| **宏观** | 央行货币政策执行报告、城镇储户/银行家/企业家问卷调查报告（**64 份**） |
| **白酒** | 茅台/五粮液/泸州老窖/洋河/山西汾酒/古井贡等龙头年报、分红公告、白酒行业白皮书（**28 份**） |
| **红利** | 中证红利成分股年报 + 分红派息实施公告（神华/工行/长电/大秦/招行…）（**28 份**） |
| **贵金属** | 黄金/铜龙头年报 + 世界黄金协会报告（**30 份**） |
| **信源** | 央行官网公开披露 + 巨潮资讯网（cninfo）公告直链——**全部公开权威、可溯源、便于定期增量更新** |

### 步骤 ② 结构化提取（`build_kb/extract_markdown.py`）

用 **PyMuPDF（fitz）逐页解析，两遍扫描**：

1. **第一遍**：扫描全文字号，取**中位数作为"正文字号"基准**；
2. **第二遍**：字号 ≥ 正文 × 1.22 **且** 行长度 ≤ 20 字符 → 判为标题，并推定一级/二级/三级；正文按段落聚合并**保留所属页码**；
3. **输出**：结构化 Markdown + 中间 JSON（`_blocks.json`，含每个 block 的 `is_heading` / `level` / `page` / `text`）。

> 为什么要"两遍 + 字号中位数"？因为年报 PDF 没有语义标签，字号是唯一的层级线索；用中位数而非固定阈值，才能适配不同模板排版的年报。**标题层级是下一步切分的锚点**——有了层级才能"贴着章节切"，不至于把不同小节硬拼进一个 chunk。

### 步骤 ③ 语义切分（`build_kb/semantic_chunk.py`）

**参数卡片**：

| 参数 | 值 | 作用 |
|---|---|---|
| `MAX_CHARS` | **520** | 单 chunk 字数上限（适配 bge-small-zh 的 512 token 窗口） |
| `MIN_CHARS` | **120** | 单 chunk 字数下限，太短丢弃 |
| `MIN_CN_RATIO` | **0.45** | 中文占比阈值，低于此值的长块丢弃 |

**算法（`chunk_by_headings`）**：

- 维护一个**标题栈**（`title_chain_stack`），遇标题时回退到对应层级再压入 —— 于是每个块都带完整的标题链（形如 `【一、经营情况 > （三）成本分析】`）；
- **flush 触发条件**：遇到一级标题，或当前累积正文超过 `MAX_CHARS`；
- **句子级累积**：正文按 `(?<=[。！？；：])` 切句后逐句并入当前块，避免"半句话被切开"；
- **页码追踪**：用 `pages` 集合记录本块横跨的页，最终写 `page_start` / `page_end`；
- **中文占比过滤**：`chinese_ratio(text) < 0.45` 的块直接丢弃 —— 这一条专门用来**过滤双语年报的英文页眉/目录/免责声明**，是真正的噪声闸；
- **回退路径**：若该文件标题数 < 3（说明解析没识别出结构），改用 `chunk_by_page` **按页切分**；
- **ID 规则**：`chunk_id = f"{行业}_{文件名}_{序号:03d}"`；
- **输出**：`knowledge_base/chunks/<行业>.jsonl`，每行一个 chunk（含 `industry / source / title / page_start / page_end / text / chunk_id`）。

> 注意：切分时**每个 chunk 的文本都带标题链前缀**，这会明显提升检索命中率——因为 bge 编码时"成本分析"这类章节语义也被编进去了。

### 步骤 ④ 向量化（`build_kb/embed_store.py`）

| 项 | 内容 |
|---|---|
| **模型** | `BAAI/bge-small-zh-v1.5` —— 中文效果好、**512 维**、体积小 |
| **批量** | `batch_size=64` |
| **L2 归一化** | `normalize_embeddings=True` → **向量模长=1** → 余弦相似度等价于点积（省一次开方，且不受向量长度影响） |
| **替代性** | bge 是**星火 Embedding 的本地等价替代**——下游只需把编码函数换成星火知识库 API 即可严格对接原设计 |

### 步骤 ⑤ 入库（Chroma 持久化）

按行业创建 **4 个独立 collection**，统一 `hnsw:space = cosine`：

| 行业 | collection 名 | chunk 数 | 文档数 |
|---|---|---|---|
| 白酒 | `baijiu` | 2,973 | 28 |
| 红利 | `dividend` | 4,972 | 28 |
| 贵金属 | `precious` | 3,601 | 30 |
| 宏观 | `macro` | 1,048 | 64 |
| **合计** | — | **12,594** | **152** |

每条记录写入：`ids = chunk_id`、`embeddings`、`documents = text`、`metadatas = {industry, source, title, page_start, page_end}`。

**为什么要分 4 个库？** 对应项目「**按行业分账号管理知识库**」的设计：
1. **缩小检索域 → 提升精度**（问白酒批价不会召回贵金属研报，天然隔绝跨行业噪声）；
2. **便于分库维护与增量更新**（更新白酒年报只需重建 baijiu 库）。

---

## 3.2 在线查询：五个环节

### 环节 ① 行业路由

进入 Consult 流程后先做行业意图识别（`app.py` L1490）：

```python
rag_key = next((k for k in ["白酒", "红利", "贵金属"] if k in query), "default")
kb_tag = "宏观" if rag_key == "default" else rag_key
```

命中关键词则路由到对应 collection；**无明确行业时回退到 macro 通用库**。路由的价值：避免跨行业噪声（问白酒批价不会召回贵金属研报）+ 降低单库检索规模、提升 Top-K 精度。

> 📌 **诚实说明**：当前实现是**关键词匹配式路由**，不是 LLM 意图分类。优点是零成本、零延迟、可预测；缺点是口语变体（如"酱香科技"）命中不了。这是明确的已知局限与优化点。

### 环节 ② 查询向量化

用**与建库完全相同的 bge 模型**对 query 编码，并按 bge 官方建议拼接检索指令前缀：

```
为这个句子生成表示以用于检索相关文章：{query}
```

**为什么要加前缀？** bge 在指令微调（instruction tuning）时就是"带指令编码查询、不带指令编码文档"训练的。不按它训练时的姿势用，向量分布会对不齐，召回质量明显下降。**离线入库与在线查询两侧的编码口径必须一致**——这是 RAG 最常见的翻车点之一。

### 环节 ③ 相似度检索

在目标 collection 内做**余弦相似度 Top-K** 召回：

```python
qe = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).tolist()[0]
res = coll.query(query_embeddings=[qe], n_results=3,
                 include=["documents", "metadatas", "distances"])
sim = 1 - res["distances"][0][0]      # 余弦相似度（cosine 距离取补）
```

**关键细节**：Chroma 存的是**距离**（distance），要 `1 - distance` 才是相似度。这个转换写错，整个指标体系就全乱了。

**两段式检索（本版增强）**：

```
bge 余弦召回 Top-100 候选  →  重排取 Top-5
                              ├─ 后端 A：cross-encoder  BAAI/bge-reranker-base（最优）
                              └─ 后端 B：late-interaction（ColBERT 式 MaxSim，零下载退路）← 本版实际生效
hybrid 权重：0.6 × bi-encoder 余弦 + 0.4 × late-interaction（各自归一化后混合）
```

重排解决的是"**同主体兄弟 chunk 挤占**"问题（见 3.4 节）。实测全局精确 chunk 命中率 7.27% → **7.59%**（白酒/红利上升，**贵金属小幅回落** 6.08% → 5.82%）。

> ⚠️ **本版生效的是"退路"后端，不是最优后端**：cross-encoder 因模型缓存实际是 ONNX 格式、`CrossEncoder` 无法加载，降级成了 late-interaction。2026-09-15 补做的三路受控对照（见 §3.6）显示真 cross-encoder 明显更强——**即在当时，上线的重排方案是已知次优的**。

### 环节 ④ Prompt 拼接（抑幻觉第一道闸）

系统指令明确约束：

> 「你是金融投顾专家，**仅依据【参考资料】作答**，每条结论须**标注来源 PDF 名称与页码**，**不得编造、不得超范围**。」

检索片段与原始问题按固定模板拼接为增强提示词。**约束式 Prompt 是抑幻觉的第一道闸——模型被强制"看着资料说话"。**

### 环节 ⑤ 生成 + 信源标注

LLM 基于增强提示词生成答案，关键结论后回写 `[来源：XXX.pdf pNN]`，实现**逐条可溯源**。之后 Consult 流程还会再经 **Verify Agent** 把答案与知识库/联网数据**二次比对**，进一步压低幻觉率。

用户在界面上能看到**命中片段 + 相似度分数**——信任来自"**可解释 + 可溯源**"。

---

## 3.3 ⚠️ 线上 Demo 的真实架构：离线检索快照

这一点必须讲清楚，否则容易误解：

| 侧 | 实现 | 依赖 |
|---|---|---|
| **离线（真实能力）** | bge-small-zh 编码查询（带指令前缀）→ 从 Chroma 四库取**全量向量** → numpy 全量余弦打分 → 两段式重排取 Top-5（`build_kb/build_retrieval_eval.py` 实跑） | sentence-transformers + chromadb + numpy |
| **线上（Demo 运行）** | `kb.py` 的 `get_rag_hits` 从 `kb_data.json` 的 `retrieval` 字段读取**预计算的检索快照**，不做任何向量计算 | 仅 `os` / `json` |

看 `requirements.txt` 就能印证 —— **没有 chromadb、没有 sentence-transformers、没有 torch**：

```
streamlit>=1.36.0
streamlit-option-menu>=0.4.0
plotly>=5.22.0
pandas>=2.0.0
numpy>=1.26.0
openai>=1.0.0
langgraph>=0.2.0
```

**为什么这么设计？**
1. **体积与启动速度**：装 torch + chromadb 会让 Streamlit Cloud 镜像大几百 MB，冷启动从几秒变几十秒；
2. **断网可演示**：检索结果已随仓库部署，不依赖任何外部服务；
3. **数字同源**：快照里的 `score`（余弦相似度）、`rerank_score`、`source`、`page` **都是离线实跑的真实值**，不是编造的。

**工作方式**：`get_rag_hits(industry, user_query)` 拿用户问题去和快照里该行业的 200~290 个预置查询做**字符重叠度（`_overlap`）比对**，选出最相近的那组查询，返回它的 Top-5 命中。

> 📌 **这带来一个必须承认的局限**：自由输入的问题走的是"**最近邻预置查询**"检索，而不是实时向量检索。如果用户问的问题与 2,754 条预置查询差异很大（比如一个全新话题），返回的片段相关性会下降。这是 Demo 形态的取巧，**真实检索能力由离线脚本实跑证明**。讲的时候主动说明，比被追问出来好得多。

### 快照到底是怎么生成的（三步，`build_kb/build_retrieval_eval.py`）

**是**：用 **BAAI/bge-small-zh-v1.5 + Chroma 四库**实跑出来的真实结果。但有两个精确细节必须拧清。

**第 1 步 · 从 Chroma 取全量向量**

```python
client = chromadb.PersistentClient(path=CHROMA_DIR)   # knowledge_base/chroma
coll   = client.get_collection(coll_name)             # baijiu / dividend / precious / macro
data   = coll.get(include=["embeddings", "documents", "metadatas"])
emb_n  = emb / np.linalg.norm(emb, axis=1, keepdims=True)      # L2 归一化
```

**第 2 步 · 用 bge 编码查询，全库打分**

```python
Q_PREFIX = "为这个句子生成表示以用于检索相关文章："
qe    = model.encode([Q_PREFIX + q], normalize_embeddings=True)   # 同一个 bge 模型 + 指令前缀
sims  = emb_n @ qe                                                # L2 归一化后，余弦 ⇔ 点积
order = np.argsort(-sims)
gold_rank = int(np.where(order == gi)[0][0]) + 1                   # gold 在整库的真实排名
```

> ⚠️ **关键细节（容易被问倒）**：这里**不是**用 Chroma 的 `query()` 接口做检索，而是把向量拉出来在 **numpy 里做全量暴力余弦**。
> **为什么？** 因为必须拿到 gold 在**整库的真实排名 `gold_rank`**，而 `coll.query()` 只返回 Top-K、拿不到排名。**正是这个 `gold_rank`，让我后来算出了"约 63% 的 gold 落在 Top-100 之外"这个决定性结论。**
>
> （仓库里另有一个 `verify_retrieval.py` 是走 Chroma `query()` 接口的，用于演示知识库质量；它刻意**不加**指令前缀，以便直观展示检索效果。）

**第 3 步 · 两段式重排后写回快照**

```
bge 余弦召回 Top-100（RERANK_K = 100）
  → 重排器取 Top-5（TOP_K = 5）
     · 后端 A（最优）：cross-encoder  BAAI/bge-reranker-base
     · 后端 B（退路）：late-interaction（ColBERT 式 MaxSim，复用 bge 的 token 级表征）
     · 本次实际生效后端 = B（late-interaction）
       原因：HF 缓存里的 bge-reranker-base 实际是 ONNX 格式，
             `sentence_transformers.CrossEncoder` 按 safetensors / pytorch_model.bin 查找，
             必然加载失败 → 触发回退。详见 §3.6。
     · hybrid 权重：0.6 × bi-encoder 余弦 + 0.4 × late-interaction（各自归一化后混合）
```

结果写回 `kb_data.json` 的 `retrieval`（2,754 条查询 × Top-5）+ `retrieval_gold`（含 `gold_rank`）。

**所以两边的分工是**：离线用 bge + Chroma **真跑**出结果并落盘；线上 `kb.py` **只读 JSON、不做任何向量计算**。一句话——**离线真跑、线上回放。**

**快照里的真实字段**（每条命中）：

```json
{
  "rank": 1,
  "title": "一、审计意见",
  "source": "五粮液_2025年年度报告.pdf",
  "page": 48,
  "score": 0.681,          // bge 余弦相似度（真实值）
  "rerank_score": 1.0,     // 混合重排分（真实值）
  "text": "【一、审计意见】 我们审计了宜宾五粮液股份有限公司…"
}
```

---

## 3.4 检索鲁棒性：`kb.py` 为什么写得这么"防御"

`kb.py` 从头到尾透着一句话：**本地正常、云端空结果，这个坑我们踩过太多次了。**

### 四层兜底（`get_rag_hits` L268–319）

```
① 本行业 collection 命中
      ↓ 空
② 跨全部行业全局兜底（遍历其它 3 个行业收集命中）
      ↓ 空
③ _finalize 强制全量兜底（从 qmap / retr 递归抽全命中）
      ↓ 空
④ except 里再兜底一次全量
```

### 五个具体防御点

**① 通用递归收集器 `_iter_hits`（L71–85）**

不假设 `retrieval[行业]` 是 `dict` 还是 `list`——递归下钻，只要字典里有 `text/source/page/title/content/chunk` 任一字段就认作命中。

> 起因：**云端 `retrieval[行业]` 可能是 `list` 而不是 `dict`**，一上来就 `.items()` 直接抛异常。

**② 查询 key 强转 str（`_overlap` L88–104）**

```python
try:
    a, b = str(a), str(b)
    ...
except Exception:
    return 0
```

> 起因：`retrieval[行业]` 的查询 key **不一定是字符串**（云端出现过 int / list）。对非字符串 key 做 `ch in q` 比较会抛 `TypeError`，被外层 `except` 吞掉 → 返回空。而**空查询探针走 `overlap=0` 分支、不触发比较，所以探针命中正常、真实查询却空**——这就是典型"本地正常云端空"的现场。

**③ 绝不"提前返回最佳查询"（`_score_hits` + `_finalize`）**

错误写法（历史版本）：找到重叠度最高的那个查询就直接 `return` 它的 hits —— **如果那个查询映射到空 `[]`，整体就返回空**。
正确写法：**把整个行业所有查询的命中全部收集成列表 → 统一排序 → 去重 → 取 Top-K**。单个查询为空只贡献 0 条，绝不拖垮整体。

**④ 排序与去重（`_finalize` L144–169）**

```python
scored.sort(key=lambda t: (-t[0], -t[1]))   # 先按问题-查询字符重叠降序，再按 bundle 内 score 降序
key = (h.get("text") or h.get("content") or "")[:80]   # 用正文前 80 字做去重键
result[:4]                                   # 取 Top-4
```

**⑤ 构建指纹 `KB_RETRIEVE_BUILD`（L32）**

```python
KB_RETRIEVE_BUILD = "20260906-pooled-v5"
```

这个常量会被写进所有告警/状态文案。**作用：云端报旧文案时，一眼就能看出它跑的是哪一版 `get_rag_hits`，判断是不是陈旧部署。** 配合页脚的 git 短哈希（`_app_build`），形成"版本可自证"机制。

### 诊断体系

| 函数 | 作用 |
|---|---|
| `kb_status_info()`（L236–265） | 返回部署环境真实状态：是否加载 / 实际类型 / 路径 / 文件是否存在 / 大小 / JSON 能否解析 / 顶层键 / 加载失败原因 / 检索指纹 |
| `kb_unload_reason()`（L185–222） | 返回"为何没有检索片段"的可读原因；**先锁定 `real_err` 再跑空查询探针**（顺序反了探针会覆盖真实错误） |
| `kb_unavailable_message()`（L225–233） | 生成状态文案：**KB 已加载时用中性语气**（不再报"未命中"失败），未加载时才给原因 |

> ⭐ **排障铁律（血泪总结）**：告警文案里写的变量，必须与触发它的判断条件核对的是**同一个变量**。曾经把「检索空」误报成「KB 未加载」，误导排查方向很久。而且「资源已加载」≠「检索有命中」，必须**分开判断、分开报错**。

---

## 3.5 RAG 评测：2,754 条 chunk-derived 查询

### 测试集怎么造（关键设计）

**不是人工手写问题**（那样指标虚高、还容易无意识作弊），而是业界标准的 **chunk-derived benchmark**（与 BEIR / MS MARCO / RAGAS testset 同源）：

```
从 12,594 个真实 chunk 中筛出「合格 chunk」
   ↘ 合格标准：散文型（is_prose）+ 长度 60~800 字 + 含数字 + 命中金融关键词（FIN_KW 125 词）
   ↘ 筛后得 8,115 个合格 chunk（白酒1695 / 红利3172 / 贵金属2266 / 宏观982）
   ↘ 为每个 chunk 「反向合成」一个"答案就在这一段里"的问题
   ↘ 该 chunk 所属主体（公司 / 政策主题）即为 gold qrels（标准答案）
```

**相关性判定**（RAGAS 式 entity/document-level）：
- **二值**：Top-K 命中 gold 主体上下文 → 相关=1，否则 0；
- **NDCG 分级**：精确命中源 chunk = 2，同主体其他 chunk = 1。

**评测口径**：bge 编码 → 所属 collection 内余弦 Top-5（本版叠加混合重排）→ 计算标准 IR 指标。

### 真实结果（2,754 条）

| 指标 | 数值 | 解读 |
|---|---|---|
| Recall@5 | **0.9628** | 96.3% 的问题能翻到正确公司的资料 |
| Precision@5 | 0.8881 | Top-5 里 88.8% 是相关片段 |
| MRR | 0.9385 | 正确片段平均排在第 1 位附近 |
| NDCG@5 | 0.9348 | 综合排序质量 |
| **精确 chunk 命中率@5** | **0.0759**（重排前 0.0727） | ⚠️ 诚实公开的短板 |
| 来源覆盖（Top-5） | 2.521 | 平均来自 2.52 份不同文档 |
| 余弦相似度均值 | 0.6651（Top-1） | — |

### 生成端评测（RAGAS 的另一半）

用**与线上专家智能体完全相同的 system/user prompt**（`generation_eval.generation_prompt`）拼 Top-5 片段生成答案，再由 **DeepSeek 当裁判（LLM-as-Judge）**逐条打 0~1 分：

| 指标 | 数值 | 解读 |
|---|---|---|
| **Faithfulness 忠实度** | **0.8988** | 90% 内容能在检索资料里找到依据，基本无幻觉 |
| **Answer Relevance 答案相关性** | **0.8666** | 87% 回答切题 |
| **Context Utilization 上下文利用率** | **0.8744** | 87% 回答真用上了检索片段 |

分行业忠实度：白酒 0.909 / 红利 0.911 / 贵金属 0.934 / **宏观 0.841**（宏观同时是检索短板，两处一致）。

无 API Key 或断网时脚本**自动降级为离线代理指标**，并如实标注 `mode=proxy`——**不用假数字冒充真值**。

### 精确命中率为什么只有 7.6%？（归因）

| 失效模式 | 占比 | 说明 |
|---|---|---|
| **近距亲兄弟挤占** | ~12% | gold 排在第 6–20 名，被同公司其他 chunk 顶出 Top-5 |
| **淹没在同公司 chunk 海** | ~63% | gold 整库排到 100 名开外 |

**证据**：未命中的查询里，**86.6% 的 Top-5 至少含 1 个同公司 chunk**；Top-5 中平均 2.95/5 条来自同一家公司 → **实体级检索极准，只是"具体哪一段"定不准**。

**反例佐证**：宏观精确命中率反而最高（11.2%）——因为它 chunk 数少、同质度低、兄弟少，越容易 pinpoint。红利最低（5.9%）——同公司分红政策段落高度雷同。

**为什么放宽 chunk 长度上限反而可能变差**：长 chunk 会混合多个主题 → embedding 被平均化得更"通用" → 更易被其他通用 chunk 超分；同时合格 chunk 基数变大、同主体"兄弟片段"更多，精确命中的分母也被推大。

> ⭐ **"低"不代表"坏"**：实体级召回 96.3%、生成忠实度 0.90 —— LLM 拿到同公司的另一段有用信息，通常同样能答好。这个指标的本质是**排序特异性诊断器**，它精准指向下一步优化方向：**① 换更强/领域化 embedding（需重嵌 Chroma）；② 查询改写/扩展让 gold 进 Top-100；③ 更细粒度切分 + 按公司分桶。**
>
> ⚠️ 重排的境遇也印证了这点：**约 63% 的 gold 落在 Top-100 之外** → 任何"只重排已召回候选"的重排器在结构上就够不到它们。**精确命中率的天花板被检索覆盖率锁死，重排只能在候选池内部起作用。**
>
> 但要注意"候选池内部"仍有可观空间，**别把这句话误读成"重排无用"**：换更强的重排器（真 cross-encoder）能把候选池内的命中率再抬一大截——见 §3.6 的三路对照（6% → 10% → 17%）。**准确的两层归因是：池内有空间（换重排器，二阶）；池外是天花板（提覆盖率，一阶）。**

---

## 3.6 重排器三路对照实验（2026-09-15）

### 动机：先质疑自己的选型依据

§3.2 里"两段式检索"生效的是 late-interaction，当时写进文档的理由是"HF 下载太慢、零额外下载更实际"。**复盘时发现这个论证有问题**——那是环境约束，不是技术判断；把"当时只能这样"写成"应该这样"，等于让一个偶然的工程限制冒充技术结论。

于是先解决模型可用性：

```
HF 缓存 models--BAAI--bge-reranker-base/ 里实际是 ONNX 格式（protobuf 头，含 pytorch / roberta 节点）
  → CrossEncoder 按 model.safetensors / pytorch_model.bin 查找 → 必然失败
  → 绕开封装，直接用 onnxruntime.InferenceSession（输入 input_ids + attention_mask，输出 logits (batch,1)）
  → 17.9 ms/对（4 线程 CPU），打分方向正确（相关段落 −0.13 / 无关 −3.8、−9.9）
```

### 实验设计：只换最后一步排序器

同一批查询、同一个 bi-encoder Top-100 候选池、同一套命中判定口径（三路完全一致），唯一变量是"谁来排这 100 个候选"：

| 路 | 排序器 | 说明 |
|---|---|---|
| **A** | 无（纯 bi-encoder 取 Top-5） | 基线 |
| **B** | late-interaction hybrid（0.6 余弦 + 0.4 MaxSim） | 当时的上线方案 |
| **C** | **真 cross-encoder**（bge-reranker-base，ONNX 推理） | 待验证方案 |

样本：每行业 25 条查询（确定性等距抽样、可复现），共 100 条。

**工程上的三个坑**（都是实踩出来的）：

1. **torch 与 1.1GB 的 ONNX 同进程会被静默杀掉**（无任何 Python 报错、进程直接消失）→ 拆成**两段式独立进程**：stage A 只用 bge + Chroma 产出候选落盘，stage B 只加载 ONNX 打分。
2. **ONNX 默认内存池在长序列 + batch > 1 时同样会被杀** → `SessionOptions.enable_cpu_mem_arena = False`，输入截断到 256 token、batch 降到 2。
3. 进程仍会在跑完 1~3 个行业后被环境回收 → 加**按行业增量落盘**，分 4 次续跑完成。

### 结果

| 行业 | A 纯 bi-encoder | B late-interaction | **C cross-encoder** |
|---|---|---|---|
| 白酒 | 16.0% | 24.0% | **32.0%** |
| 红利 | 0.0% | 0.0% | **12.0%** |
| 贵金属 | 0.0% | 0.0% | **8.0%** |
| 宏观 | 8.0% | 16.0% | **16.0%** |
| **总体（n=100）** | **6.0%** | **10.0%** | **17.0%** |

**四个行业上排序完全一致：C ≥ B ≥ A，无一例外。**

### 结论与必须声明的局限

**结论**：
- 真 cross-encoder 是三者中最强的；在 B 和 A 全部为零的两个行业（红利、贵金属）上它仍能捞出 gold —— 说明它确实在建模更细的 query–doc 交互，而不是简单放大相似度。
- 因此 §3.2 里"late-interaction 是更实际的选择"应改判为：**"它是在 cross-encoder 不可用时的退路"**。这是对自己此前技术选型的一次修正。
- 但这**不动摇**覆盖率结论：C 依然只能在 Top-100 候选池内部选，池外那 63% 照样够不到。

**局限（写进任何结论都必须一并交代）**：
- **n=100 太小**：10% 量级的命中率在 n=100 下的 95% 置信区间约 ±6pt，**绝对幅度不可外推**；要升级为主指标需全量重跑 2,754 条（约 27.5 万候选对，CPU 预计 1.5 小时以上）。
- 命中判定用的是 `(source, page)` **代理口径**（比主指标按 `chunk_id` 判定宽松），三路一致故**可作相对比较**，但**不可与 headline 的 0.0759 直接对比**。
- C 阶段按 256 token 截断，可能轻微低估 cross-encoder 的能力。

> 📄 数据文件：`fin_synagent/rerank_experiment.json`（方法论 / 样本量 / 局限 / 下一步）。
> 🧪 实验脚本：`exp_ce_stageA.py`（候选产出）· `exp_ce_stageB.py`（cross-encoder 打分，支持续跑）。

---

# 第四部分 · 三个模块如何咬合成一条链

```
用户提问
   │
   ├─→【智能咨询】retrieve 节点 ──调用──→【RAG 知识库】get_rag_hits(行业, 问题)
   │        ↑                                     ↑
   │   行业路由（关键词）                    离线建库（bge + Chroma 四库）
   │        │                                     ↑
   │   把 Top-5 片段拼成 rag_ctx            评测脚本实跑 → 写入 kb_data.json 快照
   │        ↓
   │   expert → critic ⇄ revise → verify → summarize
   │
   └─→【智能荐股】自建筛选树（不依赖 RAG，走真实行情 + 四维特征 + 确定性打分）
```

**两条能力的定位差异很清晰**：

| 维度 | 智能咨询 | 智能荐股 |
|---|---|---|
| 输入 | 自由文本问题 | 结构化选择（行业 + 风险偏好） |
| 推理形态 | 多智能体流水线 + 反思回环 | 筛选树 + 四维特征 + 确定性加权打分 |
| 与知识库关系 | **强依赖**（检索是核心环节） | 不依赖（用行情/财务数据） |
| 核心机制 | 批评—修订回环 + 信源求证 | 可解释打分 + 结构校验回环 |
| 输出 | 分析结论 + 信源标注 | Top-3 推荐 + 分项得分明细 |

---

# 附：三模块速查表

| 模块 | 环节数 | 关键节点/步骤 | 回环 | 关键数字 |
|---|---|---|---|---|
| **智能咨询** | 7 | leader → retrieve → expert → critic ⇄ revise → verify → summarize | 有（max_loop=2） | 7 节点；行业路由 3 库 + 宏观兜底 |
| **智能荐股** | 12 | fetch_data / planner / build_pool / fetch_comments / 四维特征 / synthesize / scorer / reasoner ⇄ critic | 有（max_loop=1） | 5 候选 → Top-3；权重 0.30/0.30/0.25/0.15 |
| **RAG 知识库** | 离线 5 + 在线 5 | 收集 → 提取 → 切分 → 向量化 → 入库 ／ 路由 → 编码 → 检索 → 拼 Prompt → 生成标注 | — | 152 文档 / 12,594 chunk / 512 维；2,754 条评测 |
| **重排对照**（附加实验） | 3 路 | 纯 bi-encoder ／ late-interaction（上线）／ 真 cross-encoder | — | n=100：6% / 10% / **17%**；四行业排序一致 |

---

*本文档所有描述均对照仓库当前代码（`agent_graph.py` / `screen_graph.py` / `kb.py` / `app.py` / `build_kb/*.py`）与 `kb_data.json` 实值编写，含明确标注的已知局限（关键词式行业路由、线上检索为离线快照、critic 强制回环、当前重排后端为次优退路等）。*
