# Audit Realisme Metode SATPAM

Tanggal audit: 2026-06-03

Target:

| Dokumen | Fokus audit |
|---|---|
| `final_proposal_satpam.pptx` | Apakah klaim slide realistis untuk prototype |
| `SATPAM_Proposal_Comprehensive.md` | Apakah metode yang ditulis layak, terlalu luas, atau perlu diganti |
| `SRS.md` | Pembanding batasan scope prototype |

## Kesimpulan Singkat

SATPAM sudah realistis jika diposisikan sebagai prototype analitik berbasis data dummy, rule-based scoring, graph visualization, dan human verification.

Yang belum sepenuhnya realistis bukan idenya, tetapi beberapa pilihan metode dan wording yang terdengar terlalu besar untuk prototype kecil. Bagian yang paling perlu diganti atau dipersempit adalah A* sebagai algoritma utama, anomaly detection, community detection, crawler sederhana, dan rekomendasi blokir.

## Status Realisme Per Area

| Area | Status | Penilaian | Rekomendasi |
|---|---|---|---|
| Data dummy/simulasi | Realistis | Sangat cocok untuk prototype dan aman secara etika. | Pertahankan. |
| Entity extraction regex/rule-based | Realistis | Cocok untuk URL, domain, nomor WA, rekening dummy, keyword, APK. | Pertahankan sebagai metode utama extraction. |
| Graph database Neo4j | Realistis | Layak untuk demo relasi dan evidence path. | Pertahankan, tetapi batasi ukuran graph. |
| Risk scoring rule-based | Realistis | Cocok untuk prototype karena mudah dijelaskan dan tidak overclaim AI. | Jadikan metode utama analisis risiko. |
| BFS untuk koneksi terdekat | Realistis | Mudah diterapkan dan mudah dijelaskan evaluator. | Jadikan metode pencarian utama untuk evidence path awal. |
| Dijkstra/UCS untuk jalur berbobot | Cukup realistis | Masuk akal jika edge diberi bobot investigasi atau risk cost. | Gunakan jika butuh jalur berbobot; tidak wajib untuk MVP. |
| A* sebagai algoritma utama | Perlu diganti posisi | Bisa dipakai, tetapi rawan dipertanyakan karena heuristic harus jelas dan valid. | Turunkan menjadi metode opsional atau pembanding. |
| DFS/DLS/IDS/BDS lengkap | Terlalu luas | Terlihat seperti daftar algoritma, bukan metode MVP yang fokus. | Pilih 2-3 saja: BFS, Dijkstra/UCS, optional A*. |
| Community detection | Terlalu berat untuk prototype kecil | Neo4j GDS/community detection bisa menambah kompleksitas. | Ganti menjadi rule-based cluster atau degree centrality sederhana. |
| Centrality | Realistis jika sederhana | Degree centrality mudah dihitung dan berguna untuk node prioritas. | Pertahankan hanya degree centrality sederhana. |
| Anomaly detection transaksi | Kurang realistis | Butuh data transaksi cukup banyak dan validasi statistik/model. | Ganti menjadi rule-based transaction pattern detection. |
| Crawler sederhana | Perlu diperjelas | Bisa disalahpahami sebagai crawling target ilegal nyata. | Ganti menjadi crawler finding dummy/simulasi atau crawler publik legal berizin. |
| Traffic log otomatis | Perlu dibatasi | Berisiko dianggap monitoring trafik nyata. | Gunakan traffic log simulasi dengan label `simulation_only`. |
| Output blokir domain | Tidak aman jika tanpa konteks | Bisa terdengar seperti auto-blocking. | Ganti menjadi rekomendasi review pemblokiran setelah approval manusia. |
| Target 1.000 node/5.000 relationship | Cukup realistis | Masuk akal jika dataset dummy dan traversal dibatasi. | Pertahankan sebagai target uji, bukan janji produksi. |

## Bagian Proposal Yang Perlu Diganti Metode

| Lokasi | Isi saat ini | Masalah | Ganti menjadi |
|---|---|---|---|
| `SATPAM_Proposal_Comprehensive.md:338-350` | A* Search disebut algoritma utama paling kuat. | A* klasik butuh cost dan heuristic yang jelas; untuk graph risiko dummy, evaluator bisa bertanya validitas heuristic. | Metode utama: rule-based risk scoring + BFS untuk evidence path. A* dipakai sebagai risk-prioritized path search opsional. |
| `SATPAM_Proposal_Comprehensive.md:377-383` | Deteksi aliran dana memakai BFS/DFS/DLS, BDS, A*, risk scoring, community detection, centrality, anomaly detection. | Terlalu banyak metode untuk prototype kecil. | Gunakan BFS untuk tracing, Dijkstra/UCS opsional untuk weighted path, rule-based transaction pattern detection, dan degree centrality sederhana. |
| `SATPAM_Proposal_Comprehensive.md:383` | Mendeteksi transaksi tidak normal: Anomaly Detection. | Tidak realistis tanpa data transaksi nyata/besar dan baseline normal. | Ganti menjadi rule-based transaction pattern detection. |
| `SATPAM_Proposal_Comprehensive.md:411-413` | Community detection dan centrality. | Community detection bisa terlalu berat jika memakai Neo4j GDS. | Ganti menjadi rule-based cluster berdasarkan connected component atau degree centrality sederhana. |
| `SATPAM_Proposal_Comprehensive.md:424-453` | Heuristic A* diberi banyak bobot risiko. | Bobot terlihat subjektif jika tidak dijelaskan sebagai rule demo. | Tegaskan bobot adalah konfigurasi rule prototype, bukan model statistik/forensik final. |
| `SATPAM_Proposal_Comprehensive.md:562` | Rekomendasi tindakan: Blokir domain, investigasi rekening, tandai APK. | Bisa bertentangan dengan no auto-blocking. | Rekomendasi review pemblokiran, investigasi lanjutan, dan tandai APK sebagai kandidat review. |
| `SATPAM_Proposal_Comprehensive.md:735` | Prototype memakai data simulasi, laporan dummy, crawler sederhana, dan Neo4j. | Crawler sederhana ambigu. | Prototype memakai data simulasi, laporan dummy, import crawler finding dummy, dan Neo4j. |

## Bagian PPT Yang Perlu Disesuaikan

| Slide | Isi saat ini | Status | Rekomendasi |
|---:|---|---|---|
| 5 | A* search + scoring menjadi bagian utama flow. | Masih aman, tapi A* tampak terlalu dominan. | Ubah narasi menjadi graph search + rule scoring; A* disebut opsional/advanced. |
| 6 | A*/BFS UCS/BDS ditampilkan dalam core. | Cukup luas untuk prototype. | Tampilkan BFS + rule scoring sebagai core; UCS/A*/BDS sebagai optional algorithms. |
| 7 | Search: A*, BFS, UCS, BDS. | Terlalu banyak jika disebut semua sebagai implementasi MVP. | Ubah menjadi BFS/evidence path + optional weighted search. |
| 8 | A* risk path untuk prioritas. | Perlu heuristic yang jelas. | Ubah menjadi search-based risk path; A* hanya contoh metode jika heuristic sudah terdokumentasi. |
| 9 | Target MVP 1.000 node, 5.000 relationship, dashboard < 3 detik. | Masih realistis dengan data dummy. | Tegaskan target ini untuk dataset prototype lokal, bukan deployment produksi. |

## Metode Yang Lebih Realistis Untuk Proposal

### Metode Utama Yang Disarankan

```text
1. Data dummy/simulasi
2. Rule-based entity extraction
3. Graph modeling dengan Neo4j
4. BFS untuk evidence path dan neighborhood search
5. Rule-based risk scoring
6. Degree centrality sederhana untuk node prioritas
7. Rule-based cluster sederhana
8. Dashboard explainable
9. Human verification
```

### Metode Opsional/Future Work

```text
1. A* risk-prioritized path search
2. Dijkstra/UCS untuk weighted investigation path
3. Bi-Directional Search untuk menemukan titik temu laporan dan blacklist
4. Community detection dengan Neo4j GDS
5. Anomaly detection berbasis statistik/ML jika data nyata dan baseline tersedia
6. Crawler publik legal berizin
```

## Narasi Pengganti Yang Lebih Aman

Gunakan narasi ini untuk mengganti klaim metode yang terlalu besar:

> Pada tahap prototype, SATPAM tidak menggunakan model AI prediktif kompleks atau data transaksi nyata. Metode utama yang digunakan adalah graph modeling, BFS untuk menelusuri jalur bukti, rule-based risk scoring untuk menentukan prioritas, serta dashboard explainable dengan human verification. A* Search, UCS, dan community detection diposisikan sebagai metode tambahan atau pengembangan lanjutan apabila heuristic, bobot edge, dan dataset sudah tervalidasi.

Narasi untuk crawler:

> Prototype tidak melakukan crawling ke situs ilegal atau monitoring trafik nyata. Input crawler dan traffic hanya berupa dataset dummy/simulasi yang meniru bentuk crawler finding dan traffic log, dengan label `simulation_only`.

Narasi untuk blokir:

> SATPAM tidak melakukan auto-blocking. Sistem hanya menghasilkan rekomendasi prioritas dan kandidat review. Status rekomendasi pemblokiran hanya dapat muncul setelah proses verifikasi manusia dan tetap bukan eksekusi blokir teknis.

## Rekomendasi Final

| Prioritas | Aksi |
|---:|---|
| 1 | Ganti posisi A* dari metode utama menjadi metode opsional/advanced. |
| 2 | Ganti anomaly detection menjadi rule-based transaction pattern detection. |
| 3 | Ganti community detection menjadi rule-based cluster atau degree centrality sederhana untuk MVP. |
| 4 | Ganti crawler sederhana menjadi import crawler finding dummy/simulasi. |
| 5 | Ganti blokir domain menjadi rekomendasi review pemblokiran setelah human approval. |
| 6 | Tegaskan semua target performa hanya untuk dataset prototype lokal. |

## Kesimpulan Akhir

PPT dan proposal tidak perlu dirombak total. Konsep SATPAM sudah kuat dan realistis sebagai prototype. Yang perlu diganti adalah framing metode supaya lebih sederhana, lebih aman, dan lebih mudah dipertanggungjawabkan:

```text
Fokus realistis = Graph + BFS + Rule-Based Scoring + Explainability + Human Review
Advanced/future = A* + UCS/BDS + Community Detection + Anomaly Detection + Real Crawler
```
