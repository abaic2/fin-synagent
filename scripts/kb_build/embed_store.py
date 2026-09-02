# -*- coding: utf-8 -*-
"""
Step 3: 中文向量化 + Chroma 入库
加载 BAAI/bge-small-zh-v1.5（中文 embedding，维度 512），批量生成向量，
按行业建 4 个持久化 collection：macro / baijiu / dividend / precious。
（对应项目"按行业分账号管理知识库"的设计。下游若要严格对接星火，
把 SentenceTransformer 换成星火 Embedding API 即可。）

用法：
    export KB_ROOT=/path/to/your/project
    python embed_store.py
"""
import os, json
import chromadb
from sentence_transformers import SentenceTransformer

KB_ROOT = os.environ.get("KB_ROOT", os.getcwd())
CHUNKS_DIR = os.path.join(KB_ROOT, "knowledge_base", "chunks")
CHROMA_DIR = os.path.join(KB_ROOT, "knowledge_base", "chroma")
MODEL_NAME = "BAAI/bge-small-zh-v1.5"
BATCH = 64

# 行业中文 -> collection 英文名
COLL_MAP = {
    "宏观": "macro",
    "白酒": "baijiu",
    "红利": "dividend",
    "贵金属": "precious",
}

def main():
    print(f"加载 embedding 模型: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_sentence_embedding_dimension()
    print(f"  向量维度 = {dim}")

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    total = 0
    for ind, coll_name in COLL_MAP.items():
        fpath = os.path.join(CHUNKS_DIR, ind + ".jsonl")
        if not os.path.exists(fpath):
            print(f"[SKIP] {ind}: 无 chunks 文件")
            continue
        rows = [json.loads(l) for l in open(fpath, encoding="utf-8")]
        texts = [r["text"] for r in rows]

        # 批量编码（L2 归一化：余弦相似度 = 点积）
        embeddings = model.encode(
            texts, batch_size=BATCH, show_progress_bar=False,
            normalize_embeddings=True, convert_to_numpy=True,
        )

        # 重建 collection（覆盖旧数据）
        try:
            client.delete_collection(coll_name)
        except Exception:
            pass
        coll = client.create_collection(name=coll_name, metadata={"industry": ind, "hnsw:space": "cosine"})

        ids, docs, metas = [], [], []
        for r, emb in zip(rows, embeddings):
            ids.append(r["chunk_id"])
            docs.append(r["text"])
            metas.append({
                "industry": r["industry"],
                "source": r["source"],
                "title": r["title"],
                "page_start": int(r["page_start"]),
                "page_end": int(r["page_end"]),
            })
        # 分批 add
        for i in range(0, len(ids), BATCH):
            coll.add(
                ids=ids[i:i+BATCH],
                embeddings=embeddings[i:i+BATCH].tolist(),
                documents=docs[i:i+BATCH],
                metadatas=metas[i:i+BATCH],
            )
        total += len(ids)
        print(f"[OK] {ind} -> collection '{coll_name}': {len(ids)} 条, 维度 {dim}")

    print(f"\n入库完成，共 {total} 条。存储路径: {CHROMA_DIR}")

if __name__ == "__main__":
    main()
