#!/usr/bin/env python3
"""Sof Python PDF matn ekstraktori (v2).
Matn sahifa /Contents oqimida, har bir glyf alohida BT/ET bloki sifatida,
cm/Tm matritsalari orqali joylashtirilgan. SamsungSans Identity-H + ToUnicode.
"""
import re, zlib, sys

def load(path):
    with open(path, 'rb') as f:
        return f.read()

def get_objects(data):
    objs = {}
    for m in re.finditer(rb'(\d+)\s+(\d+)\s+obj', data):
        num = int(m.group(1))
        start = m.end()
        end = data.find(b'endobj', start)
        if end == -1:
            continue
        objs[num] = data[start:end]
    return objs

def get_stream(obj):
    m = re.search(rb'stream\r?\n', obj)
    if not m:
        return None
    start = m.end()
    end = obj.find(b'endstream', start)
    raw = obj[start:end]
    if raw.endswith(b'\n'): raw = raw[:-1]
    if raw.endswith(b'\r'): raw = raw[:-1]
    if b'FlateDecode' in obj[:m.start()]:
        for cut in (raw, raw[:-1], raw[:-2], raw[1:]):
            try:
                return zlib.decompress(cut)
            except Exception:
                continue
        return raw
    return raw

# ---------- Sahifa tartibi ----------
def find_root_pages(objs):
    for num, obj in objs.items():
        if b'/Catalog' in obj[:200]:
            m = re.search(rb'/Pages\s+(\d+)\s+\d+\s+R', obj)
            if m:
                return int(m.group(1))
    return None

def get_page_order(objs):
    root = find_root_pages(objs)
    order = []
    def walk(num, seen):
        if num in seen: return
        seen.add(num)
        obj = objs.get(num, b'')
        head = obj[:300]
        if b'/Type' in head and b'/Pages' in head:
            m = re.search(rb'/Kids\s*\[([^\]]*)\]', obj, re.S)
            if m:
                for km in re.finditer(rb'(\d+)\s+\d+\s+R', m.group(1)):
                    walk(int(km.group(1)), seen)
        elif b'/Type' in head and b'/Page' in head:
            order.append(num)
    if root is not None:
        walk(root, set())
    if not order:
        for num in sorted(objs):
            head = objs[num][:300]
            if b'/Type' in head and b'/Page' in head and b'/Pages' not in head:
                order.append(num)
    return order

# ---------- CMap ----------
def hexstr_to_unicode(h):
    out = []
    for i in range(0, len(h), 4):
        seg = h[i:i+4]
        if len(seg) == 4:
            out.append(chr(int(seg, 16)))
    return ''.join(out)

def parse_cmap(stream):
    mapping = {}
    if not stream:
        return mapping
    txt = stream.decode('latin1')
    for block in re.findall(r'beginbfchar(.*?)endbfchar', txt, re.S):
        for m in re.finditer(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', block):
            mapping[int(m.group(1), 16)] = hexstr_to_unicode(m.group(2))
    for block in re.findall(r'beginbfrange(.*?)endbfrange', txt, re.S):
        for m in re.finditer(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', block):
            lo = int(m.group(1), 16); hi = int(m.group(2), 16); base = int(m.group(3), 16)
            for i in range(hi - lo + 1):
                mapping[lo + i] = chr(base + i)
    return mapping

def parse_widths(objs, descobj):
    """DescendantFont /W massivdan {cid: width} (1/1000 em).
    Format: 'c [w1 w2 ...]' yoki 'c1 c2 w' aralash."""
    widths = {}
    body = objs.get(descobj, b'')
    dwm = re.search(rb'/DW\s+([\d.]+)', body)
    dw = float(dwm.group(1)) if dwm else 1000.0
    # /W dan keyingi balansli [ ... ] ni topish
    wi = body.find(b'/W')
    if wi == -1:
        return widths, dw
    lb = body.find(b'[', wi)
    if lb == -1:
        return widths, dw
    depth = 0; end = lb
    for k in range(lb, len(body)):
        ch = body[k:k+1]
        if ch == b'[': depth += 1
        elif ch == b']':
            depth -= 1
            if depth == 0:
                end = k; break
    arr = body[lb+1:end].decode('latin1')
    tokens = re.findall(r'\[|\]|[-+]?\d*\.?\d+', arr)
    j = 0
    while j < len(tokens):
        if tokens[j] in ('[', ']'):
            j += 1; continue
        c = int(float(tokens[j])); j += 1
        if j < len(tokens) and tokens[j] == '[':
            j += 1; k = 0
            while j < len(tokens) and tokens[j] != ']':
                widths[c + k] = float(tokens[j]); k += 1; j += 1
            if j < len(tokens) and tokens[j] == ']': j += 1
        elif j + 1 < len(tokens):
            c2 = int(float(tokens[j])); w = float(tokens[j+1]); j += 2
            for cid in range(c, c2 + 1):
                widths[cid] = w
    return widths, dw

def font_to_data(fontobj, objs, cache):
    if fontobj in cache:
        return cache[fontobj]
    body = objs.get(fontobj, b'')
    m = re.search(rb'/ToUnicode\s+(\d+)\s+\d+\s+R', body)
    cm = parse_cmap(get_stream(objs[int(m.group(1))])) if m else {}
    dm = re.search(rb'/DescendantFonts\s*\[\s*(\d+)', body)
    widths, dw = parse_widths(objs, int(dm.group(1))) if dm else ({}, 1000.0)
    cache[fontobj] = (cm, widths, dw)
    return cache[fontobj]

def page_fonts(page_body, objs, cache):
    """Sahifa /Resources /Font dict -> {fontname: (cmap, widths, dw)}"""
    fonts = {}
    fm = re.search(rb'/Font\s*<<(.*?)>>', page_body, re.S)
    if not fm:
        return fonts
    for m in re.finditer(rb'/(\w+)\s+(\d+)\s+\d+\s+R', fm.group(1)):
        fonts[m.group(1).decode('latin1')] = font_to_data(int(m.group(2)), objs, cache)
    return fonts

# ---------- Matritsa ----------
def mul(m1, m2):
    """m1 ni avval, keyin m2 ni qo'llaydigan kompozit matritsa."""
    a1,b1,c1,d1,e1,f1 = m1
    a2,b2,c2,d2,e2,f2 = m2
    return (
        a1*a2 + b1*c2,
        a1*b2 + b1*d2,
        c1*a2 + d1*c2,
        c1*b2 + d1*d2,
        e1*a2 + f1*c2 + e2,
        e1*b2 + f1*d2 + f2,
    )

def apply_pt(m, x, y):
    a,b,c,d,e,f = m
    return (a*x + c*y + e, b*x + d*y + f)

# ---------- Content stream tokenizer ----------
tok_re = re.compile(rb"""
      (?P<num>[-+]?\d*\.?\d+)
    | /(?P<name>[^\s/\[\]<>(){}]+)
    | <(?P<hex>[0-9A-Fa-f\s]*)>
    | \[(?P<arr>[^\]]*)\]
    | (?P<op>[A-Za-z'"*]+)
""", re.X | re.S)

def decode_hex_codes(h):
    h = re.sub(r'\s+', '', h)
    codes = []
    for i in range(0, len(h) - 3, 4):
        codes.append(int(h[i:i+4], 16))
    return codes

def interpret(stream, fonts):
    """(x, y, text, adv_dev) ro'yxatini qaytaradi (qurilma koordinatalarida).
    adv_dev = glyfning qurilma fazosidagi gorizontal advance kengligi."""
    items = []
    if not stream:
        return items
    ctm = (1,0,0,1,0,0)
    stack = []
    tm = (1,0,0,1,0,0)
    tlm = (1,0,0,1,0,0)
    cur = (({}, {}, 1000.0))  # (cmap, widths, dw)
    fontsize = 1.0
    operands = []

    def emit(codes):
        cmap, widths, dw = cur
        if not codes:
            return
        s = ''.join(cmap.get(c, '') for c in codes)
        # advance: barcha kodlar kengligi yig'indisi (text fazosida)
        wsum = sum(widths.get(c, dw) for c in codes) / 1000.0 * fontsize
        comb = mul(tm, ctm)
        ux, uy = apply_pt(tm, 0, 0)
        dx, dy = apply_pt(ctm, ux, uy)
        # advance vektori (wsum, 0) ni comb ning chiziqli qismi orqali
        adv_dx = wsum * comb[0]
        adv_dy = wsum * comb[1]
        adv_dev = (adv_dx**2 + adv_dy**2) ** 0.5
        items.append((dx, dy, s, adv_dev))

    for m in tok_re.finditer(stream):
        if m.group('num') is not None:
            operands.append(float(m.group('num')))
        elif m.group('name') is not None:
            operands.append('/' + m.group('name').decode('latin1'))
        elif m.group('hex') is not None:
            operands.append(('hex', m.group('hex').decode('latin1')))
        elif m.group('arr') is not None:
            operands.append(('arr', m.group('arr').decode('latin1')))
        elif m.group('op') is not None:
            op = m.group('op').decode('latin1')
            if op == 'q':
                stack.append(ctm)
            elif op == 'Q':
                if stack: ctm = stack.pop()
            elif op == 'cm' and len(operands) >= 6:
                ctm = mul(tuple(operands[-6:]), ctm)
            elif op == 'BT':
                tm = (1,0,0,1,0,0); tlm = (1,0,0,1,0,0)
            elif op == 'Tm' and len(operands) >= 6:
                tm = tuple(operands[-6:]); tlm = tm
            elif op in ('Td','TD') and len(operands) >= 2:
                tx, ty = operands[-2], operands[-1]
                tlm = mul((1,0,0,1,tx,ty), tlm); tm = tlm
            elif op == 'T*':
                tm = tlm
            elif op == 'Tf' and len(operands) >= 2:
                fname = operands[-2]
                if isinstance(fname, str) and fname.startswith('/'):
                    cur = fonts.get(fname[1:], ({}, {}, 1000.0))
                if isinstance(operands[-1], float):
                    fontsize = operands[-1]
            elif op in ('Tj', "'", '"'):
                for o in reversed(operands):
                    if isinstance(o, tuple) and o[0] == 'hex':
                        emit(decode_hex_codes(o[1])); break
            elif op == 'TJ':
                for o in reversed(operands):
                    if isinstance(o, tuple) and o[0] == 'arr':
                        for p in re.findall(r'<([0-9A-Fa-f\s]*)>', o[1]):
                            emit(decode_hex_codes(p))
                        break
            operands = []
    return items

# ---------- Sahifa matnini yig'ish ----------
def assemble(items):
    if not items:
        return ''
    items = [it for it in items if it[2] != '']
    if not items:
        return ''
    YTOL = 4.0
    rows = []  # (y, [(x, text, adv)])
    for x, y, t, adv in sorted(items, key=lambda it: -it[1]):
        placed = False
        for row in rows:
            if abs(row[0] - y) <= YTOL:
                row[1].append((x, t, adv)); placed = True; break
        if not placed:
            rows.append((y, [(x, t, adv)]))
    rows.sort(key=lambda r: -r[0])
    out = []
    for y, chars in rows:
        chars.sort(key=lambda p: p[0])
        line = ''; prev = None
        for x, t, adv in chars:
            if prev is not None:
                px, pt, padv = prev
                gap = x - px
                extra = gap - padv
                thr = max(padv * 0.30, 1.3)
                if extra > thr and not line.endswith(' ') and t not in (' ', ',', '.', '!', '?', ';', ':'):
                    line += ' '
            line += t
            prev = (x, t, adv)
        out.append(line.rstrip())
    return '\n'.join(out)

def extract(path):
    data = load(path)
    objs = get_objects(data)
    pages = get_page_order(objs)
    sys.stderr.write(f"Sahifalar: {len(pages)}\n")
    cache = {}
    out_pages = []
    for pnum in pages:
        page = objs.get(pnum, b'')
        fonts = page_fonts(page, objs, cache)
        # Contents (bitta yoki massiv)
        cstreams = b''
        cm = re.search(rb'/Contents\s+(\d+)\s+\d+\s+R', page)
        if cm:
            st = get_stream(objs.get(int(cm.group(1)), b''))
            if st: cstreams += st + b'\n'
        else:
            am = re.search(rb'/Contents\s*\[([^\]]*)\]', page)
            if am:
                for r in re.finditer(rb'(\d+)\s+\d+\s+R', am.group(1)):
                    st = get_stream(objs.get(int(r.group(1)), b''))
                    if st: cstreams += st + b'\n'
        items = interpret(cstreams, fonts)
        out_pages.append(assemble(items))
    return '\n'.join(out_pages)

if __name__ == '__main__':
    inp, outp = sys.argv[1], sys.argv[2]
    text = extract(inp)
    with open(outp, 'w', encoding='utf-8') as f:
        f.write(text)
    sys.stderr.write(f"Yozildi: {outp} ({len(text)} belgi)\n")
