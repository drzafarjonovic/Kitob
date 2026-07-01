#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium reader quruvchi.
`index.html` ichidagi reader-shell shablonini oladi, `boblar/Bob_*.html`
tarjimalarini bitta premium o'quvchi HTMLga yig'adi.
Har yangi bob qo'shilganda qayta ishga tushiriladi:
    python3 Tarjima/build_reader.py
Natija: Tarjima/Garri_Potter_va_Lanatlangan_Bola.html
"""
import os, re, glob, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BOBLAR = os.path.join(ROOT, "Tarjima", "boblar")
OUT = os.path.join(ROOT, "Tarjima", "Garri_Potter_va_Lanatlangan_Bola.html")

TITLE = "ЛАЪНАТЛАНГАН БОЛА"
SUB = "Гарри Поттер ва Лаънатланган бола"
ACCENT = "#7b1113"
BOOKCFG = {"id": "cursed-child-uz", "key": "gp_cursed_child_uz", "title": TITLE}


def extract_shell():
    """index.html dan reader-shell shablonini ajratib, escaped script'larni tiklaydi."""
    with open(INDEX, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    m = re.search(r'<script[^>]*id="reader-shell"[^>]*>', html)
    if not m:
        raise SystemExit("reader-shell topilmadi")
    start = m.end()
    end = html.index("</script>", start)  # birinchi escaped BO'LMAGAN </script>
    shell = html[start:end]
    shell = shell.replace(r"<\/script>", "</script>")  # escaped -> real
    return shell


def parse_chapter(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    t = re.search(r'<h2 class="heading">\s*(.*?)\s*</h2>', html, re.S)
    raw_title = re.sub(r"\s+", " ", t.group(1)).strip() if t else "БОБ"
    # "1-боб. Матн" -> num="1-БОБ", title="МАТН"
    mm = re.match(r"\s*(\d+)\s*-\s*боб\.?\s*(.*)", raw_title, re.I)
    if mm:
        num = mm.group(1) + "-БОБ"
        title = mm.group(2).strip().upper()
    else:
        num, title = "", raw_title.upper()
    # userstuff ichidagi paragraflar
    body = re.search(r'<div class="userstuff">(.*?)</div>', html, re.S)
    body = body.group(1) if body else html
    paras = re.findall(r"<p>.*?</p>", body, re.S)
    out = []
    for p in paras:
        inner = re.sub(r"</?p>", "", p).strip()
        if inner == "+++":
            out.append('<p style="text-align:center;letter-spacing:.5em;color:var(--muted);margin:1.6em 0">&#10023; &#10023; &#10023;</p>')
        else:
            out.append("<p>" + inner + "</p>")
    return num, title, "\n".join(out)


def num_key(path):
    m = re.search(r"Bob_(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else 0


def main():
    files = sorted(glob.glob(os.path.join(BOBLAR, "Bob_*.html")), key=num_key)
    if not files:
        raise SystemExit("boblar/ ichida Bob_*.html topilmadi")
    sections = []
    for i, path in enumerate(files, 1):
        num, title, para_html = parse_chapter(path)
        head = '<div class="chapter-head">'
        if num:
            head += '<div class="chapter-num">%s</div>' % num
        head += '<h2 class="chapter-title">%s</h2></div>' % title
        sections.append(
            '<section class="chapter" id="ch-%d">\n%s\n%s\n</section>' % (i, head, para_html)
        )
    chapters_html = "\n".join(sections)

    shell = extract_shell()
    shell = shell.replace("@@TITLE@@", TITLE)
    shell = shell.replace("@@SUB@@", SUB)
    shell = shell.replace("@@ACCENT@@", ACCENT)
    shell = shell.replace("@@CHAPTERS@@", chapters_html)
    shell = shell.replace("@@BOOKCFG@@", json.dumps(BOOKCFG, ensure_ascii=False))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(shell)
    print("Yozildi: %s  (%d bob)" % (OUT, len(files)))


if __name__ == "__main__":
    main()
