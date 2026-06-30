#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-book premium reader generator.

Reads each book's `matn.txt`, cleans noise (page numbers, watermarks, repeated
running headers, front/back matter), splits into chapters, re-flows the
hard-wrapped lines into paragraphs, and assembles a self-contained reader HTML
per book by reusing the shared engine (head.html + chrome + app.js + part2.js).

Also builds the `index.html` library landing page linking to all books.

Output files are written to the repository root so the relative references to
icons/, manifest.json and sw.js keep working.
"""
import os, re, html, json

BASE = os.path.dirname(os.path.abspath(__file__))      # .../Kitob/build
ROOT = os.path.dirname(BASE)                            # .../Kitob
BOOKDIR = os.path.join(ROOT, "Garri Potter kitoblari")

def _favicon():
    import base64
    try:
        b = open(os.path.join(ROOT, "icons", "icon.svg"), "rb").read()
        return "data:image/svg+xml;base64," + base64.b64encode(b).decode()
    except Exception:
        return "icons/icon.svg"

FAVICON = _favicon()

# ----------------------------------------------------------------------------
# Book catalogue
# ----------------------------------------------------------------------------
BOOKS = [
    dict(n=1, key="gp_reader_b1", folder="1 - Afsungarlar Toshi",
         title="Falsafiy Tosh", sub="Birinchi kitob",
         accent="#7b1113"),
    dict(n=2, key="gp_reader_b2", folder="2 - Sirlar Xonasi",
         title="Maxfiy Xona", sub="Ikkinchi kitob",
         accent="#1f6f4a"),
    dict(n=3, key="gp_reader_b3", folder="3 - Azkaban Mahbusi",
         title="Azkaban Mahbusi", sub="Uchinchi kitob",
         accent="#5b3a8a"),
    dict(n=4, key="gp_reader_b4", folder="4 - Olovli Kosa",
         title="Otashli Jom", sub="To\u02bbrtinchi kitob",
         accent="#b5651d"),
    dict(n=5, key="gp_reader_b5", folder="5 - Feniks Ordeni",
         title="Qaqnus Ordeni", sub="Beshinchi kitob",
         accent="#1d6fa5"),
    dict(n=6, key="gp_reader_b6", folder="6 - Yarim Qonli Shahzoda",
         title="Chala Zot Shahzoda", sub="Oltinchi kitob",
         accent="#7a5901"),
    dict(n=7, key="gp_reader_b7", folder="7 - Ajal Tuhfalari",
         title="Ajal Tuhfalari", sub="Yettinchi kitob",
         accent="#4a4a4a", cut_at=26168),
    dict(n=8, key="gp_reader_b8", folder="8 - La'natlangan Bola",
         title="La'natlangan Bola", sub="Sakkizinchi kitob \u00b7 Sahna asari",
         accent="#0b5d63"),
]

# ----------------------------------------------------------------------------
# Cleaning helpers
# ----------------------------------------------------------------------------
WATERMARK = re.compile(r"(t\.me|Admin\s*:|@[A-Za-z0-9_]{3,}|uForum|pottermanlar)", re.I)
PAGENUM   = re.compile(r"^\s*\d{1,4}\s*$")

# Chapter heading: optional roman / cyrillic-uppercase ordinal prefix, then БОБ/BOB
HEAD_RE = re.compile(
    r"^\s*((?:[IVXLCDM]+|[\u0410-\u042f\u040e\u0492\u049a\u0498\u04b2\u0401]+"
    r"(?:\s+[\u0410-\u042f\u040e\u0492\u049a\u0498\u04b2\u0401]+)?)\s+)?"
    r"(\u0411\u041e\u0411|BOB)\b\.?\s*(.*)$"
)

EPILOGUE = {"\u0425\u041e\u0422\u0418\u041c\u0410", "\u042d\u041f\u0418\u041b\u041e\u0413",
            "XOTIMA", "EPILOG"}

def is_heading(line):
    s = line.strip()
    if not s or len(s) > 80:
        return None
    if s in EPILOGUE:
        return s
    m = HEAD_RE.match(s)
    if not m:
        return None
    prefix, _bob, title = m.group(1), m.group(2), m.group(3)
    # must start with БОБ/BOB or a roman / ordinal-word prefix
    if prefix is None and not (s.startswith("\u0411\u041e\u0411") or s.startswith("BOB")):
        return None
    title = title.strip(" .\u2014-")
    if len(title) > 64:
        return None
    return title

def load_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")

def clean_lines(raw, cut_at=None):
    if cut_at:
        raw = raw[:cut_at]
    # frequency of short lines -> repeated running headers.
    # Restrict to UPPERCASE-dominant lines so we never strip real dialogue
    # like "Garri." or "Germiona." that legitimately repeats.
    freq = {}
    for ln in raw:
        s = ln.strip()
        if s and len(s) < 50 and s == s.upper() and any(c.isalpha() for c in s):
            freq[s] = freq.get(s, 0) + 1
    repeated = set(s for s, c in freq.items()
                   if c > 4 and not is_heading(s) and not PAGENUM.match(s))
    out = []
    for ln in raw:
        s = ln.strip()
        if not s:
            out.append("")           # keep blank as a soft separator
            continue
        if PAGENUM.match(ln):
            continue
        if WATERMARK.search(s):
            continue
        if s in repeated:
            continue
        out.append(ln.rstrip())
    return out

def split_chapters(lines):
    """Return list of (title, [body_lines]). Lines before the first heading
    (front matter) are dropped."""
    chapters = []
    cur_title, cur_body = None, []
    for ln in lines:
        t = is_heading(ln)
        if t is not None:
            if cur_title is not None:
                chapters.append((cur_title, cur_body))
            cur_title, cur_body = (t if t else "Bob"), []
        else:
            if cur_title is not None:
                cur_body.append(ln)
    if cur_title is not None:
        chapters.append((cur_title, cur_body))
    return chapters

SEP_RE = re.compile(r"^[\s*\u2022\u25c6\u25cf\u2727\u2731.\u2014\u2013-]{3,}$")

def reflow(body):
    """Re-assemble hard-wrapped lines into paragraphs / scene separators."""
    widths = [len(l) for l in body if l.strip()]
    if widths:
        widths.sort()
        maxw = widths[int(len(widths) * 0.9)]
    else:
        maxw = 80
    thresh = max(40, maxw - 12)
    paras, cur = [], []

    def flush():
        if cur:
            paras.append(" ".join(x.strip() for x in cur).strip())
            cur.clear()

    for raw in body:
        s = raw.strip()
        if not s:
            flush(); continue
        if SEP_RE.match(s) and len(s) <= 12:
            flush(); paras.append("@@SEP@@"); continue
        dialogue = s[0] in "-\u2013\u2014"
        indented = (len(raw) - len(raw.lstrip())) >= 2
        if cur and (dialogue or indented):
            flush()
        cur.append(s)
        if len(s) < thresh:
            flush()
    flush()
    # collapse consecutive separators / leading-trailing seps
    cleaned = []
    for p in paras:
        if p == "@@SEP@@" and (not cleaned or cleaned[-1] == "@@SEP@@"):
            continue
        cleaned.append(p)
    while cleaned and cleaned[0] == "@@SEP@@":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "@@SEP@@":
        cleaned.pop()
    return cleaned

def chapter_html(idx, title, paras):
    num = "XOTIMA" if title in EPILOGUE else ("%d-BOB" % (idx + 1))
    out = ['<section class="chapter" id="ch-%d">' % (idx + 1)]
    out.append('<div class="chapter-head"><div class="chapter-num">%s</div>'
               '<h2 class="chapter-title">%s</h2></div>' % (num, html.escape(title)))
    for p in paras:
        if p == "@@SEP@@":
            out.append('<div class="scene-sep">\u2727 \u2727 \u2727</div>')
        else:
            out.append("<p>%s</p>" % html.escape(p))
    out.append("</section>")
    return "\n".join(out)

# ----------------------------------------------------------------------------
# Shared glossary (books 1-7)
# ----------------------------------------------------------------------------
GLOSSARY = {
    "Qahramonlar": [
        ["Garri Potter", "Tirik qolgan bola; peshonasidagi chaqmoq izi bilan tanilgan bosh qahramon."],
        ["Ron Uizli", "Garrining sodiq do\u02bbsti, Uizlilar oilasining kenja o\u02bbg\u02bbli."],
        ["Germiona Greynjer", "Aqlli va kitobsevar jodugar; uchlikning uchinchi a'zosi."],
        ["Albus Dambldor", "Xogvarts maktabining donishmand bosh direktori."],
        ["Severus Snegg", "Iksirlar ustozi; sirli va ziddiyatli shaxs."],
        ["Lord Voldemort", "Nomi aytilmaydigan qora sehrgar; asosiy yovuz kuch."],
        ["Rubeus Hagrid", "Xogvarts o\u02bbrmonbonisi va Garrining mehribon do\u02bbsti."],
    ],
    "Joylar": [
        ["Xogvarts", "Sehrgarlik va jodugarlik maktabi."],
        ["Diagon xiyoboni", "Sehrli savdo ko\u02bbchasi."],
        ["To\u02bbqqiz-uchdan-bir platforma", "Xogvarts ekspressiga chiqiladigan sirli platforma."],
        ["Sehrgarlik vazirligi", "Sehrli dunyo hukumati."],
    ],
    "Sehrlar": [
        ["Expelliarmus", "Qurolsizlantirish sehri."],
        ["Lumos", "Hassa uchini yorituvchi sehr."],
        ["Expecto Patronum", "Dementorlardan himoya qiluvchi homiy sehri."],
        ["Wingardium Leviosa", "Buyumlarni havoga ko\u02bbtaruvchi sehr."],
    ],
    "Atamalar": [
        ["Maripat (Magl)", "Sehrli qobiliyatga ega bo\u02bblmagan oddiy odam."],
        ["Kviddich", "Supurgilarda o\u02bbynaladigan sehrli sport o\u02bbyini."],
        ["Dementor", "Baxtni so\u02bbruvchi qorong\u02bbu maxluq."],
        ["Fakultetlar", "Gryffindor, Slizerin, Puffenduy va Kogtevran."],
    ],
}

# ----------------------------------------------------------------------------
# Assemble readers
# ----------------------------------------------------------------------------
def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def patch_engine(app_js, part2_js):
    app_js = app_js.replace('var KEY = "gp_reader_v2";',
                            'var KEY = (window.BOOK && window.BOOK.key) || "gp_reader_v2";')
    part2_js = part2_js.replace('var GLOSSARY = {',
                                'var GLOSSARY = (window.BOOK && window.BOOK.glossary) || {', 1)
    return app_js, part2_js

def build_book(book, head, chrome_top, chrome_bot, app_js, part2_js):
    path = os.path.join(BOOKDIR, book["folder"], "matn.txt")
    raw = load_lines(path)
    lines = clean_lines(raw, book.get("cut_at"))
    chapters = split_chapters(lines)
    parts = []
    total_words = 0
    for i, (title, body) in enumerate(chapters):
        paras = reflow(body)
        total_words += sum(len(p.split()) for p in paras if p != "@@SEP@@")
        parts.append(chapter_html(i, title, paras))
    chapters_html = "\n".join(parts)

    disp = html.escape(book["title"])
    # head: title + accent
    h = head.replace("<title>GARRI POTTER VA LA&#x27;NATLANGAN BOLA</title>",
                     "<title>Garri Potter \u2014 %s</title>" % disp)
    h = h.replace('  --accent: #7b1113;',
                  '  --accent: %s;' % book["accent"])
    # chrome_top: topbar title + cover
    ct = chrome_top.replace(
        '<span class="title" id="cur-chapter-title">GARRI POTTER VA LA&#x27;NATLANGAN BOLA</span>',
        '<span class="title" id="cur-chapter-title">%s</span>' % disp)
    ct = ct.replace('<h1 class="big">GARRI POTTER VA LA&#x27;NATLANGAN BOLA</h1>',
                    '<h1 class="big">%s</h1>' % disp)
    ct = ct.replace('<div class="sub">Roman<br>J.K. Rouling, Jon Tiffani, Jek Torn pyesasiga asoslangan</div>',
                    '<div class="sub">%s<br>J.K. Rouling</div>' % html.escape(book["sub"]))
    h = h.replace('href="icons/icon.svg"', 'href="%s"' % FAVICON)
    # back-to-library button before the TOC button.
    # Works both standalone (navigate to index.html) and inside the library
    # iframe (postMessage so the shell can hide the viewer without a reload).
    ct = ct.replace(
        '<button class="iconbtn" id="btn-toc" title="Mundarija (C)" aria-label="Mundarija">',
        '<a class="iconbtn" href="index.html" title="Kutubxona" aria-label="Kutubxona" '
        'style="text-decoration:none" '
        "onclick=\"if(window.parent!==window){window.parent.postMessage('gp-back','*');return false;}\">"
        '<svg viewBox="0 0 24 24"><path d="M3 7v13h18V7M3 7l3-4h12l3 4M3 7h18"/>'
        '<line x1="12" y1="3" x2="12" y2="20"/></svg></a>'
        '<button class="iconbtn" id="btn-toc" title="Mundarija (C)" aria-label="Mundarija">')

    cfg = {"key": book["key"], "id": book["n"], "title": book["title"]}
    if book["n"] != 8:
        cfg["glossary"] = GLOSSARY
    cfg_script = "<script>window.BOOK=%s;</script>\n" % json.dumps(cfg, ensure_ascii=False)

    final = (h.rstrip() + "\n" + ct.rstrip() + "\n" + chapters_html + "\n"
             + chrome_bot.rstrip() + "\n" + cfg_script
             + "<script>\n" + app_js.rstrip() + "\n" + part2_js.rstrip()
             + "\n</script>\n</body>\n</html>\n")
    return final, len(chapters), total_words

def build_single(summary, readers):
    # Single self-contained file (per the spec's "platforma bitta HTML fayl").
    # Every book is embedded, but as an INERT <script type="text/plain"> block
    # rather than a parsed JS object, so the browser does NOT parse ~13MB of
    # book HTML as JavaScript on startup. A book is only read out and rendered
    # (via the viewer iframe's srcdoc) when the reader actually opens it.
    books_json = json.dumps(summary, ensure_ascii=False)
    # Escape only the closing script tag so the inner reader HTML cannot break
    # out of its text/plain wrapper. openBook() reverses this before rendering.
    data_blocks = "\n".join(
        '<script type="text/plain" id="bookdata-%d">%s</script>'
        % (n, readers[n].replace("</script>", "<\\/script>"))
        for n in sorted(readers)
    )
    crest = (
        '<svg class="crest" viewBox="0 0 64 64" aria-hidden="true">'
        '<path d="M32 3l24 9v16c0 14-10 24-24 30C18 52 8 42 8 28V12z" fill="none" '
        'stroke="currentColor" stroke-width="2.5"/>'
        '<path d="M32 14c4 5 4 10 0 15-4-5-4-10 0-15z" fill="currentColor"/>'
        '<circle cx="32" cy="36" r="4" fill="none" stroke="currentColor" stroke-width="2"/>'
        '<path d="M22 44h20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
    )
    css = """
:root{--bg:#faf8f3;--bg2:#f1ede3;--fg:#2b2b2b;--muted:#7a7368;--accent:#7b1113;
--panel:#fff;--panel2:#f6f3ec;--border:#e6e0d4;--shadow:rgba(40,30,10,.14);--shadow2:rgba(40,30,10,.28);}
[data-theme="sepia"]{--bg:#f4ecd8;--bg2:#ece1c6;--fg:#4b3f2f;--muted:#8a795d;--accent:#8a5a1a;--panel:#fbf4e3;--panel2:#f2e8cf;--border:#e3d6b8;--shadow:rgba(80,55,15,.16);--shadow2:rgba(80,55,15,.3);}
[data-theme="dark"]{--bg:#1a1c20;--bg2:#15171a;--fg:#d6d9dd;--muted:#8b9197;--accent:#e0934a;--panel:#23262c;--panel2:#2b2f36;--border:#353a42;--shadow:rgba(0,0,0,.45);--shadow2:rgba(0,0,0,.65);}
[data-theme="amoled"]{--bg:#000;--bg2:#050505;--fg:#d8dadd;--muted:#7f8489;--accent:#d98a3d;--panel:#0c0c0e;--panel2:#131316;--border:#232327;--shadow:rgba(0,0,0,.8);--shadow2:rgba(0,0,0,.95);}
[data-theme="night"]{--bg:#0f1726;--bg2:#0b111d;--fg:#c5d2e6;--muted:#7585a0;--accent:#5b9bd5;--panel:#162032;--panel2:#1c293f;--border:#273349;--shadow:rgba(0,0,0,.5);--shadow2:rgba(0,0,0,.7);}
[data-theme="warm"]{--bg:#fbeee0;--bg2:#f4e0cc;--fg:#432e1f;--muted:#9b7a5e;--accent:#c2541b;--panel:#fdf3e8;--panel2:#f6e6d4;--border:#ecd7bf;--shadow:rgba(120,70,20,.16);--shadow2:rgba(120,70,20,.3);}
*{box-sizing:border-box;}
#viewer{position:fixed;inset:0;width:100%;height:100%;border:0;z-index:60;background:var(--bg);}
body.reading{overflow:hidden;}
html,body{margin:0;padding:0;}
body{background:var(--bg);color:var(--fg);font-family:Georgia,'Times New Roman',serif;
-webkit-font-smoothing:antialiased;transition:background .3s,color .3s;min-height:100vh;}
.wrap{max-width:1100px;margin:0 auto;padding:1.2rem 1.1rem 4rem;}
header.top{display:flex;align-items:center;gap:.8rem;padding:.6rem 0 1.4rem;}
header.top .logo{display:flex;align-items:center;gap:.7rem;flex:1;min-width:0;}
header.top .crest{width:40px;height:40px;color:var(--accent);flex:none;}
header.top h1{font-size:1.25rem;margin:0;line-height:1.1;}
header.top h1 small{display:block;font-size:.72rem;color:var(--muted);font-weight:400;letter-spacing:.04em;text-transform:uppercase;margin-top:.15rem;font-family:system-ui,sans-serif;}
.theme-btn{width:42px;height:42px;border-radius:11px;border:1px solid var(--border);background:var(--panel);color:var(--fg);cursor:pointer;font-size:1.1rem;display:inline-flex;align-items:center;justify-content:center;}
.theme-pop{position:absolute;right:1.1rem;top:64px;background:var(--panel);border:1px solid var(--border);border-radius:14px;box-shadow:0 14px 40px var(--shadow2);padding:.6rem;display:none;grid-template-columns:repeat(4,1fr);gap:.4rem;z-index:20;}
.theme-pop.open{display:grid;}
.theme-pop button{width:46px;height:40px;border-radius:9px;border:2px solid var(--border);cursor:pointer;font-weight:700;font-family:Georgia,serif;}
.theme-pop button.sel{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent) inset;}
.hero{background:linear-gradient(135deg,var(--panel),var(--panel2));border:1px solid var(--border);
border-radius:20px;padding:1.3rem;margin-bottom:1.8rem;display:flex;gap:1.2rem;align-items:center;box-shadow:0 8px 28px var(--shadow);}
.hero .mini{width:74px;height:104px;border-radius:10px;flex:none;display:flex;align-items:center;justify-content:center;color:#fff;box-shadow:0 6px 18px var(--shadow2);}
.hero .mini .crest{width:42px;height:42px;color:#fff;}
.hero .info{flex:1;min-width:0;}
.hero .lbl{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);font-family:system-ui,sans-serif;font-weight:700;}
.hero h2{margin:.2rem 0 .3rem;font-size:1.3rem;}
.hero .pbar{height:6px;background:var(--bg2);border-radius:6px;overflow:hidden;margin:.7rem 0 .2rem;}
.hero .pbar i{display:block;height:100%;background:var(--accent);border-radius:6px;}
.hero .pct{font-size:.78rem;color:var(--muted);font-family:system-ui,sans-serif;}
.hero .go{margin-top:.8rem;display:inline-block;background:var(--accent);color:#fff;text-decoration:none;
padding:.6rem 1.3rem;border-radius:999px;font-family:system-ui,sans-serif;font-weight:600;font-size:.9rem;}
.section-title{font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);font-family:system-ui,sans-serif;font-weight:700;margin:0 0 .9rem;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1.1rem;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:16px;overflow:hidden;
text-decoration:none;color:inherit;display:flex;flex-direction:column;transition:transform .18s,box-shadow .18s,border-color .18s;}
.card:hover{transform:translateY(-4px);box-shadow:0 14px 34px var(--shadow2);border-color:var(--accent);}
.card .cover{height:158px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;position:relative;gap:.5rem;}
.card .cover .crest{width:48px;height:48px;color:rgba(255,255,255,.92);}
.card .cover .bnum{position:absolute;top:.6rem;left:.7rem;font-size:.72rem;font-family:system-ui,sans-serif;background:rgba(255,255,255,.2);padding:.15rem .5rem;border-radius:999px;}
.card .cover .done{position:absolute;top:.6rem;right:.7rem;font-size:.9rem;}
.card .meta{padding:.8rem .9rem 1rem;flex:1;display:flex;flex-direction:column;}
.card .meta h3{margin:0 0 .25rem;font-size:1.04rem;line-height:1.2;}
.card .meta .sub{font-size:.78rem;color:var(--muted);font-family:system-ui,sans-serif;flex:1;}
.card .meta .stat{font-size:.72rem;color:var(--muted);font-family:system-ui,sans-serif;margin-top:.55rem;display:flex;justify-content:space-between;}
.card .pbar{height:5px;background:var(--bg2);border-radius:5px;overflow:hidden;margin-top:.55rem;}
.card .pbar i{display:block;height:100%;background:var(--accent);}
footer{text-align:center;color:var(--muted);font-size:.8rem;font-family:system-ui,sans-serif;margin-top:2.5rem;}
@media(max-width:560px){.grid{grid-template-columns:repeat(2,1fr);gap:.7rem;}
.card .cover{height:130px;}.hero{flex-direction:column;text-align:center;}.hero .info{text-align:center;}}
"""
    js = """
var BOOKS=__BOOKS__;
var COVERS={1:'#7b1113',2:'#1f6f4a',3:'#5b3a8a',4:'#b5651d',5:'#1d6fa5',6:'#7a5901',7:'#3a3a3a',8:'#0b5d63'};
var THEMES=[['day','Light','#faf8f3','#7b1113'],['sepia','Sepia','#f4ecd8','#8a5a1a'],
['dark','Dark','#1a1c20','#e0934a'],['amoled','AMOLED','#000','#d98a3d'],
['night','Night','#0f1726','#5b9bd5'],['warm','Warm','#fbeee0','#c2541b']];
function gv(c){return 'linear-gradient(150deg,'+c+',rgba(0,0,0,.35))';}
function prog(key){try{var d=JSON.parse(localStorage.getItem(key));return (d&&d.progress&&d.progress.pct)||0;}catch(e){return 0;}}
function esc(s){return String(s).replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
function fmtW(w){return w>=1000?Math.round(w/1000)+'k':w;}
var CREST='__CREST__';
function render(){
  var grid=document.getElementById('grid');
  grid.innerHTML=BOOKS.map(function(b){
    var p=prog(b.key);var col=COVERS[b.n]||b.accent;
    return '<a class="card" href="javascript:void(0)" onclick="openBook('+b.n+');return false;">'+
      '<div class="cover" style="background:'+gv(col)+'">'+
        '<span class="bnum">'+b.n+'-kitob</span>'+(p>=99?'<span class="done">\\u2713</span>':'')+
        CREST+'</div>'+
      '<div class="meta"><h3>'+esc(b.title)+'</h3>'+
        '<div class="sub">'+esc(b.sub)+'</div>'+
        '<div class="stat"><span>'+b.chapters+' bob</span><span>'+fmtW(b.words)+" so'z</span></div>"+
        (p>0?'<div class="pbar"><i style="width:'+p+'%"></i></div>':'')+
      '</div></a>';
  }).join('');
  renderHero();
}
function renderHero(){
  var host=document.getElementById('hero');var last=null;
  try{last=JSON.parse(localStorage.getItem('gp_last_book'));}catch(e){}
  var b=null;
  if(last&&last.id){b=BOOKS.filter(function(x){return x.n===last.id;})[0];}
  if(!b){host.style.display='none';return;}
  var p=prog(b.key);var col=COVERS[b.n]||b.accent;
  host.style.display='flex';
  host.innerHTML='<div class="mini" style="background:'+gv(col)+'">'+CREST+'</div>'+
    '<div class="info"><div class="lbl">Davom etish</div><h2>'+esc(b.title)+'</h2>'+
    '<div class="pbar"><i style="width:'+p+'%"></i></div>'+
    '<div class="pct">'+p+'% o\\'qildi \\u00b7 '+b.chapters+' bob</div>'+
    '<a class="go" href="javascript:void(0)" onclick="openBook('+b.n+');return false;">O\\'qishni davom ettirish</a></div>';
}
// theme
var root=document.documentElement;
function applyTheme(t){root.setAttribute('data-theme',t);try{localStorage.setItem('gp_library_theme',t);}catch(e){}
  var mc=document.getElementById('mtc');if(mc){var m={day:'#7b1113',sepia:'#8a5a1a',dark:'#1a1c20',amoled:'#000',night:'#0f1726',warm:'#c2541b'};mc.setAttribute('content',m[t]||'#7b1113');}
  Array.prototype.forEach.call(document.querySelectorAll('.theme-pop button'),function(x){x.classList.toggle('sel',x.dataset.t===t);});}
function buildThemePop(){var p=document.getElementById('themepop');
  p.innerHTML=THEMES.map(function(t){return '<button data-t="'+t[0]+'" title="'+t[1]+'" style="background:'+t[2]+';color:'+t[3]+'">Aa</button>';}).join('');
  Array.prototype.forEach.call(p.querySelectorAll('button'),function(x){x.onclick=function(){applyTheme(x.dataset.t);};});}
document.getElementById('themebtn').onclick=function(e){e.stopPropagation();document.getElementById('themepop').classList.toggle('open');};
document.addEventListener('click',function(){document.getElementById('themepop').classList.remove('open');});
function openBook(n){
  var v=document.getElementById('viewer');
  var el=document.getElementById('bookdata-'+n);
  // restore the escaped closing script tag, then render only this book
  var bad='<'+String.fromCharCode(92)+'/script>';var good='<'+'/script>';
  v.srcdoc=el?el.textContent.split(bad).join(good):'';
  v.hidden=false;
  document.getElementById('lib').style.display='none';
  document.body.classList.add('reading');
  try{location.hash='kitob-'+n;}catch(e){}
}
function showLibrary(){
  var v=document.getElementById('viewer');
  v.hidden=true; v.removeAttribute('srcdoc');
  document.getElementById('lib').style.display='';
  document.body.classList.remove('reading');
  try{if(location.hash){history.replaceState(null,'',location.pathname+location.search);}}catch(e){}
  render();
}
window.addEventListener('message',function(e){if(e&&e.data==='gp-back'){showLibrary();}});
window.addEventListener('hashchange',function(){
  var m=/kitob-(\\d+)/.exec(location.hash);
  if(m){if(document.getElementById('viewer').hidden){openBook(+m[1]);}}
  else{if(!document.getElementById('viewer').hidden){showLibrary();}}
});
var savedTheme='day';try{savedTheme=localStorage.getItem('gp_library_theme')||'day';}catch(e){}
buildThemePop();applyTheme(savedTheme);render();
(function(){var m=/kitob-(\\d+)/.exec(location.hash);if(m){openBook(+m[1]);}})();
"""
    js = js.replace("__BOOKS__", books_json).replace("__CREST__", crest)
    doc = (
        '<!DOCTYPE html>\n<html lang="uz" data-theme="day">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n'
        '<meta name="theme-color" content="#7b1113" id="mtc">\n'
        '<meta name="description" content="Garri Potter \u2014 o\'zbekcha elektron kutubxona. 8 kitob, premium o\'quvchi.">\n'
        '<link rel="icon" type="image/svg+xml" href="' + FAVICON + '">\n'
        '<title>Garri Potter \u2014 Kutubxona</title>\n<style>' + css + '</style>\n</head>\n<body>\n'
        '<div id="themepop" class="theme-pop"></div>\n'
        '<div class="wrap" id="lib">\n'
        '<header class="top"><span class="logo">'
        + crest.replace('class="crest"', 'class="crest"')
        + '<h1>Garri Potter<small>O\'zbekcha kutubxona \u00b7 8 kitob</small></h1></span>'
        '<button class="theme-btn" id="themebtn" title="Mavzu" aria-label="Mavzu">\u25d0</button></header>\n'
        '<div class="hero" id="hero"></div>\n'
        '<div class="section-title">Barcha kitoblar</div>\n'
        '<div class="grid" id="grid"></div>\n'
        '<footer>J.K. Rouling \u00b7 o\'zbek tilidagi tarjima \u00b7 Premium Reader</footer>\n'
        '</div>\n'
        '<iframe id="viewer" hidden title="O\'qish oynasi"></iframe>\n'
        + data_blocks + '\n'
        '<script>\n' + js + '\n</script>\n</body>\n</html>\n'
    )
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)


def main():
    head = read(os.path.join(BASE, "head.html"))
    chrome_top = read(os.path.join(BASE, "chrome_top.html"))
    chrome_bot = read(os.path.join(BASE, "chrome_bottom.html"))
    app_js = read(os.path.join(BASE, "app.js"))
    part2_js = read(os.path.join(BASE, "part2.js"))
    app_js, part2_js = patch_engine(app_js, part2_js)

    summary = []
    readers = {}
    for b in BOOKS:
        rh, nch, nw = build_book(b, head, chrome_top, chrome_bot, app_js, part2_js)
        readers[b["n"]] = rh
        summary.append(dict(n=b["n"], key=b["key"], title=b["title"], sub=b["sub"],
                            accent=b["accent"], chapters=nch, words=nw))
        print("kitob-%d  %-20s  boblar=%-3d  so'z=%-7d  %d KB"
              % (b["n"], b["title"], nch, nw, len(rh) // 1024))
    build_single(summary, readers)
    sz = os.path.getsize(os.path.join(ROOT, "index.html"))
    print("index.html (yagona self-contained fayl): %.2f MB" % (sz / 1048576))
    return summary

if __name__ == "__main__":
    main()
