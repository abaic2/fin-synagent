"""Fin Synagent · 知识库离线 bundle 加载与检索（独立模块）

把 KB 的加载、检索、诊断从 app.py 抽离为本模块，原因：
  * 之前通过 LangGraph `state["rag_fn"]` 注入检索函数，在云端（不同 langgraph 版本）
    Callable 类型 channel 未被可靠传播，导致 `retrieve_node` 拿到 `rag_fn=None` → 静默空结果。
  * 抽成独立模块后，`agent_graph.retrieve_node` 直接 `from kb import get_rag_hits` 调用，
    彻底消除依赖注入的脆弱环节；app.py 也直接 import 复用，单一数据源。

本模块只依赖 os / json / sys，不依赖 Streamlit，可被任意模块安全导入。
"""
from __future__ import annotations

import os
import json

KB_DATA_PATH = os.path.join(os.path.dirname(__file__), "kb_data.json")

# 模块级直接加载一次（Streamlit 每个进程只跑一次模块级代码，无需 cache）
KB_LOAD_ERROR = None


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
    需进一步看 retrieval 子结构。永远带上路径与真实诊断，杜绝『未知原因』。"""
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
    # KB 健康加载：钻取 retrieval 子结构，看本次检索域是否有数据
    retrieval = KB.get("retrieval")
    ret_keys = list(retrieval.keys()) if isinstance(retrieval, dict) else f"非 dict（{type(retrieval).__name__}）"
    coll_key = "宏观" if rag_key in (None, "default") else rag_key
    sub = retrieval.get(coll_key, {}) if isinstance(retrieval, dict) else {}
    sub_n = len(sub) if isinstance(sub, dict) else "n/a"
    return (f"KB 已正常加载（顶层 {len(KB)} 键，retrieval 含行业：{ret_keys}）；"
            f"本次检索域 '{coll_key}' 有 {sub_n} 条查询 → 应能命中；"
            f"若仍无片段，请查 Streamlit 云端日志『get_rag_hits EMPTY』（路径：{KB_DATA_PATH}）")


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
    """从真实 Chroma 检索 bundle 中按行业路由取出 Top 片段。

    鲁棒性（根除反复出现的『未命中』空结果）：
      * KB 缺失 → 返回 []
      * 检索域缺失 / 行业 key 不匹配 → 自动跨全部行业 collection 联合检索
      * 只要 KB 有任何检索数据，就绝不静默返回空
    """
    if not KB:
        return []
    coll_key = "宏观" if industry == "default" else industry
    retr = KB.get("retrieval", {}) or {}
    qmap = retr.get(coll_key, {})
    if not isinstance(qmap, dict) or not qmap:
        # 兜底：联合全部行业 collection 做一次全局检索，避免 key 不匹配导致空结果
        merged = {}
        for cq in retr.values():
            if isinstance(cq, dict):
                merged.update(cq)
        qmap = merged
    # 选取与用户问题字符重叠最多的代表性查询
    best, best_score = None, 0
    if user_query:
        for q, hits in qmap.items():
            s = sum(1 for ch in set(user_query) if ch in q)
            if s > best_score:
                best_score, best = s, hits
    if best and best_score > 0:
        return best
    # 兜底：聚合该（或全局）全部命中、按相似度去重取 Top-4
    seen, pool = set(), []
    for hits in qmap.values():
        for h in hits:
            if not isinstance(h, dict):
                continue
            key = (h.get("source"), h.get("page"), h.get("title"))
            if key not in seen:
                seen.add(key)
                pool.append(h)
    pool.sort(key=lambda x: -float(x.get("score", 0) or 0))
    result = pool[:4]
    if not result:
        import sys
        print(f"[FinSynagent] get_rag_hits EMPTY: coll_key={coll_key!r}, qmap_size={len(qmap)}, "
              f"KB_top_keys={list(KB.keys())[:10] if isinstance(KB, dict) else 'KB?'}, "
              f"retrieval_keys={list(retr.keys()) if isinstance(retr, dict) else 'KB?'}, "
              f"path={KB_DATA_PATH}", file=sys.stderr)
    return result
