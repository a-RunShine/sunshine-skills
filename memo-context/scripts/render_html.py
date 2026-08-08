#!/usr/bin/env python3
"""Render memo-context daily page.html from article.md + annotations.json.

Inputs (in contexts/YYYY-MM-DD/):
    article.md          — Step 3 产出的文字稿，含 *word* 重点词标记
    annotations.json    — Step 5.5 产出的混合派标注

Output:
    contexts/YYYY-MM-DD/page.html  — 单页 HTML（双侧边栏 + 暗色模式 + 顶部 banner）

Usage:
    python3 scripts/render_html.py                    # 用今天日期
    python3 scripts/render_html.py --date 2026-08-04  # 指定日期
    python3 scripts/render_html.py --dir contexts/2026-08-04  # 指定目录
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# Project root: <project>/.claude/skills/memo-context/scripts/render_html.py
#   → <project> = 5 levels up from __file__
SKILL_DIR = Path(__file__).resolve().parent.parent      # memo-context/
PROJECT_ROOT = SKILL_DIR.parent.parent.parent           # 墨墨记单词/
CONTEXTS_DIR = PROJECT_ROOT / "contexts"


# ---------------------------------------------------------------------------
# Markdown / inline parser
# ---------------------------------------------------------------------------

# Match *word* but not **bold** and not \*literal\*
EM_PATTERN = re.compile(r"(?<!\*)\*([^*\s]+?)\*(?!\*)")
# Sentence-emphasis: "Presumably" -> "presumably" for word-list jump
WORD_LOWER = str.lower


def parse_paragraphs(md_text: str) -> list[str]:
    """Extract Passage paragraphs and convert *word* to <em>word</em>.

    Strategy:
    1. If '## Passage' section exists, use only that range (D 模式)
    2. Otherwise, split whole doc by blank lines and skip non-passage
       (headers / question formats / answer formats)
    """
    # 1) Try ## Passage section
    passage_match = re.search(
        r"##\s*Passage\s*\n(.*?)(?=\n##\s|\Z)",
        md_text, re.DOTALL,
    )
    if passage_match:
        passage_text = passage_match.group(1)
    else:
        passage_text = md_text

    raw_paragraphs = re.split(r"\n\s*\n", passage_text.strip())
    out: list[str] = []
    for p in raw_paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith("#"):
            continue
        # 题号格式 (1. ... / 2. ...) — D 模式题目
        if re.match(r"^\d+\.\s", p):
            continue
        if p.startswith("【答案】"):
            continue
        # *word* → <em>word</em>
        p_html = EM_PATTERN.sub(r"<em>\1</em>", p)
        out.append(p_html)
    return out


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

CSS = """
:root {
  --bg: #faf7f2;
  --bg-soft: #f3ede3;
  --bg-soft-2: #ede4d4;
  --text: #2a2520;
  --text-soft: #6b5e52;
  --accent: #c0392b;
  --accent-soft: #e8c1bb;
  --highlight: #f7d36b;
  --border: #d8cfc1;
  --exam-bg: #fef5e7;
  --memo-bg: #e8f4f8;
  --sidebar-l: 240px;
  --sidebar-r: 320px;
  --font-base: 16px;
  --font-mono: "SF Mono", "JetBrains Mono", Consolas, monospace;
  --font-sans: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-serif: "Georgia", "Source Han Serif SC", "Songti SC", serif;
}

/* 头图横幅 */
.cover-banner {
  position: relative;
  width: 100%;
  max-height: 360px;
  overflow: hidden;
  background: #0e0a06;
}
.cover-banner img {
  display: block;
  width: 100%;
  height: 360px;
  object-fit: cover;
  object-position: center 40%;
  filter: contrast(1.05) saturate(0.95);
}
.cover-caption {
  position: absolute;
  bottom: 16px;
  left: 24px;
  font-family: var(--font-serif);
  font-size: 0.95rem;
  color: #f3e7c8;
  letter-spacing: 0.04em;
  text-shadow: 0 1px 4px rgba(0,0,0,0.6);
  font-style: italic;
}
[data-theme="dark"] .cover-banner {
  filter: brightness(0.85);
}
[data-theme="dark"] {
  --bg: #1a1714;
  --bg-soft: #25211c;
  --bg-soft-2: #2e2820;
  --text: #d8cfbe;
  --text-soft: #8a7e6c;
  --accent: #e07b6b;
  --accent-soft: #5e3a35;
  --highlight: #c89a3e;
  --border: #3a3329;
  --exam-bg: #3a2f1f;
  --memo-bg: #1f3a40;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: var(--font-sans);
  font-size: var(--font-base);
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
  transition: background 0.2s, color 0.2s;
}
header.page-header {
  position: sticky; top: 0; z-index: 20;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  padding: 14px 24px;
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 12px;
}
header h1 { margin: 0; font-size: 20px; font-weight: 600; font-family: var(--font-serif); }
header .meta { font-size: 12px; color: var(--text-soft); font-family: var(--font-mono); margin-top: 2px; }
header .meta span { margin-right: 14px; }
.toolbar { display: flex; gap: 8px; align-items: center; }
.toolbar button, .toolbar select {
  background: var(--bg-soft); color: var(--text);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 6px 12px; font-size: 13px;
  cursor: pointer; font-family: var(--font-sans);
}
.toolbar button:hover { background: var(--accent-soft); }

.layout {
  display: grid;
  grid-template-columns: var(--sidebar-l) 1fr var(--sidebar-r);
  min-height: calc(100vh - 80px);
  transition: grid-template-columns 0.2s;
}
.layout.left-collapsed { grid-template-columns: 0 1fr var(--sidebar-r); }
.layout.right-collapsed { grid-template-columns: var(--sidebar-l) 1fr 0; }
.layout.both-collapsed { grid-template-columns: 0 1fr 0; }
.layout.left-collapsed main { padding-left: 60px; }
.layout.right-collapsed main { padding-right: 60px; }
.layout.both-collapsed main { padding-left: 60px; padding-right: 60px; }

aside.sidebar {
  position: sticky; top: 76px; align-self: start;
  max-height: calc(100vh - 76px); overflow-y: auto;
  background: var(--bg-soft);
  padding: 18px 14px;
  transition: opacity 0.2s, padding 0.2s;
}
aside.sidebar.left { border-right: 1px solid var(--border); }
aside.sidebar.right { border-left: 1px solid var(--border); }
.layout.left-collapsed aside.left,
.layout.right-collapsed aside.right {
  opacity: 0; padding-left: 0; padding-right: 0;
  pointer-events: none; overflow: hidden;
}
aside h2 {
  font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--text-soft); margin: 0 0 12px;
  display: flex; align-items: center; gap: 6px;
}
aside h2 .count {
  background: var(--bg-soft-2); color: var(--text-soft);
  font-size: 10px; padding: 1px 6px; border-radius: 8px;
  font-weight: 500;
}
.word-group { margin-bottom: 16px; }
.word-group h3 { font-size: 11px; color: var(--text-soft); margin: 6px 0 4px; font-weight: 500; }
aside ul { list-style: none; padding: 0; margin: 0; }
aside li a {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 8px; font-size: 13px;
  color: var(--text); text-decoration: none;
  border-radius: 4px; font-family: var(--font-mono);
  cursor: pointer;
}
aside li a:hover { background: var(--accent-soft); }
aside li a .num { font-size: 9px; color: var(--text-soft); margin-left: auto; }

aside.right .para-group {
  margin-bottom: 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
aside.right .para-group > summary {
  list-style: none; cursor: pointer;
  padding: 8px 12px;
  font-size: 12px; font-family: var(--font-mono);
  color: var(--accent); background: var(--bg-soft-2);
  display: flex; align-items: center; justify-content: space-between;
  user-select: none;
}
aside.right .para-group > summary::-webkit-details-marker { display: none; }
aside.right .para-group > summary::after {
  content: '▾'; transition: transform 0.2s;
  color: var(--text-soft); font-size: 10px;
}
aside.right .para-group:not([open]) > summary::after { transform: rotate(-90deg); }
aside.right .para-group .cards { padding: 8px; display: grid; gap: 8px; }

.annotation-card {
  padding: 10px 12px; border-radius: 6px;
  border-left: 3px solid; font-size: 13px; line-height: 1.6;
}
.annotation-card.exam { background: var(--exam-bg); border-color: #e67e22; }
.annotation-card.memo { background: var(--memo-bg); border-color: #2980b9; }
.annotation-card .head {
  display: flex; align-items: center; gap: 6px; margin-bottom: 4px;
}
.annotation-card .word { font-family: var(--font-mono); font-weight: 700; font-size: 13px; }
.annotation-card .badge {
  font-size: 9px; padding: 1px 5px; border-radius: 3px;
  background: rgba(0,0,0,0.1); color: var(--text); font-weight: 500;
}
.annotation-card .title { font-weight: 600; margin-bottom: 3px; font-size: 12px; }
.annotation-card .content { color: var(--text-soft); font-size: 12px; }
.annotation-card b { color: var(--text); }

/* Toolbar 里的侧栏 toggle 按钮：展开/收起都是同一个按钮，状态用 .collapsed 区分 */
.sidebar-toggle {
  position: relative;
  display: inline-flex; align-items: center; gap: 4px;
}
.sidebar-toggle .arrow {
  display: inline-block;
  font-size: 10px;
  transition: transform 0.2s;
  opacity: 0.6;
}
.sidebar-toggle.collapsed {
  background: var(--accent-soft);
  color: var(--accent);
  border-color: var(--accent);
}
.sidebar-toggle.collapsed .arrow { opacity: 1; }
.sidebar-toggle.left.collapsed .arrow { transform: rotate(180deg); }
.sidebar-toggle.right.collapsed .arrow { transform: rotate(0deg); }

main {
  padding: 24px 36px 100px;
  max-width: 760px;
  margin: 0 auto;
  width: 100%;
}
section.paragraph {
  margin-bottom: 56px; padding-bottom: 36px;
  border-bottom: 1px dashed var(--border);
}
section.paragraph:last-child { border-bottom: none; }
section .para-num {
  display: inline-block; font-family: var(--font-mono);
  font-size: 11px; color: var(--accent);
  background: var(--accent-soft);
  padding: 2px 8px; border-radius: 3px;
  margin-bottom: 10px;
}
section p.para-text {
  font-family: var(--font-serif); font-size: 16px;
  line-height: 1.95; margin: 12px 0;
}
section p.para-text em { font-style: normal; font-weight: 600; }
[data-theme="light"] section p.para-text em {
  background: linear-gradient(transparent 55%, var(--highlight) 55%);
  padding: 0 2px;
}
[data-theme="dark"] section p.para-text em {
  color: #e8c97a;
  text-decoration: underline wavy;
  text-decoration-color: var(--highlight);
  text-decoration-thickness: 1.5px;
  text-underline-offset: 4px;
  background: transparent;
}

@media print {
  .toolbar, aside.sidebar, .sidebar-toggle { display: none; }
  .layout { grid-template-columns: 1fr; }
  main { max-width: none; }
  section.paragraph { page-break-inside: avoid; }
  aside.right { position: static; max-height: none; }
}
@media (max-width: 980px) {
  .layout { grid-template-columns: 0 1fr 0; }
  aside.sidebar { position: fixed; top: 76px; bottom: 60px; max-height: none; z-index: 12; }
  aside.sidebar.left { left: 0; width: var(--sidebar-l); transform: translateX(-100%); }
  aside.sidebar.left.open { transform: translateX(0); }
  aside.sidebar.right { right: 0; width: var(--sidebar-r); transform: translateX(100%); }
  aside.sidebar.right.open { transform: translateX(0); }
  main { padding: 16px; }
}
"""


JS = """
function toggleTheme() {
  const html = document.documentElement;
  const cur = html.getAttribute('data-theme') || 'light';
  const next = cur === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', next);
  localStorage.setItem('memo-theme', next);
  document.getElementById('theme-btn').textContent =
    next === 'light' ? '🌙 暗色模式' : '☀️ 亮色模式';
}
function setFontSize(size) {
  document.documentElement.style.setProperty('--font-base', size);
  localStorage.setItem('memo-font', size);
}
function toggleSidebar(side) {
  const layout = document.querySelector('.layout');
  layout.classList.toggle(side + '-collapsed');
  // 同步 toolbar 里的 toggle 按钮状态
  const btn = document.querySelector('.sidebar-toggle[data-side="' + side + '"]');
  if (btn) btn.classList.toggle('collapsed', layout.classList.contains(side + '-collapsed'));
  if (window.innerWidth <= 980) {
    const aside = document.querySelector('aside.' + side);
    if (aside) aside.classList.toggle('open');
  }
  localStorage.setItem('memo-sidebar-' + side,
    layout.classList.contains(side + '-collapsed') ? '1' : '0');
}
function jumpToWord(word) {
  const ems = document.querySelectorAll('main section.paragraph p.para-text em');
  for (const em of ems) {
    if (em.textContent.trim().toLowerCase() === word.toLowerCase()) {
      em.scrollIntoView({ behavior: 'smooth', block: 'center' });
      em.style.transition = 'background 0.3s';
      const orig = em.style.background;
      em.style.background = 'rgba(192, 57, 43, 0.25)';
      setTimeout(() => { em.style.background = orig; }, 800);
      return;
    }
  }
}
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('memo-theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
    const btn = document.getElementById('theme-btn');
    if (btn) btn.textContent = savedTheme === 'light' ? '🌙 暗色模式' : '☀️ 亮色模式';
  }
  const savedFont = localStorage.getItem('memo-font');
  if (savedFont) {
    document.documentElement.style.setProperty('--font-base', savedFont);
    const sel = document.getElementById('font-sel');
    if (sel) sel.value = savedFont;
  }
  ['left', 'right'].forEach(side => {
    if (localStorage.getItem('memo-sidebar-' + side) === '1') {
      document.querySelector('.layout').classList.add(side + '-collapsed');
      const btn = document.querySelector('.sidebar-toggle[data-side="' + side + '"]');
      if (btn) btn.classList.add('collapsed');
    }
  });
  document.querySelectorAll('aside.left a[data-word]').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      jumpToWord(a.dataset.word);
    });
  });
});
"""


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------

def render_word_list(words: list[str], group: str, start_idx: int = 1) -> str:
    items = "\n".join(
        f'<li><a data-word="{w}" href="#word-{w}">{w}<span class="num">[{i}]</span></a></li>'
        for i, w in enumerate(words, start_idx)
    )
    return f'<div class="word-group"><h3>{group}</h3><ul>{items}</ul></div>'


def render_paragraph(pid: int, total: int, text_html: str) -> str:
    return (
        f'<section class="paragraph" id="para-{pid}">\n'
        f'  <span class="para-num">Paragraph {pid} / {total}</span>\n'
        f'  <p class="para-text">{text_html}</p>\n'
        f'</section>'
    )


def render_para_group(p: dict, total: int) -> str:
    cards_html = "\n".join(
        f'''<div class="annotation-card {c["type"]}">
  <div class="head">
    <span class="word">{c["word"]}</span>
    <span class="badge">{"考试派" if c["type"] == "exam" else "记忆派"}</span>
  </div>
  <div class="title">{c["title"]}</div>
  <div class="content">{c["content"]}</div>
</div>'''
        for c in p.get("cards", [])
    )
    open_attr = ' open' if p["id"] == 1 else ''
    return (
        f'<details class="para-group"{open_attr}>\n'
        f'  <summary>Paragraph {p["id"]} / {total} · {len(p.get("cards", []))} 张卡</summary>\n'
        f'  <div class="cards">\n{cards_html}\n  </div>\n'
        f'</details>'
    )


def render(meta: dict, paragraphs: list[str], annotations: dict, audio_path: str | None, cover_path: str | None = None) -> str:
    main_words = meta["main_words"]
    supporting_words = meta.get("supporting_words", [])

    word_list_main = render_word_list(main_words, "主线词", 1)
    word_list_supp = (
        render_word_list(supporting_words, "配角词", len(main_words) + 1)
        if supporting_words else ""
    )

    total_para = len(paragraphs)
    paragraphs_html = "\n".join(
        render_paragraph(i + 1, total_para, p) for i, p in enumerate(paragraphs)
    )

    # Annotations: 优先用 annotations.paragraphs，否则只渲染"按段"列表
    ann_paragraphs = annotations.get("paragraphs", [])
    para_groups = "\n".join(render_para_group(p, len(ann_paragraphs)) for p in ann_paragraphs)
    total_cards = sum(len(p.get("cards", [])) for p in ann_paragraphs)

    audio_block = ""
    if audio_path:
        audio_block = (
            '<footer class="audio-bar">\n'
            '  <span class="label">▶ 朗读 (D 模式仅 Passage)</span>\n'
            f'  <audio id="main-audio" controls preload="metadata" src="{audio_path}">\n'
            '    您的浏览器不支持 audio 元素。\n'
            '  </audio>\n'
            '</footer>'
        )

    cover_block = ""
    if cover_path:
        cover_block = (
            '<div class="cover-banner">\n'
            f'  <img src="{cover_path}" alt="{meta.get("title", "封面")} — 今日精读封面" />\n'
            f'  <div class="cover-caption">{meta.get("title", "")} · {meta["date"]}</div>\n'
            '</div>\n\n'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta['date']} · 墨墨学霸笔记 · {meta.get('title', '')}</title>
<style>{CSS}</style>
</head>
<body>

{cover_block}<header class="page-header">
  <div>
    <h1>📓 墨墨·学霸笔记 · {meta.get('title', '')}</h1>
    <div class="meta">
      <span>📅 {meta['date']}</span>
      <span>📚 {meta.get('mode', 'D')}</span>
      <span>🎯 主线 {len(main_words)} 词</span>
      <span>👀 配角 {len(supporting_words)} 词</span>
      <span>📝 {total_cards} 张卡</span>
    </div>
  </div>
  <div class="toolbar">
    <button class="sidebar-toggle left" data-side="left" onclick="toggleSidebar('left')" title="收放左栏 (词表)">
      <span class="arrow">◀</span><span class="label">词表</span>
    </button>
    <button class="sidebar-toggle right" data-side="right" onclick="toggleSidebar('right')" title="收放右栏 (标注卡)">
      <span class="label">标注</span><span class="arrow">▶</span>
    </button>
    <select id="font-sel" onchange="setFontSize(this.value)">
      <option value="14px">小字</option>
      <option value="16px" selected>中字</option>
      <option value="18px">大字</option>
      <option value="20px">超大</option>
    </select>
    <button id="theme-btn" onclick="toggleTheme()">🌙 暗色模式</button>
    <button onclick="window.print()">🖨 导出 PDF</button>
  </div>
</header>

<div class="layout">
  <aside class="sidebar left">
    <h2>📌 今日词表 <span class="count">{len(main_words) + len(supporting_words)}</span></h2>
    {word_list_main}
    {word_list_supp}
  </aside>

  <main>
{paragraphs_html}
  </main>

  <aside class="sidebar right">
    <h2>📝 学霸标注 <span class="count">{total_cards}</span></h2>
{para_groups}
  </aside>
</div>

{audio_block}

<script>{JS}</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Cover image (Step 3.5 产物，由 Mavis agent 用 image_synthesize 生成)
#
# 本脚本只负责嵌入 cover.png（如存在），不负责生图。
# 生图流程：Step 3.5 由 Mavis agent 调 image_synthesize → cover.png
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_meta_from_md(md_text: str, annotations: dict, date_str: str) -> dict:
    """Build meta dict (for header / word list) by combining annotations + fallback."""
    return {
        "date": date_str,
        "mode": annotations.get("mode", "D"),
        "title": annotations.get("title", "(无标题)"),
        "main_words": annotations.get("main_words", []),
        "supporting_words": annotations.get("supporting_words", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render memo-context daily HTML")
    parser.add_argument("--date", default=date.today().isoformat(),
                        help="日期 (YYYY-MM-DD)，默认今天")
    parser.add_argument("--dir", type=Path, default=None,
                        help="覆盖默认 contexts/<date>/ 目录")
    # Cover 图选项（Step 3.5 产物，agent 提前生成）
    parser.add_argument("--no-cover", action="store_true",
                        help="完全跳过封面图（连 banner 块都不渲染）")
    args = parser.parse_args()

    base = args.dir or (CONTEXTS_DIR / args.date)
    article_md = base / "article.md"
    annotations_json = base / "annotations.json"
    audio_mp3 = base / "audio.mp3"
    cover_png = base / "cover.png"
    out_html = base / "page.html"

    if not article_md.exists():
        print(f"❌ 缺 {article_md}（Step 3 产出）", file=sys.stderr)
        return 1
    if not annotations_json.exists():
        print(f"❌ 缺 {annotations_json}（Step 5.5 产出）", file=sys.stderr)
        return 1

    md_text = article_md.read_text(encoding="utf-8")
    annotations = json.loads(annotations_json.read_text(encoding="utf-8"))

    paragraphs = parse_paragraphs(md_text)
    if not paragraphs:
        print(f"❌ {article_md} 没解析到段落（确认有 Passage 部分）", file=sys.stderr)
        return 1

    # Word list fallback: 如果 annotations 里没 main_words，从段落 *word* 抓
    if not annotations.get("main_words"):
        found = set()
        for p in paragraphs:
            for m in EM_PATTERN.finditer(p):
                found.add(m.group(1))
        annotations["main_words"] = sorted(found)
        print(f"⚠️  annotations.json 缺 main_words，从 article.md 抽出 {len(found)} 个词", file=sys.stderr)

    meta = build_meta_from_md(md_text, annotations, args.date)

    # Cover 处理：--no-cover 完全跳过；否则复用 <base>/cover.png（如有）
    # cover.png 由 Step 3.5（Mavis agent + image_synthesize）生成
    cover_path = None
    if args.no_cover:
        pass
    elif cover_png.exists():
        cover_path = "cover.png"
    else:
        print(f"ℹ️  无 cover.png，banner 块不渲染（Step 3.5 由 agent 用 image_synthesize 生成）")

    # audio 路径：用相对路径（page.html 在同目录，audio.mp3 也在）
    audio_path = "audio.mp3" if audio_mp3.exists() else None

    html = render(meta, paragraphs, annotations, audio_path, cover_path=cover_path)

    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    size_kb = out_html.stat().st_size / 1024
    print(f"✅ {out_html} ({size_kb:.1f} KB)")
    if cover_path:
        print(f"   cover: {cover_path}")
    if audio_path:
        print(f"   audio: {audio_path}")
    print(f"   paragraphs: {len(paragraphs)} | cards: {sum(len(p.get('cards', [])) for p in annotations.get('paragraphs', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
