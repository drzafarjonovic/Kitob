#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-book premium reader generator.

Reads each book's `matn.txt`, cleans noise (page numbers, watermarks, repeated
running headers, front/back matter), splits into chapters, re-flows the
hard-wrapped lines into paragraphs, and assembles a self-contained reader HTML
per book by reusing the shared engine (head.html + chrome + app.js + part2.js).

Also builds the `index.html` library landing page linking to all books.

Output files are written to the repository root so the relative references to
icons/, manifest.json and sw.js keep working.
"""
import os, re, html, json

BASE = os.path.dirname(os.path.abspath(__file__))      # .../Kitob/build
ROOT = os.path.dirname(BASE)                            # .../Kitob
BOOKDIR = os.path.join(ROOT, "Garri Potter kitoblari")

def _favicon():
    import base64
    try:
        b = open(os.path.join(ROOT, "icons", "icon.svg"), "rb").read()
        return "data:image/svg+xml;base64," + base64.b64encode(b).decode()
    except Exception:
        return "icons/icon.svg"

FAVICON = _favicon()

# ----------------------------------------------------------------------------
# Book catalogue
# ----------------------------------------------------------------------------
BOOKS = [
    dict(n=1, key="gp_reader_b1", folder="1 - Afsungarlar Toshi",
         title="Falsafiy Tosh", sub="Birinchi kitob",
         accent="#7b1113"),
    dict(n=2, key="gp_reader_b2", folder="2 - Sirlar Xonasi",
         title="Maxfiy Xona", sub="Ikkinchi kitob",
         accent="#1f6f4a"),
    dict(n=3, key="gp_reader_b3", folder="3 - Azkaban Mahbusi",
         title="Azkaban Mahbusi", sub="Uchinchi kitob",
         accent="#5b3a8a"),
    dict(n=4, key="gp_reader_b4", folder="4 - Olovli Kosa",
         title="Otashli Jom", sub="To\u02bbrtinchi kitob",
         accent="#b5651d"),
    dict(n=5, key="gp_reader_b5", folder="5 - Feniks Ordeni",
         title="Qaqnus Ordeni", sub="Beshinchi kitob",
         accent="#1d6fa5"),
    dict(n=6, key="gp_reader_b6", folder="6 - Yarim Qonli Shahzoda",
         title="Chala Zot Shahzoda", sub="Oltinchi kitob",
         accent="#7a5901"),
    dict(n=7, key="gp_reader_b7", folder="7 - Ajal Tuhfalari",
         title="Ajal Tuhfalari", sub="Yettinchi kitob",
         accent="#4a4a4a", cut_at=26168),
    dict(n=8, key="gp_reader_b8", folder="8 - La'natlangan Bola",
         title="La'natlangan Bola", sub="Sakkizinchi kitob \u00b7 Sahna asari",
         accent="#0b5d63"),
]

# ----------------------------------------------------------------------------
# Cleaning helpers
# ----------------------------------------------------------------------------
WATERMARK = re.compile(r"(t\.me|Admin\s*:|@[A-Za-z0-9_]{3,}|uForum|pottermanlar)", re.I)
PAGENUM   = re.compile(r"^\s*\d{1,4}\s*$")

# Chapter heading: optional roman / cyrillic-uppercase ordinal prefix, then БОБ/BOB
HEAD_RE = re.compile(
    r"^\s*((?:[IVXLCDM]+|[\u0410-\u042f\u040e\u0492\u049a\u0498\u04b2\u0401]+"
    r"(?:\s+[\u0410-\u042f\u040e\u0492\u049a\u0498\u04b2\u0401]+)?)\s+)?"
    r"(\u0411\u041e\u0411|BOB)\b\.?\s*(.*)$"
)

EPILOGUE = {"\u0425\u041e\u0422\u0418\u041c\u0410", "\u042d\u041f\u0418\u041b\u041e\u0413",
            "XOTIMA", "EPILOG"}

def is_heading(line):
    s = line.strip()
    if not s or len(s) > 80:
        return None
    if s in EPILOGUE:
        return s
    m = HEAD_RE.match(s)
    if not m:
        return None
    prefix, _bob, title = m.group(1), m.group(2), m.group(3)
    # must start with БОБ/BOB or a roman / ordinal-word prefix
    if prefix is None and not (s.startswith("\u0411\u041e\u0411") or s.startswith("BOB")):
        return None
    title = title.strip(" .\u2014-")
    if len(title) > 64:
        return None
    return title

def load_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")

def clean_lines(raw, cut_at=None):
    if cut_at:
        raw = raw[:cut_at]
    # frequency of short lines -> repeated running headers.
    # Restrict to UPPERCASE-dominant lines so we never strip real dialogue
    # like "Garri." or "Germiona." that legitimately repeats.
    freq = {}
    for ln in raw:
        s = ln.strip()
        if s and len(s) < 50 and s == s.upper() and any(c.isalpha() for c in s):
            freq[s] = freq.get(s, 0) + 1
    repeated = set(s for s, c in freq.items()
                   if c > 4 and not is_heading(s) and not PAGENUM.match(s))
    out = []
    for ln in raw:
        s = ln.strip()
        if not s:
            out.append("")           # keep blank as a soft separator
            continue
        if PAGENUM.match(ln):
            continue
        if WATERMARK.search(s):
            continue
        if s in repeated:
            continue
        out.append(ln.rstrip())
    return out

def split_chapters(lines):
    """Return list of (title, [body_lines]). Lines before the first heading
    (front matter) are dropped."""
    chapters = []
    cur_title, cur_body = None, []
    for ln in lines:
        t = is_heading(ln)
        if t is not None:
            if cur_title is not None:
                chapters.append((cur_title, cur_body))
            cur_title, cur_body = (t if t else "Bob"), []
        else:
            if cur_title is not None:
                cur_body.append(ln)
    if cur_title is not None:
        chapters.append((cur_title, cur_body))
    return chapters

SEP_RE = re.compile(r"^[\s*\u2022\u25c6\u25cf\u2727\u2731.\u2014\u2013-]{3,}$")

def reflow(body):
    """Re-assemble hard-wrapped lines into paragraphs / scene separators."""
    widths = [len(l) for l in body if l.strip()]
    if widths:
        widths.sort()
        maxw = widths[int(len(widths) * 0.9)]
    else:
        maxw = 80
    thresh = max(40, maxw - 12)
    paras, cur = [], []

    def flush():
        if cur:
            paras.append(" ".join(x.strip() for x in cur).strip())
            cur.clear()

    for raw in body:
        s = raw.strip()
        if not s:
            flush(); continue
        if SEP_RE.match(s) and len(s) <= 12:
            flush(); paras.append("@@SEP@@"); continue
        dialogue = s[0] in "-\u2013\u2014"
        indented = (len(raw) - len(raw.lstrip())) >= 2
        if cur and (dialogue or indented):
            flush()
        cur.append(s)
        if len(s) < thresh:
            flush()
    flush()
    # collapse consecutive separators / leading-trailing seps
    cleaned = []
    for p in paras:
        if p == "@@SEP@@" and (not cleaned or cleaned[-1] == "@@SEP@@"):
            continue
        cleaned.append(p)
    while cleaned and cleaned[0] == "@@SEP@@":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "@@SEP@@":
        cleaned.pop()
    return cleaned

def chapter_html(idx, title, paras):
    num = "XOTIMA" if title in EPILOGUE else ("%d-BOB" % (idx + 1))
    out = ['<section class="chapter" id="ch-%d">' % (idx + 1)]
    out.append('<div class="chapter-head"><div class="chapter-num">%s</div>'
               '<h2 class="chapter-title">%s</h2></div>' % (num, html.escape(title)))
    for p in paras:
        if p == "@@SEP@@":
            out.append('<div class="scene-sep">\u2727 \u2727 \u2727</div>')
        else:
            out.append("<p>%s</p>" % html.escape(p))
    out.append("</section>")
    return "\n".join(out)

# ----------------------------------------------------------------------------
# Shared glossary (books 1-7)
# ----------------------------------------------------------------------------
GLOSSARY = {
    "Qahramonlar": [
        ["Garri Potter", "Tirik qolgan bola; peshonasidagi chaqmoq izi bilan tanilgan bosh qahramon."],
        ["Ron Uizli", "Garrining sodiq do\u02bbsti, Uizlilar oilasining kenja o\u02bbg\u02bbli."],
        ["Germiona Greynjer", "Aqlli va kitobsevar jodugar; uchlikning uchinchi a'zosi."],
        ["Albus Dambldor", "Xogvarts maktabining donishmand bosh direktori."],
        ["Severus Snegg", "Iksirlar ustozi; sirli va ziddiyatli shaxs."],
        ["Lord Voldemort", "Nomi aytilmaydigan qora sehrgar; asosiy yovuz kuch."],
        ["Rubeus Hagrid", "Xogvarts o\u02bbrmonbonisi va Garrining mehribon do\u02bbsti."],
    ],
    "Joylar": [
        ["Xogvarts", "Sehrgarlik va jodugarlik maktabi."],
        ["Diagon xiyoboni", "Sehrli savdo ko\u02bbchasi."],
        ["To\u02bbqqiz-uchdan-bir platforma", "Xogvarts ekspressiga chiqiladigan sirli platforma."],
        ["Sehrgarlik vazirligi", "Sehrli dunyo hukumati."],
    ],
    "Sehrlar": [
        ["Expelliarmus", "Qurolsizlantirish sehri."],
        ["Lumos", "Hassa uchini yorituvchi sehr."],
        ["Expecto Patronum", "Dementorlardan himoya qiluvchi homiy sehri."],
        ["Wingardium Leviosa", "Buyumlarni havoga ko\u02bbtaruvchi sehr."],
    ],
    "Atamalar": [
        ["Maripat (Magl)", "Sehrli qobiliyatga ega bo\u02bblmagan oddiy odam."],
        ["Kviddich", "Supurgilarda o\u02bbynaladigan sehrli sport o\u02bbyini."],
        ["Dementor", "Baxtni so\u02bbruvchi qorong\u02bbu maxluq."],
        ["Fakultetlar", "Gryffindor, Slizerin, Puffenduy va Kogtevran."],
    ],
}

# ----------------------------------------------------------------------------
# "Sehrli Olam" (Wizarding World) — interaktiv ensiklopediya ma'lumotlari.
# Har maqola `book` maydoni bilan belgilangan: u qaysi kitobda ochilishini
# bildiradi va spoiler himoyasi shu asosda ishlaydi.
# cat: qahramon | joy | sehr | mavjudot | buyum | fakultet
# ----------------------------------------------------------------------------
def _e(id, name, cat, book, tag, desc, house="", rel=None, c1="", c2=""):
    return {"id": id, "name": name, "cat": cat, "book": book, "house": house,
            "tag": tag, "desc": desc, "rel": rel or [], "c1": c1, "c2": c2}

def _l(name, x, y, book, tag, desc, ref=""):
    return {"name": name, "x": x, "y": y, "book": book, "tag": tag, "desc": desc, "ref": ref}

def _f(name, x, y, book, house=""):
    return {"name": name, "x": x, "y": y, "book": book, "house": house}

WORLD = {
    "entries": [
        # ---- Qahramonlar ----
        _e("garri", "Garri Potter", "qahramon", 1, "Tirik qolgan bola",
           "Peshonasidagi chaqmoq izi bilan tanilgan bosh qahramon. Voldemort hujumidan omon qolgan yagona bola; Gryffindor fakultetida o'qiydi.",
           "gryffindor", ["ron", "germiona", "voldemort", "dambldor", "lily_james"]),
        _e("ron", "Ron Uizli", "qahramon", 1, "Sodiq do'st",
           "Garrining eng yaqin do'sti, katta Uizlilar oilasining kenja o'g'li. Mard, hazilkash va sadoqatli.",
           "gryffindor", ["garri", "germiona", "moli", "fred_jorj", "jinni"]),
        _e("germiona", "Germiona Greynjer", "qahramon", 1, "Zukko jodugar",
           "Maripat oilasidan chiqqan g'oyat aqlli va kitobsevar jodugar; uchlikning miyasi. Keyinchalik Sehrgarlik vaziri bo'ladi.",
           "gryffindor", ["garri", "ron"]),
        _e("dambldor", "Albus Dambldor", "qahramon", 1, "Bosh direktor",
           "Xogvartsning donishmand bosh direktori, davrning eng qudratli sehrgari. Garrining ustozi va himoyachisi.",
           "gryffindor", ["garri", "snegg", "voldemort", "feniks"]),
        _e("hagrid", "Rubeus Hagrid", "qahramon", 1, "O'rmonboni",
           "Yarim-gigant, Xogvarts o'rmonbonisi va Garrining mehribon do'sti. Sehrli mavjudotlarni juda sevadi.",
           "gryffindor", ["garri", "aragog", "bakljak"]),
        _e("snegg", "Severus Snegg", "qahramon", 1, "Iksirlar ustozi",
           "Sirli va ziddiyatli Iksirlar ustozi, Slizerin dekani. Uning haqiqiy sadoqati kitob so'ngida ochiladi.",
           "slizerin", ["dambldor", "garri", "lily_james", "voldemort"]),
        _e("makgonagal", "Minerva Makgonagal", "qahramon", 1, "Transfiguratsiya ustozi",
           "Qat'iyatli Transfiguratsiya professori va Gryffindor dekani; anigamag (mushukka aylana oladi).",
           "gryffindor", ["dambldor"]),
        _e("voldemort", "Lord Voldemort", "qahramon", 1, "Nomi aytilmaydigan",
           "Asl ismi Tom Ridl. Asrning eng qora sehrgari, sehrli dunyoni bo'ysundirishga intilgan asosiy yovuz kuch.",
           "slizerin", ["garri", "bellatrisa", "xorkruks", "snegg"]),
        _e("draco", "Drako Malfoy", "qahramon", 1, "Slizerin raqibi",
           "Kibrli sof qonli sehrgar, Garrining maktabdagi asosiy raqibi. Malfoy oilasining vorisi.",
           "slizerin", ["snegg", "voldemort"]),
        _e("nevill", "Nevill Longbottom", "qahramon", 1, "Botir gerbolog",
           "Dastlab uquvsiz ko'ringan, ammo jasoratli Gryffindor o'quvchisi; gerbologiyada iqtidorli.",
           "gryffindor", ["garri", "luna"]),
        _e("jinni", "Jinni Uizli", "qahramon", 2, "Uizlilarning qizi",
           "Uizlilar oilasining yagona qizi; kuchli va mustaqil jodugar. Keyinchalik Garrining rafiqasi bo'ladi.",
           "gryffindor", ["ron", "garri", "moli"]),
        _e("dobbi", "Dobbi", "qahramon", 2, "Ozod uy-elfi",
           "Malfoylar xizmatidagi uy-elfi; Garrini ogohlantirib himoya qiladi va oxir-oqibat ozodlikka erishadi.",
           "", ["garri", "draco"]),
        _e("sirius", "Sirius Blek", "qahramon", 3, "Garrining cho'qintirgan otasi",
           "Azkabandan qochgan begunoh mahbus; aslida Garrining cho'qintirgan otasi va sodiq himoyachisi. Anigamag (qora it).",
           "gryffindor", ["garri", "lyupin", "petigryu"]),
        _e("lyupin", "Remus Lyupin", "qahramon", 3, "Bo'ri-odam ustoz",
           "Mehribon Qora kuchlardan himoya ustozi; bo'ri-odam. Sirius va Jeymsning eski do'sti.",
           "gryffindor", ["sirius", "petigryu", "garri"]),
        _e("petigryu", "Piter Petigryu", "qahramon", 3, "Sotqin",
           "Jeyms Potterning eski do'sti; Potterlar sirini Voldemortga sotgan xoin. Anigamag (kalamush).",
           "gryffindor", ["sirius", "lyupin", "voldemort"]),
        _e("sedrik", "Sedrik Diggori", "qahramon", 4, "Xogvarts chempioni",
           "Halol va olijanob Puffenduy o'quvchisi, Uch Afsungar Bellashuvi ishtirokchisi. Uning fojiasi seriyada burilish nuqtasi bo'ladi.",
           "puffenduy", ["garri", "voldemort"]),
        _e("muudi", "Alastor Muudi", "qahramon", 4, "Sehrgar-ovchi",
           "Sirli ko'zi bilan tanilgan taniqli qora sehrgar-ovchi (auror); \"Doimo hushyor!\" shiori bilan mashhur.",
           "", ["dambldor"]),
        _e("umbrij", "Doloris Umbrij", "qahramon", 5, "Vazirlik nozirasi",
           "Pushti kiyingan, zohiran shirin, aslida shafqatsiz Vazirlik amaldori; Xogvartsda zolim tartib o'rnatadi.",
           "slizerin", ["vazirlik"]),
        _e("bellatrisa", "Bellatrisa Lestranj", "qahramon", 5, "Sodiq izdosh",
           "Voldemortning eng fanatik va shafqatsiz izdoshi; kuchli qora jodugar.",
           "slizerin", ["voldemort", "sirius"]),
        _e("luna", "Luna Lavgud", "qahramon", 5, "Xayolparast",
           "G'ayrioddiy, samimiy va dono Kogtevran o'quvchisi; boshqalar shubha qilgan narsalarga ishonadi.",
           "kogtevran", ["garri", "nevill"]),
        _e("slughorn", "Horas Slughorn", "qahramon", 6, "Iksirlar ustozi",
           "Nufuzli shogirdlarni yig'ishni yaxshi ko'radigan Iksirlar professori; Voldemortning o'tmishi haqida muhim sirni saqlaydi.",
           "slizerin", ["voldemort", "dambldor"]),
        _e("fred_jorj", "Fred va Jorj Uizli", "qahramon", 1, "Hazil ustalari",
           "Uizlilar oilasining egizak aka-ukalari; hazil-mutoyiba va ixtirolari bilan mashhur.",
           "gryffindor", ["ron", "moli"]),
        _e("moli", "Moli Uizli", "qahramon", 1, "Mehribon ona",
           "Uizlilar oilasining g'amxo'r onasi; Garrini o'z farzandidek qabul qiladi.",
           "gryffindor", ["ron", "jinni", "fred_jorj"]),
        _e("lily_james", "Lili va Jeyms Potter", "qahramon", 1, "Garrining ota-onasi",
           "Garrini himoya qilib halok bo'lgan ota-ona. Lilining muhabbat qurboni Garrini Voldemortdan asraydi.",
           "gryffindor", ["garri", "voldemort", "snegg"]),

        # ---- Joylar ----
        _e("xogvarts", "Xogvarts", "joy", 1, "Sehrgarlik maktabi",
           "Sehrgarlik va jodugarlik maktabi; to'rt fakultetga bo'lingan qadimiy qal'a. Voqealarning asosiy maskani.",
           "", ["gryffindor", "slizerin", "puffenduy", "kogtevran", "ormon"]),
        _e("diagon", "Diagon xiyoboni", "joy", 1, "Sehrli savdo ko'chasi",
           "Sehrgarlar xarid qiladigan yashirin savdo ko'chasi: tayoqchalar, kitoblar, buyumlar.",
           "", ["gringotts"]),
        _e("platform", "To'qqiz-uchdan-bir platforma", "joy", 1, "Sirli platforma",
           "Kings Kross vokzalidagi 9¾ platforma; Xogvarts ekspressiga shu yerdan chiqiladi.",
           "", ["xogvarts"]),
        _e("gringotts", "Gringotts banki", "joy", 1, "Sehrgarlar banki",
           "Goblinlar boshqaradigan yer ostidagi eng xavfsiz sehrli bank.",
           "", ["diagon"]),
        _e("ormon", "Taqiqlangan o'rmon", "joy", 1, "Sirli o'rmon",
           "Xogvarts yonidagi xatarli o'rmon; kentavrlar, akromantulalar va boshqa mavjudotlar makoni.",
           "", ["hagrid", "aragog", "xogvarts"]),
        _e("maxfiyxona", "Maxfiy Xona", "joy", 2, "Yashirin xona",
           "Salazar Slizerin qurgan afsonaviy yashirin xona; ichida qo'rqinchli maxluq yashiringan.",
           "", ["bazilisk", "voldemort"]),
        _e("azkaban", "Azkaban", "joy", 3, "Sehrgarlar qamoqxonasi",
           "Dementorlar qo'riqlaydigan dahshatli sehrli qamoqxona.",
           "", ["dementor", "sirius"]),
        _e("xogsmid", "Xogsmid", "joy", 3, "Sehrgarlar qishlog'i",
           "Britaniyadagi yagona to'liq sehrli qishloq; Xogvarts o'quvchilari dam olishga boradi.",
           "", ["xogvarts"]),
        _e("vazirlik", "Sehrgarlik Vazirligi", "joy", 5, "Sehrli hukumat",
           "Sehrli dunyoning hukumati; qonunlar va tartibni boshqaradi.",
           "", ["umbrij"]),
        _e("godrik", "Godrik Jarligi", "joy", 7, "Potterlar qishlog'i",
           "Potter oilasi yashagan qishloq; Garrining ota-onasi shu yerda halok bo'lgan.",
           "", ["lily_james", "garri"]),

        # ---- Sehrlar ----
        _e("expelliarmus", "Expelliarmus", "sehr", 1, "Qurolsizlantirish",
           "Raqibning tayoqchasini qo'lidan uchirib yuboruvchi sehr; Garrining eng sevimli afsuni.",
           "", ["garri"]),
        _e("lumos", "Lumos", "sehr", 1, "Yorug'lik",
           "Tayoqcha uchini chiroqdek yorituvchi oddiy, ammo foydali sehr.", ""),
        _e("wingardium", "Wingardium Leviosa", "sehr", 1, "Havoga ko'tarish",
           "Buyumlarni havoga ko'taruvchi sehr; birinchi kursda o'rganiladi.",
           "", ["germiona", "ron"]),
        _e("patronum", "Expecto Patronum", "sehr", 3, "Homiy sehri",
           "Dementorlardan himoya qiluvchi nurli homiy chaqiruvchi murakkab sehr; baxtli xotira talab qiladi.",
           "", ["dementor", "garri"]),
        _e("avada", "Avada Kedavra", "sehr", 4, "O'lim sehri",
           "Uch kechirilmas sehrdan biri — bir zumda o'ldiruvchi la'nat. Undan himoya yo'q.",
           "", ["voldemort"]),
        _e("accio", "Accio", "sehr", 4, "Chaqiruv",
           "Uzoqdagi buyumni o'ziga tortib chaqiruvchi sehr.", ""),
        _e("sectumsempra", "Sectumsempra", "sehr", 6, "Kesuvchi la'nat",
           "Snegg o'ylab topgan, ko'rinmas qilich kabi chuqur yara qoldiruvchi xatarli sehr.",
           "", ["snegg"]),
        _e("obliviate", "Obliviate", "sehr", 2, "Xotirani o'chirish",
           "Insonning xotirasini o'chiruvchi yoki o'zgartiruvchi sehr.", ""),

        # ---- Mavjudotlar ----
        _e("dementor", "Dementor", "mavjudot", 3, "Baxt o'g'risi",
           "Insondan barcha xursandchilikni so'rib oluvchi qorong'u maxluq; Azkabanni qo'riqlaydi.",
           "", ["azkaban", "patronum"]),
        _e("bazilisk", "Bazilisk", "mavjudot", 2, "Ilonlar shohi",
           "Nigohi o'ldiruvchi ulkan ilon; Maxfiy Xonada yashiringan.",
           "", ["maxfiyxona"]),
        _e("bakljak", "Bakljak", "mavjudot", 3, "Hipogrif",
           "Yarim-burgut, yarim-ot mag'rur mavjudot; Hagridning suyukli hayvoni.",
           "", ["hagrid", "sirius"]),
        _e("feniks", "Feniks", "mavjudot", 2, "Olovqush",
           "Yonib qayta tug'iluvchi sehrli qush; ko'z yoshlari davolaydi. Dambldorning hamrohi.",
           "", ["dambldor"]),
        _e("aragog", "Aragog", "mavjudot", 2, "Ulkan o'rgimchak",
           "Taqiqlangan o'rmonda yashovchi gapiradigan akromantul; Hagridning eski do'sti.",
           "", ["hagrid", "ormon"]),
        _e("bogart", "Bogart", "mavjudot", 3, "Qo'rquv maxlug'i",
           "Har kimga uning eng qo'rqadigan narsasi qiyofasida ko'rinuvchi shakl o'zgartiruvchi mavjudot; \"Riddikulus\" bilan yengiladi.",
           "", ["lyupin"]),

        # ---- Buyumlar ----
        _e("falsafiytosh", "Falsafiy Tosh", "buyum", 1, "Abadiylik toshi",
           "Har qanday metallni oltinga aylantiruvchi va abadiy hayot beruvchi afsonaviy tosh.",
           "", ["voldemort"]),
        _e("kundalik", "Ridl kundaligi", "buyum", 2, "Sirli kundalik",
           "Yosh Tom Ridlning xotirasini saqlagan sehrli kundalik; aslida Voldemortning bir bo'lagi.",
           "", ["voldemort", "xorkruks", "jinni"]),
        _e("rido", "Ko'rinmas rido", "buyum", 1, "Yashirin libos",
           "Kiygan kishini butunlay ko'rinmas qiluvchi kamyob rido; Garriga otasidan meros.",
           "", ["garri", "tuhfalar"]),
        _e("xarita", "Qaroqchilar xaritasi", "buyum", 3, "Sehrli xarita",
           "Xogvartsdagi har bir insonning joylashuvini real vaqtda ko'rsatuvchi sehrli xarita.",
           "", ["garri", "lyupin", "sirius"]),
        _e("vaqt", "Vaqt Aylantirgich", "buyum", 3, "Vaqt asbobi",
           "Egasini bir necha soat orqaga qaytaruvchi kichik sehrli asbob.",
           "", ["germiona"]),
        _e("jom", "Otashli Jom", "buyum", 4, "Chempion tanlovchi",
           "Uch Afsungar Bellashuvi chempionlarini tanlaydigan sehrli jom (kubok).",
           "", ["sedrik", "garri"]),
        _e("xorkruks", "Xorkrukslar", "buyum", 6, "Jon parchalari",
           "Voldemort o'z jonini bo'lib yashirgan buyumlar; ularni yo'q qilmaguncha u o'lmaydi.",
           "", ["voldemort", "kundalik", "tuhfalar"]),
        _e("tuhfalar", "Ajal Tuhfalari", "buyum", 7, "Uch muqaddas buyum",
           "Buzilmas tayoqcha, Tiriltiruvchi tosh va Ko'rinmas rido — o'lim ustidan hokimlik beruvchi uch buyum.",
           "", ["rido", "voldemort"]),
        _e("shlyapa", "Saralovchi Shlyapa", "buyum", 1, "Fakultet tanlovchi",
           "Yangi o'quvchilarni to'rt fakultetga taqsimlovchi gapiradigan qadimiy shlyapa.",
           "", ["gryffindor", "slizerin", "puffenduy", "kogtevran"]),
        _e("oyna", "Yeshek Oynasi", "buyum", 1, "Orzular ko'zgusi",
           "Insonga qalbining eng chuqur orzusini ko'rsatuvchi sehrli ko'zgu.",
           "", ["garri", "dambldor"]),

        # ---- Fakultetlar ----
        _e("gryffindor", "Gryffindor", "fakultet", 1, "Jasorat va mardlik",
           "Jasur, mard va olijanob yuraklilar fakulteti. Ramzi — sher; ranglari qizil va oltin.",
           "", ["garri", "ron", "germiona", "dambldor"], "#7b1113", "#d4af37"),
        _e("slizerin", "Slizerin", "fakultet", 1, "Topqirlik va iroda",
           "Ayyor, qat'iyatli va maqsadga intiluvchilar fakulteti. Ramzi — ilon; ranglari yashil va kumush.",
           "", ["snegg", "draco", "voldemort"], "#1a472a", "#a7b0b3"),
        _e("puffenduy", "Puffenduy", "fakultet", 1, "Sadoqat va halollik",
           "Mehnatkash, sodiq va adolatlilar fakulteti. Ramzi — bo'rsiq; ranglari sariq va qora.",
           "", ["sedrik"], "#d3a625", "#372e29"),
        _e("kogtevran", "Kogtevran", "fakultet", 1, "Donishmandlik va zukkolik",
           "Aqlli, ijodkor va bilimga chanqoqlar fakulteti. Ramzi — burgut; ranglari ko'k va bronza.",
           "", ["luna"], "#0e1a40", "#946b2d"),
    ],
    "timeline": [
        {"year": "1926", "book": 6, "title": "Tom Ridlning tug'ilishi",
         "desc": "Kelajakda Lord Voldemortga aylanadigan Tom Ridl dunyoga keladi."},
        {"year": "1980", "book": 1, "title": "Garri Potter tug'iladi",
         "desc": "Bashoratda tilga olingan bola \u2014 Garri \u2014 dunyoga keladi."},
        {"year": "1981", "book": 1, "title": "Voldemortning qulashi",
         "desc": "Voldemort Potterlarni o'ldiradi, biroq Garriga qilgan la'nati o'ziga qaytib, u yo'qoladi. Garri \"Tirik qolgan bola\"ga aylanadi."},
        {"year": "1991", "book": 1, "title": "Xogvartsga qabul",
         "desc": "Garri sehrgar ekanini bilib, Xogvartsga o'qishga boradi va Ron hamda Germiona bilan do'stlashadi."},
        {"year": "1992", "book": 2, "title": "Maxfiy Xona ochiladi",
         "desc": "Qadimiy Maxfiy Xona ochilib, o'quvchilarga xavf soladi; Garri baziliskni yengadi."},
        {"year": "1993", "book": 3, "title": "Sirius Blekning qochishi",
         "desc": "Azkabandan qochgan Sirius Garrining cho'qintirgan otasi ekani ma'lum bo'ladi."},
        {"year": "1994", "book": 4, "title": "Uch Afsungar Bellashuvi",
         "desc": "Garri bellashuvga tortiladi; Sedrik halok bo'ladi va Voldemort qaytadan tanaga kiradi."},
        {"year": "1995", "book": 5, "title": "Feniks Ordeni",
         "desc": "Voldemortga qarshi Orden tiklanadi; Vazirlikda jang bo'lib, Sirius halok bo'ladi."},
        {"year": "1996", "book": 6, "title": "Dambldorning halokati",
         "desc": "Garri Voldemortning o'tmishi va xorkrukslarni o'rganadi; Dambldor halok bo'ladi."},
        {"year": "1997", "book": 7, "title": "Xorkrukslar ovi",
         "desc": "Garri, Ron va Germiona maktabni tark etib, Voldemortning xorkrukslarini yo'q qilishga kirishadi."},
        {"year": "1998", "book": 7, "title": "Xogvarts jangi",
         "desc": "Buyuk jangda Voldemort mag'lub etiladi; sehrli dunyoga tinchlik qaytadi."},
        {"year": "2020", "book": 8, "title": "La'natlangan Bola",
         "desc": "Garrining o'g'li Albus va Skorpius Vaqt Aylantirgich bilan o'tmishga aralashib, xatarga yo'liqishadi."},
    ],
    "families": [
        {"name": "Potter oilasi", "book": 1,
         "note": "Sehrli dunyoning eng mashhur oilasi.",
         "levels": [["Jeyms Potter", "Lili Potter"],
                    ["Garri Potter", "Jinni Uizli"],
                    ["Jeyms S. Potter", "Albus S. Potter", "Lili L. Potter"]]},
        {"name": "Uizli oilasi", "book": 1,
         "note": "Katta, mehribon va sof qonli sehrgarlar oilasi.",
         "levels": [["Artur Uizli", "Moli Uizli"],
                    ["Bill", "Charli", "Persi", "Fred", "Jorj", "Ron", "Jinni"]]},
        {"name": "Malfoy oilasi", "book": 1,
         "note": "Kibrli va nufuzli sof qonli oila.",
         "levels": [["Lyusius Malfoy", "Narsissa Malfoy"],
                    ["Drako Malfoy", "Astoriya Greengrass"],
                    ["Skorpius Malfoy"]]},
        {"name": "Blek oilasi", "book": 3,
         "note": "Qadimiy va sirli sof qonli sulola.",
         "levels": [["Orion Blek", "Valburga Blek"],
                    ["Sirius Blek", "Regulus Blek"],
                    ["Narsissa", "Bellatrisa", "Andromeda (amakivachcha)"]]},
    ],
    # Interaktiv xaritalar (Marauder uslubi). x/y \u2014 foizlarda (0-100).
    # Har xarita o'z dekorativ SVG "art" ga ega; book \u2014 spoiler chegarasi.
    "map": {
        "maps": [
            {"id": "grounds", "name": "Hogvarts hududi", "art": "grounds", "book": 1,
             "locations": [
                _l("Buyuk Zal / Qal'a", 50, 30, 1, "Bosh bino", "Hogvarts qal'asining yuragi; darvozadan Buyuk Zalga kiriladi.", "xogvarts"),
                _l("Astronomiya minorasi", 40, 12, 1, "Eng baland minora", "Yulduzlarni kuzatish darslari o'tadigan qal'aning eng baland minorasi."),
                _l("Boyqushxona", 63, 15, 1, "Xat-xabar", "Maktab va o'quvchilarning boyqushlari yashaydigan minora."),
                _l("Kviddich maydoni", 16, 34, 1, "Sport", "Baland minorali stadion; supurgilardagi kviddich o'yinlari shu yerda."),
                _l("Issiqxonalar", 66, 34, 1, "Gerbologiya", "Sehrli o'simliklar yetishtiriladigan issiqxonalar; gerbologiya darslari joyi."),
                _l("Ichki hovli", 46, 40, 1, "Markaziy maydon", "Qal'aning ichki hovlisi va ko'priklari; tanaffusda o'quvchilar yig'iladi."),
                _l("Kaltaklovchi Tol", 30, 50, 2, "Xavfli daraxt", "Yaqinlashganni shoxlari bilan uradigan jangovar daraxt; ostida yashirin yo'l bor."),
                _l("Hagrid kulbasi", 26, 62, 1, "O'rmonboni uyi", "O'rmon chekkasidagi kulba; Hagridning uyi va sehrli mavjudotlar joyi.", "hagrid"),
                _l("Taqiqlangan O'rmon", 13, 72, 1, "Xavfli hudud", "O'quvchilarga taqiqlangan qorong'u o'rmon; kentavr va akromantulalar makoni.", "ormon"),
                _l("Qayiqxona", 66, 66, 1, "Ko'l bo'yi", "Birinchi kurs o'quvchilari qal'aga qayiqlarda kelib tushadigan bino."),
                _l("Qora Ko'l", 48, 84, 1, "Suv osti olami", "Qal'a yonidagi ulkan ko'l; suvparilar va ulkan kalmar makoni."),
             ],
             "figures": [
                _f("Garri", 47, 32, 1, "gryffindor"),
                _f("Hagrid", 27, 58, 1, ""),
                _f("Luna", 60, 30, 5, "kogtevran"),
             ]},
            {"id": "castle", "name": "Qal'a ichki qismi", "art": "castle", "book": 1,
             "locations": [
                _l("Direktor kabineti", 50, 14, 2, "Boshqaruv", "Aylanma zinapoya ortidagi kabinet; portretlar va Saralovchi Shlyapa shu yerda.", "dambldor"),
                _l("Gryffindor minorasi", 28, 22, 1, "Yotoqxona", "Semiz Xonim portreti ortidagi Gryffindor umumiy xonasi; iliq maskan.", "gryffindor"),
                _l("Kogtevran minorasi", 72, 22, 1, "Yotoqxona", "Kirish uchun topishmoq javobini talab qiluvchi minora.", "kogtevran"),
                _l("Talab Xonasi", 58, 32, 5, "Sirli xona", "Faqat chin muhtojga paydo bo'ladigan sehrli xona; har safar boshqacha.", ""),
                _l("Kutubxona", 68, 42, 1, "Bilim maskani", "Minglab sehrli kitoblar; Taqiqlangan bo'lim ham shu yerda.", "germiona"),
                _l("Kasalxona qanoti", 32, 40, 1, "Shifoxona", "Madam Pomfri boshqaradigan shifoxona.", ""),
                _l("Katta zinapoya", 50, 46, 1, "Harakatlanuvchi zinalar", "O'z holicha joyini o'zgartiradigan sirli zinapoyalar tarmog'i.", ""),
                _l("Yashirin yo'llar", 22, 54, 3, "Maxfiy o'tishlar", "Qal'adan Xogsmidga olib boruvchi yo'llar; Qaroqchilar xaritasida ko'rsatilgan.", "xarita"),
                _l("Puffenduy yerto'lasi", 38, 74, 1, "Yotoqxona", "Oshxona yaqinidagi qulay, o'simliklarga boy umumiy xona.", "puffenduy"),
                _l("Oshxona", 56, 74, 4, "Uy-elflar", "Buyuk Zal ostidagi ulkan oshxona; yuzlab uy-elflar ovqat tayyorlaydi.", "dobbi"),
                _l("Slizerin zindoni", 44, 86, 1, "Yer osti yotoqxonasi", "Qora ko'l ostidagi salqin zindondagi umumiy xona; yashil xira nur.", "slizerin"),
                _l("Maxfiy Xona", 62, 90, 2, "Yashirin xona", "Salazar Slizerin qurgan afsonaviy xona; hojatxona orqali kiriladi.", "maxfiyxona"),
             ],
             "figures": [
                _f("Garri", 30, 26, 1, "gryffindor"),
                _f("Ron", 34, 24, 1, "gryffindor"),
                _f("Germiona", 66, 44, 1, "gryffindor"),
                _f("Dambldor", 50, 18, 1, ""),
                _f("Snegg", 44, 82, 1, "slizerin"),
                _f("Drako", 48, 84, 1, "slizerin"),
             ]},
            {"id": "diagon", "name": "Diagon xiyoboni", "art": "diagon", "book": 1,
             "locations": [
                _l("Gringotts banki", 80, 26, 1, "Sehrgarlar banki", "Goblinlar boshqaradigan yer ostidagi eng xavfsiz bank.", "gringotts"),
                _l("Ollivander tayoqchalari", 18, 40, 1, "Tayoqcha do'koni", "Miloddan avvalgi 382-yildan beri sifatli sehrli tayoqchalar sotuvchi do'kon."),
                _l("Kitob do'koni", 40, 30, 1, "Darsliklar", "\"Flourish va Blotts\" \u2014 barcha sehrli kitoblar va darsliklar do'koni."),
                _l("Muzqaymoq do'koni", 52, 46, 1, "Shirinlik", "Florean Fortesk'ning mashhur sehrli muzqaymoqlari."),
                _l("Qozon do'koni", 30, 58, 1, "Anjomlar", "Har xil o'lchamdagi qozonlar va iksir anjomlariga to'la do'kon."),
                _l("Uizlilarning hazil do'koni", 62, 56, 6, "Hazil-mutoyiba", "Fred va Jorj ochgan mashhur hazil buyumlari do'koni."),
                _l("Qaltis Xiyobon", 68, 72, 2, "Qorong'u ko'cha", "Qora sehr buyumlari sotiladigan xatarli yon ko'cha (Knockturn)."),
             ]},
            {"id": "hogsmeade", "name": "Xogsmid", "art": "hogsmeade", "book": 3,
             "locations": [
                _l("Uch Supurgi", 46, 42, 3, "Taverna", "Madam Rosmerta yurituvchi issiq taverna; mashhur slivan sharbati shu yerda."),
                _l("Asal Osmoni", 28, 34, 3, "Shirinliklar", "\"Honeydukes\" \u2014 turli sehrli shirinliklarga to'la do'kon."),
                _l("Zonko hazil do'koni", 62, 36, 3, "Hazil buyumlari", "O'quvchilarning sevimli hazil-mutoyiba buyumlari do'koni."),
                _l("Cho'chqa Boshi", 18, 56, 3, "Sirli taverna", "Xira va sirli taverna; maxfiy uchrashuvlar joyi."),
                _l("Boyqush pochtasi", 70, 56, 3, "Pochta", "Yuzlab boyqushlar orqali xat va posilka jo'natiladigan pochta."),
                _l("Qichqiruvchi Kulba", 50, 74, 3, "Arvohli bino", "Britaniyaning eng arvohli sanalgan binosi; aslida sir yashiradi."),
             ]},
        ],
    },
}

# ----------------------------------------------------------------------------
# Personajlarning to'liq biografiyasi. Har maydon [label, qiymat, book]:
# `book` > o'quvchi darajasidan bo'lsa, maydon "keyinroq ochiladi" holatida
# yashiriladi (maydon-darajasida spoiler himoyasi). facts: [book, matn].
# ----------------------------------------------------------------------------
CHARBIO = {
    "garri": {"rows": [
        ["To'liq ism", "Garri Jeyms Potter", 1],
        ["Tug'ilgan", "31-iyul, 1980-yil", 1],
        ["Qon maqomi", "Yarim qonli", 1],
        ["Fakultet", "Gryffindor", 1],
        ["Tayoqcha", "Chsetan (holli), 11 dyuym, feniks pati", 1],
        ["Patronus", "Bug'u (kiyik)", 3],
        ["Oilasi", "Jeyms va Lili Potter (ota-ona)", 1],
        ["Kasbi", "O'quvchi; keyinchalik auror", 1],
    ], "facts": [
        [1, "Bir yoshida Voldemort hujumidan omon qoldi; peshonasida chaqmoq izi qoldi."],
        [1, "O'n bir yoshida sehrgar ekanini bilib, Xogvartsga o'qishga bordi."],
        [1, "Ron va Germiona bilan Falsafiy toshni Voldemortdan asrab qoldi."],
        [3, "Dementorlardan himoya uchun kuchli Patronus sehrini o'rgandi."],
        [4, "Uch Afsungar Bellashuviga majburan tortildi."],
        [5, "Do'stlari bilan Dumbledor Armiyasini tuzdi."],
    ]},
    "ron": {"rows": [
        ["To'liq ism", "Ronald Bilius Uizli", 1],
        ["Tug'ilgan", "1-mart, 1980-yil", 1],
        ["Qon maqomi", "Sof qonli", 1],
        ["Fakultet", "Gryffindor", 1],
        ["Patronus", "Jek-rassel terer (it)", 5],
        ["Oilasi", "Uizlilar oilasi (kenja o'g'il)", 1],
        ["Kasbi", "O'quvchi", 1],
    ], "facts": [
        [1, "Xogvarts poyezdida Garri bilan tanishib, eng yaqin do'stiga aylandi."],
        [1, "Ulkan sehrli shaxmat o'yinida o'zini qurbon qildi."],
        [2, "Buzuq uchar mashinada Xogvartsga bordi."],
    ]},
    "germiona": {"rows": [
        ["To'liq ism", "Germiona Jin Greynjer", 1],
        ["Tug'ilgan", "19-sentyabr, 1979-yil", 1],
        ["Qon maqomi", "Maripat (Muggle) oilasidan", 1],
        ["Fakultet", "Gryffindor", 1],
        ["Tayoqcha", "Uzum, ajdaho yurak tomiri", 1],
        ["Patronus", "Suvsar", 5],
        ["Kasbi", "O'quvchi; keyinchalik Vazirlikda", 1],
    ], "facts": [
        [1, "O'tkir aqli bilan uchlikni ko'p bor qutqardi."],
        [3, "Vaqt Aylantirgich yordamida bir vaqtda ko'proq dars oldi."],
    ]},
    "dambldor": {"rows": [
        ["To'liq ism", "Albus Persival Vulfrik Brayan Dambldor", 1],
        ["Tug'ilgan", "1881-yil", 1],
        ["Qon maqomi", "Yarim qonli", 1],
        ["Fakultet", "Gryffindor", 1],
        ["Patronus", "Feniks", 5],
        ["Kasbi", "Xogvarts bosh direktori", 1],
        ["Tayoqcha", "(7-kitobda oydinlashadi)", 7],
    ], "facts": [
        [1, "Chaqaloq Garrini Dursllar eshigi oldiga qoldirdi."],
        [2, "Feniksi orqali Garriga Maxfiy Xonada yordam yubordi."],
        [5, "Voldemortga qarshi Feniks Ordenini boshqardi."],
        [6, "Voldemortning o'tmishi va xorkrukslar sirini Garriga ocha boshladi."],
    ]},
    "hagrid": {"rows": [
        ["To'liq ism", "Rubeus Hagrid", 1],
        ["Tug'ilgan", "6-dekabr, 1928-yil", 1],
        ["Qon maqomi", "Yarim-gigant", 1],
        ["Fakultet", "Gryffindor (o'qigan)", 1],
        ["Kasbi", "O'rmonboni; keyin ustoz", 1],
    ], "facts": [
        [1, "Garriga sehrgar ekanini aytib, uni Xogvartsga olib keldi."],
        [1, "Yashirincha ajdaho tuxumini boqishga urindi."],
        [3, "Sehrli mavjudotlarni parvarishlash ustozi bo'ldi."],
    ]},
    "snegg": {"rows": [
        ["To'liq ism", "Severus Snegg", 1],
        ["Tug'ilgan", "9-yanvar, 1960-yil", 1],
        ["Qon maqomi", "Yarim qonli", 6],
        ["Fakultet", "Slizerin", 1],
        ["Kasbi", "Iksirlar ustozi; Slizerin dekani", 1],
        ["Patronus", "Kiyik (bug'u)", 7],
    ], "facts": [
        [1, "Garriga nisbatan sovuq va qattiqqo'l munosabatda bo'ldi."],
        [6, "O'zini 'Chala Zot Shahzoda' deb atagani ma'lum bo'ldi."],
        [7, "Uning haqiqiy sadoqati va Liliga bo'lgan muhabbati ochildi."],
    ]},
    "makgonagal": {"rows": [
        ["To'liq ism", "Minerva Makgonagal", 1],
        ["Tug'ilgan", "4-oktabr, 1935-yil", 1],
        ["Qon maqomi", "Yarim qonli", 1],
        ["Fakultet", "Gryffindor", 1],
        ["Kasbi", "Transfiguratsiya ustozi; Gryffindor dekani", 1],
        ["Alohida", "Anigamag \u2014 mushukka aylanadi", 1],
    ], "facts": [
        [1, "Yangi o'quvchilarni saralash marosimida boshchilik qildi."],
    ]},
    "voldemort": {"rows": [
        ["To'liq ism", "Tom Marvolo Ridl", 2],
        ["Tug'ilgan", "31-dekabr, 1926-yil", 6],
        ["Qon maqomi", "Yarim qonli", 6],
        ["Fakultet", "Slizerin", 2],
        ["Tayoqcha", "Zarnab (yew), 13.5 dyuym, feniks pati", 4],
        ["Kasbi", "Qora sehrgar", 1],
    ], "facts": [
        [1, "Garrining ota-onasini o'ldirgan, so'ng sirli ravishda yo'qolgan kuch."],
        [2, "Yosh Tom Ridl xotirasi kundalik orqali qaytishga urindi."],
        [4, "To'liq tanaga qaytib, kuch-qudratini tikladi."],
        [6, "O'tmishi va xorkrukslari asta-sekin ochila boshladi."],
    ]},
    "draco": {"rows": [
        ["To'liq ism", "Drako Lyusius Malfoy", 1],
        ["Tug'ilgan", "5-iyun, 1980-yil", 1],
        ["Qon maqomi", "Sof qonli", 1],
        ["Fakultet", "Slizerin", 1],
        ["Tayoqcha", "Do'lana, 10 dyuym, edinrog tuki", 1],
        ["Oilasi", "Lyusius va Narsissa Malfoy", 1],
    ], "facts": [
        [1, "Garriga do'stlik taklif qildi; rad etilgach, raqibiga aylandi."],
        [6, "Voldemortdan og'ir va sirli vazifa oldi."],
    ]},
    "nevill": {"rows": [
        ["To'liq ism", "Nevill Longbottom", 1],
        ["Tug'ilgan", "30-iyul, 1980-yil", 1],
        ["Qon maqomi", "Sof qonli", 1],
        ["Fakultet", "Gryffindor", 1],
        ["Kasbi", "O'quvchi; keyin Gerbologiya ustozi", 1],
    ], "facts": [
        [1, "Dastlab uquvsiz ko'rindi, ammo jasoratini namoyon qildi."],
        [5, "Voldemortga qarshi kurashga qo'shildi."],
    ]},
    "jinni": {"rows": [
        ["To'liq ism", "Jinevra (Jinni) Molli Uizli", 2],
        ["Tug'ilgan", "11-avgust, 1981-yil", 2],
        ["Qon maqomi", "Sof qonli", 2],
        ["Fakultet", "Gryffindor", 2],
        ["Oilasi", "Uizlilar oilasi (yagona qiz)", 2],
    ], "facts": [
        [2, "Ridl kundaligining sirli ta'siriga tushib qoldi."],
    ]},
    "dobbi": {"rows": [
        ["To'liq ism", "Dobbi", 2],
        ["Qon maqomi", "Uy-elfi", 2],
        ["Kasbi", "(dastlab) Malfoylar xizmatkori", 2],
    ], "facts": [
        [2, "Garrini yaqinlashayotgan xavfdan ogohlantirishga urindi."],
        [2, "Garri hiyla ishlatib, uni ozodlikka chiqardi."],
    ]},
    "sirius": {"rows": [
        ["To'liq ism", "Sirius Blek", 3],
        ["Tug'ilgan", "1959-yil", 3],
        ["Qon maqomi", "Sof qonli", 3],
        ["Fakultet", "Gryffindor", 3],
        ["Alohida", "Anigamag \u2014 qora itga aylanadi", 3],
        ["Oilasi", "Garrining cho'qintirgan otasi", 3],
    ], "facts": [
        [3, "Azkabandan qochib, o'zining begunohligini isbotladi."],
    ]},
    "lyupin": {"rows": [
        ["To'liq ism", "Remus Jon Lyupin", 3],
        ["Tug'ilgan", "10-mart, 1960-yil", 3],
        ["Qon maqomi", "Yarim qonli", 3],
        ["Fakultet", "Gryffindor", 3],
        ["Kasbi", "Qora kuchlardan himoya ustozi", 3],
        ["Alohida", "Bo'ri-odam", 3],
    ], "facts": [
        [3, "Garriga Patronus sehrini sabr bilan o'rgatdi."],
    ]},
    "petigryu": {"rows": [
        ["To'liq ism", "Piter Petigryu", 3],
        ["Qon maqomi", "Sof qonli", 3],
        ["Fakultet", "Gryffindor", 3],
        ["Alohida", "Anigamag \u2014 kalamush (Korason)", 3],
    ], "facts": [
        [3, "O'n ikki yil kalamush qiyofasida yashiringani fosh bo'ldi."],
    ]},
    "sedrik": {"rows": [
        ["To'liq ism", "Sedrik Diggori", 4],
        ["Qon maqomi", "Sof qonli", 4],
        ["Fakultet", "Puffenduy", 4],
        ["Kasbi", "O'quvchi; Xogvarts chempioni", 4],
    ], "facts": [
        [4, "Uch Afsungar Bellashuvida Xogvartsni sharaf bilan ifodaladi."],
    ]},
    "muudi": {"rows": [
        ["To'liq ism", "Alastor Muudi", 4],
        ["Qon maqomi", "Sof qonli", 4],
        ["Kasbi", "Auror (sehrgar-ovchi)", 4],
        ["Alohida", "Sehrli ko'z; shiori \u2014 \"Doimo hushyor!\"", 4],
    ], "facts": [
        [4, "Qora kuchlardan himoya darsini o'tdi."],
    ]},
    "umbrij": {"rows": [
        ["To'liq ism", "Doloris Jeyn Umbrij", 5],
        ["Qon maqomi", "Yarim qonli", 5],
        ["Fakultet", "Slizerin (o'qigan)", 5],
        ["Kasbi", "Vazirlik amaldori; Bosh inkvizitor", 5],
    ], "facts": [
        [5, "Xogvartsda zolim va qattiq tartib o'rnatdi."],
    ]},
    "bellatrisa": {"rows": [
        ["To'liq ism", "Bellatrisa Lestranj (Blek)", 5],
        ["Qon maqomi", "Sof qonli", 5],
        ["Fakultet", "Slizerin", 5],
        ["Tayoqcha", "Yong'oq, ajdaho yurak tomiri", 5],
        ["Kasbi", "O'lim Yeguvchi", 5],
    ], "facts": [
        [5, "Vazirlikdagi jangda faol qatnashdi."],
    ]},
    "luna": {"rows": [
        ["To'liq ism", "Luna Lavgud", 5],
        ["Tug'ilgan", "13-fevral, 1981-yil", 5],
        ["Qon maqomi", "Sof qonli", 5],
        ["Fakultet", "Kogtevran", 5],
    ], "facts": [
        [5, "Garrining eng samimiy va sodiq do'stlaridan biriga aylandi."],
    ]},
    "slughorn": {"rows": [
        ["To'liq ism", "Horas Slughorn", 6],
        ["Qon maqomi", "Sof qonli", 6],
        ["Fakultet", "Slizerin", 6],
        ["Kasbi", "Iksirlar ustozi", 6],
    ], "facts": [
        [6, "Voldemortning o'tmishiga oid muhim sirni saqlab kelardi."],
    ]},
    "fred_jorj": {"rows": [
        ["To'liq ism", "Fred va Jorj Uizli", 1],
        ["Tug'ilgan", "1-aprel, 1978-yil", 1],
        ["Qon maqomi", "Sof qonli", 1],
        ["Fakultet", "Gryffindor", 1],
        ["Kasbi", "Hazil-mutoyiba do'koni asoschilari", 1],
    ], "facts": [
        [1, "Hazillari bilan Garrini kuldirib, unga g'amxo'rlik qilishdi."],
        [3, "Qaroqchilar xaritasini Garriga sovg'a qilishdi."],
    ]},
    "moli": {"rows": [
        ["To'liq ism", "Molli Uizli (Prevett)", 1],
        ["Qon maqomi", "Sof qonli", 1],
        ["Fakultet", "Gryffindor (o'qigan)", 1],
        ["Kasbi", "Uy bekasi; Feniks Ordeni a'zosi", 1],
    ], "facts": [
        [1, "Platformada Garriga yo'l ko'rsatdi."],
        [2, "Garrini o'z uyida iliq kutib oldi."],
    ]},
    "lily_james": {"rows": [
        ["To'liq ism", "Jeyms Potter va Lili Potter (Evans)", 1],
        ["Qon maqomi", "Jeyms \u2014 sof qonli; Lili \u2014 Muggle oilasidan", 1],
        ["Fakultet", "Gryffindor", 1],
        ["Kasbi", "Feniks Ordeni a'zolari", 1],
    ], "facts": [
        [1, "Garrini himoya qilib halok bo'lishdi; Lilining muhabbati Garrini asrab qoldi."],
    ]},
}
for _c in WORLD["entries"]:
    if _c["id"] in CHARBIO:
        _c["rows"] = CHARBIO[_c["id"]]["rows"]
        _c["facts"] = CHARBIO[_c["id"]]["facts"]

# ----------------------------------------------------------------------------
# Assemble readers
# ----------------------------------------------------------------------------
def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def patch_engine(app_js, part2_js):
    app_js = app_js.replace('var KEY = "gp_reader_v2";',
                            'var KEY = (window.BOOK && window.BOOK.key) || "gp_reader_v2";')
    part2_js = part2_js.replace('var GLOSSARY = {',
                                'var GLOSSARY = (window.BOOK && window.BOOK.glossary) || {', 1)
    return app_js, part2_js

def build_chapters(book):
    """Return (chapters_html, n_chapters, n_words) for one book.
    This is the only per-book unique payload now — the reader engine is shared."""
    path = os.path.join(BOOKDIR, book["folder"], "matn.txt")
    raw = load_lines(path)
    lines = clean_lines(raw, book.get("cut_at"))
    chapters = split_chapters(lines)
    parts = []
    total_words = 0
    for i, (title, body) in enumerate(chapters):
        paras = reflow(body)
        total_words += sum(len(p.split()) for p in paras if p != "@@SEP@@")
        parts.append(chapter_html(i, title, paras))
    return "\n".join(parts), len(chapters), total_words


def build_shell(head, chrome_top, chrome_bot, app_js, part2_js):
    """Build the ONE shared reader template (~90 KB) stored a single time.

    Per-book values are placeholders that openBook() substitutes at runtime:
      @@TITLE@@  @@SUB@@  @@ACCENT@@  @@BOOKCFG@@  @@CHAPTERS@@
    This removes the previous 8x duplication of the engine (CSS+JS)."""
    h = head.replace("<title>GARRI POTTER VA LA&#x27;NATLANGAN BOLA</title>",
                     "<title>Garri Potter \u2014 @@TITLE@@</title>")
    h = h.replace('  --accent: #7b1113;', '  --accent: @@ACCENT@@;')
    h = h.replace('href="icons/icon.svg"', 'href="%s"' % FAVICON)
    # chrome_top: topbar title + cover
    ct = chrome_top.replace(
        '<span class="title" id="cur-chapter-title">GARRI POTTER VA LA&#x27;NATLANGAN BOLA</span>',
        '<span class="title" id="cur-chapter-title">@@TITLE@@</span>')
    ct = ct.replace('<h1 class="big">GARRI POTTER VA LA&#x27;NATLANGAN BOLA</h1>',
                    '<h1 class="big">@@TITLE@@</h1>')
    ct = ct.replace('<div class="sub">Roman<br>J.K. Rouling, Jon Tiffani, Jek Torn pyesasiga asoslangan</div>',
                    '<div class="sub">@@SUB@@<br>J.K. Rouling</div>')
    # back-to-library button before the TOC button.
    ct = ct.replace(
        '<button class="iconbtn" id="btn-toc" title="Mundarija (C)" aria-label="Mundarija">',
        '<a class="iconbtn" href="index.html" title="Kutubxona" aria-label="Kutubxona" '
        'style="text-decoration:none" '
        "onclick=\"if(window.parent!==window){window.parent.postMessage('gp-back','*');return false;}\">"
        '<svg viewBox="0 0 24 24"><path d="M3 7v13h18V7M3 7l3-4h12l3 4M3 7h18"/>'
        '<line x1="12" y1="3" x2="12" y2="20"/></svg></a>'
        '<button class="iconbtn" id="btn-toc" title="Mundarija (C)" aria-label="Mundarija">')

    cfg_script = "<script>window.BOOK=@@BOOKCFG@@;</script>\n"
    final = (h.rstrip() + "\n" + ct.rstrip() + "\n@@CHAPTERS@@\n"
             + chrome_bot.rstrip() + "\n" + cfg_script
             + "<script>\n" + app_js.rstrip() + "\n" + part2_js.rstrip()
             + "\n</script>\n</body>\n</html>\n")
    return final

def build_single(summary, shell, chapters_map):
    # Single self-contained file (per the spec's "platforma bitta HTML fayl").
    # The reader ENGINE (CSS + ~60 KB JS) is stored ONCE in #reader-shell.
    # Each book contributes only its chapter HTML in #bookdata-N. openBook()
    # stitches shell + chapters together (via the viewer iframe's srcdoc) only
    # when a book is actually opened — so nothing heavy parses on startup and
    # the engine is no longer duplicated 8x.
    books_json = json.dumps(summary, ensure_ascii=False)
    gloss_json = json.dumps(GLOSSARY, ensure_ascii=False)
    world_json = json.dumps(WORLD, ensure_ascii=False)
    # Foydalanuvchi tasdig'i bilan: Maps/ dagi illyustratsiya xaritasi
    # ko'rinadigan atribut (kredit) bilan alohida ko'rinish sifatida qo'shiladi.
    import base64
    _illus = os.path.join(ROOT, "Maps",
        "old-but-useful-map-of-hogwarts-v0-mthRYJCEB3-7yvurS1T1oY0EgS-nzG1d4ySf1Vg-KbY.jpg")
    if os.path.exists(_illus):
        try:
            _b = open(_illus, "rb").read()
            _uri = "data:image/jpeg;base64," + base64.b64encode(_b).decode()
            _wm = json.loads(world_json)
            _wm["map"]["maps"].append({
                "id": "illustration", "name": "Illyustratsiya", "art": "", "img": _uri,
                "credit": "Xarita: Gamma-ray-burst \u00b7 DeviantArt",
                "book": 1, "locations": [], "figures": []})
            world_json = json.dumps(_wm, ensure_ascii=False)
        except Exception:
            pass
    _grounds = (
        '<path d="M1 5 L30 5 L30 33 Q22 37 15 34 Q8 38 1 33 Z" fill="#4f6f3f"/>'
        '<path d="M1 56 L25 56 Q28 66 21 76 Q11 82 2 76 Z" fill="#4f6f3f"/>'
        '<path d="M5 12 l2 -4 l2 4 z M10 11 l2 -4 l2 4 z M15 13 l2 -4 l2 4 z M20 11 l2 -4 l2 4 z M25 13 l2 -4 l2 4 z M8 19 l2 -4 l2 4 z M18 20 l2 -4 l2 4 z"/>'
        '<path d="M5 61 l2 -4 l2 4 z M10 63 l2 -4 l2 4 z M15 61 l2 -4 l2 4 z M8 68 l2 -4 l2 4 z M18 66 l2 -4 l2 4 z"/>'
        '<path d="M30 72 Q48 66 70 71 Q81 74 80 84 Q77 95 58 96 Q39 97 31 91 Q25 83 30 72 Z" fill="#3f6b86"/>'
        '<path d="M35 80 q6 -2 12 0 M42 86 q6 -2 12 0" stroke-width="0.3" fill="none"/>'
        '<path d="M33 44 Q45 49 58 46 L58 42 L33 42 Z" fill="#7a6a4a"/>'
        '<path d="M40 42 L40 26 L44 23 L52 23 L56 26 L56 42 Z" fill="#efe7d0"/>'
        '<path d="M40 30 L56 30 M48 23 L48 42" stroke-width="0.3"/>'
        '<path d="M40 24 l0 2 M44 22 l0 2 M52 22 l0 2 M56 24 l0 2"/>'
        '<path d="M38 42 L38 15 L43 15 L43 42 Z" fill="#efe7d0"/>'
        '<path d="M37.5 15 L40.5 7 L43.5 15 Z" fill="currentColor"/>'
        '<path d="M40.5 7 L40.5 3.5 L43 4.5 L40.5 5.5"/>'
        '<circle cx="50" cy="36" r="4" fill="#efe7d0"/><circle cx="50" cy="36" r="1"/>'
        '<path d="M50 30 L47.5 26 L50 22 L52.5 26 Z" fill="currentColor"/>'
        '<path d="M34 42 L34 31 L37 31 L37 42 Z" fill="#efe7d0"/><path d="M33.3 31 L35.5 27 L37.7 31 Z" fill="currentColor"/>'
        '<path d="M58 42 L58 30 L61 30 L61 42 Z" fill="#efe7d0"/><path d="M57.3 30 L59.5 26 L61.7 30 Z" fill="currentColor"/>'
        '<path d="M61 42 L72 42 L72 35 L66.5 31 L61 35 Z" fill="#efe7d0"/>'
        '<path d="M61 35 L66.5 31 L72 35" fill="none"/>'
        '<path d="M72 43 L88 43"/><path d="M73 43 q2 -4 4 0 M77 43 q2 -4 4 0 M81 43 q2 -4 4 0 M85 43 q2 -4 4 0" stroke-width="0.3" fill="none"/>'
        '<path d="M88 39 L92 39 L92 46 L88 46 Z" fill="#efe7d0"/>'
        '<path d="M62 36 a3 2.5 0 0 1 6 0 Z" fill="#cfe0d0"/><path d="M68 35 a2.5 2 0 0 1 5 0 Z" fill="#cfe0d0"/>'
        '<path d="M61 20 L61 13 L65 13 L65 20 Z" fill="#efe7d0"/><path d="M60.3 13 L63 9 L65.7 13 Z" fill="currentColor"/>'
        '<ellipse cx="16" cy="35" rx="8" ry="4" fill="none"/>'
        '<path d="M11 34 L11 29 M16 34 L16 28 M21 34 L21 29"/>'
        '<circle cx="11" cy="28.5" r="0.9"/><circle cx="16" cy="27.5" r="0.9"/><circle cx="21" cy="28.5" r="0.9"/>'
        '<path d="M30 54 L30 48 M30 48 q-4 -2 -6 -5 M30 48 q4 -2 6 -5 M30 49 q-6 0 -9 2 M30 49 q6 0 9 2 M30 48 q-2 -5 -2 -8 M30 48 q2 -5 2 -8"/>'
        '<path d="M23 64 a3 3 0 0 1 6 0 Z" fill="#e7d8b8"/><path d="M22.4 62 L26 58 L29.6 62 Z" fill="currentColor"/>'
        '<path d="M28 59 L28 55" fill="none"/>'
        '<circle cx="21" cy="66" r="0.5"/><circle cx="23" cy="67" r="0.5"/><circle cx="25" cy="67.5" r="0.5"/>'
        '<path d="M63 66 L69 66 L67.5 63 L64.5 63 Z" fill="#e7d8b8"/>'
        '<path d="M50 97 Q48 78 46 60 Q44 50 48 44" stroke-width="0.5" fill="none"/>'
        '<path d="M42 44 Q34 54 27 60" stroke-width="0.4" fill="none"/>'
        '<path d="M34 40 Q25 38 19 36" stroke-width="0.4" fill="none"/>'
    )
    _castle = (
        '<path d="M12 92 L12 40 L24 40 L24 16 L32 16 L32 40 L44 40 L44 26 L56 26 L56 12 L60 12 L60 40 L70 40 L70 16 L78 16 L78 40 L88 40 L88 92 Z" fill="#efe7d0"/>'
        '<path d="M23 16 L28 8 L33 16 Z" fill="currentColor"/>'
        '<path d="M55 12 L58.5 3 L62 12 Z" fill="currentColor"/>'
        '<path d="M69 16 L74 8 L79 16 Z" fill="currentColor"/>'
        '<path d="M58.5 3 L58.5 0.5 L61 1.5 L58.5 2.5" fill="none"/>'
        '<path d="M12 52 L88 52 M12 64 L88 64 M12 76 L88 76" stroke-width="0.3"/>'
        '<path d="M12 76 L88 76 L88 92 L12 92 Z" fill="#5b4636" opacity="0.45"/>'
        '<path d="M44 46 L52 50 L44 54 L52 58 L44 62" fill="none" stroke-width="0.5"/>'
        '<path d="M27 30 l0 5 M29 30 l0 5 M47 34 l0 5 M49 34 l0 5 M72 30 l0 5 M74 30 l0 5" stroke-width="0.3"/>'
        '<path d="M17 56 l0 4 M19 56 l0 4 M66 56 l0 4 M68 56 l0 4" stroke-width="0.3"/>'
        '<path d="M12 54 L5 57"/>'
        '<path d="M60 78 Q64 85 62 90" fill="none"/><circle cx="62" cy="90" r="2" fill="none"/>'
    )
    _diagon = (
        '<path d="M6 66 Q30 58 48 46 Q64 36 84 26" stroke-width="1.2"/>'
        '<path d="M12 72 Q34 64 52 52 Q68 42 90 32" stroke-width="1.2"/>'
        '<path d="M16 66 l3 -2 M26 61 l3 -2 M36 55 l3 -2 M46 48 l3 -2 M56 42 l3 -2 M68 35 l3 -2" stroke-width="0.3"/>'
        '<path d="M12 46 L12 36 L22 34 L22 44 Z" fill="#efe7d0"/><path d="M12 36 L17 32 L22 34" fill="none"/>'
        '<path d="M34 36 L34 26 L46 24 L46 34 Z" fill="#e3d3b0"/><path d="M34 26 L40 22 L46 24" fill="none"/>'
        '<path d="M46 50 L46 42 L56 40 L56 48 Z" fill="#efe7d0"/><path d="M46 42 L51 38 L56 40" fill="none"/>'
        '<path d="M24 62 L24 54 L34 52 L34 60 Z" fill="#e3d3b0"/><path d="M24 54 L29 50 L34 52" fill="none"/>'
        '<path d="M56 60 L56 50 L66 48 L66 58 Z" fill="#efe7d0"/><path d="M56 50 L61 46 L66 48" fill="none"/>'
        '<path d="M74 30 L74 18 L90 18 L90 30 Z" fill="#f2eeda"/><path d="M77 30 L77 20 M81 30 L81 20 M85 30 L85 20 M89 30 L89 20" stroke-width="0.3"/><path d="M73 18 L82 12 L91 18 Z" fill="currentColor"/>'
        '<path d="M62 66 Q68 72 70 78" stroke-width="0.8"/><path d="M64 68 L64 76 L72 76 L72 68 Z" fill="#4a3a30"/>'
    )
    _hogsmeade = (
        '<path d="M0 30 L14 12 L26 26 L40 8 L54 24 L70 10 L86 26 L100 14 L100 34 L0 34 Z" fill="#d8d2c0"/>'
        '<path d="M9 21 l5 -4 l5 5 M35 15 l5 -4 l5 5 M65 15 l5 -4 l5 5" fill="#f7f4ea"/>'
        '<path d="M6 64 Q40 56 94 62" stroke-width="1"/>'
        '<path d="M24 44 L24 36 L30 30 L36 36 L36 44 Z" fill="#efe7d0"/><path d="M23 37 L30 29 L37 37 Z" fill="#f7f4ea"/>'
        '<path d="M40 50 L40 42 L46 36 L52 42 L52 50 Z" fill="#efe7d0"/><path d="M39 43 L46 35 L53 43 Z" fill="#f7f4ea"/>'
        '<path d="M56 44 L56 36 L62 30 L68 36 L68 44 Z" fill="#efe7d0"/><path d="M55 37 L62 29 L69 37 Z" fill="#f7f4ea"/>'
        '<path d="M14 62 L14 54 L20 49 L26 54 L26 62 Z" fill="#e7d8b8"/><path d="M13 55 L20 48 L27 55 Z" fill="#f7f4ea"/>'
        '<path d="M64 62 L64 54 L70 49 L76 54 L76 62 Z" fill="#efe7d0"/><path d="M63 55 L70 48 L77 55 Z" fill="#f7f4ea"/>'
        '<path d="M44 78 L44 70 L50 64 L56 70 L56 78 Z" fill="#d8ccb4"/><path d="M43 71 L50 63 L57 71 Z" fill="none"/><path d="M48 78 L48 74 L52 74 L52 78" fill="none"/>'
        '<circle cx="18" cy="42" r="0.5"/><circle cx="34" cy="50" r="0.5"/><circle cx="52" cy="56" r="0.5"/><circle cx="70" cy="46" r="0.5"/><circle cx="82" cy="52" r="0.5"/><circle cx="26" cy="58" r="0.5"/><circle cx="60" cy="62" r="0.5"/><circle cx="12" cy="48" r="0.5"/><circle cx="46" cy="58" r="0.5"/>'
    )
    def _art(paths):
        return ('<svg class="map-svg" viewBox="0 0 100 100" preserveAspectRatio="none" fill="none" '
                'stroke="currentColor" stroke-width="0.4" stroke-linejoin="round" stroke-linecap="round" '
                'aria-hidden="true"><g class="ink">' + paths + '</g></svg>')
    maparts = {"grounds": _art(_grounds), "castle": _art(_castle),
               "diagon": _art(_diagon), "hogsmeade": _art(_hogsmeade)}
    mapdeco = (
        '<svg class="map-compass" viewBox="0 0 40 44" aria-hidden="true">'
        '<circle cx="20" cy="24" r="14" fill="none" stroke="currentColor" stroke-width="0.9"/>'
        '<path d="M20 10 L23 24 L20 38 L17 24 Z" fill="currentColor"/>'
        '<path d="M6 24 L20 21 L34 24 L20 27 Z" fill="none" stroke="currentColor" stroke-width="0.7"/>'
        '<text x="20" y="7" text-anchor="middle" font-size="6" fill="currentColor" '
        'font-family="Georgia,serif">N</text></svg>'
        '<span class="map-corner tl"></span><span class="map-corner tr"></span>'
        '<span class="map-corner bl"></span><span class="map-corner br"></span>'
    )
    # --- Saralash Qalpoqchasi (Sorting Hat) data, injected as JSON ---
    houses = {
        "gryffindor": {"name": "Gryffindor", "tag": "Jasorat, mardlik va olijanoblik",
                       "c1": "#7b1113", "c2": "#d4af37",
                       "desc": "Gryffindor jasur yuraklilarni qadrlaydi. Sen qiyinchilikdan "
                               "qo'rqmaysan, haqiqat uchun kurashasan va do'stlaring uchun "
                               "o'zingni ayamaysan."},
        "slytherin": {"name": "Slizerin", "tag": "Topqirlik, iroda va maqsadga intilish",
                      "c1": "#1a472a", "c2": "#a7b0b3",
                      "desc": "Slizerin maqsadi aniq, zukko va qat'iyatli sehrgarlarni "
                              "tanlaydi. Sen o'z yo'lingni bilasan va unga ishonch bilan "
                              "boryapsan."},
        "hufflepuff": {"name": "Puffenduy", "tag": "Sadoqat, halollik va mehnatsevarlik",
                       "c1": "#d3a625", "c2": "#372e29",
                       "desc": "Puffenduy mehnatkash, sodiq va adolatli qalblarni qadrlaydi. "
                               "Sen sabrli, samimiy va ishonchli hamrohsan."},
        "ravenclaw": {"name": "Kogtevran", "tag": "Donishmandlik, zukkolik va izlanish",
                      "c1": "#0e1a40", "c2": "#946b2d",
                      "desc": "Kogtevran bilim va ijodni sevuvchilarni tanlaydi. Sening "
                              "qiziquvchanliging va o'tkir aqling seni boshqalardan ajratib "
                              "turadi."},
    }
    quiz = [
        {"q": "Kechki Hogvarts koridorida sirli ovoz eshitding. Nima qilasan?",
         "a": [{"t": "Darhol borib o'zim tekshiraman.", "h": "gryffindor"},
               {"t": "Avval kuzataman va mantiqan o'ylab ko'raman.", "h": "ravenclaw"},
               {"t": "Do'stlarimni chaqirib, birga boramiz.", "h": "hufflepuff"},
               {"t": "Menga foyda keltirsa, ehtiyotkorlik bilan yondashaman.", "h": "slytherin"}]},
        {"q": "Sehrgarlikda eng qadrlaydigan fazilating qaysi?",
         "a": [{"t": "Jasorat va mardlik.", "h": "gryffindor"},
               {"t": "Aql, bilim va donishmandlik.", "h": "ravenclaw"},
               {"t": "Halollik va sadoqat.", "h": "hufflepuff"},
               {"t": "Topqirlik va maqsadga erishish.", "h": "slytherin"}]},
        {"q": "Qaysi dars senga eng yoqadi?",
         "a": [{"t": "Qorong'u kuchlardan himoya.", "h": "gryffindor"},
               {"t": "Sehrlar va afsunlar.", "h": "ravenclaw"},
               {"t": "Gerbologiya.", "h": "hufflepuff"},
               {"t": "Iksirlar tayyorlash.", "h": "slytherin"}]},
        {"q": "Sehrli tayoqchang nima uchun xizmat qilsin?",
         "a": [{"t": "Adolat uchun kurashishga.", "h": "gryffindor"},
               {"t": "Sirlarni ochish va o'rganishga.", "h": "ravenclaw"},
               {"t": "Yaqinlarimni himoya qilishga.", "h": "hufflepuff"},
               {"t": "O'z orzularimga erishishga.", "h": "slytherin"}]},
    ]
    ui_text = {
        "sortTitle": "Saralash Qalpoqchasi",
        "sortIntro": "Bir necha savolga javob ber \u2014 Saralash Qalpoqchasi seni Hogvartsning "
                     "qaysi fakultetiga yo'naltirishini aytib beradi.",
        "begin": "Boshlash", "close": "Yopish", "retake": "Qayta saralash",
        "your": "Sening fakulteting", "q": "Savol", "result": "Saralash natijasi",
        "tryHat": "Saralash Qalpoqchasini sina",
    }
    houses_json = json.dumps(houses, ensure_ascii=False)
    quiz_json = json.dumps(quiz, ensure_ascii=False)
    uitext_json = json.dumps(ui_text, ensure_ascii=False)
    # Escape only the closing script tag so the inner reader HTML cannot break
    # out of its text/plain wrapper. openBook() reverses this before rendering.
    reader_shell_block = ('<script type="text/plain" id="reader-shell">%s</script>'
                          % shell.replace("</script>", "<\\/script>"))
    data_blocks = "\n".join(
        '<script type="text/plain" id="bookdata-%d">%s</script>'
        % (n, chapters_map[n].replace("</script>", "<\\/script>"))
        for n in sorted(chapters_map)
    )
    crest = (
        '<svg class="crest" viewBox="0 0 64 64" aria-hidden="true">'
        '<path d="M32 3l24 9v16c0 14-10 24-24 30C18 52 8 42 8 28V12z" fill="none" '
        'stroke="currentColor" stroke-width="2.5"/>'
        '<path d="M32 14c4 5 4 10 0 15-4-5-4-10 0-15z" fill="currentColor"/>'
        '<circle cx="32" cy="36" r="4" fill="none" stroke="currentColor" stroke-width="2"/>'
        '<path d="M22 44h20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
    )
    hat_svg = (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
        'stroke-linejoin="round" stroke-linecap="round" aria-hidden="true">'
        '<path d="M12 3 L8.3 14 H15.7 Z"/>'
        '<path d="M4.5 14 C8 16.2 16 16.2 19.5 14 L18.2 17.4 C14 19 10 19 5.8 17.4 Z"/></svg>'
    )
    world_svg = (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
        '<path d="M12 3c2.5 2.6 3.8 5.7 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.7-3.8-9S9.5 5.6 12 3z"/></svg>'
    )
    css = """
:root{--bg:#faf8f3;--bg2:#f1ede3;--fg:#2b2b2b;--muted:#7a7368;--accent:#7b1113;
--panel:#fff;--panel2:#f6f3ec;--border:#e6e0d4;--shadow:rgba(40,30,10,.14);--shadow2:rgba(40,30,10,.28);}
[data-theme="sepia"]{--bg:#f4ecd8;--bg2:#ece1c6;--fg:#4b3f2f;--muted:#8a795d;--accent:#8a5a1a;--panel:#fbf4e3;--panel2:#f2e8cf;--border:#e3d6b8;--shadow:rgba(80,55,15,.16);--shadow2:rgba(80,55,15,.3);}
[data-theme="dark"]{--bg:#1a1c20;--bg2:#15171a;--fg:#d6d9dd;--muted:#8b9197;--accent:#e0934a;--panel:#23262c;--panel2:#2b2f36;--border:#353a42;--shadow:rgba(0,0,0,.45);--shadow2:rgba(0,0,0,.65);}
[data-theme="amoled"]{--bg:#000;--bg2:#050505;--fg:#d8dadd;--muted:#7f8489;--accent:#d98a3d;--panel:#0c0c0e;--panel2:#131316;--border:#232327;--shadow:rgba(0,0,0,.8);--shadow2:rgba(0,0,0,.95);}
[data-theme="night"]{--bg:#0f1726;--bg2:#0b111d;--fg:#c5d2e6;--muted:#7585a0;--accent:#5b9bd5;--panel:#162032;--panel2:#1c293f;--border:#273349;--shadow:rgba(0,0,0,.5);--shadow2:rgba(0,0,0,.7);}
[data-theme="warm"]{--bg:#fbeee0;--bg2:#f4e0cc;--fg:#432e1f;--muted:#9b7a5e;--accent:#c2541b;--panel:#fdf3e8;--panel2:#f6e6d4;--border:#ecd7bf;--shadow:rgba(120,70,20,.16);--shadow2:rgba(120,70,20,.3);}
*{box-sizing:border-box;}
#viewer{position:fixed;inset:0;width:100%;height:100%;border:0;z-index:60;background:var(--bg);}
body.reading{overflow:hidden;}
html,body{margin:0;padding:0;}
body{background:var(--bg);color:var(--fg);font-family:Georgia,'Times New Roman',serif;
-webkit-font-smoothing:antialiased;transition:background .3s,color .3s;min-height:100vh;}
.wrap{max-width:1100px;margin:0 auto;padding:1.2rem 1.1rem 4rem;}
header.top{display:flex;align-items:center;gap:.8rem;padding:.6rem 0 1.4rem;}
header.top .logo{display:flex;align-items:center;gap:.7rem;flex:1;min-width:0;}
header.top .crest{width:40px;height:40px;color:var(--accent);flex:none;}
header.top h1{font-size:1.25rem;margin:0;line-height:1.1;}
header.top h1 small{display:block;font-size:.72rem;color:var(--muted);font-weight:400;letter-spacing:.04em;text-transform:uppercase;margin-top:.15rem;font-family:system-ui,sans-serif;}
.theme-btn{width:42px;height:42px;border-radius:11px;border:1px solid var(--border);background:var(--panel);color:var(--fg);cursor:pointer;font-size:1.1rem;display:inline-flex;align-items:center;justify-content:center;}
.theme-pop{position:absolute;right:1.1rem;top:64px;background:var(--panel);border:1px solid var(--border);border-radius:14px;box-shadow:0 14px 40px var(--shadow2);padding:.6rem;display:none;grid-template-columns:repeat(4,1fr);gap:.4rem;z-index:20;}
.theme-pop.open{display:grid;}
.theme-pop button{width:46px;height:40px;border-radius:9px;border:2px solid var(--border);cursor:pointer;font-weight:700;font-family:Georgia,serif;}
.theme-pop button.sel{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent) inset;}
.hero{background:linear-gradient(135deg,var(--panel),var(--panel2));border:1px solid var(--border);
border-radius:20px;padding:1.3rem;margin-bottom:1.8rem;display:flex;gap:1.2rem;align-items:center;box-shadow:0 8px 28px var(--shadow);}
.hero .mini{width:74px;height:104px;border-radius:10px;flex:none;display:flex;align-items:center;justify-content:center;color:#fff;box-shadow:0 6px 18px var(--shadow2);}
.hero .mini .crest{width:42px;height:42px;color:#fff;}
.hero .info{flex:1;min-width:0;}
.hero .lbl{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);font-family:system-ui,sans-serif;font-weight:700;}
.hero h2{margin:.2rem 0 .3rem;font-size:1.3rem;}
.hero .pbar{height:6px;background:var(--bg2);border-radius:6px;overflow:hidden;margin:.7rem 0 .2rem;}
.hero .pbar i{display:block;height:100%;background:var(--accent);border-radius:6px;}
.hero .pct{font-size:.78rem;color:var(--muted);font-family:system-ui,sans-serif;}
.hero .go{margin-top:.8rem;display:inline-block;background:var(--accent);color:#fff;text-decoration:none;
padding:.6rem 1.3rem;border-radius:999px;font-family:system-ui,sans-serif;font-weight:600;font-size:.9rem;}
.section-title{font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);font-family:system-ui,sans-serif;font-weight:700;margin:0 0 .9rem;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1.1rem;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:16px;overflow:hidden;
text-decoration:none;color:inherit;display:flex;flex-direction:column;transition:transform .18s,box-shadow .18s,border-color .18s;}
.card:hover{transform:translateY(-4px);box-shadow:0 14px 34px var(--shadow2);border-color:var(--accent);}
.card .cover{height:158px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;position:relative;gap:.5rem;}
.card .cover .crest{width:48px;height:48px;color:rgba(255,255,255,.92);}
.card .cover .bnum{position:absolute;top:.6rem;left:.7rem;font-size:.72rem;font-family:system-ui,sans-serif;background:rgba(255,255,255,.2);padding:.15rem .5rem;border-radius:999px;}
.card .cover .done{position:absolute;top:.6rem;right:.7rem;font-size:.9rem;}
.card .meta{padding:.8rem .9rem 1rem;flex:1;display:flex;flex-direction:column;}
.card .meta h3{margin:0 0 .25rem;font-size:1.04rem;line-height:1.2;}
.card .meta .sub{font-size:.78rem;color:var(--muted);font-family:system-ui,sans-serif;flex:1;}
.card .meta .stat{font-size:.72rem;color:var(--muted);font-family:system-ui,sans-serif;margin-top:.55rem;display:flex;justify-content:space-between;}
.card .pbar{height:5px;background:var(--bg2);border-radius:5px;overflow:hidden;margin-top:.55rem;}
.card .pbar i{display:block;height:100%;background:var(--accent);}
footer{text-align:center;color:var(--muted);font-size:.8rem;font-family:system-ui,sans-serif;margin-top:2.5rem;}
@media(max-width:560px){.grid{grid-template-columns:repeat(2,1fr);gap:.7rem;}
.card .cover{height:130px;}.hero{flex-direction:column;text-align:center;}.hero .info{text-align:center;}}
/* ===== Atmosfera (ambient canvas portal) ===== */
#bg{position:fixed;inset:0;width:100%;height:100%;z-index:0;display:block;pointer-events:none;}
.wrap{position:relative;z-index:1;}
.theme-btn{transition:border-color .25s,transform .15s;}
.theme-btn:active{transform:scale(.92);}
.theme-btn svg{width:20px;height:20px;}
header.top .actions{display:flex;gap:.5rem;align-items:center;}
/* ===== Fakultet chip ===== */
#housechip{margin:-0.5rem 0 1.5rem;}
.chip{display:inline-flex;align-items:center;gap:.55rem;background:var(--panel);border:1px solid var(--border);
color:var(--fg);font-family:system-ui,sans-serif;font-size:.84rem;padding:.5rem .9rem;border-radius:999px;
cursor:pointer;box-shadow:0 5px 16px var(--shadow);transition:border-color .2s,transform .15s;}
.chip:hover{border-color:var(--accent);transform:translateY(-1px);}
.chip strong{font-weight:700;}
.chip-dot{width:15px;height:15px;border-radius:50%;background:var(--accent);display:inline-block;
box-shadow:0 0 0 2px var(--panel),0 0 9px var(--accent);}
.chip-invite{color:var(--muted);}
/* ===== Saralash Qalpoqchasi modal ===== */
.hat-overlay{position:fixed;inset:0;z-index:80;background:rgba(8,6,10,.62);-webkit-backdrop-filter:blur(4px);
backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;padding:1.2rem;animation:hatfade .25s ease;}
.hat-overlay[hidden]{display:none;}
@keyframes hatfade{from{opacity:0}to{opacity:1}}
.hat-card{position:relative;max-width:440px;width:100%;max-height:90vh;overflow:auto;background:var(--panel);
color:var(--fg);border:1px solid var(--border);border-radius:22px;padding:1.7rem 1.5rem;
box-shadow:0 26px 70px rgba(0,0,0,.55);text-align:center;animation:hatpop .32s cubic-bezier(.2,.85,.3,1);}
@keyframes hatpop{from{transform:translateY(16px) scale(.96);opacity:0}to{transform:none;opacity:1}}
.hat-card h2{margin:.35rem 0 .1rem;font-size:1.55rem;}
.hat-card h3.hat-q{font-size:1.2rem;margin:.25rem 0 1.15rem;line-height:1.35;}
.hat-card p{color:var(--muted);font-size:.93rem;line-height:1.55;font-family:system-ui,sans-serif;margin:.5rem 0 0;}
.hat-x{position:absolute;top:.65rem;right:.7rem;width:34px;height:34px;border-radius:50%;border:1px solid var(--border);
background:var(--panel2);color:var(--fg);font-size:1.25rem;cursor:pointer;line-height:1;}
.hat-x:hover{border-color:var(--accent);}
.hat-step{font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;color:var(--accent);
font-family:system-ui,sans-serif;font-weight:700;}
.hat-emblem{color:var(--accent);margin-bottom:.2rem;}
.hat-emblem .crest{width:58px;height:58px;}
.hat-opts{display:flex;flex-direction:column;gap:.6rem;text-align:left;}
.hat-opt{background:var(--panel2);border:1px solid var(--border);color:var(--fg);font-family:system-ui,sans-serif;
font-size:.95rem;padding:.85rem 1rem;border-radius:13px;cursor:pointer;transition:transform .12s,border-color .12s,background .12s;}
.hat-opt:hover{border-color:var(--accent);transform:translateX(3px);}
.hat-actions{display:flex;gap:.6rem;justify-content:center;margin-top:1.3rem;flex-wrap:wrap;}
.hat-go{background:var(--accent);color:#fff;border:0;padding:.72rem 1.6rem;border-radius:999px;cursor:pointer;
font-family:system-ui,sans-serif;font-weight:600;font-size:.95rem;}
.hat-ghost{background:transparent;color:var(--muted);border:1px solid var(--border);padding:.72rem 1.2rem;
border-radius:999px;cursor:pointer;font-family:system-ui,sans-serif;font-size:.9rem;}
.hat-ghost:hover{border-color:var(--accent);color:var(--fg);}
.hat-house{width:98px;height:98px;border-radius:50%;margin:.7rem auto .3rem;display:flex;align-items:center;
justify-content:center;box-shadow:0 12px 32px rgba(0,0,0,.42);}
.hat-house .crest{width:54px;height:54px;color:#fff;}
.hat-tag{color:var(--accent);font-family:system-ui,sans-serif;font-weight:600;font-size:.87rem;}
/* ===== Sehrli Olam (Wizarding World) paneli ===== */
.world-card{position:relative;display:flex;flex-direction:column;max-width:820px;width:100%;height:88vh;
background:var(--panel);color:var(--fg);border:1px solid var(--border);border-radius:22px;overflow:hidden;
box-shadow:0 26px 70px rgba(0,0,0,.55);animation:hatpop .32s cubic-bezier(.2,.85,.3,1);}
.world-top{display:flex;align-items:center;gap:.7rem;padding:1rem 1.1rem;border-bottom:1px solid var(--border);
background:linear-gradient(135deg,var(--panel),var(--panel2));}
.world-top .wt-crest{width:34px;height:34px;color:var(--accent);flex:none;}
.world-top h2{font-size:1.2rem;margin:0;flex:1;min-width:0;}
.world-top h2 small{display:block;font-size:.68rem;color:var(--muted);font-weight:400;font-family:system-ui,sans-serif;text-transform:uppercase;letter-spacing:.08em;}
.world-x{width:36px;height:36px;border-radius:50%;border:1px solid var(--border);background:var(--panel2);
color:var(--fg);font-size:1.3rem;cursor:pointer;line-height:1;flex:none;}
.world-x:hover{border-color:var(--accent);}
.spoiler-tg{display:inline-flex;align-items:center;gap:.4rem;font-family:system-ui,sans-serif;font-size:.74rem;
color:var(--muted);background:var(--panel2);border:1px solid var(--border);border-radius:999px;padding:.35rem .7rem;cursor:pointer;flex:none;}
.spoiler-tg.on{color:var(--accent);border-color:var(--accent);}
.world-tabs{display:flex;gap:.2rem;padding:.5rem .7rem 0;border-bottom:1px solid var(--border);overflow-x:auto;}
.world-tabs button{background:none;border:0;border-bottom:2px solid transparent;color:var(--muted);
font-family:system-ui,sans-serif;font-size:.86rem;font-weight:600;padding:.6rem .7rem;cursor:pointer;white-space:nowrap;}
.world-tabs button.sel{color:var(--accent);border-bottom-color:var(--accent);}
.world-body{flex:1;overflow-y:auto;padding:1rem 1.1rem 2rem;}
.world-search{width:100%;background:var(--bg2);border:1px solid var(--border);border-radius:11px;
color:var(--fg);font-family:system-ui,sans-serif;font-size:.92rem;padding:.65rem .9rem;margin-bottom:.7rem;}
.world-cats{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1rem;}
.wcat{background:var(--panel2);border:1px solid var(--border);color:var(--muted);font-family:system-ui,sans-serif;
font-size:.78rem;padding:.4rem .8rem;border-radius:999px;cursor:pointer;}
.wcat.sel{background:var(--accent);border-color:var(--accent);color:#fff;}
.world-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.7rem;}
.wcard{position:relative;text-align:left;background:var(--panel2);border:1px solid var(--border);border-radius:14px;
padding:.8rem;cursor:pointer;transition:transform .14s,border-color .14s,box-shadow .14s;color:inherit;overflow:hidden;}
.wcard:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 10px 24px var(--shadow2);}
.wcard .wc-ic{font-size:1.5rem;line-height:1;}
.wcard .wc-name{font-weight:700;font-size:.95rem;margin:.4rem 0 .15rem;line-height:1.2;}
.wcard .wc-tag{font-size:.74rem;color:var(--muted);font-family:system-ui,sans-serif;}
.wh-dot{display:inline-block;width:10px;height:10px;border-radius:50%;vertical-align:middle;margin-right:.3rem;}
.wbadge{position:absolute;top:.5rem;right:.55rem;font-size:.62rem;font-family:system-ui,sans-serif;
background:var(--bg2);color:var(--muted);padding:.1rem .4rem;border-radius:999px;border:1px solid var(--border);}
.wcard.locked .wc-name,.wcard.locked .wc-tag{filter:blur(5px);-webkit-filter:blur(5px);user-select:none;}
.wcard.locked .wc-ic{opacity:.35;}
.lock-note{position:absolute;inset:auto 0 0 0;font-size:.64rem;text-align:center;color:var(--accent);
font-family:system-ui,sans-serif;padding:.25rem;background:linear-gradient(0deg,var(--panel2),transparent);}
.world-empty{color:var(--muted);font-family:system-ui,sans-serif;text-align:center;padding:2rem 0;}
/* detail */
.wd-back{background:none;border:0;color:var(--accent);font-family:system-ui,sans-serif;font-size:.85rem;
cursor:pointer;padding:.2rem 0;margin-bottom:.6rem;display:inline-flex;align-items:center;gap:.3rem;}
.wd-hero{border-radius:16px;padding:1.1rem;color:#fff;margin-bottom:.9rem;background:linear-gradient(150deg,var(--accent),rgba(0,0,0,.4));}
.wd-hero .wd-ic{font-size:2rem;}
.wd-hero h3{margin:.3rem 0 .1rem;font-size:1.4rem;}
.wd-hero .wd-tag{font-family:system-ui,sans-serif;font-size:.82rem;opacity:.92;}
.wd-meta{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:.8rem;}
.wd-chip{font-family:system-ui,sans-serif;font-size:.72rem;background:var(--panel2);border:1px solid var(--border);
color:var(--muted);padding:.3rem .7rem;border-radius:999px;}
.wd-desc{line-height:1.7;font-size:1rem;margin-bottom:1.1rem;}
.wd-rel-t{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
font-family:system-ui,sans-serif;font-weight:700;margin-bottom:.5rem;}
.wd-rel{display:flex;flex-wrap:wrap;gap:.45rem;}
.wd-rel button{background:var(--panel2);border:1px solid var(--border);color:var(--fg);font-family:system-ui,sans-serif;
font-size:.8rem;padding:.4rem .8rem;border-radius:999px;cursor:pointer;}
.wd-rel button:hover{border-color:var(--accent);color:var(--accent);}
.wd-facts{background:var(--panel2);border:1px solid var(--border);border-radius:12px;padding:.7rem .85rem;margin-bottom:1.1rem;}
.wf-row{display:flex;gap:.7rem;font-family:system-ui,sans-serif;font-size:.86rem;line-height:1.45;padding:.28rem 0;border-bottom:1px solid var(--border);}
.wf-row:last-child{border-bottom:0;}
.wf-l{flex:none;width:40%;color:var(--muted);}
.wf-v{flex:1;font-weight:600;}
.wd-lock{color:var(--accent);font-weight:600;font-size:.82rem;font-style:italic;}
.wd-facts-list{display:flex;flex-direction:column;gap:.55rem;margin-bottom:1.1rem;}
.wfact{font-family:system-ui,sans-serif;font-size:.88rem;line-height:1.55;padding-left:.75rem;border-left:3px solid var(--accent);}
.wfact-b{display:inline-block;font-size:.66rem;font-weight:800;color:var(--accent);letter-spacing:.02em;margin-right:.45rem;text-transform:uppercase;}
.wfact-hid{font-family:system-ui,sans-serif;font-size:.8rem;color:var(--muted);font-style:italic;padding-left:.75rem;}
/* timeline */
.world-tl{position:relative;padding-left:1.4rem;}
.world-tl:before{content:"";position:absolute;left:6px;top:6px;bottom:6px;width:2px;background:var(--border);}
.tl-item{position:relative;margin-bottom:1.3rem;}
.tl-item:before{content:"";position:absolute;left:-1.4rem;top:4px;width:12px;height:12px;border-radius:50%;
background:var(--accent);box-shadow:0 0 0 3px var(--panel);}
.tl-year{font-family:system-ui,sans-serif;font-weight:800;color:var(--accent);font-size:.95rem;}
.tl-title{font-weight:700;font-size:1.02rem;margin:.1rem 0 .2rem;}
.tl-desc{color:var(--muted);font-family:system-ui,sans-serif;font-size:.85rem;line-height:1.55;}
.tl-item.locked .tl-title,.tl-item.locked .tl-desc{filter:blur(5px);-webkit-filter:blur(5px);cursor:pointer;}
/* family */
.fam{margin-bottom:1.6rem;}
.fam-name{font-weight:700;font-size:1.1rem;}
.fam-note{color:var(--muted);font-family:system-ui,sans-serif;font-size:.82rem;margin:.15rem 0 .8rem;}
.fam-level{display:flex;flex-wrap:wrap;justify-content:center;gap:.5rem;margin-bottom:.4rem;position:relative;}
.fam-level+.fam-level:before{content:"";position:absolute;top:-.5rem;left:50%;width:2px;height:.5rem;background:var(--border);}
.fam-box{background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:.45rem .8rem;
font-family:system-ui,sans-serif;font-size:.82rem;font-weight:600;}
@media(max-width:560px){.world-card{height:94vh;max-width:100%;border-radius:16px;}
.world-grid{grid-template-columns:repeat(2,1fr);}}
/* ===== Hogvarts xaritasi (Marauder uslubi) ===== */
.map-toolbar{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;margin-bottom:.7rem;}
.map-toggle{display:inline-flex;align-items:center;gap:.4rem;font-family:system-ui,sans-serif;font-size:.76rem;
background:var(--panel2);border:1px solid var(--border);color:var(--muted);border-radius:999px;padding:.35rem .8rem;cursor:pointer;}
.map-toggle.on{color:#5b3a1a;border-color:#8a5a1a;background:#f0e2c4;}
.map-hint{font-family:system-ui,sans-serif;font-size:.72rem;color:var(--muted);}
.map-wrap{position:relative;width:100%;aspect-ratio:10/7;border-radius:14px;overflow:hidden;
border:1px solid #b79b6a;background:radial-gradient(120% 120% at 50% 0%,#f3e7c9,#e5d3aa 55%,#d8c49a);
box-shadow:inset 0 0 60px rgba(120,85,35,.35);}
.map-wrap:before{content:"";position:absolute;inset:0;pointer-events:none;
background:repeating-linear-gradient(0deg,rgba(120,85,35,.05) 0 2px,transparent 2px 5px);opacity:.5;}
.map-svg{position:absolute;inset:0;width:100%;height:100%;color:#5b3f1e;opacity:.72;pointer-events:none;}
.map-title{position:absolute;top:2%;left:0;right:0;text-align:center;font-family:Georgia,serif;font-style:italic;
color:#6b4a22;font-size:clamp(.8rem,2.6vw,1.15rem);letter-spacing:.03em;pointer-events:none;text-shadow:0 1px 0 rgba(255,250,235,.5);}
.map-mk{position:absolute;transform:translate(-50%,-50%);display:flex;flex-direction:column;align-items:center;
gap:2px;background:none;border:0;cursor:pointer;padding:0;z-index:2;}
.mk-dot{width:11px;height:11px;border-radius:50%;background:#6b1b1c;box-shadow:0 0 0 3px rgba(240,226,196,.85),0 0 6px rgba(107,27,28,.6);transition:transform .15s;}
.map-mk:hover .mk-dot,.map-mk:focus .mk-dot{transform:scale(1.5);}
.mk-lbl{font-family:Georgia,serif;font-size:clamp(.5rem,1.7vw,.72rem);color:#4a2f12;white-space:nowrap;
background:rgba(243,231,205,.82);padding:0 .3rem;border-radius:4px;max-width:22vw;overflow:hidden;text-overflow:ellipsis;}
.map-mk:hover .mk-lbl{background:#f3e7cd;font-weight:700;}
.map-mk.locked{cursor:pointer;}
.map-mk.locked .mk-dot{background:#8a8072;box-shadow:0 0 0 3px rgba(240,226,196,.7);}
.map-mk.locked .mk-lbl{filter:blur(4px);}
.map-fig{position:absolute;transform:translate(-50%,-50%);z-index:3;display:none;flex-direction:column;align-items:center;
pointer-events:none;animation:figstep 3.4s ease-in-out infinite;}
.map-wrap.marauder .map-fig{display:flex;}
.map-wrap.marauder .map-mk .mk-lbl{opacity:.35;}
.fig-ic{font-size:clamp(.7rem,2vw,1rem);line-height:1;filter:sepia(1) saturate(.6);}
.fig-nm{font-family:Georgia,serif;font-style:italic;font-size:clamp(.5rem,1.6vw,.7rem);color:#3a2a12;
background:rgba(243,231,205,.7);padding:0 .25rem;border-radius:3px;white-space:nowrap;}
@keyframes figstep{0%,100%{transform:translate(-50%,-50%)}50%{transform:translate(-46%,-53%)}}
.map-legend{margin-top:.7rem;font-family:system-ui,sans-serif;font-size:.72rem;color:var(--muted);text-align:center;}
.map-img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#efe7d0;}
.map-credit{position:absolute;bottom:6px;right:8px;font-family:system-ui,sans-serif;font-size:.6rem;color:#5b3f1e;background:rgba(243,231,205,.8);padding:.12rem .45rem;border-radius:4px;border:1px solid rgba(138,90,26,.4);}
.map-toolbar{justify-content:space-between;}
.map-sels{display:flex;flex-wrap:wrap;gap:.35rem;}
.mapsel{background:var(--panel2);border:1px solid var(--border);color:var(--muted);font-family:system-ui,sans-serif;font-size:.74rem;padding:.35rem .75rem;border-radius:999px;cursor:pointer;}
.mapsel.sel{background:#8a5a1a;border-color:#8a5a1a;color:#fff;}
.mapsel.locked{opacity:.5;cursor:not-allowed;}
.map-svg .ink path,.map-svg .ink circle{stroke-dasharray:280;stroke-dashoffset:0;}
.map-wrap.reveal .map-svg{animation:mapfade 1s ease;}
.map-wrap.reveal .map-svg .ink path,.map-wrap.reveal .map-svg .ink circle{stroke-dashoffset:280;animation:inkdraw 1.5s ease forwards;}
@keyframes mapfade{from{opacity:0}to{opacity:.72}}
@keyframes inkdraw{to{stroke-dashoffset:0}}
.map-wrap.reveal .map-mk{animation:mkfade .9s ease both;}
@keyframes mkfade{from{opacity:0}to{opacity:1}}
.map-oath{position:absolute;left:0;right:0;bottom:5%;text-align:center;font-family:Georgia,serif;font-style:italic;color:#6b4a22;font-size:clamp(.55rem,2vw,.82rem);opacity:0;pointer-events:none;padding:0 6%;}
.map-wrap.reveal .map-oath{animation:oath 3.6s ease forwards;}
@keyframes oath{0%{opacity:0}18%{opacity:.9}72%{opacity:.9}100%{opacity:0}}
.map-compass{position:absolute;right:3.5%;bottom:7%;width:clamp(26px,7vw,42px);height:auto;color:#6b4a22;opacity:.55;pointer-events:none;}
.map-corner{position:absolute;width:15px;height:15px;border:2px solid #8a5a1a;opacity:.5;pointer-events:none;}
.map-corner.tl{top:7px;left:7px;border-right:0;border-bottom:0;}
.map-corner.tr{top:7px;right:7px;border-left:0;border-bottom:0;}
.map-corner.bl{bottom:7px;left:7px;border-right:0;border-top:0;}
.map-corner.br{bottom:7px;right:7px;border-left:0;border-top:0;}
.map-wrap.marauder .map-fig{animation-duration:6s;animation-timing-function:ease-in-out;animation-iteration-count:infinite;}
.map-wrap.marauder .map-fig.fig-v0{animation-name:wanderA;}
.map-wrap.marauder .map-fig.fig-v1{animation-name:wanderB;}
.map-wrap.marauder .map-fig.fig-v2{animation-name:wanderC;}
@keyframes wanderA{0%{transform:translate(-50%,-50%)}30%{transform:translate(-38%,-58%)}65%{transform:translate(-60%,-44%)}100%{transform:translate(-50%,-50%)}}
@keyframes wanderB{0%{transform:translate(-50%,-50%)}35%{transform:translate(-62%,-52%)}70%{transform:translate(-42%,-60%)}100%{transform:translate(-50%,-50%)}}
@keyframes wanderC{0%{transform:translate(-50%,-50%)}40%{transform:translate(-52%,-40%)}75%{transform:translate(-58%,-58%)}100%{transform:translate(-50%,-50%)}}
@media(prefers-reduced-motion:reduce){.map-wrap.reveal .map-svg .ink path,.map-wrap.reveal .map-svg .ink circle{stroke-dasharray:none;stroke-dashoffset:0;animation:none;}.map-wrap.marauder .map-fig{animation:none;}}
"""
    js = """
var BOOKS=__BOOKS__;
var GLOSSARY_SHARED=__GLOSS__;
var COVERS={1:'#7b1113',2:'#1f6f4a',3:'#5b3a8a',4:'#b5651d',5:'#1d6fa5',6:'#7a5901',7:'#3a3a3a',8:'#0b5d63'};
var THEMES=[['day','Kunduzgi','#faf8f3','#7b1113'],['sepia','Sepiya','#f4ecd8','#8a5a1a'],
['dark','Tungi','#1a1c20','#e0934a'],['amoled','AMOLED','#000','#d98a3d'],
['night','Yarim tun','#0f1726','#5b9bd5'],['warm','Iliq','#fbeee0','#c2541b']];
function gv(c){return 'linear-gradient(150deg,'+c+',rgba(0,0,0,.35))';}
function prog(key){try{var d=JSON.parse(localStorage.getItem(key));return (d&&d.progress&&d.progress.pct)||0;}catch(e){return 0;}}
function esc(s){return String(s).replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
function fmtW(w){return w>=1000?Math.round(w/1000)+'k':w;}
var CREST='__CREST__';
function render(){
  var grid=document.getElementById('grid');
  grid.innerHTML=BOOKS.map(function(b){
    var p=prog(b.key);var col=COVERS[b.n]||b.accent;
    return '<a class="card" href="#kitob-'+b.n+'">'+
      '<div class="cover" style="background:'+gv(col)+'">'+
        '<span class="bnum">'+b.n+'-kitob</span>'+(p>=99?'<span class="done">\\u2713</span>':'')+
        CREST+'</div>'+
      '<div class="meta"><h3>'+esc(b.title)+'</h3>'+
        '<div class="sub">'+esc(b.sub)+'</div>'+
        '<div class="stat"><span>'+b.chapters+' bob</span><span>'+fmtW(b.words)+" so'z</span></div>"+
        (p>0?'<div class="pbar"><i style="width:'+p+'%"></i></div>':'')+
      '</div></a>';
  }).join('');
  renderHero();renderHouseChip();
}
function renderHero(){
  var host=document.getElementById('hero');var last=null;
  try{last=JSON.parse(localStorage.getItem('gp_last_book'));}catch(e){}
  var b=null;
  if(last&&last.id){b=BOOKS.filter(function(x){return x.n===last.id;})[0];}
  if(!b){host.style.display='none';return;}
  var p=prog(b.key);var col=COVERS[b.n]||b.accent;
  host.style.display='flex';
  host.innerHTML='<div class="mini" style="background:'+gv(col)+'">'+CREST+'</div>'+
    '<div class="info"><div class="lbl">Davom etish</div><h2>'+esc(b.title)+'</h2>'+
    '<div class="pbar"><i style="width:'+p+'%"></i></div>'+
    '<div class="pct">'+p+'% o\\'qildi \\u00b7 '+b.chapters+' bob</div>'+
    '<a class="go" href="#kitob-'+b.n+'">O\\'qishni davom ettirish</a></div>';
}
// theme
var root=document.documentElement;
function applyTheme(t){root.setAttribute('data-theme',t);try{localStorage.setItem('gp_library_theme',t);}catch(e){}
  var mc=document.getElementById('mtc');if(mc){var m={day:'#7b1113',sepia:'#8a5a1a',dark:'#1a1c20',amoled:'#000',night:'#0f1726',warm:'#c2541b'};mc.setAttribute('content',m[t]||'#7b1113');}
  Array.prototype.forEach.call(document.querySelectorAll('.theme-pop button'),function(x){x.classList.toggle('sel',x.dataset.t===t);});
  if(window.Portal){Portal.repaint();}}
function buildThemePop(){var p=document.getElementById('themepop');
  p.innerHTML=THEMES.map(function(t){return '<button data-t="'+t[0]+'" title="'+t[1]+'" style="background:'+t[2]+';color:'+t[3]+'">Aa</button>';}).join('');
  Array.prototype.forEach.call(p.querySelectorAll('button'),function(x){x.onclick=function(){applyTheme(x.dataset.t);};});}
document.getElementById('themebtn').onclick=function(e){e.stopPropagation();document.getElementById('themepop').classList.toggle('open');};
document.addEventListener('click',function(){document.getElementById('themepop').classList.remove('open');});
function openBook(n){
  var v=document.getElementById('viewer');
  var shellEl=document.getElementById('reader-shell');
  var dataEl=document.getElementById('bookdata-'+n);
  if(!shellEl||!dataEl){return;}
  // restore the escaped closing script tags in both the shared shell and the
  // book's chapters, then stitch them together for this book only.
  var bad='<'+String.fromCharCode(92)+'/script>';var good='<'+'/script>';
  var shell=shellEl.textContent.split(bad).join(good);
  var chapters=dataEl.textContent.split(bad).join(good);
  var b=null;for(var i=0;i<BOOKS.length;i++){if(BOOKS[i].n===n){b=BOOKS[i];break;}}
  if(!b){return;}
  var cfg={key:b.key,id:b.n,title:b.title};
  if(b.gloss){cfg.glossary=GLOSSARY_SHARED;}
  v.srcdoc=shell.split('@@TITLE@@').join(b.title)
    .split('@@SUB@@').join(b.sub)
    .split('@@ACCENT@@').join(b.accent)
    .split('@@BOOKCFG@@').join(JSON.stringify(cfg))
    .split('@@CHAPTERS@@').join(chapters);
  v.hidden=false;
  document.getElementById('lib').style.display='none';
  document.body.classList.add('reading');
  if(window.Portal){Portal.pause();}
  try{v.focus();}catch(e){}
  try{location.hash='kitob-'+n;}catch(e){}
}
function showLibrary(){
  var v=document.getElementById('viewer');
  v.hidden=true; v.removeAttribute('srcdoc');
  document.getElementById('lib').style.display='';
  document.body.classList.remove('reading');
  if(window.Portal){Portal.resume();}
  try{if(location.hash){history.replaceState(null,'',location.pathname+location.search);}}catch(e){}
  render();
}
window.addEventListener('message',function(e){if(e&&e.data==='gp-back'){showLibrary();}});
window.addEventListener('hashchange',function(){
  var m=/kitob-(\\d+)/.exec(location.hash);
  if(m){if(document.getElementById('viewer').hidden){openBook(+m[1]);}}
  else{if(!document.getElementById('viewer').hidden){showLibrary();}}
});
// ===== Saralash Qalpoqchasi (Sorting Hat) =====
var HOUSES=__HOUSES__;var QUIZ=__QUIZ__;var T=__T__;
function getHouse(){try{return localStorage.getItem('gp_house')||'';}catch(e){return '';}}
function setHouse(h){try{localStorage.setItem('gp_house',h);}catch(e){}}
var hatState=null;
function hatShell(inner){return '<div class="hat-card" role="dialog" aria-modal="true"><button class="hat-x" id="hatx" aria-label="'+esc(T.close)+'">\\u00d7</button>'+inner+'</div>';}
function bindClose(){var x=document.getElementById('hatx');if(x){x.onclick=hatClose;}}
function hatClose(){document.getElementById('hatmodal').hidden=true;}
function hatOpen(force){var h=getHouse();
  if(h&&!force){hatResult(h);}else{hatState={i:0,score:{gryffindor:0,slytherin:0,hufflepuff:0,ravenclaw:0}};hatStep();}
  document.getElementById('hatmodal').hidden=false;}
function hatStep(){var m=document.getElementById('hatmodal');var i=hatState.i;
  if(i===0){m.innerHTML=hatShell('<div class="hat-emblem">'+CREST+'</div><h2>'+esc(T.sortTitle)+'</h2><p>'+esc(T.sortIntro)+'</p><div class="hat-actions"><button class="hat-go" id="hatstart">'+esc(T.begin)+'</button></div>');
    document.getElementById('hatstart').onclick=function(){hatState.i=1;hatStep();};bindClose();return;}
  var q=QUIZ[i-1];
  var opts=q.a.map(function(o){return '<button class="hat-opt" data-h="'+o.h+'">'+esc(o.t)+'</button>';}).join('');
  m.innerHTML=hatShell('<div class="hat-step">'+esc(T.q)+' '+i+' / '+QUIZ.length+'</div><h3 class="hat-q">'+esc(q.q)+'</h3><div class="hat-opts">'+opts+'</div>');
  Array.prototype.forEach.call(m.querySelectorAll('.hat-opt'),function(b){b.onclick=function(){hatState.score[b.getAttribute('data-h')]++;if(hatState.i>=QUIZ.length){hatFinish();}else{hatState.i++;hatStep();}};});
  bindClose();}
function hatFinish(){var s=hatState.score,best=[],max=-1;
  for(var k in s){if(s[k]>max){max=s[k];best=[k];}else if(s[k]===max){best.push(k);}}
  var h=best[Math.floor(Math.random()*best.length)];setHouse(h);hatResult(h);renderHouseChip();}
function hatResult(h){var m=document.getElementById('hatmodal');var d=HOUSES[h];
  m.innerHTML=hatShell('<div class="hat-step">'+esc(T.result)+'</div><div class="hat-house" style="background:linear-gradient(150deg,'+d.c1+','+d.c2+')">'+CREST+'</div><h2>'+esc(d.name)+'</h2><div class="hat-tag">'+esc(d.tag)+'</div><p>'+esc(d.desc)+'</p><div class="hat-actions"><button class="hat-go" id="hatok">'+esc(T.close)+'</button><button class="hat-ghost" id="hatretry">'+esc(T.retake)+'</button></div>');
  document.getElementById('hatok').onclick=hatClose;document.getElementById('hatretry').onclick=function(){hatOpen(true);};bindClose();}
function renderHouseChip(){var host=document.getElementById('housechip');if(!host){return;}
  var h=getHouse();var hb=document.getElementById('hatbtn');
  if(h){var d=HOUSES[h];host.innerHTML='<button class="chip" id="chipbtn"><span class="chip-dot" style="background:linear-gradient(150deg,'+d.c1+','+d.c2+')"></span>'+esc(T.your)+': <strong>'+esc(d.name)+'</strong></button>';if(hb){hb.style.borderColor=d.c1;}}
  else{host.innerHTML='<button class="chip chip-invite" id="chipbtn"><span class="chip-dot"></span>'+esc(T.tryHat)+'</button>';if(hb){hb.style.borderColor='';}}
  var cb=document.getElementById('chipbtn');if(cb){cb.onclick=function(){hatOpen(false);};}}
document.getElementById('hatmodal').addEventListener('click',function(e){if(e.target===this){hatClose();}});
document.getElementById('hatbtn').onclick=function(e){e.stopPropagation();hatOpen(false);};
(function(){var wm=document.getElementById('worldmodal');if(wm){wm.addEventListener('click',function(e){if(e.target===this){worldClose();}});}
var wb=document.getElementById('worldbtn');if(wb){wb.onclick=function(e){e.stopPropagation();worldOpen();};}})();
document.addEventListener('keydown',function(e){if(e.key==='Escape'||e.keyCode===27){hatClose();worldClose();}});

// ===== Sehrli Olam (Wizarding World) =====
var WORLD=__WORLD__;
var MAPARTS=__MAPARTS__;var MAPDECO=__MAPDECO__;
var WCAT={all:['Barchasi','\\uD83D\\uDCDA'],qahramon:['Qahramonlar','\\uD83E\\uDDD9'],fakultet:['Fakultetlar','\\uD83D\\uDEE1'],joy:['Joylar','\\uD83C\\uDFF0'],sehr:['Sehrlar','\\u2728'],mavjudot:['Mavjudotlar','\\uD83D\\uDC3E'],buyum:['Buyumlar','\\uD83D\\uDDDD']};
var HCOL={gryffindor:['#7b1113','#d4af37','Gryffindor'],slizerin:['#1a472a','#a7b0b3','Slizerin'],puffenduy:['#d3a625','#372e29','Puffenduy'],kogtevran:['#0e1a40','#946b2d','Kogtevran']};
var HMAP={gryffindor:'gryffindor',slytherin:'slizerin',hufflepuff:'puffenduy',ravenclaw:'kogtevran'};
var wState={tab:'enc',cat:'all',q:'',detail:null,map:'grounds'};var wRevealed={};var wMarauder=false;
function wById(id){for(var i=0;i<WORLD.entries.length;i++){if(WORLD.entries[i].id===id)return WORLD.entries[i];}return null;}
function spoilerOn(){try{return localStorage.getItem('gp_spoiler')!=='off';}catch(e){return true;}}
function setSpoiler(v){try{localStorage.setItem('gp_spoiler',v?'on':'off');}catch(e){}}
function wFrontier(){var f=1;BOOKS.forEach(function(b){if(prog(b.key)>0&&b.n>f)f=b.n;});try{var l=JSON.parse(localStorage.getItem('gp_last_book'));if(l&&l.id&&l.id>f)f=l.id;}catch(e){}return f;}
function wLocked(book,key){return spoilerOn()&&book>wFrontier()&&!wRevealed[key];}
function wGrad(e){if(e.c1)return 'linear-gradient(150deg,'+e.c1+','+e.c2+')';if(e.house&&HCOL[e.house])return 'linear-gradient(150deg,'+HCOL[e.house][0]+','+HCOL[e.house][1]+')';return 'linear-gradient(150deg,var(--accent),rgba(0,0,0,.4))';}
function worldOpen(){wState={tab:'enc',cat:'all',q:'',detail:null,map:'grounds'};
  var m=document.getElementById('worldmodal');if(!m)return;
  m.innerHTML='<div class="world-card" role="dialog" aria-modal="true" aria-label="Sehrli Olam">'+
    '<div class="world-top">'+CREST.replace('class="crest"','class="wt-crest"')+
    '<h2>Sehrli Olam<small>Garri Potter ensiklopediyasi</small></h2>'+
    '<button class="spoiler-tg'+(spoilerOn()?' on':'')+'" id="wspoiler" title="Spoiler himoyasi">\\uD83D\\uDEE1 Spoiler</button>'+
    '<button class="world-x" id="wx" aria-label="Yopish">\\u00d7</button></div>'+
    '<div class="world-tabs" id="wtabs">'+
      '<button data-t="enc" class="sel">\\uD83D\\uDCD6 Ensiklopediya</button>'+
      '<button data-t="tl">\\uD83D\\uDD70 Voqealar tasmasi</button>'+
      '<button data-t="fam">\\uD83C\\uDF33 Oila daraxti</button>'+
      '<button data-t="map">\\uD83D\\uDDFA Xarita</button>'+
    '</div><div class="world-body" id="world-body"></div></div>';
  document.getElementById('wx').onclick=worldClose;
  document.getElementById('wspoiler').onclick=function(){setSpoiler(!spoilerOn());this.classList.toggle('on',spoilerOn());worldRenderBody();};
  Array.prototype.forEach.call(document.querySelectorAll('#wtabs button'),function(b){b.onclick=function(){wState.tab=b.getAttribute('data-t');wState.detail=null;Array.prototype.forEach.call(document.querySelectorAll('#wtabs button'),function(x){x.classList.toggle('sel',x===b);});worldRenderBody();};});
  worldRenderBody();m.hidden=false;}
function worldClose(){var m=document.getElementById('worldmodal');if(m)m.hidden=true;}
function worldRenderBody(){var body=document.getElementById('world-body');if(!body)return;
  if(wState.detail){
    if(wState.detail.indexOf('loc:')===0){body.innerHTML=wLocDetailHTML(wState.detail.slice(4));}
    else{body.innerHTML=wDetailHTML(wState.detail);}
    wBindDetail(body);body.scrollTop=0;return;}
  if(wState.tab==='enc'){wRenderEnc(body);}else if(wState.tab==='tl'){wRenderTL(body);}
  else if(wState.tab==='map'){wRenderMap(body);}else{wRenderFam(body);}}
function wRenderEnc(body){
  var cats=['all','qahramon','fakultet','joy','sehr','mavjudot','buyum'];
  var chips=cats.map(function(c){return '<button class="wcat'+(wState.cat===c?' sel':'')+'" data-c="'+c+'">'+WCAT[c][1]+' '+WCAT[c][0]+'</button>';}).join('');
  var q=wState.q.trim().toLowerCase();
  var list=WORLD.entries.filter(function(e){if(wState.cat!=='all'&&e.cat!==wState.cat)return false;
    if(q){if((e.name+' '+e.tag+' '+e.desc).toLowerCase().indexOf(q)<0)return false;}return true;});
  var myHouse=HMAP[getHouse()]||'';
  var cards=list.map(function(e){var locked=wLocked(e.book,e.id);
    var dot=(e.house&&HCOL[e.house])?'<span class="wh-dot" style="background:'+HCOL[e.house][0]+'"></span>':'';
    var mine=(e.cat==='fakultet'&&e.id===myHouse)?' style="border-color:'+e.c1+';border-width:2px"':'';
    return '<button class="wcard'+(locked?' locked':'')+'" data-id="'+e.id+'"'+mine+'>'+
      '<div class="wc-ic">'+WCAT[e.cat][1]+'</div><span class="wbadge">'+e.book+'-kitob</span>'+
      '<div class="wc-name">'+dot+esc(e.name)+'</div><div class="wc-tag">'+esc(e.tag)+'</div>'+
      (locked?'<div class="lock-note">\\uD83D\\uDD12 '+e.book+'-kitobda ochiladi</div>':'')+'</button>';}).join('');
  body.innerHTML='<input class="world-search" id="wq" placeholder="Ensiklopediyadan qidirish..." value="'+esc(wState.q).replace(/"/g,'&quot;')+'">'+
    '<div class="world-cats">'+chips+'</div>'+
    (list.length?'<div class="world-grid">'+cards+'</div>':'<div class="world-empty">Hech narsa topilmadi.</div>');
  var qi=document.getElementById('wq');qi.oninput=function(){var s=qi.selectionStart;wState.q=qi.value;wRenderEnc(body);var n=document.getElementById('wq');if(n){n.focus();try{n.setSelectionRange(s,s);}catch(e){}}};
  Array.prototype.forEach.call(body.querySelectorAll('.wcat'),function(b){b.onclick=function(){wState.cat=b.getAttribute('data-c');wRenderEnc(body);};});
  Array.prototype.forEach.call(body.querySelectorAll('.wcard'),function(b){b.onclick=function(){wState.detail=b.getAttribute('data-id');worldRenderBody();};});}
function wDetailHTML(id){var e=wById(id);if(!e)return '<div class="world-empty">Topilmadi.</div>';
  if(wLocked(e.book,e.id)){return '<button class="wd-back" data-back="1">\\u2039 Orqaga</button>'+
    '<div class="wd-hero" style="background:linear-gradient(150deg,#555,#222)"><div class="wd-ic">\\uD83D\\uDD12</div><h3>Spoiler himoyasi</h3><div class="wd-tag">Bu maqola '+e.book+'-kitobda ochiladi</div></div>'+
    '<p class="wd-desc">Agar syujet sirini oldindan bilishni istamasangiz, avval '+e.book+"-kitobni o'qing.</p>"+
    '<div class="wd-rel"><button data-reveal="'+e.id+'">Baribir ko\\u02bbrsatish</button></div>';}
  var meta='<span class="wd-chip">'+WCAT[e.cat][0]+'</span><span class="wd-chip">'+e.book+'-kitob</span>';
  if(e.house&&HCOL[e.house])meta+='<span class="wd-chip">\\uD83D\\uDEE1 '+HCOL[e.house][2]+'</span>';
  var fr=wFrontier();
  var bio='';
  if(e.rows&&e.rows.length){bio='<div class="wd-facts">'+e.rows.map(function(r){
    var v=(r[2]>fr)?'<span class="wd-lock">\\uD83D\\uDD12 keyinroq ochiladi</span>':esc(r[1]);
    return '<div class="wf-row"><span class="wf-l">'+esc(r[0])+'</span><span class="wf-v">'+v+'</span></div>';}).join('')+'</div>';}
  var facts='';
  if(e.facts&&e.facts.length){var vis=e.facts.filter(function(f){return f[0]<=fr;});var hid=e.facts.length-vis.length;
    if(vis.length||hid){facts='<div class="wd-rel-t">Muhim voqealar</div><div class="wd-facts-list">'+
      vis.map(function(f){return '<div class="wfact"><span class="wfact-b">'+f[0]+'-kitob</span>'+esc(f[1])+'</div>';}).join('')+
      (hid>0?'<div class="wfact-hid">\\uD83D\\uDD12 Yana '+hid+' ta voqea keyingi kitoblarda ochiladi</div>':'')+'</div>';}}
  var rels=e.rel.map(function(rid){var r=wById(rid);return r?'<button data-id="'+rid+'">'+esc(r.name)+'</button>':'';}).join('');
  return '<button class="wd-back" data-back="1">\\u2039 Orqaga</button>'+
    '<div class="wd-hero" style="background:'+wGrad(e)+'"><div class="wd-ic">'+WCAT[e.cat][1]+'</div><h3>'+esc(e.name)+'</h3><div class="wd-tag">'+esc(e.tag)+'</div></div>'+
    '<div class="wd-meta">'+meta+'</div><p class="wd-desc">'+esc(e.desc)+'</p>'+bio+facts+
    (rels?'<div class="wd-rel-t">Bog\\u02bbliq maqolalar</div><div class="wd-rel">'+rels+'</div>':'');}
function wBindDetail(body){var back=body.querySelector('[data-back]');if(back)back.onclick=function(){wState.detail=null;worldRenderBody();};
  var rev=body.querySelector('[data-reveal]');if(rev)rev.onclick=function(){wRevealed[rev.getAttribute('data-reveal')]=1;worldRenderBody();};
  var revl=body.querySelector('[data-reveal-loc]');if(revl)revl.onclick=function(){wRevealed[revl.getAttribute('data-reveal-loc')]=1;worldRenderBody();};
  Array.prototype.forEach.call(body.querySelectorAll('.wd-rel button[data-id]'),function(b){b.onclick=function(){wState.detail=b.getAttribute('data-id');worldRenderBody();};});}
function wRenderTL(body){var items=WORLD.timeline.map(function(t,i){var locked=wLocked(t.book,'tl'+i);
    return '<div class="tl-item'+(locked?' locked':'')+'" data-tl="'+i+'">'+
      '<div class="tl-year">'+esc(t.year)+' <span class="wbadge" style="position:static">'+t.book+'-kitob</span></div>'+
      '<div class="tl-title">'+esc(t.title)+'</div><div class="tl-desc">'+esc(t.desc)+'</div></div>';}).join('');
  body.innerHTML='<div class="world-tl">'+items+'</div>';
  Array.prototype.forEach.call(body.querySelectorAll('.tl-item.locked'),function(el){el.onclick=function(){wRevealed['tl'+el.getAttribute('data-tl')]=1;wRenderTL(body);};});}
function wRenderFam(body){body.innerHTML=WORLD.families.map(function(f){var locked=wLocked(f.book,'fam-'+f.name);
    var levels=f.levels.map(function(lv){return '<div class="fam-level">'+lv.map(function(n){return '<span class="fam-box">'+esc(n)+'</span>';}).join('')+'</div>';}).join('');
    return '<div class="fam"><div class="fam-name">'+esc(f.name)+'</div><div class="fam-note">'+esc(f.note)+'</div>'+
      (locked?'<div class="world-empty">\\uD83D\\uDD12 '+f.book+'-kitobda ochiladi</div>':levels)+'</div>';}).join('');}
function wRenderMap(body){var M=WORLD.map,fr=wFrontier(),i;
  var chips=M.maps.map(function(m){var lk=(m.book>fr);
    return '<button class="mapsel'+(m.id===wState.map?' sel':'')+(lk?' locked':'')+'" data-map="'+m.id+'">'+esc(m.name)+(lk?' \\uD83D\\uDD12':'')+'</button>';}).join('');
  var mp=null;for(i=0;i<M.maps.length;i++){if(M.maps[i].id===wState.map){mp=M.maps[i];break;}}
  if(!mp||mp.book>fr){mp=null;for(i=0;i<M.maps.length;i++){if(M.maps[i].book<=fr){mp=M.maps[i];wState.map=mp.id;break;}}}
  var inner='';
  if(mp&&mp.img){
    inner='<div class="map-wrap reveal" id="mapwrap"><img class="map-img" src="'+mp.img+'" alt="Hogvarts xaritasi (illyustratsiya)"/>'+MAPDECO+
      '<div class="map-title">'+esc(mp.name)+'</div>'+
      (mp.credit?'<div class="map-credit">'+esc(mp.credit)+'</div>':'')+'</div>';
  }else if(mp){
    var mks=(mp.locations||[]).map(function(l,ix){var locked=wLocked(l.book,'loc-'+mp.id+'-'+ix);
      return '<button class="map-mk'+(locked?' locked':'')+'" style="left:'+l.x+'%;top:'+l.y+'%" data-loc="'+ix+'" title="'+esc(l.name)+'"><span class="mk-dot"></span><span class="mk-lbl">'+esc(l.name)+'</span></button>';}).join('');
    var figs=(mp.figures||[]).map(function(f,fi){if(wLocked(f.book,'fig-'+mp.id+'-'+fi))return '';
      var col=(f.house&&HCOL[f.house])?HCOL[f.house][0]:'#3a2a12';
      return '<div class="map-fig fig-v'+(fi%3)+'" style="left:'+f.x+'%;top:'+f.y+'%"><span class="fig-ic">\\uD83D\\uDC63</span><span class="fig-nm" style="color:'+col+'">'+esc(f.name)+'</span></div>';}).join('');
    inner='<div class="map-wrap reveal'+(wMarauder?' marauder':'')+'" id="mapwrap">'+(MAPARTS[mp.art]||'')+MAPDECO+
      '<div class="map-title">'+esc(mp.name)+'</div>'+
      '<div class="map-oath">\u201cMen tantanali qasam ichamanki, hech qanday yaxshilik qilmayman\u201d</div>'+
      mks+figs+'</div>';
  }else{inner='<div class="world-empty">Xarita hozircha yopiq.</div>';}
  body.innerHTML='<div class="map-toolbar"><div class="map-sels">'+chips+'</div>'+
    '<button class="map-toggle'+(wMarauder?' on':'')+'" id="mrd">\\uD83D\\uDC63 Marauder rejimi</button></div>'+inner+
    '<div class="map-legend">Joy ustiga bosing \u2014 tavsif. Izlar vakillik (iconic) joylashuv.</div>';
  var mrd=document.getElementById('mrd');if(mrd)mrd.onclick=function(){wMarauder=!wMarauder;var w=document.getElementById('mapwrap');if(w)w.classList.toggle('marauder',wMarauder);this.classList.toggle('on',wMarauder);};
  Array.prototype.forEach.call(body.querySelectorAll('.mapsel'),function(b){b.onclick=function(){if(b.className.indexOf('locked')>=0)return;wState.map=b.getAttribute('data-map');worldRenderBody();};});
  Array.prototype.forEach.call(body.querySelectorAll('.map-mk'),function(b){b.onclick=function(){wState.detail='loc:'+b.getAttribute('data-loc');worldRenderBody();};});}
function wLocDetailHTML(ix){var M=WORLD.map,mp=null,i;for(i=0;i<M.maps.length;i++){if(M.maps[i].id===wState.map){mp=M.maps[i];break;}}
  var l=(mp&&mp.locations)?mp.locations[+ix]:null;if(!l)return '<div class="world-empty">Topilmadi.</div>';
  var key='loc-'+wState.map+'-'+ix;
  if(wLocked(l.book,key)){return '<button class="wd-back" data-back="1">\\u2039 Orqaga</button>'+
    '<div class="wd-hero" style="background:linear-gradient(150deg,#6b4a22,#3a2a12)"><div class="wd-ic">\\uD83D\\uDD12</div><h3>Spoiler himoyasi</h3><div class="wd-tag">Bu joy '+l.book+'-kitobda ochiladi</div></div>'+
    '<p class="wd-desc">Bu maskan haqidagi ma\\u02bblumot '+l.book+"-kitobda ochiladi.</p>"+
    '<div class="wd-rel"><button data-reveal-loc="'+key+'">Baribir ko\\u02bbrsatish</button></div>';}
  var rel='';if(l.ref){var r=wById(l.ref);if(r)rel='<div class="wd-rel-t">Bog\\u02bbliq maqola</div><div class="wd-rel"><button data-id="'+l.ref+'">'+esc(r.name)+' \u2192</button></div>';}
  return '<button class="wd-back" data-back="1">\\u2039 Orqaga</button>'+
    '<div class="wd-hero" style="background:linear-gradient(150deg,#7a5a2a,#3a2a12)"><div class="wd-ic">\\uD83C\\uDFF0</div><h3>'+esc(l.name)+'</h3><div class="wd-tag">'+esc(l.tag)+'</div></div>'+
    '<div class="wd-meta"><span class="wd-chip">Joy</span><span class="wd-chip">Birinchi: '+l.book+'-kitob</span></div>'+
    '<p class="wd-desc">'+esc(l.desc)+'</p>'+rel;}

// ===== Atmosfera: ambient canvas portal =====
(function(){
  var c=document.getElementById('bg');if(!c){return;}var ctx=c.getContext('2d');
  var reduce=!!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches);
  var DPR=Math.min(window.devicePixelRatio||1,2);
  var W=0,H=0,parts=[],raf=0,paused=false,px=0,py=0,tx=0,ty=0;
  function cssVar(n,f){var v=getComputedStyle(document.documentElement).getPropertyValue(n);return (v&&v.trim())||f;}
  function toRGBA(hex,a){hex=(hex||'').replace('#','');if(hex.length===3){hex=hex.charAt(0)+hex.charAt(0)+hex.charAt(1)+hex.charAt(1)+hex.charAt(2)+hex.charAt(2);}
    var r=parseInt(hex.substr(0,2),16),g=parseInt(hex.substr(2,2),16),b=parseInt(hex.substr(4,2),16);
    if(isNaN(r)){return 'rgba(123,17,19,'+a+')';}return 'rgba('+r+','+g+','+b+','+a+')';}
  function spawn(rand){return{x:Math.random()*W,y:rand?Math.random()*H:H+8*DPR,r:(Math.random()*1.5+0.5)*DPR,s:(Math.random()*0.45+0.12)*DPR,ph:Math.random()*6.283,sp:Math.random()*0.018+0.004,a:Math.random()*0.45+0.18};}
  function build(){var n=Math.round(Math.min(110,Math.max(26,(window.innerWidth*window.innerHeight)/16000)));if(reduce){n=Math.min(n,36);}parts=[];for(var i=0;i<n;i++){parts.push(spawn(true));}}
  function paint(){var bg=cssVar('--bg','#faf8f3'),ac=cssVar('--accent','#7b1113');
    ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);
    var g=ctx.createRadialGradient(W*0.5,H*0.08,0,W*0.5,H*0.08,Math.max(W,H)*0.75);
    g.addColorStop(0,toRGBA(ac,0.12));g.addColorStop(1,toRGBA(ac,0));ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    tx+=(px-tx)*0.05;ty+=(py-ty)*0.05;
    for(var i=0;i<parts.length;i++){var p=parts[i];var fl=0.55+0.45*Math.sin(p.ph*2);
      ctx.beginPath();ctx.arc(p.x+tx,p.y+ty,p.r,0,6.283);ctx.fillStyle=toRGBA(ac,p.a*fl);ctx.fill();}}
  function frame(){for(var i=0;i<parts.length;i++){var p=parts[i];p.y-=p.s;p.ph+=p.sp;p.x+=Math.sin(p.ph)*0.3*DPR;if(p.y<-8*DPR){parts[i]=spawn(false);}}paint();raf=requestAnimationFrame(frame);}
  function start(){if(raf||paused){return;}if(reduce){paint();return;}raf=requestAnimationFrame(frame);}
  function stop(){if(raf){cancelAnimationFrame(raf);raf=0;}}
  function resize(){DPR=Math.min(window.devicePixelRatio||1,2);c.width=Math.floor(window.innerWidth*DPR);c.height=Math.floor(window.innerHeight*DPR);W=c.width;H=c.height;c.style.width=window.innerWidth+'px';c.style.height=window.innerHeight+'px';build();paint();}
  var rz;window.addEventListener('resize',function(){clearTimeout(rz);rz=setTimeout(resize,180);});
  document.addEventListener('visibilitychange',function(){if(document.hidden){stop();}else if(!paused){start();}});
  if(!('ontouchstart' in window)){window.addEventListener('pointermove',function(e){var cx=window.innerWidth/2,cy=window.innerHeight/2;px=(e.clientX-cx)/cx*8*DPR;py=(e.clientY-cy)/cy*8*DPR;});}
  window.Portal={pause:function(){paused=true;stop();c.style.display='none';},resume:function(){paused=false;c.style.display='';start();},repaint:function(){if(reduce||!raf){paint();}}};
  resize();start();
})();

var savedTheme='day';try{savedTheme=localStorage.getItem('gp_library_theme')||'day';}catch(e){}
buildThemePop();applyTheme(savedTheme);render();
(function(){var m=/kitob-(\\d+)/.exec(location.hash);if(m){openBook(+m[1]);}})();
"""
    js = js.replace("__BOOKS__", books_json).replace("__CREST__", crest)
    js = js.replace("__GLOSS__", gloss_json).replace("__WORLD__", world_json)
    js = js.replace("__MAPARTS__", json.dumps(maparts, ensure_ascii=False))
    js = js.replace("__MAPDECO__", json.dumps(mapdeco, ensure_ascii=False))
    js = (js.replace("__HOUSES__", houses_json)
            .replace("__QUIZ__", quiz_json)
            .replace("__T__", uitext_json))
    doc = (
        '<!DOCTYPE html>\n<html lang="uz" data-theme="day">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n'
        '<meta name="theme-color" content="#7b1113" id="mtc">\n'
        '<meta name="description" content="Garri Potter \u2014 o\'zbekcha elektron kutubxona. 8 kitob, premium o\'quvchi.">\n'
        '<link rel="icon" type="image/svg+xml" href="' + FAVICON + '">\n'
        '<title>Garri Potter \u2014 Kutubxona</title>\n<style>' + css + '</style>\n</head>\n<body>\n'
        '<canvas id="bg" aria-hidden="true"></canvas>\n'
        '<div id="themepop" class="theme-pop"></div>\n'
        '<div class="wrap" id="lib">\n'
        '<header class="top"><span class="logo">'
        + crest
        + '<h1>Garri Potter<small>O\'zbekcha kutubxona \u00b7 8 kitob</small></h1></span>'
        '<span class="actions">'
        '<button class="theme-btn" id="worldbtn" title="Sehrli Olam" '
        'aria-label="Sehrli Olam \u2014 ensiklopediya">' + world_svg + '</button>'
        '<button class="theme-btn" id="hatbtn" title="Saralash Qalpoqchasi" '
        'aria-label="Saralash Qalpoqchasi">' + hat_svg + '</button>'
        '<button class="theme-btn" id="themebtn" title="Mavzu" aria-label="Mavzu">\u25d0</button>'
        '</span></header>\n'
        '<div class="hero" id="hero"></div>\n'
        '<div id="housechip"></div>\n'
        '<div class="section-title">Barcha kitoblar</div>\n'
        '<div class="grid" id="grid"></div>\n'
        '<footer>J.K. Rouling \u00b7 o\'zbek tilidagi tarjima \u00b7 Premium o\'quvchi</footer>\n'
        '</div>\n'
        '<div id="hatmodal" class="hat-overlay" hidden></div>\n'
        '<div id="worldmodal" class="hat-overlay" hidden></div>\n'
        '<iframe id="viewer" hidden title="O\'qish oynasi"></iframe>\n'
        + reader_shell_block + '\n'
        + data_blocks + '\n'
        '<script>\n' + js + '\n</script>\n</body>\n</html>\n'
    )
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)


def main():
    head = read(os.path.join(BASE, "head.html"))
    chrome_top = read(os.path.join(BASE, "chrome_top.html"))
    chrome_bot = read(os.path.join(BASE, "chrome_bottom.html"))
    app_js = read(os.path.join(BASE, "app.js"))
    part2_js = read(os.path.join(BASE, "part2.js"))
    app_js, part2_js = patch_engine(app_js, part2_js)

    summary = []
    chapters_map = {}
    shell = build_shell(head, chrome_top, chrome_bot, app_js, part2_js)
    for b in BOOKS:
        ch_html, nch, nw = build_chapters(b)
        chapters_map[b["n"]] = ch_html
        summary.append(dict(n=b["n"], key=b["key"], title=b["title"], sub=b["sub"],
                            accent=b["accent"], chapters=nch, words=nw,
                            gloss=(b["n"] != 8)))
        print("kitob-%d  %-20s  boblar=%-3d  so'z=%-7d  %d KB"
              % (b["n"], b["title"], nch, nw, len(ch_html) // 1024))
    build_single(summary, shell, chapters_map)
    sz = os.path.getsize(os.path.join(ROOT, "index.html"))
    print("index.html (yagona self-contained fayl): %.2f MB" % (sz / 1048576))
    return summary

if __name__ == "__main__":
    main()
