# KB Build Scripts（知识库建库脚本集）

把「PDF 语料 → 结构化 Markdown → 语义切分 → 中文向量化 → Chroma 入库 → 检索验证」全流程脚本化、可复用。
所有脚本通过环境变量 `KB_ROOT` 定位项目根目录（默认当前目录），目录约定：

```
<KB_ROOT>/
├── corpus/rag/<行业>/        # 输入：各行业 PDF（宏观/白酒/红利/贵金属）
└── knowledge_base/
    ├── markdown/             # Step1 输出：结构化 .md + _blocks.json（带页码/层级）
    ├── chunks/               # Step2 输出：<行业>.jsonl（语义 chunk）
    └── chroma/               # Step3 输出：4 个持久化 collection
```

## 运行顺序

```bash
export KB_ROOT=/path/to/your/project
pip install pymupdf sentence-transformers chromadb

# 0) 下载语料（可选，已有 corpus/rag 可跳过）
python download_annual_reports.py     # 9 家龙头年报
python download_supplement.py         # 季报/ESG/分红公告
python download_pbc_survey.py         # 央行 3 类问卷调查报告

# 1) PDF -> Markdown（结构化 + 标题层级 + 页码）
python extract_markdown.py
# 2) 语义切分（同主题一个 chunk，中文占比过滤噪声）
python semantic_chunk.py
# 3) bge 向量化 + 按行业 Chroma 入库
python embed_store.py
# 4) 真实查询 Top-K 召回验证
python verify_retrieval.py
```

## 脚本清单

| 脚本 | 阶段 | 关键依赖 | 作用 |
|------|------|----------|------|
| `download_annual_reports.py` | 0 | urllib | 巨潮 API 下载 9 家龙头年报 |
| `download_supplement.py` | 0 | urllib, json | 巨潮季报/ESG/分红公告补料 |
| `download_pbc_survey.py` | 0 | urllib, re | 央行问卷调查报告 PDF |
| `extract_markdown.py` | 1 | PyMuPDF | PDF→结构化 Markdown + 中间 JSON |
| `semantic_chunk.py` | 2 | re | 语义切分 + 中文占比过滤 |
| `embed_store.py` | 3 | sentence-transformers, chromadb | bge 向量化 + 分行业入库 |
| `verify_retrieval.py` | 4 | sentence-transformers, chromadb | 各行业真实查询检索验证 |

> 下游若要严格对接星火，把 `embed_store.py` 中的 `SentenceTransformer` 替换为星火 Embedding API 即可；bge 仅作为无星火 API 时的本地等价替代。
