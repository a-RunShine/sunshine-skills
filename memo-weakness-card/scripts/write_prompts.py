#!/usr/bin/env python3
"""
Step 2: 写 prompt 模板

读 cwd/.today-weak/cards-clean.json（Agent 在 Step 1.5 用 LLM 知识生成）
→ 分图（每张 ≤ 12 词）→ 写 dense-prompt-N.txt 到 cwd/.today-weak/

用法（从项目根目录跑）：
  python3 ~/.claude/skills/memo-weakness-card/scripts/write_prompts.py
"""
import argparse
import json
import sys
from pathlib import Path

OUT_DIR = Path.cwd() / ".today-weak"
CARDS_FILE = OUT_DIR / "cards-clean.json"

WORDS_PER_CHART = 12  # 每张图最多 12 词（3×4 网格）

# Prompt 模板 - 引用 references/prompt-template.md 里的同一份
TEMPLATE = """A flat illustrated vocabulary poster, 16:9 landscape, 2K resolution.

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

WORDS ({n} entries, in grid order: row 1 left-to-right, then row 2, then row 3):

{word_blocks}

CRITICAL CONSTRAINTS:
- ONLY bold the target word inside example sentences, do NOT bold anything else
- Each cell must contain ALL 4 elements above, no missing
- {n} cells in a strict 3×4 grid (or fewer for last chart), no overlap
- Do NOT add any extra text, watermark, page number, or label outside the cells
- Do NOT add a title bar or header
"""


def fill_card_block(idx: int, card: dict) -> str:
    return (
        f"{idx}. {card['spelling']} — {card['phonetic']} {card['pos']} — "
        f"{card['meaning_zh']} — {card['example_en_clean']} — "
        f"Mnemonic hint: {card['mnemonic_visual']}"
    )


def fill_chart_prompt(cards: list[dict]) -> str:
    n = len(cards)
    blocks = "\n".join(
        fill_card_block(i, c) for i, c in enumerate(cards, 1)
    )
    return TEMPLATE.format(n=n, word_blocks=blocks)


def chunk_cards(cards: list[dict], size: int = WORDS_PER_CHART) -> list[list[dict]]:
    return [cards[i:i + size] for i in range(0, len(cards), size)]


def main() -> int:
    parser = argparse.ArgumentParser(description="写 dense-prompt 模板")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help="输出目录（默认 cwd/.today-weak）",
    )
    args = parser.parse_args()
    out_dir = args.out_dir
    cards_file = out_dir / "cards-clean.json"

    if not cards_file.exists():
        print(f"[ERROR] {cards_file} 不存在，请先在 cwd 用 LLM 知识填 cards-clean.json", file=sys.stderr)
        return 1

    cards = json.loads(cards_file.read_text())
    if not cards:
        print(f"[ERROR] {cards_file} 是空数组，无词可写", file=sys.stderr)
        return 1

    chunks = chunk_cards(cards)
    print(f"[INFO] {len(cards)} words → {len(chunks)} 张图")

    for n, chunk in enumerate(chunks, 1):
        prompt = fill_chart_prompt(chunk)
        path = out_dir / f"dense-prompt-{n}.txt"
        path.write_text(prompt)
        print(f"[OK] wrote {path} ({len(chunk)} words, {len(prompt)} chars)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
