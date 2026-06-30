---
inclusion: always
---

# Arxitektura cheklovlari — `index.html`

Bu loyihaning bosh sahifasi `index.html` quyidagi qat'iy cheklovlarga
bo'ysunadi. Har qanday o'zgartirish shu qoidalarni buzmasligi kerak:

## 1. Bitta fayl (single-file)
- BARCHA narsa — HTML, CSS, JS va 8 ta kitob matni — bitta `index.html`
  faylida qolishi shart.
- Kontentni alohida fayllarga ajratish, `fetch`, lazy-load yoki tashqi
  resurslarga bog'lash **TAQIQLANADI**.
- Kitoblar `<script type="text/plain" id="bookdata-N">` bloklarida embedded
  saqlanadi va `iframe.srcdoc` orqali ochiladi.

## 2. PWA / offline kerak emas
- Service worker (`sw.js`), `manifest.json` va PWA bilan bog'liq kod
  ishlatilmaydi. Mavjud dead-code (`navigator.serviceWorker.register`)
  tozalanishi mumkin.

## 3. Generatsiya
- `index.html` `build/gen.py` orqali generatsiya qilinadi. Doimiy
  o'zgarishlar `build/` shablonlarida ham yangilanishi kerak, aks holda
  keyingi build'da yo'qoladi.
