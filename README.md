# 🚩 Fin Synagent · 基于多智能体协同的智能投顾

基于大语言模型的多智能体人机协同投顾推理模式 —— Streamlit 演示 Demo。

## 功能

- 🏠 **Home**：产品介绍、设计理念（深思熟虑 / 实事求是 / 小心求证）、操作流程、迭代回顾
- 💬 **Consult 智能咨询**：Leader 任务拆解 → Expert 专家回答 → Critic 批评监督 → Search & Verify 联网求证 → Summary 总结，全程透明可观测、可追问
- 📊 **Screen 智能荐股**：筛选树荐股思维（宏观 → 行业 → 个股），覆盖白酒 / 红利 / 贵金属三大行业，分析师视角推荐理由 + 可视化走势
- 🔥 **星火大模型模拟**：模拟讯飞星火 Spark4.0 Ultra / Max / Pro / Lite 的调用链路，参数可调（temperature / top_k / max_tokens），流式生成 + 模拟 API 报文
- 🧪 **测试与评估**：AI as Judge（均分 28.41，p=0.017 显著优于 SOTA）、AI as Customers、人工评估、消融实验
- 🧠 **技术设计**：System-2 工作流、筛选树、微调（SparkPro + FinCUGE）与知识库构建

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署到 Streamlit Community Cloud

1. 将本目录推送到 GitHub 公开仓库（`app.py` 与 `requirements.txt` 位于仓库根目录或子目录均可）
2. 访问 https://share.streamlit.io ，使用 GitHub 账号登录
3. 点击 **Create app** → 选择仓库、分支与 `app.py` 路径 → **Deploy**

> ⚠️ 本 Demo 数据为模拟数据，不构成投资建议。
