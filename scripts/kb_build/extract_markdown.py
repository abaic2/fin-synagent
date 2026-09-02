# -*- coding: utf-8 -*-
"""
Step 1: PDF -> Markdown (structured)
遍历 <KB_ROOT>/corpus/rag 下四个行业目录，用 PyMuPDF 提取文本，
依据字体大小 + 章节编号模式识别标题层级，输出结构化的 Markdown 到
<KB_ROOT>/knowledge_base/markdown/。
同时输出一份中间 json（带页码/标题层级），供语义切分使用。

用法：
    export KB_ROOT=/path/to/your/project   # 可选，默认当前目录
    python extract_markdown.py
"""
import os, re, json
import fitz  # PyMuPDF

KB_ROOT = os.environ.get("KB_ROOT", os.getcwd())
SRC = os.path.join(KB_ROOT, "corpus", "rag")
OUT_MD = os.path.join(KB_ROOT, "knowledge_base", "markdown")
OUT_JSON = os.path.join(KB_ROOT, "knowledge_base", "markdown", "_blocks.json")
INDUSTRIES = ["宏观", "白酒", "红利", "贵金属"]

# 章节/小节标题模式（年报与政府报告常见）
SEC_PATTERNS = [
    re.compile(r'^第[一二三四五六七八九十百零\d]+[章节编条部]'),          # 第一节 / 第1章
    re.compile(r'^[一二三四五六七八九十百零]+[、.．]'),                  # 一、 / 二．
    re.compile(r'^（?[一二三四五六七八九十]+）'),                       # （一） / 一）
    re.compile(r'^\d+[\.、]'),                                          # 1. / 2、
    re.compile(r'^[0-9０-９]+[\.、]'),                                  # 全角数字
]
SUB_PAT = re.compile(r'[\u4e00-\u9fff]{2,30}(?:报告|分析|情况|说明|摘要|预案|方案|公告|数据|表|图)\s*$')

def is_heading_line(text, size, body_med):
    t = text.strip()
    if not t or len(t) > 60:
        return False
    # 必须含中文，排除纯数字/表格数据行
    if not re.search(r'[\u4e00-\u9fff]', t):
        return False
    # 模式命中（章节/编号）
    for p in SEC_PATTERNS:
        if p.match(t):
            return True
    # 字体明显大于正文 且 较短（收紧阈值，避免表格短行误判）
    if size and body_med and size >= body_med * 1.22 and len(t) <= 20:
        return True
    return False

def heading_level(text, size, h1_med, h2_med):
    t = text.strip()
    if re.match(r'^第[一二三四五六七八九十百零\d]+[章节编条部]', t) or re.match(r'^[一二三四五六七八九十百零]+[、.．]', t):
        return 1
    if size and h1_med and size >= h1_med * 1.05:
        return 1
    return 2

def extract_pdf(path):
    doc = fitz.open(path)
    # 第一遍：确定正文字号中位数
    sizes = []
    for page in doc:
        for blk in page.get_text("dict")["blocks"]:
            if blk.get("type") != 0:
                continue
            for line in blk["lines"]:
                for sp in line["spans"]:
                    if sp["text"].strip():
                        sizes.append(sp["size"])
    sizes.sort()
    body_med = sizes[len(sizes)//2] if sizes else 10.0
    h1_med = sizes[int(len(sizes)*0.92)] if sizes else body_med*1.3
    h2_med = sizes[int(len(sizes)*0.82)] if sizes else body_med*1.15

    blocks = []  # {page, level, text}
    for pno, page in enumerate(doc, start=1):
        for blk in page.get_text("dict")["blocks"]:
            if blk.get("type") != 0:
                continue
            # 合并同一 block 内文本行
            cur_size = None
            cur_lines = []
            for line in blk["lines"]:
                line_text = "".join(sp["text"] for sp in line["spans"]).strip()
                max_size = max((sp["size"] for sp in line["spans"]), default=body_med)
                if not line_text:
                    continue
                if cur_lines and (is_heading_line(line_text, max_size, body_med) != is_heading_line(cur_lines[-1], cur_size, body_med) or abs(max_size-cur_size) > 1.5):
                    # flush
                    flush(blocks, cur_lines, cur_size, body_med, h1_med, h2_med, pno)
                    cur_lines = []
                cur_lines.append(line_text)
                cur_size = max_size
            if cur_lines:
                flush(blocks, cur_lines, cur_size, body_med, h1_med, h2_med, pno)
    doc.close()
    return blocks

def flush(blocks, lines, size, body_med, h1_med, h2_med, pno):
    text = " ".join(lines).strip()
    text = re.sub(r'\s+', " ", text)
    if not text:
        return
    if is_heading_line(text, size, body_med):
        level = heading_level(text, size, h1_med, h2_med)
        blocks.append({"page": pno, "level": level, "text": text, "is_heading": True})
    else:
        blocks.append({"page": pno, "level": 0, "text": text, "is_heading": False})

def main():
    os.makedirs(OUT_MD, exist_ok=True)
    all_blocks = {}
    summary = []
    for ind in INDUSTRIES:
        src_dir = os.path.join(SRC, ind)
        if not os.path.isdir(src_dir):
            continue
        out_dir = os.path.join(OUT_MD, ind)
        os.makedirs(out_dir, exist_ok=True)
        for fn in sorted(os.listdir(src_dir)):
            if not fn.lower().endswith(".pdf"):
                continue
            fpath = os.path.join(src_dir, fn)
            try:
                blocks = extract_pdf(fpath)
            except Exception as e:
                print(f"[WARN] 提取失败 {fn}: {e}")
                continue
            # 写 markdown
            md_path = os.path.join(out_dir, fn[:-4] + ".md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(f"# {fn[:-4]}\n\n")
                f.write(f"> 来源行业：{ind}  |  文件：{fn}\n\n---\n\n")
                last_level = 0
                for b in blocks:
                    if b["is_heading"]:
                        hashes = "#" * (b["level"]+1)
                        f.write(f"\n{hashes} {b['text']}\n\n")
                    else:
                        f.write(b["text"] + "\n\n")
            all_blocks[fn] = {"industry": ind, "blocks": blocks}
            n_head = sum(1 for b in blocks if b["is_heading"])
            summary.append((ind, fn, len(blocks), n_head, os.path.getsize(fpath)//1024))
            print(f"[OK] {ind}/{fn}: {len(blocks)} 文本块, {n_head} 标题, {os.path.getsize(fpath)//1024}KB")
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_blocks, f, ensure_ascii=False, indent=1)
    print("\n=== 汇总 ===")
    for s in summary:
        print(f"  {s[0]:>4} | {s[1][:40]:<40} | blocks={s[2]:>4} heads={s[3]:>3} size={s[4]}KB")
    print(f"中间数据已写入: {OUT_JSON}")

if __name__ == "__main__":
    main()
