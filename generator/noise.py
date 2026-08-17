"""LANGKAH 5 — noise wajib pada daftar edge.

Dua dari empat jenis noise wajib dikerjakan di sini:

| Jenis | Target |
|---|---|
| Edge hilang (missing evidence) | 10% edge dihapus acak |
| Edge salah (false link) | 2% edge palsu ditambahkan |

Dua jenis lainnya — hard negative dan hard positive — sudah ditandai
`population.py` dan diwujudkan `features.py` serta `evidence.py`.

Tiga hal yang perlu diketahui pembaca lain:

1. **Penghapusan benar-benar acak seragam**, tanpa pengecualian. Node yang
   kebetulan kehilangan seluruh edge-nya dibiarkan begitu dan jumlahnya
   dilaporkan, bukan dilindungi. Melindunginya berarti memilih edge mana yang
   boleh hilang, dan itu bukan lagi "dihapus acak".

2. **Edge palsu tetap type-legal** menurut tabel legalitas edge di `schema.py`.
   Edge palsu yang melanggar kontrak tipe akan trivial disaring dan sekaligus
   merusak `HeteroData` di sisi model.

3. **Edge palsu tetap patuh penjaga G7.** Edge palsu memang salah, tetapi ia
   terbit di `edges.csv` yang dipublikasikan. Kalau ia boleh mengalirkan dana
   dari sisi judol ke sisi pinjol, dataset ini memuat justru hal yang belum
   dikonfirmasi PPATK (Oktober 2023), dan siapa pun bisa membantah klaim
   lintas-ekosistem SATPAM dengan satu query. Penjaganya mutlak.

Setelah modul ini, `features.recompute_derived_features()` **wajib** dipanggil:
`feat_degree_*` dan `feat_report_count` harus mengacu pada daftar edge final.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from generator.config import GeneratorParams
from generator.records import EdgeRecord, NodeRecord
from generator.schema import legal_triples
from generator.timeline import Timeline
from generator.weights import sample_weight

#: Batas percobaan mencari pasangan node untuk satu edge palsu, agar tidak
#: berputar tanpa akhir bila kombinasi tipenya kebetulan sudah penuh.
MAX_FALSE_EDGE_ATTEMPTS: int = 40


@dataclass(frozen=True)
class NoiseReport:
    """Ringkasan noise yang benar-benar diterapkan, untuk manifest dan build."""

    edges_before: int
    edges_dropped: int
    false_edges_added: int
    edges_after: int
    isolated_nodes_after: int
    false_edge_attempts_failed: int

    @property
    def drop_share_actual(self) -> float:
        if self.edges_before == 0:
            return 0.0
        return self.edges_dropped / self.edges_before

    @property
    def false_share_actual(self) -> float:
        """Porsi edge palsu terhadap daftar edge FINAL."""
        if self.edges_after == 0:
            return 0.0
        return self.false_edges_added / self.edges_after

    def as_dict(self) -> dict[str, float | int]:
        return {
            "edges_before_noise": self.edges_before,
            "edges_dropped": self.edges_dropped,
            "drop_share_actual": round(self.drop_share_actual, 6),
            "false_edges_added": self.false_edges_added,
            "false_share_actual": round(self.false_share_actual, 6),
            "false_edge_attempts_failed": self.false_edge_attempts_failed,
            "edges_after_noise": self.edges_after,
            "isolated_nodes_after_noise": self.isolated_nodes_after,
        }


def apply(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    nodes: list[NodeRecord],
    edges: list[EdgeRecord],
) -> tuple[list[EdgeRecord], NoiseReport]:
    """Terapkan noise wajib dan kembalikan daftar edge final beserta laporannya.

    Args:
        nodes: Seluruh node; dipakai untuk memilih ujung edge palsu dan untuk
            menghitung node yang menjadi terisolasi.
        edges: Daftar edge hasil `evidence.sow_all()`. Tidak diubah di tempat;
            daftar baru yang dikembalikan.
    """
    before = len(edges)
    kept = _drop_edges(params, rng, edges)
    false_edges, failed = _add_false_edges(params, rng, timeline, nodes, kept)

    final = kept + false_edges
    touched: set[str] = set()
    for edge in final:
        touched.add(edge.src_id)
        touched.add(edge.dst_id)

    report = NoiseReport(
        edges_before=before,
        edges_dropped=before - len(kept),
        false_edges_added=len(false_edges),
        edges_after=len(final),
        isolated_nodes_after=sum(1 for node in nodes if node.node_id not in touched),
        false_edge_attempts_failed=failed,
    )
    return final, report


def _drop_edges(
    params: GeneratorParams,
    rng: np.random.Generator,
    edges: list[EdgeRecord],
) -> list[EdgeRecord]:
    """Buang `edge_drop_share` edge secara acak seragam (missing evidence).

    Inilah yang membuat noise benar-benar mengurangi sinyal: karena
    `feat_degree_*` dihitung setelah langkah ini, bukti yang hilang benar-benar
    hilang dari mata model, bukan cuma hilang dari berkas.
    """
    if not edges or params.edge_drop_share <= 0:
        return list(edges)

    n_drop = int(round(len(edges) * params.edge_drop_share))
    if n_drop <= 0:
        return list(edges)
    n_drop = min(n_drop, len(edges))

    dropped = set(
        int(index)
        for index in rng.choice(len(edges), size=n_drop, replace=False)
    )
    return [edge for index, edge in enumerate(edges) if index not in dropped]


def _add_false_edges(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    nodes: list[NodeRecord],
    kept: list[EdgeRecord],
) -> tuple[list[EdgeRecord], int]:
    """Tambahkan `false_edge_share` edge palsu yang tetap type-legal.

    Bentuk triple `(src_type, rel_type, dst_type)` diambil dari daftar triple
    sah (`generator.schema.legal_triples()`), lalu kedua ujungnya dipilih acak
    dari tipe yang bersangkutan.

    **Bobotnya diambil dari distribusi yang sama dengan edge asli** bertipe relasi
    yang sama. Semula edge palsu diberi tier bobot rendah dengan alasan "bukti
    yang salah semestinya lemah", dan itu keliru: kalau edge palsu selalu berbobot
    rendah, ia bisa disaring hanya dengan mengambang bobot, dan seluruh maksud
    noise edge-salah hilang. Edge salah yang berguna adalah edge yang tidak
    bisa dibedakan dari yang benar — kesalahan penautan di lapangan justru sering
    datang dengan bukti yang tampak meyakinkan.

    Kandidat ditolak bila: ujungnya sama, triple-nya sudah ada, atau ia berupa
    aliran dana lintas-ekosistem (penjaga G7). Jumlah kandidat yang gagal
    dilaporkan agar tidak ada kekurangan yang lolos tanpa terlihat.
    """
    if not kept or params.false_edge_share <= 0:
        return [], 0

    n_false = int(round(len(kept) * params.false_edge_share))
    if n_false <= 0:
        return [], 0

    by_type: dict[str, list[NodeRecord]] = {}
    for node in nodes:
        by_type.setdefault(node.node_type, []).append(node)

    triples = [
        triple
        for triple in legal_triples()
        if by_type.get(triple[0]) and by_type.get(triple[2])
    ]
    if not triples:
        return [], n_false

    seen = {(edge.src_id, edge.dst_id, edge.rel_type) for edge in kept}
    false_edges: list[EdgeRecord] = []
    failed = 0

    while len(false_edges) < n_false:
        edge = _draw_false_edge(params, rng, timeline, by_type, triples, seen)
        if edge is None:
            failed = n_false - len(false_edges)
            break
        seen.add((edge.src_id, edge.dst_id, edge.rel_type))
        false_edges.append(edge)

    return false_edges, failed


def _draw_false_edge(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    by_type: dict[str, list[NodeRecord]],
    triples: list[tuple[str, str, str]],
    seen: set[tuple[str, str, str]],
) -> EdgeRecord | None:
    """Coba temukan satu edge palsu yang sah. None bila gagal berkali-kali."""
    for _ in range(MAX_FALSE_EDGE_ATTEMPTS):
        src_type, rel_type, dst_type = triples[int(rng.integers(0, len(triples)))]
        src_pool = by_type[src_type]
        dst_pool = by_type[dst_type]
        src = src_pool[int(rng.integers(0, len(src_pool)))]
        dst = dst_pool[int(rng.integers(0, len(dst_pool)))]

        if src.node_id == dst.node_id:
            continue
        if (src.node_id, dst.node_id, rel_type) in seen:
            continue
        # Penjaga G7 berlaku juga bagi edge palsu — lihat docstring modul.
        if (
            rel_type == "transferred_to"
            and src.side
            and dst.side
            and src.side != dst.side
        ):
            continue

        earliest = max(src.first_seen_at, dst.first_seen_at)
        latest = min(src.last_seen_at, dst.last_seen_at)
        first_seen = (
            earliest
            if latest <= earliest
            else timeline.sample_between(rng, earliest, latest)
        )
        return EdgeRecord(
            src_id=src.node_id,
            dst_id=dst.node_id,
            rel_type=rel_type,
            weight=sample_weight(params, rng, rel_type),
            first_seen_at=first_seen,
            rule_tag="false_link",
        )
    return None
