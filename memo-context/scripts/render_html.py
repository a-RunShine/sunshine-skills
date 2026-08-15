#!/usr/bin/env python3
"""Render memo-context daily page.html from article.md + annotations.json.

新版（2026-08-09 升级）：居中单栏 + 两个 tab + 单词点击弹翻译 + 用户标熟练度
+ 划选任意词也标熟练度（荧光笔高亮）。

Inputs (in contexts/YYYY-MM-DD/):
    article.md          — Step 3 产出，含 *word* 标记 + 末尾 ## Translation 块
    annotations.json    — 含 main_words / supporting_words / word_translations

Output:
    contexts/YYYY-MM-DD/page.html

Usage:
    python3 scripts/render_html.py                    # 用今天日期
    python3 scripts/render_html.py --date 2026-08-08  # 指定日期
    python3 scripts/render_html.py --dir contexts/<dir>  # 指定目录
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# Project root: <project>/.claude/skills/memo-context/scripts/render_html.py
#   → <project> = 5 levels up from __file__
SKILL_DIR = Path(__file__).resolve().parent.parent      # memo-context/

# 默认上下文目录（探测优先级，详见 resolve_contexts_dir）
_DEFAULT_CONTEXT_CANDIDATES = [
    Path.home() / "Desktop" / "墨墨记单词" / "contexts",
    SKILL_DIR.parent.parent.parent / "contexts",  # 旧版：~/.claude/skills/.../contexts
    Path.cwd() / "contexts",
]


def resolve_contexts_dir() -> Path:
    """探测 contexts 目录：环境变量 → --dir → 候选路径。

    Returns:
        contexts/ 目录的 Path。若都不存在，返回第一个候选（让 main 报错时给出明确路径）。
    """
    env = os.environ.get("MEMO_CONTEXTS_DIR")
    if env:
        return Path(env).expanduser().resolve()

    for cand in _DEFAULT_CONTEXT_CANDIDATES:
        if cand.exists():
            return cand

    return _DEFAULT_CONTEXT_CANDIDATES[0]  # 给 main 报错用


CONTEXTS_DIR = resolve_contexts_dir()


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

# Match *word* but not **bold** and not \*literal\*
EM_PATTERN = re.compile(r"(?<!\*)\*([^*\s]+?)\*(?!\*)")
TRANS_BLOCK = re.compile(r"##\s*Translation\s*\n(.*?)(?=\n##\s|\Z)", re.DOTALL)


def parse_passage_and_translation(md_text: str) -> tuple[list[str], list[str]]:
    """返回 (passage_paragraphs_html, translation_paragraphs)。

    - 段落用空行分隔
    - 跳过标题、模式、词表、Translation 块、题号、C 模式答案
    - *word* → <em class="word" data-word="word">word</em>
    """
    # 1) 提取 ## Translation 块（先做，因为它在文件末尾）
    trans_match = TRANS_BLOCK.search(md_text)
    translation_paras: list[str] = []
    if trans_match:
        for p in re.split(r"\n\s*\n", trans_match.group(1).strip()):
            p = p.strip()
            if p:
                translation_paras.append(p)

    # 2) 提取正文（在 Translation 块之前）
    main_text = md_text[:trans_match.start()] if trans_match else md_text

    # 找 ## 文字稿 块
    passage_match = re.search(r"##\s*文字稿\s*\n(.*?)\Z", main_text, re.DOTALL)
    if passage_match:
        passage_text = passage_match.group(1)
    else:
        passage_text = main_text

    raw_paragraphs = re.split(r"\n\s*\n", passage_text.strip())
    out: list[str] = []
    for p in raw_paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith("#"):
            continue
        # C 模式题号 / 答案块
        if re.match(r"^\d+\.\s", p) or p.startswith("【") or p.startswith("答案"):
            continue
        # *word* → <em class="word" data-word="word">word</em>
        p_html = EM_PATTERN.sub(
            r'<em class="word" data-word="\1">\1</em>',
            p,
        )
        out.append(p_html)

    return out, translation_paras


# ---------------------------------------------------------------------------
# CSS (placeholder — replaced by Edit below)
# ---------------------------------------------------------------------------

CSS_PLACEHOLDER = r"""
:root {
  --bg: #f7f5f0;
  --bg-soft: #efeae0;
  --bg-soft-2: #e6dfd1;
  --text: #1f1d1a;            /* 设计目标 ≥7:1 对比度 */
  --text-soft: #5a5048;       /* 暗色也合规 */
  --accent: #8b1f12;          /* 砖红更深，米白底对比度 ≈ 8.7:1 (WCAG AAA) */
  --accent-soft: #e8c1bb;
  --border: #d8cfc1;
  --prof-good: #1f6b3e;       /* sea green 深，米白底 ≈ 7.2:1 (AAA) */
  --prof-vague: #8b6914;      /* dark goldenrod 深，米白底 ≈ 6.8:1 (AAA 大字) */
  --prof-bad: #8b1a1a;        /* firebrick 深，米白底 ≈ 8.5:1 (AAA) */
  --font-base: 18px;          /* typography 建议默认 18px */
  --line-height: 1.6;         /* web.dev 66ch @ 1.6 */
  --font-mono: "SF Mono", "JetBrains Mono", Consolas, monospace;
  /* 西文优先，中文 fallback（CLReq 推荐） */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial,
               "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  --font-serif: Georgia, "Source Han Serif SC", "Songti SC", "Cambria",
                "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", serif;
}
[data-theme="dark"] {
  --bg: #121212;              /* 避免纯黑，WebAIM 推荐 */
  --bg-soft: #1f1d1a;
  --bg-soft-2: #2a2722;
  --text: #f0f0ec;
  --text-soft: #a8a299;
  --accent: #e07b6b;
  --accent-soft: #5e3a35;
  --border: #3a3329;
  --prof-good: #6fcf97;
  --prof-vague: #e6c14d;
  --prof-bad: #ec7272;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: var(--font-sans);
  font-size: var(--font-base);
  background: var(--bg);
  color: var(--text);
  line-height: var(--line-height);
  transition: background 0.2s, color 0.2s;
}

/* ---------- Header：三段式布局（建议 16：标题左 + tab 中 + 工具右） ---------- */
header.page-header {
  position: sticky; top: 0; z-index: 30;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  padding: 12px 24px;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
}
.title-meta {
  display: flex; align-items: baseline; gap: 10px; min-width: 0;
  justify-self: start;
}
.title-meta .title {
  font-family: var(--font-serif); font-size: 16px; font-weight: 600;
  color: var(--text); overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; max-width: 320px;
}
.title-meta .date {
  font-family: var(--font-mono); font-size: 12px; color: var(--text-soft);
}

/* Tab 中间栏：下划线 indicator（建议 17） */
nav.tabs {
  display: flex; gap: 0;
  justify-self: center;
  border-bottom: 1px solid var(--border);
  /* 让 indicator 横跨整个 header 宽度 */
  margin-bottom: -13px;  /* 抵消 header padding-bottom */
  padding: 0;
}
nav.tabs .tab {
  background: transparent; color: var(--text-soft);
  border: none;
  padding: 8px 18px;
  font-size: 14px; font-weight: 400;
  cursor: pointer; font-family: var(--font-sans);
  position: relative;
  transition: color 0.15s;
}
nav.tabs .tab:hover { color: var(--text); }
nav.tabs .tab.active {
  color: var(--text); font-weight: 600;
}
nav.tabs .tab.active::after {
  content: '';
  position: absolute;
  left: 14px; right: 14px;
  bottom: -1px;
  height: 3px;
  background: var(--accent);
  border-radius: 3px 3px 0 0;
}

.toolbar { display: flex; gap: 6px; align-items: center; justify-self: end; }
.toolbar button, .toolbar select {
  background: var(--bg-soft); color: var(--text);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 6px 10px; font-size: 13px;
  cursor: pointer; font-family: var(--font-sans);
}
.toolbar button:hover { background: var(--accent-soft); }

/* ---------- Main / Tabs ---------- */
main {
  margin: 0 auto;
  padding: 24px 24px 100px;
  max-width: none;  /* main 不限制宽度，由各 tab 自管 */
}
.tab-pane { display: none; }
.tab-pane.active { display: block; }

/* 建议 19：阅读 tab 沉浸（66ch 单栏）+ 单词 tab 扫描（宽 grid） */
#tab-reading {
  max-width: 100%;  /* 笔记栏存在时不限制阅读宽度，让 grid 自管 */
  margin: 0 auto;
  padding: 16px 0;
}
#tab-words {
  max-width: 1100px;  /* 单词 tab 用更宽容器，让 grid 卡片能展更多列 */
  margin: 0 auto;
  padding: 0;
}

/* 阅读区两栏布局：左阅读 + 右笔记（笔记栏默认 380px，可由用户拖拽调节 240-600px） */
.reading-layout {
  display: grid;
  grid-template-columns: minmax(0, 66ch) minmax(240px, 1fr);
  gap: 32px;
  align-items: start;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 16px;
}
.reading-content {
  min-width: 0;
  max-width: 66ch;
}
/* 笔记栏：默认 380px，可由用户拖拽右下角调节（CSS resize） */
.notes-panel {
  width: 380px;
  min-width: 240px;
  max-width: 600px;
  position: sticky;
  top: 76px;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  display: flex; flex-direction: column;
  max-height: calc(100vh - 100px);
  /* CSS 原生 resize：右下角拖拽手柄；overflow 必须不是 visible */
  resize: both;
  overflow: auto;
}
.notes-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.notes-title {
  font-family: var(--font-serif); font-size: 14px; font-weight: 600;
  color: var(--text); margin: 0;
  display: flex; align-items: center; gap: 4px;
}
.notes-title .icon { vertical-align: -2px; }
.notes-clear {
  background: transparent; border: 1px solid var(--border);
  border-radius: 6px; padding: 4px 8px;
  cursor: pointer; color: var(--text-soft);
  transition: all 0.15s;
  display: flex; align-items: center;
}
.notes-clear:hover { color: var(--prof-bad); border-color: var(--prof-bad); }
.notes-clear .icon { width: 1em; height: 1em; margin: 0; }
#notes-textarea {
  flex: 1;
  width: 100%;
  min-height: 280px;
  /* resize: both 让 textarea 也支持右下角拖拽 */
  resize: both;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 12px;
  background: var(--bg);
  color: var(--text);
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
               -apple-system, sans-serif;
  font-size: 14px;
  line-height: 1.65;
  outline: none;
  transition: border-color 0.15s;
}
#notes-textarea:focus { border-color: var(--accent); }
#notes-textarea::placeholder { color: var(--text-soft); opacity: 0.7; }
.notes-footer {
  display: flex; justify-content: space-between;
  margin-top: 8px;
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-soft);
}

/* ---------- Reading Pane ---------- */
section.paragraph { margin-bottom: 40px; }
section.paragraph .para-num {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px; color: var(--accent);
  letter-spacing: 0.04em;
  margin-bottom: 8px;
  padding: 2px 6px;
  background: var(--accent-soft);
  border-radius: 3px;
}
section.paragraph p.para-text {
  font-family: var(--font-serif);
  font-size: var(--font-base);
  line-height: var(--line-height);
  margin: 8px 0;
  color: var(--text);
}
/* 已选词：半透明背景高亮（NN/g 调研 52% 用户偏好）+ hover 时下划虚线作为次级反馈
   注意：不能用 padding（会撑开字符），改用 box-shadow 给视觉"外间距" */
section.paragraph em.word {
  font-style: normal; font-weight: inherit;
  cursor: pointer;
  background: rgba(139, 31, 18, 0.10);  /* 12% 透明 --accent */
  border-radius: 3px;
  box-shadow: 0 0 0 1px transparent;  /* 占位但不撑 layout，给视觉呼吸感 */
  transition: background 0.15s, box-shadow 0.15s;
}
section.paragraph em.word:hover {
  background: rgba(139, 31, 18, 0.20);
  box-shadow: 0 0 0 1px rgba(139, 31, 18, 0.25);
}
section.paragraph em.word.prof-熟练 { background: rgba(31, 107, 62, 0.20); }
section.paragraph em.word.prof-模糊 { background: rgba(139, 105, 20, 0.22); }
section.paragraph em.word.prof-陌生 { background: rgba(139, 26, 26, 0.20); }

/* 段落翻译折叠 */
details.para-trans { margin-top: 12px; font-size: 13px; }
details.para-trans > summary {
  list-style: none; cursor: pointer;
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 12px; color: var(--accent);
  padding: 4px 10px;
  border: 1px dashed var(--accent-soft);
  border-radius: 4px;
  user-select: none;
}
details.para-trans > summary::-webkit-details-marker { display: none; }
details.para-trans > summary::before { content: '+ '; }
details.para-trans[open] > summary::before { content: '− '; }
details.para-trans > summary:hover { background: var(--accent-soft); }
details.para-trans p.trans-text {
  /* 中文翻译：苹方/雅黑 400，字号明显比英文正文大（用户要求） */
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
               -apple-system, BlinkMacSystemFont, sans-serif;
  font-weight: 400;
  font-size: 1.3em;
  color: var(--text);
  line-height: 1.75;
  /* 与上方英文段落和下方距离都拉大，让中文翻译看起来"独立" */
  margin: 20px 0 24px;
  padding: 18px 24px;
  background: var(--bg-soft);
  border-left: 4px solid var(--accent);  /* border 加粗，让"翻译卡片"感更强 */
  border-radius: 0 8px 8px 0;
  letter-spacing: 0.01em;
}
details.para-trans p.trans-text[lang="zh-Hans-CN"] {
  font-feature-settings: "palt";
}

/* 划选高亮 span（inline 元素：margin/padding/box-shadow 都会撑开字符间距；只留背景色 + border-radius） */
.prof-highlight {
  cursor: pointer;
  border-radius: 2px;
}
.prof-highlight.prof-熟练 { background: rgba(46, 204, 113, 0.30); }
.prof-highlight.prof-模糊 { background: rgba(241, 196, 15, 0.40); }
.prof-highlight.prof-陌生 { background: rgba(231, 76, 60, 0.30); }

/* ---------- Word Pane ---------- */
.word-filter {
  display: flex; gap: 8px; flex-wrap: wrap;
  margin-bottom: 24px;
}
.word-group-title {
  font-family: var(--font-serif);
  font-size: 14px; font-weight: 600;
  color: var(--text-soft);
  margin: 24px 0 12px;
  letter-spacing: 0.02em;
}
.word-group-title:first-of-type { margin-top: 0; }

/* ---------- Empty state ---------- */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  background: var(--bg-soft);
  border: 1px dashed var(--border);
  border-radius: 12px;
  margin: 16px 0;
}
.empty-state .empty-icon { font-size: 36px; margin: 0 0 8px; opacity: 0.6; }
.empty-state .empty-title { font-family: var(--font-serif); font-size: 16px; font-weight: 600; margin: 0 0 6px; color: var(--text); }
.empty-state .empty-desc { font-size: 13px; color: var(--text-soft); margin: 0; line-height: 1.6; }
[lang="zh-Hans-CN"] .empty-state .empty-title { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; }
.word-filter .filter {
  background: var(--bg-soft); color: var(--text);
  border: 1px solid var(--border); border-radius: 18px;
  padding: 6px 14px; font-size: 13px;
  cursor: pointer; font-family: var(--font-sans);
}
.word-filter .filter:hover { background: var(--accent-soft); }
.word-filter .filter.active {
  background: var(--accent); color: #fff; border-color: var(--accent);
}
ul.word-grid {
  list-style: none; padding: 0; margin: 0;
  display: grid; gap: 8px;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}
/* 单词卡片化：边框 + 8px 圆角 + 内边距（建议 9）*/
ul.word-grid li.word-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}
ul.word-grid li.word-item:hover {
  background: var(--accent-soft); border-color: var(--accent);
}
ul.word-grid li.word-item .word-text {
  font-family: var(--font-mono); font-size: 14px; font-weight: 600;
}
ul.word-grid li.word-item .word-num {
  font-size: 10px; color: var(--text-soft);
}
/* 熟练度色块：饱和度双信号（实心色边框）+ 浅背景（建议 21） */
ul.word-grid li.word-item.prof-熟练 {
  background: rgba(31, 107, 62, 0.12); border-color: var(--prof-good); border-left-width: 3px;
}
ul.word-grid li.word-item.prof-模糊 {
  background: rgba(139, 105, 20, 0.12); border-color: var(--prof-vague); border-left-width: 3px;
}
ul.word-grid li.word-item.prof-陌生 {
  background: rgba(139, 26, 26, 0.12); border-color: var(--prof-bad); border-left-width: 3px;
}

/* ---------- Popup ---------- */
.popup {
  position: fixed;
  z-index: 100;
  background: var(--bg);
  /* Flat 2.0 风格：1px 边框 + 极轻阴影（NNG 建议 13） */
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  padding: 14px 16px;
  min-width: 240px;
  max-width: 320px;
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--text);
}
.popup.hidden { display: none; }
.popup-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.popup-word {
  font-family: var(--font-mono); font-weight: 700; font-size: 15px;
  color: var(--accent);
}
.popup-close {
  background: transparent; border: none; font-size: 18px;
  cursor: pointer; color: var(--text-soft);
  padding: 0 4px; line-height: 1;
}
.popup-close:hover { color: var(--accent); }
.popup-trans {
  font-size: 13px; line-height: 1.6; color: var(--text);
  margin-bottom: 10px;
  padding: 8px 10px;
  background: var(--bg-soft);
  border-radius: 4px;
}
.popup-trans.empty { color: var(--text-soft); font-style: italic; }
.popup-trans.hidden { display: none; }
.popup-actions { display: flex; gap: 6px; }
.popup-actions .prof-btn {
  flex: 1;
  background: var(--bg-soft); color: var(--text);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 6px 4px; font-size: 12px;
  cursor: pointer; font-family: var(--font-sans);
  transition: all 0.15s;
}
.popup-actions .prof-btn:hover { background: var(--accent-soft); }
.popup-actions .prof-btn.active-熟练 {
  background: var(--prof-good); color: #fff; border-color: var(--prof-good);
}
.popup-actions .prof-btn.active-模糊 {
  background: var(--prof-vague); color: #1a1714; border-color: var(--prof-vague);
}
.popup-actions .prof-btn.active-陌生 {
  background: var(--prof-bad); color: #fff; border-color: var(--prof-bad);
}

/* ---------- Print / Mobile ---------- */
/* ---------- 排版：列宽 66ch + 中英文字体栈分离 ---------- */
section.paragraph p.para-text { line-height: var(--line-height); }
details.para-trans p.trans-text { line-height: 1.7; }

/* CLReq 推荐：中英文字体按 lang 拆分 */
:lang(zh) {
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
               -apple-system, sans-serif;
}

/* ---------- prefers-reduced-motion：fade-only（默认就只 fade，不加 scale） ---------- */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 1ms !important;
    transition-duration: 1ms !important;
  }
}

/* ---------- sr-only：视觉隐藏但屏幕阅读器可见 ---------- */
.sr-only {
  position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
}

/* ---------- SVG 图标：统一 stroke-based + 跟随 currentColor ---------- */
.icon {
  width: 1.1em;
  height: 1.1em;
  display: inline-block;
  vertical-align: -2px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
  margin-right: 4px;
}
.icon-lg { width: 36px; height: 36px; margin: 0; stroke-width: 1.4; opacity: 0.6; }
/* 熟练度圆点：固定熟练度色，不跟随 currentColor（用户应该一眼看出语义） */
.icon-dot { width: 1em; height: 1em; display: inline-block; vertical-align: -2px; margin-right: 3px; }
.icon-dot.icon-good { fill: var(--prof-good); }
.icon-dot.icon-vague { fill: var(--prof-vague); }
.icon-dot.icon-bad { fill: var(--prof-bad); }
.tab .icon { margin-right: 5px; }
.word-group-title .icon { margin-right: 6px; vertical-align: -3px; }

/* ---------- Help Popup ---------- */
.help-popup { min-width: 320px; max-width: 420px; }
.help-popup .help-list {
  list-style: none; padding: 0; margin: 0;
  display: grid; gap: 6px; font-size: 13px;
}
.help-popup kbd {
  display: inline-block;
  background: var(--bg-soft); color: var(--text);
  border: 1px solid var(--border); border-radius: 3px;
  padding: 1px 6px; font-family: var(--font-mono); font-size: 11px;
  margin: 0 2px;
}
.help-popup .popup-word { font-size: 14px; font-weight: 600; }

/* ---------- 熟练度按钮：四重编码（颜色 + emoji + 文字 + 数字键） ---------- */
.popup-actions .prof-btn { display: flex; align-items: center; justify-content: center; gap: 3px; }
.popup-actions .prof-btn .prof-key {
  font-family: var(--font-mono); font-size: 10px;
  opacity: 0.6; margin-left: 2px;
}
.popup-actions .prof-btn .prof-label { font-size: 11px; }

/* ---------- Print ---------- */
@media print {
  header.page-header, .popup, .word-filter { display: none; }
  main { max-width: none; padding: 0; }
  section.paragraph { page-break-inside: avoid; }
  ul.word-grid { grid-template-columns: repeat(3, 1fr); }
  section.paragraph em.word { text-decoration: none; }
}
@media (max-width: 900px) {
  /* 窄屏：阅读区单列，笔记栏折叠到底部（不再 side-by-side） */
  .reading-layout {
    grid-template-columns: 1fr;
    gap: 24px;
    padding: 0;
  }
  .reading-content { max-width: none; }
  .notes-panel {
    position: static;  /* 不再 sticky，避免占据 viewport */
    max-height: none;
  }
}
@media (max-width: 640px) {
  header.page-header { padding: 10px 14px; }
  main { padding: 16px; }
  .title-meta .title { max-width: 180px; font-size: 14px; }
  .toolbar select, .toolbar button { padding: 5px 8px; font-size: 12px; }
}
"""


# ---------------------------------------------------------------------------
# JS (placeholder — replaced by Edit below)
# ---------------------------------------------------------------------------

JS_PLACEHOLDER = r"""
(function() {
  'use strict';
  const DATA = window.__MEMO_DATA__;
  const DATE = DATA.date;
  const STORAGE_KEY = 'memo-proficiency-' + DATE;
  const LEVELS = ['熟练', '模糊', '陌生'];

  // ---- CSS attribute escape (for selectors) ----
  function cssEscape(s) {
    return String(s).replace(/(["\\\[\]\(\)\{\}\:\;\.\,\#\@\&\=\?\!\+\*\/\%\^\$\|])/g, '\\$1');
  }

  // ---- Proficiency storage ----
  function loadProf() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch (e) { return {}; }
  }
  function saveProf(p) { localStorage.setItem(STORAGE_KEY, JSON.stringify(p)); }
  function getProf(word) {
    return loadProf()[String(word).toLowerCase()] || null;
  }
  function setProf(word, level) {
    const p = loadProf();
    const w = String(word).toLowerCase();
    if (!level || p[w] === level) { delete p[w]; }
    else { p[w] = level; }
    saveProf(p);
    applyProficiency(w, p[w] || null);
    updateCounts();
    if (currentFilter() !== 'all') refreshWordList();
  }
  function clearAllProf() {
    if (!confirm('确认清空今日所有熟练度标注？此操作不可撤销。')) return;
    localStorage.removeItem(STORAGE_KEY);
    document.querySelectorAll('.prof-熟练, .prof-模糊, .prof-陌生').forEach(el => {
      el.classList.remove('prof-熟练', 'prof-模糊', 'prof-陌生');
    });
    updateCounts();
    refreshWordList();
  }
  window.clearAllProficiency = clearAllProf;

  // ---- Apply proficiency to all visual elements of a word ----
  function applyProficiency(word, level) {
    const sel = cssEscape(word);
    const lvls = ['prof-熟练', 'prof-模糊', 'prof-陌生'];
    const targets = [
      `em.word[data-word="${sel}"]`,
      `span.prof-highlight[data-word="${sel}"]`,
      `li.word-item[data-word="${sel}"]`,
    ];
    targets.forEach(s => {
      document.querySelectorAll(s).forEach(el => {
        el.classList.remove('prof-熟练', 'prof-模糊', 'prof-陌生');
        if (level) el.classList.add('prof-' + level);
      });
    });
  }

  // ---- Counts (for filter buttons) ----
  function updateCounts() {
    const p = loadProf();
    let good = 0, vague = 0, bad = 0;
    Object.values(p).forEach(v => {
      if (v === '熟练') good++;
      else if (v === '模糊') vague++;
      else if (v === '陌生') bad++;
    });
    const allInList = new Set([
      ...DATA.main_words.map(w => w.toLowerCase()),
      ...DATA.supporting_words.map(w => w.toLowerCase()),
    ]);
    const extraCount = Object.keys(p).filter(w => !allInList.has(w)).length;
    const total = DATA.main_words.length + DATA.supporting_words.length + extraCount;
    const btn = (sel, txt) => {
      const b = document.querySelector(sel);
      if (b) b.textContent = txt;
    };
    btn('[data-filter="all"]', `全部 (${total})`);
    btn('[data-filter="陌生"]', `陌生 (${bad})`);
    btn('[data-filter="模糊"]', `模糊 (${vague})`);
    btn('[data-filter="熟练"]', `熟练 (${good})`);
    const ec = document.getElementById('extra-count');
    if (ec) ec.textContent = extraCount;
  }

  // ---- Extra words (用户在原文里划过但不在 55 词里的) ----
  function renderExtraWords() {
    const p = loadProf();
    const allInList = new Set([
      ...DATA.main_words.map(w => w.toLowerCase()),
      ...DATA.supporting_words.map(w => w.toLowerCase()),
    ]);
    const extras = Object.keys(p)
      .filter(w => !allInList.has(w))
      .sort();
    const ul = document.getElementById('extra-words');
    if (!ul) return;
    ul.innerHTML = extras.map(w => {
      const lv = p[w];
      const lvClass = lv ? ' prof-' + lv : '';
      return `<li class="word-item${lvClass}" data-word="${w}" data-extra="1">`
           + `<span class="word-text">${w}</span>`
           + `<span class="word-num">+</span>`
           + `</li>`;
    }).join('');
    // Empty state 显隐
    const emptyExtra = document.getElementById('empty-extra');
    if (emptyExtra) emptyExtra.hidden = extras.length > 0;
  }

  // ---- Popup ----
  const popup = document.getElementById('word-popup');
  let popupWord = null;
  let popupOpenedAt = 0;  // popup 刚打开的时间戳，期间点击不关闭
  let popupTriggerEl = null;  // W3C APG: 关闭时焦点还原到触发元素

  function showPopup(word, x, y, withTranslation) {
    popupWord = String(word).toLowerCase();
    popup.querySelector('.popup-word').textContent = popupWord;
    const transEl = popup.querySelector('.popup-trans');
    if (withTranslation) {
      const trans = DATA.word_translations[popupWord] || '';
      if (trans) {
        transEl.textContent = trans;
        transEl.classList.remove('empty', 'hidden');
      } else {
        transEl.textContent = '(暂无翻译)';
        transEl.classList.add('empty');
        transEl.classList.remove('hidden');
      }
    } else {
      // 划词弹窗：不显示翻译区
      transEl.textContent = '';
      transEl.classList.add('hidden');
      transEl.classList.remove('empty');
    }
    const cur = getProf(popupWord);
    popup.querySelectorAll('.prof-btn').forEach(b => {
      const active = b.dataset.level === cur;
      b.classList.toggle('active-' + b.dataset.level, active);
      b.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
    popup.classList.remove('hidden');
    popupOpenedAt = Date.now();
    positionPopup(x, y);
  }

  function positionPopup(x, y) {
    const rect = popup.getBoundingClientRect();
    const vw = window.innerWidth, vh = window.innerHeight;
    let px = x + 8, py = y + 8;
    if (px + rect.width > vw - 8) px = vw - rect.width - 8;
    if (py + rect.height > vh - 8) py = vh - rect.height - 8;
    if (px < 8) px = 8;
    if (py < 8) py = 8;
    popup.style.left = px + 'px';
    popup.style.top = py + 'px';
  }

  function closePopup() {
    popup.classList.add('hidden');
    const wasOpen = popupWord;
    popupWord = null;
    // W3C APG: 关闭时焦点还原到触发元素
    if (popupTriggerEl) {
      try { popupTriggerEl.focus({ preventScroll: false }); } catch (e) {}
      popupTriggerEl = null;
    }
    return wasOpen;
  }
  window.closePopup = closePopup;

  // aria-live 提示保存状态
  function announce(msg) {
    const el = document.getElementById('sr-status');
    if (el) el.textContent = msg;
  }

  popup.querySelectorAll('.prof-btn').forEach(b => {
    b.addEventListener('click', () => {
      if (!popupWord) return;
      const level = b.dataset.level;
      const cur = getProf(popupWord);
      setProf(popupWord, cur === level ? null : level);
      const after = getProf(popupWord);
      popup.querySelectorAll('.prof-btn').forEach(x => {
        const active = x.dataset.level === after;
        x.classList.toggle('active-' + x.dataset.level, active);
        x.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      announce(after ? `${popupWord} 标为 ${after}` : `已取消 ${popupWord} 的熟练度`);
    });
  });

  // ---- Click 事件委托：prof-highlight / em.word / li.word-item 统一在 document 上处理 ----
  // （prof-highlight 是 wrap 时动态创建的，无法在创建时预先绑定 click，用事件委托解决）
  document.addEventListener('click', (e) => {
    // 1) 点击 prof-highlight（划过的词）
    const span = e.target.closest('span.prof-highlight');
    if (span) {
      e.stopPropagation();
      popupTriggerEl = span;
      const inEmWord = !!span.closest('em.word');
      // em.word 内的 prof-highlight → 显示翻译；普通位置的 → 只弹熟练度
      showPopup(span.dataset.word, e.clientX, e.clientY, inEmWord);
      return;
    }
    // 2) 点击 em.word（入选词，未划过的部分）
    const em = e.target.closest('em.word');
    if (em) {
      e.stopPropagation();
      popupTriggerEl = em;
      showPopup(em.dataset.word, e.clientX, e.clientY, true);
      return;
    }
    // 3) 点击 li.word-item（单词页）
    const li = e.target.closest('li.word-item');
    if (li) {
      e.stopPropagation();
      popupTriggerEl = li;
      const rect = li.getBoundingClientRect();
      showPopup(li.dataset.word, rect.left, rect.top, true);
      return;
    }
    // 4) 其他区域：关闭 popup（mouseup 弹窗有 200ms 保护期）
    if (Date.now() - popupOpenedAt < 200) return;
    closePopup();
  });

  // ---- Selection (划选任意单词 → 标熟练度 + 荧光笔) ----
  // 用 TreeWalker 遍历 range 内的 textNode，逐个 splitText+包裹，
  // 避免 extractContents + insertNode 在跨元素（em.word 边界）时把 startContainer 移到 fragment 导致插入位置错乱
  function wrapSelectionAsHighlight(range, text) {
    const commonAncestor = range.commonAncestorContainer;
    const block = commonAncestor.nodeType === 1 ? commonAncestor : commonAncestor.parentElement;
    if (!block) return false;
    if (block.closest('.popup, header, .word-filter, .word-grid, .para-num, .para-trans')) return false;
    if (!block.closest('p.para-text')) return false;

    // 收集 range 内所有 textNode
    const textNodes = [];
    // Chrome 怪癖：TreeWalker 从 textNode 开始时 nextNode 不返回 textNode 自身
    if (commonAncestor.nodeType === 3 && range.intersectsNode(commonAncestor)) {
      textNodes.push(commonAncestor);
    }
    const walker = document.createTreeWalker(
      commonAncestor,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          return range.intersectsNode(node) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
        }
      }
    );
    let n;
    while ((n = walker.nextNode())) textNodes.push(n);
    if (textNodes.length === 0) return false;

    const wordLower = text.toLowerCase();
    const cur = getProf(text);

    // 从后往前处理（避免 splitText 改变 textNode 顺序导致索引错乱）
    for (let i = textNodes.length - 1; i >= 0; i--) {
      const tn = textNodes[i];
      const isStart = (tn === range.startContainer);
      const isEnd = (tn === range.endContainer);
      let startOff = isStart ? range.startOffset : 0;
      let endOff = isEnd ? range.endOffset : tn.nodeValue.length;

      if (startOff >= endOff) continue;

      // 拆分：把 [startOff, endOff) 段包成 span
      const span = document.createElement('span');
      span.className = 'prof-highlight';
      span.dataset.word = wordLower;
      if (cur) span.classList.add('prof-' + cur);

      let middle = tn;
      if (endOff < tn.nodeValue.length) {
        tn.splitText(endOff);   // 后段拆出
      }
      if (startOff > 0) {
        middle = tn.splitText(startOff);  // 前段拆出，留下 middle = [startOff, endOff)
      }
      // middle 现在是 [startOff, endOff) 段
      middle.parentNode.insertBefore(span, middle);
      span.appendChild(middle);
    }
    return true;
  }

  document.addEventListener('mouseup', (e) => {
    // 阻止 click 事件随后关闭刚弹出的 popup（mouseup → click 顺序）
    if (popup.contains(e.target)) return;
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    const text = sel.toString().trim();
    if (!text) return;
    if (/\s/.test(text)) return;        // 必须单词（无空格）
    if (/[^a-zA-Z\-']/i.test(text)) return;  // 仅字母
    if (text.length > 30) return;
    const range = sel.getRangeAt(0);
    const wrapped = wrapSelectionAsHighlight(range, text);
    if (!wrapped) { sel.removeAllRanges(); return; }
    sel.removeAllRanges();
    e.stopPropagation();   // 阻止 click handler 关闭 popup
    e.preventDefault();
    showPopup(text, e.clientX, e.clientY, false);  // fixed 定位用 viewport 坐标
  });

  // 点击其他地方关闭 popup（mouseup 触发的弹窗有 200ms 保护期，防 click 立即关闭）
  document.addEventListener('click', (e) => {
    if (Date.now() - popupOpenedAt < 200) return;
    if (!popup.contains(e.target) && !e.target.closest('em.word, li.word-item')) {
      closePopup();
    }
  });

  // ---- Tabs ----
  document.querySelectorAll('nav.tabs .tab').forEach(t => {
    t.addEventListener('click', () => {
      const name = t.dataset.tab;
      document.querySelectorAll('nav.tabs .tab').forEach(x => x.classList.toggle('active', x === t));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === 'tab-' + name));
      closePopup();
    });
  });

  // ---- Word filter ----
  function currentFilter() {
    const a = document.querySelector('.word-filter .filter.active');
    return a ? a.dataset.filter : 'all';
  }
  function refreshWordList() {
    const filter = currentFilter();
    const p = loadProf();
    let visible = 0;
    // 主列表
    document.querySelectorAll('#word-list li.word-item').forEach(li => {
      const w = li.dataset.word;
      const show = (filter === 'all' || p[w] === filter);
      li.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    // 额外划过的词也要按 filter 过滤
    document.querySelectorAll('#extra-words li.word-item').forEach(li => {
      const w = li.dataset.word;
      const show = (filter === 'all' || p[w] === filter);
      li.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    // 主列表空状态
    const emptyAll = document.getElementById('empty-all');
    if (emptyAll) {
      if (visible === 0 && filter !== 'all') {
        emptyAll.hidden = false;
        emptyAll.querySelector('.empty-title').textContent = `没有${filter}的词`;
        emptyAll.querySelector('.empty-desc').textContent = `试试切换筛选，或者去阅读页标一些单词。`;
      } else if (visible === 0 && filter === 'all') {
        emptyAll.hidden = false;
        emptyAll.querySelector('.empty-title').textContent = '今日还没有单词';
        emptyAll.querySelector('.empty-desc').textContent = '在阅读页点击红色背景的入选词开始标记。';
      } else {
        emptyAll.hidden = true;
      }
    }
  }
  document.querySelectorAll('.word-filter .filter').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('.word-filter .filter').forEach(x => x.classList.toggle('active', x === b));
      refreshWordList();
    });
  });

  // ---- Theme / Font / Line ----
  function toggleTheme() {
    const html = document.documentElement;
    const cur = html.getAttribute('data-theme') || 'light';
    const next = cur === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('memo-theme', next);
    document.getElementById('theme-btn').innerHTML = next === 'light'
      ? '<svg class="icon" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 0 1 6.707 2.707a8.001 8.001 0 1 0 10.586 10.586z"/></svg>'
      : '<svg class="icon" viewBox="0 0 20 20"><circle cx="10" cy="10" r="3"/><path d="M10 1v2m0 14v2M1 10h2m14 0h2M4.2 4.2l1.4 1.4m8.8 8.8l1.4 1.4M4.2 15.8l1.4-1.4m8.8-8.8l1.4-1.4"/></svg>';
  }
  window.toggleTheme = toggleTheme;
  function setFontSize(size) {
    document.documentElement.style.setProperty('--font-base', size);
    localStorage.setItem('memo-font', size);
  }
  window.setFontSize = setFontSize;
  function setLineHeight(lh) {
    document.documentElement.style.setProperty('--line-height', lh);
    localStorage.setItem('memo-line', lh);
  }
  window.setLineHeight = setLineHeight;

  // ---- 笔记栏：localStorage 持久化 + 自动保存 ----
  const NOTES_KEY = 'memo-notes-' + DATE;
  const notesTa = document.getElementById('notes-textarea');
  const notesStats = document.getElementById('notes-stats');

  function loadNotes() {
    if (!notesTa) return;
    try {
      notesTa.value = localStorage.getItem(NOTES_KEY) || '';
    } catch (e) {
      notesTa.value = '';
    }
    updateNotesStats();
  }

  function saveNotes() {
    if (!notesTa) return;
    try {
      localStorage.setItem(NOTES_KEY, notesTa.value);
    } catch (e) {
      console.warn('笔记保存失败', e);
    }
  }

  function updateNotesStats() {
    if (!notesTa || !notesStats) return;
    const len = notesTa.value.length;
    notesStats.textContent = `${len} 字`;
  }

  function clearNotes() {
    if (!notesTa) return;
    if (!confirm('确认清空今日笔记？此操作不可撤销。')) return;
    notesTa.value = '';
    saveNotes();
    updateNotesStats();
    notesTa.focus();
    announce('已清空今日笔记');
  }
  window.clearNotes = clearNotes;

  // 自动保存（input 事件 + 500ms 防抖）
  if (notesTa) {
    let saveTimer = null;
    notesTa.addEventListener('input', () => {
      updateNotesStats();
      clearTimeout(saveTimer);
      saveTimer = setTimeout(saveNotes, 500);
    });
    // 失焦立即保存（不等待 500ms）
    notesTa.addEventListener('blur', () => {
      clearTimeout(saveTimer);
      saveNotes();
    });
    // Ctrl+Enter 不提交，只是换行（textarea 默认行为，无需拦截）
    // Esc 关闭弹窗时会 blur textarea，不影响
  }

  // ---- Help popup ----
  const helpPopup = document.getElementById('help-popup');
  function showHelp() {
    helpPopup.classList.remove('hidden');
    popupOpenedAt = Date.now();
    // 居中
    const vw = window.innerWidth, vh = window.innerHeight;
    const rect = helpPopup.getBoundingClientRect();
    helpPopup.style.left = Math.max(8, (vw - rect.width) / 2) + 'px';
    helpPopup.style.top = Math.max(8, (vh - rect.height) / 3) + 'px';
  }
  function closeHelp() { helpPopup.classList.add('hidden'); }
  window.showHelp = showHelp;
  window.closeHelp = closeHelp;

  // ---- 键盘快捷键（Anki/Maimemo/LingQ/ReadLang 全支持） ----
  // 1/2/3 = 标熟练度；Esc = 关弹窗（focus 还原）；? = 帮助
  document.addEventListener('keydown', (e) => {
    // 用户在输入框里时不拦截
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    // Esc：关弹窗或帮助
    if (e.key === 'Escape') {
      if (!helpPopup.classList.contains('hidden')) { closeHelp(); e.preventDefault(); return; }
      if (!popup.classList.contains('hidden')) { closePopup(); e.preventDefault(); return; }
    }
    // ?：显示/隐藏帮助（Shift+/ 也算）
    if (e.key === '?' || (e.shiftKey && e.key === '/')) {
      e.preventDefault();
      if (helpPopup.classList.contains('hidden')) showHelp();
      else closeHelp();
      return;
    }

    // 弹窗打开时的快捷键：1/2/3 标熟练度
    if (!popup.classList.contains('hidden') && popupWord) {
      const keyMap = { '1': '陌生', '2': '模糊', '3': '熟练' };
      const level = keyMap[e.key];
      if (level) {
        e.preventDefault();
        const cur = getProf(popupWord);
        setProf(popupWord, cur === level ? null : level);
        const after = getProf(popupWord);
        popup.querySelectorAll('.prof-btn').forEach(x => {
          const active = x.dataset.level === after;
          x.classList.toggle('active-' + x.dataset.level, active);
          x.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
        announce(after ? `${popupWord} 标为 ${after}` : `已取消 ${popupWord} 的熟练度`);
        return;
      }
    }
  });

  // ---- Init ----
  document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('memo-theme');
    if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme);
      document.getElementById('theme-btn').innerHTML = savedTheme === 'light'
      ? '<svg class="icon" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 0 1 6.707 2.707a8.001 8.001 0 1 0 10.586 10.586z"/></svg>'
      : '<svg class="icon" viewBox="0 0 20 20"><circle cx="10" cy="10" r="3"/><path d="M10 1v2m0 14v2M1 10h2m14 0h2M4.2 4.2l1.4 1.4m8.8 8.8l1.4 1.4M4.2 15.8l1.4-1.4m8.8-8.8l1.4-1.4"/></svg>';
    }
    const savedFont = localStorage.getItem('memo-font');
    if (savedFont) {
      document.documentElement.style.setProperty('--font-base', savedFont);
      document.getElementById('font-sel').value = savedFont;
    }
    const savedLine = localStorage.getItem('memo-line');
    if (savedLine) {
      document.documentElement.style.setProperty('--line-height', savedLine);
      const sel = document.getElementById('line-sel');
      if (sel) sel.value = savedLine;
    }
    const p = loadProf();
    Object.entries(p).forEach(([w, lv]) => applyProficiency(w, lv));
    renderExtraWords();
    updateCounts();
    loadNotes();  /* 加载今日笔记 */
  });
})();
"""


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------

def render_paragraph(pid: int, total: int, html: str, trans: str) -> str:
    trans_block = ""
    if trans:
        trans_block = (
            f'<details class="para-trans">\n'
            f'  <summary>显示中文翻译</summary>\n'
            f'  <p class="trans-text">{trans}</p>\n'
            f'</details>'
        )
    return (
        f'<section class="paragraph" id="para-{pid}">\n'
        f'  <span class="para-num">P{pid}</span>\n'
        f'  <p class="para-text">{html}</p>\n'
        f'  {trans_block}\n'
        f'</section>'
    )


def render_word_item(idx: int, w: str) -> str:
    return (
        f'<li class="word-item" data-word="{w}" data-idx="{idx}">'
        f'<span class="word-text">{w}</span>'
        f'<span class="word-num">#{idx}</span>'
        f'</li>'
    )


def render(meta: dict, paragraphs: list[str], translations: list[str],
           annotations: dict) -> str:
    main_words = meta["main_words"]
    supp_words = meta.get("supporting_words", [])
    all_words = main_words + supp_words

    total_para = len(paragraphs)
    paragraphs_html = "\n".join(
        render_paragraph(i + 1, total_para, p,
                         translations[i] if i < len(translations) else "")
        for i, p in enumerate(paragraphs)
    )

    # 单词合并渲染（不分主支线）
    word_list_html = "\n".join(
        render_word_item(i + 1, w) for i, w in enumerate(all_words)
    )

    # 内嵌数据供 JS 使用（避免二次 JSON 解析）
    data_json = json.dumps({
        "date": meta["date"],
        "title": meta.get("title", ""),
        "mode": meta.get("mode", ""),
        "main_words": main_words,
        "supporting_words": supp_words,
        "word_translations": annotations.get("word_translations", {}),
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta['date']} · {meta.get('title', '今日精读')}</title>
<style>{CSS_PLACEHOLDER}</style>
</head>
<body>

<header class="page-header">
  <nav class="tabs" role="tablist" aria-label="主导航">
    <button class="tab active" role="tab" aria-selected="true" data-tab="reading" id="tab-btn-reading" aria-controls="tab-reading"><svg class="icon" viewBox="0 0 20 20"><path d="M2 4.5A1.5 1.5 0 0 1 3.5 3H6v14H3.5A1.5 1.5 0 0 1 2 15.5v-11zM18 4.5A1.5 1.5 0 0 0 16.5 3H14v14h2.5a1.5 1.5 0 0 0 1.5-1.5v-11z"/></svg> 阅读</button>
    <button class="tab" role="tab" aria-selected="false" data-tab="words" id="tab-btn-words" aria-controls="tab-words" tabindex="-1"><svg class="icon" viewBox="0 0 20 20"><path d="M3 3h6v14H2z"/><path d="M11 3h7v14h-7z"/></svg> 今日单词</button>
  </nav>
  <div class="title-meta">
    <span class="title">{meta.get('title', '')}</span>
    <span class="date">{meta['date']}</span>
  </div>
  <div class="toolbar">
    <select id="font-sel" onchange="setFontSize(this.value)" title="字号" aria-label="字号">
      <option value="16px">小字</option>
      <option value="18px" selected>中字</option>
      <option value="20px">大字</option>
      <option value="22px">超大</option>
    </select>
    <select id="line-sel" onchange="setLineHeight(this.value)" title="行高" aria-label="行高">
      <option value="1.5">紧凑</option>
      <option value="1.6" selected>适中</option>
      <option value="1.7">宽松</option>
    </select>
    <button id="theme-btn" onclick="toggleTheme()" title="主题切换（暗/亮）" aria-label="切换主题"><svg class="icon" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 0 1 6.707 2.707a8.001 8.001 0 1 0 10.586 10.586z"/></svg></button>
    <button onclick="clearAllProficiency()" title="清空熟练度" aria-label="清空今日熟练度"><svg class="icon" viewBox="0 0 20 20"><path d="M5 6h10M8 6V4h4v2m1 0v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6h8z"/></svg></button>
    <button onclick="window.print()" title="导出 PDF" aria-label="导出 PDF"><svg class="icon" viewBox="0 0 20 20"><path d="M6 8V3h8v5M4 8h12v6h-3v2H7v-2H4V8z"/><path d="M8 11h4"/></svg></button>
    <button onclick="showHelp()" title="快捷键帮助" aria-label="快捷键帮助">?</button>
  </div>
</header>

<main>
  <section id="tab-reading" class="tab-pane active" role="tabpanel" aria-labelledby="tab-btn-reading">
    <div class="reading-layout">
      <div class="reading-content">
{paragraphs_html}
      </div>
      <aside class="notes-panel" aria-label="笔记栏">
        <div class="notes-header">
          <h2 class="notes-title">
            <svg class="icon" viewBox="0 0 20 20"><path d="M3 4h11l3 3v9a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/><path d="M14 4v3h3M6 10h6M6 13h4"/></svg>
            <span>今日笔记</span>
          </h2>
          <button class="notes-clear" onclick="clearNotes()" aria-label="清空笔记" title="清空笔记">
            <svg class="icon" viewBox="0 0 20 20"><path d="M5 6h10M8 6V4h4v2m1 0v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6h8z"/></svg>
          </button>
        </div>
        <textarea id="notes-textarea"
                  placeholder="随手记下想法的、生词用法、阅读灵感…&#10;&#10;（自动保存到 localStorage）"
                  aria-label="笔记内容"></textarea>
        <div class="notes-footer">
          <span id="notes-stats" class="notes-stats">0 字</span>
          <span class="notes-date">{meta['date']}</span>
        </div>
      </aside>
    </div>
  </section>
  <section id="tab-words" class="tab-pane" role="tabpanel" aria-labelledby="tab-btn-words">
    <div class="word-filter" role="tablist" aria-label="按熟练度筛选">
      <button class="filter active" role="tab" aria-selected="true" data-filter="all" aria-controls="word-list">全部 (0)</button>
      <button class="filter" role="tab" aria-selected="false" data-filter="陌生" aria-controls="word-list" tabindex="-1">陌生 (0)</button>
      <button class="filter" role="tab" aria-selected="false" data-filter="模糊" aria-controls="word-list" tabindex="-1">模糊 (0)</button>
      <button class="filter" role="tab" aria-selected="false" data-filter="熟练" aria-controls="word-list" tabindex="-1">熟练 (0)</button>
    </div>
    <ul class="word-grid" data-group="all" id="word-list">{word_list_html}</ul>
    <div class="empty-state" id="empty-all" hidden>
      <p class="empty-icon"><svg class="icon icon-lg" viewBox="0 0 20 20"><path d="M2 4.5A1.5 1.5 0 0 1 3.5 3H6v14H3.5A1.5 1.5 0 0 1 2 15.5v-11zM18 4.5A1.5 1.5 0 0 0 16.5 3H14v14h2.5a1.5 1.5 0 0 0 1.5-1.5v-11z"/></svg></p>
      <p class="empty-title">还没有标过单词</p>
      <p class="empty-desc">点击文中红色背景的词标熟练度，或拖选任意单词划线标记。</p>
    </div>
    <h3 class="word-group-title"><svg class="icon" viewBox="0 0 20 20"><path d="M10 4v12M4 10h12"/></svg> 额外划过的词 (<span id="extra-count">0</span>)</h3>
    <ul class="word-grid" data-group="extra" id="extra-words"><!-- JS 填充 --></ul>
    <div class="empty-state" id="empty-extra" hidden>
      <p class="empty-icon"><svg class="icon icon-lg" viewBox="0 0 20 20"><path d="M14.586 3.414a2 2 0 0 1 2.828 0l1.172 1.172a2 2 0 0 1 0 2.828L8 16H4v-4l10.586-8.586z"/></svg></p>
      <p class="empty-title">还没有额外划词</p>
      <p class="empty-desc">在阅读页用鼠标选中任意单词即可划线标记。</p>
    </div>
  </section>
</main>

<div id="word-popup" class="popup hidden" role="dialog" aria-label="单词熟练度" aria-describedby="popup-trans">
  <div class="popup-header">
    <span class="popup-word" id="popup-word-label"></span>
    <button class="popup-close" onclick="closePopup()" aria-label="关闭">×</button>
  </div>
  <div class="popup-trans" id="popup-trans"></div>
  <div class="popup-actions" role="group" aria-label="熟练度">
    <button class="prof-btn" data-level="熟练" aria-label="熟练（按 1 键）" aria-pressed="false"><svg class="icon-dot icon-good" viewBox="0 0 20 20"><circle cx="10" cy="10" r="5"/></svg><span class="prof-label">熟练</span><span class="prof-key">1</span></button>
    <button class="prof-btn" data-level="模糊" aria-label="模糊（按 2 键）" aria-pressed="false"><svg class="icon-dot icon-vague" viewBox="0 0 20 20"><circle cx="10" cy="10" r="5"/></svg><span class="prof-label">模糊</span><span class="prof-key">2</span></button>
    <button class="prof-btn" data-level="陌生" aria-label="陌生（按 3 键）" aria-pressed="false"><svg class="icon-dot icon-bad" viewBox="0 0 20 20"><circle cx="10" cy="10" r="5"/></svg><span class="prof-label">陌生</span><span class="prof-key">3</span></button>
  </div>
</div>

<!-- 帮助弹窗 -->
<div id="help-popup" class="popup hidden help-popup" role="dialog" aria-label="快捷键帮助">
  <div class="popup-header">
    <span class="popup-word"><svg class="icon" viewBox="0 0 20 20"><rect x="2" y="6" width="16" height="9" rx="1"/><path d="M6 9h1m2 0h1m2 0h1m2 0h1M6 12h1m2 0h1m2 0h1m2 0h1M5 12h6"/></svg> 快捷键</span>
    <button class="popup-close" onclick="closeHelp()" aria-label="关闭">×</button>
  </div>
  <ul class="help-list">
    <li><kbd>1</kbd> / <kbd>2</kbd> / <kbd>3</kbd> 标熟练度（陌生/模糊/熟练）</li>
    <li><kbd>Esc</kbd> 关闭弹窗，焦点还原</li>
    <li><kbd>?</kbd> / <kbd>Shift</kbd>+<kbd>/</kbd> 显示/隐藏此帮助</li>
    <li><kbd>j</kbd> / <kbd>k</kbd> 下一个/上一个入选词</li>
    <li><kbd>n</kbd> / <kbd>p</kbd> 下一段/上一段</li>
    <li><kbd>Tab</kbd> 焦点移到下一个单词</li>
  </ul>
</div>

<!-- aria-live 提示保存 -->
<div id="sr-status" role="status" aria-live="polite" class="sr-only"></div>

<script>window.__MEMO_DATA__ = {data_json};</script>
<script>{JS_PLACEHOLDER}</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Render memo-context daily HTML")
    parser.add_argument("--date", default=date.today().isoformat(),
                        help="日期 (YYYY-MM-DD)，默认今天")
    parser.add_argument("--dir", type=Path, default=None,
                        help="覆盖默认 contexts/<date>/ 目录")
    args = parser.parse_args()

    base = args.dir or (CONTEXTS_DIR / args.date)
    article_md = base / "article.md"
    annotations_json = base / "annotations.json"
    out_html = base / "page.html"

    if not article_md.exists():
        print(f"❌ 缺 {article_md}（Step 3 产出）", file=sys.stderr)
        return 1
    if not annotations_json.exists():
        print(f"❌ 缺 {annotations_json}（Step 3 产出）", file=sys.stderr)
        return 1

    md_text = article_md.read_text(encoding="utf-8")
    annotations = json.loads(annotations_json.read_text(encoding="utf-8"))

    paragraphs, translations = parse_passage_and_translation(md_text)
    if not paragraphs:
        print(f"❌ {article_md} 没解析到段落（确认有 '## 文字稿' 部分）", file=sys.stderr)
        return 1

    # Word list fallback: 从段落 *word* 抓
    main_words = annotations.get("main_words", [])
    supp_words = annotations.get("supporting_words", [])
    if not main_words:
        found = set()
        for p in paragraphs:
            for m in EM_PATTERN.finditer(p):
                found.add(m.group(1))
        main_words = sorted(found)
        annotations["main_words"] = main_words
        print(f"⚠️  annotations.json 缺 main_words，从 article.md 抽出 {len(found)} 个词", file=sys.stderr)

    meta = {
        "date": args.date,
        "mode": annotations.get("mode", "A"),
        "title": annotations.get("title", "(无标题)"),
        "main_words": main_words,
        "supporting_words": supp_words,
    }

    html = render(meta, paragraphs, translations, annotations)

    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    size_kb = out_html.stat().st_size / 1024
    print(f"✅ {out_html} ({size_kb:.1f} KB)")
    print(f"   paragraphs: {len(paragraphs)} | translations: {len(translations)} | words: {len(main_words) + len(supp_words)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())