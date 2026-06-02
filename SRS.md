# Software Requirements Specification (SRS)

## SATPAM: Search-based AI Threat Prevention and Mapping

Sistem Graph Intelligence untuk Deteksi, Pemetaan, dan Prioritisasi Risiko Ekosistem Judi Online dan Pinjaman Online Ilegal di Indonesia

---

## 1. Informasi Dokumen

| Item | Keterangan |
|---|---|
| Nama Dokumen | Software Requirements Specification (SRS) SATPAM |
| Versi | 1.0 |
| Tanggal | 2026-06-02 |
| Status | Draft awal komprehensif |
| Disusun Untuk | Prototype kecil berbasis data dummy |
| Bahasa | Bahasa Indonesia |

### 1.1 Riwayat Revisi

| Versi | Tanggal | Perubahan |
|---|---|---|
| 1.0 | 2026-06-02 | Penyusunan SRS awal berdasarkan referensi SATPAM dan keputusan scope prototype |

---

## 2. Ringkasan Eksekutif

SATPAM adalah sistem AI berbasis graph intelligence yang dirancang untuk membantu mendeteksi, memetakan, menjelaskan, dan memprioritaskan risiko dari ekosistem judi online (judol) dan pinjaman online (pinjol) ilegal. Sistem ini memandang masalah judol-pinjol ilegal sebagai jaringan entitas yang saling terhubung, bukan sebagai kasus tunggal.

Dalam prototype awal, SATPAM akan menggunakan data dummy dari berbagai sumber simulasi, seperti laporan masyarakat, domain/URL, akun promosi, nomor WhatsApp, rekening bank, e-wallet, QRIS, APK, keyword, transaksi simulasi, dan blacklist dummy. Data tersebut akan dibentuk menjadi graph, dianalisis menggunakan algoritma search terutama A* Search, diberi skor risiko secara rule-based, lalu divisualisasikan dalam dashboard.

Output utama sistem bukan vonis hukum, melainkan indikasi risiko yang explainable. SATPAM harus mampu menjawab pertanyaan seperti:

- Apakah sebuah entitas terindikasi berisiko?
- Entitas tersebut terhubung ke siapa saja?
- Jalur bukti apa yang membuat entitas tersebut dianggap berisiko?
- Cluster jaringan mana yang terlihat mencurigakan?
- Node mana yang harus diprioritaskan untuk diverifikasi?
- Apakah ada pola early warning dari entitas baru yang mirip dengan jaringan lama?

Prototype SATPAM harus memiliki mekanisme human verification. Semua hasil AI harus diberi label sebagai rekomendasi atau indikasi, bukan keputusan final. Entitas dengan risiko tinggi atau critical boleh otomatis masuk status `blacklist_candidate`, tetapi tidak boleh otomatis menjadi blacklist final atau terkena blokir nyata. Status `recommended_for_blocking` hanya boleh diberikan setelah review/approval manusia dalam konteks prototype.

---

## 3. Tujuan Dokumen

Dokumen ini bertujuan untuk mendefinisikan kebutuhan perangkat lunak SATPAM secara komprehensif untuk tahap prototype kecil. SRS ini menjadi acuan untuk:

- Menyusun proposal teknis dan proposal presentasi.
- Menentukan batasan scope prototype.
- Menentukan fitur minimum dan fitur pendukung.
- Menentukan aktor, alur kerja, dan kebutuhan data.
- Menentukan arsitektur sistem yang disarankan.
- Menentukan kebutuhan fungsional dan non-fungsional.
- Menentukan prinsip keamanan, privasi, etika, dan verifikasi manusia.
- Menjadi dasar implementasi MVP/prototype di tahap berikutnya.

---

## 4. Latar Belakang

Judi online dan pinjol ilegal merupakan masalah digital yang kompleks karena melibatkan banyak kanal, identitas, dan pola relasi. Satu kasus dapat melibatkan link promosi, domain, shortlink, akun media sosial, nomor WhatsApp, rekening bank, e-wallet, QRIS, APK, keyword, laporan korban, serta transaksi yang berpindah-pindah.

Pendekatan yang hanya memblokir satu domain, satu rekening, atau satu nomor belum cukup untuk memahami jaringan yang lebih besar. Pelaku dapat mengganti domain, nomor, rekening, akun promosi, package name APK, atau media distribusi. Karena itu, SATPAM dirancang sebagai sistem pendukung analisis yang menyatukan berbagai entitas ke dalam satu graph risiko.

SATPAM tidak menggantikan lembaga resmi, aparat, atau sistem existing. SATPAM berfungsi sebagai prototype analitik yang menunjukkan bagaimana data lintas entitas dapat dipetakan, dicari jalurnya, dinilai risikonya, dan dijelaskan kepada analis.

---

## 5. Keputusan Scope Awal

Berdasarkan keputusan awal pengguna, scope SATPAM adalah sebagai berikut:

| Area | Keputusan |
|---|---|
| Fokus ancaman | Judol dan pinjol ilegal sekaligus |
| Pengguna | Gabungan, tetapi prototype difokuskan pada pengguna internal/analis dan pelapor dummy |
| Sumber input | Kombinasi beberapa sumber simulasi |
| Jenis data | Data dummy untuk semua entitas |
| Entitas graph | Semua entitas utama dimasukkan |
| Output | Deteksi risiko, jalur hubungan, path bukti, prioritas tindakan, cluster, early warning, rekomendasi |
| Algoritma utama | A* Search |
| Algoritma pendukung | BFS, DFS/DLS/IDS, UCS/Dijkstra, Bi-Directional Search, centrality, community detection |
| Risk scoring | Rule-based pada tahap prototype |
| Early warning | Wajib ada |
| Traffic dan crawler intelligence | Wajib ada dalam bentuk simulasi log trafik dan simulasi hasil crawler/scraper |
| Dashboard visual graph | Wajib ada |
| Human verification | Wajib ada |
| Blacklist/blocking | Otomatis hanya sampai `blacklist_candidate`; blacklist final dan blokir harus melalui human verification |
| Skala | Prototype kecil |
| Bentuk sistem | Kombinasi web dashboard, API backend, sistem analitik internal, dan modul pelaporan |
| Teknologi | Disarankan oleh AI engineer berdasarkan kebutuhan |

---

## 6. Product Vision

### 6.1 Visi

SATPAM menjadi sistem analitik berbasis graph yang membantu analis memahami ekosistem judol-pinjol ilegal melalui peta hubungan, skor risiko, jalur bukti, dan rekomendasi prioritas yang dapat diverifikasi manusia.

### 6.2 Misi Prototype

Prototype SATPAM harus membuktikan bahwa:

- Data dummy dari berbagai sumber dapat digabungkan menjadi graph risiko.
- Sistem dapat mengekstrak entitas dari laporan sederhana.
- Sistem dapat membuat node dan relationship secara konsisten.
- Sistem dapat menelusuri jalur risiko menggunakan A* dan algoritma pendukung.
- Sistem dapat menghitung skor risiko secara rule-based.
- Sistem dapat menjelaskan alasan risiko dengan path dan rule yang aktif.
- Sistem dapat menampilkan graph, cluster, entity detail, dan rekomendasi di dashboard.
- Sistem dapat memisahkan hasil AI dengan hasil verifikasi manusia.
- Sistem dapat memproses simulasi log trafik dan simulasi hasil crawler/scraper sebagai sumber sinyal risiko.
- Sistem dapat menandai entitas berisiko tinggi sebagai kandidat blacklist tanpa melakukan blokir otomatis.

### 6.3 Nilai Utama

| Nilai | Penjelasan |
|---|---|
| Connected intelligence | Melihat hubungan antar entitas, bukan hanya entitas tunggal |
| Explainable risk | Menampilkan alasan risiko dan jalur bukti |
| Prioritization | Membantu menentukan entitas/jalur yang perlu ditangani lebih dulu |
| Early warning | Mendeteksi pola baru yang mirip dengan jaringan lama |
| Human-in-the-loop | Hasil AI harus diverifikasi manusia |
| Privacy-aware | Data korban dan data sensitif harus dilindungi |

---

## 7. Scope Sistem

### 7.1 In Scope Prototype

Prototype SATPAM mencakup:

- Form input laporan dummy.
- Import dataset dummy dari file JSON/CSV.
- Simulasi sumber data:
  - laporan masyarakat,
  - blacklist dummy,
  - data domain/URL,
  - data akun promosi,
  - data nomor WhatsApp,
  - data rekening bank,
  - data e-wallet,
  - data QRIS,
  - data APK,
  - data keyword,
  - data transaksi simulasi,
  - data crawler simulasi,
  - data log trafik simulasi.
- Entity extraction sederhana berbasis regex dan rule.
- Normalisasi entitas.
- Deduplication entitas.
- Graph builder.
- Penyimpanan graph di Neo4j.
- Search engine berbasis graph.
- A* Search sebagai algoritma utama untuk prioritisasi jalur risiko.
- BFS untuk eksplorasi koneksi terdekat.
- DFS/DLS/IDS untuk pencarian jalur dengan batas kedalaman.
- UCS/Dijkstra untuk jalur dengan cost investigasi.
- Bi-Directional Search untuk mencari titik temu antara laporan baru dan blacklist.
- Rule-based risk scoring.
- Early warning detection.
- Traffic and crawler intelligence berbasis data simulasi.
- Blacklist candidate workflow.
- Human verification workflow.
- Dashboard analitik.
- Visualisasi graph.
- Entity detail page.
- Case review page.
- Audit log.
- API backend.
- Export laporan analisis dalam format JSON dan/atau PDF/Markdown sederhana.

### 7.2 Out of Scope Prototype

Hal berikut tidak termasuk scope prototype awal:

- Integrasi dengan data resmi bank, e-wallet, PPATK, OJK, Komdigi, atau kepolisian.
- Pemblokiran domain/rekening/aplikasi secara nyata.
- Blacklist final otomatis tanpa review manusia.
- Monitoring trafik jaringan nyata.
- Intersepsi DNS, packet capture, atau inspeksi trafik pengguna nyata.
- Pengunduhan atau eksekusi APK ilegal asli.
- Scraping agresif, scraping target ilegal nyata, atau scraping yang melanggar ToS platform.
- Hacking, credential stuffing, bypass keamanan, atau investigasi ilegal.
- Penyimpanan data pribadi korban asli.
- Machine learning production-grade.
- Model deteksi fraud berbasis transaksi nyata.
- Deployment nasional.
- Sistem pengambilan keputusan hukum.
- Penentuan seseorang sebagai pelaku.

### 7.3 Future Scope

Pengembangan lanjutan dapat mencakup:

- Integrasi data resmi dan berizin.
- Model ML/anomaly detection yang dilatih dengan data terkurasi.
- Integrasi threat intelligence.
- Integrasi dashboard multi-instansi.
- Graph analytics skala besar.
- Real-time monitoring.
- Federated data sharing dengan kontrol akses ketat.
- Case management untuk investigasi resmi.

---

## 8. Definisi dan Istilah

| Istilah | Definisi |
|---|---|
| SATPAM | Search-based AI Threat Prevention and Mapping |
| Judol | Judi online |
| Pinjol ilegal | Pinjaman online yang tidak legal/terindikasi ilegal |
| Graph | Struktur data berisi node dan relationship |
| Node | Entitas dalam graph, seperti domain, rekening, APK, nomor WA |
| Relationship | Hubungan antar node |
| Entity extraction | Proses mengekstrak entitas dari teks/input |
| Risk score | Skor risiko berdasarkan rule dan relasi |
| Early warning | Peringatan awal untuk pola/entitas yang mulai mencurigakan |
| Human verification | Validasi manusia atas hasil AI |
| Blacklist dummy | Daftar entitas simulasi yang dianggap berisiko |
| Blacklist candidate | Entitas yang direkomendasikan sistem untuk masuk daftar review blacklist |
| Confirmed blacklist | Entitas yang sudah disetujui manusia sebagai blacklist dalam konteks prototype |
| Recommended for blocking | Status rekomendasi blokir setelah analisis/verifikasi, bukan eksekusi blokir otomatis |
| Traffic log simulasi | Data dummy yang meniru DNS log, access log, redirect log, atau domain request log |
| Crawler finding | Data dummy yang meniru hasil crawler/scraper publik seperti URL, keyword, redirect, dan akun promosi |
| Evidence path | Jalur graph yang menjadi alasan risiko |
| A* Search | Algoritma pencarian jalur berbasis cost aktual dan heuristic |
| BFS | Breadth First Search |
| DFS | Depth First Search |
| DLS | Depth Limited Search |
| IDS | Iterative Deepening Search |
| UCS | Uniform Cost Search |
| BDS | Bi-Directional Search |
| Centrality | Ukuran pentingnya node dalam graph |
| Community detection | Algoritma untuk menemukan cluster/komunitas dalam graph |

---

## 9. Stakeholder dan Aktor

### 9.1 Stakeholder

| Stakeholder | Kepentingan |
|---|---|
| Pelapor/masyarakat | Menyampaikan laporan mencurigakan |
| Analis | Meninjau risiko, graph, path, dan rekomendasi |
| Supervisor | Mengawasi hasil verifikasi dan prioritas kasus |
| Admin sistem | Mengelola user, rules, dataset dummy, konfigurasi |
| Developer/AI engineer | Membangun dan menguji prototype |
| Pihak institusi/penguji | Menilai kelayakan konsep dan implementasi |

### 9.2 Aktor Sistem

| Aktor | Deskripsi |
|---|---|
| Public Reporter | Pengguna yang memasukkan laporan melalui form terbatas |
| Analyst | Pengguna internal yang menganalisis graph dan risiko |
| Supervisor | Pengguna internal yang memvalidasi keputusan/verifikasi analis |
| System Admin | Pengguna yang mengelola konfigurasi sistem |
| API Client | Sistem eksternal simulasi yang mengirim data dummy melalui API |
| SATPAM Engine | Komponen otomatis yang melakukan extraction, graph build, search, scoring, dan alert |

### 9.3 Hak Akses

| Role | Hak Akses Utama |
|---|---|
| Public Reporter | Submit laporan, melihat status laporan terbatas |
| Analyst | Melihat dashboard, graph, path, risk score, melakukan verifikasi awal |
| Supervisor | Mengubah status akhir, menyetujui eskalasi, melihat ringkasan prioritas |
| System Admin | Mengelola user, rules, dataset dummy, konfigurasi, audit log |
| API Client | Mengirim data dan menerima hasil analisis terbatas sesuai token |

---

## 10. Perspektif Produk

SATPAM adalah aplikasi web dan API backend yang terdiri dari beberapa modul:

- Modul pelaporan.
- Modul data ingestion dummy.
- Modul entity extraction.
- Modul graph builder.
- Graph database.
- Modul graph search.
- Modul risk scoring.
- Modul early warning.
- Modul traffic and crawler intelligence.
- Modul blacklist candidate and review.
- Modul human verification.
- Modul dashboard dan visualisasi graph.
- Modul audit dan export.

Sistem prototype dapat berjalan secara lokal menggunakan Docker Compose atau instalasi lokal. Untuk kebutuhan presentasi/proposal, sistem cukup menunjukkan alur end-to-end dari input dummy sampai dashboard hasil analisis.

---

## 11. Rekomendasi Teknologi

### 11.1 Stack Utama

| Komponen | Rekomendasi | Alasan |
|---|---|---|
| Backend API | Python FastAPI | Cocok untuk API, rule engine, algoritma search, dan prototyping cepat |
| Graph Database | Neo4j Community Edition | Cocok untuk property graph dan query relasi |
| Frontend | React + TypeScript + Vite | Cocok untuk dashboard interaktif |
| Graph Visualization | Cytoscape.js | Kuat untuk node-link graph di browser |
| Styling UI | Tailwind CSS atau CSS module | Cepat untuk prototype |
| Auth Prototype | JWT/session sederhana + RBAC | Cukup untuk simulasi role |
| Data Seed | JSON/CSV | Mudah dibuat, diimpor, dan dijelaskan |
| Testing Backend | pytest | Cocok untuk Python |
| Testing Frontend | Vitest + Playwright | Cocok untuk unit dan UI verification |
| Container | Docker Compose | Memudahkan menjalankan backend, frontend, dan Neo4j |

### 11.2 Alternatif

| Komponen | Alternatif |
|---|---|
| Backend | Node.js Express/NestJS |
| Graph Database | Memgraph, ArangoDB |
| Visualization | D3.js, Sigma.js |
| Dashboard sederhana | Streamlit |

### 11.3 Rekomendasi Final untuk Prototype

Rekomendasi final:

```text
Frontend: React + TypeScript + Cytoscape.js
Backend: Python FastAPI
Database: Neo4j Community
Algorithm Engine: Python
Dataset: JSON/CSV dummy
Deployment lokal: Docker Compose
```

---

## 12. Arsitektur Sistem

### 12.1 Diagram Konseptual

```text
Public Reporter / Analyst / Admin
        |
        v
Web Dashboard + Report Form
        |
        v
Backend API (FastAPI)
        |
        +--> Entity Extraction Engine
        +--> Graph Builder
        +--> Search Algorithm Engine
        +--> Risk Scoring Engine
        +--> Early Warning Engine
        +--> Traffic & Crawler Intelligence Module
        +--> Blacklist Candidate Module
        +--> Human Verification Module
        +--> Audit & Export Module
        |
        v
Neo4j Graph Database
```

### 12.2 Alur Utama

```text
Input laporan/data dummy
-> validasi input
-> entity extraction
-> normalisasi entitas
-> deduplication
-> pembuatan node dan relationship
-> graph storage
-> graph search
-> risk scoring
-> traffic/crawler correlation
-> early warning check
-> blacklist candidate check
-> dashboard result
-> human verification
-> status final sementara
```

### 12.3 Komponen Sistem

| Komponen | Tanggung Jawab |
|---|---|
| Report Intake | Menerima laporan dari form/API |
| Data Importer | Memuat dataset dummy JSON/CSV |
| Entity Extractor | Mengekstrak URL, domain, nomor, rekening, APK, keyword |
| Normalizer | Menyamakan format entitas |
| Graph Builder | Membuat node dan relationship |
| Graph Repository | Menyimpan dan mengambil data dari Neo4j |
| Search Engine | Menjalankan A*, BFS, DFS/DLS/IDS, UCS, BDS |
| Risk Scoring Engine | Menghitung skor entitas, path, cluster, dan laporan |
| Early Warning Engine | Mendeteksi pola baru yang berisiko |
| Traffic and Crawler Intelligence | Memproses log trafik simulasi dan hasil crawler/scraper dummy sebagai sinyal risiko |
| Blacklist Candidate Module | Menandai entitas berisiko sebagai kandidat blacklist dan mengelola workflow review |
| Verification Module | Mengelola review manusia |
| Recommendation Engine | Memberikan rekomendasi tindakan |
| Dashboard UI | Menampilkan graph, skor, path, cluster, alert |
| Audit Module | Mencatat tindakan user dan sistem |
| Export Module | Mengekspor hasil analisis |

---

## 13. Data Source Prototype

### 13.1 Sumber Data Dummy

| Sumber | Bentuk Data | Contoh Isi |
|---|---|---|
| Laporan masyarakat dummy | JSON/CSV/form | Deskripsi, URL, nomor WA, rekening, bukti teks |
| Blacklist dummy | JSON/CSV | Domain, nomor, rekening, APK, keyword |
| Simulasi crawler | JSON/CSV | URL promosi, redirect, teks iklan, akun promosi |
| Simulasi scraper | JSON/CSV | Cuplikan teks promosi, bio akun, hashtag, link keluar |
| Simulasi log trafik | JSON/CSV | DNS request, access log, redirect event, domain request count |
| Simulasi transaksi | JSON/CSV | Transfer korban ke rekening, rekening ke e-wallet |
| Simulasi APK | JSON/CSV | Nama aplikasi, package name, permission |
| Simulasi media sosial | JSON/CSV | Username, platform, bio link, keyword |
| Simulasi QRIS/e-wallet | JSON/CSV | Merchant ID, nama alias, koneksi rekening |

### 13.2 Prinsip Data Dummy

- Semua data harus fiktif.
- Tidak memakai nomor telepon asli.
- Tidak memakai rekening asli.
- Tidak memakai domain ilegal asli.
- Tidak memakai identitas korban asli.
- Domain dummy harus memakai pola aman seperti `.test`, `.example`, atau nama fiktif yang jelas.
- Screenshot/bukti untuk prototype cukup berupa teks simulasi.
- Dataset harus mencakup kasus risiko rendah, sedang, tinggi, dan false positive.

### 13.3 Ukuran Dataset Awal

Rekomendasi ukuran dataset prototype:

| Entitas | Jumlah Minimum |
|---|---:|
| Report | 10-20 |
| Victim dummy | 10-20 |
| Domain/URL | 15-30 |
| Link shortener dummy | 5-10 |
| Social media account | 10-15 |
| PhoneNumber | 10-20 |
| BankAccount | 10-20 |
| EWallet | 5-10 |
| QRISMerchant | 5-10 |
| APK | 5-10 |
| Keyword | 20-40 |
| Transaction | 30-80 |
| TrafficEvent | 30-80 |
| CrawlerFinding | 20-60 |
| BlacklistEntity | 20-40 |
| BlacklistCandidate | 10-30 |
| Cluster | 3-5 |

---

## 14. Model Data Graph

### 14.1 Node Utama

| Node | Deskripsi | Properti Minimum |
|---|---|---|
| Report | Laporan masuk | id, source, description, createdAt, status |
| Victim | Pelapor/korban dummy | id, alias, riskExposureLevel |
| URL | URL lengkap | id, rawUrl, normalizedUrl, domain, firstSeenAt |
| Domain | Domain situs | id, domainName, category, riskScore |
| LinkShortener | Shortlink/redirector | id, shortUrl, provider |
| SocialMediaAccount | Akun promosi | id, platform, username, profileUrl |
| PhoneNumber | Nomor WhatsApp/telepon | id, normalizedNumber, countryCode, reportCount |
| BankAccount | Rekening bank | id, bankName, accountAlias, maskedAccountNumber |
| EWallet | Dompet digital | id, provider, walletAlias, maskedWalletId |
| QRISMerchant | Merchant QRIS | id, merchantAlias, merchantCategory |
| APK | Aplikasi | id, appName, packageName, requestedPermissions |
| Keyword | Kata kunci promosi | id, keyword, category, weight |
| Transaction | Transaksi simulasi | id, amount, timestamp, channel, transactionType |
| TrafficEvent | Event trafik simulasi | id, eventType, timestamp, sourceAlias, destinationDomain, requestCount |
| CrawlerFinding | Temuan crawler/scraper dummy | id, findingType, sourceUrl, contentSummary, matchedKeywords, capturedAt |
| BlacklistEntity | Entitas blacklist dummy | id, entityType, reason, severity |
| BlacklistCandidate | Kandidat blacklist | id, entityId, candidateReason, recommendedAction, status, createdAt |
| BlacklistDecision | Keputusan blacklist prototype | id, decision, reviewerId, decisionNote, decidedAt |
| Cluster | Kelompok jaringan | id, name, clusterType, riskScore |
| Evidence | Bukti pendukung dummy | id, evidenceType, contentSummary, createdAt |
| RiskAssessment | Hasil scoring | id, score, level, explanation, createdAt |
| VerificationCase | Kasus verifikasi | id, status, reviewerId, decisionNote |
| Recommendation | Rekomendasi tindakan | id, actionType, priority, reason |
| User | User sistem | id, name, role, status |
| AuditLog | Log aktivitas | id, actorId, action, targetId, timestamp |

### 14.2 Relationship Utama

| Relationship | Dari | Ke | Makna |
|---|---|---|---|
| REPORTED | Victim | Report | Korban/pelapor membuat laporan |
| MENTIONS | Report | Entity | Laporan menyebut entitas |
| CONTAINS_KEYWORD | Report/URL/SocialMediaAccount | Keyword | Konten mengandung keyword |
| REDIRECTS_TO | URL/LinkShortener | URL/Domain | Link mengarah ke target |
| PROMOTES | SocialMediaAccount | URL/Domain/APK | Akun mempromosikan entitas |
| CONTACTS | Domain/URL/SocialMediaAccount | PhoneNumber | Entitas mengarah ke nomor |
| USES_ACCOUNT | PhoneNumber/Domain/APK | BankAccount/EWallet/QRISMerchant | Entitas menggunakan akun pembayaran |
| TRANSFERRED_TO | Victim/BankAccount/EWallet | BankAccount/EWallet | Aliran dana simulasi |
| OBSERVED_TRAFFIC_TO | TrafficEvent | Domain/URL | Event trafik dummy mengarah ke domain/URL |
| HAS_REDIRECT_EVENT | TrafficEvent/CrawlerFinding | URL/Domain | Trafik atau crawler menemukan redirect |
| CRAWLED_FROM | CrawlerFinding | URL/SocialMediaAccount | Temuan berasal dari URL/akun tertentu |
| FOUND_ENTITY | CrawlerFinding | Entity | Crawler/scraper dummy menemukan entitas |
| LINKED_TO_APK | Domain/URL/SocialMediaAccount | APK | Entitas mengarah ke APK |
| REQUESTS_PERMISSION | APK | Permission/Keyword | APK meminta permission |
| SIMILAR_TO | Entity | Entity | Kemiripan dengan entitas lama |
| PART_OF_CLUSTER | Entity | Cluster | Entitas bagian dari cluster |
| BLACKLISTED_AS | Entity | BlacklistEntity | Entitas masuk blacklist dummy |
| FLAGGED_AS_CANDIDATE | Entity | BlacklistCandidate | Entitas ditandai sebagai kandidat blacklist |
| DECIDED_AS | BlacklistCandidate | BlacklistDecision | Kandidat memiliki keputusan review |
| HAS_EVIDENCE | Report/Entity | Evidence | Memiliki bukti pendukung |
| HAS_RISK_ASSESSMENT | Entity/Report/Path/Cluster | RiskAssessment | Memiliki hasil scoring |
| HAS_RECOMMENDATION | RiskAssessment | Recommendation | Hasil scoring menghasilkan rekomendasi |
| OPENED_CASE | Report/RiskAssessment | VerificationCase | Membuka kasus verifikasi |
| REVIEWED_BY | VerificationCase | User | Kasus direview oleh user |
| AUDITED_BY | AuditLog | User | Log terkait user |

### 14.3 Properti Standar Node

Setiap node disarankan memiliki properti:

| Properti | Deskripsi |
|---|---|
| id | ID unik internal |
| type | Jenis node |
| label | Nama tampilan |
| source | Sumber data dummy |
| firstSeenAt | Waktu pertama muncul |
| lastSeenAt | Waktu terakhir muncul |
| confidence | Confidence awal |
| riskScore | Skor risiko |
| riskLevel | low, medium, high, critical |
| verificationStatus | unreviewed, needs_review, verified_risk, false_positive, escalated |
| createdAt | Waktu dibuat |
| updatedAt | Waktu diperbarui |

### 14.4 Properti Standar Relationship

Setiap relationship disarankan memiliki properti:

| Properti | Deskripsi |
|---|---|
| id | ID relationship |
| source | Sumber data dummy |
| confidence | Confidence relasi |
| weight | Bobot traversal/search |
| evidenceId | Bukti yang mendukung relasi |
| firstSeenAt | Waktu pertama terlihat |
| lastSeenAt | Waktu terakhir terlihat |
| createdAt | Waktu dibuat |

---

## 15. Kebutuhan Fungsional

### 15.1 Modul Pelaporan

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-001 | Sistem harus menyediakan form laporan untuk memasukkan deskripsi, URL, nomor WhatsApp, rekening, e-wallet, QRIS, APK, akun promosi, dan kategori dugaan. | Must |
| FR-002 | Sistem harus mengizinkan pelapor dummy mengirim laporan tanpa melihat graph internal. | Must |
| FR-003 | Sistem harus memberikan ID laporan setelah laporan berhasil dibuat. | Must |
| FR-004 | Sistem harus memvalidasi format input dasar seperti URL, nomor, dan panjang teks. | Must |
| FR-005 | Sistem harus menandai laporan baru dengan status `new` atau `auto_triaged`. | Must |
| FR-006 | Sistem harus menyimpan ringkasan laporan, bukan data pribadi mentah. | Must |

### 15.2 Modul Import Data Dummy

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-007 | Sistem harus dapat mengimpor dataset dummy dari JSON/CSV. | Must |
| FR-008 | Sistem harus memvalidasi schema dataset sebelum import. | Must |
| FR-009 | Sistem harus menolak dataset yang mengandung field PII nyata yang tidak disamarkan. | Should |
| FR-010 | Sistem harus menyediakan log hasil import, termasuk jumlah node dan relationship yang dibuat. | Must |
| FR-011 | Sistem harus dapat melakukan reset dataset prototype melalui admin. | Should |

### 15.3 Modul Entity Extraction

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-012 | Sistem harus mengekstrak URL dari teks laporan. | Must |
| FR-013 | Sistem harus mengekstrak domain dari URL. | Must |
| FR-014 | Sistem harus mengekstrak nomor telepon/WhatsApp Indonesia dari teks. | Must |
| FR-015 | Sistem harus mengekstrak kandidat rekening bank dari pola angka dummy. | Must |
| FR-016 | Sistem harus mengekstrak e-wallet dan QRIS merchant dummy jika tersedia. | Must |
| FR-017 | Sistem harus mengekstrak nama APK dan package name dari input. | Must |
| FR-018 | Sistem harus mendeteksi keyword judol dan pinjol ilegal dari teks. | Must |
| FR-019 | Sistem harus memberi confidence untuk hasil extraction. | Should |
| FR-020 | Sistem harus menampilkan hasil extraction agar dapat direview analis. | Should |

### 15.4 Modul Normalisasi dan Deduplication

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-021 | Sistem harus menormalisasi URL dan domain sebelum disimpan. | Must |
| FR-022 | Sistem harus menormalisasi nomor telepon ke format konsisten. | Must |
| FR-023 | Sistem harus menyamarkan rekening dan e-wallet pada tampilan UI. | Must |
| FR-024 | Sistem harus menggabungkan entitas duplikat berdasarkan normalized key. | Must |
| FR-025 | Sistem harus menyimpan alias jika satu entitas muncul dalam beberapa variasi penulisan. | Should |

### 15.5 Modul Graph Builder

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-026 | Sistem harus membuat node untuk setiap entitas yang valid. | Must |
| FR-027 | Sistem harus membuat relationship berdasarkan sumber data dan hasil extraction. | Must |
| FR-028 | Sistem harus menyimpan confidence dan source pada setiap relationship. | Must |
| FR-029 | Sistem harus menghindari pembuatan relationship duplikat. | Must |
| FR-030 | Sistem harus memperbarui properti `firstSeenAt` dan `lastSeenAt`. | Should |

### 15.6 Modul Search Algorithm

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-031 | Sistem harus menjalankan A* Search untuk mencari jalur risiko paling prioritas dari entitas awal ke target berisiko. | Must |
| FR-032 | Sistem harus menjalankan BFS untuk menampilkan koneksi terdekat sampai kedalaman tertentu. | Must |
| FR-033 | Sistem harus mendukung DFS atau DLS untuk eksplorasi jalur mendalam dengan batas kedalaman. | Should |
| FR-034 | Sistem harus mendukung IDS untuk pencarian bertahap pada graph kecil. | Could |
| FR-035 | Sistem harus mendukung UCS/Dijkstra untuk mencari jalur dengan cost investigasi paling rendah. | Should |
| FR-036 | Sistem harus mendukung Bi-Directional Search untuk mencari titik temu antara laporan baru dan blacklist. | Should |
| FR-037 | Sistem harus mengembalikan path dalam bentuk node, relationship, cost, risk score, dan explanation. | Must |
| FR-038 | Sistem harus membatasi depth traversal agar prototype tetap stabil. | Must |
| FR-039 | Sistem harus menyimpan hasil search sebagai analisis yang dapat dibuka ulang. | Should |

### 15.7 Modul Risk Scoring

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-040 | Sistem harus menghitung skor risiko entitas secara rule-based. | Must |
| FR-041 | Sistem harus menghitung skor risiko path. | Must |
| FR-042 | Sistem harus menghitung skor risiko laporan. | Must |
| FR-043 | Sistem harus menghitung skor risiko cluster. | Should |
| FR-044 | Sistem harus menampilkan kontribusi tiap rule terhadap skor. | Must |
| FR-045 | Sistem harus mengelompokkan skor menjadi low, medium, high, dan critical. | Must |
| FR-046 | Sistem harus memungkinkan admin mengubah bobot rule pada prototype. | Should |
| FR-047 | Sistem harus menjalankan ulang scoring setelah rule berubah. | Should |

### 15.8 Modul Early Warning

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-048 | Sistem harus membuat alert jika entitas baru mirip dengan blacklist dummy. | Must |
| FR-049 | Sistem harus membuat alert jika domain baru mengandung keyword risiko dan terhubung ke nomor/rekening mencurigakan. | Must |
| FR-050 | Sistem harus membuat alert jika satu rekening menerima banyak transaksi kecil dari banyak korban dummy. | Must |
| FR-051 | Sistem harus membuat alert jika dana keluar cepat dari rekening kolektor ke rekening/e-wallet lain. | Should |
| FR-052 | Sistem harus membuat alert jika APK meminta permission sensitif dan terhubung ke domain/nomor berisiko. | Should |
| FR-053 | Sistem harus menampilkan alert berdasarkan prioritas. | Must |
| FR-054 | Sistem harus mengizinkan analis menandai alert sebagai reviewed, escalated, atau false positive. | Must |

### 15.9 Modul Graph Analytics

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-055 | Sistem harus menampilkan degree centrality sederhana untuk node. | Should |
| FR-056 | Sistem harus menandai node dengan banyak koneksi sebagai node prioritas. | Should |
| FR-057 | Sistem harus mendeteksi cluster sederhana berdasarkan relasi yang padat. | Should |
| FR-058 | Sistem harus menampilkan cluster jaringan berisiko pada dashboard. | Should |
| FR-059 | Sistem dapat menambahkan PageRank atau betweenness centrality pada tahap lanjutan. | Could |

### 15.10 Modul Human Verification

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-060 | Sistem harus membuat verification case untuk laporan/path/alert berisiko tinggi. | Must |
| FR-061 | Sistem harus menyediakan status verifikasi: unreviewed, needs_review, verified_risk, false_positive, escalated, closed. | Must |
| FR-062 | Sistem harus mengizinkan analis memberi catatan verifikasi. | Must |
| FR-063 | Sistem harus mengizinkan supervisor menyetujui atau mengubah keputusan analis. | Should |
| FR-064 | Sistem harus membedakan hasil otomatis dan hasil verifikasi manusia. | Must |
| FR-065 | Sistem harus menyimpan riwayat perubahan status. | Must |

### 15.11 Modul Dashboard

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-066 | Sistem harus menyediakan dashboard ringkasan jumlah laporan, entitas, alert, dan kasus verifikasi. | Must |
| FR-067 | Sistem harus menampilkan daftar entitas berisiko tinggi. | Must |
| FR-068 | Sistem harus menampilkan graph visualization interaktif. | Must |
| FR-069 | Sistem harus menampilkan detail node ketika node diklik. | Must |
| FR-070 | Sistem harus menampilkan evidence path dan alasan risiko. | Must |
| FR-071 | Sistem harus menyediakan filter berdasarkan jenis entitas, risk level, status verifikasi, dan sumber data. | Should |
| FR-072 | Sistem harus menyediakan halaman detail laporan. | Must |
| FR-073 | Sistem harus menyediakan halaman daftar early warning. | Must |
| FR-074 | Sistem harus menyediakan halaman case review. | Must |
| FR-075 | Sistem harus menyediakan halaman konfigurasi rule untuk admin. | Should |

### 15.12 Modul Rekomendasi

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-076 | Sistem harus menghasilkan rekomendasi tindakan berdasarkan risk level dan jenis entitas. | Must |
| FR-077 | Rekomendasi harus menggunakan bahasa indikatif, bukan vonis. | Must |
| FR-078 | Sistem harus menyarankan prioritas verifikasi, bukan pemblokiran otomatis. | Must |
| FR-079 | Sistem harus menampilkan alasan di balik rekomendasi. | Must |

### 15.13 Modul API

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-080 | Sistem harus menyediakan API untuk membuat laporan. | Must |
| FR-081 | Sistem harus menyediakan API untuk mencari entitas. | Must |
| FR-082 | Sistem harus menyediakan API untuk mengambil graph neighborhood. | Must |
| FR-083 | Sistem harus menyediakan API untuk menjalankan analisis path. | Must |
| FR-084 | Sistem harus menyediakan API untuk mengambil risk assessment. | Must |
| FR-085 | Sistem harus menyediakan API untuk memperbarui status verifikasi. | Must |
| FR-086 | Sistem harus menyediakan API untuk export hasil analisis. | Should |
| FR-087 | Sistem harus membatasi akses API berdasarkan role/token. | Must |

### 15.14 Modul Audit dan Export

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-088 | Sistem harus mencatat aktivitas penting user dan sistem. | Must |
| FR-089 | Sistem harus mencatat perubahan rule scoring. | Must |
| FR-090 | Sistem harus mencatat perubahan status verifikasi. | Must |
| FR-091 | Sistem harus dapat mengekspor ringkasan analisis tanpa data sensitif mentah. | Should |
| FR-092 | Sistem harus dapat mengekspor daftar node dan relationship untuk kebutuhan demo. | Should |

### 15.15 Modul Traffic and Crawler Intelligence

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-093 | Sistem harus dapat menerima/import log trafik simulasi seperti DNS request, access log, redirect log, dan domain request count. | Must |
| FR-094 | Sistem harus dapat menerima/import hasil crawler/scraper dummy seperti URL promosi, redirect chain, teks promosi, akun promosi, keyword, nomor, dan link APK. | Must |
| FR-095 | Sistem harus membuat node `TrafficEvent` untuk event trafik simulasi yang valid. | Must |
| FR-096 | Sistem harus membuat node `CrawlerFinding` untuk temuan crawler/scraper dummy yang valid. | Must |
| FR-097 | Sistem harus menghubungkan `TrafficEvent` dan `CrawlerFinding` ke entitas graph seperti URL, Domain, Keyword, SocialMediaAccount, PhoneNumber, BankAccount, dan APK. | Must |
| FR-098 | Sistem harus mendeteksi pola trafik dummy yang mencurigakan, seperti request berulang ke domain berisiko atau lonjakan akses ke domain baru. | Should |
| FR-099 | Sistem harus mendeteksi pola crawler dummy yang mencurigakan, seperti redirect chain panjang, keyword promosi berisiko, atau akun promosi yang menyebarkan banyak URL. | Must |
| FR-100 | Sistem harus memicu early warning jika trafik/crawler dummy menemukan entitas yang terhubung ke blacklist dummy atau cluster high-risk. | Must |
| FR-101 | Sistem harus menandai semua traffic/crawler source pada prototype sebagai `simulation_only`. | Must |
| FR-102 | Sistem tidak boleh melakukan crawling/scraping target ilegal nyata pada prototype. | Must |

### 15.16 Modul Blacklist Candidate and Review

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-103 | Sistem harus otomatis menandai entitas dengan risk level high/critical sebagai `blacklist_candidate` jika memenuhi rule tertentu. | Must |
| FR-104 | Sistem harus membuat `VerificationCase` untuk setiap kandidat blacklist high/critical. | Must |
| FR-105 | Sistem harus menampilkan alasan kandidat blacklist berdasarkan rule, risk score, confidence, dan evidence path. | Must |
| FR-106 | Sistem tidak boleh mengubah status entitas menjadi `confirmed_blacklist` tanpa aksi review manusia. | Must |
| FR-107 | Sistem tidak boleh melakukan blokir nyata terhadap domain, rekening, nomor, e-wallet, QRIS, APK, atau akun promosi. | Must |
| FR-108 | Analyst harus dapat memberi keputusan awal untuk kandidat: needs_more_evidence, reject_candidate, confirm_candidate, atau escalate. | Must |
| FR-109 | Supervisor harus dapat menyetujui kandidat menjadi `confirmed_blacklist` dalam konteks prototype. | Should |
| FR-110 | Setelah disetujui, sistem dapat memberi status `recommended_for_blocking` sebagai rekomendasi tindakan, bukan eksekusi blokir. | Must |
| FR-111 | Sistem harus mencatat semua perubahan status kandidat blacklist dalam audit log. | Must |
| FR-112 | Sistem harus menyediakan daftar kandidat blacklist yang dapat difilter berdasarkan jenis entitas, risk level, source, dan status review. | Must |

---

## 16. Use Case Utama

### UC-001: Submit Laporan Dummy

| Item | Keterangan |
|---|---|
| Aktor | Public Reporter / Analyst |
| Tujuan | Mengirim laporan berisi indikasi judol/pinjol ilegal |
| Precondition | User membuka form laporan |
| Main Flow | User mengisi deskripsi, URL, nomor, rekening, APK, lalu submit |
| Output | Laporan dibuat, entitas diekstrak, graph diperbarui, scoring awal dibuat |
| Postcondition | Laporan masuk daftar review |

### UC-002: Import Dataset Dummy

| Item | Keterangan |
|---|---|
| Aktor | Admin |
| Tujuan | Memasukkan data dummy untuk demo |
| Precondition | Dataset JSON/CSV tersedia |
| Main Flow | Admin upload/import dataset, sistem validasi, node/relationship dibuat |
| Output | Graph dummy siap dianalisis |
| Postcondition | Import log tersimpan |

### UC-003: Analisis Jalur Risiko

| Item | Keterangan |
|---|---|
| Aktor | Analyst |
| Tujuan | Mencari jalur risiko dari satu entitas |
| Precondition | Entitas ada di graph |
| Main Flow | Analyst memilih node, menjalankan A* atau BFS, sistem menampilkan path |
| Output | Evidence path, risk score, explanation, rekomendasi |
| Postcondition | Hasil analisis dapat disimpan |

### UC-004: Early Warning

| Item | Keterangan |
|---|---|
| Aktor | SATPAM Engine, Analyst |
| Tujuan | Mendeteksi pola baru yang berisiko |
| Precondition | Ada entitas baru atau graph berubah |
| Main Flow | Sistem menjalankan rule early warning, membuat alert |
| Output | Alert dengan prioritas dan alasan |
| Postcondition | Alert masuk antrian review |

### UC-005: Human Verification

| Item | Keterangan |
|---|---|
| Aktor | Analyst, Supervisor |
| Tujuan | Memvalidasi hasil AI |
| Precondition | Ada laporan/path/alert yang perlu review |
| Main Flow | Analyst membuka case, melihat path dan rule, memberi keputusan |
| Output | Status berubah menjadi verified_risk, false_positive, escalated, atau closed |
| Postcondition | Audit log tersimpan |

### UC-006: Eksplorasi Graph

| Item | Keterangan |
|---|---|
| Aktor | Analyst |
| Tujuan | Memahami hubungan antar entitas |
| Precondition | Graph tersedia |
| Main Flow | Analyst membuka graph explorer, filter node, klik entity, lihat detail |
| Output | Visualisasi graph dan detail node |
| Postcondition | Analyst dapat membuka analisis path dari node terpilih |

### UC-007: Import Traffic Log Simulasi

| Item | Keterangan |
|---|---|
| Aktor | Admin / API Client |
| Tujuan | Memasukkan sinyal trafik dummy sebagai sumber analisis |
| Precondition | File/API payload log trafik simulasi tersedia |
| Main Flow | Sistem menerima DNS/access/redirect log dummy, validasi, membuat `TrafficEvent`, lalu menghubungkan ke domain/URL |
| Output | Traffic event masuk graph dan dapat memicu alert |
| Postcondition | Semua event ditandai `simulation_only` |

### UC-008: Import Crawler/Scraper Finding Dummy

| Item | Keterangan |
|---|---|
| Aktor | Admin / API Client |
| Tujuan | Memasukkan hasil crawler/scraper dummy |
| Precondition | Dataset crawler/scraper dummy tersedia |
| Main Flow | Sistem menerima URL promosi, redirect chain, teks promosi, keyword, akun promosi, nomor, atau APK dummy |
| Output | `CrawlerFinding` dibuat dan terhubung ke entitas graph |
| Postcondition | Temuan crawler dapat dipakai untuk scoring dan early warning |

### UC-009: Review Blacklist Candidate

| Item | Keterangan |
|---|---|
| Aktor | Analyst, Supervisor |
| Tujuan | Meninjau entitas high/critical yang direkomendasikan sebagai kandidat blacklist |
| Precondition | Sistem sudah membuat `BlacklistCandidate` dari hasil scoring/alert |
| Main Flow | Analyst melihat evidence path, rule aktif, traffic/crawler finding, lalu memberi keputusan awal; supervisor dapat menyetujui |
| Output | Kandidat menjadi rejected, needs_more_evidence, escalated, atau confirmed_blacklist |
| Postcondition | Jika disetujui, sistem hanya memberi status `recommended_for_blocking` tanpa blokir nyata |

---

## 17. Algoritma dan Logika Analitik

### 17.1 A* Search sebagai Algoritma Utama

A* Search digunakan untuk mencari jalur paling prioritas dari entitas awal ke entitas target berisiko. Formula umum:

```text
f(n) = g(n) + h(n)
```

Dalam SATPAM:

| Komponen | Makna |
|---|---|
| g(n) | Cost aktual dari jalur yang sudah dilewati |
| h(n) | Estimasi risiko atau peluang hubungan berbahaya ke depan |
| f(n) | Nilai prioritas jalur |

Untuk prototype, A* dapat disesuaikan sebagai risk-prioritized path search. Karena A* klasik mencari cost terkecil, sistem dapat menggunakan transformasi cost agar risiko tinggi menjadi prioritas tinggi, misalnya:

```text
edgeCost = maxCost - riskWeight
pathPriority = accumulatedCost + heuristicCost
```

Atau:

```text
priorityScore = accumulatedRisk + heuristicRisk
```

Dengan catatan dokumentasi sistem harus jelas apakah implementasi memakai cost minimization atau risk maximization.

### 17.2 Heuristic A*

Contoh heuristic untuk prototype:

| Indikator | Tambahan Risiko |
|---|---:|
| Entitas terhubung ke blacklist dummy | +35 |
| Nomor WhatsApp pernah muncul di beberapa laporan | +30 |
| Rekening menerima banyak transfer kecil | +25 |
| Domain mengandung keyword judol/pinjol ilegal | +20 |
| APK meminta permission sensitif | +20 |
| Akun promosi menyebarkan banyak URL | +20 |
| Entitas mirip dengan entitas blacklist | +20 |
| Dana keluar cepat ke rekening/e-wallet lain | +20 |
| Terhubung ke cluster critical | +30 |
| Traffic log simulasi menunjukkan lonjakan request ke domain baru | +15 |
| Crawler/scraper dummy menemukan redirect chain panjang | +15 |
| Temuan crawler terhubung ke akun promosi dan nomor/rekening yang sama | +25 |

### 17.3 Algoritma Pendukung

| Algoritma | Fungsi |
|---|---|
| BFS | Menampilkan koneksi terdekat dari node awal sampai depth tertentu |
| DFS | Menelusuri jalur mendalam untuk eksplorasi investigasi |
| DLS | Membatasi DFS agar traversal tidak terlalu luas |
| IDS | Mencari bertahap dari depth kecil ke besar |
| UCS/Dijkstra | Mencari jalur dengan cost investigasi paling rendah |
| Bi-Directional Search | Mencari titik temu antara laporan baru dan blacklist |
| Degree Centrality | Mencari node dengan koneksi terbanyak |
| Betweenness Centrality | Mencari node jembatan antar cluster, optional |
| PageRank | Mencari node berpengaruh, optional |
| Community Detection | Mengelompokkan node menjadi cluster |

### 17.4 Batas Traversal Prototype

Untuk menjaga performa prototype:

| Parameter | Nilai Awal |
|---|---:|
| Max depth BFS | 3 |
| Max depth A* | 5 |
| Max path result | 10 |
| Max node graph display | 200 |
| Max relationship graph display | 500 |
| Timeout query | 5 detik |

---

## 18. Rule-Based Risk Scoring

### 18.1 Level Risiko

| Score | Level | Makna |
|---:|---|---|
| 0-24 | Low | Risiko rendah atau belum cukup bukti |
| 25-49 | Medium | Ada indikasi awal |
| 50-74 | High | Banyak indikator risiko |
| 75-100 | Critical | Sangat prioritas untuk diverifikasi |

### 18.2 Komponen Skor Entitas

Contoh formula awal:

```text
Entity Risk Score =
20% jumlah dan kualitas laporan
+ 20% koneksi ke blacklist dummy
+ 15% pola relasi mencurigakan
+ 15% keyword/konten berisiko
+ 10% pola transaksi simulasi
+ 10% sinyal traffic/crawler simulasi
+ 10% kemiripan dengan entitas berisiko lama
```

### 18.3 Komponen Skor Path

```text
Path Risk Score =
35% rata-rata risiko node
+ 25% risiko maksimum node dalam path
+ 20% bobot relationship
+ 10% kedekatan ke blacklist
+ 10% confidence evidence
```

### 18.4 Komponen Skor Laporan

```text
Report Risk Score =
30% entitas yang disebut
+ 25% path risiko terbaik
+ 20% jumlah rule aktif
+ 15% hubungan ke cluster
+ 10% kualitas informasi laporan
```

### 18.5 Contoh Rule

| Rule ID | Kondisi | Dampak |
|---|---|---:|
| R-001 | Domain mengandung keyword `slot`, `maxwin`, `bonus`, atau sejenisnya | +15 |
| R-002 | Deskripsi mengandung keyword pinjol ilegal seperti `cair cepat`, `tanpa BI checking`, `sebar data` | +15 |
| R-003 | Nomor WhatsApp muncul di lebih dari 3 laporan | +25 |
| R-004 | Rekening menerima transfer dari lebih dari 5 korban dummy | +25 |
| R-005 | Entitas terhubung langsung ke blacklist dummy | +35 |
| R-006 | Domain mengarah ke APK mencurigakan | +20 |
| R-007 | APK meminta permission kontak/SMS/lokasi | +20 |
| R-008 | Transaksi masuk dan keluar dalam waktu kurang dari 10 menit | +20 |
| R-009 | Akun promosi menyebarkan lebih dari 5 URL | +20 |
| R-010 | Entitas mirip dengan domain/nomor/rekening lama yang berisiko | +20 |
| R-011 | Traffic log simulasi menunjukkan lonjakan request ke domain baru berisiko | +15 |
| R-012 | Crawler/scraper dummy menemukan redirect chain lebih dari 2 langkah | +15 |
| R-013 | Crawler/scraper dummy menemukan keyword promosi dan nomor/rekening pada sumber yang sama | +25 |
| R-014 | Entitas memiliki risk level critical dan confidence minimal medium | Tandai `blacklist_candidate` |
| R-015 | Entitas sudah `confirmed_blacklist` oleh reviewer | Tandai `recommended_for_blocking` |

### 18.6 Confidence

Risk score dan confidence harus dipisahkan.

| Konsep | Makna |
|---|---|
| Risk score | Tingkat risiko berdasarkan indikator |
| Confidence | Seberapa kuat data/evidence yang mendukung skor |

Contoh:

```text
Risk Score: 85/100
Confidence: Medium
Alasan: banyak rule aktif, tetapi data masih dummy dan belum diverifikasi manusia.
```

---

## 19. Early Warning

### 19.1 Tujuan

Early warning bertujuan mendeteksi entitas atau pola baru yang mulai terlihat mencurigakan sebelum menjadi kasus besar. Pada prototype, early warning menggunakan rule dan graph pattern sederhana.

### 19.2 Jenis Alert

| Alert | Kondisi |
|---|---|
| Similar Entity Alert | Entitas baru mirip dengan blacklist dummy |
| Keyword-Contact Alert | Domain/akun mengandung keyword risiko dan mencantumkan nomor |
| Payment Fan-in Alert | Banyak korban dummy transfer ke rekening yang sama |
| Fast Transfer Alert | Dana masuk lalu cepat keluar |
| APK Permission Alert | APK terhubung ke laporan dan meminta permission sensitif |
| Cross-Ecosystem Alert | Jalur judol terhubung ke pinjol ilegal |
| Cluster Growth Alert | Cluster berisiko bertambah node dalam waktu pendek |
| Traffic Spike Alert | Log trafik simulasi menunjukkan lonjakan request ke domain/URL baru |
| Suspicious Redirect Alert | Crawler/scraper dummy menemukan redirect chain panjang atau berulang |
| Blacklist Candidate Alert | Entitas memenuhi rule untuk masuk kandidat blacklist |

### 19.3 Prioritas Alert

| Level | Kondisi |
|---|---|
| Low | Satu indikator ringan |
| Medium | Dua indikator atau koneksi tidak langsung ke risiko |
| High | Banyak indikator atau koneksi dekat ke blacklist |
| Critical | Terhubung ke blacklist, banyak laporan, dan pola transaksi mencurigakan |
| Blacklist Candidate | Status tambahan untuk entitas yang memenuhi syarat `blacklist_candidate` dan harus dibuatkan verification case |

### 19.4 Output Alert

Setiap alert harus memuat:

- ID alert.
- Jenis alert.
- Entitas utama.
- Risk level.
- Confidence.
- Rule yang memicu alert.
- Evidence path.
- Rekomendasi verifikasi.
- Status review.

---

## 20. Human Verification Workflow

### 20.1 Prinsip

SATPAM tidak boleh membuat keputusan final secara otomatis. Hasil sistem adalah indikasi risiko dan rekomendasi prioritas. Keputusan akhir harus melalui review manusia.

### 20.2 Status Verifikasi

| Status | Makna |
|---|---|
| unreviewed | Belum direview |
| needs_review | Perlu review manusia |
| verified_risk | Risiko terverifikasi pada konteks prototype |
| false_positive | Dianggap tidak berisiko setelah review |
| escalated | Perlu eskalasi ke pihak berwenang dalam skenario simulasi |
| closed | Case selesai |

### 20.3 Alur Verifikasi

```text
Risk result/alert dibuat
-> sistem membuka verification case
-> analyst melihat graph, path, rule, dan evidence
-> analyst memberi keputusan awal
-> supervisor dapat menyetujui/mengubah keputusan
-> status dan catatan disimpan
-> audit log dibuat
```

### 20.4 Aturan Bahasa

Sistem harus menggunakan bahasa yang hati-hati:

- Gunakan `terindikasi berisiko`, bukan `pelaku`.
- Gunakan `perlu verifikasi`, bukan `terbukti`.
- Gunakan `rekomendasi tindakan`, bukan `perintah tindakan`.
- Gunakan `data dummy/simulasi` saat demo.

### 20.5 Blacklist Candidate Workflow

Entitas high/critical tidak langsung diblokir atau masuk blacklist final. Sistem hanya boleh melakukan auto-flag sebagai kandidat.

```text
Entitas baru/updated
-> risk scoring
-> traffic/crawler correlation
-> rule blacklist candidate aktif
-> status: blacklist_candidate
-> verification case dibuat
-> analyst review evidence path
-> supervisor approval jika diperlukan
-> confirmed_blacklist atau rejected/false_positive
-> recommended_for_blocking jika confirmed
```

### 20.6 Status Kandidat Blacklist

| Status | Makna |
|---|---|
| not_candidate | Entitas tidak memenuhi syarat kandidat |
| blacklist_candidate | Sistem merekomendasikan review blacklist |
| needs_more_evidence | Reviewer meminta bukti tambahan |
| rejected_candidate | Reviewer menolak kandidat |
| false_positive | Entitas dianggap tidak berisiko pada konteks review |
| confirmed_blacklist | Reviewer menyetujui kandidat sebagai blacklist prototype |
| recommended_for_blocking | Sistem merekomendasikan blokir setelah approval, tanpa eksekusi blokir nyata |
| escalated | Perlu eskalasi dalam skenario simulasi |

### 20.7 Aturan Blacklist dan Blocking

- Auto-flag diperbolehkan untuk `blacklist_candidate`.
- Auto-block tidak diperbolehkan pada prototype.
- `confirmed_blacklist` harus berasal dari aksi reviewer manusia.
- `recommended_for_blocking` adalah output rekomendasi, bukan tindakan teknis.
- Semua perubahan status harus tercatat di audit log.
- UI harus menampilkan pembeda jelas antara `blacklist_candidate`, `confirmed_blacklist`, dan `recommended_for_blocking`.

---

## 21. Dashboard dan UI Requirements

### 21.1 Halaman Utama

Dashboard utama harus menampilkan:

- Total laporan.
- Total entitas.
- Total alert.
- Total verification case.
- Distribusi risk level.
- Entitas paling berisiko.
- Cluster paling berisiko.
- Ringkasan traffic/crawler finding simulasi.
- Jumlah blacklist candidate.
- Alert terbaru.
- Case yang perlu review.

### 21.2 Report Intake Page

Form laporan harus memiliki field:

- Deskripsi laporan.
- URL/domain.
- Nomor WhatsApp/telepon.
- Rekening bank.
- E-wallet.
- QRIS.
- APK/app name/package name.
- Akun media sosial.
- Kategori dugaan: judol, pinjol ilegal, gabungan, tidak tahu.
- Tombol submit.

### 21.3 Graph Explorer

Graph explorer harus mendukung:

- Visualisasi node dan edge.
- Warna node berdasarkan jenis entitas.
- Warna/ketebalan edge berdasarkan confidence atau weight.
- Ukuran node berdasarkan centrality/risk score.
- Filter jenis node.
- Filter risk level.
- Filter status verifikasi.
- Filter source: report, dummy blacklist, traffic simulation, crawler simulation.
- Klik node untuk membuka detail.
- Klik edge untuk melihat alasan relasi.
- Tombol `Find Risk Path`.
- Tombol `Show Neighborhood`.

### 21.4 Entity Detail Page

Halaman detail entitas harus menampilkan:

- Jenis entitas.
- Label/nama tampilan.
- Risk score.
- Risk level.
- Confidence.
- Status verifikasi.
- Sumber data.
- First seen dan last seen.
- Relationship terkait.
- Rule yang aktif.
- Path penting.
- Rekomendasi.
- Status kandidat blacklist jika ada.
- Traffic/crawler finding terkait jika ada.
- Riwayat review.

### 21.5 Risk Path Page

Halaman path harus menampilkan:

- Node awal dan node target.
- Algoritma yang digunakan.
- Daftar path.
- Skor per path.
- Jalur bukti.
- Rule aktif pada path.
- Rekomendasi prioritas.
- Tombol buka verification case.

### 21.6 Early Warning Page

Halaman early warning harus menampilkan:

- Daftar alert.
- Jenis alert.
- Prioritas.
- Entitas terkait.
- Waktu dibuat.
- Status review.
- Alasan alert.
- Source alert, termasuk traffic/crawler jika relevan.
- Tombol review.

### 21.7 Verification Case Page

Halaman verifikasi harus menampilkan:

- Ringkasan case.
- Risk score dan confidence.
- Evidence path.
- Rule aktif.
- Data pendukung.
- Catatan analis.
- Status.
- Aksi: mark needs_review, verified_risk, false_positive, escalated, closed.
- Panel kandidat blacklist jika case berasal dari auto-flag high/critical.

### 21.8 Admin Rule Page

Admin rule page harus menampilkan:

- Daftar rule.
- Bobot rule.
- Status aktif/tidak aktif.
- Deskripsi rule.
- Simulasi dampak perubahan bobot.
- Audit perubahan.

### 21.9 Traffic and Crawler Intelligence Page

Halaman traffic/crawler intelligence harus menampilkan:

- Daftar `TrafficEvent` simulasi.
- Daftar `CrawlerFinding` dummy.
- Jenis source: DNS log, access log, redirect log, crawler, scraper.
- Entitas yang ditemukan atau dihubungkan.
- Matched keyword.
- Redirect chain.
- Request count atau frekuensi event.
- Risk contribution.
- Alert yang dipicu.
- Label jelas `simulation_only`.

### 21.10 Blacklist Candidate Page

Halaman blacklist candidate harus menampilkan:

- Daftar entitas dengan status `blacklist_candidate`.
- Jenis entitas.
- Risk score dan confidence.
- Evidence path.
- Rule yang memicu kandidat.
- Traffic/crawler finding terkait.
- Status review.
- Keputusan analyst/supervisor.
- Aksi review: needs_more_evidence, reject_candidate, confirm_candidate, escalate.
- Label bahwa `recommended_for_blocking` bukan eksekusi blokir otomatis.

---

## 22. API Requirements

### 22.1 Endpoint Utama

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | /api/reports | Membuat laporan |
| GET | /api/reports | Mengambil daftar laporan |
| GET | /api/reports/{id} | Mengambil detail laporan |
| POST | /api/import/dummy-data | Import dataset dummy |
| GET | /api/entities | Mencari entitas |
| GET | /api/entities/{id} | Detail entitas |
| GET | /api/graph/neighborhood | Mengambil graph sekitar node |
| POST | /api/analysis/path-search | Menjalankan A*/BFS/dll |
| GET | /api/risk/{entityId} | Mengambil risk assessment |
| GET | /api/alerts | Mengambil early warning |
| PATCH | /api/alerts/{id}/status | Update status alert |
| GET | /api/traffic-events | Mengambil daftar traffic event simulasi |
| POST | /api/traffic-events/import | Import traffic log simulasi |
| GET | /api/crawler-findings | Mengambil daftar crawler/scraper finding dummy |
| POST | /api/crawler-findings/import | Import crawler/scraper finding dummy |
| GET | /api/blacklist-candidates | Mengambil daftar kandidat blacklist |
| GET | /api/blacklist-candidates/{id} | Mengambil detail kandidat blacklist |
| PATCH | /api/blacklist-candidates/{id}/decision | Update keputusan kandidat blacklist |
| GET | /api/verification-cases | Daftar verification case |
| PATCH | /api/verification-cases/{id} | Update verifikasi |
| GET | /api/rules | Daftar rule scoring |
| PATCH | /api/rules/{id} | Update rule |
| GET | /api/export/analysis/{id} | Export hasil analisis |

### 22.2 Contoh Request Laporan

```json
{
  "source": "dummy_user_report",
  "categoryHint": "gabungan",
  "description": "Saya diarahkan dari akun promosi ke situs bonus slot, lalu diminta menghubungi WA dan transfer. Setelah itu ditawari aplikasi pinjaman cepat cair.",
  "urls": ["https://bonus-slot-demo.test/promo"],
  "phoneNumbers": ["0812-0000-1111"],
  "bankAccounts": [
    {
      "bankName": "Bank Dummy",
      "accountAlias": "Rekening Promo 01",
      "maskedAccountNumber": "1234****9999"
    }
  ],
  "apps": [
    {
      "appName": "DanaCepat Demo",
      "packageName": "id.demo.danacepat"
    }
  ]
}
```

### 22.3 Contoh Response Analisis

```json
{
  "analysisId": "analysis-001",
  "algorithm": "A_STAR",
  "riskScore": 88,
  "riskLevel": "critical",
  "confidence": "medium",
  "blacklistStatus": "blacklist_candidate",
  "sourceSignals": [
    "dummy_user_report",
    "crawler_simulation",
    "traffic_simulation"
  ],
  "topPath": [
    "Report:report-001",
    "URL:url-001",
    "Domain:domain-001",
    "PhoneNumber:phone-001",
    "BankAccount:bank-001",
    "APK:apk-001"
  ],
  "triggeredRules": [
    "R-001",
    "R-003",
    "R-005",
    "R-006",
    "R-007",
    "R-011",
    "R-014"
  ],
  "recommendations": [
    "Prioritaskan untuk verifikasi analis",
    "Periksa hubungan nomor dan rekening dengan laporan lain",
    "Tandai APK sebagai entitas yang perlu review",
    "Buat verification case untuk kandidat blacklist"
  ]
}
```

---

## 23. Kebutuhan Non-Fungsional

### 23.1 Performance

| ID | Kebutuhan |
|---|---|
| NFR-001 | Dashboard ringkasan harus tampil dalam waktu kurang dari 3 detik pada dataset prototype. |
| NFR-002 | Query neighborhood graph depth 3 harus selesai dalam waktu kurang dari 5 detik pada dataset prototype. |
| NFR-003 | Path search A* depth 5 harus selesai dalam waktu kurang dari 5 detik pada dataset prototype. |
| NFR-004 | Import dataset dummy awal harus selesai dalam waktu kurang dari 30 detik. |

### 23.2 Scalability

| ID | Kebutuhan |
|---|---|
| NFR-005 | Prototype minimal harus mendukung 1.000 node dan 5.000 relationship. |
| NFR-006 | Desain sistem harus dapat diperluas ke puluhan ribu node pada tahap lanjutan. |
| NFR-007 | Traversal harus memiliki limit depth dan limit jumlah hasil. |

### 23.3 Security

| ID | Kebutuhan |
|---|---|
| NFR-008 | Sistem harus memiliki role-based access control. |
| NFR-009 | API harus membutuhkan token/session untuk akses internal. |
| NFR-010 | Data sensitif harus disamarkan di UI. |
| NFR-011 | Sistem harus mencatat aktivitas penting dalam audit log. |
| NFR-012 | Input user harus divalidasi dan disanitasi. |
| NFR-013 | Sistem tidak boleh menampilkan link ilegal asli dalam bentuk clickable pada demo. |
| NFR-014 | Sistem tidak boleh melakukan live traffic interception, packet capture, atau inspeksi trafik pengguna nyata pada prototype. |
| NFR-015 | Sistem tidak boleh menjalankan crawler/scraper nyata ke target ilegal atau platform yang tidak diizinkan. |
| NFR-016 | Sistem tidak boleh mengeksekusi auto-blocking terhadap entitas apa pun. |

### 23.4 Privacy

| ID | Kebutuhan |
|---|---|
| NFR-017 | Prototype harus menggunakan data dummy. |
| NFR-018 | Jika di masa depan memakai data asli, sistem harus menerapkan data minimization. |
| NFR-019 | Identitas korban harus dianonimkan. |
| NFR-020 | Rekening, nomor, e-wallet, dan QRIS harus dimasking pada UI umum. |
| NFR-021 | Export tidak boleh memuat data sensitif mentah. |
| NFR-022 | Semua traffic/crawler data prototype harus diberi label `simulation_only`. |

### 23.5 Explainability

| ID | Kebutuhan |
|---|---|
| NFR-023 | Setiap risk score harus memiliki penjelasan rule yang aktif. |
| NFR-024 | Setiap rekomendasi harus memiliki alasan. |
| NFR-025 | Setiap path harus dapat ditelusuri node dan relationship-nya. |
| NFR-026 | Sistem harus membedakan risk score dan confidence. |
| NFR-027 | Setiap status `blacklist_candidate` harus memiliki evidence path dan rule pemicu. |
| NFR-028 | UI harus membedakan `blacklist_candidate`, `confirmed_blacklist`, dan `recommended_for_blocking`. |

### 23.6 Usability

| ID | Kebutuhan |
|---|---|
| NFR-029 | Dashboard harus dapat digunakan oleh analis non-programmer. |
| NFR-030 | Label risiko harus jelas dan konsisten. |
| NFR-031 | Graph explorer harus menyediakan filter agar tidak terlalu padat. |
| NFR-032 | Status verifikasi harus mudah dipahami. |

### 23.7 Maintainability

| ID | Kebutuhan |
|---|---|
| NFR-033 | Rule scoring harus dipisahkan dari logic API utama. |
| NFR-034 | Modul search harus dapat diuji secara terpisah. |
| NFR-035 | Dataset dummy harus mudah diperbarui. |
| NFR-036 | Dokumentasi endpoint dan data model harus tersedia. |
| NFR-037 | Modul traffic/crawler intelligence harus dipisahkan dari modul crawler nyata agar prototype tidak keliru dipakai untuk scraping langsung. |

### 23.8 Reliability

| ID | Kebutuhan |
|---|---|
| NFR-038 | Sistem harus menangani input tidak lengkap tanpa crash. |
| NFR-039 | Sistem harus mencatat error import dan extraction. |
| NFR-040 | Sistem harus memiliki fallback jika graph query gagal. |

### 23.9 Testability

| ID | Kebutuhan |
|---|---|
| NFR-041 | Entity extraction harus memiliki unit test. |
| NFR-042 | Risk scoring harus memiliki unit test. |
| NFR-043 | Search algorithm harus memiliki test untuk path yang diharapkan. |
| NFR-044 | API utama harus memiliki integration test. |
| NFR-045 | Dashboard utama harus diverifikasi dengan UI test sederhana. |
| NFR-046 | Traffic/crawler import dan blacklist candidate workflow harus memiliki test. |

---

## 24. Keamanan, Etika, dan Batasan Hukum

### 24.1 Prinsip Etika

SATPAM harus mengikuti prinsip berikut:

- Menggunakan data dummy untuk prototype.
- Tidak melakukan hacking.
- Tidak melakukan transaksi ilegal.
- Tidak mengunduh atau menjalankan APK ilegal asli.
- Tidak melakukan scraping agresif atau scraping target ilegal nyata.
- Tidak melakukan monitoring trafik jaringan nyata pada prototype.
- Tidak melanggar ToS platform.
- Tidak menyimpan data korban asli.
- Tidak menuduh individu/entitas sebagai pelaku.
- Menggunakan istilah indikatif.
- Mengubah risiko tinggi menjadi `blacklist_candidate`, bukan blokir otomatis.
- Menyediakan human verification.
- Menyediakan audit trail.
- Menjaga privasi dan masking data.
- Menghindari publikasi link atau detail operasional yang dapat disalahgunakan.

### 24.2 Larangan Sistem

Sistem tidak boleh:

- Memblokir domain/rekening secara otomatis.
- Memasukkan entitas ke confirmed blacklist tanpa review manusia.
- Melakukan live traffic interception, packet capture, DNS interception, atau inspeksi trafik pengguna nyata.
- Melakukan crawler/scraper nyata ke situs ilegal atau platform tanpa izin.
- Menghasilkan instruksi untuk mengakses layanan ilegal.
- Menampilkan link ilegal asli sebagai tautan aktif.
- Memproses data pribadi nyata tanpa izin.
- Menentukan seseorang sebagai pelaku.
- Menghilangkan kebutuhan verifikasi manusia.
- Menggunakan hasil AI sebagai dasar vonis hukum.

### 24.3 Human Oversight

Setiap output risiko harus memiliki:

- Label "terindikasi".
- Confidence.
- Alasan rule.
- Evidence path.
- Status verifikasi.
- Catatan reviewer.

---

## 25. Data Governance

### 25.1 Klasifikasi Data

| Jenis Data | Klasifikasi | Perlakuan |
|---|---|---|
| Data dummy | Aman untuk prototype | Boleh ditampilkan |
| Nomor/rekening dummy | Sensitif simulasi | Tetap dimasking |
| Data korban asli | Tidak digunakan | Dilarang pada prototype |
| Link ilegal asli | Tidak digunakan | Dilarang pada prototype |
| APK ilegal asli | Tidak digunakan | Dilarang pada prototype |
| Traffic log simulasi | Data dummy | Harus diberi label `simulation_only` |
| Crawler finding dummy | Data dummy | Harus diberi label `simulation_only` |
| Blacklist candidate | Internal review | Tidak boleh dianggap blacklist final |
| Confirmed blacklist prototype | Internal review | Hanya hasil approval manusia dalam konteks prototype |
| Audit log | Internal | Hanya admin/supervisor |

### 25.2 Retensi Data Prototype

- Dataset dummy dapat direset oleh admin.
- Audit log disimpan selama prototype berjalan.
- Export hanya boleh berisi ringkasan dan data tersamarkan.

### 25.3 Masking

Contoh masking:

```text
PhoneNumber: 0812-0000-1111 -> 0812****1111
BankAccount: 123456789999 -> 1234****9999
EWallet: 089900001111 -> 0899****1111
```

---

## 26. Acceptance Criteria

Prototype SATPAM dianggap berhasil jika memenuhi kriteria berikut:

| ID | Kriteria |
|---|---|
| AC-001 | User dapat mengirim laporan dummy melalui form. |
| AC-002 | Sistem dapat mengekstrak URL, domain, nomor, rekening, APK, dan keyword dari laporan. |
| AC-003 | Sistem dapat membuat node dan relationship di Neo4j. |
| AC-004 | Dashboard dapat menampilkan graph interaktif. |
| AC-005 | User dapat memilih node dan melihat entity detail. |
| AC-006 | Sistem dapat menjalankan BFS untuk neighborhood graph. |
| AC-007 | Sistem dapat menjalankan A* untuk path prioritas risiko. |
| AC-008 | Sistem dapat menghitung risk score rule-based. |
| AC-009 | Sistem dapat menjelaskan skor melalui rule yang aktif. |
| AC-010 | Sistem dapat membuat early warning alert. |
| AC-011 | Sistem dapat membuka verification case untuk alert/laporan berisiko tinggi. |
| AC-012 | Analyst dapat mengubah status verifikasi. |
| AC-013 | Audit log tercatat untuk perubahan penting. |
| AC-014 | Semua data dalam demo adalah dummy atau tersamarkan. |
| AC-015 | Sistem tidak menggunakan bahasa vonis seperti "terbukti pelaku". |
| AC-016 | Sistem dapat mengimpor traffic log simulasi dan membuat node `TrafficEvent`. |
| AC-017 | Sistem dapat mengimpor crawler/scraper finding dummy dan membuat node `CrawlerFinding`. |
| AC-018 | Traffic/crawler finding dapat memicu early warning jika memenuhi rule. |
| AC-019 | Entitas high/critical dapat otomatis masuk status `blacklist_candidate`. |
| AC-020 | Entitas tidak dapat menjadi `confirmed_blacklist` tanpa review manusia. |
| AC-021 | Sistem tidak melakukan blokir nyata dan hanya menampilkan `recommended_for_blocking` sebagai rekomendasi. |

---

## 27. Rencana Implementasi Prototype

### 27.1 Fase 1: Foundation

Durasi estimasi: 1-2 minggu.

Deliverable:

- Struktur project.
- Docker Compose untuk Neo4j, backend, frontend.
- Schema data dummy.
- Seed dataset awal.
- API health check.

### 27.2 Fase 2: Data dan Graph

Durasi estimasi: 1-2 minggu.

Deliverable:

- Entity extraction sederhana.
- Normalisasi entitas.
- Graph builder.
- Import dataset dummy.
- Import traffic log simulasi.
- Import crawler/scraper finding dummy.
- Query dasar Neo4j.

### 27.3 Fase 3: Search dan Scoring

Durasi estimasi: 1-2 minggu.

Deliverable:

- BFS neighborhood.
- A* path risk.
- Rule-based risk scoring.
- Explanation engine.
- Early warning rules.
- Traffic/crawler correlation rules.
- Blacklist candidate rules.

### 27.4 Fase 4: Dashboard dan Verification

Durasi estimasi: 1-2 minggu.

Deliverable:

- Dashboard ringkasan.
- Graph explorer.
- Entity detail.
- Risk path view.
- Early warning page.
- Traffic/crawler intelligence page.
- Blacklist candidate page.
- Verification case workflow.

### 27.5 Fase 5: Testing dan Demo

Durasi estimasi: 1 minggu.

Deliverable:

- Unit test extraction/scoring/search.
- Integration test API.
- UI smoke test.
- Demo scenario.
- Export ringkasan analisis.

---

## 28. Demo Scenario

### 28.1 Scenario A: Laporan Judol

Input:

```text
Pelapor dummy menemukan link promosi bonus slot dari akun media sosial.
Link tersebut mengarah ke domain dummy, mencantumkan nomor WA, dan meminta transfer ke rekening dummy.
```

Output yang diharapkan:

- Entitas URL, domain, akun promosi, nomor, rekening, keyword dibuat.
- Graph menampilkan hubungan promosi -> URL -> domain -> WA -> rekening.
- Risk score high/critical.
- Rule keyword dan rekening aktif.
- Verification case dibuat.

### 28.2 Scenario B: Laporan Pinjol Ilegal

Input:

```text
Pelapor dummy menerima tawaran aplikasi pinjaman cepat cair.
APK meminta permission kontak/SMS dan terhubung ke nomor debt collector dummy.
```

Output yang diharapkan:

- Entitas APK, permission, nomor, keyword dibuat.
- Risk score high.
- Alert APK permission dibuat.
- Evidence path ditampilkan.

### 28.3 Scenario C: Keterkaitan Judol dan Pinjol

Input:

```text
Korban dummy kalah di situs judol lalu menerima tawaran APK pinjol dari nomor yang sama.
```

Output yang diharapkan:

- Sistem menemukan path judol -> WA -> APK pinjol.
- Cross-Ecosystem Alert dibuat.
- Risk score critical.
- Rekomendasi prioritas verifikasi muncul.

### 28.4 Scenario D: Aliran Dana Simulasi

Input:

```text
Banyak korban dummy transfer nominal kecil ke satu rekening.
Rekening tersebut mengirim dana ke e-wallet dummy dalam waktu singkat.
```

Output yang diharapkan:

- Payment Fan-in Alert dibuat.
- Fast Transfer Alert dibuat.
- Rekening kolektor menjadi node prioritas.
- Cluster transaksi ditampilkan.

### 28.5 Scenario E: Traffic dan Crawler Intelligence

Input:

```text
Traffic log simulasi menunjukkan banyak request ke domain baru.
Crawler finding dummy menemukan redirect chain dari akun promosi ke domain tersebut, lalu menemukan keyword bonus slot dan nomor WA.
```

Output yang diharapkan:

- Node `TrafficEvent` dan `CrawlerFinding` dibuat.
- Domain, URL, akun promosi, keyword, dan nomor WA terhubung dalam graph.
- Traffic Spike Alert dan Suspicious Redirect Alert dibuat.
- Risk score domain meningkat karena kombinasi traffic/crawler signal.
- Semua source ditampilkan sebagai `simulation_only`.

### 28.6 Scenario F: Blacklist Candidate Review

Input:

```text
Sebuah domain dummy memiliki risk score critical, terhubung ke blacklist dummy, muncul pada crawler finding, dan disebut dalam beberapa laporan.
```

Output yang diharapkan:

- Sistem otomatis menandai domain sebagai `blacklist_candidate`.
- Verification case dibuat.
- Analyst melihat evidence path dan rule pemicu.
- Supervisor dapat menyetujui menjadi `confirmed_blacklist`.
- Sistem menampilkan `recommended_for_blocking` tanpa melakukan blokir nyata.

---

## 29. Risiko Proyek dan Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Scope terlalu luas | Prototype tidak selesai | Batasi ke dataset dummy dan fitur core |
| Graph terlalu padat | Dashboard sulit dibaca | Gunakan filter, depth limit, dan pagination |
| False positive | Salah interpretasi risiko | Human verification dan confidence |
| Overclaiming AI | Proposal terlihat tidak realistis | Tegaskan prototype, rule-based, dan data dummy |
| Masalah privasi | Risiko etika | Jangan gunakan data asli, lakukan masking |
| Salah paham sebagai auto-blocking system | Risiko hukum dan false positive | Tegaskan blacklist candidate dan human approval |
| Traffic/crawler disangka monitoring nyata | Risiko privasi dan legal | Label `simulation_only` dan larang live interception |
| Algoritma A* kurang tepat jika heuristic tidak jelas | Analisis lemah | Dokumentasikan heuristic dan gunakan BFS/BDS sebagai pembanding |
| Performa Neo4j lambat pada query luas | UI lambat | Batasi traversal dan index node |
| Visualisasi sulit dipahami | User bingung | Gunakan warna, legenda, filter, dan detail panel |

---

## 30. Testing Requirements

### 30.1 Unit Test

| Modul | Test |
|---|---|
| Entity Extractor | URL, domain, nomor, rekening, APK, keyword |
| Normalizer | URL, phone, account masking |
| Risk Scoring | Rule aktif, bobot, score cap 100 |
| A* Search | Path prioritas sesuai heuristic |
| BFS | Neighborhood sesuai depth |
| Early Warning | Alert muncul sesuai rule |
| Traffic/Crawler Intelligence | Import event/finding dummy dan korelasi ke entitas |
| Blacklist Candidate | Auto-flag kandidat dan larangan confirmed blacklist tanpa reviewer |

### 30.2 Integration Test

| Flow | Test |
|---|---|
| Submit laporan | Laporan -> extraction -> graph -> scoring |
| Import dataset | File -> validation -> graph |
| Path analysis | API -> search engine -> Neo4j -> response |
| Traffic/crawler import | Payload -> validation -> TrafficEvent/CrawlerFinding -> graph -> alert |
| Blacklist candidate review | Risk score -> candidate -> verification -> decision -> audit log |
| Verification | Case -> status update -> audit log |

### 30.3 UI Test

| Halaman | Test |
|---|---|
| Dashboard | Ringkasan muncul |
| Report Form | Submit berhasil |
| Graph Explorer | Node/edge tampil |
| Entity Detail | Risk dan relationship tampil |
| Alert Page | Alert dapat direview |
| Traffic/Crawler Page | Event dan finding simulasi tampil dengan label `simulation_only` |
| Blacklist Candidate Page | Kandidat dapat direview tanpa auto-block |
| Verification Case | Status dapat diubah |

---

## 31. Dokumentasi yang Dibutuhkan

Dokumentasi pendukung yang perlu dibuat:

- README instalasi prototype.
- Dokumentasi schema dataset dummy.
- Dokumentasi API.
- Dokumentasi rule scoring.
- Dokumentasi algoritma search.
- Dokumentasi traffic/crawler simulation schema.
- Dokumentasi blacklist candidate workflow.
- Dokumentasi etika dan batasan sistem.
- Demo script.
- User guide singkat untuk analyst.

---

## 32. Open Questions Tidak Blocking

Pertanyaan berikut dapat diputuskan setelah SRS awal disetujui:

| Pertanyaan | Dampak |
|---|---|
| Apakah role public reporter benar-benar dibuat di prototype atau cukup form internal? | Mempengaruhi auth dan UI |
| Apakah export harus PDF, Markdown, atau JSON saja? | Mempengaruhi modul export |
| Apakah rule scoring boleh diedit dari UI atau cukup file konfigurasi? | Mempengaruhi admin page |
| Apakah dashboard harus memakai desain formal instansi atau gaya produk startup? | Mempengaruhi UI |
| Apakah demo perlu login multi-role penuh? | Mempengaruhi waktu implementasi |
| Apakah community detection harus benar-benar memakai Neo4j GDS atau cukup simulasi rule cluster? | Mempengaruhi kompleksitas |
| Apakah crawler pada MVP berikutnya tetap simulasi atau menggunakan crawler publik legal dan berizin? | Mempengaruhi etika, legal, dan infrastruktur |
| Apakah rekomendasi blokir cukup diekspor sebagai laporan atau perlu integrasi resmi pada tahap lanjutan? | Mempengaruhi governance dan integrasi |

---

## 33. Kesimpulan

SRS ini mendefinisikan SATPAM sebagai prototype kecil tetapi lengkap secara konsep: sistem gabungan web dashboard, API backend, graph database, search algorithm engine, risk scoring engine, early warning engine, dan human verification workflow.

SATPAM difokuskan pada judol dan pinjol ilegal secara bersamaan, menggunakan data dummy, semua entitas utama, A* Search sebagai algoritma utama, algoritma pendukung untuk eksplorasi graph, scoring rule-based, dashboard visual, serta prinsip etika dan privasi yang ketat.

Target utama prototype bukan membuktikan bahwa sistem bisa langsung dipakai untuk penindakan nyata, melainkan menunjukkan bahwa pendekatan graph intelligence dapat membantu menyatukan data yang tersebar, menjelaskan hubungan antar entitas, menemukan jalur risiko, memunculkan peringatan awal, dan membantu manusia memprioritaskan verifikasi.
