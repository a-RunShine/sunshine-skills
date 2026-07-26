---
name: xiaohongshu-image-batch
description: 从原始素材或主题，批量制作小红书图文内容（3:4 竖版，6-8 张为一组）。内置 /grilling 对齐（一次一问 + 给推荐 + project brief）、锚图定风格、批量出图、审稿抓 bug、配套正文 5 步标准流程。适用：算法题解（含代码）、生活随笔、读书笔记、产品评测、技术科普等任何主题的图文合集。触发关键词：「生成小红书图文」、「出 5 张图」、「按这个风格批量出图」、「我有个素材想做小红书」。
---

# xiaohongshu-image-batch

把"原始素材 → 小红书图文合集"做成可复用工作流。核心 4 步：

1. **/grilling 对齐**（一次一问 + 给推荐）→ 生成 **project brief**（唯一文档）
2. **锚图定风格**（从已确认的一张图提取 5 项规范）
3. **批量出图**（`image_synthesize` 一次多张）
4. **审稿 + 配套正文**（代码/风格/文字 + 标题/tag/评论钩子）

## 工作流

### Step 1：/grilling 对齐

按 `/grilling` 原则跑，**一次问一个问题 + 每次给推荐答案**。
问题清单见 `references/grill-me-checklist.md`。

grill 完的决策落地到 **project brief**（项目综合概览），模板见 `references/project-brief-template.md`。

**禁止行为**：
- ❌ 一次问多个问题（违反 `/grilling`："Asking multiple questions at once is bewildering"）
- ❌ 不给推荐答案（违反 `/grilling`："For each question, provide your recommended answer"）
- ❌ 用户没确认前出图（违反 `/grilling`："Do not act on it until I confirm"）

### Step 2：锚图定风格

让用户选一张**锚图**作为风格基线（可以是他给的素材图，也可以 AI 生成 1-2 张"风格样本"让他选）。

从锚图提取 5 项规范：
1. 画布底色（hex）
2. 主描边色（hex）
3. 主高亮色（hex）
4. 标题字体感觉（圆润/手写/粗体/宋体）
5. 代码块风格（如有代码：黑底 + macOS + VS Code 配色）

详细风格词典见 `references/style-cookbook.md`。

### Step 3：批量出图

- 工具：`image_synthesize`，一次最多 10 张
- 推荐规模：**1 主图 + 5-7 细节 = 6-8 张一组**
- prompt 必带：①风格规范 ②完整内容（如含代码必须逐字贴） ③"按字生成"约束
- 详细页型骨架见 `references/page-templates.md`
- 内容结构见 `references/content-structures.md`

⚠️ **封面单独设计**：封面是首图，决定点开率。封面要更夸张/更抓人，但底色和字体感觉必须和后续内容页统一。

### Step 4：审稿 + 配套正文

**审稿**每张图必查清单：
1. 文字是否清晰可读（不被裁切、字号合适）
2. 代码（如有）是否拼写正确——**Gemini 渲染 Java 代码经常乱码**
3. 风格是否与锚图一致（颜色/字体/装饰）
4. emoji 是否在合适位置
5. 内容是否传达清楚（小白能不能看懂）

常见 7 类 bug 修复方法见 `references/error-playbook.md`。

⚠️ **必查代码错乱**：如果带代码，每次出图后用 read 工具把代码块放大看，发现乱码立即重做（重做时给完整代码 + "逐字生成"约束）。

**配套正文**直接给用户：
- 标题（带钩子 / 系列号 / 数字反差）
- 正文（开头钩子 3-5 行 + 核心 5-10 行 + 收尾金句）
- tag 5-10 个
- 评论区置顶（引导评论/收藏）
- 发布顺序（按图编号）
- 发布时间建议

## project brief

唯一文档。grill 完所有决策的汇总：

```
xiaohongshu/<主题>/brief.md
```

包含：
- 元信息（主题、系列号、平台、图数、状态）
- 受众 / 角度 / 调性 / 风格基线
- 玩梗路线 / 出图形式
- 内容结构（图清单）
- 配套规范（标题 / 正文 / tag / 评论钩子 / 发布时间）
- 关键风险点
- Grill 对齐记录
- 出图 checklist

执行层（出图）直接照 brief 走。

## 工具调用规范

| 工具 | 用途 | 时机 |
|------|------|------|
| `ask_user` | grill 一次一问 | Step 1 |
| `image_synthesize` | 批量出图 | Step 3、Step 4 重做 |
| `read` | 审稿时放大看代码 | Step 4 |
| `bash` (mkdir) | 建输出目录 | Step 3 前 |
| `mavis cron` | 长任务监控 | 可选 |

## 输出规范

- 图片目录：`xiaohongshu/<主题>/图N-<页型>.png`
- 图片格式：3:4 竖版，2K 分辨率
- 命名按发布顺序，方便用户检查
- brief 放在项目目录：`xiaohongshu/<主题>/brief.md`

## 关键经验（踩过的坑）

1. **/grilling 原则：一次一问 + 给推荐** —— 之前我一次甩 4 个问题让用户"bewildering"，是错的
2. **Gemini 渲染代码经常乱码** —— 必须在 prompt 里给完整代码 + 强调"按字生成"
3. **第一次出图后必须 review 抓 bug** —— 不要直接交付
4. **风格定调要靠一张锚图对齐**，不是空想
5. **封面是单独决策点**，不要混在内容页里
6. **grilling 不可跳过** —— 用户给的细节越少，跑偏越严重
7. **代码块在暖色画布里"黑底+macOS 红绿灯"是合规的视觉混搭**，不需要整个图都是暖色
8. **brief 是唯一落地文档**——ADR / glossary 对小红书图文太重，砍掉

## 限制

- **不适合**长图（1 张 1 万字 + 复杂排版）
- **不适合**实时数据内容（榜单、新闻）
- **中文文字渲染有缺陷**——必要时先用 HTML/Pillow 渲染再合成
- **Gemini 的 Java 关键字拼写**——必须 prompt 给完整代码

## 完整示例

参考对话记录：`234.回文链表(Stack & Deque)` 主题，输出目录 `xiaohongshu/234_回文链表/`。
那次 7 张图的关键节点：
1. /grilling 4 维度对齐（刚入门算法 / 方法1+3 / 反差玩梗 / 暖色手绘）—— **一次一问 + 给推荐**
2. **生成 project brief**（grill 结果落地为唯一文档）
3. 用原图 2 作为锚图定风格
4. 第一次出图 → 发现代码乱码 → 给完整代码重做
5. 封面单独设计（"带你刷力扣 #234"系列号 + 50 行 vs 5 行对比）
6. 配套正文 + 7 张图打包

## 完整流程速记

```
1. /grilling (ask_user 一次一问 + 给推荐)
   ↓
2. 生成 project brief（用户确认）
   ↓
3. 选锚图 → 提取 5 项风格规范
   ↓
4. 批量出图 (image_synthesize, prompt 开头必带风格规范)
   ↓
5. 审稿 (检查代码 / 风格 / 文字) + 配套正文
```
