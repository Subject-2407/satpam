"""Alat bantu anotasi manual SATPAM (milik orang A).

Menyiapkan sampel node untuk dianotasi tiga anggota tim, membuat lembar kerja
per anotator, lalu menggabungkan jawaban menjadi `human_annotations.csv`
beserta laporan kesepakatan antar-anotator.

Tiga batasan yang menjaga validitas anotasi:

1. **Tidak mengimpor apa pun dari `generator/`.** Lewat `generate()` seluruh
   kolom jawaban bisa diakses; jalannya ditutup sepenuhnya.
2. **Tidak pernah membaca kolom ground truth.** Pembacaan node memakai
   `rules.loader` yang berbasis allowlist kolom.
3. **Lembar kerja anotator tidak memuat `rule_score`, `rule_level`,
   `triggered_rules`, maupun nama strata.** Skor rule dipakai untuk *memilih*
   node, tidak untuk ditunjukkan. Nama strata pun disembunyikan: menuliskan
   "proksi hard negative" di lembar kerja sama saja dengan membocorkan jawaban.

Semua itu dijaga `tests/test_annotation_hides_answers.py`.
"""

__version__ = "1.0.0"
