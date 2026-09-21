# 已知坑（Anti-patterns）

这些是本次（音乐节 v1/v2）踩过的具体坑。**每条都附"怎么避免"**。

## ❌ 坑 1：8 张全部 2×2 格子

**症状**：8 页都是整齐的 2×2 网格，画面节奏单调，看 3 页就审美疲劳。

**原因**：AI 默认 2×2 是最稳妥的排版，省 prompt。

**怎么避免**：

- 在 prompt 里**显式指定** layout 变体（见 `style-vocabulary.md` 的 4 种 layout）
- 8 页至少用 3 种不同 layout
- 高潮页（P6）用 1 大 + 3 小；行动页（P2/P5）用横长 + 竖长

## ❌ 坑 2：caption box 漏画

**症状**：caption box 是叙事自包含的关键。但 P3（过场页）这种"画面简洁"的页最容易漏。

**原因**：AI 觉得"这页画面简单，可以不画 caption box"。

**怎么避免**：

- **每张 prompt 都显式加** "MANDATORY narrator caption box at the very bottom... DO NOT OMIT"
- 出图后**逐张肉眼检查** caption box 是否真的存在
- 漏了的页**单张重跑**，不要全量重跑
- 重跑时在 prompt 头部加 "CRITICAL: caption box is MANDATORY, do not omit"

**本次案例**：音乐节 v1 全部 8 张都没画 caption box（prompt 写得太轻），v2 加了强调但 P3 仍然漏，单张重跑加了 "CRITICAL" 才解决。

## ❌ 坑 3：风格 anchor 用封面页

**症状**：用 P1（封面，构图最简单）做 anchor → 风格样本看不出问题 → 批量出图后才发现格子节奏、人物、风格都不对。

**怎么避免**：

- **anchor 用高潮页 / 转折页**（音乐节是 P6 TB 出现）
- 这种页同时考验：人物、格子节奏、色彩、caption box、特殊符号
- 通过 anchor 才能暴露大多数风险

## ❌ 坑 4：批量出图再检查

**症状**：一次 batch 出 8 张 → 用户反馈"叙事断裂"或"风格不对" → 全量重做。

**怎么避免**：

- 严格按 5 步流程：anchor → 文案 → batch → 检查
- anchor 阶段不通过不进入 batch
- batch 出图后**先肉眼逐张检查 caption box** 再交给用户
- 单页问题单页修，不扩散

## ❌ 坑 5：中文乱码 / 错字

**症状**：caption box 里的中文变成"锟斤拷"、方块字、错别字。

**原因**：

- AI 模型对中文字符的渲染能力有限
- 长段落（> 50 字）尤其容易出问题
- 拟声词/对白里的中文也容易翻车

**怎么避免**：

- caption 控制在 30-60 字，**短而稳**
- prompt 加 "correct Chinese characters, no garbled text, no box characters"
- 出图后**逐字检查** caption 和对白
- 错字少 → 单字 PS 修；乱码多 → 整张重跑

## ❌ 坑 6：画真名乐队 / 明星

**症状**：用户说"画 TB" → AI 试图画 3 个具体人物 → 画走样、可能侵权。

**怎么避免**：

- 默认不画真人 / 真乐队 / 真明星
- 用符号代替：舞台 + 灯光 + 3 剪影 + 简化乐器
- prompt 显式加 "Do not draw real people / real band members; use silhouettes and symbols only"
- 唯一例外：用户明确授权 + 提供照片 reference + 接受画走样风险

## ❌ 坑 7：火柴人过度演化

**症状**：用户说"用我的火柴人做" → AI 画成完整漫画人物 → 风格不统一。

**原因**：AI 倾向往"完整人物"演化，因为这样更容易画表情。

**怎么避免**：

- prompt 显式说"simplified manga character, not full realistic"
- 接受"简化漫画人物"（圆头 + 简单身材 + 简单发型），不必死磕纯火柴人
- 给参考图（用户的火柴人 PNG）作为 input_file_path
- 在 anchor 阶段就锁定人物的简化程度

## ❌ 坑 8：caption 写成长段落

**症状**：caption 写 100+ 字、4-5 句话 → AI 渲染中文崩、画风被压。

**怎么避免**：

- 30-60 字、1-2 句（见 caption-box-spec.md）
- 长内容拆成多页，不要挤一页
- 8 页 caption 连起来是一段完整独白，但每页只讲自己的小节

## ❌ 坑 9：全彩 / 颜色饱和度过高

**症状**：manga 失去黑白感，全彩看起来像数字插画、不是漫画。

**怎么避免**：

- 默认 B&W + 局部彩
- 1-3 页上色（情绪峰值），不要每页都上
- 用 muted 色（apricot / dusty pink / cream），不要 digital 饱和色
- prompt 加 "watercolor wash, NOT saturated digital color"

## ❌ 坑 10：风格 anchor 通过后批量出图风格漂移

**症状**：anchor 看着对，但批量 8 张出来后风格变了。

**原因**：每张 prompt 独立写，base 风格段不一致。

**怎么避免**：

- 抽出一个 `BASE_STYLE_BLOCK` 字符串，8 张图共用
- 每张 prompt = BASE_STYLE_BLOCK + PAGE_SPECIFIC
- 出图后**对比 anchor 和批量图**，有偏差就改 BASE 重出

## ❌ 坑 11：用户没灵感时硬上 anchor

**症状**：用户说"想画个故事，但没想好" → 直接让用户选 anchor 页 → 用户卡住。

**怎么避免**：

- 在 Step 1 跑**动态 grill**（见 SKILL.md "决策池"），不要硬塞 6 问
- 在 Step 2 之前先帮用户**梳理故事节奏**（用 list 列出 8 页的简单剧情）
- 让用户**先确认页面剧情**再选 anchor
- anchor 是"高潮页"不是用户主观选的

## ❌ 坑 12：色彩页选错

**症状**：彩色页选在过场页或低潮页，浪费了上色机会。

**怎么避免**：

- 上色页选**情绪最高**的：圆梦、高潮、转折、治愈
- 通常是 P1（开篇定调）、P4（转折）、P6（高潮）、P8（圆梦）中的一个或多个
- 不超过 3 页上色

## ❌ 坑 13：publish-pack 跟图不对应

**症状**：正文里写"看 P3 暗恋那段" → 但 P3 是赶路不是暗恋 → 读者对不上。

**怎么避免**：

- 写正文时**打开图**逐张对
- 不说"第 X 页"（每张图不是序号，是节奏），用"开头 / 中段 / 结尾"或"暗恋那页 / 圆梦那页"
- 标签用情绪词不用"第 X 张"

## 总结：本次（音乐节）的 5 大教训

1. **anchor 必做**——v1 没做 anchor 就批量 → 风格重做
2. **caption box 必做**——v1 完全没画 → v2 重做 + P3 单跑
3. **5 步流程不能省**——v1 跳了 Step 1 grill 和 Step 3 文案
4. **简化人物 OK**——v2 允许火柴人 → 简化漫画人物的演化
5. **符号代替真人**——TB 不能画真人，画剪影 + 舞台
