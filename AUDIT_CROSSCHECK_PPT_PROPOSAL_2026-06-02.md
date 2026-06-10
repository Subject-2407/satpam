# Laporan Crosscheck PPT dan Proposal SATPAM

Tanggal audit: 2026-06-02

Target audit:

| Target | Fungsi dalam audit |
|---|---|
| `final_proposal_satpam.pptx` | Materi presentasi final, diekstrak dari XML slide PPTX |
| `SATPAM_Proposal_Comprehensive.md` | Proposal naratif yang dibandingkan dengan SRS dan dokumen latar belakang |

Dokumen sumber pembanding:

| Dokumen | Fungsi dalam audit |
|---|---|
| `docs/SRS.md` | Sumber requirement, scope, arsitektur, safety, dan acceptance criteria |
| `SATPAM_Latar_Belakang_Gap_Inovasi.md` | Sumber latar belakang, gap, novelty, dan rumusan masalah |
| `slides_outline.md` | Rencana klaim dan on-slide text per slide |
| `speaker_notes.md` | Narasi presentasi per slide |
| `references.md` | Daftar referensi ringkas untuk slide closing |

Catatan metode:

| Item | Catatan |
|---|---|
| Ekstraksi PPT | Isi PPT diekstrak langsung dari `ppt/slides/slide*.xml` dalam file `.pptx`. |
| Nomor baris | Referensi baris memakai nomor baris file saat audit ini dijalankan. |

Legenda skor:

| Skor | Arti |
|---|---|
| ✅ | Didukung jelas oleh dokumen sumber dan konsisten dengan outline/notes. |
| ⚠️ | Didukung sebagian, tetapi ada penyederhanaan, ambiguitas, atau mismatch minor. |
| ❌ | Tidak didukung, bertentangan, atau berpotensi misleading secara substantif. |

## Ringkasan Eksekutif

| Aspek | Skor | Ringkasan |
|---|---:|---|
| Klaim inti PPT vs SRS/proposal/latar belakang | ✅ | Semua klaim utama PPT memiliki dukungan dokumen sumber. |
| Akurasi statistik PPATK | ✅ | Angka Rp286,84 T, 422,1 juta transaksi, dan 12,3 juta depositor konsisten dengan `SATPAM_Latar_Belakang_Gap_Inovasi.md:15`, `SATPAM_Proposal_Comprehensive.md:46`, dan `references.md:3`. |
| Scope prototype dan safety | ✅ | PPT menegaskan data dummy, masking, `simulation_only`, human verification, dan no auto-blocking sesuai `docs/SRS.md:43`, `docs/SRS.md:1084`, `docs/SRS.md:1120`, `docs/SRS.md:1150-1153`, dan `docs/SRS.md:1448-1453`. |
| Kesesuaian PPT dengan slide outline | ⚠️ | Ada mismatch minor pada proof object slide 2 dan detail validasi slide 7. |
| Kesesuaian PPT dengan speaker notes | ⚠️ | Notes sangat selaras, tetapi notes slide 8 belum menyebut "human verification by design" yang muncul di PPT/outline. |
| Proposal komprehensif vs SRS | ⚠️ | Proposal kuat secara konsep, tetapi ada dua frasa yang perlu diperjelas: "crawler sederhana" dan "Blokir domain". |
| Referensi slide 10 vs `references.md` | ✅ | Nomor referensi [1]-[11] dan [J1]-[J8] di slide 10 selaras dengan `references.md`. |
| Klaim tidak didukung | ✅ | Tidak ditemukan klaim PPT yang masuk kategori ❌. |

## Audit Per Slide PPT

| Slide | Klaim utama dari PPT | Bukti sumber relevan | Outline/Notes | Skor | Temuan dan rekomendasi |
|---:|---|---|---|---:|---|
| 1 | SATPAM adalah sistem graph intelligence untuk deteksi, pemetaan, prioritisasi, explainability, dan human verification. | `docs/SRS.md:30` mendefinisikan graph intelligence dan jaringan entitas. `docs/SRS.md:43` menegaskan human verification dan bukan keputusan final. `SATPAM_Proposal_Comprehensive.md:13` menyebut graph search untuk deteksi, pemetaan, dan prioritisasi. `SATPAM_Latar_Belakang_Gap_Inovasi.md:21` mendukung graph search berbasis Neo4j dan algoritma search. | Outline sesuai di `slides_outline.md:5` dan `slides_outline.md:9`. Notes sesuai di `speaker_notes.md:5`. | ✅ | Klaim title kuat dan tidak overclaim. Tidak perlu perbaikan substantif. |
| 2 | Skala judol masif dan bergerak lintas kanal digital-keuangan; statistik PPATK 2025 dipakai sebagai urgensi. | `SATPAM_Latar_Belakang_Gap_Inovasi.md:15` memuat Rp286,84 T, 422,1 juta transaksi, dan 12,3 juta depositor. `SATPAM_Proposal_Comprehensive.md:46` memuat angka yang sama. `docs/SRS.md:64` menjelaskan kanal URL, WA, rekening, e-wallet, QRIS, APK. `references.md:3` memuat referensi PPATK. | Claim dan on-slide text sesuai `slides_outline.md:13` dan `slides_outline.md:17`. Notes sesuai `speaker_notes.md:9`. | ⚠️ | Klaim dan angka valid. Catatan minor: outline menyebut proof object rantai kanal konten/WA/rekening/QRIS/e-wallet/APK, sedangkan PPT aktual menampilkan alur "Laporan -> Crawler -> Transaksi -> Skor -> Dashboard". Rekomendasi: sesuaikan visual PPT dengan outline atau ubah outline agar menyebut pipeline sinyal. |
| 3 | Sistem existing kuat di domain masing-masing, tetapi relasi lintas ekosistem belum menjadi pusat analisis; SATPAM bukan pengganti lembaga. | `SATPAM_Latar_Belakang_Gap_Inovasi.md:17` menyebut Komdigi, OJK, IASC, PPATK, dan kepolisian. `SATPAM_Latar_Belakang_Gap_Inovasi.md:31-35` merinci sistem existing. `SATPAM_Latar_Belakang_Gap_Inovasi.md:44` menyimpulkan ruang pengembangan pada integrasi lintas data, relasi, dan prioritas risiko. `SATPAM_Proposal_Comprehensive.md:141` menyatakan SATPAM bukan pengganti lembaga. | Outline sesuai `slides_outline.md:21` dan `slides_outline.md:25`. Notes sesuai `speaker_notes.md:13`. | ✅ | Klaim selaras dengan dokumen sumber. Tidak ditemukan kontradiksi. |
| 4 | Tantangan utama adalah mengubah sinyal tersebar menjadi evidence path/risk path yang explainable. | `docs/SRS.md:34-41` memuat pertanyaan tentang indikasi risiko, jalur bukti, cluster, prioritas verifikasi, dan early warning. `SATPAM_Latar_Belakang_Gap_Inovasi.md:328-334` memuat rumusan masalah graph, integrasi data, dan algoritma search. `speaker_notes.md:17` menjabarkan lima pertanyaan yang sama. | Outline sesuai `slides_outline.md:29` dan `slides_outline.md:33`. Notes sesuai `speaker_notes.md:17`. | ⚠️ | Klaim utama valid. Catatan minor: pertanyaan #2 di slide menyebut laporan, domain, rekening, APK, blacklist, tetapi notes menambahkan nomor WhatsApp, crawler finding, dan transaksi simulasi. Rekomendasi: jika ruang slide cukup, tambahkan "WA/sinyal simulasi" atau biarkan sebagai ringkasan slide dan pertahankan detail di notes. |
| 5 | SATPAM menyatukan input multi-sumber, entity extraction, graph intelligence, A* search, scoring, dashboard, dan human verification. | `docs/SRS.md:32` mendukung data dummy multi-sumber, graph, A*, scoring, dan dashboard. `docs/SRS.md:138-167` mendukung form laporan, import dummy, extraction, graph builder, Neo4j, A*, BFS, UCS, BDS, scoring. `docs/SRS.md:420-428` mendukung laporan, blacklist dummy, crawler simulasi, transaksi simulasi, APK, QRIS/e-wallet. `docs/SRS.md:1120-1153` mendukung blacklist candidate, approval manusia, dan bukan blokir nyata. | Outline sesuai `slides_outline.md:37` dan `slides_outline.md:41`. Notes sesuai `speaker_notes.md:21`. | ✅ | Slide ini sangat selaras dengan SRS, terutama batas aman prototype: data dummy, masking, `simulation_only`, human review, no auto-blocking. |
| 6 | Arsitektur memisahkan input, ingestion/processing, graph intelligence, scoring/explanation/alert, dashboard, verification, audit, dan export. | `docs/SRS.md:346-408` memuat diagram konseptual, alur utama, dan komponen sistem. `docs/SRS.md:396-408` mendukung importer, extractor, graph builder, Neo4j, search engine, risk scoring, traffic/crawler intelligence, dashboard. `docs/SRS.md:626-631` mendukung A*, BFS, UCS/Dijkstra, dan Bi-Directional Search. `docs/SRS.md:686-693` mendukung dashboard, graph visualization, evidence path, dan early warning. | Outline sesuai `slides_outline.md:45` dan `slides_outline.md:49`. Notes sesuai `speaker_notes.md:25`. | ✅ | Komponen PPT konsisten dengan SRS. Tidak ada klaim arsitektur yang tidak didukung. |
| 7 | Workflow prototype berjalan dari data dummy sampai rekomendasi prioritas melalui extract, normalize/dedup, graph build, search, score, explain, review. | `docs/SRS.md:374-387` memuat alur input dummy sampai dashboard dan human verification. `docs/SRS.md:595-608` mendukung extraction, masking, normalisasi, dan deduplication. `docs/SRS.md:626-632` mendukung A*, BFS, UCS/Dijkstra, BDS, dan output path/explanation. `speaker_notes.md:29` memuat pipeline yang sama. | Outline sesuai `slides_outline.md:53` dan `slides_outline.md:57`. Notes sesuai `speaker_notes.md:29`. | ⚠️ | Klaim valid. Catatan minor: outline dan notes menyebut validasi, tetapi label workflow di PPT tidak menampilkan validasi secara eksplisit. Rekomendasi: ubah step awal menjadi "Validate + Extract" atau tambahkan validasi kecil sebelum extract. |
| 8 | Novelty SATPAM adalah network-based intelligence, graph intelligence, A* risk path, judol-pinjol linkage, explainable score, dan human verification by design. | `SATPAM_Latar_Belakang_Gap_Inovasi.md:148-150` menyebut pergeseran dari entity-based detection ke network-based intelligence. `SATPAM_Latar_Belakang_Gap_Inovasi.md:187-215` mendukung search-based risk path dan algoritma. `SATPAM_Latar_Belakang_Gap_Inovasi.md:217-248` mendukung risk scoring dan judol-pinjol linkage. `SATPAM_Latar_Belakang_Gap_Inovasi.md:280-299` mendukung explainable detection. `docs/SRS.md:1084` mendukung human verification. | Outline sesuai `slides_outline.md:61` dan `slides_outline.md:65`. Notes cukup sesuai di `speaker_notes.md:33`, tetapi belum menyebut human verification. | ⚠️ | Klaim novelty kuat. Catatan minor: speaker notes slide 8 tidak menyebut "human verification by design", padahal PPT memuatnya. Rekomendasi: tambahkan satu kalimat notes bahwa novelty tetap aman karena final decision melewati reviewer manusia. |
| 9 | SATPAM memberi manfaat analitik dan roadmap prototype lima fase; target MVP 1.000 node, 5.000 relationship, dashboard kurang dari 3 detik. | `docs/SRS.md:102-116` mendukung misi prototype, graph, extraction, path, scoring, explanation, dashboard. `docs/SRS.md:1417` mendukung dashboard kurang dari 3 detik. `docs/SRS.md:1426` mendukung 1.000 node dan 5.000 relationship. `docs/SRS.md:1623-1678` mendukung roadmap fase foundation, data/graph, search/scoring, dashboard/verification, testing/demo. | Outline sesuai `slides_outline.md:69` dan `slides_outline.md:73`. Notes sesuai `speaker_notes.md:37`. | ✅ | Roadmap dan target MVP didukung langsung oleh SRS. Tidak ada mismatch substantif. |
| 10 | SATPAM adalah decision-support, bukan alat vonis otomatis; referensi utama PPATK, Komdigi, OJK/IASC, Neo4j, dokumen lokal, dan jurnal acuan. | `docs/SRS.md:1887-1891` menyimpulkan prototype kecil, data dummy, A*, graph intelligence, dan human verification. `SATPAM_Proposal_Comprehensive.md:729-735` menyimpulkan graph intelligence explainable dan verifikasi manusia. `references.md` memuat referensi [1]-[11] dan [J1]-[J8] yang disebut di slide. | Outline sesuai `slides_outline.md:77` dan `slides_outline.md:81`. Notes sesuai `speaker_notes.md:41`. | ✅ | Closing dan compact references selaras. Tidak ditemukan referensi slide yang hilang dari `references.md`. |

## Crosscheck Proposal Komprehensif

| Aspek proposal | Bukti proposal | Pembanding sumber | Skor | Temuan dan rekomendasi |
|---|---|---|---:|---|
| Definisi SATPAM sebagai graph search/intelligence | `SATPAM_Proposal_Comprehensive.md:13` dan `SATPAM_Proposal_Comprehensive.md:729-733` | Konsisten dengan `docs/SRS.md:30-32` dan `SATPAM_Latar_Belakang_Gap_Inovasi.md:21`. | ✅ | Konsep inti proposal selaras dengan SRS dan latar belakang. |
| Statistik PPATK 2025 | `SATPAM_Proposal_Comprehensive.md:46` | Konsisten dengan `SATPAM_Latar_Belakang_Gap_Inovasi.md:15` dan `references.md:3`. | ✅ | Angka dan sumber selaras. |
| Sistem existing dan gap | `SATPAM_Proposal_Comprehensive.md:56-67`, `SATPAM_Proposal_Comprehensive.md:141-158` | Konsisten dengan `SATPAM_Latar_Belakang_Gap_Inovasi.md:31-44` dan `SATPAM_Latar_Belakang_Gap_Inovasi.md:136-158`. | ✅ | Tidak ada kontradiksi. |
| Input prototype dan crawler | `SATPAM_Proposal_Comprehensive.md:230-237` dan `SATPAM_Proposal_Comprehensive.md:244` | SRS membatasi crawler/trafik ke simulasi atau sumber legal: `docs/SRS.md:88`, `docs/SRS.md:734-741`, `docs/SRS.md:1440-1441`, `docs/SRS.md:1453`. | ⚠️ | Frasa "crawler sederhana" di proposal dapat dibaca sebagai crawler nyata. Rekomendasi: ubah menjadi "crawler finding dummy/simulasi atau crawler publik legal berizin dengan label `simulation_only`". |
| Output rekomendasi tindakan | `SATPAM_Proposal_Comprehensive.md:562` | SRS melarang keputusan final otomatis dan auto-blocking: `docs/SRS.md:43`, `docs/SRS.md:1084`, `docs/SRS.md:1120`, `docs/SRS.md:1145`, `docs/SRS.md:1150-1153`, `docs/SRS.md:1442`. | ⚠️ | "Blokir domain" masih terlalu tegas jika tanpa qualifier. Rekomendasi: ganti menjadi "rekomendasi review pemblokiran setelah approval manusia; tanpa eksekusi blokir nyata". |
| Algoritma search | `SATPAM_Proposal_Comprehensive.md:298-304`, `SATPAM_Proposal_Comprehensive.md:324-335`, `SATPAM_Proposal_Comprehensive.md:731` | Konsisten dengan `docs/SRS.md:84-85`, `docs/SRS.md:626-631`, dan `docs/SRS.md:920-925`. | ✅ | Algoritma utama dan pendukung selaras. |
| Data dummy, etika, dan implementasi nyata | `SATPAM_Proposal_Comprehensive.md:592`, `SATPAM_Proposal_Comprehensive.md:735` | Konsisten dengan `docs/SRS.md:1448-1453`, `docs/SRS.md:1512-1525`, dan `docs/SRS.md:1562-1568`. | ✅ | Pesan prototype vs implementasi nyata sudah ada, tetapi dua frasa di atas tetap perlu diperjelas agar tidak ambigu. |

## Kesesuaian Outline dan Speaker Notes

| Aspek | Skor | Bukti | Catatan |
|---|---:|---|---|
| Jumlah slide | ✅ | PPT berisi 10 slide; outline memiliki slide 1-10 di `slides_outline.md:3-81`; notes memiliki slide 1-10 di `speaker_notes.md:3-41`. | Struktur lengkap. |
| Judul dan urutan narasi | ✅ | Outline dan notes mengikuti urutan Title, Background, Existing Gap, Problem, Solution, Architecture, Workflow, Innovation, Benefits/Roadmap, Closing. | Tidak ada slide lompat atau tertukar. |
| Klaim utama per slide | ✅ | Semua claim outline muncul di PPT, minimal dalam bentuk ringkas. | Klaim didukung oleh SRS/latar/proposal. |
| Proof object slide 2 | ⚠️ | Outline `slides_outline.md:15` meminta problem infographic statistik dan rantai kanal; PPT menampilkan statistik dan pipeline sinyal. | Perbedaan visual minor, bukan kontradiksi isi. |
| Validasi pada workflow slide 7 | ⚠️ | Outline `slides_outline.md:57` dan notes `speaker_notes.md:29` menyebut validasi; PPT slide 7 tidak memberi label validasi eksplisit. | Validasi ada di slide 6, tetapi slide 7 bisa dibuat lebih presisi. |
| Human verification pada slide 8 | ⚠️ | PPT slide 8 memuat "Human verification by design"; notes `speaker_notes.md:33` belum menyebut frasa ini. | Tambahkan satu kalimat ke notes jika revisi diperbolehkan. |
| Referensi closing | ✅ | PPT slide 10 menyebut [1]-[11] dan [J1]-[J8]; `references.md` memuat daftar tersebut. | Selaras. |

## Temuan Utama

| ID | Severity | Area | Temuan | Dampak | Rekomendasi |
|---|---:|---|---|---|---|
| F-01 | Medium | Proposal | `SATPAM_Proposal_Comprehensive.md:562` memakai contoh "Blokir domain" sebagai rekomendasi tindakan. | Berpotensi dibaca sebagai tindakan otomatis, padahal SRS melarang auto-blocking. | Perjelas menjadi rekomendasi review pemblokiran setelah approval manusia, tanpa eksekusi blokir nyata. |
| F-02 | Medium | Proposal | `SATPAM_Proposal_Comprehensive.md:244` memakai frasa "crawler sederhana". | Berpotensi ambigu terhadap batasan SRS tentang crawler nyata dan `simulation_only`. | Gunakan istilah "crawler finding dummy/simulasi" atau "crawler publik legal berizin". |
| F-03 | Low | PPT vs Outline | Slide 2 tidak sepenuhnya mengikuti proof object rantai kanal yang direncanakan outline. | Visual dapat terasa kurang menjelaskan klaim "lintas kanal" walau angka dan narasi valid. | Tambahkan label kanal seperti konten, WA, rekening, QRIS/e-wallet, APK, atau ubah outline. |
| F-04 | Low | PPT vs Outline/Notes | Slide 7 tidak menampilkan validasi eksplisit pada pipeline. | Workflow sedikit kurang presisi dibanding SRS/notes. | Tambahkan "Validate + Extract" atau step validasi kecil. |
| F-05 | Low | Notes vs PPT | Notes slide 8 belum menyebut human verification by design. | Narasi novelty kurang menekankan governance yang sudah ada di PPT. | Tambahkan satu kalimat bahwa novelty tetap human-in-the-loop. |

## Klaim Tidak Didukung atau Kontradiksi

| Kategori | Hasil |
|---|---|
| Klaim PPT tidak didukung sumber | Tidak ditemukan. |
| Kontradiksi langsung PPT vs SRS | Tidak ditemukan. |
| Kontradiksi langsung notes vs PPT | Tidak ditemukan; hanya ada omission minor pada slide 8. |
| Kontradiksi proposal vs SRS | Tidak ada kontradiksi eksplisit, tetapi ada ambiguitas medium pada wording "Blokir domain" dan "crawler sederhana". |

## Rekomendasi Perbaikan Prioritas

| Prioritas | Rekomendasi | Alasan |
|---:|---|---|
| 1 | Perjelas `SATPAM_Proposal_Comprehensive.md:562` agar output "blokir" selalu disebut sebagai rekomendasi setelah approval manusia dan bukan tindakan otomatis. | Ini menjaga konsistensi dengan SRS safety dan mengurangi risiko overclaim. |
| 2 | Perjelas `SATPAM_Proposal_Comprehensive.md:244` agar crawler prototype disebut simulasi/dummy atau legal berizin dengan label `simulation_only`. | Ini menjaga konsistensi dengan batasan crawler dan privacy di SRS. |
| 3 | Selaraskan visual slide 2 dengan outline atau update outline agar sesuai visual pipeline aktual. | Ini meningkatkan konsistensi dokumen presentasi. |
| 4 | Tambahkan kata "Validate" pada pipeline slide 7 jika revisi PPT diperbolehkan. | Ini membuat workflow lebih sesuai dengan SRS dan notes. |
| 5 | Tambahkan satu kalimat human verification pada notes slide 8 jika revisi notes diperbolehkan. | Ini menyamakan narasi novelty dengan PPT dan SRS. |

## Kesimpulan Audit

| Area | Kesimpulan |
|---|---|
| PPT final | Layak dipakai. Klaim utama kuat, sumber pendukung tersedia, dan tidak ditemukan klaim besar yang tidak didukung. |
| Proposal komprehensif | Secara konsep selaras, tetapi perlu dua klarifikasi wording agar tidak tampak melebihi batas SRS. |
| Risiko presentasi | Rendah. Risiko terbesar bukan akurasi fakta, melainkan interpretasi kata "blokir" dan "crawler" jika pembaca tidak melihat batasan SRS. |
| Status keseluruhan | ✅ Lolos dengan catatan minor-medium. |
