#!/usr/bin/env python3
"""Assemble the premium reader: new chrome + preserved book chapters + new engine."""
import re, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ORIG = os.path.join(ROOT, "Garri_Potter_va_Lanatlangan_Bola.html")
OUT  = os.path.join(ROOT, "Garri_Potter_va_Lanatlangan_Bola.html")

def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

orig = read(ORIG)

# --- extract the chapter sections (preserve book content verbatim) ---
start = orig.find('<section class="chapter"')
end_marker = orig.find('<div class="chapter-nav" id="end-nav"')
if start == -1 or end_marker == -1:
    print("ERROR: could not locate chapter boundaries", file=sys.stderr)
    sys.exit(1)
# back up to the line start of the end marker
end = orig.rfind("\n", start, end_marker)
chapters = orig[start:end].rstrip() + "\n"

# sanity: count chapters
n = chapters.count('<section class="chapter"')
print("Chapters preserved:", n)
if n < 29:
    print("ERROR: expected >=29 chapters, got", n, file=sys.stderr)
    sys.exit(1)

head        = read(os.path.join(BASE, "head.html")).rstrip() + "\n"
chrome_top  = read(os.path.join(BASE, "chrome_top.html")).rstrip() + "\n"
chrome_bot  = read(os.path.join(BASE, "chrome_bottom.html")).rstrip() + "\n"
app_js      = read(os.path.join(BASE, "app.js")).rstrip() + "\n"
part2_js    = read(os.path.join(BASE, "part2.js")).rstrip() + "\n"

final = (
    head
    + chrome_top
    + chapters
    + chrome_bot
    + "\n<script>\n"
    + app_js
    + "\n"
    + part2_js
    + "</script>\n</body>\n</html>\n"
)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(final)

print("Wrote", OUT, "(%d bytes)" % len(final))
print("Total lines:", final.count("\n") + 1)
