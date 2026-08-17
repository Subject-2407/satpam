"""Bagian B SATPAM — pemuat data, R-GCN, dan baseline.

Aturan yang berlaku di seluruh paket ini:

- `gt_illicit` hanya untuk evaluasi. Ia tidak pernah masuk fitur, tidak pernah
  masuk loss, dan tidak pernah dipakai memilih model atau hyperparameter.
- `weak_labels.csv` hanya untuk pelatihan. Dilarang dipakai sebagai label
  pengujian.
- Metrik utama AUPRC, bukan ROC-AUC.
- Split temporal dari kolom `split`, diverifikasi ulang di `loader.py`.
"""

from .loader import (
    ENTITY_TYPES,
    FEATURE_COLUMNS,
    NODE_TYPES,
    REL_TYPES,
    SatpamData,
    load_seed,
)
from .metrics import METRIC_COLUMNS, evaluate, reliability_curve

__all__ = [
    "ENTITY_TYPES",
    "FEATURE_COLUMNS",
    "METRIC_COLUMNS",
    "NODE_TYPES",
    "REL_TYPES",
    "SatpamData",
    "evaluate",
    "load_seed",
    "reliability_curve",
]
