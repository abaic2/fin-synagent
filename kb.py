"""Fin Synagent · 知识库离线 bundle 加载与检索（独立模块）

把 KB 的加载、检索、诊断从 app.py 抽离为本模块，原因：
  * 之前通过 LangGraph `state["rag_fn"]` 注入检索函数，在云端（不同 langgraph 版本）
    Callable 类型 channel 未被可靠传播，导致 `retrieve_node` 拿到 `rag_fn=None` → 静默空结果。
  * 抽成独立模块后，`agent_graph.retrieve_node` 直接 `from kb import get_rag_hits` 调用，
    彻底消除依赖注入的脆弱环节；app.py 也直接 import 复用，单一数据源。

本模块只依赖 os / json / sys，不依赖 Streamlit，可被任意模块安全导入。

检索鲁棒性（根除反复出现的『已加载却未命中』空结果）：
  * KB 缺失 / retrieval 非 dict → 返回 []
  * 行业集合可能是 dict（query→hits）或 list（命中列表 / {query,hits} 对），
    用通用递归收集器 `_iter_hits` 从任意结构中抽取命中，杜绝结构假设导致空结果。
  * 排序：有查询则按『字符重叠』降序（最相关在前），否则按 bundle 内 score 降序；
    关键：**收集整个行业的所有命中后统一排序取 Top-K，绝不因单个查询缺失/为空而整体返回空**。
  * 行业集合缺失或为空 → 跨全部行业全局兜底。
  * 全程 try/except，任何异常都转为可读错误（写入 KB_RETRIEVE_ERROR）并返回 []，绝不静默。
"""
from __future__ import annotations

import os
import json

KB_DATA_PATH = os.path.join(os.path.dirname(__file__), "kb_data.json")

# 模块级直接加载一次（Streamlit 每个进程只跑一次模块级代码，无需 cache）
KB_LOAD_ERROR = None
# 最近一次 get_rag_hits 的失败原因（空结果或异常），供告警自诊断内联展示
KB_RETRIEVE_ERROR = None


def _read_kb_bundle(path):
    """读取离线知识库 bundle。返回 (data, error)：
    - 成功：(dict, None)
    - 失败：(None, 可读原因字符串)
    兼容性：用 utf-8-sig 容忍带 BOM 的文件；缺失/损坏/结构异常均给出可读原因。"""
    if not os.path.exists(path):
        return None, f"文件不存在：{path}"
    try:
        with open(path, encoding="utf-8-sig") as f:  # utf-8-sig 兼容带 BOM 的源文件
            data = json.load(f)
    except Exception as e:
        return None, f"JSON 解析失败：{type(e).__name__}：{e}"
    if not isinstance(data, dict) or "retrieval" not in data:
        return None, "结构异常：缺少 'retrieval' 字段，可能不是有效的知识库 bundle"
    return data, None


def load_kb_data():
    """一次性加载离线知识库 bundle。

    注：曾用 @st.cache_data 包裹，但 Streamlit 缓存对大对象/返回元组的序列化会返回
    损坏的假值（空 dict 等），导致『KB 非 None 却为假值』的疑难降级，故改为直接加载。"""
    return _read_kb_bundle(KB_DATA_PATH)


KB, KB_LOAD_ERROR = load_kb_data()
if KB is None:
    import sys
    print(f"[FinSynagent] WARNING: kb_data.json 未加载 -> {KB_LOAD_ERROR}", file=sys.stderr)


def _iter_hits(node):
    """从任意 KB 检索节点（dict / list / 嵌套）中递归抽取所有『命中』片段字典。

    命中字典的判定：包含任一常见字段（text/source/page/title/content/chunk）。
    这样无论行业集合是 dict(query→hits) 还是 list(hits) 还是 list({query,hits})，
    都能正确抽全，彻底消除因结构假设导致的空结果。"""
    if isinstance(node, dict):
        if any(k in node for k in ("text", "source", "page", "title", "content", "chunk")):
            yield node
        else:
            for v in node.values():
                yield from _iter_hits(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_hits(v)


def _overlap(a, b):
    """字符重叠计数（集合交集大小），用于衡量用户问题与某条已存查询的相关度。"""
    if not a or not b:
        return 0
    sa = set(a)
    return sum(1 for ch in sa if ch in b)


def _score_hits(node, user_query):
    """从任意结构 node 中抽取命中并打分，返回 [(overlap, stored_score, hit), ...]。

    - node 为 dict 时视为 query→hits 映射：每条命中按『用户问题与 query 的字符重叠』打分，
      重叠高的查询其命中更相关。
    - node 为 list / 嵌套时：递归收集，overlap 记为 0（按 bundle 内 score 排序）。
    - 单个查询 hits 为空（[] 或缺失）只贡献 0 条，绝不会拖垮整体返回，这是根除空结果的关键。
    """
    scored = []
    if isinstance(node, dict):
        for q, hits in node.items():
            overlap = _overlap(user_query, q) if user_query else 0
            if isinstance(hits, list):
                items = hits
            else:
                items = [hits]  # 单条命中也包成列表统一处理
            for h in items:
                if isinstance(h, dict):
                    scored.append((overlap, float(h.get("score", 0) or 0), h))
                else:
                    # 极少数非字典条目：包装保留原文，按 0 分参与排序
                    scored.append((overlap, 0.0, {"text": str(h)}))
    else:
        # list / 其他：递归收集，overlap 记 0
        for h in _iter_hits(node):
            scored.append((0, float(h.get("score", 0) or 0), h))
    return scored


def _reread_file_diag():
    """重新读取 kb_data.json 现场，返回文件实际结构诊断（供 KB 健康但检索空时对比）。"""
    try:
        with open(KB_DATA_PATH, encoding="utf-8-sig") as f:
            raw = f.read()
        real = json.loads(raw)
        real_type = type(real).__name__
        real_keys = list(real.keys())[:10] if isinstance(real, dict) else "n/a"
        return f"文件实际：type={real_type}, len={len(real) if hasattr(real, '__len__') else 'n/a'}, top_keys={real_keys}, 大小={len(raw)}B"
    except Exception as e:
        return f"复核读取失败：{type(e).__name__}：{e}"


def kb_unload_reason(rag_key=None):
    """返回『为何没有检索片段』的可读诊断。重点：KB 已加载 ≠ 检索必有命中，
    需进一步看 retrieval 子结构；并用空查询探针现场复测，把真实原因内联展示，
    杜绝『未知原因』，也无需再去翻云端日志。

    永远带上路径与真实诊断。"""
    if KB_LOAD_ERROR:
        return f"KB 加载失败：{KB_LOAD_ERROR}（路径：{KB_DATA_PATH}）"
    if KB is None:
        if not os.path.exists(KB_DATA_PATH):
            return f"KB 文件不存在（路径：{KB_DATA_PATH}）"
        try:
            with open(KB_DATA_PATH, encoding="utf-8-sig") as f:
                d = json.load(f)
        except Exception as e:
            return f"KB JSON 解析失败：{type(e).__name__}：{e}（路径：{KB_DATA_PATH}）"
        if not isinstance(d, dict) or "retrieval" not in d:
            return f"KB 文件结构异常：缺少 'retrieval' 字段（路径：{KB_DATA_PATH}）"
        return f"KB 文件已读取但解析结果为 None（路径：{KB_DATA_PATH}）"
    if not bool(KB):
        kb_type = type(KB).__name__
        kb_len = len(KB) if hasattr(KB, "__len__") else "n/a"
        return f"KB 是假值（type={kb_type}, len={kb_len}）；{_reread_file_diag()}（路径：{KB_DATA_PATH}）"
    # KB 健康加载：先捕获『触发本次告警的真实查询』留下的错误，再跑空查询探针（避免探针覆盖）
    real_err = KB_RETRIEVE_ERROR
    retrieval = KB.get("retrieval")
    ret_keys = list(retrieval.keys()) if isinstance(retrieval, dict) else f"非 dict（{type(retrieval).__name__}）"
    coll_key = "宏观" if rag_key in (None, "default") else rag_key
    probe = get_rag_hits(rag_key, "") if callable(get_rag_hits) else []
    reason = (f"KB 已正常加载（顶层 {len(KB)} 键，retrieval 含行业：{ret_keys}）；"
              f"本次检索域 '{coll_key}'，空查询探针命中 {len(probe)} 条")
    if real_err:
        reason += f"；真实检索失败原因：{real_err}"
    elif len(probe) == 0:
        reason += "；检索函数本应返回命中但未返回，请查云端日志『get_rag_hits』"
    return reason


def kb_unavailable_message(rag_key=None):
    """生成『检索不可用』告警文案：准确区分『KB 没加载』与『KB 已加载但检索未命中』。"""
    if KB is None or not bool(KB):
        return f"知识库 bundle 未加载（{kb_unload_reason(rag_key)}），已回退至通用分析。"
    return f"知识库已加载，但本次检索未命中相关片段（{kb_unload_reason(rag_key)}），已回退至通用分析。"


def kb_status_info():
    """知识库加载诊断：返回部署环境的真实状态，供状态面板与告警复用。"""
    info = {
        "loaded": bool(KB),  # 用 bool 而非 is not None：空 dict/list 等假值也判为未加载
        "actual_type": type(KB).__name__,
        "path": KB_DATA_PATH,
        "exists": os.path.exists(KB_DATA_PATH),
        "size": None,
        "parse_ok": None,
        "keys": None,
        "reason": kb_unload_reason(),
    }
    if info["exists"]:
        try:
            info["size"] = os.path.getsize(KB_DATA_PATH)
        except Exception:
            pass
        try:
            with open(KB_DATA_PATH, encoding="utf-8-sig") as f:
                d = json.load(f)
            info["parse_ok"] = True
            info["keys"] = list(d.keys()) if isinstance(d, dict) else None
        except Exception as e:
            info["parse_ok"] = False
            info["keys"] = None
            info["reason"] = f"JSON 解析失败：{type(e).__name__}：{e}（路径：{KB_DATA_PATH}）"
    elif not info["reason"]:
        info["reason"] = f"文件不存在（路径：{KB_DATA_PATH}）"
    return info


def get_rag_hits(industry, user_query):
    """从离线检索 bundle 中按行业路由取出 Top-K 片段。

    鲁棒性（根除反复出现的『已加载却未命中』空结果）：
      * KB 缺失 / retrieval 非 dict → 返回 []
      * 任意结构（dict / list / 嵌套）都能抽全命中
      * 排序逻辑：收集整个行业的所有命中 → 按『字符重叠降序、其次 bundle 内 score 降序』统一排序
        → 去重取 Top-K。即使某个查询映射为空、或结构异常，也只会少几条，绝不会整体返回空。
      * 行业集合缺失或为空 → 跨全部行业全局兜底
      * 任意异常 → 转为可读错误（KB_RETRIEVE_ERROR）并返回 []，绝不静默
    """
    global KB_RETRIEVE_ERROR
    KB_RETRIEVE_ERROR = None
    if not KB:
        KB_RETRIEVE_ERROR = "KB 未加载（模块级加载失败）"
        return []
    try:
        coll_key = "宏观" if industry in (None, "default") else industry
        retr = KB.get("retrieval", {}) or {}
        if not isinstance(retr, dict):
            KB_RETRIEVE_ERROR = f"retrieval 非 dict（{type(retr).__name__}）"
            return []

        # 1) 收集本行业全部命中并打分（overlap, stored_score, hit）
        qmap = retr.get(coll_key, {})
        scored = _score_hits(qmap, user_query)

        # 2) 本行业为空 → 跨全部行业全局兜底
        if not scored:
            for ckey, cval in retr.items():
                if ckey == coll_key:
                    continue
                scored.extend(_score_hits(cval, user_query))

        if not scored:
            KB_RETRIEVE_ERROR = (
                f"空结果: coll_key={coll_key!r}, qmap_type={type(qmap).__name__}, "
                f"qmap_size={len(qmap) if hasattr(qmap, '__len__') else 'n/a'}, "
                f"retrieval_keys={list(retr.keys())}")
            import sys
            print(f"[FinSynagent] get_rag_hits EMPTY: {KB_RETRIEVE_ERROR}; path={KB_DATA_PATH}",
                  file=sys.stderr)
            return []

        # 3) 排序：字符重叠降序，其次 bundle 内 score 降序
        scored.sort(key=lambda t: (-t[0], -t[1]))

        # 4) 去重（同一片段可能来自多个查询/集合）后取 Top-K
        seen, result = set(), []
        for _, _, h in scored:
            key = (h.get("text") or "")[:80]
            if key in seen:
                continue
            seen.add(key)
            result.append(h)
        return result[:4]
    except Exception as e:
        import sys
        import traceback
        KB_RETRIEVE_ERROR = f"异常: {type(e).__name__}: {e}"
        print(f"[FinSynagent] get_rag_hits ERROR: {e!r}\n{traceback.format_exc()}", file=sys.stderr)
        return []
