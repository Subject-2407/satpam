# Slides Outline - Proposal SATPAM

## 1. Title

**Claim:** SATPAM memetakan risiko judol-pinjol ilegal sebagai jaringan, bukan kasus tunggal.

**Proof object:** Hero network visual + capability rail.

**On-slide text:** SATPAM, Search-based AI Threat Prevention and Mapping, Graph Intelligence untuk Deteksi dan Prioritisasi Ekosistem Judol-Pinjol Ilegal.

## 2. Background / Urgency

**Claim:** Skala judol sudah masif dan bergerak lintas kanal digital-keuangan.

**Proof object:** Problem infographic berisi statistik PPATK dan rantai kanal: konten, WA, rekening, QRIS/e-wallet, APK.

**On-slide text:** Rp286,84 T, 422,1 juta transaksi, 12,3 juta depositor; masalah bukan hanya situs, tetapi ekosistem.

## 3. Existing System and Gap

**Claim:** Sistem existing kuat di domain masing-masing, tetapi relasi lintas ekosistem belum menjadi pusat analisis.

**Proof object:** Comparison table existing system vs SATPAM.

**On-slide text:** existing: blokir/laporan/analisis terpisah; SATPAM: graph, path bukti, risk score, prioritas, human verification.

## 4. Problem Statement

**Claim:** Tantangan utama adalah mengubah laporan dan sinyal tersebar menjadi jalur risiko yang dapat dijelaskan.

**Proof object:** Five-question problem map.

**Rumusan masalah:** bagaimana merancang graph, menghubungkan sumber data, menerapkan AI search, menghitung risiko, dan menjelaskan hasil.

## 5. Proposed Solution: SATPAM

**Claim:** SATPAM menyatukan laporan, crawler, transaksi simulasi, dan blacklist menjadi peta risiko terverifikasi.

**Proof object:** SATPAM solution flow.

**On-slide text:** input multi-sumber -> ekstraksi entitas -> graph intelligence -> graph search + rule scoring -> dashboard + human review.

## 6. System Architecture

**Claim:** Arsitektur SATPAM memisahkan ingestion, graph intelligence, scoring, dan verifikasi agar aman untuk prototype.

**Proof object:** System architecture diagram.

**On-slide text:** Report form/API, importer, entity extraction, graph builder, Neo4j, search engine, risk scoring, early warning, dashboard.

## 7. Method / Workflow

**Claim:** Metode prototype berjalan end-to-end dari data dummy sampai rekomendasi prioritas.

**Proof object:** Method pipeline.

**On-slide text:** validasi -> ekstraksi -> normalisasi -> dedup -> graph build -> BFS evidence path + optional A*/UCS/BDS -> rule score -> explanation -> review.

## 8. Innovation / Novelty

**Claim:** Novelty SATPAM adalah network-based intelligence yang explainable dan human-in-the-loop.

**Proof object:** Innovation matrix.

**On-slide text:** graph intelligence, search-based risk path, judol-pinjol linkage, early warning, explainable detection, human verification.

## 9. Benefits and Implementation Roadmap

**Claim:** SATPAM memberi manfaat analitik sekarang dan jalur implementasi realistis untuk prototype.

**Proof object:** Benefit stack + 5-phase roadmap timeline.

**On-slide text:** prioritas verifikasi, cluster jaringan, evidence path, audit trail, data dummy, tanpa auto-block.

## 10. Closing and References

**Claim:** SATPAM bukan alat vonis otomatis, tetapi decision-support untuk membaca jaringan risiko lebih cepat dan transparan.

**Proof object:** Closing thesis + compact references.

**On-slide text:** Detect, Map, Explain, Prioritize, Verify; referensi institusional, Neo4j, dokumen SATPAM, dan jurnal acuan [J1]-[J8].
