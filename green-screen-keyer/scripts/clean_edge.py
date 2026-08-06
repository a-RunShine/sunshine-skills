#!/usr/bin/env python3
"""
PIL edge cleanup for green-screen keying.

Two stages:
  1. Default: zero out semi-transparent pixels that are green-dominant
     (kills the residual green halo around the white stroke)
  2. Optional --fix-stroke: pull "white-ish stroke" pixels toward pure white
     (kills the "white stroke tinted green from the background" artifact)

Usage:
  clean_edge.py input.png                   # step 1 only
  clean_edge.py input.png -o out.png        # step 1, explicit output
  clean_edge.py input.png --fix-stroke      # step 1 + step 2
  clean_edge.py input.png --resize 240      # scale down first (240x240)
"""

import argparse
from pathlib import Path
from PIL import Image


def step1_zero_green_halo(im: Image.Image) -> int:
    """Zero out alpha for semi-transparent green-dominant pixels.
    Returns the count of pixels touched.
    """
    px = im.load()
    w, h = im.size
    cleared = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if 20 < a < 230 and g > r + 18 and g > b + 18:
                px[x, y] = (r, g, b, 0)
                cleared += 1
    return cleared


def step2_fix_white_stroke(im: Image.Image) -> int:
    """Pull 'white-ish stroke' pixels (high r/b, green-dominant) toward pure white.
    Returns the count of pixels touched.
    """
    px = im.load()
    w, h = im.size
    fixed = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # White-ish: r and b both high (skin/clothes/hair have low b)
            if a > 50 and r > 200 and b > 200 and g > r and g > b:
                g_adv = g - max(r, b)
                if g_adv < 2:
                    continue
                # Pull r/b toward g
                strength = min(1.0, g_adv / 30.0)
                new_r = int(r + (g - r) * strength)
                new_b = int(b + (g - b) * strength)
                px[x, y] = (new_r, g, new_b, a)
                fixed += 1
    return fixed


def auto_detect_key_color(im: Image.Image, sample_width: int = 100) -> tuple[int, int, int] | None:
    """Sample the outer `sample_width` pixels and find the most common color.
    Returns (r, g, b) or None if image is too small.
    """
    w, h = im.size
    if w < sample_width * 2 or h < sample_width * 2:
        sample_width = min(w, h) // 4
    if sample_width == 0:
        return None

    from collections import Counter
    counter = Counter()
    # Sample top, bottom, left, right edges
    for y in range(sample_width):
        for x in range(w):
            counter[im.getpixel((x, y))] += 1
            counter[im.getpixel((x, h - 1 - y))] += 1
    for x in range(sample_width):
        for y in range(sample_width, h - sample_width):
            counter[im.getpixel((x, y))] += 1
            counter[im.getpixel((w - 1 - x, y))] += 1
    most_common, _ = counter.most_common(1)[0]
    return most_common


def main():
    ap = argparse.ArgumentParser(description="PIL edge cleanup for green-screen keying")
    ap.add_argument("input", help="Input PNG path (already keyed by ffmpeg, or just the raw green-screen PNG)")
    ap.add_argument("-o", "--output", help="Output PNG path (default: overwrite input)")
    ap.add_argument("--fix-stroke", action="store_true",
                    help="Also pull white-ish stroke pixels toward pure white (step 2)")
    ap.add_argument("--resize", type=int, default=0,
                    help="Resize to NxN before processing (e.g. 240 for WeChat-style)")
    ap.add_argument("--detect-key-color", action="store_true",
                    help="Print auto-detected key color and exit (debug aid)")
    args = ap.parse_args()

    src = Path(args.input)
    dst = Path(args.output) if args.output else src

    im = Image.open(src).convert("RGBA")

    if args.detect_key_color:
        key = auto_detect_key_color(im)
        if key:
            print(f"detected key color: rgb{key} = #{key[0]:02X}{key[1]:02X}{key[2]:02X}")
        else:
            print("could not detect key color (image too small)")
        return

    if args.resize:
        im = im.resize((args.resize, args.resize), Image.LANCZOS)

    cleared = step1_zero_green_halo(im)
    fixed = 0
    if args.fix_stroke:
        fixed = step2_fix_white_stroke(im)

    im.save(dst, "PNG", optimize=True)
    print(f"step1 (green halo zeroed): {cleared} px")
    if args.fix_stroke:
        print(f"step2 (white stroke de-stain): {fixed} px")
    print(f"saved: {dst}")


if __name__ == "__main__":
    main()
