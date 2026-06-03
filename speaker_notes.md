# Speaker Notes - Narasi 10 Menit Proposal SATPAM

## Slide 1 - Title (0:00-0:50)

Selamat pagi/siang. Pada presentasi ini saya mengusulkan **SATPAM**, singkatan dari **Search-based AI Threat Prevention and Mapping**. Ide utamanya adalah membangun sistem AI-assisted berbasis graph intelligence untuk membantu mendeteksi, memetakan, dan memprioritaskan risiko pada ekosistem judi online dan pinjaman online ilegal. SATPAM tidak diposisikan sebagai sistem penindakan otomatis. Sistem ini adalah decision-support untuk analis: membantu melihat hubungan antar entitas, menampilkan jalur bukti, memberi skor risiko, lalu tetap meminta verifikasi manusia sebelum tindakan lanjut.

## Slide 2 - Background / Urgency (0:50-1:55)

Masalah judol dan pinjol ilegal tidak bisa dilihat sebagai masalah satu situs atau satu aplikasi saja. Data PPATK mencatat pada tahun 2025 perputaran dana judol mencapai Rp286,84 triliun, dengan 422,1 juta transaksi dan 12,3 juta orang melakukan deposit melalui bank, e-wallet, dan QRIS. Ini menunjukkan bahwa masalahnya sudah lintas kanal: ada konten promosi, domain, nomor WhatsApp, rekening, QRIS, e-wallet, APK, dan laporan masyarakat. Kalau tiap kanal dianalisis sendiri-sendiri, pola jaringan besarnya sulit terlihat. Di situlah urgensi SATPAM muncul.

## Slide 3 - Existing System and Gap (1:55-2:55)

Indonesia sebenarnya sudah memiliki sistem dan lembaga yang penting. Komdigi menangani konten dan pemblokiran ruang digital, OJK dan Satgas PASTI menangani aktivitas keuangan ilegal, IASC menjadi kanal laporan scam transaksi keuangan, PPATK menganalisis aliran dana mencurigakan, dan kepolisian menangani penegakan hukum. Gap yang ingin diambil SATPAM bukan menggantikan mereka, tetapi menghubungkan potongan data yang tersebar. Sistem existing sering kuat pada domain masing-masing, sedangkan SATPAM menambahkan peta relasi: link ini mengarah ke domain mana, domain terhubung ke nomor apa, nomor terhubung ke rekening mana, dan apakah rekening atau APK itu muncul pada laporan lain.

## Slide 4 - Problem Statement (2:55-3:50)

Rumusan masalahnya dapat diringkas menjadi lima pertanyaan. Pertama, bagaimana merancang sistem AI berbasis graph search untuk memetakan ekosistem judol-pinjol ilegal. Kedua, bagaimana menghubungkan laporan, domain, nomor WhatsApp, rekening, APK, crawler finding, transaksi simulasi, dan blacklist dummy ke dalam satu graph database. Ketiga, bagaimana menerapkan algoritma searching seperti BFS untuk evidence path, dengan UCS, Bi-Directional Search, dan A* sebagai opsi lanjutan untuk menemukan jalur risiko. Keempat, bagaimana menghitung skor risiko dan prioritas tindakan. Kelima, bagaimana hasil itu dijelaskan dalam bentuk path bukti yang mudah dipahami analis.

## Slide 5 - Proposed Solution: SATPAM (3:50-4:55)

SATPAM menjawab masalah tersebut dengan alur multi-sumber. Input dapat berasal dari laporan masyarakat, crawler finding dummy atau scraper publik yang legal dan berizin, indikator transaksi simulasi, blacklist dummy, dan data APK simulasi. Sistem kemudian melakukan entity extraction untuk mengambil URL, domain, nomor, rekening, keyword, QRIS, e-wallet, dan APK. Setelah itu, data dinormalisasi dan dibangun menjadi graph. Di atas graph ini, BFS membantu menelusuri evidence path, rule-based risk scoring menghitung tingkat risiko, dan A* dapat dipakai sebagai opsi lanjutan jika heuristic sudah jelas. Dashboard menampilkan prioritas serta evidence path. Hasil high atau critical hanya menjadi blacklist candidate, bukan blokir otomatis.

## Slide 6 - System Architecture (4:55-6:00)

Arsitektur SATPAM terdiri dari empat lapisan besar. Lapisan pertama adalah input: report form, API, import dataset dummy, crawler finding, traffic log simulasi, dan transaksi simulasi. Lapisan kedua adalah ingestion dan processing: validasi, extraction, normalization, deduplication, dan graph builder. Lapisan ketiga adalah intelligence core: Neo4j sebagai graph database, BFS dan rule-based scoring sebagai inti analisis, serta UCS, BDS, dan A* sebagai opsi lanjutan, ditambah early warning serta explanation engine. Lapisan terakhir adalah dashboard dan verification workflow. Di sini analis melihat graph, skor, cluster, rekomendasi, audit log, dan melakukan human verification.

## Slide 7 - Method / Workflow (6:00-7:05)

Metode yang digunakan pada prototype dibuat realistis dan aman. Data yang digunakan adalah data dummy atau simulasi. Pipeline dimulai dari input dan validasi, lalu entity extraction berbasis regex dan rule sederhana. Entitas dinormalisasi, disamarkan jika sensitif, lalu dideduplicate. Graph builder membuat node dan relationship. Setelah itu, BFS digunakan sebagai metode utama untuk koneksi terdekat dan evidence path, sementara UCS, Bi-Directional Search, dan A* diposisikan sebagai opsi lanjutan jika cost, bobot edge, dan heuristic sudah terdokumentasi. Output akhirnya adalah risk score, explanation, early warning, dashboard, dan review manusia.

## Slide 8 - Innovation / Novelty (7:05-8:05)

Novelty SATPAM ada pada perubahan cara melihat masalah. Sistem tidak lagi hanya entity-based detection, melainkan network-based intelligence. Pertama, graph intelligence menyatukan entitas digital dan finansial. Kedua, search-based risk path membuat hasil deteksi bisa ditelusuri. Ketiga, judol-pinjol linkage detection mencoba melihat hubungan antara kerugian judol dan tawaran pinjol ilegal. Keempat, risk scoring berbasis relasi membantu menentukan prioritas. Kelima, explainable detection membuat sistem tidak hanya memberi label, tetapi juga menjawab kenapa sebuah entitas dianggap berisiko. Yang penting, novelty ini tetap human-in-the-loop: sistem memberi kandidat dan alasan, sedangkan keputusan akhir tetap diverifikasi manusia.

## Slide 9 - Benefits and Roadmap (8:05-9:10)

Manfaat SATPAM untuk prototype adalah membantu analis memprioritaskan kasus, melihat cluster jaringan, memahami evidence path, dan mengurangi risiko salah tafsir karena hasil AI tetap berada dalam human-in-the-loop. Roadmap implementasinya bisa dilakukan dalam lima fase: foundation dan schema data; data ingestion dan graph builder; search dan scoring; dashboard dan verification; lalu testing dan demo. Dengan roadmap ini, sistem tetap kompetitif secara teknologi, tetapi tidak overclaim karena semua data pada prototype adalah dummy dan sistem tidak melakukan auto-blocking.

## Slide 10 - Closing and References (9:10-10:00)

Sebagai penutup, SATPAM dapat diringkas dalam lima kata: detect, map, explain, prioritize, verify. Sistem ini membantu membaca masalah judol-pinjol ilegal sebagai jaringan yang saling terhubung. Kontribusinya adalah menyatukan laporan publik, crawler finding, indikator transaksi, blacklist, graph search, risk scoring, dan dashboard prioritas dalam satu konsep yang explainable. Referensi utama berasal dari dokumen PPATK, Komdigi, OJK/IASC, dokumentasi Neo4j, serta dokumen SRS dan proposal SATPAM yang menjadi basis rancangan.
