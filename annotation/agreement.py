"""Kesepakatan antar-anotator: Fleiss' kappa dan Cohen's kappa berpasangan.

Kappa dipakai sebagai ukuran **kualitas anotasi**, bukan ukuran kebenarannya.
Kesepakatan tinggi berarti tugasnya terdefinisi jelas dan anotator memahaminya
sama; kesepakatan rendah pada strata tertentu berarti strata itu memang ambigu.

Yang dihitung:

- **Fleiss' kappa** untuk ketiga anotator sekaligus. Cohen's kappa hanya berlaku
  untuk dua rater, jadi Fleiss yang menjadi angka utama.
- **Cohen's kappa berpasangan** A-B, A-C, B-C, untuk melihat apakah ada satu
  anotator yang menyimpang dari dua lainnya.
- **Persen kesepakatan mentah** sebagai pendamping — kappa bisa rendah hanya
  karena kelas sangat tidak seimbang, dan persen kesepakatan menahan salah tafsir.
- **Kappa per strata.** Ini yang paling berguna untuk pelaporan: bila kesepakatan
  jatuh di strata ambigu dan tinggi di strata yang rule engine yakin, itu bukti
  kuantitatif bahwa strata ambigu memang sulit.
- **Selang kepercayaan bootstrap** untuk kappa. Dipakai saat membandingkan dua
  ronde anotasi: tanpa selang, kenaikan kappa antar-ronde tidak bisa dibedakan
  dari kebetulan ukuran sampel.

Pita tafsir memakai Landis & Koch, *Biometrics* 33(1), 1977.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

#: Ulangan bootstrap dan benihnya. Benih tetap supaya laporan yang dihasilkan
#: dua kali dari data yang sama menghasilkan angka yang sama persis.
BOOTSTRAP_REPEATS = 4000
BOOTSTRAP_SEED = 7

#: Pita tafsir Landis & Koch (1977).
LANDIS_KOCH: tuple[tuple[float, str], ...] = (
    (0.81, "hampir sempurna"),
    (0.61, "kuat"),
    (0.41, "sedang"),
    (0.21, "lumayan"),
    (0.00, "lemah"),
)


def interpret(kappa: float) -> str:
    """Tafsir kualitatif sebuah nilai kappa (Landis & Koch, 1977)."""
    if kappa < 0:
        return "lebih buruk dari kebetulan"
    for threshold, label in LANDIS_KOCH:
        if kappa >= threshold:
            return label
    return "lemah"


@dataclass
class AgreementResult:
    """Hasil perhitungan kesepakatan."""

    n_items: int
    n_raters: int
    fleiss_kappa: float
    percent_agreement: float
    unanimous: int
    pairwise_cohen: dict[str, float] = field(default_factory=dict)
    per_stratum: dict[str, dict[str, float]] = field(default_factory=dict)
    label_rate: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "n_items": self.n_items,
            "n_raters": self.n_raters,
            "fleiss_kappa": round(self.fleiss_kappa, 4),
            "fleiss_interpretation": interpret(self.fleiss_kappa),
            "percent_agreement": round(self.percent_agreement, 4),
            "unanimous_items": self.unanimous,
            "pairwise_cohen": {
                pair: round(value, 4) for pair, value in self.pairwise_cohen.items()
            },
            "per_stratum": {
                name: {key: round(value, 4) for key, value in stats.items()}
                for name, stats in self.per_stratum.items()
            },
            "label_rate_per_annotator": {
                name: round(value, 4) for name, value in self.label_rate.items()
            },
        }


def fleiss_kappa(ratings: list[list[int]]) -> float:
    """Fleiss' kappa untuk kategori biner.

    Args:
        ratings: Satu daftar per item, berisi label 0/1 dari setiap rater.
            Semua item harus punya jumlah rater yang sama.

    Returns:
        Nilai kappa. 0.0 bila seluruh rater memberi label identik untuk semua
        item — pada keadaan itu kesepakatan yang teramati sama dengan yang
        diharapkan kebetulan, dan kappa tidak terdefinisi.
    """
    if not ratings:
        return 0.0
    n_raters = len(ratings[0])
    if n_raters < 2 or any(len(row) != n_raters for row in ratings):
        raise ValueError("setiap item harus dinilai jumlah rater yang sama, minimal 2")

    n_items = len(ratings)
    counts = [[row.count(0), row.count(1)] for row in ratings]

    # Kesepakatan teramati per item.
    item_agreement = [
        (sum(value * value for value in row) - n_raters) / (n_raters * (n_raters - 1))
        for row in counts
    ]
    observed = sum(item_agreement) / n_items

    # Proporsi setiap kategori di seluruh penilaian.
    totals = [sum(row[category] for row in counts) for category in (0, 1)]
    proportions = [value / (n_items * n_raters) for value in totals]
    expected = sum(value * value for value in proportions)

    if expected >= 1.0:
        return 0.0
    return (observed - expected) / (1.0 - expected)


def cohen_kappa(first: list[int], second: list[int]) -> float:
    """Cohen's kappa untuk dua rater, kategori biner."""
    if len(first) != len(second):
        raise ValueError("kedua daftar penilaian harus sama panjang")
    if not first:
        return 0.0

    n = len(first)
    observed = sum(1 for a, b in zip(first, second) if a == b) / n

    expected = 0.0
    for category in (0, 1):
        expected += (first.count(category) / n) * (second.count(category) / n)

    if expected >= 1.0:
        return 0.0
    return (observed - expected) / (1.0 - expected)


def compute_agreement(
    labels: dict[str, dict[str, int]],
    stratum_of: dict[str, str] | None = None,
) -> AgreementResult:
    """Hitung seluruh ukuran kesepakatan.

    Args:
        labels: Pemeta `annotator_id` -> (`node_id` -> label 0/1).
        stratum_of: Opsional, untuk kappa per strata. Hanya dipakai koordinator.
    """
    annotators = sorted(labels)
    if len(annotators) < 2:
        raise ValueError("butuh minimal dua anotator untuk menghitung kesepakatan")

    shared = set(labels[annotators[0]])
    for name in annotators[1:]:
        shared &= set(labels[name])
    items = sorted(shared)
    if not items:
        raise ValueError("tidak ada node yang dinilai oleh seluruh anotator")

    matrix = [[labels[name][node_id] for name in annotators] for node_id in items]

    unanimous = sum(1 for row in matrix if len(set(row)) == 1)
    percent = unanimous / len(items)

    pairwise: dict[str, float] = {}
    for index, first in enumerate(annotators):
        for second in annotators[index + 1 :]:
            pairwise[f"{first}-{second}"] = cohen_kappa(
                [labels[first][node_id] for node_id in items],
                [labels[second][node_id] for node_id in items],
            )

    per_stratum: dict[str, dict[str, float]] = {}
    if stratum_of:
        grouped: dict[str, list[str]] = {}
        for node_id in items:
            grouped.setdefault(stratum_of.get(node_id, "?"), []).append(node_id)
        for name, members in sorted(grouped.items()):
            rows = [[labels[a][node_id] for a in annotators] for node_id in members]
            positive = sum(sum(row) for row in rows)
            per_stratum[name] = {
                "n_items": float(len(members)),
                "fleiss_kappa": fleiss_kappa(rows),
                "percent_agreement": sum(
                    1 for row in rows if len(set(row)) == 1
                )
                / len(members),
                "positive_rate": positive / (len(members) * len(annotators)),
            }

    return AgreementResult(
        n_items=len(items),
        n_raters=len(annotators),
        fleiss_kappa=fleiss_kappa(matrix),
        percent_agreement=percent,
        unanimous=unanimous,
        pairwise_cohen=pairwise,
        per_stratum=per_stratum,
        label_rate={
            name: sum(labels[name][node_id] for node_id in items) / len(items)
            for name in annotators
        },
    )


def bootstrap_kappa_ci(
    labels: dict[str, dict[str, int]],
    *,
    repeats: int = BOOTSTRAP_REPEATS,
    seed: int = BOOTSTRAP_SEED,
    level: float = 0.95,
) -> tuple[float, float]:
    """Selang kepercayaan Fleiss' kappa lewat bootstrap atas node.

    Yang diundi adalah **node**, bukan penilaian per rater: ketiga penilaian
    satu node ikut terbawa sekaligus, karena ketergantungan antar-rater pada
    node yang sama justru yang sedang diukur.

    Dipakai untuk menjawab satu pertanyaan saja — apakah kappa dua ronde
    berbeda, atau selisihnya masih muat di dalam ketidakpastian ukuran sampel.
    Selang yang tidak beririsan sudah cukup untuk menyatakan ada beda; selang
    yang beririsan **belum tentu** berarti tidak ada beda.
    """
    annotators = sorted(labels)
    shared = set(labels[annotators[0]])
    for name in annotators[1:]:
        shared &= set(labels[name])
    items = sorted(shared)
    if len(items) < 2:
        return (0.0, 0.0)

    rows = {node_id: [labels[a][node_id] for a in annotators] for node_id in items}
    rng = random.Random(seed)
    values = []
    for _ in range(repeats):
        draw = [rows[items[rng.randrange(len(items))]] for _ in range(len(items))]
        values.append(fleiss_kappa(draw))
    values.sort()
    tail = (1.0 - level) / 2.0
    return (
        values[int(tail * repeats)],
        values[min(int((1.0 - tail) * repeats), repeats - 1)],
    )


def majority_label(votes: list[int]) -> int:
    """Label suara terbanyak. Dengan tiga rater biner, seri tidak mungkin."""
    return 1 if sum(votes) * 2 > len(votes) else 0
