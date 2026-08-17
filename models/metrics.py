"""Metrik evaluasi SATPAM.

Satu tempat untuk semua metrik supaya R-GCN dan keempat baseline dinilai dengan
definisi yang identik. Kalau tiap model menghitung metriknya sendiri, perbedaan
kecil pada penanganan ambang atau pengurutan bisa disalahartikan sebagai
perbedaan performa.

Urutan pelaporan: **AUPRC lebih dulu.** Pada data dengan
sekitar 7% positif, ROC-AUC memberi gambaran terlalu optimistis karena
didominasi kelas mayoritas, jadi ia hanya pelengkap dan tidak boleh dipakai
sebagai metrik utama.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

#: Nilai k untuk Recall@k. Mewakili berapa banyak node yang realistis
#: sanggup direview analis.
RECALL_AT_K: tuple[int, ...] = (50, 100)

#: Ambang keputusan untuk metrik yang butuh label biner (Recall, Macro-F1).
#: Dipatok 0,5 dan tidak disetel per model — menyetel ambang per model dengan
#: melihat hasil akan membuat perbandingan antar-model tidak setara.
DECISION_THRESHOLD: float = 0.5

#: Jumlah bin untuk ECE.
ECE_BINS: int = 10


def evaluate(
    y_true: np.ndarray,
    y_score: np.ndarray,
    *,
    recall_at_k: tuple[int, ...] = RECALL_AT_K,
    threshold: float = DECISION_THRESHOLD,
) -> dict[str, float]:
    """Hitung seluruh metrik untuk satu himpunan prediksi.

    Args:
        y_true: label biner 0/1. **Harus** `gt_illicit`, bukan weak label —
            evaluasi terhadap `weak_labels.csv` dilarang.
        y_score: skor kontinu, makin tinggi makin berisiko. Untuk metrik
            kalibrasi (ECE, Brier) skor harus berupa probabilitas 0..1.
        recall_at_k: daftar k untuk Recall@k.
        threshold: ambang untuk Recall dan Macro-F1.

    Returns:
        Dict metrik. `auprc` adalah metrik utama.
    """
    y_true = np.asarray(y_true).astype(int).ravel()
    y_score = np.asarray(y_score, dtype=np.float64).ravel()
    if y_true.shape != y_score.shape:
        raise ValueError(f"bentuk tidak cocok: {y_true.shape} vs {y_score.shape}")
    if y_true.size == 0:
        raise ValueError("tidak ada node untuk dievaluasi")
    if not np.isfinite(y_score).all():
        raise ValueError("y_score memuat NaN/inf")

    n_pos = int(y_true.sum())
    out: dict[str, float] = {
        "n": float(y_true.size),
        "n_pos": float(n_pos),
        "pos_rate": float(n_pos / y_true.size),
    }

    # Bila satu kelas tidak muncul, metrik berbasis peringkat tidak terdefinisi.
    # Kembalikan NaN daripada angka yang menyesatkan.
    if n_pos == 0 or n_pos == y_true.size:
        degenerate = ["auprc", "roc_auc", "recall", "precision", "macro_f1"]
        out.update({name: float("nan") for name in degenerate})
        out.update({f"recall_at_{k}": float("nan") for k in recall_at_k})
        out["ece"] = float("nan")
        out["brier"] = float("nan")
        return out

    # --- metrik utama ---
    out["auprc"] = float(average_precision_score(y_true, y_score))

    # --- pelengkap berbasis peringkat ---
    out["roc_auc"] = float(roc_auc_score(y_true, y_score))

    # --- Recall@k: analis hanya mereview k teratas ---
    order = np.argsort(-y_score, kind="stable")
    for k in recall_at_k:
        top = order[: min(k, y_true.size)]
        out[f"recall_at_{k}"] = float(y_true[top].sum() / n_pos)

    # --- metrik berbasis ambang ---
    y_pred = (y_score >= threshold).astype(int)
    out["recall"] = float(recall_score(y_true, y_pred, zero_division=0))
    out["precision"] = float(precision_score(y_true, y_pred, zero_division=0))
    out["macro_f1"] = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    # --- kalibrasi (wajib dilaporkan, karena skor dipakai memprioritaskan review) ---
    out["ece"] = expected_calibration_error(y_true, y_score)
    out["brier"] = brier_score(y_true, y_score)

    return out


def expected_calibration_error(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = ECE_BINS
) -> float:
    """Expected Calibration Error dengan bin lebar-sama.

    ECE = Σ (|B_m| / n) × |akurasi(B_m) − keyakinan(B_m)|

    Hanya bermakna bila `y_prob` benar-benar probabilitas. Bila model
    menghasilkan skor tak terkalibrasi, angka ini besar — dan itu justru
    informasi yang dicari untuk dibandingkan sebelum dan sesudah
    temperature scaling.
    """
    y_true = np.asarray(y_true).astype(int).ravel()
    y_prob = np.asarray(y_prob, dtype=np.float64).ravel()
    if y_prob.min() < 0.0 or y_prob.max() > 1.0:
        return float("nan")

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    # `right=True` pada bin pertama agar p=0 tidak jatuh ke luar rentang.
    index = np.clip(np.digitize(y_prob, edges[1:-1], right=False), 0, n_bins - 1)

    total = 0.0
    for bin_id in range(n_bins):
        rows = index == bin_id
        count = int(rows.sum())
        if count == 0:
            continue
        accuracy = float(y_true[rows].mean())
        confidence = float(y_prob[rows].mean())
        total += (count / y_true.size) * abs(accuracy - confidence)
    return float(total)


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Brier score = rata-rata kuadrat selisih probabilitas dan label."""
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    y_prob = np.asarray(y_prob, dtype=np.float64).ravel()
    return float(np.mean((y_prob - y_true) ** 2))


def reliability_curve(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = ECE_BINS
) -> dict[str, np.ndarray]:
    """Titik-titik untuk reliability diagram.

    Returns:
        Dict berisi `confidence`, `accuracy`, dan `count` per bin yang terisi.
    """
    y_true = np.asarray(y_true).astype(int).ravel()
    y_prob = np.asarray(y_prob, dtype=np.float64).ravel()
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    index = np.clip(np.digitize(y_prob, edges[1:-1], right=False), 0, n_bins - 1)

    confidence, accuracy, count = [], [], []
    for bin_id in range(n_bins):
        rows = index == bin_id
        if not rows.any():
            continue
        confidence.append(float(y_prob[rows].mean()))
        accuracy.append(float(y_true[rows].mean()))
        count.append(int(rows.sum()))
    return {
        "confidence": np.asarray(confidence),
        "accuracy": np.asarray(accuracy),
        "count": np.asarray(count),
    }


#: Urutan kolom saat metrik ditulis ke CSV. AUPRC diletakkan di depan.
METRIC_COLUMNS: tuple[str, ...] = (
    "auprc",
    "recall",
    "recall_at_50",
    "recall_at_100",
    "macro_f1",
    "precision",
    "roc_auc",
    "ece",
    "brier",
    "n",
    "n_pos",
    "pos_rate",
)
