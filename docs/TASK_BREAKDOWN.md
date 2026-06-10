# Pembagian Pengembangan SATPAM

Dokumen ini merangkum pembagian pengembangan sistem SATPAM berdasarkan kebutuhan pada `docs/SRS.md`. Tujuannya agar pengerjaan prototype lebih rapi, mudah dibagi ke 3 orang, dan tetap menghasilkan demo end-to-end yang bisa ditunjukkan.

## Ringkasan Sistem

SATPAM adalah prototype sistem graph intelligence untuk membantu mendeteksi, memetakan, menjelaskan, dan memprioritaskan risiko ekosistem judi online dan pinjaman online ilegal menggunakan data dummy.

Output utama sistem:

- Laporan dummy dapat diproses menjadi entitas.
- Entitas disimpan sebagai graph.
- Sistem dapat mencari hubungan antar entitas.
- Sistem dapat menampilkan evidence path.
- Sistem dapat menghitung risk score berbasis rule.
- Sistem dapat membuat early warning.
- Sistem dapat menandai entitas sebagai `blacklist_candidate`.
- Semua keputusan akhir tetap melalui human verification.

## Pembagian Besar Pengembangan

Pengembangan dibagi menjadi 3 stream utama:

| Stream | Fokus | Output Utama |
|---|---|---|
| 1. Backend & Platform | API, database, workflow sistem | FastAPI, Neo4j connection, endpoint, auth sederhana, audit log |
| 2. Data, Graph & AI Engine | Pengolahan data, graph, algoritma, scoring | Entity extraction, graph builder, BFS, risk scoring, early warning |
| 3. Frontend, Dashboard & Demo | UI, visualisasi, integrasi, demo | Dashboard, report form, graph explorer, entity detail, verification UI |

## Pembagian Jobdesk untuk 3 Orang

### Orang 1: Backend & Platform Engineer

Fokus utama: membangun fondasi backend, API, database connection, dan workflow sistem.

Tanggung jawab:

- Membuat struktur backend menggunakan FastAPI.
- Menyiapkan Docker Compose untuk backend, frontend, dan Neo4j.
- Membuat koneksi backend ke Neo4j.
- Membuat API health check.
- Membuat endpoint untuk submit laporan dummy.
- Membuat endpoint untuk import dataset dummy.
- Membuat endpoint untuk mengambil detail entitas.
- Membuat endpoint untuk mengambil graph neighborhood.
- Membuat endpoint untuk hasil analisis risiko.
- Membuat endpoint verification case.
- Membuat endpoint update status verifikasi.
- Membuat audit log untuk aksi penting.
- Membuat auth/RBAC sederhana untuk role analyst, supervisor, dan admin.
- Membuat fitur export hasil analisis sederhana dalam format JSON atau Markdown.

Deliverable utama:

- Backend API berjalan.
- Neo4j bisa menerima node dan relationship.
- API bisa dipakai frontend.
- Verification workflow tersedia.
- Audit log tercatat.

Acceptance criteria yang paling terkait:

- AC-001: User dapat mengirim laporan dummy melalui form.
- AC-003: Sistem dapat membuat node dan relationship di Neo4j.
- AC-011: Sistem dapat membuka verification case.
- AC-012: Analyst dapat mengubah status verifikasi.
- AC-013: Audit log tercatat.
- AC-020: Entitas tidak dapat menjadi `confirmed_blacklist` tanpa review manusia.

## Orang 2: Data, Graph & AI Engineer

Fokus utama: membangun logic inti SATPAM, yaitu data dummy, entity extraction, graph builder, search, scoring, dan alert.

Tanggung jawab:

- Menyusun dataset dummy awal.
- Membuat schema dataset dummy untuk:
  - report,
  - domain,
  - URL,
  - akun promosi,
  - nomor WhatsApp,
  - rekening bank,
  - e-wallet,
  - QRIS,
  - APK,
  - keyword,
  - transaksi simulasi,
  - traffic log simulasi,
  - crawler finding dummy,
  - blacklist dummy.
- Membuat entity extraction sederhana berbasis regex dan rule.
- Membuat normalisasi entitas.
- Membuat deduplication entitas.
- Membuat logic graph builder.
- Menentukan jenis node dan relationship yang dipakai di Neo4j.
- Implementasi BFS untuk neighborhood graph dan evidence path.
- Membuat rule-based risk scoring.
- Membuat explanation engine untuk menjelaskan rule yang aktif.
- Membuat early warning detection.
- Membuat traffic/crawler correlation rule.
- Membuat blacklist candidate rule.
- Memastikan sistem memakai bahasa indikatif, bukan vonis.
- Memastikan semua data bersifat dummy dan tersamarkan.

Deliverable utama:

- Dataset dummy siap dipakai.
- Entity extraction berjalan.
- Graph dapat terbentuk dari laporan/import.
- BFS evidence path berjalan.
- Risk score dan explanation tersedia.
- Early warning dan blacklist candidate dapat muncul.

Acceptance criteria yang paling terkait:

- AC-002: Sistem dapat mengekstrak URL, domain, nomor, rekening, APK, dan keyword.
- AC-006: Sistem dapat menjalankan BFS.
- AC-007: Sistem dapat menampilkan evidence path.
- AC-008: Sistem dapat menghitung risk score.
- AC-009: Sistem dapat menjelaskan skor melalui rule aktif.
- AC-010: Sistem dapat membuat early warning alert.
- AC-016: Sistem dapat mengimpor traffic log simulasi.
- AC-017: Sistem dapat mengimpor crawler/scraper finding dummy.
- AC-018: Traffic/crawler finding dapat memicu early warning.
- AC-019: Entitas high/critical dapat otomatis masuk status `blacklist_candidate`.

## Orang 3: Frontend, Dashboard & Demo Engineer

Fokus utama: membangun tampilan pengguna, visualisasi graph, integrasi API, dan persiapan demo.

Tanggung jawab:

- Membuat struktur frontend menggunakan React, TypeScript, dan Vite.
- Membuat layout dashboard utama.
- Membuat report form untuk submit laporan dummy.
- Membuat dashboard ringkasan risiko.
- Membuat graph explorer menggunakan Cytoscape.js.
- Membuat filter graph berdasarkan depth, jenis node, dan risk level.
- Membuat entity detail page.
- Membuat risk path view untuk melihat evidence path.
- Membuat early warning page.
- Membuat traffic/crawler intelligence page.
- Membuat blacklist candidate page.
- Membuat verification case page.
- Membuat UI untuk update status verifikasi.
- Menampilkan label `simulation_only` pada traffic/crawler data.
- Memastikan data sensitif ditampilkan dalam bentuk masked.
- Memastikan UI tidak menampilkan link ilegal sebagai clickable link.
- Menyiapkan demo scenario dan UI smoke test.

Deliverable utama:

- Dashboard bisa digunakan analis.
- Graph bisa divisualisasikan secara interaktif.
- User bisa melihat detail entitas dan evidence path.
- Alert dan verification case bisa direview.
- Demo end-to-end siap dipresentasikan.

Acceptance criteria yang paling terkait:

- AC-001: User dapat mengirim laporan dummy melalui form.
- AC-004: Dashboard dapat menampilkan graph interaktif.
- AC-005: User dapat memilih node dan melihat entity detail.
- AC-007: Sistem dapat menampilkan evidence path.
- AC-011: Sistem dapat membuka verification case.
- AC-012: Analyst dapat mengubah status verifikasi.
- AC-014: Semua data dalam demo adalah dummy atau tersamarkan.
- AC-015: Sistem tidak menggunakan bahasa vonis.
- AC-021: Sistem tidak melakukan blokir nyata.

## Rencana Implementasi per Minggu

### Minggu 1: Foundation

Target: project bisa jalan secara lokal.

| Orang | Pekerjaan |
|---|---|
| Orang 1 | Setup backend FastAPI, Docker Compose, Neo4j, health check |
| Orang 2 | Menentukan schema data dummy dan contoh dataset awal |
| Orang 3 | Setup frontend React/Vite dan layout dashboard awal |

Output minggu 1:

- Backend bisa dijalankan.
- Frontend bisa dijalankan.
- Neo4j tersedia.
- Dataset dummy awal tersedia.

### Minggu 2: Data dan Graph

Target: data dummy bisa masuk dan menjadi graph.

| Orang | Pekerjaan |
|---|---|
| Orang 1 | Endpoint submit report dan import dataset |
| Orang 2 | Entity extraction, normalisasi, deduplication, graph builder |
| Orang 3 | Form laporan dan tampilan daftar entitas awal |

Output minggu 2:

- Laporan dummy bisa dikirim.
- Entitas bisa diekstrak.
- Node dan relationship bisa dibuat di Neo4j.
- UI bisa menampilkan data awal.

### Minggu 3: Search dan Scoring

Target: sistem bisa menganalisis risiko.

| Orang | Pekerjaan |
|---|---|
| Orang 1 | Endpoint graph neighborhood, entity detail, dan analysis result |
| Orang 2 | BFS evidence path, rule-based scoring, explanation engine |
| Orang 3 | Graph explorer, entity detail, risk score display |

Output minggu 3:

- BFS bisa mencari hubungan antar entitas.
- Evidence path bisa ditampilkan.
- Risk score muncul dengan explanation.
- Graph explorer bisa digunakan.

### Minggu 4: Alert dan Human Verification

Target: workflow review manusia berjalan.

| Orang | Pekerjaan |
|---|---|
| Orang 1 | Verification case API, audit log, status update |
| Orang 2 | Early warning, traffic/crawler correlation, blacklist candidate rule |
| Orang 3 | Alert page, blacklist candidate page, verification UI |

Output minggu 4:

- Early warning bisa muncul.
- Entitas high/critical bisa masuk `blacklist_candidate`.
- Analyst bisa melakukan review.
- Supervisor bisa menyetujui status final prototype.
- Audit log tercatat.

### Minggu 5: Testing dan Demo

Target: prototype siap dipresentasikan.

| Orang | Pekerjaan |
|---|---|
| Orang 1 | Integration test API dan pengecekan workflow backend |
| Orang 2 | Unit test extraction, scoring, search, blacklist candidate |
| Orang 3 | UI smoke test, demo scenario, rapikan tampilan presentasi |

Output minggu 5:

- Test utama berjalan.
- Demo scenario siap.
- Export hasil analisis tersedia.
- Prototype siap dipresentasikan.

## Prioritas MVP

Fitur yang wajib dikerjakan terlebih dahulu:

1. Submit laporan dummy.
2. Entity extraction sederhana.
3. Normalisasi dan deduplication.
4. Graph builder ke Neo4j.
5. BFS evidence path.
6. Rule-based risk scoring.
7. Explanation rule aktif.
8. Dashboard graph interaktif.
9. Entity detail.
10. Early warning.
11. Blacklist candidate.
12. Human verification.
13. Audit log.
14. Demo scenario.

## Fitur Opsional Setelah MVP Stabil

Fitur berikut dapat dikerjakan jika waktu masih cukup:

- A* Search.
- UCS/Dijkstra.
- Bi-Directional Search.
- Degree centrality lanjutan.
- Community detection.
- Rule editor dari UI.
- Export PDF.
- Multi-role login yang lebih lengkap.
- Dashboard admin konfigurasi.

## Batasan Penting

Selama pengembangan prototype, tim wajib mengikuti batasan berikut:

- Hanya memakai data dummy.
- Tidak memakai nomor telepon asli.
- Tidak memakai rekening asli.
- Tidak memakai domain ilegal asli.
- Tidak melakukan scraping nyata ke target ilegal.
- Tidak melakukan monitoring trafik nyata.
- Tidak melakukan pemblokiran nyata.
- Tidak membuat vonis seperti "terbukti pelaku".
- Selalu gunakan istilah seperti "terindikasi", "risiko", "rekomendasi", atau "perlu verifikasi".
- Status `blacklist_candidate` boleh dibuat otomatis.
- Status `confirmed_blacklist` hanya boleh dibuat setelah review manusia.
- Status `recommended_for_blocking` hanya berupa rekomendasi, bukan eksekusi blokir.

## Format Koordinasi Harian

Setiap anggota tim disarankan memberi update singkat dengan format:

```text
Kemarin:
- ...

Hari ini:
- ...

Kendala:
- ...

Butuh dari anggota lain:
- ...
```

## Definisi Selesai

Sebuah fitur dianggap selesai jika:

- Fitur bisa dijalankan secara lokal.
- API atau UI sudah terhubung dengan alur utama.
- Data dummy bisa digunakan.
- Error utama sudah ditangani.
- Tidak melanggar batasan etika dan privacy pada SRS.
- Minimal sudah dicek manual.
- Untuk logic penting, sudah ada unit test atau integration test sederhana.

## Rekomendasi Cara Kerja

- Kerjakan dengan pendekatan end-to-end kecil, bukan menunggu semua modul sempurna.
- Gunakan data dummy yang konsisten dari awal.
- Setiap API yang dibuat backend sebaiknya langsung diberi contoh response.
- Frontend dapat memakai mock data dulu, lalu diganti ke API asli.
- Logic scoring dan search sebaiknya dipisahkan dari route API agar mudah dites.
- Setiap perubahan status penting harus masuk audit log.
- Demo harus fokus pada alur: laporan masuk, entitas terbentuk, graph terlihat, risk score muncul, evidence path tampil, lalu diverifikasi manusia.

