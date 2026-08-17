"""Bentuk data node dan edge selama generator berjalan.

Dipisah dari modul yang membangunnya supaya `features.py`, `noise.py`, dan
`validate.py` cukup bergantung pada bentuk datanya, bukan pada modul yang
memproduksinya.

Kedua record punya medan kerja **internal** — flag noise, sisi ekosistem, tag
aturan generatif — yang tidak pernah masuk berkas keluaran. Pengamannya ada di
`to_csv_row()`: fungsi itu membandingkan kunci barisnya dengan kontrak kolom
yang sudah ditetapkan dan gagal keras kalau tidak persis sama. Jadi menambah
medan internal baru tidak mungkin membocorkannya ke CSV secara diam-diam.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from generator.schema import EDGES_COLUMNS, NODES_COLUMNS
from generator.timeline import Timeline


@dataclass
class NodeRecord:
    """Satu node beserta ground truth dan medan kerja internalnya.

    Medan `feat_*` dan `split` sengaja dibiarkan kosong saat node dibuat;
    `features.py` dan `split.py` yang mengisinya.
    """

    # -- identitas ------------------------------------------------------
    node_id: str
    node_type: str
    first_seen_at: datetime
    last_seen_at: datetime

    # -- ground truth, disalin dari rencana operator ---------------------
    gt_illicit: int
    gt_operator_id: str
    gt_ecosystem: str

    # -- medan internal, TIDAK diekspor ke CSV ------------------------
    #: Node ilegal yang jejaknya sengaja ditekan (hard negative).
    hard_negative: bool = False
    #: Node sah yang sengaja dibuat tampak mencurigakan (hard positive).
    hard_positive: bool = False
    #: G7 — sisi ekosistem node operator: `judol` atau `pinjol`. Kosong untuk
    #: node sah. Dipakai penjaga G7: `transferred_to` tidak boleh lintas-sisi.
    side: str = ""
    #: G7 — node infrastruktur yang dipakai bersama oleh kedua sisi operator.
    shared_infra: bool = False
    #: G2 — rekening dormant yang diambil alih operator.
    dormant: bool = False
    #: G4 — id rantai rotasi domain, kosong bila tidak ikut rotasi.
    rotation_chain: str = ""
    #: G4 — posisi dalam rantai rotasi, -1 bila tidak ikut rotasi.
    rotation_index: int = -1

    # -- fitur, diisi features.py -------------------------------------
    feat_degree_in: float = 0.0
    feat_degree_out: float = 0.0
    feat_age_days: float = 0.0
    feat_report_count: float = 0.0
    feat_txn_count: float = 0.0
    feat_txn_amount_sum: float = 0.0
    feat_is_qris: int = 0
    feat_kw_score: float = 0.0

    # -- split, diisi split.py -----------------------------------------
    split: str = ""

    @property
    def is_illicit(self) -> bool:
        return self.gt_illicit == 1

    @property
    def in_rotation_chain(self) -> bool:
        return bool(self.rotation_chain)

    @property
    def apparent_illicit(self) -> bool:
        """Kelas yang *terlihat* dari luar, bukan ground truth-nya.

        Inilah wujud noise yang disengaja: node hard negative benar-benar ilegal tetapi
        tampak bersih, dan node hard positive benar-benar sah tetapi tampak
        mencurigakan. `features.py` memakai properti ini untuk memilih
        distribusi fitur, sehingga kedua kelas sengaja saling tumpang tindih.
        """
        if self.hard_negative:
            return False
        if self.hard_positive:
            return True
        return self.is_illicit

    def to_csv_row(self, timeline: Timeline) -> dict[str, object]:
        """Baris `nodes.csv` — tepat kolom yang sudah ditetapkan, tidak lebih."""
        row: dict[str, object] = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "first_seen_at": timeline.to_iso(self.first_seen_at),
            "last_seen_at": timeline.to_iso(self.last_seen_at),
            "feat_degree_in": self.feat_degree_in,
            "feat_degree_out": self.feat_degree_out,
            "feat_age_days": self.feat_age_days,
            "feat_report_count": self.feat_report_count,
            "feat_txn_count": self.feat_txn_count,
            "feat_txn_amount_sum": self.feat_txn_amount_sum,
            "feat_is_qris": self.feat_is_qris,
            "feat_kw_score": self.feat_kw_score,
            "gt_illicit": self.gt_illicit,
            "gt_operator_id": self.gt_operator_id,
            "gt_ecosystem": self.gt_ecosystem,
            "split": self.split,
        }
        _check_columns(row, NODES_COLUMNS, "nodes.csv")
        return row


@dataclass
class EdgeRecord:
    """Satu edge bukti beserta tag aturan generatif yang menerbitkannya."""

    # -- kolom kontrak ---------------------------------------------------
    src_id: str
    dst_id: str
    rel_type: str
    weight: float
    first_seen_at: datetime

    # -- medan internal, TIDAK diekspor ke CSV ------------------------
    #: Aturan generatif yang menerbitkan edge ini (`G1`..`G8`), atau
    #: `background` untuk edge latar node sah, atau `false_link` untuk edge
    #: palsu.
    #: Dipakai untuk diagnostik build dan untuk penjaga G7 di `validate.py`.
    rule_tag: str = ""

    @property
    def key(self) -> tuple[str, str, str]:
        """Identitas edge untuk pencegahan duplikat."""
        return (self.src_id, self.dst_id, self.rel_type)

    def to_csv_row(self, timeline: Timeline) -> dict[str, object]:
        """Baris `edges.csv` — tepat kolom yang sudah ditetapkan, tidak lebih."""
        row: dict[str, object] = {
            "src_id": self.src_id,
            "dst_id": self.dst_id,
            "rel_type": self.rel_type,
            "weight": self.weight,
            "first_seen_at": timeline.to_iso(self.first_seen_at),
        }
        _check_columns(row, EDGES_COLUMNS, "edges.csv")
        return row


def _check_columns(
    row: dict[str, object],
    expected: tuple[str, ...],
    label: str,
) -> None:
    """Gagal keras bila kunci baris tidak persis sama dengan kontrak kolom yang diharapkan."""
    if tuple(row) != expected:
        raise AssertionError(
            f"baris {label} tidak cocok dengan kontrak §5.3.\n"
            f"  diharapkan: {expected}\n"
            f"  didapat   : {tuple(row)}"
        )
