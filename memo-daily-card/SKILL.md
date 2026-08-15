---
name: memo-daily-card
description: Use when the user wants to automatically generate "today's all 55 words" as dense illustrated cards, split into two batches (weak words / known words) and push to Feishu DM. Combines Maimemo's get_today_items × 2 merge logic with image_synthesize dense-grid rendering. Triggers: "/memo-daily" / "今日全词出图" / "今日55词大图" / "daily-card".
---

# memo-daily-card

把墨墨今天**所有学过**的 55 词自动分成**两批**（薄弱 + 认识），每批攒成 **1-N 张密集讲解大图**（每张 ≤ 12 词，3×4 网格）发到飞书，全程不需用户确认。

## 核心规则

- **数据源**：`get_today_items` 合并 `is_finished=true` + `is_finished=false` 两次（复用 `memo-context/SKILL.md` Step 1-2 策略，不依赖 grill-me / ask_user）
- **分类**：
  - `weak` = `first_response ∈ {VAGUE, FORGET}` ∪ `tags ⊋ STICKING`
  - `known` = 其余（含 `STUDY_RESPONSE_UNSPECIFIED` 新词）
- **分图规则**：⌈N/12⌉ 张大图，每张固定 3×4 网格，**每张词数 ≤ 12**（24 词 → 2 张，13 词 → 2 张，12 词 → 1 张，9 词 → 1 张）
- **两批发送**：
  - 批 1 薄弱：先发"今天薄弱词 N 词"介绍 + N 张大图（FORGET > STICKING > VAGUE > study_count asc 排）
  - 批 2 认识：再发"今天认识词 M 词"介绍 + M 张大图（墨墨原序）
- **全自动**：跑完即结束，**不** grill-me、**不**等用户反馈、**不**留改稿钩子
- **空批处理**：
  - 薄弱 = 0 → 跳过薄弱批，只发认识批
  - 认识 = 0 → 跳过认识批，只发薄弱批（理论上不会出现，因为 55 词至少一部分认识）
- **风格**：v1 锁"可爱叙事风 + 思源黑体"，**不**参数化

## 步骤（按顺序执行，Agent + Scripts 混合模式）

**Agent 介入点**：Step 1.5（Mavis 知识填 5 元素）——墨墨里 0 interpretations 时，**必须**用 LLM 知识兜底，纯 scripts 搞不定。

### Step 1: 拉今日 55 词 + 分类 — Agent 调 `scripts/fetch_today.py`

```bash
python3 ~/.claude/skills/memo-daily-card/scripts/fetch_today.py
```

- 调 `POST /study/get_today_items` × 2（is_finished=true + is_finished=false，limit=200 各）
- 按 `voc_id` 去重合并 → 任意时点都拿全 55 词（= progress.total）
- 客户端分类：weak / known
- 排序：弱前认后；弱内部 FORGET > STICKING > VAGUE > study_count asc；认内部墨墨原序
- 输出 `.today-weak/today.json`（每词含 `voc_id` + `spelling` + `first_response` + `tags` + `study_count` + `category`）
- 边界：API 失败 → 抛错退出，飞书**不**发

**API 详情**：见 `references/maimemo-merge.md`

### Step 1.5: Mavis 知识填 5 元素 — **Agent 用 LLM 生成**

```bash
# Agent 在跑 skill 时，手动用 LLM 知识填 55 词的 5 元素
# 不调用任何 script，纯 Agent 自身能力
```

读 `.today-weak/today.json` 的 words 列表，对每词用训练知识填：

```json
{
  "voc_id": "...",
  "spelling": "clinic",
  "phonetic": "/ˈklɪnɪk/",
  "pos": "n.",
  "meaning_zh": "诊所；门诊部",
  "example_en_clean": "She went to the clinic for a check-up.",
  "mnemonic_visual": "a small white clinic with a red cross sign",
  "category": "weak"  // 或 "known"，从 today.json 原样复制
}
```

**为什么不调墨墨 API 拉 interpretations/phrases？**
- 经验证：用户墨墨里这些词**全 0 内容**（没存过），墨墨拉了也是空
- 墨墨有内容时反而**格式不一致**（可能只有 interpretation 没 phrase，或反之），统一走 LLM 知识更稳
- LLM 知识对常见词准确率 95%+（已在 8/6 验证 24 词 100% 可用，55 词同理）
- 55 词 → 5 批 12 词 LLM 调用（Agent 可分批填，单批失败不影响其他批）

**输出** `.today-weak/cards-clean.json`（JSON 数组，按 `today.json` 顺序，含 `category` 字段）

### Step 2: 写 prompt 模板（分两批）— `scripts/write_prompts.py`

```bash
python3 ~/.claude/skills/memo-daily-card/scripts/write_prompts.py
```

- 读 `cards-clean.json` → 按 `category` 拆成 `weak_cards` / `known_cards`
- 每批独立分图：`chunks = [cards[i:i+12] for i in range(0, len(cards), 12)]`
- 每图写一个 `dense-prompt-{weak|known}-{N}.txt` 到 `.today-weak/`
- prompt 结构化：3×4 网格 + 每格 5 元素（助记图 + 拼写 + 音标词性 + 中文释义 + 例句加粗）+ 风格约束（思源黑体 / 留白 / 颜色）+ 防误标约束
- 空批跳过（0 词不写 prompt）

**Prompt 模板细节**：见 `references/prompt-template.md`

### Step 3: 出图 — Agent 调 `image_synthesize`

读 `.today-weak/dense-prompt-{weak|known}-*.txt`：

**关键坑**（已踩过）：
- `output_file_path` 必须用**相对路径**（如 `weakness-part1.png` / `knownness-part1.png`），不能绝对路径（image_synthesize 拒绝绝对路径，会报"is outside the workspace"）
- 相对路径写入到 `/Users/sunshine/.minimax/workspace/`（agent default workspace），**必须**手动 `cp` 到 `cwd/.today-weak/`
- `aspect_ratio="16:9"` + `resolution="2K"`

```bash
# 出图后必须搬图
cp /Users/sunshine/.minimax/workspace/weakness-part1.png /Users/sunshine/Desktop/墨墨记单词/.today-weak/
cp /Users/sunshine/.minimax/workspace/knownness-part1.png /Users/sunshine/Desktop/墨墨记单词/.today-weak/
# ...以此类推
```

- 失败处理：单图失败 → 跳过该图，render_and_send 会发"图 N 失败"告警；全部图失败 → 发 fallback 文本

### Step 4: 压缩 + 飞书发送（分两批）— `scripts/render_and_send.py`

```bash
# dry-run（仅压缩 + 预览，不发）
python3 ~/.claude/skills/memo-daily-card/scripts/render_and_send.py

# 真发飞书
python3 ~/.claude/skills/memo-daily-card/scripts/render_and_send.py --send
```

读 `.today-weak/today.json` + `.today-weak/{weakness,knownness}-part*.png`：

- 按 `today.json.date` 过滤旧图（旧图挪到 `.bak/`，避免被误发）
- PNG → JPEG 压缩（quality 88, 85% resize，target ≤ 1MB；飞书 5MB 限制）
- 飞书分两批发：
  1. **批 1 薄弱**（如果 weak_n > 0）：1 条 Markdown 介绍 + N 张 `--image <basename>.jpg`（**单引号**包裹避免反引号被 bash 吃；必须 `cd .today-weak/ && lark-cli` — cwd-relative basename；**全部** `--as bot`）
  2. **批 2 认识**（如果 known_n > 0）：1 条 Markdown 介绍 + M 张图
- 失败处理：image_synthesize 单图失败 → 跳过该图；lark 失败 → 发 fallback 文本

**飞书坑细节**：见 `references/lark-send.md`

## 使用方式

```bash
# 手动触发（用户说"今天 55 词出图"）
/memo-daily

# 定时触发（cron 已在 memo-weakness-daily-20h 配置）
#   20:00 跑（Mavis agent 必须在场执行 Step 1.5）：
#   cd ~/Desktop/墨墨记单词   # cwd 必须是项目根
#   python3 ~/.claude/skills/memo-daily-card/scripts/fetch_today.py
#   # Step 1.5 - Agent 用 LLM 知识分批填 cwd/.today-weak/cards-clean.json
#   python3 ~/.claude/skills/memo-daily-card/scripts/write_prompts.py
#   # Step 3 - Agent 调 image_synthesize（相对路径 → cp 到 .today-weak/）
#   python3 ~/.claude/skills/memo-daily-card/scripts/render_and_send.py --send
```

## 输出目录

所有中间产物 + 最终图都落在 **cwd** 的 `.today-weak/`（cwd 必须是项目根）：

```
<项目根>/.today-weak/
├── today.json              # Step 1 输出（含 stats + 分类 + 55 词）
├── cards-clean.json        # Step 1.5（Agent 用 LLM 知识填 55 词 5 元素 + category）
├── dense-prompt-weak-1.txt # Step 2 输出（薄弱批，N 张）
├── dense-prompt-weak-2.txt
├── dense-prompt-known-1.txt # Step 2 输出（认识批，M 张）
├── dense-prompt-known-2.txt
├── weakness-part1.png      # Step 3 原始 PNG（5-6MB，留档）
├── weakness-part1.jpg      # Step 4 压缩后（≤ 1MB，飞书发送用）
├── knownness-part1.png
└── knownness-part1.jpg
```

`.today-weak/` 加 `.gitignore`（不提交）。

## 失败回退矩阵

| Step | 失败 | 处理 |
|---|---|---|
| Step 1 | API 拉不到 | 抛错退出，飞书**不**发（不打扰） |
| Step 1.5 | Agent LLM 知识填失败 | 抛错退出，飞书**不**发 |
| Step 2 | 写 prompt 失败 | 抛错退出，**不**发飞书 |
| Step 3 | 单图 image_synthesize 失败 | 跳过该图，飞书发"图 N 失败"告警 |
| Step 3 | 全部图失败 | 飞书发 fallback 文本（"出图失败"）|
| Step 4 | 飞书 Markdown 介绍失败 | 跳过介绍，直接发图 |
| Step 4 | 飞书图片发送失败 | 跳过该图，整体**不**中断 |
| 边界 | 薄弱 0 词 | 跳过薄弱批，只发认识批 |
| 边界 | 认识 0 词 | 跳过认识批，只发薄弱批（理论上不会出现） |
| 边界 | 薄弱+认识 0 词 | 全部跳过（理论上不会出现，55 词总 ≥ 0） |

## 时区与墨墨每日重置

- 墨墨 **凌晨 4:00** 重置今日任务（不是自然日 0:00）— 用户在 0:00-3:59 跑脚本时，`get_today_items` 拿的是**昨天**的 55 词
- `fetch_today.py` 的 `maimemo_today()` 函数处理这个偏移（4:00 切日期）
- 飞书介绍消息里写的"今天 N 词"也用 `today.json.date`，跟 API 语义一致

## 已知瑕疵（不修，知道就行）

- 助记图风格：模型自行选（实测：可爱叙事风居多，偶有写实）
- 字号：模型自行定（实测：12 词时偏大，24 词时偏小，但都清晰可读）
- 大小写：模型自行选拼写大小写（实测：part 1 大写、part 2 小写，不统一但不影响）
- 音标次重音位置：`counterbalance` 等长词可能不准（Mavis 知识兜底的固有限制）
- 知识兜底准确度：Mavis 训练知识对常见词准确率 95%+，但对低频/学术词可能有误差
- 5 批 12 词 LLM 调用：偶有单批失败，Agent 需重试该批

## 风格锚定（v1 锁，不改）

- **字体**：思源黑体（Source Han Sans / Noto Sans CJK）
- **助记图风**：可爱叙事插画风（避免写实/像素/极简）
- **网格**：3×4（行 × 列 = 3 行 × 4 列 = 12 格/图）
- **每格 5 元素**：
  1. 助记图（40% 高度，顶部）
  2. 拼写（大字号 + 音标 + 词性 一行）
  3. 中文释义（中号）
  4. 完整英文例句（目标词加粗，10-20 词）
  5. 留白（底部 10%）

## 依赖

- Python 3 + `requests` + `Pillow`
- `lark-cli`（已装在 `~/.lark-cli/bin/lark-cli` 或 PATH 里）
- 墨墨 token 在本 skill 自己的 `<skill_dir>/.env`（含 `MAIMEMO_TOKEN=...`）

## 相关 skill

- `memo-weakness-card`（v1，已废弃）：只画薄弱词版本，被本 skill 取代
- `memo-context`：基于"今日全 55 词"写文章（不同定位——语境派 vs 讲解派）
- `memo-suite` v1.1 数据分析：可看历史薄弱趋势（不参与本 skill）

## 踩过的坑（已写入 references）

- `get_today_items` 必须合并 `is_finished` 两次 — `references/maimemo-merge.md`
- `image_synthesize` 相对路径写 → cp 搬图；绝对路径会被拒 — `references/prompt-template.md` 末尾
- `lark-cli im +messages-send` 默认 user 身份发不出 — 用 `--as bot` — `references/lark-send.md`
- `lark-cli --file` 绝对路径和 `..` 都被拒 — `cd <dir> && --file <basename>` — `references/lark-send.md`
- `lark-cli` markdown 双引号陷阱 — 反引号被 bash 吃 — 用单引号 — `references/lark-send.md`
- `lark-cli` 单条消息 5MB 上限 — PNG → JPEG 压缩 — `references/lark-send.md`
- `lark-cli` 1.0.83+：image/file 跟 markdown 互斥，必须分两条发 — `references/lark-send.md`
