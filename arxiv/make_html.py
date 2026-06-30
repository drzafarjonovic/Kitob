#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_html.py — "Garri Potter va La'natlangan Bola" romanini o'qishga moslangan,
mustaqil (self-contained) HTML kitobga aylantiradi. Kindle/elektron o'quvchiga
o'xshash funksiyalar: mundarija, tema (kunduz/sepiya/tun), shrift o'lchami,
o'qish holatini eslab qolish (localStorage), progress, navigatsiya, xatcho'p,
qidiruv. CSS va JS bevosita fayl ichida — internetsiz, oflayn ishlaydi.

Sof Python stdlib. Tashqi kutubxona kerak emas.
"""

import html
import json
import os
import re
import sys

# Skript arxiv/ papkasida, manba va chiqish fayllari esa loyiha ildizida.
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "Garri_Potter_va_Lanatlangan_Bola_Roman.txt")
OUT = os.path.join(ROOT, "Garri_Potter_va_Lanatlangan_Bola.html")

CHAPTER_RE = re.compile(r"^([IVXLC]+)\s+BOB\.\s+(.+)$")
SCENE_SEP = "* * *"


def parse(text):
    """Matnni sarlavha bloki + boblar (sarlavha, sahna paragraflari) ga ajratadi."""
    lines = text.replace("\r\n", "\n").split("\n")

    title_block = []
    chapters = []
    cur = None
    i = 0
    # Sarlavha blokini yig'amiz (birinchi BOB sarlavhasiga qadar).
    while i < len(lines):
        m = CHAPTER_RE.match(lines[i].strip())
        if m:
            break
        title_block.append(lines[i])
        i += 1

    # Boblarni o'qiymiz.
    while i < len(lines):
        line = lines[i]
        m = CHAPTER_RE.match(line.strip())
        if m:
            if cur is not None:
                chapters.append(cur)
            cur = {"num": m.group(1), "title": m.group(2).strip(), "body": []}
        else:
            if cur is not None:
                cur["body"].append(line)
        i += 1
    if cur is not None:
        chapters.append(cur)

    return title_block, chapters


def split_paragraphs(body_lines):
    """Bob tanasini sahna va paragraflarga bo'ladi.
    Qaytaradi: blocks ro'yxati. Har blok ('sep', None) yoki ('p', matn)."""
    blocks = []
    buf = []

    def flush():
        if buf:
            para = " ".join(s.strip() for s in buf if s.strip())
            if para:
                blocks.append(("p", para))
            buf.clear()

    for raw in body_lines:
        s = raw.strip()
        if s == SCENE_SEP:
            flush()
            blocks.append(("sep", None))
        elif s == "":
            flush()
        else:
            buf.append(s)
    flush()
    return blocks


def render_chapter_html(ch, idx):
    parts = [f'<section class="chapter" id="ch{idx}" data-index="{idx}">']
    parts.append('<header class="chapter-head">')
    parts.append(f'<div class="chapter-num">{html.escape(ch["num"])} BOB</div>')
    parts.append(f'<h2 class="chapter-title">{html.escape(ch["title"])}</h2>')
    parts.append('</header>')
    for kind, val in split_paragraphs(ch["body"]):
        if kind == "sep":
            parts.append('<div class="scene-sep" aria-hidden="true">* * *</div>')
        else:
            parts.append(f'<p>{html.escape(val)}</p>')
    parts.append('</section>')
    return "\n".join(parts)


def build(title_block, chapters):
    # Sarlavha matnlari.
    tb = [l.strip() for l in title_block if l.strip()]
    book_title = tb[0] if tb else "Roman"
    subtitle_lines = tb[1:] if len(tb) > 1 else []

    toc_items = []
    for idx, ch in enumerate(chapters):
        label = f'{html.escape(ch["num"])}. {html.escape(ch["title"])}'
        toc_items.append(
            f'<li><a href="#ch{idx}" data-goto="{idx}">'
            f'<span class="toc-num">{html.escape(ch["num"])}</span>'
            f'<span class="toc-name">{html.escape(ch["title"])}</span></a></li>'
        )
    toc_html = "\n".join(toc_items)

    chapters_html = "\n".join(render_chapter_html(ch, i) for i, ch in enumerate(chapters))

    # Boblar metama'lumoti JS uchun.
    chapter_meta = [{"num": ch["num"], "title": ch["title"]} for ch in chapters]
    meta_json = json.dumps(chapter_meta, ensure_ascii=False)

    subtitle_html = "<br>".join(html.escape(s) for s in subtitle_lines)

    return PAGE.format(
        book_title=html.escape(book_title),
        subtitle_html=subtitle_html,
        toc_html=toc_html,
        chapters_html=chapters_html,
        meta_json=meta_json,
        chapter_count=len(chapters),
    )


PAGE = r"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{book_title}</title>
<style>
:root {{
  --bg: #faf8f3;
  --fg: #2b2b2b;
  --muted: #7a7368;
  --accent: #7b1113;
  --panel: #ffffff;
  --panel-border: #e6e0d4;
  --shadow: rgba(0,0,0,0.12);
  --sel: #f3e6c8;
  --reading-width: 38rem;
  --font-scale: 1;
  --font-family: Georgia, 'Times New Roman', 'Noto Serif', serif;
}}
[data-theme="sepia"] {{
  --bg: #f4ecd8;
  --fg: #4b3f2f;
  --muted: #8a795d;
  --accent: #8a5a1a;
  --panel: #fbf4e3;
  --panel-border: #e3d6b8;
  --shadow: rgba(60,40,10,0.15);
  --sel: #e8d6a8;
}}
[data-theme="night"] {{
  --bg: #15171a;
  --fg: #cfd2d6;
  --muted: #8b9197;
  --accent: #d98a3d;
  --panel: #1e2126;
  --panel-border: #2c3036;
  --shadow: rgba(0,0,0,0.5);
  --sel: #3a3320;
}}

* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-family);
  line-height: 1.75;
  transition: background .3s ease, color .3s ease;
  -webkit-font-smoothing: antialiased;
}}
::selection {{ background: var(--sel); }}

/* Progress bar */
#progress-track {{
  position: fixed; top: 0; left: 0; right: 0; height: 4px;
  background: transparent; z-index: 60;
}}
#progress-bar {{
  height: 100%; width: 0%;
  background: var(--accent);
  transition: width .15s ease;
}}

/* Top bar */
#topbar {{
  position: fixed; top: 0; left: 0; right: 0;
  height: 52px; z-index: 50;
  display: flex; align-items: center; gap: .5rem;
  padding: 0 .75rem;
  background: var(--panel);
  border-bottom: 1px solid var(--panel-border);
  box-shadow: 0 1px 6px var(--shadow);
}}
#topbar .title {{
  font-size: .9rem; font-weight: 600; color: var(--fg);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  flex: 1; min-width: 0;
}}
#topbar .pct {{ font-size: .8rem; color: var(--muted); white-space: nowrap; }}
.iconbtn {{
  background: transparent; border: 1px solid transparent;
  color: var(--fg); cursor: pointer;
  width: 38px; height: 38px; border-radius: 8px;
  font-size: 1.1rem; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
  transition: background .15s ease;
}}
.iconbtn:hover {{ background: var(--sel); }}

/* Sidebar (TOC) */
#overlay {{
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  opacity: 0; pointer-events: none; transition: opacity .25s ease; z-index: 70;
}}
#overlay.open {{ opacity: 1; pointer-events: auto; }}
#sidebar {{
  position: fixed; top: 0; left: 0; bottom: 0;
  width: 320px; max-width: 85vw; z-index: 80;
  background: var(--panel);
  border-right: 1px solid var(--panel-border);
  transform: translateX(-105%); transition: transform .28s ease;
  display: flex; flex-direction: column;
  box-shadow: 2px 0 18px var(--shadow);
}}
#sidebar.open {{ transform: translateX(0); }}
#sidebar h3 {{
  margin: 0; padding: 1rem 1.25rem; font-size: 1rem;
  border-bottom: 1px solid var(--panel-border); color: var(--accent);
  display: flex; align-items: center; justify-content: space-between;
}}
#toc {{ list-style: none; margin: 0; padding: .5rem 0; overflow-y: auto; flex: 1; }}
#toc li a {{
  display: flex; gap: .6rem; align-items: baseline;
  padding: .55rem 1.25rem; text-decoration: none; color: var(--fg);
  border-left: 3px solid transparent; transition: background .15s ease;
}}
#toc li a:hover {{ background: var(--sel); }}
#toc li a.active {{ border-left-color: var(--accent); background: var(--sel); }}
.toc-num {{ color: var(--muted); font-size: .8rem; min-width: 2.6rem; font-variant: small-caps; }}
.toc-name {{ font-size: .95rem; }}

/* Settings popover */
#settings {{
  position: fixed; top: 56px; right: .75rem; z-index: 75;
  background: var(--panel); border: 1px solid var(--panel-border);
  border-radius: 12px; padding: 1rem; width: 280px;
  box-shadow: 0 8px 26px var(--shadow);
  display: none;
}}
#settings.open {{ display: block; }}
#settings .row {{ margin-bottom: 1rem; }}
#settings .row:last-child {{ margin-bottom: 0; }}
#settings label {{ display: block; font-size: .78rem; color: var(--muted);
  text-transform: uppercase; letter-spacing: .05em; margin-bottom: .5rem; }}
.theme-opts, .seg {{ display: flex; gap: .5rem; }}
.theme-opts button, .seg button {{
  flex: 1; padding: .5rem; border-radius: 8px; cursor: pointer;
  border: 1px solid var(--panel-border); background: transparent; color: var(--fg);
  font-size: .85rem;
}}
.theme-opts button.sel, .seg button.sel {{
  border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset;
}}
.sw-day {{ background:#faf8f3; }} .sw-sepia {{ background:#f4ecd8; }}
.sw-night {{ background:#15171a; color:#fff !important; }}

/* Search */
#searchbox {{
  position: fixed; top: 56px; left: 50%; transform: translateX(-50%);
  z-index: 75; width: min(34rem, 92vw);
  background: var(--panel); border: 1px solid var(--panel-border);
  border-radius: 12px; box-shadow: 0 8px 26px var(--shadow);
  display: none; padding: .75rem;
}}
#searchbox.open {{ display: block; }}
#searchbox input {{
  width: 100%; padding: .6rem .75rem; font-size: 1rem;
  border: 1px solid var(--panel-border); border-radius: 8px;
  background: var(--bg); color: var(--fg); font-family: inherit;
}}
#search-results {{ max-height: 50vh; overflow-y: auto; margin-top: .5rem; }}
#search-results .res {{
  padding: .5rem .6rem; border-radius: 8px; cursor: pointer; font-size: .9rem;
}}
#search-results .res:hover {{ background: var(--sel); }}
#search-results .res .loc {{ color: var(--muted); font-size: .78rem; display:block; margin-bottom:.15rem; }}
#search-results mark {{ background: var(--accent); color:#fff; padding: 0 2px; border-radius: 3px; }}
.search-hint {{ color: var(--muted); font-size:.82rem; padding:.4rem .6rem; }}

/* Reading area */
#book {{
  max-width: var(--reading-width);
  margin: 0 auto; padding: 84px 1.25rem 7rem;
}}
.cover {{
  text-align: center; padding: 14vh 0 10vh; border-bottom: 1px solid var(--panel-border);
  margin-bottom: 2rem;
}}
.cover .big {{
  font-size: calc(2.1rem * var(--font-scale)); line-height: 1.2;
  color: var(--accent); margin: 0 0 1.25rem; letter-spacing: .02em;
}}
.cover .sub {{ color: var(--muted); font-size: calc(1rem * var(--font-scale)); font-style: italic; }}

.chapter {{ padding-top: 1.5rem; scroll-margin-top: 64px; }}
.chapter-head {{ text-align: center; margin: 2.5rem 0 2rem; }}
.chapter-num {{
  font-variant: small-caps; letter-spacing: .18em; color: var(--muted);
  font-size: calc(.8rem * var(--font-scale)); margin-bottom: .4rem;
}}
.chapter-title {{
  font-size: calc(1.5rem * var(--font-scale)); color: var(--accent);
  margin: 0; font-weight: 600;
}}
.chapter-head::after {{
  content: ""; display: block; width: 56px; height: 2px;
  background: var(--accent); opacity: .5; margin: 1rem auto 0;
}}
#book p {{
  font-size: calc(1.12rem * var(--font-scale));
  margin: 0 0 1.15rem; text-align: justify; hyphens: auto;
  text-indent: 1.4em;
}}
#book p:first-of-type, .chapter-head + p {{ text-indent: 0; }}
.scene-sep {{
  text-align: center; color: var(--muted); margin: 2rem 0;
  letter-spacing: .8em; font-size: calc(1rem * var(--font-scale));
}}

/* Chapter nav */
.chapter-nav {{
  display: flex; justify-content: space-between; gap: 1rem;
  margin: 3rem 0 1rem; padding-top: 1.5rem; border-top: 1px solid var(--panel-border);
}}
.chapter-nav button {{
  background: transparent; border: 1px solid var(--panel-border); color: var(--fg);
  padding: .6rem 1rem; border-radius: 10px; cursor: pointer; font-family: inherit;
  font-size: .9rem; max-width: 48%; text-align: left;
}}
.chapter-nav button:hover:not(:disabled) {{ background: var(--sel); }}
.chapter-nav button:disabled {{ opacity: .35; cursor: default; }}
.chapter-nav .nxt {{ text-align: right; }}
.chapter-nav small {{ display:block; color: var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; }}

/* Bookmark button (floating) */
#bookmark-btn {{
  position: fixed; right: 1rem; bottom: 1.25rem; z-index: 55;
  width: 48px; height: 48px; border-radius: 50%;
  background: var(--accent); color: #fff; border: none; cursor: pointer;
  font-size: 1.25rem; box-shadow: 0 4px 14px var(--shadow);
  display: inline-flex; align-items:center; justify-content:center;
}}
#toast {{
  position: fixed; bottom: 1.5rem; left: 50%; transform: translateX(-50%);
  background: var(--fg); color: var(--bg); padding: .6rem 1.1rem;
  border-radius: 999px; font-size: .85rem; z-index: 90;
  opacity: 0; pointer-events: none; transition: opacity .25s ease;
}}
#toast.show {{ opacity: .95; }}

mark.find-hit {{ background: #ffd54a; color:#000; border-radius:2px; }}

@media (max-width: 480px) {{
  #book {{ padding-left: 1rem; padding-right: 1rem; }}
  #topbar .pct {{ display: none; }}
}}
@media print {{
  #topbar, #progress-track, #bookmark-btn, #sidebar, #overlay,
  #settings, #searchbox, .chapter-nav {{ display: none !important; }}
  #book {{ max-width: none; padding: 0; }}
}}
</style>
</head>
<body>
<div id="progress-track"><div id="progress-bar"></div></div>

<header id="topbar">
  <button class="iconbtn" id="btn-toc" title="Mundarija" aria-label="Mundarija">&#9776;</button>
  <span class="title" id="cur-chapter-title">{book_title}</span>
  <span class="pct" id="pct-label">0%</span>
  <button class="iconbtn" id="btn-search" title="Qidiruv" aria-label="Qidiruv">&#128269;</button>
  <button class="iconbtn" id="btn-settings" title="Sozlamalar" aria-label="Sozlamalar">&#9881;</button>
</header>

<div id="settings">
  <div class="row">
    <label>Mavzu</label>
    <div class="theme-opts">
      <button data-theme="day" class="sw-day">Kunduz</button>
      <button data-theme="sepia" class="sw-sepia">Sepiya</button>
      <button data-theme="night" class="sw-night">Tun</button>
    </div>
  </div>
  <div class="row">
    <label>Shrift o'lchami</label>
    <div class="seg">
      <button id="font-dec">A&minus;</button>
      <button id="font-reset">Asl</button>
      <button id="font-inc">A&plus;</button>
    </div>
  </div>
  <div class="row">
    <label>Qator kengligi</label>
    <div class="seg">
      <button data-width="narrow">Tor</button>
      <button data-width="normal">O'rta</button>
      <button data-width="wide">Keng</button>
    </div>
  </div>
</div>

<div id="searchbox">
  <input type="text" id="search-input" placeholder="Kitob ichidan qidirish..." autocomplete="off">
  <div id="search-results"></div>
</div>

<div id="overlay"></div>
<aside id="sidebar">
  <h3>Mundarija <button class="iconbtn" id="btn-toc-close" aria-label="Yopish">&times;</button></h3>
  <ul id="toc">
{toc_html}
  </ul>
</aside>

<main id="book">
  <div class="cover">
    <h1 class="big">{book_title}</h1>
    <div class="sub">{subtitle_html}</div>
  </div>
{chapters_html}
  <div class="chapter-nav" id="end-nav">
    <button class="prv" id="nav-prev"><small>Oldingi</small><span id="nav-prev-t"></span></button>
    <button class="nxt" id="nav-next"><small>Keyingi</small><span id="nav-next-t"></span></button>
  </div>
</main>

<button id="bookmark-btn" title="Xatcho'p qo'yish / o'tish">&#9734;</button>
<div id="toast"></div>

<script>
(function() {{
  "use strict";
  var CHAPTERS = {meta_json};
  var COUNT = {chapter_count};
  var KEY = "gp-curse-reader";

  var state = {{
    theme: "day",
    fontScale: 1,
    width: "normal",
    scrollY: 0,
    chapter: 0,
    bookmark: null
  }};

  function load() {{
    try {{
      var s = JSON.parse(localStorage.getItem(KEY) || "{{}}");
      Object.assign(state, s);
    }} catch (e) {{}}
  }}
  var saveTimer = null;
  function save() {{
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function() {{
      try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}}
    }}, 250);
  }}

  var root = document.documentElement;
  function applyTheme() {{
    root.setAttribute("data-theme", state.theme);
    document.querySelectorAll(".theme-opts button").forEach(function(b) {{
      b.classList.toggle("sel", b.dataset.theme === state.theme);
    }});
  }}
  function applyFont() {{
    root.style.setProperty("--font-scale", state.fontScale);
  }}
  var WIDTHS = {{ narrow: "30rem", normal: "38rem", wide: "46rem" }};
  function applyWidth() {{
    root.style.setProperty("--reading-width", WIDTHS[state.width] || WIDTHS.normal);
    document.querySelectorAll("[data-width]").forEach(function(b) {{
      b.classList.toggle("sel", b.dataset.width === state.width);
    }});
  }}

  // --- Sidebar / overlay ---
  var sidebar = document.getElementById("sidebar");
  var overlay = document.getElementById("overlay");
  function openSidebar() {{ sidebar.classList.add("open"); overlay.classList.add("open"); }}
  function closeSidebar() {{ sidebar.classList.remove("open"); overlay.classList.remove("open"); }}
  document.getElementById("btn-toc").onclick = openSidebar;
  document.getElementById("btn-toc-close").onclick = closeSidebar;
  overlay.onclick = function() {{ closeSidebar(); closeSearch(); }};

  // --- Settings popover ---
  var settings = document.getElementById("settings");
  document.getElementById("btn-settings").onclick = function(e) {{
    e.stopPropagation(); closeSearch(); settings.classList.toggle("open");
  }};
  document.querySelectorAll(".theme-opts button").forEach(function(b) {{
    b.onclick = function() {{ state.theme = b.dataset.theme; applyTheme(); save(); }};
  }});
  document.querySelectorAll("[data-width]").forEach(function(b) {{
    b.onclick = function() {{ state.width = b.dataset.width; applyWidth(); save(); }};
  }});
  document.getElementById("font-inc").onclick = function() {{
    state.fontScale = Math.min(1.8, state.fontScale + 0.1); applyFont(); save();
  }};
  document.getElementById("font-dec").onclick = function() {{
    state.fontScale = Math.max(0.8, state.fontScale - 0.1); applyFont(); save();
  }};
  document.getElementById("font-reset").onclick = function() {{
    state.fontScale = 1; applyFont(); save();
  }};
  document.addEventListener("click", function(e) {{
    if (settings.classList.contains("open") &&
        !settings.contains(e.target) &&
        e.target.id !== "btn-settings") {{
      settings.classList.remove("open");
    }}
  }});

  // --- Progress + current chapter tracking ---
  var bar = document.getElementById("progress-bar");
  var pct = document.getElementById("pct-label");
  var curTitle = document.getElementById("cur-chapter-title");
  var sections = Array.prototype.slice.call(document.querySelectorAll(".chapter"));
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll("#toc a"));

  function currentChapterIndex() {{
    var probe = window.scrollY + 80;
    var idx = 0;
    for (var i = 0; i < sections.length; i++) {{
      if (sections[i].offsetTop <= probe) idx = i; else break;
    }}
    return idx;
  }}

  function updateProgress() {{
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var p = max > 0 ? (window.scrollY / max) : 0;
    p = Math.max(0, Math.min(1, p));
    bar.style.width = (p * 100).toFixed(1) + "%";
    pct.textContent = Math.round(p * 100) + "%";

    var ci = currentChapterIndex();
    if (ci !== state.chapter) {{
      state.chapter = ci;
      var c = CHAPTERS[ci];
      curTitle.textContent = c ? (c.num + ". " + c.title) : "{book_title}";
      tocLinks.forEach(function(a, i) {{ a.classList.toggle("active", i === ci); }});
      updateNav(ci);
    }}
    state.scrollY = window.scrollY;
    save();
  }}

  var ticking = false;
  window.addEventListener("scroll", function() {{
    if (!ticking) {{
      window.requestAnimationFrame(function() {{ updateProgress(); ticking = false; }});
      ticking = true;
    }}
  }}, {{ passive: true }});
  window.addEventListener("resize", updateProgress);

  // --- TOC navigation ---
  tocLinks.forEach(function(a) {{
    a.onclick = function(e) {{
      e.preventDefault();
      var idx = parseInt(a.dataset.goto, 10);
      gotoChapter(idx);
      closeSidebar();
    }};
  }});
  function gotoChapter(idx) {{
    idx = Math.max(0, Math.min(COUNT - 1, idx));
    var el = document.getElementById("ch" + idx);
    if (el) window.scrollTo({{ top: el.offsetTop - 56, behavior: "smooth" }});
  }}

  // --- Chapter nav buttons ---
  var navPrev = document.getElementById("nav-prev");
  var navNext = document.getElementById("nav-next");
  var navPrevT = document.getElementById("nav-prev-t");
  var navNextT = document.getElementById("nav-next-t");
  function updateNav(ci) {{
    if (ci > 0) {{ navPrev.disabled = false; navPrevT.textContent = CHAPTERS[ci-1].title; }}
    else {{ navPrev.disabled = true; navPrevT.textContent = "—"; }}
    if (ci < COUNT - 1) {{ navNext.disabled = false; navNextT.textContent = CHAPTERS[ci+1].title; }}
    else {{ navNext.disabled = true; navNextT.textContent = "—"; }}
  }}
  navPrev.onclick = function() {{ gotoChapter(state.chapter - 1); }};
  navNext.onclick = function() {{ gotoChapter(state.chapter + 1); }};

  document.addEventListener("keydown", function(e) {{
    if (e.target.tagName === "INPUT") return;
    if (e.key === "ArrowRight") gotoChapter(state.chapter + 1);
    else if (e.key === "ArrowLeft") gotoChapter(state.chapter - 1);
  }});

  // --- Bookmark ---
  var bmBtn = document.getElementById("bookmark-btn");
  bmBtn.onclick = function() {{
    if (state.bookmark != null && Math.abs(state.bookmark - window.scrollY) < 40) {{
      // Already at bookmark — jump nowhere; just inform.
      toast("Siz xatcho'pdasiz");
      return;
    }}
    if (state.bookmark == null) {{
      state.bookmark = window.scrollY; save(); refreshBm();
      toast("Xatcho'p qo'yildi");
    }} else {{
      // Go to bookmark, then offer to replace via long logic — keep simple: jump.
      window.scrollTo({{ top: state.bookmark, behavior: "smooth" }});
      toast("Xatcho'pga o'tildi");
    }}
  }};
  bmBtn.oncontextmenu = function(e) {{
    e.preventDefault();
    state.bookmark = window.scrollY; save(); refreshBm();
    toast("Xatcho'p yangilandi");
  }};
  function refreshBm() {{
    bmBtn.innerHTML = state.bookmark != null ? "&#9733;" : "&#9734;";
  }}

  var toastEl = document.getElementById("toast");
  var toastTimer = null;
  function toast(msg) {{
    toastEl.textContent = msg; toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function() {{ toastEl.classList.remove("show"); }}, 1800);
  }}

  // --- Search ---
  var searchBox = document.getElementById("searchbox");
  var searchInput = document.getElementById("search-input");
  var searchResults = document.getElementById("search-results");
  function openSearch() {{
    settings.classList.remove("open");
    searchBox.classList.add("open"); overlay.classList.add("open");
    searchInput.focus();
  }}
  function closeSearch() {{
    searchBox.classList.remove("open");
    if (!sidebar.classList.contains("open")) overlay.classList.remove("open");
  }}
  document.getElementById("btn-search").onclick = function(e) {{
    e.stopPropagation();
    if (searchBox.classList.contains("open")) closeSearch(); else openSearch();
  }};

  // Build a lightweight index of paragraphs.
  var PARAS = [];
  sections.forEach(function(sec, ci) {{
    sec.querySelectorAll("p").forEach(function(p) {{
      PARAS.push({{ ci: ci, el: p, text: p.textContent }});
    }});
  }});

  function escRe(s) {{ return s.replace(/[.*+?^${{}}()|[\]\\]/g, "\\$&"); }}
  function clearFindHits() {{
    document.querySelectorAll("mark.find-hit").forEach(function(m) {{
      var t = document.createTextNode(m.textContent);
      m.parentNode.replaceChild(t, m); m.parentNode.normalize();
    }});
  }}

  var searchTimer = null;
  searchInput.addEventListener("input", function() {{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(runSearch, 180);
  }});
  function runSearch() {{
    var q = searchInput.value.trim();
    searchResults.innerHTML = "";
    if (q.length < 2) {{
      searchResults.innerHTML = '<div class="search-hint">Kamida 2 ta belgi kiriting.</div>';
      return;
    }}
    var ql = q.toLowerCase();
    var hits = [], cap = 60;
    for (var i = 0; i < PARAS.length && hits.length < cap; i++) {{
      var pos = PARAS[i].text.toLowerCase().indexOf(ql);
      if (pos !== -1) hits.push({{ p: PARAS[i], pos: pos }});
    }}
    if (!hits.length) {{
      searchResults.innerHTML = '<div class="search-hint">Hech narsa topilmadi.</div>';
      return;
    }}
    searchResults.innerHTML =
      '<div class="search-hint">' + hits.length + (hits.length >= cap ? "+" : "") + ' natija</div>';
    hits.forEach(function(h) {{
      var t = h.p.text;
      var start = Math.max(0, h.pos - 35);
      var snippet = (start > 0 ? "…" : "") +
        t.slice(start, h.pos) +
        "<mark>" + t.substr(h.pos, q.length) + "</mark>" +
        t.slice(h.pos + q.length, h.pos + q.length + 45) + "…";
      var c = CHAPTERS[h.p.ci];
      var div = document.createElement("div");
      div.className = "res";
      div.innerHTML = '<span class="loc">' + c.num + ". " + c.title + "</span>" + snippet;
      div.onclick = function() {{
        closeSearch();
        h.p.el.scrollIntoView({{ behavior: "smooth", block: "center" }});
        clearFindHits();
        highlight(h.p.el, q);
      }};
      searchResults.appendChild(div);
    }});
  }}
  function highlight(el, q) {{
    var re = new RegExp(escRe(q), "ig");
    el.innerHTML = el.textContent.replace(re, function(m) {{
      return '<mark class="find-hit">' + m + "</mark>";
    }});
    setTimeout(clearFindHits, 4000);
  }}

  document.addEventListener("keydown", function(e) {{
    if (e.key === "Escape") {{ closeSearch(); closeSidebar(); settings.classList.remove("open"); }}
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f") {{
      e.preventDefault(); openSearch();
    }}
  }});

  // --- Init / restore ---
  load();
  applyTheme(); applyFont(); applyWidth(); refreshBm();
  window.addEventListener("load", function() {{
    if (state.scrollY && state.scrollY > 0) {{
      window.scrollTo(0, state.scrollY);
    }}
    updateProgress();
  }});
  updateProgress();
}})();
</script>
</body>
</html>"""


def main():
    with open(SRC, "r", encoding="utf-8") as f:
        text = f.read()
    title_block, chapters = parse(text)
    if len(chapters) != 29:
        print("OGOHLANTIRISH: bob soni 29 emas:", len(chapters), file=sys.stderr)
    out = build(title_block, chapters)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    print("Yozildi:", OUT)
    print("Boblar:", len(chapters))
    print("Hajm (KB):", round(len(out.encode("utf-8")) / 1024, 1))


if __name__ == "__main__":
    main()
