#!/usr/bin/env python3
"""
Step 4: PNG 压缩 + 飞书发送

读 cwd/.today-weak/weakness-part{N}.png（**必须已经由 Agent 用 image_synthesize 生成**）
→ 压缩成 JPEG → 发飞书（Markdown 介绍 + N 张图）

**默认 --dry-run**（仅压缩 PNG → JPEG + 打印"将发送"信息，**不**真发飞书）。
**必须显式 --send** 才会真发飞书（防 smoke test 误发）。

边界：
- 0 张图（weak.json count=0）→ 发"今天没薄弱词"提示
- 单图压缩失败 → 跳过该图
- 飞书介绍失败 → 跳过介绍直接发图
- 飞书图片失败 → 跳过该图，整体不中断
- 全部图失败 → 发 fallback 文本

用法（从项目根目录跑）：
  # dry-run（仅压缩 + 预览，不发）
  python3 ~/.claude/skills/memo-weakness-card/scripts/render_and_send.py

  # 真发飞书
  python3 ~/.claude/skills/memo-weakness-card/scripts/render_and_send.py --send
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ---------- 路径常量 ----------
OUT_DIR = Path.cwd() / ".today-weak"
WEAK_FILE = OUT_DIR / "weak.json"

# ---------- 飞书配置 ----------
USER_ID = "ou_48931ee833d5c20d0d37927b3b6a917f"   # 何东波，self DM

# ---------- 压缩配置 ----------
JPEG_QUALITY = 88
JPEG_RESIZE = 0.85   # PNG 5-6MB → JPEG ~0.6MB


# ---------- 工具函数 ----------
def read_weak() -> dict | None:
    if not WEAK_FILE.exists():
        return None
    return json.loads(WEAK_FILE.read_text())


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


# ---------- 飞书发送 ----------
def send_intro(count: int, v: int, f: int, s: int, k: int, dry_run: bool = True) -> bool:
    msg = f"**今天薄弱词 {count} 个**（VAGUE {v} + FORGET {f} + STICKING {s}），分 {k} 张大图讲解 ✓"
    if dry_run:
        print(f"[DRY-RUN] would send intro: {msg}")
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


def send_empty_notice(dry_run: bool = True) -> bool:
    msg = "**今天没薄弱词**，所有词都记住了，恭喜 ✓"
    if dry_run:
        print(f"[DRY-RUN] would send empty notice: {msg}")
        return True
    print(f"[INFO] sending empty notice")
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
        print(f"[WARN] empty notice send failed: {r.stderr.strip()[:200]}", file=sys.stderr)
        return False
    print(f"[OK] empty notice sent")
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
    msg = "**出图失败**：今天薄弱词讲解图未能生成，请检查 .today-weak/ 日志"
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


# ---------- 主流程 ----------
def main() -> int:
    parser = argparse.ArgumentParser(description="压缩 PNG 并发送飞书")
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
    weak_file = out_dir / "weak.json"

    if dry_run:
        print("=" * 60)
        print("[MODE] DRY-RUN（不真发飞书）。加 --send 才真发。")
        print("=" * 60)
    else:
        print("=" * 60)
        print("[MODE] SEND（真发飞书）")
        print("=" * 60)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 0. 读 weak.json
    if not weak_file.exists():
        print(f"[ERROR] {weak_file} 不存在，请先跑 fetch_weak.py", file=sys.stderr)
        return 1
    weak = json.loads(weak_file.read_text())

    count = weak.get("count", 0)
    stats = weak.get("stats", {})
    v = stats.get("vague", 0)
    f_ = stats.get("forget", 0)
    s = stats.get("sticking", 0)

    # 1. 词数 = 0 → 发提示退出
    if count == 0:
        print(f"[INFO] 0 词，发空提示")
        send_empty_notice(dry_run=dry_run)
        return 0

    # 2. 找所有 PNG（必须由 Agent 提前用 image_synthesize 生成）
    #    按 weak.json.date 过滤：只发今天生成的图（mtime >= 当天 00:00），
    #    旧图（非今天）自动挪到 .bak/（避免被误发，bug 复现 2026-08-07 part2 8/6 旧图被混发）
    from datetime import datetime, timedelta
    target_date = weak.get("date")  # "YYYY-MM-DD"
    if not target_date:
        # fallback: 用今天本地日期
        target_date = datetime.now().strftime("%Y-%m-%d")
    cutoff = datetime.strptime(target_date, "%Y-%m-%d")  # 当天 00:00

    all_pngs = sorted(out_dir.glob("weakness-part*.png"))
    png_files = []
    stale_pngs = []
    for p in all_pngs:
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        if mtime >= cutoff:
            png_files.append(p)
        else:
            stale_pngs.append(p)

    # 旧图挪到 .bak/（不删，便于恢复）
    if stale_pngs:
        bak_dir = out_dir / ".bak"
        bak_dir.mkdir(exist_ok=True)
        for p in stale_pngs:
            p_mtime = p.stat().st_mtime
            p_mtime_str = datetime.fromtimestamp(p_mtime).strftime("%Y%m%d")
            target = bak_dir / f"{p.stem}.{p_mtime_str}.bak{p.suffix}"
            p.rename(target)
            # 同步挪 .jpg（如果存在）
            jpg_sibling = p.with_suffix(".jpg")
            if jpg_sibling.exists():
                jpg_target = target.with_suffix(".jpg")
                jpg_sibling.rename(jpg_target)
            print(f"[CLEANUP] stale PNG → .bak/: {p.name} (mtime={datetime.fromtimestamp(p_mtime):%Y-%m-%d %H:%M})")

    if not png_files:
        print(f"[ERROR] {out_dir}/weakness-part*.png 不存在（过滤 target_date={target_date} 后），Agent 必须先调 image_synthesize", file=sys.stderr)
        return 1
    k = len(png_files)
    print(f"[INFO] {count} words → {k} 张 PNG（target_date={target_date}，过滤掉 {len(stale_pngs)} 张旧图）")

    # 3. 压缩 PNG → JPEG
    success_jpgs: list[Path] = []
    failed = 0
    for png in png_files:
        jpg = png.with_suffix(".jpg")
        if compress_png_to_jpg(png, jpg):
            success_jpgs.append(jpg)
        else:
            failed += 1

    if not success_jpgs:
        print(f"[ERROR] 全部 {k} 张图压缩失败，发 fallback 告警")
        send_fallback_error(dry_run=dry_run)
        return 1

    # 4. 飞书发送
    send_intro(count, v, f_, s, len(success_jpgs), dry_run=dry_run)

    cwd = os.getcwd()
    try:
        os.chdir(out_dir)  # 关键：cd 到 .today-weak（lark-cli --file cwd-relative）
        for jpg in success_jpgs:
            send_image(jpg.name, dry_run=dry_run)
    finally:
        os.chdir(cwd)

    # 5. 统计
    print(f"[DONE] 成功 {len(success_jpgs)}/{k} 张图" + ("（dry-run 未发）" if dry_run else "（飞书已通知）"))
    if failed > 0:
        print(f"[WARN] 失败 {failed} 张（压缩失败）", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
