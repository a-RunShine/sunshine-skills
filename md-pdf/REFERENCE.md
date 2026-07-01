# md-pdf 技术参考

## 1. 主题系统

### THEMES 字典

`scripts/convert_md_to_pdf.py` 顶部的 `THEMES` 字典定义所有主题：

```python
THEMES = {
    "claude-brown": {
        "name": "Claude 深棕 (默认)",
        "bg": (R, G, B),       # 全页底色
        "h1": (R, G, B),       # 标题色
        "h2": (R, G, B),       "h3": (R, G, B),   "h4": (R, G, B),
        "body": (R, G, B),     # 正文字色
        "footer": (R, G, B),   # 页脚色
        "code_text": (R, G, B),
        "table_header_bg": (R, G, B),
        "table_header_text": (R, G, B),
        "code_bg": (R, G, B),  # 代码块底色
        "border": (R, G, B),   # 边框/分隔线色
        "inline_code_bg": (R, G, B),
    },
    ...
}
```

### 新增自定义主题

1. 在 `THEMES` 字典添加 key（建议用 kebab-case，如 `my-corp-blue`）
2. 填齐所有字段（13 个 RGB 元组）
3. 通过 `--theme=my-corp-blue` 即可使用

### 主题色用途映射

| 字段 | 用途 |
|---|---|
| `bg` | 每一页底色 (`header()` 绘制矩形) |
| `h1` / `h2` / `h3` / `h4` | 各级别标题色 |
| `body` | 正文、表格数据、引用 |
| `footer` | 页脚章节名+页码 |
| `code_text` / `code_bg` | 代码块文字/背景 |
| `table_header_bg` / `table_header_text` | 表格表头 |
| `border` | 表格边框、分隔线 |
| `inline_code_bg` | 行内代码底色（当前未使用，预留） |

## 2. 字符路由（per-character font switching）

### 字符分类

```python
def _is_math_char(ch):
    """数学/逻辑/装饰符号: 0x2070-0x209F, 0x2200-0x22FF, 0x2700-0x27BF"""
    if not ch or ord(ch) < 0x2000: return False
    cp = ord(ch)
    return (0x2070 <= cp <= 0x209F or 0x2200 <= cp <= 0x22FF or 0x2700 <= cp <= 0x27BF)

def _is_latin_char(ch):
    """拉丁/ASCII: U+0000-U+007F + U+00A0-U+024F"""
    if not ch or len(ch) != 1: return False
    cp = ord(ch)
    return cp < 0x80 or (0x00A0 <= cp <= 0x024F)
```

### 路由规则（`_write_rich` / `add_heading`）

| 字符 | 当前字体 | 路由到 | 原因 |
|---|---|---|---|
| Latin (A-z, 0-9, 标点) | Heiti / Songti | **Latin** (JetBrains Mono) | 编程字体拉丁字形美观 |
| Math (⋈ ∃ ∀ ₀₁₂) | Heiti | **Songti** (Arial Unicode) | Heiti 不含数学符号 |
| CJK (中) | Latin (误) | **Songti** | Latin 字体无 CJK |
| 其他 (Heiti) | Heiti | 保持 | 默认 |

### 实现细节

- 字符循环里维护 `cur_active_font`，避免无谓 `set_font()` 调用（性能优化）
- 切换条件：当前激活字体 ≠ 目标字体
- 切换后调 `set_font(target, style, size)`，再 `write(line_h, ch)`

### 不支持混字体的场景

| 渲染方法 | 字体 | 原因 |
|---|---|---|
| `_render_code_block` | Latin (整块) | 代码几乎纯拉丁，单字体最简 |
| `_render_table` 数据行 | Songti | 表格走 `cell()` + `multi_cell(dry_run=True)` 排版预演，不支持 per-character 切换 |
| 表格内 Latin 字符 | Songti 内的 Latin 字形 | 视觉略不同但功能正常 |

## 3. 字体配置

### 默认路径（macOS）

```python
_FONT_HEADING_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",     # 标题用 (CJK 粗体)
    "/System/Library/Fonts/PingFang.ttc",
]
_FONT_BODY_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # 正文+数学 (38K 字形)
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/Library/Fonts/Songti.ttc",
]
_FONT_LATIN_CANDIDATES = [
    "/Users/sunshine/Library/Fonts/JetBrainsMono-Regular.ttf",  # Latin/代码
    "/System/Library/Fonts/Menlo.ttc",                          # 备选
]
```

### 替换字体

修改对应 `_FONT_*_CANDIDATES` 列表的第一个元素即可。脚本会按顺序找第一个存在的字体。

### 非 macOS 适配

将 macOS 路径替换为 Linux/Windows 等效路径：
- Linux: `/usr/share/fonts/truetype/wqy/wqy-microhei.ttc`（文泉驿微米黑，CJK）
- Windows: `C:/Windows/Fonts/msyh.ttc`（微软雅黑）

JetBrains Mono 跨平台可从 [官网](https://www.jetbrains.com/lp/mono/) 下载。

## 4. fpdf2 集成

### 字体注册

```python
# 标题 + CJK
self.add_font("Heiti", style="", fname=FONT_HEADING)
self.add_font("Heiti", style="B", fname=FONT_HEADING)

# CJK+math (区分 TTC vs TTF)
if FONT_BODY.lower().endswith(".ttc"):
    self.add_font("Songti", "", fname=FONT_BODY, collection_font_number=1)
    self.add_font("Songti", "B", fname=FONT_BODY, collection_font_number=1)
else:
    self.add_font("Songti", "", fname=FONT_BODY)
    self.add_font("Songti", "B", fname=FONT_BODY)
```

**为什么区分 TTC vs TTF？**
- TTC (TrueType Collection) 包含多个字形子集，需要 `collection_font_number` 指定子集索引
- TTF 单文件不需要该参数，传入会报错

### 字符渲染

- `set_font(family, style, size)` — 切换字体
- `write(h, ch)` — 逐字符写入（支持 inline 切换字体）
- `multi_cell(w, h, text)` — 多行文本框（**不支持**混字体）
- `cell(w, h, text)` — 单元格（**不支持**混字体）
- `get_string_width(ch)` — 当前字体下的字符宽度（**必须**与 set_font 配对）

### 已知 fpdf2 限制

- `multi_cell` / `cell` 内不能切换字体（这是 fpdf2 架构限制）
- macOS .ttc 报 `feat NOT subset` / `morx NOT subset` 警告是**无害的**（字体子集化不支持，但字体仍能渲染）
- `set_auto_page_break` 后超长文本会自动分页

## 5. 数学符号支持

Arial Unicode.ttf (38,917 glyphs) 是 macOS 自带的"四合一"字体：

| 范围 | 字符 | 用途 |
|---|---|---|
| U+2070-U+209F | ₀₁₂₃⁴⁵⁶⁷⁸⁹ | 上下标 |
| U+2200-U+22FF | ∀∃∈∉∋∌∪∩⊂⊃⊆⊇⋈ | 数学算子 |
| U+2700-U+27BF | ✓✗✦✧ | 装饰符号 |

**对比 Songti.ttc (32,965 glyphs)**：含上下标，但**不含** 0x2200-0x22FF 数学算子。

**修复前症状**：`Font MPDFAA+SongtiSCBold is missing the following glyphs: '⋈' (⋈)` 警告 + 空白豆腐块。

**修复后**：math 字符自动路由到 Songti (=Arial Unicode) 渲染。

## 6. 字符 emoji 剥离

`_EMOJI_RE` 移除以下字符：

- 表情符号 (U+1F300-1FAFF, U+1F600-1F64F, ...)
- 杂项符号 (U+2600-27BF)
- 麻将扑克 (U+1F000-1F02F, U+1F0A0-1F0FF)
- 交通 (U+1F680-1F6FF)
- ⭐ (U+2B50)

**保留**（不剥离）：
- → 箭头 (U+2192)
- ✓ ✗ (U+2713/2717) — 由用户/项目决定
- 数学算子（已纳入 `_is_math_char`）

**为何 0x2700-0x27BF 还在剥离范围？**

此范围包含 ✓✗ 等杂项符号，emoji 范围与之重叠。如果你的项目允许 ✓/✗ 在 PDF 中真实显示，可以从 `_EMOJI_RE` 中移除此范围。

## 7. 字体回退

```python
if FONT_LATIN is None:
    print("提示：未找到 Latin 字体（JetBrains Mono/Menlo），将 fallback 到 CJK 字体渲染拉丁字符。")
```

Latin 字体未找到时，会把 `add_font("Latin", ...)` 注册为 CJK 字体（同为 Arial Unicode 或 Songti）。视觉上 Latin 字符会用 CJK 字体的 Latin 部分渲染。

## 8. CLI 参数解析

```python
parser.add_argument("md_path", help="输入的 Markdown 文件路径")
parser.add_argument("pdf_path", nargs="?", default=None, help="输出 PDF 路径（默认同目录同名 .pdf）")
parser.add_argument("--theme", choices=list(THEMES.keys()), default=DEFAULT_THEME, help="PDF 主题色")
parser.add_argument("--chapter-name", default=None, help="页脚显示的章节名")
```

扩展建议：
- `--font-latin PATH`：覆盖 Latin 字体
- `--font-cjk PATH`：覆盖 CJK 字体
- `--no-footer`：禁用页脚
- `--no-ornament`：禁用装饰图标

## 9. 关键文件清单

| 文件 | 行数 | 作用 |
|---|---|---|
| `scripts/convert_md_to_pdf.py` | ~800 | 核心脚本 |
| `scripts/ocr_pdf.swift` | ~150 | macOS OCR |
| `scripts/merge_qa.py` | ~100 | 题目合并 |
| `scripts/check_residue.py` | ~50 | 残留检查 |
| `scripts/make_lined_paper.py` | ~150 | 信纸模板 |
| `assets/ornament.png` | 1 文件 | 装饰图标 |
| `templates/qa_template.md` | 1 文件 | 题库模板 |
| `examples/example_qa.md` | 1 文件 | 中性示例 |

## 10. 已知问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 表格内 Latin 字符不是 JetBrains Mono | `cell()` 不支持混字体 | 已知限制，建议接受 |
| `️` 变体选择符渲染警告 | STHeiti 不含 | 无影响（字符本身零宽） |
| `feat NOT subset` / `morx NOT subset` 警告 | macOS .ttc 不支持字体子集化 | 无害 |
| 数学符号后跟 emoji 时可能误剥离 | emoji 范围与 math 范围不重叠但相邻 | 已知 case，极少触发 |

## 11. 调试技巧

### 验证字符是否被剥离

```python
import re
_EMOJI_RE = re.compile("[...your pattern...]")
text = "Hello ⭐ World"
print(_EMOJI_RE.sub("", text))  # "Hello  World"
```

### 验证字符路由

```python
import sys
sys.path.insert(0, "/path/to/md-pdf/scripts")
from convert_md_to_pdf import _is_math_char, _is_latin_char

# 测试特定字符
for ch in "ABC中文⋈∃∀₀₁₂":
    print(f"{ch}: latin={_is_latin_char(ch)}, math={_is_math_char(ch)}")
```

### 提取 PDF 文本验证数学符号

```python
from pypdf import PdfReader
reader = PdfReader("output.pdf")
text = ""
for p in reader.pages: text += p.extract_text()
print(text.count("⋈"), text.count("∃"), text.count("∀"))
```

## 12. 扩展方向

1. **新增主题**：编辑 `THEMES` 字典
2. **替换字体**：修改 `_FONT_*_CANDIDATES`
3. **新增导出格式**：HTML/EPUB（需要新依赖）
4. **CJK 字体自动检测**：避免硬编码 macOS 路径
5. **双栏/多栏排版**：fpdf2 支持，需要改 `_render_*` 方法
6. **页眉**：仿照页脚结构添加
