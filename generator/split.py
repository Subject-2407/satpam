"""LANGKAH 7 — temporal split berdasarkan `first_seen_at`.

Batasnya mengikat: `train` persentil 0–70, `val` 70–85, `test` 85–100. Split
acak per-node dilarang karena akan membocorkan informasi masa depan dan
menghapus skenario early warning yang ingin disimulasikan.

**Ambang batasnya ikut dicatat ke manifest.** Persentil bisa dihitung dengan
beberapa metode interpolasi yang hasilnya berbeda-beda, jadi kalau hanya
persentilnya yang disebut, orang lain yang menghitung ulang bisa mendapat
pembagian berbeda dari kolom `split` dan menyimpulkan generatornya salah.
Dengan ambang batas berupa timestamp yang tercatat, verifikasinya tidak perlu
menebak metode apa pun: bandingkan saja `first_seen_at` dengan ambangnya.

Diagnostik jumlah positif per split juga dilaporkan. Ini yang menahan kegagalan
paling mahal: bila rotasi domain membuat hampir semua node ilegal mendarat di
`train`, bagian `test` bisa nyaris tanpa positif dan AUPRC di sana tidak
bermakna — dan tanpa diagnostik, itu baru ketahuan berhari-hari kemudian.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from generator.config import GeneratorParams
from generator.records import NodeRecord
from generator.schema import SPLITS
from generator.timeline import Timeline


@dataclass(frozen=True)
class SplitReport:
    """Ambang batas dan sebaran hasil temporal split."""

    train_threshold: datetime
    val_threshold: datetime
    counts: dict[str, int]
    illicit_counts: dict[str, int]

    @property
    def splits_without_positives(self) -> list[str]:
        """Split yang tidak punya node positif sama sekali."""
        return [name for name in SPLITS if self.illicit_counts.get(name, 0) == 0]

    def as_dict(self, timeline: Timeline) -> dict[str, object]:
        """Bentuk untuk `manifest.params` (opsi (a) yang disetujui)."""
        total = sum(self.counts.values()) or 1
        return {
            "train_threshold": timeline.to_iso(self.train_threshold),
            "val_threshold": timeline.to_iso(self.val_threshold),
            "nodes": dict(self.counts),
            "illicit_nodes": dict(self.illicit_counts),
            "illicit_share": {
                name: round(
                    self.illicit_counts.get(name, 0) / max(self.counts.get(name, 0), 1),
                    6,
                )
                for name in SPLITS
            },
            "node_share": {
                name: round(self.counts.get(name, 0) / total, 6) for name in SPLITS
            },
        }


def assign_temporal_split(
    params: GeneratorParams,
    timeline: Timeline,
    nodes: Sequence[NodeRecord],
) -> SplitReport:
    """Isi kolom `split` tiap node menurut persentil `first_seen_at`.

    Tidak memakai keacakan sama sekali: hasilnya sepenuhnya ditentukan oleh
    `first_seen_at`, jadi dua kali jalan atas populasi yang sama selalu
    menghasilkan pembagian yang sama.

    Aturan batasnya eksplisit — `offset <= ambang_train` masuk `train`,
    `ambang_train < offset <= ambang_val` masuk `val`, sisanya `test`.
    """
    if not nodes:
        return SplitReport(
            train_threshold=timeline.start,
            val_threshold=timeline.start,
            counts={name: 0 for name in SPLITS},
            illicit_counts={name: 0 for name in SPLITS},
        )

    offsets = np.array(
        [timeline.offset_seconds(node.first_seen_at) for node in nodes], dtype=float
    )
    train_cut = float(np.percentile(offsets, params.split_train_pct))
    val_cut = float(np.percentile(offsets, params.split_val_pct))

    counts = {name: 0 for name in SPLITS}
    illicit_counts = {name: 0 for name in SPLITS}

    for node, offset in zip(nodes, offsets):
        if offset <= train_cut:
            name = "train"
        elif offset <= val_cut:
            name = "val"
        else:
            name = "test"
        node.split = name
        counts[name] += 1
        if node.is_illicit:
            illicit_counts[name] += 1

    return SplitReport(
        train_threshold=timeline.at_fraction(train_cut / timeline.total_seconds),
        val_threshold=timeline.at_fraction(val_cut / timeline.total_seconds),
        counts=counts,
        illicit_counts=illicit_counts,
    )
