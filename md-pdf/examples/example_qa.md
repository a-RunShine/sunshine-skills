# md-pdf skill 使用示例

本示例展示 `md-pdf` skill 的核心能力：Markdown → PDF 转换、4 套主题、按字符路由字体（含数学符号真实显示）。

## 章节 1：基础 Markdown 语法

普通段落：包含中文（汉字）、English mixed text、数字 123、标点。

行内**粗体** + 嵌套**双星号**。

> 引用块：测试主题色在引用场景的呈现。

- 无序列表项 A
- 无序列表项 B
- 无序列表项 C

## 章节 2：数学符号

测试按字符路由字体（数学符号 → Arial Unicode，Latin 字符 → JetBrains Mono）：

- 自然连接：`R ⋈ S` 是关系代数的核心算子
- 存在量词：`∃x ∈ S, P(x)`
- 全称量词：`∀x ∈ S, P(x) holds`
- 集合关系：`A ⊂ B`，`A ⊃ B`
- 下标：`H₂O`，`CO₂`，`x₁ + x₂ = y₁ + y₂`

## 章节 3：代码块

测试代码块使用 JetBrains Mono 渲染：

```python
def fibonacci(n: int) -> int:
    """Compute the n-th Fibonacci number using memoization."""
    cache = {0: 0, 1: 1}
    for i in range(2, n + 1):
        cache[i] = cache[i - 1] + cache[i - 2]
    return cache[n]

print(fibonacci(10))  # Output: 55
```

```sql
-- 关系代数示例
SELECT R.A, S.B
FROM R INNER JOIN S ON R.id = S.r_id
WHERE R.value > 100 AND S.created_at >= '2024-01-01';
```

## 章节 4：表格

测试表格主题色（表头底色 + 边框 + 文字色）：

| 主题 | 背景色 | 主调 | 适合场景 |
|---|---|---|---|
| claude-brown | 信纸米 | 深棕 | 默认/笔记 |
| academic | 纯白 | 黑白 | 论文/正式 |
| bilibili-pink | 纯白 | B站粉 | 娱乐/分享 |
| lol | 深蓝 | LoL金 | 游戏/视觉 |

## 调用方式

### 4 套主题示例

```bash
# 默认 Claude 深棕
python3 scripts/convert_md_to_pdf.py input.md

# 学术黑白
python3 scripts/convert_md_to_pdf.py input.md --theme=academic

# B 站骚粉
python3 scripts/convert_md_to_pdf.py input.md --theme=bilibili-pink

# 英雄联盟
python3 scripts/convert_md_to_pdf.py input.md --theme=lol
```

### 指定输出路径和章节名

```bash
python3 scripts/convert_md_to_pdf.py input.md output.pdf \
  --theme=claude-brown \
  --chapter-name="示例章节"
```

### 批量重生成

```bash
find . -name "*.md" -not -name "INDEX.md" \
  | xargs -I{} python3 scripts/convert_md_to_pdf.py {} --theme=claude-brown
```

## 注意事项

- 数学符号 `⋈ ∃ ∀ ⊂` 等会真实显示（不再渲染成空白豆腐块）
- Latin 字符用 JetBrains Mono 渲染
- 代码块优先用 JetBrains Mono
- 表格内 Latin 字符 fallback 到 CJK 字体的 Latin 部分（功能正常，视觉略不同）
- 页脚：装饰图标 + 章节名 + 页码（首页若未指定章节名则省略）
