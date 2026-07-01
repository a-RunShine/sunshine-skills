#!/usr/bin/env python3
"""Merge base and supplement question markdown into one enhanced file."""

from __future__ import annotations

import argparse
from pathlib import Path


def strip_title_block(text: str) -> str:
    """Conservatively remove only a leading title/description block.

    This avoids scanning deep into the document for the first horizontal rule,
    which can accidentally delete real chapter content.
    """
    lines = text.strip().splitlines()
    if not lines:
        return ""
    if not lines[0].startswith("# "):
        return text.strip()

    # Remove the first H1 title.
    idx = 1

    # Remove immediately following blank lines and short description lines.
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    while idx < len(lines) and (
        lines[idx].startswith("说明：")
        or lines[idx].startswith("说明:")
        or lines[idx].startswith("依据")
    ):
        idx += 1
        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1

    # Remove a separator only if it is still part of the opening block.
    if idx < len(lines) and lines[idx].strip() == "---":
        idx += 1
        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1

    return "\n".join(lines[idx:]).strip()


def assert_no_script_residue(text: str) -> None:
    bad_tokens = ["p.write_text", "print(p)", "print(len(", "\nPY\n"]
    found = [token for token in bad_tokens if token in text]
    if found:
        raise ValueError(f"possible script residue found: {found}")


def ensure_safe_output(base_path: Path, supplement_path: Path, output_path: Path, overwrite: bool) -> None:
    base_resolved = base_path.resolve()
    supplement_resolved = supplement_path.resolve()
    output_resolved = output_path.resolve()

    if output_resolved == base_resolved:
        raise ValueError("output path must not be the same as base input")
    if output_resolved == supplement_resolved:
        raise ValueError("output path must not be the same as supplement input")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"output already exists: {output_path}. Use --overwrite to replace it.")


def read_nonempty(path: Path, label: str) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{label} file is empty: {path}")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", help="base exercise markdown")
    parser.add_argument("supplement", help="supplement exercise markdown")
    parser.add_argument("output", help="merged enhanced markdown")
    parser.add_argument("--title", default="分章节练习题（标准增强版）",
                        help="合并后文件的标题")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing an existing output file")
    args = parser.parse_args()

    base_path = Path(args.base)
    supplement_path = Path(args.supplement)
    output_path = Path(args.output)

    ensure_safe_output(base_path, supplement_path, output_path, args.overwrite)

    base = read_nonempty(base_path, "base")
    supplement = strip_title_block(read_nonempty(supplement_path, "supplement"))

    content = f"# {args.title}\n\n"
    content += "说明：本文件由原练习题与补充强化题合并而成。前半部分是基础覆盖题，后半部分是针对审查报告补齐的重点、易错和应用题。\n\n"
    content += "---\n\n# 第一部分：基础覆盖题\n\n"
    content += base
    content += "\n\n---\n\n# 第二部分：补充强化题\n\n"
    content += supplement.rstrip() + "\n"

    assert_no_script_residue(content)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(output_path)
    print(f"lines={len(content.splitlines())}")


if __name__ == "__main__":
    main()
