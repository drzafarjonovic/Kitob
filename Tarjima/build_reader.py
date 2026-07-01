#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium reader quruvchi.
1) `boblar/Bob_*.html` tarjimalarini bitta standalone premium o'quvchiga yig'adi
   (Tarjima/Garri_Potter_va_Lanatlangan_Bola.html).
2) Aynan shu boblarni `index.html` kutubxonasiga 9-KITOB sifatida qo'shadi/yangilaydi
   (eski 8-kitobga TEGILMAYDI). Shunda ilovadagi to'liq premium reader (progress,
   davom etish, xatcho'p) bizning tarjimaga ham tatbiq etiladi.

Ishga tushirish (har yangi bobdan keyin):
    python3 Tarjima/build_reader.py

Eslatma: progress/saqlash top-sahifa (kutubxona) orqali ishlaydi — patch_index_storage.py
bir marta qo'llanган bo'lishi kerak (mobil brauzerlarda ham ishlashi uchun).
"""
import os, re, glob, json, html as htmlmod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BOBLAR = os.path.join(ROOT, "Tarjima", "boblar")
OUT = os.path.join(ROOT, "Tarjima", "Garri_Potter_va_Lanatlangan_Bola.html")

TITLE = "ЛАЪНАТЛАНГАН БОЛА"
SUB = "Гарри Поттер ва Лаънатланган бола"
ACCENT = "#7b1113"

# 8-kitob obyekti (BOOKS massivida) — 9-kitobни shundan keyin qo'shamiz. TEGILMAYDI.
N8 = ('{"n": 8, "key": "gp_reader_b8", "title": "La\'natlangan Bola", '
      '"sub": "Sakkizinchi kitob \u00b7 Sahna asari", "accent": "#0b5d63", '
      '"chapters": 29, "words": 40833, "gloss": false}')

SCENE_BREAK = ('<p style="text-align:center;letter-spacing:.5em;color:var(--muted);'
               'margin:1.6em 0">&#10023; &#10023; &#10023;</p>')


def parse_chapter(path):
    with open(path, "r", encoding="utf-8") as f:
        h = f.read()
    t = re.search(r'<h2 class="heading">\s*(.*?)\s*</h2>', h, re.S)
    raw = re.sub(r"\s+", " ", t.group(1)).strip() if t else "БОБ"
    mm = re.match(r"\s*(\d+)\s*-\s*боб\.?\s*(.*)", raw, re.I)
    if mm:
        num, title = mm.group(1) + "-БОБ", mm.group(2).strip().upper()
    else:
        num, title = "", raw.upper()
    body = re.search(r'<div class="userstuff">(.*?)</div>', h, re.S)
    body = body.group(1) if body else h
    paras = re.findall(r"<p>.*?</p>", body, re.S)
    out = []
    for p in paras:
        inner = re.sub(r"</?p>", "", p).strip()
        out.append(SCENE_BREAK if inner == "+++" else "<p>" + inner + "</p>")
    return num, title, out


def num_key(path):
    m = re.search(r"Bob_(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else 0


def build_sections(files):
    sections, words = [], 0
    for i, path in enumerate(files, 1):
        num, title, paras = parse_chapter(path)
        for p in paras:
            words += len(re.sub(r"<[^>]+>", "", p).split())
        head = '<div class="chapter-head">'
        if num:
            head += '<div class="chapter-num">%s</div>' % num
        head += '<h2 class="chapter-title">%s</h2></div>' % title
        sections.append('<section class="chapter" id="ch-%d">\n%s\n%s\n</section>'
                        % (i, head, "\n".join(paras)))
    return sections, words


def extract_shell(html):
    m = re.search(r'<script[^>]*id="reader-shell"[^>]*>', html)
    start = m.end()
    end = html.index("</script>", start)
    return html[start:end].replace(r"<\/script>", "</script>")


def build_standalone(html, chapters_html):
    shell = extract_shell(html)
    shell = (shell.replace("@@TITLE@@", TITLE).replace("@@SUB@@", SUB)
                  .replace("@@ACCENT@@", ACCENT)
                  .replace("@@SAVED@@", "null")
                  .replace("@@BOOKCFG@@", json.dumps(
                      {"id": "cursed-child-uz", "key": "gp_reader_b9", "title": TITLE},
                      ensure_ascii=False))
                  .replace("@@CHAPTERS@@", chapters_html))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(shell)


def inject_book9(html, chapters_html, nchap, nwords):
    data = chapters_html.replace("</script>", r"<\/script>")
    block = '<script type="text/plain" id="bookdata-9">' + data + "</script>"
    # bookdata-9: yaratish yoki yangilash
    if 'id="bookdata-9"' in html:
        html = re.sub(r'<script type="text/plain" id="bookdata-9">.*?</script>',
                      lambda m: block, html, count=1, flags=re.S)
    else:
        anchor = "</section></script>\n<script>\n\nvar BOOKS="
        assert html.count(anchor) == 1, "bookdata-8->library anchor topilmadi"
        html = html.replace(anchor, "</section></script>\n" + block + "\n<script>\n\nvar BOOKS=", 1)
    # BOOKS n:9 obyekti
    n9 = ('{"n": 9, "key": "gp_reader_b9", "title": "La\'natlangan Bola", '
          '"sub": "To\'qqizinchi kitob \u00b7 Yangi tarjima", "accent": "#7b1113", '
          '"chapters": %d, "words": %d, "gloss": false}' % (nchap, nwords))
    if '"gp_reader_b9"' in html.split("var BOOKS=", 1)[1][:4000]:
        html = re.sub(r'\{"n": 9,[^}]*\}', lambda m: n9, html, count=1)
    else:
        assert html.count(N8 + "]") == 1, "BOOKS n8 anchor topilmadi"
        html = html.replace(N8 + "]", N8 + ", " + n9 + "]", 1)
    # COVERS 9
    if ",9:'#" not in html:
        assert html.count("8:'#0b5d63'};") == 1, "COVERS anchor topilmadi"
        html = html.replace("8:'#0b5d63'};", "8:'#0b5d63',9:'#7b1113'};", 1)
    return html


def main():
    files = sorted(glob.glob(os.path.join(BOBLAR, "Bob_*.html")), key=num_key)
    if not files:
        raise SystemExit("boblar/ ichida Bob_*.html topilmadi")
    sections, words = build_sections(files)
    chapters_html = "\n".join(sections)

    html = open(INDEX, encoding="utf-8", errors="replace").read()
    build_standalone(html, chapters_html)
    html = inject_book9(html, chapters_html, len(files), words)
    open(INDEX, "w", encoding="utf-8").write(html)
    print("Yozildi: standalone reader + index.html 9-kitob (%d bob, ~%d so'z)" % (len(files), words))


if __name__ == "__main__":
    main()
