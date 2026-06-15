# AI 股票分析助手

基于 Streamlit + DeepSeek 的简易股票分析界面，集成多智能体协作分析。

## 功能特性

- 实时行情查询（A股/港股/美股）
- K线走势可视化
- 技术指标自动计算（MA/RSI/MACD/量比）
- 多智能体协作分析（基本面/技术面/资金面/综合决策）
- 三档分析深度（快速/标准/深度）
- 一键导出 Markdown 报告
- Token 消耗与成本实时统计

## 快速开始

### 1. 安装依赖

```bash
pip install streamlit requests pandas
```

### 2. 获取 API Key

到 https://platform.deepseek.com 注册并获取 API Key（新用户送额度）。

### 3. 启动应用

```bash
streamlit run app.py
```

浏览器自动打开 http://localhost:8501

### 4. 使用步骤

1. 左侧填入 DeepSeek API Key
2. 输入股票代码（如 000628）
3. 选择分析深度
4. 点击「🚀 开始分析」
5. 等待 30 秒 - 3 分钟，查看报告

## 核心架构

```
用户输入（股票代码）
       ↓
[数据层] 东方财富 API
       ↓
实时行情 + K线 + 技术指标
       ↓
[AI 层] DeepSeek 多智能体
   ├─ 基本面分析师
   ├─ 技术面分析师
   ├─ 资金面分析师
   └─ 综合决策师
       ↓
Markdown 报告 + 下载
```

## 成本说明

DeepSeek-V3 Flash 价格：
- 输入：¥0.5 / 百万 tokens
- 输出：¥1 / 百万 tokens
- 平均单次分析：约 ¥0.001 - ¥0.005

## 免责声明

本工具仅供学习研究使用，不构成投资建议。股市有风险，投资需谨慎。
