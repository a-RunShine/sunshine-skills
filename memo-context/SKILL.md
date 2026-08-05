---
name: memo-context
description: Use when the user wants to turn today's Maimemo vocabulary into a contextual story/novel/dialogue for listening practice, save context to a daily archive, or push specific words back into a Maimemo cloud wordbook. Triggers: "今日精读" / "今晚生成" / "讲个故事" / "用对话" / "讲没记住的" / "灌 X Y Z" / "memo-context".
---

# memo-context

把墨墨今日词汇转成短文/小说/对话，朗读并按日存档，帮你从真实语境强化记忆。

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

### Step 1: 拉取今日单词

**两条路径，看用户触发选：**

| 用户触发 | 用哪个端点 | 怎么筛 |
|---|---|---|
| 默认（"今日精读" 等）| `POST /study/get_today_items` | 直接拿今日清单（墨墨 App "今日学习"列表）|
| "讲没记住的" / "模糊的" / "忘的" | `POST /study/query_study_records` | 拉全量，客户端筛 `last_response ∈ {VAGUE, FORGET}` ∪ `tags ∋ STICKING` |

**重要前置检查：** 先调 `POST /study/get_study_progress` 看今天学习进度（`finished/total`）。如果 `finished == total` 且用户没要求"讲没记住的"，提示"今天已学完 N 个，是否还做精读？"

**`get_today_items` 退路（重要）**：学完当天后,此接口可能返回 0（API 行为:已学完的清单不再返回）。如果返回 0,**自动 fallback**：
- 改用 `query_study_records`(limit=200)拉全量
- 客户端筛 `add_date.startswith(TODAY) ∪ next_study_date.startswith(TODAY)` — 这是"今日学过的所有词",一般 50-60 个
- 把这个集合作为 Step 2 的词源,而不是"只 due 的 9 词"

API 详情见 `references/maimemo-api/index.md`（含 schema/字段语义/时区/限流）和 `references/maimemo-api/study.md`（5 个端点完整文档）。

**字段 enum 速查：**
- `last_response`: `FAMILIAR` / `VAGUE` / `FORGET` / `WELL_FAMILIAR` / `CANCEL_WELL_FAMILIAR`（**注意 FORGET 不是 FORGOT**）
- `tags`: `STICKING` / `WELL_FAMILIAR`

**完成条件：** 拿到词列表（`voc_spelling` + `last_response` + `tags` + `study_count` + `add_date` + `next_study_date`）,理想情况 ≥ 12 词,最少 ≥ 5 词

### Step 2: 选主线词 + 配角词

**词源（重要）：从"今日学过的所有词"里挑，不是只从 today_due 里挑。**

```python
# 推荐拉法
records = query_study_records(limit=200)
today_words = [r for r in records
               if r["add_date"].startswith(TODAY)        # 今天新学的
               or r["next_study_date"].startswith(TODAY)] # 今天 due 复习的
# → 一般 50-60 词（学完的 55 + 没学完的 due 词）
# 退路:如果 get_today_items 不空,用它的返回;否则用 query_study_records 的 today 筛选
```

**挑词原则（按重要性降序，从 today_words 里挑）：**
1. **新词**（`add_date == 今天` 或 `study_count <= 1`）— 必进主线，最需"第一次消化"
2. **STICKING 标签词** — 必进主线，"难记"是核心痛点
3. **VAGUE 词**（`last_response == "VAGUE"`）— 必进主线
4. **今日 due 词**（`next_study_date == 今天`）— 优先进主线
5. **剩余 FAMILIAR 词** — 凑数用,主线满后进配角

**数量规则：**
- **主线 12-25 词**（按 today_words 总数动态调，**目标是 18-22 词**）— 每词 2-3 次，文中反复出现
- **配角 0-15 词** — 剩余 today_words 各提 1 次挂脸熟
- **底线**：today_words >= 12 时,主线 12-25;today_words < 12 时,**全部进主线**(无配角)
- **不要因为 today_due 只有 9 个就把主线缩到 9 词** —— 把 today 学过的其他 FAMILIAR 词也用上

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
- 题目与答案另起一节（不朗读）

**深度参考（按需）：** `references/exam-format.md` 含完整考研大纲、来源刊物统计、英一/英二区别、生成 prompt 模板、自检清单。

**完成条件：** 完整文字稿 + 单词使用记录（哪个词在哪段）

### Step 4: 朗读

Mavis 自带 TTS：
- `synthesize_speech(text, output_file_path)`
- 输出 mp3 路径：`./contexts/YYYY-MM-DD/audio.mp3`
- voice 默认 `male-qn-qingse`，英文内容用 0.9 速度（清晰度优先于节奏）
- **D 模式只朗读 Passage 部分，不朗读题目与答案**（题目供用户事后自测用）

**完成条件：** mp3 文件生成（用户能听到）

### Step 4.5: 生成封面图（推荐）

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

### Step 5: 存档

**新结构（2026-08-04 起）：** 每日内容存为目录，而不是单文件。

```
contexts/YYYY-MM-DD/
├── article.md       # 文字稿
├── audio.mp3        # 朗读
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

## 音频
[mp3 链接]
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

## 音频
[audio.mp3](./audio.mp3)
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

**关于封面图**：脚本会**自动检测** `cover.png`（Step 4.5 产物），存在就嵌入到页面顶部的 banner 块；不存在就不渲染 banner（HTML 照常可用）。要强制跳过用 `--no-cover`。

**HTML 设计**：
- **顶部头图 banner**（如 cover.png 存在）：360px 高，object-fit: cover，左下角斜体 caption
- **双侧边栏**（可收放）：左 = 词表（点词跳转 + 闪红），右 = 标注卡（按段分组 details 折叠）
- **顶部工具栏**：字号 / 倍速 / 暗色模式 / 导出 PDF
- **底部音频播放器**：HTML5 audio，可倍速
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
- **失败降级** — API 拉不到词 → 提示检查 token；TTS 失败 → 跳过朗读只存档
- **客户端时区** — API 字段 `*_date` 是 UTC，但 anchor 在每天 16:00Z（即北京时间当天 0 点）。判断"今天"用 `next_study_date.startswith("2026-08-03")` 这种字符串前缀匹配就行，不用 DateTime 换算
- **D 模式出题标准** — 完整硬约束已写在 Step 3 D 模式核心约束块（题型/干扰项/答案特征/写作风格）。`references/exam-format.md` 是深度出处（含考研大纲、来源刊物、英一/英二差异、生成 prompt 模板、自检清单），需要时再读
