# Latar Belakang, Gap, dan Inovasi Sistem SATPAM

## SATPAM: Search-based AI Threat Prevention and Mapping

---

## 1. Latar Belakang / Pendahuluan

Perkembangan teknologi digital di Indonesia membawa dampak besar terhadap cara masyarakat berkomunikasi, bertransaksi, dan mengakses layanan keuangan. Namun, perkembangan tersebut juga membuka ruang bagi munculnya berbagai bentuk kejahatan digital, salah satunya adalah **judi online (judol)** dan **pinjaman online (pinjol) ilegal**. Kedua masalah ini tidak hanya berdampak pada aspek teknologi, tetapi juga menyentuh aspek sosial, ekonomi, hukum, dan keamanan nasional.

Judi online menjadi masalah yang sangat serius karena dapat menyebabkan kecanduan, kerugian ekonomi, konflik keluarga, penurunan produktivitas, dan dorongan untuk mencari uang tambahan melalui cara yang berisiko seperti pinjol ilegal. Di sisi lain, pinjol ilegal sering memanfaatkan kondisi korban yang sedang terdesak secara finansial dengan menawarkan pinjaman cepat, bunga tidak wajar, ancaman penyebaran data pribadi, dan praktik penagihan yang intimidatif.

Masalah judol dan pinjol ilegal juga tidak dapat dilihat sebagai dua masalah yang benar-benar terpisah. Dalam banyak kasus, seseorang yang mengalami kerugian akibat judol dapat menjadi lebih rentan terhadap tawaran pinjol ilegal. Sebaliknya, pinjol ilegal juga dapat menjadi bagian dari ekosistem digital yang sama dengan berbagai bentuk penipuan, promosi ilegal, penyalahgunaan data pribadi, dan aliran dana mencurigakan.

Dari sisi skala masalah, PPATK mencatat bahwa pada tahun 2025 perputaran dana judi online mencapai **Rp286,84 triliun** dari **422,1 juta transaksi**, dengan sekitar **12,3 juta orang** melakukan deposit melalui bank, e-wallet, dan QRIS. Data ini menunjukkan bahwa judi online bukan sekadar masalah konten digital, tetapi juga berkaitan erat dengan aliran dana, sistem pembayaran, dan aktivitas keuangan yang masif.[^ppatk-2025]

Pemerintah Indonesia sebenarnya telah memiliki berbagai sistem dan lembaga untuk menangani masalah ini. Kominfo/Komdigi memiliki sistem pemantauan dan pemblokiran konten digital ilegal, termasuk melalui mesin crawling AIS. OJK melalui Satgas PASTI melakukan cyber patrol terhadap aktivitas keuangan ilegal, termasuk pinjol ilegal. IASC berperan sebagai pusat penanganan scam transaksi keuangan. PPATK menganalisis aliran dana mencurigakan. Kepolisian menangani aspek penindakan hukum.

Namun, tantangan utamanya adalah bahwa ekosistem judol dan pinjol ilegal bekerja sebagai **jaringan lintas kanal**. Satu kasus dapat melibatkan website, shortlink, akun media sosial, nomor WhatsApp, rekening bank, e-wallet, QRIS, aplikasi APK, korban, dan aliran dana. Jika setiap elemen dianalisis secara terpisah, maka hubungan besar di baliknya sulit terlihat.

Oleh karena itu, diperlukan sebuah pendekatan yang mampu memetakan ekosistem judol dan pinjol ilegal sebagai sebuah **jaringan hubungan**. Dalam konteks inilah sistem **SATPAM (Search-based AI Threat Prevention and Mapping)** diusulkan. SATPAM adalah konsep sistem AI berbasis **graph search** yang memanfaatkan database graf seperti Neo4j untuk menghubungkan berbagai entitas digital dan finansial, lalu menggunakan algoritma searching seperti BFS, DFS, UCS, BDS, dan A* untuk menemukan jalur risiko, koneksi tersembunyi, dan prioritas penanganan.

---

## 2. Sistem yang Sudah Ada Saat Ini

Saat ini, Indonesia telah memiliki beberapa sistem, lembaga, dan mekanisme untuk menangani masalah judi online, pinjol ilegal, dan penipuan digital.

| Sistem / Lembaga | Fokus Utama | Bentuk Penanganan | Keterangan |
|---|---|---|---|
| **Kominfo / Komdigi** | Konten digital ilegal | Pemblokiran website, URL, dan konten negatif | Berfokus pada ruang digital dan konten daring |
| **AIS Kominfo / Komdigi** | Crawling konten negatif | Mengais dan mendeteksi konten internet negatif | Digunakan untuk deteksi konten dalam skala besar |
| **OJK / Satgas PASTI** | Aktivitas keuangan ilegal | Cyber patrol, pemblokiran pinjol ilegal, edukasi masyarakat | Berfokus pada pinjol ilegal, investasi ilegal, dan entitas keuangan ilegal |
| **IASC** | Penipuan transaksi keuangan | Menerima laporan, koordinasi pemblokiran rekening, penyelamatan dana korban | Berfokus pada scam dan transaksi keuangan |
| **PPATK** | Aliran dana mencurigakan | Analisis transaksi keuangan dan dugaan pencucian uang | Berfokus pada financial intelligence |
| **Kepolisian** | Penegakan hukum | Investigasi, penyidikan, dan penindakan pelaku | Berfokus pada proses hukum |

Komdigi memiliki AIS sebagai mesin pengais konten internet negatif yang melakukan crawling terhadap alamat internet. Sistem ini menunjukkan bahwa pemerintah sudah memiliki pendekatan teknologi untuk mendeteksi konten negatif dalam skala besar.[^komdigi-ais]

OJK melalui Satgas PASTI juga telah melakukan cyber patrol dan pemblokiran terhadap aplikasi atau website pinjol ilegal. OJK menyebut bahwa tindakan tegas terhadap pinjol ilegal dilakukan bersama kepolisian dan Kominfo melalui cyber patrol serta pemblokiran aplikasi atau website pinjol ilegal.[^ojk-pinjol-ilegal]

IASC atau Indonesia Anti-Scam Centre juga telah menjadi kanal penting dalam penanganan penipuan transaksi keuangan. OJK menjelaskan bahwa IASC berkaitan dengan penanganan laporan penipuan dan masyarakat diminta selalu mengecek informasi resmi melalui kanal OJK.[^ojk-iasc]

Dengan demikian, dapat disimpulkan bahwa sistem penanganan judol, pinjol ilegal, dan scam digital **sudah ada**, tetapi masih memiliki ruang pengembangan terutama pada aspek integrasi lintas data, pemetaan relasi, dan prioritas risiko.

---

## 3. Masalah pada Sistem Existing

### 3.1 Ekosistem Masih Berjalan Sendiri-sendiri

Masalah utama dari sistem existing adalah ekosistem data yang masih cenderung berjalan sendiri-sendiri. Setiap lembaga memiliki fokus dan sumber data yang berbeda.

| Ekosistem | Contoh Data | Fokus Saat Ini | Kelemahan Jika Terpisah |
|---|---|---|---|
| **Ekosistem konten digital** | Website, URL, domain, akun promosi, keyword | Deteksi dan blokir konten | Sulit melihat rekening, APK, atau aliran dana di balik konten |
| **Ekosistem pinjol ilegal** | Nama aplikasi, website pinjol, entitas ilegal | Penutupan pinjol ilegal | Belum tentu terhubung otomatis dengan judol atau rekening terkait |
| **Ekosistem transaksi** | Rekening, e-wallet, QRIS, nominal transaksi | Analisis keuangan | Sulit mengetahui sumber promosi, website, atau APK asal transaksi |
| **Ekosistem laporan korban** | Kronologi, screenshot, nomor WA, rekening tujuan | Pengaduan dan tindak lanjut | Laporan bisa terisolasi jika tidak dihubungkan ke laporan lain |
| **Ekosistem penegakan hukum** | Bukti, pelaku, kasus, pasal hukum | Penyidikan dan penindakan | Membutuhkan jalur bukti dan prioritas kasus yang jelas |
| **Ekosistem edukasi masyarakat** | Imbauan, artikel, kampanye | Pencegahan umum | Belum tentu personal atau berbasis pola risiko aktual |

Jika ekosistem ini tidak dihubungkan, maka sistem hanya melihat potongan-potongan kecil dari masalah besar. Padahal, dalam praktiknya, satu link judi online dapat terhubung ke akun promosi, nomor WhatsApp admin, rekening bank, e-wallet, APK pinjol ilegal, dan laporan korban lain.

### 3.2 Sistem Masih Cenderung Reaktif

Banyak sistem existing bekerja setelah kasus atau entitas terdeteksi. Misalnya:

- website diblokir setelah ditemukan,
- rekening diblokir setelah dilaporkan,
- pinjol ilegal ditutup setelah teridentifikasi,
- korban melapor setelah mengalami kerugian,
- konten dihapus setelah tersebar.

Pendekatan ini tetap penting, tetapi masih bersifat reaktif. Padahal, pelaku judol dan pinjol ilegal dapat bergerak cepat dengan membuat domain baru, rekening baru, nomor baru, atau aplikasi baru.

### 3.3 Pelaku Mudah Mengganti Identitas Digital

Pelaku dapat dengan mudah mengganti identitas digital, seperti:

- domain website,
- shortlink,
- akun media sosial,
- nomor WhatsApp,
- rekening bank,
- e-wallet,
- QRIS merchant,
- nama APK,
- package name aplikasi,
- template halaman promosi.

Akibatnya, sistem yang hanya memblokir satu entitas tidak selalu mampu memutus jaringan secara keseluruhan.

### 3.4 Output Sistem Existing Belum Selalu Berupa Pemetaan Jaringan

Sistem existing biasanya menghasilkan output seperti:

- link diblokir,
- aplikasi ditutup,
- rekening diblokir,
- laporan diteruskan,
- konten dihapus.

Output tersebut penting, tetapi belum selalu menunjukkan:

- entitas ini terhubung ke siapa saja,
- jalur uang mengalir ke mana,
- nomor WhatsApp ini muncul di laporan mana saja,
- domain ini mirip dengan domain lama atau tidak,
- rekening mana yang menjadi pusat jaringan,
- entitas mana yang harus ditangani lebih dulu.

Di sinilah pendekatan graph intelligence menjadi relevan.

---

## 4. Perbedaan Sistem Existing dengan SATPAM

| Aspek | Sistem Existing | SATPAM |
|---|---|---|
| Cara melihat masalah | Melihat konten, laporan, transaksi, atau aplikasi secara terpisah | Melihat seluruh entitas sebagai jaringan yang saling terhubung |
| Fokus utama | Deteksi, pemblokiran, laporan, atau penindakan | Deteksi, pemetaan, pencarian jalur, risk scoring, dan prioritas tindakan |
| Model data | Umumnya berbasis daftar, laporan, tabel, atau sistem terpisah | Berbasis graph database dengan node dan relationship |
| Output | Link diblokir, rekening diblokir, aplikasi ditutup | Jalur risiko, skor risiko, cluster jaringan, node prioritas, alasan deteksi |
| Kemampuan analisis relasi | Terbatas jika data berada di sistem berbeda | Kuat karena relasi menjadi inti model data |
| Kemampuan explainability | Tidak selalu menunjukkan jalur bukti | Menampilkan path: korban → link → domain → WA → rekening → APK |
| Kesesuaian dengan AI search | Tidak selalu eksplisit | Langsung menggunakan BFS, DFS, UCS, BDS, dan A* |
| Tujuan tambahan | Penindakan terhadap entitas tertentu | Pemutusan jaringan dan early warning |

---

## 5. Gap Penelitian / Celah yang Diambil

Berdasarkan kondisi sistem existing, gap penelitian yang dapat diambil adalah sebagai berikut:

| No | Gap | Penjelasan |
|---|---|---|
| 1 | **Integrasi lintas ekosistem belum optimal** | Data konten, laporan, transaksi, aplikasi, dan rekening belum tentu berada dalam satu model hubungan yang terpadu |
| 2 | **Hubungan judol dan pinjol ilegal belum banyak dipetakan sebagai satu jaringan risiko** | Judol dan pinjol ilegal sering dibahas terpisah, padahal dapat saling berhubungan dalam siklus kerugian korban |
| 3 | **Sistem existing lebih banyak berorientasi pada pemblokiran entitas** | Pemblokiran penting, tetapi belum cukup untuk melihat jaringan di balik entitas tersebut |
| 4 | **Belum ada pemetaan jalur risiko yang explainable** | Sistem perlu menunjukkan kenapa sebuah entitas berisiko melalui path yang dapat dipahami |
| 5 | **Prioritas tindakan belum selalu berbasis graph risk** | Banyak entitas mencurigakan membutuhkan mekanisme prioritas berdasarkan dampak dan koneksi |
| 6 | **Regenerasi jaringan belum mudah dideteksi** | Domain, rekening, dan APK baru dapat muncul kembali dengan pola yang mirip |
| 7 | **Data laporan masyarakat belum tentu langsung menjadi graph intelligence** | Laporan masyarakat berisi banyak bukti, tetapi perlu diubah menjadi entitas dan hubungan yang bisa dianalisis |

---

## 6. Inovasi Sistem SATPAM

Inovasi utama SATPAM adalah mengubah pendekatan dari **entity-based detection** menjadi **network-based intelligence**.

### 6.1 Inovasi 1: Graph Intelligence

SATPAM menyimpan data sebagai graf, bukan hanya sebagai daftar kasus. Dalam graf, setiap entitas menjadi node dan setiap hubungan menjadi relationship.

Contoh node:

- `Victim`
- `Report`
- `Domain`
- `Shortlink`
- `SocialMediaAccount`
- `PhoneNumber`
- `BankAccount`
- `EWallet`
- `QRISMerchant`
- `APK`
- `Keyword`
- `Transaction`
- `BlacklistEntity`

Contoh relationship:

- `REPORTED`
- `MENTIONS`
- `REDIRECTS_TO`
- `PROMOTES`
- `CONTACTS`
- `USES_ACCOUNT`
- `TRANSFERRED_TO`
- `LINKED_TO_APK`
- `SIMILAR_TO`
- `PART_OF_CLUSTER`

Neo4j cocok untuk pendekatan ini karena menggunakan model property graph yang terdiri dari node, relationship, dan property.[^neo4j-concepts]

### 6.2 Inovasi 2: Search-based Risk Path

SATPAM menggunakan algoritma searching untuk mencari jalur risiko.

Contoh:

```text
Korban
→ Laporan
→ Link promosi
→ Domain judol
→ WhatsApp admin
→ Rekening
→ APK pinjol ilegal
```

Algoritma yang dapat digunakan:

| Algoritma | Fungsi |
|---|---|
| **BFS** | Mencari koneksi terdekat dari sebuah laporan |
| **DFS** | Menelusuri satu jalur investigasi secara mendalam |
| **DLS** | Membatasi kedalaman pencarian |
| **IDS** | Mencari bertahap dari kedalaman rendah ke tinggi |
| **UCS** | Mencari jalur dengan cost paling optimal |
| **BDS** | Mencari titik temu antara laporan baru dan blacklist lama |
| **A\*** | Mencari jalur paling berisiko menggunakan heuristic |

Neo4j Graph Data Science menyediakan algoritma path finding seperti Dijkstra, A*, Yen’s Shortest Path, dan Breadth First Search.[^neo4j-pathfinding] BFS sendiri merupakan algoritma traversal yang mengunjungi node berdasarkan jarak yang semakin meningkat dari node awal.[^neo4j-bfs]

### 6.3 Inovasi 3: Risk Scoring Berbasis Relasi

SATPAM tidak hanya memberi label “berbahaya” atau “aman”, tetapi menghitung skor risiko berdasarkan hubungan antar entitas.

Contoh indikator risiko:

| Indikator | Dampak terhadap Risiko |
|---|---|
| Entitas pernah dilaporkan | Risiko naik |
| Terhubung ke blacklist lama | Risiko sangat naik |
| Terhubung ke banyak korban | Risiko naik |
| Rekening menerima banyak transaksi kecil | Risiko naik |
| Dana cepat keluar dari rekening | Risiko naik |
| Domain mengandung keyword judol | Risiko naik |
| APK meminta akses kontak/SMS | Risiko naik |
| Nomor WA muncul di banyak laporan | Risiko naik |
| Domain mirip dengan domain lama | Risiko naik |

Contoh formula sederhana:

```text
Risk Score =
30% laporan masyarakat
+ 20% koneksi ke blacklist
+ 20% pola transaksi mencurigakan
+ 15% hubungan dengan domain/APK ilegal
+ 15% kecepatan dana masuk-keluar
```

### 6.4 Inovasi 4: Judol-Pinjol Linkage Detection

SATPAM tidak hanya mendeteksi judol dan pinjol ilegal secara terpisah, tetapi mencari hubungan antara keduanya.

Contoh pola:

```text
Korban melihat iklan judol
→ masuk ke situs judol
→ kalah uang
→ ditawari pinjaman cepat
→ mengunduh APK pinjol ilegal
→ data kontak disalahgunakan
→ korban diteror penagih
```

Inovasi ini penting karena menunjukkan bahwa judol dan pinjol ilegal dapat menjadi bagian dari satu siklus risiko sosial-ekonomi.

### 6.5 Inovasi 5: Prioritas Tindakan Berbasis Risiko

SATPAM dapat membantu menentukan entitas mana yang perlu diprioritaskan.

| Entitas | Skor Risiko | Alasan | Prioritas |
|---|---:|---|---|
| Rekening A | 93 | Terhubung ke 40 korban dan 3 domain judol | Sangat tinggi |
| Nomor WA B | 88 | Muncul di 12 laporan dan 5 website | Tinggi |
| Domain C | 81 | Mengandung keyword judol dan redirect ke WA | Tinggi |
| APK D | 76 | Meminta akses kontak dan SMS | Sedang-tinggi |
| Akun promosi E | 70 | Menyebarkan banyak shortlink | Sedang |

Dengan pendekatan ini, sistem tidak hanya mendeteksi, tetapi juga membantu menjawab:

> “Mana yang harus ditangani lebih dulu agar dampaknya paling besar?”

### 6.6 Inovasi 6: Explainable Detection

SATPAM dapat memberikan alasan deteksi dalam bentuk jalur bukti.

Contoh output:

```text
Risk Score: 91/100
Kategori: Judol terhubung pinjol ilegal

Jalur bukti:
Laporan korban
→ Link promosi
→ Domain judol
→ WhatsApp admin
→ Rekening
→ APK pinjol ilegal

Alasan risiko:
1. Domain mengandung keyword judol.
2. Nomor WA muncul di 12 laporan.
3. Rekening menerima banyak transaksi kecil.
4. APK meminta akses kontak dan SMS.
5. Jalur ini terhubung ke blacklist lama.
```

Dengan demikian, hasil sistem lebih mudah dipahami oleh manusia.

---

## 7. Posisi SATPAM terhadap Sistem Existing

SATPAM tidak menggantikan lembaga atau sistem existing. SATPAM dapat diposisikan sebagai sistem pendukung analisis.

| Sistem Existing | Peran SATPAM sebagai Pelengkap |
|---|---|
| Komdigi memblokir konten | SATPAM membantu menunjukkan hubungan konten dengan rekening, WA, APK, dan laporan |
| OJK/Satgas PASTI menangani pinjol ilegal | SATPAM membantu melihat hubungan pinjol ilegal dengan judol, akun promosi, dan korban |
| IASC menerima laporan scam | SATPAM membantu mengubah laporan menjadi graph intelligence |
| PPATK menganalisis transaksi | SATPAM secara konseptual membantu menghubungkan pola transaksi dengan entitas digital |
| Kepolisian menindak pelaku | SATPAM membantu menyediakan jalur bukti dan prioritas investigasi |

Kalimat posisi yang aman:

> SATPAM bukan pengganti sistem pemerintah, melainkan konsep sistem pendukung analisis yang menghubungkan data lintas ekosistem menjadi graph intelligence untuk membantu deteksi, pemetaan, dan prioritas risiko.

---

## 8. Rumusan Masalah

Berdasarkan latar belakang dan gap di atas, rumusan masalah yang dapat digunakan adalah:

1. Bagaimana merancang sistem AI berbasis graph search untuk memetakan ekosistem judol dan pinjol ilegal?
2. Bagaimana menghubungkan data laporan masyarakat, domain, nomor WhatsApp, rekening, APK, dan blacklist ke dalam satu graph database?
3. Bagaimana menerapkan algoritma searching seperti BFS, DFS, UCS, BDS, dan A* untuk menemukan jalur risiko?
4. Bagaimana sistem dapat memberikan skor risiko dan prioritas tindakan berdasarkan hubungan antar entitas?
5. Bagaimana sistem dapat menampilkan hasil deteksi secara explainable melalui jalur bukti?

---

## 9. Tujuan Penelitian / Pengembangan

Tujuan dari penelitian atau pengembangan sistem SATPAM adalah:

1. Merancang konsep sistem AI untuk mendeteksi dan memetakan ekosistem judol-pinjol ilegal.
2. Membuat model graph database yang dapat menghubungkan berbagai entitas digital dan finansial.
3. Menerapkan algoritma searching untuk menemukan jalur hubungan dan risiko.
4. Menghasilkan risk scoring untuk menilai tingkat bahaya suatu entitas atau jalur.
5. Menampilkan hasil analisis dalam bentuk jalur bukti, skor risiko, dan rekomendasi prioritas.
6. Menunjukkan novelty sistem dibandingkan sistem existing yang masih cenderung terpisah antar ekosistem.

---

## 10. Batasan Penelitian / Sistem

Agar sistem tetap realistis dan etis, batasan yang dapat digunakan adalah:

1. Sistem tidak melakukan hacking atau akses ilegal.
2. Sistem tidak melakukan transaksi pada situs judol atau pinjol ilegal.
3. Prototype menggunakan data dummy, data simulasi, atau data publik yang legal.
4. Data rekening dan data pribadi korban harus dianonimkan.
5. Sistem hanya memberikan status “terindikasi berisiko”, bukan memvonis pelaku.
6. Hasil sistem tetap memerlukan verifikasi manusia.
7. Integrasi dengan data resmi seperti transaksi bank, e-wallet, atau PPATK hanya dapat dilakukan jika ada izin lembaga terkait.

---

## 11. Contoh Narasi Singkat untuk Proposal

Berikut narasi singkat yang bisa digunakan langsung dalam proposal:

> Judi online dan pinjol ilegal merupakan permasalahan digital yang semakin kompleks karena melibatkan banyak entitas seperti website, akun promosi, nomor WhatsApp, rekening, e-wallet, QRIS, aplikasi, korban, dan aliran dana. Pemerintah Indonesia telah memiliki berbagai sistem penanganan seperti pemblokiran konten oleh Komdigi, cyber patrol oleh OJK/Satgas PASTI, pelaporan scam melalui IASC, serta analisis transaksi oleh PPATK. Namun, sistem-sistem tersebut masih cenderung berfokus pada ekosistemnya masing-masing.
>
> Permasalahan utama yang muncul adalah belum optimalnya pemetaan hubungan lintas ekosistem. Padahal, satu kasus judi online dapat terhubung dengan rekening tertentu, nomor WhatsApp admin, akun promosi, aplikasi pinjol ilegal, dan laporan korban lain. Oleh karena itu, dibutuhkan sistem yang tidak hanya mendeteksi satu entitas, tetapi juga memetakan jaringan hubungan antar entitas.
>
> Penelitian ini mengusulkan SATPAM, yaitu Search-based AI Threat Prevention and Mapping, sebagai sistem berbasis graph search untuk mendeteksi dan memetakan risiko judol-pinjol ilegal. SATPAM memanfaatkan graph database untuk menyimpan entitas sebagai node dan hubungan sebagai relationship. Selanjutnya, algoritma searching seperti BFS, DFS, UCS, BDS, dan A* digunakan untuk mencari jalur risiko, menemukan koneksi tersembunyi, dan menentukan prioritas tindakan.
>
> Inovasi utama SATPAM terletak pada pendekatan graph intelligence yang menghubungkan data laporan, domain, rekening, nomor WhatsApp, APK, dan blacklist menjadi satu peta risiko yang explainable. Dengan pendekatan ini, sistem tidak hanya menghasilkan label “berbahaya”, tetapi juga menunjukkan alasan, jalur bukti, skor risiko, dan rekomendasi prioritas penanganan.

---

## 12. Kesimpulan Bagian Pendahuluan dan Gap

Berdasarkan pembahasan di atas, dapat disimpulkan bahwa sistem penanganan judol dan pinjol ilegal di Indonesia sudah ada, tetapi masih memiliki gap dalam aspek integrasi data lintas ekosistem, pemetaan jaringan, explainability, dan prioritas tindakan berbasis risiko.

SATPAM hadir sebagai inovasi yang memandang judol dan pinjol ilegal sebagai masalah jaringan. Dengan menggunakan graph database dan algoritma searching AI, SATPAM dapat membantu menghubungkan berbagai entitas yang sebelumnya terlihat terpisah, mencari jalur risiko, menilai tingkat bahaya, dan memberikan rekomendasi prioritas.

Dengan demikian, novelty SATPAM bukan sekadar mendeteksi situs atau aplikasi ilegal, tetapi membangun sistem **graph intelligence** yang mampu memetakan dan menjelaskan ekosistem judol-pinjol ilegal secara lebih menyeluruh.

---

## Referensi

[^ppatk-2025]: PPATK. (2026). *Catatan Capaian Strategis PPATK Tahun 2025: Menjaga Kedaulatan dan Integritas Ekonomi Bangsa*. https://www.ppatk.go.id/siaran_pers/read/1594/catatan-capaian-strategis-ppatk-tahun-2025-menjaga-kedaulatan-dan-integritas-ekonomi-bangsa-jakarta-28-januari-2026-b001hm0531i2026-.html

[^komdigi-ais]: Kementerian Komunikasi dan Digital. *Mengenal AIS, Mesin Pengais Konten Internet Negatif Milik Kominfo*. https://www.komdigi.go.id/berita/sorotan-media/detail/mengenal-ais-mesin-pengais-konten-internet-negatif-milik-kominfo

[^ojk-pinjol-ilegal]: Otoritas Jasa Keuangan. (2021). *Waspada! Pinjaman Online Ilegal*. https://ojk.go.id/id/berita-dan-kegiatan/info-terkini/Pages/Waspada%21-Pinjaman-Online-Ilegal.aspx

[^ojk-iasc]: Otoritas Jasa Keuangan. (2025). *Waspada Penipuan Website Mengatasnamakan Indonesia Anti-Scam Centre (IASC)*. https://ojk.go.id/id/berita-dan-kegiatan/info-terkini/Pages/Waspada-Penipuan-Website-Mengatasnamakan-Indonesia-Anti-Scam-Centre-IASC.aspx

[^ojk-satgas-pasti]: Otoritas Jasa Keuangan. (2024). *Satgas PASTI Blokir 585 Pinjol Ilegal dan Pinpri serta 17 Investasi Ilegal*. https://ojk.go.id/id/berita-dan-kegiatan/info-terkini/Pages/Satgas-Pasti-Blokir-585-Pinjol-Ilegal-dan-Pinpri-serta-17-Investasi-Ilegal.aspx

[^komdigi-judol]: Kementerian Komunikasi dan Digital. (2024). *Tekan Penyebaran Konten Judi Online, Komdigi Intensifkan Patroli Siber*. https://www.komdigi.go.id/berita/siaran-pers/detail/tekan-penyebaran-konten-judi-online-komdigi-intensifkan-patroli-siber

[^neo4j-concepts]: Neo4j Documentation. *Graph Database Concepts*. https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/

[^neo4j-pathfinding]: Neo4j Graph Data Science Documentation. *Path Finding*. https://neo4j.com/docs/graph-data-science/current/algorithms/pathfinding/

[^neo4j-bfs]: Neo4j Graph Data Science Documentation. *Breadth First Search*. https://neo4j.com/docs/graph-data-science/current/algorithms/bfs/

[^neo4j-fraud]: Neo4j. *Graph Databases for Fraud Detection & Analytics*. https://neo4j.com/use-cases/fraud-detection/
