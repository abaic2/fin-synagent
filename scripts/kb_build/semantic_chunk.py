# -*- coding: utf-8 -*-
"""
Step 2: 语义切分 (Semantic Chunking)
读取 _blocks.json（带标题层级与页码），按"同主题一个 chunk"原则切分：
  - 一级/二级标题作为切分锚点
  - 单 chunk 字数上限 ~520（适配 bge-small-zh 512 token），下限 ~120
  - 标题过少的文件回退为按页切分
  - 中文占比 < 45% 的长块丢弃（过滤双语年报英文页眉页脚噪声）
输出 <KB_ROOT>/knowledge_base/chunks/<行业>.jsonl，每行一个 chunk（含 metadata）。

用法：
    export KB_ROOT=/path/to/your/project
    python semantic_chunk.py
"""
import os, re, json

KB_ROOT = os.environ.get("KB_ROOT", os.getcwd())
BLOCKS_JSON = os.path.join(KB_ROOT, "knowledge_base", "markdown", "_blocks.json")
OUT_DIR = os.path.join(KB_ROOT, "knowledge_base", "chunks")
MAX_CHARS = 520
MIN_CHARS = 120
INDUSTRIES = ["宏观", "白酒", "红利", "贵金属"]

SENT_SPLIT = re.compile(r'(?<=[。！？；：])')

def split_sentences(text):
    parts = SENT_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]

def chinese_ratio(text):
    """中文字符占比，用于过滤双语年报的英文页眉页脚噪声"""
    cn = len(re.findall(r'[\u4e00-\u9fff]', text))
    total = len(re.sub(r'\s', '', text))
    return (cn / total) if total else 0.0

MIN_CN_RATIO = 0.45  # 中文占比低于此值且较长的块直接丢弃

def chunk_by_headings(blocks, source, industry):
    chunks = []
    cur = None  # {title_chain, level, sents, pages:set}
    def flush():
        nonlocal cur
        if cur is None:
            return
        text = cur["title_chain"] + "\n" + "".join(cur["sents"])
        text = re.sub(r'\s+', " ", text).strip()
        if len(text) >= MIN_CHARS and chinese_ratio(text) >= MIN_CN_RATIO:
            chunks.append({
                "industry": industry, "source": source,
                "title": cur["title"],
                "page_start": min(cur["pages"]), "page_end": max(cur["pages"]),
                "text": text,
            })
        cur = None
    title_chain_stack = [""]
    for b in blocks:
        if b["is_heading"]:
            lvl = b["level"]
            # 维持标题栈
            while len(title_chain_stack) > lvl:
                title_chain_stack.pop()
            title_chain_stack = title_chain_stack[:lvl-1] if lvl > 1 else []
            title_chain_stack.append(b["text"])
            chain = " > ".join([t for t in title_chain_stack if t])
            # 一级标题或当前已较大 -> 切分
            if cur is not None and (lvl == 1 or len("".join(cur["sents"])) > MAX_CHARS):
                flush()
            if cur is None:
                cur = {"title_chain": "【" + chain + "】", "title": b["text"], "level": lvl,
                       "sents": [], "pages": set()}
            else:
                # 并入当前（更新标题链，正文继续）
                cur["title_chain"] = "【" + chain + "】"
                cur["title"] = b["text"]
        else:
            sents = split_sentences(b["text"])
            for s in sents:
                if cur is None:
                    cur = {"title_chain": "", "title": "(正文)", "level": 0, "sents": [], "pages": set()}
                cur["sents"].append(s)
                cur["pages"].add(b["page"])
                if len("".join(cur["sents"])) >= MAX_CHARS:
                    flush()
    flush()
    return chunks

def chunk_by_page(blocks, source, industry):
    chunks = []
    page_text = {}
    for b in blocks:
        page_text.setdefault(b["page"], []).append(b["text"])
    for pg, sents in sorted(page_text.items()):
        text = re.sub(r'\s+', " ", " ".join(sents)).strip()
        if len(text) < MIN_CHARS or chinese_ratio(text) < MIN_CN_RATIO:
            continue
        chunks.append({
            "industry": industry, "source": source, "title": f"第{pg}页",
            "page_start": pg, "page_end": pg, "text": text,
        })
    return chunks

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    data = json.load(open(BLOCKS_JSON, encoding="utf-8"))
    total = 0
    for ind in INDUSTRIES:
        out_path = os.path.join(OUT_DIR, ind + ".jsonl")
        n = 0
        with open(out_path, "w", encoding="utf-8") as fout:
            for source, meta in data.items():
                if meta["industry"] != ind:
                    continue
                blocks = meta["blocks"]
                n_head = sum(1 for b in blocks if b["is_heading"])
                if n_head >= 3:
                    chunks = chunk_by_headings(blocks, source, ind)
                else:
                    chunks = chunk_by_page(blocks, source, ind)
                for i, c in enumerate(chunks):
                    c["chunk_id"] = f"{ind}_{source[:-4]}_{i:03d}"
                    fout.write(json.dumps(c, ensure_ascii=False) + "\n")
                    n += 1
        total += n
        print(f"[OK] {ind}: {n} 个 chunk -> {out_path}")
    print(f"\n总计 {total} 个语义 chunk")

if __name__ == "__main__":
    main()
