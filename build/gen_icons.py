#!/usr/bin/env python3
"""Generate brand PNG icons with a pure-Python PNG writer (no deps)."""
import zlib, struct, os, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(ROOT, "icons")
os.makedirs(ICONS, exist_ok=True)

MAROON = (123, 17, 19)
DARK   = (74, 8, 9)
GOLD   = (240, 201, 90)

def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside

def make_png(size, path, maskable=False):
    bolt = [(0.56,0.10),(0.30,0.56),(0.46,0.56),(0.40,0.90),(0.70,0.40),(0.53,0.40)]
    bolt = [(px*size, py*size) for px, py in bolt]
    radius = size * (0.0 if maskable else 0.20)
    cx, cy = size/2, size/2
    rows = bytearray()
    for y in range(size):
        rows.append(0)  # filter type 0
        for x in range(size):
            # rounded-corner alpha (only when not maskable)
            a = 255
            if not maskable:
                dx = max(radius - x, x - (size - radius), 0)
                dy = max(radius - y, y - (size - radius), 0)
                if dx > 0 and dy > 0 and (dx*dx + dy*dy) > radius*radius:
                    a = 0
            # radial gradient background
            d = math.hypot(x - cx, y - cy) / (size * 0.72)
            d = min(d, 1.0)
            r = int(MAROON[0]*(1-d) + DARK[0]*d)
            g = int(MAROON[1]*(1-d) + DARK[1]*d)
            b = int(MAROON[2]*(1-d) + DARK[2]*d)
            if point_in_poly(x + 0.5, y + 0.5, bolt):
                r, g, b = GOLD
            rows += bytes((r, g, b, a))
    raw = zlib.compress(bytes(rows), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", raw)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote", path, "(%d bytes)" % len(png))

make_png(192, os.path.join(ICONS, "icon-192.png"))
make_png(512, os.path.join(ICONS, "icon-512.png"))
make_png(512, os.path.join(ICONS, "icon-maskable-512.png"), maskable=True)

# SVG crest icon
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs><radialGradient id="g" cx="50%" cy="42%" r="70%">
<stop offset="0%" stop-color="#7b1113"/><stop offset="100%" stop-color="#4a0809"/></radialGradient></defs>
<rect width="512" height="512" rx="104" fill="url(#g)"/>
<path d="M287 51 L154 287 H236 L205 461 L358 205 H271 Z" fill="#f0c95a"/>
</svg>'''
with open(os.path.join(ICONS, "icon.svg"), "w", encoding="utf-8") as f:
    f.write(svg)
print("wrote icon.svg")
