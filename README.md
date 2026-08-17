# SATPAM

Sistem graph intelligence untuk deteksi dan prioritisasi risiko ekosistem judi
online (judol) dan pinjaman online ilegal di Indonesia. Pendekatannya
membandingkan model graph neural network relasional (R-GCN) dengan pendekatan
berbasis aturan dan tiga baseline non-graph, pada data sintetik dengan label
ground truth yang ditanam terpisah dari label pelatihan.

## Aturan yang mengikat seluruh kode di repo ini

Aturan ini menentukan validitas seluruh perbandingan model dan tidak boleh
dilanggar oleh perubahan apa pun:

1. **`generator/` dan `rules/` tidak boleh saling impor.** Generator menanam
   ground truth (`gt_illicit`) secara independen dari cara rule engine
   menghitung skor. Bila keduanya berbagi logika, model hanya akan belajar
   meniru rule engine dan seluruh perbandingan jadi tidak bermakna. Ditegakkan
   `tests/test_no_circularity.py` dan `tests/test_rules_blind_to_ground_truth.py`.
2. **Evaluasi hanya boleh memakai kolom `gt_*`.** `weak_labels.csv` (keluaran
   rule engine) hanya untuk pelatihan. Kolom `gt_*` tidak boleh masuk fitur
   model maupun label pelatihan mana pun.
3. **Split berdasarkan waktu, bukan acak.** Kolom `split` di `nodes.csv`
   ditentukan dari `first_seen_at`, sudah final, dan tidak boleh dibuat ulang
   secara acak per node.
4. **AUPRC adalah metrik utama**, bukan ROC-AUC atau accuracy. Datanya
   timpang, sekitar 5 sampai 10 persen positif tergantung seed.
5. **Empat baseline wajib dijalankan dan dilaporkan apa adanya**: rule-based,
   MLP, XGBoost dengan agregasi tetangga, dan GCN homogen. Kalau salah satu
   baseline mengalahkan R-GCN pada suatu cakupan, itu dilaporkan apa adanya,
   bukan disembunyikan.

Skema kolom lengkap ada di kode yang mendefinisikannya, bukan di dokumen
terpisah: lihat `generator/schema.py` untuk `nodes.csv`/`edges.csv`, dan
`rules/loader.py` untuk kolom yang boleh dibaca rule engine.

## Setup

```bash
pip install -r requirements.txt
```

Latih di CPU. Graph-nya sekitar 5.000 node per seed, tidak butuh GPU.

## Generator data sintetik

```bash
python -m generator.build --seed 42          # satu seed
python -m generator.build --all-seeds        # seluruh seed resmi (42-46)
python -m generator.build --seed 42 --dry-run    # jalankan + validasi, tanpa menulis
python -m generator.build --seed 42 --nodes 400  # smoke test cepat
```

Keluaran ke `data/synthetic/seed_{SEED}/`: `nodes.csv`, `edges.csv`,
`manifest.json`. Generator tidak menulis apa pun bila validasi gagal.

Memeriksa direktori keluaran yang sudah ada, tanpa menjalankan generator:

```bash
python -m generator.build --validate-only data/synthetic/seed_42
```

### Yang perlu diketahui saat memakai datanya

- **Evaluasi hanya terhadap `gt_illicit`.** Kolom `gt_*` lain (`gt_operator_id`, `gt_ecosystem`) untuk analisis, bukan untuk fitur.
- **Split sudah ditentukan** di kolom `split`, temporal. Ambang batasnya berupa timestamp tercatat di `manifest.params.split_diagnostics`, jadi pembagiannya bisa diverifikasi tanpa menebak metode interpolasi.
- **`feat_degree_in/out` dan `feat_report_count` dihitung dari `edges.csv` final**, sesudah noise ditambahkan. Menghitung ulang dari `edges.csv` harus memberi angka yang identik.
- **Jumlah positif per split berbeda antar-seed.** Lihat `manifest.params.split_diagnostics`. Seed 44 hanya punya 18 positif di `test`, jadi varians metrik di seed itu memang tinggi, bukan tanda model tidak stabil.
- **Tidak ada satu fitur pun yang membelah kelas sendirian** (AUC per fitur antara 0,37 dan 0,73). Ini disengaja, supaya perbandingan antar-metode tetap bermakna.
- **`edges.csv.weight` ditentukan hanya oleh `rel_type`**, bukan oleh aturan generatif yang menerbitkan edge-nya, sehingga bobot tidak bisa dipakai menyaring edge palsu.

## Rule engine (baseline B1 + label lemah)

```bash
python -m rules.build --seed 42              # satu seed
python -m rules.build --all-seeds            # seluruh seed resmi
python -m rules.build --seed 42 --tier srs-only   # ablasi: hanya aturan inti
python -m rules.build --seed 42 --dry-run
```

Membaca `nodes.csv` dan `edges.csv`, menulis `weak_labels.csv` (label lemah
untuk pelatihan) dan `weak_labels_audit.json` (asal-usul dan ambang tiap
aturan, bukan bagian kontrak data).

Diadaptasi dari [scoring.py sistem v1](src-old/backend/app/services/ai_engine/scoring.py).
Bobot dan ambangnya diwarisi dari kode yang ditulis sebelum generator ada,
sehingga independensinya terhadap generator bisa ditunjukkan langsung dari
riwayat kode, bukan hanya diklaim.

### Yang perlu diketahui saat memakainya

- **`weak_labels.csv` hanya untuk pelatihan.** Dilarang menghitung metrik terhadapnya.
- **Sepuluh aturan, dua tier.** Delapan aturan inti `R-G1` sampai `R-G8`, dan dua aturan tambahan `R-X1`/`R-X2` yang bisa dimatikan dengan `--tier srs-only` bila ingin membandingkan hanya dengan aturan inti.
- **Rule engine tidak pernah melihat kolom `gt_*`.** `rules/loader.py` memakai allowlist kolom, bukan blocklist, jadi kolom ground truth tidak pernah masuk ke objek yang dilihat modul skoring.
- **Rule engine tidak mengimpor `generator/`.** Skema data adalah satu-satunya titik temu; kedua sisi mengimplementasikannya sendiri-sendiri.
- **Kalibrasi ambang butuh skala penuh.** Ambang dikalibrasi ke persentil sebaran teramati. Pada graph kecil (ratusan node) sampelnya terlalu tipis dan rule engine jatuh di bawah laju dasar; pada 5.000 node ia 2 sampai 3 kali laju dasar.

## Anotasi manual

```bash
python -m annotation.build sample --seed 42 --subdir anotasi_ronde1
python -m annotation.build merge  --seed 42 --subdir anotasi_ronde1
```

Prosedur lengkap, termasuk kriteria pelabelan dan cara menambah ronde baru,
ada di [annotation/PANDUAN_ANOTASI.md](annotation/PANDUAN_ANOTASI.md).

Ringkasnya: sampel dipilih berstrata (bukan acak) supaya kasus sulit ikut
terwakili, tiga anotator menilai node yang sama secara mandiri, dan lembar
kerjanya tidak memuat skor rule engine maupun kolom ground truth apa pun.

Repo ini menyertakan dua ronde anotasi nyata di
`data/synthetic/seed_42/anotasi_ronde1/` dan `anotasi_ronde2/`. Ronde kedua
menunjukkan kappa naik dari 0,177 menjadi 0,542 setelah satu ronde kalibrasi,
dan komponen propagasi umpan balik pada `models/feedback.py` hanya
menghasilkan perbaikan performa yang bermakna secara statistik pada anotasi
ronde kedua, bukan ronde pertama. Detail angkanya ada di
`experiments/results/rep20_ronde1/` dan `rep20_ronde2/`.

`human_annotations.csv` dan `answers_*.csv` di-commit meski berupa CSV di
`data/`, karena keduanya hasil kerja manusia dan tidak dapat dibuat ulang dari
kode.

## Melatih model dan menjalankan eksperimen

```bash
# tabel hasil utama: R-GCN vs 4 baseline, 5 seed, uji Wilcoxon
python experiments/train.py --seeds 42 43 44 45 46

# ablasi umpan balik analis (lihat models/feedback.py untuk mekanismenya)
python experiments/ablation.py --seed 42 --repeats 20
```

Hasil ditulis sebagai CSV ke `experiments/results/`, tidak hanya dicetak ke
layar. Model dilatih dan dipilih (early stopping) memakai label lemah dari
rule engine, lalu dievaluasi terhadap `gt_illicit` yang tidak pernah dilihat
selama pelatihan. AUPRC dilaporkan sebagai mean plus minus standar deviasi
lintas seed, dengan uji Wilcoxon signed-rank R-GCN melawan tiap baseline.

## Menjalankan tes

```bash
pytest                  # tes cepat
pytest -m slow          # tes skala penuh (~7 detik)
```

| Berkas | Yang dijaga |
|---|---|
| `tests/test_no_circularity.py` | `generator/` tidak mengimpor `rules/` atau logika skoringnya |
| `tests/test_generator_contract.py` | Skema kolom, legalitas edge, invariant ground truth, split temporal, medan internal tidak bocor ke CSV, determinisme, dan tidak ada fitur yang membelah kelas sendirian |
| `tests/test_rules_blind_to_ground_truth.py` | `rules/` tidak mengimpor `generator/` dan tidak pernah menyebut kolom `gt_*` |
| `tests/test_weak_labels_are_weak.py` | `weak_labels.csv` tetap lemah (AUPRC di bawah 0,85) tapi tidak lebih buruk dari menebak, dan ablasi tier berfungsi |
| `tests/test_annotation_hides_answers.py` | `annotation/` tidak mengimpor `generator/`, lembar kerja tidak membocorkan skor rule engine atau kolom `gt_*`, dan ketiga anotator menerima item sama dengan urutan tampilan berbeda |

## Struktur repo

| Folder | Isi |
|---|---|
| `generator/` | Generator data sintetis. Dilarang impor dari `rules/` |
| `rules/` | Rule engine (`scoring.py`), label lemah untuk pelatihan. Dilarang impor dari `generator/` |
| `annotation/` | Alat bantu anotasi manual, lihat `annotation/PANDUAN_ANOTASI.md` |
| `models/` | Model ML: R-GCN dan baseline (MLP, XGBoost, GCN homogen) |
| `experiments/` | Skrip pelatihan dan evaluasi, hasil ke `experiments/results/` sebagai CSV |
| `integration/` | Backend FastAPI dan Neo4j untuk dashboard, lihat `integration/README.md` |
| `tests/` | Tes kontrak yang menjaga aturan di bagian atas berkas ini |
| `data/` | Keluaran generator dan anotasi manusia. CSV keluaran generator di-gitignore karena dapat dibuat ulang; anotasi manusia di-commit karena tidak bisa |
