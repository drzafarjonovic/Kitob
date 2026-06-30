# LOYIHA: "Garri Potter va La'natlangan Bola" — pyesadan romanga

## 1. Loyihaning maqsadi

J.K. Rouling, Jon Tiffani va Jek Torn qalamiga mansub **"Garri Potter va
La'natlangan Bola"** asari aslida **sahna asari (pyesa)** ko'rinishida yozilgan:
remarka (sahna ko'rsatmalari) va personajlar dialogidan iborat. Bu loyihaning
maqsadi — o'sha pyesani **to'laqonli badiiy romanga** aylantirish:

- quruq dialoglarni boy nasriy bayonga ko'chirish;
- sahna ko'rsatmalarini tasviriy parchalarga aylantirish;
- personajlarning ichki kechinmalari, atrof-muhit, atmosfera va hissiyotni
  qo'shib, o'quvchini voqea ichiga olib kiradigan roman yaratish.

Hammasi **o'zbek tilida, lotin alifbosida** amalga oshiriladi.

## 2. Manba materiallar

| Fayl | Tavsifi |
|------|---------|
| `text/part1.txt` | Pyesaning I qismi (Akt 1–2). PDF dan chiqarilgan matn. |
| `text/part2.txt` | Pyesaning II qismi (Akt 3–4). PDF dan chiqarilgan matn. |
| `text/Garri_Potter_va_Ajal_Tuhfalari.txt` | **Uslub namunasi.** "Ajal Tuhfalari" romanining o'zbekcha tarjimasi (Shokir Dolimov). Badiiy uslub shu asarga qarab moslanadi. |
| `Garri_Potter_va_Lanatlangan_Bola_Roman.txt` | **Asosiy ish fayli** — yozilayotgan roman. |
| `*.pdf` | Asl manba PDF fayllari. |
| `extract_pdf.py` | PDF dan matn chiqaruvchi sof Python skripti (stdlib, CTM/Tm matritsa interpretatori + `/W` kenglik massivi orqali so'z bo'shliqlarini aniqlash). |

## 3. Roman tuzilishi

- Roman **29 bobdan** iborat (`N BOB. NOMI` ko'rinishidagi sarlavhalar).
- Bob ichidagi sahnalar `* * *` ajratgichi bilan bo'linadi.
- Dialog **uzun tire (—)** bilan beriladi.
- Pyesaning Akt/Parda/Saxna tuzilishi roman boblariga quyidagicha taqsimlangan
  (bir bob bir necha sahnani qamrashi mumkin).

### Boblar ro'yxati
1. Kings Kross
2. Xogvars Ekspressi
3. Saralovchi Shlyapa
4. Sehrgarlik Vazirligi
5. Ota va o'g'il
6. Tush va uyg'onish
7. Xogvars Ekspressida qochish
8. Muqaddas Osvald uyi
9. Qidiruv
10. Germionaning kabineti
11. Voldemortning ovozi
12. Taqiqlangan o'rmon
13. Uch Afsungar Bellashuvi
14. O'zgargan dunyo
15. Ikkinchi urinish
16. Ko'l ostida
17. Qorong'u dunyo
18. Muqobil dunyoda kurash
19. Haqiqatga qaytish
20. Delfi sirlari
21. Labirint
22. Voldemortning qizi
23. Vaqt oralig'ida
24. Shotland balandliklari
25. Godrik Jarligi
26. Ota-onalarning birligi
27. Avliyo Jeremi cherkovi
28. Yakuniy jang
29. Qurbonlik

## 4. Bajarilgan asosiy bosqichlar

### 4.1. PDF dan matn chiqarish
Sandboxda PDF kutubxonalari yo'qligi sababli sof Python (faqat stdlib)
`extract_pdf.py` yozildi va pyesaning ikkala qismi `text/part1.txt`,
`text/part2.txt` ga chiqarildi.

### 4.2. Boblarni kengaytirish
Qisqa qolib ketgan boblar pyesa manbasiga sodiq holda kengaytirildi
(dialoglar va voqealar to'liq qo'shildi).

### 4.3. Tushib qolgan voqealarni tiklash
To'liq tekshiruv natijasida pyesaning **Akt 3, 16–21-sahnalari** butunlay
tushib qolgani aniqlandi va ikki yangi bob bilan to'ldirildi:
- **XXI. Labirint** — Delfining tayoqchalarni sindirishi, Kreygning o'ldirilishi,
  labirint, Sedrikning qutqarishi, Vaqt Chig'irig'ining yo'q qilinishi.
- **XXII. Voldemortning qizi** — Ron-Germiona qayta nikoh, Amos "jiyanim yo'q",
  bashorat devori, Voldemortning qizi fosh bo'lishi.

Shundan so'ng eski boblar qayta raqamlandi; roman 27 bobdan **29 bobga** yetdi.

### 4.4. Badiiy uslubni tatbiq qilish (HOZIRGI BOSQICH)
"Ajal Tuhfalari" namunasidagi boy adabiy uslub butun romanga tatbiq
qilinmoqda. Tafsilotlar uchun pastga qarang.

## 5. Badiiy uslubni tatbiq qilish — metodologiya

Namunaviy uslub tamoyillari `.kiro/steering/uslub.md` faylida to'liq
hujjatlashtirilgan. Qisqacha:

1. **Uzun, ko'p qatlamli jumlalar** — ravishdosh zanjirlari bilan
   (-gancha, -ib, -gach, -arkan, -guncha).
2. **Jonli gap fe'llari** — "dedi" o'rniga: o'kirdi, g'udulladi, xitob qildi,
   ma'lum qildi, entikdi, pichirladi va h.k.
3. **Boy, adabiy lug'at** — rido, bashara, koshona, ko'lanka, yog'du, qa'r...
4. **Sezgi va atmosfera** — yorug'-soya, tovush, harorat, hid doimo tasvirlanadi.
5. **Hissiyotni tana harakati orqali ko'rsatish** ("yuzi toshdek qotdi").
6. **Metafora va o'xshatishlar**.
7. **Erkin ko'chirma gap** (ichki monolog).

### Qat'iy qoidalar
- **Syujet, voqealar ketma-ketligi va dialog mazmuni o'zgartirilmaydi** —
  faqat ifoda boyitiladi.
- **Bob hajmlari sun'iy tenglashtirilmaydi** — har bobning tabiiy o'lchami
  saqlanadi (foydalanuvchi talabi).
- Lotin alifbosi saqlanadi (namuna kirillda bo'lsa-da).
- Yo'l-yo'lakay imloviy xatolar va tasodifiy kirill harflar ham tuzatiladi.

### Ish tartibi
- Boblar **5 tadan** partiyalab qayta ishlanadi.
- **Har partiyadan keyin foydalanuvchidan ruxsat so'raladi.**
- Har partiya alohida commit qilinib, `uslub-tatbiq` branchiga push qilinadi.
- Har partiyadan so'ng kirill harflar tekshiruvi o'tkaziladi.

## 6. Hozirgi holat (uslub tatbiqi bo'yicha)

| Boblar | Holat |
|--------|-------|
| Uslub qo'llanmasi (`.kiro/steering/uslub.md`) | ✅ tayyor |
| I–IV | ✅ tayyor |
| V–IX | ✅ tayyor |
| X–XXIX | ⏳ navbatda |

**Joriy branch:** `uslub-tatbiq`
**Navbatdagi partiya:** X–XIV boblar.

## 7. Ish jarayoni (Git)

- Har o'zgarish alohida, ma'noli commit bilan saqlanadi.
- Ishlar `uslub-tatbiq` branchida olib boriladi va GitHub'ga push qilinadi.
- Tugagach, `main`ga merge qilinadi (foydalanuvchi tasdig'i bilan).
- Repozitoriy: `drzafarjonovic/Kitob`.

## 8. Texnik eslatmalar

- `extract_pdf.py` "La'natlangan Bola" PDF lari (SamsungSans, Identity-H,
  ToUnicode CMap) uchun ishlaydi. "Ajal Tuhfalari" PDF si esa embedded
  TrueType subset font (ToUnicode'siz) bo'lgani uchun u skript bilan
  chiqarilmagan; uning TXT versiyasini foydalanuvchi qo'lda tayyorlab,
  `text/` papkasiga joylagan.



## 9. Davom ettirish (continuity) — "davom et" deyilganda

Loyiha boshqa sessiyada ham uzilishsiz davom etishi uchun:

- `.kiro/steering/uslub.md` fayli **avtomatik yuklanadi** (`inclusion: always`),
  shuning uchun uslub tamoyillari, **atamalar lug'ati**, **konkret namunalar**
  va **to'xtash nuqtasi** har doim ko'z oldida bo'ladi.
- "Davom et" deyilganda ish **X bobdan** (uslub tatbiqi bo'yicha) — yoki
  `uslub.md` dagi "TO'XTASH NUQTASI" bo'limida ko'rsatilgan joydan — davom etadi.
- **Drift (uslubiy/atamaviy tebranish) xavfi** atamalar lug'ati va allaqachon
  o'tkazilgan I–IX boblar yordamida minimallashtirilgan. Eng ishonchli langar —
  shu I–IX boblarning ohangiga monand davom etish.

> Atamalar izchilligi: butun kitob bo'yicha bir martalik birxillashtirish
> bajarildi (Xogvars→Xogvarts, Volan-de-Mort→Voldemort,
> Vaqt aylanasi→Vaqt Chig'irig'i, Jinni→Jinna, Makgonagall→Makgonagal).
> Kanonik shakllar `.kiro/steering/uslub.md` dagi "ATAMALAR LUG'ATI" da.



## 10. Yakuniy bosqich: bitta PDF fayl

**Talab:** barcha boblar badiiy uslubga o'tkazilib bo'lingach, butun roman
**bitta PDF faylga** jamlanadi (chop etishga/tarqatishga tayyor kitob).

### Holat: ✅ BAJARILDI — `make_pdf.py` → `Garri_Potter_va_Lanatlangan_Bola.pdf`
(6x9 dyuymli kitob, 184 sahifa, Times-Roman/Bold WinAnsi, ikki tomonga
tekislash, sarlavha sahifasi, sahifa raqamlari, em-dash 0x97 ga moslangan).

### Texnik reja
Sandboxda PDF vositalari yo'q (`pandoc`, `wkhtmltopdf`, `libreoffice`,
`pdflatex` — hech biri), `pip install` ham ishlamaydi. Shuning uchun PDF
**sof Python (faqat stdlib)** bilan, `extract_pdf.py` dagi PDF bilimiga
tayanib yaratiladi (masalan, `make_pdf.py`):

- Matndagi yagona muhim ASCII bo'lmagan belgi — **uzun tire (—, U+2014)**;
  apostrof oddiy ASCII (`'`). Shu bois standart PDF shrifti
  (Times-Roman, WinAnsiEncoding) yetarli — tire WinAnsi'da `0x97` ga moslanadi.
- Kerak bo'lsa, chiroyliroq ko'rinish uchun TTF (Noto) shrifti ichiga joylanadi.
- PDF tarkibi: sarlavha sahifasi (asar nomi, mualliflar, tarjima izohi),
  boblar (har biri yangi sahifadan, sarlavha + matn), so'z bo'yicha qator
  bo'lish (word-wrap), sahifa raqamlari.
- Natija: `Garri_Potter_va_Lanatlangan_Bola.pdf`.

> Eslatma: chiqarishdan oldin matn yana bir bart kirill harflar va imlo
> bo'yicha tekshiriladi (quyidagi 11-bandga qarang).

## 11. Sifat tekshiruvlari (har doim)

- **Kirill harflar:** `grep -nP "[А-Яа-яЁёҚқҒғҲҳЎў]"` — natija 0 bo'lishi shart.
  (Bir marta butun kitob bo'yicha tozalandi: lotin so'zlar ichiga tushib qolgan
  39 ta tasodifiy kirill harf homoglif sifatida lotinga o'girildi.)
- **Atamalar:** kanonik shakllarga muvofiqligi (5-band va lug'at).
- **Bob butunligi:** 29 ta bob, sarlavhalar va `* * *` ajratgichlari joyida.



## 12. Yakuniy bosqich: HTML kitob (Kindle-ga o'xshash o'quvchi)

**Talab:** barcha boblar uslubga o'tkazilib bo'lingach, romanning **o'qishga
moslangan HTML versiyasi** ham tayyorlanadi — Kindle/elektron kitob o'quvchiga
o'xshash, qulay va oson o'qiladigan qilib.

### Holat: ✅ BAJARILDI — `make_html.py` → `Garri_Potter_va_Lanatlangan_Bola.html`
(mustaqil/self-contained, 332 KB, oflayn ishlaydi; quyidagi barcha
Kindle-ga o'xshash funksiyalar bilan).

### Texnik yondashuv
HTML uchun hech qanday tashqi vosita kerak emas — sof Python skript
(`make_html.py`) roman matnini bitta **mustaqil (self-contained) HTML
faylga** aylantiradi: CSS va JavaScript bevosita fayl ichida bo'ladi
(internetga ulanmasdan, oflayn ishlaydi). Natija:
`Garri_Potter_va_Lanatlangan_Bola.html`.

### Kindle-ga o'xshash funksiyalar
- **Mundarija (TOC):** barcha 29 bobga bosib o'tish; yon panel yoki ochiladigan ro'yxat.
- **Mavzu (tema) almashtirish:** kunduzgi / sepiya / tungi (dark mode) rejimlar.
- **Shrift o'lchamini sozlash:** kattalashtirish/kichraytirish tugmalari.
- **Qulay tipografika:** serif shrift, qulay qator uzunligi (~65–75 belgi),
  kengaytirilgan qator oralig'i, markazlangan o'qish ustuni.
- **O'qish holatini eslab qolish:** oxirgi o'qilgan joy `localStorage` da
  saqlanadi — qayta ochilganda o'sha yerdan davom etadi.
- **O'qish jarayoni ko'rsatkichi:** yuqorida progress-bar va "% o'qildi".
- **Boblar orasida harakat:** Oldingi / Keyingi bob tugmalari, klaviatura
  o'qlari (← →) bilan.
- **Xatcho'p (bookmark):** istalgan joyni belgilab qo'yish (`localStorage`).
- **Qidiruv:** kitob ichidan matn qidirish (ixtiyoriy).
- **Moslashuvchan (responsive):** telefon, planshet va kompyuterda bir xil qulay.

### Yakuniy chiqishlar (umumiy)
| Fayl | Maqsadi |
|------|---------|
| `Garri_Potter_va_Lanatlangan_Bola.txt` | Asosiy manba (tahrir uchun) |
| `Garri_Potter_va_Lanatlangan_Bola.pdf` | Chop etishga tayyor (10-band) |
| `Garri_Potter_va_Lanatlangan_Bola.html` | O'qishga mos, Kindle-ga o'xshash (12-band) |
