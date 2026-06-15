#!/usr/bin/env python3
"""
AI 股票分析助手 - Mac .icns 图标生成工具

功能：
1. 生成 1024×1024 主图标（深蓝底 + K线 + AI 网络 + 上升趋势）
2. 缩放到 7 个标准尺寸（16/32/64/128/256/512/1024）
3. 用 Mac 自带 iconutil 打包成 .icns

依赖：Pillow（项目已有）
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def make_master_icon(size=1024):
    """生成主图标 (PIL)"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (size, size), (10, 25, 41))
    draw = ImageDraw.Draw(img)

    # 圆角蒙版
    radius = int(size * 0.22)
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [(0, 0), (size, size)], radius=radius, fill=255
    )
    img.putalpha(mask)
    draw = ImageDraw.Draw(img)

    # 比例因子（基于 1024 设计的坐标）
    s = size / 512.0

    # 顶部 AI 神经网络节点
    nodes_l1 = [(80, 60), (140, 50), (200, 60), (260, 50), (320, 60), (380, 50)]
    nodes_l2 = [(140, 30), (260, 30), (320, 25)]
    node_r = int(8 * s)
    line_w = max(1, int(2 * s))

    # 连线
    for x1, y1 in nodes_l1:
        for x2, y2 in nodes_l2:
            draw.line([(x1*s, y1*s), (x2*s, y2*s)], fill=(79, 195, 247), width=line_w)
    # 节点
    for x, y in nodes_l1 + nodes_l2:
        cx, cy = x*s, y*s
        draw.ellipse([(cx-node_r, cy-node_r), (cx+node_r, cy+node_r)],
                     fill=(79, 195, 247), outline=(255,255,255),
                     width=max(1, int(1.5*s)))

    # K 线图
    klines = [
        (100, 220, 280, 200, 'green'),
        (160, 240, 290, 220, 'green'),
        (220, 260, 300, 240, 'red'),
        (280, 230, 270, 210, 'green'),
        (340, 250, 290, 230, 'green'),
        (400, 270, 310, 250, 'red'),
    ]
    shadow_w = max(2, int(4 * s))
    body_w = int(30 * s)

    for x, o, h, l, color in klines:
        color_rgb = (38, 166, 154) if color == 'green' else (239, 83, 80)
        cx = x * s
        # 影线
        draw.line([(cx, l*s), (cx, h*s)], fill=color_rgb, width=shadow_w)
        # 实体
        top, bottom = min(o*s, h*s), max(o*s, h*s)
        draw.rectangle([(cx-body_w/2, top), (cx+body_w/2, bottom)], fill=color_rgb)

    # 底部上升趋势虚线
    for x in range(80, 440, 20):
        draw.line([(x*s, 380*s), ((x+10)*s, 360*s)],
                  fill=(79, 195, 247), width=max(2, int(3*s)))

    # 箭头
    arrow = [(420*s, 360*s), (440*s, 340*s), (440*s, 380*s)]
    draw.polygon(arrow, fill=(79, 195, 247))

    # 底部数据点
    dot_r = max(2, int(8 * s))
    for x in [140, 256, 372]:
        cx, cy = x*s, 428*s
        draw.ellipse([(cx-dot_r, cy-dot_r), (cx+dot_r, cy+dot_r)],
                     fill=(79, 195, 247))

    return img


def make_all_sizes(master):
    """生成 7 个尺寸"""
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    out_dir = Path("icon_pngs")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir()

    paths = {}
    for sz in sizes:
        img = master.resize((sz, sz), Image.LANCZOS)
        # 添加圆角
        mask = Image.new('L', (sz, sz), 0)
        r = max(1, int(sz * 0.22))
        ImageDraw = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw
        ImageDraw.Draw(mask).rounded_rectangle(
            [(0, 0), (sz, sz)], radius=r, fill=255
        )
        img.putalpha(mask)

        path = out_dir / f"icon_{sz}x{sz}.png"
        img.save(path)
        paths[sz] = path
        print(f"  ✓ {path.name}")
    return paths


def build_iconset(paths):
    """打包成 .icns"""
    iconset = Path("icon.iconset")
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()

    # macOS iconset 命名规则
    mapping = [
        (16,   "icon_16x16.png"),
        (32,   "icon_16x16@2x.png"),    # 32px 是 16@2x
        (32,   "icon_32x32.png"),
        (64,   "icon_32x32@2x.png"),
        (128,  "icon_128x128.png"),
        (256,  "icon_128x128@2x.png"),
        (256,  "icon_256x256.png"),
        (512,  "icon_256x256@2x.png"),
        (512,  "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    for sz, name in mapping:
        src = paths.get(sz)
        if src:
            shutil.copy(src, iconset / name)

    print()
    print("🎨 调用 iconutil 打包 .icns...")
    result = subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", "AI股票分析.icns"],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        icns = Path("AI股票分析.icns")
        kb = icns.stat().st_size / 1024
        print(f"✅ 成功: AI股票分析.icns ({kb:.1f} KB)")
        return icns
    else:
        print(f"❌ iconutil 失败: {result.stderr.strip()}")
        return None


def cleanup():
    for d in ["icon_pngs", "icon.iconset"]:
        if Path(d).exists():
            shutil.rmtree(d)


def main():
    print("═══════════════════════════════════════════════════════")
    print("       🎨 AI 股票分析助手 - 图标生成工具")
    print("═══════════════════════════════════════════════════════")
    print()

    try:
        from PIL import Image
    except ImportError:
        print("❌ 需要 Pillow")
        print("   pip install Pillow")
        sys.exit(1)

    print("[1/3] 生成主图标 (1024x1024)...")
    master = make_master_icon(1024)
    master.save("icon_master_preview.png")
    print(f"  ✓ 预览: icon_master_preview.png")

    print()
    print("[2/3] 生成各尺寸 PNG...")
    paths = make_all_sizes(master)

    print()
    print("[3/3] 打包 .icns...")
    icns = build_iconset(paths)

    print()
    cleanup()

    if icns:
        print()
        print("═══════════════════════════════════════════════════════")
        print(f"  ✅ 图标生成完成: {icns.absolute()}")
        print()
        print("  预览方式：")
        print("  • Finder 中双击 AI股票分析.icns（用「预览」打开）")
        print("  • 或运行: open AI股票分析.icns")
        print()
        print("  后续可以：")
        print("  • 设置为 Finder 文件夹图标")
        print("  • 设置为应用图标（需要打包 .app）")
        print("  • 替换 macOS 应用图标")
        print("═══════════════════════════════════════════════════════")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
