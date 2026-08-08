---
name: memo-context
description: Use when the user wants to turn today's Maimemo vocabulary into a contextual story/novel/dialogue for listening practice, save context to a daily archive, or push specific words back into a Maimemo cloud wordbook. Triggers: "今日精读" / "今晚生成" / "讲个故事" / "用对话" / "讲没记住的" / "灌 X Y Z" / "出图" / "全图" / "不要图" / "跳过图" / "memo-context".
---

# memo-context

把墨墨今日词汇转成短文/小说/对话并按日存档，帮你从真实语境强化记忆。

## 模式

- **A 短文** — 800-1000 词的连贯短文
- **B 小说** — 1000-1500 词的章节，有角色有剧情
- **C 对话** — 5-8 轮对话，2-3 人
- **D 考研阅读**（default）— 550-650 词议论文（模仿经济学人/卫报风格）+ 5 道四选一（主旨/细节/推理/词义/态度）

**切换词：**
- "讲个故事" / "来篇小说" / "小说" → B
- "用对话" / "练口语" / "对话" → C
- "短文" / "随便" / "来篇 A" → A
- 默认（无切换词）→ D

## 步骤

- **Step 1**: 拉取今日单词
- **Step 2**: 选主线词 + 配角词
- **Step 3**: 写内容（按 A/B/C/D 模式）
- **Step 4**: 生成封面图（可选）
- **Step 4.5**: 生成分段卡片（默认必做，可选跳过 / 全图变体）
- **Step 5**: 存档
- **Step 5.5**: 生成学霸标注（混合派）
- **Step 6**: 渲染 HTML
- **Step 7**: 等用户回灌（用户主导，不主动）

### Step 1: 拉取今日单词

**两条路径，看用户触发选：**

| 用户触发 | 用哪个端点 | 怎么筛 |
|---|---|---|
| 默认（"今日精读" 等）| `POST /study/get_today_items` | **合并 is_finished=true + is_finished=false 两次调用**（按 voc_id 去重），拿今日学习全集 55 词（= progress.total，跟墨墨 App "今日学习"列表 1:1）|
| "讲没记住的" / "模糊的" / "忘的" | `POST /study/query_study_records` | 拉全量，客户端筛 `last_response ∈ {VAGUE, FORGET}` ∪ `tags ∋ STICKING` |

**重要前置检查：** 先调 `POST /study/get_study_progress` 看今天学习进度（`finished/total`），**仅用于诊断"已学/未学"比例，不是词源**。

**`get_today_items` 必须合并两次（重要）**：
- 18:00 跑时用户通常只学完 21 词（半学完）→ `is_finished=true` 返回 21，`is_finished=false` 返回 34
- 23:00+ 用户已学完所有 55 词 → `is_finished=true` 返回 55，`is_finished=false` 返回 0
- **任何时点都必须合并两次按 voc_id 去重**才能拿全 55 词
- **不要**只调一次（半学完时会漏 34 词——这就是 2026-08-06 当晚 v1/v2 出错的根因）
- **不 fallback** 到 `query_study_records`（用户明确要"只针对今天"，不要全量库）

API 详情见 `references/maimemo-api/index.md`（含 schema/字段语义/时区/限流）和 `references/maimemo-api/study.md`（5 个端点完整文档）。

**字段 enum 速查：**
- `get_today_items` 返回 `first_response`：`FAMILIAR` / `VAGUE` / `FORGET` / `WELL_FAMILIAR` / `CANCEL_WELL_FAMILIAR`（**注意 FORGET 不是 FORGOT**）
- `get_today_items` 还返回 `is_new`（bool，新词/复习词）和 `is_finished`（bool，已学/未学）
- `query_study_records` 返回 `last_response`（同 enum）+ `tags`（`STICKING` / `WELL_FAMILIAR`）+ `add_date` / `next_study_date` / `study_count`
- **关键**：两个端点字段名不同，别混用——`get_today_items` 用 `first_response`，`query_study_records` 用 `last_response`

**完成条件：** 拿到合并后的词列表（`voc_spelling` + `first_response` + `is_new` + `tags`），理想情况 = 55 词（= progress.total），最少 ≥ 12 词

### Step 2: 选主线词 + 配角词

**词源（重要）：从合并 is_finished 两次调用后的 55 词里挑。**

```python
# 推荐拉法（必须合并两次）
finished_items = get_today_items(is_finished=True, limit=200)    # 已学
unfinished_items = get_today_items(is_finished=False, limit=200)  # 未学
# 按 voc_id 去重合并
seen = set()
today_words = []
for it in finished_items + unfinished_items:
    if it["voc_id"] not in seen:
        seen.add(it["voc_id"])
        today_words.append(it)
# → 任何时点都拿全 55 词（= progress.total）
```

**挑词原则（按重要性降序，从 today_words 里按 is_new × first_response 分四类挑）：**

| 优先级 | 类别 | 字段判断 | 处理 |
|---|---|---|---|
| 1 | **新词 + 不熟悉** | `is_new=true AND first_response ∈ {VAGUE, FORGET}` 或 `tags ⊋ STICKING` | **必进主线**（"所有新学"+"第一次消化"）|
| 1 | **复习词 + 不熟悉** | `is_new=false AND first_response ∈ {VAGUE, FORGET}` 或 `tags ⊋ STICKING` | **必进主线**（"部分不熟悉"复习词）|
| 2 | **新词 + 熟悉** | `is_new=true AND first_response == FAMILIAR` | **全部进配角**（"所有新学"挂脸熟）|
| 3 | **复习词 + 熟悉** | `is_new=false AND first_response == FAMILIAR` | **默认不写**（用户说"该用可以用"时再进配角）|

**数量规则：**
- **主线 18-25 词**（按 today_words 动态调，**目标是 22 词**）— 每词 2-3 次，文中反复出现
- **配角 0-20 词** — 剩余 today_words 各提 1 次挂脸熟
- **底线**：today_words >= 12 时,主线 18-25;today_words < 12 时,**全部进主线**(无配角)
- **不要因为 is_finished=false 0 词就跳过** —— 18:00 跑时是常态，合并后才能拿全 55 词

**挑完输出挑选理由**让用户 review（"今天挑 vivid、tangible、eloquent + grace 作主线，因为能串成'艺术展'故事"）。

**完成条件：** 主线词列表 + 配角词列表 + 挑选理由

### Step 3: 写内容

按模式生成。

| 模式 | 长度 | 结构 |
|---|---|---|
| A 短文 | 500-600 词 | 起承转合 |
| B 小说 | 500-600 词 | 一章完整剧情 |
| C 对话 | 500-600 词（5-8 轮）| 2-3 人 |
| D 考研阅读 | 文章 550-650 词 + 5 道四选一 | 4-5 段议论文（社科/教育/医学伦理/科技），模仿经济学人/卫报 |

**通用要求：**
- 主线词每词 2-3 次（被"真正消化"）
- 配角词各提 1 次（挂个脸熟）
- 内容必须自然，不为用词而用词
- 文字稿里**标记每个词出现位置**（vivid *[1]*, *[2]*, *[3]*）

### D 模式核心约束（考研阅读 — default）

**文章硬约束：**
- 词数 550-650，4-5 段，**生词密度 ≤ 3%**（约 ≤15 个生词）
- 题材：社科/教育/医学伦理/科技政策类，**避开政治与中美国情**
- 风格模仿经济学人/卫报：长难句占比 ≥ 30%（含 ≥2 个从句）、抽象学术名词（phenomenon/perception/institution/prevalence）、转折/让步词密集（however/yet/while/although/consequently）、回避口语化与第一二人称
- 题文同序：题目顺序 ≈ 段落顺序（约 60% 准确度）

**5 道题模板与顺序：**

| # | 题型 | 题干标志 |
|---|---|---|
| 1 | 主旨大意 | `The passage is mainly about...` / `Which of the following best summarizes...` |
| 2 | 细节定位 | `According to Paragraph X, ...` |
| 3 | 推理判断 | `It can be inferred that...` / `The author implies that...` |
| 4 | 词义猜测 | `The word "..." (in line X) is closest in meaning to` |
| 5 | 态度观点 | `The author's attitude toward ... is one of` |

**6 大干扰项手法（每题至少用 2 种）：**
1. 偷换概念（张冠李戴）— 偷换主语/动作发出者/范围/时态/极性
2. 望文生义 — 凭空给某名词加文中不存在的动宾搭配
3. 细节杂糅 — 跨句拼凑，修饰关系断裂
4. 因果倒置 — "A 导致 B" → "B 导致 A"
5. 答非所问 — 文中提到但答错问点（例：题问作者态度，选项讲他人态度）
6. 无中生有 — 完全捏造，原文无此信息

**答案特征（决定哪个是正确选项）：**
- 正确选项 = 原文某句的**同义改写**，不直接抄原句
- 含 `some/perhaps/seem/about/probably` 缓和词的多为正确
- 含 `certainly/extremely/never/always/must` 绝对化词的多为错误
- 主旨题答案要能覆盖全文、不含细节性名词
- 例证题答案在**例子前面的观点句**，不在例子本身

**存档模板：**
- Passage 段用词位置标记 *[1]*、*[2]*...
- 题目与答案另起一节

**深度参考（按需）：** `references/exam-format.md` 含完整考研大纲、来源刊物统计、英一/英二区别、生成 prompt 模板、自检清单。

**完成条件：** 完整文字稿 + 单词使用记录（哪个词在哪段）

### Step 4: 生成封面图（推荐）

> **目的**：给单页 HTML 配一张主题头图，让页面不单调。**默认推荐做**，用户可要求跳过。

**调用 Mavis 自带的 `image_synthesize` 工具：**

```python
image_synthesize(
    requests=[{
        "prompt": "<根据文章主题设计的 prompt>",
        "output_file_path": "./contexts/YYYY-MM-DD/cover.png",
        "aspect_ratio": "16:9",
        "resolution": "2K",
    }]
)
```

**Prompt 设计原则**：
- **场景化**：把文章的"画面感"用英文写出来（老屋/阁楼/手稿/咖啡馆/考场 等）
- **风格统一**：油画感 / 电影剧照 / 写实摄影 选一种（推荐 cinematic painterly, 16:9 widescreen）
- **色调参考**：根据故事情绪定（暖琥珀=怀旧/冷蓝灰=紧张/暗橙=压抑 等）
- **避免**：抽象元素、文字水印、人脸特写（避免不自然）

**Prompt 模板**：
```
A cinematic [场景] scene featuring [关键道具/人物]. 
Soft [光线] light filters through, illuminating [氛围元素]. 
The atmosphere is [情绪形容词], evoking [主题词]. 
[风格要求] composition, [色调] tones, [光影要求] lighting, 16:9 widescreen.
```

**完成条件**：`cover.png` 写到 `contexts/YYYY-MM-DD/`

**降级**：生成失败 → 直接进 Step 6，HTML 不带 banner 块，文章照常可用。

### Step 4.5: 生成分段卡片（默认必做）

> **目的**：把今日文章按段拆成 9:16 竖图卡片，方便手机阅读 + 小红书/朋友圈分享。**默认每次必做**（无触发词），用户说 `不要图` / `跳过图` 时跳过。

**默认行为**：
- 每次跑 memo-context 必做（无触发词）
- **段数 ≤ 2 时跳过**（短文塞一组卡片太散）
- **段落拆法**：`⌈N/2⌉` 张卡片（默认 2 段/卡）
  - 3 段 → 2 张
  - 5 段 → 3 张
  - 6 段 → 3 张
  - 8 段 → 4 张
  - 10+ 段 → 5+ 张

**输出位置**：
```
contexts/YYYY-MM-DD/
├── card-1.png       # 段 1-2
├── card-2.png       # 段 3-4
└── card-N.png       # 段 (2N-1), (2N)
```

**调用 Mavis `image_synthesize`**：
```python
image_synthesize(
    requests=[{
        "prompt": "<见下方 Prompt 模板>",
        "output_file_path": "./contexts/YYYY-MM-DD/card-N.png",
        "aspect_ratio": "9:16",
        "resolution": "1K",
    }]
)
```

**Prompt 模板（3 条硬约束防翻车）**：
```
A 9:16 vertical reading-card poster, warm cinematic painterly style.
Top caption: "2026-08-05 — <article_title> · Part N of M".
Thin horizontal divider.
The main body renders the following English text CLEARLY and LEGIBLY
in a clean serif typeface on a SOFT CREAM-PAPER BACKGROUND WITHOUT
ANY HIGHLIGHT.

CRITICAL HIGHLIGHTING RULE: ONLY the words wrapped in asterisks below
get a small pale yellow rounded-rectangle background and slightly
bolder weight. ALL other words MUST stay on plain cream background
with NO yellow background, NO highlight, NO box, NO shading.
Highlight exactly these and nothing else:

"<article_paragraphs_joined_with_asterisked_main_words>"

Render every single word, character, and punctuation mark EXACTLY
as written. Do not abbreviate, summarize, paraphrase, translate,
or omit. Do not add background highlight to non-asterisked words.
Faint watercolor illustration of <scene matching this part's theme>
glows softly in the bottom margin, low contrast, like a watermark.
9:16 vertical, 1K resolution, no face close-up, no Chinese
characters, no extra captions.
```

**底部插图 prompt（按段落位置选）**：
- 段 1-2（开端/勘探）:高原日落 + 孤独身影 + 化石切片
- 段 3-4（争议/资金）:博物馆实验室 + 显微镜 + 羽毛化石
- 段 5-6（公开/反思）:展览厅 + 玻璃罩里的化石翅膀 + 聚光灯
- 段 7+ :按文章主题自拟（古都/海洋/太空/职场...），保持"低对比度 watermark"风格

**完成条件**：N 张 `card-N.png` 写到 `contexts/YYYY-MM-DD/`，跟 cover.png 放同目录

**降级**：
- 某张 card 生成失败 → 重试 1 次；仍失败则跳过该张，继续出下一张
- 全失败 → 整个 Step 4.5 跳过（不阻塞主流程）

**反悔触发词（跳过 Step 4.5）**：
- `不要图` / `跳过图` / `无图` → 整个 Step 4.5 跳过

**变体 — 全图（可选）**：
- 触发词：`全图` / `长图` / `超高图`
- 产物：`full-long.png`，9:16 **4K**（3072×5504），塞全部段落（500-700 词也可塞下）
- **18:00 定时任务默认不带**（体积 ~20MB，zip 涨到 ~25MB）—— 只有手动跑才加

### Step 5: 存档

**新结构（2026-08-04 起）：** 每日内容存为目录，而不是单文件。

```
contexts/YYYY-MM-DD/
├── article.md       # 文字稿
├── annotations.json # 学霸标注（Step 5.5 产出）
└── page.html        # 单页网页（Step 6 产出）
```

`article.md` 内容：

文件结构（A/B/C 模式）：
```markdown
# YYYY-MM-DD

## 模式
A 短文

## 主线词
vivid, tangible, ...

## 配角词
abandon, ...

## 文字稿
[内容 + 词位置标记]
```

D 模式附加结构（紧跟 Passage 后追加）：
```markdown
## 题目

1. The passage is mainly about ...
   [A] ... [B] ... [C] ... [D] ...

2. ...

3. ...

4. ...

5. ...

## 答案与解析

1. 【答案】B 【解析】定位句+同义替换+干扰项手法
2. ...
3. ...
4. ...
5. ...
```

**完成条件：** `article.md` 写入 `contexts/YYYY-MM-DD/`

### Step 5.5: 生成学霸标注（混合派）

> **目的**：让每段的关键词有"考点 + 口诀"双视角标注，强化记忆 + 应试能力。

**调 LLM 生成 → 写入 `contexts/YYYY-MM-DD/annotations.json`**

**标注风格（混合派）**：
- **考试派**（每段每词必出）：考点·搭配 / 考点·构词 / 考点·辨析 / 易混对比 / 考点·频考
- **记忆派**（关键难词加 1 个）：谐音口诀 / 词根串联 / 画面联想 / 搭配口诀

**Prompt 模板**：见 `references/annotation-style.md` § 3（LLM Prompt 模板）— 复制粘贴替换 `{{...}}` 变量。

**JSON schema**：见 `references/annotation-style.md` § 1

**完成条件：** `annotations.json` 写入，结构符合 schema（每段 1-3 张卡，至少 1 张考试派）

### Step 6: 渲染 HTML

调 `scripts/render_html.py` 把 article.md + annotations.json 渲染成单页网页。

```bash
python3 .claude/skills/memo-context/scripts/render_html.py --date YYYY-MM-DD
```

**输出**：`contexts/YYYY-MM-DD/page.html`

**关于封面图**：脚本会**自动检测** `cover.png`（Step 4 产物），存在就嵌入到页面顶部的 banner 块；不存在就不渲染 banner（HTML 照常可用）。要强制跳过用 `--no-cover`。

**HTML 设计**：
- **顶部头图 banner**（如 cover.png 存在）：360px 高，object-fit: cover，左下角斜体 caption
- **双侧边栏**（可收放）：左 = 词表（点词跳转 + 闪红），右 = 标注卡（按段分组 details 折叠）
- **顶部工具栏**：字号 / 暗色模式 / 导出 PDF
- **暗色模式 highlight 改下划线**（避免"白字黄底"违和）+ 头图自动调暗 15%

**完成条件：** `page.html` 生成（用户用浏览器打开本地路径可看）

### Step 7: 等用户回灌（用户主导，不主动）

**不主动回灌。** 等用户说：
- "灌 X Y Z" → 灌指定词
- "灌带 * 的" / "都灌" → 灌所有标记词
- "灌主线" → 灌所有主线词

**回灌执行：**
- `POST /open/api/v1/notepads` 创建云词本
- `notepad.content` = 一行一个词（可用 `# 章节` 分组）
- `notepad.title` = `今日精读-YYYY-MM-DD`
- `notepad.brief` = 一句今日语境摘要
- `notepad.tags` = `["memo-context"]`

**完成条件：**
- 用户没说灌 → 停在这
- 用户说灌 → 调 API + 告诉用户"已灌 X 个词，打开墨墨 App 就能看到"

## Access Token

第一次跑问用户要墨墨 access token，存到 `./.claude/skills/memo-context/.env`（项目本地）。

后续读这个文件。401（过期）时重新问。

## 注意事项

- **回灌不主动** — 必须用户说"灌"才执行
- **限流** — 墨墨 API：10秒 20 / 60秒 40 / 5小时 2000 次。每天 1-3 篇内容不会撞限流
- **失败降级** — API 拉不到词 → 提示检查 token
- **客户端时区** — API 字段 `*_date` 是 UTC，但 anchor 在每天 16:00Z（即北京时间当天 0 点）。判断"今天"用 `next_study_date.startswith("2026-08-03")` 这种字符串前缀匹配就行，不用 DateTime 换算
- **D 模式出题标准** — 完整硬约束已写在 Step 3 D 模式核心约束块（题型/干扰项/答案特征/写作风格）。`references/exam-format.md` 是深度出处（含考研大纲、来源刊物、英一/英二差异、生成 prompt 模板、自检清单），需要时再读
