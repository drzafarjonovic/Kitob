#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_pdf.py — "Garri Potter va La'natlangan Bola" romanini chop etishga tayyor
bitta PDF kitobga jamlaydi. Sof Python stdlib (tashqi kutubxonasiz).

Texnika: standart PDF shriftlari (Times-Roman / Times-Bold, WinAnsiEncoding).
Matndagi yagona ASCII bo'lmagan belgi — uzun tire (—, U+2014) — WinAnsi'da
0x97 baytiga moslanadi. Justifikatsiya (ikki tomonga tekislash) Tw (word
spacing) operatori orqali amalga oshiriladi. Kitob formati 6x9 dyuym.
"""

import os
import re
import sys
import zlib

# Skript arxiv/ papkasida, manba va chiqish fayllari esa loyiha ildizida.
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "Garri_Potter_va_Lanatlangan_Bola_Roman.txt")
OUT = os.path.join(ROOT, "Garri_Potter_va_Lanatlangan_Bola.pdf")

# --- Sahifa geometriyasi (1 dyuym = 72 punkt). 6 x 9 dyuym kitob ---
PAGE_W = 432.0   # 6"
PAGE_H = 648.0   # 9"
MARGIN_X = 54.0
MARGIN_TOP = 60.0
MARGIN_BOT = 64.0
TEXT_W = PAGE_W - 2 * MARGIN_X
TOP_Y = PAGE_H - MARGIN_TOP        # birinchi qator bazasi shu yerdan pastda boshlanadi

# Matn parametrlari
BODY_FS = 11.0
BODY_LEAD = 16.5
CH_TITLE_FS = 17.0
CH_NUM_FS = 10.0
PARA_INDENT = 18.0      # paragraf qizil qatori (punkt)
SCENE_GAP = BODY_LEAD   # sahna ajratgichi atrofidagi bo'shliq

CHAPTER_RE = re.compile(r"^([IVXLC]+)\s+BOB\.\s+(.+)$")
SCENE_SEP = "* * *"

# --- AFM kenglik jadvallari (1000 em birligida) ---
TIMES_ROMAN = {
    ' ':250,'!':333,'"':408,'#':500,'$':500,'%':833,'&':778,"'":180,'(':333,')':333,
    '*':500,'+':564,',':250,'-':333,'.':250,'/':278,'0':500,'1':500,'2':500,'3':500,
    '4':500,'5':500,'6':500,'7':500,'8':500,'9':500,':':278,';':278,'<':564,'=':564,
    '>':564,'?':444,'@':921,'A':722,'B':667,'C':667,'D':722,'E':611,'F':556,'G':722,
    'H':722,'I':333,'J':389,'K':722,'L':611,'M':889,'N':722,'O':722,'P':556,'Q':722,
    'R':667,'S':556,'T':611,'U':722,'V':722,'W':944,'X':722,'Y':722,'Z':611,'[':333,
    '\\':278,']':333,'^':469,'_':500,'`':333,'a':444,'b':500,'c':444,'d':500,'e':444,
    'f':333,'g':500,'h':500,'i':278,'j':278,'k':500,'l':278,'m':778,'n':500,'o':500,
    'p':500,'q':500,'r':333,'s':389,'t':278,'u':500,'v':500,'w':722,'x':500,'y':500,
    'z':444,'{':480,'|':200,'}':480,'~':541,'\u2014':1000,
}
TIMES_BOLD = {
    ' ':250,'!':333,'"':555,'#':500,'$':500,'%':1000,'&':833,"'":278,'(':333,')':333,
    '*':500,'+':570,',':250,'-':333,'.':250,'/':278,'0':500,'1':500,'2':500,'3':500,
    '4':500,'5':500,'6':500,'7':500,'8':500,'9':500,':':333,';':333,'<':570,'=':570,
    '>':570,'?':500,'@':930,'A':722,'B':667,'C':722,'D':722,'E':667,'F':611,'G':778,
    'H':778,'I':389,'J':500,'K':778,'L':667,'M':944,'N':722,'O':778,'P':611,'Q':778,
    'R':722,'S':556,'T':667,'U':722,'V':722,'W':1000,'X':722,'Y':722,'Z':667,'[':333,
    '\\':278,']':333,'^':581,'_':500,'`':333,'a':500,'b':556,'c':444,'d':556,'e':444,
    'f':333,'g':500,'h':556,'i':278,'j':333,'k':556,'l':278,'m':833,'n':556,'o':500,
    'p':556,'q':556,'r':444,'s':389,'t':333,'u':556,'v':500,'w':722,'x':500,'y':500,
    'z':444,'{':394,'|':220,'}':394,'~':520,'\u2014':1000,
}


def char_w(ch, table, fs):
    return table.get(ch, 500) / 1000.0 * fs


def text_width(s, table, fs):
    return sum(char_w(c, table, fs) for c in s)


def pdf_escape(s):
    """Matnni WinAnsi baytlariga o'tkazadi (em-dash -> 0x97) va PDF satr uchun
    maxsus belgilarni qochiradi. Bytes qaytaradi."""
    s = s.replace('\u2014', '\x97')
    s = s.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')
    return s.encode('latin-1', 'replace')


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse(text):
    lines = text.replace('\r\n', '\n').split('\n')
    title_block, chapters, cur, i = [], [], None, 0
    while i < len(lines):
        if CHAPTER_RE.match(lines[i].strip()):
            break
        title_block.append(lines[i].strip())
        i += 1
    while i < len(lines):
        m = CHAPTER_RE.match(lines[i].strip())
        if m:
            if cur:
                chapters.append(cur)
            cur = {'num': m.group(1), 'title': m.group(2).strip(), 'body': []}
        elif cur is not None:
            cur['body'].append(lines[i])
        i += 1
    if cur:
        chapters.append(cur)
    return [t for t in title_block if t], chapters


def chapter_blocks(body):
    """Bob tanasini ('p', matn) yoki ('sep', None) bloklariga ajratadi."""
    blocks, buf = [], []

    def flush():
        if buf:
            para = ' '.join(x.strip() for x in buf if x.strip())
            if para:
                blocks.append(('p', para))
            buf.clear()

    for raw in body:
        s = raw.strip()
        if s == SCENE_SEP:
            flush(); blocks.append(('sep', None))
        elif s == '':
            flush()
        else:
            buf.append(s)
    flush()
    return blocks


def wrap_words(words, table, fs, max_w):
    """So'zlarni qatorlarga bo'ladi. Har qator so'zlar ro'yxati."""
    lines, cur, cur_w = [], [], 0.0
    space_w = char_w(' ', table, fs)
    for w in words:
        ww = text_width(w, table, fs)
        if not cur:
            cur, cur_w = [w], ww
        elif cur_w + space_w + ww <= max_w:
            cur.append(w); cur_w += space_w + ww
        else:
            lines.append(cur); cur, cur_w = [w], ww
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Layout -> qatorlar oqimi (har biri sahifaga joylanadigan element)
# Har element: dict(type, ...) bilan y-yuqoridan-pastga tartibda.
# ---------------------------------------------------------------------------
class LineFlow:
    """Sahifalarga bo'lish uchun "qatorlar" oqimini yaratadi."""
    def __init__(self):
        self.items = []  # ketma-ket joylashtiriladigan elementlar

    def add(self, **kw):
        self.items.append(kw)


def build_flow(chapters):
    flow = LineFlow()
    for ci, ch in enumerate(chapters):
        # Har bob yangi sahifadan
        flow.add(type='pagebreak')
        # Bob sarlavhasidan oldin bo'shliq
        flow.add(type='space', h=70)
        flow.add(type='center', font='B', fs=CH_NUM_FS,
                 text=ch['num'] + ' BOB', leadafter=CH_NUM_FS * 2.0,
                 spaced=True)
        # Sarlavha (kerak bo'lsa ko'p qatorga)
        title = ch['title']
        title_lines = wrap_words(title.split(), TIMES_BOLD, CH_TITLE_FS, TEXT_W)
        for tl in title_lines:
            flow.add(type='center', font='B', fs=CH_TITLE_FS,
                     text=' '.join(tl), leadafter=CH_TITLE_FS * 1.3)
        flow.add(type='rule', leadafter=BODY_LEAD * 1.6)

        first_para = True
        for kind, val in chapter_blocks(ch['body']):
            if kind == 'sep':
                flow.add(type='center', font='R', fs=BODY_FS, text='* * *',
                         leadbefore=SCENE_GAP, leadafter=SCENE_GAP, spaced_seps=True)
                first_para = True
                continue
            words = val.split()
            indent = 0.0 if first_para else PARA_INDENT
            # Birinchi qator chekinish (indent) bilan, qolganlari to'liq kenglikda
            lines = wrap_words_indent(words, TIMES_ROMAN, BODY_FS, TEXT_W, indent)
            n = len(lines)
            for li, ln in enumerate(lines):
                last = (li == n - 1)
                flow.add(type='body', words=ln['words'],
                         indent=ln['indent'], justify=not last)
            first_para = False
    return flow


def wrap_words_indent(words, table, fs, max_w, first_indent):
    """Birinchi qatorda chekinish (indent) hisobga olingan word-wrap."""
    lines, cur, cur_w = [], [], 0.0
    space_w = char_w(' ', table, fs)
    avail = max_w - first_indent
    indent = first_indent
    for w in words:
        ww = text_width(w, table, fs)
        if not cur:
            cur, cur_w = [w], ww
        elif cur_w + space_w + ww <= avail:
            cur.append(w); cur_w += space_w + ww
        else:
            lines.append({'words': cur, 'indent': indent})
            cur, cur_w = [w], ww
            indent = 0.0
            avail = max_w
    if cur:
        lines.append({'words': cur, 'indent': indent})
    return lines


# ---------------------------------------------------------------------------
# Flow -> sahifalar (content stream)
# ---------------------------------------------------------------------------
def emit_pages(flow):
    pages = []          # har biri content stream stringlari ro'yxati
    cur = []
    y = TOP_Y
    space_w = char_w(' ', TIMES_ROMAN, BODY_FS)

    def new_page():
        nonlocal cur, y
        if cur:
            pages.append(cur)
        cur = []
        y = TOP_Y

    def ensure(h):
        """Joriy sahifada h balandlik bo'lmasa, yangi sahifa ochadi."""
        nonlocal y
        if y - h < MARGIN_BOT:
            new_page()

    for it in flow.items:
        t = it['type']
        if t == 'pagebreak':
            new_page()
        elif t == 'space':
            y -= it['h']
            if y < MARGIN_BOT:
                new_page()
        elif t == 'rule':
            # Markazda qisqa chiziq
            ensure(it.get('leadafter', BODY_LEAD))
            cx = PAGE_W / 2.0
            half = 28.0
            cur.append('0.5 G 0.7 w {:.1f} {:.1f} m {:.1f} {:.1f} l S 0 G'.format(
                cx - half, y, cx + half, y))
            y -= it.get('leadafter', BODY_LEAD)
        elif t == 'center':
            lb = it.get('leadbefore', 0.0)
            if lb:
                y -= lb
            ensure(it['fs'] + 4)
            table = TIMES_BOLD if it['font'] == 'B' else TIMES_ROMAN
            txt = it['text']
            charspace = 0.0
            if it.get('spaced'):
                charspace = 1.8   # "N BOB" — harflar orasini biroz ochish
            w = text_width(txt, table, it['fs']) + charspace * (len(txt) - 1)
            x = (PAGE_W - w) / 2.0
            fontname = 'F2' if it['font'] == 'B' else 'F1'
            tc = ' {:.2f} Tc'.format(charspace) if charspace else ' 0 Tc'
            cur.append('BT /{} {:.1f} Tf{} {:.2f} {:.2f} Td ({}) Tj ET'.format(
                fontname, it['fs'], tc, x, y, pdf_escape(txt).decode('latin-1')))
            y -= it.get('leadafter', it['fs'] * 1.3)
        elif t == 'body':
            ensure(BODY_LEAD)
            words = it['words']
            indent = it['indent']
            x = MARGIN_X + indent
            line_str = ' '.join(words)
            tw = 0.0
            if it['justify'] and len(words) > 1:
                natural = text_width(line_str, TIMES_ROMAN, BODY_FS)
                avail = TEXT_W - indent
                extra = avail - natural
                gaps = len(words) - 1
                if extra > 0 and gaps > 0:
                    tw = extra / gaps
                    # haddan tashqari cho'zilishni cheklash
                    if tw > BODY_FS * 0.5:
                        tw = BODY_FS * 0.5
            cur.append('BT /F1 {:.1f} Tf {:.3f} Tw {:.2f} {:.2f} Td ({}) Tj ET'.format(
                BODY_FS, tw, x, y, pdf_escape(line_str).decode('latin-1')))
            y -= BODY_LEAD
    new_page()
    return pages


# ---------------------------------------------------------------------------
# Title page
# ---------------------------------------------------------------------------
def make_title_page(title_block):
    cur = []
    title = title_block[0] if title_block else 'Roman'
    subs = title_block[1:]

    # Sarlavhani so'zlarga bo'lib markazga (katta shrift)
    big_fs = 24.0
    y = PAGE_H * 0.66
    tlines = wrap_words(title.split(), TIMES_BOLD, big_fs, TEXT_W)
    for tl in tlines:
        s = ' '.join(tl)
        w = text_width(s, TIMES_BOLD, big_fs)
        x = (PAGE_W - w) / 2.0
        cur.append('BT /F2 {:.1f} Tf {:.2f} {:.2f} Td ({}) Tj ET'.format(
            big_fs, x, y, pdf_escape(s).decode('latin-1')))
        y -= big_fs * 1.3

    # Bezak chiziq
    y -= 24
    cx = PAGE_W / 2.0
    cur.append('0.5 G 0.8 w {:.1f} {:.1f} m {:.1f} {:.1f} l S 0 G'.format(
        cx - 80, y, cx + 80, y))
    y -= 40

    for i, sub in enumerate(subs):
        fs = 12.0
        font = 'F1'
        italic = False
        for ln in wrap_words(sub.split(), TIMES_ROMAN, fs, TEXT_W):
            s = ' '.join(ln)
            w = text_width(s, TIMES_ROMAN, fs)
            x = (PAGE_W - w) / 2.0
            cur.append('BT /{} {:.1f} Tf {:.2f} {:.2f} Td ({}) Tj ET'.format(
                font, fs, x, y, pdf_escape(s).decode('latin-1')))
            y -= fs * 1.5
        y -= 6
    return cur


# ---------------------------------------------------------------------------
# PDF assembly
# ---------------------------------------------------------------------------
def add_page_number(stream_lines, page_index, total):
    """Sahifa raqamini pastga markazga qo'shadi (title page = 0 raqamsiz)."""
    num = str(page_index)
    fs = 9.0
    w = text_width(num, TIMES_ROMAN, fs)
    x = (PAGE_W - w) / 2.0
    y = MARGIN_BOT - 26
    if y < 12:
        y = 24
    stream_lines.append('BT /F1 {:.1f} Tf {:.2f} {:.2f} Td ({}) Tj ET'.format(
        fs, x, y, num))


def build_pdf(title_block, chapters):
    flow = build_flow(chapters)
    body_pages = emit_pages(flow)

    all_pages = [make_title_page(title_block)] + body_pages

    # Sahifa raqamlari (title sahifasidan keyin 2-betdan boshlab)
    for idx, p in enumerate(all_pages):
        if idx == 0:
            continue
        add_page_number(p, idx + 1, len(all_pages))

    # --- PDF obyektlarini yig'ish ---
    objects = []  # (id, bytes)

    def add_obj(data):
        objects.append(data)
        return len(objects)  # 1-asosli id

    # Fontlar
    f1_id = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman "
                    b"/Encoding /WinAnsiEncoding >>")
    f2_id = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold "
                    b"/Encoding /WinAnsiEncoding >>")

    page_ids = []
    content_ids = []
    # Pages obyekti id ni oldindan band qilamiz (keyin yoziladi)
    # Avval content va page obyektlarini yaratamiz, parent ni keyin biriktiramiz.
    # Parent id ni hisoblab qo'yamiz: barcha contents+pages dan keyin.
    # Soddalik uchun: avval contents, keyin page node lar, keyin Pages, keyin Catalog.

    for lines in all_pages:
        raw = ('\n'.join(lines)).encode('latin-1', 'replace')
        comp = zlib.compress(raw)
        stream = (b"<< /Length " + str(len(comp)).encode() +
                  b" /Filter /FlateDecode >>\nstream\n" + comp + b"\nendstream")
        cid = add_obj(stream)
        content_ids.append(cid)

    # Pages node id (keyin to'ldiriladi) — joy band qilamiz
    pages_node_id = len(objects) + len(all_pages) + 1

    for cid in content_ids:
        page_obj = (
            "<< /Type /Page /Parent {} 0 R "
            "/MediaBox [0 0 {:.2f} {:.2f}] "
            "/Resources << /Font << /F1 {} 0 R /F2 {} 0 R >> >> "
            "/Contents {} 0 R >>"
        ).format(pages_node_id, PAGE_W, PAGE_H, f1_id, f2_id, cid).encode()
        pid = add_obj(page_obj)
        page_ids.append(pid)

    kids = ' '.join('{} 0 R'.format(pid) for pid in page_ids)
    pages_obj = ("<< /Type /Pages /Count {} /Kids [{}] >>".format(
        len(page_ids), kids)).encode()
    real_pages_id = add_obj(pages_obj)
    assert real_pages_id == pages_node_id, (real_pages_id, pages_node_id)

    catalog_id = add_obj(
        ("<< /Type /Catalog /Pages {} 0 R >>".format(real_pages_id)).encode())

    # --- Faylni yozish ---
    out = bytearray()
    out += b"%PDF-1.5\n%\xe2\xe3\xcf\xd3\n"
    offsets = [0] * (len(objects) + 1)
    for i, data in enumerate(objects, start=1):
        offsets[i] = len(out)
        out += str(i).encode() + b" 0 obj\n" + data + b"\nendobj\n"

    xref_pos = len(out)
    n = len(objects) + 1
    out += b"xref\n0 " + str(n).encode() + b"\n"
    out += b"0000000000 65535 f \n"
    for i in range(1, n):
        out += "{:010d} 00000 n \n".format(offsets[i]).encode()
    out += (b"trailer\n<< /Size " + str(n).encode() +
            b" /Root " + str(catalog_id).encode() + b" 0 R >>\n")
    out += b"startxref\n" + str(xref_pos).encode() + b"\n%%EOF\n"

    return bytes(out), len(all_pages)


def main():
    with open(SRC, 'r', encoding='utf-8') as f:
        text = f.read()
    title_block, chapters = parse(text)
    if len(chapters) != 29:
        print("OGOHLANTIRISH: bob soni 29 emas:", len(chapters), file=sys.stderr)
    data, npages = build_pdf(title_block, chapters)
    with open(OUT, 'wb') as f:
        f.write(data)
    print("Yozildi:", OUT)
    print("Boblar:", len(chapters))
    print("Sahifalar:", npages)
    print("Hajm (KB):", round(len(data) / 1024, 1))


if __name__ == "__main__":
    main()
