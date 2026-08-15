---
name: memo-context
description: Use when the user wants to turn today's Maimemo vocabulary into a contextual scene/novel/reading passage for memory reinforcement, then read it in a local HTML page with click-to-translate and per-word proficiency tagging. Triggers: "今日精读" / "今晚生成" / "讲个故事" / "小说" / "考研阅读" / "做阅读题" / "讲没记住的" / "灌 X Y Z" / "memo-context".
---
# memo-context

把墨墨今日词汇转成场景片段/小说/考研阅读，按日存档，并产出可阅读的 HTML（单词点击弹翻译 + 用户标熟练度 + 段落翻译折叠 + 今日单词筛选）。

## 模式

- **A 场景片段**（default）— 多个独立小场景，一个场景可以包含多个单词
- **B 小说** — 500-600 词的有趣小说
- **C 考研阅读**（optional）— 550-650 词议论文 + 5 道四选一

**切换词：**

- "讲个故事" / "小说" / "来篇 B" → B
- "考研阅读" / "做阅读题" / "来篇 C" → C
- 默认 → A

## 步骤

- **Step 1**: 拉取今日单词
- **Step 2**: 选主线词 + 配角词
- **Step 3**: 写文章 + 生成翻译（同次 LLM 调用）
- **渲染**: `python3 scripts/render_html.py` 产出 `contexts/<日期>/page.html`

---

### Step 1: 拉取今日单词

**路径：**


| 用户触发              | 端点                          | 怎么筛                                                                                 |
| --------------------- | ----------------------------- | -------------------------------------------------------------------------------------- |
| 默认（"今日精读" 等） | `POST /study/get_today_items` | **合并 is_finished=true + is_finished=false 两次**（按 voc_id 去重），拿今日全集 55 词 |

**`get_today_items` 必须合并两次**：18:00 半学完时 `is_finished=true` 返回 21、`is_finished=false` 返回 34；23:00+ 学完后只 `is_finished=true` 有 55 词。**任何时点都合并去重**才能拿全 55 词。**不要** fallback 到 `query_study_records`。

**字段 enum：**

- `first_response`：`FAMILIAR` / `VAGUE` / `FORGET` / `WELL_FAMILIAR` / `CANCEL_WELL_FAMILIAR`（**注意 FORGET 不是 FORGOT**）
- `is_new`（新词/复习词）、`is_finished`（已学/未学）
- `tags`：`STICKING` / `WELL_FAMILIAR`

API 详情见 `references/maimemo-api/study.md`。

**完成条件：** 拿到合并后的词列表（理想 55 词，最少 ≥ 12 词）

---

### Step 2: 选词

```python
# 必须合并两次去重
finished = get_today_items(is_finished=True, limit=200)
unfinished = get_today_items(is_finished=False, limit=200)
seen, today_words = set(), []
for it in finished + unfinished:
    if it["voc_id"] not in seen:
        seen.add(it["voc_id"]); today_words.append(it)
```

所有词**全部进入待写列表**

---

### Step 3: 写文章 + 生成翻译（一次 LLM 调用）

LLM 在同次调用中产出三件事（避免二次调用浪费 token + 上下文漂移）：

1. **article.md 主体** — 场景/小说/考研阅读（保留旧行为：`#word*` 标记重点词）
2. **article.md 末尾 `## Translation` 块** — 每段一段中文翻译（每段顺序与正文一致）
3. **annotations.json `word_translations` 字段** — 每个入选词的中文释义

**通用要求（沿用旧版）：**

- 所有入选词至少出现 1 次
- 自然用词，标记每个词位置（vivid *[1]*）

#### article.md 结构

```markdown
# YYYY-MM-DD

## 模式
A 短文

## 主线词
incidence, estate, indignation, ...

## 配角词
postwar, wholly, paternal, ...

## 文字稿

（段落 1：英文，含 *word* 重点词标记）

（段落 2：英文，含 *word* 重点词标记）

...

## Translation

（段落 1 中文翻译）

（段落 2 中文翻译）

...
```

**`## Translation` 约束：**

- 段数与正文段数**严格一致**
- 中文地道自然，必要时调整语序（不要逐词死译）
- 长度约为英文段的 60-80%

#### annotations.json 结构（新版）

```json
{
  "date": "2026-08-08",
  "mode": "A",
  "title": "The Whitmore Estate",
  "word_translations": {
    "incidence": "n. 发生率",
    "estate": "n. 房地产；遗产",
    "indignation": "n. 愤慨；义愤",
    "postwar": "adj. 战后的",
    "..."
  },
  "main_words": ["incidence", "estate", ...],
  "supporting_words": ["postwar", "wholly", ...]
}
```

**字段约束：**

- `word_translations`：覆盖**所有** main_words + supporting_words，**键名用单词原形小写**，值为简短中文释义（含词性 + ≤ 15 字）
- 不再有 `paragraphs[].cards`（旧版混合派标注卡已删除，HTML 不再渲染）
- 不再有封面图 / 音频字段（新版页面无头图无音频条）

#### LLM Prompt 模板（追加到现有 Step 3 prompt 末尾）

```
# 翻译产出（同次调用）

输出三件事：
1. 文章正文（含 *word* 标记，保留原 Step 3 风格）
2. 文章末尾 `## Translation` 块：每段一段中文翻译，段数与正文一致
3. JSON 块（用 ```json ... ``` 包裹，不要其他解释）：

{
  "date": "{{TODAY}}",
  "mode": "{{MODE}}",
  "title": "{{TITLE}}",
  "word_translations": {
    "word1": "n. 释义",
    "word2": "v. 释义",
    ...
  },
  "main_words": [...按选词顺序],
  "supporting_words": [...]
}

约束：
- word_translations 必须覆盖所有 main_words + supporting_words
- 释义格式："词性. 中文释义"，多个义项用；分隔
- 不要写"详见词典""常用词"等无信息内容
- JSON 顶层无注释，键名用单词原形小写
```

---

## 渲染

```bash
python3 scripts/render_html.py                    # 用今天日期
python3 scripts/render_html.py --date 2026-08-08  # 指定日期
python3 scripts/render_html.py --dir contexts/<dir>  # 指定目录
```

读 `article.md` + `annotations.json`，产出 `contexts/<日期>/page.html`（居中单栏 + 两个 tab）。

**输入校验（缺一即报错退出）：**

- `article.md` 存在
- `annotations.json` 存在且含 `word_translations` 字段
- `article.md` 含 `## Translation` 块（段落数 ≥ 1）

**输出：** 单文件 `page.html`，内嵌 CSS+JS，无外部依赖（除 Google Fonts 可选）。

---

## 页面功能

### 两个 tab


| tab         | 功能                                                                                                                                         |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 📖 阅读     | 居中段落（680px 行宽），重点词下划虚线，点击弹翻译+熟练度卡片；段落末尾"显示中文翻译"折叠/展开；划选任意单词弹熟练度小条并用对应色荧光笔高亮 |
| 📚 今日单词 | 默认按段落出现顺序平铺所有 main_words + supporting_words；顶部筛选按钮：全部 / 陌生 / 模糊 / 熟练；点击单词弹翻译+熟练度卡片                 |

### 单词交互


| 类型                  | 视觉                                     | 点击行为                                                          |
| --------------------- | ---------------------------------------- | ----------------------------------------------------------------- |
| `*word*` 标记的入选词 | 下划虚线（砖红`#c0392b`，offset 4px）    | 弹 280px 浮动卡片：标题（单词 + ×关闭）+ 中文释义 + 熟练度三按钮 |
| 划选的任意词          | 默认无样式；标熟练度后用对应色荧光笔高亮 | 弹 200px 浮动小条：熟练度三按钮（无翻译，因非入选词）             |

**两种视觉正交：** 入选词的下划虚线**不**因熟练度变化，荧光笔**只**出现在划选的非入选词上（或入选词的标熟练度反馈用卡片，不改下划）。

### 熟练度交互


| 行为                          | 结果                               |
| ----------------------------- | ---------------------------------- |
| 单击 🟢熟练 / 🟡模糊 / 🔴陌生 | 设为对应状态；再点同色清除（无色） |
| 弹窗 /× 关闭                 | 不改熟练度，仅关闭                 |
| 顶部 🗑 清空按钮              | 二次确认后清空今日所有熟练度       |

**存储：** localStorage `memo-proficiency-YYYY-MM-DD` → `{word: "熟悉"|"模糊"|"陌生"}`

**颜色：**

- 熟练 `#2ecc71`（绿）
- 模糊 `#f1c40f`（黄）
- 陌生 `#e74c3c`（红）

荧光笔透明度 ≈ 25-35%（不挡文字）。

### 工具栏


| 按钮           | 功能                                                     |
| -------------- | -------------------------------------------------------- |
| 🌙 / ☀️ 主题 | 切换亮 / 暗色模式（localStorage 记忆）                   |
| Aa 字号        | 14px / 16px / 18px / 20px                                |
| 🗑 清空        | 二次确认后清空今日熟练度                                 |
| 🖨 导出 PDF    | window.print()（配合 @media print CSS：单栏 + 无工具栏） |

### 视觉风格

- 背景：亮 `#f7f5f0` / 暗 `#1a1714`
- 字体：Georgia / 思源宋体 / -apple-system
- 强调色：砖红 `#c0392b`（hover/focus/重点词下划）
- 段落：居中 680px、行高 1.95、字号 16px（默认）
- 间距：段落间 32px（段标签距上段 24px）
- 段标签：`P1` `P2` …（小字、衬线、橙色，左对齐在段首上方）

---

#### B 小说

500-600 词单章节，有角色有剧情，所有词至少出现 1 次。`## Translation` 块为整篇小说的中文翻译（1 段）。

---

#### C 考研阅读（optional）

550-650 词议论文 + 5 道四选一（主旨/细节/推理/词义/态度）。**严格约束**：

- 题材：社科/教育/医学伦理/科技政策，**避开政治与中美国情**
- 风格：模仿经济学人/卫报 — 长难句占比 ≥ 30%（含 ≥2 个从句）、抽象学术名词（phenomenon/perception/institution/prevalence）、转折/让步词密集（however/yet/while/although/consequently）、回避口语化与第一二人称
- 生词密度 ≤ 3%
- 题文同序：题目顺序 ≈ 段落顺序（约 60% 准确度）

**5 道题模板与顺序：**


| # | 题型     | 题干标志                                              |
| - | -------- | ----------------------------------------------------- |
| 1 | 主旨大意 | `The passage is mainly about...`                      |
| 2 | 细节定位 | `According to Paragraph X, ...`                       |
| 3 | 推理判断 | `It can be inferred that...`                          |
| 4 | 词义猜测 | `The word "..." (in line X) is closest in meaning to` |
| 5 | 态度观点 | `The author's attitude toward ... is one of`          |

**6 大干扰项手法**（每题至少用 2 种）：偷换概念 / 望文生义 / 细节杂糅 / 因果倒置 / 答非所问 / 无中生有

**答案特征：** 正确选项 = 原文某句的**同义改写**；含 `some/perhaps/seem/about/probably` 缓和词的多为正确；含 `certainly/extremely/never/always/must` 绝对化词的多为错误；例证题答案在**例子前面的观点句**，不在例子本身。

深度参考 `references/exam-format.md`（含考研大纲、来源刊物、英一/英二差异、自检清单）。

---

## 反例清单（生成时避开）

- ❌ 释义只写"n. 苹果"（无词性或只有单词释义）→ ✅ `n. 苹果；果树`
- ❌ 段落翻译逐词死译（"the cat sat on the mat" → "那 猫 坐 在 那 垫子"）→ ✅ 地道中文，必要时调整语序
- ❌ `word_translations` 漏词（缺某个入选词）→ ✅ 必须覆盖所有 main_words + supporting_words
- ❌ 段落数与 `## Translation` 段数不一致 → ✅ 严格 1:1
- ❌ 把"荧光笔"和"下划虚线"混在一起（入选词标熟练度时改成荧光色）→ ✅ 两者正交，下划虚线保持砖红不动
