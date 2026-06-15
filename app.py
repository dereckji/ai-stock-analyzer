# -*- coding: utf-8 -*-
"""
AI 股票分析助手 - Streamlit 简易界面
基于 DeepSeek API + AkShare 实时数据
"""

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="AI 股票分析助手",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 侧边栏配置
# ============================================================
with st.sidebar:
    st.title("⚙️ 配置")

    api_key = st.text_input(
        "DeepSeek API Key",
        value=st.session_state.get("api_key", ""),
        type="password",
        help="到 platform.deepseek.com 注册获取"
    )
    st.session_state["api_key"] = api_key

    st.divider()

    market = st.radio(
        "市场",
        ["A股", "港股", "美股"],
        index=0,
        horizontal=True
    )

    # 预设股票
    st.divider()
    st.caption("📋 快速选择")
    preset_stocks = {
        "A股": ["000628 高新发展", "600519 贵州茅台", "601318 中国平安", "300750 宁德时代"],
        "港股": ["00700 腾讯控股", "09988 阿里巴巴", "03690 美团"],
        "美股": ["AAPL 苹果", "TSLA 特斯拉", "NVDA 英伟达", "MSFT 微软"]
    }
    preset = st.selectbox("热门股票", ["自定义"] + preset_stocks[market])

    if preset != "自定义":
        default_code = preset.split()[0]
    else:
        default_code = ""

    stock_code = st.text_input("股票代码", value=default_code, placeholder="如 000628")

    st.divider()

    analysis_depth = st.select_slider(
        "分析深度",
        options=["快速", "标准", "深度"],
        value="标准",
        help="深度越大，调用 LLM 次数越多，耗时越长"
    )

    run_btn = st.button("🚀 开始分析", type="primary", use_container_width=True)

    st.divider()
    st.caption("💡 提示")
    st.caption("• 标准分析约 30-60 秒")
    st.caption("• 深度分析约 1-3 分钟")
    st.caption("• 数据来源：东方财富 / 新浪财经")


# ============================================================
# 数据获取层
# ============================================================
# 尝试导入 akshare，本地安装后会自动使用
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    st.warning("⚠️ 未安装 akshare，请运行 `pip install akshare` 获取实时数据")


def _mock_realtime_data(code):
    """演示用 mock 数据（当 akshare 不可用时）"""
    return {
        "代码": code,
        "名称": f"演示股票{code}",
        "最新价": 18.50,
        "涨跌额": 0.32,
        "涨跌幅%": 1.76,
        "最高": 18.80,
        "最低": 18.10,
        "今开": 18.18,
        "昨收": 18.18,
        "成交量": 152300,
        "成交额": 281750000,
        "市盈率": 22.5,
        "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def _mock_kline_data(code, days=30):
    """演示用 mock K线数据"""
    import numpy as np
    np.random.seed(hash(code) % 1000)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    base = 18.0
    closes = base + np.cumsum(np.random.randn(days) * 0.3)
    df = pd.DataFrame({
        "日期": dates.strftime("%Y-%m-%d"),
        "开盘": closes - np.random.rand(days) * 0.2,
        "收盘": closes,
        "最高": closes + np.random.rand(days) * 0.3,
        "最低": closes - np.random.rand(days) * 0.3,
        "成交量": np.random.randint(50000, 200000, days),
        "成交额": np.random.randint(80000000, 300000000, days).astype(float),
        "振幅%": np.random.rand(days) * 4,
        "涨跌幅%": np.random.randn(days) * 1.5,
        "换手率%": np.random.rand(days) * 5
    })
    return df


def _get_realtime_sina(code):
    """新浪财经实时行情（A股）"""
    # 沪市加 sh，深市加 sz
    if code.startswith(("6", "9")):
        symbol = f"sh{code}"
    else:
        symbol = f"sz{code}"
    url = f"https://hq.sinajs.cn/list={symbol}"
    headers = {"Referer": "https://finance.sina.com.cn"}
    r = requests.get(url, headers=headers, timeout=8)
    text = r.text.strip()
    # 格式: var hq_str_sh600000="兆易创新,150.000,149.500,...";
    if '""' in text or not text:
        return None
    quote_part = text.split('"', 1)[1].split('"')[0]
    fields = quote_part.split(',')
    # 新浪字段: 名称,今开,昨收,最新价,最高,最低,买一,卖一,成交量,成交额,...
    if len(fields) < 32:
        return None
    name = fields[0]
    open_p = float(fields[1] or 0)
    prev_close = float(fields[2] or 0)
    current = float(fields[3] or 0)
    high = float(fields[4] or 0)
    low = float(fields[5] or 0)
    volume = int(float(fields[8] or 0))  # 股
    amount = float(fields[9] or 0)       # 元
    change = current - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0
    return {
        "代码": code,
        "名称": name,
        "最新价": current,
        "涨跌额": round(change, 3),
        "涨跌幅%": round(change_pct, 2),
        "最高": high,
        "最低": low,
        "今开": open_p,
        "昨收": prev_close,
        "成交量": volume,
        "成交额": amount,
        "市盈率": 0,
        "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def _get_realtime_tx(code):
    """腾讯财经实时行情（A股）"""
    if code.startswith(("6", "9")):
        symbol = f"sh{code}"
    else:
        symbol = f"sz{code}"
    url = f"https://qt.gtimg.cn/q={symbol}"
    r = requests.get(url, timeout=8)
    text = r.text.strip()
    # 格式: v_sh600000="1~兆易创新~600000~150.00~149.50~...~";
    if '""' in text or '~' not in text:
        return None
    parts = text.split('"')[1].split('~')
    if len(parts) < 35:
        return None
    name = parts[1]
    current = float(parts[3] or 0)
    prev_close = float(parts[4] or 0)
    open_p = float(parts[5] or 0)
    volume = int(float(parts[6] or 0))  # 手
    amount = float(parts[37] or 0) if len(parts) > 37 else 0
    high = float(parts[33] or 0)
    low = float(parts[34] or 0)
    change = current - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0
    return {
        "代码": code,
        "名称": name,
        "最新价": current,
        "涨跌额": round(change, 3),
        "涨跌幅%": round(change_pct, 2),
        "最高": high,
        "最低": low,
        "今开": open_p,
        "昨收": prev_close,
        "成交量": volume * 100,  # 手转股
        "成交额": amount,
        "市盈率": 0,
        "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def _get_realtime_eastmoney(code):
    """东方财富实时行情（A股）"""
    if code.startswith(("6", "9")):
        secid = f"1.{code}"
    else:
        secid = f"0.{code}"
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "secid": secid,
        "fields": "f43,f44,f45,f46,f47,f48,f58,f60,f169,f170,f171",
        "invt": 2,
        "fltt": 2
    }
    r = requests.get(url, params=params, timeout=8)
    data = r.json().get("data", {})
    if not data:
        return None
    return {
        "代码": code,
        "名称": data.get("f58", "N/A"),
        "最新价": data.get("f43", 0) / 100,
        "涨跌额": data.get("f169", 0) / 100,
        "涨跌幅%": data.get("f170", 0) / 100,
        "最高": data.get("f44", 0) / 100,
        "最低": data.get("f45", 0) / 100,
        "今开": data.get("f46", 0) / 100,
        "昨收": data.get("f60", 0) / 100,
        "成交量": data.get("f47", 0),
        "成交额": data.get("f48", 0),
        "市盈率": data.get("f171", 0) / 100,
        "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@st.cache_data(ttl=300)
def get_stock_realtime(code, market="A股"):
    """获取实时行情（多源 fallback：东方财富 → 新浪 → 腾讯）"""
    if market != "A股":
        return _mock_realtime_data(code)

    # 多个数据源依次尝试（新浪和腾讯稳定，东方财富常被封）
    sources = [
        ("新浪财经", _get_realtime_sina),
        ("腾讯财经", _get_realtime_tx),
        ("东方财富", _get_realtime_eastmoney),
    ]
    for source_name, source_func in sources:
        try:
            data = source_func(code)
            if data and data.get("最新价", 0) > 0:
                return data
        except Exception as e:
            continue

    st.warning(f"所有数据源均失败（{code}），使用演示数据")
    return _mock_realtime_data(code)


def _get_kline_sina(code, days):
    """新浪财经 K 线"""
    if code.startswith(("6", "9")):
        symbol = f"sh{code}"
    else:
        symbol = f"sz{code}"
    # scale=240 日K, 1=不复权
    url = f"https://quotes.money.163.com/service/chddata.html"
    # 新浪接口比较复杂，用网易备用
    # 改用腾讯
    return None


def _get_kline_tx(code, days):
    """腾讯财经 K 线"""
    if code.startswith(("6", "9")):
        symbol = f"sh{code}"
    else:
        symbol = f"sz{code}"
    # klt=101 日K, fqt=1 前复权
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {
        "param": f"{symbol},day,,,{days},qfq"
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if data.get("code") != 0:
        return None
    klines = data.get("data", {}).get(symbol, {}).get("day") or \
             data.get("data", {}).get(symbol, {}).get("qfqday")
    if not klines:
        return None
    rows = []
    for k in klines:
        if len(k) < 6:
            continue
        rows.append({
            "日期": k[0],
            "开盘": float(k[1]),
            "收盘": float(k[2]),
            "最高": float(k[3]),
            "最低": float(k[4]),
            "成交量": int(float(k[5])),
            "成交额": 0,
            "振幅%": 0,
            "涨跌幅%": 0,
            "换手率%": 0
        })
    if not rows:
        return None
    return pd.DataFrame(rows)


def _get_kline_eastmoney(code, days):
    """东方财富 K 线"""
    if code.startswith(("6", "9")):
        secid = f"1.{code}"
    else:
        secid = f"0.{code}"
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": 101,
        "fqt": 1,
        "end": "20500101",
        "lmt": days
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json().get("data", {})
    klines = data.get("klines", [])
    if not klines:
        return None
    rows = []
    for k in klines:
        parts = k.split(",")
        if len(parts) < 11:
            continue
        rows.append({
            "日期": parts[0],
            "开盘": float(parts[1]),
            "收盘": float(parts[2]),
            "最高": float(parts[3]),
            "最低": float(parts[4]),
            "成交量": int(parts[5]),
            "成交额": float(parts[6]),
            "振幅%": float(parts[7]),
            "涨跌幅%": float(parts[8]),
            "换手率%": float(parts[10]) if len(parts) > 10 else 0
        })
    return pd.DataFrame(rows) if rows else None


@st.cache_data(ttl=3600)
def get_kline_data(code, days=30, market="A股"):
    """获取 K 线数据（多源 fallback）"""
    if market != "A股":
        return _mock_kline_data(code, days)

    # 多个数据源依次尝试（腾讯 K 线稳定）
    sources = [
        ("腾讯财经", _get_kline_tx),
        ("东方财富", _get_kline_eastmoney),
    ]
    for source_name, source_func in sources:
        try:
            df = source_func(code, days)
            if df is not None and not df.empty:
                return df
        except Exception:
            continue

    st.warning(f"K线数据获取失败（{code}），使用演示数据")
    return _mock_kline_data(code, days)


def calc_technical_indicators(df):
    """计算技术指标"""
    if df.empty or len(df) < 20:
        return {}

    close = df["收盘"]
    result = {}

    # 均线
    result["MA5"] = round(close.tail(5).mean(), 2)
    result["MA10"] = round(close.tail(10).mean(), 2)
    result["MA20"] = round(close.tail(20).mean(), 2)

    # 当前价相对均线
    cur = close.iloc[-1]
    result["当前价"] = round(cur, 2)

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).tail(14).mean()
    loss = (-delta.where(delta < 0, 0)).tail(14).mean()
    if loss > 0:
        rs = gain / loss
        result["RSI14"] = round(100 - (100 / (1 + rs)), 2)
    else:
        result["RSI14"] = 100

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9).mean()
    macd = (dif - dea) * 2
    result["MACD_DIF"] = round(dif.iloc[-1], 3)
    result["MACD_DEA"] = round(dea.iloc[-1], 3)
    result["MACD_BAR"] = round(macd.iloc[-1], 3)

    # 近期表现
    result["5日涨幅%"] = round((cur / close.iloc[-6] - 1) * 100, 2) if len(close) >= 6 else 0
    result["20日涨幅%"] = round((cur / close.iloc[-21] - 1) * 100, 2) if len(close) >= 21 else 0

    # 成交量
    result["5日均量"] = int(df["成交量"].tail(5).mean())
    result["今日量比"] = round(df["成交量"].iloc[-1] / df["成交量"].tail(5).mean(), 2)

    return result


# ============================================================
# AI 分析层
# ============================================================
def call_deepseek(prompt, system_prompt="你是一位专业的股票投资分析师", max_tokens=2000):
    """调用 DeepSeek API"""
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return None, "❌ 请先在侧边栏填写 DeepSeek API Key"

    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "stream": False
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        result = r.json()
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        return content, usage
    except requests.exceptions.Timeout:
        return None, "⏱️ 请求超时，请重试"
    except Exception as e:
        return None, f"❌ API 调用失败: {e}"


def format_stock_context(realtime, tech, kline_df):
    """格式化股票数据为 AI Prompt"""
    context = f"""
【实时行情】
- 股票代码：{realtime['代码']}
- 股票名称：{realtime['名称']}
- 最新价：{realtime['最新价']} 元
- 涨跌幅：{realtime['涨跌幅%']}%
- 今开：{realtime['今开']} | 最高：{realtime['最高']} | 最低：{realtime['最低']} | 昨收：{realtime['昨收']}
- 成交量：{realtime['成交量']:,} 手
- 成交额：{realtime['成交额']:,} 元
- 市盈率：{realtime['市盈率']}

【技术指标】
- MA5：{tech.get('MA5', 'N/A')} | MA10：{tech.get('MA10', 'N/A')} | MA20：{tech.get('MA20', 'N/A')}
- RSI(14)：{tech.get('RSI14', 'N/A')}
- MACD：DIF={tech.get('MACD_DIF', 'N/A')} DEA={tech.get('MACD_DEA', 'N/A')} BAR={tech.get('MACD_BAR', 'N/A')}
- 5日涨幅：{tech.get('5日涨幅%', 'N/A')}% | 20日涨幅：{tech.get('20日涨幅%', 'N/A')}%
- 量比：{tech.get('今日量比', 'N/A')}

【近期 K 线（最近5日）】
{kline_df.tail(5)[['日期', '开盘', '收盘', '最高', '最低', '涨跌幅%', '换手率%']].to_string(index=False) if not kline_df.empty else '无数据'}
"""
    return context


# ============================================================
# 多智能体分析（简化版 4 角色）
# ============================================================
AGENT_PROMPTS = {
    "基本面分析师": """你是一位基本面分析师，擅长研究公司财务和行业地位。
请基于提供的行情数据，重点分析：
1. 估值水平（结合市盈率）
2. 财务健康度（基于价格走势和成交额间接判断）
3. 行业地位与近期表现
4. 给出基本面评分（0-100）和 1-2 句结论
格式：评分 + 结论，控制在 200 字内。""",

    "技术面分析师": """你是一位技术分析师，擅长 K 线形态和指标解读。
请基于提供的技术指标数据，重点分析：
1. 均线系统（多头/空头/缠绕）
2. MACD 信号（金叉/死叉/顶背离/底背离）
3. RSI 超买超卖
4. 量价配合（放量/缩量）
5. 给出技术面评分（0-100）和 1-2 句结论
格式：评分 + 结论，控制在 200 字内。""",

    "资金面分析师": """你是一位资金面分析师，擅长解读资金流向。
请基于成交量、量比、换手率数据，重点分析：
1. 主力资金动向（基于量能推测）
2. 筹码稳定性（换手率判断）
3. 短期资金关注度
4. 给出资金面评分（0-100）和 1-2 句结论
格式：评分 + 结论，控制在 200 字内。""",

    "综合决策师": """你是一位资深投资经理，需要综合三方观点形成最终投资建议。
请基于以下信息：
- 给出明确的投资评级（强烈买入/买入/持有/卖出/强烈卖出）
- 给出综合评分（0-100）
- 给出目标价位区间
- 给出止损位
- 列出 3 个核心买入理由和 3 个核心风险点
- 用 Markdown 格式，控制在 500 字内"""
}


def run_multi_agent_analysis(realtime, tech, kline_df, depth="标准"):
    """运行多智能体分析"""
    context = format_stock_context(realtime, tech, kline_df)
    results = {}

    progress = st.progress(0, text="🚀 AI 团队开始分析...")

    if depth == "快速":
        agents_to_run = ["综合决策师"]
    elif depth == "标准":
        agents_to_run = ["技术面分析师", "资金面分析师", "综合决策师"]
    else:  # 深度
        agents_to_run = ["基本面分析师", "技术面分析师", "资金面分析师", "综合决策师"]

    total = len(agents_to_run)
    total_tokens = 0

    for i, agent in enumerate(agents_to_run):
        progress.progress((i) / total, text=f"🤖 {agent} 思考中...")

        if agent == "综合决策师":
            # 综合决策师需要看前面所有结果
            prior = "\n\n".join([f"【{k}】\n{v}" for k, v in results.items()])
            prompt = f"{context}\n\n【各分析师观点】\n{prior}\n\n请给出最终投资建议。"
        else:
            prompt = f"{context}\n\n请从你的专业角度分析这只股票。"

        content, usage = call_deepseek(
            prompt,
            system_prompt=AGENT_PROMPTS[agent],
            max_tokens=1500 if agent == "综合决策师" else 800
        )

        if content:
            results[agent] = content
            if isinstance(usage, dict):
                total_tokens += usage.get("total_tokens", 0)
        else:
            results[agent] = f"❌ {usage}"
            return None, total_tokens

        time.sleep(0.5)  # 避免限流

    progress.progress(1.0, text="✅ 分析完成！")
    time.sleep(1)
    progress.empty()

    return results, total_tokens


# ============================================================
# 主界面
# ============================================================
st.title("📈 AI 股票分析助手")
st.caption("DeepSeek + 多智能体协作 · 实时行情 · 一键生成分析报告")

# API Key 提示
if not api_key:
    st.warning("⚠️ 请先在左侧边栏填入 DeepSeek API Key")
    st.info("💡 注册地址：https://platform.deepseek.com （新用户送额度）")
    st.stop()

# 股票代码提示
if not stock_code:
    st.info("👈 请在左侧输入股票代码后点击「开始分析」")
    st.markdown("### 📊 支持的股票示例")
    cols = st.columns(4)
    samples = [
        ("000628", "高新发展"),
        ("600519", "贵州茅台"),
        ("601318", "中国平安"),
        ("300750", "宁德时代"),
    ]
    for col, (code, name) in zip(cols, samples):
        with col:
            st.metric(label=f"{code}\n{name}", value="示例")
    st.stop()


# ============================================================
# 触发分析
# ============================================================
if run_btn:
    # 第 1 步：获取行情
    with st.spinner(f"📡 正在获取 {stock_code} 实时行情..."):
        realtime = get_stock_realtime(stock_code, market)

    if not realtime:
        st.error(f"❌ 未找到股票 {stock_code}，请检查代码是否正确")
        st.stop()

    # 显示基本信息
    st.success(f"✓ 找到 **{realtime['名称']}** ({realtime['代码']})")

    # 实时行情卡片
    col1, col2, col3, col4 = st.columns(4)
    price = realtime['最新价']
    change_pct = realtime['涨跌幅%']

    with col1:
        st.metric("最新价", f"{price} 元", f"{realtime['涨跌额']:+.2f}")
    with col2:
        delta_color = "normal" if change_pct >= 0 else "inverse"
        st.metric("涨跌幅", f"{change_pct}%", delta_color=delta_color)
    with col3:
        st.metric("今开", f"{realtime['今开']}")
    with col4:
        st.metric("市盈率", f"{realtime['市盈率']}")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("最高", f"{realtime['最高']}")
    with col6:
        st.metric("最低", f"{realtime['最低']}")
    with col7:
        st.metric("成交量", f"{realtime['成交量']:,}")
    with col8:
        st.metric("成交额", f"{realtime['成交额']:,.0f}")

    st.divider()

    # 第 2 步：获取 K 线和技术指标
    with st.spinner("📊 计算技术指标..."):
        kline_df = get_kline_data(stock_code, days=60, market=market)
        tech = calc_technical_indicators(kline_df)

    # K 线走势图
    if not kline_df.empty:
        st.subheader("📉 近期走势（60日）")
        chart_data = kline_df.set_index("日期")[["开盘", "收盘", "最高", "最低"]].astype(float)
        st.line_chart(chart_data["收盘"], height=300)

        with st.expander("📋 查看 K 线明细"):
            st.dataframe(
                kline_df.tail(20).style.format({
                    "开盘": "{:.2f}",
                    "收盘": "{:.2f}",
                    "最高": "{:.2f}",
                    "最低": "{:.2f}",
                    "涨跌幅%": "{:.2f}",
                    "换手率%": "{:.2f}"
                }),
                use_container_width=True
            )

    # 技术指标
    if tech:
        st.subheader("🔧 技术指标")
        cols = st.columns(6)
        metrics = [
            ("MA5", f"{tech.get('MA5', 0)}"),
            ("MA10", f"{tech.get('MA10', 0)}"),
            ("MA20", f"{tech.get('MA20', 0)}"),
            ("RSI14", f"{tech.get('RSI14', 0)}"),
            ("5日涨幅%", f"{tech.get('5日涨幅%', 0)}%"),
            ("量比", f"{tech.get('今日量比', 0)}"),
        ]
        for col, (label, val) in zip(cols, metrics):
            with col:
                st.metric(label, val)

    st.divider()

    # 第 3 步：AI 多智能体分析
    st.subheader("🤖 AI 多智能体分析")
    st.caption(f"分析深度：{analysis_depth} | 预计调用 {1 if analysis_depth=='快速' else 3 if analysis_depth=='标准' else 4} 次 LLM")

    start_time = time.time()
    results, total_tokens = run_multi_agent_analysis(realtime, tech, kline_df, analysis_depth)
    elapsed = time.time() - start_time

    if results:
        # 显示各 Agent 观点
        for agent, content in results.items():
            with st.expander(f"💼 {agent} 的观点", expanded=(agent == "综合决策师")):
                st.markdown(content)

        # 统计信息
        st.divider()
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("⏱️ 耗时", f"{elapsed:.1f} 秒")
        with col_b:
            st.metric("📊 Token 消耗", f"{total_tokens:,}")
        if total_tokens > 0:
            cost = total_tokens * 0.000001  # DeepSeek 价格约 1元/百万token
            with col_c:
                st.metric("💰 成本估算", f"¥{cost:.4f}")

        # 免责声明
        st.warning("""
⚠️ **免责声明**
本工具由 AI 自动生成分析结果，仅供学习研究使用，不构成任何投资建议。
股市有风险，投资需谨慎。AI 决策可能存在幻觉和错误，请独立判断。
        """)

        # 导出按钮
        report_md = f"""# AI 股票分析报告

**股票**：{realtime['名称']} ({realtime['代码']})
**分析时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析深度**：{analysis_depth}

---

## 实时行情

| 项目 | 数值 |
|---|---|
| 最新价 | {realtime['最新价']} 元 |
| 涨跌幅 | {realtime['涨跌幅%']}% |
| 今开 | {realtime['今开']} |
| 昨收 | {realtime['昨收']} |
| 最高 | {realtime['最高']} |
| 最低 | {realtime['最低']} |
| 成交量 | {realtime['成交量']:,} |
| 市盈率 | {realtime['市盈率']} |

---

## AI 团队分析

""" + "\n\n".join([f"### {k}\n\n{v}" for k, v in results.items()]) + f"""

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Token 消耗：{total_tokens:,} | 耗时：{elapsed:.1f}秒*
"""

        st.download_button(
            label="📥 下载 Markdown 报告",
            data=report_md,
            file_name=f"{realtime['代码']}_AI分析_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True
        )


# ============================================================
# 页脚
# ============================================================
st.divider()
st.caption("""
🔧 **技术栈**：Streamlit + DeepSeek API + 东方财富数据
📚 **数据来源**：公开行情数据，仅供研究使用
🤖 **AI 模型**：DeepSeek-V3 / Flash 系列
""")
