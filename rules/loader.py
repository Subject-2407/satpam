"""Pembaca `nodes.csv` dan `edges.csv` untuk rule engine.

Modul ini adalah satu-satunya tempat rule engine menyentuh berkas, dan di sini
pula pembatasan terpentingnya dipasang: **daftar kolom yang dibaca berupa
allowlist, bukan blocklist.** Kolom jawaban tidak disebut namanya di mana pun
dalam paket `rules/`, jadi ia tidak pernah masuk ke objek yang dilihat modul
skoring. Melarang lewat allowlist lebih kuat daripada melarang lewat blocklist:
kolom baru apa pun yang muncul di berkas otomatis tidak terbaca, bukan otomatis
terbaca.

Nama kolom di bawah disalin secara mandiri, bukan diimpor dari `generator/`.
Duplikasi ini disengaja — lihat docstring paket.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

#: Kolom `nodes.csv` yang boleh dibaca rule engine.
#: Sengaja hanya kolom teramati: identitas, waktu, dan delapan kolom `feat_*`.
OBSERVABLE_NODE_COLUMNS: tuple[str, ...] = (
    "node_id",
    "node_type",
    "first_seen_at",
    "last_seen_at",
    "feat_degree_in",
    "feat_degree_out",
    "feat_age_days",
    "feat_report_count",
    "feat_txn_count",
    "feat_txn_amount_sum",
    "feat_is_qris",
    "feat_kw_score",
)

#: Kolom `edges.csv`. Seluruhnya teramati.
EDGE_COLUMNS: tuple[str, ...] = (
    "src_id",
    "dst_id",
    "rel_type",
    "weight",
    "first_seen_at",
)

#: Delapan tipe node, disalin mandiri.
NODE_TYPES: tuple[str, ...] = (
    "domain",
    "phone",
    "bank_account",
    "ewallet",
    "apk",
    "social_account",
    "report",
    "victim",
)

#: Delapan tipe relation, disalin mandiri.
REL_TYPES: tuple[str, ...] = (
    "promotes",
    "contacts",
    "uses_account",
    "transferred_to",
    "mentions",
    "reported",
    "linked_to_apk",
    "redirects_to",
)

#: Tipe node yang membawa rekening/dompet, dipakai beberapa aturan.
ACCOUNT_TYPES: frozenset[str] = frozenset({"bank_account", "ewallet"})


@dataclass(frozen=True)
class RuleNode:
    """Node sebagaimana terlihat rule engine — hanya kolom teramati."""

    node_id: str
    node_type: str
    first_seen_at: datetime
    last_seen_at: datetime
    feat_degree_in: float
    feat_degree_out: float
    feat_age_days: float
    feat_report_count: float
    feat_txn_count: float
    feat_txn_amount_sum: float
    feat_is_qris: int
    feat_kw_score: float

    @property
    def mean_ticket(self) -> float:
        """Nominal rata-rata per transaksi; 0 bila tidak ada transaksi.

        Dipakai aturan R-G1 untuk menangkap "nominal kecil" pada aturan
        generatif G1.
        """
        if self.feat_txn_count <= 0:
            return 0.0
        return self.feat_txn_amount_sum / self.feat_txn_count

    @property
    def degree_total(self) -> float:
        return self.feat_degree_in + self.feat_degree_out


@dataclass(frozen=True)
class RuleEdge:
    """Edge sebagaimana terlihat rule engine."""

    src_id: str
    dst_id: str
    rel_type: str
    weight: float
    first_seen_at: datetime


def load_nodes(path: Path) -> list[RuleNode]:
    """Baca `nodes.csv`, ambil hanya kolom pada `OBSERVABLE_NODE_COLUMNS`."""
    nodes: list[RuleNode] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, OBSERVABLE_NODE_COLUMNS, path.name)
        for row in reader:
            nodes.append(
                RuleNode(
                    node_id=row["node_id"],
                    node_type=row["node_type"],
                    first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
                    last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
                    feat_degree_in=float(row["feat_degree_in"]),
                    feat_degree_out=float(row["feat_degree_out"]),
                    feat_age_days=float(row["feat_age_days"]),
                    feat_report_count=float(row["feat_report_count"]),
                    feat_txn_count=float(row["feat_txn_count"]),
                    feat_txn_amount_sum=float(row["feat_txn_amount_sum"]),
                    feat_is_qris=int(float(row["feat_is_qris"])),
                    feat_kw_score=float(row["feat_kw_score"]),
                )
            )
    return nodes


def load_edges(path: Path) -> list[RuleEdge]:
    """Baca `edges.csv`."""
    edges: list[RuleEdge] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, EDGE_COLUMNS, path.name)
        for row in reader:
            edges.append(
                RuleEdge(
                    src_id=row["src_id"],
                    dst_id=row["dst_id"],
                    rel_type=row["rel_type"],
                    weight=float(row["weight"]),
                    first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
                )
            )
    return edges


def _require_columns(
    found: list[str] | None,
    needed: tuple[str, ...],
    label: str,
) -> None:
    """Gagal keras bila kolom yang dibutuhkan tidak ada di berkas."""
    present = set(found or ())
    missing = [column for column in needed if column not in present]
    if missing:
        raise ValueError(
            f"{label} kekurangan kolom yang dibutuhkan rule engine: {missing}"
        )
