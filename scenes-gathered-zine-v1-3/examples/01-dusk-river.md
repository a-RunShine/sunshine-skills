# Example 1 · 黄昏江景（Dusk River）

**Skill 主类**：`scenes-gathered-zine-v1-3`
**适用场景**：地平线主导 + 远处建筑/桥 + 落日 + 放射状云层 + 水面反光

---

## 1. 来源

- 照片类型：江边日落（永乐江景）
- 主体：高层住宅楼（左侧）、跨江桥（右侧）、低悬落日（右上）、远山、水面放射反光
- 情绪：黄昏、独处、安静、收工回家的片刻

## 2. Scene Card（场景识别卡）

| 字段 | 内容 |
|---|---|
| Core subjects | 高层公寓楼剪影、跨江桥、低悬落日 |
| Supporting elements | 远山轮廓、江面、放射状云层、左侧风车（**Omit**） |
| Spatial invariants | 建筑偏左、桥水平横穿右段、太阳在右上、山在天际、水占下半 |
| Dominant gesture | 水平地平线 + 太阳放射光束 |
| Visual-weight map | 建筑中重（深色块）、太阳为高亮焦点、水面反光为次焦点 |
| Native color atmosphere | 暖金黄主导，灰白过渡，蓝色仅在天顶远云 |
| Source-shape candidates | 水平地平线、放射云、桥的水平线、太阳圆盘 |
| Natural quiet areas | 天空上半、水面下半、天顶远云 |
| Semantic minimum | 江边 + 桥 + 落日 + 放射云 = 识别此场景的最小组合 |

## 3. 设计决策

| 决策项 | 选择 | 理由 |
|---|---|---|
| Layout | Transformative seam（地平线撕纸） | 地平线天然是水平撕裂线 |
| Photo / illustration shares | 摄影 ~35%，插画场 ~55%，留白 ~10% | 上方留给放射光场与 underprint |
| Primary grammar | **Field-led**（天空放射场） | 放射云是源形状最有力的延续 |
| Supporting grammar | Silhouette-led（建筑剪影） | 给画面一个深色锚点 |
| Chromatic hue | **Saturated cobalt blue** | 温度桥：与暖金形成冷暖对话 |
| Integration mode | **Underprint passage** | 蓝从太阳下方的云带向上延伸入插画场 |
| Color area | ~8-10% | 半色调 underprint，承担结构而非装饰 |
| Torn edge 位置 | 地平线（建筑底部/远岸到水面） | 35-50% 可见周长 |
| Micro-text | "Stillness"（独立词，英文） | 独立场景词，对应"静默"的情绪 |
| 字体 | 打字机衬线，小写，暖炭色 | 与纸面融为一体 |

## 4. Abstraction Map

| 操作 | 内容 |
|---|---|
| **Retain** | 建筑剪影、太阳位置、桥水平线、远山轮廓 |
| **Merge** | 放射云合并为单一放射手势；建筑 + 任何近景植被合并为单一深色剪影块 |
| **Omit** | 风车、远处建筑群、单体窗户、桥墩细节、叶子/水波细节 |
| **Transform** | 密集云层纹理 → 4-6 条稀疏半色调放射光束；建筑 → 一块深色剪影带 3-5 个破窗缺口 |
| **Expose** | 天空上方大片留白；水面下半留白；微文本周围的安静纸面 |

## 5. 提示词骨架（按 SKILL.md "Prompt Shape" 四段式填入）

```
Paragraph 1 — Canvas and attention geometry:
Vertical 3:5 paper poster, flat scan, warm cream aged paper with matte fibers, soft scan noise.
Photograph torn-paper anchor in lower 35%; abstract illustration field fills upper 55% as quiet cream sky.
Eye path: torn horizon edge → setting sun + radiating beams → cobalt blue underprint → quiet paper exit at top.
Reserved text area: lower-right quiet water pocket.

Paragraph 2 — Scene fidelity:
Preserve a high-rise apartment building silhouette at left-of-center, horizontal bridge across mid-right horizon,
setting sun at upper-right, low mountain ridge far, wide river below with strong sun reflection.
Photography is warm gold, recognizable as a dusk river scene.

Paragraph 3 — Illustration, chromatic, torn edge, micro-text:
[Fill from SKILL.md "Photo-Specific Prompt Compiler" fields 7-11]

Paragraph 4 — Reproduction mood and constraints:
[Fill from "Hard Avoids" + paper/scan/mood fields]
```

## 6. 实际产出参考

- 源图：用户提供的「永乐江景.jpg」
- 生成图：`gathered_scenes_yongle_river.png`（9:16 ≈ 3:5，钴蓝 underprint + 建筑剪影 + Stillness 文本）
- 验证：撕纸边缘可读、放射光束成型、建筑剪影正确、留白充分、色相承担结构角色

## 7. 失败教训（避免重复踩坑）

- `aspect_ratio=3:5` 在当前后端不兼容，会导致整次生成失败
- 解决：用 `aspect_ratio=9:16`（≈3:5）替代
- 长 prompt + reference image + 3:5 + 2K 组合会触发失败，必要时去掉 `resolution` 参数
