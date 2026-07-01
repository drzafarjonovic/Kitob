#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
index.html reader-shell'iga IndexedDB ZAXIRA qatlamini qo'shadi.
Maqsad: file:// (Chrome) yoki localStorage bloklangan holatlarda ham progress saqlansin.
- saveRaw: localStorage + parent postMessage + IndexedDB (uchchala joyga).
- init oxirida: agar localStorage bo'sh bo'lsa, IndexedDB'dan holatni tiklaydi.
Qat'iy ADDITIV va himoyalangan: faqat localStorage bo'sh bo'lganda IDBdan tiklaydi,
shuning uchun mavjud xatti-harakatni buzmaydi. Idempotent.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
html = open(INDEX, encoding="utf-8", errors="replace").read()

if "idbInitAndRestore" in html:
    print("IDB fallback allaqachon mavjud — hech narsa qilinmadi.")
    sys.exit(0)

edits = []

# 1) IDB yordamchilarini KEY dan keyin, Store dan oldin qo'shish
IDB_HELPERS = '''  /* ---------- IndexedDB zaxira (file:// va localStorage bloklangan holatlar) ---------- */
  var _idb = null;
  function idbOpen(cb) {
    try {
      if (!window.indexedDB) { cb && cb(); return; }
      var r = indexedDB.open("gp_reader_db", 1);
      r.onupgradeneeded = function () { try { r.result.createObjectStore("kv"); } catch (e) {} };
      r.onsuccess = function () { _idb = r.result; cb && cb(); };
      r.onerror = function () { cb && cb(); };
    } catch (e) { cb && cb(); }
  }
  function idbSet(obj) {
    try { if (_idb) _idb.transaction("kv", "readwrite").objectStore("kv").put(obj, KEY); } catch (e) {}
  }
  function idbGet(cb) {
    try {
      if (!_idb) { cb(null); return; }
      var rq = _idb.transaction("kv", "readonly").objectStore("kv").get(KEY);
      rq.onsuccess = function () { cb(rq.result || null); };
      rq.onerror = function () { cb(null); };
    } catch (e) { cb(null); }
  }
'''
edits.append(('idb-helpers',
    '  var KEY = (window.BOOK && window.BOOK.key) || "gp_reader_v2";\n  var Store = {',
    '  var KEY = (window.BOOK && window.BOOK.key) || "gp_reader_v2";\n' + IDB_HELPERS + '  var Store = {'))

# 2) saveRaw ichida IDBga ham yozish
edits.append(('idb-save',
    '      try { localStorage.setItem(KEY, JSON.stringify(obj)); } catch (e) {}\n      try { if (window.parent && window.parent !== window)',
    '      try { localStorage.setItem(KEY, JSON.stringify(obj)); } catch (e) {}\n      idbSet(obj);\n      try { if (window.parent && window.parent !== window)'))

# 3) init oxirida IDBdan tiklash funksiyasini chaqirish + ta'rifi
IDB_RESTORE = '''    idbInitAndRestore();
    function idbInitAndRestore() {
      idbOpen(function () {
        var haveLS = false; try { haveLS = !!localStorage.getItem(KEY); } catch (e) {}
        if (haveLS || window.__GP_SAVED__) return;
        idbGet(function (saved) {
          if (!saved || (S.progress && S.progress.scroll > 0)) return;
          try {
            S.settings = Object.assign({}, DEFAULTS, saved.settings || {});
            S.bookmarks = saved.bookmarks || []; S.highlights = saved.highlights || [];
            S.notes = saved.notes || []; S.searchHistory = saved.searchHistory || [];
            S.progress = saved.progress || { scroll: 0, pct: 0 }; S.stats = saved.stats || S.stats;
            SettingsUI.apply(); renderAllHighlights(); updateProgress(); updateLibBadge();
            if (S.progress.scroll > 0) { window.scrollTo(0, S.progress.scroll); setTimeout(function () { window.scrollTo(0, S.progress.scroll); }, 120); }
          } catch (e) {}
        });
      });
    }
'''
edits.append(('idb-restore',
    '    updateProgress();\n    Library.render();\n',
    '    updateProgress();\n    Library.render();\n' + IDB_RESTORE))

for name, old, new in edits:
    c = html.count(old)
    if c != 1:
        print("ABORT: '%s' anchor %d marta (1 kutilgan). Fayl o'zgartirilmadi." % (name, c))
        sys.exit(1)

for name, old, new in edits:
    html = html.replace(old, new, 1)

open(INDEX, "w", encoding="utf-8").write(html)
print("IDB fallback qo'shildi:", ", ".join(n for n, _, _ in edits))
