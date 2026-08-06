# Threshold rationale

Every number in the pipeline is here for a reason. If you tune them, you should know what you're trading.

## ffmpeg colorkey: similarity=0.30, blend=0.10

**similarity** = "how close to the key color before we start cutting". Range 0.0–1.0.

- 0.05–0.15: leaves a green halo around the white stroke. NO.
- 0.30 (default): cuts the bulk of the green, leaves a thin residual halo that PIL step 2 finishes off.
- 0.50+: starts eating into the subject (yellow/olive/brown pixels with g-dominant components get chopped).

**blend** = "how soft the alpha transition is around the cutoff". Range 0.0–1.0.

- 0.05: hard cutoff → jaggy edges.
- 0.10 (default): smooth anti-aliased transition.
- 0.20+: the keyer gets "lazy" and leaves more green in the subject's edge.

## PIL step 1: `20 < a < 230 && g > r+18 && g > b+18`

**alpha range 20-230**:

- `a < 20`: nearly fully transparent, doesn't matter what we do
- `a > 230`: solid stroke or solid subject, no halo problem
- `20-230`: the anti-aliased ring around the white stroke → exactly where the green halo lives

**g > r+18 and g > b+18**:

- White stroke: RGB ≈ (255, 255, 255), `g - r ≈ 0`, `g - b ≈ 0` → **safe** (not green-dominant)
- Green halo: RGB ≈ (135, 234, 185), `g - r ≈ 80+`, `g - b ≈ 50+` → **target** (zeroed out)
- Brown hair (R 100, G 60, B 30): g not dominant → **safe**
- Yellow hoodie (R 220, G 170, B 80): g not dominant (r is) → **safe**
- Olive clothes (R 130, G 140, B 60): g dominant... but at alpha=255 (solid), not in the 20-230 range → **safe**

The threshold `18` is conservative — g must be at least 18 higher than both r and b. Real green halo pixels are 50+ above. The 18 floor protects against edge cases where a subject pixel happens to be slightly green (grass, leaves).

## PIL step 2 (`--fix-stroke` only): `a > 50 && r > 200 && b > 200 && g > r && g > b`

The "white stroke got slightly tinted green" artifact. After step 1, the stroke core itself (alpha=255) might still have a faint green cast (RGB ~ (240, 252, 245) instead of pure white). This step pulls it toward pure white.

**Why off by default**: this step assumes the stroke is white-ish. If your subject has any light-pastel colors that happen to be high-r and high-b (e.g., light pink cheeks, light blue sky), step 2 would also de-tint those — possibly wrong. Enable with `--fix-stroke` when you know you have white strokes.

**Why `r > 200 && b > 200`**: this is the "white-ish" filter. Skin tones have b < 150. Hair has b < 80. Yellow hoodie has b < 100. Only white strokes (and pure white) have both r and b above 200.

**Why strength = `min(1.0, g_adv / 30.0)`**: pulls toward white proportionally to how green-tinted the pixel is. A pixel at (255, 255, 255) is untouched. A pixel at (235, 255, 245) gets pulled to ~(255, 255, 255). A pixel at (200, 230, 210) only gets half-pulled.

## Auto-detect: outermost 100px

The key color is sampled from the outermost 100px of the image (top/bottom/left/right bands). Assumes:

- The subject doesn't touch the edges
- The background is the same color all the way around

If your image violates either assumption, pass `--key-color` manually or pre-crop the image.

## Validation: how to know it worked

```python
from PIL import Image
im = Image.open("output.png").convert("RGBA")
px = im.load()
green_halo = sum(
    1 for y in range(im.size[1]) for x in range(im.size[0])
    if 20 < px[x, y][3] < 230
    and px[x, y][1] > px[x, y][0] + 18
    and px[x, y][1] > px[x, y][2] + 18
)
print(f"residual green halo: {green_halo}")
```

- < 50: excellent, ship it
- 50–200: probably fine, but check on a dark background
- 200+: something's wrong, likely the wrong key color or the subject has a green stripe near the edge

## What's NOT here (and why)

- **AI segmentation (rembg / isnet-anime)**: too heavy for "known flat color" cases. Use this skill when the background is predictable; use rembg when it's not.
- **De-flickering / temporal consistency**: this is a per-image pipeline, no video support.
- **Spill suppression (Advanced Spill Reduction)**: not implemented. If you find the green tint is too strong, try `--fix-stroke` first, then if still bad, drop similarity to 0.25.
