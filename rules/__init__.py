"""Rule engine SATPAM — baseline B1 dan penghasil label lemah.

Paket ini menghasilkan `weak_labels.csv` yang dipakai **hanya untuk
pelatihan** — ini aturan keras yang tidak boleh dilanggar. Ia diadaptasi dari
`scoring.py` sistem SATPAM v1.0 di
`src-old/backend/app/services/ai_engine/scoring.py`.

Dua batasan yang menjaga validitas eksperimen:

1. **Tidak mengimpor apa pun dari `generator/`.** Kontrak format kolom adalah
   satu-satunya titik temu; kedua sisi menyalinnya sendiri-sendiri. Kalau rule engine
   mengimpor modul generator, keduanya berhenti menjadi artefak independen dan
   perubahan di satu sisi diam-diam mengubah sisi lain.

2. **Tidak pernah membaca kolom ground truth.** `loader.py` memakai daftar
   kolom yang diizinkan, bukan daftar kolom yang dilarang, sehingga kolom
   jawaban tidak pernah masuk ke objek yang dilihat modul skoring. Dijaga oleh
   `tests/test_rules_blind_to_ground_truth.py`.

Bobot, ambang bilangan bulat, dan batas level diwarisi dari sistem v1.0 yang
ditulis **sebelum** generator ada, jadi tidak mungkin tersetel ke data yang
dihasilkannya.
"""

__version__ = "1.0.0"
