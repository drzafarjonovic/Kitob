#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pure-Python text extractor for the Book 6 PDF.

Classic PDF 1.5 (no object streams), Type0/Identity-H fonts with ToUnicode
CMaps and FlateDecode. We reconstruct text with correct word spaces and line
breaks by interpreting the text-showing operators together with glyph widths
(/W, /DW) and the text/line matrices.
"""
import re, sys, zlib

PDF = sys.argv[1] if len(sys.argv) > 1 else \
    "Garri Potter kitoblari/6 - Yarim Qonli Shahzoda/6. Garri Potter va Chalazot shaxzoda (1).pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/book6_extracted.txt"

data = open(PDF, "rb").read()

obj_re = re.compile(rb"(\d+)\s+\d+\s+obj\b(.*?)\bendobj", re.S)
objects = {int(m.group(1)): m.group(2) for m in obj_re.finditer(data)}

def dict_part(body):
    i = body.find(b"stream")
    return body[:i] if i >= 0 else body

def get_stream(body):
    if body is None:
        return None
    i = body.find(b"stream")
    if i < 0:
        return None
    j = i + len(b"stream")
    if body[j:j+2] == b"\r\n":
        j += 2
    elif body[j:j+1] in (b"\n", b"\r"):
        j += 1
    k = body.find(b"endstream", j)
    raw = body[j:k]
    if b"FlateDecode" in body[:i]:
        try:
            return zlib.decompress(raw)
        except Exception:
            return None
    return raw

# --- CMap (ToUnicode) ------------------------------------------------------
def hexstr_to_unicode(h):
    if len(h) <= 4:
        v = int(h, 16)
        return chr(v) if v <= 0x10FFFF else ""
    return "".join(chr(int(h[i:i+4], 16)) for i in range(0, len(h) - 3, 4))

def parse_cmap(b):
    m = {}
    s = b.decode("latin-1", "replace")
    for blk in re.findall(r"beginbfchar(.*?)endbfchar", s, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            m[int(src, 16)] = hexstr_to_unicode(dst)
    for blk in re.findall(r"beginbfrange(.*?)endbfrange", s, re.S):
        for lo, hi, dst in re.findall(
                r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            base = int(dst, 16)
            for k, _ in enumerate(range(int(lo, 16), int(hi, 16) + 1)):
                m[int(lo, 16) + k] = chr(base + k) if base + k <= 0x10FFFF else ""
        for lo, hi, arr in re.findall(
                r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", blk, re.S):
            for k, dst in enumerate(re.findall(r"<([0-9A-Fa-f]+)>", arr)):
                m[int(lo, 16) + k] = hexstr_to_unicode(dst)
    return m

cmaps = {}
for num, body in objects.items():
    st = get_stream(body)
    if st and (b"beginbfchar" in st or b"beginbfrange" in st):
        cmaps[num] = parse_cmap(st)

# --- CIDFont widths (/W, /DW) ---------------------------------------------
def parse_widths(cidfont_body):
    d = dict_part(cidfont_body).decode("latin-1", "replace")
    dw_m = re.search(r"/DW\s+(\d+)", d)
    dw = int(dw_m.group(1)) if dw_m else 1000
    widths = {}
    wm = re.search(r"/W\s*\[(.*?)\]\s*(?:/|>>)", d, re.S)
    if not wm:
        wm = re.search(r"/W\s*\[(.*)\]", d, re.S)
    if wm:
        body = wm.group(1)
        # tokens: ints and bracket groups
        i = 0
        toks = re.findall(r"\[|\]|-?\d+\.?\d*", body)
        k = 0
        while k < len(toks):
            t = toks[k]
            if t == "[":
                k += 1; continue
            # pattern: c [ w... ]  OR  cfirst clast w
            if k + 1 < len(toks) and toks[k+1] == "[":
                c = int(float(t)); k += 2
                idx = 0
                while k < len(toks) and toks[k] != "]":
                    widths[c + idx] = float(toks[k]); idx += 1; k += 1
                k += 1  # skip ]
            elif k + 2 < len(toks):
                a = int(float(toks[k])); b = int(float(toks[k+1])); w = float(toks[k+2])
                for cc in range(a, b + 1):
                    widths[cc] = w
                k += 3
            else:
                k += 1
    return dw, widths

# Type0 font -> (cmap, dw, widths)
ref_re = re.compile(rb"/ToUnicode\s+(\d+)\s+\d+\s+R")
desc_re = re.compile(rb"/DescendantFonts\s*\[?\s*(\d+)\s+\d+\s+R")
font_info = {}
for num, body in objects.items():
    d = dict_part(body)
    if b"/Type0" in d:
        cm = None
        r = ref_re.search(d)
        if r and int(r.group(1)) in cmaps:
            cm = cmaps[int(r.group(1))]
        dw, widths = 1000, {}
        dm = desc_re.search(d)
        if dm:
            dw, widths = parse_widths(objects.get(int(dm.group(1)), b""))
        if cm is not None:
            font_info[num] = (cm, dw, widths)

# --- resources: font name -> Type0 obj num --------------------------------
fontdict_re = re.compile(rb"/Font\s*<<(.*?)>>", re.S)
name_ref_re = re.compile(rb"/([A-Za-z0-9_.\-]+)\s+(\d+)\s+\d+\s+R")
res_ref_re = re.compile(rb"/Resources\s+(\d+)\s+\d+\s+R")

def page_fontmap(body):
    d = dict_part(body)
    fd = fontdict_re.search(d)
    block = fd.group(1) if fd else None
    if block is None:
        rr = res_ref_re.search(d)
        if rr:
            fd2 = fontdict_re.search(objects.get(int(rr.group(1)), b""))
            block = fd2.group(1) if fd2 else None
    fmap = {}
    if block:
        for name, onum in name_ref_re.findall(block):
            onum = int(onum)
            if onum in font_info:
                fmap[name.decode("latin-1")] = font_info[onum]
    return fmap

def get_page_contents(body):
    d = dict_part(body)
    m = re.search(rb"/Contents\s+(\d+)\s+\d+\s+R", d)
    if m:
        return get_stream(objects.get(int(m.group(1)), b"")) or b""
    m = re.search(rb"/Contents\s*\[(.*?)\]", d, re.S)
    if m:
        parts = re.findall(rb"(\d+)\s+\d+\s+R", m.group(1))
        return b"\n".join(get_stream(objects.get(int(p), b"")) or b"" for p in parts)
    return b""

# --- tokenizer -------------------------------------------------------------
def tokenize(content):
    i, n = 0, len(content)
    toks = []
    while i < n:
        c = content[i:i+1]
        if c == b"(":
            j = i + 1; depth = 1; buf = bytearray()
            while j < n and depth > 0:
                ch = content[j]
                if ch == 0x5C:
                    nxt = content[j+1:j+2]
                    esc = {b"n":10,b"r":13,b"t":9,b"b":8,b"f":12,b"(":40,b")":41,b"\\":92}
                    if nxt in esc:
                        buf.append(esc[nxt]); j += 2; continue
                    mo = re.match(rb"[0-7]{1,3}", content[j+1:j+4])
                    if mo:
                        buf.append(int(mo.group(0), 8) & 0xFF); j += 1 + len(mo.group(0)); continue
                    j += 1; continue
                if ch == 0x28: depth += 1; buf.append(ch); j += 1
                elif ch == 0x29:
                    depth -= 1
                    if depth > 0: buf.append(ch)
                    j += 1
                else: buf.append(ch); j += 1
            toks.append(("str", bytes(buf))); i = j
        elif c == b"<" and content[i+1:i+2] != b"<":
            j = content.find(b">", i)
            hexs = re.sub(rb"\s", b"", content[i+1:j])
            if len(hexs) % 2: hexs += b"0"
            toks.append(("str", bytes.fromhex(hexs.decode("latin-1")))); i = j + 1
        elif c == b"[":
            toks.append(("[", None)); i += 1
        elif c == b"]":
            toks.append(("]", None)); i += 1
        elif c in b" \t\r\n":
            i += 1
        else:
            j = i
            while j < n and content[j:j+1] not in b" \t\r\n()<>[]":
                j += 1
            toks.append(("op", content[i:j])); i = j
    return toks

SPACE_CHARS = set(" \u00a0")

def render_page(body):
    fmap = page_fontmap(body)
    toks = tokenize(get_page_contents(body))
    out = []
    # text state
    Tm = [1,0,0,1,0,0]; Tlm = [1,0,0,1,0,0]
    size = 10.0; Tc = 0.0; Tw = 0.0; TL = 0.0
    font = None
    prev_x = prev_y = None
    stack = []

    def mul(m, t):  # m * translate? we use simple compose: new = a(matrix) where t applied
        return t

    def translate(tx, ty):
        nonlocal Tlm, Tm
        Tlm = [Tlm[0], Tlm[1], Tlm[2], Tlm[3],
               Tlm[0]*tx + Tlm[2]*ty + Tlm[4],
               Tlm[1]*tx + Tlm[3]*ty + Tlm[5]]
        Tm = Tlm[:]

    def num(tok):
        try: return float(tok)
        except: return 0.0

    i = 0
    operands = []
    while i < len(toks):
        typ, val = toks[i]
        if typ == "str":
            operands.append(("str", val)); i += 1; continue
        if typ == "[":
            # gather array until ]
            arr = []
            i += 1
            while i < len(toks) and toks[i][0] != "]":
                arr.append(toks[i]); i += 1
            i += 1
            operands.append(("arr", arr)); continue
        if typ == "op":
            # Distinguish PostScript operands (numbers, /names, bool/null) from
            # real operators. Operands accumulate; operators execute.
            if (val.startswith(b"/") or val in (b"true", b"false", b"null")
                    or re.match(rb"^[+-]?\d*\.?\d+$", val)):
                operands.append(("op", val)); i += 1; continue
            op = val
            o = operands
            if op == b"BT":
                Tm = [1,0,0,1,0,0]; Tlm = [1,0,0,1,0,0]; prev_x = prev_y = None
                if out and not out[-1].endswith("\n"):
                    out.append("\n")
            elif op == b"Tf":
                if len(o) >= 2 and o[-2][0] == "op":
                    name = o[-2][1][1:].decode("latin-1")
                    font = fmap.get(name)
                if o and o[-1][0] == "op":
                    pass
                # size is last numeric operand
                if len(o) >= 1:
                    try: size = float(o[-1][1]) if o[-1][0]=="op" else size
                    except: pass
            elif op == b"Tc":
                Tc = num(o[-1][1]) if o and o[-1][0]=="op" else Tc
            elif op == b"Tw":
                Tw = num(o[-1][1]) if o and o[-1][0]=="op" else Tw
            elif op == b"TL":
                TL = num(o[-1][1]) if o and o[-1][0]=="op" else TL
            elif op == b"Tm":
                if len(o) >= 6:
                    vals = [num(o[k][1]) for k in range(-6,0)]
                    Tm = vals[:]; Tlm = vals[:]; prev_x=prev_y=None
            elif op == b"Td":
                if len(o) >= 2:
                    translate(num(o[-2][1]), num(o[-1][1]))
            elif op == b"TD":
                if len(o) >= 2:
                    TL = -num(o[-1][1]); translate(num(o[-2][1]), num(o[-1][1]))
            elif op == b"T*":
                translate(0, -TL)
            elif op in (b"Tj", b"'", b'"', b"TJ"):
                if op in (b"'", b'"'):
                    translate(0, -TL)
                # current position
                cx, cy = Tm[4], Tm[5]
                if prev_y is not None and abs(cy - prev_y) > size*0.5:
                    out.append("\n")
                elif prev_x is not None and (cx - prev_x) > size*0.22:
                    out.append(" ")
                # render operand(s)
                segs = []
                if op == b"TJ":
                    arr = o[-1][1] if o and o[-1][0]=="arr" else []
                    for t,v in arr:
                        if t == "str": segs.append(("s", v))
                        elif t == "op": segs.append(("n", num(v)))
                else:
                    sv = None
                    for t,v in reversed(o):
                        if t == "str": sv = v; break
                    if sv is not None: segs.append(("s", sv))
                advance = 0.0
                for kind, v in segs:
                    if kind == "n":
                        adj = -v/1000.0*size
                        advance += adj
                        if adj > size*0.18:
                            out.append(" ")
                    else:
                        if font:
                            cm, dw, widths = font
                            for k in range(0, len(v)-1, 2):
                                cid = (v[k]<<8)|v[k+1]
                                ch = cm.get(cid, "")
                                out.append(ch)
                                w = widths.get(cid, dw)/1000.0*size + Tc
                                if ch in SPACE_CHARS: w += Tw
                                advance += w
                        else:
                            s = v.decode("latin-1","replace"); out.append(s)
                            advance += len(s)*size*0.5
                Tm[4] += advance
                prev_x = Tm[4]; prev_y = cy
            operands = []
            i += 1
            continue
        i += 1
    return "".join(out)

# page order
page_nums = [n for n in sorted(objects)
             if re.search(rb"/Type\s*/Page\b", dict_part(objects[n]))
             and not re.search(rb"/Type\s*/Pages\b", dict_part(objects[n]))]

parts = []
for pn in page_nums:
    try:
        parts.append(render_page(objects[pn]))
    except Exception as e:
        parts.append("")
text = "\n".join(parts)
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r" *\n *", "\n", text)
text = re.sub(r"\n{3,}", "\n\n", text)

open(OUT, "w", encoding="utf-8").write(text)
print("Yozildi:", OUT, "| belgilar:", len(text), "| sahifa:", len(page_nums),
      "| fontlar:", len(font_info))
print("\n=== boshi (420 belgi) ===\n" + text[:420])
