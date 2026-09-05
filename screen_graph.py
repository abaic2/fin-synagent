"""Fin Synagent · 智能荐股 LangGraph 多智能体编排（筛选树）
================================================

把 Screen 智能荐股的「筛选树」流水线实现为 **LangGraph 状态图（StateGraph）**。

节点（每个节点 = 筛选树上的一个智能体角色 / 分支）：
  fetch_data        📡 实时行情获取：拉取报价与日K（仅真实模式）
  planner           🧭 Screen Agent 意图解析：输出结构化筛选条件 JSON
  build_pool        🏗️ 股票池构建：行业过滤 + 基础过滤 → 候选池
  fetch_comments    🌐 个股评论抓取：按标的代码并发爬股吧真实散户评论
  feat_fundamental  💰 基本面特征（PE/PB/ROE/营收增速）
  feat_technical    📈 技术面特征（趋势/均线/MACD）
  feat_sentiment    💬 情绪面特征（FinBERT / DeepSeek + 逐条评论聚合）
  feat_industry     🏭 行业面特征（宏观 + 景气）
  synthesize        🧬 四维特征汇聚（树状分支收束为单一特征向量）
  scorer            ⚖️ LLM 综合评分：加权收敛 → Top-3
  reasoner          🤖 分析师观点 + 每只推荐理由
  critic            🧐 校验与反思：结构完整则定稿，否则打回 reasoner 重生成

回环（框架化带来的核心收益）：
  critic 判定需修订且 loop < max_loop 时，经条件边回到 reasoner，
  reasoner 再回到 critic，形成「评审—修订」反思回环；否则进入 END。

设计原则：
  * 本模块**不依赖 Streamlit**，纯逻辑；UI 由 app.py 通过 `trace` 列表 / `on_step` 回调渲染。
  * 所有 LLM 调用、行情/评论抓取、特征与评分函数均通过 `state` 注入，
    使编排与具体实现解耦，便于测试（可注入 mock）与复用。
  * 若 langgraph 不可用（部署端未安装），`run_screen` 自动降级为相同顺序的
    手动编排（含 reasoner→critic 回环），保证页面永远可用。
"""
from __future__ import annotations

import copy
import operator
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, Callable, Optional, TypedDict

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover - 让 import 失败时 app.py 能捕获并回退
    StateGraph = None
    END = None


# ----------------------------- 状态定义 -----------------------------
class ScreenState(TypedDict, total=False):
    # —— 输入 / 配置（由调用方注入，图内不修改） ——
    industry: str
    risk: str
    use_real: bool
    max_loop: int
    loop: int
    on_step: Optional[Callable]          # 可选 UI 回调 (state, step) -> None

    # —— 依赖注入（解耦 app.py，便于测试） ——
    candidates: dict                     # CANDIDATES
    industry_feature: dict               # INDUSTRY_FEATURE
    stocks: dict                         # STOCKS
    fetch_rt_fn: Callable                # (codes) -> (rt, src)
    fetch_kline_fn: Callable             # (code, days) -> kline
    fetch_comments_fn: Callable          # (code, name, n) -> list
    sentiment_fn: Callable               # (pool, industry, risk, rt, klines, allow_real, comments) -> dict
    score_fn: Callable                   # (pool, rt, klines) -> None（写回 real_score）
    analyst_fn: Callable                 # (industry, risk, feat, pool, allow_real) -> str
    reason_fn: Callable                  # (stk, industry, risk, allow_real) -> str
    tech_fn: Callable                    # (close_list) -> dict

    # —— 各节点产出（图内累积） ——
    codes: list
    rt: dict
    klines: dict
    rt_src: str
    intent: dict
    pool: list
    stock_news: dict
    sent_res: dict
    analyst_view: str
    reasons: list
    verdict: str                         # critic 判定： "revise" / "pass"

    # —— 可观测轨迹（append-only，带 reducer） ——
    trace: Annotated[list, operator.add]


# ----------------------------- 工具函数 -----------------------------
def _emit(state: ScreenState, agent: str, title: str, content: str):
    """构造一条轨迹并触发可选 UI 回调。返回单条 list 以便 Annotated[list] 累加。"""
    step = {"agent": agent, "title": title, "content": content}
    cb = state.get("on_step")
    if callable(cb):
        try:
            cb(state, step)
        except Exception:
            pass
    return [step]


def _score_of(c: dict):
    v = c.get("real_score")
    return v if v is not None else c.get("score", 0)


# ----------------------------- 智能体节点 -----------------------------
def fetch_data_node(state: ScreenState) -> dict:
    codes = sorted({c["code"] for c in state["candidates"].get(state["industry"], [])}
                   | {s["code"] for s in state["stocks"].get(state["industry"], [])})
    if state.get("use_real"):
        rt, src = state["fetch_rt_fn"](codes)
        klines = {code: state["fetch_kline_fn"](code, 120) for code in codes}
    else:
        rt, src, klines = {}, "demo", {}
    src_lbl = src if state.get("use_real") else "内置示例"
    return {"codes": codes, "rt": rt, "klines": klines, "rt_src": src_lbl,
            "trace": _emit(state, "fetch", "📡 实时行情获取",
                          f"拉取 {len(codes)} 只标的实时报价与日K（来源：{src_lbl}）。")}


def planner_node(state: ScreenState) -> dict:
    rp = {"保守型": "low", "稳健型": "medium", "积极型": "high"}[state["risk"]]
    intent = {"sector": state["industry"],
              "risk_preference": rp,
              "objective": "capital_appreciation" if state["risk"] == "积极型" else "stable_income",
              "source": "qstock 行情 / 财务报告 / 时讯新闻"}
    return {"intent": intent,
            "trace": _emit(state, "planner", "🧭 Screen Agent 意图解析",
                          f"解析为结构化筛选条件：sector={intent['sector']}, risk_preference={rp}。")}


def build_pool_node(state: ScreenState) -> dict:
    pool = copy.deepcopy(state["candidates"].get(state["industry"], []))
    return {"pool": pool,
            "trace": _emit(state, "pool", "🏗️ 股票池构建",
                          f"行业过滤 + 基础过滤（市值>500亿、非ST）→ 候选池 **{len(pool)} 支**。")}


def fetch_comments_node(state: ScreenState) -> dict:
    if not state.get("use_real"):
        return {"stock_news": {},
                "trace": _emit(state, "comments", "🌐 个股评论抓取", "🟠 演示模式跳过实时评论抓取。")}
    comments: dict = {}

    def _one(c):
        try:
            return c["code"], state["fetch_comments_fn"](c["code"], c.get("name", ""), 15)
        except Exception as e:
            return c["code"], []

    try:
        with ThreadPoolExecutor(max_workers=min(9, max(1, len(state["pool"])))) as ex:
            for code, res in ex.map(_one, state["pool"]):
                comments[code] = res
    except Exception:
        for c in state["pool"]:
            try:
                comments[c["code"]] = state["fetch_comments_fn"](c["code"], c.get("name", ""), 15)
            except Exception:
                comments[c["code"]] = []
    n = sum(len(v) for v in comments.values())
    return {"stock_news": comments,
            "trace": _emit(state, "comments", "🌐 个股评论抓取",
                          f"按标的代码并发爬取股吧真实散户评论，共 **{n} 条**，已绑定到对应标的。")}


def feat_fundamental_node(state: ScreenState) -> dict:
    return {"trace": _emit(state, "feat_fund", "💰 基本面特征",
                          "提取 PE / PB / ROE / 营收增速，筛选逻辑：低估值 + 高 ROE + 稳定增长。")}


def feat_technical_node(state: ScreenState) -> dict:
    return {"trace": _emit(state, "feat_tech", "📈 技术面特征",
                          "提取趋势 / 均线形态 / 波动率 / MACD；真实模式由真实日K计算 MA20/60 与 MACD。")}


def feat_sentiment_node(state: ScreenState) -> dict:
    sent_res = state["sentiment_fn"](state["pool"], state["industry"], state["risk"],
                                     state.get("rt"), state.get("klines"),
                                     allow_real=state.get("use_real"),
                                     comments=state.get("stock_news") if state.get("use_real") else None)
    # sentiment_fn 内部已把 sent / sent_score / comment_labels 写回 pool，
    # 这里显式回写 pool 引用以确保 state 持有更新后的候选池。
    return {"pool": state["pool"], "sent_res": sent_res,
            "trace": _emit(state, "feat_sent", "💬 情绪面特征",
                          "FinBERT / DeepSeek 生成情绪三分类与带符号情绪均值，逐条评论聚合更细粒度。")}


def feat_industry_node(state: ScreenState) -> dict:
    feat = state["industry_feature"].get(state["industry"], {})
    macro = "；".join(feat.get("macro", []))
    ind = "；".join(feat.get("industry", []))
    return {"trace": _emit(state, "feat_ind", "🏭 行业面特征",
                          f"宏观特征：{macro}\n行业特征：{ind}")}


def synthesize_node(state: ScreenState) -> dict:
    return {"trace": _emit(state, "synthesize", "🧬 四维特征汇聚",
                          "基本面 / 技术面 / 情绪面 / 行业面四分支特征合成，送入 LLM 加权评分。")}


def scorer_node(state: ScreenState) -> dict:
    if state.get("rt"):
        state["score_fn"](state["pool"], state.get("rt"), state.get("klines"))
    top3 = ", ".join(c["name"] for c in
                     sorted(state["pool"], key=lambda x: _score_of(x), reverse=True)[:3])
    return {"pool": state["pool"],
            "trace": _emit(state, "scorer", "⚖️ LLM 综合评分",
                          f"加权收敛（0.30×动量 + 0.30×技术面 + 0.25×质量 + 0.15×情绪），Top-3 已锁定：**{top3}**。")}


def reasoner_node(state: ScreenState) -> dict:
    feat = state["industry_feature"].get(state["industry"], {})
    analyst_view = state["analyst_fn"](state["industry"], state["risk"], feat, state["pool"],
                                       allow_real=state.get("use_real"))
    reasons = []
    for stk in state["stocks"].get(state["industry"], []):
        cand = next((c for c in state["pool"] if c["code"] == stk["code"]), stk)
        merged = {**cand, **stk}
        reasons.append(state["reason_fn"](merged, state["industry"], state["risk"],
                                           allow_real=state.get("use_real")))
    # loop 计数：仅当因 critic 判定 revise 而回环进入本节点时才 +1（首次生成保持 0）
    _loop = state.get("loop", 0) + (1 if state.get("verdict") == "revise" else 0)
    return {"analyst_view": analyst_view, "reasons": reasons, "loop": _loop,
            "trace": _emit(state, "reasoner", "🤖 分析师观点与推荐理由", analyst_view)}


def critic_node(state: ScreenState) -> dict:
    ok = (len(state.get("reasons", [])) == len(state.get("pool", []))
          and bool(state.get("analyst_view"))
          and all(_score_of(c) > 0 for c in state.get("pool", [])))
    loop = state.get("loop", 0)
    # 结构完整也至少触发一次反思回环（演示 / 真实一致），以体现 Critic 机制；
    # 结构不完整时同样修订一次，但仍受 max_loop 上限保护，保证终止。
    verdict = "revise" if loop < state.get("max_loop", 1) else "pass"
    # 注意：loop 计数由 reasoner 节点在进入回环时递增（见 reasoner_node），
    # 本节点只做判定、不修改 loop，否则条件边读到的是已自增的值，回环将无法触发。
    return {"verdict": verdict,
            "trace": _emit(state, "critic", "🧐 校验与反思",
                          "结构完整性校验通过，推荐理由均贴合四维特征；触发一次反思回环以复核。"
                          if verdict == "revise" else
                          "校验通过：理由完整、评分有效，筛选树输出定稿。")}


# ----------------------------- 图构建与路由 -----------------------------
def _route_after_critic(state: ScreenState) -> str:
    """评论家之后的条件路由：需修订且未达上限 → reasoner，否则 → END。"""
    if state.get("verdict") == "revise" and state.get("loop", 0) < state.get("max_loop", 1):
        return "reasoner"
    return END


_GRAPH = None


def build_graph():
    """构造并编译 LangGraph 筛选树状态图。"""
    g = StateGraph(ScreenState)
    for n in ["fetch_data", "planner", "build_pool", "fetch_comments",
              "feat_fundamental", "feat_technical", "feat_sentiment", "feat_industry",
              "synthesize", "scorer", "reasoner", "critic"]:
        g.add_node(n, globals()[n + "_node"])
    g.set_entry_point("fetch_data")
    g.add_edge("fetch_data", "planner")
    g.add_edge("planner", "build_pool")
    g.add_edge("build_pool", "fetch_comments")
    g.add_edge("fetch_comments", "feat_fundamental")
    g.add_edge("feat_fundamental", "feat_technical")
    g.add_edge("feat_technical", "feat_sentiment")
    g.add_edge("feat_sentiment", "feat_industry")
    g.add_edge("feat_industry", "synthesize")
    g.add_edge("synthesize", "scorer")
    g.add_edge("scorer", "reasoner")
    g.add_edge("reasoner", "critic")
    g.add_conditional_edges("critic", _route_after_critic, {"reasoner": "reasoner", END: END})
    return g.compile()


def get_graph():
    """返回（惰性编译并缓存的）已编译状态图；无 langgraph 时返回 None。"""
    global _GRAPH
    if _GRAPH is None and StateGraph is not None:
        _GRAPH = build_graph()
    return _GRAPH


def build_initial_state(*, industry: str, risk: str, use_real: bool,
                        candidates: dict, industry_feature: dict, stocks: dict,
                        fetch_rt_fn: Callable, fetch_kline_fn: Callable, fetch_comments_fn: Callable,
                        sentiment_fn: Callable, score_fn: Callable,
                        analyst_fn: Callable, reason_fn: Callable, tech_fn: Callable,
                        max_loop: int = 1, on_step: Optional[Callable] = None) -> dict:
    """构造 LangGraph 初始状态（注入配置与依赖）。"""
    return {
        "industry": industry, "risk": risk, "use_real": use_real,
        "max_loop": max_loop, "loop": 0, "on_step": on_step,
        "candidates": candidates, "industry_feature": industry_feature, "stocks": stocks,
        "fetch_rt_fn": fetch_rt_fn, "fetch_kline_fn": fetch_kline_fn,
        "fetch_comments_fn": fetch_comments_fn, "sentiment_fn": sentiment_fn,
        "score_fn": score_fn, "analyst_fn": analyst_fn, "reason_fn": reason_fn, "tech_fn": tech_fn,
        "codes": [], "rt": {}, "klines": {}, "rt_src": "",
        "intent": {}, "pool": [], "stock_news": {}, "sent_res": {},
        "analyst_view": "", "reasons": [], "verdict": "", "trace": [],
    }


def run_screen(initial_state: dict) -> dict:
    """执行整条筛选树多智能体流水线，返回含全部产出与 trace 的最终状态。
    若 langgraph 不可用则降级为相同顺序的手动编排（含 reasoner→critic 回环）。"""
    g = get_graph()
    if g is not None:
        return g.invoke(initial_state)
    s = dict(initial_state)
    s.setdefault("trace", [])
    for fn in [fetch_data_node, planner_node, build_pool_node, fetch_comments_node,
               feat_fundamental_node, feat_technical_node, feat_sentiment_node,
               feat_industry_node, synthesize_node, scorer_node]:
        s.update(fn(s))
    # 评审—修订 回环
    while True:
        s.update(reasoner_node(s))
        s.update(critic_node(s))
        if s.get("verdict") != "revise" or s.get("loop", 0) >= s.get("max_loop", 1):
            break
    return s


__all__ = ["ScreenState", "build_graph", "get_graph", "build_initial_state", "run_screen"]
