#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
index.html'ga BIR MARTALIK struktura tuzatishi:
Reader (srcdoc iframe) localStorage'i mobil brauzerlarda (Safari srcdoc null-origin)
ishlamaydi. Shuning uchun butun saqlashni TOP sahifa (kutubxona) zimmasiga o'tkazamiz:
 - kutubxona kitob ochganda saqlangan holatni readerga inject qiladi (@@SAVED@@),
 - reader progressni postMessage bilan kutubxonaga yuboradi,
 - kutubxona uni O'Z localStorage'iga yozadi (top-origin — hamma joyda ishlaydi).
Idempotent: agar allaqachon patch qilingan bo'lsa, hech narsa qilmaydi.
Har bir anchor aniq 1 marta topilishi tekshiriladi; aks holda ABORT (yozilmaydi).
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")

html = open(INDEX, encoding="utf-8", errors="replace").read()

if "__GP_SAVED__" in html:
    print("Allaqachon patch qilingan — hech narsa qilinmadi.")
    sys.exit(0)

edits = []  # (nom, old, new)

# 1) Reader Store: load -> avval inject qilingan holatni ol; saveRaw -> parentga ham yubor
edits.append(("Store", """  var Store = {
    load: function () {
      try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
      catch (e) { return {}; }
    },
    saveRaw: function (obj) {
      try { localStorage.setItem(KEY, JSON.stringify(obj)); return true; }
      catch (e) { return false; }
    }
  };""", """  var Store = {
    load: function () {
      try { if (window.__GP_SAVED__) return window.__GP_SAVED__; } catch (e) {}
      try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
      catch (e) { return {}; }
    },
    saveRaw: function (obj) {
      try { localStorage.setItem(KEY, JSON.stringify(obj)); } catch (e) {}
      try { if (window.parent && window.parent !== window) window.parent.postMessage({ __gp: "save", key: KEY, data: obj }, "*"); } catch (e) {}
      return true;
    }
  };"""))

# 2) window.BOOK qatoriga saqlangan holat injeksiyasini qo'shish
edits.append(("BOOKCFG-line",
    "window.BOOK=@@BOOKCFG@@;",
    "window.BOOK=@@BOOKCFG@@;window.__GP_SAVED__=@@SAVED@@;"))

# 3) openBook: saqlangan holatni o'qib, srcdoc'ga inject qilish
edits.append(("openBook-saved-read",
    "  if(b.gloss){cfg.glossary=GLOSSARY_SHARED;}\n  v.srcdoc=shell.split('@@TITLE@@').join(b.title)",
    "  if(b.gloss){cfg.glossary=GLOSSARY_SHARED;}\n  var __saved='null';try{var __sv=localStorage.getItem(b.key);if(__sv)__saved=__sv;}catch(e){}\n  v.srcdoc=shell.split('@@TITLE@@').join(b.title)"))

edits.append(("openBook-saved-inject",
    ".split('@@BOOKCFG@@').join(JSON.stringify(cfg))\n    .split('@@CHAPTERS@@').join(chapters);",
    ".split('@@BOOKCFG@@').join(JSON.stringify(cfg))\n    .split('@@SAVED@@').join(__saved)\n    .split('@@CHAPTERS@@').join(chapters);"))

# 4) Kutubxona xabar tinglovchisi: reader yuborgan 'save'ni localStorage'ga yozish
edits.append(("msg-listener",
    "window.addEventListener('message',function(e){if(e&&e.data==='gp-back'){showLibrary();}});",
    "window.addEventListener('message',function(e){var d=e&&e.data;if(d&&d.__gp==='save'&&d.key){try{localStorage.setItem(d.key,JSON.stringify(d.data));}catch(err){}try{render();}catch(err){}return;}if(d==='gp-back'){showLibrary();}});"))

# --- Har bir anchor aniq 1 marta ekanini tekshir ---
for name, old, new in edits:
    c = html.count(old)
    if c != 1:
        print("ABORT: '%s' anchor %d marta topildi (1 kutilgan). Fayl o'zgartirilmadi." % (name, c))
        sys.exit(1)

for name, old, new in edits:
    html = html.replace(old, new, 1)

open(INDEX, "w", encoding="utf-8").write(html)
print("Struktura patch qo'llandi:", ", ".join(n for n, _, _ in edits))
