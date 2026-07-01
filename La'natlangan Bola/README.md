# Garri Potter va La'natlangan Bola

Bu papka Harry Potter seriyasining 8-asari — **"Garri Potter va La'natlangan Bola"**
(J.K. Rouling, Jon Tiffani, Jek Torn) bilan bog'liq **barcha materiallarni** bir
joyda, tartibli saqlaydi. Asl asar sahna asari (pyesa) ko'rinishida yozilgan va bu
yerda uni to'laqonli **romanga** aylantirish loyihasining manba, natija, hujjat va
skriptlari jamlangan.

## Papka tuzilishi

```
La'natlangan Bola/
├── 01-pyesa/        Asl pyesa (manba)
├── 02-roman/        Romanga aylantirilgan natija
├── 03-hujjatlar/    Loyiha hujjatlari va rejalar
└── 04-skriptlar/    PDF ekstraktor va generator skriptlar
```

### 01-pyesa/ — Asl pyesa (manba)
Asarning asl, sahna asari (pyesa) ko'rinishi — lotin alifbosida.

| Fayl | Tavsif |
|------|--------|
| `Pyesa - 1-qism (Akt 1-2).pdf` | Pyesaning I qismi (Akt 1–2), PDF. |
| `Pyesa - 2-qism (Akt 3-4).pdf` | Pyesaning II qismi (Akt 3–4), PDF. |
| `part1.txt` | I qismning PDF'dan chiqarilgan (extract) matni. |
| `part2.txt` | II qismning PDF'dan chiqarilgan (extract) matni. |

### 02-roman/ — Romanga aylantirilgan natija
Pyesadan yaratilgan to'laqonli badiiy roman va uni o'qish uchun formatlar.

| Fayl | Tavsif |
|------|--------|
| `Garri_Potter_va_Lanatlangan_Bola_Roman.txt` | **Asosiy natija** — roman matni (lotin alifbosida). |
| `Garri_Potter_va_Lanatlangan_Bola.pdf` | Romanning chop etishga tayyor PDF varianti. |
| `Garri_Potter_va_Lanatlangan_Bola_old_reader.html` | Romanning eski, mustaqil HTML o'quvchisi (arxiv). |

> Eslatma: roman matni ayni shu ko'rinishda seriya o'quvchisiga ham
> `Garri Potter kitoblari/8 - La'natlangan Bola/matn.txt` sifatida qo'shilgan.
> Asosiy `index.html` o'quvchi ilovasi shu seriya papkasidan generatsiya qilinadi.

### 03-hujjatlar/ — Loyiha hujjatlari
Loyihaning maqsadi, reja va tekshiruv natijalari.

| Fayl | Tavsif |
|------|--------|
| `loyiha.md` | Loyihaning umumiy tavsifi va maqsadi. |
| `LOYIHA_HUJJATI.md` | Batafsil loyiha hujjati (manba/natija fayllar, jarayon). |
| `bob_rejasi.md` | Roman boblarining pyesa pardalariga moslashtirilgan rejasi. |
| `TEKSHIRUV_NATIJASI.md` | Roman va pyesa mosligini tekshirish natijalari. |

### 04-skriptlar/ — Skriptlar
Sof Python (tashqi kutubxonasiz) yordamchi skriptlar.

| Fayl | Tavsif |
|------|--------|
| `extract_pdf.py` | PDF matn ekstraktori (cm/Tm matritsa, Identity-H). |
| `extract_pdf2.py` | 1-bayt va 2-bayt (Type0/CID) fontlarni qo'llovchi ekstraktor. |
| `extract_pdf_simple.py` | Oddiy TrueType (1-baytli) fontlar uchun ekstraktor. |
| `make_html.py` | Roman `.txt` → o'qishga moslangan mustaqil HTML. |
| `make_pdf.py` | Roman `.txt` → chop etishga tayyor PDF. |

## Skriptlardan foydalanish

`extract_pdf*.py` skriptlari PDF yo'lini argument sifatida oladi, masalan:

```bash
python3 "04-skriptlar/extract_pdf2.py" "01-pyesa/Pyesa - 1-qism (Akt 1-2).pdf"
```

`make_html.py` va `make_pdf.py` esa manbani `02-roman/Garri_Potter_va_Lanatlangan_Bola_Roman.txt`
dan o'qib, natijani shu `02-roman/` papkasiga yozadi:

```bash
python3 "04-skriptlar/make_html.py"
python3 "04-skriptlar/make_pdf.py"
```
