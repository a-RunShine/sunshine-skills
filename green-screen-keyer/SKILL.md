---
name: green-screen-keyer
description: 抠"绿幕底 + 白描边贴纸"风格的 PNG，输出干净透明底。Make sure to use this skill whenever the user mentions 绿幕抠图 / 绿幕去底 / 表情包抠图 / sticker keyer / green screen keyer, or pastes a flat-color green background PNG with a white-stroked sticker/character on it, even if they don't explicitly ask for "keying" — this skill handles the whole pipeline including the residual green halo that plain ffmpeg colorkey leaves behind.
---

# Green Screen Keyer

## When to use

Use this skill when the user has a PNG that is:

- A **green screen** background (uniform green, typically `#00B050` cinematic green or `#00FF00` pure green)
- A **white-stroked** sticker / character / icon on top of it
- Needs to be **made transparent** for downstream use (表情包 / 小红书贴纸 / 微信表情 / UI 元素 / 公众号头图)

**Do not use** when:

- The background isn't a flat color (use rembg / isnet-anime instead)
- The asset has no white stroke and no anti-alias halo problem
- The user just wants to swap one color for another (single-pass colorkey is enough)

## What it does

Two-step pipeline that solves the "residual green halo" problem:

1. **ffmpeg colorkey** (`similarity=0.30, blend=0.10`) — rough keying, removes the bulk of the green background, keeps the subject's anti-aliased edges
2. **PIL edge cleanup** — scans semi-transparent pixels (`20 < alpha < 230`) where green dominates (`g > r+18 && g > b+18`) and zeroes them out — the white stroke is alpha=255 so it's safe; the half-transparent halo around the stroke is exactly the target

Optionally a third step: **white stroke de-stain** — for the "white stroke got slightly green-tinted from the background" problem. Off by default.

Auto-detects the key color from the image's edge pixels (no need to pass `--key-color`).

## Usage

### Quick one-shot (default)

```bash
~/.claude/skills/green-screen-keyer/scripts/key_green.sh input.png output.png
```

Auto-detects green color, runs the two-step pipeline, writes transparent PNG.

### Batch (a folder of PNGs)

```bash
for f in raw/*.png; do
  ~/.claude/skills/green-screen-keyer/scripts/key_green.sh "$f" "out/$(basename "$f")"
done
```

### With the white-stroke de-stain step (optional)

```bash
python3 ~/.claude/skills/green-screen-keyer/scripts/clean_edge.py \
  output.png --fix-stroke
```

### With 240×240 WeChat-style thumbnail

```bash
~/.claude/skills/green-screen-keyer/scripts/key_green.sh input.png out_240.png --resize 240
```

## Output expectations

- **Format**: PNG, RGBA
- **Size**: same as input (or `--resize N` to scale)
- **Transparency**: the green background should be 100% transparent (`alpha=0`)
- **Subject**: preserved with anti-aliased edges
- **Residual green halo**: 0 to a few hundred pixels per image (out of ~1M total), invisible to the eye

A quick quality check after keying:

```python
from PIL import Image
im = Image.open("output.png").convert("RGBA")
px = im.load()
green_halo = sum(
    1 for y in range(im.size[1]) for x in range(im.size[0])
    if 20 < px[x, y][3] < 230 and px[x, y][1] > px[x, y][0] + 18 and px[x, y][1] > px[x, y][2] + 18
)
print(f"residual green halo pixels: {green_halo}")
# Expect: < 100 for clean results
```

## Why two steps

`ffmpeg colorkey` is a single parameter (`similarity`) controlling "how close to the key color before we cut". The catch:

- Too small (0.08–0.15) → the white stroke's anti-aliased halo is *partially* green and survives the keyer → you see a **faint green ring** around the sticker
- Too large (0.5+) → the keyer starts eating into the subject (yellow/olive clothes, brown hair, anything greenish)

The fundamental problem: ffmpeg can't distinguish "subject edge with anti-aliasing" from "white stroke with anti-aliasing" because they look the same in RGB space.

**PIL's edge cleanup** uses the alpha channel that ffmpeg produces:

- White stroke core: `alpha=255` → never touched
- White stroke halo: `alpha` 200–230, g-dominant → **zeroed** (target)
- Subject edge: `alpha` 200–230, **NOT** g-dominant (brown, orange, etc.) → safe
- Subject core: `alpha=255` → never touched

That's the trick: **alpha range separates the two cases that RGB alone can't**.

For the full parameter rationale, see `references/threshold.md`.

## When the auto-detect might fail

The script samples edge pixels to find the dominant background color. It picks the most common color in the **outermost 100px** of the image. This breaks if:

- The subject fills the entire frame (no edge pixels are background)
- The background is not a single solid color (gradient, photo bg)
- The image has been pre-multiplied with alpha

In these cases, fall back to manual `--key-color 0x00B050` or use a different tool.

## File layout

```
green-screen-keyer/
├── SKILL.md                  # This file
├── scripts/
│   ├── key_green.sh          # Main entry: ffmpeg + PIL pipeline
│   └── clean_edge.py         # Standalone PIL edge cleanup (also handles --fix-stroke)
└── references/
    └── threshold.md          # Why these specific numbers
```

`key_green.sh` calls `clean_edge.py` for step 2 (and optional step 3). Run them independently if you need fine-grained control.
