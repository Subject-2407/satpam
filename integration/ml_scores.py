"""
Pemetaan skor model orang B ke field API `mlScore` dan `mlConfidence`.

Sumber: `experiments/results/predictions.csv`, dihasilkan oleh
`python experiments/train.py --save-predictions` ([experiments/train.py:287]).
Kolomnya: `seed, model, node_id, node_type, split, prob, rule_score, gt_illicit`.

## Yang dipetakan

| Field API | Sumber |
|---|---|
| `mlScore` | `prob` model `rgcn` — model utama SATPAM |
| `mlConfidence` | diturunkan dari `prob`, lihat di bawah |
| `mlScoreMlp`, `mlScoreXgbGraph`, `mlScoreGcnHomogeneous` | `prob` tiap baseline |

`mlConfidence` **tidak ada** di `predictions.csv` — orang B tidak menghasilkan
kolom confidence. Ia diturunkan di sini dari entropi prediksi,
`H(p) = -Σ p log p`, dinormalkan ke rentang 0–1:

    mlConfidence = 1 - H(p) / ln 2

Jadi p=0,5 memberi confidence 0 (model paling bimbang) dan p→0 atau p→1
memberi confidence 1. Skor prioritas antrean review adalah entropinya
sendiri, yaitu `1 - mlConfidence` — tidak disimpan terpisah karena redundan.

## Yang sengaja TIDAK dipetakan

Baseline `rule_based` di `predictions.csv` adalah `rule_score` yang dinormalkan
ke 0–1 ([models/baselines.py:42]), jadi ia sudah tersaji utuh sebagai `riskScore`
(0–100) hasil impor `weak_labels.csv`. Menyajikannya lagi dengan awalan `ml`
akan menyesatkan: rule engine bukan model ML.

Kolom `gt_illicit` dibaca modul ini **hanya** untuk menulis
`test_case_candidates.csv` di mesin lokal, dan tidak pernah ikut ke properti node.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_PATH = REPO_ROOT / "experiments" / "results" / "predictions.csv"

# Model utama sistem. Catatan jujur: pada cakupan 6 tipe
# entitas, GCN homogen justru lebih tinggi (AUPRC 0,5208 vs 0,4744).
# `mlScore` tetap memakai R-GCN karena itulah
# model yang ditetapkan sebagai model sistem; skor GCN homogen tetap ikut
# tersaji sebagai `mlScoreGcnHomogeneous` supaya perbandingannya bisa dilihat
# di dashboard, bukan disembunyikan.
PRIMARY_MODEL = "rgcn"

# model di predictions.csv -> nama properti node
ALTERNATIVE_MODELS: dict[str, str] = {
    "mlp": "mlScoreMlp",
    "xgb_graph": "mlScoreXgbGraph",
    "gcn_homogeneous": "mlScoreGcnHomogeneous",
}

_LN2 = math.log(2.0)


class PredictionsMissingError(FileNotFoundError):
    """`predictions.csv` belum dibangkitkan."""


def normalized_confidence(prob: float) -> float:
    """`1 - H(p)/ln 2` dengan `H` entropi biner."""
    p = min(max(float(prob), 0.0), 1.0)
    if p <= 0.0 or p >= 1.0:
        return 1.0
    entropy = -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))
    return round(1.0 - entropy / _LN2, 6)


def load_predictions(seed: int, path: Path | None = None) -> pd.DataFrame:
    """Baca `predictions.csv` dan sisakan satu seed."""
    source = path or PREDICTIONS_PATH
    if not source.exists():
        raise PredictionsMissingError(
            f"{source} tidak ada. Bangkitkan lebih dulu:\n"
            "  python experiments/train.py --save-predictions --results-dir <dir sementara>\n"
            "lalu salin HANYA predictions.csv ke experiments/results/.\n"
            "Menjalankannya langsung dengan --results-dir default dan --seeds "
            "tunggal akan menimpa main_results_*.csv milik orang B."
        )
    frame = pd.read_csv(source)
    subset = frame[frame["seed"] == seed]
    if subset.empty:
        available = sorted(frame["seed"].unique().tolist())
        raise ValueError(f"seed {seed} tidak ada di {source.name}; tersedia: {available}")
    return subset


def build_ml_properties(seed: int, path: Path | None = None) -> dict[str, dict[str, Any]]:
    """`node_id` -> properti ML yang siap ditempel ke node Neo4j.

    `criticalSubgraph` **tidak** dihasilkan di sini — lihat
    `integration/backend/app/services/ml_layer.py`.
    """
    subset = load_predictions(seed, path)
    wide = subset.pivot_table(index="node_id", columns="model", values="prob", aggfunc="first")

    if PRIMARY_MODEL not in wide.columns:
        raise ValueError(
            f"model {PRIMARY_MODEL!r} tidak ada di predictions.csv; "
            f"tersedia: {sorted(wide.columns)}"
        )

    properties: dict[str, dict[str, Any]] = {}
    for node_id, row in wide.iterrows():
        primary = float(row[PRIMARY_MODEL])
        entry: dict[str, Any] = {
            "mlScore": round(primary, 6),
            "mlConfidence": normalized_confidence(primary),
            "mlModel": PRIMARY_MODEL,
            "mlSeed": int(seed),
        }
        for model_name, field_name in ALTERNATIVE_MODELS.items():
            if model_name in wide.columns and pd.notna(row[model_name]):
                entry[field_name] = round(float(row[model_name]), 6)
        properties[str(node_id)] = entry
    return properties


def build_test_case_candidates(seed: int, path: Path | None = None) -> pd.DataFrame:
    """Tabel kandidat kasus uji studi responden — **lokal saja**.

    Inilah satu-satunya keluaran yang memuat `gt_*`. Berkas ini di-gitignore dan
    tidak pernah masuk Neo4j: `GET /api/entities/...` mengembalikan node apa
    adanya, sehingga `gt_illicit` di Neo4j akan terbaca responden dan merusak
    validitas studi.

    Perhatikan satuan `rule_score` di sini: kolom ini datang dari
    `predictions.csv` dan sudah **dinormalkan ke 0–1** oleh loader orang B
    ([models/baselines.py:42]), sedangkan `riskScore` di Neo4j memakai skala
    **0–100** asli `weak_labels.csv`. Keduanya angka yang sama, beda skala.
    """
    subset = load_predictions(seed, path)
    primary = subset[subset["model"] == PRIMARY_MODEL].copy()
    primary["mlScore"] = primary["prob"].round(6)
    primary["mlConfidence"] = primary["prob"].map(normalized_confidence)
    columns = [
        "node_id",
        "node_type",
        "split",
        "mlScore",
        "mlConfidence",
        "rule_score",
        "gt_illicit",
    ]
    return (
        primary[columns]
        .sort_values(["gt_illicit", "mlScore"], ascending=[False, False])
        .reset_index(drop=True)
    )
