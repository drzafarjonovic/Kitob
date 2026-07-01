# HOLAT — Loyiha Master Hujjati (Progress + Workflow + Log)

> ⚠️ **YANGI SESSIYA / YANGI AI UCHUN:** Bu fayl loyihaning YAGONA to'liq manbai.
> Repoga ulanib "davom et" deyilsa, boshqa hech narsa so'ramasdan quyidagini bajar:
> 1) Shu faylni to'liq o'qi. 2) `01_Lugat.md` va `02_Style_Guide.md` ni o'qi.
> 3) Quyidagi «BOBLAR HOLATI» jadvalidan birinchi ⬜ (yoki 🔄) bobni top.
> 4) «HAR BIR BOB UCHUN ANIQ ISH TARTIBI» bo'limi bo'yicha o'sha bobni tarjima qil.
> Sifat, uslub, terminologiya va usul HECH QACHON o'zgarmasligi shart.

---

## 1. LOYIHA MAQSADI
`Harry_Potter_and_the.html` (Harry Potter and the Cursed Child pyesasining
romanlashtirilgan **inglizcha** versiyasi; manba: AO3, muallif "BoleynC") ni
**o'zbek tiliga, KIRILL alifbosida** shunday tarjima qilish — natija Garri Potter
seriyasining **rasmiy 8-kitobi** kabi o'qilsin. O'quvchi tarjimani emas, original
o'zbekcha Garri Potter kitobini o'qiyotgandek his qilishi kerak.

## 2. TAMAL QARORLAR (hech qachon o'zgarmaydi)
- **Alifbo:** KIRILL (foydalanuvchi tasdiqladi — variant A). Lotin ISHLATILMAYDI.
- **Yagona uslubiy manba:** faqat `Garri Potter kitoblari/` ichidagi **1–7 kitoblar**
  (kirill, `matn.txt`). Uslub, terminologiya, ismlar, ohang — hammasi shulardan olinadi.
- **🚫 QAT'IY TAQIQ (hech qachon ochilmaydi/o'qilmaydi/manba qilinmaydi):**
  - `La'natlangan Bola/` papkasi (eski romanlashtirilgan tarjima)
  - `Garri Potter kitoblari/8 - La'natlangan Bola/`
  - `arxiv/` (Ajal Tuhfalari matni va b.)
  Bu materiallarga qarash ham mumkin emas.
- **Ritm:** bobma-bob. Har bob alohida `.html` fayl (`boblar/Bob_NN.html`).
- **Bob nomlari:** o'zbekchaga o'giriladi (Act=парда, Scene=саҳна, Part=қисм,
  "and a Half"=«ярим», "Three Quarters"=«чорак»).
- **Git workflow:** har bir tugallangan qadamdan (har bob + har o'zgarishdan) keyin
  `main` branchiga commit + `push_to_remote` (github power) bilan push. To'g'ridan-to'g'ri
  `git push` ISHLAMAYDI (auth yo'q) — github power `push_to_remote` ishlatiladi.
- **Chatda minimal yozish.** Ish tugagach qisqa "tayyor" deyiladi; foydalanuvchi
  "davom et" deganda keyingi bob boshlanadi.
- **Har qadamdan keyin shu HOLAT.md to'liq yangilanadi** (jadval + LOG bo'limi).

## 3. MANBA TUZILMASI VA BOBNI QANDAY AJRATISH
- Manba fayl: `Harry_Potter_and_the.html` (~1.9MB, ~280k so'z, inglizcha).
- **4 ta Akt, 77 ta bob.** Har bobning HTML tuzilmasi:
  ```
  <div class="meta group">
    <h2 class="heading"> Chapter N: ... </h2>
    ...
  <!--chapter content-->
  <div class="userstuff">
    <p>...</p><p>...</p>   <-- ASOSIY BADIIY MATN SHU YERDA
  </div>
  <!--/chapter content-->
  ```
- **Bobni ajratish usuli:** `grep -n 'class="heading"'` bilan bob sarlavhalari
  qatorlarini top; N-bobning matni N-chi `<!--chapter content-->` dan keyingi
  `<div class="userstuff">` bloki (keyingi `<!--/chapter content-->` gacha).
  Matnni `read_file` (offset/limit) bilan o'qi. Bir bob ~4–8k so'z, `<p>` teglari
  uzun satrlarda joylashgan.
- **Bob boshlari (qator raqami, ma'lumot uchun):** Bob 1 sarlavhasi ~76-qatorda;
  har bobda `<h2 class="heading">` bor. Ajratishda har safar grep bilan aniqla
  (qator raqamlari o'zgarmagan bo'lsa ham tekshir).

## 4. NATIJA TUZILMASI (`Tarjima/` papkasi)
| Fayl | Mazmun |
|---|---|
| `HOLAT.md` | Shu master hujjat (progress + workflow + log) |
| `00_Uslub_tahlili.md` | 7 kitob uslub tahlili |
| `01_Lugat.md` | Terminologik lug'at (o'zgarmas; yangi terminlar qo'shiladi) |
| `02_Style_Guide.md` | Tarjima uslub qo'llanmasi |
| `boblar/Bob_01.html` … `Bob_77.html` | Tarjima qilingan boblar (toza manba matn) |
| `build_reader.py` | Premium reader quruvchi skript. (1) standalone o'quvchini yig'adi; (2) index.html'ga 9-KITOB sifatida qo'shadi/yangilaydi (eski 8-kitobga tegmaydi) |
| `patch_index_storage.py` | BIR MARTALIK skript: index.html'ga saqlash ko'prigini o'rnatadi (progress mobil brauzerlarda ham ishlashi uchun — top-sahifa orqali localStorage) |
| `Garri_Potter_va_Lanatlangan_Bola.html` | ⭐ standalone PREMIUM READER (reader-shell asosida; har bobdan keyin qayta quriladi) |

## 5. HAR BIR BOB UCHUN ANIQ ISH TARTIBI (aynan shunday bajarilsin)
1. `01_Lugat.md` + `02_Style_Guide.md` ni yodga ol.
2. Manbadan navbatdagi bob matnini ajratib, `read_file` bilan **to'liq** o'qi.
3. Bobda uchraydigan **maxsus terminlarni** (yangi ism/joy/sehr/buyum) `01_Lugat.md`
   dan tekshir. Lug'atda bo'lmasa — **7 kitobdan `grep` bilan qidir** (kirill
   shakllarni sina). Topilsa aynan o'sha shaklni ol; topilmasa konventsiya bo'yicha
   transliteratsiya/tarjima qilib, `01_Lugat.md` ga qo'sh (🔧 belgi bilan).
4. **Faylni bo'laklab yoz** (MUHIM texnik qoida): bitta katta `fs_write` UZILIB
   qoladi. Shuning uchun:
   - avval `fs_write` bilan HTML skeletini yoz (head + `<h2 class="heading">` bob
     nomi + ochilgan `<div class="userstuff">`),
   - so'ng matnni `fs_append` bilan **bir necha qismda** (~15–20 `<p>` dan) qo'sh,
   - oxirida `fs_append` bilan `</div></div></body></html>` ni yop.
5. **Dialog/uslub qoidalari** (`02_Style_Guide.md` dan):
   - Gapiruvchi replika `<p>` ichida `— ` (tire+probel) bilan boshlanadi.
   - Muallif izohi tire bilan: `— ..., — деди Скорпиус, ...`
   - Izoh fe'llari xilma-xil: деди, сўради, хитоб қилди, ғудранди, пичирлади…
   - Ichki fikr/urg'u: «...» yoki `<em>...</em>`.
   - Ingliz `"..."`/`'...'` → o'zbekcha «...».
6. **Sifat nazorati (har bob yakunida majburiy):**
   - `grep -oE "<p>" | wc -l` — manba `<p>` soniga yaqin bo'lsin (hech narsa tushmasin).
   - `+++` sahna ajratgichlari soni manbadagidek saqlansin.
   - Lug'at terminlari to'g'ri ishlatilganini `grep` bilan tekshir; xato/eski
     terminlar (масалан «Хогвартс», «қум соатча», «тарафдорлари») **0** bo'lsin.
   - Mazmun to'liq, personaj ovozi izchil, grammatika/imlo toza.
7. `HOLAT.md` da bobni ✅ belgila, «Joriy holat» va «LOG» ni yangila.
8. **HAR BOB 3 JOYGA SAQLANADI:**
   - (a) `Tarjima/boblar/Bob_NN.html` — bob tarjimasi (toza manba matn; yuqorida yozildi).
   - (b) `python3 Tarjima/build_reader.py` ni ishga tushir — bitta skript qolgan IKKI joyni
     avtomatik yangilaydi: **standalone o'quvchi** `Tarjima/Garri_Potter_va_Lanatlangan_Bola.html`
     va **`index.html` kutubxonasidagi 9-kitob** (bookdata-9 + BOOKS n:9 + COVERS).
   - Tekshir: standalone'da `@@` placeholder 0; `index.html`da 9 ta bookdata skript va
     eski 8-kitob (`gp_reader_b8`) joyida turibdi.
9. `HOLAT.md` ni yangila: «HOZIRGI HOLAT» (tayyor N/77 + satr holati), «BOBLAR HOLATI»
   jadvalida bobni ✅ qil, «LOG» ga yozuv qo'sh.
10. `git add` (`boblar/Bob_NN.html` + `Garri_Potter_va_Lanatlangan_Bola.html` + `index.html`
    + `Tarjima/HOLAT.md` + o'zgargan bo'lsa `01_Lugat.md`) → `git commit`
    → github power `push_to_remote` (`main`).
11. Qisqa "tayyor" deb bildir.

> ℹ️ **Premium reader haqida:** har bob toza `boblar/Bob_NN.html` sifatida yoziladi
> (tarjima manbai). `build_reader.py` ularni (a) standalone o'quvchi
> `Garri_Potter_va_Lanatlangan_Bola.html` ga va (b) `index.html` kutubxonasiga **9-kitob**
> sifatida yig'adi (eski 8-kitobga TEGILMAYDI). Foydalanuvchi ilovadan (index.html) 9-kitobni
> ochib o'qiydi. Unda mavzular, qidiruv, xatcho'p, izoh, Lotin/Kirill almashtirish, bob
> navigatsiyasi bor. Reader kirill matnini canonical saqlaydi.
>
> ⚙️ **Progress/saqlash (MUHIM):** reader `srcdoc` iframe ichida ishlaydi; mobil brauzerlar
> (iOS Safari) srcdoc iframega null-origin berib localStorage'ni bloklaydi. Shuning uchun
> saqlash TOP-sahifa (kutubxona) orqali amalga oshiriladi: reader progressni `postMessage`
> bilan yuboradi, kutubxona o'z localStorage'iga yozadi; kitob ochilганда saqlangan holat
> readerga inject qilinadi (`window.__GP_SAVED__`). Bu ko'prik `patch_index_storage.py` bilan
> BIR MARTA o'rnatilgan. **Muhim:** o'quvchi haqiqiy manzildan (masalan GitHub Pages `https`)
> ochilishi kerak — GitHub "blob"/manba ko'rinishida JS umuman ishlamaydi.

---

## 6. HOZIRGI HOLAT

**Joriy bosqich:** 4 (Bobma-bob tarjima). **Tayyor boblar: 4/77.**

| Bosqich | Holat |
|---|---|
| 0. Papka + HOLAT.md | ✅ |
| 1. Uslub tahlili (`00_Uslub_tahlili.md`) | ✅ |
| 2. Lug'at (`01_Lugat.md`) | ✅ (tasdiqlangan; tarjima davomida kengaytiriladi) |
| 3. Style Guide (`02_Style_Guide.md`) | ✅ |
| Foydalanuvchi tasdig'i (0–3) | ✅ |
| 4. Bobma-bob tarjima | 🔄 4/77 |
| 5. Yakuniy yig'ish | ⬜ |

**📍 SATRMA-SATR HOLAT (manba `Harry_Potter_and_the.html`):**
- Tarjima qilingan: **1–4-boblar** = manba satrlari **84–158** (Bob 1: 84–86, Bob 2: 105–107, Bob 3: 130–133, Bob 4: 156–158).
- Oxirgi tarjima qilingan manba satri: **158** (Bob 4 `userstuff` oxiri; `/chapter content` marker 159-satrda).
- To'liq satr xaritasi — pastdagi «BOBLAR HOLATI» jadvalida (har bob uchun aniq satrlar).

**➡️ KEYINGI QADAM:** `Bob_05` — «Act One: Scene Four Part Four» → «5-боб. Биринчи парда, тўртинчи саҳна, тўртинчи қисм».
- Manba satrlari: **userstuff 181–188** (markerlar 180–189).
- Ajratish: 5-chi `<!--chapter content-->` blokini `read_file` (offset≈179) bilan o'qi.

---

## 7. BAJARILGAN ISHLAR LOG (to'liq tarix — nima va qanday qilingani)

### 2026-07-01 — 0–3 bosqichlar (tayyorgarlik)
- **0.** `Tarjima/` papkasi va shu `HOLAT.md` yaratildi.
- **1.** `00_Uslub_tahlili.md`: 7 kitobdan (b1 ochilishi, b3 vaqt chig'irig'i sahnasi,
  b4 Diggorilar dialogi) namunalar o'qilib, uslub aniqlandi — kirill imlo (Ў Қ Ғ Ҳ +
  ruscha ж ц щ ъ ь ё э), boy/sifatlashli rivoyat, tire bilan dialog, «...» va `...`.
- **2.** `01_Lugat.md`: terminlar 7 kitobdan `grep` bilan tekshirib qulflandi.
  Tasdiqlangan asosiylari: Хогварц, Хогсмёд, Гриффиндор/Слизерин/Равенкло/Хуффльпуфф,
  Гарри/Рон Уэсли/Гермиона Грэнжер/Дамблдор/Снегг/Вольдеморт/Реддл, Альбус Северус,
  Драко, Седрик/Амос Диггори, Жинни(Жинни), Квидиш, Сайёди, портшлюс, галлеон,
  Кўринмас плаш, магл, сеҳрли таёқча, супурги, аврор, дементор, Қақнус ордени, патронум,
  sehrlar (Экспеллиармус, Ступефай, Люмос, Авада Кедавра, Империо, Круцио, Экспекто патронум).
- **3.** `02_Style_Guide.md`: dialog/tinish/ohang/QC qoidalari yozildi.
- Hammasi `main`ga push qilindi.

### 2026-07-01 — Foydalanuvchi terminologik tuzatishlari (7 kitobdan tasdiqlangan)
- **Time-Turner** → «вақт чиғири» (b3: «Буни вақт чиғири, деб аташади»). (Eski «қум соатча» bekor qilindi.)
- **Death Eater** → «Ўлимдан мириқувчи(лар)» (7 kitobda yuzlab marta).
- **Snitch** → «Тилла чаққон».
- **Dark Mark** → «Ажал белгиси» (~60 marta).
- 7 kitobda YO'Q — konventsiya bo'yicha qulflangan (foydalanuvchi "o'zing qaror qil" dedi):
  Скорпиус, Роза, Хьюго, Астория, Дельфи/Дельфини; Бладжер, Квоффл, Урувчи (Beater),
  Ҳужумчи (Chaser), Дарвозабон (Keeper).

### 2026-07-01 — Bob 1 tarjimasi (`boblar/Bob_01.html`) ✅
- **Nima:** 1-bob to'liq tarjima qilindi — «1-боб. Биринчи парда: биринчи, иккинчи ва
  учинчи саҳналар». Mazmun: Alьbusning ichki iztirobi va oila munosabatlari (Гарри,
  Жинни, Жеймс, Лили, tog'a-xolalar), Хогварцга jo'nash (Кингс Кросс, to'siqdan o'tish),
  poyezdda Roza bilan suhbat va **Скорпиус bilan tanishuv** sahnasi.
- **Qanday:** Bob 1 uchun qo'shimcha terminlar 7 kitobdan tekshirilib lug'atga qo'shildi
  (Сараловчи шляпа, Катта Зал, мадам Трюк=Madam Hooch, назоратчи=prefect, шоколадли бақа;
  🔧: «Хогварц экспресси», умумий хона, Портловчи қарталар, Қора Лорд, сквиб, Малфойлар қасри).
  Fayl skeleti `fs_write` bilan, matn `fs_append` bilan 11 qismda yozildi (katta `fs_write`
  uzilgani sabab). Dialog tire bilan, fikrlar «...»/`<em>` bilan.
- **Nazorat natijasi:** 249 `<p>` (manba ~248 — hech narsa tushmagan), 6 ta `+++`,
  barcha terminlar lug'atga mos, xato terminlar 0.
- **Push:** `main` (commit «1-bob tarjima qilindi …»).

### 2026-07-01 — Premium reader qo'shildi (foydalanuvchi talabi) ✅
- **Nima:** Boblar endi `main/index.html` dagi premium o'quvchi (reader-shell) bilan
  o'qiladi — qulay o'qish uchun. Natija: `Tarjima/Garri_Potter_va_Lanatlangan_Bola.html`.
- **Qanday:** `Tarjima/build_reader.py` skripti yozildi. U `index.html` dan reader-shell
  shablonini ajratadi (escaped `<\/script>` → `</script>`), `boblar/Bob_*.html` larni
  o'qib, har birini `<section class="chapter">` ga aylantiradi, placeholderlarni
  (@@TITLE@@, @@SUB@@, @@ACCENT@@, @@CHAPTERS@@, @@BOOKCFG@@) to'ldiradi va o'quvchini yozadi.
  `+++` sahna ajratgichlari bezakli `✦ ✦ ✦` ga aylantirildi.
- **Muhim:** har yangi bobdan keyin `python3 Tarjima/build_reader.py` qayta ishga tushiriladi
  (workflow 8-qadam). Toza `boblar/Bob_NN.html` — manba; reader — yig'ilgan natija.
- **Reader imkoniyatlari:** mavzular (kunduz/tun/…), qidiruv, xatcho'p, izoh, o'qish jarayoni,
  Lotin/Kirill almashtirish (kirill canonical), bob navigatsiyasi.
- **Nazorat:** placeholderlar 0, 1 bob, `<!DOCTYPE html>`…`</html>` butun.
- **Push:** `main`.

### 2026-07-01 — Bob 2 tarjimasi (`boblar/Bob_02.html`) ✅
- **Nima:** 2-bob to'liq tarjima — «2-боб. Биринчи парда, тўртинчи саҳна, биринчи қисм».
  Mazmun: Сараланиш маросими (Катта Зал, сузиб юрган шамлар), Роза → Гриффиндор,
  Скорпиус → Слизерин, Альбус кутилмаганда → Слизерин (шляпа билан ички суҳбат),
  Слизерин умумий хонаси ва ётоқхона (Малфойлар қасри, товуслар), уриш дарси —
  Альбус супургисини кўтара олмайди («слизеринлик сквиб»).
- **Qanday:** Manba 104–108-qatorlar (userstuff). Skelet `fs_write`, matn `fs_append`
  bilan 5 qismda. Terminlar tekshirildi; kanon tuzatishlari: Madam Hooch = «Трюк хоним»
  (b1), broom "Up!" = «Тур!» (b1) — lug'atga qo'shildi. Squib = «сквиб» (🔧),
  Dark Wizard = «қора сеҳргар», Exploding Snap = «Портловчи қарталар».
- **Nazorat:** 128/128 `<p>` (manba bilan aynan mos), 4 ta `+++`, terminlar to'g'ri,
  xato terminlar 0.
- **Reader:** `build_reader.py` qayta ishga tushirildi → 2 bob, placeholderlar 0.
- **Push:** `main`.

### 2026-07-01 — Premium reader progress tuzatildi + 9-kitob qo'shildi (foydalanuvchi talabi) ✅
- **Muammo:** reader `srcdoc` iframe ichида ishлаганида progress bar/davom etish/localStorage
  mobil brauzerlarda (iOS Safari srcdoc null-origin) ishlamаган.
- **Yechim:** saqlash TOP-sahifa (kutubxona) zиммасига o'tkazildi. `patch_index_storage.py`
  (bir martalik) index.html'ga ko'prik o'rnатди: reader Store.saveRaw → `postMessage({__gp:"save"})`
  → kutubxona localStorage'ига yozади; kitob ochilганда saqlangan holat readerга inject qилинади
  (`window.__GP_SAVED__` → shell'да `@@SAVED@@` placeholder). Top-origin localStorage barcha
  muhitда (https, hatto file:// top-level) ishлайди. Qoʻshimcha: patch_index_idb.py reader-shellga IndexedDB zaxira qatlamini qoʻshdi — localStorage bloklangan yoki file:// holatlarda ham progress saqlanadi (additiv, himoyalangan). Standalone oʻquvchi toʻliq offline (tashqi resurs yoʻq): Chromeда file:// bilan ochilganda ham progress/davom etish ishlaydi.
- **9-kitob:** `build_reader.py` endi tarjimамизни index.html'га **9-kitob** sifatida
  qo'шади/yangilaйди (BOOKS n:9, bookdata-9, COVERS 9). **Eski 8-kitоб (gp_reader_b8)
  TEGILMАДИ** — saqlaнди. 9-kitob key: `gp_reader_b9`.
- **build_reader.py yangilanди:** standalone o'quvchи (`@@SAVED@@`→null) + index.html 9-kitob
  create-or-update. Har bobдан keyin ishga tushириlади.
- **Nazorat:** index.html — 9 bookdata skript, BOOKS n:9 to'g'ri, massив `}]` bilan yopiladi,
  eski 8-kitob joyida, fayl butun. Standalone — placeholderlar 0, 3 bob.
- **Push:** `main`.

### 2026-07-01 — Bob 3 tarjimasi (`boblar/Bob_03.html`) ✅
- **Nima:** 3-bob to'liq tarjima — «3-боб. Биринчи парда, тўртинчи саҳна, иккинчи қисм».
  Bu — muallifning o'zi qo'shgan "filler" bob (birinchi yil davomida Альбус va Скорпиус
  do'stligi, taъna-dashnom, ovqat/kutubxona/fan haqidagi suhbat, Роза bilan uzoqlashish,
  otalar munosabati, yil oxiri va platformada vidolashuv, Драко paydo bo'lishi).
  Bosh qismidagi muallif izohi (blockquote — hikoya emas) tarjima QILINMADI.
- **Qanday:** Manba 130–133-qatorlar (userstuff). Skelet + 3 qism `fs_append`.
  Kanon tekshiruvi: History of Magic = «Сеҳргарлик тарихи» (b1, 46 marta) — lug'atga qo'shildi.
  restricted section = «тақиқланган бўлим» (🔧), geek = «китобхўр» (🔧).
- **Nazorat:** 72/72 `<p>` (aynan mos), 4 ta `+++`, terminlar to'g'ri, xato terminlar 0.
- **Reader:** `build_reader.py` → 3 bob, placeholderlar 0.
- **Push:** `main`.

### 2026-07-01 — Bob 4 tarjimasi (`boblar/Bob_04.html`) ✅
- **Nima:** 4-bob to'liq tarjima — «4-боб. Биринчи парда, тўртинчи саҳна, учинчи қисм».
  Bu ham muallif qo'shgan "roman" bob — Альбуснинг **иккинчи йили** (bir yil qamrab
  oladi). Mazmun: Кингс Кросс платформасида отаси Гарри билан оғриқли суҳбат («мендан
  нарироқ туринг», «Гарри Поттернинг слизеринлик ўғли»), Жеймснинг мазаху ҳайдаши,
  Роза билан совуқ видолашув (қон-қариндошлик, «маглвачча» ҳақорати, садоқат),
  Скорпиуснинг келиши; Розанинг «Гриффиндор»га Ҳужумчи бўлиши ва Макгонагаллнинг
  бир тарафлама мақтови; дамламалар тайёрлаш дарсидаги фалокат (Полли Чапман, Карл
  Женкинс таъналари, қозон портлаши); Альбуснинг ўсиб-улғайиши ва ўқишдаги ютуқлари
  (Гербология, Сеҳргарлик тарихи — Скорпиус ёрдамида); Скорпиус онасининг бетоблиги;
  йил охирида поездда сукунат ва платформада Драконинг ўғлига меҳри. Bosh qismidagi
  muallif izohi (blockquote «Chapter Notes» — hikoya emas) tarjima QILINMADI.
- **Qanday:** Manba 156–158-qatorlar (userstuff). Skelet `fs_write` + matn 7 qismda
  `fs_append`. **Kanon tekshiruvi (7 kitobdan grep):** Mudblood = «маглвачча»
  (b2: «жирканч маглвачча»), Potions class = «дамламалар тайёрлаш дарси» (b1, 10 marta),
  potion = «дамлама», cauldron = «қозон», Herbology = «Гербология», Neville Longbottom =
  «Невилль/Лонгботтом», Aunt Angelina = «Ангелина хола» (b2 imlosi «Ангелина»),
  owl post = «укки почтаси». 🔧: Полли Чапман, Карл Женкинс, Тезакбомба (Dungbomb),
  бикорн шохи, саламандра қони. Barchasi lug'atga qo'shildi.
- **Nazorat:** 114/114 `<p>` (aynan mos), 7 ta `+++` (manbadek), 3/3 `<em>`, terminlar
  to'g'ri, xato/eski terminlar 0, matnda lotin harf yo'q.
- **Reader:** `build_reader.py` → 4 bob (~13989 so'z), standalone placeholderlar 0,
  index.html 9 bookdata skript, eski 8-kitob (gp_reader_b8) joyida.
- **Push:** `main`.

---

## 8. BOBLAR HOLATI (77 bob)
Belgilar: ⬜ boshlanmagan · 🔄 jarayonda · ✅ tayyor+nazoratdan o'tgan+push

> **Manba satrlari** = `Harry_Potter_and_the.html` dagi o'sha bobning `userstuff`
> bloki (tarjima qilinadigan asosiy matn). Bob N ni ajratish: N-chi
> `<!--chapter content-->` / `<!--/chapter content-->` markerlari orasi.

| # | Bob (inglizcha sarlavha) | Manba satrlari (userstuff) | Holat |
|---|---|---|---|
| 1 | Act One: Scenes One, Two, and Three | 84–86 | ✅ `boblar/Bob_01.html` |
| 2 | Act One Scene Four Part One | 105–107 | ✅ `boblar/Bob_02.html` |
| 3 | Act One: Scene Four Part Two | 130–133 | ✅ `boblar/Bob_03.html` |
| 4 | Act One: Scene Four Part Three | 156–158 | ✅ `boblar/Bob_04.html` |
| 5 | Act One: Scene Four Part Four | 181–188 | ⬜ |
| 6 | Act One: Scene Four Part Five | 211–225 | ⬜ |
| 7 | Act One: Scene Five | 248–252 | ⬜ |
| 8 | Act One: Scene Six | 275–277 | ⬜ |
| 9 | Act One: Scene Seven | 300–302 | ⬜ |
| 10 | Act One: Scenes Eight and Nine | 325–331 | ⬜ |
| 11 | Act One: Scene Ten | 354–356 | ⬜ |
| 12 | Act One: Scene Eleven | 379–384 | ⬜ |
| 13 | Act One: Scene Eleven and a Half | 407–409 | ⬜ |
| 14 | Act One: Scene Twelve | 432–434 | ⬜ |
| 15 | Act One: Scenes Thirteen and Fourteen | 457–459 | ⬜ |
| 16 | Act One: Scene Fifteen | 482–484 | ⬜ |
| 17 | Act One: Scene Sixteen | 507–511 | ⬜ |
| 18 | Act One: Scene Eighteen | 534–538 | ⬜ |
| 19 | Act One: Scene Nineteen | 561–577 | ⬜ |
| 20 | Act Two: Scene Four | 600–602 | ⬜ |
| 21 | Act Two: Scenes Six and Seven | 625–651 | ⬜ |
| 22 | Act Two: Scene Eight | 674–678 | ⬜ |
| 23 | Act Two: Scene Nine | 700–702 | ⬜ |
| 24 | Act Two: Scene Eleven | 725–727 | ⬜ |
| 25 | Act Two: Scene Twelve | 750–754 | ⬜ |
| 26 | Act Two: Scene Twelve and a Half | 777–797 | ⬜ |
| 27 | Act Two: Scene Thirteen | 820–822 | ⬜ |
| 28 | Act Two: Scene Fourteen | 845–847 | ⬜ |
| 29 | Act Two: Scene Fifteen | 870–876 | ⬜ |
| 30 | Act Two: Scene Sixteen | 899–901 | ⬜ |
| 31 | Act Two: Scene Eighteen | 924–928 | ⬜ |
| 32 | Act Two: Scene Nineteen | 951–953 | ⬜ |
| 33 | Act Two: Scene Twenty | 976–986 | ⬜ |
| 34 | Act Three: Scene 0.5 | 1009–1017 | ⬜ |
| 35 | Act Three: Scene One | 1040–1044 | ⬜ |
| 36 | Act Three: Scene Two | 1067–1077 | ⬜ |
| 37 | Act Three: Scene Three | 1100–1102 | ⬜ |
| 38 | Act Three: Scene Three and a Half | 1125–1127 | ⬜ |
| 39 | Act Three: Scene Four | 1149–1163 | ⬜ |
| 40 | Act Three: Scene Five | 1186–1188 | ⬜ |
| 41 | Act Three: Scenes Six and Seven | 1211–1213 | ⬜ |
| 42 | Act Three: Scene Eight | 1236–1244 | ⬜ |
| 43 | Act Three: Scene Nine | 1267–1281 | ⬜ |
| 44 | Act Three: Scene Ten | 1304–1308 | ⬜ |
| 45 | Act Three: Scene Ten and a Half | 1331–1333 | ⬜ |
| 46 | Act Three: Scene Ten and Three Quarters | 1356–1358 | ⬜ |
| 47 | Act Three: Scene Eleven | 1381–1389 | ⬜ |
| 48 | Act Three: Scene Eleven and a Half | 1412–1426 | ⬜ |
| 49 | Act Three: Scene Fourteen | 1449–1455 | ⬜ |
| 50 | Act Three: Scenes Twelve and Thirteen | 1478–1482 | ⬜ |
| 51 | Act Three: Scene Fourteen and a Half | 1505–1513 | ⬜ |
| 52 | Act Three: Scene Fifteen | 1536–1538 | ⬜ |
| 53 | Act Three: Scene Sixteen | 1561–1573 | ⬜ |
| 54 | Act Three: Scene Sixteen and a Half | 1596–1600 | ⬜ |
| 55 | Act Three: Scene Seventeen | 1623–1625 | ⬜ |
| 56 | Act Three: Scene Eighteen | 1648–1650 | ⬜ |
| 57 | Act Three: Scene Nineteen | 1673–1677 | ⬜ |
| 58 | Act Three: Scene Twenty | 1700–1714 | ⬜ |
| 59 | Act Three: Scene Twenty-One | 1737–1741 | ⬜ |
| 60 | Act Four: Scene 0.5 | 1764–1770 | ⬜ |
| 61 | Act Four: Scene One | 1793–1795 | ⬜ |
| 62 | Act Four: Scene Two | 1818–1820 | ⬜ |
| 63 | Act Four: Scene Two and a Half | 1843–1845 | ⬜ |
| 64 | Act Four: Scene Three | 1868–1870 | ⬜ |
| 65 | Act Four: Scene Four | 1893–1907 | ⬜ |
| 66 | Act Four: Scene Five | 1930–1932 | ⬜ |
| 67 | Act Four: Scene Five and a Half | 1955–1957 | ⬜ |
| 68 | Act Four: Scene Six | 1980–1994 | ⬜ |
| 69 | Act Four: Scenes Seven and Eight | 2017–2027 | ⬜ |
| 70 | Act Four: Scene Nine | 2050–2052 | ⬜ |
| 71 | Act Four: Scene Ten | 2075–2077 | ⬜ |
| 72 | Act Four: Scene Eleven | 2100–2106 | ⬜ |
| 73 | Act Four: Scene Twelve | 2129–2147 | ⬜ |
| 74 | Act Four: Scene Thirteen | 2170–2172 | ⬜ |
| 75 | Act Four Scene Thirteen and a Half | 2195–2197 | ⬜ |
| 76 | Act Four: Scene Fourteen | 2220–2224 | ⬜ |
| 77 | Act Four: Scene Fifteen | 2247–2263 | ⬜ |
