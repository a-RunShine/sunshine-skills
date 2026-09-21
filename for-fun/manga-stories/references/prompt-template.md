# Manga Prompt 模板

## 通用 base 段（每张图共享，复制粘贴）

```
Single manga page, vertical 3:4 aspect ratio, black-and-white Japanese manga 
illustration with selective color accents.

[STYLE BLOCK - see below]

[PANEL LAYOUT - varies per page]

[PAGE-SPECIFIC CONTENT - varies per page]

MANDATORY NARRATOR CAPTION BOX at the very bottom of the page:
- Black rectangular border, 2-3px stroke
- Light cream/off-white background (#F5F0E6 or similar)
- Handwritten Chinese text inside, ~1/8 of page height
- Text is the page's narrator caption (not dialog)
- Caption must be readable and grammatically correct Chinese
- DO NOT OMIT the caption box on any page
```

## 风格块（STYLE BLOCK）

### 简化漫画风格（推荐默认）

```
Style references: 浅野いにお《SOLANIN》mood, ARAKI Yohihi line quality,
孤独摇滚 (BOCCHI THE ROCK) youth-rock energy.

Line: clean black ink lines, variable weight, hand-drawn feel.
Characters: simplified, slightly stylized — round heads, simple facial
features (dot eyes, curved mouth). Acceptable evolution from stick figures
into simplified manga characters (slight body, simple clothes, hair as
black silhouette or color block). DO NOT make them photorealistic or
overly detailed.
Panels: 4-6 panels in free layout (not strict 2x2). Mix large establishing
panels, medium action panels, and small detail panels. Panels have clean
black borders.
Tone: screentone shading (halftone dots) for shadows and atmosphere,
speed lines for movement, hatching for darkness.
Speech bubbles: sharp rectangular corners (not rounded), thin black border.
Onomatopoeia: bold black hand-drawn Japanese-style sound effects (e.g.
"ドンドン" "グルグル" "シーン" "ドキドキ"). Chinese onomatopoeia OK too
("咚" "哐当" "心跳").
Selective color: 1-3 pages use color on key emotional moments
(meeting the idol, healing, dream coming true). Color palette: muted 
apricot #E8B57E, dusty pink #E5B5B5, soft blue-gray #B8C5D6. Color should
feel like watercolor wash, NOT saturated digital color.
Background: minimal — focus on character expression and mood, not scenery.
```

### 写实漫画风格（不推荐默认，太重）

```
Style references: 井上雄彦《SLAM DUNK》, 浦沢直樹《MONSTER》.
Realistic manga, detailed cross-hatching, dramatic shadows.
Only use if user explicitly asks.
```

### 极简/儿童漫画风格（备选）

```
Style references: 矢口高雄《钓鬼》simple, やなせたかし《アンパンマン》.
Very simple line work, large empty areas, childlike.
Use for: 童话 / 极简叙事 / 萌系治愈.
```

## 每页 prompt 模板（page-specific）

```
PAGE N: [页面小标题]

Panel layout: 
- Panel 1 (top, full width): [画面描述] e.g. "wide establishing shot of
  a music festival at dusk, distant stage lights glowing"
- Panel 2 (middle-left, 60% width): [画面描述]
- Panel 3 (middle-right, 40% width): [画面描述]
- Panel 4 (bottom-left, half): [画面描述]
- Panel 5 (bottom-right, half): [画面描述]

Main subject: [主角在做什么, 表情, 姿态].
Other elements: [对白 / 拟声词 / 关键细节].
Color: [B&W / selective color on which element]
Caption text: "[完整旁白原文，1-2 句，30-60 字]"

CRITICAL: 
- Caption box at the very bottom is MANDATORY, do not omit
- All Chinese text must render correctly (no garbled characters)
- Do not draw real people / real bands; use symbols (stage, light, silhouettes)
```

## 示例：音乐节 P6（TB 出现）

```
PAGE 6: TB appears

Style references: 浅野いにお《SOLANIN》mood, 孤独摇滚 youth-rock energy.
Single manga page, vertical 3:4, B&W Japanese manga with selective color
(soft apricot and dusty pink wash on stage lights only).

Panel layout:
- Panel 1 (top, full width): the festival stage, three musician silhouettes
  backlit by apricot stage lights. Simplified guitar and drum kit outlines.
  No facial features on musicians (silhouettes only).
- Panel 2 (middle, 60% width): the main character (round head, dot eyes,
  small smile) standing in the crowd, looking up at the stage. Hands slightly
  raised. Selective color on character's face (dusty pink flush) and stage
  (apricot).
- Panel 3 (middle, 40% width): close-up of main character's face, eyes
  glistening, mouth slightly open in awe. Selective color on tears/eyes.
- Panel 4 (bottom, full width): the crowd's hands raised, sea of silhouettes
  facing the glowing stage. Selective color on stage lights and a few
  scattered phone screens (apricot).

Main subject: a young person in the crowd seeing their idol band for the
first time — awe, disbelief, joy.
Other elements: small speech bubble near character with "..." (speechless).
Onomatopoeia: bold "胸がドキドキ" or "心跳" near chest.
Color: apricot and dusty pink wash on stage, character face, and a few
phone screens. Everything else B&W.
Caption text: "他们出现了。20 分钟、3 首歌。我意识到，我爱的、我想到的，
都可以是真的。"

CRITICAL:
- Caption box at the very bottom is MANDATORY
- All Chinese text must render correctly (no garbled characters)
- Do not draw real people / real band members; use silhouettes and symbols only
```

## 出图参数

```python
image_synthesize(
    requests=[{
        "prompt": "<完整 prompt 字符串>",
        "output_file_path": "manga/图N-标题-manga.png",
        "input_file_paths": ["<用户的火柴人/角色参考>"],  # 可选
        "aspect_ratio": "3:4",
        "resolution": "2K"  # 或 "1K" 看效果
    }]
)
```

## 出图后的肉眼检查清单

每张出图后立刻看：

- [ ] 底部真的有 caption box 吗？（**最常漏**）
- [ ] 中文渲染正确吗？无乱码？
- [ ] 4-6 格子有没有？节奏不单调？
- [ ] 关键页上色了吗？
- [ ] 风格跨页一致吗？（和 anchor 比对）
- [ ] 主角形象在 8 页里统一吗？

漏 caption box → 单张重跑，不要全量重跑。
