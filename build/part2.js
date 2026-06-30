  /* ============================================================
     COMBINED PAINTER (highlights + search hits)
     ============================================================ */
  var FIND_HITS = [];
  var currentFindId = null;
  function paintPara(idx) {
    var p = paras[idx]; if (!p) return;
    var text = PARA_TEXT[idx];
    var hs = S.highlights.filter(function (h) { return h.p === idx; });
    var fs = FIND_HITS.filter(function (f) { return f.p === idx; });
    if (!hs.length && !fs.length) { p.textContent = text; return; }
    var pts = {}; pts[0] = 1; pts[text.length] = 1;
    hs.forEach(function (h) { pts[clamp(h.start,0,text.length)] = 1; pts[clamp(h.end,0,text.length)] = 1; });
    fs.forEach(function (f) { pts[clamp(f.start,0,text.length)] = 1; pts[clamp(f.start + f.len,0,text.length)] = 1; });
    var arr = Object.keys(pts).map(Number).sort(function (a, b) { return a - b; });
    var html = "";
    for (var i = 0; i < arr.length - 1; i++) {
      var a = arr[i], b = arr[i + 1]; if (b <= a) continue;
      var seg = esc(text.slice(a, b));
      var h = null, f = null, j;
      for (j = 0; j < hs.length; j++) { if (hs[j].start <= a && hs[j].end >= b) { h = hs[j]; break; } }
      for (j = 0; j < fs.length; j++) { if (fs[j].start <= a && fs[j].start + fs[j].len >= b) { f = fs[j]; break; } }
      var open = "", close = "";
      if (h) { open += '<span class="hl' + (h.note ? " has-note" : "") + '" data-hl="' + h.id + '" data-color="' + h.color + '"' + (h.note ? ' title="' + esc(h.note) + '"' : "") + ">"; close = "</span>" + close; }
      if (f) { open += '<mark class="find-hit' + (f.id === currentFindId ? " current" : "") + '" data-find="' + f.id + '">'; close = "</mark>" + close; }
      html += open + seg + close;
    }
    p.innerHTML = html;
  }

  /* ============================================================
     SEARCH
     ============================================================ */
  var searchBox = $("#searchbox"), searchInput = $("#search-input"), searchCount = $("#search-count"), searchResults = $("#search-results");
  var searchOpts = { case: false, word: false, regex: false, hilite: true };
  var searchMatches = [], searchPos = -1, searchDebounce;

  function openSearch() {
    closePanels();
    searchBox.classList.add("open");
    setTimeout(function () { searchInput.focus(); searchInput.select(); }, 60);
    if (!searchInput.value) renderSearchIdle();
  }
  function closeSearch() {
    searchBox.classList.remove("open");
    clearFinds();
  }
  function clearFinds() {
    var affected = {};
    FIND_HITS.forEach(function (f) { affected[f.p] = true; });
    FIND_HITS = []; currentFindId = null;
    Object.keys(affected).forEach(function (k) { paintPara(+k); });
  }
  function buildRegex(q) {
    var flags = "g" + (searchOpts.case ? "" : "i");
    var pat = q;
    if (!searchOpts.regex) pat = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (searchOpts.word) pat = "\\b" + pat + "\\b";
    try { return new RegExp(pat, flags); } catch (e) { return null; }
  }
  function doSearch() {
    var q = searchInput.value.trim();
    clearFinds();
    searchMatches = []; searchPos = -1;
    if (q.length < 2) { renderSearchIdle(); searchCount.textContent = ""; return; }
    var re = buildRegex(q);
    if (!re) { searchCount.textContent = "xato regex"; searchResults.innerHTML = '<div class="search-hint">Regulyar ifoda noto\'g\'ri</div>'; return; }
    var total = 0, cap = 800;
    for (var pi = 0; pi < PARA_TEXT.length; pi++) {
      var text = PARA_TEXT[pi], m; re.lastIndex = 0;
      while ((m = re.exec(text)) !== null) {
        if (m[0].length === 0) { re.lastIndex++; continue; }
        total++;
        if (searchMatches.length < cap) {
          searchMatches.push({ id: "f" + searchMatches.length, p: pi, start: m.index, len: m[0].length });
        }
        if (total > 5000) break;
      }
      if (total > 5000) break;
    }
    searchCount.textContent = total ? (total + " ta natija") : "topilmadi";
    if (searchOpts.hilite) applyFinds();
    renderSearchResults(q);
    if (searchMatches.length) { searchPos = 0; gotoMatch(0, false); }
  }
  function applyFinds() {
    FIND_HITS = searchMatches.slice();
    var byP = {}; FIND_HITS.forEach(function (f) { byP[f.p] = true; });
    Object.keys(byP).forEach(function (k) { paintPara(+k); });
  }
  function renderSearchResults(q) {
    if (!searchMatches.length) { searchResults.innerHTML = '<div class="search-hint">Hech narsa topilmadi.</div>'; return; }
    searchResults.innerHTML = searchMatches.slice(0, 120).map(function (m, i) {
      var text = PARA_TEXT[m.p];
      var from = Math.max(0, m.start - 40), to = Math.min(text.length, m.start + m.len + 50);
      var pre = (from > 0 ? "…" : "") + esc(text.slice(from, m.start));
      var hit = "<mark>" + esc(text.slice(m.start, m.start + m.len)) + "</mark>";
      var post = esc(text.slice(m.start + m.len, to)) + (to < text.length ? "…" : "");
      var ci = chapterOfPara(m.p);
      return '<div class="res" data-i="' + i + '"><span class="loc">' + esc(chapterMeta[ci] ? chapterMeta[ci].title : "") + '</span>' + pre + hit + post + '</div>';
    }).join("");
    $$("#search-results .res").forEach(function (r) {
      on(r, "click", function () { searchPos = +r.dataset.i; gotoMatch(searchPos, true); });
    });
  }
  function renderSearchIdle() {
    var h = S.searchHistory;
    if (!h.length) { searchResults.innerHTML = '<div class="search-hint">Kamida 2 ta harf kiriting.</div>'; return; }
    searchResults.innerHTML = '<div class="search-hint">So\'nggi qidiruvlar</div><div class="search-hist">' +
      h.map(function (q) { return '<span class="h">' + esc(q) + '</span>'; }).join("") + '</div>';
    $$("#search-results .search-hist .h").forEach(function (el) {
      on(el, "click", function () { searchInput.value = el.textContent; doSearch(); });
    });
  }
  function gotoMatch(i, fromList) {
    if (!searchMatches.length) return;
    searchPos = (i + searchMatches.length) % searchMatches.length;
    var m = searchMatches[searchPos];
    currentFindId = m.id;
    if (searchOpts.hilite) { paintPara(m.p); }
    else { FIND_HITS = [m]; paintPara(m.p); }
    var p = paras[m.p];
    smoothScrollTo(p.getBoundingClientRect().top + window.scrollY - topbarOffset() - 60);
    searchCount.textContent = (searchPos + 1) + " / " + searchMatches.length + (searchMatches.length >= 800 ? "+" : "");
    if (searchOpts.hilite) { var prev = $(".find-hit.current:not([data-find='" + m.id + "'])"); }
  }
  function commitHistory() {
    var q = searchInput.value.trim();
    if (q.length >= 2) {
      S.searchHistory = [q].concat(S.searchHistory.filter(function (x) { return x !== q; })).slice(0, 12);
      save();
    }
  }
  function bindSearch() {
    on($("#btn-search"), "click", function () { searchBox.classList.contains("open") ? closeSearch() : openSearch(); });
    on(searchInput, "input", function () { clearTimeout(searchDebounce); searchDebounce = setTimeout(doSearch, 180); });
    on(searchInput, "keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); commitHistory(); if (e.shiftKey) gotoMatch(searchPos - 1); else gotoMatch(searchPos + 1); }
      if (e.key === "Escape") { closeSearch(); }
    });
    on($("#search-next"), "click", function () { gotoMatch(searchPos + 1); commitHistory(); });
    on($("#search-prev"), "click", function () { gotoMatch(searchPos - 1); commitHistory(); });
    $$("#searchbox .opt").forEach(function (o) {
      on(o, "click", function () {
        var k = o.dataset.opt; searchOpts[k] = !searchOpts[k];
        o.classList.toggle("on", searchOpts[k]);
        doSearch();
      });
    });
  }

  /* ============================================================
     STATISTICS
     ============================================================ */
  function todayKey() { var d = new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
  function fmtDur(sec) {
    sec = Math.round(sec);
    if (sec < 60) return sec + " son";
    if (sec < 3600) return Math.floor(sec / 60) + " daq";
    var h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60);
    return h + " s " + (m ? m + " d" : "");
  }
  Stats = {
    lastActivity: Date.now(),
    maxPct: (S.stats.maxPct || 0),
    bump: function () { this.lastActivity = Date.now(); },
    onProgress: function (p) {
      if (p > this.maxPct) { this.maxPct = p; S.stats.maxPct = p; }
      this.bump();
    },
    tick: function () {
      if (document.hidden) return;
      if (Date.now() - this.lastActivity > 90000) return; // idle
      var k = todayKey();
      S.stats.days[k] = (S.stats.days[k] || 0) + 1;
      S.stats.totalSeconds = (S.stats.totalSeconds || 0) + 1;
      S.stats.activeSeconds = (S.stats.activeSeconds || 0) + 1;
      if (S.stats.totalSeconds % 10 === 0) save();
    },
    sumDays: function (n) {
      var total = 0, now = new Date();
      for (var i = 0; i < n; i++) {
        var d = new Date(now); d.setDate(now.getDate() - i);
        var k = d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
        total += S.stats.days[k] || 0;
      }
      return total;
    },
    wpm: function () {
      var mins = (S.stats.activeSeconds || 0) / 60;
      var wordsRead = (this.maxPct) * totalWords;
      if (mins < 1 || wordsRead < 50) return 0;
      return Math.round(wordsRead / mins);
    },
    render: function () {
      $("#st-today").textContent = fmtDur(this.sumDays(1));
      $("#st-week").textContent = fmtDur(this.sumDays(7));
      $("#st-month").textContent = fmtDur(this.sumDays(30));
      $("#st-total").textContent = fmtDur(S.stats.totalSeconds || 0);
      var wpm = this.wpm();
      $("#st-wpm").textContent = wpm ? wpm : "—";
      var remaining = Math.max(0, (1 - this.maxPct) * totalWords);
      var eta = wpm ? remaining / wpm : 0;
      $("#st-eta").textContent = (wpm && eta > 0.5) ? fmtDur(eta * 60) : (this.maxPct >= 0.999 ? "tugadi" : "—");
      var bestCh = "—";
      $("#st-details").innerHTML =
        "Jami so'zlar: <b>" + totalWords.toLocaleString() + "</b><br>" +
        "O'qilgan (taxminiy): <b>" + Math.round(this.maxPct * 100) + "%</b><br>" +
        "Qolgan so'zlar: <b>" + Math.round(remaining).toLocaleString() + "</b><br>" +
        "Belgilashlar: <b>" + S.highlights.length + "</b> · Xatcho'plar: <b>" + S.bookmarks.length + "</b>";
      this.drawChart();
    },
    drawChart: function () {
      var cv = $("#weekChart"); if (!cv || !cv.getContext) return;
      var ctx = cv.getContext("2d");
      var W = cv.width = cv.clientWidth * 2, H = cv.height = 240;
      ctx.clearRect(0, 0, W, H);
      var days = [], labels = [], now = new Date(), max = 1;
      var names = ["Yak", "Dush", "Sesh", "Chor", "Pay", "Jum", "Shan"];
      for (var i = 6; i >= 0; i--) {
        var d = new Date(now); d.setDate(now.getDate() - i);
        var k = d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
        var v = (S.stats.days[k] || 0) / 60;
        days.push(v); labels.push(names[d.getDay()]); if (v > max) max = v;
      }
      var pad = 30, bw = (W - pad * 2) / 7 * 0.6, gap = (W - pad * 2) / 7;
      var accent = getComputedStyle(root).getPropertyValue("--accent").trim() || "#7b1113";
      var muted = getComputedStyle(root).getPropertyValue("--muted").trim() || "#888";
      ctx.font = "20px sans-serif"; ctx.textAlign = "center";
      days.forEach(function (v, i) {
        var x = pad + gap * i + (gap - bw) / 2;
        var bh = (H - 60) * (v / max);
        var y = H - 40 - bh;
        ctx.fillStyle = accent; ctx.globalAlpha = .85;
        roundRect(ctx, x, y, bw, bh, 6); ctx.fill();
        ctx.globalAlpha = 1; ctx.fillStyle = muted;
        ctx.fillText(labels[i], x + bw / 2, H - 14);
        if (v >= 1) { ctx.fillStyle = accent; ctx.fillText(Math.round(v) + "d", x + bw / 2, y - 6); }
      });
    }
  };
  function roundRect(ctx, x, y, w, h, r) {
    if (h < 1) h = 1; r = Math.min(r, h / 2, w / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  /* ============================================================
     GLOSSARY (Harry Potter premium)
     ============================================================ */
  var GLOSSARY = {
    "Qahramonlar": [
      ["Garri Potter", "Tirik qolgan bola; endi Sehrgarlik vazirligida ishlovchi ota. Hikoyada uchinchi farzandi Albus bilan munosabati markazda turadi."],
      ["Albus Severus Potter", "Garri va Jinnining o'rtancha o'g'li. Slizerin fakultetiga tushadi va Skorpius bilan do'stlashadi."],
      ["Skorpius Malfoy", "Drako Malfoyning o'g'li; aqlli, mehribon va sodiq do'st. Albusning eng yaqin sherigi."],
      ["Jinni Potter", "Garrining rafiqasi, jurnalist va g'amxo'r ona."],
      ["Ron Uizli", "Garrining eng yaqin do'sti; Hazil do'koni egasi."],
      ["Germiona Greynjer", "Sehrgarlik vaziri; kuchli va tamoyilli rahbar."],
      ["Drako Malfoy", "Skorpiusning otasi; o'tmishdagi raqib, endi o'g'li uchun tashvishlanuvchi ota."],
      ["Delfi", "Sirli yosh ayol; voqealarning asosiy antagonisti."]
    ],
    "Joylar": [
      ["Xogvarts", "Sehrgarlik va jodugarlik maktabi."],
      ["To'qqis-uchdan-bir platforma", "Xogvarts ekspressiga chiqiladigan sirli platforma."],
      ["Sehrgarlik vazirligi", "Sehrli dunyo hukumati joylashgan idora."],
      ["Godrik cho'qqisi", "Potterlar oilasiga bog'liq tarixiy maskan."]
    ],
    "Sehrlar": [
      ["Expelliarmus", "Qurolsizlantirish sehri — Garrining mashhur tutumi."],
      ["Lumos", "Hassa uchini yorituvchi sehr."],
      ["Expecto Patronum", "Dementorlardan himoya qiluvchi homiy sehri."],
      ["Crucio", "Taqiqlangan azoblovchi sehr."]
    ],
    "Atamalar": [
      ["Vaqt aylantirgich (Time-Turner)", "Vaqt orqaga qaytaruvchi qurilma; hikoyaning markaziy mavzusi."],
      ["Dementor", "Baxtni so'ruvchi qorong'i maxluq."],
      ["Polyjus iksiri", "Boshqa odam qiyofasiga kirish imkonini beruvchi iksir."]
    ]
  };
  Glossary = {
    rendered: false,
    render: function () {
      if (this.rendered) return;
      var box = $("#glossary-list");
      box.innerHTML = Object.keys(GLOSSARY).map(function (cat) {
        return '<div class="gloss-cat"><h4>' + esc(cat) + '</h4>' +
          GLOSSARY[cat].map(function (it) {
            return '<div class="gloss-item"><div class="term">' + esc(it[0]) + '</div><div class="desc">' + esc(it[1]) + '</div></div>';
          }).join("") + '</div>';
      }).join("");
      this.rendered = true;
    }
  };

  /* ============================================================
     EXPORT / IMPORT
     ============================================================ */
  function download(name, content, type) {
    var blob = new Blob([content], { type: type || "text/plain;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
  }
  function exportData(fmt) {
    var payload = { app: "GarriPotterReader", version: 2, exported: new Date().toISOString(),
      bookmarks: S.bookmarks, highlights: S.highlights, settings: S.settings };
    if (fmt === "json") { download("garri-potter-reader.json", JSON.stringify(payload, null, 2), "application/json"); }
    else if (fmt === "csv") {
      var rows = [["tur", "bob", "matn", "rang/izoh", "foiz", "sana"]];
      S.bookmarks.forEach(function (b) { rows.push(["xatchop", b.chapter, b.name, "", b.pct + "%", fmtDate(b.ts)]); });
      S.highlights.forEach(function (h) { rows.push(["belgilash", chapterMeta[h.ci] ? chapterMeta[h.ci].title : "", h.text, h.note || h.color, "", fmtDate(h.ts)]); });
      var csv = rows.map(function (r) { return r.map(function (c) { return '"' + String(c).replace(/"/g, '""') + '"'; }).join(","); }).join("\n");
      download("garri-potter-reader.csv", "\ufeff" + csv, "text/csv;charset=utf-8");
    } else {
      var txt = "GARRI POTTER VA LA'NATLANGAN BOLA — Eksport\n\n=== XATCHO'PLAR ===\n";
      S.bookmarks.forEach(function (b) { txt += "• [" + b.chapter + " " + b.pct + "%] " + b.name + "\n"; });
      txt += "\n=== BELGILASHLAR & IZOHLAR ===\n";
      S.highlights.forEach(function (h) { txt += "• (" + (chapterMeta[h.ci] ? chapterMeta[h.ci].title : "") + ") \"" + h.text + "\"" + (h.note ? "\n   Izoh: " + h.note : "") + "\n"; });
      download("garri-potter-reader.txt", txt);
    }
    toast("Eksport qilindi: " + fmt.toUpperCase());
  }
  function importData(file) {
    var r = new FileReader();
    r.onload = function () {
      try {
        var d = JSON.parse(r.result);
        if (d.bookmarks) S.bookmarks = mergeById(S.bookmarks, d.bookmarks);
        if (d.highlights) S.highlights = mergeById(S.highlights, d.highlights);
        if (d.settings) S.settings = Object.assign({}, DEFAULTS, S.settings, d.settings);
        SettingsUI.apply(); renderAllHighlights(); Library.render(); updateLibBadge(); saveNow();
        toast("Import muvaffaqiyatli");
      } catch (e) { toast("Import xato: noto'g'ri fayl"); }
    };
    r.readAsText(file);
  }
  function mergeById(a, b) {
    var seen = {}; a.forEach(function (x) { seen[x.id] = true; });
    b.forEach(function (x) { if (!seen[x.id]) { a.push(x); seen[x.id] = true; } });
    return a;
  }
  function bindData() {
    $$("[data-export]").forEach(function (b) { on(b, "click", function () { exportData(b.dataset.export); }); });
    on($("#import-btn"), "click", function () { $("#import-file").click(); });
    on($("#import-file"), "change", function (e) { if (e.target.files[0]) importData(e.target.files[0]); e.target.value = ""; });
    on($("#print-btn"), "click", function () { closePanels(); setTimeout(function () { window.print(); }, 300); });
    on($("#reset-btn"), "click", function () {
      openDialog('<h3>Hammasini tozalash</h3><p style="color:var(--fg-soft);font-size:.9rem;line-height:1.6">Barcha xatcho\'p, belgilash, izoh va statistika o\'chiriladi. Bu amalni ortga qaytarib bo\'lmaydi.</p>' +
        '<div class="dialog-actions"><button class="btn" id="rs-cancel">Bekor</button><button class="btn primary" id="rs-ok" style="background:#c0392b;border-color:#c0392b">O\'chirish</button></div>');
      on($("#rs-cancel"), "click", closeDialog);
      on($("#rs-ok"), "click", function () {
        S.bookmarks = []; S.highlights = []; S.notes = []; S.searchHistory = [];
        S.stats = { days: {}, totalSeconds: 0, wordsRead: 0, activeSeconds: 0, maxPct: 0 };
        Stats.maxPct = 0;
        renderAllHighlights(); Library.render(); updateLibBadge(); saveNow();
        closeDialog(); toast("Hammasi tozalandi");
      });
    });
  }

  /* ============================================================
     TOPBAR AUTO-HIDE
     ============================================================ */
  var topbar = $("#topbar"), fabStack = $("#fab-stack");
  var lastY = 0;
  function onScrollUI(y) {
    if (!S.settings.autohide) { topbar.classList.remove("hidden"); return; }
    if (y > lastY && y > 160) { topbar.classList.add("hidden"); }
    else { topbar.classList.remove("hidden"); }
    fabStack.classList.toggle("hidden", y < 400);
    lastY = y;
  }

  /* ============================================================
     RIPPLE EFFECT
     ============================================================ */
  function bindRipples() {
    $$(".iconbtn, .fab").forEach(function (btn) {
      on(btn, "pointerdown", function (e) {
        if (S.settings.anim <= 0 || S.settings.reduceMotion) return;
        var r = document.createElement("span"); r.className = "ripple";
        var rect = btn.getBoundingClientRect();
        var size = Math.max(rect.width, rect.height);
        r.style.width = r.style.height = size + "px";
        r.style.left = (e.clientX - rect.left - size / 2) + "px";
        r.style.top = (e.clientY - rect.top - size / 2) + "px";
        btn.appendChild(r);
        setTimeout(function () { if (r.parentNode) r.parentNode.removeChild(r); }, 600);
      });
    });
  }

  /* ============================================================
     GESTURES
     ============================================================ */
  function bindGestures() {
    var sx = 0, sy = 0, st = 0, moved = false, lastTap = 0;
    var pinchStart = 0, pinching = false, baseScale = 1;
    on(book, "touchstart", function (e) {
      if (e.touches.length === 2) {
        pinching = true;
        pinchStart = dist(e.touches[0], e.touches[1]);
        baseScale = S.settings.fontScale;
        return;
      }
      var t = e.touches[0]; sx = t.clientX; sy = t.clientY; st = Date.now(); moved = false;
    }, { passive: true });
    on(book, "touchmove", function (e) {
      if (pinching && e.touches.length === 2) {
        var d = dist(e.touches[0], e.touches[1]);
        var ratio = d / pinchStart;
        S.settings.fontScale = clamp(+(baseScale * ratio).toFixed(2), 0.8, 2.2);
        SettingsUI.apply();
        return;
      }
      moved = true;
    }, { passive: true });
    on(book, "touchend", function (e) {
      if (pinching) { pinching = false; toast("Shrift: " + Math.round(S.settings.fontScale * 100) + "%"); return; }
      var t = e.changedTouches[0];
      var dx = t.clientX - sx, dy = t.clientY - sy, dt = Date.now() - st;
      // swipe
      if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.8 && dt < 600) {
        if (dx < 0) gotoChapter(curChapter + 1); else gotoChapter(curChapter - 1);
        return;
      }
      // double tap to toggle UI
      if (!moved && Math.abs(dx) < 12 && Math.abs(dy) < 12) {
        var now = Date.now();
        if (now - lastTap < 320) {
          toggleUI();
          lastTap = 0;
        } else lastTap = now;
      }
    }, { passive: true });
  }
  function dist(a, b) { var dx = a.clientX - b.clientX, dy = a.clientY - b.clientY; return Math.sqrt(dx * dx + dy * dy); }
  function toggleUI() {
    var hidden = topbar.classList.toggle("hidden");
    fabStack.classList.toggle("hidden", hidden);
  }

  /* ============================================================
     KEYBOARD SHORTCUTS
     ============================================================ */
  function bindKeys() {
    on(document, "keydown", function (e) {
      var tag = (e.target.tagName || "").toLowerCase();
      var typing = tag === "input" || tag === "textarea" || e.target.isContentEditable;
      if ((e.ctrlKey || e.metaKey) && (e.key === "f" || e.key === "F")) { e.preventDefault(); openSearch(); return; }
      if (typing) return;
      switch (e.key) {
        case "ArrowRight": e.preventDefault(); gotoChapter(curChapter + 1); break;
        case "ArrowLeft": e.preventDefault(); gotoChapter(curChapter - 1); break;
        case "ArrowDown": window.scrollBy({ top: 120, behavior: "auto" }); break;
        case "ArrowUp": window.scrollBy({ top: -120, behavior: "auto" }); break;
        case " ": case "PageDown": e.preventDefault(); window.scrollBy({ top: window.innerHeight * 0.88, behavior: smoothBehavior() }); break;
        case "PageUp": e.preventDefault(); window.scrollBy({ top: -window.innerHeight * 0.88, behavior: smoothBehavior() }); break;
        case "Home": e.preventDefault(); smoothScrollTo(0); break;
        case "End": e.preventDefault(); smoothScrollTo(document.body.scrollHeight); break;
        case "b": case "B": panel($("#library")); Library.render(); break;
        case "s": case "S": panel($("#settings")); break;
        case "c": case "C": panel($("#sidebar")); break;
        case "m": case "M": addBookmark(); break;
        case "F11": break; // native
        case "Escape": closePanels(); closeSearch(); closeDialog(); hideSelToolbar(); break;
        default: break;
      }
    });
  }
  function smoothBehavior() { return (S.settings.anim > 0 && !S.settings.reduceMotion) ? "smooth" : "auto"; }

  /* ============================================================
     PWA
     ============================================================ */
  function registerSW() {
    if ("serviceWorker" in navigator && location.protocol.indexOf("http") === 0) {
      navigator.serviceWorker.register("sw.js").catch(function () {});
    }
  }

  /* ============================================================
     WIRING + INIT
     ============================================================ */
  function bindChrome() {
    on($("#btn-toc"), "click", function () { panel($("#sidebar")); });
    on($("#btn-toc-close"), "click", function () { closePanels(); });
    on($("#btn-library"), "click", function () { panel($("#library")); Library.render(); });
    on($("#btn-library-close"), "click", function () { closePanels(); });
    on($("#btn-settings"), "click", function () { panel($("#settings")); });
    on($("#btn-settings-close"), "click", function () { closePanels(); });
    on($("#nav-prev"), "click", function () { gotoChapter(curChapter - 1); });
    on($("#nav-next"), "click", function () { gotoChapter(curChapter + 1); });
    on($("#fab-bookmark"), "click", function () { addBookmark(); });
    on($("#fab-up"), "click", function () { smoothScrollTo(0); });
    on($("#add-bookmark"), "click", function () { addBookmark(); });
  }

  function init() {
    try {
      if (window.BOOK && window.BOOK.id) {
        localStorage.setItem("gp_last_book", JSON.stringify({ id: window.BOOK.id, t: Date.now() }));
      }
    } catch (e) {}
    buildModel();
    buildTOC();
    buildThemeGrid();
    buildPresets();
    SettingsUI.apply();
    bindSettings();
    bindTabs();
    bindSelection();
    bindSearch();
    bindData();
    bindChrome();
    bindKeys();
    bindGestures();
    bindRipples();
    renderAllHighlights();
    updateLibBadge();

    // restore reading position
    if (S.progress.scroll > 0) {
      window.scrollTo(0, S.progress.scroll);
      setTimeout(function () { window.scrollTo(0, S.progress.scroll); }, 120);
    }

    // scroll handling (rAF, passive)
    var ticking = false;
    function onScroll() {
      Stats.bump();
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(function () {
          updateProgress();
          onScrollUI(window.scrollY);
          ticking = false;
        });
      }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", function () { updateProgress(); Stats.drawChart(); });
    ["click", "keydown", "touchstart", "mousemove"].forEach(function (ev) {
      window.addEventListener(ev, function () { Stats.bump(); }, { passive: true });
    });

    updateProgress();
    Library.render();

    // stats ticker
    setInterval(function () { Stats.tick(); }, 1000);

    // registerSW();  // PWA hozircha o'chirilgan (arxivda) — keyinroq yoqiladi
    // welcome
    setTimeout(function () { if (!S.progress.scroll) toast("Xush kelibsiz — yoqimli o'qish!"); }, 800);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();

})();
