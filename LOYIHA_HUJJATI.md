# LOYIHA HUJJATI: Pyesadan Roman Formatiga Aylantirish

## MAQSAD

"Harry Potter va La'natlangan Bola" pyesasini (I va II qism) bitta uzluksiz roman holiga keltirish.
Natijada kitob xuddi Harry Potter seriyasining 8-kitobidek o'qilishi kerak.

---

## MANBA FAYLLAR

Repository: `drzafarjonovic/Kitob`

1. **7.Garri Potter va ajal tuhfalari.pdf** — Uslub (Style Guide). Kirill yozuvida.
2. **8.Garri Potter va La'natlangan bola 1-qism (1).pdf** — Pyesa I qism (Akt 1-2). Lotin yozuvida.
3. **Garri Potter va La'natlangan bola 2-qism@GARRIPOTTER8.pdf** — Pyesa II qism (Akt 3-4). Lotin yozuvida.

---

## NATIJA FAYL

`Garri_Potter_va_Lanatlangan_Bola_Roman.txt` — Bitta uzluksiz roman fayli (lotin yozuvida)

---

## QANDAY QILINMOQDA

### 1. PDF dan matn chiqarish

PDF fayllar maxsus font encoding (CID/ToUnicode CMap) ishlatadi. Standart kutubxonalar (pymupdf, pdftotext) mavjud emas.
**Yechim:** Pure Python PDF parser yozildi:
- CMap jadvallarini parse qilish
- Har bir sahifadagi BT/ET bloklaridan matn chiqarish
- Tm (text matrix) orqali x,y koordinatalarni aniqlash
- cm (concatenate matrix) transformlarni hisoblash
- Y koordinata bo'yicha qatorlarga guruhlash
- X koordinata bo'yicha belgilar orasidagi bo'shliqni aniqlash

**Matn chiqarish kodi:**
```
python3 script — PDF ni o'qib, text/ papkaga saqlaydi
- text/part1.txt (La'natlangan bola 1-qism)
- text/part2.txt (La'natlangan bola 2-qism)
```

Eslatma: text/ papkasi git ga qo'shilmagan. Har sessiyada qayta chiqarish kerak.

### 2. Uslub tahlili

Harry Potter va Ajal Tuhfalari (7-kitob) uslubi tahlil qilindi:
- **Bob boshlanishi:** Joy + atmosfera tavsiri bilan boshlanadi
- **Dialog:** Tire (—) bilan boshlanadi, "dedi X" attributsiya bilan
- **Tasvir:** Boy — atrof-muhit, hid, tovush, yorug'lik
- **Ichki monolog:** Erkin oqim, qahramon fikrlari bevosita
- **Paragraflar:** 3-6 jumla
- **O'tishlar:** Yumshoq, mantiqiy
- **Jang sahnalari:** Qisqa jumlalar, tez harakat
- **Hissiyot:** Ichki kechinmalar orqali

### 3. Bob tuzilmasi

`bob_rejasi.md` faylida 27 bob rejalashtirilgan:
- Pyesadagi 4 akt (~75 parda/saxna) → 27 bob
- Har bir bob mantiqan yaxlit voqealar ketma-ketligi
- Har bir bob 1000-3000 so'z (pyesadagi material hajmiga qarab)

### 4. Roman yozish tartibi

Har bir bob uchun:
1. Pyesa matnini to'liq o'qish (text/part1.txt yoki text/part2.txt)
2. Barcha dialoglarni 100% saqlab qolish
3. Sahna ko'rsatmalarini (remarka) tasvir va ichki monologga aylantirish
4. Joy, muhit, kayfiyat tasvirini qo'shish
5. Dialog orasiga tana harakatlari, pauzalar, hissiyotlar qo'shish

---

## HOZIRGI HOLAT (yangilangan: 30-iyun 2026)

### Tekshiruvdan o'tdi. Tuzatish boshlandi.

**Bajarilgan tuzatishlar:**
- ✅ XI bob kengaytirildi (406 → 767 so'z)

**Navbatdagi tuzatishlar (prioritet bo'yicha):**
1. XVII bob kengaytirish (849 so'z) — Akt3, 3-5 pardalar qo'shish (Drako Vazir, Kutubxona, Damlamalar xonasi)
2. XXV bob kengaytirish (730 so'z) — Garri Volan-de-Mort qiyofasiga kirish dialoglari to'liq yozish
3. XXVI bob kengaytirish (767 so'z) — Delfi bilan uchrashish dialoglari (parseltong, uchish, "Ota")
4. XXVII bob kengaytirish (701 so'z) — Qurbonlik sahnasi, yakuniy Sedrik qabri dialoglari
5. IV bob kengaytirish (614 so'z) — Germiona bilan dialog to'liq qo'shish
6. XIV bob kengaytirish (870 so'z) — Makgonagal xarita sahnasi qo'shish
7. XVI bob kengaytirish (860 so'z) — Garri-Mirtl dialogi qo'shish
8. XXII bob kengaytirish (390 so'z) — Vokzal sahnasi muhit tasviri qo'shish

**TEXNIK ESLATMA:** text/ papkasi git ga qo'shilmagan. Har sessiyada qayta chiqarish kerak (yuqoridagi Python skript). Hozir `text/part2.txt` mavjud, lekin commit qilinmagan.

---

## ESKI HOLAT

### Yozilgan boblar (I-X):

| # | Bob nomi | Pyesa manbasi | Holat |
|---|----------|---------------|-------|
| I | Kings Kross | Akt1, Parda 1-2 (part1, qator 14-139) | ✅ |
| II | Xogvars Ekspressi | Akt1, Parda 3 (part1, qator 140-237) | ✅ |
| III | Saralovchi Shlyapa | Akt1, Parda 4 (part1, qator 238-372) | ✅ |
| IV | Sehrgarlik Vazirligi | Akt1, Parda 5 (part1, qator 465-547) | ✅ |
| V | Ota va o'g'il | Akt1, Parda 6-7 (part1, qator 548-729) | ✅ |
| VI | Tush va uyg'onish | Akt1, Parda 8-9 (part1, qator 730-839) | ✅ |
| VII | Xogvars Ekspressida qochish | Akt1, Parda 10-11 (part1, qator 840-989) | ✅ |
| VIII | Muqaddas Osvald uyi | Akt1, Parda 12-14 (part1, qator 990-1125) | ✅ |
| IX | Qidiruv | Akt1, Parda 15-17 (part1, qator 1126-1280) | ✅ |
| X | Germionaning kabineti | Akt1, Parda 18-19 + O'n Beshinchi (part1, qator 1281-1520) | ✅ |

### Yozilmagan boblar (XI-XXVII):

| # | Bob nomi | Pyesa manbasi |
|---|----------|---------------|
| XI | Birinchi tush | Akt2, Parda 1-2 (part1, qator 1521-1578) |
| XII | Qidiruv va Taqiqlangan o'rmon | Akt2, Parda 3-6 (part1, qator 1579-1781) |
| XIII | Uch afsungar bellashuvi, 1994-yil | Akt2, Parda 7-8 (part1, qator 1782-1983) |
| XIV | O'zgargan dunyo | Akt2, Parda 9-13 (part1, qator 1984-2231) |
| XV | Ikkinchi urinish | Akt2, Parda 14-17 (part1, qator 2232-2527) |
| XVI | Garri va Dambldor | Akt2, Parda 18-20 (part1, qator 2528-2979) |
| XVII | Qorong'u dunyo | Akt3, Parda 1-5 (part2, qator 13-284) |
| XVIII | Muqobil dunyoda kurash | Akt3, Parda 6-9 (part2, qator 285-642) |
| XIX | Haqiqatga qaytish | Akt3, Parda 10-13 (part2, qator 643-844) |
| XX | Delfi sirlari | Akt3, Parda 14-16 (part2, qator 845-1076) |
| XXI | Germiona kabinetida | Akt3, Parda 17-19 (part2, qator 1077-1263) |
| XXII | Uchinchi vazifa | Akt3, Parda 20-21 (part2, qator 1264-1504) |
| XXIII | Godrik Jarligiga qaytish | Akt4, Parda 1-3 (part2, qator 1505-1682) |
| XXIV | Garri va Drako | Akt4, Parda 4-6 (part2, qator 1683-1957) |
| XXV | Godrik Jarligida jang | Akt4, Parda 7-9 (part2, qator 2042-2191) |
| XXVI | Avliyo Jeremi cherkovi | Akt4, Parda 10-11 (part2, qator 2192-2520) |
| XXVII | Qurbonlik | Akt4, Parda 12-15 (part2, qator 2521-oxiri) |

---

## KEYINGI SESSIYA UCHUN KO'RSATMA

Agar yangi sessiya boshlansa:

1. **Avval text fayllarni qayta chiqarish kerak** (text/ papkasi git da yo'q):
   - part1.txt va part2.txt ni PDF lardan chiqarish (yuqoridagi Python skript)

2. **Hozirgi roman faylini o'qish:**
   - `Garri_Potter_va_Lanatlangan_Bola_Roman.txt` — hozirgi natija

3. **Keyingi bobni yozish:**
   - Yuqoridagi jadvaldan keyingi yozilmagan bobni topish
   - part1.txt yoki part2.txt dan tegishli qatorlarni o'qish
   - Roman formatida yozish (barcha dialog va voqealarni saqlab)
   - Asosiy faylga qo'shish

4. **Push qilish:**
   - `git add -A && git commit -m "XI-... boblar" && push to main`

---

## MUHIM QOIDALAR

1. Pyesadagi voqealar ketma-ketligi 100% saqlanadi
2. Dialoglar 100% saqlanadi (faqat formatlanadi)
3. Hech qanday yangi syujet qo'shilmaydi
4. Hech qanday voqea qisqartirilmaydi
5. Hech qanday voqea o'zgartirilmaydi
6. Faqat yozilish shakli o'zgaradi (pyesa → roman)
7. Uslub — HP Ajal Tuhfalari kitobiga mos
8. Til — O'zbek (Lotin yozuvi)
9. Dialog — tire (—) bilan boshlanadi
10. Personaj ismlari katta harf bilan yozilmaydi (faqat gap boshida)

---

## TEXNIK MA'LUMOTLAR

- **Repository:** drzafarjonovic/Kitob
- **Branch:** main
- **PDF parser:** Pure Python (re, zlib modullari). Network cheklangan — pip install ishlamaydi.
- **Font:** PDF larda CID font + ToUnicode CMap ishlatiladi
- **Encoding:** Part 1-2 lotin (4-byte hex per glyph), Ajal Tuhfalari kirill (1-byte per glyph)
