# prompt-template: dense-prompt 结构化模板

## cards-clean.json schema

```json
[
  {
    "voc_id": "abc123",
    "spelling": "clinic",
    "phonetic": "/ˈklɪnɪk/",
    "pos": "n.",
    "meaning_zh": "诊所；门诊部",
    "example_en_clean": "She went to the clinic for a check-up.",
    "mnemonic_visual": "a small white clinic with a red cross sign",
    "fallback": false
  },
  ...
]
```

字段语义：
- `spelling`：从 `get_today_items` 拿
- `phonetic / pos / meaning_zh / example_en_clean / mnemonic_visual`：
  - 若 `fallback=false`：从墨墨 `interpretations + phrases` 拼
  - 若 `fallback=true`：用 Mavis 训练知识填
- `fallback`：标是否用知识兜底（仅用于统计，不影响出图）

## dense-prompt 模板

直接复制下面这段，替换 `{{...}}` 变量：

```
A flat illustrated vocabulary poster, 16:9 landscape, 2K resolution.

GRID LAYOUT: exactly 3 rows × 4 columns = 12 cells, in the same order as WORDS list below.
Each cell occupies the same area, with a thin rounded border separating cells.

STYLE:
- cute narrative illustration style (NOT realistic, NOT pixel art, NOT minimalist)
- warm pastel background (cream / light yellow / soft beige)
- Source Han Sans / Noto Sans CJK font for all text
- generous white space inside each cell
- high readability, soft shadows

EACH CELL (top to bottom, in this exact order):
1. MNEMONIC IMAGE (top ~40% of cell): a small cute illustration that visualizes the mnemonic_visual hint
2. SPELLING (large bold black text) + phonetic + POS on same line, e.g. "clinic /ˈklɪnɪk/ n."
3. MEANING_ZH (medium black text, Chinese)
4. EXAMPLE SENTENCE (small black text, complete English sentence, **the target word is BOLD**)

WORDS (12 entries, in grid order: row 1 left-to-right, then row 2, then row 3):

1. {{spelling_1}} — {{phonetic_1}} {{pos_1}} — {{meaning_zh_1}} — {{example_en_1}} — Mnemonic hint: {{mnemonic_visual_1}}
2. {{spelling_2}} — ...
3. {{spelling_3}} — ...
4. {{spelling_4}} — ...
5. {{spelling_5}} — ...
6. {{spelling_6}} — ...
7. {{spelling_7}} — ...
8. {{spelling_8}} — ...
9. {{spelling_9}} — ...
10. {{spelling_10}} — ...
11. {{spelling_11}} — ...
12. {{spelling_12}} — ...

CRITICAL CONSTRAINTS:
- ONLY bold the target word inside example sentences, do NOT bold anything else
- Each cell must contain ALL 5 elements above, no missing
- 12 cells in a strict 3×4 grid, no overlap
- Do NOT add any extra text, watermark, page number, or label outside the cells
- Do NOT add a title bar or header
```

## 变量替换代码（write_prompts.py 实现）

```python
def fill_template(cards: list[dict], template: str) -> str:
    out = template
    for i, c in enumerate(cards, 1):
        out = out.replace(f"{{{{spelling_{i}}}}}", c["spelling"])
        out = out.replace(f"{{{{phonetic_{i}}}}}", c["phonetic"])
        out = out.replace(f"{{{{pos_{i}}}}}", c["pos"])
        out = out.replace(f"{{{{meaning_zh_{i}}}}}", c["meaning_zh"])
        out = out.replace(f"{{{{example_en_{i}}}}}", c["example_en_clean"])
        out = out.replace(f"{{{{mnemonic_visual_{i}}}}}", c["mnemonic_visual"])
    return out

# 写多张图 prompt
def write_prompts(cards: list[dict], out_dir: str, template: str):
    chunks = [cards[i:i+12] for i in range(0, len(cards), 12)]
    for n, chunk in enumerate(chunks, 1):
        filled = fill_template(chunk, template)
        path = f"{out_dir}/dense-prompt-{n}.txt"
        open(path, "w").write(filled)
        print(f"wrote {path} ({len(chunk)} words)")
```

## image_synthesize 调用坑（重要）

- **必须用绝对路径**写 `output_file_path`（相对路径会落到 agent default workspace `/Users/sunimax/workspace/`，不在项目目录）

```python
import os
# cwd 是项目根时
requests = [
    {
        "prompt": open(f".today-weak/dense-prompt-{n}.txt").read(),
        "output_file_path": os.path.abspath(f".today-weak/weakness-part{n}.png"),
        "aspect_ratio": "16:9",
        "resolution": "2K",
    }
    for n in range(1, n_charts + 1)
]
```

- **单 call 上限 10 个 requests**（本 skill 词数 ≤ 120 都能塞一个 call，超过要分批）
- 出图失败信息：`0/1 images saved (1 failed/missing)` — 单图失败不抛错，由 render_and_send.py 检查文件存在

## PNG → JPEG 压缩

飞书单消息 ≤ 5MB，PNG 5-6MB 超限，必须压：

```python
from PIL import Image
img = Image.open(png_path).convert("RGB")
# 85% resize（16:9 2K 原始 ~2752×1536 → 2339×1305）
new_size = (int(img.width * 0.85), int(img.height * 0.85))
img = img.resize(new_size, Image.LANCZOS)
img.save(jpg_path, "JPEG", quality=88, optimize=True)
# 实测 5.87MB PNG → 0.6MB JPEG
```

## 24 词实测（2026-08-06）

- 2 张图：part 1 (5.87MB PNG → 0.6MB JPEG), part 2 (5.20MB PNG → 0.6MB JPEG)
- 飞书消息：1 条 Markdown 介绍 + 2 条图片
- 整体耗时：拉词 1.5s + 拉细节 30s（限流）+ 出图 60s + 压缩 1s + 飞书 3s ≈ 95s
