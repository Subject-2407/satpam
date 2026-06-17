# Speaker Notes (Humanized) — Narasi 10 Menit Proposal SATPAM

---

## Slide 1 — Judul (0:00–0:50)

Selamat pagi, Pak/Bu. Terima kasih atas kesempatan ini.

Hari ini saya ingin mempresentasikan sebuah proposal sistem yang saya namai **SATPAM** — *Search-based AI Threat Prevention and Mapping*. Nama ini saya pilih sengaja, karena idenya memang mirip satpam sungguhan: dia tidak menghakimi sendiri, tapi juga tidak tinggal diam. Dia melihat, mencatat, memetakan, lalu melaporkan ke yang berwenang.

Secara teknis, SATPAM adalah sistem berbasis *graph intelligence* yang membantu mendeteksi dan memetakan risiko pada ekosistem judi online dan pinjaman online ilegal. Yang penting untuk saya tekankan sejak awal — ini bukan sistem yang langsung memblokir atau menindak. Ini adalah *decision-support tool* untuk analis manusia.

---

## Slide 2 — Latar Belakang / Urgensi (0:50–1:55)

Sebelum kita bicara solusi, izinkan saya dulu menunjukkan seberapa besar masalahnya.

Data PPATK tahun 2025 mencatat perputaran dana judi online di Indonesia mencapai **Rp286,84 triliun** — dengan **422 juta lebih transaksi** dan **12,3 juta orang** yang terlibat melalui bank, e-wallet, dan QRIS.

Angka itu bukan sekadar statistik. Itu berarti ada jutaan orang yang mungkin juga menjadi target pinjaman online ilegal setelahnya. Dan yang membuat masalah ini rumit adalah: semuanya tersebar di banyak kanal — ada domain web, nomor WhatsApp, rekening bank, QRIS, APK, sampai kiriman di media sosial. Kalau kita analisis satu per satu secara terpisah, kita tidak akan pernah melihat pola jaringannya secara utuh.

Di situlah urgensi SATPAM muncul.

---

## Slide 3 — Sistem yang Ada & Gap-nya (1:55–2:55)

Tentu saja, Indonesia tidak mulai dari nol. Sudah ada banyak pihak yang bekerja di ruang ini.

Komdigi menangani pemblokiran konten digital. OJK dan Satgas PASTI mengawasi aktivitas keuangan ilegal. IASC menyediakan kanal laporan penipuan transaksi. PPATK menganalisis aliran dana mencurigakan. Dan tentu kepolisian yang mengeksekusi penegakan hukum.

Jadi pertanyaannya: *kalau sudah ada semua itu, apa yang kurang?*

Yang kurang adalah **peta hubungan antar-entitas lintas sistem**. Setiap lembaga kuat di domainnya masing-masing, tapi data mereka jarang tersambung. SATPAM tidak ingin menggantikan siapapun. Yang ingin dilakukan hanyalah: *menghubungkan titik-titik yang belum tersambung* — link ini ke domain mana, domain itu terhubung ke nomor apa, nomor itu muncul di rekening yang mana, dan apakah rekening atau APK itu pernah dilaporkan sebelumnya.

---

## Slide 4 — Rumusan Masalah (2:55–3:50)

Dari konteks tadi, ada lima pertanyaan yang ingin dijawab oleh SATPAM.

Pertama, bagaimana merancang sistem AI berbasis *graph search* untuk memetakan ekosistem judol-pinjol ilegal secara terpadu?

Kedua, bagaimana menghubungkan berbagai sumber data — laporan, domain, nomor WhatsApp, rekening, APK, hingga blacklist — ke dalam satu *graph database*?

Ketiga, bagaimana menerapkan algoritma pencarian seperti **BFS** untuk menemukan jalur bukti, dengan UCS, Bi-Directional Search, dan A* sebagai opsi lanjutan?

Keempat, bagaimana menghitung skor risiko dan menentukan prioritas tindakan secara terstruktur?

Dan kelima, bagaimana menyajikan semua itu dalam bentuk yang bisa dipahami dan diverifikasi oleh analis manusia?

Itulah kelima rumusan masalah yang menjadi pondasi SATPAM.

---

## Slide 5 — Solusi yang Diusulkan: SATPAM (3:50–4:55)

Sekarang mari kita lihat bagaimana SATPAM menjawab masalah tadi.

Alurnya dimulai dari **input multi-sumber**: bisa dari laporan masyarakat, *crawler finding* dari sumber publik yang legal dan berizin, indikator transaksi simulasi, blacklist dummy, atau data APK simulasi.

Dari sana, sistem melakukan **entity extraction** — mengambil elemen-elemen penting seperti URL, domain, nomor kontak, rekening, QRIS, e-wallet, dan APK. Entitas-entitas ini kemudian dinormalisasi dan disusun menjadi sebuah **graph**.

Di atas graph inilah kecerdasan buatan bekerja. BFS digunakan untuk menelusuri *evidence path*, lalu *rule-based risk scoring* menghitung seberapa berisiko sebuah entitas. A* bisa dipakai sebagai opsi lanjutan jika heuristik sudah jelas.

Hasilnya ditampilkan di dashboard sebagai kandidat prioritas. Dan saya perlu tegaskan: hasil *high* atau *critical* hanya menjadi **kandidat blacklist**, bukan pemblokiran otomatis. Keputusan akhir tetap di tangan manusia.

---

## Slide 6 — Arsitektur Sistem (4:55–6:00)

Kalau kita lihat arsitekturnya secara lebih teknis, SATPAM terdiri dari **empat lapisan**.

Lapisan pertama adalah **Input** — ini adalah pintu masuk data: form laporan, API, import dataset dummy, crawler finding, dan log transaksi simulasi.

Lapisan kedua adalah **Ingestion & Processing** — di sinilah data divalidasi, diekstrak entitasnya, dinormalisasi, dideduplicate, lalu dibangun menjadi graph.

Lapisan ketiga, yang paling inti, adalah **Intelligence Core** — menggunakan Neo4j sebagai graph database, BFS dan rule-based scoring sebagai metode utama, ditambah modul *early warning* dan *explanation engine*.

Dan lapisan terakhir adalah **Dashboard & Verification Workflow** — di sinilah analis melihat graph, skor risiko, cluster jaringan, dan rekomendasi, sebelum melakukan verifikasi manual.

Empat lapisan ini bekerja berurutan, tapi dirancang agar setiap tahapnya bisa diaudit.

---

## Slide 7 — Metode & Workflow (6:00–7:05)

Untuk prototype, saya memilih pendekatan yang realistis sekaligus aman secara etika.

**Semua data yang digunakan adalah data dummy atau simulasi.** Ini penting karena kita tidak ingin ada risiko kebocoran informasi sensitif dalam lingkungan pengembangan.

Pipeline-nya berjalan seperti ini: data masuk → validasi → entity extraction berbasis regex dan rule sederhana → normalisasi dan pseudonymisasi jika data sensitif → deduplicate → graph builder membuat node dan relasi.

Setelah graph terbentuk, **BFS menjadi metode utama** untuk menemukan koneksi terdekat dan *evidence path* antar entitas. Sementara UCS, Bi-Directional Search, dan A* diposisikan sebagai **opsi lanjutan** — baru relevan ketika bobot edge, cost, dan heuristik sudah terdokumentasi dengan baik.

Output akhirnya adalah: *risk score*, penjelasan alasan, *early warning*, dashboard visual, dan proses review oleh manusia.

---

## Slide 8 — Inovasi & Novelty (7:05–8:05)

Lalu, apa yang membuat SATPAM berbeda dari sistem yang sudah ada?

Kuncinya ada pada **perubahan cara pandang** terhadap masalah ini.

Selama ini banyak sistem bekerja secara *entity-based* — satu entitas dicek, lalu dilabeli. SATPAM mengusulkan pendekatan **network-based intelligence**: yang penting bukan hanya siapa entitasnya, tapi *bagaimana dia terhubung* dengan yang lain.

Ada lima poin novelty. Pertama, **graph intelligence** yang menyatukan entitas digital dan finansial. Kedua, **search-based risk path** yang membuat hasil deteksi bisa ditelusuri jejaknya. Ketiga, **judol-pinjol linkage detection** — sistem ini mencoba melihat apakah ada pola bahwa korban kerugian judol kemudian menjadi target tawaran pinjol ilegal. Keempat, **risk scoring berbasis relasi** untuk menentukan prioritas. Kelima, **explainable detection** — sistem tidak hanya memberi label "berisiko", tapi juga menjawab *kenapa*.

Dan yang mengikat semuanya: **human-in-the-loop**. Sistem hanya memberi kandidat dan alasan, keputusan akhir tetap di tangan manusia yang bertanggung jawab.

---

## Slide 9 — Manfaat & Roadmap (8:05–9:10)

Secara praktis, apa yang bisa diharapkan dari prototype SATPAM?

Sistem ini membantu analis untuk **memprioritaskan kasus** — bukan lagi melihat satu per satu laporan secara acak, tapi berdasarkan skor dan kluster jaringan. Analis juga bisa **memahami evidence path** dengan jelas: kenapa entitas A dianggap berisiko, apa hubungannya dengan B dan C? Dan karena semua keputusan masih diverifikasi manusia, risiko salah tafsir akibat *over-reliance* pada AI bisa diminimalkan.

Untuk roadmap-nya, saya membaginya ke dalam **lima fase**: pertama, foundation dan schema data; kedua, data ingestion dan graph builder; ketiga, search dan scoring; keempat, dashboard dan verification; dan kelima, testing dan demo.

Dengan roadmap ini, SATPAM tetap kompetitif secara teknologi, tanpa *overclaim* — karena semua data di prototype adalah dummy dan sistem tidak melakukan pemblokiran otomatis.

---

## Slide 10 — Penutup & Referensi (9:10–10:00)

Sebagai penutup, kalau saya harus meringkas SATPAM dalam lima kata saja, kata itu adalah:

**Detect. Map. Explain. Prioritize. Verify.**

Kelima kata itu mencerminkan cara SATPAM memandang masalah judol-pinjol ilegal — bukan sebagai kumpulan entitas terpisah, tapi sebagai **jaringan yang saling terhubung**.

Kontribusi utama proposal ini ada pada upaya menyatukan laporan publik, *crawler finding*, indikator transaksi, blacklist, *graph search*, *risk scoring*, dan dashboard prioritas — semua dalam satu konsep yang *explainable* dan tetap menghormati peran manusia sebagai pengambil keputusan akhir.

Referensi utama berasal dari dokumen PPATK, Komdigi, OJK/IASC, dokumentasi resmi Neo4j, serta jurnal acuan tentang web scraping dan text mining untuk deteksi judi online, graph database untuk fraud detection, cybersecurity knowledge graph, CTI graph, explainable fraud detection, dan human-in-the-loop feedback.

Dokumen SRS dan proposal SATPAM tetap menjadi basis rancangan sistem, sedangkan jurnal-jurnal tersebut menguatkan alasan kenapa pendekatan SATPAM memakai entity extraction, graph intelligence, evidence path, explainable scoring, dan verifikasi manusia.

Terima kasih. Saya siap menerima pertanyaan atau masukan dari Bapak/Ibu.

---

> **Catatan untuk presenter:** Kalau ada pertanyaan soal *kenapa BFS* yang dipilih sebagai metode utama — jawabannya bisa dikaitkan dengan sifat graph judol-pinjol yang cenderung *unweighted* pada tahap awal. BFS cocok untuk menemukan jalur terpendek dalam konteks ini sebelum bobot relasi didefinisikan lebih formal.
