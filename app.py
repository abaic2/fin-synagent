# -*- coding: utf-8 -*-
"""
Fin Synagent - 基于多智能体协同的智能投顾 Demo (v2)
UI 全面升级 + 星火大模型模拟引擎
还原自《基于多智能体协同的智能投顾设计》/《AIGC》/《创作思路说明》
"""
import json
import time
import random
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="Fin Synagent · 多智能体协同智能投顾",
    page_icon="🚩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================== 设计系统
NAVY = "#0A1F44"
NAVY2 = "#16305E"
ROYAL = "#2B4C9B"
BLUE = "#4A6FD4"
GOLD = "#C9A227"
GOLD2 = "#E8C766"
GOLD_L = "#F6ECD0"
RED = "#E54545"      # 涨（A股规范）
GREEN = "#1E9E6A"    # 跌
INK = "#22304F"
MUTE = "#6B7699"
BG = "#F4F6FB"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Noto+Serif+SC:wght@600;900&display=swap');

html, body, [class*="css"] {{ font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif; }}
.stApp {{ background: {BG}; }}
.block-container {{ padding-top: 1.6rem; max-width: 1180px; }}
h1,h2,h3 {{ font-family: "Noto Sans SC", sans-serif; }}

/* ---------- HERO ---------- */
.hero {{
  position: relative; overflow: hidden;
  background: linear-gradient(125deg, #081733 0%, {NAVY} 32%, {NAVY2} 62%, #2b4c9b 100%);
  border-radius: 24px; padding: 58px 52px 50px 52px; color: #fff;
  box-shadow: 0 20px 50px rgba(10,31,68,.35); margin-bottom: 30px;
}}
.hero::before {{
  content:""; position:absolute; width:520px; height:520px; right:-140px; top:-190px;
  background: radial-gradient(circle, rgba(201,162,39,.42) 0%, rgba(201,162,39,0) 65%);
  animation: float1 9s ease-in-out infinite;
}}
.hero::after {{
  content:""; position:absolute; width:380px; height:380px; left:-120px; bottom:-190px;
  background: radial-gradient(circle, rgba(74,111,212,.5) 0%, rgba(74,111,212,0) 65%);
  animation: float2 11s ease-in-out infinite;
}}
@keyframes float1 {{ 0%,100%{{transform:translate(0,0)}} 50%{{transform:translate(-26px,20px)}} }}
@keyframes float2 {{ 0%,100%{{transform:translate(0,0)}} 50%{{transform:translate(24px,-16px)}} }}
.hero .kicker {{
  font-size:.82rem; letter-spacing:4px; color:{GOLD2}; font-weight:500;
  text-transform:uppercase; margin-bottom:14px; position:relative; z-index:1;
}}
.hero h1 {{
  font-family:"Noto Serif SC", serif; font-size:3.1rem; font-weight:900;
  margin:0 0 10px 0; letter-spacing:2px; position:relative; z-index:1;
  background: linear-gradient(90deg,#FFFFFF 30%, {GOLD2} 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}}
.hero .sub {{ font-size:1.08rem; color:#C6D3F0; max-width:760px; line-height:1.7; position:relative; z-index:1; margin-bottom:22px; }}
.hero .tag {{
  display:inline-block; position:relative; z-index:1;
  background: rgba(255,255,255,.08); backdrop-filter: blur(6px);
  color:{GOLD_L}; border:1px solid rgba(201,162,39,.5);
  padding:5px 16px; border-radius:999px; font-size:.82rem; margin:0 8px 6px 0;
}}
.hero-mini {{ padding:34px 40px 30px 40px; margin-bottom:24px; }}
.hero-mini h1 {{ font-size:2rem; }}

/* ---------- 卡片 ---------- */
.card {{
  background: rgba(255,255,255,.9); backdrop-filter: blur(8px);
  border-radius:18px; padding:24px 24px 20px 24px;
  border:1px solid #E4E9F4; box-shadow:0 6px 20px rgba(22,48,94,.06);
  height:100%; transition: all .25s ease;
}}
.card:hover {{ transform: translateY(-4px); box-shadow:0 14px 32px rgba(22,48,94,.13); border-color:#C9D5EF; }}
.card .icon {{
  width:46px; height:46px; border-radius:13px; display:flex; align-items:center; justify-content:center;
  font-size:1.45rem; margin-bottom:12px;
  background: linear-gradient(135deg, #EDF1FC, #E2E9FA); border:1px solid #D8E1F5;
}}
.card h4 {{ margin:0 0 8px 0; color:{NAVY}; font-size:1.05rem; font-weight:700; }}
.card p {{ color:{MUTE}; font-size:.9rem; line-height:1.7; margin:0; }}

/* ---------- 小节标题 ---------- */
.sec-title {{
  font-family:"Noto Serif SC", serif; font-size:1.5rem; font-weight:900; color:{NAVY};
  margin:40px 0 4px 0; display:flex; align-items:center; gap:12px;
}}
.sec-title::before {{
  content:""; width:7px; height:26px; border-radius:4px;
  background: linear-gradient(180deg, {GOLD}, {GOLD2});
  box-shadow:0 2px 8px rgba(201,162,39,.45);
}}
.sec-sub {{ color:{MUTE}; font-size:.9rem; margin:2px 0 20px 19px; }}

/* ---------- 步骤 / 时间线 ---------- */
.step {{
  background:#fff; border:1px solid #E4E9F4; border-radius:14px; padding:16px 18px; margin-bottom:12px;
  border-left:5px solid {ROYAL}; box-shadow:0 3px 12px rgba(22,48,94,.05);
}}
.step b {{ color:{NAVY}; }}
.tl {{ border-left:3px solid #D9E1F2; padding-left:22px; margin-left:8px; }}
.tl-item {{ margin-bottom:22px; position:relative; }}
.tl-item::before {{
  content:""; position:absolute; left:-29px; top:5px; width:14px; height:14px; border-radius:50%;
  background: radial-gradient(circle at 35% 35%, {GOLD2}, {GOLD});
  border:3px solid #fff; box-shadow:0 0 0 2.5px {GOLD}, 0 3px 8px rgba(201,162,39,.5);
}}
.tl-item b {{ color:{NAVY}; font-size:1rem; }}
.tl-item p {{ color:{MUTE}; font-size:.88rem; margin:3px 0 0 0; line-height:1.6; }}

/* ---------- 智能体 ---------- */
.agent {{
  border-radius:16px; padding:16px 12px; border:1px solid #E4E9F4; background:#fff;
  text-align:center; transition: all .25s ease; box-shadow:0 3px 10px rgba(22,48,94,.05);
}}
.agent:hover {{ transform: translateY(-3px); }}
.agent .em {{ font-size:1.9rem; }}
.agent .role {{ font-weight:700; font-size:.95rem; color:{NAVY}; margin-top:4px; }}
.agent .desc {{ color:{MUTE}; font-size:.8rem; line-height:1.5; margin-top:2px; }}
.a-leader {{ border-top:4px solid {NAVY2}; }}
.a-expert {{ border-top:4px solid {BLUE}; }}
.a-critic {{ border-top:4px solid {GOLD}; }}
.a-verify {{ border-top:4px solid {GREEN}; }}
.a-sum    {{ border-top:4px solid {RED}; }}

/* ---------- 股票卡 ---------- */
.stock-card {{
  background: linear-gradient(160deg, #FFFFFF 60%, #F4F7FE 100%);
  border-radius:18px; padding:20px 22px; border:1px solid #E4E9F4;
  box-shadow:0 6px 18px rgba(22,48,94,.07); margin-bottom:4px;
}}
.stock-name {{ font-size:1.15rem; font-weight:800; color:{NAVY}; }}
.stock-code {{ color:#98A2C0; font-size:.8rem; margin-left:6px; }}
.up {{ color:{RED}; font-weight:800; }}
.down {{ color:{GREEN}; font-weight:800; }}

/* ---------- KPI ---------- */
.kpi {{
  position:relative; overflow:hidden;
  background: linear-gradient(150deg, #FFFFFF 40%, #EEF2FC 100%);
  border:1px solid #E4E9F4; border-radius:18px; padding:22px 14px; text-align:center;
  box-shadow:0 5px 16px rgba(22,48,94,.06);
}}
.kpi::after {{ content:""; position:absolute; top:0; left:0; right:0; height:4px;
  background: linear-gradient(90deg, {GOLD}, {GOLD2}, {GOLD}); }}
.kpi .v {{ font-family:"Noto Serif SC",serif; font-size:1.9rem; font-weight:900; color:{NAVY}; }}
.kpi .k {{ font-size:.8rem; color:{MUTE}; margin-top:2px; }}

.pill {{
  display:inline-block; background:#EDF1FA; color:{NAVY2}; border-radius:8px;
  padding:4px 12px; font-size:.78rem; margin:2px 5px 2px 0; border:1px solid #DCE3F2; font-weight:500;
}}
.src {{
  background:#F2FAF6; border:1px solid #D5EBDF; border-radius:10px;
  padding:9px 13px; font-size:.82rem; color:#2C5A41; margin-bottom:7px;
}}

/* ---------- 星火模型卡 ---------- */
.spark-card {{
  border-radius:18px; padding:20px 22px; height:100%; color:#fff;
  box-shadow:0 10px 26px rgba(22,48,94,.18); transition: all .25s ease;
  border:1px solid rgba(255,255,255,.25);
}}
.spark-card:hover {{ transform: translateY(-4px) scale(1.01); }}
.spark-card h4 {{ color:#fff; margin:8px 0 6px 0; font-size:1.05rem; }}
.spark-card p {{ color:rgba(255,255,255,.85); font-size:.82rem; line-height:1.6; margin:0; }}
.spark-card .badge {{
  display:inline-block; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.4);
  font-size:.7rem; padding:2px 10px; border-radius:999px;
}}

/* ---------- 流式输出 ---------- */
.gen-box {{
  background:#fff; border:1px solid #E4E9F4; border-radius:16px; padding:20px 24px;
  box-shadow:0 4px 14px rgba(22,48,94,.06); line-height:1.85; font-size:.95rem; color:{INK};
}}
.cursor {{ display:inline-block; width:9px; height:18px; background:{GOLD}; vertical-align:-3px;
  animation: blink .8s steps(1) infinite; border-radius:2px; }}
@keyframes blink {{ 50% {{ opacity:0; }} }}

/* ---------- 侧边栏 ---------- */
section[data-testid="stSidebar"],
div[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #081733 0%, {NAVY} 55%, {NAVY2} 100%) !important;
  border-right: 1px solid rgba(201,162,39,.25);
}}
section[data-testid="stSidebar"] > div,
div[data-testid="stSidebar"] > div,
div[data-testid="stSidebarContent"],
div[data-testid="stSidebar"] [data-testid="stSidebarContent"],
div[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
  background: transparent !important;
}}
section[data-testid="stSidebar"] *, div[data-testid="stSidebar"] * {{ color:#FFFFFF !important; }}
section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small,
div[data-testid="stSidebar"] .stCaption, div[data-testid="stSidebar"] small {{ color:#AFC2E8 !important; }}
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color:#FFFFFF !important; }}
/* 白底输入控件保持深色字 */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] [data-baseweb="select"] *,
section[data-testid="stSidebar"] [data-baseweb="select"] input,
section[data-testid="stSidebar"] [data-baseweb="popover"] * {{ color:{INK} !important; }}
div[data-testid="stSidebar"] .stButton > button {{
  background: rgba(255,255,255,.08); border: 1px solid rgba(201,162,39,.45);
  color: #FFFFFF !important; border-radius: 11px; transition: all .2s ease; font-weight:500;
}}
div[data-testid="stSidebar"] .stButton > button:hover {{
  background: rgba(201,162,39,.16); border-color: rgba(201,162,39,.7); transform: translateX(2px);
}}
div[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background: linear-gradient(90deg, {GOLD}, {GOLD2}); color: {NAVY} !important;
  border: none; font-weight: 700;
}}
.sb-brand {{ text-align:center; padding:10px 0 4px 0; }}
.sb-brand .logo {{ font-family:"Noto Serif SC",serif; font-size:1.55rem; font-weight:900; color:#fff !important; letter-spacing:1px; }}
.sb-brand .logo span {{ color:{GOLD2} !important; }}
.sb-brand .slogan {{ font-size:.72rem; color:#C9D4F2 !important; letter-spacing:2.5px; margin-top:2px; }}

.footer {{
  text-align:center; color:#96A0BD; font-size:.8rem; margin-top:56px; padding-top:18px;
  border-top:1px solid #E0E6F2;
}}
</style>
""", unsafe_allow_html=True)

PLOTLY_BASE = dict(font=dict(family="Noto Sans SC", color=INK), paper_bgcolor="white", plot_bgcolor="white")

# ============================================================== 数据
STOCKS = {
    "白酒": [
        {"name": "贵州茅台", "code": "600519.SH", "price": 1688.00, "chg": +1.86, "pe": 27.4, "mv": "2.12万亿",
         "reason": "高端白酒绝对龙头，品牌壁垒深厚，出厂价与一批价坚挺，直销渠道占比持续提升带来吨价上行；现金流充沛，分红率稳定，弱周期属性在行业调整期具备防御价值。"},
        {"name": "五粮液", "code": "000858.SZ", "price": 141.25, "chg": +0.94, "pe": 17.8, "mv": "5483亿",
         "reason": "普五批价企稳回升，公司控量挺价策略执行坚决；1618、低度系列放量贡献增量；估值处于近五年低位，安全边际充足，弹性空间大。"},
        {"name": "泸州老窖", "code": "000568.SZ", "price": 156.40, "chg": -0.62, "pe": 15.2, "mv": "2302亿",
         "reason": "国窖1573稳居高端第三极，腰部产品特曲、窖龄酒复苏明确；费用管控精细化，净利率仍有上行空间；短期受行业去库存扰动，回调即配置机会。"},
    ],
    "红利": [
        {"name": "中国神华", "code": "601088.SH", "price": 41.72, "chg": +1.24, "pe": 12.6, "mv": "8288亿",
         "reason": "煤电运化一体化产业链，长协煤占比高平滑周期波动；连续多年分红率超 70%，股息率约 5.6%，是红利资产的核心压舱石。"},
        {"name": "长江电力", "code": "600900.SH", "price": 27.95, "chg": +0.58, "pe": 21.3, "mv": "6839亿",
         "reason": "全球最大水电上市公司，六库联调提升发电效率，来水偏丰叠加电价市场化改革；类债属性突出，分红承诺 70% 以上，确定性极强。"},
        {"name": "工商银行", "code": "601398.SH", "price": 6.18, "chg": -0.16, "pe": 6.1, "mv": "2.20万亿",
         "reason": "国有大行龙头，资产质量稳健，不良率持续下行；股息率超 5%，险资与被动资金持续增配，受益于中特估与市值管理政策。"},
    ],
    "贵金属": [
        {"name": "紫金矿业", "code": "601899.SH", "price": 18.64, "chg": +2.31, "pe": 16.9, "mv": "4926亿",
         "reason": "铜金双轮驱动，卡莫阿、巨龙铜矿放量进入收获期；美联储降息周期开启利好金价，公司矿产金产量三年复合增速超 20%，量价齐升。"},
        {"name": "山东黄金", "code": "600547.SH", "price": 29.87, "chg": +1.05, "pe": 38.2, "mv": "1336亿",
         "reason": "纯正黄金标的，金价上行期业绩弹性最大；西岭金矿探矿权注入预期强化资源储备；避险需求与央行购金构成中长期支撑。"},
        {"name": "中金黄金", "code": "600489.SH", "price": 14.52, "chg": -0.88, "pe": 22.7, "mv": "703亿",
         "reason": "央企背景，纱岭金矿投产在即带来产量跃升；集团资产注入预期明确；短期跟随板块回调，估值修复空间可观。"},
    ],
}

INDUSTRY_FEATURE = {
    "白酒": {"macro": ["社零餐饮消费回暖", "CPI 温和回升", "流动性合理充裕"],
             "industry": ["批价企稳回升", "渠道库存去化至良性", "头部集中度提升"],
             "view": "行业处于周期底部右侧，需求弱复苏、供给端主动出清，龙头阿尔法属性凸显。"},
    "红利": {"macro": ["十年期国债收益率低位", "市值管理新政催化", "险资配置需求旺盛"],
             "industry": ["股息率相对债券利差走阔", "央国企分红意愿提升", "现金流稳定"],
             "view": "无风险利率下行环境中，高股息资产配置价值持续凸显，攻守兼备。"},
    "贵金属": {"macro": ["美联储降息预期升温", "实际利率下行", "地缘风险抬升避险需求"],
             "industry": ["全球央行连续购金", "矿产供给刚性", "金价屡创新高"],
             "view": "美元信用体系松动叠加降息周期，黄金中长期牛市格局确立，铜金共振。"},
}

# Screen 候选池（含四维特征与 LLM 综合评分，源自《Fin Synagent (9)》Screen 流程）
CANDIDATES = {
    "白酒": [
        {"name": "贵州茅台", "code": "600519.SH", "pe": 27.4, "pb": 9.5, "roe": 32.1, "rev": 15.8,
         "trend": "上升趋势", "ma": "MA20 > MA60", "vol": "低波动", "macd": "金叉",
         "sent": (0.78, 0.08, 0.14), "score": 91.2},
        {"name": "五粮液", "code": "000858.SZ", "pe": 17.8, "pb": 4.1, "roe": 24.5, "rev": 11.2,
         "trend": "震荡向上", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.71, 0.11, 0.18), "score": 86.7},
        {"name": "泸州老窖", "code": "000568.SZ", "pe": 15.2, "pb": 4.4, "roe": 28.7, "rev": 13.5,
         "trend": "横盘整理", "ma": "MA20 ≈ MA60", "vol": "中波动", "macd": "粘合",
         "sent": (0.64, 0.15, 0.21), "score": 84.3},
        {"name": "山西汾酒", "code": "600809.SH", "pe": 19.6, "pb": 5.8, "roe": 26.3, "rev": 16.9,
         "trend": "横盘整理", "ma": "MA20 < MA60", "vol": "高波动", "macd": "死叉",
         "sent": (0.58, 0.19, 0.23), "score": 82.5},
        {"name": "洋河股份", "code": "002304.SZ", "pe": 13.9, "pb": 2.9, "roe": 20.4, "rev": 6.7,
         "trend": "弱势整理", "ma": "MA20 < MA60", "vol": "中波动", "macd": "死叉",
         "sent": (0.52, 0.22, 0.26), "score": 80.1},
    ],
    "红利": [
        {"name": "中国神华", "code": "601088.SH", "pe": 12.6, "pb": 1.9, "roe": 15.2, "rev": 3.1,
         "trend": "上升趋势", "ma": "MA20 > MA60", "vol": "低波动", "macd": "金叉",
         "sent": (0.74, 0.09, 0.17), "score": 90.5},
        {"name": "长江电力", "code": "600900.SH", "pe": 21.3, "pb": 3.1, "roe": 14.8, "rev": 8.4,
         "trend": "上升趋势", "ma": "MA20 > MA60", "vol": "低波动", "macd": "金叉",
         "sent": (0.72, 0.10, 0.18), "score": 88.9},
        {"name": "工商银行", "code": "601398.SH", "pe": 6.1, "pb": 0.7, "roe": 10.6, "rev": 1.2,
         "trend": "震荡向上", "ma": "MA20 > MA60", "vol": "低波动", "macd": "金叉",
         "sent": (0.66, 0.12, 0.22), "score": 85.4},
        {"name": "陕西煤业", "code": "601225.SH", "pe": 11.4, "pb": 2.3, "roe": 20.1, "rev": -2.3,
         "trend": "横盘整理", "ma": "MA20 ≈ MA60", "vol": "中波动", "macd": "粘合",
         "sent": (0.59, 0.17, 0.24), "score": 83.8},
        {"name": "宁沪高速", "code": "600377.SH", "pe": 12.8, "pb": 1.6, "roe": 12.4, "rev": 5.6,
         "trend": "横盘整理", "ma": "MA20 ≈ MA60", "vol": "低波动", "macd": "粘合",
         "sent": (0.55, 0.18, 0.27), "score": 81.2},
    ],
    "贵金属": [
        {"name": "紫金矿业", "code": "601899.SH", "pe": 16.9, "pb": 3.8, "roe": 22.6, "rev": 18.3,
         "trend": "上升趋势", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.81, 0.07, 0.12), "score": 91.8},
        {"name": "山东黄金", "code": "600547.SH", "pe": 38.2, "pb": 5.1, "roe": 13.4, "rev": 21.7,
         "trend": "上升趋势", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.75, 0.10, 0.15), "score": 87.3},
        {"name": "中金黄金", "code": "600489.SH", "pe": 22.7, "pb": 2.6, "roe": 11.2, "rev": 12.5,
         "trend": "震荡向上", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.68, 0.13, 0.19), "score": 84.9},
        {"name": "赤峰黄金", "code": "600988.SH", "pe": 25.4, "pb": 3.2, "roe": 12.8, "rev": 15.1,
         "trend": "横盘整理", "ma": "MA20 ≈ MA60", "vol": "高波动", "macd": "粘合",
         "sent": (0.61, 0.16, 0.23), "score": 82.6},
        {"name": "银泰黄金", "code": "000975.SZ", "pe": 20.8, "pb": 2.4, "roe": 11.6, "rev": 9.8,
         "trend": "弱势整理", "ma": "MA20 < MA60", "vol": "中波动", "macd": "死叉",
         "sent": (0.54, 0.20, 0.26), "score": 80.4},
    ],
}

# RAG 模拟检索片段（源自文档：券商研报 / 协会报告 / 财报）
RAG_CHUNKS = {
    "白酒": [
        ("券商白酒深度研报：库存周期与批价跟踪", 0.923, "渠道库存去化至 1.5-2 个月良性区间，飞天批价站稳 2200 元上方……"),
        ("中酒协行业报告：二季度终端动销调研", 0.887, "宴席与商务场景修复明显，次高端以下价位带动销环比改善……"),
        ("头部酒企财报：茅台 / 五粮液 2026Q2", 0.851, "直销占比提升带动吨价上行，分红率维持高位，现金流充沛……"),
    ],
    "红利": [
        ("券商红利策略专题：股息率与利率利差", 0.917, "中证红利股息率约 5.2%，与 10Y 国债利差处于历史高位……"),
        ("央国企分红政策汇编：市值管理指引", 0.879, "鼓励提高分红频次与比例，多家央企承诺分红率 70% 以上……"),
        ("公用事业 / 煤炭年报：现金流与分红覆盖", 0.842, "经营现金流对分红覆盖率 1.5 倍以上，长协机制平滑周期……"),
    ],
    "贵金属": [
        ("券商贵金属中期策略：金铜共振", 0.928, "美联储降息周期开启，实际利率下行，金价中枢上移……"),
        ("世界黄金协会：全球央行购金季报", 0.895, "全球央行连续 30 个月净购金，新兴市场央行增持显著……"),
        ("头部矿企财报：紫金 / 山金产量指引", 0.858, "矿产金产量三年复合增速超 20%，资源储备持续扩张……"),
    ],
    "default": [
        ("券商 A 股中期策略：哑铃配置", 0.876, "高股息防御 + 景气成长进攻，底部区域分批布局……"),
        ("货币政策执行报告（季度）", 0.842, "保持流动性合理充裕，引导实体融资成本下行……"),
        ("资本市场改革文件汇编", 0.815, "市值管理、分红回购新政持续落地，夯实市场底部……"),
    ],
}

CONSULT_SCRIPT = {
    "白酒": {
        "subtasks": ["行业景气度与终端动销分析", "竞争格局与头部酒企策略研判", "估值水平与投资风险评估"],
        "experts": ["白酒行业专家", "宏观消费分析师"],
        "expert_answer": "根据知识库 2026 年最新研报：\n\n**1. 景气度**：二季度以来白酒终端动销环比改善，宴席与商务场景修复明显，渠道反馈库存已去化至 1.5-2 个月的良性区间。高端酒批价率先企稳，飞天茅台一批价维持在 2200 元上方。\n\n**2. 竞争格局**：行业进入存量竞争阶段，市场份额加速向头部集中。CR5 收入占比已超 45%，区域酒企分化加剧，具备品牌力与渠道掌控力的龙头将持续收割份额。\n\n**3. 估值与风险**：板块当前 PE-TTM 约 18 倍，处于近十年 10% 分位以下，配置价值凸显。风险点在于需求复苏斜率不及预期与批价波动。",
        "critic": "回答整体扎实，但有两点需要补充：① 需区分高端、次高端与区域酒的不同逻辑，不能一概而论；② 应给出更明确的短期/中长期持有建议，并引用具体批价数据佐证。",
        "expert_revise": "已按评论家意见修正：高端酒（茅台、五粮液）确定性最强，适合中长期持有；次高端弹性大但需等待动销验证，建议短期波段操作。补充数据：普五批价已由 920 元回升至 960 元，国窖 1573 批价稳定在 880 元左右。",
        "verify": ["《白酒行业 2026 年中期策略：底部蓄势，龙头先行》· 中信证券研究部 · 2026-06",
                   "《酒类流通协会：二季度渠道库存调研报告》· 2026-07",
                   "新浪财经 · 飞天茅台批价日报 · 2026-07-27"],
        "summary": "综合来看，白酒行业正处于周期底部右侧：库存良性、批价企稳、估值处于历史低位。高端龙头具备确定的中长期配置价值，建议以茅台、五粮液为核心底仓，次高端择机波段参与；中长期持有为主，短期关注中秋备货催化。",
    },
    "红利": {
        "subtasks": ["红利产业链上下游结构拆解", "高股息资产的定价逻辑", "细分板块股息率与持续性比较"],
        "experts": ["红利策略专家", "资产配置分析师"],
        "expert_answer": "按产业上下游逻辑拆解红利行业投资逻辑：\n\n**上游（资源类）**：煤炭、油气、有色等资源品企业资本开支高峰已过，自由现金流充沛，长协机制平滑周期波动，是红利资产的「现金奶牛」，如中国神华、陕西煤业。\n\n**中游（公用事业与交运）**：水电、核电、高速公路具备特许经营属性，需求刚性、现金流可预测性强，长江电力、宁沪高速为代表，类债属性突出。\n\n**下游（金融与消费）**：国有大行不良率下行、分红比例稳定在 30% 以上；白电、纺服龙头分红率持续提升。\n\n定价核心在于：股息率与无风险利率的利差。当前 10Y 国债收益率约 1.7%，而中证红利指数股息率约 5.2%，利差处于历史高位，配置价值显著。",
        "critic": "逻辑框架清晰，但建议补充：① 红利资产的拥挤度与潜在回撤风险；② 不同细分板块分红可持续性的量化依据（分红率、经营现金流覆盖率）。",
        "expert_revise": "补充如下：拥挤度方面，红利指数换手率仍低于历史中位数，尚未过热；风险方面，若经济复苏超预期导致利率快速上行，红利资产将阶段性跑输。可持续性上，煤炭/水电板块经营现金流对分红的覆盖率均在 1.5 倍以上。",
        "verify": ["《红利策略深度：从哑铃一端到压舱石》· 华泰证券 · 2026-05",
                   "中证指数公司 · 中证红利指数股息率月报 · 2026-06",
                   "Wind 资讯 · 上市公司 2025 年度分红实施公告汇总"],
        "summary": "红利行业的投资逻辑可沿「上游资源现金流—中游特许经营—下游金融消费」的产业链条展开，核心驱动是股息率与无风险利率的高利差。建议以中国神华、长江电力等现金流确定性强的标的为底仓，长期持有获取股息与估值修复的双重收益，同时关注利率快速上行带来的阶段性波动风险。",
    },
    "贵金属": {
        "subtasks": ["全球宏观与货币政策环境研判", "黄金供需格局与价格驱动分析", "贵金属板块标的选择与风险提示"],
        "experts": ["贵金属行业专家", "宏观策略分析师"],
        "expert_answer": "基于知识库最新研报与国际市场数据：\n\n**1. 宏观环境**：美联储 6 月议息会议释放明确鸽派信号，市场预期年内降息两次；美国实际利率下行是金价最核心的驱动变量。叠加地缘政治风险反复，避险需求持续。\n\n**2. 供需格局**：全球央行已连续 30 个月净购金，中国、波兰、土耳其央行增持明显；矿产金供给刚性，回收金弹性有限。金价突破 2400 美元/盎司后站稳，沪金主力合约创出新高。\n\n**3. 投资结论**：贵金属板块在当前市场中具备明确的配置价值，黄金股相对金价存在杠杆弹性，建议关注资源储量扩张确定性强的龙头。风险在于降息节奏不及预期引发的阶段性回调。",
        "critic": "回答数据翔实，但需补充：① 白银等工业属性贵金属与黄金的差异；② 短期持有与长期持有的具体建议；③ 金价与黄金股估值的相对位置。",
        "expert_revise": "补充说明：白银兼具工业属性，光伏需求支撑其弹性大于黄金，但波动也更大；黄金股当前估值隐含金价约 2200 美元，低于现价，存在修复空间。建议：长期持有黄金龙头，短期回调即加仓窗口。",
        "verify": ["《贵金属行业 2026 年中期策略：金铜共振》· 国泰君安有色团队 · 2026-06",
                   "世界黄金协会 · 全球央行购金季度报告 · 2026Q2",
                   "COMEX 黄金期货与沪金主力合约行情数据 · 2026-07-27"],
        "summary": "贵金属行业当前值得投资：美联储降息周期、央行持续购金与避险需求构成三重驱动，黄金中长期牛市格局确立。建议以紫金矿业、山东黄金等资源扩张确定性强的龙头为主，长期持有为主、短期回调加仓；关注降息节奏变化带来的波动风险。",
    },
    "default": {
        "subtasks": ["宏观经济环境与政策面分析", "相关行业景气度与趋势研判", "投资策略与风险管理建议"],
        "experts": ["宏观策略分析师", "金融知识库专家"],
        "expert_answer": "基于金融行业知识库与联网检索信息：\n\n**1. 宏观层面**：当前国内货币政策保持合理充裕，财政发力稳增长，资本市场改革深化（市值管理、分红回购新政），为权益市场提供底部支撑。\n\n**2. 行业层面**：建议沿「高股息防御 + 景气成长进攻」的哑铃思路配置：一端是红利、公用事业等现金流资产；另一端是 AI、高端制造等政策支持方向。\n\n**3. 策略层面**：个人投资者应结合自身风险偏好与资金期限，避免追涨杀跌，采用定投或分批建仓方式平滑波动。",
        "critic": "回答框架完整，但个性化不足：建议结合用户的风险承受能力与投资期限给出更具体的配置比例建议。",
        "expert_revise": "已修正：稳健型投资者可按「60% 红利固收 + 30% 宽基指数 + 10% 行业主题」配置；积极型可提高行业主题至 30%，并设置 8% 止损纪律。",
        "verify": ["《2026 年中期 A 股策略展望》· 中金公司研究部 · 2026-06",
                   "中国人民银行 · 2026 年第二季度货币政策执行报告",
                   "沪深交易所 · 上市公司市值管理指引解读"],
        "summary": "当前市场环境下，建议采取哑铃型配置策略：以红利资产打底获取确定性收益，以政策支持的成长方向博取弹性。请结合您的风险偏好与资金期限执行，并坚持纪律化投资。如需针对白酒、红利、贵金属等具体行业的深度分析，欢迎继续追问。",
    },
}

GUIDE_PROMPTS = [
    "根据最近白酒行业的行情，你能得出什么结果？",
    "请你按照产业上下游的逻辑说明红利行业的投资逻辑？",
    "贵金属行业在目前的股票市场中值得投资吗？",
    "【追问】现在市场看好这个行业吗？建议短期持有还是长期持有？",
]

SPARK_MODELS = {
    "Spark4.0 Ultra": {"domain": "4.0Ultra", "desc": "星火最强旗舰模型，分析与推理能力卓越，Fin 1.5 起作为专家模型，内生联网搜索。", "grad": "linear-gradient(135deg,#7A4FD0,#4A2C9B)", "badge": "专家模型 · 本项目采用"},
    "Spark Max": {"domain": "generalv3.5", "desc": "高性能通用模型，兼顾速度与质量，适合复杂任务拆解与总结。", "grad": "linear-gradient(135deg,#2B4C9B,#16305E)", "badge": "旗舰"},
    "Spark Pro": {"domain": "generalv3", "desc": "均衡型模型，支持微调定制，本项目以其为基座完成金融领域微调（lr=8e-5, 5 epochs）。", "grad": "linear-gradient(135deg,#2E7DB2,#1A4E7A)", "badge": "支持微调"},
    "Spark Lite": {"domain": "general", "desc": "轻量级免费模型，响应极快，适合高并发轻量问答场景。", "grad": "linear-gradient(135deg,#3E9E8F,#206655)", "badge": "极速免费"},
}

# ============================================================== 星火大模型模拟引擎
def match_script(query: str) -> dict:
    for key in ["白酒", "红利", "贵金属"]:
        if key in query:
            return CONSULT_SCRIPT[key]
    return CONSULT_SCRIPT["default"]


def spark_generate(prompt: str, model: str, system: str = "") -> str:
    """模拟星火大模型生成：金融关键词命中知识库，否则模板化组织回答。"""
    script = match_script(prompt)
    if script is not CONSULT_SCRIPT["default"]:
        body = script["expert_answer"] + "\n\n**综合建议**：" + script["summary"]
    else:
        topic = prompt.strip().rstrip("？?。")[:30] or "该问题"
        body = (
            f"关于「{topic}」，基于星火大模型的金融语料训练与联网检索信息，为您梳理如下：\n\n"
            f"**一、背景与现状**：该议题涉及宏观经济环境、行业景气度与市场情绪的多重博弈。"
            f"当前国内货币政策保持合理充裕，资本市场改革持续深化，为相关领域提供了稳定的政策底部。\n\n"
            f"**二、核心逻辑**：从投资视角看，建议从供需格局、估值分位与资金结构三个维度评估。"
            f"历史经验表明，在市场分歧较大、估值处于历史中低分位时进行分批布局，长期胜率更高。\n\n"
            f"**三、风险提示**：需警惕外部环境变化、政策节奏不及预期以及流动性边际收紧带来的波动风险。"
            f"请结合自身风险承受能力与资金期限审慎决策。\n\n"
            f"以上为模拟星火大模型生成的分析框架，如需针对白酒、红利、贵金属行业的深度投顾报告，"
            f"可前往 **Consult 智能咨询** 页面体验多智能体协同推理。"
        )
    if system:
        body = f"（已遵循系统设定：{system[:40]}）\n\n" + body
    if "Lite" in model:
        # 轻量模型：精简输出
        body = body.split("**二、")[0] if "**二、" in body else body[:400]
    return body


def spark_stream(text: str, placeholder, speed: float = 0.012):
    """打字机流式渲染"""
    out = ""
    step = 3
    for i in range(0, len(text), step):
        out += text[i:i + step]
        placeholder.markdown(f'<div class="gen-box">{out}<span class="cursor"></span></div>', unsafe_allow_html=True)
        time.sleep(speed)
    placeholder.markdown(f'<div class="gen-box">{out}</div>', unsafe_allow_html=True)
    return out


def mock_spark_response(model: str, prompt: str, answer: str, temperature: float, top_k: int, max_tokens: int):
    """模拟讯飞星火 Web API v4.0 的响应帧结构"""
    return {
        "header": {"code": 0, "message": "Success", "sid": f"cht{random.randint(10**10, 10**11-1)}mock", "status": 2},
        "payload": {
            "choices": {"status": 2, "seq": 0, "text": [{"role": "assistant", "content": answer[:120] + "……"}]},
            "usage": {"text": {"question_tokens": len(prompt) // 2, "prompt_tokens": len(prompt) // 2 + 12,
                               "completion_tokens": len(answer) // 2, "total_tokens": len(prompt) // 2 + len(answer) // 2 + 12}},
            "model": {"domain": SPARK_MODELS[model]["domain"], "temperature": temperature, "top_k": top_k, "max_tokens": max_tokens},
        },
    }

# ============================================================== 图表
def make_price_series(base: float, days: int = 120, drift: float = 0.0006, vol: float = 0.016):
    rng = np.random.default_rng(int(base * 100) % 2**32)
    rets = rng.normal(drift, vol, days)
    price = base * np.exp(np.cumsum(rets))
    price = price / price[-1] * base
    idx = pd.date_range(end=pd.Timestamp.today(), periods=days, freq="B")
    return pd.DataFrame({"date": idx, "close": np.round(price, 2)})


def price_chart(df: pd.DataFrame, name: str):
    import plotly.graph_objects as go
    up = df["close"].iloc[-1] >= df["close"].iloc[0]
    color = RED if up else GREEN
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["close"], mode="lines",
                             line=dict(color=color, width=2.2, shape="spline", smoothing=0.6), name=name,
                             fill="tozeroy", fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.09)"))
    fig.update_layout(**PLOTLY_BASE, height=270, margin=dict(l=8, r=8, t=34, b=8),
                      title=dict(text=f"{name} · 近 120 个交易日走势", font=dict(size=13, color=NAVY)),
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#EEF1F8"), showlegend=False)
    return fig


def bar_chart():
    import plotly.graph_objects as go
    models = ["Kimi AI", "Spark Max", "Spark Ultra", "Fin Synagent"]
    scores = [26.41, 25.06, 26.47, 28.41]
    colors = ["#C3CDE4", "#C3CDE4", "#C3CDE4", GOLD]
    fig = go.Figure(go.Bar(x=models, y=scores, marker=dict(color=colors, line=dict(color="rgba(0,0,0,0)")),
                           text=[f"{s:.2f}" for s in scores], textposition="outside",
                           textfont=dict(color=NAVY, size=14, family="Noto Serif SC")))
    fig.update_layout(**PLOTLY_BASE, height=360, margin=dict(l=10, r=10, t=44, b=10), bargap=0.42,
                      title=dict(text="AI as Judge · 17 条 Query 平均得分（满分 30）", font=dict(size=15, color=NAVY)),
                      yaxis=dict(range=[0, 32], gridcolor="#EEF1F8"))
    return fig


def customer_chart():
    import plotly.graph_objects as go
    users = ["投资小白", "业余投资者", "专业投资者", "财经博主", "私募基金经理", "投顾助手", "金融新手", "理财新手"]
    scores = [8, 9, 3, 6, 7, 9, 8, 8]
    fig = go.Figure(go.Bar(y=users, x=scores, orientation="h",
                           marker_color=[GOLD if s >= 8 else BLUE if s >= 6 else "#C3CDE4" for s in scores],
                           text=scores, textposition="outside", textfont=dict(color=NAVY, size=13)))
    fig.update_layout(**PLOTLY_BASE, height=360, margin=dict(l=10, r=36, t=44, b=10),
                      title=dict(text="AI as Customers · 模拟用户满意度评分（满分 10）", font=dict(size=15, color=NAVY)),
                      xaxis=dict(range=[0, 11], gridcolor="#EEF1F8"))
    return fig

# ============================================================== 页面：Home
def page_home():
    st.markdown("""
    <div class="hero">
      <div class="kicker">Multi-Agent Robo-Advisor · System-2 Reasoning</div>
      <h1>🚩 Fin Synagent</h1>
      <div class="sub">基于大语言模型的多智能体人机协同投顾推理模式 —— 让专业投顾服务跨越门槛，触手可及。</div>
      <span class="tag">🤖 Multi-Agent 协同</span><span class="tag">🧠 System-2 深思熟虑</span>
      <span class="tag">📚 行业知识库</span><span class="tag">🔍 透明工作流</span><span class="tag">🛡️ 幻觉监督</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">核心功能</div><div class="sec-sub">Consult 智能咨询 · Screen 智能荐股 · 透明化工作流 · 星火大模型驱动</div>', unsafe_allow_html=True)
    cards = [
        ("💬", "Consult 智能咨询", "领导智能体拆解任务、专家智能体专业回答、评论家与求证智能体双重监督，全程可观测、可干预、可追问。"),
        ("📊", "Screen 智能荐股", "基于技术分析与财务分析的筛选树荐股思维，以分析师视角推荐行业个股并给出理由与可视化走势。"),
        ("🏭", "行业深度分析", "覆盖白酒、红利、贵金属三大行业知识库，检索高质量研报融入提示词，信息全部可溯源。"),
        ("🔥", "星火大模型模拟", "内置 Spark4.0 Ultra / Max / Pro / Lite 模拟引擎，参数可调、流式生成，还原真实调用体验。"),
    ]
    for col, (icon, title, desc) in zip(st.columns(4), cards):
        with col:
            st.markdown(f'<div class="card"><div class="icon">{icon}</div><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-title">设计理念</div><div class="sec-sub">概要设计三原则</div>', unsafe_allow_html=True)
    prins = [
        ("🧠", "01 · 深思熟虑", "模拟人脑 System-2 系统运作，明确 LLM 意识边界，以任务拆解工作流实现降本提效。"),
        ("📐", "02 · 实事求是", "采用可视化平台部署，构建多智能体工作流与金融行业知识库，基于事实与数据进行分析。"),
        ("🔎", "03 · 小心求证", "增设知识库与联网求证监控幻觉，叠加用户反馈与追问机制，实现全链路监督。"),
    ]
    for col, (icon, title, desc) in zip(st.columns(3), prins):
        with col:
            st.markdown(f'<div class="card"><div class="icon">{icon}</div><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-title">操作流程</div><div class="sec-sub">四步获得专业投顾服务</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="step"><b>STEP 1 · 输入咨询</b><br><span style="color:#6B7699;font-size:.88rem">在 Consult 页输入您的投资问题，或使用侧边栏引导词快速开始。</span></div>
        <div class="step"><b>STEP 2 · 任务拆解</b><br><span style="color:#6B7699;font-size:.88rem">领导智能体将问题拆解为子任务并分配专家，您可以补充或调整拆解结果（人机协同）。</span></div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="step"><b>STEP 3 · 求证监督</b><br><span style="color:#6B7699;font-size:.88rem">评论家批评改进、搜索与求证智能体联网核验，信息源全部可溯源。</span></div>
        <div class="step"><b>STEP 4 · 总结与追问</b><br><span style="color:#6B7699;font-size:.88rem">总结领导输出最终建议；您可针对结论追问，或前往 Screen 获取个股推荐。</span></div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">评估结果一览</div><div class="sec-sub">AI as Judge · AI as Customers · 人工评估三重验证</div>', unsafe_allow_html=True)
    kpis = [("28.41", "AI 评估均分（满分30）"), ("+8.21%", "显著优于 SOTA 模型"), ("p=0.017", "t 检验显著性"), ("3 大行业", "白酒 · 红利 · 贵金属知识库")]
    for col, (v, k) in zip(st.columns(4), kpis):
        with col:
            st.markdown(f'<div class="kpi"><div class="v">{v}</div><div class="k">{k}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-title">版本迭代回顾</div><div class="sec-sub">基于问题持续进化 · Fin 1.0 → Fin 3.0</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="tl">
      <div class="tl-item"><b>Fin 1.0</b><p>领导选择专家、批评家批评、专家补充的基础流程；发现注意力分散、批评笼统、微调专家能力不足等问题。</p></div>
      <div class="tl-item"><b>Fin 1.5</b><p>采用 Spark4.0 Ultra 作为专家模型，分析处理能力大幅增强，内生联网搜索参考最新消息。</p></div>
      <div class="tl-item"><b>Fin 2.0</b><p>引入任务分解提升注意力；批评家内化为专家自反思；增加知识库 Verify 环节与历史信息抽取。</p></div>
      <div class="tl-item"><b>Fin 2.5</b><p>增加任务分解程度选项（人机协同）；显示联网检索信源；反思环节模型自提示驱动。</p></div>
      <div class="tl-item"><b>Fin 3.0</b><p>增设 Screen 荐股板块，Streamlit 界面由单页进化为多页应用。</p></div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================== 页面：Consult
def run_workflow(query: str, decomp_level: int):
    script = match_script(query)
    st.markdown("---")
    st.markdown("##### 🔄 多智能体协同工作流（透明可观测）")

    with st.status("👔 **Leader 领导智能体** · 正在进行任务拆解…", expanded=True) as s:
        time.sleep(0.9)
        st.write(f"识别问题意图：行业咨询 / 投资建议 · 拆解粒度：**{decomp_level} 级**")
        for i, t in enumerate(script["subtasks"], 1):
            st.write(f"📌 子任务 {i}：{t}")
        st.write(f"🎯 已分配专家：{'、'.join(script['experts'])}")
        s.update(label="👔 **Leader 领导智能体** · 任务拆解完成，可补充子任务", state="complete")
    with st.expander("🙋 人机协同 · 对拆解任务进行补充（可选）"):
        st.text_input("输入您希望补充的分析方向，专家将一并考虑：", key=f"supp_{time.time()}")

    # RAG 知识库检索
    rag_key = next((k for k in ["白酒", "红利", "贵金属"] if k in query), "default")
    with st.status("📚 **知识库检索（RAG）** · 正在检索行业知识库…", expanded=True) as s:
        time.sleep(0.6)
        st.write("**检索流程**：语义段落切分（Semantic Chunking）→ 星火 Embedding 向量化 → Chroma 向量库 → 查询向量化 → 余弦相似度 Top-K 检索 → Prompt 拼接")
        for title, score, snippet in RAG_CHUNKS[rag_key]:
            st.markdown(f'<div class="src">📄 <b>{title}</b> · 相似度 <b>{score:.3f}</b><br><span style="color:#4A6A56;">{snippet}</span></div>', unsafe_allow_html=True)
        s.update(label="📚 **知识库检索（RAG）** · 命中 Top-3 高相关片段，已注入专家提示词", state="complete")

    with st.status("🎓 **专家智能体（Spark4.0 Ultra）** · 正在基于检索片段生成专业回答…", expanded=True) as s:
        time.sleep(0.8)
        ph = st.empty()
        spark_stream(script["expert_answer"], ph, speed=0.006)
        s.update(label="🎓 **专家智能体（Spark4.0 Ultra）** · 回答生成完毕", state="complete")

    with st.status("🧐 **评论家智能体** · 正在审查专家回答…", expanded=True) as s:
        time.sleep(0.8)
        st.write(script["critic"])
        c1, c2 = st.columns(2)
        c1.button("👍 认同批评意见", key=f"agree_{time.time()}")
        c2.button("✋ 不认同，给出反馈", key=f"disagree_{time.time()}")
        s.update(label="🧐 **评论家智能体** · 批评意见已输出", state="complete")

    with st.status("✍️ **专家智能体** · 针对批评与追问完善回答…", expanded=True) as s:
        time.sleep(0.7)
        st.write(script["expert_revise"])
        s.update(label="✍️ **专家智能体** · 回答已完善", state="complete")

    with st.status("🔎 **搜索与求证智能体** · 正在联网检索并核验真实性…", expanded=True) as s:
        time.sleep(0.9)
        st.write("已检索知识库与互联网，交叉验证关键数据，未发现幻觉内容。信息源如下：")
        for src in script["verify"]:
            st.markdown(f'<div class="src">📄 {src}</div>', unsafe_allow_html=True)
        s.update(label="🔎 **搜索与求证智能体** · 验证通过 · 信息可溯源", state="complete")

    with st.status("📋 **总结领导** · 正在汇总全部信息…", expanded=True) as s:
        time.sleep(0.6)
        s.update(label="📋 **总结领导** · 最终建议", state="complete")
    st.success(script["summary"])
    st.caption("💡 您可以继续追问（如：现在市场看好吗？短期还是长期持有？），系统将结合上下文持续回答。")
    return script["summary"]


def page_consult():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Consult · Multi-Agent Reasoning</div>
      <h1 style="font-size:2rem;">💬 智能投顾咨询</h1>
      <div class="sub" style="margin-bottom:0;">System-2 深思熟虑 · Multi-Agent 互相监督 · Web 检索 &amp; 知识库求证 · 显式思维链</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🧭 引导词")
        for gp in GUIDE_PROMPTS:
            if st.button(gp, key=f"guide_{gp}", use_container_width=True):
                st.session_state["pending_query"] = gp
        st.markdown("---")
        st.markdown("### ⚙️ 任务分解程度")
        decomp_level = st.slider("拆解粒度（人机协同选项）", 1, 5, 3)
        st.caption("粒度越高，子任务越细，专家注意力越集中。")

    st.markdown("""
    <div style="margin-bottom:14px;">
      <span class="pill">人机交互</span><span class="pill">System-2</span><span class="pill">Multi-Agent</span>
      <span class="pill">Web &amp; Verify</span><span class="pill">信息可溯源</span><span class="pill">可追问</span>
    </div>
    """, unsafe_allow_html=True)

    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    for msg in st.session_state["chat"]:
        with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "🚩"):
            st.markdown(msg["content"])

    query = st.chat_input("请输入您的投资咨询问题，例如：白酒行业最近行情如何？")
    if "pending_query" in st.session_state:
        query = st.session_state.pop("pending_query")

    if query:
        st.session_state["chat"].append({"role": "user", "content": query})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(query)
        with st.chat_message("assistant", avatar="🚩"):
            summary = run_workflow(query, decomp_level)
        st.session_state["chat"].append({"role": "assistant", "content": summary})

# ============================================================== 页面：Screen
def page_screen():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Screen · Tree-of-Thought Stock Picking</div>
      <h1 style="font-size:2rem;">📊 智能荐股</h1>
      <div class="sub" style="margin-bottom:0;">筛选树荐股思维 · 分析师视角与需求验证 · 可视化市场信息</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🎯 荐股设置")
        industry = st.selectbox("选择目标行业", list(STOCKS.keys()))
        risk = st.radio("风险偏好（先验提示词）", ["保守型", "稳健型", "积极型"], index=1)
        run = st.button("🚀 开始智能筛选", use_container_width=True, type="primary")

    feat = INDUSTRY_FEATURE[industry]
    st.markdown(f"**当前方案**：行业 = `{industry}` · 风险偏好 = `{risk}` · 数据源 = qstock 行情 / 财务报告 / 时讯情感（glm-4-flash 分类）")

    if run:
        pool = CANDIDATES[industry]

        with st.status("🧭 **Screen Agent** · 正在解析投资意图…", expanded=True) as s:
            time.sleep(0.7)
            st.json({"sector": industry,
                     "risk_preference": {"保守型": "low", "稳健型": "medium", "积极型": "high"}[risk],
                     "objective": "capital_appreciation" if risk == "积极型" else "stable_income",
                     "source": "qstock 行情 / 财务报告 / 时讯新闻"})
            s.update(label="🧭 **Screen Agent** · 意图解析完成，已生成结构化筛选条件", state="complete")

        with st.status("🏗️ **股票池构建** · 正在从行业板块过滤候选标的…", expanded=True) as s:
            time.sleep(0.7)
            st.write(f"行业过滤：`{industry}` 子行业 → 基础过滤：市值 > 500 亿、日均成交 > 1 亿、非 ST → 候选池 **{len(pool)} 支**")
            st.dataframe(pd.DataFrame([{"股票": c["name"], "代码": c["code"]} for c in pool]),
                         use_container_width=True, hide_index=True)
            s.update(label="🏗️ **股票池构建** · 候选池就绪", state="complete")

        with st.status("🧬 **多维特征提取** · 基本面 / 技术面 / 情绪面 / 行业面 → 特征合成…", expanded=True) as s:
            time.sleep(0.9)
            t1, t2, t3, t4 = st.tabs(["💰 基本面特征", "📈 技术面特征", "💬 情绪面特征（FinBERT）", "🏭 行业面特征"])
            with t1:
                st.dataframe(pd.DataFrame([{"股票": c["name"], "市盈率PE": c["pe"], "市净率PB": c["pb"],
                                            "ROE(%)": c["roe"], "营收增速(%)": c["rev"]} for c in pool]),
                             use_container_width=True, hide_index=True)
                st.caption("数据来源：qstock 财务报表接口 · 筛选逻辑：低估值 + 高 ROE + 稳定增长")
            with t2:
                st.dataframe(pd.DataFrame([{"股票": c["name"], "趋势": c["trend"], "均线形态": c["ma"],
                                            "波动率": c["vol"], "MACD": c["macd"]} for c in pool]),
                             use_container_width=True, hide_index=True)
                st.caption("数据来源：qstock 行情接口 · 筛选逻辑：上升趋势 + 均线多头 + MACD 金叉优先")
            with t3:
                import plotly.graph_objects as go
                fig = go.Figure()
                names = [c["name"] for c in pool]
                fig.add_trace(go.Bar(name="正面", x=names, y=[c["sent"][0] for c in pool], marker_color=RED))
                fig.add_trace(go.Bar(name="中性", x=names, y=[c["sent"][2] for c in pool], marker_color="#C3CDE4"))
                fig.add_trace(go.Bar(name="负面", x=names, y=[c["sent"][1] for c in pool], marker_color=GREEN))
                fig.update_layout(**PLOTLY_BASE, barmode="stack", height=320, margin=dict(l=10, r=10, t=30, b=10),
                                  title=dict(text="FinBERT 新闻情感三分类（正面 / 中性 / 负面）", font=dict(size=13, color=NAVY)),
                                  yaxis=dict(gridcolor="#EEF1F8"), legend=dict(orientation="h", y=1.12))
                st.plotly_chart(fig, use_container_width=True)
                st.caption("FinBERT：基于 BERT 架构、在海量金融语料（财报 / 研报 / 新闻）上微调的情感分析模型")
            with t4:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**🌐 宏观特征**")
                    for f in feat["macro"]:
                        st.write("✅", f)
                with c2:
                    st.markdown("**🏭 行业特征**")
                    for f in feat["industry"]:
                        st.write("✅", f)
            s.update(label="🧬 **多维特征提取** · 特征合成完毕，送入 LLM 评分", state="complete")

        with st.status("⚖️ **LLM 综合评分** · 分析师视角打分 → 排序 → TopK 筛选…", expanded=True) as s:
            time.sleep(0.8)
            import plotly.graph_objects as go
            names = [c["name"] for c in pool]
            scores = [c["score"] for c in pool]
            fig = go.Figure(go.Bar(x=names, y=scores,
                                   marker_color=[GOLD if i < 3 else "#C3CDE4" for i in range(len(pool))],
                                   text=scores, textposition="outside", textfont=dict(color=NAVY, size=13)))
            fig.update_layout(**PLOTLY_BASE, height=300, margin=dict(l=10, r=10, t=30, b=10),
                              title=dict(text=f"LLM 综合评分（金色 = Top-3 入选）· 满分 100", font=dict(size=13, color=NAVY)),
                              yaxis=dict(range=[0, 100], gridcolor="#EEF1F8"))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("评分 Prompt：You are a senior equity analyst. 综合基本面 / 技术面 / 情绪面 / 行业面四维特征，0-100 打分")
            s.update(label="⚖️ **LLM 综合评分** · Top-3 标的已锁定", state="complete")

        st.info(f"**分析师观点**：{feat['view']}")

        st.markdown("#### 🏆 推荐组合（Top-3）· 已生成推荐解释")
        cols = st.columns(3)
        for col, stk in zip(cols, STOCKS[industry]):
            with col:
                chg_cls = "up" if stk["chg"] >= 0 else "down"
                sign = "+" if stk["chg"] >= 0 else ""
                st.markdown(f"""
                <div class="stock-card">
                  <div><span class="stock-name">{stk['name']}</span><span class="stock-code">{stk['code']}</span></div>
                  <div style="margin:10px 0 4px 0;">
                    <span style="font-size:1.65rem;font-weight:900;color:{NAVY};font-family:'Noto Serif SC',serif;">¥{stk['price']:.2f}</span>
                    <span class="{chg_cls}" style="margin-left:10px;font-size:1.02rem;">{sign}{stk['chg']:.2f}%</span>
                  </div>
                  <div style="font-size:.82rem;color:#7A86A6;">市盈率 {stk['pe']} · 总市值 {stk['mv']}</div>
                </div>
                """, unsafe_allow_html=True)
                df = make_price_series(stk["price"])
                st.plotly_chart(price_chart(df, stk["name"]), use_container_width=True)
                with st.expander("📌 推荐理由（分析师视角）"):
                    st.write(stk["reason"])
        st.caption("💡 侧边栏可切换行业与风险偏好；历史数据与可视化图表支持回溯查看。数据为演示模拟。")
    else:
        st.markdown('<div class="sec-title">Screen 完整流程</div><div class="sec-sub">用户偏好 → 条件解析 → 股票池构建 → 多维评分 → 排序筛选 → 输出推荐</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="card"><div class="icon">🧬</div><h4>四维特征提取</h4><p>基本面（PE/PB/ROE/营收增速）、技术面（趋势/均线/波动率/MACD）、情绪面（FinBERT 三分类）、行业面（宏观+景气），特征合成后送入 LLM。</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="card"><div class="icon">⚖️</div><h4>LLM 评分与 TopK 筛选</h4><p>资深分析师视角对候选池 0-100 综合打分，排序后 Top-3 入选，自动生成推荐解释与可视化走势。</p></div>', unsafe_allow_html=True)
        st.info("👈 请在左侧侧边栏选择行业与风险偏好，点击「开始智能筛选」运行工作流。")

# ============================================================== 页面：星火大模型模拟
def page_spark():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">iFLYTEK SparkDesk · Simulation Playground</div>
      <h1 style="font-size:2rem;">🔥 星火大模型模拟</h1>
      <div class="sub" style="margin-bottom:0;">模拟讯飞星火认知大模型的调用与流式生成 · 本项目 Consult / Screen 均由其驱动</div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("⚠️ 本页面为星火大模型的**模拟演示**：不调用真实 API，生成内容来自内置金融知识库模板，用于还原真实调用链路。")

    st.markdown('<div class="sec-title" style="margin-top:18px;">选择模型版本</div><div class="sec-sub">对应星火 Web API 的 domain 参数</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    if "spark_model" not in st.session_state:
        st.session_state["spark_model"] = "Spark4.0 Ultra"
    for col, (name, meta) in zip(cols, SPARK_MODELS.items()):
        with col:
            st.markdown(f"""
            <div class="spark-card" style="background:{meta['grad']};">
              <span class="badge">{meta['badge']}</span>
              <h4>{name}</h4><p>{meta['desc']}</p>
            </div>""", unsafe_allow_html=True)
            if st.button(f"{'✅ 当前模型' if st.session_state['spark_model'] == name else '选用 ' + name}",
                         key=f"pick_{name}", use_container_width=True,
                         type="primary" if st.session_state["spark_model"] == name else "secondary"):
                st.session_state["spark_model"] = name
                st.rerun()
    model = st.session_state["spark_model"]

    st.markdown('<div class="sec-title">参数配置</div><div class="sec-sub">与星火 Web API v4.0 parameter.chat 字段一一对应</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        temperature = st.slider("🌡️ temperature（核采样阈值）", 0.0, 1.0, 0.5, 0.05,
                                help="越高越发散，星火建议 0.5")
    with c2:
        top_k = st.slider("🎲 top_k（候选集大小）", 1, 6, 4, help="从 k 个候选中随机选择，星火范围 1-6")
    with c3:
        max_tokens = st.slider("📏 max_tokens（最大生成长度）", 256, 8192, 2048, 256)
    system = st.text_input("🧾 System Prompt（人格 / 角色设定，可选）",
                           placeholder="例如：你是一位严谨的金融分析师，只基于事实与数据回答。")

    st.markdown('<div class="sec-title">发起对话</div><div class="sec-sub">流式输出 · 模拟 SSE 逐帧返回</div>', unsafe_allow_html=True)
    q = st.chat_input("向星火大模型提问，例如：白酒行业最近行情如何？")

    with st.expander("📦 查看模拟 API 请求报文（Web API v4.0）"):
        st.json({
            "header": {"app_id": "xxxxxxxx", "uid": "demo_user"},
            "parameter": {"chat": {"domain": SPARK_MODELS[model]["domain"], "temperature": temperature,
                                   "top_k": top_k, "max_tokens": max_tokens}},
            "payload": {"message": {"text": [{"role": "system", "content": system or "（未设置）"},
                                             {"role": "user", "content": q or "（等待输入）"}]}},
        })

    if "spark_history" not in st.session_state:
        st.session_state["spark_history"] = []
    for msg in st.session_state["spark_history"]:
        with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "🔥"):
            st.markdown(msg["content"])

    if q:
        st.session_state["spark_history"].append({"role": "user", "content": q})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(q)
        with st.chat_message("assistant", avatar="🔥"):
            answer = spark_generate(q, model, system)
            ph = st.empty()
            spark_stream(answer, ph, speed=0.008)
            with st.expander("📡 模拟响应帧（最终帧 · status=2）"):
                st.json(mock_spark_response(model, q, answer, temperature, top_k, max_tokens))
        st.session_state["spark_history"].append({"role": "assistant", "content": answer})

# ============================================================== 页面：评估测试
def page_eval():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Evaluation · Triple Verification</div>
      <h1 style="font-size:2rem;">🧪 测试与评估</h1>
      <div class="sub" style="margin-bottom:0;">AI as Judge · AI as Customers · Human Check · 消融实验</div>
    </div>
    """, unsafe_allow_html=True)

    st.plotly_chart(bar_chart(), use_container_width=True)
    st.markdown("""
    <div class="card" style="margin-top:8px;">
      <h4>📐 统计检验（Fin Synagent vs Kimi）</h4>
      <p>均值差异 -1.1765（Kimi 更低）· 95% 置信区间 (-2.1266, -0.2264) · <b>P-value = 0.0168 &lt; 0.05</b>。
      统计检验表明 Fin Synagent 的表现显著优于其他模型，尤其在白酒、贵金属、红利等细分行业，SOTA 模型表现不佳，而 Fin Synagent 性能稳定良好。</p>
    </div>
    """, unsafe_allow_html=True)

    st.plotly_chart(customer_chart(), use_container_width=True)
    st.markdown("""
    <div class="card" style="margin-top:8px;">
      <h4>👥 模拟用户结论</h4>
      <p>通过第三方大模型生成 20 个不同投资水平的模拟用户进行交互与反馈：项目普适性较强，<b>尤其适于新手投资者</b>（投资小白 8 分、业余投资者 9 分、投顾助手 9 分）。</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="card"><div class="icon">🧑‍🎓</div><h4>Human Check 人工评估</h4>
        <p>金融专业研究生对比大模型服务与 Fin Synagent 的回答：Fin Synagent 在框架逻辑性、分析深度与前瞻性建议上更优——能够从宏观经济指标、行业动态与市场情绪等多因素给出全面洞察，在风险管理、投资策略与市场趋势解读方面优势明显。</p></div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="card"><div class="icon">🧬</div><h4>消融实验</h4>
        <p><b>微调组件</b>：微调后模型更能抓住「投资」关键词，给出贴合需求的投资关注建议。<br>
        <b>工作流组件</b>：相比单纯与星火大模型交互，工作流在问题全面性与深度上更胜一筹，信息更丰富详细。</p></div>
        """, unsafe_allow_html=True)

# ============================================================== 页面：技术架构
def page_tech():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Architecture · System-2 Workflow</div>
      <h1 style="font-size:2rem;">🧠 技术设计</h1>
      <div class="sub" style="margin-bottom:0;">类人脑 System-2 投顾推理模式 · 多智能体工作流 · 知识库与微调</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">Consult 工作流设计</div><div class="sec-sub">类脑 System-2 · 深思熟虑</div>', unsafe_allow_html=True)
    roles = [
        ("👔", "Leader 领导", "任务拆解<br>降本提效", "a-leader"),
        ("🎓", "Expert 专家", "知识库增强<br>专业回答", "a-expert"),
        ("🧐", "Critic 评论家", "批评监督<br>对齐偏好", "a-critic"),
        ("🔎", "Search & Verify", "联网检索<br>求证幻觉", "a-verify"),
        ("📋", "Summary 总结", "概括输出<br>支持追问", "a-sum"),
    ]
    for col, (icon, name, desc, cls) in zip(st.columns(5), roles):
        with col:
            st.markdown(f'<div class="agent {cls}"><div class="em">{icon}</div><div class="role">{name}</div><div class="desc">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="margin-top:14px;">
      <h4>🔄 流程说明</h4>
      <p>用户输入 Query → Leader 任务拆解（用户可补充，人机协同）→ 分配专家基于任务提示词专业回答 → 评论家批评、用户可反馈 → 专家完善 → 搜索与求证智能体验证真实性 → 总结领导输出 → 用户可追问或开启新对话。<br>
      Part1 完成后自动将记录作为 Part2 背景，保证上下文连贯。</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">Screen 筛选树设计</div><div class="sec-sub">树状思维 · 特征筛选</div>', unsafe_allow_html=True)
    items = [
        ("🎯", "① 风险偏好先验", "根据投资者风险偏好设定先验风险信息提示词，对齐投资目标。"),
        ("🧩", "② 三维特征获取", "qstock 接口获取资产定价、技术分析、宏观新闻三维特征，glm-4-flash 完成新闻情感分类。"),
        ("🌳", "③ 树推理荐股", "大模型依赖树状思维筛选特征、预测涨跌，结合风险偏好推荐行业个股。"),
    ]
    for col, (icon, title, desc) in zip(st.columns(3), items):
        with col:
            st.markdown(f'<div class="card"><div class="icon">{icon}</div><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-title">模型微调与知识库</div><div class="sec-sub">专业性保障</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="card"><div class="icon">🔧</div><h4>微调</h4>
        <p>微调数据集来自数据增强后的证券从业、基金从业资格考试知识库，以及讯飞 FinCUGE 金融训练数据集；基座模型 SparkPro，学习率 8e-5，训练 5 轮，一键发布至星火平台。</p></div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="card"><div class="icon">📚</div><h4>知识库</h4>
        <p>分领域收集高质量金融研报，PDF 转 Markdown 优化后经星火知识库 API 上传，构建红利、白酒、贵金属三大行业知识库；检索内容融入提示词，定期更新维护。</p></div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">创新点</div><div class="sec-sub">四大核心创新</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="step"><b>01 · 多智能体人机协同工作流</b><br><span style="color:#6B7699;font-size:.88rem">凭借星火大模型构筑多智能体协同体系，智能体与人类紧密协作，整体性能显著提升。</span></div>
    <div class="step"><b>02 · 透明化工作流与任务拆解创新</b><br><span style="color:#6B7699;font-size:.88rem">用户可在透明工作流中干预智能体生成内容辅助决策，并可追问，建议更可控、更契合需求。</span></div>
    <div class="step"><b>03 · 可解释性强化</b><br><span style="color:#6B7699;font-size:.88rem">用户可直观观测各智能体协作产生的内容，从整体层面强化可解释性，构建对 AI 的信任。</span></div>
    <div class="step"><b>04 · 知识库增强提示</b><br><span style="color:#6B7699;font-size:.88rem">检索获取的知识库内容融入提示词，大幅提升回答准确性与精度，维护便捷、可持续更新。</span></div>
    """, unsafe_allow_html=True)

# ============================================================== 页面：面试建议
INTERVIEW_BEHAVIOR = [
    ("请举一个你主动设定高难度目标，最后成功落地完成的例子。",
     "市面上普通 AI 只能简单回答投资问题，存在分析片面、数据不实、普通散户难以理解的问题，我主动提出要搭建一套完整的 AI 金融投研辅助工具。",
     "独立完成一套多智能体协同智能投顾系统，达到专业分析师级别的回答质量。",
     "① 将大目标拆解为 Consult 咨询与 Screen 荐股两大模块；② 自学多智能体工作流、RAG 检索增强与 SFT 微调技术；③ 从 Fin 1.0 到 3.0 持续迭代，每个版本针对暴露的问题定向优化。",
     "系统在 AI as Judge 评测中取得 28.41/30 的平均分，统计检验显著优于 Kimi、Spark 等 SOTA 模型（p=0.017），并成功部署上线。"),
    ("讲一个你面对大量繁杂信息、多重问题，快速梳理关键、分清轻重缓急解决问题的案例。",
     "搭建系统时涉及行业资料整理、咨询逻辑设计、选股规则、效果测试等多块内容，初期团队思路分散，各模块输出标准不一。",
     "统一各模块的输出标准与接口约定，保证系统整体协同推进。",
     "① 将信息按『数据层—模型层—交互层』三层归类；② 用优先级矩阵（影响面 × 紧急度）排序任务；③ 制定工作流规范文档，明确每个 Agent 的输入输出契约。",
     "各模块快速对齐，开发效率显著提升，项目按计划完成集成测试。"),
    ("举例说明你用客观事实、逻辑说服持反对意见的人，统一方案的经历。",
     "设计咨询模块时，有伙伴认为不需要额外的资料校验环节，觉得会拉长系统响应时间。",
     "说服团队接受 Search & Verify 事实校验环节。",
     "① 收集无校验环节时模型产生幻觉的实际案例（编造研报名称、张冠李戴数据）；② 设计对比实验，用有无 Verify 的回答质量评分说话；③ 提出异步检索方案平衡响应速度。",
     "团队一致同意保留校验环节，系统幻觉率显著下降，用户信任度提升。"),
    ("分享一次你和团队产生较大观点分歧，主动协调化解矛盾、合力完成任务的经历。",
     "设计选股模块时，团队出现明显分歧：一部分人认为只看财务基本面筛选即可，另一部分人坚持叠加行情与市场情绪。",
     "在不伤和气的前提下确定技术方案。",
     "① 不急于站队，组织双方各自陈述依据；② 提议用消融实验裁决：分别用纯基本面与四维特征方案跑历史数据回测；③ 用命中率与回撤数据客观对比。",
     "数据证明多维特征方案显著更优，团队欣然采纳『基本面+技术面+情绪面+行业面』四维方案，荐股质量明显提升。"),
    ("讲一个你主动提出创新思路，落地后显著优化项目效果的案例。",
     "传统 AI 投顾只能给出单一结论，要么看多要么看空，普通散户很难看懂行业全貌，且经常缺少真实数据支撑。",
     "从交互层面创新，提升系统的可解释性与用户信任。",
     "① 提出『透明工作流 + 显式思维链』设计，让用户直观看到任务拆解、专家作答、求证监督全过程；② 增加追问机制与信源展示，信息全部可溯源。",
     "可解释性大幅增强，模拟用户测评中新手投资者给出 8-9 分高分，成为项目核心创新点。"),
    ("描述一次时间紧张、资源有限、压力较大的场景，你如何推进并顺利交付成果。",
     "项目交付期限提前，行业研报与投资素材储备不足，人手有限，既要完成咨询模块又要搭建选股模块。",
     "在压缩后的期限内保质保量交付。",
     "① 砍除非核心功能，聚焦 Consult 与 Screen 两条主线；② 复用已沉淀的知识库与提示词模板，避免重复建设；③ 任务并行化，每日站会对齐进度与风险。",
     "系统按期上线并通过全部测试用例，核心功能零缺陷交付。"),
    ("分享一次你从零快速学习全新领域知识，马上落地解决实际问题的经历。",
     "此前没有系统学习过专业投研分析框架，但要搭建 AI 金融投研工具，必须快速掌握行业分析、股票筛选与投资者风险偏好等知识。",
     "在短时间内建立投研知识体系并转化为系统能力。",
     "① 以产业链分析法为主线，精读白酒、红利、贵金属三大行业高质量券商研报；② 向金融专业同学请教关键指标含义；③ 边学边做，把学到的分析框架沉淀为知识库与提示词模板。",
     "独立完成三大行业知识库与分析模块，系统回答质量通过金融专业研究生人工评测认可。"),
]

INTERVIEW_TECH = [
    ("什么是 Agent？Agent 和 LLM 有什么区别？",
     "Agent 是能够感知信息、做出决策并执行行动以完成目标的智能系统。\n\n**LLM = 只负责回答/生成**；**Agent = 能思考 + 能规划 + 能行动**。Agent 以 LLM 为大脑，叠加任务规划、工具调用（搜索、数据库、API）与记忆能力，可以自主完成多步骤复杂任务。"),
    ("什么是 RAG？完整流程是什么？有什么作用？⭐面试高频",
     "RAG（Retrieval-Augmented Generation，检索增强生成）是在生成前先检索外部知识、把检索结果拼入提示词再生成答案的技术。\n\n**完整流程（7 步）**：① 文档切分（本项目用语义段落切分 Semantic Chunking，同一主题划为一个 Chunk）→ ② 向量化（星火 Embedding 模型编码）→ ③ 存入向量数据库（Chroma）→ ④ 查询向量化 → ⑤ 相似度检索（余弦相似度 Top-K）→ ⑥ Prompt 拼接（系统指令约束：严格依据资料、标注来源）→ ⑦ 生成答案。\n\n**作用**：① 解决模型知识不新的问题；② 解决知识不全的问题、避免幻觉；③ 让模型能访问私域 / 内部数据。"),
    ("什么是模型幻觉？产生原因是什么？如何抑制？",
     "幻觉是大模型生成看似合理但与事实不符内容的现象。\n\n**典型表现**：① 编造事实（把不存在的论文、新闻、数据说成真的）；② 张冠李戴（把 A 的结论安到 B 头上）；③ 虚构引用。\n\n**原因**：语言流畅性优先于真实性；缺少实时知识核对机制。\n\n**本项目对策**：RAG 知识库约束回答依据 + Search Agent 联网检索 + Verify Agent 事实校验，输出与网络数据、知识库数据双重比对。"),
    ("什么是微调？什么是 LoRA 微调？",
     "**微调（Fine-tune）**：通用大模型见过海量数据但不懂你的专属任务与风格，微调就是用领域数据继续训练，让模型掌握专属能力。本项目用证券/基金从业题库 + FinCUGE 数据集 + 行业研报问答对，在星火平台对 Spark 模型做 SFT 微调。\n\n**LoRA**：不改动原模型任何权重，在 Transformer 注意力模块旁额外插入两个极小的低秩矩阵 A、B，只训练这两个矩阵。\n\n**LoRA 优势**：① 显存门槛低；② 训练速度快；③ 权重可随时开关切换。\n\n**步骤**：准备专属数据集 → 冻结原始权重、仅开启 LoRA 矩阵训练 → 少量轮次训练收敛（本项目 lr=8e-5，5 epochs）→ 保存并绑定 LoRA 权重发布。"),
    ("什么是 Prompt Engineering？高质量 Prompt 的基本结构？",
     "Prompt Engineering 本质是用自然语言精确描述需求，引导模型输出高质量结果。\n\n**高质量 Prompt 四要素**：① 角色（Role：你是资深金融分析师）；② 任务（Task：明确要做什么）；③ 上下文 / 约束（依据给定资料、不得编造、标注来源）；④ 输出格式（分点、表格、JSON 等）。\n\n本项目 Screen 的评分 Prompt 即采用『资深股票分析师』角色 + 四维特征输入 + 0-100 结构化打分输出。"),
    ("你们的三层评测体系是怎么设计的？",
     "① **AI as Judge**：第三方大模型从相关性、完整性、逻辑性三个维度 0-30 分批量打分，并用 t 检验做显著性验证（本项目 p=0.017 显著优于 SOTA）；② **AI as Customers**：生成 20 个不同投资水平的模拟用户身份提问并反馈评分，验证普适性；③ **人工交叉评测**：金融专业研究生按统一标准（单题满分 30，覆盖行业数据、产业链分析、风险提示、无幻觉四点）主观评测。另配合**消融实验**验证微调与工作流组件的各自贡献。"),
]

def page_interview():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Interview Playbook · STAR & Tech Q&A</div>
      <h1 style="font-size:2rem;">🎤 项目面试建议</h1>
      <div class="sub" style="margin-bottom:0;">AI 面试行为题（STAR 法则） · 技术高频问答 · 全部答案锚定 Fin Synagent 真实项目经历</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">第一部分 · AI 面试行为题</div><div class="sec-sub">STAR 法则：Situation 背景 → Task 任务 → Action 行动 → Result 结果</div>', unsafe_allow_html=True)
    for i, (q, s, t, a, r) in enumerate(INTERVIEW_BEHAVIOR, 1):
        with st.expander(f"**Q{i} · {q}**"):
            st.markdown(f"""
            <div class="step" style="border-left-color:#2B4C9B;"><b>S · 背景</b><br><span style="color:#55607a;font-size:.9rem;">{s}</span></div>
            <div class="step" style="border-left-color:#4A6FD4;"><b>T · 任务</b><br><span style="color:#55607a;font-size:.9rem;">{t}</span></div>
            <div class="step" style="border-left-color:#C9A227;"><b>A · 行动</b><br><span style="color:#55607a;font-size:.9rem;">{a}</span></div>
            <div class="step" style="border-left-color:#1E9E6A;"><b>R · 结果</b><br><span style="color:#55607a;font-size:.9rem;">{r}</span></div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">第二部分 · 技术高频问答</div><div class="sec-sub">围绕本项目核心技术点：Multi-Agent · RAG · 微调 / LoRA · 幻觉抑制 · 评测体系</div>', unsafe_allow_html=True)
    for q, a in INTERVIEW_TECH:
        with st.expander(f"**{q}**"):
            st.markdown(a)

    st.markdown("""
    <div class="card" style="margin-top:22px;">
      <h4>💡 答题小贴士</h4>
      <p>① 行为题务必落到<b>量化结果</b>（28.41 分、p=0.017、模拟用户 8-9 分）；② 技术题先给一句话定义，再讲流程，最后落到<b>本项目怎么用的</b>；
      ③ 被追问 RAG 时主动说出七步流程与语义切分细节——这是面试高频考点。</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================== 导航
PAGES = {
    "首页": page_home,
    "智能咨询": page_consult,
    "智能荐股": page_screen,
    "星火大模型": page_spark,
    "测试评估": page_eval,
    "技术设计": page_tech,
    "面试建议": page_interview,
}
NAV_ICONS = ["house-door", "chat-square-text", "graph-up-arrow", "fire", "clipboard2-data", "cpu", "mic"]

with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="logo">🚩 Fin <span>Synagent</span></div>
      <div class="slogan">MULTI-AGENT ROBO-ADVISOR</div>
    </div>
    """, unsafe_allow_html=True)
    choice = option_menu(
        menu_title=None,
        options=list(PAGES.keys()),
        icons=NAV_ICONS,
        default_index=0,
        styles={
            "container": {
                "padding": "10px 8px", "background-color": "#0E2450",
                "border-radius": "14px", "border": "1px solid rgba(201,162,39,0.35)",
            },
            "icon": {"color": "#E8C766", "font-size": "16px"},
            "nav-link": {
                "font-size": "16px", "font-family": "Noto Sans SC", "text-align": "left",
                "margin": "4px 0", "padding": "10px 16px", "border-radius": "12px",
                "color": "#FFFFFF", "font-weight": "600",
                "--hover-color": "rgba(201,162,39,0.22)",
                "border": "1px solid transparent",
            },
            "nav-link-selected": {
                "background": "linear-gradient(90deg, rgba(201,162,39,0.35), rgba(201,162,39,0.10))",
                "border": "1px solid rgba(201,162,39,0.75)",
                "color": "#FFE9A8", "font-weight": "800",
                "border-left": "4px solid #E8C766",
            },
        },
    )
    st.markdown("---")
    st.caption("富国开贸团队 · 演示 Demo v2")
    st.caption("⚠️ 数据为模拟数据，不构成投资建议")

PAGES[choice]()

st.markdown('<div class="footer">🚩 Fin Synagent · 基于大语言模型的多智能体人机协同投顾推理模式 · 仅供演示</div>', unsafe_allow_html=True)
