# Example 2 · 雨夜独行（Rainy Night Walker）

**Skill 主类**：`scenes-gathered-zine-v1-3`
**适用场景**：单个人物 / 强剪影主体 + 街道延伸 + 雨夜人工光

> 与 Example 1 对比：主导语法从 **Field-led** 切到 **Silhouette-led**，色相从冷蓝（温度桥）切到暖品红（语义强调），撕纸边界从水平地平线切到人物轮廓。

---

## 1. 来源

- 照片类型：雨夜街灯下独行者
- 主体：打伞或披外套的人（中央或偏中）、街灯拉长的光斑、湿漉漉的街面
- 情绪：孤独、收工、雨声、城市夜晚的安静

## 2. Scene Card

| 字段 | 内容 |
|---|---|
| Core subjects | 独行者剪影（中央）、街灯光晕（背景） |
| Supporting elements | 湿街反光、远处建筑立面、雨丝（**Omit**） |
| Spatial invariants | 人居中或略偏左、灯在背后或侧上方、街道从画面中心向画面深处延伸 |
| Dominant gesture | 垂直（人物站立）+ 街面消失点 |
| Visual-weight map | 人物剪影为主焦点（深色高密度），灯光为次焦点（高亮高彩） |
| Native color atmosphere | 暖橙（钠灯）+ 冷青（雨夜）+ 黑色（人物） |
| Source-shape candidates | 人物垂直剪影、灯光光锥、湿街反光带 |
| Natural quiet areas | 天空中部、人物脚下、街道边缘 |
| Semantic minimum | 街灯 + 一个人 + 雨夜 = 识别此场景的最小组合 |

## 3. 设计决策

| 决策项 | 选择 | 理由 |
|---|---|---|
| Layout | Directional split（按人物与街道的视线 / 消失点方向） | 强化"独行"的方向感 |
| Photo / illustration shares | 摄影 ~40%，插画场 ~45%，留白 ~15% | 人物需要较大照片占比以保识别度 |
| Primary grammar | **Silhouette-led**（人物剪影） | 人物是此场景最强的源形状 |
| Supporting grammar | Field-led（街灯光场） | 灯的辐射光给画面一个柔和包围 |
| Chromatic hue | **Saturated magenta-pink / 番茄红** | 源 resonance：街灯本身的暖色被强化 |
| Integration mode | **Source continuation**（光锥从人物头部延伸向上） | 色相与人物的连接形成"孤独被照亮"语义 |
| Color area | ~5-7% | opaque replacement + underprint 混合 |
| Torn edge 位置 | 沿人物剪影轮廓的左/右侧 + 头顶 + 脚下小块 | 让照片边缘"贴着人"撕开，最具触觉感 |
| Micro-text | "Solitude"（独立词，英文）或 "Rain · Lamp · Solitude"（关键词序列） | 关键词序列适合多元素场景 |
| 字体 | 打字机衬线，小写，暖炭色 | 与纸面融为一体 |

## 4. Abstraction Map

| 操作 | 内容 |
|---|---|
| **Retain** | 人物剪影轮廓、站姿、伞或外套的形状特征；街灯位置；街道延伸方向 |
| **Merge** | 雨丝全部省略（避免 lace 感）；多光源合并为一个主导光锥 |
| **Omit** | 雨丝、远处建筑窗户、招牌文字、行人、车辆、电线杆 |
| **Transform** | 街灯 → 一片不规则光晕（halftone 渐变）；湿街 → 几条稀疏的横线表示反光带；天空 → 一片均匀的深色 ink field |
| **Expose** | 人物脚下留白、街道远处留白、文本附近的纸面留白 |

## 5. 提示词骨架

```
Paragraph 1 — Canvas and attention geometry:
Vertical 3:5 paper poster, flat scan, warm cream aged paper with matte fibers, soft scan noise.
Photograph torn-paper anchor in lower 40% (subject's feet visible); illustration field extends upward as a
dark field-led sky with a single light source. Eye path: light source → figure silhouette → magenta light
cone above head → quiet paper at top corners. Reserved text area: lower-left or lower-right quiet corner.

Paragraph 2 — Scene fidelity:
Preserve a single standing figure silhouette at center (umbrella or coat), a street lamp glow behind or
side-above, wet street with subtle reflection bands. Photography is dark and warm, recognizable as a rainy
night urban scene.

Paragraph 3 — Illustration, chromatic, torn edge, micro-text:
Primary: silhouette-led — one large dark mass carries the figure, broken contour only at the shoulders
and hem. Supporting: field-led — a soft halftone field around the lamp implies atmosphere.
Retain: figure silhouette, lamp position, street direction. Merge: rain into silence. Omit: rain streaks,
windows, signs, people, vehicles, wires. Transform: lamp into one halftone glow, wet street into 2-3
sparse horizontal lines.
Chromatic: saturated magenta-pink (or tomato red) as source continuation — a translucent light cone
rising from the lamp through and beyond the figure's head, halftone misregistered, ~55% opacity, ~5-7%
poster area. Function: semantic emphasis + photo-illustration bridge.
Torn edge: along the figure's left and right contour and across the top of the head, irregular fibrous
fringe, ~35-50% of photo perimeter.
Micro-text: "Solitude" or "Rain · Lamp · Solitude" in small vintage typewriter serif, lowercase, warm-
charcoal ink, placed in a lower quiet corner, baseline parallel to street horizon, ~1.5% poster height.

Paragraph 4 — Reproduction mood and constraints:
[Fill from "Hard Avoids" + paper/scan/mood fields]
```

## 6. 与 Example 1 的差异对照

| 维度 | Example 1（黄昏江景） | Example 2（雨夜独行） |
|---|---|---|
| 主导语法 | Field-led | Silhouette-led |
| 辅助语法 | Silhouette-led | Field-led |
| 色相 | Cobalt blue（温度桥） | Magenta-pink（语义强调） |
| 集成模式 | Underprint passage | Source continuation（光锥） |
| 撕纸边界 | 水平地平线 | 沿人物轮廓 |
| 源形状 | 放射云 + 地平线 | 人物剪影 + 光锥 |
| 留白重点 | 天空上半 | 人物脚下 + 街道远端 |
| 微文本形式 | Standalone word | Standalone word 或 keyword sequence |

## 7. 适用 / 不适用

**适用**
- 单人 / 强剪影主体
- 雨夜、雾天、深夜等低光场景
- 街道、桥、走廊、隧道等有消失点 / 方向的场景
- 想强调孤独、距离、等待等情绪

**不适用**
- 多人场景（剪影过密会变 lace）
- 城市天际线（交给 Example 1 的 Field-led 更合适）
- 纯人像特写（场景太"贴脸"会失去纸刊距离感）
