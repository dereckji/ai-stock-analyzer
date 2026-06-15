#!/bin/bash
# AI 股票分析助手 - Mac 一键打包
# 完成后会生成 .app 文件，可拖到启动台 / 桌面 / 应用程序文件夹

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo ""
echo "═══════════════════════════════════════════════════════"
echo "      📦 AI 股票分析助手 - Mac 打包工具"
echo "═══════════════════════════════════════════════════════"
echo ""

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 需要 Python 3.8+${NC}"
    echo "运行 ./启动.command 先装依赖"
    exit 1
fi

echo -e "${YELLOW}[1/4]${NC} 检查系统架构..."
ARCH=$(uname -m)
echo -e "${GREEN}✓${NC} 你的 Mac: $ARCH (Apple Silicon / Intel)"

# 创建虚拟环境
if [ ! -d "build_venv" ]; then
    echo -e "${YELLOW}[2/4]${NC} 创建打包环境..."
    python3 -m venv build_venv
fi

source build_venv/bin/activate
pip install --upgrade pip -q

# 安装打包工具
echo -e "${YELLOW}[3/4]${NC} 安装 py2app..."
pip install py2app -q
echo -e "${GREEN}✓${NC} py2app 已安装"

# 执行打包
echo -e "${YELLOW}[4/4]${NC} 开始打包（约 3-5 分钟）..."
echo "    首次打包会下载较多依赖，请耐心等待..."

# 创建 setup.py 用于 py2app
cat > setup.py << 'PYEOF'
from setuptools import setup

APP = ['app.py']
OPTIONS = {
    'argv_emulation': False,
    'packages': ['streamlit', 'akshare', 'pandas', 'numpy', 'requests', 'altair', 'toolz'],
    'iconfile': None,
    'plist': {
        'CFBundleName': 'AI股票分析',
        'CFBundleDisplayName': 'AI 股票分析助手',
        'CFBundleIdentifier': 'com.local.aistock',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0',
        'LSMinimumSystemVersion': '10.13',
        'NSHighResolutionCapable': True,
    },
    'includes': ['streamlit.web.cli', 'streamlit.runtime.scriptrunner'],
    'excludes': ['tkinter', 'matplotlib.tests', 'pytest'],
}

setup(
    app=APP,
    name='AI股票分析',
    options={'app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=['streamlit', 'akshare', 'pandas', 'requests'],
)
PYEOF

python setup.py py2app 2>&1 | tail -20

if [ -d "dist/AI股票分析.app" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo -e "  ${GREEN}✅ 打包成功！${NC}"
    echo ""
    echo "  APP 位置: $(pwd)/dist/AI股票分析.app"
    echo ""
    echo "  使用方法："
    echo "  1. 打开 Finder 进入 dist 文件夹"
    echo "  2. 把 AI股票分析.app 拖到:"
    echo "     • 桌面"
    echo "     • 启动台 (Launchpad)"
    echo "     • 应用程序文件夹 (/Applications)"
    echo "  3. 双击运行"
    echo ""
    echo "  首次运行需要在「系统设置 → 隐私与安全性」"
    echo "  点击「仍要打开」"
    echo "═══════════════════════════════════════════════════════"

    # 自动打开 Finder 定位
    open dist/
else
    echo -e "${RED}❌ 打包失败，请查看上方日志${NC}"
fi

echo ""
read -p "按回车键退出..."
