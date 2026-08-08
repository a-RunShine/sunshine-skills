#!/usr/bin/env python3
"""
Step 1: 拉薄弱词

读墨墨 token（从 skill 自己的 .env）→ 调 get_today_items × 2 合并去重 → 筛 VAGUE ∪ FORGET ∪ STICKING → 排序
→ 写 .today-weak/weak.json 到**当前工作目录**（cwd 必须是项目根）

边界：
- 词数 = 0 → 仍写 weak.json (count=0)，不抛错
- API 失败 → 抛错退出，飞书不发送

用法（从项目根目录跑）：
  python3 ~/.claude/skills/memo-weakness-card/scripts/fetch_weak.py
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

# ---------- 路径常量 ----------
SKILL_DIR = Path(__file__).resolve().parent.parent   # scripts/ 的父级 = skill 根
ENV_FILE = SKILL_DIR / ".env"
OUT_DIR = Path.cwd() / ".today-weak"                 # 写到 cwd
OUT_FILE = OUT_DIR / "weak.json"

# ---------- 墨墨 API ----------
API_BASE = "https://open.maimemo.com/open/api/v1"
TOKEN = open(ENV_FILE).read().split("=", 1)[1].strip()
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def get_study_progress() -> dict:
    r = requests.post(
        f"{API_BASE}/study/get_study_progress",
        headers=HEADERS, json={}, timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("progress", {})


def get_today_items(is_finished: bool, limit: int = 200) -> list:
    r = requests.post(
        f"{API_BASE}/study/get_today_items",
        headers=HEADERS,
        json={"is_finished": is_finished, "limit": limit},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("today_items", [])


def fetch_all_today_words() -> list:
    """合并 is_finished=true + false 两次调用，按 voc_id 去重。"""
    finished = get_today_items(is_finished=True, limit=200)
    unfinished = get_today_items(is_finished=False, limit=200)
    seen = set()
    merged = []
    for it in finished + unfinished:
        vid = it["voc_id"]
        if vid in seen:
            continue
        seen.add(vid)
        merged.append(it)
    return merged


# ---------- 弱信号筛 + 排序 ----------
PRIORITY = {"FORGET": 0, "STICKING": 1, "VAGUE": 2}


def maimemo_today(now: float | None = None) -> str:
    """墨墨今日 = 当前本地时间 - (4h 内偏移)。

    墨墨 4:00 重置今日任务，0:00-3:59 跑时墨墨"今日" = 昨天。
    """
    from datetime import datetime, timedelta
    t = datetime.fromtimestamp(now if now is not None else time.time())
    if t.hour < 4:
        t = t - timedelta(days=1)
    return t.strftime("%Y-%m-%d")


def is_weak(word: dict) -> bool:
    return (
        word.get("first_response") in {"VAGUE", "FORGET"}
        or "STICKING" in (word.get("tags") or [])
    )


def weak_priority(word: dict) -> int:
    fr = word.get("first_response")
    tags = word.get("tags") or []
    if fr == "FORGET":
        return PRIORITY["FORGET"]
    if "STICKING" in tags:
        return PRIORITY["STICKING"]
    if fr == "VAGUE":
        return PRIORITY["VAGUE"]
    return 9


def sort_weak(words: list) -> list:
    return sorted(
        words,
        key=lambda w: (weak_priority(w), w.get("study_count", 999)),
    )


# ---------- 主流程 ----------
def main() -> int:
    parser = argparse.ArgumentParser(description="拉今日薄弱词")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help=f"输出目录（默认 cwd/.today-weak）",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "weak.json"

    print(f"[INFO] skill dir: {SKILL_DIR}")
    print(f"[INFO] env file:  {ENV_FILE}")
    print(f"[INFO] cwd:       {Path.cwd()}")
    print(f"[INFO] out dir:   {out_dir}")

    # 1. 诊断
    progress = get_study_progress()
    print(f"[INFO] study progress: {progress.get('finished')}/{progress.get('total')}")

    # 2. 拉今日全集
    all_today = fetch_all_today_words()
    print(f"[INFO] today words merged: {len(all_today)}")

    # 3. 筛薄弱
    weak = [w for w in all_today if is_weak(w)]
    print(f"[INFO] weak words: {len(weak)}")

    # 4. 排序
    weak_sorted = sort_weak(weak)

    # 5. 统计
    stats = {
        "total": len(all_today),
        "weak_total": len(weak_sorted),
        "vague": sum(1 for w in weak_sorted if w.get("first_response") == "VAGUE"),
        "forget": sum(1 for w in weak_sorted if w.get("first_response") == "FORGET"),
        "sticking": sum(1 for w in weak_sorted if "STICKING" in (w.get("tags") or [])),
    }

    # 6. 输出
    out = {
        "date": maimemo_today(),
        "progress": progress,
        "stats": stats,
        "count": len(weak_sorted),
        "words": [
            {
                "voc_id": w["voc_id"],
                "spelling": w["voc_spelling"],
                "first_response": w.get("first_response"),
                "is_new": w.get("is_new"),
                "tags": w.get("tags") or [],
                "study_count": w.get("study_count", 0),
                "reason_flags": [
                    f for f in [
                        "FORGET" if w.get("first_response") == "FORGET" else None,
                        "VAGUE" if w.get("first_response") == "VAGUE" else None,
                        "STICKING" if "STICKING" in (w.get("tags") or []) else None,
                    ] if f
                ],
            }
            for w in weak_sorted
        ],
    }

    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"[OK] wrote {out_file} ({stats['weak_total']} weak words)")
    print(f"[STATS] vague={stats['vague']} forget={stats['forget']} sticking={stats['sticking']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except requests.RequestException as e:
        print(f"[ERROR] API failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
