# Integrasi Sistem

Menyambungkan data sintetik dan skor model ke backend FastAPI dan Neo4j, untuk
dashboard dan studi responden.

| Berkas | Isi |
|---|---|
| `schema_map.py` | Pemetaan skema data (lihat `generator/schema.py`) ke skema node/relationship backend |
| `ml_scores.py` | `predictions.csv` menjadi `mlScore`, `mlConfidence` (dari entropi prediksi) |
| `import_synthetic.py` | Impor seed 42 ke Neo4j lewat `POST /api/import/dummy-data` |
| `backend/` | Backend FastAPI, salinan dari `src-old/backend/` dengan perubahan aditif |
| `backend/app/services/ml_layer.py` | Satu-satunya tempat field ML disisipkan ke response |
| `tests/test_no_gt_leak.py` | 20 tes penjaga; yang terpenting: ground truth tidak boleh keluar lewat API |

---

## Urutan menjalankan

```bash
# 0. Dependensi (requirements.txt akar hanya memuat pustaka ML)
pip install -r integration/requirements.txt

# 1. predictions.csv, skor per node dari eksperimen utama.
#    PENTING: pakai --results-dir sementara. Menjalankan train.py dengan
#    --results-dir default dan --seeds tunggal akan menimpa main_results_*.csv
#    resmi dengan hasil satu seed.
python experiments/train.py --save-predictions --results-dir /tmp/pred_run
cp /tmp/pred_run/predictions.csv experiments/results/

# 2. Neo4j + backend
cd integration/backend && docker compose up -d && cd ../..

# 3. Periksa payload tanpa mengirim apa pun
python integration/import_synthetic.py --seed 42 --dry-run

# 4. Impor
python integration/import_synthetic.py --seed 42

# 5. Tes penjaga
python -m pytest integration/tests -q                          # tes integrasi
docker exec satpam-backend python -m pytest tests -q           # tes backend
```

Impor bersifat idempoten (endpoint memakai MERGE): menjalankan langkah 4 dua kali
tetap menghasilkan 5.000 node dan 18.447 relationship, bukan dua kali lipat.

Langkah 1 makan sekitar 260 detik untuk 6 seed. Hasilnya deterministik: keenam
berkas agregat yang ikut ditulis tereproduksi byte-identik dengan tabel hasil
resmi di `experiments/results/main_results_summary.csv`, jadi `predictions.csv`
yang dihasilkan benar-benar sepadan dengan angka resmi, bukan run terpisah
dengan angka berbeda.

`predictions.csv` (~10 MB) di-gitignore karena dapat dibuat ulang persis.

---

## Yang masuk Neo4j, dan yang tidak

Seed 42 dipakai sebagai data demo dashboard: 5.000 node, 18.447 relationship.

| Sumber | Menjadi |
|---|---|
| `nodes.csv` identitas + `feat_*` | properti node |
| `edges.csv` | relationship |
| `weak_labels.csv` | `riskScore` (0–100), `riskLevel`, `triggeredRules` |
| `predictions.csv` | `mlScore`, `mlConfidence`, `mlScore{Mlp,XgbGraph,GcnHomogeneous}` |

**`gt_illicit`, `gt_operator_id`, dan `gt_ecosystem` tidak diimpor.**
`GET /api/entities/{node_type}/{node_id}` mengembalikan node Neo4j apa adanya
tanpa menyaring properti, jadi ground truth di Neo4j sama dengan ground truth
yang terbit lewat API. Kalau sampai terimpor, ground truth akan terbaca
responden studi (lihat `integration/responder_study/`), yang membatalkan
validitas studi itu.

Pemetaannya ditulis ke `integration/test_case_candidates.csv` (di-gitignore),
dipakai koordinator untuk memilih 5 kasus demo secara manual. Penjagaannya aktif
di dua lapis: `schema_map.sanitize_properties()` melempar exception di sisi
impor, dan `ml_layer.strip_forbidden()` menyaring di sisi response bila ground
truth masuk lewat jalur lain (Neo4j Browser, skrip ad-hoc, dump lama).

---

## Prinsip aditif

> Field lama (`riskScore`, `explanation`, `triggeredRules`) tidak ditimpa.
> Field baru (`mlScore`, `mlConfidence`, `criticalSubgraph`) ditambahkan terpisah.

`GET /api/entities/{node_type}/{node_id}` sekarang mengembalikan:

```json
{
  "entity": { "riskScore": 35, "riskLevel": "medium", "triggeredRules": ["R-G4", "R-G5"], "...": "..." },
  "ml": {
    "mlScore": 0.999948,
    "mlConfidence": 0.999187,
    "criticalSubgraph": null,
    "criticalSubgraphStatus": "not_available",
    "mlModel": "rgcn",
    "mlSeed": 42,
    "mlBaselineScores": { "mlScoreMlp": 0.132602, "mlScoreXgbGraph": 0.399922, "mlScoreGcnHomogeneous": 0.633265 },
    "mlUncertainty": 0.000813
  }
}
```

`GET /api/analysis/{node_type}/{node_id}` mempertahankan `assessment`,
`evidencePath`, `earlyWarnings`, dan `blacklistCandidate` apa adanya, lalu
menambah blok `ml` dan `ruleV2`.

`riskScore` bertipe int 0–100 sementara `mlScore` float 0–1, jadi keduanya
memang tidak dapat saling menggantikan.

### `mlScore` memakai R-GCN, dan itu perlu dijelaskan

`mlScore` adalah `prob` dari model `rgcn`, model utama SATPAM. Pada cakupan
enam tipe entitas, GCN homogen justru lebih tinggi (AUPRC 0,5208 vs 0,4744,
lihat `experiments/results/main_results_summary.csv`). Karena itu skor
keempat baseline lain ikut disajikan sebagai `mlBaselineScores`, supaya
perbandingannya terlihat di dashboard dan tidak tersembunyi.

`mlConfidence` tidak ada di `predictions.csv`, ia diturunkan dari entropi
prediksi: `mlConfidence = 1 - H(p)/ln 2`. Skor prioritas antrean review adalah
entropinya sendiri, tersaji sebagai `mlUncertainty`.

---

## `criticalSubgraph`, masih placeholder

GNNExplainer menghasilkan evidence subgraph, dan modulnya (yang punya
`data.hetero`, bobot model terlatih, dan `torch_geometric.explain`) ada di
`experiments/explain.py`, bukan di `integration/`. Modul ini tidak menulis
ulang logikanya.

Nilainya sekarang selalu `null` dengan `criticalSubgraphStatus: "not_available"`.
Titik sambungnya ada di `load_critical_subgraphs()`
([backend/app/services/ml_layer.py](backend/app/services/ml_layer.py)), yang
menunggu berkas:

`experiments/results/critical_subgraphs.json`

```json
{
  "seed": 42,
  "model": "rgcn",
  "subgraphs": {
    "domain_00042": {
      "nodes": ["domain_00042", "phone_00013", "bank_account_00007"],
      "edges": [
        { "src": "domain_00042", "dst": "phone_00013", "relType": "contacts", "importance": 0.83 }
      ]
    }
  }
}
```

`relType` memakai nama relasi dari skema data (huruf kecil, lihat
`generator/schema.py`), bukan label Neo4j. `importance` adalah bobot edge
mask GNNExplainer, dari 0 sampai 1.

**Di dalam Docker, path bawaan itu tidak terjangkau.** `docker-compose.yml`
me-mount hanya `integration/backend` ke `/app`, jadi `experiments/results/` tidak
ada sama sekali di dalam container. Saat berkasnya sudah dibuat, tambahkan mount
dan arahkan lewat variabel lingkungan:

```yaml
  backend:
    environment:
      - SATPAM_CRITICAL_SUBGRAPH_PATH=/data/critical_subgraphs.json
    volumes:
      - .:/app
      - ../../experiments/results:/data:ro
```

Begitu berkas itu ada, tidak ada kode lain yang perlu diubah. Tes
`test_critical_subgraph_langsung_terpakai_begitu_berkasnya_ada` membuktikan
sambungannya sudah benar.

`data.hetero` sengaja dibangun tanpa reverse edge dan diperuntukkan untuk
GNNExplainer serta dashboard, supaya arah relasinya cocok dengan Neo4j.

---

## Catatan tentang backend v1

Backend disalin dari `src-old/backend/` ke `integration/backend/`, dengan
perubahan aditif. `src-old/` dibiarkan sebagai arsip v1 yang tidak tersentuh,
karena beberapa bagian backend saat ini masih menyalin logikanya langsung.

Spec API v1 ada di `docs-old/openapi.json`.

### Keterbatasan yang sengaja tidak ditambal

15 rule v1 (`R-001` sampai `R-015` di `backend/app/services/ai_engine/scoring.py`)
mengandalkan tipe node v1 (`URL`, `Keyword`, `Transaction`, `TrafficEvent`,
`BlacklistEntity`) yang tidak ada di skema data saat ini. Akibatnya
`assessment.triggeredRules` dari `GET /api/analysis/...` nyaris selalu kosong
atas data sintetik v2.

Ini sudah dikonfirmasi empiris, bukan dugaan. Atas `domain_00001` yang
`riskScore`-nya 35 dari rule engine saat ini, `GET /api/analysis/Domain/domain_00001`
mengembalikan `score: 0`, `level: "low"`, `triggeredRules: []`, dengan
`explanation` berbunyi "Belum ada rule risiko utama yang aktif pada data dummy
saat ini." Blok `ruleV2` di response yang sama menunjukkan angka sebenarnya:
`35`, `medium`, `["R-G4", "R-G5"]`.

Ini bukan kerusakan akibat perubahan di `integration/`: rule engine v1 memang
tidak cocok dengan skema data saat ini. Rule engine yang sungguhan (`rules/`)
keluarannya sudah tersaji utuh sebagai properti node
`riskScore`/`riskLevel`/`triggeredRules` serta blok `ruleV2`. Keputusan yang
diambil: laporkan sebagai keterbatasan, jangan menambal `scoring.py` v1.

Konsekuensi praktis untuk studi responden: perbandingan "penjelasan rule-based
vs evidence subgraph" belum bisa dijalankan dari endpoint `analysis` apa
adanya, karena sisi rule-based-nya kosong. Sumber penjelasan rule-based yang
layak dipakai adalah `ruleV2.triggeredRules`.

### Field kosmetik yang disintesis

Model Pydantic v1 mewajibkan field yang tidak ada padanannya di skema saat ini
(`domainName`, `normalizedNumber`, `maskedAccountNumber`, `profileUrl`, dan
beberapa lainnya). Nilainya disintesis deterministik dari `node_id` dengan
bentuk yang mustahil dibaca sebagai identitas nyata: TLD `.example` (RFC 2606)
dan awalan `SIM-`. Jangan pernah menggantinya dengan nilai yang tampak
realistis.

Satu di antaranya perlu perhatian: `ReportNode.categoryHint` adalah enum wajib
(`judol` / `pinjol_illegal` / `cross_ecosystem` / `payment_flow` /
`traffic_crawler` / `benign`) yang satu-satunya sumber informasinya adalah
`gt_ecosystem`. Memakai itu berarti membocorkan ground truth, jadi nilainya
dibuat **konstan** untuk seluruh 700 node report: konstanta tidak membawa
informasi pembeda apa pun sehingga tidak dapat membimbing responden studi.
Jangan dibaca sebagai klasifikasi.
