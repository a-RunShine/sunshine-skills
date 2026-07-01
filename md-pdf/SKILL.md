---
name: md-pdf
description: Use when the user wants to convert Markdown content into a polished PDF with selectable theme (claude-brown / academic / bilibili-pink / lol) and per-character font routing (CJK + Latin JetBrains Mono + math symbols); primary use is rendering study notes, exercise questions, AI lectures, and templates. Also supports PDF OCR (Swift + Apple Vision), question-set merging, and residue checking as secondary helpers.
---

# md-pdf

将 Markdown 渲染为带主题色和按字符路由字体的可打印 PDF 的全局 skill。

## 这个 skill 做什么

**主能力：MD → PDF**

使用 fpdf2 将 Markdown 转为 PDF，支持：

- **4 套主题**（`--theme` 参数选择）
- **3 套字体按字符路由**：CJK 字符、Latin 字符、数学/逻辑符号各自使用最合适的字体
- 行内格式（`**粗体**`）、代码块、引用块、有序/无序列表、表格、分隔线
- 页脚装饰图标 + 章节名 + 页码
- 数学符号（`⋈ ∃ ∀ ∈ ∪` 等）真实显示

**辅能力**（仅在用户的实际目标匹配时使用）：

- **PDF OCR**（`scripts/ocr_pdf.swift`）：使用 Apple PDFKit + Vision 提取扫描版 PDF 文本
- **题目合并**（`scripts/merge_qa.py`）：合并基础题和补充强化题
- **残留检查**（`scripts/check_residue.py`）：检查 .md 是否有脚本残留
- **信纸模板**（`scripts/make_lined_paper.py`）：生成可打印的横线格信纸

不应用于：与学习/打印无关的通用 PDF 操作（合并/拆分/旋转/签名/表单/加密等）——这些用通用 pdf skill。

## 何时使用

- "把这个 MD 转成 PDF"
- "用 Claude 深棕/学术黑白/B站骚粉/LOL 主题生成 PDF"
- "把笔记/讲义/选择题/AI 讲解 生成 PDF"
- "生成可打印的练习题 / 信纸 / 答题卡 PDF"
- "OCR 这个扫描版 PDF"（辅）
- "合并基础题和补充强化题"（辅）
- "检查最终 .md 有没有脚本残留"（辅）

不应用于：

- 与学习输出无关的通用 PDF 操作
- 从零生成 Markdown 内容
- Office 文档（.docx/.xlsx/.pptx）—— 用 officecli skill

## 主题

通过 `--theme` 参数选择，默认 `claude-brown`：

| 主题 | 背景 | 主调 | 适合 |
|---|---|---|---|
| `claude-brown` | 信纸米色 `#FFFBF5` | 深棕/琥珀橙 | 默认，文档/笔记/复习 |
| `academic` | 纯白 `#FFFFFF` | 黑白灰 | 论文/技术报告/正式文档 |
| `bilibili-pink` | 纯白 `#FFFFFF` | B站粉 `#FB7299` | 娱乐向/笔记分享 |
| `lol` | 深蓝 `#0A0E27` | LoL 金 `#C8AA6E` | 游戏向/视觉冲击 |

主题控制：页面底色、H1-H4 渐变、正文/页脚/代码块文字色、表格表头/边框色、行内代码底色。

## 字体（按字符路由）

| 字符类型 | 默认字体 | 范围 |
|---|---|---|
| CJK 字符 | `Arial Unicode.ttf` | 汉字、假名、韩文等 |
| Latin 字符 | `JetBrains Mono Regular` | ASCII + 拉丁扩展 A-B |
| 数学/逻辑符号 | `Arial Unicode.ttf`（CJK 字体） | U+2070-U+209F, U+2200-U+22FF, U+2700-U+27BF |
| 代码块 | `JetBrains Mono Regular` | 整块代码 |

**字符路由原理**：`_write_rich` 和 `add_heading` 逐字符检测，根据 `_is_latin_char()` 和 `_is_math_char()` 动态切到对应字体族。CJK 字符用 CJK 字体（确保显示汉字），Latin 字符用 JetBrains Mono（编程字体的拉丁字符美观），数学符号用 CJK 字体（JetBrains 不含这些字符）。

**字体源**（macOS 默认路径）：

- CJK 标题：`/System/Library/Fonts/STHeiti Medium.ttc`（含粗体变体）
- CJK 正文+数学：`/System/Library/Fonts/Supplemental/Arial Unicode.ttf`（38K 字形全覆盖）
- Latin：`/Users/sunshine/Library/Fonts/JetBrainsMono-Regular.ttf`（如未装则降级到 `/System/Library/Fonts/Menlo.ttc`）

非 macOS 系统：编辑脚本中的 `_FONT_*_CANDIDATES` 列表。

## 命令行参数

```bash
python3 scripts/convert_md_to_pdf.py input.md [output.pdf] [选项]
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `md_path` | 输入的 Markdown 文件（位置参数） | 必填 |
| `pdf_path` | 输出的 PDF 文件（位置参数） | 同目录同名 `.pdf` |
| `--theme` | 主题色 | `claude-brown` |
| `--chapter-name` | 页脚显示的章节名 | 从文件名提取 `第X章_XXX` 格式（中文场景） |

**主题取值**：`claude-brown` / `academic` / `bilibili-pink` / `lol`

## 必需环境

- Python 3 + `fpdf2>=2.5.0`（需要 `collection_font_number` 支持）
- macOS 推荐（自带 STHeiti/Songti/Arial Unicode + PDFKit + Vision）
- 其他系统：编辑脚本中的字体路径变量

## 典型工作流

### 主流程：MD → PDF

```bash
# 最简调用
python3 scripts/convert_md_to_pdf.py input.md

# 指定主题
python3 scripts/convert_md_to_pdf.py input.md --theme=academic

# 指定输出路径 + 章节名
python3 scripts/convert_md_to_pdf.py input.md output.pdf --theme=lol --chapter-name="第3章 关系代数"
```

页脚显示规则：第 1 页如果未指定章节名则省略页脚；后续页显示装饰图标 + 章节名 + 页码。

### 批量重生成

```bash
# 当前目录及子目录所有 .md 批量转 PDF
find . -name "*.md" -not -name "INDEX.md" | xargs -I{} python3 scripts/convert_md_to_pdf.py {}
```

### 信纸模板

```bash
python3 scripts/make_lined_paper.py -o P -n 25           # A4 纵向 25 行
python3 scripts/make_lined_paper.py -o L -n 20 -t "草稿纸"  # A4 横向 20 行带标题
```

### PDF OCR（辅）

```bash
swift scripts/ocr_pdf.swift input.pdf output_dir output_ocr.txt
```

渲染每一页为图片，通过 Apple Vision OCR 提取文本，输出每页置信度。

### 题目合并（辅）

```bash
python3 scripts/merge_qa.py base.md supplement.md final.md
```

输出路径必须与输入不同；加 `--overwrite` 允许覆盖。

合并后用 `scripts/check_residue.py final.md` 检查脚本残留。

## 质量检查清单

成功的 PDF 应该有：

- ✅ 主题色正确（背景色、标题色、正文色都符合所选主题）
- ✅ 字体正确（Latin 字符是 JetBrains Mono，汉字是 Arial Unicode 的 CJK 部分）
- ✅ 数学符号真实显示（`⋈ ∃ ∀` 等，不是空白）
- ✅ 页脚正确（章节名 + 页码，首页若未指定章节名则省略）
- ✅ 无 emoji/豆腐块（`⭐✓✗` 已被剥离或正确渲染）
- ✅ 无文字溢出/截断
- ✅ 表格边框清晰
- ✅ 代码块用 JetBrains Mono 渲染（带连字或无连字）

## 常见问题

**Q: 怎么新增自定义主题？**

编辑 `scripts/convert_md_to_pdf.py` 中的 `THEMES` 字典，添加新 key 即可。需要的字段：
```python
"my-theme": {
    "name": "我的主题",          # 显示用
    "bg": (R, G, B),             # 全页底色
    "h1": (R, G, B),             "h2": (R, G, B),   "h3": (R, G, B),   "h4": (R, G, B),
    "body": (R, G, B),           "footer": (R, G, B),
    "code_text": (R, G, B),
    "table_header_bg": (R, G, B), "table_header_text": (R, G, B),
    "code_bg": (R, G, B),        "border": (R, G, B),
    "inline_code_bg": (R, G, B),
}
```

**Q: 怎么用别的 Latin 字体替代 JetBrains Mono？**

修改 `_FONT_LATIN_CANDIDATES` 列表，把你想用的字体路径放首位。

**Q: 怎么在非 macOS 上运行？**

修改 `_FONT_HEADING_CANDIDATES` / `_FONT_BODY_CANDIDATES` / `_FONT_LATIN_CANDIDATES` 三个列表。

**Q: 为什么表格里 Latin 字符不是 JetBrains Mono？**

表格走 `cell()` + `multi_cell(dry_run=True)` 排版预演，不支持 per-character 字体切换。表格内 Latin 字符会 fallback 到 CJK 字体的 Latin 部分（视觉上略不一致，但功能正常）。

## 包含文件

- `scripts/convert_md_to_pdf.py` — **核心**，MD → PDF，4 主题 + 字符路由
- `scripts/make_lined_paper.py` — 横线格信纸模板
- `scripts/ocr_pdf.swift` — macOS PDFKit + Vision OCR
- `scripts/merge_qa.py` — 合并基础题和补充强化题
- `scripts/check_residue.py` — 残留检查
- `assets/ornament.png` — 装饰图标（页脚左侧）
- `examples/example_qa.md` — 中性示例
- `templates/qa_template.md` — 题库模板
- `REFERENCE.md` — 详细技术参考
