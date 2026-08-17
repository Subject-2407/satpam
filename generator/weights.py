"""Definisi tunggal bobot bukti sebuah edge (`edges.csv.weight`).

Ditaruh di modul sendiri karena dua penerbit edge memakainya — `evidence.py`
untuk edge asli dan `noise.py` untuk edge palsu — dan keduanya **wajib**
memakai distribusi yang sama. Kalau definisinya terpisah, keduanya bisa
berselisih dan bobot berubah menjadi penanda "edge ini palsu".

**Bobot ditentukan hanya oleh jenis relasi.** Tidak oleh aturan generatif yang
menerbitkannya, tidak oleh sah atau tidaknya node di kedua ujungnya. Itu arti
"kekuatan bukti" yang benar: keandalan sebuah tautan bergantung pada kanal
pengamatannya, bukan pada siapa yang diamati.

Setelan sebelumnya membiarkan tiap aturan memilih tier bobotnya sendiri. Karena
aturan G1-G8 hanya berlaku pada node operator sementara edge latar hanya pada
node sah, bobot menjadi salinan label: median 0,671 untuk edge antar dua node
ilegal berbanding 0,447 untuk edge antar dua node sah, dan rata-rata bobot per
node sendirian memisahkan kelas pada AUC 0,795 — lebih bocor daripada fitur mana
pun di `nodes.csv`.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

import numpy as np

from generator.config import FloatRange, GeneratorParams

#: Pembulatan bobot agar keluaran CSV rapi dan bisa dibandingkan persis.
WEIGHT_DECIMALS: int = 4


def tier_bounds(params: GeneratorParams, rel_type: str) -> FloatRange:
    """Rentang bobot untuk sebuah tipe relasi.

    Raises:
        KeyError: bila tipe relasi belum diberi tier. `GeneratorParams` sudah
            memeriksanya saat dibuat, jadi ini hanya jaring terakhir.
    """
    tier = params.weight_tier_of_relation[rel_type]
    return {
        "high": params.weight_tier_high,
        "mid": params.weight_tier_mid,
        "low": params.weight_tier_low,
    }[tier]


def sample_weight(
    params: GeneratorParams,
    rng: np.random.Generator,
    rel_type: str,
) -> float:
    """Ambil satu bobot bukti untuk edge bertipe relasi `rel_type`."""
    low, high = tier_bounds(params, rel_type)
    return round(float(rng.uniform(low, high)), WEIGHT_DECIMALS)
