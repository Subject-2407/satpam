"""Pembagian bilangan bulat menurut bobot.

Dipakai bersama oleh `operators.py` (membagi node ilegal ke antar-operator dan
ke tipe node) dan `population.py` (membagi kuota tipe node sah). Ditaruh di
modul sendiri supaya tidak ada modul yang perlu mengimpor nama privat modul
lain.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

import numpy as np


def largest_remainder(weights: np.ndarray | list[float], total: int) -> list[int]:
    """Bagi `total` butir menurut `weights` dengan metode sisa terbesar.

    Deterministik, dan jumlah hasilnya selalu tepat `total` — dua sifat yang
    tidak dimiliki pembulatan biasa. Saat sisa dua bagian sama besar, indeks
    yang lebih kecil menang, sehingga hasilnya tidak bergantung pada urutan
    pengurutan yang tak stabil.

    Contoh:
        >>> largest_remainder([0.5, 0.3, 0.2], 10)
        [5, 3, 2]
        >>> sum(largest_remainder([0.16, 0.08, 0.11, 0.14, 0.05, 0.46], 8))
        8
    """
    share = np.asarray(weights, dtype=float)
    if share.size == 0:
        return []
    if total <= 0:
        return [0] * share.size

    total_weight = share.sum()
    if total_weight <= 0:
        raise ValueError("jumlah bobot harus positif")

    share = share / total_weight
    exact = share * total
    floors = np.floor(exact).astype(int)
    shortfall = total - int(floors.sum())

    if shortfall > 0:
        order = sorted(
            range(share.size),
            key=lambda i: (-(exact[i] - floors[i]), i),
        )
        for i in order[:shortfall]:
            floors[i] += 1

    return [int(value) for value in floors]
