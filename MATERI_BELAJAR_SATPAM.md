# Materi Belajar SATPAM

## 1. Gambaran Besar

SATPAM adalah singkatan dari **Search-based AI Threat Prevention and Mapping**.

Sistem ini dirancang sebagai **sistem pendukung analisis** untuk membantu memahami ekosistem judi online dan pinjaman online ilegal sebagai sebuah jaringan, bukan sebagai kasus tunggal.

Inti idenya:

```text
Masalah judol-pinjol ilegal tidak hanya berupa satu website, satu rekening, atau satu APK.
Masalahnya adalah jaringan entitas yang saling terhubung.
```

SATPAM membantu menjawab pertanyaan seperti:

- Link mencurigakan ini terhubung ke domain mana?
- Domain ini terhubung ke nomor WhatsApp apa?
- Nomor WhatsApp ini muncul di laporan lain atau tidak?
- Rekening ini terhubung ke blacklist lama atau tidak?
- APK ini berhubungan dengan jaringan judol atau pinjol ilegal?
- Entitas mana yang harus diprioritaskan untuk diverifikasi?

SATPAM **bukan sistem penindakan otomatis**. Sistem ini tidak memblokir domain, tidak menetapkan pelaku, dan tidak menggantikan lembaga resmi. Output-nya adalah indikasi, skor risiko, jalur bukti, dan kandidat review yang tetap harus diverifikasi manusia.

## 2. Masalah yang Ingin Diselesaikan

Judol dan pinjol ilegal bekerja lintas kanal. Satu kasus bisa melibatkan:

- konten promosi,
- shortlink,
- domain website,
- akun media sosial,
- nomor WhatsApp,
- rekening bank,
- e-wallet,
- QRIS,
- APK pinjol ilegal,
- korban,
- laporan masyarakat,
- transaksi simulasi,
- blacklist lama.

Sistem existing sudah ada dan penting, tetapi sering bekerja pada domain masing-masing:

| Sistem/Lembaga | Fokus |
|---|---|
| Komdigi | Konten digital dan pemblokiran situs/konten |
| OJK/Satgas PASTI | Pinjol ilegal dan aktivitas keuangan ilegal |
| IASC | Laporan scam dan transaksi penipuan |
| PPATK | Analisis aliran dana mencurigakan |
| Kepolisian | Penegakan hukum |

Gap yang diambil SATPAM:

```text
Data ada, tetapi relasinya belum selalu menjadi pusat analisis.
```

Dengan kata lain, sistem existing bisa mengetahui bahwa sebuah link berbahaya atau sebuah rekening mencurigakan, tetapi belum tentu langsung menunjukkan jaringan lengkap:

```text
Laporan -> Link -> Domain -> WhatsApp -> Rekening -> APK -> Blacklist
```

## 3. Posisi SATPAM

SATPAM diposisikan sebagai:

- **decision-support system**,
- **graph intelligence system**,
- **risk mapping tool**,
- **evidence path explorer**,
- **prototype analitik berbasis data dummy/simulasi**.

SATPAM tidak diposisikan sebagai:

- sistem blokir otomatis,
- sistem vonis hukum,
- sistem hacking,
- sistem crawling target ilegal nyata,
- sistem pengganti Komdigi, OJK, PPATK, IASC, atau kepolisian.

Kalimat aman untuk menjelaskan posisi sistem:

> SATPAM adalah konsep sistem pendukung analisis yang menghubungkan data lintas ekosistem menjadi graph intelligence untuk membantu deteksi, pemetaan, penjelasan jalur bukti, dan prioritas verifikasi manusia.

## 4. Ide Utama: Dari Entity-Based ke Network-Based

Pendekatan biasa sering bersifat **entity-based**:

```text
Apakah link ini berbahaya?
Apakah rekening ini mencurigakan?
Apakah APK ini ilegal?
```

SATPAM memakai pendekatan **network-based**:

```text
Link ini terhubung ke siapa saja?
Rekening ini muncul di jaringan mana?
APK ini berhubungan dengan domain dan nomor WhatsApp apa?
Jalur risiko apa yang membuat entitas ini penting?
```

Perbedaan sederhananya:

| Pendekatan | Fokus | Kelemahan |
|---|---|---|
| Entity-based | Satu entitas | Relasi besar bisa tidak terlihat |
| Network-based | Jaringan entitas | Lebih cocok untuk pola regenerasi dan keterhubungan |

## 5. Input Data SATPAM

Untuk prototype, input yang paling aman adalah data dummy atau simulasi:

```text
Laporan masyarakat dummy
+ crawler finding dummy/simulasi
+ blacklist dummy
+ data transaksi simulasi
+ data APK simulasi
```

Contoh input:

| Sumber | Contoh Isi | Catatan |
|---|---|---|
| Laporan masyarakat | Link, nomor WA, rekening, kronologi | Aman untuk demo jika dummy |
| Crawler finding dummy | Domain, shortlink, keyword promosi | Bukan crawling ilegal nyata |
| Blacklist dummy | Domain/rekening/nomor lama | Untuk simulasi koneksi risiko |
| Transaksi simulasi | Transfer korban ke rekening tertentu | Tidak memakai data bank nyata |
| APK simulasi | Nama APK, permission, package name | Tidak perlu mengunduh APK ilegal |

Batas penting:

- Tidak menggunakan data pribadi nyata tanpa izin.
- Tidak melakukan live traffic interception.
- Tidak melakukan crawler ke target ilegal atau platform tidak berizin.
- Semua data sensitif harus dimasking atau dibuat dummy.

## 6. Entitas dalam Graph

SATPAM menyimpan data sebagai graph. Dalam graph, objek disebut **node**, hubungan disebut **relationship**, dan detail tambahan disebut **property**.

Contoh node:

| Node | Arti |
|---|---|
| `Report` | Laporan masyarakat |
| `Victim` | Korban atau pelapor dummy |
| `Domain` | Domain website |
| `Shortlink` | Link pendek |
| `PhoneNumber` | Nomor WhatsApp/admin |
| `BankAccount` | Rekening bank dummy |
| `EWallet` | E-wallet dummy |
| `QRISMerchant` | Merchant QRIS dummy |
| `APK` | Aplikasi pinjol/judol simulasi |
| `Keyword` | Kata promosi, misalnya slot, bonus, cair cepat |
| `Transaction` | Transaksi simulasi |
| `BlacklistEntity` | Entitas lama yang masuk daftar risiko dummy |

Contoh relationship:

| Relationship | Arti |
|---|---|
| `REPORTED` | Korban membuat laporan |
| `MENTIONS` | Laporan menyebut link/domain/nomor |
| `REDIRECTS_TO` | Shortlink mengarah ke domain |
| `CONTACTS` | Domain mengarah ke nomor WA |
| `USES_ACCOUNT` | Nomor/admin memakai rekening |
| `TRANSFERRED_TO` | Transaksi menuju rekening |
| `LINKED_TO_APK` | Domain/WA terhubung ke APK |
| `SIMILAR_TO` | Entitas mirip dengan entitas lama |
| `PART_OF_CLUSTER` | Entitas berada dalam cluster jaringan |

Contoh jalur:

```text
Report
-> Shortlink
-> Domain Judol
-> WhatsApp Admin
-> BankAccount
-> APK Pinjol
-> BlacklistEntity
```

## 7. Alur Kerja Sistem

Alur utama SATPAM:

```text
1. Input data
2. Validasi data
3. Entity extraction
4. Normalisasi dan masking
5. Deduplication
6. Graph builder
7. Graph storage di Neo4j
8. BFS evidence path
9. Rule-based risk scoring
10. Explanation dan dashboard
11. Human verification
```

Penjelasan tiap tahap:

| Tahap | Fungsi |
|---|---|
| Input data | Menerima laporan, crawler finding dummy, blacklist dummy, transaksi simulasi |
| Validasi | Memastikan data punya format aman dan tidak berisi input berbahaya |
| Entity extraction | Mengambil URL, domain, nomor WA, rekening, keyword, APK |
| Normalisasi | Menyamakan format, misalnya nomor HP dan URL |
| Masking | Menyamarkan data sensitif |
| Deduplication | Menggabungkan entitas yang sama agar tidak dobel |
| Graph builder | Membuat node dan relationship |
| Graph storage | Menyimpan graph di Neo4j |
| Search | Menelusuri koneksi dan evidence path |
| Scoring | Menghitung skor risiko berdasarkan rule |
| Dashboard | Menampilkan graph, skor, cluster, dan rekomendasi |
| Verification | Manusia memeriksa sebelum tindakan lanjut |

## 8. Metode Analitik yang Dipakai

Untuk prototype, metode utama yang paling realistis adalah:

```text
Graph modeling + BFS evidence path + rule-based risk scoring
```

### BFS Evidence Path

BFS digunakan untuk mencari koneksi terdekat dari satu node.

Contoh pertanyaan:

```text
Dari laporan ini, node apa saja yang bisa ditemukan dalam 1 sampai 3 langkah?
```

Contoh hasil:

```text
Report-001
-> Shortlink-01
-> Domain-Judol-01
-> WA-Admin-01
-> Rekening-01
```

Kenapa BFS cocok untuk MVP:

- mudah dijelaskan,
- cocok untuk graph kecil,
- hasilnya berupa jalur yang mudah dipahami,
- tidak membutuhkan heuristic rumit.

### Rule-Based Risk Scoring

Risk scoring menghitung risiko berdasarkan rule yang bisa dijelaskan.

Contoh indikator:

| Indikator | Dampak |
|---|---|
| Entitas muncul di banyak laporan | Risiko naik |
| Terhubung ke blacklist dummy | Risiko naik besar |
| Domain mengandung keyword judol | Risiko naik |
| Nomor WA muncul di banyak domain | Risiko naik |
| Rekening menerima banyak transaksi kecil | Risiko naik |
| Dana cepat keluar ke rekening/e-wallet lain | Risiko naik |
| APK meminta permission sensitif | Risiko naik |

Contoh formula sederhana:

```text
Risk Score =
30% laporan masyarakat
+ 20% koneksi ke blacklist
+ 20% pola transaksi mencurigakan
+ 15% hubungan dengan domain/APK ilegal
+ 15% kecepatan dana masuk-keluar
```

### A*, UCS, dan BDS

A*, UCS, dan Bi-Directional Search tetap relevan, tetapi untuk prototype lebih aman diposisikan sebagai opsi lanjutan:

| Algoritma | Posisi dalam SATPAM |
|---|---|
| BFS | Core untuk evidence path |
| UCS/Dijkstra | Opsional untuk jalur berbobot/cost investigasi |
| BDS | Opsional untuk mencari titik temu laporan baru dengan blacklist |
| A* | Advanced jika heuristic dan bobot edge sudah terdokumentasi |

Alasan A* tidak dijadikan satu-satunya fondasi MVP:

- A* membutuhkan heuristic yang jelas.
- Heuristic harus bisa dijelaskan dan dipertanggungjawabkan.
- Data dummy lebih cocok untuk rule-based scoring yang transparan.
- BFS + scoring sudah cukup untuk menunjukkan evidence path dan prioritas.

## 9. Risk Level dan Output

Output SATPAM bukan hanya label "aman" atau "berbahaya".

Output yang diharapkan:

| Output | Arti |
|---|---|
| Risk score | Skor risiko, misalnya 88/100 |
| Risk level | Low, medium, high, critical |
| Evidence path | Jalur bukti yang menjelaskan alasan risiko |
| Cluster jaringan | Kelompok entitas yang saling terhubung |
| Node prioritas | Entitas yang paling penting diverifikasi |
| Explanation | Rule yang aktif dan alasan sistem memberi skor |
| Blacklist candidate | Kandidat review, bukan blacklist final |
| Recommendation | Rekomendasi prioritas untuk reviewer |

Contoh output:

```text
Entitas awal: laporan-001
Risk Score: 91/100
Risk Level: Critical

Evidence Path:
Laporan korban
-> Link promosi
-> Domain judol
-> WhatsApp admin
-> Rekening
-> APK pinjol ilegal

Alasan risiko:
1. Domain mengandung keyword judol.
2. Nomor WA muncul di banyak laporan.
3. Rekening terhubung ke blacklist dummy.
4. APK meminta permission sensitif.
5. Jalur ini menghubungkan judol dan pinjol ilegal.

Rekomendasi:
Masukkan sebagai blacklist candidate untuk review manusia.
```

## 10. Arsitektur Sistem

Arsitektur sederhana SATPAM:

```text
Input Layer
-> Ingestion & Processing
-> Graph Database
-> Intelligence Core
-> Dashboard & Human Verification
```

Komponen utama:

| Komponen | Fungsi |
|---|---|
| Report Intake | Menerima laporan dari form/API |
| Data Importer | Memuat dataset dummy |
| Entity Extractor | Mengambil URL, domain, nomor, rekening, APK, keyword |
| Normalizer | Menyamakan format dan masking |
| Graph Builder | Membuat node dan relationship |
| Neo4j Graph Database | Menyimpan graph |
| Search Engine | Menjalankan BFS core dan algoritma opsional |
| Risk Scoring Engine | Menghitung skor risiko |
| Explanation Engine | Menjelaskan alasan risiko |
| Dashboard | Menampilkan graph, skor, path, dan prioritas |
| Verification Workflow | Reviewer manusia memutuskan tindak lanjut |

## 11. Dashboard yang Dibayangkan

Dashboard SATPAM sebaiknya menampilkan:

- ringkasan jumlah laporan,
- jumlah entitas high/critical,
- jumlah blacklist candidate,
- graph explorer,
- detail entitas,
- risk score,
- evidence path,
- cluster jaringan,
- daftar prioritas review,
- audit log,
- status human verification.

Contoh halaman:

| Halaman | Fungsi |
|---|---|
| Dashboard utama | Melihat ringkasan risiko |
| Report intake | Input laporan dummy |
| Graph explorer | Melihat jaringan node dan edge |
| Entity detail | Melihat profil satu entitas |
| Risk path page | Melihat jalur bukti |
| Early warning | Melihat sinyal baru yang berisiko |
| Verification case | Review manusia terhadap kandidat |
| Blacklist candidate page | Daftar kandidat review |

## 12. Skenario Demo yang Mudah Dipahami

### Skenario 1: Laporan Link Judol

Input:

```text
Pelapor memberi shortlink promosi judol dan nomor WhatsApp admin.
```

Proses:

```text
Sistem mengekstrak shortlink, domain, nomor WA, dan keyword.
Sistem membuat node dan relationship.
BFS mencari koneksi ke rekening dan blacklist dummy.
Risk scoring menghitung skor.
Dashboard menampilkan evidence path.
```

Output:

```text
Risk Score: 88/100
Evidence Path: Report -> Shortlink -> Domain -> WA -> Rekening
Status: blacklist_candidate
```

### Skenario 2: Judol Terhubung Pinjol Ilegal

Input:

```text
Laporan menyebut korban kalah uang di judol lalu diarahkan ke APK pinjol ilegal.
```

Proses:

```text
Sistem menghubungkan domain judol, nomor WA, rekening, dan APK pinjol.
Sistem mendeteksi linkage judol-pinjol.
```

Output:

```text
Risk Score: 93/100
Alasan: domain judol terhubung ke APK pinjol ilegal melalui WA admin.
```

### Skenario 3: Aliran Dana Simulasi

Input:

```text
Data transaksi dummy menunjukkan banyak transfer kecil ke satu rekening.
```

Proses:

```text
BFS menelusuri rekening tujuan.
Degree centrality mencari rekening yang paling banyak menerima koneksi.
Risk scoring menaikkan skor karena pola transaksi mencurigakan.
```

Output:

```text
Risk Score: 91/100
Node prioritas: Rekening A
Alasan: banyak transaksi kecil, terhubung ke domain, dan muncul di laporan.
```

## 13. Scope Prototype

Untuk tugas kuliah/proposal, scope yang disarankan:

| Area | Scope |
|---|---|
| Data | Dummy/simulasi |
| Input | Laporan, crawler finding dummy, blacklist dummy, transaksi simulasi |
| Database | Neo4j atau graph model sederhana |
| Extraction | Regex/rule sederhana |
| Search | BFS evidence path |
| Scoring | Rule-based risk scoring |
| Analytics | Degree centrality sederhana, rule-based cluster |
| Output | Dashboard, evidence path, skor risiko |
| Safety | Human verification, no auto-blocking |

Yang tidak perlu dilakukan pada prototype:

- crawling target ilegal nyata,
- integrasi data bank/PPATK/OJK resmi,
- auto-blocking,
- hacking,
- transaksi ke layanan ilegal,
- model AI prediktif kompleks,
- anomaly detection berat tanpa dataset valid.

## 14. Batasan Etis dan Keamanan

SATPAM harus aman secara etika.

Prinsip utama:

- Gunakan data dummy atau simulasi.
- Jangan menampilkan link ilegal asli sebagai clickable link.
- Jangan mengeksekusi pemblokiran.
- Jangan menyimpulkan entitas sebagai pelaku.
- Gunakan istilah "terindikasi", "berisiko", atau "kandidat review".
- Semua keputusan akhir harus melalui manusia.
- Data sensitif harus dimasking.

Kalimat aman:

```text
SATPAM hanya menghasilkan indikasi risiko dan rekomendasi prioritas.
Sistem tidak melakukan auto-blocking dan tidak menggantikan proses resmi.
```

## 15. Novelty yang Harus Kamu Pahami

Novelty SATPAM ada pada lima hal:

1. **Graph Intelligence**
   Data digital dan finansial disatukan menjadi graph.

2. **Search-based Risk Path**
   Sistem mencari jalur risiko, bukan hanya memberi label.

3. **Judol-Pinjol Linkage Detection**
   Sistem melihat kemungkinan hubungan antara kerugian judol dan tawaran pinjol ilegal.

4. **Risk Scoring Berbasis Relasi**
   Prioritas ditentukan dari hubungan antar entitas, bukan hanya satu indikator.

5. **Explainable Detection**
   Sistem menampilkan alasan dan jalur bukti.

Tambahan penting:

6. **Human-in-the-loop**
   Output sistem tetap harus diverifikasi manusia sebelum tindak lanjut.

## 16. Cara Menjelaskan SATPAM dalam 30 Detik

Versi singkat:

> SATPAM adalah sistem graph intelligence untuk membantu analis memahami ekosistem judol dan pinjol ilegal sebagai jaringan. Sistem mengubah laporan, domain, nomor WhatsApp, rekening, APK, transaksi simulasi, dan blacklist dummy menjadi graph. Setelah itu, BFS digunakan untuk mencari evidence path, risk scoring menghitung prioritas, dan dashboard menampilkan jalur bukti serta kandidat review. SATPAM bukan auto-blocking system, melainkan decision-support dengan verifikasi manusia.

## 17. Cara Menjelaskan SATPAM dalam 2 Menit

Versi agak lengkap:

> Masalah judol dan pinjol ilegal tidak cukup dilihat sebagai satu situs atau satu aplikasi. Dalam praktiknya, satu kasus bisa melibatkan konten promosi, shortlink, domain, nomor WhatsApp, rekening, e-wallet, QRIS, APK, laporan korban, dan aliran dana. Sistem existing sudah kuat pada domain masing-masing, tetapi relasi lintas ekosistem belum selalu menjadi pusat analisis.
>
> SATPAM diusulkan sebagai sistem pendukung analisis berbasis graph intelligence. Data dummy dari berbagai sumber diekstrak menjadi entitas, dinormalisasi, lalu disimpan sebagai node dan relationship di graph database. Dengan BFS, sistem dapat menampilkan jalur bukti dari laporan ke entitas berisiko. Dengan rule-based risk scoring, sistem menghitung prioritas risiko secara explainable.
>
> Output SATPAM berupa risk score, evidence path, cluster jaringan, node prioritas, dan blacklist candidate. Namun, sistem tidak melakukan pemblokiran otomatis. Semua hasil tetap harus melewati human verification.

## 18. Pertanyaan yang Mungkin Ditanyakan Dosen/Evaluator

### Apa bedanya SATPAM dengan sistem existing?

Sistem existing fokus pada konten, laporan, transaksi, atau penindakan. SATPAM fokus menghubungkan semua data itu ke dalam satu graph agar jalur risiko dan relasi lintas kanal terlihat.

### Kenapa memakai graph database?

Karena masalah judol-pinjol adalah masalah jaringan. Graph database cocok untuk melihat hubungan antar domain, WA, rekening, APK, laporan, dan blacklist.

### Kenapa memakai BFS?

BFS cocok untuk mencari koneksi terdekat dan evidence path. Untuk prototype, BFS mudah dijelaskan dan tidak membutuhkan heuristic rumit.

### Lalu A* dipakai untuk apa?

A* bisa dipakai sebagai metode lanjutan untuk risk-prioritized path search jika heuristic dan bobot edge sudah terdokumentasi. Pada MVP, A* bukan fondasi utama.

### Bagaimana risk score dihitung?

Risk score dihitung berdasarkan rule, misalnya jumlah laporan, koneksi ke blacklist, pola transaksi simulasi, keyword domain, dan hubungan ke APK mencurigakan.

### Apakah SATPAM melakukan blokir otomatis?

Tidak. SATPAM hanya memberi kandidat review dan rekomendasi prioritas. Keputusan final tetap melalui manusia.

### Apakah sistem memakai data nyata?

Untuk prototype, tidak. Sistem memakai data dummy/simulasi agar aman secara etika dan hukum.

### Apa kontribusi utamanya?

Kontribusinya adalah mengubah data yang terpisah menjadi graph intelligence yang explainable, sehingga analis bisa melihat jalur bukti, skor risiko, cluster jaringan, dan prioritas verifikasi.

## 19. Hal yang Harus Kamu Hafal

Kalau hanya sempat menghafal beberapa poin, hafalkan ini:

1. SATPAM adalah decision-support, bukan sistem penindakan otomatis.
2. Masalah judol-pinjol dilihat sebagai jaringan lintas kanal.
3. Data utama: laporan, domain, WA, rekening, APK, transaksi simulasi, blacklist dummy.
4. Model utama: graph database berisi node dan relationship.
5. Metode MVP: BFS evidence path + rule-based risk scoring.
6. Output: risk score, evidence path, cluster, prioritas, blacklist candidate.
7. Semua hasil harus melalui human verification.

## 20. Ringkasan Satu Halaman

```text
Nama:
SATPAM - Search-based AI Threat Prevention and Mapping

Masalah:
Judol dan pinjol ilegal bekerja sebagai jaringan lintas kanal.

Gap:
Data konten, laporan, transaksi, rekening, APK, dan blacklist masih sering dianalisis terpisah.

Solusi:
Menyatukan entitas ke dalam graph database, lalu menelusuri hubungan dan risiko.

Input:
Laporan dummy, crawler finding dummy, blacklist dummy, transaksi simulasi, APK simulasi.

Entitas:
Report, Domain, Shortlink, PhoneNumber, BankAccount, EWallet, QRIS, APK, Keyword, Transaction, BlacklistEntity.

Metode:
BFS evidence path + rule-based risk scoring.
A*, UCS, BDS sebagai opsi lanjutan.

Output:
Risk score, evidence path, cluster, node prioritas, explanation, blacklist candidate.

Keamanan:
Data dummy, masking, no auto-blocking, human-in-the-loop.

Novelty:
Entity-based detection -> network-based intelligence.
```

## 21. Sumber Materi

Materi belajar ini disusun dari:

- `SATPAM_Proposal_Comprehensive.md`
- `SATPAM_Latar_Belakang_Gap_Inovasi.md`

Catatan framing:

- Materi ini mengikuti revisi terbaru yang memosisikan **BFS evidence path + rule-based risk scoring** sebagai inti MVP.
- **A* Search** tetap disebut sebagai opsi lanjutan jika heuristic dan bobot edge sudah terdokumentasi.
