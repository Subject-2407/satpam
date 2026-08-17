"""Temperature scaling untuk kalibrasi skor.

Kalibrasi wajib dilaporkan karena skor dipakai **memprioritaskan review analis**:
skor 0,9 seharusnya berarti sekitar sembilan dari sepuluh node
seperti itu benar-benar ilegal, bukan sekadar "lebih tinggi dari 0,8".

Metode: satu parameter suhu `T` yang membagi logit sebelum softmax, dicari
dengan meminimalkan NLL pada split val (Guo dkk., ICML 2017). `T` tunggal tidak
mengubah urutan peringkat, jadi AUPRC dan Recall@k **tidak berubah** — yang
berubah hanya ECE dan Brier.

> **Catatan penting untuk interpretasi hasil.** Suhu dicocokkan terhadap weak
> label di split val, karena `gt_illicit` dilarang menyentuh pelatihan dan
> pemilihan parameter. Weak label punya laju positif sekitar 41% pada node
> entitas, sementara ground truth sekitar 7%. Selisih laju dasar sebesar itu
> tidak dapat dihapus oleh penskalaan monoton satu parameter: model akan tetap
> tampak terlalu yakin ketika ECE-nya diukur terhadap `gt_illicit`. Ini
> konsekuensi yang memang mengikuti protokol puritan, bukan bug — dan justru
> temuan yang layak dilaporkan. `fit_prior_correction` disediakan untuk
> menunjukkan seberapa banyak sisa galat kalibrasi yang berasal murni dari
> selisih laju dasar tersebut.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F


def fit_temperature(
    logit: np.ndarray,
    y: np.ndarray,
    *,
    max_iter: int = 200,
    lr: float = 0.01,
) -> float:
    """Cari suhu yang meminimalkan NLL.

    Args:
        logit: `[n, 2]` logit mentah pada himpunan kalibrasi (split val).
        y: label biner pada himpunan yang sama. Sesuai protokol puritan, ini
            weak label — bukan `gt_illicit`.

    Returns:
        Suhu `T > 0`. `T > 1` berarti model terlalu yakin dan skornya dilunakkan.
    """
    logit_t = torch.as_tensor(np.asarray(logit, dtype=np.float64), dtype=torch.float32)
    y_t = torch.as_tensor(np.asarray(y).astype(int), dtype=torch.long)
    if logit_t.ndim != 2:
        raise ValueError(f"logit harus [n, 2], diterima {logit_t.shape}")
    if len(torch.unique(y_t)) < 2:
        # Tanpa kedua kelas, NLL tidak punya minimum yang bermakna.
        return 1.0

    # Dioptimalkan dalam log-ruang supaya T selalu positif tanpa perlu proyeksi.
    log_t = torch.zeros(1, requires_grad=True)
    optimizer = torch.optim.LBFGS([log_t], lr=lr, max_iter=max_iter)

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        loss = F.cross_entropy(logit_t / torch.exp(log_t), y_t)
        loss.backward()
        return loss

    optimizer.step(closure)  # type: ignore[arg-type]
    return float(torch.exp(log_t.detach()).item())


def apply_temperature(logit: np.ndarray, temperature: float) -> np.ndarray:
    """Terapkan suhu dan kembalikan probabilitas kelas 1.

    Karena `T` tunggal bersifat monoton, seluruh metrik berbasis peringkat
    (AUPRC, Recall@k, ROC-AUC) tidak berubah. Hanya ECE dan Brier yang bergerak.
    """
    if temperature <= 0:
        raise ValueError(f"suhu harus positif, diterima {temperature}")
    scaled = torch.as_tensor(np.asarray(logit, dtype=np.float64), dtype=torch.float32)
    return F.softmax(scaled / temperature, dim=1)[:, 1].numpy().astype(np.float64)


def fit_prior_correction(prob: np.ndarray, source_rate: float, target_rate: float) -> np.ndarray:
    """Geser probabilitas dari laju dasar `source_rate` ke `target_rate`.

    Koreksi laju dasar baku (Saerens dkk., 2002; Elkan, 2001):

        p' = (p × r_t / r_s) / (p × r_t / r_s + (1 − p) × (1 − r_t) / (1 − r_s))

    Dipakai sebagai **diagnostik**, bukan bagian pipeline utama: ia menunjukkan
    berapa banyak sisa galat kalibrasi terhadap `gt_illicit` yang semata-mata
    berasal dari selisih laju positif weak label dan ground truth. Memakainya
    sebagai koreksi resmi akan membutuhkan `target_rate` dari ground truth, dan
    itu berarti `gt` ikut menyetel keluaran model.
    """
    prob = np.clip(np.asarray(prob, dtype=np.float64), 1e-12, 1 - 1e-12)
    if not 0 < source_rate < 1 or not 0 < target_rate < 1:
        raise ValueError("laju dasar harus di antara 0 dan 1")
    pos = prob * (target_rate / source_rate)
    neg = (1 - prob) * ((1 - target_rate) / (1 - source_rate))
    return pos / (pos + neg)
