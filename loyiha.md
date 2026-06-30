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

> Ochiq masala: qo'lyozmada ayrim atamalar hali aralash yozilgan
> (Xogvars/Xogvarts, Voldemort/Volan-de-Mort, Vaqt Chig'irig'i/Vaqt aylanasi,
> Jinna/Jinni). Bular uslub tatbiqi davomida bob-bob kanonik shaklga keltiriladi;
> istalsa, butun kitob bo'yicha bir martalik birxillashtirish ham mumkin.
