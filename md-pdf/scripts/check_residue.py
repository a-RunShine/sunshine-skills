#!/usr/bin/env python3
"""Check a markdown file for accidental script residue."""
from __future__ import annotations

import argparse
from pathlib import Path

STRONG_RISK = [
    "p.write_text",
    ".write_text(",
    "read_text(",
    "from pathlib import Path",
    "import argparse",
    'if __name__ == "',
    "python3 - <<",
    "cat <<",
    "\nEOF\n",
    "\nPY\n",
    "print(p)",
]

WEAK_RISK = [
    "print(len(",
]


def check_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    issues = 0

    for token in STRONG_RISK:
        if token in text:
            print(f"[STRONG] found '{token}'")
            issues += 1

    for token in WEAK_RISK:
        if token in text:
            print(f"[WEAK] found '{token}' (may be false positive)")
            issues += 1

    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="markdown file to check")
    args = parser.parse_args()
    path = Path(args.file)
    issues = check_file(path)
    if issues:
        print(f"\n{issues} potential residue issue(s) found. Review file manually.")
        raise SystemExit(1)
    print("No script residue detected.")


if __name__ == "__main__":
    main()
