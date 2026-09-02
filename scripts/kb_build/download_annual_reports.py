# -*- coding: utf-8 -*-
"""从巨潮资讯批量下载三大行业龙头公司最新年度报告（RAG 素材）。
用法：
    export KB_ROOT=/path/to/your/project
    python download_annual_reports.py
"""
import os, json, time, urllib.parse, urllib.request

KB_ROOT = os.environ.get("KB_ROOT", os.getcwd())
BASE = os.path.join(KB_ROOT, "corpus", "rag")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
           "Content-Type": "application/x-www-form-urlencoded"}

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

def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def get_org_id(code, name):
    d = post("http://www.cninfo.com.cn/new/information/topSearch/query",
             {"keyWord": name, "maxSecNum": 5})
    for item in d:
        if item["code"] == code:
            return item["orgId"]
    return None

def get_latest_annual(code, org_id, column):
    d = post("http://www.cninfo.com.cn/new/hisAnnouncement/query", {
        "pageNum": 1, "pageSize": 30, "column": column, "tabName": "fulltext",
        "stock": f"{code},{org_id}", "category": "category_ndbg_szsh;",
        "seDate": "2024-01-01~2026-08-01"})
    anns = d.get("announcements") or []
    for a in anns:
        t = a["announcementTitle"]
        if "年度报告" in t and "摘要" not in t and "英文" not in t and "取消" not in t and "更正" not in t:
            return t, a["adjunctUrl"]
    return None, None

def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())

ok, fail = [], []
for ind, code, name, col in COMPANIES:
    try:
        org = get_org_id(code, name)
        title, adjunct = get_latest_annual(code, org, col)
        if not adjunct:
            fail.append((name, "no report found"))
            continue
        fname = f"{BASE}/{ind}/{name}_{title.replace('：','').replace(' ','')}.pdf"
        download("http://static.cninfo.com.cn/" + adjunct, fname)
        ok.append(fname)
        print("OK", fname)
        time.sleep(1)
    except Exception as e:
        fail.append((name, str(e)))
        print("FAIL", name, e)

print(f"\ndone: {len(ok)} ok, {len(fail)} fail")
for n, e in fail:
    print("fail:", n, e)
