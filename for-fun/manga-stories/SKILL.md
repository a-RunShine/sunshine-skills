---
name: manga-stories
description: |
  Generate a vertical (3:4) Japanese-manga style image set that turns a diary / 
  personal story / 暗恋 / 追星 / 治愈 / 圆梦 narrative into an 8-page self-contained
  manga for 小红书 / Instagram / 个人公众号. Triggers on "manga 版 / 分镜 / 
  日式漫画 / 连环画版 / 给我画一话 / 漫画分镜 / manga me this". Style is B&W line 
  with selective color on emotional peaks, simplified characters, narrator caption 
  box at the bottom of every page for self-contained reading.
---
# manga-stories

把一段私人叙事（日记 / 暗恋 / 追星 / 治愈 / 圆梦等）做成 8 页日式分镜漫画，
3:4 竖版，黑白为主 + 关键页局部彩色，**每页独立可读**（底部 narrator 旁白框）。

## ✅ 本 skill 已被实测

**Case 1：音乐节 v1 → v2**（2026-08-05）

- 输入：用户日记《5.5 音乐节·我见到了 TB》
- v1：跳了 anchor / 没画 caption box → 失败（"叙事断裂"）
- v2：完整走 5 步流程 → 成功 8 张
- 详见 `examples/case-study-brief.md` + `examples/` 下 9 张图

**对本 skill 的反馈**：

- caption box 是核心设计，不能省
- anchor 用高潮页（P6）能一次暴露大部分风险
- 简化人物（火柴人 → 简化漫画人物）的演化是允许的
- 真人/真乐队必须用符号代替（剪影 + 舞台）

## 何时调用

用户说类似下面这些：

- "把这个故事画成 manga 版"
- "给我做个分镜 / 漫画分镜"
- "日式漫画 / 连环画版"
- "manga me this / 给我画一话"
- "用《孤独摇滚》/ 浅野いにお那种风格画"
- "用我的日记做一集漫画"

## 何时不调用

- 想要水彩 / 暖色手绘 / 绘本 / 插画 → 走 `xiaohongshu-image-batch` 的 warm 版或其他画风 skill
- 想要动画 / 视频分镜（含时间轴、配音）→ 走 `canvas-design` 或视频脚本 skill
- 想要 GIF / 表情包 / 单张大图 → 不属于本 skill 范围

## 核心交付

- **8 张 3:4 竖版图**（1 封面 + 7 内容；如故事确实讲不完可扩到 10–12 张，**不要硬塞**）
- **每页底部 narrator 旁白框**：黑色边框 + 浅奶白底 + 手写感中文，1/8 页面高度
- **黑白为主 + 关键页局部彩色**（建议 1-3 页：情绪最高潮的转折 / 圆梦 / 治愈）
- 简化人物（演化自火柴人 OK，不必强求纯火柴人）
- 4-6 格子自由编排（不要千篇一律 2×2）
- 中文对白 / 拟声词（粗体黑手写体）
- 附带 `publish-pack.md` 发布文案包

## 5 步流程

### Step 1 · 动态对齐（先听后问）

**不要预设 6 问清单**。先看用户给了什么，再决定要问什么。

#### 工作方式

1. **通读用户的故事 / 日记**——先自己心里过一遍情绪曲线
2. **看用户自己说了什么**——已经说过的就不问，已经默认的就不问
3. **列出"我还不知道的关键决策"**——这些才需要问
4. **用 `ask_user` 一次一问**——不要 6 连问轰炸（方法见 `references/grill-method.md`）

#### 决策池（按需取用，不是必答）

下面是**可问的所有问题**，但**不是都要问**。根据故事选 1-5 个问：

```
[范围]    你想画整篇 / 还是挑一段 / 还是只画高潮？
[张数]    想要几页？(默认 8，看故事长度加减)
[风格]    写实漫画 / 简化 / 极简 / 复古 / 萌系？(给参考样图更直观)
[参考]    有没有喜欢的 manga / 漫画家风格可以参考？
[真实人物] 故事里有真人/真乐队吗？→ 决定要不要问授权
[人物设定] 你 / 故事里的人 怎么画？火柴人？简化漫画？有参考图吗？
[情绪锚点] 这故事里情绪最复杂 / 最想画好的是哪一页？(影响 anchor)
[系列]    是单期还是系列第一期？
[标签]    想要什么主题标签？(追星 / 暗恋 / 治愈 / 圆梦 / 友情 / 校园)
[画面张力] 想要单页节奏慢一点（看仔细）还是快一点（信息量大）？
[彩色页] 哪几页想上色？(默认 1-3 页选情绪最高潮)
[发布平台] 准备发小红书 / 公众号 / IG？影响 caption 长度
```

#### 必问的最小集

**不管什么故事，2 个问题必问**：

1. **风格细化**（如果用户没给风格线索）
2. **anchor 页是哪张 / 故事里哪一帧最重要**

其他都看情况。

#### 完成标准

- 用户回答完所有**当时需要的**问题
- 你心里能讲出"这个故事的 8 页大概是什么"
- 生成 `brief.md` 把决策落档（**只落实际决策**，不要 6 问都填表）

### Step 2 · 风格 anchor 样本

只画 1 张图（anchor 页），等待用户确认或改方向。

- 用 `image_synthesize`，aspect_ratio=`3:4`，reference image 可选（用户的火柴人 / 自画像）
- prompt 模板见 `references/prompt-template.md`
- **caption box 在 anchor 这一张就要画上**——它不是事后贴的，是图的组成部分

**完成标准**：用户回复"OK / 风格对了 / 可以继续"，才进入 Step 3。
若用户说"再换种感觉"或"调整 XX"，改 prompt 重跑 anchor，不要进入批量阶段。

### Step 3 · 文案 + Caption 设计

8 页每页都要在动笔前定好：

1. **画面剧情**（1-2 句话）——格子怎么排，这格画什么
2. **底部 narrator 旁白**（1-2 句话，约 30-60 字）——独立可读的关键
3. **格子内对白 / 拟声词**（可选）——补充情绪

文案设计原则见 `references/caption-box-spec.md`。

**完成标准**：8 页（或 N 页）的 `(画面, 旁白, 对白)` 三元组都写完。

### Step 4 · 批量出图（每张都要 caption box）

- 每张图独立 prompt，但**共享 base 风格描述**（见 `references/prompt-template.md`）
- **每张 prompt 必须显式包含 "narrator caption box at the very bottom, black border, light cream bg, handwritten Chinese text"**
- 一次 batch 出 8 张，节省时间
- 出图后**逐张肉眼检查 caption box 是否真的画出来**——P3、P5 这种"过场"页最容易漏
- 见 `references/anti-patterns.md` 已知坑

**完成标准**：8 张图都画上 caption box。漏了的单张重跑（不要全量重跑）。

### Step 5 · 叙事自检 + 交付

用 `references/checklist.md` 逐页过：

- 每页独立打开看，旁白框 + 画面是否讲清一个独立小节？
- 中文渲染正确（无乱码、无错字）？
- 4-6 格子节奏感（不要全是大格或全是大格）？
- 关键页确实上了颜色（1-3 页）？
- 是否有不能 / 不该画的具体人物（真名乐队、明星）？用符号替代

写 `publish-pack.md`：标题 / 正文 / 标签 / 备注，参考 `xiaohongshu-image-batch` 的输出格式。

**完成标准**：publish-pack.md 落档 + 8 张图全部可独立阅读 + 用 `<media>` 标签把图发给用户。

## 关键原则（每次都要遵守）

1. **Anchor 必做**。永远先出 1 张风格样本。批量重做的代价远高于 anchor 慢一步。
2. **Caption box 必做**。每页都要。没有 caption box 的 manga 一定"叙事断裂"——这是本次踩过最大的坑。
3. **真人 / 乐队用符号**。不画真名乐队成员（除非用户明确授权），用舞台 + 灯光 + 剪影 + 简化吉他/鼓符号。
4. **简化人物 OK**。火柴人 → 简化漫画人物的演化是允许的，不必死磕纯火柴人。
5. **中文要写对**。prompt 里强调"correct Chinese characters, no garbled text"，出图后肉眼检查每个字。
6. **4-6 格子自由编排**。不要每页 2×2。可以用 1 大格 + 3 小格、横长格、跨页格等。
7. **彩色克制**。黑白为主，1-3 页局部彩色（情绪峰值 / 转折 / 圆梦），不要全彩。
8. **AI 自动加的细节是好是坏要看**。它会自己加墨镜、皱纹、拟声词——保留有意义的，删掉跑题的。

## 文件结构（建议）

```
项目根/
├── brief.md                    # 动态对齐后的实际决策（不是填表 6 问）
├── manga/
│   ├── anchor-样本.png         # Step 2 的风格样本
│   ├── 图1-封面-manga.png
│   ├── ...
│   ├── 图8-...-manga.png
│   └── publish-pack-manga.md   # Step 5 的发布文案包
└── 原始日记.md                  # 用户提供
```

## 与其他 skill 的边界


| Skill                     | 何时用                                                                                                                              |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `xiaohongshu-image-batch` | 暖色手绘 / 治愈系 / 非 manga 风格                                                                                                   |
| `canvas-design`           | 海报、视觉设计、PDF 排版                                                                                                            |
| `grilling`                | **不调用**。本 skill 内置 grill 方法（见 `references/grill-method.md`）。外部 grilling 适合对完整方案做 11 问 stress test，目标不同 |
| `writing-great-skills`    | 本 skill 自身的写法参考                                                                                                             |

## 已知坑（详见 references/anti-patterns.md）

- ❌ 出图时省 caption box → 必叙事断裂
- ❌ 8 页一次 batch 出完再检查 → 漏了重做代价大
- ❌ 风格 anchor 用封面页（封面最简单，看不出风险）→ 应该用高潮页 anchor
- ❌ 全部 2×2 格子 → 节奏单调
- ❌ 中文对白/旁白不检查 → 容易出乱码
- ❌ 画真名乐队 / 明星 → 用符号代替
