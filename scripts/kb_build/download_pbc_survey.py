# -*- coding: utf-8 -*-
"""下载央行银行家/企业家/储户问卷调查报告 PDF（宏观景气度素材）。
用法：
    export KB_ROOT=/path/to/your/project
    python download_pbc_survey.py
"""
import os, re, urllib.request

KB_ROOT = os.environ.get("KB_ROOT", os.getcwd())
OUT = os.path.join(KB_ROOT, "corpus", "rag", "宏观")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
BASE = "https://www.pbc.gov.cn"

PAGES = {
    "2025Q4_银行家问卷调查报告": "https://www.pbc.gov.cn/diaochatongjisi/116219/116227/2026012320124966002/index.html",
    "2025Q4_企业家问卷调查报告": "https://www.pbc.gov.cn/diaochatongjisi/116219/116227/2026012320114154002/index.html",
    "2025Q4_城镇储户问卷调查报告": "https://www.pbc.gov.cn/diaochatongjisi/116219/116227/2026012320103962314/index.html",
    "2025Q3_银行家问卷调查报告": "https://www.pbc.gov.cn/diaochatongjisi/116219/116227/5878574/index.html",
    "2025Q3_企业家问卷调查报告": "https://www.pbc.gov.cn/diaochatongjisi/116219/116227/5878579/index.html",
    "2025Q3_城镇储户问卷调查报告": "https://www.pbc.gov.cn/diaochatongjisi/116219/116227/5878563/index.html",
}

def fetch_pdf(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    for m in re.finditer(r'([a-zA-Z0-9_/.-]{20,}\.pdf)', html):
        p = m.group(1)
        full = p if p.startswith("http") else BASE + p
        return full
    return None

ok = []
for name, url in PAGES.items():
    try:
        pdf = fetch_pdf(url)
        if not pdf:
            print("NO PDF", name); continue
        path = f"{OUT}/{name}.pdf"
        req = urllib.request.Request(pdf, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
            f.write(r.read())
        ok.append(path); print("OK", path)
    except Exception as e:
        print("FAIL", name, e)

print(f"\n[PBC问卷] done: {len(ok)} ok")
