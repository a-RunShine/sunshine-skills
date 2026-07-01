#!/usr/bin/env python3
"""将 Markdown 文件转为支持中文的 PDF，支持行内格式、代码块、表格等。

支持 4 套主题（--theme 参数）：claude-brown / academic / bilibili-pink / lol。
支持 3 套字体：CJK 字体（默认 Arial Unicode，含 CJK + 数学符号），
               标题字体（默认 STHeiti Medium），Latin 字体（默认 JetBrains Mono）。
按字符路由：Latin 字符用 Latin 字体，CJK/数学字符用 CJK 字体。"""

import re
import os
import sys
from pathlib import Path

import fpdf

_fpdf_version = tuple(int(x) for x in fpdf.__version__.split("."))
if _fpdf_version < (2, 5, 0):
    print(f"错误：需要 fpdf2 >= 2.5.0，当前版本为 {fpdf.__version__}")
    print("请运行: pip install 'fpdf2>=2.5.0'")
    raise SystemExit(1)

from fpdf import FPDF

# macOS 中文字体路径候选列表
_FONT_HEADING_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
_FONT_BODY_CANDIDATES = [
    # 首选 Arial Unicode:macOS 自带 38K 字形,含 CJK + 数学符号 + 下标 + 拉丁四合一
    # 解决 Songti 缺 ⋈∃∀ 等数学符号的渲染空白(tofu)问题
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/Library/Fonts/Songti.ttc",
]
_FONT_LATIN_CANDIDATES = [
    # JetBrains Mono:编程字体,1.3K 字形无 CJK,专用于拉丁/代码
    "/Users/sunshine/Library/Fonts/JetBrainsMono-Regular.ttf",
    "/System/Library/Fonts/Menlo.ttc",  # macOS 内置备选
]


def _find_font(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


FONT_HEADING = _find_font(_FONT_HEADING_CANDIDATES)
FONT_BODY = _find_font(_FONT_BODY_CANDIDATES)
FONT_LATIN = _find_font(_FONT_LATIN_CANDIDATES)

if FONT_HEADING is None or FONT_BODY is None:
    print("警告：未找到所需的中文字体。")
    print("  标题字体候选：", _FONT_HEADING_CANDIDATES)
    print("  正文字体候选：", _FONT_BODY_CANDIDATES)
    if sys.platform != "darwin":
        print("  在非 macOS 系统上，请修改脚本中的字体路径变量。")
    raise SystemExit(1)

if FONT_LATIN is None:
    print("提示：未找到 Latin 字体（JetBrains Mono/Menlo），将 fallback 到 CJK 字体渲染拉丁字符。")

# --- 主题注册表 (RGB 元组, 0-255) ---
# 通过 --theme 参数选择。key 即 CLI 取值
THEMES = {
    "claude-brown": {
        "name": "Claude 深棕 (默认)",
        "bg": (255, 251, 245),
        "h1": (217, 119, 7),         "h2": (92, 58, 33),    "h3": (92, 58, 33),    "h4": (120, 85, 55),
        "body": (61, 43, 31),        "footer": (194, 104, 10),
        "code_text": (50, 35, 22),
        "table_header_bg": (240, 228, 201), "table_header_text": (92, 58, 33),
        "code_bg": (245, 234, 208),  "border": (217, 196, 162),
        "inline_code_bg": (250, 243, 225),
        "quote_bg": (252, 246, 232),
    },
    "academic": {
        "name": "学术黑白",
        "bg": (255, 255, 255),
        "h1": (0, 0, 0),             "h2": (0, 0, 0),       "h3": (0, 0, 0),       "h4": (51, 51, 51),
        "body": (26, 26, 26),        "footer": (102, 102, 102),
        "code_text": (26, 26, 26),
        "table_header_bg": (240, 240, 240), "table_header_text": (0, 0, 0),
        "code_bg": (248, 248, 248),  "border": (200, 200, 200),
        "inline_code_bg": (240, 240, 240),
        "quote_bg": (244, 246, 250),
    },
    "bilibili-pink": {
        "name": "B站骚粉",
        "bg": (255, 255, 255),
        "h1": (251, 114, 153),       "h2": (251, 114, 153), "h3": (0, 161, 214),   "h4": (165, 105, 189),
        "body": (42, 42, 42),        "footer": (251, 114, 153),
        "code_text": (42, 42, 42),
        "table_header_bg": (253, 237, 243), "table_header_text": (251, 114, 153),
        "code_bg": (252, 240, 245),  "border": (251, 200, 215),
        "inline_code_bg": (252, 240, 245),
        "quote_bg": (254, 240, 248),
    },
    "lol": {
        "name": "英雄联盟",
        "bg": (10, 14, 39),
        "h1": (200, 170, 110),       "h2": (200, 170, 110), "h3": (139, 195, 74),  "h4": (139, 195, 74),
        "body": (200, 200, 210),     "footer": (200, 170, 110),
        "code_text": (220, 220, 230),
        "table_header_bg": (24, 30, 60), "table_header_text": (200, 170, 110),
        "code_bg": (20, 24, 50),     "border": (60, 70, 110),
        "inline_code_bg": (24, 30, 60),
        "quote_bg": (28, 32, 60),
    },
}
DEFAULT_THEME = "claude-brown"

# --- 装饰图标（页脚左侧）---
ORNAMENT_PATH = Path(__file__).resolve().parent.parent / "assets" / "ornament.png"
if not ORNAMENT_PATH.exists():
    print(f"提示：未找到装饰图标 {ORNAMENT_PATH}，页脚将省略图标。")
    ORNAMENT_PATH = None


# --- 反引号剥离(用于走 multi_cell 路径的标题/表格/纯文本,不走 _write_rich) ---
def _strip_backticks(text):
    """剥离所有反引号: 配对 `xxx`→xxx, 单独 `→空。已配对的反引号在 PDF 里渲染成豆腐块, 全部剥离"""
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.replace("`", "")


# --- emoji 移除 ---
# 覆盖范围: 表情符号 + 杂项符号 + 麻将 + 扑克 + 表情 A 区 + 交通 + 补充符号
# 已单独补 ⭐(U+2B50) + ⊂(U+2282): 这两个常误用,且在 STHeiti/Songti 中均渲染成豆腐块
# 已知未覆盖(有意保留): →(U+2192 箭头/数学常用) / ✓✗(U+2713/2717,AGENTS.md 已禁用但偶尔漏)
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF"
    "\u2600-\u27BF"
    "\U0001F000-\U0001F02F"
    "\U0001F0A0-\U0001F0FF"
    "\U0001F100-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\u2B50"           # ⭐ 白色中等星号
    "\u2282"           # ⊂ 子集符号
    "]+",
    flags=re.UNICODE,
)


def _remove_emoji(text):
    return _EMOJI_RE.sub("", text).strip()


# --- 字符路由辅助 ---
def _is_math_char(ch):
    """数学/逻辑/装饰符号: STHeiti 不含, 需切到 Songti(=Arial Unicode)"""
    if not ch or ord(ch) < 0x2000:
        return False
    cp = ord(ch)
    return (
        0x2070 <= cp <= 0x209F   # 上下标 ₀₁₂₃
        or 0x2200 <= cp <= 0x22FF  # 数学算子 ⋈∃∀∈∩∪
        or 0x2700 <= cp <= 0x27BF  # 装饰符号 ✓✗
    )


def _is_latin_char(ch):
    """拉丁/ASCII 字符: 切到 Latin 字体 (JetBrains Mono)"""
    if not ch or len(ch) != 1:
        return False
    cp = ord(ch)
    return cp < 0x80 or (0x00A0 <= cp <= 0x024F)


class MarkdownPDF(FPDF):
    def __init__(self, theme=DEFAULT_THEME, chapter_name=""):
        super().__init__(format="A4")
        self.theme = THEMES.get(theme, THEMES[DEFAULT_THEME])
        self.chapter_name = chapter_name
        self.set_auto_page_break(True, margin=36)
        self.set_top_margin(15)
        self.add_font("Heiti", style="", fname=FONT_HEADING)
        self.add_font("Heiti", style="B", fname=FONT_HEADING)
        if FONT_BODY.lower().endswith(".ttc"):
            self.add_font("Songti", style="", fname=FONT_BODY, collection_font_number=1)
            self.add_font("Songti", style="B", fname=FONT_BODY, collection_font_number=1)
        else:
            self.add_font("Songti", style="", fname=FONT_BODY)
            self.add_font("Songti", style="B", fname=FONT_BODY)
        if FONT_LATIN:
            if FONT_LATIN.lower().endswith(".ttc"):
                self.add_font("Latin", style="", fname=FONT_LATIN, collection_font_number=1)
                self.add_font("Latin", style="B", fname=FONT_LATIN, collection_font_number=1)
            else:
                self.add_font("Latin", style="", fname=FONT_LATIN)
                self.add_font("Latin", style="B", fname=FONT_LATIN)
        else:
            self.add_font("Latin", style="", fname=FONT_BODY,
                          collection_font_number=1 if FONT_BODY.lower().endswith(".ttc") else None)
            self.add_font("Latin", style="B", fname=FONT_BODY,
                          collection_font_number=1 if FONT_BODY.lower().endswith(".ttc") else None)
        self.set_left_margin(20)
        self.set_right_margin(20)
        self.set_text_color(*self._t("body"))

    def _t(self, key):
        return self.theme[key]

    # --- 页面背景：信纸米色 ---
    def header(self):
        self.set_fill_color(*self._t("bg"))
        self.rect(0, 0, self.w, self.h, "F")
        self.set_text_color(*self._t("body"))
        self.set_xy(self.l_margin, self.t_margin)

    # --- 页脚：装饰图标 + 章节名 + 页码 ---
    def footer(self):
        if self.page_no() == 1 and not self.chapter_name:
            # 第一页且无章节名，跳过页脚
            return
        self.set_y(-16)
        # 左侧装饰图标
        if ORNAMENT_PATH:
            self.image(str(ORNAMENT_PATH), x=self.l_margin, y=self.h - 13, w=6)
            text_x = self.l_margin + 8
        else:
            text_x = self.l_margin
        # 中间：章节名
        self.set_font("Heiti", "", 8)
        self.set_text_color(*self._t("footer"))
        self.set_x(text_x)
        if self.chapter_name:
            self.cell(self.w / 2 - text_x, 5, self.chapter_name, align="L")
        # 右侧：页码
        self.set_x(self.w / 2)
        self.cell(self.w / 2 - self.r_margin, 5, f"— {self.page_no()} —", align="R")
        # 恢复默认文字色
        self.set_text_color(*self._t("body"))

    # --- 行内格式解析 ---
    # 简化版: 只处理 **bold**,反引号已在 _write_rich 入口由 _strip_backticks 剥离
    _INLINE_RE = re.compile(r"\*\*(.+?)\*\*")

    def _parse_inline(self, text):
        """拆分为 [(text, style), ...]，style: normal / bold"""
        fragments = []
        last_end = 0
        for m in self._INLINE_RE.finditer(text):
            if m.start() > last_end:
                part = text[last_end:m.start()]
                if part:
                    fragments.append((part, "normal"))
            fragments.append((m.group(1), "bold"))
            last_end = m.end()
        if last_end < len(text):
            part = text[last_end:]
            if part:
                fragments.append((part, "normal"))
        return fragments if fragments else [(text, "normal")]
        return fragments if fragments else [(text, "normal")]

    # --- 富文本段落输出（核心引擎）---
    def _write_rich(
        self, text, base_size=10.5, base_font="Songti",
        line_height=None, align="L", indent=0,
    ):
        """逐字符输出，支持 **粗体** 混排，自动换行
        反引号由 _strip_backticks 入口剥离，不再渲染 code 样式
        """
        if line_height is None:
            line_height = base_size * 0.5
        text = _strip_backticks(text)  # 入口剥离反引号
        fragments = self._parse_inline(text)
        max_x = self.w - self.r_margin
        x_start = self.l_margin + indent
        self.set_x(x_start)

        for frag_text, style in fragments:
            if style == "bold":
                cur_fam, cur_style = "Heiti", "B"
            else:
                cur_fam, cur_style = base_font, ""
            self.set_text_color(*self._t("body"))

            cur_active_font = None
            for ch in frag_text:
                # math 字符切到 Songti(Arial Unicode, 含数学符号)
                if _is_math_char(ch) and cur_fam == "Heiti":
                    target_font = "Songti"
                else:
                    target_font = cur_fam
                if target_font != cur_active_font:
                    self.set_font(target_font, cur_style, base_size)
                    cur_active_font = target_font

                ch_w = self.get_string_width(ch)
                if ch != "\n" and self.get_x() + ch_w > max_x:
                    self.ln(line_height)
                    self.set_x(x_start)
                self.write(line_height, ch)

        # 收尾用完整行高（原 line_height * 0.6 偏短，会导致"段落/列表项 → 块级元素（代码块/引用块/表格）"时矩形起点侵入上一行文字）
        self.ln(line_height)

    # --- 原始纯文本输出（标题等无需解析的场景）---
    def write_text(self, text, size=11, bold=False, align="L", color=None):
        style = "B" if bold else ""
        font_name = "Heiti" if bold else "Songti"
        text = _strip_backticks(text)  # 走 multi_cell,反引号剥离
        self.set_font(font_name, style, size)
        if color:
            self.set_text_color(*color)
        else:
            self.set_text_color(*self._t("body"))
        self.multi_cell(0, size * 0.55, text, align=align)

    # --- 标题（扩展至 level 4）---
    def add_heading(self, text, level):
        sizes = {1: 18, 2: 15, 3: 12, 4: 11}
        size = sizes.get(level, 11)
        text = _strip_backticks(text)
        self.set_x(self.l_margin)
        # 含 math 字符 → 走逐字符渲染路径, math 字符切到 Songti
        # 不处理 Latin 切换(避免行高不一致)
        if any(_is_math_char(c) for c in text):
            return self._add_heading_math_aware(text, level, size)
        # 纯 CJK + Latin 标题: 保持原 multi_cell 路径
        self.set_font("Heiti", "B", size)
        if level == 1:
            self.set_text_color(*self._t("h1"))
            self.ln(2)
            self.multi_cell(0, size * 0.6, text, align="C")
            self.ln(4)
        elif level == 2:
            self.ln(2)
            self.set_text_color(*self._t("h2"))
            self.multi_cell(0, size * 0.55, text, align="L")
            self.ln(1)
        elif level == 3:
            self.ln(1)
            self.set_text_color(*self._t("h2"))
            self.multi_cell(0, size * 0.5, text, align="L")
            self.ln(0.5)
        elif level == 4:
            self.ln(0.5)
            self.set_text_color(*self._t("h4"))
            self.multi_cell(0, size * 0.5, text, align="L")
            self.ln(0.5)
        self.set_text_color(*self._t("body"))

    def _add_heading_math_aware(self, text, level, size):
        """标题含 math 字符时: 逐字符渲染, math 字符切到 Songti(Arial Unicode)。
        不切 Latin 字体(避免行高不一致)。
        """
        if level == 1:
            color, line_h, ln_before, ln_after = self._t("h1"), size * 0.6, 2, 4
        elif level == 2:
            color, line_h, ln_before, ln_after = self._t("h2"), size * 0.55, 2, 1
        elif level == 3:
            color, line_h, ln_before, ln_after = self._t("h2"), size * 0.5, 1, 0.5
        else:
            color, line_h, ln_before, ln_after = self._t("h4"), size * 0.5, 0.5, 0.5

        self.ln(ln_before)
        self.set_text_color(*color)
        max_x = self.w - self.r_margin
        x_start = self.l_margin
        self.set_x(x_start)
        cur_active = None
        for ch in text:
            if ch == "\n":
                self.ln(line_h)
                self.set_x(x_start)
                continue
            if _is_math_char(ch):
                target = "Songti"
            else:
                target = "Heiti"
            if target != cur_active:
                self.set_font(target, "B", size)
                cur_active = target
            ch_w = self.get_string_width(ch)
            if self.get_x() + ch_w > max_x:
                self.ln(line_h)
                self.set_x(x_start)
            self.write(line_h, ch)
        self.ln(ln_after)
        self.set_text_color(*self._t("body"))

    # --- 分隔线 ---
    def add_separator(self):
        self.set_draw_color(*self._t("border"))
        self.set_line_width(0.5)
        self.set_x(self.l_margin)
        self.ln(2)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)

    # --- 代码块 ---
    def _render_code_block(self, code_lines):
        # 代码块字体 7.5pt,行间距 4.5mm
        line_h = 4.5
        block_h = len(code_lines) * line_h + 4
        x0 = self.l_margin
        w_block = self.w - x0 - self.r_margin

        if self.get_y() + block_h > self.h - self.b_margin:
            self.add_page()

        y0 = self.get_y()
        self.set_fill_color(*self._t("code_bg"))
        self.set_draw_color(*self._t("border"))
        self.rect(x0, y0, w_block, block_h, "DF")

        self.set_text_color(*self._t("code_text"))
        self.set_y(y0 + 2)

        # 代码块按字符切字体: Latin → JetBrains Mono, CJK → Songti
        for line in code_lines:
            self.set_x(x0 + 3)
            text = _strip_backticks(line)
            cur_active = None
            for ch in text:
                if ch == "\n":
                    self.ln(line_h)
                    self.set_x(x0 + 3)
                    continue
                if _is_latin_char(ch):
                    target = "Latin"
                else:
                    target = "Songti"
                if target != cur_active:
                    self.set_font(target, "", 7.5)
                    cur_active = target
                ch_w = self.get_string_width(ch)
                if self.get_x() + ch_w > x0 + w_block - 3:
                    self.ln(line_h)
                    self.set_x(x0 + 3)
                self.write(line_h, ch)
            self.ln(line_h)

        self.set_text_color(*self._t("body"))
        self.ln(4)

    # --- 引用块 ---
    def _render_blockquote(self, text_lines):
        """引用块: 米黄背景 + 琥珀左竖条, 多行聚合为一块
        text_lines: 已剥离 '> ' 前缀的连续行列表, 空字符串代表裸 > 行
        """
        if not text_lines:
            return

        # 1. 预处理: 剥离反引号 + 去掉加粗标记(放弃加粗, 仅保留文字)
        cleaned = []
        for t in text_lines:
            t = _strip_backticks(t)
            t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
            cleaned.append(t)

        # 2. 布局参数(mm)
        indent = 5         # 整块距左边距
        bar_w = 2          # 左竖条宽度
        pad_x = 4          # 竖条与文字间距
        pad_y = 2          # 上下内边距
        right_pad = 2      # 右侧留白
        base_size = 10.5
        line_h = base_size * 0.5  # 5.25

        # 3. 计算坐标
        x0 = self.l_margin + indent
        w_block = self.w - x0 - self.r_margin
        x_text = x0 + bar_w + pad_x
        w_text = w_block - bar_w - pad_x - right_pad
        max_x_text = x_text + w_text

        # 4. 预计算总高度: 用 multi_cell dry_run 拿到每行的子行数
        self.set_font("Songti", "", base_size)
        total_sub_lines = 0
        for t in cleaned:
            if t == "":
                total_sub_lines += 1   # 裸 > 行占一行高
                continue
            subs = self.multi_cell(w_text, line_h, t,
                                   dry_run=True, output="LINES")
            total_sub_lines += len(subs) if subs else 1
        block_h = total_sub_lines * line_h + 2 * pad_y

        # 5. 分页: 整块高度超剩余空间则强制换页
        if self.get_y() + block_h > self.h - self.b_margin:
            self.add_page()

        # 6. 画米黄背景矩形
        y0 = self.get_y()
        self.set_fill_color(*self._t("quote_bg"))
        self.rect(x0, y0, w_block, block_h, "F")

        # 7. 画琥珀左竖条(用 h1 色)
        self.set_fill_color(*self._t("h1"))
        self.rect(x0, y0, bar_w, block_h, "F")

        # 8. 写文字(h2 色, Songti 字体, 逐字符, 自动换行)
        self.set_text_color(*self._t("h2"))
        self.set_font("Songti", "", base_size)
        self.set_xy(x_text, y0 + pad_y)
        for t in cleaned:
            if t == "":
                self.ln(line_h)
                continue
            for ch in t:
                if ch == "\n":
                    self.ln(line_h)
                    self.set_x(x_text)
                    continue
                ch_w = self.get_string_width(ch)
                if self.get_x() + ch_w > max_x_text:
                    self.ln(line_h)
                    self.set_x(x_text)
                self.write(line_h, ch)
            # 每源行结束换行(下个源行从新行起)
            self.ln(line_h)

        # 9. 收尾: 块后 2mm 间距 + 恢复 body 色
        self.set_y(y0 + block_h + 2)
        self.set_text_color(*self._t("body"))

    # --- 无序列表 ---
    def _render_list_item(self, text):
        self._write_rich("• " + text, base_size=10.5, line_height=5.2, indent=5)

    # --- 表格 ---
    def _render_table(self, headers, data_rows):
        ncols = len(headers)
        table_w = self.w - self.l_margin - self.r_margin
        col_w = table_w / ncols
        line_h = 5.5

        def _clean(text):
            # 表格走 cell()+multi_cell dry_run,反引号和 **粗体** 都不会自动解析
            # 必须显式剥离
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            text = _strip_backticks(text)
            return text

        def _calc_lines(text, font, size):
            """预计算文本在给定列宽下的子行列表"""
            self.set_font(*font, size)
            return self.multi_cell(col_w, line_h, _clean(text),
                                   dry_run=True, output="LINES")

        # --- 表头：预计算 + 逐子行 cell() ---
        header_font = ("Heiti", "B")
        header_lines_list = [_calc_lines(h, header_font, 9) for h in headers]
        header_max_lines = max((len(lns) for lns in header_lines_list), default=1)
        header_total_h = header_max_lines * line_h

        if self.get_y() + header_total_h > self.h - self.b_margin:
            self.add_page()

        self.set_font("Heiti", "B", 9)
        self.set_fill_color(*self._t("table_header_bg"))
        self.set_draw_color(*self._t("border"))
        self.set_text_color(*self._t("h1"))

        header_start_y = self.get_y()
        for sub in range(header_max_lines):
            self.set_x(self.l_margin)
            if header_max_lines == 1:
                border = 1
            elif sub == 0:
                border = "LTR"
            elif sub == header_max_lines - 1:
                border = "LBR"
            else:
                border = "LR"
            for ci in range(ncols):
                lines = header_lines_list[ci]
                text = lines[sub] if sub < len(lines) else ""
                self.cell(col_w, line_h, text, border=border, fill=True, align="C")
            self.ln(line_h)
        self.set_y(header_start_y + header_total_h)

        # --- 数据行：预计算 + 逐子行 cell() ---
        self.set_text_color(*self._t("body"))
        body_font = ("Songti", "")

        for row in data_rows:
            cell_lines_list = [_calc_lines(c, body_font, 9) for c in row]
            max_lines = max((len(lns) for lns in cell_lines_list), default=1)
            row_total_h = max_lines * line_h

            if self.get_y() + row_total_h > self.h - self.b_margin:
                self.add_page()

            self.set_font("Songti", "", 9)
            row_start_y = self.get_y()
            for sub in range(max_lines):
                self.set_x(self.l_margin)
                if max_lines == 1:
                    border = 1
                elif sub == 0:
                    border = "LTR"
                elif sub == max_lines - 1:
                    border = "LBR"
                else:
                    border = "LR"
                for ci in range(ncols):
                    lines = cell_lines_list[ci]
                    text = lines[sub] if sub < len(lines) else ""
                    self.cell(col_w, line_h, text, border=border)
                self.ln(line_h)
            self.set_y(row_start_y + row_total_h)

        self.ln(3)

    # --- 练习题输出方法（改为走 _write_rich）---
    def add_answer_line(self, text):
        self.set_text_color(*self._t("h2"))
        self._write_rich(text, base_size=9, line_height=4.5)
        self.set_text_color(*self._t("body"))
        self.ln(2)

    def add_question(self, text):
        self._write_rich(text, base_size=10.5, line_height=5.0)

    def add_option(self, text):
        self._write_rich(text, base_size=10, line_height=7.0, indent=8)

    def add_judge(self, text):
        self._write_rich(text, base_size=10.5, line_height=5.0)

    def add_paragraph(self, text):
        self._write_rich(text, base_size=10.5, line_height=5.2)
        self.ln(1)


def _extract_chapter_name(md_path):
    """从 Markdown 文件名提取章节名（如「第四章_数据库安全性」）。

    命名规范：第X章_章节名_类型.扩展名。无匹配时返回空串。
    """
    stem = Path(md_path).stem
    m = re.match(r"^(第[一二三四五六七八九十百零\d]+章(?:[^_]*))", stem)
    if m:
        return m.group(1)
    return ""


def _preprocess_lines(lines):
    """预处理行列表，改善 PDF 渲染间距（不改 md 源文件）：
    1. 有序列表项（N. xxx）之间无空行时，插入空行，避免 PDF 中挤在一起
    2. 无序列表项（- xxx）之间无空行时，插入空行
    3. ### 小标题前只有1个空行时，补到2个空行，增强视觉分隔
    4. 题号行（数字. xxx）前一行非空时，插入空行，让题目之间有视觉分隔
    """
    result = []
    ordered_re = re.compile(r"^\d+\.\s+\S")
    unordered_re = re.compile(r"^-\s+\S")
    question_re = re.compile(r"^\d+\.\s+\S")  # 与 ordered 相同，但语义上专指题号
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)

        cur_stripped = line.strip()
        is_ordered = bool(ordered_re.match(cur_stripped))
        is_unordered = bool(unordered_re.match(cur_stripped))
        is_list = is_ordered or is_unordered

        # 规则1+2：当前是列表项，下一行也是同类型列表项（中间无空行），插入空行
        if is_list and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            if next_stripped and (ordered_re.match(next_stripped) or unordered_re.match(next_stripped)):
                result.append("\n")

        # 规则3：下一行是 ### 小标题，当前不是空行，插入空行
        if i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            if next_stripped.startswith("### ") and cur_stripped != "":
                result.append("\n")

        # 规则4：当前非空且下一行是题号行（覆盖"上一题选项 → 下一题题干"的间距）
        if i + 1 < len(lines) and cur_stripped != "":
            next_stripped = lines[i + 1].strip()
            if question_re.match(next_stripped):
                result.append("\n")

        i += 1
    return result


def convert_md_to_pdf(md_path, pdf_path, theme=DEFAULT_THEME, chapter_name=None):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 预处理：改善列表项间距和小标题前间距（不改源文件）
    lines = _preprocess_lines(lines)

    if chapter_name is None:
        chapter_name = _extract_chapter_name(md_path)
    pdf = MarkdownPDF(theme=theme, chapter_name=chapter_name)
    pdf.add_page()

    i = 0
    in_code_block = False
    code_lines = []

    def _is_question_separator(idx):
        """判断 lines[idx] 是否是题号间的空行（前一个非空行是选项行，下一个非空行是题号行）"""
        prev_stripped = ""
        for j in range(idx - 1, -1, -1):
            if lines[j].strip():
                prev_stripped = lines[j].strip()
                break
        next_stripped = ""
        for j in range(idx + 1, len(lines)):
            if lines[j].strip():
                next_stripped = lines[j].strip()
                break
        option_re = re.compile(r"^[A-F]\.\s+\S")
        question_re = re.compile(r"^\d+\.\s+\S")
        return bool(option_re.match(prev_stripped) and question_re.match(next_stripped))

    while i < len(lines):
        line = lines[i].rstrip()

        # 代码块状态机
        if in_code_block:
            if line.strip().startswith("```"):
                pdf._render_code_block(code_lines)
                code_lines = []
                in_code_block = False
                i += 1
                continue
            code_lines.append(line)
            i += 1
            continue

        # 预处理：移除 emoji
        line = _remove_emoji(line)

        if not line:
            # 题号间空行用更大间距（5mm vs 2mm）
            pdf.ln(5 if _is_question_separator(i) else 2)
            i += 1
            continue

        if line.strip() == "---":
            pdf.add_separator()
            i += 1
            continue

        # 代码块开始（含 ```java 等语言标识）
        if line.strip().startswith("```"):
            in_code_block = True
            code_lines = []
            i += 1
            continue

        # 标题（#### 必须在 ### 前面）
        m = re.match(r"^#### (.+)", line)
        if m:
            pdf.add_heading(m.group(1), 4)
            i += 1
            continue

        m = re.match(r"^### (.+)", line)
        if m:
            pdf.add_heading(m.group(1), 3)
            i += 1
            continue

        m = re.match(r"^## (.+)", line)
        if m:
            pdf.add_heading(m.group(1), 2)
            i += 1
            continue

        m = re.match(r"^# (.+)", line)
        if m:
            pdf.add_heading(m.group(1), 1)
            i += 1
            continue

        # 引用块: 聚合连续 > 行(含裸 > 空行)为一块
        if line.startswith("> ") or line.strip() == ">":
            block_lines = []
            while i < len(lines):
                cur = lines[i].rstrip()
                if cur.startswith("> "):
                    block_lines.append(cur[2:])  # 去掉 "> " 前缀
                    i += 1
                elif cur.strip() == ">":
                    block_lines.append("")        # 裸 > 行: 块内空行
                    i += 1
                else:
                    break
            pdf._render_blockquote(block_lines)
            continue

        # 表格：当前行以 | 开头且下一行是 |---| 分隔线
        if (
            line.strip().startswith("|")
            and i + 1 < len(lines)
            and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip())
        ):
            headers = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            data_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                data_rows.append(row)
                i += 1
            pdf._render_table(headers, data_rows)
            continue

        # 无序列表
        m = re.match(r"^-\s+(.+)", line)
        if m:
            pdf._render_list_item(m.group(1))
            i += 1
            continue

        # --- 以下为原有练习题匹配逻辑 ---
        # 答案行匹配：行内含多个题号答案（如 "1.B 2.C 3.D"）才算答案行
        if re.match(r"^\d+\.\s*[A-Z√×]\s+\d+\.", line) or re.match(
            r"^\d+\.[A-Z√×]\s+\d+\.", line
        ):
            pdf.add_answer_line(line)
            i += 1
            continue

        # 单个答案行（如 "1.B" 结尾、且整行是答案汇总格式）
        if re.match(r"^\d+\.\s*[A-Z√×]+$", line.strip()):
            pdf.add_answer_line(line)
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.+)", line)
        if m:
            pdf.add_question(line)
            i += 1
            continue

        m = re.match(r"^([A-F])\.\s+(.+)", line)
        if m:
            pdf.add_option(line)
            i += 1
            continue

        if re.match(r"^\d+\. [√×]", line):
            pdf.add_judge(line)
            i += 1
            continue

        pdf.add_paragraph(line)
        i += 1

    pdf.output(pdf_path)
    print(f"PDF 已生成: {pdf_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="将 Markdown 文件转为 PDF（支持 4 套主题 + JetBrains Mono 拉丁字体）"
    )
    parser.add_argument(
        "md_path",
        help="输入的 Markdown 文件路径",
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=None,
        help="输出的 PDF 文件路径（默认同目录同名 .pdf）",
    )
    parser.add_argument(
        "--theme",
        choices=list(THEMES.keys()),
        default=DEFAULT_THEME,
        help=f"PDF 主题色 (默认: {DEFAULT_THEME})。可选: {', '.join(THEMES.keys())}",
    )
    parser.add_argument(
        "--chapter-name",
        default=None,
        help="页脚显示的章节名 (默认从文件名提取第X章_XXX 格式)",
    )
    args = parser.parse_args()

    md_path = args.md_path
    pdf_path = args.pdf_path or str(Path(md_path).with_suffix(".pdf"))

    if not Path(md_path).exists():
        print(f"错误：输入文件不存在: {md_path}")
        raise SystemExit(1)

    print(f"使用主题: {THEMES[args.theme]['name']} ({args.theme})")
    convert_md_to_pdf(
        md_path, pdf_path,
        theme=args.theme,
        chapter_name=args.chapter_name,
    )
