---
name: memo-weakness-card
description: Use when the user wants to automatically generate "today's weak words" as dense illustrated explanation cards and push to Feishu DM. Combines Maimemo's get_today_items × 2 merge logic with image_synthesize dense-grid rendering. Triggers: "/memo-weakness" / "薄弱词出图" / "今日弱词大图" / "weakness-card" / "讲薄弱词的图".
---

# memo-weakness-card

把墨墨今天**所有学过**的词里**薄弱**的（VAGUE ∪ FORGET ∪ STICKING）自动攒成 **1-N 张密集讲解大图**（每张 ≤ 12 词，3×4 网格）发到飞书，全程不需用户确认。

## 核心规则

- **数据源**：`get_today_items` 合并 `is_finished=true` + `is_finished=false` 两次（复用 `memo-context/SKILL.md` Step 1-2 策略，不依赖 grill-me / ask_user）
- **薄弱定义**：`first_response ∈ {VAGUE, FORGET}` ∪ `tags ⊋ STICKING`
- **分图规则**：⌈N/12⌉ 张大图，每张固定 3×4 网格，**每张词数 ≤ 12**（24 词 → 2 张，13 词 → 2 张，12 词 → 1 张）
- **全自动**：跑完即结束，**不** grill-me、**不**等用户反馈、**不**留改稿钩子
- **空词处理**：`词数 = 0` → 发条飞书"今天没有薄弱词，恭喜 ✓"，**不**出图
- **少词处理**：`1-3 词` → 仍出 1 张图，空格子用"你今天学得很稳 ✓"占位
- **风格**：v1 锁"可爱叙事风 + 思源黑体"，**不**参数化

## 步骤（按顺序执行，Agent + Scripts 混合模式）

**Agent 介入点**：Step 1.5（Mavis 知识填 5 元素）——墨墨里 0 interpretations 时，**必须**用 LLM 知识兜底，纯 scripts 搞不定。

### Step 1: 拉薄弱词 — Agent 调 `scripts/fetch_weak.py`

```bash
python3 .claude/skills/memo-weakness-card/scripts/fetch_weak.py
```

- 调 `POST /study/get_today_items` × 2（is_finished=true + is_finished=false，limit=200 各）
- 按 `voc_id` 去重合并 → 任意时点都拿全 55 词（= progress.total）
- 客户端筛 `first_response ∈ {VAGUE, FORGET}` ∪ `tags ⊋ STICKING`
- 排序：`FORGET` > `STICKING` > `VAGUE` > `study_count` asc（学得少但弱排前面）
- 输出 `.today-weak/weak.json`（`voc_id` + `spelling` + `first_response` + `tags` + `study_count`）
- 边界：`词数 = 0` → 写 `weak.json` 含 `"count": 0`，**不**抛错（由 send_lark.py 决定发条提示）

**API 详情**：见 `references/maimemo-merge.md`

### Step 1.5: Mavis 知识填 5 元素 — **Agent 用 LLM 生成**

```bash
# Agent 在跑 skill 时，手动用 LLM 知识填 24 词的 5 元素
# 不调用任何 script，纯 Agent 自身能力
```

读 `.today-weak/weak.json` 的 words 列表，对每词用训练知识填：

```json
{
  "voc_id": "...",
  "spelling": "clinic",
  "phonetic": "/ˈklɪnɪk/",
  "pos": "n.",
  "meaning_zh": "诊所；门诊部",
  "example_en_clean": "She went to the clinic for a check-up.",
  "mnemonic_visual": "a small white clinic with a red cross sign"
}
```

**为什么不调墨墨 API 拉 interpretations/phrases？**
- 经验证：用户墨墨里这 24 词**全 0 内容**（没存过），墨墨拉了也是空
- 墨墨有内容时反而**格式不一致**（可能只有 interpretation 没 phrase，或反之），统一走 LLM 知识更稳
- LLM 知识对常见词准确率 95%+（已在 8/6 验证 24 词 100% 可用）

**输出** `.today-weak/cards-clean.json`（JSON 数组，按 `weak.json` 顺序）

### Step 2: 写 prompt 模板 — `scripts/write_prompts.py`

```bash
python3 .claude/skills/memo-weakness-card/scripts/write_prompts.py
```

- 读 `cards-clean.json` → 分图：`chunks = [cards[i:i+12] for i in range(0, len(cards), 12)]`
- 每图写一个 `dense-prompt-{N}.txt` 到 `.today-weak/`
- prompt 结构化：3×4 网格 + 每格 5 元素（助记图 + 拼写 + 音标词性 + 中文释义 + 例句加粗）+ 风格约束（思源黑体 / 留白 / 颜色）+ 防误标约束
- prompt 模板见 `references/prompt-template.md`

### Step 3 + 4: 出图 + 飞书发送 — `scripts/render_and_send.py`

```bash
python3 .claude/skills/memo-weakness-card/scripts/render_and_send.py
```

读 `.today-weak/dense-prompt-*.txt`：
- 调 Mavis `image_synthesize`（requests 数组，N 个图 = 1 个 call）
  - **绝对路径** `output_file_path`（避免落到 `/Users/sunshine/.minimax/workspace/`）
  - `aspect_ratio="16:9"` + `resolution="2K"`
- PNG 5-6MB → 用 PIL 转 JPEG（quality 88, 85% resize，target ≤ 1MB）
- 发飞书：
  1. 1 条 Markdown 介绍（**单引号**包裹避免反引号被 bash 吃）
  2. N 条 `--file <basename>.jpg`（必须 `cd .today-weak/ && lark-cli` — cwd-relative basename）
  3. **全部** `--as bot`
- 失败处理：image_synthesize 单图失败 → 跳过该图 + 发条告警；lark 失败 → 发 fallback 文本

**飞书坑细节**：见 `references/lark-send.md`

## 使用方式

```bash
# 手动触发（用户说"今天薄弱词出图"）
/memo-weakness

# 定时触发（v1.1 - cron 接入，本 skill v1 不带 cron 配置，外部配）
# 22:00 跑（Mavis agent 必须在场执行 Step 1.5）：
#   cd <项目根>   # cwd 必须是项目根
#   python3 ~/.claude/skills/memo-weakness-card/scripts/fetch_weak.py
#   # Step 1.5 - Agent 用 LLM 知识填 cwd/.today-weak/cards-clean.json
#   python3 ~/.claude/skills/memo-weakness-card/scripts/write_prompts.py
#   # Step 3 - Agent 调 image_synthesize（绝对路径写 PNG 到 cwd/.today-weak/）
#   python3 ~/.claude/skills/memo-weakness-card/scripts/render_and_send.py --send
```

## 输出目录

所有中间产物 + 最终图都落在 **cwd** 的 `.today-weak/`（cwd 必须是项目根）：

```
<项目根>/.today-weak/
├── weak.json              # Step 1 输出
├── cards-clean.json       # Step 1.5（Agent 用 LLM 知识填）
├── dense-prompt-1.txt     # Step 2 输出（每图一个）
├── dense-prompt-2.txt
├── weakness-part1.png     # Step 3 原始 PNG（5-6MB，留档）
├── weakness-part1.jpg     # Step 4 压缩后（≤ 1MB，飞书发送用）
├── weakness-part2.png
└── weakness-part2.jpg
```

`.today-weak/` 加 `.gitignore`（不提交）。

## 失败回退矩阵

| Step | 失败 | 处理 |
|---|---|---|
| Step 1 | API 拉不到 | 抛错退出，飞书**不**发（不打扰） |
| Step 1 | 词数 = 0 | 写 `weak.json`（count=0），继续；Step 4 发飞书"今天没薄弱词 ✓" |
| Step 1.5 | Agent LLM 知识填失败 | 抛错退出，飞书**不**发 |
| Step 2 | 写 prompt 失败 | 抛错退出，**不**发飞书 |
| Step 3 | 单图 image_synthesize 失败 | 跳过该图，飞书发"图 N 失败"告警 |
| Step 3 | 全部图失败 | 飞书发 fallback 文本（"出图失败"）|
| Step 3 | 飞书 Markdown 介绍失败 | 跳过介绍，直接发图 |
| Step 3 | 飞书图片发送失败 | 跳过该图，整体**不**中断 |

## 时区与墨墨每日重置

- 墨墨 **凌晨 4:00** 重置今日任务（不是自然日 0:00）— 用户在 0:00-3:59 跑脚本时，`get_today_items` 拿的是**昨天**的 55 词
- `fetch_weak.py` 的 `maimemo_today()` 函数处理这个偏移（4:00 切日期）
- 飞书介绍消息里写的"今天 N 词"也用 `weak.json.date`，跟 API 语义一致

## 已知瑕疵（不修，知道就行）

- 助记图风格：模型自行选（实测：可爱叙事风居多，偶有写实）
- 字号：模型自行定（实测：12 词时偏大，24 词时偏小，但都清晰可读）
- 大小写：模型自行选拼写大小写（实测：part 1 大写、part 2 小写，不统一但不影响）
- 音标次重音位置：`counterbalance` 等长词可能不准（Mavis 知识兜底的固有限制）
- 知识兜底准确度：Mavis 训练知识对常见词准确率 95%+，但对低频/学术词可能有误差

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

- `memo-context`：基于"今日全 55 词"写文章（不同定位——语境派 vs 讲解派）
- `memo-suite` v1.1 数据分析：可看历史薄弱趋势（不参与本 skill）

## 踩过的坑（已写入 references）

- `get_today_items` 必须合并 `is_finished` 两次 — `references/maimemo-merge.md`
- `image_synthesize` 相对路径解析到 agent default workspace — 用绝对路径 — `references/prompt-template.md` 末尾
- `lark-cli im +messages-send` 默认 user 身份发不出 — 用 `--as bot` — `references/lark-send.md`
- `lark-cli --file` 绝对路径和 `..` 都被拒 — `cd <dir> && --file <basename>` — `references/lark-send.md`
- `lark-cli` markdown 双引号陷阱 — 反引号被 bash 吃 — 用单引号 — `references/lark-send.md`
- `lark-cli` 单条消息 5MB 上限 — PNG → JPEG 压缩 — `references/lark-send.md`
