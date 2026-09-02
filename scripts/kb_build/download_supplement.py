# -*- coding: utf-8 -*-
"""补充 RAG 语料：巨潮季报 / ESG / 分红公告（9 家公司）。
用法：
    export KB_ROOT=/path/to/your/project
    python download_supplement.py
"""
import os, json, time, urllib.parse, urllib.request

KB_ROOT = os.environ.get("KB_ROOT", os.getcwd())
BASE = os.path.join(KB_ROOT, "corpus", "rag")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
HEADERS = {"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"}

COMPANIES = [
    ("白酒", "600519", "贵州茅台", "sse"),
    ("白酒", "000858", "五粮液", "szse"),
    ("白酒", "000568", "泸州老窖", "szse"),
    ("红利", "601088", "中国神华", "sse"),
    ("红利", "600900", "长江电力", "sse"),
    ("红利", "601398", "工商银行", "sse"),
    ("贵金属", "601899", "紫金矿业", "sse"),
    ("贵金属", "600547", "山东黄金", "sse"),
    ("贵金属", "600489", "中金黄金", "sse"),
]

KEYWORDS = {
    "季报": ["第一季度报告", "第三季度报告"],
    "ESG": ["社会责任报告", "ESG报告", "可持续发展报告"],
    "分红": ["利润分配", "分红派息实施", "权益分派实施"],
}

ok, fail = [], []

def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def get_org_id(code, name):
    d = post("http://www.cninfo.com.cn/new/information/topSearch/query",
             {"keyWord": name, "maxSecNum": 5})
    for item in d:
        if item.get("code") == code:
            return item["orgId"]
    return None

def query_anns(code, org_id, column):
    d = post("http://www.cninfo.com.cn/new/hisAnnouncement/query", {
        "pageNum": 1, "pageSize": 60, "column": column, "tabName": "fulltext",
        "stock": f"{code},{org_id}", "seDate": "2025-01-01~2026-08-01"})
    return d.get("announcements") or []

def clean(title):
    return title.replace("：", "").replace(" ", "").replace("/", "_").replace("\\", "_")

def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
        f.write(r.read())

# ---------- 巨潮：季报 / ESG / 分红 ----------
for ind, code, name, col in COMPANIES:
    try:
        org = get_org_id(code, name)
        anns = query_anns(code, org, col)
        for cat, kws in KEYWORDS.items():
            for kw in kws:
                hit = None
                for a in anns:
                    t = a["announcementTitle"]
                    if kw in t and not any(x in t for x in ["摘要", "英文", "更正", "取消", "调整"]):
                        hit = (t, a["adjunctUrl"]); break
                if hit:
                    title, adjunct = hit
                    fname = f"{BASE}/{ind}/{name}_{clean(title)}.pdf"
                    if os.path.exists(fname):
                        continue
                    try:
                        download("http://static.cninfo.com.cn/" + adjunct, fname)
                        ok.append(fname); print("OK", fname)
                    except Exception as e:
                        fail.append((name, title, str(e))); print("FAIL", name, title, e)
                    time.sleep(0.6)
    except Exception as e:
        fail.append((name, "query", str(e))); print("FAIL", name, e)
    time.sleep(0.5)

print(f"\n[巨潮] done: {len(ok)} ok, {len(fail)} fail")
for x in fail:
    print("  fail:", x)
