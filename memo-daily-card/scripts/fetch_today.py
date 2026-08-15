#!/usr/bin/env python3
"""
Step 1: 拉今日 55 词 + 分类（薄弱 / 认识）

读墨墨 token（从 skill 自己的 .env）→ 调 get_today_items × 2 合并去重 → 按"先薄弱后认识"排
→ 写 .today-weak/today.json 到**当前工作目录**（cwd 必须是项目根）

分类规则：
- weak = first_response ∈ {VAGUE, FORGET} ∪ tags ⊋ STICKING
- known = 其余

排序：
- 弱前认后
- 弱内部：FORGET > STICKING > VAGUE > study_count asc
- 认内部：保留墨墨原序

用法（从项目根目录跑）：
  python3 ~/.claude/skills/memo-daily-card/scripts/fetch_today.py
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

# ---------- 路径常量 ----------
SKILL_DIR = Path(__file__).resolve().parent.parent   # scripts/ 的父级 = skill 根
ENV_FILE = SKILL_DIR / ".env"
OUT_DIR = Path.cwd() / ".today-weak"                 # 写到 cwd
OUT_FILE = OUT_DIR / "today.json"

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


# ---------- 弱信号分类 + 排序 ----------
PRIORITY = {"FORGET": 0, "STICKING": 1, "VAGUE": 2}


def maimemo_today(now: float | None = None) -> str:
    """墨墨今日 = 当前本地时间 - (4h 内偏移)。"""
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


def _pick_known_index(known_words: list, all_today: list) -> list:
    """让 known_words 按墨墨原序排（用 all_today 的下标）。"""
    index_map = {w["voc_id"]: i for i, w in enumerate(all_today)}
    return sorted(
        known_words,
        key=lambda w: index_map.get(w["voc_id"], 999999),
    )


# ---------- 主流程 ----------
def main() -> int:
    parser = argparse.ArgumentParser(description="拉今日 55 词 + 分类薄弱/认识")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help="输出目录（默认 cwd/.today-weak）",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "today.json"

    print(f"[INFO] skill dir: {SKILL_DIR}")
    print(f"[INFO] cwd:       {Path.cwd()}")
    print(f"[INFO] out dir:   {out_dir}")

    # 1. 诊断
    progress = get_study_progress()
    print(f"[INFO] study progress: {progress.get('finished')}/{progress.get('total')}")

    # 2. 拉今日全集
    all_today = fetch_all_today_words()
    print(f"[INFO] today words merged: {len(all_today)}")

    # 3. 分类
    weak_words = [w for w in all_today if is_weak(w)]
    known_words = [w for w in all_today if not is_weak(w)]
    print(f"[INFO] weak: {len(weak_words)}, known: {len(known_words)}")

    # 4. 排序（弱前认后）
    weak_sorted = sorted(
        weak_words,
        key=lambda w: (weak_priority(w), w.get("study_count", 999)),
    )
    known_sorted = _pick_known_index(known_words, all_today)
    final = weak_sorted + known_sorted

    # 5. 统计
    stats = {
        "total": len(all_today),
        "weak_total": len(weak_sorted),
        "known_total": len(known_sorted),
        "vague": sum(1 for w in weak_sorted if w.get("first_response") == "VAGUE"),
        "forget": sum(1 for w in weak_sorted if w.get("first_response") == "FORGET"),
        "sticking": sum(1 for w in weak_sorted if "STICKING" in (w.get("tags") or [])),
    }

    # 6. 输出
    weak_vid_set = {w["voc_id"] for w in weak_sorted}
    out = {
        "date": maimemo_today(),
        "progress": progress,
        "stats": stats,
        "words": [
            {
                "voc_id": w["voc_id"],
                "spelling": w["voc_spelling"],
                "first_response": w.get("first_response"),
                "is_new": w.get("is_new"),
                "tags": w.get("tags") or [],
                "study_count": w.get("study_count", 0),
                "category": "weak" if w["voc_id"] in weak_vid_set else "known",
                "reason_flags": [
                    f for f in [
                        "FORGET" if w.get("first_response") == "FORGET" else None,
                        "VAGUE" if w.get("first_response") == "VAGUE" else None,
                        "STICKING" if "STICKING" in (w.get("tags") or []) else None,
                    ] if f
                ],
            }
            for w in final
        ],
    }

    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"[OK] wrote {out_file}")
    print(f"[STATS] total={stats['total']} weak={stats['weak_total']} known={stats['known_total']} | "
          f"vague={stats['vague']} forget={stats['forget']} sticking={stats['sticking']}")
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
