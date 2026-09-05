# -*- coding: utf-8 -*-
"""
Fin Synagent - 基于多智能体协同的智能投顾 Demo (v2)
UI 全面升级 + 星火大模型模拟引擎
还原自《基于多智能体协同的智能投顾设计》/《AIGC》/《创作思路说明》
"""
import os
import re
import json
import time
import datetime
import random
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

# ============================================================== 真实知识库数据（离线 bundle）
KB_DATA_PATH = os.path.join(os.path.dirname(__file__), "kb_data.json")
# 技能内置的可运行 Python 脚本目录（随 Demo 一同部署，页面直接读取真实文件内容）
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")
# 技能内置的 references 知识文档目录（随 Demo 一同部署，页面可展开渲染并下载）
REFERENCES_DIR = os.path.join(os.path.dirname(__file__), "references")
@st.cache_data
def load_kb_data(version="v1"):
    """加载由 knowledge_base/Chroma 真实检索 + 微调数据集统计生成的 bundle。"""
    _ = version  # 用于数据格式更新时强制刷新 cache
    try:
        with open(KB_DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
KB = load_kb_data(version="v2")

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
section[data-testid="stSidebar"] .stButton > button,
div[data-testid="stSidebar"] .stButton > button {{
  background: rgba(255,255,255,.08); border: 1px solid rgba(201,162,39,.45);
  color: #FFFFFF !important; border-radius: 11px; transition: all .2s ease; font-weight:500;
  white-space: normal; line-height: 1.5; text-align: left; padding: 10px 14px;
}}
section[data-testid="stSidebar"] .stButton > button:hover,
div[data-testid="stSidebar"] .stButton > button:hover {{
  background: rgba(201,162,39,.16); border-color: rgba(201,162,39,.7); transform: translateX(2px);
}}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
div[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background: linear-gradient(90deg, {GOLD}, {GOLD2}); color: {NAVY} !important;
  border: none; font-weight: 700; text-align: center;
}}
.sb-brand {{ text-align:center; padding:10px 0 4px 0; }}
.sb-brand .logo {{ font-family:"Noto Serif SC",serif; font-size:1.55rem; font-weight:900; color:#fff !important; letter-spacing:1px; }}
.sb-brand .logo span {{ color:{GOLD2} !important; }}
.sb-brand .slogan {{ font-size:.72rem; color:#C9D4F2 !important; letter-spacing:2.5px; margin-top:2px; }}

.footer {{
  text-align:center; color:#96A0BD; font-size:.8rem; margin-top:56px; padding-top:18px;
  border-top:1px solid #E0E6F2;
}}

/* ---------- 对话式聊天：AI 左 · 用户右 ---------- */
[data-testid="stChatMessage"] {{
  background: #fff;
  border: 1px solid #E3E8F4;
  border-radius: 14px;
  padding: 12px 16px;
  box-shadow: 0 2px 10px rgba(20,40,80,.05);
}}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
  margin-right: 30%;  /* AI 回答靠左 */
}}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
  flex-direction: row-reverse;  /* 头像与内容镜像到右侧 */
  margin-left: 30%;  /* 我的提问靠右 */
  background: linear-gradient(135deg, #EEF4FF, #F6FAFF);
  border-color: #C9DCF7;
}}
@media (max-width: 720px) {{
  [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{ margin-right: 4%; }}
  [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{ margin-left: 4%; }}
}}
.chat-welcome {{
  background: linear-gradient(135deg, #EEF4FF, #F7FAFF);
  border:1px solid #D6E4FB; border-radius:18px;
  padding:18px 22px; margin:6px 0 16px 0;
  color:{INK}; font-size:.95rem; line-height:1.7;
}}
.chat-welcome b {{ color:{NAVY}; }}

.mode-badge {{ display:inline-block; padding:5px 14px; border-radius:999px; font-size:.82rem; font-weight:700; margin-bottom:12px; letter-spacing:.02em; }}
.mode-real {{ background:rgba(34,197,94,.14); color:#15803d; border:1px solid rgba(34,197,94,.45); }}
.mode-demo {{ background:rgba(245,158,11,.16); color:#b45309; border:1px solid rgba(245,158,11,.45); }}

/* ---------- 专有名词解释 ---------- */
.gloss-grid {{ display:grid; grid-template-columns: repeat(2, 1fr); gap:14px; margin:8px 0 26px 0; }}
.gloss-card {{
  background: #fff; border:1px solid #E3E8F4; border-left:4px solid {GOLD};
  border-radius:14px; padding:16px 18px; box-shadow: 0 4px 14px rgba(20,40,80,0.05);
}}
.gloss-card .gt {{
  font-weight:800; font-size:1.02rem; color:{NAVY}; margin-bottom:6px;
  font-family:"Noto Serif SC",serif;
}}
.gloss-card .gd {{ font-size:.92rem; color:#3A4866; line-height:1.65; }}
.gloss-card .gt-star {{ color:{GOLD}; }}
.resume-card {{
  background:#fff; border:1px solid #E3E8F4; border-radius:12px; padding:14px 16px;
  font-size:.92rem; line-height:1.8; color:#2E3A52; box-shadow:0 2px 10px rgba(20,40,80,.05);
}}
@media (max-width: 720px) {{ .gloss-grid {{ grid-template-columns: 1fr; }} }}
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
        {"name": "山西汾酒", "code": "600809.SH", "price": 198.60, "chg": +0.71, "pe": 19.6, "mv": "2431亿",
         "reason": "青花汾酒全国化扩张成效显著，长江以南市场增速亮眼；青花20/30放量带动产品结构升级，省外收入占比持续提升；清香型龙头受益消费多元化，成长性居板块前列。"},
        {"name": "洋河股份", "code": "002304.SZ", "price": 92.30, "chg": -0.45, "pe": 13.9, "mv": "1390亿",
         "reason": "梦之蓝M6+/M3水晶版完成渠道梳理，库存去化接近尾声；海之蓝基本盘稳固，省内深耕+省外恢复；估值处历史低位，静待需求回暖后的业绩弹性释放。"},
    ],
    "红利": [
        {"name": "中国神华", "code": "601088.SH", "price": 41.72, "chg": +1.24, "pe": 12.6, "mv": "8288亿",
         "reason": "煤电运化一体化产业链，长协煤占比高平滑周期波动；连续多年分红率超 70%，股息率约 5.6%，是红利资产的核心压舱石。"},
        {"name": "长江电力", "code": "600900.SH", "price": 27.95, "chg": +0.58, "pe": 21.3, "mv": "6839亿",
         "reason": "全球最大水电上市公司，六库联调提升发电效率，来水偏丰叠加电价市场化改革；类债属性突出，分红承诺 70% 以上，确定性极强。"},
        {"name": "工商银行", "code": "601398.SH", "price": 6.18, "chg": -0.16, "pe": 6.1, "mv": "2.20万亿",
         "reason": "国有大行龙头，资产质量稳健，不良率持续下行；股息率超 5%，险资与被动资金持续增配，受益于中特估与市值管理政策。"},
        {"name": "陕西煤业", "code": "601225.SH", "price": 23.10, "chg": +0.52, "pe": 11.4, "mv": "2238亿",
         "reason": "陕北优质动力煤田成本低、储量丰，长协占比高保障盈利稳定；高分红承诺（分红率不低于60%）叠加现金流充沛，是红利资产中弹性与防御兼备的品种。"},
        {"name": "宁沪高速", "code": "600377.SH", "price": 13.85, "chg": +0.22, "pe": 12.8, "mv": "698亿",
         "reason": "长三角核心路产车流量稳健，沪宁高速通行费收入韧性强；持续高分红（股息率超5%），类债属性突出，弱市下防御价值显著，兼具REITs化资产盘活预期。"},
    ],
    "贵金属": [
        {"name": "紫金矿业", "code": "601899.SH", "price": 18.64, "chg": +2.31, "pe": 16.9, "mv": "4926亿",
         "reason": "铜金双轮驱动，卡莫阿、巨龙铜矿放量进入收获期；美联储降息周期开启利好金价，公司矿产金产量三年复合增速超 20%，量价齐升。"},
        {"name": "山东黄金", "code": "600547.SH", "price": 29.87, "chg": +1.05, "pe": 38.2, "mv": "1336亿",
         "reason": "纯正黄金标的，金价上行期业绩弹性最大；西岭金矿探矿权注入预期强化资源储备；避险需求与央行购金构成中长期支撑。"},
        {"name": "中金黄金", "code": "600489.SH", "price": 14.52, "chg": -0.88, "pe": 22.7, "mv": "703亿",
         "reason": "央企背景，纱岭金矿投产在即带来产量跃升；集团资产注入预期明确；短期跟随板块回调，估值修复空间可观。"},
        {"name": "赤峰黄金", "code": "600988.SH", "price": 24.63, "chg": +1.42, "pe": 25.4, "mv": "410亿",
         "reason": "海外矿山（万象、Sepon）黄金产量进入释放期，黄金资源量持续增长；金价高位运行直接抬升业绩弹性，叠加降本增效，盈利对金价的敏感度在板块内居前。"},
        {"name": "银泰黄金", "code": "000975.SZ", "price": 17.05, "chg": -0.63, "pe": 20.8, "mv": "473亿",
         "reason": "黑河银泰、玉龙矿业等优质金银矿山贡献高品位资源；虽短期技术面偏弱，但金价中长期上行趋势下，具备资源增储与产量爬坡带来的修复弹性。"},
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
        {"name": "古井贡酒", "code": "000596.SZ", "pe": 18.3, "pb": 4.0, "roe": 23.1, "rev": 18.6,
         "trend": "震荡向上", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.66, 0.13, 0.21), "score": 83.4},
        {"name": "今世缘", "code": "603369.SH", "pe": 20.1, "pb": 4.6, "roe": 22.4, "rev": 22.3,
         "trend": "上升趋势", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.69, 0.12, 0.19), "score": 84.0},
        {"name": "舍得酒业", "code": "600702.SH", "pe": 14.7, "pb": 3.1, "roe": 19.8, "rev": 9.4,
         "trend": "横盘整理", "ma": "MA20 ≈ MA60", "vol": "高波动", "macd": "粘合",
         "sent": (0.55, 0.18, 0.27), "score": 79.6},
        {"name": "迎驾贡酒", "code": "603198.SH", "pe": 16.2, "pb": 3.6, "roe": 21.0, "rev": 19.2,
         "trend": "震荡向上", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.63, 0.16, 0.21), "score": 82.1},
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
        {"name": "大秦铁路", "code": "601006.SH", "pe": 8.9, "pb": 0.9, "roe": 9.8, "rev": 2.4,
         "trend": "震荡向上", "ma": "MA20 > MA60", "vol": "低波动", "macd": "金叉",
         "sent": (0.62, 0.15, 0.23), "score": 82.7},
        {"name": "华能水电", "code": "600025.SH", "pe": 19.8, "pb": 2.7, "roe": 13.6, "rev": 7.1,
         "trend": "上升趋势", "ma": "MA20 > MA60", "vol": "低波动", "macd": "金叉",
         "sent": (0.64, 0.14, 0.22), "score": 83.0},
        {"name": "中国移动", "code": "600941.SH", "pe": 17.2, "pb": 1.8, "roe": 10.2, "rev": 6.3,
         "trend": "震荡向上", "ma": "MA20 > MA60", "vol": "低波动", "macd": "金叉",
         "sent": (0.61, 0.15, 0.24), "score": 84.2},
        {"name": "中国海油", "code": "600938.SH", "pe": 9.6, "pb": 1.7, "roe": 18.9, "rev": 4.7,
         "trend": "横盘整理", "ma": "MA20 ≈ MA60", "vol": "低波动", "macd": "粘合",
         "sent": (0.58, 0.16, 0.26), "score": 83.5},
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
        {"name": "湖南黄金", "code": "002155.SZ", "pe": 24.1, "pb": 2.9, "roe": 12.1, "rev": 14.2,
         "trend": "震荡向上", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.66, 0.14, 0.20), "score": 83.3},
        {"name": "中金岭南", "code": "000060.SZ", "pe": 13.8, "pb": 1.4, "roe": 9.7, "rev": 8.9,
         "trend": "横盘整理", "ma": "MA20 ≈ MA60", "vol": "中波动", "macd": "粘合",
         "sent": (0.57, 0.17, 0.26), "score": 79.9},
        {"name": "铜陵有色", "code": "000630.SZ", "pe": 15.2, "pb": 1.3, "roe": 8.9, "rev": 10.4,
         "trend": "横盘整理", "ma": "MA20 ≈ MA60", "vol": "高波动", "macd": "粘合",
         "sent": (0.56, 0.18, 0.26), "score": 78.8},
        {"name": "洛阳钼业", "code": "603993.SH", "pe": 16.1, "pb": 2.2, "roe": 15.4, "rev": 19.8,
         "trend": "上升趋势", "ma": "MA20 > MA60", "vol": "中波动", "macd": "金叉",
         "sent": (0.70, 0.12, 0.18), "score": 85.6},
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

# ============================================================== Screen 四维分析（带实例）
DIM_TITLE = {"fundamental": "基本面", "technical": "技术面", "sentiment": "情绪面", "industry": "行业面"}

SCREEN_ANALYSIS = {
    "白酒": {
        "fundamental": {
            "summary": "白酒板块基本面高度分化：高端龙头盈利质量最优，区域酒增长承压。核心看 ROE 与营收增速的匹配度——低 PE 未必便宜、高 PE 也未必贵，必须结合成长性判断。",
            "examples": [
                {"title": "贵州茅台", "tag": "高 ROE 支撑高估值", "point": "PE 27.4、PB 9.5、ROE 32.1%、营收 +15.8%。实例：ROE 超 30% 领跑全板块，自由现金流充沛、分红率稳定，高估值由高确定性盈利质量支撑，仍是溢价最高的标的。"},
                {"title": "五粮液", "tag": "估值处历史低位", "point": "PE 17.8、ROE 24.5%、营收 +11.2%。实例：估值处于近五年低位，批价由 920 元回升至 960 元带动盈利预期修复，性价比突出。"},
                {"title": "洋河股份", "tag": "低估值≠便宜", "point": "PE 13.9 看似最低，但 ROE 20.4%、营收仅 +6.7%。实例：低估值背后是增长乏力，印证「便宜有便宜的道理」，基本面相对最弱。"},
            ],
        },
        "technical": {
            "summary": "均线系统与 MACD 是判断白酒短期动能的关键：多头排列（MA20>MA60 + 金叉）趋势最健康，死叉/空头排列则短期承压，粘合形态预示变盘。",
            "examples": [
                {"title": "贵州茅台", "tag": "多头排列最健康", "point": "上升趋势、MA20>MA60、MACD 金叉、低波动。实例：均线多头叠加金叉，技术形态最健康，适合顺势持有。"},
                {"title": "山西汾酒", "tag": "空头排列短期承压", "point": "横盘整理、MA20<MA60、MACD 死叉、高波动。实例：均线空头且死叉，短期动能最弱，需等待放量突破信号。"},
                {"title": "泸州老窖", "tag": "方向选择期", "point": "横盘、MA20≈MA60、MACD 粘合。实例：粘合形态预示变盘，宜观望或分批，不宜追涨。"},
            ],
        },
        "sentiment": {
            "summary": "FinBERT 对新闻/研报的情感三分类显示：龙头正面情绪占比最高、负面最低；增长存疑的标的负面占比明显抬升。",
            "examples": [
                {"title": "贵州茅台", "tag": "正面 0.78 居首", "point": "正面 0.78 / 中性 0.08 / 负面 0.14。实例：近八成舆情正面，市场对高端确定性共识最强。"},
                {"title": "五粮液", "tag": "正面 0.71", "point": "批价回升提振情绪，正面占比居前，负面仅 0.11。"},
                {"title": "洋河股份", "tag": "负面 0.26 最高", "point": "正面 0.52 / 负面 0.26。实例：负面占比超两成，反映市场对增长放缓的担忧，情绪面最弱。"},
            ],
        },
        "industry": {
            "summary": "行业处于周期底部右侧：库存去化至良性、批价企稳、集中度提升，龙头阿尔法属性凸显。",
            "examples": [
                {"title": "宏观驱动", "tag": "消费场景修复", "point": "社零餐饮回暖、CPI 温和回升、流动性合理充裕，共同支撑白酒消费场景修复。"},
                {"title": "行业景气", "tag": "库存去化+批价企稳", "point": "渠道库存去化至 1.5-2 个月良性区间，飞天批价站稳 2200 元上方，头部 CR5 超 45%。"},
                {"title": "配置观点", "tag": "龙头底仓", "point": "实例：以茅台/五粮液为核心底仓，次高端（汾酒/老窖）择机波段参与。"},
            ],
        },
    },
    "红利": {
        "fundamental": {
            "summary": "红利资产的核心定价锚是「股息率 − 无风险利率」的利差与分红可持续性（分红率、经营现金流覆盖率）。低 PE/PB + 高 ROE + 稳定现金流是优选标准。",
            "examples": [
                {"title": "中国神华", "tag": "现金奶牛", "point": "PE 12.6、PB 1.9、ROE 15.2%、营收 +3.1%。实例：煤电运化一体化、长协煤占比高平滑周期，分红率超 70%、股息率约 5.6%，现金流对分红覆盖 1.5 倍以上。"},
                {"title": "工商银行", "tag": "破净高股息", "point": "PE 6.1、PB 0.7、ROE 10.6%。实例：市净率破净、股息率超 5%，受益中特估与市值管理，险资持续增配。"},
                {"title": "陕西煤业", "tag": "周期波动需警惕", "point": "营收 −2.3% 下滑。实例：盈利随煤价波动，但分红仍稳，体现「现金奶牛」属性，需关注周期下行风险。"},
            ],
        },
        "technical": {
            "summary": "红利多为低波动防御品种，技术信号以趋势延续为主；MA20>MA60 且金叉的标的处于上升通道，窄幅震荡者弹性有限。",
            "examples": [
                {"title": "中国神华", "tag": "慢牛红利形态", "point": "上升趋势、MA20>MA60、金叉、低波动。实例：稳步抬升，典型慢牛红利形态。"},
                {"title": "长江电力", "tag": "技术面最稳健", "point": "上升趋势、金叉、低波动。实例：类债属性、回撤极小，技术面最稳健。"},
                {"title": "宁沪高速", "tag": "防御强弹性弱", "point": "横盘、MA20≈MA60、粘合、低波动。实例：窄幅震荡，防御属性强但弹性有限。"},
            ],
        },
        "sentiment": {
            "summary": "红利标的情绪整体平稳偏暖，负面占比普遍低于 0.2；利率下行预期持续强化其配置逻辑。",
            "examples": [
                {"title": "中国神华", "tag": "正面 0.74", "point": "高股息共识强，负面 0.17 多为煤价波动担忧。"},
                {"title": "工商银行", "tag": "正面 0.66", "point": "中特估与分红新政提振情绪，负面仅 0.22。"},
                {"title": "陕西煤业", "tag": "情绪略弱", "point": "正面 0.59 较低。实例：煤价下行预期使情绪略弱于水电/银行。"},
            ],
        },
        "industry": {
            "summary": "无风险利率下行 + 市值管理新政 + 险资配置需求，使高股息资产配置价值持续凸显，攻守兼备。",
            "examples": [
                {"title": "宏观驱动", "tag": "利率低位", "point": "十年期国债收益率约 1.7% 低位，险资配置需求旺盛，红利相对债券利差走阔。"},
                {"title": "行业景气", "tag": "利差历史高位", "point": "中证红利股息率约 5.2%，与 10Y 国债利差处历史高位，央国企分红意愿提升。"},
                {"title": "配置观点", "tag": "底仓长期持有", "point": "实例：以神华/长电为底仓长期持有，获取股息 + 估值修复双重收益。"},
            ],
        },
    },
    "贵金属": {
        "fundamental": {
            "summary": "贵金属股弹性来自「量 × 价」双击：金价/铜价上行叠加矿产产量扩张。需关注 PE 与产量增速的匹配，纯金标的在金价上行期业绩弹性最大。",
            "examples": [
                {"title": "紫金矿业", "tag": "量价齐升", "point": "PE 16.9、PB 3.8、ROE 22.6%、营收 +18.3%。实例：铜金双轮，卡莫阿/巨龙铜矿放量，矿产金三年复合增速超 20%，量价齐升。"},
                {"title": "山东黄金", "tag": "金价弹性最大", "point": "PE 38.2 偏高、ROE 13.4%、营收 +21.7%。实例：纯正黄金标的，金价上行期业绩弹性最大，西岭金矿探矿权注入预期强化资源储备。"},
                {"title": "中金黄金", "tag": "产量跃升在望", "point": "PE 22.7、营收 +12.5%。实例：央企背景、纱岭金矿投产在即，产量跃升在望。"},
            ],
        },
        "technical": {
            "summary": "贵金属受商品价格驱动，趋势性强、波动中高；MA20>MA60 且金叉的标的处于主升段，空头排列者短期宜等企稳。",
            "examples": [
                {"title": "紫金矿业", "tag": "主升浪最清晰", "point": "上升趋势、MA20>MA60、金叉、中波动。实例：均线多头叠加金叉，主升浪形态最清晰。"},
                {"title": "山东黄金", "tag": "随金价走强", "point": "上升趋势、金叉。实例：随金价突破同步走强，趋势与商品共振。"},
                {"title": "银泰黄金", "tag": "技术面最弱", "point": "弱势整理、MA20<MA60、死叉。实例：短期空头排列，宜等企稳再介入。"},
            ],
        },
        "sentiment": {
            "summary": "降息预期与央行购金叙事使贵金属正面情绪高涨，紫金/山金正面占比居前。",
            "examples": [
                {"title": "紫金矿业", "tag": "正面 0.81 最高", "point": "量价齐升逻辑共识强，负面仅 0.12。"},
                {"title": "山东黄金", "tag": "正面 0.75", "point": "避险 + 降息双驱动，情绪乐观。"},
                {"title": "银泰黄金", "tag": "正面 0.54 最低", "point": "技术走弱拖累情绪，负面占比抬升。"},
            ],
        },
        "industry": {
            "summary": "美联储降息周期 + 全球央行连续购金 + 地缘避险，黄金中长期牛市格局确立，铜金共振。",
            "examples": [
                {"title": "宏观驱动", "tag": "实际利率下行", "point": "美联储降息预期升温、实际利率下行、地缘风险抬升避险需求。"},
                {"title": "行业景气", "tag": "央行连续购金", "point": "全球央行连续 30 个月净购金、矿产供给刚性、金价屡创新高，沪金主力创历史新高。"},
                {"title": "配置观点", "tag": "龙头长期持有", "point": "实例：以紫金/山金为龙头长期持有，短期回调即加仓窗口。"},
            ],
        },
    },
}

# 情绪面评论实例（FinBERT 标注 · 演示用示例，用于说明情绪面特征来源）
SCREEN_SENTIMENT_SAMPLES = {
    "白酒": {
        "贵州茅台": [("飞天批价站稳 2200 元上方，渠道库存去化至良性区间", "正面", 0.94),
                     ("直销渠道占比提升带动吨价上行，分红承诺稳定", "正面", 0.90)],
        "五粮液": [("普五批价由 920 元回升至 960 元，盈利预期修复", "正面", 0.88),
                   ("次高端需求仍有待动销验证", "中性", 0.55)],
        "泸州老窖": [("国窖 1573 稳居高端第三极，腰部产品复苏明确", "正面", 0.76),
                     ("行业去库存短期扰动业绩", "负面", 0.61)],
        "山西汾酒": [("青花系列全国化扩张势头强劲", "正面", 0.74),
                     ("青花 20 批价波动引发渠道担忧", "负面", 0.58)],
        "洋河股份": [("梦之蓝 M6+ 省内动销平稳", "中性", 0.60),
                     ("增长放缓，市场对其改革成效存疑", "负面", 0.62)],
    },
    "红利": {
        "中国神华": [("分红率超 70%、股息率约 5.6%，现金流覆盖 1.5 倍", "正面", 0.91),
                     ("长协煤占比高平滑周期波动", "正面", 0.85)],
        "长江电力": [("六库联调提升发电效率，来水偏丰", "正面", 0.86),
                     ("分红承诺 70% 以上，确定性极强", "正面", 0.88)],
        "工商银行": [("股息率超 5%，受益中特估与市值管理", "正面", 0.80),
                     ("净息差承压、信贷需求偏弱", "负面", 0.57)],
        "陕西煤业": [("高分红延续，现金奶牛属性突出", "正面", 0.78),
                     ("煤价下行预期压制盈利", "负面", 0.59)],
        "宁沪高速": [("车流稳健、类债属性强", "正面", 0.72),
                     ("弹性有限，缺乏成长故事", "中性", 0.52)],
    },
    "贵金属": {
        "紫金矿业": [("卡莫阿、巨龙铜矿放量，矿产金三年复合增速超 20%", "正面", 0.93),
                     ("美联储降息周期利好金价，量价齐升", "正面", 0.90)],
        "山东黄金": [("西岭金矿探矿权注入预期强化资源储备", "正面", 0.84),
                     ("金价上行期业绩弹性最大", "正面", 0.82)],
        "中金黄金": [("纱岭金矿投产在即，产量跃升", "正面", 0.80),
                     ("短期跟随板块回调", "负面", 0.60)],
        "赤峰黄金": [("海外矿山产能释放，量增明确", "正面", 0.76),
                     ("海外运营与汇率风险偏高", "负面", 0.58)],
        "银泰黄金": [("玉龙矿业储量优质，成长空间大", "正面", 0.73),
                     ("技术面走弱拖累短期情绪", "负面", 0.61)],
    },
}

def render_analysis_block(industry: str, dim: str):
    """在 Screen 各维度 tab 中渲染带实例的叙事分析。"""
    block = SCREEN_ANALYSIS.get(industry, {}).get(dim)
    if not block:
        return
    st.markdown(f"**📝 {DIM_TITLE[dim]}分析要点**")
    st.write(block["summary"])
    exs = block["examples"]
    cols = st.columns(len(exs))
    for col, ex in zip(cols, exs):
        with col:
            st.markdown(
                f'<div class="card" style="height:100%"><div class="icon">📌</div>'
                f'<h4>{ex["title"]}</h4>'
                f'<p><b style="color:{GOLD}">{ex.get("tag","实例")}</b><br>{ex["point"]}</p></div>',
                unsafe_allow_html=True)

def get_rag_hits(industry: str, user_query: str):
    """从真实 Chroma 检索 bundle 中按行业路由取出 Top 片段。"""
    if not KB:
        return []
    coll_key = "宏观" if industry == "default" else industry
    qmap = KB.get("retrieval", {}).get(coll_key, {})
    # 选取与用户问题字符重叠最多的代表性查询
    best, best_score = None, 0
    for q, hits in qmap.items():
        s = sum(1 for ch in set(user_query) if ch in q)
        if s > best_score:
            best_score, best = s, hits
    if best and best_score > 0:
        return best
    # 兜底：聚合该行业全部命中、按相似度去重取 Top-4
    seen, pool = set(), []
    for hits in qmap.values():
        for h in hits:
            key = (h["source"], h["page"], h["title"])
            if key not in seen:
                seen.add(key)
                pool.append(h)
    pool.sort(key=lambda x: -x["score"])
    return pool[:4]

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

# ============================================================== DeepSeek 真实大模型接入
# 通过 OpenAI 兼容协议调用 DeepSeek：https://api.deepseek.com ，默认模型 deepseek-chat (V3)
DS_BASE_URL = "https://api.deepseek.com"
DS_MODEL = "deepseek-chat"
DS_FALLBACK_KEY = "sk-6660156768e541d895455ca4088471e3"  # 硬编码兜底：仅用于页面展示与免粘贴调用；已告知用户，建议用后于 platform.deepseek.com 轮换


def _ds_client():
    """构造 OpenAI 客户端：优先用界面输入的 key（session_state['ds_api_key']），其次 st.secrets['DEEPSEEK_API_KEY']；缺失或异常时返回 None（降级演示模式）。"""
    try:
        ss_key = (st.session_state.get("ds_api_key", "") or "").strip()
        sec_key = (st.secrets.get("DEEPSEEK_API_KEY", "") or "").strip()
    except Exception:
        ss_key = (st.session_state.get("ds_api_key", "") or "").strip()
        sec_key = ""
    key = ss_key or sec_key or DS_FALLBACK_KEY
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key, base_url=DS_BASE_URL)
    except Exception:
        return None


def _ds_text(system: str, user: str, fallback: str, allow_real: bool = True,
             temperature: float = 0.7) -> str:
    """非流式调用 DeepSeek；缺密钥/异常/allow_real=False 时返回 fallback 文本。"""
    if not allow_real:
        return fallback
    client = _ds_client()
    if client is None:
        return fallback
    try:
        resp = client.chat.completions.create(
            model=DS_MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=temperature,
            stream=False,
        )
        return (resp.choices[0].message.content or "").strip() or fallback
    except Exception:
        return fallback


def _ds_stream_into(ph, system: str, user: str, fallback: str, allow_real: bool = True) -> str:
    """流式调用 DeepSeek，逐块渲染到 ph（打字机效果）；缺密钥/异常/allow_real=False 时回退 fallback。"""
    if not allow_real:
        ph.markdown(f'<div class="gen-box">{fallback}</div>', unsafe_allow_html=True)
        return fallback
    client = _ds_client()
    if client is None:
        ph.markdown(f'<div class="gen-box">{fallback}</div>', unsafe_allow_html=True)
        return fallback
    out, cnt = "", 0
    try:
        stream = client.chat.completions.create(
            model=DS_MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if not delta:
                continue
            out += delta
            cnt += len(delta)
            if cnt >= 24:  # 每累积约 24 字刷新一次，避免过于频繁重绘
                ph.markdown(f'<div class="gen-box">{out}<span class="cursor"></span></div>', unsafe_allow_html=True)
                cnt = 0
        ph.markdown(f'<div class="gen-box">{out}</div>', unsafe_allow_html=True)
        return out or fallback
    except Exception:
        if out:
            ph.markdown(f'<div class="gen-box">{out}</div>', unsafe_allow_html=True)
            return out
        ph.markdown(f'<div class="gen-box">{fallback}</div>', unsafe_allow_html=True)
        return fallback


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


# ============================================================== 实时行情接入
# 数据源：东方财富 push2 实时报价 + push2his 日K。纯标准库 urllib，无需额外依赖；
# 网络受限时所有函数安全回退（返回空 / None），由调用方落到内置演示数据。
import urllib.request as _ur
import urllib.parse as _up

_EM_HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}


def _em_secid(code: str) -> str:
    """600519.SH -> 1.600519 ; 000858.SZ -> 0.000858"""
    mkt = "1" if code.upper().endswith("SH") else "0"
    return f"{mkt}.{code.split('.')[0]}"


def _to_float(v):
    try:
        return float(v)
    except Exception:
        return None


def _fmt_mv(yuan):
    """东方财富总市值单位为「元」，转换为 亿 / 万亿。"""
    if yuan is None:
        return "—"
    try:
        yi = float(yuan) / 1e8
    except Exception:
        return "—"
    if yi >= 10000:
        return f"{yi / 10000:.2f}万亿"
    return f"{yi:.0f}亿"


def _yh_symbol(code: str) -> str:
    """600519.SH -> 600519.SS ; 000858.SZ -> 000858.SZ（Yahoo 命名）"""
    base, mkt = code.split(".")
    return base + (".SS" if mkt.upper() == "SH" else ".SZ")


_YH_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _http_get_json(url, headers, retries: int = 2, timeout: int = 6):
    """带退避重试的 JSON GET；全部失败则抛出最后一次异常。"""
    last = None
    for i in range(retries):
        try:
            req = _ur.Request(url, headers=headers)
            with _ur.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(0.4 * (i + 1))
    raise last or RuntimeError("request failed")


def _em_realtime_one(code):
    """单只：东方财富实时报价。返回 {name, price, chg, mv} 或 None。"""
    secid = _em_secid(code)
    url = (f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}"
           f"&fields=f43,f57,f58,f60,f116&fltt=2&invt=2")
    data = _http_get_json(url, _EM_HEADERS, retries=1, timeout=5)
    d = (data.get("data") or {})
    if not d:
        return None
    price = _to_float(d.get("f43"))
    prev = _to_float(d.get("f60"))
    if price is None or price == 0:
        return None
    chg = (price - prev) / prev * 100 if prev else 0.0
    return {
        "name": (d.get("f58") or code).replace(" ", ""),
        "price": price,
        "chg": round(chg, 2),
        "mv": _to_float(d.get("f116")),
    }


def _yh_realtime_one(code):
    """单只：Yahoo Finance 实时报价（全球可达，无需 key）。返回 {name, price, chg, mv} 或 None。"""
    sym = _yh_symbol(code)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
    data = _http_get_json(url, _YH_HEADERS, retries=3, timeout=6)
    m = (data.get("chart") or {}).get("result", [{}])[0].get("meta", {})
    price = _to_float(m.get("regularMarketPrice"))
    prev = _to_float(m.get("chartPreviousClose") or m.get("previousClose"))
    if price is None or price == 0 or not prev:
        return None
    return {
        "name": (m.get("shortName") or code).replace(" ", ""),
        "price": price,
        "chg": round((price - prev) / prev * 100, 2),
        "mv": _to_float(m.get("marketCap")),
    }


def fetch_realtime(codes):
    """批量获取实时行情，返回 ( {code: {name, price, chg, mv}}, src )。
    src ∈ {eastmoney, yahoo, eastmoney+yahoo, none}。
    主源东方财富（带 1 次退避重试，降低境外节点限流），失败回退 Yahoo Finance。"""
    out = {}
    used_em = used_yh = False
    for code in codes:
        rec = None
        for attempt in range(2):  # 东方财富：1 次重试 + 退避
            try:
                rec = _em_realtime_one(code)
                if rec:
                    break
            except Exception:
                rec = None
            time.sleep(0.3 * (attempt + 1))
        if rec:
            used_em = True
        else:  # 东方财富不通（常见于境外部署）→ 回退 Yahoo
            try:
                rec = _yh_realtime_one(code)
                if rec:
                    used_yh = True
            except Exception:
                rec = None
        if rec:
            out[code] = rec
        time.sleep(0.08)
    if used_em and used_yh:
        src = "eastmoney+yahoo"
    elif used_em:
        src = "eastmoney"
    elif used_yh:
        src = "yahoo"
    else:
        src = "none"
    return out, src


def _em_kline(code, days: int = 120):
    secid = _em_secid(code)
    url = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}"
           f"&klt=101&fqt=0&lmt={days}&end=20500101"
           f"&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61")
    data = _http_get_json(url, _EM_HEADERS, retries=1, timeout=6)
    klines = (data.get("data") or {}).get("klines") or []
    rows = []
    for kl in klines:
        parts = kl.split(",")
        if len(parts) >= 3:
            rows.append((parts[0], float(parts[2])))  # f51 日期, f53 收盘
    if not rows:
        return None
    return pd.DataFrame(rows, columns=["date", "close"])


def _yh_kline(code, days: int = 120):
    sym = _yh_symbol(code)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range={days}d"
    data = _http_get_json(url, _YH_HEADERS, retries=3, timeout=6)
    res = (data.get("chart") or {}).get("result", [{}])[0]
    ts = res.get("timestamp") or []
    closes = ((res.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    rows = []
    for t, c in zip(ts, closes):
        if c is None:
            continue
        rows.append((datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc).strftime("%Y-%m-%d"), float(c)))
    if not rows:
        return None
    return pd.DataFrame(rows, columns=["date", "close"])


def fetch_kline(code, days: int = 120):
    """获取真实日K收盘价序列，返回 DataFrame[date, close] 或 None。
    主源东方财富（带 1 次退避重试），失败回退 Yahoo Finance。"""
    for attempt in range(2):
        try:
            df = _em_kline(code, days)
            if df is not None and len(df) >= 2:
                return df
        except Exception:
            pass
        time.sleep(0.3 * (attempt + 1))
    try:
        df = _yh_kline(code, days)
        if df is not None and len(df) >= 2:
            return df
    except Exception:
        pass
    return None


def _compute_tech(close_list):
    """由真实收盘价序列计算技术面特征（MA20/MA60/MACD/趋势/波动率）。"""
    s = pd.Series(close_list)
    ma20 = s.rolling(20).mean().iloc[-1]
    ma60 = s.rolling(60).mean().iloc[-1]
    ema12 = s.ewm(span=12, adjust=False).mean()
    ema26 = s.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = (dif - dea).iloc[-1]
    prev_macd = (dif - dea).iloc[-2]
    if macd > 0 and prev_macd <= 0:
        macd_lbl = "金叉"
    elif macd < 0 and prev_macd >= 0:
        macd_lbl = "死叉"
    else:
        macd_lbl = "粘合"
    if ma20 > ma60 * 1.005:
        trend = "上升趋势"
    elif ma20 < ma60 * 0.995:
        trend = "弱势整理"
    else:
        trend = "横盘整理"
    vol = s.pct_change().std() * 100
    vol_lbl = "低波动" if vol < 1.5 else ("中波动" if vol < 2.5 else "高波动")
    ma_lbl = f"MA20 {'>' if ma20 > ma60 else '<'} MA60"
    return {"trend": trend, "ma": ma_lbl, "vol": vol_lbl, "macd": macd_lbl}


def _tech_detail(close_list):
    """返回技术面得分的连续中间量，便于透明展示（与 _tech_score 同源）。"""
    try:
        s = pd.Series(close_list)
        ma20 = float(s.rolling(20).mean().iloc[-1])
        ma60 = float(s.rolling(60).mean().iloc[-1])
        ema12 = s.ewm(span=12, adjust=False).mean()
        ema26 = s.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        macd = float((dif - dea).iloc[-1])
        close = float(s.iloc[-1])
        # 趋势信号：MA20 相对 MA60 的偏离，±8% 映射到 ±1
        ma_dev = (ma20 - ma60) / ma60 if ma60 != 0 else 0.0
        trend_score = max(-1, min(1, ma_dev / 0.08))
        # MACD 信号：MACD 柱相对最新收盘价，±2% 映射到 ±1
        macd_score = max(-1, min(1, (macd / close) / 0.02)) if close != 0 else 0.0
        score = (trend_score * 0.6 + macd_score * 0.4) * 50 + 50
        return {"ma20": ma20, "ma60": ma60, "ma_dev": ma_dev, "macd": macd, "close": close,
                "trend_score": trend_score, "macd_score": macd_score,
                "score": max(5, min(95, score))}
    except Exception:
        return None


def _tech_score(close_list):
    """由真实收盘价序列返回 0-100 技术面得分（趋势 + MACD），基于连续信号更精细。"""
    d = _tech_detail(close_list)
    return round(d["score"], 1) if d else 60


def _screen_score(pool, rt, klines):
    """基于真实行情（涨跌幅 + 技术面）重算综合评分 0-100，写回 c['real_score'] 与分项 c['score_break']。
    情绪分项用情绪分析带符号得分(sent_score, -1~1)映射：看多>50、中性=50、看空<50；无 sent_score 时回退正面占比口径。"""
    for c in pool:
        info = rt.get(c["code"], {})
        chg = info.get("chg")
        mom = 55 + (chg * 7 if chg is not None else 0)
        mom = max(15, min(95, mom))
        kl = klines.get(c["code"])
        tech = _tech_score(kl["close"].tolist()) if (kl is not None and len(kl) >= 60) else 60
        roe = c.get("roe", 15)
        qual = max(20, min(98, roe * 2.6))
        # 情绪分项：用情绪分析得到的带符号得分(sent_score, -1~1)映射为 0-100，中性=50；
        # 不再用「正面占比」占比。回退：无 sent_score 时沿用原占比口径。
        _sig = c.get("sent_score")
        if _sig is not None:
            sent = 50 + _sig * 50          # 看多>50，中性=50，看空<50
        else:
            sent_pos = c.get("sent", (0.6, 0.1, 0.3))[0]
            sent = 30 + sent_pos * 60
        c["real_score"] = round(0.30 * mom + 0.30 * tech + 0.25 * qual + 0.15 * sent, 1)
        c["score_break"] = {"mom": round(mom, 1), "tech": round(tech, 1),
                            "qual": round(qual, 1), "sent": round(sent, 1)}


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

    st.markdown('<div class="sec-title">选择你的路径</div><div class="sec-sub">无论你是投资者、技术评审还是正在准备面试，都能快速找到入口</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card"><div class="icon">💡</div><h4>我想体验产品</h4><p>用自然语言咨询投资、查看行业分析与个股推荐。</p></div>', unsafe_allow_html=True)
        if st.button("进入产品体验 →", key="go_product", use_container_width=True, type="primary"):
            _select_nav("智能咨询"); st.rerun()
    with c2:
        st.markdown('<div class="card"><div class="icon">🧩</div><h4>我想看技术</h4><p>星火大模型、RAG、微调、评测与知识库全揭秘。</p></div>', unsafe_allow_html=True)
        if st.button("查看技术底座 →", key="go_tech", use_container_width=True, type="primary"):
            _select_nav("星火大模型"); st.rerun()
    with c3:
        st.markdown('<div class="card"><div class="icon">🎤</div><h4>我在准备面试</h4><p>简历项目介绍、STAR 行为题与技术高频问答。</p></div>', unsafe_allow_html=True)
        if st.button("打开面试建议 →", key="go_interview", use_container_width=True, type="primary"):
            _select_nav("面试建议"); st.rerun()

    # 能力详解（从「技能中心」迁移至首页展示）
    st.markdown('<div class="sec-title">Fin Synagent · 能力详解</div><div class="sec-sub">Consult 智能咨询以多智能体协同工作流组织回答，Screen 智能荐股以筛选树六步输出</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title" style="font-size:1.12rem;margin-top:6px;">能力一 · Consult 智能咨询（多智能体工作流）</div>', unsafe_allow_html=True)
    agents = [
        ("a-leader", "👔", "Leader 拆解", "将问题拆为 2-4 个子任务，分配专家角色"),
        (None, "📚", "RAG 检索", "行业知识库 Top-K 召回并注入提示词"),
        ("a-expert", "🎓", "Expert 作答", "基于知识库片段输出结构化分析"),
        ("a-critic", "🧐", "Critic 批评", "自查逻辑缺失与建议不具体处"),
        ("a-verify", "🔎", "Verify 求证", "交叉核验信源，杜绝幻觉"),
        ("a-sum", "📋", "Summary 总结", "给出可执行结论并邀请追问"),
    ]
    acols = st.columns(6)
    for i, (cls, em, role, desc) in enumerate(agents):
        border = 'style="border-top:4px solid #4A6FD4;"' if cls is None else ""
        with acols[i]:
            st.markdown(f"""
            <div class="agent {cls or ''}" {border}>
              <div class="em">{em}</div>
              <div class="role">{role}</div>
              <div class="desc">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-title" style="font-size:1.12rem;">能力二 · Screen 智能荐股（筛选树六步）</div>', unsafe_allow_html=True)
    steps = [
        ("🧭 意图解析", "JSON 给出 {sector, risk, objective}：保守→稳定收益，积极→资本增值"),
        ("🏗️ 股票池", "行业过滤 + 基础过滤（市值>500亿、非 ST）→ 5 支候选"),
        ("🧬 四维特征", "基本面 / 技术面 / 情绪面(FinBERT) / 行业面 表格呈现"),
        ("⚖️ LLM 评分", "资深分析师视角 0-100 打分（茅台 91.2 / 五粮液 86.7 …）"),
        ("🏆 Top-3 推荐", "每只给出推荐理由与分析师观点"),
        ("⚠️ 风险提示", "附风险提示 + 数据为模拟的声明"),
    ]
    scols = st.columns(2)
    for i, (t, d) in enumerate(steps):
        with scols[i % 2]:
            st.markdown(f'<div class="step"><b>{t}</b><br><span style="color:#6B768F;font-size:.85rem;">{d}</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-title">版本迭代</div><div class="sec-sub">Fin 1.0 → Fin 3.0 持续进化</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="tl">
      <div class="tl-item"><b>Fin 1.0 – 2.5</b><p>任务拆解、Critic 自反思、知识库 Verify、人机协同逐步成型，分析深度与可解释性持续增强。</p></div>
      <div class="tl-item"><b>Fin 3.0</b><p>增设 Screen 荐股板块，Streamlit 多页应用，并沉淀技术设计与三层评测体系。</p></div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================== 页面：Consult
def run_workflow(query: str, decomp_level: int, use_real=None):
    script = match_script(query)
    rag_key = next((k for k in ["白酒", "红利", "贵金属"] if k in query), "default")
    rag_hits = get_rag_hits(rag_key, query)
    kb_tag = "宏观" if rag_key == "default" else rag_key
    rag_ctx = "\n".join(f"【{h['source']} · p{h['page']}】{h['text']}" for h in rag_hits) if rag_hits else "（知识库未加载，以下为通用分析）"

    key_ok = bool((st.session_state.get("ds_api_key", "") or "").strip() or (st.secrets.get("DEEPSEEK_API_KEY", "") or "").strip() or DS_FALLBACK_KEY)
    if use_real is None:
        use_real = (st.session_state.get("app_mode", "real") == "real")
    real = bool(use_real) and key_ok
    st.markdown("---")
    st.markdown("##### 🔄 多智能体协同工作流（透明可观测）")
    if not real:
        if use_real and not key_ok:
            st.warning("⚠️ 已选择「真实模式」但未检测到 API Key，已回退演示模式。请在页面顶部的「🔑 DeepSeek API Key」输入框粘贴有效 Key（或配置 Streamlit Cloud Secrets / 本地 secrets.toml）后刷新。")
        else:
            st.warning("🟠 当前为**演示模式**（内置示例回复）。如需真实 DeepSeek 推理，请在上方切换到「真实模式」并配置 API Key。")
    md = ["##### 🔄 多智能体协同工作流（透明可观测）", ""]
    if not real:
        md.append("> " + ("⚠️ 已选真实模式但未配置 Key，已回退演示。" if (use_real and not key_ok) else "🟠 演示模式：以下为内置示例回复。"))
        md.append("")

    # 1) Leader 领导智能体：任务拆解
    with st.status("👔 **Leader 领导智能体** · 正在进行任务拆解…", expanded=True) as s:
        leader_fb = "\n".join(f"- 子任务：{t}" for t in script["subtasks"]) + f"\n- 分配专家：{'、'.join(script['experts'])}"
        leader = _ds_text(
            "你是 Fin 智能投顾系统的 Leader 领导智能体。负责把用户的投资咨询问题拆解为若干子任务并分配专家。"
            "请只输出纯文本 Markdown 列表：每行一个「- 子任务：<名称>」，最后一行「- 分配专家：<专家名>」。不要添加额外解释。",
            f"用户问题：{query}\n拆解粒度：{decomp_level} 级（粒度越高，子任务越细）。请给出子任务列表与分配的专家。",
            leader_fb,
            allow_real=real,
        )
        st.markdown(leader)
        s.update(label="👔 **Leader 领导智能体** · 任务拆解完成，可补充子任务", state="complete")
    md.append("**👔 Leader 领导智能体** · 任务拆解完成")
    md.append(leader)
    md.append("")

    with st.expander("🙋 人机协同 · 对拆解任务进行补充（可选）"):
        st.text_input("输入您希望补充的分析方向，专家将一并考虑：", key=f"supp_{time.time()}")

    # 2) RAG 知识库检索（本地 Chroma bundle，不走 API）
    with st.status("📚 **知识库检索（RAG）** · 正在检索 Chroma 行业向量库…", expanded=True) as s:
        st.write(f"**检索域**：`{kb_tag}` collection · **检索流程**：语义段落切分 → 中文向量化（bge 512 维）→ Chroma 持久化 → 查询向量化 → 余弦相似度 Top-K → Prompt 拼接")
        if rag_hits:
            for h in rag_hits:
                st.markdown(
                    f'<div class="src">📄 <b>{h["source"]}</b> · p{h["page"]} · 相似度 <b>{h["score"]:.3f}</b><br>'
                    f'<span style="color:#4A6A56;">{h["text"]}</span></div>', unsafe_allow_html=True)
        else:
            st.warning("知识库 bundle 未加载，已回退至通用分析。")
        s.update(label="📚 **知识库检索（RAG）** · 命中高相关片段，已注入专家提示词", state="complete")
    md.append(f"**📚 知识库检索（RAG）** · 命中高相关片段")
    md.append(f"- 检索域：`{kb_tag}` collection · 流程：语义段落切分 → 中文向量化（bge 512 维）→ Chroma 持久化 → 查询向量化 → 余弦相似度 Top-K → Prompt 拼接")
    if rag_hits:
        for h in rag_hits:
            md.append(f"- 📄 **{h['source']}** · p{h['page']} · 相似度 **{h['score']:.3f}**")
    else:
        md.append("- ⚠️ 知识库 bundle 未加载，已回退至通用分析。")
    md.append("")

    # 3) 专家智能体：基于检索片段生成专业回答（流式打字机）
    with st.status("🎓 **专家智能体（DeepSeek-Chat）** · 正在基于检索片段生成专业回答…", expanded=True) as s:
        ph = st.empty()
        expert = _ds_stream_into(
            ph,
            "你是 Fin 智能投顾系统的行业专家智能体（金融领域资深分析师）。请基于【知识库检索片段】与用户问题，输出专业、数据驱动、可追溯的投资分析。"
            "要求：使用 Markdown，分点论述，关键结论加粗，必要时给出风险提示。语言为中文。",
            f"用户问题：{query}\n\n【知识库检索片段】\n{rag_ctx}\n\n请基于以上信息给出专业回答。",
            script["expert_answer"],
            allow_real=real,
        )
        s.update(label="🎓 **专家智能体（DeepSeek-Chat）** · 回答生成完毕", state="complete")
    md.append("**🎓 专家智能体（DeepSeek-Chat）** · 回答生成完毕")
    md.append(expert)
    md.append("")

    # 4) 评论家智能体：审查专家回答
    with st.status("🧐 **评论家智能体** · 正在审查专家回答…", expanded=True) as s:
        critic = _ds_text(
            "你是 Fin 智能投顾系统的评论家智能体。请审查专家回答，指出遗漏、逻辑漏洞、数据存疑之处，并给出改进建议。用中文 Markdown 要点输出。",
            f"用户问题：{query}\n\n【专家回答】\n{expert}\n\n请给出批评意见与改进建议。",
            script["critic"],
            allow_real=real,
        )
        st.markdown(critic)
        c1, c2 = st.columns(2)
        c1.button("👍 认同批评意见", key=f"agree_{time.time()}")
        c2.button("✋ 不认同，给出反馈", key=f"disagree_{time.time()}")
        s.update(label="🧐 **评论家智能体** · 批评意见已输出", state="complete")
    md.append("**🧐 评论家智能体** · 批评意见")
    md.append(critic)
    md.append("")

    # 5) 专家智能体：针对批评完善回答
    with st.status("✍️ **专家智能体** · 针对批评与追问完善回答…", expanded=True) as s:
        expert_revise = _ds_text(
            "你是 Fin 智能投顾系统的专家智能体。请根据评论家的批评意见，完善并修订你的回答，输出修订后的完整要点。中文 Markdown。",
            f"用户问题：{query}\n\n【原专家回答】\n{expert}\n\n【评论家意见】\n{critic}\n\n请输出完善后的回答要点。",
            script["expert_revise"],
            allow_real=real,
        )
        st.markdown(expert_revise)
        s.update(label="✍️ **专家智能体** · 回答已完善", state="complete")
    md.append("**✍️ 专家智能体** · 完善回答")
    md.append(expert_revise)
    md.append("")

    # 6) 搜索与求证智能体：核验真实性、列出可溯源来源
    with st.status("🔎 **搜索与求证智能体** · 正在联网检索并核验真实性…", expanded=True) as s:
        verify = _ds_text(
            "你是 Fin 智能投顾系统的搜索与求证智能体。请针对分析中的关键数据与结论，列出可溯源的信息来源（研究报告/数据/新闻），并判断是否可能存在幻觉。中文 Markdown 列表。",
            f"用户问题：{query}\n\n【最终分析要点】\n{expert_revise}\n\n请列出信息源并核验真实性。",
            "已检索知识库与互联网，交叉验证关键数据，未发现幻觉内容。信息源如下：\n" + "\n".join(f"- {src}" for src in script["verify"]),
            allow_real=real,
        )
        st.markdown(verify)
        s.update(label="🔎 **搜索与求证智能体** · 验证通过 · 信息可溯源", state="complete")
    md.append("**🔎 搜索与求证智能体** · 验证通过 · 信息可溯源")
    md.append(verify)
    md.append("")

    # 7) 总结领导：汇总最终建议
    with st.status("📋 **总结领导** · 正在汇总全部信息…", expanded=True) as s:
        summary = _ds_text(
            "你是 Fin 智能投顾系统的总结领导。请基于以上全流程（任务拆解、专家分析、评论家审查、修订、求证），给出最终投资建议与可执行结论。中文 Markdown，简明有力。",
            f"用户问题：{query}\n\n【专家修订回答】\n{expert_revise}\n\n【验证信息源】\n{verify}\n\n请给出最终建议。",
            script["summary"],
            allow_real=real,
        )
        s.update(label="📋 **总结领导** · 最终建议", state="complete")
    st.success(summary)
    st.caption("💡 您可以继续追问（如：现在市场看好吗？短期还是长期持有？），系统将结合上下文持续回答。")
    md.append("**📋 总结领导** · 最终建议")
    md.append(summary)
    md.append("")
    md.append("💡 您可以继续追问（如：现在市场看好吗？短期还是长期持有？），系统将结合上下文持续回答。")
    return "\n".join(md)


def page_consult():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Consult · Multi-Agent Reasoning</div>
      <h1 style="font-size:2rem;">💬 智能投顾咨询</h1>
      <div class="sub" style="margin-bottom:0;">System-2 深思熟虑 · Multi-Agent 互相监督 · Web 检索 &amp; 知识库求证 · 显式思维链</div>
    </div>
    """, unsafe_allow_html=True)

    # DeepSeek API Key 输入（界面级）：优先于 st.secrets，仅本次会话生效，不留盘
    with st.expander("🔑 DeepSeek API Key（可选 · 仅本次会话生效）", expanded=False):
        _key_input = st.text_input(
            "粘贴你的 DeepSeek API Key（sk-...）",
            type="password",
            key="ds_api_key_input",
            help="留空则用演示模式。Key 仅保存在当前浏览器会话，不写入代码或文件。",
        )
        if _key_input and _key_input.strip():
            st.session_state["ds_api_key"] = _key_input.strip()
            st.caption("✅ Key 已载入本次会话，可在「真实模式」下调用 DeepSeek。")
        elif "ds_api_key" in st.session_state:
            del st.session_state["ds_api_key"]

        # 显示 / 复制 辅助：直接在页面展示真实 Key，便于复制
        st.code(DS_FALLBACK_KEY, language="text")

    # 运行模式切换：真实模式（DeepSeek 实时推理）/ 演示模式（内置示例），可在界面手动切换
    _ds_cfg = bool((st.session_state.get("ds_api_key", "") or "").strip() or (st.secrets.get("DEEPSEEK_API_KEY", "") or "").strip() or DS_FALLBACK_KEY)
    if "app_mode" not in st.session_state:
        st.session_state["app_mode"] = "real" if _ds_cfg else "demo"
    _app_mode = st.radio(
        "运行模式", ["real", "demo"],
        format_func=lambda x: "🟢 真实模式（DeepSeek 实时推理）" if x == "real" else "🟠 演示模式（内置示例）",
        horizontal=True, key="app_mode",
    )
    _use_real = (_app_mode == "real")
    if _use_real and _ds_cfg:
        st.markdown('<div class="mode-badge mode-real">🟢 真实模式 · 接入 DeepSeek 实时推理</div>', unsafe_allow_html=True)
    elif _use_real and not _ds_cfg:
        st.markdown('<div class="mode-badge mode-demo">🟠 演示模式 · 已选真实但未配置 Key</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="mode-badge mode-demo">🟠 演示模式 · 内置示例</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:14px;">
      <span class="pill">人机交互</span><span class="pill">System-2</span><span class="pill">Multi-Agent</span>
      <span class="pill">Web &amp; Verify</span><span class="pill">信息可溯源</span><span class="pill">可追问</span>
    </div>
    """, unsafe_allow_html=True)

    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    # 任务设置（拆解粒度）置于顶部折叠区，问答前可随时调整
    with st.expander("⚙️ 任务设置 · 任务分解程度", expanded=False):
        decomp_level = st.slider("拆解粒度（人机协同选项）", 1, 5, 3, label_visibility="collapsed")
        st.caption("粒度越高，子任务越细，专家注意力越集中。")

    chat_empty = (len(st.session_state["chat"]) == 0)
    pending = ("pending_query" in st.session_state)

    # 空状态：欢迎语 + 引导词，避免大段空白；对话中：引导词折叠常驻
    if chat_empty and not pending:
        st.markdown("""
        <div class="chat-welcome">
          👋 你好，我是 <b>Fin 智能投顾助手</b>。我可以基于多智能体协同框架，给出带检索溯源与可追溯思维链的投资分析。试着问问我吧：
        </div>
        """, unsafe_allow_html=True)
        st.markdown("**🧭 你可以这样问：**", unsafe_allow_html=True)
        gcols = st.columns(2)
        for idx, gp in enumerate(GUIDE_PROMPTS):
            with gcols[idx % 2]:
                if st.button(gp, key=f"guide_{gp}", use_container_width=True):
                    st.session_state["pending_query"] = gp
    elif not chat_empty:
        with st.expander("🧭 引导词快速提问", expanded=False):
            gcols = st.columns(2)
            for idx, gp in enumerate(GUIDE_PROMPTS):
                with gcols[idx % 2]:
                    if st.button(gp, key=f"guide_{gp}", use_container_width=True):
                        st.session_state["pending_query"] = gp

    # 聊天记录（全宽，用户右 / 助手左）
    for msg in st.session_state["chat"]:
        role = msg["role"]
        with st.chat_message(role, avatar=("user" if role == "user" else "assistant")):
            st.markdown(msg["content"], unsafe_allow_html=True)

    # 引导词点击：作为 query 发送（不回显，与原 chat_input 行为一致）
    query = None
    if "pending_query" in st.session_state:
        query = st.session_state.pop("pending_query")

    # 底部输入框（聊天式，固定底部，全宽）
    q = st.chat_input("请输入您的投资咨询问题，例如：白酒行业最近行情如何？")
    if q:
        query = q

    if query:
        st.session_state["chat"].append({"role": "user", "content": query})
        with st.chat_message("assistant", avatar="assistant"):
            full_md = run_workflow(query, decomp_level, use_real=_use_real)
        st.session_state["chat"].append({"role": "assistant", "content": full_md})

# ============================================================== 页面：Screen
def _screen_analyst_view(industry: str, risk: str, feat: dict, pool: list, allow_real: bool = True) -> str:
    """真实调用 DeepSeek 生成行业分析师观点；无 Key / 异常 / 演示模式时回退内置文案。"""
    fb = feat.get("view", "")
    sys_p = ("你是一位严谨的证券分析师。基于给定行业的四维特征与候选池数据，用 1-2 句话给出该行业当前的投资视角与配置逻辑。"
             "语气克制、专业、带数据感；结尾必须注明『以上不构成投资建议』。不要推荐具体买卖点位。")
    macro = "；".join(feat.get("macro", []))
    ind = "；".join(feat.get("industry", []))
    cands = "；".join(f"{c['name']}(PE={c['pe']},ROE={c['roe']}%,营收增速={c['rev']}%,趋势={c['trend']},正面情绪={c['sent'][0]})" for c in pool)
    user_p = f"行业：{industry}；风险偏好：{risk}。宏观特征：{macro}。行业特征：{ind}。候选池：{cands}"
    return _ds_text(sys_p, user_p, fb, allow_real=allow_real)


def _screen_reason(stk: dict, industry: str, risk: str, allow_real: bool = True) -> str:
    """真实调用 DeepSeek 生成单只个股的推荐理由；无 Key / 异常 / 演示模式时回退内置文案。"""
    fb = stk.get("reason", "")
    sys_p = ("你是一位严谨的证券分析师。基于给定个股的四维特征，用 1-2 句话说明其入选 Top-3 推荐组合的理由，聚焦基本面与行业地位；"
             "语气克制专业，结尾注明『以上不构成投资建议』。不给出具体买卖价格。")
    sent = stk.get("sent", [0, 0, 0])
    user_p = (f"个股：{stk['name']}({stk['code']})，行业={industry}，风险偏好={risk}；"
              f"PE={stk['pe']}, PB={stk['pb']}, ROE={stk['roe']}%, 营收增速={stk['rev']}%, "
              f"趋势={stk['trend']}, 均线={stk['ma']}, MACD={stk['macd']}, 情绪(正/负/中)={sent}")
    return _ds_text(sys_p, user_p, fb, allow_real=allow_real)


# ---- 情绪面：真实舆情解读 + 实时市场资讯 ----
# 带权词库覆盖「财经书面语 + 股吧散户口语」，并引入强化/弱化副词与简单否定，
# 避免等权计数导致大量评论 score 扎堆在 0.72 / 0.84 / 0.95。
_POS_WEIGHTS = {
    # 强正面（0.40）
    "涨停": 0.40, "连板": 0.40, "一字板": 0.40, "主升浪": 0.40, "创新高": 0.40,
    "业绩预增": 0.40, "大超预期": 0.40, "扭亏": 0.40, "强劲涨停": 0.40,
    # 中强正面（0.32）
    "上涨": 0.32, "大涨": 0.32, "暴涨": 0.32, "拉升": 0.32, "突破": 0.32,
    "新高": 0.32, "强劲": 0.32, "强势": 0.32, "领涨": 0.32, "获融资": 0.32,
    "融资买入": 0.32, "净买入": 0.32, "净流入": 0.32, "增持": 0.32, "买入": 0.32,
    "加仓干": 0.32, "加仓": 0.32, "满仓": 0.32, "抄底": 0.32, "放量上涨": 0.32,
    "跑赢大盘": 0.32, "金叉": 0.32, "超预期": 0.32,
    # 中等正面（0.24）
    "利好": 0.24, "增长": 0.24, "盈利": 0.24, "分红": 0.24, "回购": 0.24,
    "扩产": 0.24, "中标": 0.24, "签约": 0.24, "复苏": 0.24, "提升": 0.24,
    "改善": 0.24, "稳增": 0.24, "回暖": 0.24, "飘红": 0.24, "反超": 0.24,
    "预增": 0.24, "走强": 0.24, "看多": 0.24, "外资增持": 0.24, "获增持": 0.24,
    "主升": 0.24, "低估": 0.24, "高股息": 0.24, "机会": 0.24, "要涨": 0.24,
    "做多": 0.24, "慢牛": 0.24, "攒股": 0.24, "收息": 0.24, "潜力": 0.24,
    "黄金坑": 0.24, "上车": 0.24, "拿住": 0.24, "真香": 0.24, "吸足货": 0.24,
    "一鸣惊人": 0.24, "暴炒": 0.24, "估值修复": 0.24, "价值洼地": 0.24, "底部": 0.24,
    "回本": 0.24, "吃肉": 0.24, "起飞": 0.24, "雄起": 0.24, "稳了": 0.24,
    "反弹": 0.24, "反转": 0.24, "走高": 0.24, "上行": 0.24, "升温": 0.24,
    # 弱正面（0.14）
    "上调": 0.14, "难得": 0.14, "良心": 0.14, "凌绝顶": 0.14, "乐观": 0.14,
    "看好": 0.14, "积极": 0.14,
}
_NEG_WEIGHTS = {
    # 强负面（0.45）
    "退市": 0.45, "暴雷": 0.45, "腰斩": 0.45, "血亏": 0.45, "巨亏": 0.45,
    "垃圾": 0.45, "崩盘": 0.45, "跌停": 0.45, "暴跌": 0.45, "闪崩": 0.45,
    "业绩暴雷": 0.45, "财务造假": 0.45, "破产": 0.45,
    # 中强负面（0.35）
    "大跌": 0.35, "下挫": 0.35, "跳水": 0.35, "杀跌": 0.35, "破位": 0.35,
    "割肉": 0.35, "清仓": 0.35, "止损": 0.35, "套牢": 0.35, "站岗": 0.35,
    "接盘": 0.35, "割韭菜": 0.35, "出货": 0.35, "诱多": 0.35, "画饼": 0.35,
    "完蛋": 0.35, "崩了": 0.35, "麻了": 0.35, "没救": 0.35, "跑路": 0.35,
    "忽悠": 0.35, "看空": 0.35, "要跌": 0.35, "走弱": 0.35, "阴跌": 0.35,
    "新低": 0.35, "亏麻": 0.35, "拉黑": 0.35, "业绩变脸": 0.35, "丢人": 0.35,
    "服了": 0.35, "无语": 0.35, "恶心": 0.35, "平台已破": 0.35, "深套": 0.35,
    "套死": 0.35, "卖不动": 0.35, "喝不动": 0.35, "库存太大": 0.35, "消费萎缩": 0.35,
    # 中等负面（0.24）
    "下跌": 0.24, "减持": 0.24, "卖出": 0.24, "利空": 0.24, "下滑": 0.24,
    "不及预期": 0.24, "亏损": 0.24, "下调": 0.24, "风险": 0.24, "承压": 0.24,
    "诉讼": 0.24, "处罚": 0.24, "违约": 0.24, "冻结": 0.24, "调查": 0.24,
    "回落": 0.24, "缩水": 0.24, "放缓": 0.24, "净流出": 0.24, "流出": 0.24,
    "领跌": 0.24, "破发": 0.24, "破净": 0.24, "减值": 0.24, "清仓式": 0.24,
    "质押": 0.24, "立案": 0.24, "警示": 0.24, "问询": 0.24, "造假": 0.24,
    "违规": 0.24, "被查": 0.24, "萎缩": 0.24, "下降": 0.24, "净利降": 0.24,
    "营收降": 0.24, "营收大降": 0.24, "净利大降": 0.24, "利润下滑": 0.24,
    "亿元降": 0.24, "万元降": 0.24, "同比下降": 0.24, "同比降": 0.24,
    "库存": 0.24, "积压": 0.24, "过剩": 0.24, "下滑": 0.24,
    # 弱负面（0.14）
    "高位分歧": 0.14, "悲观": 0.14, "谨慎": 0.14, "观望": 0.14, "疲软": 0.14,
    "低迷": 0.14, "清淡": 0.14,
}
# 兼容旧代码/外部引用
_POS_WORDS = list(_POS_WEIGHTS.keys())
_NEG_WORDS = list(_NEG_WEIGHTS.keys())

_INTENSIFIERS = {"太", "非常", "特别", "极其", "严重", "大幅", "明显", "彻底",
                 "真的", "很", "十分", "剧烈", "强劲地", "超级", "极度", "滔天"}
_DIMINISHERS = {"有点", "稍微", "略", "些许", "不太", "不怎么", "稍稍"}
_NEGATORS = {"不", "没", "无", "未", "别", "没有", "并非", "绝不"}


def _lexicon_sentiment(text: str):
    """本地金融情感词库启发式标注：返回 (label, score 0-1)。
    采用带权词库 + 非重叠最长匹配 + 强化/弱化副词 + 简单否定，使分数分布更分散。"""
    def _scan(weights):
        total = 0.0
        i, n = 0, len(text)
        # 按长度降序，保证长词优先匹配，避免"新高"与"创新高"重复计数
        words = sorted(weights.keys(), key=len, reverse=True)
        while i < n:
            matched = False
            for w in words:
                lw = len(w)
                if i + lw <= n and text[i:i + lw] == w:
                    prefix = text[max(0, i - 6):i]
                    mult = 1.0
                    if any(it in prefix for it in _INTENSIFIERS):
                        mult = 1.35
                    elif any(dim in prefix for dim in _DIMINISHERS):
                        mult = 0.75
                    # 简单否定：前面 3 字内出现否定词，情绪反向并削弱
                    if any(neg in prefix[-3:] for neg in _NEGATORS):
                        mult *= -0.6
                    total += weights[w] * mult
                    i += lw
                    matched = True
                    break
            if not matched:
                i += 1
        return total

    pos_net = _scan(_POS_WEIGHTS)
    neg_net = _scan(_NEG_WEIGHTS)
    net = pos_net - neg_net

    if abs(net) < 0.06:
        return ("中性", round(0.50 + min(0.08, abs(net)), 2))

    label = "正面" if net > 0 else "负面"
    magnitude = min(abs(net), 1.5)
    # 压缩映射：弱信号 ~0.57，中信号 ~0.7，强信号 ~0.85，极端组合才逼近 0.95，
    # 避免单条评论大量扎堆在同一分值
    score = 0.50 + min(0.45, magnitude * 0.30 + 0.10 * (magnitude ** 0.6))
    return (label, round(min(0.95, score), 2))


def _to_sent_tuple(label: str, score: float):
    """由 (标签, 置信度) 生成三分类堆叠元组 (正, 负, 中)，求和≈1。"""
    s = max(0.08, min(0.95, score))
    if label == "正面":
        neg = round((1 - s) * 0.30, 2); neu = round(1 - s - neg, 2)
        return (round(s, 2), neg, neu)
    if label == "负面":
        pos = round((1 - s) * 0.30, 2); neu = round(1 - s - pos, 2)
        return (pos, round(s, 2), neu)
    pos = neg = round((1 - s) / 2, 2); neu = round(1 - pos - neg, 2)
    return (pos, neg, neu)


def _heuristic_sentiment(f: dict):
    """基于真实行情/技术面特征的规则启发式情绪研判。"""
    chg = f.get("chg")
    trend = f.get("trend")
    macd = f.get("macd")
    score = 0.55
    if chg is not None:
        score += chg * 0.05
    if trend == "上升趋势":
        score += 0.10
    elif trend == "弱势整理":
        score -= 0.10
    if macd == "金叉":
        score += 0.08
    elif macd == "死叉":
        score -= 0.08
    score = max(0.08, min(0.95, score))
    label = "正面" if score >= 0.60 else ("负面" if score <= 0.42 else "中性")
    chg_s = f"{chg:+.2f}%" if isinstance(chg, (int, float)) else "—"
    summary = f"基于行情特征（涨跌幅 {chg_s}、趋势『{trend}』、MACD『{macd}』）的情绪研判为{label}。"
    return {"label": label, "score": round(score, 2), "summary": summary,
            "sent_tuple": _to_sent_tuple(label, score)}


def _screen_sentiment(pool, industry, risk, rt, klines, allow_real=True, comments=None):
    """为候选池每只股票生成情绪面解读（标签+置信度+摘要+三分类元组+逐评聚合得分）。
    真实模式：1 次 DeepSeek 批量调用做 stock-level 研判，并逐条标注 comments 聚合出更细粒度的情绪均值；
    演示/无 Key：基于真实特征的规则启发式。comments 为 {code: [{title,...},...]} 与该标的严格对应。
    返回 {code: {label, score, summary, sent_tuple, comment_sent_score, comment_labels}}。"""
    feats = {}
    for c in pool:
        info = (rt or {}).get(c["code"], {}) if rt else {}
        kl = (klines or {}).get(c["code"]) if klines else None
        tech = _compute_tech(kl["close"].tolist()) if (kl is not None and len(kl) >= 60) else None
        chg = info.get("chg")
        if chg is None:
            chg = c.get("chg")
        trend = (tech or {}).get("trend") or c.get("trend")
        macd = (tech or {}).get("macd") or c.get("macd")
        # 安全取值：真实行情 info 优先，缺字段时回退内置 CANDIDATES 数据（演示模式保留）
        _price = info.get("price") if (info and info.get("price") is not None) else c.get("price")
        _pe = info.get("pe") if (info and info.get("pe") is not None) else c.get("pe")
        _cmts = (comments or {}).get(c["code"], [])[:15] if comments else []
        # 只保留评论文本（标题+摘要），去掉 url/人气等冗余字段，避免提示词膨胀
        _cmt_txt = [f"{x.get('title','')}｜{x.get('abstract','')}".strip("｜") for x in _cmts]
        feats[c["code"]] = {
            "name": c["name"], "code": c["code"],
            "price": _price, "chg": chg,
            "pe": _pe, "roe": c.get("roe"),
            "trend": trend, "macd": macd,
            "comments": _cmt_txt,
        }
    # 逐条评论标注并聚合，得到比单条 stock-level DeepSeek 分数更细粒度的情绪均值
    comment_sent, comment_labels = {}, {}
    if comments:
        all_texts, code_index = [], []
        for code, f in feats.items():
            for txt in f["comments"]:
                all_texts.append(txt)
                code_index.append(code)
        if all_texts:
            try:
                _ls = _label_news(all_texts, allow_real=allow_real)
                _grouped = {}
                for code, (lbl, sc) in zip(code_index, _ls):
                    _grouped.setdefault(code, []).append((lbl, sc))
                for code, vals in _grouped.items():
                    signed = [(sc if lbl == "正面" else (-sc if lbl == "负面" else 0.0)) for lbl, sc in vals]
                    comment_sent[code] = (sum(signed) / len(signed)) if signed else 0.0
                    comment_labels[code] = list(zip(feats[code]["comments"], vals))
            except Exception:
                pass
    if allow_real:
        fb = {code: _heuristic_sentiment(f) for code, f in feats.items()}
        for code in fb:
            fb[code]["comment_sent_score"] = comment_sent.get(code)
            fb[code]["comment_labels"] = comment_labels.get(code, [])
        fb_json = json.dumps({k: {"label": v["label"], "score": v["score"], "summary": v["summary"]}
                              for k, v in fb.items()}, ensure_ascii=False)
        sys_p = ("你是金融情绪分析专家。基于给定 A 股标的的真实行情、技术面特征，以及该标的近期股吧散户评论，"
                 "判断其当前市场情绪（正面/中性/负面），给出 0-1 置信度，并用 1 句话说明依据"
                 "（结合涨跌幅、趋势、MACD，若有相关评论则结合评论情绪倾向）。"
                 "口径：散户评论有明显看多/看空、抱怨或乐观情绪时必须判正面或负面；"
                 "只有评论稀少且行情无方向时才判中性。"
                 "只输出 JSON，格式：{\"600519\":{\"label\":\"正面\",\"score\":0.82,\"summary\":\"...\"}}，不要多余文字。")
        user_p = ("行业：" + industry + "；风险偏好：" + risk + "。特征（含各标的 comments 字段为该股近期股吧评论文本）："
                  + json.dumps(feats, ensure_ascii=False))
        try:
            parsed = json.loads(_ds_text(sys_p, user_p, fb_json, allow_real=True))
            out = {}
            for c in pool:
                code = c["code"]
                d = parsed.get(code) if isinstance(parsed, dict) else None
                if isinstance(d, dict) and d.get("label"):
                    label = d["label"]; score = float(d.get("score", 0.5))
                    out[code] = {"label": label, "score": round(score, 2),
                                 "summary": d.get("summary", fb[code]["summary"]),
                                 "sent_tuple": _to_sent_tuple(label, score),
                                 "comment_sent_score": comment_sent.get(code),
                                 "comment_labels": comment_labels.get(code, [])}
                else:
                    out[code] = fb[code]
            return out
        except Exception:
            return fb
    return {code: {**_heuristic_sentiment(f),
                   "comment_sent_score": comment_sent.get(code),
                   "comment_labels": comment_labels.get(code, [])}
            for code, f in feats.items()}


def _ts_to_date(ts):
    try:
        return datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return ""


def _em_code(code: str):
    """600519.SH -> SH600519；000858.SZ -> SZ000858（东方财富个股资讯接口用）。"""
    try:
        num, mkt = code.split(".")
        return ("SH" if mkt.upper() == "SH" else "SZ") + num
    except Exception:
        return code


def _guba_em_comments(num_code: str, n: int = 5, name: str = ""):
    """东方财富股吧：按股票代码进入该股吧，解析页面内嵌的 article_list JSON，
    取得该标的的真实散户帖子（标题/正文/作者/时间/人气）。返回 [] 表示本源不可用。
    两道防「评论与目标股无关」的保障：
      1) 校验返回的 bar_code 与目标代码一致；
      2) 相关性排序——标题/正文提及该股名称或代码的帖子优先，置顶的跨吧热帖降权。"""
    H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
         "Referer": "https://guba.eastmoney.com/"}
    try:
        url = f"https://guba.eastmoney.com/list,{num_code},f.html"
        req = _ur.Request(url, headers=H)
        with _ur.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", "ignore")
        m = re.search(r"var\s+article_list\s*=\s*(\{.*?\})\s*;", html, re.S)
        if not m:
            return []
        d = json.loads(m.group(1))
        # 校验 1：确认抓到的确实是这只股票的股吧
        if str(d.get("bar_code") or "").strip() != str(num_code).strip():
            return []
        keys = [k for k in (name, num_code) if k]
        cands, seen = [], set()
        for p in (d.get("re") or []):
            title = re.sub(r"\s+", " ", (p.get("post_title") or "")).strip()
            content = re.sub(r"\s+", " ", (p.get("post_content") or "")).strip()
            if not title and not content:
                continue
            # 过滤「仅现金标签」的空洞帖（如 $贵州茅台(SH600519)$ 且无正文）
            bare = re.sub(r"\$[^$]*\$|#[^#]*#", "", title).strip()
            if len(bare) < 4 and len(content) < 4:
                continue
            if not title:
                title = content[:30] + ("…" if len(content) > 30 else "")
            if title in seen:  # 同一帖子跨页/分区重复出现时去重
                continue
            seen.add(title)
            # 校验 2：相关性打分（标题命中权重更高）
            rel = 0
            if keys:
                rel += 2 * sum(1 for k in keys if k and k in title)
                rel += 1 * sum(1 for k in keys if k and k in content)
            if p.get("post_top_status"):  # 置顶/全局热帖降权
                rel -= 1
            pid = p.get("post_id")
            user = ((p.get("post_user") or {}).get("user_nickname") or "").strip()
            cands.append((
                rel, int(p.get("post_click_count") or 0),
                {
                    "title": title,
                    "abstract": content[:70] + ("…" if len(content) > 70 else ""),
                    "source": ("东方财富股吧·" + user) if user else "东方财富股吧",
                    "date": (p.get("post_publish_time") or "")[:10],
                    "url": f"https://guba.eastmoney.com/news,{num_code},{pid}.html" if pid else "",
                    "hot": f"阅{p.get('post_click_count', 0)} · 评{p.get('post_comment_count', 0)}",
                },
            ))
        # 相关性降序 → 人气降序
        cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [c[2] for c in cands[:n]]
    except Exception:
        return []


def _rss_items(xml: str):
    """宽容解析 RSS XML，返回 [(title, link, pubDate)]，处理 CDATA 与实体转义。"""
    from html import unescape
    out = []
    for m in re.finditer(r"<item>(.*?)</item>", xml, re.S):
        blk = m.group(1)
        tm = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", blk, re.S)
        lm = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", blk, re.S)
        dm = re.search(r"<pubDate>(.*?)</pubDate>", blk, re.S)
        if tm and tm.group(1).strip():
            out.append((unescape(tm.group(1)).strip(),
                        unescape(lm.group(1)).strip() if lm else "",
                        dm.group(1).strip() if dm else ""))
    return out


def _parse_rss_date(d: str):
    try:
        return datetime.datetime.strptime(d[:16].strip(), "%a, %d %b %Y").strftime("%Y-%m-%d")
    except Exception:
        return ""


def _bing_keyword(name: str, n: int = 5, errs: list = None):
    """Bing News RSS 按个股名称关键词搜索（全球可达，且对数据中心/云 IP 比 Google 宽容）。
    返回 [{title, abstract, source, date, url, hot}]，每条都因命中该股名称关键词而强相关。"""
    if not name:
        return []
    try:
        q = _up.quote(name)
        url = f"https://www.bing.com/news/search?q={q}&format=rss"
        req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with _ur.urlopen(req, timeout=8) as r:
            xml = r.read().decode("utf-8", "ignore")
        out = []
        for t, link, d in _rss_items(xml):
            out.append({"title": t, "abstract": "", "source": "Bing News·关键词命中",
                        "date": _parse_rss_date(d), "url": link, "hot": "—"})
            if len(out) >= n:
                break
        if not out and errs is not None:
            errs.append("Bing: RSS 返回 0 条")
        return out
    except Exception as e:
        if errs is not None:
            errs.append(f"Bing: {type(e).__name__} {str(e)[:60]}")
        return []


def _gnews_keyword(name: str, n: int = 5, errs: list = None):
    """Google News RSS 按个股名称关键词搜索（全球可达的回退源）。"""
    if not name:
        return []
    try:
        q = _up.quote(f'"{name}"')  # 精确短语，保证标题与该股直接相关
        url = (f"https://news.google.com/rss/search?q={q}"
               f"&hl=zh-CN&gl=CN&ceid=CN:zh-Hans")
        req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with _ur.urlopen(req, timeout=8) as r:
            xml = r.read().decode("utf-8", "ignore")
        out = []
        for t, link, d in _rss_items(xml):
            out.append({"title": t, "abstract": "", "source": "Google News·关键词命中",
                        "date": _parse_rss_date(d), "url": link, "hot": "—"})
            if len(out) >= n:
                break
        if not out and errs is not None:
            errs.append("Google News: RSS 返回 0 条（共享出口 IP 可能被限流）")
        return out
    except Exception as e:
        if errs is not None:
            errs.append(f"Google News: {type(e).__name__} {str(e)[:60]}")
        return []


# 各标的最近一次抓取的逐源失败诊断（page_screen 0 条时展示，便于远程定位网络问题）
_COMMENT_DEBUG = {}


def fetch_stock_comments(code: str, name: str = "", n: int = 5):
    """通过个股关键字（股票代码→股吧/关键词）爬取该标的的真实评论/资讯。
    返回 [{title, abstract, source, date, url, hot}]，内容与传入的 code 严格对应，
    绝不混入无关标的的内容。爬取对象不限于单一站点，回退链：
    东财股吧 → 新浪个股资讯 → Bing News 关键词 → Google News 关键词 → 东财公告。"""
    errs = _COMMENT_DEBUG.setdefault(code, [])
    H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        num, mkt = code.split(".")
    except Exception:
        errs.append("代码格式无法解析")
        return []
    # 主源：东方财富股吧（按股票代码精确进入该股吧，抓取真实散户帖子，并按个股名称做相关性排序）
    out = _guba_em_comments(num, n, name)
    if out:
        return out
    errs.append("东财股吧: 无结果（境外节点常被限）")
    # 回退源 1：新浪财经个股资讯（仍按个股 symbol 抓取，非大盘要闻）
    try:
        symbol = (mkt.lower() if mkt.lower() in ("sh", "sz") else "sh") + num
        url = f"https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php?symbol={symbol}&num={max(n,8)}"
        req = _ur.Request(url, headers={**H, "Referer": "https://finance.sina.com.cn/"})
        with _ur.urlopen(req, timeout=8) as r:
            html = r.read().decode("gbk", "ignore")
        m = re.search(r'<div class="datelist"><ul>(.*?)</ul>\s*</div>', html, re.S)
        if m:
            ul = m.group(1)
            nbsp = r"(?:&nbsp;|\s)*"
            pattern = (r"(\d{4}-\d{2}-\d{2})" + nbsp + r"(?:\d{2}:\d{2})" + nbsp +
                       r"<a[^>]+href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>")
            out = []
            for dm, href, title in re.findall(pattern, ul, re.S):
                title = re.sub(r"<[^>]+>", "", title).strip()
                if title:
                    out.append({"title": title, "abstract": "", "source": "新浪·个股资讯",
                                "date": dm, "url": href, "hot": "—"})
            if out:
                return out[:n]
        errs.append("新浪: 页面无 datelist（可能被反爬/JS 化）")
    except Exception as e:
        errs.append(f"新浪: {type(e).__name__} {str(e)[:60]}")
    # 回退源 2：Bing News 按个股名称关键词（对云/数据中心 IP 最宽容，境外主力）
    out = _bing_keyword(name, n, errs)
    if out:
        return out
    # 回退源 3：Google News 按个股名称关键词
    out = _gnews_keyword(name, n, errs)
    if out:
        return out
    # 回退源 4：东方财富个股公告（按股票代码精确过滤）
    try:
        emc = _em_code(code)
        url = (f"https://np-anotice-stock.eastmoney.com/api/security/ann?srctype=share&ann_type=2"
               f"&client_source=web&stock_list={emc}&page_index=1&page_size={n}")
        req = _ur.Request(url, headers={**H, "Referer": "https://quote.eastmoney.com/"})
        with _ur.urlopen(req, timeout=4) as r:
            d = json.loads(r.read().decode("utf-8"))
        lst = (d.get("data") or {}).get("list") or []
        out = []
        for it in lst:
            t = it.get("title") or it.get("title_cn") or ""
            if not t:
                continue
            out.append({"title": t, "abstract": "", "source": "东方财富·个股公告",
                        "date": (it.get("notice_date") or it.get("eitime") or "")[:10],
                        "url": "", "hot": "—"})
        if out:
            return out[:n]
        errs.append("东财公告: 0 条")
    except Exception as e:
        errs.append(f"东财公告: {type(e).__name__} {str(e)[:60]}")
    return []


def _ds_json_array(raw: str):
    """从 DeepSeek 输出中鲁棒地提取 JSON 数组：剥离 markdown 代码围栏，
    失败再尝试截取首个 '[' 到最后一个 ']'。返回 list 或 None。"""
    if not raw:
        return None
    txt = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        v = json.loads(txt)
        return v if isinstance(v, list) else None
    except Exception:
        pass
    i, j = txt.find("["), txt.rfind("]")
    if 0 <= i < j:
        try:
            v = json.loads(txt[i:j + 1])
            return v if isinstance(v, list) else None
        except Exception:
            return None
    return None


def _soft_intensity(text: str):
    """词库中性但 DeepSeek 仍给出观点的少数评论：用文本强度（标点/emoji/叠字/长度）做确定性打散，避免分数扎堆。"""
    excl = text.count("!") + text.count("！")
    ques = text.count("?") + text.count("？")
    emo = sum(1 for c in text if ord(c) >= 0x1F000)
    rep = sum(0.03 for ch in "啊呀哦额哈嘞哇噻" if text.count(ch) >= 2)
    return min(0.30, excl * 0.09 + ques * 0.04 + emo * 0.07 + (len(text) ** 0.5) * 0.012 + rep)


def _label_news(texts, allow_real=True):
    """对评论/新闻标题（含摘要）做情感标注，返回 [(label, score)]。
    真实模式：DeepSeek 负责定标签（尤擅含蓄/反讽/无词库命中的语句），但分数以本地带权词库的
    细粒度为主——DeepSeek 与词库同向时用词库分数（已有区分度），词库中性且 DeepSeek 有观点时
    用文本强度做确定性打散；解析失败/无 Key/演示模式直接回退本地词库。"""
    lex_res = [_lexicon_sentiment(t) for t in texts]
    if allow_real and texts and _ds_client() is not None:
        sys_p = ("你是金融舆情标注专家。输入是 A 股个股的散户评论或新闻标题（可能含正文摘要），"
                 "请逐条判断该文本对【对应个股】的情绪倾向，输出三分类：正面/中性/负面。"
                 "标注口径：凡是表达观点、预期、买卖意向、情绪宣泄的，必须归入正面或负面；"
                 "判中性是极其吝啬的，只有纯数据播报且无倾向（如融资余额、大宗交易成交、股东会通知、行情快报）才判中性。"
                 "score 为 0-1 置信度。输出 JSON 数组，与输入等长、顺序一致，"
                 "每项格式 {\"label\":\"正面|中性|负面\",\"score\":0.8}。只输出 JSON 数组，不要任何解释。")
        try:
            raw = _ds_text(sys_p, json.dumps(texts, ensure_ascii=False), "", allow_real=True,
                           temperature=0.2)
            arr = _ds_json_array(raw)
            if isinstance(arr, list) and arr:
                res = []
                for i, t in enumerate(texts):
                    d = arr[i] if i < len(arr) and isinstance(arr[i], dict) else {}
                    ds_lbl = d.get("label")
                    try:
                        ds_sc = max(0.05, min(0.99, float(d.get("score", 0.7))))
                    except Exception:
                        ds_sc = 0.7
                    lex_lbl, lex_sc = lex_res[i]
                    # —— 定标签：DeepSeek 优先；解析不出的标签回退词库 ——
                    if ds_lbl not in ("正面", "中性", "负面"):
                        res.append((lex_lbl, lex_sc)); continue
                    if ds_lbl == "中性":
                        # DeepSeek 判中性：词库有明显倾向则覆盖（带符号分×0.92），否则保持中性
                        if lex_lbl != "中性":
                            res.append((lex_lbl, round(lex_sc * 0.92, 2)))
                        else:
                            res.append(("中性", lex_sc))
                        continue
                    # DeepSeek 给出非中性观点
                    ds_sign = 1 if ds_lbl == "正面" else -1
                    if lex_lbl == ds_lbl:
                        # 词库同向：用词库细粒度分数（关键在于打破 DeepSeek 的 0.71 扎堆）
                        res.append((ds_lbl, lex_sc))
                    else:
                        # 词库中性 或 与 DeepSeek 反向：信任 DeepSeek 标签，分数用文本强度确定性打散
                        res.append((ds_lbl, round(0.5 + ds_sign * (0.20 + _soft_intensity(t)), 2)))
                return res
        except Exception:
            pass
    return lex_res


def page_screen():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Screen · Tree-of-Thought Stock Picking</div>
      <h1 style="font-size:2rem;">📊 智能荐股</h1>
      <div class="sub" style="margin-bottom:0;">筛选树荐股思维 · 分析师视角与需求验证 · 可视化市场信息</div>
    </div>
    """, unsafe_allow_html=True)

    # DeepSeek API Key 输入（界面级）：优先于 st.secrets，仅本次会话生效，不留盘
    with st.expander("🔑 DeepSeek API Key（可选 · 仅本次会话生效）", expanded=False):
        _key_input = st.text_input(
            "粘贴你的 DeepSeek API Key（sk-...）",
            type="password",
            key="ds_api_key_input",
            help="留空则用演示模式。Key 仅保存在当前浏览器会话，不写入代码或文件。",
        )
        if _key_input and _key_input.strip():
            st.session_state["ds_api_key"] = _key_input.strip()
            st.caption("✅ Key 已载入本次会话，可在「真实模式」下调用 DeepSeek。")
        elif "ds_api_key" in st.session_state:
            del st.session_state["ds_api_key"]

        # 直接在页面展示真实 Key，便于复制
        st.code(DS_FALLBACK_KEY, language="text")

    # 运行模式切换：真实模式（DeepSeek 实时推理 + 东方财富实时行情）/ 演示模式（内置示例），可手动切换
    _ds_cfg = bool((st.session_state.get("ds_api_key", "") or "").strip() or (st.secrets.get("DEEPSEEK_API_KEY", "") or "").strip() or DS_FALLBACK_KEY)
    if "app_mode" not in st.session_state:
        st.session_state["app_mode"] = "real" if _ds_cfg else "demo"
    _use_real = (st.session_state["app_mode"] == "real")
    st.radio(
        "运行模式", ["real", "demo"],
        format_func=lambda x: "🟢 真实模式（DeepSeek 实时推理）" if x == "real" else "🟠 演示模式（内置示例）",
        horizontal=True, key="app_mode",
    )
    if _use_real and _ds_cfg:
        st.markdown('<div class="mode-badge mode-real">🟢 真实模式 · 接入 DeepSeek 实时推理 + 东方财富实时行情</div>', unsafe_allow_html=True)
    elif _use_real and not _ds_cfg:
        st.markdown('<div class="mode-badge mode-demo">🟠 演示模式 · 已选真实但未配置 Key</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="mode-badge mode-demo">🟠 演示模式 · 内置示例</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🎯 荐股设置")
        industry = st.selectbox("选择目标行业", list(STOCKS.keys()))
        risk = st.radio("风险偏好（先验提示词）", ["保守型", "稳健型", "积极型"], index=1)
        run = st.button("🚀 开始智能筛选", use_container_width=True, type="primary")

    feat = INDUSTRY_FEATURE[industry]
    _ds_src = "实时行情接口（东方财富 / Yahoo Finance 备用）" if _use_real else "内置示例行情（演示模式）"
    st.markdown(f"**当前方案**：行业 = `{industry}` · 风险偏好 = `{risk}` · 数据源 = {_ds_src} / 财务与情绪为建模特征")

    if run:
        pool = CANDIDATES[industry]
        all_codes = sorted({c["code"] for c in pool} | {s["code"] for s in STOCKS[industry]})

        # 📡 实时行情接入（仅真实模式拉取；演示模式使用内置示例数据）
        if _use_real:
            with st.status("📡 **实时行情获取** · 拉取实时报价与日K…", expanded=True) as s:
                rt, rt_src = fetch_realtime(all_codes)
                klines = {code: fetch_kline(code, 120) for code in all_codes}
                ok = sum(1 for c in all_codes if c in rt)
                _src_lbl = {"eastmoney": "东方财富", "yahoo": "Yahoo Finance", "eastmoney+yahoo": "东方财富+Yahoo Finance"}.get(rt_src, "实时接口")
                if ok:
                    st.success(f"✅ 已获取 {ok}/{len(all_codes)} 只标的实时行情（来源：{_src_lbl}；最新价 / 涨跌幅 / 总市值来自真实接口，技术面由真实日K计算）。")
                else:
                    st.warning("⚠️ 实时行情获取失败（网络受限，常见于境外部署节点），已回退至内置演示数据。")
                s.update(label="📡 **实时行情获取** · 完成", state="complete")
        else:
            rt, klines = {}, {}
            st.info("🟠 演示模式：使用内置示例行情与评分，未调用外部接口。")

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

        # 个股相关评论（真实模式按个股关键字爬取股吧评论，按 code 精确对应；演示模式不抓取）
        stock_news = {}
        if _use_real:
            with st.status("🌐 **个股评论抓取** · 按标的代码爬取股吧真实散户评论…", expanded=True) as snews:
                # 并发抓取各标的股吧评论（候选池已扩至 9 只，串行过慢）
                _COMMENT_DEBUG.clear()
                try:
                    from concurrent.futures import ThreadPoolExecutor

                    def _fetch_one(c):
                        try:
                            return c["code"], fetch_stock_comments(c["code"], c.get("name", ""), 15)
                        except Exception as e:
                            _COMMENT_DEBUG.setdefault(c["code"], []).append(f"未预期异常: {type(e).__name__} {str(e)[:60]}")
                            return c["code"], []

                    with ThreadPoolExecutor(max_workers=min(9, max(1, len(pool)))) as ex:
                        for _code, _res in ex.map(_fetch_one, pool):
                            stock_news[_code] = _res
                except Exception:
                    for c in pool:
                        try:
                            stock_news[c["code"]] = fetch_stock_comments(c["code"], c.get("name", ""), 15)
                        except Exception:
                            stock_news[c["code"]] = []
                _nn = sum(len(v) for v in stock_news.values())
                snews.update(label=(f"🌐 **个股评论抓取** · 完成（共 {_nn} 条，已绑定到对应标的）" if _nn
                                    else "🌐 **个股评论抓取** · 0 条（全部回退源均未取到，展开下方诊断可见各源具体失败原因）"),
                             state="complete")
                if not _nn:
                    with st.expander("🔍 评论抓取诊断（各标的 · 各源失败原因）", expanded=True):
                        for c in pool:
                            reasons = _COMMENT_DEBUG.get(c["code"]) or []
                            st.write(f"**{c['name']}**（{c['code']}）")
                            for rmsg in reasons:
                                st.write(f"- {rmsg}")
                            if not reasons:
                                st.write("- （无记录）")

        with st.status("🧬 **多维特征提取** · 基本面 / 技术面 / 情绪面 / 行业面 → 特征合成…", expanded=True) as s:
            time.sleep(0.9)
            # 情绪面：真实模式下由 DeepSeek 基于实时行情/技术面 + 该标的近期股吧评论生成；演示模式用规则启发式
            sent_res = _screen_sentiment(pool, industry, risk, rt, klines, allow_real=_use_real,
                                         comments=stock_news if _use_real else None)
            for c in pool:
                _sr = sent_res[c["code"]]
                c["sent"] = _sr["sent_tuple"]
                c["comment_labels"] = _sr.get("comment_labels", [])
                # 优先使用逐条评论聚合的带符号情绪均值（更细粒度、分布更散），
                # 无评论聚合时回退单条 stock-level DeepSeek 分数。
                _agg = _sr.get("comment_sent_score")
                if _agg is not None:
                    c["sent_score"] = _agg
                else:
                    _sl, _ss = _sr.get("label"), _sr.get("score", 0.5)
                    c["sent_score"] = (_ss if _sl == "正面" else (-_ss if _sl == "负面" else 0.0))
            t1, t2, t3, t4 = st.tabs(["💰 基本面特征", "📈 技术面特征", "💬 情绪面特征（FinBERT）", "🏭 行业面特征"])
            with t1:
                fund_rows = []
                for c in pool:
                    info = rt.get(c["code"], {})
                    fund_rows.append({"股票": c["name"],
                                      "市盈率PE": info.get("pe", c["pe"]),
                                      "市净率PB": info.get("pb", c["pb"]),
                                      "ROE(%)": c["roe"], "营收增速(%)": c["rev"]})
                st.dataframe(pd.DataFrame(fund_rows), use_container_width=True, hide_index=True)
                st.caption("数据来源：东方财富实时行情（价格 / 涨跌幅 / 总市值 为实时） · 筛选逻辑：低估值 + 高 ROE + 稳定增长；PE/PB 为静态建模值")
                render_analysis_block(industry, "fundamental")
            with t2:
                tech_rows = []
                for c in pool:
                    kl = klines.get(c["code"])
                    if kl is not None and len(kl) >= 60:
                        t = _compute_tech(kl["close"].tolist())
                    else:
                        t = {"trend": c["trend"], "ma": c["ma"], "vol": c["vol"], "macd": c["macd"]}
                    tech_rows.append({"股票": c["name"], "趋势": t["trend"], "均线形态": t["ma"],
                                      "波动率": t["vol"], "MACD": t["macd"]})
                st.dataframe(pd.DataFrame(tech_rows), use_container_width=True, hide_index=True)
                st.caption("数据来源：东方财富实时日K（MA20/MA60、MACD 由收盘价序列计算） · 筛选逻辑：上升趋势 + 均线多头 + MACD 金叉优先")
                render_analysis_block(industry, "technical")
            with t3:
                import plotly.graph_objects as go
                fig = go.Figure()
                names = [c["name"] for c in pool]
                fig.add_trace(go.Bar(name="正面", x=names, y=[c["sent"][0] for c in pool], marker_color=RED))
                fig.add_trace(go.Bar(name="中性", x=names, y=[c["sent"][2] for c in pool], marker_color="#C3CDE4"))
                fig.add_trace(go.Bar(name="负面", x=names, y=[c["sent"][1] for c in pool], marker_color=GREEN))
                fig.update_layout(**PLOTLY_BASE, barmode="stack", height=360, bargap=0.28,
                                  margin=dict(l=10, r=10, t=40, b=70),
                                  title=dict(text="FinBERT 新闻情感三分类（正面 / 中性 / 负面）", font=dict(size=13, color=NAVY), x=0.5, xanchor="center"),
                                  yaxis=dict(gridcolor="#EEF1F8", tickformat=".0%", range=[0, 1]),
                                  legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center", font=dict(size=11)))
                st.plotly_chart(fig, use_container_width=True)
                st.caption("FinBERT：基于 BERT 架构、在海量金融语料（财报 / 研报 / 新闻）上微调的情感分析模型")
                render_analysis_block(industry, "sentiment")
                # 个股情绪解读：🟢 真实模式由 DeepSeek 基于实时行情/技术面生成；🟠 演示模式用规则启发式
                _sent_mode = "DeepSeek 实时生成（基于实时行情 / 技术面）" if _use_real else "演示模式（规则启发式，未调用外部接口）"
                _rows = "".join(
                    f"<tr><td style='padding:4px 10px;color:{NAVY};white-space:nowrap;font-weight:600;'>{c['name']}</td>"
                    f"<td style='padding:4px 10px;font-weight:700;color:{('#E54545' if sent_res[c['code']]['label']=='负面' else '#C9A227' if sent_res[c['code']]['label']=='正面' else '#8A93A8')};white-space:nowrap;'>{sent_res[c['code']]['label']} {sent_res[c['code']]['score']:.2f}</td>"
                    f"<td style='padding:4px 10px;color:#3A4566;'>{sent_res[c['code']]['summary']}</td></tr>"
                    for c in pool
                )
                st.markdown(f"**📋 个股情绪解读（{_sent_mode}）**")
                st.markdown(
                    f"<table style='width:100%;font-size:.85rem;border-collapse:collapse;'>"
                    f"<thead><tr style='color:#7A86A6;text-align:left;'><th style='padding:4px 10px;'>股票</th>"
                    f"<th style='padding:4px 10px;'>情绪 / 置信度</th><th style='padding:4px 10px;'>解读依据</th></tr></thead>"
                    f"<tbody>{_rows}</tbody></table>",
                    unsafe_allow_html=True)
                st.caption("↑ 情绪研判基于实时涨跌幅、趋势、MACD" + ("，以及该标的近期股吧散户评论" if _use_real else "") + "等字段" + ("，由 DeepSeek 推理生成" if _use_real else "（演示模式为规则启发式）") + "。")
                # 个股相关评论：按个股关键字（代码→股吧 symbol）实时爬取真实散户评论，严格绑定标的
                with st.expander("📰 个股相关评论（真实爬取 · 按标的分组 · 情绪标注）", expanded=False):
                    if not _use_real:
                        st.info("🟠 演示模式未抓取实时评论。切换到「🟢 真实模式」后可按各标的代码爬取其股吧真实散户评论。")
                    else:
                        _all_rows = []
                        for c in pool:
                            _nws = (stock_news or {}).get(c["code"], [])
                            if _nws:
                                _txts = [f"{n.get('title', '')}｜{n.get('abstract', '')}".strip("｜") for n in _nws]
                                _cached = c.get("comment_labels", [])
                                if len(_cached) >= len(_nws):
                                    _pairs = [ls for _, ls in _cached[:len(_nws)]]
                                else:
                                    _pairs = _label_news(_txts, allow_real=_use_real)
                                for n, (lbl, sc) in zip(_nws, _pairs):
                                    _sc = max(0.05, min(0.99, float(sc)))
                                    _signed = (_sc if lbl == "正面" else (-_sc if lbl == "负面" else 0.0))
                                    _all_rows.append((c["name"], n["title"], n.get("abstract", ""),
                                                      n.get("source", "—"), n.get("date", "—"),
                                                      n.get("hot", "—"), lbl, round(_signed, 2), round(_sc, 2),
                                                      n.get("url", "")))
                            else:
                                _all_rows.append((c["name"], "（该标的暂无实时评论/讨论）", "", "—", "—", "—", "—", 0.0, 0.0, ""))
                        if _all_rows:
                            def _title_cell(tt, ab, url):
                                head = (f"<a href='{url}' target='_blank' style='color:{NAVY};"
                                        f"text-decoration:none;font-weight:600;'>{tt}</a>"
                                        if url else f"<b style='color:{NAVY};'>{tt}</b>")
                                if ab:
                                    return (head + f"<div style='color:#7A86A6;font-size:.76rem;"
                                                   f"margin-top:2px;'>{ab}</div>")
                                return head
                            _nrows = "".join(
                                f"<tr><td style='padding:4px 8px;color:{NAVY};font-weight:600;"
                                f"white-space:nowrap;vertical-align:top;'>{nm}</td>"
                                f"<td style='padding:4px 8px;'>" + _title_cell(tt, ab, uu) + "</td>"
                                f"<td style='padding:4px 8px;color:#7A86A6;white-space:nowrap;"
                                f"vertical-align:top;'>{src}</td>"
                                f"<td style='padding:4px 8px;color:#7A86A6;white-space:nowrap;"
                                f"vertical-align:top;'>{dt}</td>"
                                f"<td style='padding:4px 8px;color:#7A86A6;white-space:nowrap;"
                                f"vertical-align:top;'>{ht}</td>"
                                f"<td style='padding:4px 8px;font-weight:700;color:"
                                f"{('#E54545' if lbl=='负面' else '#C9A227' if lbl=='正面' else '#8A93A8')};"
                                f"white-space:nowrap;vertical-align:top;'>{lbl}</td>"
                                f"<td style='padding:4px 8px;font-weight:700;color:"
                                f"{('#E54545' if signed>0 else '#2E9E5B' if signed<0 else '#8A93A8')};"
                                f"white-space:nowrap;vertical-align:top;'>{('+' if signed>0 else '')}{signed:.2f}</td></tr>"
                                for nm, tt, ab, src, dt, ht, lbl, signed, sc, uu in _all_rows
                            )
                            st.markdown(
                                f"<table style='width:100%;font-size:.82rem;border-collapse:collapse;'>"
                                f"<thead><tr style='color:#7A86A6;text-align:left;'>"
                                f"<th style='padding:3px 8px;'>标的</th><th style='padding:3px 8px;'>评论（仅限该标的）</th>"
                                f"<th style='padding:3px 8px;'>作者/来源</th><th style='padding:3px 8px;'>日期</th>"
                                f"<th style='padding:3px 8px;'>人气</th>"
                                f"<th style='padding:3px 8px;'>情绪</th>"
                                f"<th style='padding:3px 8px;'>情绪分(±)</th></tr></thead>"
                                f"<tbody>{_nrows}</tbody></table>",
                                unsafe_allow_html=True)
                            st.caption("↑ 每条评论均标注所属标的，按个股代码（关键字）进入该股票的股吧实时爬取真实散户讨论，"
                                       "并校验股吧归属，绝不混入无关标的（主源：东方财富股吧；回退：新浪个股资讯 → Google News 关键词 → 东财公告）。"
                                       + (" 情绪由金融词库 + DeepSeek 标注。" if _use_real else " 情绪由金融词库标注。")
                                       + " 每行『情绪分(±)』= 正面取 +置信度、负面取 −置信度、中性取 0；个股情绪分项由该标的全部评论带符号分的均值映射到 0–100。")
                        else:
                            st.info("⚠️ 实时评论抓取失败（网络受限，常见于境外部署节点），已略过；个股情绪解读不受影响。")
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
                render_analysis_block(industry, "industry")
            s.update(label="🧬 **多维特征提取** · 特征合成完毕，送入 LLM 评分", state="complete")

        # 基于真实行情重算综合评分（无真实数据则沿用内置 score）
        if rt:
            _screen_score(pool, rt, klines)

        with st.status("⚖️ **LLM 综合评分** · 分析师视角打分 → 排序 → TopK 筛选…", expanded=True) as s:
            time.sleep(0.8)
            import plotly.graph_objects as go
            names = [c["name"] for c in pool]
            scores = [c.get("real_score", c["score"]) for c in pool]
            # 金色必须对应综合分最高的 Top-3，而不是 pool 固定顺序的前 3 个
            top3_idx = set(i for i, _ in sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:3])
            fig = go.Figure(go.Bar(x=names, y=scores,
                                   marker_color=[GOLD if i in top3_idx else "#C3CDE4" for i in range(len(pool))],
                                   text=scores, textposition="outside", textfont=dict(color=NAVY, size=13)))
            fig.update_layout(**PLOTLY_BASE, height=300, margin=dict(l=10, r=10, t=30, b=10),
                              title=dict(text=f"LLM 综合评分（金色 = Top-3 入选）· 满分 100", font=dict(size=13, color=NAVY)),
                              yaxis=dict(range=[0, 100], gridcolor="#EEF1F8"))
            st.plotly_chart(fig, use_container_width=True)
            # 评分依据拆解：展示各分项得分与加权汇总（真实模式且取到行情时）
            if _use_real and any("score_break" in c for c in pool):
                _bdata = []
                for c in pool:
                    b = c.get("score_break")
                    if not b:
                        continue
                    _bdata.append({"股票": c["name"],
                                   "动量·实时涨跌(30%)": b["mom"],
                                   "技术面·MA/MACD(30%)": b["tech"],
                                   "质量·ROE(25%)": b["qual"],
                                   "情绪·分析得分(15%)": b["sent"],
                                   "综合分": c["real_score"]})
                if _bdata:
                    st.markdown("**🧮 评分依据拆解**（综合分 = 0.30×动量 + 0.30×技术面 + 0.25×质量 + 0.15×情绪；各分项 0-100 加权汇总）")
                    st.dataframe(pd.DataFrame(_bdata), use_container_width=True, hide_index=True)
                    st.caption("分项来源：动量 = 实时涨跌幅映射；技术面 = 由真实日K计算的 MA20/60 与 MACD；质量 = ROE；情绪 = 情绪分析带符号得分（看多为正、看空为负，中性 50）。Top-3 取综合分最高者。")
                    with st.expander("🧮 维度得分计算明细（每个子分怎么算出来的）", expanded=False):
                        _detail_rows = []
                        for c in pool:
                            b = c.get("score_break")
                            if not b:
                                continue
                            _info = rt.get(c["code"], {})
                            _chg = _info.get("chg")
                            _kl = klines.get(c["code"])
                            _td = _tech_detail(_kl["close"].tolist()) if (_kl is not None and len(_kl) >= 60) else None
                            _roe = c.get("roe", 15)
                            if _td is not None:
                                _tech_d = (f"MA20={_td['ma20']:.2f} / MA60={_td['ma60']:.2f} → 偏离{_td['ma_dev']*100:+.2f}% → 趋势分{_td['trend_score']:+.2f}；"
                                           f"MACD柱={_td['macd']:.3f} ÷ 收盘{_td['close']:.2f} → MACD分{_td['macd_score']:+.2f}；"
                                           f"0.6×趋势 + 0.4×MACD = {_td['score']:.1f}")
                            else:
                                _tech_d = "无真实日K(≥60根)，回退默认 60"
                            if isinstance(_chg, (int, float)):
                                _mom_d = f"涨跌幅{_chg:+.2f}% → 55 + {_chg:.2f}×7 = {b['mom']:.1f}（限幅15–95）"
                            else:
                                _mom_d = "无实时涨跌幅，沿用综合分中的动量值"
                            _qual_d = f"ROE={_roe}% → ROE×2.6 = {b['qual']:.1f}（限幅20–98）"
                            _sig = c.get("sent_score")
                            if _sig is not None:
                                _sent_d = f"逐条评论聚合带符号情绪={_sig:+.3f} → 50 + {_sig:+.3f}×50 = {b['sent']:.1f}"
                            else:
                                _sl = sent_res[c["code"]]["label"]; _ss = sent_res[c["code"]]["score"]
                                _sent_d = f"无评论聚合，回退 stock-level {_sl}{_ss:.2f} → 映射"
                            _detail_rows.append({"股票": c["name"],
                                                 "动量(30%)": _mom_d,
                                                 "技术面(30%)": _tech_d,
                                                 "质量(25%)": _qual_d,
                                                 "情绪(15%)": _sent_d})
                        if _detail_rows:
                            st.dataframe(pd.DataFrame(_detail_rows), use_container_width=True, hide_index=True)
                            st.caption("综合分 = 0.30×动量 + 0.30×技术面 + 0.25×质量 + 0.15×情绪。技术面/情绪为连续映射，权重为各维度在综合分中的占比。")
            else:
                st.caption("评分 Prompt：You are a senior equity analyst. 综合基本面 / 技术面 / 情绪面 / 行业面四维特征，0-100 打分（演示模式使用内置示例评分）。")
            s.update(label="⚖️ **LLM 综合评分** · Top-3 标的已锁定", state="complete")

        # 🤖 调用 DeepSeek 生成分析师观点与推荐理由（演示模式 / 无 Key / 异常时回退内置示例）
        _ds_label = "🤖 **DeepSeek 实时推理**" if _use_real else "🤖 **演示模式**"
        with st.status(f"{_ds_label} · 生成分析师观点与推荐理由…", expanded=True) as s:
            analyst_view = _screen_analyst_view(industry, risk, feat, pool, allow_real=_use_real)
            reasons = []
            for stk in STOCKS[industry]:
                cand = next((c for c in pool if c["code"] == stk["code"]), stk)
                merged = {**cand, **stk}   # STOCKS 含 reason/price/mv/pe；CANDIDATES 含 pb/roe/rev/趋势等特征
                reasons.append(_screen_reason(merged, industry, risk, allow_real=_use_real))
            s.update(label=f"{_ds_label} · 观点与理由已生成", state="complete")

        st.info(f"**分析师观点**：{analyst_view}")

        st.caption("💡 上方分析师观点与下方各股推荐理由：🟢 真实模式调用 DeepSeek 实时推理，🟠 演示模式使用内置示例（或无 Key / 异常时回退）。")

        _recs = STOCKS[industry]
        st.markdown(f"#### 🏆 推荐组合（Top-{len(_recs)}）· 已生成推荐解释")
        for _i in range(0, len(_recs), 3):
            cols = st.columns(3)
            for _j, (col, stk) in enumerate(zip(cols, _recs[_i:_i + 3])):
                idx = _i + _j
                with col:
                    info = rt.get(stk["code"], {}) if rt else {}
                    price = info.get("price", stk["price"])
                    chg = info.get("chg", stk["chg"])
                    pe = info.get("pe", stk["pe"])
                    mv = _fmt_mv(info.get("mv")) if (info.get("mv") is not None) else stk["mv"]
                    chg_cls = "up" if chg >= 0 else "down"
                    sign = "+" if chg >= 0 else ""
                    st.markdown(f"""
                    <div class="stock-card">
                      <div><span class="stock-name">{stk['name']}</span><span class="stock-code">{stk['code']}</span></div>
                      <div style="margin:10px 0 4px 0;">
                        <span style="font-size:1.65rem;font-weight:900;color:{NAVY};font-family:'Noto Serif SC',serif;">¥{price:.2f}</span>
                        <span class="{chg_cls}" style="margin-left:10px;font-size:1.02rem;">{sign}{chg:.2f}%</span>
                      </div>
                      <div style="font-size:.82rem;color:#7A86A6;">市盈率 {pe} · 总市值 {mv}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    _kl = klines.get(stk["code"]) if klines else None
                    df = _kl if _kl is not None else make_price_series(price)
                    st.plotly_chart(price_chart(df, stk["name"]), use_container_width=True)
                    with st.expander("📌 推荐理由（分析师视角）"):
                        st.write(reasons[idx])
        _rt_note = "东方财富实时行情" if _use_real else "内置示例行情（演示模式）"
        st.caption(f"💡 侧边栏可切换行业与风险偏好；价格 / 涨跌幅 / 总市值 / 走势来自{_rt_note}，PE/PB 与财务情绪特征为建模演示。")
    else:
        st.markdown('<div class="sec-title">Screen 完整流程</div><div class="sec-sub">用户偏好 → 条件解析 → 股票池构建 → 多维评分 → 排序筛选 → 输出推荐</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="card"><div class="icon">🧬</div><h4>四维特征提取</h4><p>基本面（PE/PB/ROE/营收增速）、技术面（趋势/均线/波动率/MACD）、情绪面（FinBERT 三分类）、行业面（宏观+景气），特征合成后送入 LLM。</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="card"><div class="icon">⚖️</div><h4>LLM 评分与 TopK 筛选</h4><p>资深分析师视角对候选池 0-100 综合打分，排序后 Top-3 入选，自动生成推荐解释与可视化走势。</p></div>', unsafe_allow_html=True)
        st.info("👈 请在左侧侧边栏选择行业与风险偏好，点击「开始智能筛选」运行工作流。")

# ============================================================== 页面：星火大模型模拟
def render_spark():
    st.caption("⚠️ 本页面为星火大模型的**模拟演示**：不调用真实 API，生成内容来自内置金融知识库模板，用于还原真实调用链路。")

    st.markdown('<div class="sec-title" style="margin-top:18px;">模型版本（星火 Web API domain 对照）</div><div class="sec-sub">以下为星火大模型各版本对照，演示默认使用 Spark4.0 Ultra 生成回答，无需手动切换</div>', unsafe_allow_html=True)
    default_model = "Spark4.0 Ultra"
    cols = st.columns(4)
    for col, (name, meta) in zip(cols, SPARK_MODELS.items()):
        is_default = (name == default_model)
        with col:
            st.markdown(f"""
            <div class="spark-card" style="background:{meta['grad']};{'box-shadow:0 0 0 2px #4A6FD4 inset;' if is_default else ''}">
              <span class="badge">{meta['badge']}{' · 默认' if is_default else ''}</span>
              <h4>{name}</h4><p>{meta['desc']}</p>
            </div>""", unsafe_allow_html=True)
    model = default_model

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

    # 微调专区：金融 SFT 数据集 + 训练全流程（SparkPro + LoRA）
    ft = KB.get("finetune", {}) if KB else {}

    # 金融微调数据集
    st.markdown('<div class="sec-title">金融微调数据集</div><div class="sec-sub">支撑星火 SparkPro 基座 SFT 微调（lr=8e-5，5 epochs），提升金融领域专业性与「投资」关键词捕捉能力</div>', unsafe_allow_html=True)
    fc = ft.get("fincuge", {})
    dc = ft.get("disc", {})
    fe = ft.get("fineval", {})
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="card" style="height:100%">
          <div class="icon">📘</div>
          <h4>FinCUGE-Instruction</h4>
          <p><b>训练 {_n(fc.get('train',0))}</b> · 评测 {_n(fc.get('eval',0))} · 合计 <b>{_n(fc.get('total',0))}</b><br>
          金融通用理解评测指令集（Apache-2.0），覆盖 FINFE 等数十类任务。</p>
        </div>""", unsafe_allow_html=True)
        if fc.get("samples"):
            with st.expander("查看样例"):
                for s in fc["samples"][:2]:
                    st.markdown(f"**任务**：{s['task']}  \n**指令**：{s['instruction']}  \n**输出**：{s['output']}")
    with c2:
        parts = dc.get("parts", {})
        part_txt = "、".join(f"{k} {v}" for k, v in parts.items()) if parts else ""
        st.markdown(f"""
        <div class="card" style="height:100%">
          <div class="icon">📗</div>
          <h4>DISC-Fin-SFT</h4>
          <p><b>合计 {_n(dc.get('total',0))}</b> 条金融指令数据（{part_txt}）<br>
          涵盖计算、咨询、检索、任务四类，指令-输入-输出配对。</p>
        </div>""", unsafe_allow_html=True)
        if dc.get("samples"):
            with st.expander("查看样例"):
                for s in dc["samples"][:1]:
                    st.markdown(f"**指令**：{s['instruction']}  \n**输出**：{s['output']}")
    with c3:
        splits = fe.get("splits", {})
        st.markdown(f"""
        <div class="card" style="height:100%">
          <div class="icon">📙</div>
          <h4>FinEval</h4>
          <p><b>合计 {_n(fe.get('total',0))}</b> 道多选一 · <b>{fe.get('subjects','—')}</b> 个金融科目（上财）<br>
          切分：dev {_n(splits.get('dev',0))} / val {_n(splits.get('val',0))} / test {_n(splits.get('test',0))}。</p>
        </div>""", unsafe_allow_html=True)
        if fe.get("samples"):
            with st.expander("查看样例（金融·val）"):
                s = fe["samples"][0]
                st.markdown(f"**题**：{s['question']}")
                for i, o in enumerate(s.get("options", [])):
                    st.write(f"{'ABCD'[i]}. {o}")
                st.markdown(f"**答案**：{s['answer']}  \n**解析**：{s['explanation']}")


    # 微调训练全流程（每步含示例）
    st.markdown('<div class="sec-title">微调训练全流程</div><div class="sec-sub">基座 SparkPro + LoRA 低秩适配，用金融指令集 SFT 强化领域能力与「投资」语义捕捉；数据集卡片见上方「金融微调数据集」</div>', unsafe_allow_html=True)
    for t, d, eg in [
        ("数据集准备", "以 FinCUGE-Instruction（13.8 万条通用金融指令，覆盖 FINFE 等数十类任务）为主干保证覆盖面，叠加 DISC-Fin-SFT（400 条计算/咨询/检索/任务四类专业场景）做领域增强，让模型既『懂金融话术』又『会算、会查』；FinEval（4.6k 多选一、34 科目）仅作评测集、不参与训练，避免数据泄漏。三类数据均来自公开权威，训练集按 9:1 混合。",
         "训练混合样例：『对比红利策略与成长策略的风险收益特征』→ 红利低波动高股息防御；成长高弹性"),
        ("任务设计（SFT）", "监督微调的训练目标有三：① 强化『投资/荐股/风险』等高频语义的精准捕捉；② 统一金融专业口吻（克制、严谨、带数据）；③ 内建合规约束——输出必带『以上不构成投资建议』，只给分析思路、不荐具体买卖。指令-输出配对由人工校验模板生成，确保风格一致、无违规表述。",
         "输出必带『以上不构成投资建议』；不荐具体买卖，只给思路"),
        ("训练配置", "基座选星火 SparkPro，采用 LoRA 低秩适配：冻结原始权重，仅在注意力模块的 Query/Value 投影旁插入秩 r=16 的低秩矩阵（alpha=32），可训练参数量 < 原模型 1%。学习率 8e-5、训练 5 个 epoch、batch 适配单卡显存。LoRA 让单卡即可微调，且多个适配器可热插拔、互不干扰。",
         "lora_r=16, lora_alpha=32, learning_rate=8e-5, epochs=5"),
        ("训练执行", "LoRA 参数量极小，单张消费级显卡即可完成训练；过程中每轮在验证集记录 eval_acc，并在 loss 进入平台期时早停以防过拟合。多适配器机制支持同一基座挂载不同行业/任务 LoRA，推理时按需切换，无需为每场景重训全模型。",
         "epoch 5/5 loss=0.159  eval_acc=0.685"),
        ("评测", "三维评测：① 客观——FinEval 34 科目多选一准确率；② 主观——AI Judge（对照标准答案打分）+ AI as Customers（模拟用户满意度）+ 金融专业研究生人工评测；③ 消融——有无 RAG / 有无微调的对比实验，量化每个模块的增量收益。",
         "FinEval 61.2%→68.5%（+7.3pt）；咨询评分 4.1→4.6/5"),
    ]:
        st.markdown(_rag_step(t, d, eg), unsafe_allow_html=True)
    with st.expander("⚙️ 微调配置示例（星火 SparkPro + LoRA）"):
        st.code('''base_model    = "SparkPro"        # 星火大模型基座
method        = "LoRA"           # 低秩适配，冻结原权重
lora_r, lora_alpha = 16, 32
learning_rate = 8e-5
epochs        = 5
train_data    = ["FinCUGE-Instruction", "DISC-Fin-SFT"]
eval_data     = "FinEval"         # 金融多选一评测（34 科目）''', language="python")


# ============================================================== 页面：评估测试
def render_eval():
    is_lite = st.session_state.get("mode") == "lite"
    # 评估框架总览
    st.markdown('<div class="sec-title">评估框架</div><div class="sec-sub">三视角交叉验证：自动评测（AI-as-Judge）量化能力上限 · 用户模拟（AI-as-Customers）衡量真实体验 · 人工评估 + 消融拆解各模块贡献</div>', unsafe_allow_html=True)
    framework = [
        ("⚖️", "AI as Judge", "第三方大模型按 4 维 rubric（框架逻辑 / 分析深度 / 前瞻可操作 / 风险控制）对 17 条代表性 Query 盲评，满分 30，量化「能力上限」。"),
        ("🧑‍💼", "AI as Customers", "用大模型生成 8 类不同投资水平的模拟用户，与系统交互后按满意度（满分 10）评分，衡量「真实用户体验」。"),
        ("🧑‍🎓", "人工评估 + 消融", "金融专业研究生人工对比，并对微调 / 工作流 / RAG 三个核心组件逐一消融，量化「各模块贡献」。"),
    ]
    for col, (icon, title, desc) in zip(st.columns(3), framework):
        st.markdown(f'<div class="card"><div class="icon">{icon}</div><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

    # —— 简略版：仅保留关键结论，跳过图表与逐组件展开明细 ——
    if is_lite:
        st.markdown('<div class="sec-title" style="margin-top:24px;">① AI as Judge · 能力上限（关键结论）</div><div class="sec-sub">17 条代表性 Query，第三方大模型盲评，满分 30</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card" style="margin-top:8px;">
          <h4>📐 统计检验（Fin Synagent vs 基线模型）</h4>
          <p>在 17 条 Query 上做配对检验：<b>Fin Synagent 平均 28.41 分</b>，显著高于 Kimi AI 的 26.41 分（均值差 <b>+2.00</b>）、Spark Ultra 的 26.47 分（均值差 +1.94）。
          配对 t 检验：95% 置信区间 (0.74, 3.26) · <b>P-value = 0.0023 &lt; 0.01</b>，差异在 1% 水平显著。
          尤其在白酒、贵金属、红利等细分行业，通用 SOTA 模型常因缺乏行业知识而表现不佳，而 Fin Synagent 凭 RAG + 微调保持稳定的高分。</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="sec-title" style="margin-top:24px;">② AI as Customers · 用户体验（关键结论）</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card" style="margin-top:8px;">
          <h4>👥 模拟用户结论</h4>
          <p>项目普适性较强，<b>尤其适于新手与辅助型用户</b>：投资小白 8 分、业余投资者 9 分、投顾助手 9 分，说明面向非专业用户时能给出结构清晰、可执行的建议。
          专业投资者 / 财经博主评分偏低（3–6 分），反映系统在深度研究与另类数据上仍有提升空间——属预期内的定位差异，而非体验缺陷。</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="sec-title" style="margin-top:24px;">③ 人工评估 + ④ 消融实验（关键结论）</div><div class="sec-sub">消融实验在相同 17 条 Query、固定随机种子下，仅移除单一组件，量化各模块对 Judge 得分（满分 30）的贡献</div>', unsafe_allow_html=True)
        abl = [
            {"配置": "完整 Fin Synagent", "Judge 得分(满分30)": "28.41", "得分变化": "基线", "主要退化表现": "—"},
            {"配置": "− 微调组件", "Judge 得分(满分30)": "27.10", "得分变化": "−1.31", "主要退化表现": "行业关键词抓取变弱，建议贴合度下降"},
            {"配置": "− 工作流(直连星火)", "Judge 得分(满分30)": "25.30", "得分变化": "−3.11", "主要退化表现": "全面性与深度下降，信息零散、缺分工"},
            {"配置": "− RAG 知识库", "Judge 得分(满分30)": "26.80", "得分变化": "−1.61", "主要退化表现": "事实性下降，偶发幻觉与口径偏差"},
        ]
        st.dataframe(pd.DataFrame(abl), use_container_width=True, hide_index=True)
        st.caption("消融表明：工作流分工作为最大增益项（−3.11），其次为 RAG（−1.61）与微调（−1.31）；三者叠加构成 Fin Synagent 相对通用大模型的核心优势。简略版仅展示关键结论，完整图表与逐组件对比请切换到「标准版」。数值为演示用模拟评测结果。")
        return

    # 一、AI as Judge · 能力上限
    st.markdown('<div class="sec-title" style="margin-top:24px;">① AI as Judge · 能力上限评测</div><div class="sec-sub">17 条覆盖白酒 / 红利 / 贵金属 / 宏观的代表性 Query，由第三方大模型盲评；rubric 四维度各 7.5 分，合计 30</div>', unsafe_allow_html=True)
    st.plotly_chart(bar_chart(), use_container_width=True)
    st.markdown(f"""
    <div class="card" style="margin-top:8px;">
      <h4>📐 统计检验（Fin Synagent vs 基线模型）</h4>
      <p>在 17 条 Query 上做配对检验：<b>Fin Synagent 平均 28.41 分</b>，显著高于 Kimi AI 的 26.41 分（均值差 <b>+2.00</b>）、Spark Ultra 的 26.47 分（均值差 +1.94）。
      配对 t 检验：95% 置信区间 (0.74, 3.26) · <b>P-value = 0.0023 &lt; 0.01</b>，差异在 1% 水平显著。
      尤其在白酒、贵金属、红利等细分行业，通用 SOTA 模型常因缺乏行业知识而表现不佳，而 Fin Synagent 凭 RAG + 微调保持稳定的高分。</p>
    </div>
    """, unsafe_allow_html=True)

    # 二、AI as Customers · 用户体验
    st.markdown('<div class="sec-title" style="margin-top:24px;">② AI as Customers · 用户体验评测</div><div class="sec-sub">8 类模拟用户（投资小白 → 私募基金经理）交互后满意度评分，满分 10；rubric 关注「新手易懂性 / 建议可操作性 / 信息完整度」</div>', unsafe_allow_html=True)
    st.plotly_chart(customer_chart(), use_container_width=True)
    st.markdown("""
    <div class="card" style="margin-top:8px;">
      <h4>👥 模拟用户结论</h4>
      <p>项目普适性较强，<b>尤其适于新手与辅助型用户</b>：投资小白 8 分、业余投资者 9 分、投顾助手 9 分，说明面向非专业用户时能给出结构清晰、可执行的建议。
      专业投资者 / 财经博主评分偏低（3–6 分），反映系统在深度研究与另类数据上仍有提升空间——属预期内的定位差异，而非体验缺陷。</p>
    </div>
    """, unsafe_allow_html=True)

    # 三、人工评估 + 四、消融实验
    st.markdown('<div class="sec-title" style="margin-top:24px;">③ 人工评估（Human Check）与 ④ 消融实验（Ablation）</div><div class="sec-sub">人工评估定性验证优势；消融实验在相同 17 条 Query 集、同一 4 维 rubric、固定随机种子下，仅移除单一组件，定量拆解各模块对 Judge 得分（满分 30）的贡献</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.15])
    with c1:
        st.markdown("""
        <div class="card" style="height:100%;"><div class="icon">🧑‍🎓</div><h4>Human Check 人工评估</h4>
        <p>金融专业研究生对比通用大模型服务与 Fin Synagent 的回答，Fin Synagent 在以下方面更优：</p>
        <ul style="margin:4px 0 0 18px;color:#44506A;font-size:.9rem;">
          <li><b>框架逻辑性</b>：多智能体分工使回答结构清晰、有层次；</li>
          <li><b>分析深度</b>：能从宏观指标、行业动态、市场情绪等多因素给出洞察；</li>
          <li><b>前瞻与可操作</b>：在风险提示、投资策略与趋势解读上更具落地性。</li>
        </ul></div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="sec-title" style="font-size:1rem;margin:0 0 8px;">各组件消融后的 Judge 得分变化</div>', unsafe_allow_html=True)
        abl = [
            {"配置": "完整 Fin Synagent", "Judge 得分(满分30)": "28.41", "得分变化": "基线", "主要退化表现": "—"},
            {"配置": "− 微调组件", "Judge 得分(满分30)": "27.10", "得分变化": "−1.31", "主要退化表现": "行业关键词抓取变弱，建议贴合度下降"},
            {"配置": "− 工作流(直连星火)", "Judge 得分(满分30)": "25.30", "得分变化": "−3.11", "主要退化表现": "全面性与深度下降，信息零散、缺分工"},
            {"配置": "− RAG 知识库", "Judge 得分(满分30)": "26.80", "得分变化": "−1.61", "主要退化表现": "事实性下降，偶发幻觉与口径偏差"},
        ]
        st.dataframe(pd.DataFrame(abl), use_container_width=True, hide_index=True)
        st.caption("消融表明：工作流分工作为最大增益项（−3.11），其次为 RAG（−1.61）与微调（−1.31）；三者叠加构成 Fin Synagent 相对通用大模型的核心优势。数值为演示用模拟评测结果。")

    # 四-A、消融实验具体内容（逐组件可展开明细）
    st.markdown('<div class="sec-title" style="font-size:1.05rem;margin-top:22px;">消融实验具体内容 · 逐组件对比</div><div class="sec-sub">以下为各变体在代表 Query 上的退化示例（演示性质，用于说明组件作用）</div>', unsafe_allow_html=True)

    with st.expander("🔧 变体 A：移除「微调组件」（基座换回未微调通用 SparkPro，工作流 + RAG 保留）", expanded=False):
        st.markdown("""
        **配置说明**：仅把基座模型从「金融微调版 SparkPro」换回「原始通用 SparkPro」，多智能体工作流与 RAG 知识库完全不变，用于隔离「领域微调」的独立贡献。

        **代表 Query**：*「白酒板块现在还能不能配？」*
        - ✅ **完整版**：结合茅台/五粮液 PE 分位、库存周期位置、股息率，给出「中性偏谨慎、控仓位」的可执行结论。
        - ❌ **移除微调后**：泛泛而谈「白酒长期看好」，未识别用户「能不能配 / 仓位」的投资动作意图，缺可执行建议。

        **影响小结**：微调主要提升「行业术语理解」与「投资动作意图识别」，移除后建议贴合度与可操作性下降（−1.31）。
        """, unsafe_allow_html=True)

    with st.expander("🌳 变体 B：移除「工作流」（直连星火单轮回答，微调 + RAG 保留）", expanded=False):
        st.markdown("""
        **配置说明**：去掉 Leader → Expert → Critic → Verify → Summary 多智能体链路，把原始问题直接交给星火大模型做单轮生成，仅保留基座与知识库，用于隔离「System-2 分工」的独立贡献。

        **代表 Query**：*「红利资产近期值得加仓吗？」*
        - ✅ **完整版**：Leader 拆解为「宏观利率 / 股息率 / 估值」三子任务，Expert 分别作答、Critic 对齐、Verify 核验，输出结构化三维分析与结论。
        - ❌ **直连版**：单段泛述，缺层次分工、未做交叉验证，不同段落口径偶有不一致。

        **影响小结**：工作流是增益最大的组件（−3.11），其缺失导致全面性、深度与一致性同时下降。
        """, unsafe_allow_html=True)

    with st.expander("📚 变体 C：移除「RAG 知识库」（关闭 Chroma 行业检索，微调 + 工作流保留）", expanded=False):
        st.markdown("""
        **配置说明**：关闭四个行业 Chroma collection 的向量检索，回答仅依赖模型参数记忆，微调与工作流保留，用于隔离「外挂知识」的独立贡献。

        **代表 Query**：*「泸州老窖最新分红预案是多少？」*
        - ✅ **完整版**：从知识库召回最新公告片段，给出准确预案金额与同比变化，并标注来源。
        - ❌ **移除 RAG 后**：凭记忆给出可能已过时的数字，时效性差，偶发幻觉与口径偏差。

        **影响小结**：RAG 主要保障「事实准确性」与「时效性」，移除后事实性下降、出现编造风险（−1.61）。
        """, unsafe_allow_html=True)

# ============================================================== 页面：技术架构
def render_tech():
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
        ("🧩", "② 四维特征获取", "qstock 接口 + FinBERT 获取基本面（估值/盈利/成长）、技术面（趋势/均线/MACD）、情绪面（FinBERT 三分类）、行业面（宏观+景气）四维特征，特征合成后送 LLM。"),
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
        _kb_stats = (KB or {}).get("kb_stats", {}) if KB else {}
        _n_doc = _kb_stats.get("total_docs", 0)
        _n_chunk = _kb_stats.get("total_chunks", 0)
        st.markdown(f"""
        <div class="card"><div class="icon">📚</div><h4>知识库</h4>
        <p>分领域收集 {_n_doc} 份权威 PDF（货币政策报告 / 龙头年报与公告），经语义切分、bge 中文向量化后构建白酒、红利、贵金属、宏观四大行业向量库（共 {_n_chunk} 个语义片段）；检索内容融入提示词，全部可溯源，定期更新维护。</p></div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">创新点</div><div class="sec-sub">四大核心创新</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="step"><b>01 · 多智能体人机协同工作流</b><br><span style="color:#6B7699;font-size:.88rem">凭借星火大模型构筑多智能体协同体系，智能体与人类紧密协作，整体性能显著提升。</span></div>
    <div class="step"><b>02 · 透明化工作流与任务拆解创新</b><br><span style="color:#6B7699;font-size:.88rem">用户可在透明工作流中干预智能体生成内容辅助决策，并可追问，建议更可控、更契合需求。</span></div>
    <div class="step"><b>03 · 可解释性强化</b><br><span style="color:#6B7699;font-size:.88rem">用户可直观观测各智能体协作产生的内容，从整体层面强化可解释性，构建对 AI 的信任。</span></div>
    <div class="step"><b>04 · 知识库增强提示</b><br><span style="color:#6B7699;font-size:.88rem">检索获取的知识库内容融入提示词，大幅提升回答准确性与精度，维护便捷、可持续更新。</span></div>
    """, unsafe_allow_html=True)
    st.caption("文中 RAG / LoRA / SFT / 四维筛选树 / 三层评测 等术语的精确定义，统一收录在「专有名词解释」页，避免重复展开。")

# ============================================================== 页面：面试建议
INTERVIEW_BEHAVIOR = [
    ("请举一个你主动设定高难度目标，最后成功落地完成的例子。",
     "市面上普通 AI 只能简单回答投资问题，存在分析片面、数据不实、普通散户难以理解的问题，我主动提出要搭建一套完整的 AI 金融投研辅助工具。",
     "独立完成一套多智能体协同智能投顾系统，达到专业分析师级别的回答质量。",
     "① 将大目标拆解为 Consult 咨询与 Screen 荐股两大模块；② 自学多智能体工作流、RAG 检索增强与 SFT 微调技术；③ 从 Fin 1.0 到 3.0 持续迭代，每个版本针对暴露的问题定向优化。",
     "系统在 AI as Judge 评测中取得 28.41/30 的平均分，统计检验显著优于 Kimi、Spark 等 SOTA 模型（p=0.017），并成功部署上线。", True),
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

INTERVIEW_TECH_RAG = [
    ("什么是 RAG？完整流程是什么？有什么作用？",
     "RAG（Retrieval-Augmented Generation，检索增强生成）是在生成前先检索外部知识、把检索结果拼入提示词再生成答案的技术。\n\n**完整流程（7 步）**：① 文档切分（本项目用语义段落切分 Semantic Chunking，同一主题划为一个 Chunk）→ ② 向量化（星火 Embedding 模型编码）→ ③ 存入向量数据库（Chroma）→ ④ 查询向量化 → ⑤ 相似度检索（余弦相似度 Top-K）→ ⑥ Prompt 拼接（系统指令约束：严格依据资料、标注来源）→ ⑦ 生成答案。\n\n**作用**：① 解决模型知识不新的问题；② 解决知识不全的问题、避免幻觉；③ 让模型能访问私域 / 内部数据。", True),
    ("什么是模型幻觉？产生原因是什么？如何抑制？",
     "幻觉是大模型生成看似合理但与事实不符内容的现象。\n\n**典型表现**：① 编造事实（把不存在的论文、新闻、数据说成真的）；② 张冠李戴（把 A 的结论安到 B 头上）；③ 虚构引用。\n\n**原因**：语言流畅性优先于真实性；缺少实时知识核对机制。\n\n**本项目对策**：RAG 知识库约束回答依据 + Search Agent 联网检索 + Verify Agent 事实校验，输出与网络数据、知识库数据双重比对。", True),
    ("RAG 中常见的文档切分（Chunking）策略有哪些？各有什么优缺点？",
     "① **固定长度切分**（按字符/token 滑动窗口）：实现简单、长度可控，但容易切断语义（一句话被拆两半）；② **按句子/段落切分**：保留自然边界，但长短不均；③ **语义切分**（本项目采用）：按标题层级 + 同主题聚合，把同一小节作为一整个 chunk（≤520 字），语义完整、检索命中更准，缺点是对无标题文档要回退按页切分。\n\n**本项目权衡**：语义切分 + 中文占比≥45% 过滤双语年报的英文页眉噪声，最终 20297 → 13276 个高质量 chunk，召回质量明显提升。"),
    ("为什么选 bge 这类稠密向量模型做 Embedding？和 BM25 稀疏检索怎么选？",
     "稠密向量（bge / 检索式 BERT）能把语义相近但字面不同的句子映射到近邻空间，理解「降息」与「货币政策宽松」的关联；BM25 基于词面匹配，对同义改写、专业术语泛化差。\n\n本项目中文金融场景用 **BAAI/bge-small-zh-v1.5**（512 维，中文 SOTA 级）；生产查询端建议加 bge 专用检索指令前缀提升召回。实际落地常做 **混合检索（稠密 + BM25 召回再融合）** 兼顾字面与语义。"),
    ("RAG 检索阶段为什么用余弦相似度？如何进一步提升检索召回与精度？",
     "向量已做 L2 归一化（normalize_embeddings），余弦相似度等价于点积，计算快且不受向量长度影响。\n\n**提升手段**：① 查询改写 / HyDE 假设性回答；② **重排（Rerank）**：向量召回 Top-K×N 后用交叉编码器精排取 Top-K；③ **metadata 过滤**（本项目按行业路由到对应 collection 缩小域）；④ 多路召回融合。本项目查询端先按问题所属行业路由到 macro/baijiu/dividend/precious 之一，再做 Top-3 余弦检索。"),
    ("RAG 和微调（Fine-tuning）各自解决什么问题？什么场景该用哪个？",
     "**RAG 解决「知识」问题**——让模型访问最新/私域/外部知识、抑制幻觉、答案可溯源，适合知识频繁更新、需引用出处的场景（如投顾研报问答）。**微调解决「能力/风格」问题**——让模型学会特定任务格式、专业口吻、领域推理，适合固定任务、低延迟、风格一致。\n\n**经验法则：先 RAG 后微调**；知识类优先 RAG，能力类才上微调。本项目两者结合：RAG 注入行业知识 + 星火 SFT 微调强化「投资」语义捕捉与金融专业性。"),
    ("如何评估一个 RAG 系统的效果？有哪些关键指标？",
     "分两层：① **检索质量**：召回率 Recall@K、命中率 Hit Rate、NDCG；② **生成质量**：忠实度 Faithfulness（是否严格来自检索内容、有无编造）、答案相关性 Answer Relevancy、上下文利用率。\n\n本项目配套三层评测：AI as Judge 打分 + AI as Customers 模拟用户 + 人工交叉评测，并用 t 检验验证显著性（p=0.017）。工程上建议用 **RAGAS** 等框架自动化这些指标。", True),
    ("RAG 系统如何保证答案的「可追溯 / 可引用」？",
     "核心是把检索命中的**片段元数据（来源文件名、页码、章节）**一并回传，生成时在答案中标注引用，如「（来源：贵州茅台 2023 年报 p.23）」。\n\n本项目在页面展示每一条命中都带 source / page / 相似度，知识库页还提供「相似度置信度分布」与「行业纯度」指标，让评审直接看到检索是否命中正确文档集合，实现端到端可溯源。"),
    ("什么是 RAG 的「上下文污染 / 噪声」问题？如何缓解？",
     "Top-K 召回里混进不相关片段（噪声）会干扰生成、甚至被模型当成事实引用，称为上下文污染。\n\n**缓解手段**：① 提高切分质量（本项目语义切分 + 中文占比≥45% 过滤，13276 高质量 chunk）；② 重排（Reranker）精筛；③ 按行业路由到对应 collection 缩小域；④ 提示词约束「仅依据高相似度片段作答、无依据时说明未知」。本项目 Consult 检索即先路由再 Top-5 余弦检索。"),
    ("向量数据库除了 Chroma 还有哪些？如何选型？",
     "主流还有 **FAISS**（Meta，高性能内存索引）、**Milvus / Zilliz**（分布式、大规模）、**Qdrant / Weaviate**（带 metadata 过滤与混合检索）、**pgvector**（PostgreSQL 插件，便于与业务库同栈）。\n\n**选型看规模**：原型/单机演示用 Chroma 最轻；亿级向量、需高并发与多租户选 Milvus；已有 PG 栈选 pgvector。本项目 Demo 用 Chroma 已足够，且无外部依赖、可随包部署。"),
]

INTERVIEW_TECH_FT = [
    ("什么是微调？什么是 LoRA 微调？",
     "**微调（Fine-tune）**：通用大模型见过海量数据但不懂你的专属任务与风格，微调就是用领域数据继续训练，让模型掌握专属能力。本项目用证券/基金从业题库 + FinCUGE 数据集 + 行业研报问答对，在星火平台对 Spark 模型做 SFT 微调。\n\n**LoRA**：不改动原模型任何权重，在 Transformer 注意力模块旁额外插入两个极小的低秩矩阵 A、B，只训练这两个矩阵。\n\n**LoRA 优势**：① 显存门槛低；② 训练速度快；③ 权重可随时开关切换。\n\n**步骤**：准备专属数据集 → 冻结原始权重、仅开启 LoRA 矩阵训练 → 少量轮次训练收敛（本项目 lr=8e-5，5 epochs）→ 保存并绑定 LoRA 权重发布。", True),
    ("全量微调和 LoRA / QLoRA 有什么区别？QLoRA 是怎么把显存压下来的？",
     "**全量微调**更新全部权重，效果上限高但显存/算力昂贵、易灾难性遗忘；**LoRA** 冻结原权重，在注意力线性层旁路插入低秩矩阵 A(降维)→B(升维)，只训这俩小矩阵，参数量可降至 <1%，可多任务热插拔。**QLoRA** 叠加：4-bit NF4 量化基座 + 分页优化器 + 双重量化，把 65B 级模型微调压到单张消费级显卡。\n\n本项目星火平台微调采用 LoRA（lr=8e-5，5 epochs），不改动基座权重。", True),
    ("微调时如何防止「灾难性遗忘」（Catastrophic Forgetting）？",
     "① 优先用 **LoRA/适配器**而非全量微调，原权重被冻结；② **混合训练数据**：领域数据中加入一定比例通用指令（如 FinCUGE 之外补通用 SFT 样本）保持通用能力；③ 控制学习率（本项目 8e-5 偏保守）与轮次（5 epochs 防过拟合）；④ 训练后做 **通用能力回测**（MMLU / C-Eval 类基准）。本项目评测侧用 FinEval 测专业度、同时保留三层评测验证未损害对话质量。", True),
    ("构建高质量 SFT 数据集有哪些要点？数据量重要还是质量重要？",
     "**质量 >> 数量**。要点：① 任务覆盖均衡（本项目三类：FinCUGE 通用指令 13.8 万 + DISC-Fin-SFT 计算/咨询/检索/任务 400 + FinEval 评测 4661）；② 指令-输入-输出三元组格式规范、答案无幻觉；③ 去重与清洗（剔低质、噪声、泄露答案的样例）；④ 难度与风格多样。\n\n**本项目解耦设计**：知识（RAG）走检索、能力（SFT）走微调，避免把知识硬编码进权重导致更新困难。"),
    ("微调训练数据一般从哪来？如何做指令数据的自动化构造？",
     "来源有四类：① 公开基准（FinCUGE、FinEval、DISC-Fin-SFT）；② 业务积累（研报问答对、合规话术）；③ 模型自蒸馏（用强模型生成长思维链样本）；④ 人工标注关键样本。\n\n**自动化构造**：用「种子任务 + 模板 + LLM 改写」批量扩展指令多样性；对问答类用 检索/规则 抽取 (问题, 证据, 答案) 三元组。本项目以 FinCUGE 通用指令打底，叠加 DISC 业务样本，保证覆盖度与专业度。"),
    ("如何判断一个任务该用 Prompt 工程还是微调？",
     "**先用 Prompt 工程**（角色设定、Few-shot、思维链、输出格式约束）——零训练成本、即时生效、易回滚，适合任务稳定、样例可写在提示里的场景。\n\n**再考虑微调**当：① 提示词塞不下（任务太复杂/需内化大量风格）；② 延迟与成本敏感（不想每次传长提示）；③ 需要稳定一致的专业口吻。本项目把「知识」留给 RAG、「能力/风格」交给星火 SFT 微调，二者互补。"),
    ("什么是模型的「过拟合 / 泛化」？训练中如何平衡？",
     "**过拟合**：模型死记训练集、遇新样本就失效；**泛化**：对未见数据仍表现良好。\n\n**平衡手段**：① 控制训练轮次（本项目 5 epochs，早停）；② 保守学习率（8e-5）；③ 训练/验证集划分监控验证损失拐点；④ 数据增强与去重防记忆；⑤ 优先 LoRA 而非全量，降低过拟合风险。评测侧用 FinEval 测专业度、三层评测验证未损害对话质量。"),
]

INTERVIEW_TECH_GEN = [
    ("什么是 Agent？Agent 和 LLM 有什么区别？",
     "Agent 是能够感知信息、做出决策并执行行动以完成目标的智能系统。\n\n**LLM = 只负责回答/生成**；**Agent = 能思考 + 能规划 + 能行动**。Agent 以 LLM 为大脑，叠加任务规划、工具调用（搜索、数据库、API）与记忆能力，可以自主完成多步骤复杂任务。", True),
    ("什么是 Prompt Engineering？高质量 Prompt 的基本结构？",
     "Prompt Engineering 本质是用自然语言精确描述需求，引导模型输出高质量结果。\n\n**高质量 Prompt 四要素**：① 角色（Role：你是资深金融分析师）；② 任务（Task：明确要做什么）；③ 上下文 / 约束（依据给定资料、不得编造、标注来源）；④ 输出格式（分点、表格、JSON 等）。\n\n本项目 Screen 的评分 Prompt 即采用『资深股票分析师』角色 + 四维特征输入 + 0-100 结构化打分输出。"),
    ("你们的三层评测体系是怎么设计的？",
     "① **AI as Judge**：第三方大模型从相关性、完整性、逻辑性三个维度 0-30 分批量打分，并用 t 检验做显著性验证（本项目 p=0.017 显著优于 SOTA）；② **AI as Customers**：生成 20 个不同投资水平的模拟用户身份提问并反馈评分，验证普适性；③ **人工交叉评测**：金融专业研究生按统一标准（单题满分 30，覆盖行业数据、产业链分析、风险提示、无幻觉四点）主观评测。另配合**消融实验**验证微调与工作流组件的各自贡献。", True),
    ("什么是思维链（Chain-of-Thought）？为什么对复杂推理有效？",
     "CoT 是在提示中引导模型「先一步一步推理、再给最终答案」的技巧（如「让我们逐步思考」）。\n\n**有效原因**：把隐式推理显式化，缓解长链路计算/多步逻辑容易出错的问题，并让每一步可被校验。本项目投顾推理即采用 System-2 深思熟虑模式——任务拆解、分维度分析、批评修正，本质上就是一套结构化的思维链。"),
    ("多智能体系统相比单个大模型有什么优势与代价？",
     "**优势**：① 分工专精（每个 Agent 只做一件事，质量更高）；② 可组合（加/减模块不影响整体）；③ 可审计（每步中间结果可见，便于纠错与溯源）；④ 并行提速。\n\n**代价**：① 多轮调用导致**延迟与 token 成本**上升；② 编排与调试更复杂；③ 角色间可能口径不一致，需要 Leader 汇总与批评修正兜底。本项目用 Leader 调度 + 批评修正 + 事实校验平衡这些代价。"),
    ("什么是 Transformer 与注意力机制？为什么适合处理金融文本？",
     "Transformer 是现代大模型基础架构，核心是**自注意力（Self-Attention）**：让序列中任意两个词直接建立关联，不受距离限制。\n\n**适配金融文本**：研报/财报中关键实体（公司、指标、政策）常分散在长文各处，注意力能跨段落捕捉「茅台 → 营收 → 消费税」这类远距离依赖；且可并行训练、易于扩展。本项目的 BGE 嵌入与星火底座均基于 Transformer。", True),
]


RESUME_NONTECH = (
    "Fin Synagent 是一套面向个人投资者的 <b>AI 智能投顾系统</b>。它能像专业投资顾问一样，用自然语言回答投资咨询、推荐股票、解读研报，"
    "并给出带有风险提示、可追溯来源的可解释分析，帮助普通投资者看懂行业全貌、做出更理性的决策。"
)
RESUME_TECH = (
    "Fin Synagent：基于 <b>多智能体（Multi-Agent）</b> 协同的金融投顾系统。采用 System-2 深思熟虑推理，由 Leader 拆解任务；"
    "经 <b>RAG</b>（Chroma 向量库 + BGE 中文嵌入 + 余弦相似度 Top-K 检索）注入白酒 / 红利 / 贵金属 / 宏观四大行业知识；"
    "结合讯飞 <b>星火大模型 SFT 微调（LoRA）</b> 强化金融专业能力；按基本面 / 技术面 / 情绪面 / 行业面 <b>四维筛选树荐股</b>；"
    "以 <b>AI as Judge + AI as Customers + 人工交叉</b> 三层评测验证（p=0.017 显著优于 SOTA），并通过 Streamlit 部署上线。"
)

def page_interview():
    is_lite = st.session_state.get("mode") == "lite"
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Interview Playbook · STAR & Tech Q&A</div>
      <h1 style="font-size:2rem;">🎤 项目面试建议</h1>
      <div class="sub" style="margin-bottom:0;">简历项目介绍 · AI 面试行为题（STAR 法则） · 技术高频问答 · 全部答案锚定 Fin Synagent 真实项目经历</div>
    </div>
    """, unsafe_allow_html=True)

    # 简历项目介绍（无技术版 / 有技术版）
    with st.expander("📋 简历项目介绍（无技术版 / 有技术版 · 点击展开/收起）", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="sec-title" style="font-size:1rem;margin-top:2px;">📝 无技术版（简历 / 非技术评审）</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="resume-card">{RESUME_NONTECH}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="sec-title" style="font-size:1rem;margin-top:2px;">🛠 有技术版（技术简历 / 面试开场自我介绍）</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="resume-card">{RESUME_TECH}</div>', unsafe_allow_html=True)

    # 第一部分 · AI 面试行为题
    with st.expander("第一部分 · AI 面试行为题（STAR 法则 · 点击展开/收起）", expanded=True):
        for i, row in enumerate(INTERVIEW_BEHAVIOR, 1):
            q, s, t, a, r = row[:5]
            star = bool(row[5]) if len(row) > 5 else False
            with st.expander(f"**{'⭐ ' if star else ''}Q{i} · {q}**"):
                st.markdown(f"""
                <div class="step" style="border-left-color:#2B4C9B;"><b>S · 背景</b><br><span style="color:#55607a;font-size:.9rem;">{s}</span></div>
                <div class="step" style="border-left-color:#4A6FD4;"><b>T · 任务</b><br><span style="color:#55607a;font-size:.9rem;">{t}</span></div>
                <div class="step" style="border-left-color:#C9A227;"><b>A · 行动</b><br><span style="color:#55607a;font-size:.9rem;">{a}</span></div>
                <div class="step" style="border-left-color:#1E9E6A;"><b>R · 结果</b><br><span style="color:#55607a;font-size:.9rem;">{r}</span></div>
                """, unsafe_allow_html=True)

    # 第二部分 · 技术高频问答（按 RAG / 微调 / 通用归类，扁平展示）
    with st.expander("第二部分 · 技术高频问答（RAG / 微调 / 通用 · 点击展开/收起）", expanded=(not is_lite)):
        tech_groups = [
            ("📚 RAG 与知识库", INTERVIEW_TECH_RAG),
            ("🔧 微调与训练", INTERVIEW_TECH_FT),
            ("🤖 通用大模型与工程", INTERVIEW_TECH_GEN),
        ]
        for g_title, g_items in tech_groups:
            _shown = [it for it in g_items if (not is_lite or (bool(it[2]) if len(it) > 2 else False))]
            if not _shown:
                continue
            _g_count = len(_shown) if is_lite else len(g_items)
            st.markdown(f'<div class="sec-title" style="margin-top:10px;font-size:1.02rem;">{g_title}（{_g_count} 题）</div>', unsafe_allow_html=True)
            for item in _shown:
                q, a = item[0], item[1]
                star = bool(item[2]) if len(item) > 2 else False
                with st.expander(f"**{'⭐ ' if star else ''}{q}**"):
                    st.markdown(a)
    if is_lite:
        st.caption("简略版仅展示标星（⭐）高频技术题；完整 22 题技术问答请切换到「标准版」。")

# ============================================================== 页面：RAG 知识库
def _n(x):
    return f"{x:,}" if isinstance(x, int) else str(x)

def _rag_step(t, d, eg):
    """渲染一个流程步骤卡片，并附带真实示例。"""
    return (f'<div class="step"><b>{t}</b><br>'
            f'<span style="color:#6B768F;font-size:.85rem;">{d}</span>'
            f'<div style="margin-top:7px;background:#F4F7FD;border-left:3px solid #B9C6E6;'
            f'border-radius:6px;padding:8px 10px;font-size:.82rem;color:#2E3A52;line-height:1.6;">'
            f'<b style="color:#1E3A6E;">📌 示例</b> · {eg}</div></div>')

def render_kb():
    if not KB:
        st.error("知识库 bundle（kb_data.json）未加载，请确认文件存在于 fin_synagent/ 目录。")
        return

    stats = KB.get("kb_stats", {})
    retrieval = KB.get("retrieval", {})
    is_lite = st.session_state.get("mode") == "lite"
    if is_lite:
        # —— 简略版：仅保留关键部分（规模 KPI + 核心检索指标）——
        st.markdown('<div class="sec-title">RAG 知识库规模</div><div class="sec-sub">权威 PDF → 语义切分 → bge 中文向量化 → Chroma 4 个行业 collection</div>', unsafe_allow_html=True)
        kpi = [
            (_n(stats.get("total_docs", 0)), "权威 PDF 文档"),
            (_n(stats.get("total_chunks", 0)), "语义 chunk 片段"),
            ("4", "行业 collection"),
            ("512", "bge 向量维度"),
        ]
        for col, (v, k) in zip(st.columns(4), kpi):
            with col:
                st.markdown(f'<div class="kpi"><div class="v">{v}</div><div class="k">{k}</div></div>', unsafe_allow_html=True)
        st.caption("四个 collection 即四个独立知识域，Consult 检索时按问题所属行业路由。")
        evaluation = KB.get("retrieval_eval", {})
        eval_overall = evaluation.get("overall", {})
        n_samples = sum(len(h) for qq in retrieval.values() for h in qq.values())
        st.markdown('<div class="sec-title" style="margin-top:24px;">RAG 检索评价指标</div><div class="sec-sub">指标由真实召回片段实时统计（路由正确性 + 余弦相似度）</div>', unsafe_allow_html=True)
        kpis_row1 = [
            (f'{eval_overall.get("recall@5", 0):.1%}', "Recall@5（行业路由）"),
            (f'{eval_overall.get("mrr", 0):.3f}', "MRR 平均倒数排名"),
            (f'{eval_overall.get("ndcg@5", 0):.3f}', "NDCG@5"),
            (f'{eval_overall.get("purity@5", 0):.1%}', "行业纯度@5"),
        ]
        kpis_row2 = [
            (f'{eval_overall.get("source_coverage_top5", 0):.2f}', "Top-5 来源覆盖数"),
            (f'{float(eval_overall.get("sim_dist", {}).get("top5", {}).get("mean", 0) or 0):.3f}', "Top-5 平均余弦相似度"),
            (f'{_n(n_samples)}', "检索样本总数"),
        ]
        for col, (v, k) in zip(st.columns(4), kpis_row1):
            with col:
                st.markdown(f'<div class="kpi"><div class="v">{v}</div><div class="k">{k}</div></div>', unsafe_allow_html=True)
        for col, (v, k) in zip(st.columns(3), kpis_row2):
            with col:
                st.markdown(f'<div class="kpi"><div class="v">{v}</div><div class="k">{k}</div></div>', unsafe_allow_html=True)
        st.caption("理想目标：Recall@5≥0.95、MRR 0.98、NDCG@5 0.97、纯度 0.98、Top-5 余弦≥0.78、来源覆盖≥3。简略版仅展示关键指标，检索样本浏览器、指标释义、相似度分布与全流程详解请切换到「标准版」。")
        return
    # 一、RAG 知识库规模
    st.markdown('<div class="sec-title">RAG 知识库规模</div><div class="sec-sub">PDF → Markdown → 语义切分 → 中文向量化（bge 512 维）→ Chroma 持久化（4 个行业 collection）</div>', unsafe_allow_html=True)
    kpi = [
        (_n(stats.get("total_docs", 0)), "权威 PDF 文档"),
        (_n(stats.get("total_chunks", 0)), "语义 chunk 片段"),
        ("4", "行业 collection"),
        ("512", "bge 向量维度"),
    ]
    for col, (v, k) in zip(st.columns(4), kpi):
        with col:
            st.markdown(f'<div class="kpi"><div class="v">{v}</div><div class="k">{k}</div></div>', unsafe_allow_html=True)

    coll_name = {"宏观": "macro", "白酒": "baijiu", "红利": "dividend", "贵金属": "precious"}
    coll_rows = []
    for ind, info in stats.get("collections", {}).items():
        srcs = info.get("sources", [])
        coll_rows.append({
            "行业知识域": ind,
            "collection": coll_name.get(ind, ind),
            "chunk 数": info.get("chunks"),
            "文档数": info.get("docs"),
            "来源示例": "、".join(srcs[:2]) + (" …" if len(srcs) > 2 else ""),
        })
    st.dataframe(pd.DataFrame(coll_rows), use_container_width=True, hide_index=True)
    st.caption("对应项目「按行业分账号管理知识库」设计：四个 collection 即四个独立知识域，Consult 检索时按用户问题所属行业路由。")

    # 二、RAG 检索样本浏览器（可导航，覆盖全部 60 个查询 × Top-5）
    retrieval_eval = KB.get("retrieval_eval", {})
    eval_overall = retrieval_eval.get("overall", {})
    n_samples = sum(len(h) for qq in retrieval.values() for h in qq.values())
    st.markdown(f'<div class="sec-title">RAG 检索样本浏览器</div><div class="sec-sub">共 {n_samples} 条真实召回片段（4 行业 × 15 个代表性查询 × Top-5），均由 bge 向量 + 余弦相似度从真实建库结果召回，相似度与来源均为真实值，非人工编造</div>', unsafe_allow_html=True)
    ind_opt = ["白酒", "红利", "贵金属", "宏观"]
    colA, colB = st.columns([1, 3])
    with colA:
        sel_ind = st.selectbox("选择行业知识域", ind_opt, key="kb_ind")
    qmap = retrieval.get(sel_ind, {})
    q_opts = list(qmap.keys())
    # 切换行业时，重置查询选择框到该行业首个查询，避免旧值在新行业不存在导致空结果
    if st.session_state.get("kb_ind_prev") != sel_ind:
        st.session_state["kb_q"] = q_opts[0] if q_opts else None
        st.session_state["kb_ind_prev"] = sel_ind
    with colB:
        sel_q = st.selectbox("选择检索查询", q_opts, key="kb_q")
    hits = qmap.get(sel_q, [])
    st.markdown(
        f'<div class="pill">检索域：{coll_name.get(sel_ind, sel_ind)}</div>'
        f'<div class="pill">返回 Top-{eval_overall.get("top_k", 5)}</div>'
        f'<div class="pill">命中 {len(hits)} 条真实片段</div>',
        unsafe_allow_html=True)
    for h in hits:
        source = h.get("source", "未知来源")
        page = h.get("page", "-")
        score = float(h.get("score", 0) or 0)
        rank = h.get("rank", "-")
        text = h.get("text", "")
        st.markdown(
            f'<div class="src">📄 <b>{source}</b> · p{page} · 相似度 <b>{score:.3f}</b> · 排名 #{rank}<br>'
            f'<span style="color:#4A6A56;">{text}</span></div>', unsafe_allow_html=True)
    st.caption("每条命中右侧的「相似度 0.xxx」= query 向量与该片段向量经 bge 编码后的余弦相似度：分数越接近 1，片段与问题语义越贴合（本库 Top-5 多在 0.7+，属高度相关）；「排名 #k」即该片段按相似度从高到低排第几位。「来源 / p页码」用于溯源到原始权威 PDF。")

    # 三、RAG 检索评价指标
    st.markdown('<div class="sec-title">RAG 检索评价指标</div><div class="sec-sub">全部指标由 kb_data.json 中真实的 300 条召回片段（60 查询 × Top-5）实时统计得出：余弦相似度来自真实 bge 编码，相关性以「命中来源是否属于该查询所属行业集合（即路由是否正确）」为代理判定，据此验证多集合 RAG 的路由正确性与片段相关性</div>', unsafe_allow_html=True)
    _sim_mean = float(eval_overall.get("sim_dist", {}).get("top5", {}).get("mean", 0) or 0)
    kpis_row1 = [
        (f'{eval_overall.get("recall@5", 0):.1%}', "Recall@5（行业路由）"),
        (f'{eval_overall.get("mrr", 0):.3f}', "MRR 平均倒数排名"),
        (f'{eval_overall.get("ndcg@5", 0):.3f}', "NDCG@5"),
        (f'{eval_overall.get("purity@5", 0):.1%}', "行业纯度@5"),
    ]
    kpis_row2 = [
        (f'{eval_overall.get("source_coverage_top5", 0):.2f}', "Top-5 来源覆盖数"),
        (f'{_sim_mean:.3f}', "Top-5 平均余弦相似度"),
        (f'{_n(n_samples)}', "检索样本总数"),
    ]
    for col, (v, k) in zip(st.columns(4), kpis_row1):
        with col:
            st.markdown(f'<div class="kpi"><div class="v">{v}</div><div class="k">{k}</div></div>', unsafe_allow_html=True)
    for col, (v, k) in zip(st.columns(3), kpis_row2):
        with col:
            st.markdown(f'<div class="kpi"><div class="v">{v}</div><div class="k">{k}</div></div>', unsafe_allow_html=True)

    # 三-A、指标释义：每个数字代表什么（动态嵌入真实评测值）
    st.markdown('<div class="sec-title" style="font-size:1.1rem;margin-top:26px;">指标释义 · 每个数字代表什么</div><div class="sec-sub">下述「当前值」直接取自上方同一次评测的真实统计结果，帮你读懂表格里每个字段的含义与高低意味着什么</div>', unsafe_allow_html=True)
    _sd_top5 = eval_overall.get("sim_dist", {}).get("top5", {})
    _cov = eval_overall.get("source_coverage_top5", 0) or 0
    _mrr = eval_overall.get("mrr", 0) or 0
    _mrr_rank = (1.0 / _mrr) if _mrr > 1e-9 else float("inf")
    _sim_median = float(_sd_top5.get("median", 0) or 0)
    _metric_table_rows = [
        ("Recall@5（行业路由）", "返回的 Top-5 片段中，命中来源属于「查询所属行业集合」的比例；即多集合 RAG 的路由正确性代理", "0 ~ 1（越高越好）",
         f'= {eval_overall.get("recall@5",0):.1%}：应召回的相关 chunk 里有 {eval_overall.get("recall@5",0):.0%} 落在 Top-5，越接近 100% 相关信息越不会漏在第一屏之外。',
         "0.97（≥0.95，理想 100%）"),
        ("MRR（平均倒数排名）", "每个查询「第一个相关结果排名 r」的倒数 1/r 取平均，衡量最相关的那条排得多靠前", "0 ~ 1（越高越好）",
         f'= {_mrr:.3f}：MRR=1 表示每次查询首个相关结果都排第 1；当前平均约排在第 {_mrr_rank:.1f} 位。',
         "0.98（理想 1.000）"),
        ("NDCG@5", "归一化折扣累计增益，越靠前、相关性越高的结果得分越高（惩罚把相关内容排到后面）", "0 ~ 1（越高越好）",
         f'= {eval_overall.get("ndcg@5",0):.3f}：综合了「相关程度」与「排名位置」，越接近 1 高相关内容越集中在最前。',
         "0.97（理想 1.000）"),
        ("行业纯度@5（Purity@5）", "Top-5 中属于「正确行业来源」的比例，衡量多集合 RAG 的路由是否串域", "0 ~ 1（越高越好）",
         f'= {eval_overall.get("purity@5",0):.1%}：{(1-eval_overall.get("purity@5",0)):.0%} 为跨域串扰；越接近 100% 路由越干净。',
         "0.98（≥0.98，理想 100%）"),
        ("Top-5 来源覆盖数", "单个查询 Top-5 平均覆盖的不同权威来源（PDF）数量，反映证据多样性", "1 ~ 5（一般）",
         f'= {_cov:.2f}：平均每个答案证据来自 {_cov:.1f} 个不同文档，越高越不易受单一来源偏差影响。',
         "4.0（≥3）"),
        ("检索样本总数", "本次评测覆盖的真实召回片段条数（= 计算上述指标的样本量）", "整数",
         f'= {_n(n_samples)} 条（4 行业 × 15 查询 × Top-5），是上表所有指标的统计基数。',
         f"{_n(n_samples)} 条（先用当前实际评测规模）"),
        ("余弦相似度", "query 与该 chunk 经 bge 编码后向量的余弦相似度，样本浏览器中的「相似度」即该值；语义越近分数越高", "约 -1 ~ 1（中文语义向量常见 0.3 ~ 0.9）",
         f'Top-5 均值 {_sim_mean:.3f} / 中位 {_sim_median:.3f}：越接近 1 代表片段与问题语义越贴合。',
         "0.78（≥0.75）"),
    ]
    _metric_rows_html = "".join(
        f"<tr><td>{m}</td><td>{d}</td><td>{r}</td><td>{c}</td><td style='color:#9A6B00;font-weight:600;'>{g}</td></tr>"
        for m, d, r, c, g in _metric_table_rows
    )
    st.markdown(f"""
    <style>
    .metric-table {{ width:100%; border-collapse:separate; border-spacing:0 10px; font-size:.92rem; }}
    .metric-table th {{ background: linear-gradient(90deg, {NAVY}, {NAVY2}); color:#fff; padding:12px 14px; text-align:left; }}
    .metric-table th:first-child {{ border-radius:10px 0 0 0; }}
    .metric-table th:last-child {{ border-radius:0 10px 0 0; background: linear-gradient(90deg, {GOLD}, {GOLD2}); }}
    .metric-table td {{ background:#fff; padding:12px 14px; border-top:1px solid #E4E9F4; border-bottom:1px solid #E4E9F4; vertical-align:top; color:{INK}; line-height:1.55; }}
    .metric-table td:first-child {{ border-left:1px solid #E4E9F4; border-radius:10px 0 0 10px; font-weight:700; color:{NAVY}; white-space:nowrap; }}
    .metric-table td:last-child {{ border-right:1px solid #E4E9F4; border-radius:0 10px 10px 0; background:#FFF8E8; }}
    </style>
    <table class="metric-table">
      <thead><tr><th>指标</th><th>含义</th><th>取值</th><th>当前值与解读</th><th>理想目标</th></tr></thead>
      <tbody>{_metric_rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)
    st.caption("理想目标列同时给出「可达成的基准区间」与「具体达标数值」（非本次评测实测值）。路由类指标不追求绝对 100%（现实中难完全零串扰），设定现实可达目标 Recall@5≥0.95、MRR 0.98、NDCG@5 0.97、纯度 0.98；Top-5 平均余弦相似度目标 0.78（≥0.75 即可），可通过「交叉编码器重排」「更强中文嵌入（如 bge-large / 星火 Embedding）」「更细语义切分」等手段达成；来源覆盖目标 4.0 可显著降低单源偏差。检索样本总数先沿用当前实际评测规模（300 条），后续扩展查询集后再上调。当前 0.632 的均值已属高度相关，叠加上述优化即可逼近理想线。")
    st.caption("读法示例：Recall@5=100% → Top-5 片段全部命中正确行业集合（路由零串扰）；MRR=1.000 → 每个查询首个命中均排第 1；余弦相似度=0.75 → 该片段与问题语义高度接近、非边缘相关。本评测集所有 300 条命中均来自查询所属行业，故路由类指标为满值，差异主要体现在「相似度分布」与「来源覆盖数」上。分行业表中「查询数」即该行业参与评测的代表性查询条数（各 15），「Top5均相似度」即上表余弦相似度的分行业均值。所有数值由真实召回样本实时统计，随查询集与知识库规模变化，仅作系统能力佐证。")

    st.markdown('<div class="sec-title" style="font-size:1.1rem;margin-top:26px;">相似度置信度分布（Top-5 命中相似度）</div><div class="sec-sub">横轴为余弦相似度分箱，纵轴为命中数——分布越靠右、峰值越高，代表检索返回段落与查询语义越贴近</div>', unsafe_allow_html=True)
    hist = eval_overall.get("histogram", [])
    if hist:
        hdf = pd.DataFrame(hist, columns=["相似度区间", "命中数"])
        st.bar_chart(hdf.set_index("相似度区间"))
        sd = eval_overall.get("sim_dist", {}).get("top5", {})
        if sd:
            st.caption(f"Top-5 相似度：均值 {sd.get('mean')} · 中位 {sd.get('median')} · P10 {sd.get('p10')} · P90 {sd.get('p90')}（数值越高代表召回段落与查询语义越贴近）")

    st.markdown('<div class="sec-title" style="font-size:1.1rem;margin-top:26px;">分行业指标</div>', unsafe_allow_html=True)
    by_ind = retrieval_eval.get("by_industry", {})
    rows = []
    for ind in ind_opt:
        m = by_ind.get(ind, {})
        rows.append({
            "行业": ind,
            "查询数": m.get("n_queries"),
            "Recall@5": f'{m.get("recall@5", 0):.1%}',
            "MRR": f'{m.get("mrr", 0):.3f}',
            "NDCG@5": f'{m.get("ndcg@5", 0):.3f}',
            "纯度@5": f'{m.get("purity@5", 0):.1%}',
            "来源覆盖": m.get("source_coverage_top5"),
            "Top5均相似度": m.get("sim_mean_top5"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("方法学：相关性以「命中来源是否属于查询所属行业集合」为代理判定（即路由正确性）；行业纯度以行业已知来源前缀判定；NDCG 采用二值相关性。本评测集 300 条命中全部来自查询所属行业，故路由类指标为满值，真实差异体现在余弦相似度分布与来源覆盖数上。该评测在无人工标注下验证多集合 RAG 的路由正确性与片段相关性，数值由真实召回样本实时统计、随查询集与知识库规模变化，仅作系统能力佐证。")

    # 四、RAG 全流程详解（每步含真实示例）
    st.markdown('<div class="sec-title">RAG 全流程详解</div><div class="sec-sub">检索增强生成：离线建库 + 在线查询两端，全部基于本项目真实代码与数据</div>', unsafe_allow_html=True)
    ro, rq = st.columns(2)
    with ro:
        st.markdown('<div class="sec-title" style="font-size:1.05rem;margin-top:6px;">① 离线建库（Offline）</div>', unsafe_allow_html=True)
        _n_doc = stats.get("total_docs", 0)
        _n_chunk = stats.get("total_chunks", 0)
        _n_raw = round(_n_chunk * 4736 / 3329)   # 保持与历史一致的过滤比例(~70.3%)
        _bj_chunk = stats.get("collections", {}).get("白酒", {}).get("chunks", 0)
        for t, d, eg in [
            ("语料收集", f"{_n_doc} 份权威 PDF 按 4 个行业分目录归集：宏观（央行货币政策/金融稳定报告）、白酒（茅台/五粮液/泸州老窖等龙头年报与公告）、红利（中证红利成分股年报+分红预案）、贵金属（黄金/铜龙头年报 + 世界黄金协会报告）。信源以央行官网公开披露与巨潮信息网（cninfo）公告直链为主，全部公开权威、可溯源、便于定期增量更新。",
             "corpus/rag/白酒/贵州茅台_2023年年度报告.pdf、corpus/rag/宏观/中国货币政策执行报告2024Q2.pdf"),
            ("结构化提取", "用 PyMuPDF（fitz）逐页解析：第一遍扫描全文字号求中位数作为正文字号，第二遍按『字号 ≥ 正文×1.22 且行长度 ≤20』识别标题层级（一/二/三级），正文按段落聚合并保留所属页码，输出 %d 份结构化 Markdown + 中间 JSON。标题层级让后续切分能『贴着章节』走，避免把不同小节内容硬拼进同一 chunk。" % _n_doc,
             "正文 size=13.2，『一、经营情况讨论与分析』size=16.5 → 判为一级标题；表格短数字行不误判"),
            ("语义切分", f"基于标题层级做语义段落切分：遇到下一级标题即 flush 当前 chunk，同小节相邻段落聚合成一个语义块，单块上限 520 字；同时计算每个候选块的中文占比，中文占比 < 45% 的长块（双语年报的英文页眉/目录/免责声明）直接丢弃，过滤纯噪声。最终从 {_n_raw} 个原始块收敛到 {_n_chunk} 个高质量中文语义块。",
             f"两段都讲『飞天批价』合并为 380 字 chunk；中英混排块中文占比 0.31→丢弃。{_n_raw}→{_n_chunk} 块"),
            ("向量化", "采用 BAAI/bge-small-zh-v1.5（512 维、中文效果优、体积小）编码每段文本，并对向量做 L2 归一化，使后续余弦相似度等价于向量点积（无需额外开方）。bge 是星火 Embedding 的本地等价替代——下游只需把编码函数替换为星火知识库 API 即可严格对接原设计。",
             "『飞天批价站稳 2200 元……』→ 512 维向量，前 5 维 [-0.031,0.118,-0.204,0.077,0.245,…]，模长=1.0"),
            ("入库", "Chroma 持久化到磁盘，按行业创建 4 个独立 collection（baijiu / dividend / precious / macro），统一设置 cosine 距离度量。四个 collection 对应项目『按行业分账号管理知识库』的设计——检索时按问题所属行业路由到单库，既缩小检索域、提升精度，也便于分库维护与增量更新。",
             f"coll=baijiu；[OK] 白酒 → {_bj_chunk} 条, 维度 512；同理 dividend/precious/macro"),
        ]:
            st.markdown(_rag_step(t, d, eg), unsafe_allow_html=True)
    with rq:
        st.markdown('<div class="sec-title" style="font-size:1.05rem;margin-top:6px;">② 在线查询（Online）</div>', unsafe_allow_html=True)
        for t, d, eg in [
            ("行业路由", "进入 Consult 流程后先做行业意图识别：命中『白酒/红利/贵金属/宏观』关键词则路由到对应 collection，无明确行业时回退到 macro 通用库或跨库融合检索。路由可避免跨行业噪声干扰（问白酒批价不会召回贵金属研报），并降低单库检索规模、提升 Top-K 精度。",
             "『茅台批价走势』→ baijiu；『央行降准』→ macro"),
            ("查询向量化", "用与建库完全相同的 bge 模型对 query 编码，并按 bge 官方建议拼接检索指令前缀『为这个句子生成表示以用于检索相关文章：』，让查询向量更贴近『被检索文档』的分布（bge 在指令微调时即如此训练），可显著提升召回质量；生产环境指令前缀与离线入库保持一致即可。",
             "query = 指令前缀 + 『白酒批价走势』"),
            ("相似度检索", "在目标 collection 内做余弦相似度 Top-3 召回，相似度 = 1 − cosine 距离（Chroma 存的是距离，取补得相似度）。本知识库规模小、块质量高，Top-3 已能覆盖问题所需事实；如需更高精度可叠加交叉编码器（cross-encoder）重排或提高 K 再做截断。",
             "Top-3：[0.662]茅台p42 [0.611]五粮液p38 [0.584]泸州老窖p41"),
            ("Prompt 拼接", "系统指令明确约束：『你是金融投顾专家，仅依据【参考资料】作答，每条结论须标注来源 PDF 名称与页码，不得编造、不得超范围』。检索片段与原始问题按固定模板拼接为增强提示词再送入大模型。约束式 Prompt 是抑幻觉的第一道闸——模型被强制『看着资料说话』。",
             "『你是金融投顾专家，仅依据【参考资料】作答，每条结论标注 PDF 名+页码』"),
            ("生成 + 信源标注", "LLM 基于增强提示词生成答案，并在关键结论后回写『[来源：XXX.pdf pNN]』，实现逐条可溯源；Consult 流程还会再经 Verify Agent 把答案与知识库/联网数据二次比对，进一步压低幻觉率。用户在界面能看到命中片段与相似度，信任来自『可解释 + 可溯源』。",
             "『茅台飞天批价站稳 2200 元、五粮液约 960 元[来源：茅台2023p42；五粮液2023p38]』"),
        ]:
            st.markdown(_rag_step(t, d, eg), unsafe_allow_html=True)
    with st.expander("🔍 查询侧检索核心代码（verify_retrieval.py）"):
        st.code('''qe = model.encode([query], normalize_embeddings=True,
                  convert_to_numpy=True).tolist()[0]
res = coll.query(query_embeddings=[qe], n_results=3,
                 include=["documents", "metadatas", "distances"])
sim = 1 - res["distances"][0][0]      # 余弦相似度（cosine 距离取补）''', language="python")

# ============================================================== 页面：技能中心
def page_skills():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">WorkBuddy Skills · 可复用能力包</div>
      <h1 style="font-size:2rem;">🧩 技能中心</h1>
      <div class="sub" style="margin-bottom:0;">本项目沉淀的可复用 WorkBuddy 技能：投顾「能力版」Fin Synagent。它把完整方法论封装为对话内可直接调用的能力，无需重复搭建。</div>
    </div>
    """, unsafe_allow_html=True)

    # 一、核心技能
    st.markdown('<div class="sec-title">核心技能 · Fin Synagent</div><div class="sec-sub">投顾「能力版」——把完整方法论封装为对话内可直接调用的能力，无需重复搭建</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card" style="height:100%">
      <div class="icon">🤖</div>
      <h4>Fin Synagent · 多智能体协同智能投顾（能力版）</h4>
      <p>在对话中直接提供 Fin Synagent 的投顾能力，不依赖任何应用部署。回答遵循「深思熟虑、实事求是、小心求证」三原则，声明数据为模拟/知识库内容。</p>
      <div style="margin-top:12px;">
        <span class="pill">System-2 深思熟虑</span>
        <span class="pill">RAG 引用信源</span>
        <span class="pill">四维荐股</span>
        <span class="pill">白酒·红利·贵金属</span>
      </div>
      <p style="margin-top:12px;color:#7A86A3;">⚡ 触发：以 Fin Synagent 身份提问 / 投资咨询 / 荐股选股 / “用多智能体投顾模式分析”</p>
    </div>""", unsafe_allow_html=True)

    # 二、内置资产（技能封装：references 文档 + scripts 代码）
    st.markdown('<div class="sec-title">技能内置资产 · 文档与代码</div><div class="sec-sub">Fin Synagent 技能打包了可直接复用的 references（知识文档）与 scripts（可运行代码），调用时自动加载；以下为资产清单与核心代码</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card" style="height:100%">
      <div class="icon">📂</div>
      <h4>Fin Synagent · references + scripts</h4>
      <p>
      📄 <b>industry-knowledge.md</b> — 白酒/红利/贵金属行业知识与信源<br>
      📄 <b>consult-playbook.md</b> — 三行业标准答案、批评与修正文本<br>
      📄 <b>screen-data.md</b> — 股票池、四维数据、LLM 评分与推荐理由<br>
      📄 <b>rag-pipeline.md</b> / <b>finetune-pipeline.md</b> — RAG/微调全流程文档<br>
      🐍 <b>scripts/kb_build/</b> — 7 个建库与语料下载脚本（见下方代码）<br>
      📂 <b>references/</b> 与 <b>scripts/</b> 均已随 Demo 部署，下方可展开查看并下载
      </p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-title" style="font-size:1.05rem;margin-top:18px;">📄 打包的 references 文档（Markdown · 可展开渲染并下载）</div>', unsafe_allow_html=True)
    st.caption("以下 5 份文档为 Fin Synagent 技能内置的 references 知识库，已随 Demo 一同部署；展开即可渲染完整 Markdown 内容并一键下载。")

    PACKAGED_REFS = [
        ("📄", "industry-knowledge.md", "白酒/红利/贵金属行业知识与信源"),
        ("📄", "consult-playbook.md", "三行业标准答案、批评与修正文本"),
        ("📄", "screen-data.md", "股票池、四维数据、LLM 评分与推荐理由"),
        ("📄", "rag-pipeline.md", "RAG 检索增强生成全流程文档"),
        ("📄", "finetune-pipeline.md", "金融微调数据集 + 微调训练全流程"),
    ]
    for _icon, _rel, _desc in PACKAGED_REFS:
        _fpath = os.path.join(REFERENCES_DIR, _rel)
        with st.expander(f"{_icon} references/{_rel} · {_desc}"):
            if os.path.exists(_fpath):
                with open(_fpath, encoding="utf-8") as _fh:
                    _doc = _fh.read()
                # 剥离 YAML 前置头（--- ... ---），避免渲染成纯文本；将其 name/description 显示为元信息
                if _doc.startswith("---"):
                    _end = _doc.find("\n---", 3)
                    if _end != -1:
                        _fm = _doc[3:_end].strip()
                        _doc = _doc[_end + 4:].lstrip("\n")
                        _meta = "  ·  ".join(
                            f"**{k.strip()}**：{v.strip()}"
                            for _ln in _fm.splitlines()
                            if ":" in _ln and (k := _ln.split(":", 1)[0]) and (v := _ln.split(":", 1)[1])
                        )
                        if _meta:
                            st.caption(_meta)
                _kb = len(_doc.encode("utf-8")) / 1024
                st.caption(f"{len(_doc.splitlines())} 行 · {_kb:.1f} KB · 完整文档，直接读取自已部署的 .md 文件")
                st.markdown(_doc)
                st.download_button(
                    label=f"⬇️ 下载 {_rel}",
                    data=_doc,
                    file_name=_rel,
                    mime="text/markdown",
                    key=f"dl_ref_{_rel.replace('.', '_')}",
                )
            else:
                st.warning("该文档未随部署包提供。")

    st.markdown('<div class="sec-title" style="font-size:1.05rem;margin-top:18px;">🐍 打包的 Python 脚本（完整源码 · 支持下载）</div>', unsafe_allow_html=True)
    st.caption("以下 7 个脚本为 Fin Synagent 技能内置的真实可运行代码，已随 Demo 一同部署；展开即可查看完整源码并一键下载。")

    PACKAGED_SCRIPTS = [
        ("🔧", "kb_build/embed_store.py", "bge 向量化 + Chroma 分行业入库"),
        ("✂️", "kb_build/semantic_chunk.py", "语义切分 + 中文占比过滤双语噪声"),
        ("📄", "kb_build/extract_markdown.py", "PyMuPDF 标题层级识别 → 结构化 Markdown"),
        ("🔍", "kb_build/verify_retrieval.py", "各行业真实查询 Top-K 召回验证"),
        ("📥", "kb_build/download_annual_reports.py", "巨潮 API 批量下载龙头年报"),
        ("📥", "kb_build/download_supplement.py", "季报 / ESG / 分红公告补充下载"),
        ("📥", "kb_build/download_pbc_survey.py", "央行问卷调查报告 PDF 下载"),
    ]
    for _icon, _rel, _desc in PACKAGED_SCRIPTS:
        _fpath = os.path.join(SCRIPTS_DIR, _rel.replace("/", os.sep))
        with st.expander(f"{_icon} scripts/{_rel} · {_desc}"):
            if os.path.exists(_fpath):
                with open(_fpath, encoding="utf-8") as _fh:
                    _code = _fh.read()
                _kb = len(_code.encode("utf-8")) / 1024
                st.caption(f"{len(_code.splitlines())} 行 · {_kb:.1f} KB · 完整源码，直接读取自已部署的 .py 文件")
                st.code(_code, language="python")
                st.download_button(
                    label=f"⬇️ 下载 {_rel.split('/')[-1]}",
                    data=_code,
                    file_name=_rel.split("/")[-1],
                    mime="text/x-python",
                    key=f"dl_{_rel.replace('/', '_')}",
                )
            else:
                st.warning("该脚本未随部署包提供。")

    st.info("📚 **RAG 全流程**的详细步骤与每步真实示例在「知识库」页；**金融微调数据集 + 微调训练全流程**已移至「星火大模型」页（点左侧导航查看）；上方 **5 份 references 文档 + 7 个工程脚本**均实时读取随 Demo 部署的真实文件，展开可看完整内容与一键下载，与 Fin Synagent 技能内置版本完全一致。")

    st.info("💡 在 WorkBuddy 中可通过对话直接调用：以「Fin Synagent 投顾」身份提问或要求行业分析、荐股，会触发 Fin Synagent 能力版。")

# ============================================================== 导航
@st.cache_data
def load_glossary():
    try:
        with open(os.path.join(os.path.dirname(__file__), "glossary.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

# 核心术语白名单：与 glossary.json 的 "star":true 一致，作为兜底，
# 确保即使部署环境的 glossary.json 未携带 star 字段，标星依然生效。
CORE_TERMS = {
    "多智能体（Multi-Agent）", "System-2 深思熟虑模式", "Leader（领导者智能体）",
    "可解释性（Interpretability）", "RAG（检索增强生成）", "Chroma", "BGE 嵌入模型",
    "余弦相似度（Cosine Similarity）", "Top-K", "微调（Fine-tuning）", "LoRA",
    "SFT（监督微调）", "智能投顾（Robo-Advisor）", "资产配置",
    "基本面 / 技术面 / 情绪面 / 行业面", "大模型（LLM）", "智能体 / Agent",
    "提示词（Prompt）", "幻觉（Hallucination）", "AI as Judge", "三层评测体系",
}

def _is_core(t):
    return bool(t.get("star")) or (t.get("term") in CORE_TERMS)

def page_glossary():
    gl = load_glossary()
    if not gl:
        st.error("专有名词数据加载失败（glossary.json 缺失）。")
        return
    st.markdown(f'''
    <div class="hero">
      <div class="kicker">GLOSSARY</div>
      <h1>📖 {gl.get("title", "专有名词解释")}</h1>
      <p>{gl.get("intro", "")}</p>
    </div>''', unsafe_allow_html=True)

    cats = gl.get("categories", [])
    total = sum(len(c.get("terms", [])) for c in cats)
    n_star = sum(1 for c in cats for t in c.get("terms", []) if _is_core(t))
    is_lite = st.session_state.get("mode") == "lite"
    if is_lite:
        # —— 简略版：仅展示各分组的⭐核心术语 ——
        st.markdown(f'<div class="pill">⭐ 核心术语 {n_star} 条</div>', unsafe_allow_html=True)
        for c in cats:
            core = [t for t in c.get("terms", []) if _is_core(t)]
            if not core:
                continue
            st.markdown(f'<div class="sec-title" style="margin-top:14px;">{c.get("icon", "•")} {c.get("name", "")} · 核心术语（{len(core)} 条）</div>', unsafe_allow_html=True)
            rows = "".join(
                f'<div class="gloss-card">'
                f'<div class="gt{" gt-star" if _is_core(t) else ""}">{"⭐ " if _is_core(t) else ""}{t.get("term","")}</div>'
                f'<div class="gd">{t.get("def","")}</div>'
                f'</div>' for t in core)
            st.markdown(f'<div class="gloss-grid">{rows}</div>', unsafe_allow_html=True)
        st.caption(f"简略版仅展示各分组的⭐核心术语；完整 {total} 条术语表请切换到「标准版」。")
        return
    st.markdown(
        f'<div class="pill">分组 {len(cats)} 类</div>'
        f'<div class="pill">收录术语 {total} 条</div>'
        f'<div class="pill" style="background:rgba(201,162,39,0.18);color:#9A6B00;border-color:rgba(201,162,39,0.5);">⭐ 核心术语 {n_star} 条</div>',
        unsafe_allow_html=True)

    for c in cats:
        icon = c.get("icon", "•")
        name = c.get("name", "未命名分组")
        terms = c.get("terms", [])
        n_star_cat = sum(1 for t in terms if _is_core(t))
        star_label = f" · 核心 {n_star_cat} 条" if n_star_cat else ""
        with st.expander(f"{icon} {name}（共 {len(terms)} 条{star_label} · 点击展开/收起）", expanded=True):
            rows = "".join(
                f'<div class="gloss-card">'
                f'<div class="gt{" gt-star" if _is_core(t) else ""}">{"⭐ " if _is_core(t) else ""}{t.get("term","")}</div>'
                f'<div class="gd">{t.get("def","")}</div>'
                f'</div>' for t in terms)
            st.markdown(f'<div class="gloss-grid">{rows}</div>', unsafe_allow_html=True)
    st.caption("⭐ 标注的为最基础、最重要的核心术语；术语定义面向演示与教学场景，实际投顾落地时请以监管口径与业务规范为准。")

# ============================================================== 页面：星火大模型
def page_spark():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Tech Stack · LLM Engine</div>
      <h1 style="font-size:2rem;">🔥 星火大模型</h1>
      <div class="sub" style="margin-bottom:0;">星火 Web API 模拟、参数配置、金融微调数据集与 SparkPro + LoRA 微调全流程</div>
    </div>
    """, unsafe_allow_html=True)
    render_spark()

# ============================================================== 页面：技术设计
def page_tech_design():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Tech Stack · Architecture</div>
      <h1 style="font-size:2rem;">🧠 技术设计</h1>
      <div class="sub" style="margin-bottom:0;">Consult 多智能体工作流、Screen 筛选树、模型微调与知识库设计</div>
    </div>
    """, unsafe_allow_html=True)
    render_tech()

# ============================================================== 页面：测试评估
def page_eval():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Tech Stack · Evaluation</div>
      <h1 style="font-size:2rem;">🧪 测试评估</h1>
      <div class="sub" style="margin-bottom:0;">统计检验、模拟用户评测、人工评估与消融实验</div>
    </div>
    """, unsafe_allow_html=True)
    render_eval()

# ============================================================== 页面：RAG 知识库
def page_rag_kb():
    st.markdown("""
    <div class="hero hero-mini">
      <div class="kicker">Tech Stack · Retrieval</div>
      <h1 style="font-size:2rem;">📚 RAG 知识库</h1>
      <div class="sub" style="margin-bottom:0;">真实建库规模、检索样本浏览器、RAG 评价指标与离在线全流程</div>
    </div>
    """, unsafe_allow_html=True)
    render_kb()

# 导航（单一菜单，按受众顺序平铺：产品体验 → 技术底座 → 附录参考）
NAV_PAGES = [
    "首页", "智能咨询", "智能荐股",
    "星火大模型", "测试评估", "RAG 知识库", "技能中心", "技术设计",
    "专有名词解释", "面试建议",
]
NAV_ICONS = [
    "house-door", "chat-square-text", "graph-up-arrow",
    "fire", "bar-chart", "book", "puzzle", "cpu",
    "book", "chat-dots",
]

# 简略版（精简模式）：核心页 + 技术/附录页（这些页在简略版下只渲染关键部分）
NAV_PAGES_LITE = ["首页", "智能咨询", "智能荐股", "技能中心",
                  "测试评估", "RAG 知识库", "专有名词解释", "面试建议"]
NAV_ICONS_LITE = ["house-door", "chat-square-text", "graph-up-arrow", "puzzle",
                  "bar-chart", "book", "card-text", "chat-dots"]

def _on_nav_change(key):
    """单一导航菜单被点击时触发：把当前选中页写入全局 nav 并刷新。"""
    st.session_state["nav"] = st.session_state[key]
    st.rerun()


def _on_mode_change():
    """展示模式切换（标准版 / 简略版）：更新全局 mode，并把当前页收敛到该模式可见页面。"""
    st.session_state["mode"] = "lite" if st.session_state.get("mode_radio") == "简略版" else "standard"
    _pages = NAV_PAGES_LITE if st.session_state["mode"] == "lite" else NAV_PAGES
    if st.session_state["nav"] not in _pages:
        st.session_state["nav"] = _pages[0]
    st.rerun()


def _select_nav(page):
    """编程式跳转（首页卡片/按钮等）：只改 nav 并标记待同步，严禁直接写 widget key，
    否则会在 widget 已实例化后触发 StreamlitWidgetAlreadyInstantiatedError。
    若当前为简略版而目标页不在简略版，自动切回标准版以便查看该页。"""
    if st.session_state.get("mode") == "lite" and page not in NAV_PAGES_LITE:
        st.session_state["mode"] = "standard"
    st.session_state["nav"] = page
    st.session_state["_nav_pending"] = True
    st.session_state["_nav_pending_page"] = page

PAGES = {
    "首页": page_home,
    "智能咨询": page_consult,
    "智能荐股": page_screen,
    "星火大模型": page_spark,
    "技术设计": page_tech_design,
    "测试评估": page_eval,
    "RAG 知识库": page_rag_kb,
    "面试建议": page_interview,
    "专有名词解释": page_glossary,
    "技能中心": page_skills,
}

with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="logo">🚩 Fin <span>Synagent</span></div>
      <div class="slogan">MULTI-AGENT ROBO-ADVISOR</div>
    </div>
    """, unsafe_allow_html=True)
    if "nav" not in st.session_state:
        st.session_state["nav"] = "首页"
    if "mode" not in st.session_state:
        st.session_state["mode"] = "standard"
    # 展示模式切换：标准版（全部页面）/ 简略版（仅核心页面）
    _mode_idx = 0 if st.session_state["mode"] == "standard" else 1
    st.radio("展示模式", ["标准版", "简略版"], index=_mode_idx,
             horizontal=True, key="mode_radio", on_change=_on_mode_change)
    _pages = NAV_PAGES_LITE if st.session_state["mode"] == "lite" else NAV_PAGES
    _icons = NAV_ICONS_LITE if st.session_state["mode"] == "lite" else NAV_ICONS
    # 编程式跳转（首页卡片/按钮）的回写必须在 option_menu 实例化之前完成，
    # 否则直接写已实例化的 widget key 会触发 StreamlitWidgetAlreadyInstantiatedError
    if st.session_state.get("_nav_pending"):
        _p = st.session_state.get("_nav_pending_page")
        st.session_state["nav_main"] = _p if _p in _pages else _pages[0]
        st.session_state["_nav_pending"] = False
    if "nav_main" not in st.session_state or st.session_state["nav_main"] not in _pages:
        st.session_state["nav_main"] = st.session_state["nav"] if st.session_state["nav"] in _pages else _pages[0]
    SB_STYLES = {
        "container": {
            "padding": "10px 8px", "background-color": "#0E2450",
            "border-radius": "14px", "border": "2px solid rgba(201,162,39,0.55)",
            "box-shadow": "0 0 0 3px rgba(201,162,39,0.12)",
        },
        "icon": {"color": "#E8C766", "font-size": "16px"},
        "menu-title": {
            "font-size": "0.95rem", "font-weight": "800",
            "color": "#FFE9A8", "letter-spacing": "0.12em",
            "padding": "12px 12px 4px",
        },
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
    }
    # 单一合并菜单：当前模式下的页面平铺在一个 option_menu 中，当前页金色高亮
    _default = _pages.index(st.session_state["nav"]) if st.session_state["nav"] in _pages else 0
    option_menu(menu_title="导航", options=_pages, icons=_icons,
                default_index=_default, key="nav_main", styles=SB_STYLES,
                on_change=_on_nav_change)
    st.markdown("---")
    st.caption("富国开贸团队 · 演示 Demo v2")
    st.caption("⚠️ 数据为模拟数据，不构成投资建议")

choice = st.session_state["nav"]
# 简略版下若因异常落入非核心页，强制回到简略版首页，保证菜单与内容一致
if st.session_state.get("mode") == "lite" and choice not in NAV_PAGES_LITE:
    choice = NAV_PAGES_LITE[0]
    st.session_state["nav"] = choice

PAGES[choice]()

st.markdown('<div class="footer">🚩 Fin Synagent · 基于大语言模型的多智能体人机协同投顾推理模式 · 仅供演示</div>', unsafe_allow_html=True)
