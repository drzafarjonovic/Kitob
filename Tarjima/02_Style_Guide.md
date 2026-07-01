# 02 — Style Guide (Tarjima uslub qo'llanmasi)

> Barcha boblar aynan shu qoidalar asosida tarjima qilinadi. Asos: `00_Uslub_tahlili.md`
> va 7 original kitob. Lug'at: `01_Lugat.md`.

## A. Umumiy tamoyil
- O'quvchi **tarjimani emas, original o'zbekcha 8-kitobni** o'qiyotgandek his qilsin.
- **So'zma-so'z emas** — ma'no, kayfiyat, badiiy ta'sir ko'chiriladi.
- Hech bir jumla tushmaydi, hech qanday mazmun qo'shilmaydi yoki qisqartirilmaydi.

## B. Alifbo va imlo
- **Kirill**, o'zbek harflari `Ў Қ Ғ Ҳ` + ruscha `ж ц щ ъ ь ё э` transliteratsiyada.
- Terminlar **faqat `01_Lugat.md` dan**. Yangi termin → avval grep bilan tekshir.

## C. Dialog
- Har replika **yangi qatordan**, boshida **`— ` (tire + probel)**.
- Muallif izohi gap ichida/oxirida tire bilan:
  `— Салом, — деди Скорпиус, кулимсираб.`
  `— Нима бўлди? — сўради Альбус.`
- Izoh fe'llarini xilma-xil qil: **деди, сўради, хитоб қилди, пичирлади, ғудуллади,
  жеркиб берди, такрорлади, эътироз билдирди** — «said» ni bir xil takrorlama.
- Personaj ovozi individual: Skorpius — ziyoli, hazilkash, sertashvish; Albus — g'amgin,
  isyonkor; Garri — vazmin, ba'zan keskin; Draco — takabbur, mag'rur.

## D. Tinish belgilari
- **«...»** — nomlar, jamoalar, kitoblar, iqtiboslar, urg'uli so'zlar uchun.
- `...` — tutilish, hayajon, uzilgan gap.
- Sehrlar undov bilan: **«Экспеллиармус!»**.
- Ingliz tirnoq (`"..."`, `'...'`) → o'zbekcha **«...»** ga.

## E. Rivoyat ohangi
- **O'tgan zamon**, uchinchi shaxs. Sahna remarkalari (pyesadan qolgan) ham **badiiy
  nasr**ga aylantiriladi — quruq "Scene. Harry enters" emas, balki tasvirli jumla.
- Gaplar boy, sifatlashli, hissiy; kinoya yumshoq.
- Temp: dialogda tez va tig'iz; tasvirda sekinroq, tafsilotli.

## F. Hissiyot, yumor, dramatizm
- **Yumor** — so'z o'yini/vaziyat orqali, o'zbekcha tabiiy iboralar bilan (yo'qolmasin).
- **Qo'rquv/dramatizm** — qisqa gaplar, sukut (`...`), zich fe'llar bilan kuchaytiriladi.
- **Ichki monolog** — Garri/Albus his-tuyg'ulari erkin ko'chma nutqda.
- Milliy iboralar: «Мерлин соқоли!», «юраги така-пука», «ранги қув ўчди» — o'rinli qo'llanadi.

## G. Sarlavhalar
- Bob nomi o'zbekchaga: `Chapter 1: Act One: Scenes One, Two, and Three`
  → **«1-боб. Биринчи парда: биринчи, иккинчи ва учинчи саҳналар»**.
- Act = **парда**, Scene = **саҳна**, Part = **қисм**, "and a Half" = **«ярим»**
  (масалан: Scene Eleven and a Half → «ўн биринчи ярим саҳна»).

## H. HTML formati
- Manba tuzilmasi saqlanadi: har bob `<div class="userstuff">`, sarlavha `<h2 class="heading">`,
  matn `<p>` teglarida. CSS/struktura tegilmaydi, faqat matn tarjima qilinadi.
- Havolalar/izohlar (AO3 metadata) tashlanadi; faqat badiiy matn qoldiriladi.

## I. Har bob uchun sifat nazorati (checklist)
1. Lug'atga (`01_Lugat.md`) to'liq mos.
2. Dialog/izoh/tinish qoidalari bajarilgan.
3. Grammatika, imlo, punktuatsiya toza.
4. Personaj nutqi izchil.
5. Hech bir gap tushmagan, mazmun o'zgarmagan.
6. Original 7 kitob ohangiga mos.
7. Yangi terminlar lug'atga qo'shilgan.
