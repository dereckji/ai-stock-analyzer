#!/bin/bash
# Mac 一键安装到应用程序文件夹

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════"
echo "      📲 安装 AI 股票分析到应用程序"
echo "═══════════════════════════════════════════════════════"
echo ""

# 优先检查 dist（py2app 打包的）
if [ -d "dist/AI股票分析.app" ]; then
    APP_PATH="dist/AI股票分析.app"
    echo "发现打包的 APP，准备安装..."
elif [ -d "AI股票分析.app" ]; then
    APP_PATH="AI股票分析.app"
    echo "发现预制 APP，准备安装..."
else
    echo "❌ 未找到 APP 文件"
    echo "请先运行 ./打包.command 打包"
    exit 1
fi

# 复制到 Applications
cp -R "$APP_PATH" /Applications/
echo -e "${GREEN}✅ 已安装到 /Applications/AI股票分析.app${NC}"
echo ""

# 询问是否添加到启动台
echo "正在注册到启动台..."
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/AI股票分析.app

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  🎉 安装完成！"
echo ""
echo "  打开方式（任选其一）："
echo "  1. 启动台 (Launchpad) 搜「AI 股票」"
echo "  2. Finder → 应用程序 → 双击 AI股票分析"
echo "  3. Spotlight (⌘+空格) 搜「AI 股票」"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "首次双击会提示「无法打开，因为它来自身份不明的开发者」"
echo "解决方法："
echo "  系统设置 → 隐私与安全性 → 向下滚动 → 点击「仍要打开」"
echo ""

read -p "按回车键继续..."
