#!/usr/bin/env python3
"""PDF matn ekstraktori v2 — 1-bayt (TrueType/Type1) VA 2-bayt (Type0/CID, Identity-H)
fontlarni qo'llab-quvvatlaydi. Sof Python (re + zlib), tashqi kutubxonasiz.

v1 (extract_pdf_simple.py) faqat 1-baytli fontlarni o'qiy olardi; Type0 (CIDFontType2)
fontli kitoblar (5, 6) har bir belgini ikkiga bo'lib, aralashtirib yuborardi.
Bu versiya font /Subtype ni aniqlab, mos baytlilikda dekodlaydi.
"""
import re, zlib, sys

def load(path):
    with open(path, 'rb') as f:
        return f.read()

def get_objects(data):
    objs = {}
    for m in re.finditer(rb'(\d+)\s+(\d+)\s+obj', data):
        num = int(m.group(1)); start = m.end()
        end = data.find(b'endobj', start)
        if end == -1: continue
        objs[num] = data[start:end]
    return objs

def get_stream(obj):
    m = re.search(rb'stream\r?\n', obj)
    if not m: return None
    start = m.end(); end = obj.find(b'endstream', start)
    raw = obj[start:end]
    if raw.endswith(b'\n'): raw = raw[:-1]
    if raw.endswith(b'\r'): raw = raw[:-1]
    if b'FlateDecode' in obj[:m.start()]:
        for cut in (raw, raw[:-1], raw[:-2], raw[1:]):
            try: return zlib.decompress(cut)
            except Exception: continue
        return raw
    return raw

def find_root_pages(objs):
    for num, obj in objs.items():
        if b'/Catalog' in obj[:300]:
            m = re.search(rb'/Pages\s+(\d+)\s+\d+\s+R', obj)
            if m: return int(m.group(1))
    return None

def get_page_order(objs):
    root = find_root_pages(objs); order = []
    def walk(num, seen):
        if num in seen: return
        seen.add(num); obj = objs.get(num, b''); head = obj[:400]
        if b'/Type' in head and b'/Pages' in head:
            m = re.search(rb'/Kids\s*\[([^\]]*)\]', obj, re.S)
            if m:
                for km in re.finditer(rb'(\d+)\s+\d+\s+R', m.group(1)):
                    walk(int(km.group(1)), seen)
        elif b'/Type' in head and b'/Page' in head:
            order.append(num)
    if root is not None: walk(root, set())
    if not order:
        for num in sorted(objs):
            head = objs[num][:400]
            if b'/Type/Page' in head and b'/Pages' not in head:
                order.append(num)
    return order

def hexstr_to_unicode(h):
    out = []
    for i in range(0, len(h), 4):
        seg = h[i:i+4]
        if len(seg) == 4: out.append(chr(int(seg, 16)))
    return ''.join(out)

def parse_cmap(stream):
    mapping = {}
    if not stream: return mapping
    txt = stream.decode('latin1')
    for block in re.findall(r'beginbfchar(.*?)endbfchar', txt, re.S):
        for m in re.finditer(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', block):
            mapping[int(m.group(1), 16)] = hexstr_to_unicode(m.group(2))
    for block in re.findall(r'beginbfrange(.*?)endbfrange', txt, re.S):
        for m in re.finditer(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', block):
            lo = int(m.group(1),16); hi = int(m.group(2),16); base = int(m.group(3),16)
            for i in range(hi - lo + 1):
                mapping[lo + i] = chr(base + i)
    return mapping

def parse_simple_widths(fontbody):
    widths = {}
    fcm = re.search(rb'/FirstChar\s+(\d+)', fontbody)
    if not fcm: return widths
    first = int(fcm.group(1))
    wm = re.search(rb'/Widths\s*\[([^\]]*)\]', fontbody, re.S)
    if not wm: return widths
    nums = re.findall(rb'[-+]?\d*\.?\d+', wm.group(1))
    for i, n in enumerate(nums):
        try: widths[first + i] = float(n)
        except ValueError: pass
    return widths

def resolve_ref(objs, body, key):
    m = re.search(key + rb'\s+(\d+)\s+\d+\s+R', body)
    return int(m.group(1)) if m else None

def parse_cid_widths(objs, descbody):
    """Type0 descendant /W [ c [w...] c1 c2 w ... ] -> {cid: width}."""
    widths = {}
    wm = re.search(rb'/W\s*\[', descbody)
    if not wm: return widths
    # capture balanced-ish W array text
    start = wm.end(); depth = 1; i = start
    while i < len(descbody) and depth:
        if descbody[i:i+1] == b'[': depth += 1
        elif descbody[i:i+1] == b']': depth -= 1
        i += 1
    body = descbody[start:i-1]
    toks = re.findall(rb'\[([^\]]*)\]|([-+]?\d*\.?\d+)', body)
    pending = []
    flat = []
    for arr, num in toks:
        if arr: flat.append(('arr', arr))
        else: flat.append(('num', float(num)))
    j = 0
    while j < len(flat):
        if j+1 < len(flat) and flat[j][0]=='num' and flat[j+1][0]=='arr':
            c = int(flat[j][1]); nums = re.findall(rb'[-+]?\d*\.?\d+', flat[j+1][1])
            for k,n in enumerate(nums): widths[c+k] = float(n)
            j += 2
        elif j+2 < len(flat) and flat[j][0]=='num' and flat[j+1][0]=='num' and flat[j+2][0]=='num':
            c1=int(flat[j][1]); c2=int(flat[j+1][1]); w=flat[j+2][1]
            for c in range(c1, c2+1): widths[c]=w
            j += 3
        else:
            j += 1
    return widths

def font_to_data(fontnum, objs, cache):
    if fontnum in cache: return cache[fontnum]
    body = objs.get(fontnum, b'')
    tnum = resolve_ref(objs, body, rb'/ToUnicode')
    cm = parse_cmap(get_stream(objs[tnum])) if tnum is not None else {}
    is_type0 = b'/Type0' in body or b'/Identity-H' in body
    if is_type0:
        nbytes = 2; dw = 1000.0; widths = {}
        # descendant font for /W and /DW
        dnum = resolve_ref(objs, body, rb'/DescendantFonts')
        descbody = b''
        if dnum is not None:
            descbody = objs.get(dnum, b'')
        else:
            dm = re.search(rb'/DescendantFonts\s*\[\s*(\d+)\s+\d+\s+R', body)
            if dm: descbody = objs.get(int(dm.group(1)), b'')
        dwm = re.search(rb'/DW\s+([-+]?\d*\.?\d+)', descbody)
        if dwm: dw = float(dwm.group(1))
        widths = parse_cid_widths(objs, descbody)
    else:
        nbytes = 1; dw = 500.0
        widths = parse_simple_widths(body)
    cache[fontnum] = (cm, widths, dw, nbytes)
    return cache[fontnum]

def page_fonts(page_body, objs, cache):
    fonts = {}
    res = None
    rnum = resolve_ref(objs, page_body, rb'/Resources')
    if rnum is not None: res = objs.get(rnum, b'')
    else:
        rm = re.search(rb'/Resources\s*<<(.*?)>>', page_body, re.S)
        if rm: res = rm.group(0)
    if res is None: return fonts
    fontdict = None
    fnum = resolve_ref(objs, res, rb'/Font')
    if fnum is not None: fontdict = objs.get(fnum, b'')
    else:
        fm = re.search(rb'/Font\s*<<(.*?)>>', res, re.S)
        if fm: fontdict = fm.group(1)
    if fontdict is None: return fonts
    for m in re.finditer(rb'/([A-Za-z0-9]+)\s+(\d+)\s+\d+\s+R', fontdict):
        fonts[m.group(1).decode('latin1')] = font_to_data(int(m.group(2)), objs, cache)
    return fonts

def mul(m1, m2):
    a1,b1,c1,d1,e1,f1 = m1; a2,b2,c2,d2,e2,f2 = m2
    return (a1*a2+b1*c2, a1*b2+b1*d2, c1*a2+d1*c2, c1*b2+d1*d2,
            e1*a2+f1*c2+e2, e1*b2+f1*d2+f2)

def apply_pt(m, x, y):
    a,b,c,d,e,f = m
    return (a*x + c*y + e, b*x + d*y + f)

tok_re = re.compile(rb"""
      (?P<num>[-+]?\d*\.?\d+)
    | /(?P<name>[^\s/\[\]<>(){}]+)
    | <(?P<hex>[0-9A-Fa-f\s]*)>
    | \[(?P<arr>(?:[^\[\]\\]|\\.)*)\]
    | \((?P<lit>(?:[^()\\]|\\.)*)\)
    | (?P<op>[A-Za-z'"*]+)
""", re.X | re.S)

def decode_hex_codes(h, nbytes=1):
    h = re.sub(r'\s+', '', h)
    step = nbytes * 2
    if len(h) % step: h = h + '0' * (step - len(h) % step)
    codes = []
    for i in range(0, len(h) - step + 1, step):
        codes.append(int(h[i:i+step], 16))
    return codes

def decode_lit(s, nbytes=1):
    out = []; i = 0
    esc = {'n':10,'r':13,'t':9,'b':8,'f':12,'(':40,')':41,'\\':92}
    while i < len(s):
        c = s[i]
        if c == '\\' and i+1 < len(s):
            nx = s[i+1]
            if nx in esc: out.append(esc[nx]); i += 2; continue
            if nx.isdigit():
                j = i+1; oct_ = ''
                while j < len(s) and len(oct_) < 3 and s[j].isdigit(): oct_ += s[j]; j += 1
                out.append(int(oct_, 8) & 0xFF); i = j; continue
            out.append(ord(nx) & 0xFF); i += 2; continue
        out.append(ord(c) & 0xFF); i += 1
    if nbytes == 1: return out
    codes = []
    for k in range(0, len(out) - 1, 2):
        codes.append((out[k] << 8) | out[k+1])
    return codes

def interpret(stream, fonts):
    items = []
    if not stream: return items
    ctm = (1,0,0,1,0,0); stack = []
    tm = (1,0,0,1,0,0); tlm = (1,0,0,1,0,0)
    cur = ({}, {}, 500.0, 1)
    fontsize = 1.0; tc = 0.0; tw = 0.0; operands = []

    def emit(codes):
        nonlocal tm
        cmap, widths, dw, nb = cur
        if not codes: return
        for code in codes:
            ch = cmap.get(code, '')
            comb = mul(tm, ctm)
            dx, dy = apply_pt(comb, 0, 0)
            w0 = widths.get(code, dw) / 1000.0
            adv = (w0 * fontsize + tc + (tw if code == 32 else 0.0))
            adv_dx = adv * comb[0]; adv_dy = adv * comb[1]
            adv_dev = (adv_dx**2 + adv_dy**2) ** 0.5
            if ch != '' and ch != '\uffff':
                items.append((dx, dy, ch, adv_dev))
            tm = mul((1,0,0,1,adv,0), tm)

    for m in tok_re.finditer(stream):
        if m.group('num') is not None: operands.append(float(m.group('num')))
        elif m.group('name') is not None: operands.append('/' + m.group('name').decode('latin1'))
        elif m.group('hex') is not None: operands.append(('hex', m.group('hex').decode('latin1')))
        elif m.group('arr') is not None: operands.append(('arr', m.group('arr').decode('latin1')))
        elif m.group('lit') is not None: operands.append(('lit', m.group('lit').decode('latin1')))
        elif m.group('op') is not None:
            op = m.group('op').decode('latin1')
            nb = cur[3]
            if op == 'q': stack.append(ctm)
            elif op == 'Q':
                if stack: ctm = stack.pop()
            elif op == 'cm' and len(operands) >= 6: ctm = mul(tuple(operands[-6:]), ctm)
            elif op == 'BT': tm = (1,0,0,1,0,0); tlm = (1,0,0,1,0,0)
            elif op == 'Tm' and len(operands) >= 6: tm = tuple(operands[-6:]); tlm = tm
            elif op in ('Td','TD') and len(operands) >= 2:
                tx, ty = operands[-2], operands[-1]
                tlm = mul((1,0,0,1,tx,ty), tlm); tm = tlm
            elif op == 'T*': tm = tlm
            elif op == 'Tc' and operands: tc = operands[-1]
            elif op == 'Tw' and operands: tw = operands[-1]
            elif op == 'Tf' and len(operands) >= 2:
                fname = operands[-2]
                if isinstance(fname, str) and fname.startswith('/'):
                    cur = fonts.get(fname[1:], ({}, {}, 500.0, 1))
                if isinstance(operands[-1], (int, float)): fontsize = operands[-1]
            elif op in ('Tj', "'", '"'):
                for o in reversed(operands):
                    if isinstance(o, tuple) and o[0] == 'hex': emit(decode_hex_codes(o[1], nb)); break
                    if isinstance(o, tuple) and o[0] == 'lit': emit(decode_lit(o[1], nb)); break
            elif op == 'TJ':
                for o in reversed(operands):
                    if isinstance(o, tuple) and o[0] == 'arr':
                        for tm2 in re.finditer(r'<([0-9A-Fa-f\s]*)>|\(((?:[^()\\]|\\.)*)\)|([-+]?\d*\.?\d+)', o[1]):
                            if tm2.group(1) is not None: emit(decode_hex_codes(tm2.group(1), nb))
                            elif tm2.group(2) is not None: emit(decode_lit(tm2.group(2), nb))
                            elif tm2.group(3) is not None:
                                kern = float(tm2.group(3)); shift = -kern / 1000.0 * fontsize
                                tm = mul((1,0,0,1,shift,0), tm)
                        break
            operands = []
    return items

def assemble(items):
    if not items: return ''
    items = [it for it in items if it[2] != '']
    if not items: return ''
    YTOL = 3.0
    rows = []
    for x, y, t, adv in sorted(items, key=lambda it: -it[1]):
        placed = False
        for row in rows:
            if abs(row[0] - y) <= YTOL:
                row[1].append((x, t, adv)); placed = True; break
        if not placed: rows.append((y, [(x, t, adv)]))
    rows.sort(key=lambda r: -r[0])
    out = []
    for y, chars in rows:
        chars.sort(key=lambda p: p[0])
        line = ''; prev = None
        for x, t, adv in chars:
            if prev is not None:
                px, pt, padv = prev
                gap = x - px; extra = gap - padv
                thr = max(padv * 0.30, 1.2)
                if extra > thr and not line.endswith(' ') and t not in (' ', ',', '.', '!', '?', ';', ':'):
                    line += ' '
            line += t; prev = (x, t, adv)
        out.append(line.rstrip())
    return '\n'.join(out)

def extract(path):
    data = load(path); objs = get_objects(data); pages = get_page_order(objs)
    sys.stderr.write("Sahifalar: %d\n" % len(pages))
    cache = {}; out_pages = []
    for pnum in pages:
        page = objs.get(pnum, b''); fonts = page_fonts(page, objs, cache)
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
    sys.stderr.write("Yozildi: %s (%d belgi)\n" % (outp, len(text)))
