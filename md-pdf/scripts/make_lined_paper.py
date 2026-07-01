#!/usr/bin/env python3
"""生成 A4 横向空白横线格信纸 PDF。

沿用 convert_md_to_pdf.py 的「Claude 深棕 + 信纸色」风格：
- 米色背景 #FFFBF5
- 顶部装饰：ornament.png + 深棕 H1 标题
- 25 行横线
- 关闭页脚
"""

import sys
from pathlib import Path

import fpdf

if tuple(int(x) for x in fpdf.__version__.split(".")) < (2, 5, 0):
    print(f"错误：需要 fpdf2 >= 2.5.0，当前版本为 {fpdf.__version__}")
    sys.exit(1)

from fpdf import FPDF

# --- 复用 convert_md_to_pdf.py 的字体 ---
_FONT_HEADING_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
_FONT_BODY_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/Library/Fonts/Songti.ttc",
]


def _find_font(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


import os

FONT_HEADING = _find_font(_FONT_HEADING_CANDIDATES)
FONT_BODY = _find_font(_FONT_BODY_CANDIDATES)
if FONT_HEADING is None or FONT_BODY is None:
    print("错误：未找到 macOS 中文字体，请修改脚本字体路径。")
    sys.exit(1)

# --- 复用配色 ---
COLOR_BROWN_DARK = (217, 119, 7)       # #D97707 主标题
COLOR_PAPER_BG = (255, 251, 245)       # #FFFBF5 背景
COLOR_PAPER_BORDER = (217, 196, 162)   # #D9C4A2 横线
COLOR_BROWN_FOOTER = (194, 104, 10)    # #C2680A 装饰文字

ORNAMENT_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "ornament.png"
)
if not ORNAMENT_PATH.exists():
    print(f"警告：未找到装饰图标 {ORNAMENT_PATH}，将省略。")
    ORNAMENT_PATH = None


class LinedPaperPDF(FPDF):
    def __init__(self, title="横线格信纸", num_lines=25, orientation="L"):
        super().__init__(format="A4", orientation=orientation)  # L=横向 P=纵向
        self.paper_title = title
        self.num_lines = num_lines
        self.orientation = orientation
        self.set_auto_page_break(False)  # 单页，禁止自动分页
        # 纵向时左右边距可稍宽，呼应 A4 比例
        if orientation == "P":
            self.set_margins(left=25, top=20, right=25)
        else:
            self.set_margins(left=22, top=18, right=22)
        self.add_font("Heiti", "", fname=FONT_HEADING)
        self.add_font("Heiti", "B", fname=FONT_HEADING)
        self.add_page()

    # 米色背景（每页都画，单页就画一次）
    def header(self):
        self.set_fill_color(*COLOR_PAPER_BG)
        self.rect(0, 0, self.w, self.h, "F")

    # 关闭页脚（用户明确不要）
    def footer(self):
        pass

    def draw_decoration(self):
        """顶部装饰：仅 ornament.png（居中），无任何文字"""
        if ORNAMENT_PATH is None:
            return
        top_y = self.t_margin
        ornament_size = 7  # mm
        icon_x = (self.w - ornament_size) / 2
        icon_y = top_y + 1.5
        self.image(str(ORNAMENT_PATH), x=icon_x, y=icon_y, w=ornament_size)

    def draw_lines(self):
        """画 num_lines 条横线"""
        # 装饰区只放一个 7mm ornament，加 6mm 上下间距 ≈ 20mm
        deco_bottom = self.t_margin + 14  # 顶部边距 18 + 装饰高 14 = 32mm
        # 底部留 15mm
        bottom_margin = 15
        usable_h = self.h - deco_bottom - bottom_margin  # mm
        line_spacing = usable_h / self.num_lines  # mm / 行

        # 横线颜色与边框色一致（卡其）
        self.set_draw_color(*COLOR_PAPER_BORDER)
        self.set_line_width(0.25)  # 细线，符合信纸

        x_start = self.l_margin
        x_end = self.w - self.r_margin

        for i in range(self.num_lines):
            # 第 i 行的中心 y
            y = deco_bottom + (i + 0.5) * line_spacing
            self.line(x_start, y, x_end, y)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="生成 A4 横/纵向横线格信纸 PDF")
    parser.add_argument("-o", "--orientation", choices=["L", "P"], default="L",
                        help="L=横向(默认) P=纵向")
    parser.add_argument("-n", "--num-lines", type=int, default=25,
                        help="每页横线行数(默认 25)")
    parser.add_argument("-t", "--title", default="横线格信纸",
                        help="页面标题")
    parser.add_argument("--out", default=None,
                        help="输出路径(默认工作区根目录)")
    args = parser.parse_args()

    if args.out:
        out_path = Path(args.out)
    else:
        suffix = "_纵向A4" if args.orientation == "P" else "_横向A4"
        out_path = Path.cwd() / f"{args.title}{suffix}.pdf"

    pdf = LinedPaperPDF(title=args.title, num_lines=args.num_lines,
                        orientation=args.orientation)
    pdf.draw_decoration()
    pdf.draw_lines()
    pdf.output(str(out_path))
    orient_label = "横向" if args.orientation == "L" else "纵向"
    size_str = "297×210 mm" if args.orientation == "L" else "210×297 mm"
    print(f"已生成: {out_path}")
    print(f"  尺寸: A4 {orient_label}  {size_str}")
    print(f"  装饰: ornament.png + 标题（顶部）  页脚: 无")
    print(f"  横线: {args.num_lines} 行")


if __name__ == "__main__":
    main()
