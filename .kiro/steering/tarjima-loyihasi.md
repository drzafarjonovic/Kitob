---
inclusion: always
---

# Cursed Child tarjima loyihasi — MAJBURIY QOIDA

Bu repoda «Harry Potter and the Cursed Child» romanini o'zbekchaga tarjima qilish
loyihasi olib borilmoqda. Foydalanuvchi "tarjimani davom et" (yoki "davom et") desa
YOKI tarjima bilan bog'liq har qanday ish qilinsa, quyidagi qoidalar SO'ZSIZ amal qiladi:

## 1. Avval master hujjatni o'qi
Har doim birinchi bo'lib **`Tarjima/HOLAT.md`** faylini to'liq o'qi. So'ng
`Tarjima/01_Lugat.md` va `Tarjima/02_Style_Guide.md` ni o'qi. Loyihaning barcha
qoidalari, qarorlari, ish tartibi va qayerda to'xtaganimiz aynan shu fayllarda.
Kelgan joydan (jadvaldagi birinchi ⬜/🔄 bobdan) davom et.

## 2. O'zgarmas tamal qarorlar
- **Alifbo:** KIRILL (lotin emas).
- **Yagona uslubiy manba:** `Garri Potter kitoblari/` (1–7 kitoblar).
- **🚫 QAT'IY TAQIQ:** `La'natlangan Bola/`, `Garri Potter kitoblari/8 - La'natlangan Bola/`
  va `arxiv/` — eski tarjima. Ochilmaydi, o'qilmaydi, manba qilinmaydi.
- Terminlar faqat `Tarjima/01_Lugat.md` dan; yangi termin 7 kitobdan `grep` bilan
  tekshiriladi, topilmasa konventsiya bo'yicha qilinib lug'atga qo'shiladi.

## 3. Sifat va usul HECH QACHON o'zgarmaydi
Tarjima sifati, uslubi, terminologiyasi va ish usuli avvalgi boblar bilan bir xil
bo'lishi shart. `HOLAT.md` dagi «HAR BIR BOB UCHUN ANIQ ISH TARTIBI» va sifat
nazorati bosqichlariga to'liq amal qil.

## 4. Har qadamdan keyin — to'liq holatni yozib bor
Har bir tugallangan ishdan (har bob yoki har o'zgarishdan) so'ng:
- **Premium reader'ni qayta qur:** `python3 Tarjima/build_reader.py` (barcha tayyor
  boblarni `Tarjima/Garri_Potter_va_Lanatlangan_Bola.html` o'quvchisiga yig'adi —
  foydalanuvchi shuni o'qiydi). Toza `boblar/Bob_NN.html` — tarjima manbai.
- `Tarjima/HOLAT.md` ni TO'LIQ yangila: «BOBLAR HOLATI» jadvali, «HOZIRGI HOLAT»
  va «BAJARILGAN ISHLAR LOG» (nima va qanday qilingani batafsil).
- Keyin `main` branchiga commit qilib, github power `push_to_remote` bilan push qil
  (to'g'ridan-to'g'ri `git push` ishlamaydi).

## 5. Muloqot
Chatda minimal yoz. Ish tugagach qisqa "tayyor" de. Foydalanuvchi "davom et" deganda
keyingi bobni boshla.
