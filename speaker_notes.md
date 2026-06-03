# Speaker Notes - Narasi 10 Menit Proposal SATPAM

## Slide 1 - Title (0:00-0:50)

Selamat pagi/siang, Pak/Bu Professor, dan teman-teman semua. Terima kasih telah meluangkan waktu untuk mendengarkan presentasi saya.

Pada kesempatan ini, saya ingin mengajukan sebuah proposal untuk proyek kecerdasan buatan yang saya sebut **SATPAM**—kepanjangan dari **Search-based AI Threat Prevention and Mapping**. 

Ide dasarnya sederhana tapi saya pikir cukup penting: kami ingin membangun sebuah sistem yang menggunakan AI dan graph intelligence untuk membantu analis mendeteksi, memetakan, dan memprioritaskan risiko pada ekosistem judi online dan pinjaman online ilegal. 

Yang perlu saya tekankan sejak awal: SATPAM **bukan** sistem penindakan otomatis. Ini adalah alat bantu—decision support system—untuk para analis. Ia membantu mereka melihat hubungan antar entitas, menunjukkan jejak bukti, memberikan skor risiko, tapi **tetap meminta verifikasi manusia** sebelum ada tindakan lanjut. Manusia tetap yang memutuskan, AI hanya membantu melihat gambaran yang lebih jelas.

## Slide 2 - Background / Urgency (0:50-1:55)

Mari kita lihat konteks masalahnya terlebih dahulu. Judol dan pinjol ilegal—ini bukan lagi masalah kecil yang bisa ditangani dengan melihat satu situs atau satu aplikasi saja.

Menurut data dari PPATK di tahun 2025—dan ini angkanya cukup mengejutkan—perputaran dana judol saja mencapai **Rp286,84 triliun** dengan **422,1 juta transaksi** dan melibatkan **12,3 juta depositor** yang mengirim uang melalui berbagai saluran: bank, e-wallet, QRIS, dan sejenisnya.

Masalahnya itu **lintas kanal**. Ada konten promosi di media sosial, domain, nomor WhatsApp, rekening bank, QRIS, e-wallet, APK, dan laporan dari masyarakat yang tertipu. Sekarang bayangkan: jika kita menganalisis setiap kanal secara terpisah—laporan terpisah, domain terpisah, rekening terpisah—pola jaringan besarnya akan sulit terlihat. Itulah mengapa SATPAM dirasa perlu: untuk melihat gambaran utuh ekosistem ini sebagai satu jaringan yang saling terhubung.

## Slide 3 - Existing System and Gap (1:55-2:55)

Sekarang, saya ingin menekankan: Indonesia **sebenarnya sudah memiliki** sistem dan lembaga-lembaga yang penting dan bekerja dengan baik. 

Ada Komdigi yang menangani konten dan pemblokiran ruang digital, OJK dan Satgas PASTI yang menangani aktivitas keuangan ilegal, IASC sebagai kanal laporan scam, PPATK yang menganalisis aliran dana mencurigakan, dan kepolisian yang melakukan penegakan hukum. Mereka semua sangat penting.

Jadi, gap yang ingin kami ambil dengan SATPAM **bukan untuk menggantikan** mereka. Sebaliknya, kami ingin **menghubungkan potongan-potongan data** yang tersebar di berbagai sistem ini. 

Sistem yang ada sudah sangat kuat pada domain mereka masing-masing, tapi setiap bekerja dengan sudut pandang mereka sendiri. SATPAM ingin menambahkan sebuah lapisan baru: peta relasi. Misalnya: link promosi ini mengarah ke domain mana? Domain itu terhubung ke nomor WhatsApp apa? Nomor itu terhubung ke rekening bank mana? Dan apakah rekening atau APK itu juga muncul di laporan masyarakat lain? Inilah perspektif jaringan yang tidak dimiliki analisis per-domain.

## Slide 4 - Problem Statement (2:55-3:50)

Dari latar belakang dan gap tersebut, saya perumusan masalahnya menjadi lima pertanyaan utama yang akan kami coba jawab melalui SATPAM.

**Pertama:** Bagaimana merancang sistem AI berbasis graph search yang benar-benar bisa memetakan ekosistem judol-pinjol ilegal dengan cara yang terukur dan dapat dipertanggungjawabkan?

**Kedua:** Bagaimana caranya kita menghubungkan semua potongan data—laporan masyarakat, domain, nomor WhatsApp, rekening bank, APK, crawler finding, bahkan transaksi simulasi dan blacklist dummy—ke dalam satu graph database yang coherent?

**Ketiga:** Dari perspektif AI, bagaimana menerapkan algoritma pencarian? BFS untuk menemukan koneksi terdekat, UCS untuk memperhitungkan cost, Bi-Directional Search untuk mencari pertemuan, atau A* jika heuristic sudah jelas?

**Keempat:** Bagaimana cara kita menghitung skor risiko dan menentukan prioritas tindakan? Apa metrik yang digunakan?

**Kelima:** Yang tidak kalah penting: bagaimana hasil sistem ini dijelaskan dalam bentuk jalur bukti yang mudah dipahami oleh analis? Karena AI yang blackbox tidak akan dipercaya.

## Slide 5 - Proposed Solution: SATPAM (3:50-4:55)

Nah, jadi bagaimana SATPAM menjawab kelima pertanyaan itu?

Sistemnya bekerja dengan alur multi-sumber. Input bisa datang dari berbagai tempat: laporan masyarakat, hasil crawler dari data publik yang legal, indikator transaksi simulasi, blacklist dummy yang sudah ada, dan data APK simulasi. Tidak ada satu sumber yang dominan—semuanya berkontribusi.

Kemudian, sistem melakukan **entity extraction**—mengidentifikasi elemen penting: URL, domain, nomor, rekening, keyword, QRIS, e-wallet, APK. Setelah itu, data dinormalisasi dan dibangun menjadi graph structure.

Di atas graph ini, kita jalankan algoritma: **BFS** untuk menelusuri jalur bukti yang dekat, **rule-based scoring** untuk menghitung risiko. Kalau sudah matang, A* bisa ditambahkan sebagai opsi untuk pencarian yang lebih intelligent.

Output akhirnya ditampilkan di dashboard: prioritas dan jejak bukti yang bisa ditelusuri. Dan yang penting: hasil tinggi atau kritis hanya menjadi **candidate untuk blacklist**, bukan blokir otomatis. Itu keputusan analis.

## Slide 6 - System Architecture (4:55-6:00)

Mari kita lihat arsitekturnya. Saya bagi SATPAM menjadi empat lapisan—think of it seperti stack, dari bottom to top.

**Lapisan pertama—Input:** Di sini kita mengumpulkan data dari berbagai sumber: report form dari masyarakat, API, import dataset dummy, crawler finding, traffic log simulasi, transaksi simulasi. Data mentah dari berbagai tempat.

**Lapisan kedua—Ingestion dan Processing:** Data yang masuk melewati quality control dan transformation. Ada validasi, entity extraction dengan pattern matching, normalization untuk menyeragamkan format, deduplication karena data duplikat pasti ada, dan graph builder yang mengubah data terstruktur menjadi node dan relationship di dalam graph.

**Lapisan ketiga—Intelligence Core:** Ini adalah jantung sistem. Neo4j sebagai graph database kita, algoritma search mulai dari BFS untuk evidence path discovery, rule-based scoring untuk menghitung risiko. Kalau mau lebih advanced, ada UCS, Bi-Directional Search, bahkan A* sebagai opsi. Plus ada early warning dan explanation engine—untuk memberi penjelasan kenapa sesuatu dianggap berisiko.

**Lapisan keempat—Output dan Verifikasi:** Dashboard menampilkan graph visualization, skor, cluster patterns, rekomendasi. Ada juga audit log untuk tracking. Dan yang penting, ada workflow untuk human verification—analis membaca hasil dan memutuskan tindakan lanjut.

## Slide 7 - Method / Workflow (6:00-7:05)

Untuk prototype, saya prioritaskan **realistis dan aman**. Data yang kita gunakan adalah data dummy atau simulasi—bukan data real yang sensitive.

Workflow-nya seperti ini: Mulai dari input dan validasi, apakah data format-nya benar. Lalu **entity extraction** dengan regex sederhana dan rule-based patterns—tidak perlu machine learning yang kompleks untuk tahap ini. Data dinormalisasi supaya format konsisten, disamarkan jika ada yang sensitive, dan dideduplicate karena duplikasi pasti ada di real world.

Setelah itu, **graph builder** membuat node untuk setiap entitas dan relationship untuk koneksi antar entitas.

Kemudian, kita jalankan **algoritma pencarian**. Di prototype ini, BFS adalah metode utama untuk discover koneksi terdekat dan evidence path. UCS, Bi-Directional Search, dan A* kami posisikan sebagai opsi lanjutan—bisa dikembang nanti kalau cost function dan heuristic sudah jelas dan terdokumentasi.

Output akhirnya: **risk score** untuk setiap node, **explanation path** yang bisa ditelusuri, **early warning** jika ada pattern mencurigakan, visualisasi di **dashboard**, dan terakhir **human review**—analis membaca dan memutuskan.

## Slide 8 - Innovation / Novelty (7:05-8:05)

Sekarang, dari perspektif kecerdasan buatan, apa sih novelty dari SATPAM?

Menurut saya, novelty-nya ada pada **perubahan paradigma**. Kita tidak lagi hanya melihat deteksi berbasis entitas individual—"apakah domain ini berisiko?"—melainkan **network-based intelligence**. Mari saya jelaskan lima aspek:

**Pertama:** **Graph Intelligence** menyatukan entitas digital (domain, APK, WhatsApp) dan finansial (rekening, QRIS, e-wallet) dalam satu representasi. Ini bukan trivial, karena biasanya mereka dianalisis di silo yang berbeda.

**Kedua:** **Search-based Risk Path** membuat hasil deteksi bisa ditelusuri. Bukan hanya "ini berisiko", tapi "ini berisiko karena terhubung ke ... dan ... melalui jalur ini". Transparency—yang penting untuk domain cybersecurity dan law enforcement.

**Ketiga:** **Judol-Pinjol Linkage Detection**—kami mencoba melihat hubungan antara ekosistem judol dan pinjol ilegal. Mereka sering terhubung, dan belum banyak sistem yang menangkap relasi ini.

**Keempat:** **Risk Scoring Berbasis Relasi**. Tidak hanya karakteristik individual, tapi juga siapa yang terhubung dengannya, pola koneksinya. Ini membantu prioritasi.

**Kelima:** **Explainable Detection**. Sistem tidak hanya memberi label berisiko, tapi juga menjawab "kenapa". Ini penting untuk trust dan accountability.

Dan yang essential: semua novelty ini tetap dalam kerangka **human-in-the-loop**. Sistem memberi kandidat dan alasan—keputusan akhir tetap di tangan manusia.

## Slide 9 - Benefits and Roadmap (8:05-9:10)

Jadi, apa sih benefit SATPAM untuk prototype dan ke depannya?

**Untuk analis**, SATPAM membantu mereka dalam beberapa hal konkret: 
- Memprioritaskan kasus—bukan semua bisa ditangani, tapi dengan risk score mereka bisa fokus ke yang paling urgent.
- Melihat cluster dan pattern jaringan—insight yang tidak terlihat kalau hanya melihat satu entitas saja.
- Memahami evidence path—bisa trace kembali kenapa sesuatu dianggap berisiko.
- Mengurangi risiko salah tafsir atau false positive, karena hasil AI tetap dalam kontrol manusia.

Untuk implementasi, saya draft **roadmap lima fase**:

**Fase 1 - Foundation:** Schema data dan data model untuk graph.  
**Fase 2 - Ingestion:** Data ingestion pipeline dan graph builder.  
**Fase 3 - Search & Scoring:** Algoritma search dan rule-based scoring.  
**Fase 4 - Dashboard & Verification:** Interface dan workflow verifikasi manusia.  
**Fase 5 - Testing & Demo:** Testing end-to-end dan demo siap presentasi.

Dengan roadmap ini, sistem tetap **kompetitif secara teknologi**, tapi juga **realistic dan tidak overclaim**. Semua data di prototype adalah dummy—ini feature, bukan limitation. Dan sistem tidak melakukan auto-blocking—keputusan tetap di tangan manusia. Ini penting untuk build trust.

## Slide 10 - Closing and References (9:10-10:00)

Sebagai penutup, saya ingin merangkum SATPAM dalam **lima kata kunci yang sederhana tapi comprehensive**:

1. **DETECT** – Mendeteksi entitas yang berisiko
2. **MAP** – Memetakan relasi dan jaringannya
3. **EXPLAIN** – Menjelaskan jalur bukti dan alasannya
4. **PRIORITIZE** – Memprioritaskan tindakan berdasarkan risiko
5. **VERIFY** – Memverifikasi dengan judgment manusia

Intinya, SATPAM membantu kita membaca masalah judol-pinjol ilegal bukan sebagai kasus-kasus terpisah, tapi sebagai **jaringan yang saling terhubung**. 

Kontribusi utamanya adalah **menyatukan** potongan-potongan: laporan publik, hasil crawler, indikator transaksi, blacklist existing, graph search algorithms, risk scoring, dan dashboard prioritas—semua dalam satu konsep yang explainable dan human-centric.

Terakhir, saya ingin mengucapkan terima kasih kepada Pak/Bu Professor atas kesempatan ini. Proposal ini didasarkan pada referensi dari dokumen PPATK, Komdigi, OJK/IASC, dokumentasi Neo4j, dan tentunya SRS dan proposal komprehensif SATPAM yang kami kembangkan. 

Saya terbuka untuk pertanyaan dan diskusi lebih lanjut. Terima kasih.
