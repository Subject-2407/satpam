# SATPAM: Search-based AI Threat Prevention and Mapping

## Sistem Graph Intelligence untuk Deteksi dan Pemetaan Ekosistem Judi Online dan Pinjaman Online Ilegal di Indonesia

---

## 1. Ringkasan Ide

**SATPAM** adalah singkatan dari:

> **Search-based AI Threat Prevention and Mapping**

SATPAM adalah konsep sistem AI berbasis **graph search** yang bertujuan untuk membantu mendeteksi, memetakan, dan memprioritaskan risiko dari ekosistem **judi online (judol)** dan **pinjaman online (pinjol) ilegal** di Indonesia.

Sistem ini tidak hanya mendeteksi apakah sebuah link, rekening, aplikasi, atau nomor WhatsApp berbahaya. Lebih dari itu, SATPAM mencoba melihat **hubungan antar entitas** seperti:

- korban,
- laporan masyarakat,
- domain website,
- link shortener,
- akun media sosial,
- nomor WhatsApp,
- rekening bank,
- e-wallet,
- QRIS,
- APK pinjol ilegal,
- kata kunci promosi,
- dan blacklist lama.

Dengan pendekatan ini, SATPAM dapat digunakan untuk menjawab pertanyaan seperti:

- Link ini terhubung ke siapa saja?
- Rekening ini pernah muncul di laporan lain atau tidak?
- Apakah sebuah APK pinjol ilegal terhubung dengan jaringan judol tertentu?
- Jalur risiko dari korban sampai ke pelaku seperti apa?
- Entitas mana yang paling penting untuk ditangani lebih dulu?

---

## 2. Latar Belakang Masalah

Judi online dan pinjol ilegal merupakan masalah serius di Indonesia karena dampaknya tidak hanya berada pada aspek teknologi, tetapi juga menyentuh aspek sosial, ekonomi, dan hukum.

Dari sisi sosial, judol dan pinjol ilegal dapat merusak keluarga, memicu konflik, memperburuk kondisi mental korban, dan menjerat kelompok rentan. PPATK pernah menyebut bahwa judi online menyasar kelompok rentan seperti remaja, pelajar, ibu rumah tangga, hingga pekerja formal.[^ppatk-perang-total]

Dari sisi ekonomi, perputaran dana judi online di Indonesia sangat besar. PPATK mencatat bahwa pada tahun 2025 perputaran dana judi online sebesar **Rp286,84 triliun** dari **422,1 juta transaksi**, dan sebanyak **12,3 juta orang** melakukan deposit melalui bank, e-wallet, dan QRIS.[^ppatk-2025]

Dari sisi hukum dan keamanan, ekosistem judol dan pinjol ilegal sulit diberantas karena pelaku dapat terus berganti domain, akun, rekening, nomor, atau aplikasi. Artinya, pendekatan yang hanya memblokir satu situs atau satu rekening belum tentu cukup untuk memutus jaringan.

Karena itu, dibutuhkan sistem yang dapat melihat masalah ini sebagai **ekosistem jaringan**, bukan sebagai kasus yang berdiri sendiri.

---

## 3. Sistem Existing Saat Ini

Indonesia sudah memiliki beberapa sistem, lembaga, dan inisiatif untuk menangani judol, pinjol ilegal, dan scam digital.

| Sistem / Lembaga | Fokus Utama | Contoh Peran | Catatan |
|---|---|---|---|
| **Kominfo / Komdigi** | Konten digital ilegal | Pemblokiran situs dan konten ilegal, termasuk judi online | Berfokus pada konten digital dan domain |
| **AIS Kominfo / Komdigi** | Crawling konten negatif | Mesin pengais konten internet negatif | Cocok untuk deteksi konten dalam skala besar |
| **OJK / Satgas PASTI** | Pinjol ilegal dan aktivitas keuangan ilegal | Cyber patrol, penutupan aplikasi dan website pinjol ilegal | Kuat pada area jasa keuangan ilegal |
| **IASC** | Penipuan transaksi keuangan | Kanal laporan dan pemblokiran rekening terkait penipuan | Kuat untuk laporan korban dan rekening |
| **PPATK** | Analisis transaksi keuangan mencurigakan | Analisis aliran dana judi online dan pencucian uang | Kuat pada financial intelligence |
| **Kepolisian** | Penegakan hukum | Investigasi dan penindakan pelaku | Membutuhkan bukti dan prioritas kasus |

Komdigi memiliki AIS sebagai mesin crawling untuk mengais konten internet negatif, termasuk konten terkait perjudian.[^komdigi-ais] OJK melalui Satgas PASTI juga melakukan pencegahan dan penanganan aktivitas keuangan ilegal, termasuk pinjol ilegal.[^ojk-satgas] Selain itu, IASC berperan dalam penanganan penipuan transaksi keuangan dan pemblokiran rekening terkait laporan masyarakat.[^ojk-iasc]

---

## 4. Masalah dari Sistem Existing

Walaupun sistem existing sudah penting dan membantu, masih terdapat beberapa masalah yang dapat menjadi celah penelitian atau novelty untuk SATPAM.

### 4.1 Ekosistem Masih Terpisah-pisah

Saat ini, tiap bagian cenderung menangani wilayahnya sendiri.

| Ekosistem | Contoh Data | Masalah Jika Berdiri Sendiri |
|---|---|---|
| **Konten digital** | Domain, link, kata kunci, akun promosi | Bisa tahu kontennya berbahaya, tetapi belum tentu tahu rekening atau aktor di belakangnya |
| **Keuangan** | Rekening, e-wallet, QRIS, nominal transaksi | Bisa tahu transaksi mencurigakan, tetapi belum tentu tahu situs atau iklan asalnya |
| **Aplikasi** | APK, nama aplikasi, permission, developer | Bisa tahu APK mencurigakan, tetapi belum tentu tahu jaringan promosi dan rekeningnya |
| **Laporan korban** | Kronologi, screenshot, nomor pelaku, bukti transfer | Data korban kuat, tetapi sulit langsung menghubungkannya ke jaringan lama |
| **Penegakan hukum** | Bukti, kasus, pelaku, pasal hukum | Butuh prioritas dan jalur bukti yang rapi |

Masalah intinya:

> Setiap sistem punya potongan puzzle, tetapi potongan tersebut belum tentu tersusun menjadi satu gambar besar.

### 4.2 Sistem Cenderung Reaktif

Banyak proses berjalan setelah:

- situs sudah ditemukan,
- korban sudah melapor,
- transaksi sudah terjadi,
- aplikasi sudah menyebar,
- rekening sudah dipakai.

Akibatnya, sistem kuat untuk merespons, tetapi masih bisa ditingkatkan menjadi sistem yang lebih prediktif atau berbasis **early warning**.

### 4.3 Pelaku Mudah Berganti Identitas Digital

Pelaku dapat berganti:

- domain,
- link shortener,
- nomor WhatsApp,
- akun promosi,
- rekening,
- QRIS,
- nama aplikasi,
- package name APK.

Maka sistem yang hanya berfokus pada satu entitas seperti satu link atau satu rekening akan mudah tertinggal.

### 4.4 Output Sering Berupa Blokir, Bukan Pemetaan Jaringan

Output sistem existing biasanya berupa:

- link diblokir,
- konten dihapus,
- rekening diblokir,
- aplikasi ditutup,
- laporan diteruskan.

SATPAM ingin menambahkan output berupa:

- jalur hubungan,
- skor risiko,
- cluster jaringan,
- node paling berbahaya,
- prioritas tindakan,
- alasan deteksi yang explainable.

---

## 5. Gap dan Novelty SATPAM

SATPAM tidak diposisikan sebagai pengganti Komdigi, OJK, PPATK, IASC, atau kepolisian. SATPAM diposisikan sebagai **sistem pendukung analisis** yang menyatukan berbagai entitas ke dalam satu graf risiko.

### 5.1 Gap Utama

| Gap | Dampak | Solusi SATPAM |
|---|---|---|
| Data masih tersebar | Hubungan antar entitas sulit terlihat | Menyatukan data ke dalam graph database |
| Sistem masih reaktif | Korban bisa bertambah sebelum tindakan | Early warning dan risk scoring |
| Pelaku cepat berganti identitas | Situs/rekening baru terus muncul | Deteksi pola regenerasi jaringan |
| Output belum selalu explainable | Sulit menjelaskan alasan risiko | Menampilkan jalur bukti |
| Banyak entitas harus ditangani | Prioritas tindakan sulit ditentukan | Risk-based prioritization |
| Judol dan pinjol sering dianalisis terpisah | Hubungan sosial-ekonomi tidak terlihat | Judol-pinjol linkage detection |

### 5.2 Novelty Utama

Novelty SATPAM adalah:

> Membangun sistem **graph intelligence** yang menghubungkan laporan masyarakat, domain, APK, rekening, e-wallet, QRIS, nomor WhatsApp, akun promosi, blacklist, dan pola transaksi menjadi satu peta risiko yang dapat ditelusuri menggunakan algoritma AI searching.

Novelty ini berbeda dari sistem deteksi biasa karena SATPAM tidak hanya bertanya:

> “Apakah link ini berbahaya?”

Tetapi juga bertanya:

> “Link ini terhubung ke siapa saja, melalui jalur apa, dan bagian mana yang harus diprioritaskan?”

---

## 6. Konsep Dasar SATPAM

SATPAM bekerja dengan prinsip:

```text
Input Data
→ Ekstraksi Entitas
→ Pembentukan Graph
→ AI Search
→ Risk Scoring
→ Visualisasi dan Rekomendasi
```

Secara sederhana:

1. User atau sistem memasukkan data mencurigakan.
2. Sistem mengambil entitas penting seperti URL, rekening, nomor HP, keyword, dan APK.
3. Entitas tersebut disimpan sebagai node dalam graph database.
4. Hubungan antar entitas disimpan sebagai relationship.
5. Algoritma search mencari jalur risiko.
6. Sistem menghitung skor risiko.
7. Sistem menampilkan hasil dalam bentuk jalur bukti, skor, dan rekomendasi.

---

## 7. Kenapa Menggunakan Graph Database seperti Neo4j?

Neo4j menggunakan model **property graph**, yaitu model data yang terdiri dari **nodes**, **relationships**, dan **properties**.[^neo4j-concepts]

| Konsep | Penjelasan | Contoh di SATPAM |
|---|---|---|
| **Node** | Objek atau entitas | Domain, rekening, korban, APK, nomor WA |
| **Relationship** | Hubungan antar entitas | `CONTACTS`, `TRANSFERRED_TO`, `PROMOTES` |
| **Property** | Detail tambahan | skor risiko, tanggal laporan, nominal transaksi |

Graph database cocok karena masalah judol-pinjol adalah masalah jaringan. Dalam kasus ini, hubungan antar data sering kali lebih penting daripada data tunggal.

Contoh:

```text
(Korban)
  └── REPORTED ──> (Laporan)
                    └── MENTIONS ──> (Link)
                                      └── REDIRECTS_TO ──> (Domain Judol)
                                                           └── CONTACTS ──> (WhatsApp Admin)
                                                                             └── USES_ACCOUNT ──> (Rekening)
```

Tanpa graph database, sistem hanya melihat potongan data. Dengan graph database, sistem dapat melihat relasi dan jalur antar data.

---

## 8. Input Data SATPAM

Input SATPAM tidak harus hanya dari laporan masyarakat. Input dapat berasal dari beberapa sumber, tergantung level implementasi.

### 8.1 Sumber Input

| Sumber Input | Contoh Data | Cocok untuk Prototype? | Catatan |
|---|---|---:|---|
| **Laporan masyarakat** | Link, nomor WA, rekening, screenshot, kronologi | Ya | Paling aman dan mudah dijelaskan |
| **Crawler / scraper publik** | Website mencurigakan, teks iklan, domain, shortlink | Ya, jika legal | Harus memperhatikan aturan platform |
| **Database blacklist** | Daftar domain, rekening, nomor HP, APK lama | Ya | Bisa menggunakan data dummy |
| **Media sosial publik** | Komentar spam, link bio, hashtag | Terbatas | Perlu hati-hati dengan privasi dan ToS |
| **APK analysis** | Permission, package name, nama aplikasi | Bisa dengan simulasi | Jangan mengunduh APK ilegal sembarangan |
| **Data transaksi simulasi** | Transfer korban ke rekening tertentu | Ya | Cocok untuk demo |
| **Log trafik otomatis** | DNS log, access log, domain request | Bisa untuk simulasi | Data asli butuh izin |
| **Data bank/e-wallet/PPATK** | Rekening dan aliran dana | Tidak untuk prototype umum | Butuh akses resmi dan perlindungan privasi |

### 8.2 Rekomendasi untuk Prototype

Untuk tugas kuliah atau proposal, input yang paling aman adalah:

```text
Laporan masyarakat + crawler finding dummy/simulasi + blacklist dummy + data transaksi simulasi
```

Untuk implementasi nyata, sistem dapat dikembangkan menjadi:

```text
Laporan masyarakat + crawler publik + blacklist resmi + log trafik + data transaksi resmi yang dianonimkan
```

---

## 9. Model Data Graf SATPAM

### 9.1 Jenis Node

| Node | Deskripsi |
|---|---|
| `Report` | Laporan masyarakat |
| `Victim` | Korban atau pelapor |
| `Domain` | Situs judol, landing page, shortlink |
| `SocialMediaAccount` | Akun promosi di Instagram, TikTok, Telegram, dan platform lain |
| `PhoneNumber` | Nomor WhatsApp admin atau debt collector |
| `BankAccount` | Rekening bank |
| `EWallet` | Dompet digital |
| `QRISMerchant` | Merchant QRIS |
| `APK` | Aplikasi pinjol ilegal atau aplikasi judol |
| `Keyword` | Kata promosi seperti “slot”, “maxwin”, “cair cepat” |
| `Transaction` | Catatan transaksi atau transfer |
| `BlacklistEntity` | Entitas yang pernah dilaporkan atau diblokir |
| `Cluster` | Kelompok jaringan mencurigakan |

### 9.2 Jenis Relationship

| Relationship | Makna |
|---|---|
| `REPORTED` | Korban membuat laporan |
| `MENTIONS` | Laporan menyebut entitas tertentu |
| `REDIRECTS_TO` | Link mengarah ke domain lain |
| `PROMOTES` | Akun promosi menyebarkan link/domain |
| `CONTACTS` | Domain mengarah ke nomor WhatsApp |
| `USES_ACCOUNT` | Admin atau domain menggunakan rekening |
| `TRANSFERRED_TO` | Korban mentransfer uang ke rekening |
| `LINKED_TO_APK` | Domain mengarah ke aplikasi tertentu |
| `REQUESTS_PERMISSION` | APK meminta permission tertentu |
| `SIMILAR_TO` | Entitas mirip dengan entitas lama |
| `PART_OF_CLUSTER` | Entitas termasuk dalam cluster tertentu |
| `BLACKLISTED_AS` | Entitas masuk daftar hitam tertentu |

---

## 10. Arsitektur Sistem SATPAM

| Lapisan | Fungsi |
|---|---|
| **Input Layer** | Menerima laporan, URL, nomor HP, rekening, APK, atau data simulasi |
| **Entity Extraction Layer** | Mengekstrak URL, nomor HP, rekening, keyword, dan nama aplikasi |
| **Graph Builder** | Membuat node dan relationship |
| **Graph Database** | Menyimpan ekosistem dalam Neo4j |
| **Search Algorithm Engine** | Menjalankan BFS sebagai core, dengan UCS, BDS, atau A* sebagai opsi lanjutan |
| **Risk Scoring Engine** | Menghitung skor risiko setiap node dan path |
| **Graph Analytics Engine** | Menjalankan rule-based cluster dan degree centrality sederhana |
| **Explainability Layer** | Menampilkan alasan risiko dan jalur bukti |
| **Dashboard** | Menampilkan graf, skor risiko, cluster, dan rekomendasi |

Contoh alur:

```text
Input laporan
→ Entity extraction
→ Neo4j graph database
→ AI search
→ Risk scoring
→ Explainable result
→ Dashboard
```

---

## 11. Penerapan Algoritma Searching AI

Neo4j Graph Data Science menyediakan berbagai algoritma path finding, termasuk **Dijkstra**, **A\***, dan **Breadth First Search**.[^neo4j-pathfinding] BFS sendiri bekerja dengan mengunjungi node berdasarkan jarak yang semakin meningkat dari node awal.[^neo4j-bfs]

### 11.1 Tabel Algoritma

| Algoritma | Fungsi dalam SATPAM | Contoh |
|---|---|---|
| **BFS** | Mencari semua koneksi terdekat dari satu entitas | Dari domain judol, cari nomor WA, rekening, dan akun promosi dalam 2–3 langkah |
| **DFS** | Menelusuri satu jalur sampai dalam | Dari iklan → link → domain → WA → rekening |
| **DLS** | DFS dengan batas kedalaman | Cari koneksi maksimal sampai kedalaman 4 |
| **IDS** | Pencarian bertahap dari kedalaman kecil ke besar | Cek kedalaman 1, 2, 3 sampai pola ditemukan |
| **UCS** | Mencari jalur dengan cost paling optimal | Pilih jalur tindakan dengan biaya investigasi paling rendah |
| **BDS** | Mencari dari dua arah | Dari laporan korban dan blacklist lama, lalu cari titik temu |
| **A\*** | Mencari jalur paling menjanjikan berdasarkan heuristic | Prioritaskan jalur yang paling mungkin ilegal dan paling berdampak |

### 11.2 Algoritma yang Paling Direkomendasikan

Untuk prototype SATPAM, metode utama yang paling realistis adalah:

> **Graph modeling + BFS evidence path + rule-based risk scoring**

Alasannya:

- BFS mudah dijelaskan untuk menelusuri hubungan terdekat,
- rule-based risk scoring lebih transparan untuk prototype,
- graph modeling tetap menunjukkan hubungan lintas entitas,
- output bisa menghasilkan jalur bukti yang explainable,
- A\* Search tetap dapat diposisikan sebagai metode tambahan jika heuristic dan bobot edge sudah terdokumentasi.

---

## 12. Deteksi Aliran Dana

Deteksi aliran dana dalam SATPAM sebaiknya tidak hanya menggunakan satu algoritma. Sistem dapat menggabungkan beberapa pendekatan:

```text
Graph Search + Rule-Based Risk Scoring + Degree Centrality Sederhana
```

### 12.1 Model Aliran Dana

Contoh:

```text
(Korban) --TRANSFERRED_TO--> (Rekening A)
(Rekening A) --TRANSFERRED_TO--> (Rekening B)
(Rekening B) --TRANSFERRED_TO--> (EWallet C)
(EWallet C) --CASH_OUT_TO--> (Rekening D)
```

### 12.2 Algoritma untuk Aliran Dana

| Kebutuhan | Algoritma |
|---|---|
| Menelusuri uang dari korban | BFS |
| Mencari jalur berbobot | UCS/Dijkstra, opsional |
| Mencari titik temu dengan rekening blacklist | Bi-Directional Search, opsional |
| Menentukan jalur paling prioritas | Rule-based Risk Scoring + BFS evidence path |
| Menghitung risiko rekening | Rule-based Risk Scoring |
| Menemukan kelompok rekening | Rule-based cluster / connected component |
| Mencari rekening pusat | Degree Centrality sederhana |
| Mendeteksi pola transaksi mencurigakan | Rule-based transaction pattern detection |

### 12.3 Risk Scoring untuk Aliran Dana

Contoh indikator risiko:

| Indikator | Penjelasan |
|---|---|
| Banyak transaksi kecil dari banyak korban | Indikasi rekening kolektor |
| Dana masuk lalu cepat keluar | Indikasi rekening transit |
| Terhubung ke domain judol | Risiko meningkat |
| Terhubung ke nomor WA yang dilaporkan | Risiko meningkat |
| Terhubung ke blacklist lama | Risiko sangat tinggi |
| Transaksi berlapis | Indikasi layering |
| Banyak transaksi di waktu singkat | Indikasi aktivitas terorganisir |
| Terhubung ke APK pinjol ilegal | Risiko gabungan judol-pinjol |

Contoh formula sederhana:

```text
Risk Score =
30% laporan masyarakat
+ 20% koneksi ke blacklist
+ 20% pola transaksi mencurigakan
+ 15% hubungan dengan domain/APK ilegal
+ 15% kecepatan dana masuk-keluar
```

### 12.4 Cluster Sederhana dan Centrality

Untuk MVP, cluster dapat dibuat secara sederhana dari connected component atau rule relasi yang sama, misalnya rekening dan domain yang muncul pada beberapa laporan. Centrality dapat digunakan untuk mencari node penting, misalnya rekening yang paling banyak menerima transfer atau menjadi jembatan aliran dana. Neo4j memiliki algoritma seperti Degree Centrality untuk mengukur jumlah hubungan masuk atau keluar dari sebuah node.[^neo4j-degree]

Dalam konteks SATPAM:

- **Rule-based cluster / connected component** membantu menemukan cluster rekening mencurigakan tanpa perlu algoritma berat.
- **Degree Centrality** membantu menemukan rekening yang paling banyak terhubung.
- **Betweenness Centrality** dapat menjadi pengembangan lanjutan untuk menemukan rekening yang menjadi jembatan antar cluster.
- **PageRank** dapat menjadi pengembangan lanjutan untuk menemukan entitas paling berpengaruh dalam jaringan.

---

## 13. A* Opsional dan Heuristic Prototype

A\* Search dapat dipakai sebagai metode tambahan untuk risk-prioritized path search jika heuristic dan bobot edge sudah dijelaskan sebagai rule prototype, bukan sebagai model forensik final. A\* Search menggunakan konsep:

```text
f(n) = g(n) + h(n)
```

Dalam SATPAM:

| Komponen | Makna |
|---|---|
| `g(n)` | Cost aktual dari jalur yang sudah dilewati |
| `h(n)` | Estimasi risiko ke depan |
| `f(n)` | Nilai prioritas jalur |

Contoh heuristic konfigurasi prototype:

| Heuristic | Bobot Risiko Contoh |
|---|---:|
| Domain mirip situs judol lama | +25 |
| Nomor WA pernah dilaporkan | +30 |
| Rekening menerima banyak transaksi kecil | +25 |
| Dana keluar kurang dari 10 menit | +20 |
| Terhubung ke blacklist lama | +35 |
| Mengandung keyword “slot”, “maxwin”, “bonus” | +15 |
| APK meminta akses kontak/SMS | +25 |
| Terhubung ke APK pinjol ilegal | +25 |
| Akun promosi menyasar pelajar | +30 |

Contoh hasil:

```text
Path 1:
Korban → Link → Domain
Risk Score: 45

Path 2:
Korban → Link → Domain → WA Admin → Rekening → APK Pinjol
Risk Score: 91

Sistem memprioritaskan Path 2 karena lebih berisiko.
```

---

## 14. Contoh Use Case Sistem

### 14.1 Use Case 1: Laporan Link Judol

Input:

```json
{
  "source": "user_report",
  "url": "https://contoh-slot-bonus.com",
  "phone": "08xxxxxxxxxx",
  "bank_account": "123456789",
  "description": "Saya diarahkan dari iklan Instagram ke situs slot, lalu diminta transfer."
}
```

Output:

```text
Risk Score: 88/100
Kategori: Judol

Jalur ditemukan:
Laporan → Link → Domain Judol → WhatsApp Admin → Rekening

Alasan:
- Domain mengandung keyword promosi judol
- Nomor WA pernah muncul di laporan lain
- Rekening menerima banyak transaksi kecil
```

### 14.2 Use Case 2: Deteksi Keterkaitan Judol dan Pinjol Ilegal

Input:

```text
Korban kalah di situs judol, lalu menerima tawaran APK pinjol cepat cair.
```

Output:

```text
Risk Score: 93/100
Kategori: Judol terhubung pinjol ilegal

Jalur:
Korban → Situs Judol → WA Admin → APK Pinjol → Akses Kontak → Ancaman Debt Collector

Rekomendasi:
- Tandai APK sebagai risiko tinggi
- Telusuri nomor WA dan rekening
- Hubungkan ke laporan korban lain
```

### 14.3 Use Case 3: Deteksi Aliran Dana

Input:

```text
Rekening A menerima banyak transfer kecil dari banyak korban.
```

Output:

```text
Risk Score: 91/100
Kategori: Rekening kolektor/transit

Jalur:
Korban 1, 2, 3 → Rekening A → Rekening B → E-Wallet C

Alasan:
- Banyak incoming transfer
- Dana cepat keluar
- Terhubung ke domain judol
- Terhubung ke rekening blacklist
```

---

## 15. Output Sistem

Output SATPAM tidak hanya berupa label “aman” atau “berbahaya”, tetapi berupa analisis yang lebih lengkap.

| Output | Contoh |
|---|---|
| Skor risiko | 91/100 |
| Kategori | Judol, pinjol ilegal, scam, gabungan judol-pinjol |
| Jalur bukti | Link → Domain → WA → Rekening → APK |
| Cluster jaringan | Cluster rekening dan domain terkait |
| Node prioritas | Rekening A, nomor WA B, domain C |
| Alasan risiko | Terhubung ke blacklist, banyak laporan, pola transaksi mencurigakan |
| Rekomendasi tindakan | Review pemblokiran setelah verifikasi manusia, investigasi rekening, tandai APK sebagai kandidat review |
| Level confidence | Rendah, sedang, tinggi |

---

## 16. Perbedaan Sistem Existing dan SATPAM

| Sistem Existing | SATPAM |
|---|---|
| Fokus pada konten, laporan, transaksi, atau penindakan secara terpisah | Menghubungkan semua ekosistem dalam satu graf |
| Output sering berupa blokir atau laporan | Output berupa jalur risiko, skor, cluster, dan rekomendasi |
| Sulit melihat hubungan lintas kanal | Memetakan hubungan domain, rekening, APK, WA, dan korban |
| Analisis sering reaktif | Bisa dikembangkan menjadi early warning |
| Deteksi satu entitas | Deteksi jaringan dan pola regenerasi |
| Kurang explainable untuk pengguna awam | Menampilkan path sebagai alasan risiko |

---

## 17. Batasan dan Etika

Karena sistem ini menyentuh data sensitif, SATPAM harus memiliki batasan etis yang jelas.

### 17.1 Batasan Sistem

| Batasan | Penjelasan |
|---|---|
| Tidak menggantikan aparat | Sistem hanya memberi rekomendasi dan analisis |
| Tidak melakukan hacking | Sistem hanya memakai data legal, simulasi, atau data berizin |
| Tidak melakukan transaksi ilegal | Sistem tidak mencoba mendaftar, membayar, atau masuk ke layanan ilegal |
| Data korban harus dianonimkan | Identitas korban harus dilindungi |
| Data rekening asli harus berizin | Untuk prototype, gunakan data dummy |
| Hasil AI harus diverifikasi manusia | Sistem dapat salah atau false positive |

### 17.2 Prinsip Etika

- Gunakan data simulasi untuk prototype.
- Hindari scraping agresif.
- Patuhi aturan platform.
- Jangan menyebarkan link judol/pinjol ilegal.
- Jangan menyimpan data pribadi korban secara terbuka.
- Jangan menuduh entitas sebagai pelaku tanpa verifikasi.
- Gunakan istilah “terindikasi” atau “berisiko” sebelum ada validasi resmi.

---

## 18. Rekomendasi Scope Prototype

Untuk tugas kuliah, disarankan membuat prototype sederhana dengan scope berikut:

### 18.1 Fitur Minimum

| Fitur | Deskripsi |
|---|---|
| Form laporan | Input link, nomor WA, rekening, dan deskripsi |
| Entity extraction sederhana | Regex untuk URL, nomor HP, rekening, dan keyword |
| Graph builder | Simpan node dan relationship |
| Graph visualization | Tampilkan jaringan sederhana |
| BFS atau DFS | Cari koneksi dari laporan |
| A\* Search | Prioritaskan path risiko |
| Risk scoring | Hitung skor berdasarkan rule |
| Dashboard hasil | Tampilkan skor, path, dan alasan |

### 18.2 Data Prototype

Gunakan data dummy seperti:

- 10 laporan korban,
- 15 domain,
- 10 nomor WhatsApp,
- 10 rekening,
- 5 APK,
- 5 akun promosi,
- 3 cluster jaringan,
- beberapa blacklist dummy.

### 18.3 Teknologi yang Bisa Digunakan

| Komponen | Teknologi |
|---|---|
| Backend | Python FastAPI / Node.js Express |
| Graph Database | Neo4j |
| Search Algorithm | Python / JavaScript |
| Dashboard | React / Vue / Laravel Blade |
| Visualisasi Graf | Neo4j Bloom / Cytoscape.js / D3.js |
| Entity Extraction | Regex + rule-based NLP sederhana |
| Dataset | Dummy data / simulasi |

---

## 19. Contoh Cypher Neo4j

### 19.1 Membuat Node

```cypher
CREATE (:Domain {
  url: "contoh-slot-bonus.com",
  riskScore: 87,
  category: "judol"
});

CREATE (:PhoneNumber {
  number: "08xxxxxxxxxx",
  reportCount: 12
});

CREATE (:BankAccount {
  accountNumber: "123456789",
  bank: "Bank X",
  reportCount: 8
});
```

### 19.2 Membuat Relationship

```cypher
MATCH (d:Domain {url: "contoh-slot-bonus.com"})
MATCH (p:PhoneNumber {number: "08xxxxxxxxxx"})
CREATE (d)-[:CONTACTS]->(p);
```

### 19.3 Mencari Jalur Risiko

```cypher
MATCH path = (r:Report)-[*1..4]-(target)
WHERE target.riskScore > 80
RETURN path;
```

Artinya:

> Cari jalur dari laporan sampai kedalaman 4 langkah yang terhubung ke entitas dengan skor risiko di atas 80.

---

## 20. Contoh Penjelasan Membumi untuk Tim

SATPAM adalah sistem yang bisa dibayangkan seperti satpam digital. Tugasnya bukan menangkap pelaku, tetapi membantu melihat mana yang mencurigakan dan bagaimana hubungan antar data.

Masalah judol dan pinjol ilegal itu tidak berdiri sendiri. Ada link, website, akun promosi, nomor WhatsApp, rekening, aplikasi, dan korban. Semua itu saling terhubung, tetapi biasanya terlihat terpisah.

Sistem existing sudah ada, seperti pemblokiran situs, penanganan pinjol ilegal, laporan korban, dan analisis transaksi. Namun, tiap bagian sering fokus pada wilayahnya sendiri.

SATPAM mencoba menyatukan semuanya ke dalam satu peta besar. Ibarat papan investigasi detektif, setiap link, rekening, nomor, dan aplikasi menjadi titik, lalu hubungan antar titik digambarkan sebagai garis.

Dengan database graf seperti Neo4j, sistem bisa menyimpan data sebagai jaringan. Setelah itu, BFS digunakan untuk mencari jalur hubungan utama, sedangkan UCS, BDS, dan A* dapat menjadi opsi lanjutan jika bobot dan heuristic sudah jelas.

Output SATPAM bukan cuma “ini berbahaya”, tetapi juga “kenapa ini berbahaya”, “terhubung ke siapa saja”, dan “mana yang harus ditangani dulu”.

---

## 21. Judul Proposal yang Direkomendasikan

Beberapa opsi judul:

1. **SATPAM: Search-based AI Threat Prevention and Mapping untuk Deteksi dan Pemetaan Ekosistem Judol-Pinjol Ilegal di Indonesia**
2. **SATPAM: Sistem Graph Intelligence Berbasis A\* Search untuk Deteksi Risiko Judol dan Pinjol Ilegal**
3. **SATPAM: Sistem Pemetaan Ancaman Judol-Pinjol Ilegal Berbasis Graph Database dan AI Search**
4. **SATPAM: Search-based AI Threat Prevention and Mapping Berbasis Neo4j untuk Analisis Jaringan Judol dan Pinjol Ilegal**

Judul yang paling direkomendasikan:

> **SATPAM: Search-based AI Threat Prevention and Mapping Berbasis Graph Search untuk Deteksi dan Prioritisasi Ekosistem Judol-Pinjol Ilegal di Indonesia**

---

## 22. Kesimpulan

SATPAM merupakan konsep sistem AI yang memandang judol dan pinjol ilegal sebagai **ekosistem jaringan**, bukan sebagai kasus tunggal. Sistem ini memanfaatkan graph database untuk menyatukan berbagai entitas seperti korban, laporan, domain, APK, nomor WhatsApp, rekening, e-wallet, QRIS, akun promosi, dan blacklist.

Dengan metode seperti BFS untuk evidence path, rule-based risk scoring, degree centrality sederhana, serta A\* Search/UCS/BDS sebagai opsi lanjutan, SATPAM dapat mencari jalur risiko, menghubungkan laporan baru dengan jaringan lama, menelusuri aliran dana, dan memberi prioritas tindakan.

Novelty utama SATPAM adalah kemampuannya untuk mengubah data yang sebelumnya terpisah-pisah menjadi **graph intelligence** yang explainable. Dengan begitu, sistem tidak hanya memberi label “berbahaya”, tetapi juga menjelaskan hubungan, jalur bukti, skor risiko, dan rekomendasi penanganan.

Untuk prototype, SATPAM dapat dibuat dengan data simulasi, laporan dummy, crawler finding dummy/simulasi, dan Neo4j. Untuk implementasi nyata, sistem memerlukan integrasi data resmi, perlindungan privasi, dan verifikasi manusia.

---

## Referensi

[^komdigi-ais]: Kementerian Komunikasi dan Informatika / Komdigi, *Blokir Situs, Sehatkan Ruang Digital*. https://www.komdigi.go.id/berita/artikel/detail/blokir-situs-sehatkan-ruang-digital

[^ojk-satgas]: Otoritas Jasa Keuangan, *Sektor Jasa Keuangan Terjaga Stabil dan Didukung Kinerja Intermediasi yang Semakin Kuat*. https://ojk.go.id/id/berita-dan-kegiatan/siaran-pers/Pages/Sektor-Jasa-Keuangan-Terjaga-Stabil-dan-Didukung-Kinerja-Intermediasi-yang-Semakin-Kuat.aspx

[^ojk-iasc]: Otoritas Jasa Keuangan, *Waspada Penipuan Website Mengatasnamakan Indonesia Anti-Scam Centre (IASC)*. https://ojk.go.id/id/berita-dan-kegiatan/info-terkini/Pages/Waspada-Penipuan-Website-Mengatasnamakan-Indonesia-Anti-Scam-Centre-IASC.aspx

[^ppatk-perang-total]: PPATK, *Pemerintah Tegaskan Perang Total terhadap Judi Online dan Pencucian Uang*. https://www.ppatk.go.id/news/read/1555/pemerintah-tegaskan-perang-total-terhadap-judi-online-dan-pencucian-uang.html

[^ppatk-2025]: PPATK, *Catatan Capaian Strategis PPATK Tahun 2025*. https://www.ppatk.go.id/siaran_pers/read/1594/catatan-capaian-strategis-ppatk-tahun-2025-menjaga-kedaulatan-dan-integritas-ekonomi-bangsa-jakarta-28-januari-2026-b001hm0531i2026-.html

[^neo4j-concepts]: Neo4j Documentation, *Graph database concepts*. https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/

[^neo4j-pathfinding]: Neo4j Graph Data Science Documentation, *Path finding*. https://neo4j.com/docs/graph-data-science/current/algorithms/pathfinding/

[^neo4j-bfs]: Neo4j Graph Data Science Documentation, *Breadth First Search*. https://neo4j.com/docs/graph-data-science/current/algorithms/bfs/

[^neo4j-community]: Neo4j Graph Data Science Documentation, *Community detection*. https://neo4j.com/docs/graph-data-science/current/algorithms/community/

[^neo4j-degree]: Neo4j Graph Data Science Documentation, *Degree Centrality*. https://neo4j.com/docs/graph-data-science/current/algorithms/degree-centrality/

[^neo4j-fraud]: Neo4j Blog, *Using Graph Data Science for Financial Fraud Detection*. https://neo4j.com/blog/financial-fraud-detection-graph-data-science-analytics-feature-engineering
