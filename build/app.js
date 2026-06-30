/* ============================================================
   PREMIUM E-BOOK READER ENGINE
   Vanilla JS. Modular. XSS-safe. localStorage persisted.
   ============================================================ */
(function () {
  "use strict";

  /* ---------- tiny DOM helpers ---------- */
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var on = function (el, ev, fn, opt) { if (el) el.addEventListener(ev, fn, opt); };
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

  /* ============================================================
     ALIFBO: Kirill -> Lotin transliteratsiya (faqat ko'rsatish uchun)
     Kitob matni asli kirillda saqlanadi (offset/qidiruv/belgilash shu
     bo'yicha ishlaydi). Lotin rejimida matn faqat ekranda o'giriladi.
     ============================================================ */
  var CYR_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "'", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h"
  };
  function isLetter(ch) { return !!ch && ch.toLowerCase() !== ch.toUpperCase(); }
  function isUpper(ch) { return isLetter(ch) && ch === ch.toUpperCase(); }
  // Core transliterator. wantMap=true returns {t, map} where map[i] is the
  // canonical (source) index for output char i (used to map search hits back).
  function translitCore(s, wantMap) {
    if (!s) return wantMap ? { t: s || "", map: [0] } : s;
    var out = "", map = wantMap ? [] : null, prevUpper = false;
    for (var i = 0; i < s.length; i++) {
      var ch = s[i], low = ch.toLowerCase(), piece;
      if (Object.prototype.hasOwnProperty.call(CYR_MAP, low)) {
        var m = CYR_MAP[low];
        if (ch === low) { piece = m; }                 // lowercase source
        else if (m.length <= 1) { piece = m.toUpperCase(); }
        else {                                          // uppercase multigraph
          var nx = s[i + 1];
          var allcaps = (isLetter(nx) && isUpper(nx)) || (!isLetter(nx) && prevUpper);
          piece = allcaps ? m.toUpperCase() : (m.charAt(0).toUpperCase() + m.slice(1));
        }
        prevUpper = (ch !== low);
      } else {
        piece = ch;
        prevUpper = isUpper(ch);
      }
      out += piece;
      if (map) { for (var k = 0; k < piece.length; k++) map.push(i); }
    }
    if (map) map.push(s.length);
    return wantMap ? { t: out, map: map } : out;
  }
  function cyr2lat(s) { return translitCore(s, false); }

  var SCRIPT = { latin: true };
  try { SCRIPT.latin = (localStorage.getItem("gp_script") || "latin") !== "cyrillic"; } catch (e) {}
  // disp(): transform a canonical (Cyrillic) string for display
  function disp(s) { return SCRIPT.latin ? cyr2lat(s) : s; }

  /* ---------- safe storage ---------- */
  var KEY = "gp_reader_v2";
  var Store = {
    load: function () {
      try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
      catch (e) { return {}; }
    },
    saveRaw: function (obj) {
      try { localStorage.setItem(KEY, JSON.stringify(obj)); return true; }
      catch (e) { return false; }
    }
  };

  /* ---------- default settings ---------- */
  var DEFAULTS = {
    theme: "day",
    font: "Georgia, 'Times New Roman', serif",
    fontScale: 1,
    lineHeight: 1.78,
    paraSpacing: 1.15,
    wordSpacing: 0,
    letterSpacing: 0,
    width: "normal",
    pageMargin: 1.25,
    align: "justify",
    weight: 400,
    brightness: 0,
    anim: 1,
    dropcap: false,
    reduceMotion: false,
    focusRing: true,
    autohide: true
  };

  var WIDTHS = { narrow: "30rem", normal: "38rem", wide: "46rem", full: "62rem" };

  var PRESETS = {
    "Klassik":  { font: "Georgia, 'Times New Roman', serif", fontScale: 1.05, lineHeight: 1.8, paraSpacing: 1.2, align: "justify", weight: 400, dropcap: true, width: "normal" },
    "Zamonaviy":{ font: "-apple-system, 'Segoe UI', Roboto, system-ui, sans-serif", fontScale: 1.0, lineHeight: 1.7, paraSpacing: 1.0, align: "left", weight: 400, dropcap: false, width: "normal" },
    "Ixcham":   { font: "Georgia, serif", fontScale: 0.95, lineHeight: 1.55, paraSpacing: 0.6, align: "justify", weight: 400, dropcap: false, width: "wide" },
    "Bemalol":  { font: "'Iowan Old Style', Palatino, serif", fontScale: 1.2, lineHeight: 2.0, paraSpacing: 1.5, align: "left", weight: 400, dropcap: true, width: "normal" },
    "Disleksiya": { font: "'OpenDyslexic', 'Comic Sans MS', sans-serif", fontScale: 1.1, lineHeight: 2.0, paraSpacing: 1.4, align: "left", weight: 400, dropcap: false, width: "normal", letterSpacing: 0.03, wordSpacing: 0.16 }
  };

  var THEMES = [
    { id: "day",      name: "Light",    bg: "#faf8f3", fg: "#7b1113" },
    { id: "sepia",    name: "Sepia",    bg: "#f4ecd8", fg: "#8a5a1a" },
    { id: "dark",     name: "Dark",     bg: "#1a1c20", fg: "#e0934a" },
    { id: "amoled",   name: "AMOLED",   bg: "#000000", fg: "#d98a3d" },
    { id: "paper",    name: "Paper",    bg: "#ffffff", fg: "#2b2b2b" },
    { id: "night",    name: "Night",    bg: "#0f1726", fg: "#5b9bd5" },
    { id: "warm",     name: "Warm",     bg: "#fbeee0", fg: "#c2541b" },
    { id: "contrast", name: "Contrast", bg: "#000000", fg: "#ffd400" }
  ];

  var THEME_COLORS = {
    day: "#7b1113", sepia: "#8a5a1a", dark: "#1a1c20", amoled: "#000000",
    paper: "#ffffff", night: "#0f1726", warm: "#c2541b", contrast: "#000000"
  };

  /* ---------- application state ---------- */
  var data = Store.load();
  var S = {
    settings: Object.assign({}, DEFAULTS, data.settings || {}),
    bookmarks: data.bookmarks || [],
    highlights: data.highlights || [],
    notes: data.notes || [],            // standalone notes [{id,p,text,quote,ts,ci}]
    searchHistory: data.searchHistory || [],
    progress: data.progress || { scroll: 0, pct: 0 },
    stats: data.stats || { days: {}, totalSeconds: 0, wordsRead: 0, activeSeconds: 0 }
  };

  var saveTimer = null;
  function save() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      Store.saveRaw({
        settings: S.settings, bookmarks: S.bookmarks, highlights: S.highlights,
        notes: S.notes, searchHistory: S.searchHistory, progress: S.progress, stats: S.stats
      });
    }, 250);
  }
  function saveNow() { clearTimeout(saveTimer); Store.saveRaw({
    settings: S.settings, bookmarks: S.bookmarks, highlights: S.highlights,
    notes: S.notes, searchHistory: S.searchHistory, progress: S.progress, stats: S.stats }); }

  /* ---------- elements & book model ---------- */
  var root = document.documentElement;
  var book = $("#book");
  var chapters = $$(".chapter");
  var paras = [];        // all #book p elements
  var PARA_TEXT = [];    // cached plain text per paragraph
  var chapterMeta = [];  // {idx, title, num, el, words, startWord}
  var totalWords = 0;

  function wordCount(t) { var m = t.trim().match(/\S+/g); return m ? m.length : 0; }

  function buildModel() {
    paras = $$("#book p");
    paras.forEach(function (p, i) {
      p.dataset.idx = i;
      PARA_TEXT[i] = p.textContent;
    });
    var wAcc = 0;
    chapters.forEach(function (ch, i) {
      var titleEl = ch.querySelector(".chapter-title");
      var numEl = ch.querySelector(".chapter-num");
      var cps = $$("p", ch);
      var w = 0;
      cps.forEach(function (p) { w += wordCount(p.textContent); });
      chapterMeta.push({
        idx: i,
        el: ch,
        title: titleEl ? titleEl.textContent.trim() : ("Bob " + (i + 1)),
        num: numEl ? numEl.textContent.trim() : "",
        words: w,
        startWord: wAcc
      });
      wAcc += w;
    });
    totalWords = wAcc || 1;
  }

  /* ============================================================
     TOAST + DIALOG
     ============================================================ */
  var toastEl = $("#toast"), toastTimer;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
  }

  var dialogBack = $("#dialog-back"), dialogEl = $("#dialog");
  function openDialog(html) {
    dialogEl.innerHTML = html;
    dialogBack.classList.add("open");
    document.body.classList.add("modal-open");
    var f = dialogEl.querySelector("textarea,input");
    if (f) setTimeout(function () { f.focus(); }, 50);
  }
  function closeDialog() { dialogBack.classList.remove("open"); document.body.classList.remove("modal-open"); }
  on(dialogBack, "click", function (e) { if (e.target === dialogBack) closeDialog(); });

  /* ============================================================
     SETTINGS / TYPOGRAPHY / THEME
     ============================================================ */
  var SettingsUI = {
    apply: function () {
      var s = S.settings;
      root.setAttribute("data-theme", s.theme);
      root.setAttribute("data-dropcap", s.dropcap ? "on" : "off");
      var st = root.style;
      st.setProperty("--font-family", s.font);
      st.setProperty("--font-scale", s.fontScale);
      st.setProperty("--line-height", s.lineHeight);
      st.setProperty("--para-spacing", s.paraSpacing + "rem");
      st.setProperty("--word-spacing", s.wordSpacing + "em");
      st.setProperty("--letter-spacing", s.letterSpacing + "em");
      st.setProperty("--reading-width", WIDTHS[s.width] || WIDTHS.normal);
      st.setProperty("--page-margin", s.pageMargin + "rem");
      st.setProperty("--text-align", s.align);
      st.setProperty("--font-weight", s.weight);
      st.setProperty("--brightness", s.brightness);
      st.setProperty("--anim-scale", s.anim);
      var mc = $("#meta-theme-color"); if (mc) mc.setAttribute("content", THEME_COLORS[s.theme] || "#7b1113");
      root.classList.toggle("reduce-motion", !!s.reduceMotion);
      document.body.classList.toggle("no-focus-ring", !s.focusRing);
      this.sync();
      save();
    },
    sync: function () {
      var s = S.settings;
      $("#font-range").value = s.fontScale;
      $("#font-val").textContent = Math.round(s.fontScale * 100) + "%";
      $("#lh-range").value = s.lineHeight; $("#lh-val").textContent = (+s.lineHeight).toFixed(2);
      $("#ps-range").value = s.paraSpacing; $("#ps-val").textContent = (+s.paraSpacing).toFixed(2);
      $("#ws-range").value = s.wordSpacing; $("#ws-val").textContent = (+s.wordSpacing).toFixed(2);
      $("#ls-range").value = s.letterSpacing; $("#ls-val").textContent = (+s.letterSpacing).toFixed(3);
      $("#pm-range").value = s.pageMargin; $("#pm-val").textContent = (+s.pageMargin).toFixed(2);
      $("#br-range").value = s.brightness; $("#br-val").textContent = Math.round((1 - s.brightness) * 100) + "%";
      $("#font-family-sel").value = s.font;
      markSeg("#width-seg", "width", s.width);
      markSeg("#align-seg", "align", s.align);
      markSeg("#weight-seg", "weight", String(s.weight));
      markSeg("#anim-seg", "anim", String(s.anim));
      $$("#theme-grid .theme-sw").forEach(function (b) { b.classList.toggle("sel", b.dataset.theme === s.theme); });
      tg("#tg-dropcap", s.dropcap); tg("#tg-reduce", s.reduceMotion);
      tg("#tg-focus", s.focusRing); tg("#tg-autohide", s.autohide);
    }
  };
  function markSeg(sel, attr, val) {
    $$(sel + " button").forEach(function (b) { b.classList.toggle("sel", b.dataset[attr] === val); });
  }
  function tg(sel, onState) { var e = $(sel); if (e) e.classList.toggle("on", !!onState); }

  function buildThemeGrid() {
    var g = $("#theme-grid");
    g.innerHTML = THEMES.map(function (t) {
      return '<button class="theme-sw" data-theme="' + t.id + '" title="' + esc(t.name) + '" aria-label="' + esc(t.name) + '">' +
             '<span class="swatch" style="background:' + t.bg + ';color:' + t.fg + '">Aa</span>' +
             '<span class="nm">' + esc(t.name) + '</span></button>';
    }).join("");
    $$("#theme-grid .theme-sw").forEach(function (b) {
      on(b, "click", function () { S.settings.theme = b.dataset.theme; SettingsUI.apply(); });
    });
  }
  function buildPresets() {
    var r = $("#preset-row");
    r.innerHTML = Object.keys(PRESETS).map(function (n) {
      return '<button class="chip" data-preset="' + esc(n) + '">' + esc(n) + '</button>';
    }).join("");
    $$("#preset-row .chip").forEach(function (b) {
      on(b, "click", function () {
        Object.assign(S.settings, PRESETS[b.dataset.preset]);
        SettingsUI.apply(); toast("Andoza qo'llandi: " + b.dataset.preset);
      });
    });
  }

  function bindSettings() {
    on($("#font-range"), "input", function (e) { S.settings.fontScale = +e.target.value; SettingsUI.apply(); });
    on($("#font-inc"), "click", function () { S.settings.fontScale = clamp(+(S.settings.fontScale + 0.05).toFixed(2), 0.8, 2.2); SettingsUI.apply(); });
    on($("#font-dec"), "click", function () { S.settings.fontScale = clamp(+(S.settings.fontScale - 0.05).toFixed(2), 0.8, 2.2); SettingsUI.apply(); });
    on($("#lh-range"), "input", function (e) { S.settings.lineHeight = +e.target.value; SettingsUI.apply(); });
    on($("#ps-range"), "input", function (e) { S.settings.paraSpacing = +e.target.value; SettingsUI.apply(); });
    on($("#ws-range"), "input", function (e) { S.settings.wordSpacing = +e.target.value; SettingsUI.apply(); });
    on($("#ls-range"), "input", function (e) { S.settings.letterSpacing = +e.target.value; SettingsUI.apply(); });
    on($("#pm-range"), "input", function (e) { S.settings.pageMargin = +e.target.value; SettingsUI.apply(); });
    on($("#br-range"), "input", function (e) { S.settings.brightness = +e.target.value; SettingsUI.apply(); });
    on($("#font-family-sel"), "change", function (e) { S.settings.font = e.target.value; SettingsUI.apply(); });
    segBind("#width-seg", "width", function (v) { S.settings.width = v; });
    segBind("#align-seg", "align", function (v) { S.settings.align = v; });
    segBind("#weight-seg", "weight", function (v) { S.settings.weight = +v; });
    segBind("#anim-seg", "anim", function (v) { S.settings.anim = +v; });
    tgBind("#tg-dropcap", function (v) { S.settings.dropcap = v; });
    tgBind("#tg-reduce", function (v) { S.settings.reduceMotion = v; });
    tgBind("#tg-focus", function (v) { S.settings.focusRing = v; });
    tgBind("#tg-autohide", function (v) { S.settings.autohide = v; });
    on($("#reset-settings"), "click", function () {
      S.settings = Object.assign({}, DEFAULTS); SettingsUI.apply(); toast("Sozlamalar tiklandi");
    });
  }
  function segBind(sel, attr, setter) {
    $$(sel + " button").forEach(function (b) {
      on(b, "click", function () { setter(b.dataset[attr]); SettingsUI.apply(); });
    });
  }
  function tgBind(sel, setter) {
    on($(sel), "click", function () {
      var e = $(sel); var nv = !e.classList.contains("on"); setter(nv); SettingsUI.apply();
    });
  }

  /* ============================================================
     PANELS (drawers)
     ============================================================ */
  var overlay = $("#overlay");
  var openPanel = null;
  function panel(el) {
    if (openPanel === el) { closePanels(); return; }
    closePanels(true);
    el.classList.add("open"); overlay.classList.add("open");
    document.body.classList.add("modal-open");
    openPanel = el;
  }
  function closePanels(skipBodyClass) {
    $$(".drawer.open").forEach(function (d) { d.classList.remove("open"); });
    overlay.classList.remove("open");
    if (!skipBodyClass) document.body.classList.remove("modal-open");
    openPanel = null;
  }
  on(overlay, "click", function () { closePanels(); closeSearch(); });

  /* ============================================================
     TABLE OF CONTENTS
     ============================================================ */
  function buildTOC() {
    var ul = $("#toc");
    ul.innerHTML = chapterMeta.map(function (c) {
      return '<li><a href="#' + c.el.id + '" data-idx="' + c.idx + '">' +
        '<span class="toc-num">' + esc(disp(c.num) || ("§" + (c.idx + 1))) + '</span>' +
        '<span class="toc-name">' + esc(disp(c.title)) + '</span>' +
        '<span class="toc-pct" data-pct="' + c.idx + '"></span></a></li>';
    }).join("");
    $$("#toc a").forEach(function (a) {
      on(a, "click", function (e) {
        e.preventDefault();
        gotoChapter(+a.dataset.idx);
        closePanels();
      });
    });
  }
  function updateTOCActive(idx) {
    $$("#toc a").forEach(function (a) {
      var i = +a.dataset.idx;
      a.classList.toggle("active", i === idx);
      var pe = a.querySelector(".toc-pct");
      if (i < idx) { pe.textContent = "✓"; pe.classList.add("toc-read"); }
      else if (i === idx) { pe.textContent = chapterReadPct(idx) + "%"; pe.classList.remove("toc-read"); }
      else { pe.textContent = ""; pe.classList.remove("toc-read"); }
    });
  }

  function gotoChapter(idx) {
    idx = clamp(idx, 0, chapterMeta.length - 1);
    var el = chapterMeta[idx].el;
    smoothScrollTo(el.offsetTop - topbarOffset());
  }
  function topbarOffset() { return ($("#topbar").offsetHeight || 54) + 10; }
  function smoothScrollTo(y) {
    window.scrollTo({ top: Math.max(0, y), behavior: S.settings.anim > 0 && !S.settings.reduceMotion ? "smooth" : "auto" });
  }

  /* ============================================================
     PROGRESS / READING POSITION
     ============================================================ */
  var curChapter = 0;
  var progressBar = $("#progress-bar"), pctLabel = $("#pct-label"), curTitle = $("#cur-chapter-title");
  var progressTrack = $("#progress-track");

  function docHeight() {
    return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight) - window.innerHeight;
  }
  function scrollPct() {
    var h = docHeight(); return h <= 0 ? 0 : clamp(window.scrollY / h, 0, 1);
  }
  function chapterReadPct(idx) {
    var c = chapterMeta[idx]; if (!c) return 0;
    var top = c.el.offsetTop - topbarOffset();
    var next = chapterMeta[idx + 1] ? chapterMeta[idx + 1].el.offsetTop - topbarOffset() : document.body.scrollHeight;
    var span = next - top; if (span <= 0) return 100;
    return clamp(Math.round((window.scrollY - top) / span * 100), 0, 100);
  }
  function detectChapter() {
    var y = window.scrollY + topbarOffset() + 4;
    var idx = 0;
    for (var i = 0; i < chapterMeta.length; i++) {
      if (chapterMeta[i].el.offsetTop <= y) idx = i; else break;
    }
    return idx;
  }

  function updateProgress() {
    var p = scrollPct();
    var pctInt = Math.round(p * 100);
    progressBar.style.width = pctInt + "%";
    pctLabel.textContent = pctInt + "%";
    progressTrack.setAttribute("aria-valuenow", pctInt);
    var idx = detectChapter();
    if (idx !== curChapter) {
      curChapter = idx;
      updateTOCActive(idx);
      curTitle.textContent = disp(chapterMeta[idx].title);
    } else {
      var ae = $("#toc a.active .toc-pct");
      if (ae) ae.textContent = chapterReadPct(idx) + "%";
    }
    S.progress.scroll = window.scrollY;
    S.progress.pct = pctInt;
    updateNavButtons();
    Stats.onProgress(p);
    save();
  }

  function updateNavButtons() {
    var prev = $("#nav-prev"), next = $("#nav-next");
    var pi = curChapter - 1, ni = curChapter + 1;
    if (pi >= 0) { prev.disabled = false; $("#nav-prev-t").textContent = disp(chapterMeta[pi].title); }
    else { prev.disabled = true; $("#nav-prev-t").textContent = "—"; }
    if (ni < chapterMeta.length) { next.disabled = false; $("#nav-next-t").textContent = disp(chapterMeta[ni].title); }
    else { next.disabled = true; $("#nav-next-t").textContent = "—"; }
  }

  /* ============================================================
     HIGHLIGHTS & NOTES (range based, per paragraph)
     ============================================================ */
  function offsetWithin(paraEl, node, nodeOffset) {
    var off = 0, done = false;
    (function walk(n) {
      if (done) return;
      if (n === node) {
        if (n.nodeType === 3) { off += nodeOffset; }
        done = true; return;
      }
      if (n.nodeType === 3) { off += n.nodeValue.length; }
      else {
        for (var i = 0; i < n.childNodes.length; i++) {
          walk(n.childNodes[i]);
          if (done) return;
        }
        if (n === node) { done = true; }
      }
    })(paraEl);
    return off;
  }
  function closestPara(node) {
    while (node && node !== document) {
      if (node.nodeType === 1 && node.tagName === "P" && node.dataset && node.dataset.idx !== undefined) {
        return node;
      }
      node = node.parentNode;
    }
    return null;
  }

  function renderPara(idx) {
    // delegates to the combined painter (highlights + search) defined below
    paintPara(idx);
  }
  function renderAllHighlights() {
    var byP = {};
    S.highlights.forEach(function (h) { byP[h.p] = true; });
    Object.keys(byP).forEach(function (k) { renderPara(+k); });
  }

  function addHighlight(color) {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return;
    var range = sel.getRangeAt(0);
    var startP = closestPara(range.startContainer);
    var endP = closestPara(range.endContainer);
    if (!startP) { toast("Faqat matn ustida belgilang"); return; }
    var si = +startP.dataset.idx;
    var ei = endP ? +endP.dataset.idx : si;
    var created = [];
    var group = uid();
    for (var i = si; i <= ei; i++) {
      var text = PARA_TEXT[i];
      var s = 0, e = text.length;
      if (i === si) s = offsetWithin(startP, range.startContainer, range.startOffset);
      if (i === ei && endP) e = offsetWithin(endP, range.endContainer, range.endOffset);
      s = clamp(s, 0, text.length); e = clamp(e, 0, text.length);
      if (e <= s) continue;
      // remove overlapping existing highlights in this range
      S.highlights = S.highlights.filter(function (h) {
        return !(h.p === i && h.start < e && h.end > s);
      });
      var rec = { id: uid(), group: group, p: i, start: s, end: e, color: color,
                  text: text.slice(s, e), note: "", ts: Date.now(), ci: chapterOfPara(i) };
      S.highlights.push(rec);
      created.push(rec);
      renderPara(i);
    }
    save();
    clearSelection();
    toast("Belgilandi");
    return created[0];
  }
  function chapterOfPara(pIdx) {
    var p = paras[pIdx];
    for (var i = chapterMeta.length - 1; i >= 0; i--) {
      if (chapterMeta[i].el.contains(p)) return i;
    }
    return 0;
  }
  function removeHighlight(id) {
    var h = S.highlights.filter(function (x) { return x.id === id; })[0];
    if (!h) return;
    var grp = h.group;
    var affected = {};
    S.highlights.forEach(function (x) { if (x.group === grp) affected[x.p] = true; });
    S.highlights = S.highlights.filter(function (x) { return x.group !== grp; });
    Object.keys(affected).forEach(function (k) { renderPara(+k); });
    save(); Library.render(); toast("Belgilash o'chirildi");
  }
  function setHighlightNote(id, note) {
    S.highlights.forEach(function (h) { if (h.id === id) { h.note = note; } });
    var h = S.highlights.filter(function (x) { return x.id === id; })[0];
    if (h) renderPara(h.p);
    save(); Library.render();
  }
  function clearSelection() {
    var s = window.getSelection(); if (s) s.removeAllRanges();
    hideSelToolbar();
  }

  /* selection toolbar */
  var selBar = $("#sel-toolbar");
  var selContext = { mode: "new", hlId: null };
  function showSelToolbarForRange() {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) { hideSelToolbar(); return; }
    var p = closestPara(sel.anchorNode);
    if (!p) { hideSelToolbar(); return; }
    var rect = sel.getRangeAt(0).getBoundingClientRect();
    if (!rect.width && !rect.height) { hideSelToolbar(); return; }
    selContext.mode = "new"; selContext.hlId = null;
    $("#sel-remove").style.display = "none";
    positionSelBar(rect);
  }
  function showSelToolbarForHl(hlEl) {
    var rect = hlEl.getBoundingClientRect();
    selContext.mode = "edit"; selContext.hlId = hlEl.dataset.hl;
    $("#sel-remove").style.display = "";
    positionSelBar(rect);
  }
  function positionSelBar(rect) {
    selBar.classList.add("open");
    var bw = selBar.offsetWidth, bh = selBar.offsetHeight;
    var x = window.scrollX + rect.left + rect.width / 2 - bw / 2;
    var y = window.scrollY + rect.top - bh - 10;
    if (y < window.scrollY + topbarOffset()) y = window.scrollY + rect.bottom + 10;
    x = clamp(x, window.scrollX + 8, window.scrollX + window.innerWidth - bw - 8);
    selBar.style.left = x + "px";
    selBar.style.top = y + "px";
  }
  function hideSelToolbar() { selBar.classList.remove("open"); }

  function bindSelection() {
    $$("#sel-toolbar .sw").forEach(function (sw) {
      on(sw, "mousedown", function (e) { e.preventDefault(); });
      on(sw, "click", function () {
        var color = sw.dataset.color;
        if (selContext.mode === "edit" && selContext.hlId) {
          S.highlights.forEach(function (h) { if (h.id === selContext.hlId) h.color = color; });
          var h = S.highlights.filter(function (x) { return x.id === selContext.hlId; })[0];
          if (h) renderPara(h.p);
          save(); Library.render(); hideSelToolbar();
        } else {
          addHighlight(color); Library.render();
        }
      });
    });
    on($("#sel-note"), "click", function () {
      var hl;
      if (selContext.mode === "edit" && selContext.hlId) {
        hl = S.highlights.filter(function (x) { return x.id === selContext.hlId; })[0];
      } else {
        hl = addHighlight("yellow");
      }
      if (hl) { hideSelToolbar(); noteDialog(hl.id); }
    });
    on($("#sel-copy"), "click", function () {
      var txt = "";
      if (selContext.mode === "edit" && selContext.hlId) {
        var h = S.highlights.filter(function (x) { return x.id === selContext.hlId; })[0];
        txt = h ? h.text : "";
      } else {
        txt = String(window.getSelection());
      }
      copyText(txt); hideSelToolbar(); clearSelection();
    });
    on($("#sel-remove"), "click", function () {
      if (selContext.hlId) removeHighlight(selContext.hlId);
      hideSelToolbar();
    });

    // text selection events
    on(document, "selectionchange", function () {
      clearTimeout(selDebounce);
      selDebounce = setTimeout(function () {
        var sel = window.getSelection();
        if (sel && !sel.isCollapsed && sel.rangeCount && closestPara(sel.anchorNode)) {
          showSelToolbarForRange();
        } else if (selContext.mode === "new") {
          hideSelToolbar();
        }
      }, 60);
    });
    // click existing highlight
    on(book, "click", function (e) {
      var hl = e.target.closest && e.target.closest(".hl");
      if (hl) { showSelToolbarForHl(hl); }
    });
    on(document, "mousedown", function (e) {
      if (!selBar.contains(e.target) && !(e.target.closest && e.target.closest(".hl"))) {
        if (selContext.mode === "edit") hideSelToolbar();
      }
    });
  }
  var selDebounce;

  function noteDialog(hlId) {
    var h = S.highlights.filter(function (x) { return x.id === hlId; })[0];
    if (!h) return;
    openDialog(
      '<h3>Izoh</h3>' +
      '<div class="c-quote" style="margin-bottom:.6rem">' + esc(h.text.slice(0, 200)) + '</div>' +
      '<textarea class="field" id="note-text" placeholder="Izohingizni yozing...">' + esc(h.note || "") + '</textarea>' +
      '<div class="dialog-actions">' +
        '<button class="btn" id="note-cancel">Bekor</button>' +
        '<button class="btn primary" id="note-save">Saqlash</button>' +
      '</div>'
    );
    on($("#note-cancel"), "click", closeDialog);
    on($("#note-save"), "click", function () {
      setHighlightNote(hlId, $("#note-text").value.trim());
      closeDialog(); toast("Izoh saqlandi");
    });
  }

  function copyText(txt) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(function () { toast("Nusxalandi"); },
        function () { fallbackCopy(txt); });
    } else fallbackCopy(txt);
  }
  function fallbackCopy(txt) {
    try {
      var ta = document.createElement("textarea");
      ta.value = txt; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select(); document.execCommand("copy");
      document.body.removeChild(ta); toast("Nusxalandi");
    } catch (e) { toast("Nusxalab bo'lmadi"); }
  }

  /* ============================================================
     BOOKMARKS
     ============================================================ */
  function addBookmark(name) {
    var idx = curChapter;
    var bm = {
      id: uid(), y: window.scrollY, ci: idx,
      chapter: chapterMeta[idx].title,
      name: name || chapterMeta[idx].title,
      excerpt: nearestText(),
      pct: Math.round(scrollPct() * 100),
      ts: Date.now()
    };
    S.bookmarks.unshift(bm);
    save(); Library.render(); updateLibBadge();
    toast("Xatcho'p qo'shildi");
  }
  function nearestText() {
    var y = window.scrollY + window.innerHeight / 2;
    var best = "";
    for (var i = 0; i < paras.length; i++) {
      var r = paras[i].getBoundingClientRect();
      var top = r.top + window.scrollY;
      if (top >= window.scrollY && top <= window.scrollY + window.innerHeight) {
        best = paras[i].textContent.slice(0, 120); break;
      }
    }
    return best;
  }
  function gotoBookmark(bm) { smoothScrollTo(bm.y); closePanels(); }
  function removeBookmark(id) {
    S.bookmarks = S.bookmarks.filter(function (b) { return b.id !== id; });
    save(); Library.render(); updateLibBadge(); toast("O'chirildi");
  }
  function renameBookmark(id) {
    var bm = S.bookmarks.filter(function (b) { return b.id === id; })[0]; if (!bm) return;
    openDialog(
      '<h3>Xatcho\'p nomi</h3>' +
      '<input class="field" id="bm-name" value="' + esc(bm.name) + '">' +
      '<div class="dialog-actions"><button class="btn" id="bm-cancel">Bekor</button>' +
      '<button class="btn primary" id="bm-save">Saqlash</button></div>'
    );
    on($("#bm-cancel"), "click", closeDialog);
    on($("#bm-save"), "click", function () {
      bm.name = $("#bm-name").value.trim() || bm.chapter; save(); Library.render(); closeDialog();
    });
  }
  function updateLibBadge() {
    var n = S.bookmarks.length + S.highlights.length;
    $("#btn-library").classList.toggle("has-items", n > 0);
  }

  /* ============================================================
     LIBRARY (tabs)
     ============================================================ */
  var Library = {
    tab: "bookmarks",
    render: function () {
      this.renderBookmarks();
      this.renderHighlights();
      this.renderNotes();
      Stats.render();
    },
    renderBookmarks: function () {
      var box = $("#bookmarks-list");
      if (!S.bookmarks.length) { box.innerHTML = empty("Hali xatcho'p yo'q.<br>O'qiyotgan joyingizni saqlang."); return; }
      box.innerHTML = S.bookmarks.map(function (b) {
        return '<div class="card" data-bm="' + b.id + '">' +
          '<div class="c-loc">' + esc(disp(b.chapter)) + ' · ' + b.pct + '%</div>' +
          '<div class="c-title">' + esc(disp(b.name)) + '</div>' +
          (b.excerpt ? '<div class="c-text">' + esc(disp(b.excerpt)) + '…</div>' : '') +
          '<div class="c-meta"><span>' + fmtDate(b.ts) + '</span><span class="c-actions">' +
            '<button data-act="rename" title="Tahrirlash">' + icon("edit") + '</button>' +
            '<button data-act="del" title="O\'chirish">' + icon("trash") + '</button>' +
          '</span></div></div>';
      }).join("");
      bindCards(box, function (id) { gotoBookmark(S.bookmarks.filter(function (b) { return b.id === id; })[0]); },
        { rename: renameBookmark, del: removeBookmark }, "bm");
    },
    renderHighlights: function () {
      var box = $("#highlights-list");
      if (!S.highlights.length) { box.innerHTML = empty("Belgilash yo'q.<br>Matnni tanlab rang tanlang."); return; }
      var sorted = S.highlights.slice().sort(function (a, b) { return a.p - b.p || a.start - b.start; });
      box.innerHTML = sorted.map(function (h) {
        return '<div class="card" data-hl="' + h.id + '">' +
          '<div class="c-loc"><span class="swatch" style="background:var(--hl-' + h.color + ')"></span>' + esc(disp(chapterMeta[h.ci] ? chapterMeta[h.ci].title : "")) + '</div>' +
          '<div class="c-quote">' + esc(disp(h.text.slice(0, 240))) + '</div>' +
          (h.note ? '<div class="c-text">📝 ' + esc(h.note) + '</div>' : '') +
          '<div class="c-meta"><span>' + fmtDate(h.ts) + '</span><span class="c-actions">' +
            '<button data-act="note" title="Izoh">' + icon("note") + '</button>' +
            '<button data-act="del" title="O\'chirish">' + icon("trash") + '</button>' +
          '</span></div></div>';
      }).join("");
      bindCards(box, function (id) {
        var h = S.highlights.filter(function (x) { return x.id === id; })[0];
        if (h) { scrollToPara(h.p); closePanels(); }
      }, { note: noteDialog, del: removeHighlight }, "hl");
    },
    renderNotes: function () {
      var box = $("#notes-list");
      var q = ($("#notes-search").value || "").toLowerCase();
      var withNotes = S.highlights.filter(function (h) { return h.note; });
      if (q) withNotes = withNotes.filter(function (h) {
        return h.note.toLowerCase().indexOf(q) >= 0 || h.text.toLowerCase().indexOf(q) >= 0;
      });
      if (!withNotes.length) { box.innerHTML = empty(q ? "Topilmadi." : "Izoh yo'q.<br>Belgilashga izoh qo'shing."); return; }
      box.innerHTML = withNotes.sort(function (a, b) { return b.ts - a.ts; }).map(function (h) {
        return '<div class="card" data-hl="' + h.id + '">' +
          '<div class="c-loc"><span class="swatch" style="background:var(--hl-' + h.color + ')"></span>' + esc(disp(chapterMeta[h.ci] ? chapterMeta[h.ci].title : "")) + '</div>' +
          '<div class="c-quote">' + esc(disp(h.text.slice(0, 160))) + '</div>' +
          '<div class="c-text">' + esc(h.note) + '</div>' +
          '<div class="c-meta"><span>' + fmtDate(h.ts) + '</span><span class="c-actions">' +
            '<button data-act="note" title="Tahrirlash">' + icon("edit") + '</button>' +
            '<button data-act="del" title="O\'chirish">' + icon("trash") + '</button>' +
          '</span></div></div>';
      }).join("");
      bindCards(box, function (id) {
        var h = S.highlights.filter(function (x) { return x.id === id; })[0];
        if (h) { scrollToPara(h.p); closePanels(); }
      }, { note: noteDialog, del: removeHighlight }, "hl");
    }
  };
  function empty(msg) { return '<div class="list-empty">' + msg + '</div>'; }
  function scrollToPara(pIdx) {
    var p = paras[pIdx]; if (!p) return;
    smoothScrollTo(p.getBoundingClientRect().top + window.scrollY - topbarOffset() - 40);
    p.style.transition = "background .2s"; var prev = p.style.background;
    p.style.background = "var(--sel)";
    setTimeout(function () { p.style.background = prev; }, 900);
  }
  function bindCards(box, onOpen, actions, attr) {
    $$(".card", box).forEach(function (card) {
      var id = card.dataset[attr];
      on(card, "click", function (e) {
        if (e.target.closest("[data-act]")) return;
        onOpen(id);
      });
      $$("[data-act]", card).forEach(function (btn) {
        on(btn, "click", function (e) { e.stopPropagation(); actions[btn.dataset.act](id); });
      });
    });
  }
  function icon(name) {
    var p = {
      edit: '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4z"/>',
      trash: '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M10 11v6M14 11v6"/>',
      note: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
    };
    return '<svg viewBox="0 0 24 24">' + (p[name] || "") + '</svg>';
  }
  function fmtDate(ts) {
    var d = new Date(ts);
    return d.getDate() + "." + (d.getMonth() + 1) + "." + d.getFullYear() + " " +
      ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2);
  }

  /* tabs */
  function bindTabs() {
    $$("#lib-tabs button").forEach(function (b) {
      on(b, "click", function () {
        Library.tab = b.dataset.tab;
        $$("#lib-tabs button").forEach(function (x) { x.classList.toggle("sel", x === b); });
        $$(".drawer-body .tabpane", $("#library")).forEach(function (p) { p.classList.remove("sel"); });
        $("#tab-" + b.dataset.tab).classList.add("sel");
        if (b.dataset.tab === "stats") Stats.render();
        if (b.dataset.tab === "glossary") Glossary.render();
      });
    });
    on($("#notes-search"), "input", function () { Library.renderNotes(); });
  }

  /* ==== forward-declared modules (defined in continuation below) ==== */
  /* Stats, Glossary, closeSearch are assigned later in the same IIFE scope. */
  var Stats, Glossary;

