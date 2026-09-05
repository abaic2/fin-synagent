"""Fin Synagent · 智能咨询 LangGraph 多智能体编排
================================================

把 Consult 智能咨询的 System-2 流水线实现为 **LangGraph 状态图（StateGraph）**。

节点（每个节点 = 一个智能体角色）：
  leader     👔 Leader 领导智能体：把用户问题拆解为子任务并分配专家
  retrieve   📚 RAG 知识库检索：从 Chroma 行业向量库召回高相关片段
  expert     🎓 专家智能体：基于检索片段生成专业回答
  critic     🧐 评论家智能体：审查专家回答，给出批评与改进建议
  revise     ✍️ 专家智能体（修订）：针对批评完善回答
  verify     🔎 搜索与求证智能体：核验真实性、列出可溯源来源
  summarize  📋 总结领导：汇总最终投资建议

回环（框架化带来的核心收益）：
  critic 判定「需要修订」且 loop < max_loop 时，经条件边回到 revise，
  revise 再回到 critic，形成真正的「批评—修订」反思回环；否则进入 verify。

设计原则：
  * 本模块**不依赖 Streamlit**，纯逻辑；UI 由 app.py 通过 `trace` 列表 / `on_step` 回调渲染。
  * LLM 调用与 RAG 检索通过 `state["llm_text"]` / `state["rag_fn"]` 注入，
    使编排与具体模型/知识库解耦，便于测试（可注入 mock）与复用。
"""
from __future__ import annotations

import operator
from typing import Annotated, Callable, Optional, TypedDict

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover - 让 import 失败时 app.py 能捕获并回退
    StateGraph = None
    END = None


# ----------------------------- 状态定义 -----------------------------
class ConsultState(TypedDict, total=False):
    # —— 输入 / 配置（由调用方注入，图内不修改） ——
    query: str
    decomp_level: int
    rag_key: str
    kb_tag: str
    real: bool
    max_loop: int
    loop: int
    script: dict                     # 演示模式 fallback 脚本（match_script 的返回值）
    llm_text: Callable               # (system, user, fallback) -> str
    rag_fn: Callable                 # (rag_key, query) -> list[hit]
    on_step: Optional[Callable]      # 可选 UI 回调 (state, step) -> None

    # —— 各智能体产出（图内累积） ——
    leader: str
    expert: str
    critic: str
    verdict: str                     # critic 判定： "revise" / "pass"
    expert_revise: str
    verify: str
    summary: str
    rag_hits: list
    rag_ctx: str

    # —— 可观测轨迹（append-only，带 reducer） ——
    trace: Annotated[list, operator.add]


# ----------------------------- 工具函数 -----------------------------
def _emit(state: ConsultState, agent: str, title: str, content: str):
    """构造一条轨迹并触发可选 UI 回调。返回单条 list 以便 Annotated[list] 累加。"""
    step = {"agent": agent, "title": title, "content": content}
    cb = state.get("on_step")
    if callable(cb):
        try:
            cb(state, step)
        except Exception:
            pass
    return [step]


# ----------------------------- 智能体节点 -----------------------------
def leader_node(state: ConsultState) -> dict:
    script = state.get("script", {}) or {}
    fb = ("\n".join(f"- 子任务：{t}" for t in script.get("subtasks", []))
          + f"\n- 分配专家：{'、'.join(script.get('experts', []))}")
    leader = state["llm_text"](
        "你是 Fin 智能投顾系统的 Leader 领导智能体。负责把用户的投资咨询问题拆解为若干子任务并分配专家。"
        "请只输出纯文本 Markdown 列表：每行一个「- 子任务：<名称>」，最后一行「- 分配专家：<专家名>」。不要添加额外解释。",
        f"用户问题：{state['query']}\n拆解粒度：{state.get('decomp_level', 3)} 级（粒度越高，子任务越细）。请给出子任务列表与分配的专家。",
        fb,
    )
    return {"leader": leader,
            "trace": _emit(state, "leader", "👔 Leader 领导智能体 · 任务拆解", leader)}


def retrieve_node(state: ConsultState) -> dict:
    rag_fn = state.get("rag_fn")
    hits = rag_fn(state["rag_key"], state["query"]) if callable(rag_fn) else []
    rag_ctx = ("\n".join(f"【{h['source']} · p{h['page']}】{h['text']}" for h in hits)
               if hits else "（知识库未加载，以下为通用分析）")
    return {"rag_hits": hits, "rag_ctx": rag_ctx,
            "trace": _emit(state, "retrieve", "📚 知识库检索（RAG）", rag_ctx)}


def expert_node(state: ConsultState) -> dict:
    exp = state["llm_text"](
        "你是 Fin 智能投顾系统的行业专家智能体（金融领域资深分析师）。请基于【知识库检索片段】与用户问题，输出专业、数据驱动、可追溯的投资分析。"
        "要求：使用 Markdown，分点论述，关键结论加粗，必要时给出风险提示。语言为中文。",
        f"用户问题：{state['query']}\n\n【知识库检索片段】\n{state['rag_ctx']}\n\n请基于以上信息给出专业回答。",
        (state.get("script", {}) or {}).get("expert_answer", ""),
    )
    return {"expert": exp,
            "trace": _emit(state, "expert", "🎓 专家智能体（DeepSeek-Chat）· 生成回答", exp)}


def critic_node(state: ConsultState) -> dict:
    crit = state["llm_text"](
        "你是 Fin 智能投顾系统的评论家智能体。请审查专家回答，指出遗漏、逻辑漏洞、数据存疑之处，并给出改进建议。用中文 Markdown 要点输出。",
        f"用户问题：{state['query']}\n\n【专家回答】\n{state['expert']}\n\n请给出批评意见与改进建议。",
        (state.get("script", {}) or {}).get("critic", ""),
    )
    # 判定回环：演示模式仅修订一次（loop==0 时 revise，之后 pass）；
    # 真实模式下依据评论家文本中的「通过/无需修改」类信号决定。
    if state.get("real"):
        _pass_kw = ["无需修改", "无需修订", "分析充分", "无需补充", "无需完善", "已较完整", "通过", "无需返工"]
        verdict = "pass" if any(k in crit for k in _pass_kw) else "revise"
    else:
        verdict = "revise" if state.get("loop", 0) == 0 else "pass"
    return {"critic": crit, "verdict": verdict,
            "trace": _emit(state, "critic", "🧐 评论家智能体 · 审查", crit)}


def revise_node(state: ConsultState) -> dict:
    rev = state["llm_text"](
        "你是 Fin 智能投顾系统的专家智能体。请根据评论家的批评意见，完善并修订你的回答，输出修订后的完整要点。中文 Markdown。",
        f"用户问题：{state['query']}\n\n【原专家回答】\n{state['expert']}\n\n【评论家意见】\n{state['critic']}\n\n请输出完善后的回答要点。",
        (state.get("script", {}) or {}).get("expert_revise", ""),
    )
    return {"expert_revise": rev, "loop": state.get("loop", 0) + 1,
            "trace": _emit(state, "revise", "✍️ 专家智能体 · 完善回答", rev)}


def verify_node(state: ConsultState) -> dict:
    script = state.get("script", {}) or {}
    fb = "已检索知识库与互联网，交叉验证关键数据，未发现幻觉内容。信息源如下：\n" + "\n".join(
        f"- {src}" for src in script.get("verify", []))
    ver = state["llm_text"](
        "你是 Fin 智能投顾系统的搜索与求证智能体。请针对分析中的关键数据与结论，列出可溯源的信息来源（研究报告/数据/新闻），并判断是否可能存在幻觉。中文 Markdown 列表。",
        f"用户问题：{state['query']}\n\n【最终分析要点】\n{state['expert_revise']}\n\n请列出信息源并核验真实性。",
        fb,
    )
    return {"verify": ver,
            "trace": _emit(state, "verify", "🔎 搜索与求证智能体 · 验证", ver)}


def summarize_node(state: ConsultState) -> dict:
    summ = state["llm_text"](
        "你是 Fin 智能投顾系统的总结领导。请基于以上全流程（任务拆解、专家分析、评论家审查、修订、求证），给出最终投资建议与可执行结论。中文 Markdown，简明有力。",
        f"用户问题：{state['query']}\n\n【专家修订回答】\n{state['expert_revise']}\n\n【验证信息源】\n{state['verify']}\n\n请给出最终建议。",
        (state.get("script", {}) or {}).get("summary", ""),
    )
    return {"summary": summ,
            "trace": _emit(state, "summarize", "📋 总结领导 · 最终建议", summ)}


# ----------------------------- 图构建与路由 -----------------------------
def _route_after_critic(state: ConsultState) -> str:
    """评论家之后的条件路由：需要修订且未达上限 → revise，否则 → verify。"""
    if state.get("verdict") == "revise" and state.get("loop", 0) < state.get("max_loop", 2):
        return "revise"
    return "verify"


_GRAPH = None


def build_graph():
    """构造并编译 LangGraph 状态图。"""
    g = StateGraph(ConsultState)
    g.add_node("leader", leader_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("expert", expert_node)
    g.add_node("critic", critic_node)
    g.add_node("revise", revise_node)
    g.add_node("verify", verify_node)
    g.add_node("summarize", summarize_node)

    g.set_entry_point("leader")
    g.add_edge("leader", "retrieve")
    g.add_edge("retrieve", "expert")
    g.add_edge("expert", "critic")
    g.add_conditional_edges("critic", _route_after_critic,
                            {"revise": "revise", "verify": "verify"})
    g.add_edge("revise", "critic")          # 修订后再次接受评论家审查（回环）
    g.add_edge("verify", "summarize")
    g.add_edge("summarize", END)
    return g.compile()


def get_graph():
    """返回（惰性编译并缓存的）已编译状态图。"""
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def build_initial_state(*, query: str, decomp_level: int, rag_key: str, kb_tag: str,
                        real: bool, script: dict, llm_text: Callable,
                        rag_fn: Callable, max_loop: int = 2,
                        on_step: Optional[Callable] = None) -> dict:
    """构造 LangGraph 初始状态（注入配置与依赖）。"""
    return {
        "query": query,
        "decomp_level": decomp_level,
        "rag_key": rag_key,
        "kb_tag": kb_tag,
        "real": real,
        "max_loop": max_loop,
        "loop": 0,
        "script": script,
        "llm_text": llm_text,
        "rag_fn": rag_fn,
        "on_step": on_step,
        "trace": [],
    }


def run_consult(initial_state: dict) -> dict:
    """执行整条多智能体流水线，返回含全部产出与 trace 的最终状态。"""
    return get_graph().invoke(initial_state)


__all__ = ["ConsultState", "build_graph", "get_graph", "build_initial_state",
           "run_consult"]
