# -*- coding: utf-8 -*-
"""
Step 4: 检索验证
用各行业的真实查询做 Top-K 召回，验证知识库质量。
查询时不加 bge 指令前缀（演示检索效果）；生产环境查询建议加
"为这个句子生成表示以用于检索相关文章：" 前缀。

用法：
    export KB_ROOT=/path/to/your/project
    python verify_retrieval.py
"""
import os
import chromadb
from sentence_transformers import SentenceTransformer

KB_ROOT = os.environ.get("KB_ROOT", os.getcwd())
CHROMA_DIR = os.path.join(KB_ROOT, "knowledge_base", "chroma")
MODEL_NAME = "BAAI/bge-small-zh-v1.5"

COLL_MAP = {"宏观": "macro", "白酒": "baijiu", "红利": "dividend", "贵金属": "precious"}

QUERIES = {
    "白酒": ["白酒行业2025年库存与批价情况", "贵州茅台的分红方案与股息率", "五粮液营收增速与经营情况"],
    "红利": ["高股息率央国企的红利策略", "中国神华分红率与现金流", "长江电力股息政策"],
    "贵金属": ["央行购金对金价的影响", "紫金矿业矿产金产量与资源储量", "山东黄金中期利润分配方案"],
    "宏观": ["2026年一季度货币政策取向", "社会融资规模与M2增速", "银行家问卷调查景气指数"],
}

def main():
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    for ind, coll_name in COLL_MAP.items():
        try:
            coll = client.get_collection(coll_name)
        except Exception:
            print(f"[SKIP] {ind}: collection 不存在")
            continue
        print(f"\n{'='*70}\n行业：{ind}  (collection={coll_name}, 共 {coll.count()} 条)\n{'='*70}")
        for q in QUERIES[ind]:
            qe = model.encode([q], normalize_embeddings=True, convert_to_numpy=True).tolist()[0]
            res = coll.query(query_embeddings=[qe], n_results=3, include=["documents", "metadatas", "distances"])
            print(f"\n🔍 查询：{q}")
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
                sim = 1 - dist
                snippet = doc[:90].replace("\n", " ")
                print(f"   [{sim:.3f}] {meta['source'][:24]} p{meta['page_start']} | {meta['title'][:24]}")
                print(f"          {snippet}...")

if __name__ == "__main__":
    main()
