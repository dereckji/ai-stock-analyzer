#!/bin/bash
# AI 股票分析助手 - Mac 一键启动（体验优化版）

set -e
cd "$(dirname "$0")"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo ""
echo "═══════════════════════════════════════════════════════"
echo "          📈 AI 股票分析助手 (Mac 版)"
echo "═══════════════════════════════════════════════════════"
echo ""

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未检测到 python3${NC}"
    echo ""
    echo "Mac 安装 Python 最简单方式："
    echo "  1. 打开「终端」(在启动台搜「终端」)"
    echo "  2. 输入以下命令并回车："
    echo "     /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "  3. 安装完后输入："
    echo "     brew install python@3.11"
    echo ""
    echo "或者直接从官网下载安装："
    echo "  https://www.python.org/downloads/macos/"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python 版本: $PYTHON_VERSION"

# 清理之前打包失败的残留
if [ -d "build_venv" ]; then
    echo -e "${BLUE}ℹ${NC} 清理之前的打包残留 (build_venv)..."
    rm -rf build_venv build dist
fi

# 检查并清理 8501 端口
if lsof -ti:8501 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC} 端口 8501 被占用，清理旧进程..."
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 创建虚拟环境（避免污染系统 Python）
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[1/3]${NC} 首次运行，创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate
echo -e "${GREEN}✓${NC} 虚拟环境已激活"

# 安装依赖
echo -e "${YELLOW}[2/3]${NC} 检查并安装依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
echo -e "${GREEN}✓${NC} 依赖就绪"

# 启动应用
echo -e "${YELLOW}[3/3]${NC} 启动应用..."
echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "  ${GREEN}应用已启动！${NC}"
echo ""
echo "  浏览器会自动打开，如未自动打开请手动访问："
echo -e "  ${GREEN}http://localhost:8501${NC}"
echo ""
echo "  关闭应用：按 Ctrl+C 或关闭此窗口"
echo "═══════════════════════════════════════════════════════"
echo ""

# 后台延迟 4 秒后自动打开浏览器（给 streamlit 启动留时间）
(
  sleep 4
  URL="http://localhost:8501"
  # 优先用默认浏览器，否则 Safari
  open "$URL" 2>/dev/null || open -a Safari "$URL" 2>/dev/null || true
) &

# 启动 streamlit
streamlit run app.py

# 应用关闭后
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  应用已停止"
echo "═══════════════════════════════════════════════════════"
