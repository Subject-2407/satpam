# Revisi Checklist - SATPAM Presentation

## Slide 1: Title
**Durasi:** 0:00-0:50

### Content Checklist
- [ ] Visual hero network ditampilkan dengan jelas
- [ ] Capability rail visible di slide
- [ ] Title: "SATPAM, Search-based AI Threat Prevention and Mapping"
- [ ] Subtitle: "Graph Intelligence untuk Deteksi dan Prioritisasi Ekosistem Judol-Pinjol Ilegal"
- [ ] Font dan ukuran sesuai dengan template

### Speaker Notes
- [ ] Jelaskan singkatan SATPAM (Search-based AI Threat Prevention and Mapping)
- [ ] Positioning: decision-support, bukan sistem penindakan otomatis
- [ ] Sebutkan tiga tujuan: deteksi, pemetaan, prioritisasi risiko
- [ ] Tekankan human-in-the-loop verification sebelum tindakan lanjut

### Design Elements
- [ ] Background color konsisten (BG: 06142B)
- [ ] Text color sesuai (TEXT: EAF6FF)
- [ ] Logo/branding jika ada terlihat jelas

---

## Slide 2: Background / Urgency
**Durasi:** 0:50-1:55

### Content Checklist
- [ ] Problem infographic berisi statistik PPATK:
  - [ ] Rp286,84 Triliun (perputaran dana judol 2025)
  - [ ] 422,1 juta transaksi
  - [ ] 12,3 juta depositor
- [ ] Rantai kanal ditampilkan:
  - [ ] Konten promosi
  - [ ] WhatsApp
  - [ ] Rekening bank
  - [ ] QRIS/e-wallet
  - [ ] APK
- [ ] Visualisasi menunjukkan skalabilitas masalah lintas kanal

### Speaker Notes
- [ ] Mulai dengan: "Masalah tidak bisa dilihat sebagai satu situs atau aplikasi saja"
- [ ] Sebutkan data PPATK tahun 2025
- [ ] Jelaskan mengapa analisis per-kanal tidak cukup
- [ ] Tekankan urgensi pendekatan network-based

### Design Elements
- [ ] Color coding untuk setiap kanal (e.g., Cyan untuk digital, Amber untuk finansial)
- [ ] Infografis mudah dibaca dari jarak jauh
- [ ] Typography kontras dengan background

---

## Slide 3: Existing System and Gap
**Durasi:** 1:55-2:55

### Content Checklist
- [ ] Comparison table: Existing System vs SATPAM
- [ ] Existing systems disebutkan:
  - [ ] Komdigi (konten & pemblokiran)
  - [ ] OJK & Satgas PASTI (aktivitas finansial ilegal)
  - [ ] IASC (kanal laporan scam)
  - [ ] PPATK (analisis dana mencurigakan)
  - [ ] Kepolisian (penegakan hukum)
- [ ] Gap analysis jelas:
  - [ ] Existing: blokir/laporan/analisis terpisah
  - [ ] SATPAM: graph, path bukti, risk score, prioritas, human verification
- [ ] Positioning: penambah, bukan pengganti sistem existing

### Speaker Notes
- [ ] Akui kekuatan sistem existing per-domain
- [ ] Jelaskan gap spesifik: relasi lintas ekosistem belum menjadi pusat analisis
- [ ] Sebutkan lima lembaga terkait
- [ ] Tekankan: SATPAM menghubungkan, bukan mengganti
- [ ] Jelaskan nilai tambah: "link mengarah ke domain mana, domain terhubung ke nomor apa, dst"

### Design Elements
- [ ] Tabel dengan visual yang jelas
- [ ] Icons untuk setiap sistem/lembaga
- [ ] Warna highlighting untuk perbedaan SATPAM

---

## Slide 4: Problem Statement
**Durasi:** 2:55-3:50

### Content Checklist
- [ ] Lima pertanyaan problem map tercantum:
  1. [ ] "Bagaimana merancang sistem AI berbasis graph search untuk ekosistem judol-pinjol ilegal?"
  2. [ ] "Bagaimana menghubungkan laporan, domain, nomor, rekening, APK, crawler, transaksi, blacklist ke satu graph?"
  3. [ ] "Bagaimana menerapkan algoritma searching (BFS, UCS, Bi-Directional, A*) untuk menemukan jalur risiko?"
  4. [ ] "Bagaimana menghitung skor risiko dan prioritas tindakan?"
  5. [ ] "Bagaimana menjelaskan hasil dalam bentuk path bukti?"
- [ ] Visualisasi problem map menunjukkan interkoneksi

### Speaker Notes
- [ ] Baca kelima pertanyaan dengan jelas dan perlahan
- [ ] Jelaskan konteks setiap pertanyaan
- [ ] Tekankan bahwa kelima aspek ini akan dijawab oleh SATPAM

### Design Elements
- [ ] Visual flow chart menunjukkan progression pertanyaan
- [ ] Icons/symbols untuk setiap pertanyaan
- [ ] Warna gradient atau numbered sections

---

## Slide 5: Proposed Solution: SATPAM
**Durasi:** 3:50-4:55

### Content Checklist
- [ ] SATPAM solution flow diagram menampilkan:
  - [ ] Input multi-sumber:
    - [ ] Laporan masyarakat
    - [ ] Crawler/scraper publik
    - [ ] Indikator transaksi simulasi
    - [ ] Blacklist dummy
    - [ ] Data APK simulasi
  - [ ] Entity extraction (URL, domain, nomor, rekening, keyword, QRIS, e-wallet, APK)
  - [ ] Graph building & normalization
  - [ ] AI search + scoring
  - [ ] Dashboard + human review
- [ ] Output: "blacklist candidate, bukan blokir otomatis"

### Speaker Notes
- [ ] Jelaskan alur dari input hingga output
- [ ] Tekankan bahwa hasil adalah "candidate", bukan keputusan final
- [ ] Sebutkan sumber data yang berbeda-beda
- [ ] Jelaskan entity extraction sebagai langkah normalisasi

### Design Elements
- [ ] Flow diagram dengan arrows yang jelas
- [ ] Color-coded stages (input = satu warna, processing = warna lain, output = warna ketiga)
- [ ] Icons untuk masing-masing sumber data

---

## Slide 6: System Architecture
**Durasi:** 4:55-6:00

### Content Checklist
- [ ] Arsitektur diagram dengan empat lapisan:
  - [ ] **Lapisan 1 - Input:**
    - [ ] Report form
    - [ ] API
    - [ ] Import dataset dummy
    - [ ] Crawler finding
    - [ ] Traffic log simulasi
    - [ ] Transaksi simulasi
  - [ ] **Lapisan 2 - Ingestion & Processing:**
    - [ ] Validasi
    - [ ] Extraction
    - [ ] Normalization
    - [ ] Deduplication
    - [ ] Graph builder
  - [ ] **Lapisan 3 - Intelligence Core:**
    - [ ] Neo4j (graph database)
    - [ ] Search engine (A*, BFS, UCS, BDS)
    - [ ] Risk scoring engine
    - [ ] Early warning
    - [ ] Explanation engine
  - [ ] **Lapisan 4 - Dashboard & Verification:**
    - [ ] Graph visualization
    - [ ] Score & cluster display
    - [ ] Rekomendasi prioritas
    - [ ] Audit log
    - [ ] Human verification workflow

### Speaker Notes
- [ ] Jelaskan empat lapisan dengan detail
- [ ] Tekankan pemisahan concerns untuk keamanan prototype
- [ ] Jelaskan peran Neo4j sebagai backbone
- [ ] Tekankan human-in-the-loop di lapisan output

### Design Elements
- [ ] Architecture diagram dengan layering visual yang jelas
- [ ] Boxes untuk komponen, dengan labels dan warna berbeda per lapisan
- [ ] Arrows menunjukkan data flow
- [ ] Tech stack labels (e.g., "Neo4j", "A* Algorithm")

---

## Slide 7: Method / Workflow
**Durasi:** 6:00-7:05

### Content Checklist
- [ ] Pipeline step ditampilkan:
  1. [ ] Input & Validasi
  2. [ ] Entity extraction (regex & rule sederhana)
  3. [ ] Normalisasi & masking (jika sensitif)
  4. [ ] Deduplication
  5. [ ] Graph builder (node & relationship)
  6. [ ] Algorithm search:
     - [ ] BFS: koneksi terdekat
     - [ ] A*: prioritas jalur risiko
     - [ ] UCS: cost investigasi
     - [ ] Bi-Directional Search: titik temu dengan blacklist lama
  7. [ ] Output: risk score, explanation, early warning, dashboard, review manusia

### Speaker Notes
- [ ] Tekankan: "Metode dibuat realistis dan aman"
- [ ] Jelaskan bahwa data adalah dummy/simulasi
- [ ] Jelaskan setiap algoritma search dan use case-nya
- [ ] Tekankan normalisasi dan dedup penting untuk graph quality

### Design Elements
- [ ] Pipeline diagram sequential (1 → 2 → 3 ... → 7)
- [ ] Algorithm box dengan penjelasan singkat
- [ ] Output box prominent di akhir
- [ ] Color coding untuk tahap (input = satu warna, processing = warna lain, output = warna ketiga)

---

## Slide 8: Innovation / Novelty
**Durasi:** 7:05-8:05

### Content Checklist
- [ ] Innovation matrix menampilkan lima aspek novelty:
  1. [ ] **Graph Intelligence:** Menyatukan entitas digital & finansial
  2. [ ] **Search-based Risk Path:** Hasil deteksi bisa ditelusuri
  3. [ ] **Judol-Pinjol Linkage Detection:** Hubungan kerugian judol dan tawaran pinjol ilegal
  4. [ ] **Risk Scoring berbasis Relasi:** Membantu menentukan prioritas
  5. [ ] **Explainable Detection:** Sistem memberi alasan, bukan hanya label
- [ ] Perubahan paradigma: entity-based → network-based intelligence

### Speaker Notes
- [ ] Mulai dengan perubahan cara melihat masalah
- [ ] Jelaskan setiap novelty secara singkat
- [ ] Tekankan: "Bukan hanya label, tetapi alasan"
- [ ] Jelaskan bagaimana network approach berbeda dari traditional detection

### Design Elements
- [ ] Innovation matrix dengan 5 cells
- [ ] Icons untuk masing-masing novelty
- [ ] Comparison visual: entity-based vs network-based
- [ ] Highlights dengan warna Mint atau Cyan

---

## Slide 9: Benefits and Roadmap
**Durasi:** 8:05-9:10

### Content Checklist
- [ ] **Benefits untuk Prototype:**
  - [ ] Memprioritaskan kasus
  - [ ] Melihat cluster jaringan
  - [ ] Memahami evidence path
  - [ ] Mengurangi risiko salah tafsir (human-in-the-loop)

- [ ] **5-Phase Implementation Roadmap:**
  1. [ ] Foundation & Schema Data
  2. [ ] Data Ingestion & Graph Builder
  3. [ ] Search & Scoring
  4. [ ] Dashboard & Verification
  5. [ ] Testing & Demo

- [ ] Timeline jelas untuk setiap fase
- [ ] Positioning: "Kompetitif secara teknologi, tidak overclaim"
- [ ] Catatan: "Semua data pada prototype adalah dummy, sistem tidak melakukan auto-blocking"

### Speaker Notes
- [ ] Jelaskan manfaat dengan contoh konkret
- [ ] Baca lima fase roadmap dengan timeline
- [ ] Tekankan: realistis dan tidak overclaim
- [ ] Jelaskan: data dummy dan human-in-the-loop adalah feature, bukan limitation

### Design Elements
- [ ] Benefit stack visual (stackable boxes)
- [ ] Roadmap timeline dengan 5 phases
- [ ] Phase durations/milestones jika ada
- [ ] Color coding untuk progress indication

---

## Slide 10: Closing and References
**Durasi:** 9:10-10:00

### Content Checklist
- [ ] **Closing Thesis - Lima Kata Kunci:**
  1. [ ] **Detect** - Deteksi entitas risiko
  2. [ ] **Map** - Pemetaan jaringan
  3. [ ] **Explain** - Penjelasan jalur bukti
  4. [ ] **Prioritize** - Prioritisasi tindakan
  5. [ ] **Verify** - Verifikasi manusia

- [ ] **Key Takeaways:**
  - [ ] SATPAM membaca masalah sebagai jaringan
  - [ ] Menyatukan laporan publik, crawler finding, indikator transaksi, blacklist, graph search, risk scoring, dashboard
  - [ ] Konsep yang explainable dan human-in-the-loop

- [ ] **References:**
  - [ ] Dokumen PPATK
  - [ ] Komdigi
  - [ ] OJK/IASC
  - [ ] Dokumentasi Neo4j
  - [ ] SRS SATPAM
  - [ ] Proposal SATPAM

### Speaker Notes
- [ ] Rekap dengan lima kata kunci dengan penekanan
- [ ] Jelaskan bagaimana kelima aspek itu bekerja bersama
- [ ] Tekankan kontribusi utama: menyatukan potongan data
- [ ] Baca atau tampilkan referensi utama
- [ ] Tawarkan Q&A session

### Design Checklist
- [ ] Slide terakhir simple dan impactful
- [ ] Lima kata kunci prominent (besar dan jelas)
- [ ] References tertata rapi (bullets atau compact list)
- [ ] Contact info jika relevan
- [ ] Thank you message (optional)

---

## Overall Presentation Checklist

### Timing & Flow
- [ ] Total durasi: 10 menit
- [ ] Setiap slide ~1 menit (slide 1 = 50s, slide 6 = 1:05 untuk akurasi)
- [ ] Speaker notes align dengan slides
- [ ] Transisi antar slide smooth dan logis

### Visual Consistency
- [ ] Font: Aptos Display (title), Aptos (body)
- [ ] Color palette konsisten:
  - [ ] BG: 06142B
  - [ ] CYAN: 38D9FF (accent, arrows, highlights)
  - [ ] MINT: 3DDC97 (positive/benefits)
  - [ ] AMBER: FFB84D (warnings/important)
  - [ ] RED: FF4D6D (critical/risks)
  - [ ] TEXT: EAF6FF (main text)
- [ ] Aspect ratio: 16:9 (13.333333 x 7.5 inches)
- [ ] Margins dan padding konsisten

### Content Accuracy
- [ ] Semua data & statistik terverifikasi
- [ ] Terminology konsisten (e.g., "risk score", "graph database", "human verification")
- [ ] Technical terms dijelaskan untuk audience umum

### Accessibility
- [ ] Text size readable dari jarak jauh (min 18pt untuk body, 32pt+ untuk title)
- [ ] Color contrast cukup (CYAN & TEXT pada BG memadai)
- [ ] No flashing animations atau effects mengganggu
- [ ] Speaker notes mudah dibaca by presenter

### Generated PPT File (generate_ppt.py)
- [ ] Semua 10 slide functions terdapat dalam code
- [ ] Images/visuals path correct (VISUALS folder)
- [ ] Output filename: final_proposal_satpam.pptx
- [ ] Color hex codes match specifications
- [ ] Text formatting functions working properly

---

## Notes untuk Presenter

1. **Pace & Delivery:**
   - Jangan terburu-buru; 10 menit cukup untuk cover semua slide
   - Pause pada kunci momen (e.g., statistik PPATK, lima pertanyaan problem)
   - Gunakan speaker notes untuk guidance, bukan verbatim reading

2. **Engagement:**
   - Ajukan pertanyaan retorik (e.g., slide 2: "Bagaimana kita menghubungkan semua data ini?")
   - Gunakan gesture untuk menunjuk visual pada slide
   - Eye contact dengan audience

3. **Emphasis Points:**
   - Slide 1: SATPAM adalah decision-support, bukan auto-blocker
   - Slide 2: Masalah sudah MASIF dan LINTAS KANAL
   - Slide 3: Gap adalah RELASI LINTAS EKOSISTEM
   - Slide 5: Output adalah CANDIDATE, bukan keputusan
   - Slide 9: Prototype TIDAK melakukan auto-blocking
   - Slide 10: Lima kata kunci = value proposition

4. **Handling Questions:**
   - Siapkan deep-dives untuk setiap slide
   - Bawa documentation (SRS, proposal) jika diperlukan
   - Jangan klaim fitur yang tidak ada pada prototype

---

## Version History

- **v1.0 (2026-06-03):** Initial checklist dari slides_outline.md, speaker_notes.md, generate_ppt.py
- Basis: Slides outline, Speaker notes, dan Generate PPT Python code
