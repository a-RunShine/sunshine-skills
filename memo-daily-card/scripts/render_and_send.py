#!/usr/bin/env python3
"""
Step 3+4: PNG 压缩 + 飞书发送（分两批：薄弱 + 认识）

读 cwd/.today-weak/today.json（stats + 分类信息）
→ 找 weakness-part{N}.png / knownness-part{N}.png（必须由 Agent 用 image_synthesize 生成）
→ 按 today.json.date 过滤旧图（旧图挪到 .bak/）
→ 压缩成 JPEG → 分两批发飞书（先薄弱批：1 介绍 + N 张图；再认识批：1 介绍 + M 张图）

**默认 --dry-run**（仅压缩 PNG → JPEG + 打印"将发送"信息，**不**真发飞书）。
**必须显式 --send** 才会真发飞书（防 smoke test 误发）。

边界：
- 薄弱 0 词 → 跳过薄弱批，只发认识批
- 认识 0 词 → 跳过认识批，只发薄弱批
- 单图压缩失败 → 跳过该图
- 飞书介绍失败 → 跳过介绍直接发图
- 飞书图片失败 → 跳过该图，整体不中断
- 全部图失败 → 发 fallback 文本

用法（从项目根目录跑）：
  # dry-run（仅压缩 + 预览，不发）
  python3 ~/.claude/skills/memo-daily-card/scripts/render_and_send.py

  # 真发飞书
  python3 ~/.claude/skills/memo-daily-card/scripts/render_and_send.py --send
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------- 路径常量 ----------
OUT_DIR = Path.cwd() / ".today-weak"
TODAY_FILE = OUT_DIR / "today.json"

# ---------- 飞书配置 ----------
USER_ID = "ou_48931ee833d5c20d0d37927b3b6a917f"   # 何东波，self DM

# ---------- 压缩配置 ----------
JPEG_QUALITY = 88
JPEG_RESIZE = 0.85   # PNG 5-6MB → JPEG ~0.6MB


# ---------- 工具函数 ----------
def read_today() -> dict | None:
    if not TODAY_FILE.exists():
        return None
    return json.loads(TODAY_FILE.read_text())


def compress_png_to_jpg(png_path: Path, jpg_path: Path) -> bool:
    """PNG → JPEG 压缩，飞书 ≤ 5MB 限制。"""
    try:
        from PIL import Image
    except ImportError:
        print("[ERROR] Pillow 未安装，跑：pip install Pillow", file=sys.stderr)
        return False

    img = Image.open(png_path).convert("RGB")
    new_size = (int(img.width * JPEG_RESIZE), int(img.height * JPEG_RESIZE))
    img = img.resize(new_size, Image.LANCZOS)
    img.save(jpg_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    size_mb = jpg_path.stat().st_size / 1024 / 1024
    print(f"[OK] compressed {png_path.name} → {jpg_path.name} ({size_mb:.2f} MB)")
    return True


def _filter_stale_pngs(out_dir: Path, target_date: str, pattern: str) -> tuple[list[Path], list[Path]]:
    """按 today.json.date 过滤 PNG：只留今天生成的，旧图挪 .bak/。"""
    cutoff = datetime.strptime(target_date, "%Y-%m-%d")
    all_pngs = sorted(out_dir.glob(pattern))
    fresh = []
    stale = []
    for p in all_pngs:
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        if mtime >= cutoff:
            fresh.append(p)
        else:
            stale.append(p)

    if stale:
        bak_dir = out_dir / ".bak"
        bak_dir.mkdir(exist_ok=True)
        for p in stale:
            p_mtime = p.stat().st_mtime
            p_mtime_str = datetime.fromtimestamp(p_mtime).strftime("%Y%m%d")
            target = bak_dir / f"{p.stem}.{p_mtime_str}.bak{p.suffix}"
            p.rename(target)
            jpg_sibling = p.with_suffix(".jpg")
            if jpg_sibling.exists():
                jpg_sibling.rename(target.with_suffix(".jpg"))
            print(f"[CLEANUP] stale PNG → .bak/: {p.name} "
                  f"(mtime={datetime.fromtimestamp(p_mtime):%Y-%m-%d %H:%M})")
    return fresh, stale


# ---------- 飞书发送 ----------
def send_intro(msg: str, dry_run: bool = True) -> bool:
    if dry_run:
        print(f"[DRY-RUN] would send intro: {msg[:80]}")
        return True
    print(f"[INFO] sending intro: {msg[:60]}...")
    r = subprocess.run(
        [
            "lark-cli", "im", "+messages-send",
            "--as", "bot",
            "--user-id", USER_ID,
            "--markdown", msg,
        ],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"[WARN] intro send failed: {r.stderr.strip()[:200]}", file=sys.stderr)
        return False
    print(f"[OK] intro sent")
    return True


def send_image(jpg_basename: str, dry_run: bool = True) -> bool:
    """发单张图（cwd 已被切到 OUT_DIR）。

    注意：用 --image 不是 --file —— --file 走 file 消息类型（用户看到"文件"图标），
    --image 走 image 消息类型（用户看到"图片"图标，可直接预览）。
    """
    if dry_run:
        print(f"[DRY-RUN] would send image: {jpg_basename}")
        return True
    print(f"[INFO] sending image: {jpg_basename}")
    r = subprocess.run(
        [
            "lark-cli", "im", "+messages-send",
            "--as", "bot",
            "--user-id", USER_ID,
            "--image", jpg_basename,
        ],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"[WARN] image send failed ({jpg_basename}): {r.stderr.strip()[:200]}", file=sys.stderr)
        return False
    print(f"[OK] image sent: {jpg_basename}")
    return True


def send_fallback_error(dry_run: bool = True) -> bool:
    msg = "**出图失败**：今天词卡未能生成，请检查 .today-weak/ 日志"
    if dry_run:
        print(f"[DRY-RUN] would send fallback error: {msg}")
        return True
    print(f"[WARN] sending fallback error notice")
    r = subprocess.run(
        [
            "lark-cli", "im", "+messages-send",
            "--as", "bot",
            "--user-id", USER_ID,
            "--markdown", msg,
        ],
        capture_output=True, text=True,
    )
    return r.returncode == 0


# ---------- 单批发送 ----------
def send_batch(
    batch_name: str,            # "weak" | "known"
    png_prefix: str,            # "weakness-part" | "knownness-part"
    intro_msg: str,
    out_dir: Path,
    target_date: str,
    dry_run: bool,
) -> bool:
    """单批：压缩 + 飞书发送。返回 True = 至少 1 张图成功发送。"""
    print(f"\n--- 批：{batch_name} ---")
    fresh_pngs, stale = _filter_stale_pngs(out_dir, target_date, f"{png_prefix}*.png")
    print(f"[INFO] {batch_name} 批：fresh={len(fresh_pngs)} stale={len(stale)}")

    if not fresh_pngs:
        print(f"[WARN] {batch_name} 批无 PNG，跳过")
        return False

    # 压缩
    success_jpgs: list[Path] = []
    failed = 0
    for png in fresh_pngs:
        jpg = png.with_suffix(".jpg")
        if compress_png_to_jpg(png, jpg):
            success_jpgs.append(jpg)
        else:
            failed += 1

    if not success_jpgs:
        print(f"[ERROR] {batch_name} 批全部 {len(fresh_pngs)} 张图压缩失败")
        return False

    # 飞书：介绍 + 图
    send_intro(intro_msg, dry_run=dry_run)

    cwd = os.getcwd()
    try:
        os.chdir(out_dir)
        for jpg in success_jpgs:
            send_image(jpg.name, dry_run=dry_run)
    finally:
        os.chdir(cwd)

    print(f"[BATCH DONE] {batch_name} 成功 {len(success_jpgs)}/{len(fresh_pngs)} 张图"
          + ("（dry-run 未发）" if dry_run else "（飞书已通知）"))
    if failed > 0:
        print(f"[WARN] {batch_name} 批失败 {failed} 张", file=sys.stderr)
    return True


# ---------- 主流程 ----------
def main() -> int:
    parser = argparse.ArgumentParser(description="压缩 PNG 并分两批发送飞书")
    parser.add_argument(
        "--send",
        action="store_true",
        help="真发飞书（默认 dry-run，只压缩 + 打印，不会真发）",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help="输入/输出目录（默认 cwd/.today-weak）",
    )
    args = parser.parse_args()
    dry_run = not args.send
    out_dir = args.out_dir
    today_file = out_dir / "today.json"

    if dry_run:
        print("=" * 60)
        print("[MODE] DRY-RUN（不真发飞书）。加 --send 才真发。")
        print("=" * 60)
    else:
        print("=" * 60)
        print("[MODE] SEND（真发飞书）")
        print("=" * 60)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 0. 读 today.json
    if not today_file.exists():
        print(f"[ERROR] {today_file} 不存在，请先跑 fetch_today.py", file=sys.stderr)
        return 1
    today = json.loads(today_file.read_text())

    target_date = today.get("date") or datetime.now().strftime("%Y-%m-%d")
    stats = today.get("stats", {})
    weak_n = stats.get("weak_total", 0)
    known_n = stats.get("known_total", 0)
    v = stats.get("vague", 0)
    f_ = stats.get("forget", 0)
    s = stats.get("sticking", 0)

    print(f"[INFO] target_date={target_date} weak={weak_n} known={known_n} "
          f"(vague={v} forget={f_} sticking={s})")

    any_success = False
    fallback_needed = False

    # 批 1：薄弱
    if weak_n > 0:
        intro = (f"**今天薄弱词 {weak_n} 个**（VAGUE {v} + FORGET {f_} + STICKING {s}），"
                 f"讲解图见下方 ✓")
        ok = send_batch(
            batch_name="weak",
            png_prefix="weakness-part",
            intro_msg=intro,
            out_dir=out_dir,
            target_date=target_date,
            dry_run=dry_run,
        )
        any_success = any_success or ok
        if not ok:
            fallback_needed = True
    else:
        print(f"\n--- 批：weak ---")
        print(f"[INFO] 薄弱 0 词，跳过薄弱批")

    # 批 2：认识
    if known_n > 0:
        intro = f"**今天认识词 {known_n} 个**，复习图见下方 ✓"
        ok = send_batch(
            batch_name="known",
            png_prefix="knownness-part",
            intro_msg=intro,
            out_dir=out_dir,
            target_date=target_date,
            dry_run=dry_run,
        )
        any_success = any_success or ok
        if not ok:
            fallback_needed = True
    else:
        print(f"\n--- 批：known ---")
        print(f"[INFO] 认识 0 词，跳过认识批")

    # 全部失败 → fallback
    if fallback_needed and not any_success:
        print(f"[ERROR] 薄弱 + 认识 批都失败，发 fallback 告警")
        send_fallback_error(dry_run=dry_run)
        return 1

    print(f"\n[DONE] 成功: {('飞书已通知' if not dry_run else 'dry-run 未发')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
