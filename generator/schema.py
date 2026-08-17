"""Kontrak data SATPAM — satu-satunya sumber kebenaran soal skema.

Kontrak ini BEKU: tiga orang bekerja paralel dengan skema ini sebagai
satu-satunya titik temu. Jangan ubah tanpa persetujuan eksplisit manusia.

Isinya:
- tipe node (8)
- tipe relation (8) beserta pasangan src -> dst yang sah
- kolom tiap berkas keluaran
- nilai `split`

Modul ini murni deklaratif: tidak ada logika skoring, tidak ada keputusan
label. Ia tidak boleh mengimpor apa pun dari `rules/` — ini aturan keras yang
tidak boleh dilanggar.
"""

from __future__ import annotations

import re
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Tipe node
# ---------------------------------------------------------------------------

#: Delapan tipe node.
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

#: Tipe node yang boleh menjadi anggota jaringan operator (`gt_illicit=1`).
#:
#: `report` dan `victim` sengaja tidak masuk: keduanya bukan bagian dari
#: jaringan pelaku, jadi selalu `gt_illicit=0` dengan `gt_operator_id` kosong
#: — konsisten dengan aturan yang mewajibkan `gt_operator_id` kosong bila
#: `gt_illicit=0`. Keterkaitan korban lintas-ekosistem (aturan G8) tersimpan
#: sebagai edge, bukan sebagai kolom pada node korban.
ILLICIT_CAPABLE_NODE_TYPES: frozenset[str] = frozenset(
    {"domain", "phone", "bank_account", "ewallet", "apk", "social_account"}
)

#: Tipe node yang boleh punya `feat_txn_count` / `feat_txn_amount_sum` != 0.
#:
#: Batasannya diturunkan dari relation `transferred_to`: tepat tiga tipe
#: inilah yang sah menjadi *src* sebuah transfer, jadi tepat tiga tipe ini
#: yang ikut dalam subgraph transaksi. Tipe lain wajib bernilai 0 sesuai
#: kontrak "0 untuk node non-finansial".
FINANCIAL_NODE_TYPES: frozenset[str] = frozenset({"bank_account", "ewallet", "victim"})

# ---------------------------------------------------------------------------
# Tipe relation dan pasangan tipe yang sah
# ---------------------------------------------------------------------------


class RelSpec(NamedTuple):
    """Pasangan tipe node yang sah untuk satu relation."""

    src_types: frozenset[str]
    dst_types: frozenset[str]


#: Delapan tipe relation.
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

#: Tabel legalitas edge: pasangan kolom "src -> dst" yang sah untuk tiap
#: relation.
#:
#: Dipakai dua arah: `evidence.py` hanya boleh menerbitkan edge yang lolos
#: tabel ini, dan `validate.py` menolak berkas keluaran yang melanggarnya.
#: Perhatian khusus bagi sisi model: `HeteroData` PyG di-key oleh triple
#: (src_type, rel_type, dst_type), jadi triple liar akan membuat edge store
#: palsu di sisi model.
EDGE_LEGALITY: dict[str, RelSpec] = {
    "promotes": RelSpec(
        frozenset({"social_account"}),
        frozenset({"domain", "apk"}),
    ),
    "contacts": RelSpec(
        frozenset({"domain", "apk", "social_account"}),
        frozenset({"phone"}),
    ),
    "uses_account": RelSpec(
        frozenset({"domain", "apk", "phone"}),
        frozenset({"bank_account", "ewallet"}),
    ),
    "transferred_to": RelSpec(
        frozenset({"victim", "bank_account", "ewallet"}),
        frozenset({"bank_account", "ewallet"}),
    ),
    "mentions": RelSpec(
        frozenset({"report"}),
        frozenset(
            {"domain", "phone", "bank_account", "ewallet", "apk", "social_account"}
        ),
    ),
    "reported": RelSpec(
        frozenset({"victim"}),
        frozenset({"report"}),
    ),
    "linked_to_apk": RelSpec(
        frozenset({"domain", "social_account"}),
        frozenset({"apk"}),
    ),
    "redirects_to": RelSpec(
        frozenset({"domain"}),
        frozenset({"domain"}),
    ),
}

# ---------------------------------------------------------------------------
# Kolom berkas keluaran (URUTAN MENGIKAT)
# ---------------------------------------------------------------------------

#: Kolom `nodes.csv`, urutan ini mengikat.
NODES_COLUMNS: tuple[str, ...] = (
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
    "gt_illicit",
    "gt_operator_id",
    "gt_ecosystem",
    "split",
)

#: Kolom `edges.csv`, urutan ini mengikat.
EDGES_COLUMNS: tuple[str, ...] = (
    "src_id",
    "dst_id",
    "rel_type",
    "weight",
    "first_seen_at",
)

#: Kolom `weak_labels.csv` (keluaran rule engine di `rules/`, bukan generator).
#: Dideklarasikan di sini karena kontrak kolomnya satu skema dengan yang di
#: atas.
WEAK_LABELS_COLUMNS: tuple[str, ...] = (
    "node_id",
    "rule_score",
    "rule_level",
    "triggered_rules",
)

#: Kolom `human_annotations.csv` (hasil anotasi manual tim).
HUMAN_ANNOTATIONS_COLUMNS: tuple[str, ...] = (
    "node_id",
    "annotator_id",
    "label",
    "confidence",
    "annotated_at",
)

#: Kolom `feat_*` pada `nodes.csv` — subset dari NODES_COLUMNS.
FEATURE_COLUMNS: tuple[str, ...] = tuple(
    col for col in NODES_COLUMNS if col.startswith("feat_")
)

#: Kolom ground truth — HANYA boleh dibaca skrip evaluasi, tidak pernah oleh
#: apa pun yang menghasilkan skor atau prediksi.
GT_COLUMNS: tuple[str, ...] = tuple(
    col for col in NODES_COLUMNS if col.startswith("gt_")
)

# ---------------------------------------------------------------------------
# Domain nilai kolom kategorikal
# ---------------------------------------------------------------------------

#: Nilai sah `gt_ecosystem`.
ECOSYSTEMS: tuple[str, ...] = ("judol", "pinjol", "both", "none")

#: Nilai `gt_ecosystem` untuk node yang benar-benar bagian jaringan ilegal.
ILLICIT_ECOSYSTEMS: tuple[str, ...] = ("judol", "pinjol", "both")

#: Nilai sah `split`.
SPLITS: tuple[str, ...] = ("train", "val", "test")

#: Nilai sah `rule_level` pada `weak_labels.csv`.
RULE_LEVELS: tuple[str, ...] = ("low", "medium", "high", "critical")

# ---------------------------------------------------------------------------
# Format node_id
# ---------------------------------------------------------------------------

#: Format `node_id`: `{node_type}_{nomor 5 digit}`, mis. `domain_00042`.
#: Nomor dihitung per-tipe, jadi `domain_00042` dan `phone_00042` bisa
#: berdampingan dan tetap unik global karena prefiks tipenya berbeda.
NODE_ID_RE: re.Pattern[str] = re.compile(
    r"^(?P<node_type>" + "|".join(sorted(NODE_TYPES, key=len, reverse=True)) + r")"
    r"_(?P<number>\d{5})$"
)

#: Lebar nomor pada `node_id`.
NODE_ID_DIGITS: int = 5

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def is_legal_edge(src_type: str, rel_type: str, dst_type: str) -> bool:
    """True bila triple (src_type, rel_type, dst_type) sah menurut tabel legalitas edge."""
    spec = EDGE_LEGALITY.get(rel_type)
    if spec is None:
        return False
    return src_type in spec.src_types and dst_type in spec.dst_types


def legal_triples() -> tuple[tuple[str, str, str], ...]:
    """Semua triple (src_type, rel_type, dst_type) yang sah menurut kontrak relasi.

    Dipakai `noise.py` untuk memilih bentuk edge palsu yang tetap type-legal,
    dan dipakai `validate.py` sebagai daftar pembanding.
    """
    triples: list[tuple[str, str, str]] = []
    for rel_type in REL_TYPES:
        spec = EDGE_LEGALITY[rel_type]
        for src_type in sorted(spec.src_types):
            for dst_type in sorted(spec.dst_types):
                triples.append((src_type, rel_type, dst_type))
    return tuple(triples)


def node_type_of(node_id: str) -> str:
    """Ambil `node_type` dari sebuah `node_id`.

    Raises:
        ValueError: bila `node_id` tidak mengikuti format kontraknya.
    """
    match = NODE_ID_RE.match(node_id)
    if match is None:
        raise ValueError(f"node_id tidak sesuai format kontrak: {node_id!r}")
    return match.group("node_type")


def _self_check() -> None:
    """Jaga agar transkripsi kontrak tetap konsisten satu sama lain."""
    assert len(NODE_TYPES) == 8, "SRS §5.1 mendefinisikan tepat 8 tipe node"
    assert len(REL_TYPES) == 8, "SRS §5.2 mendefinisikan tepat 8 tipe relation"
    assert len(set(NODE_TYPES)) == len(NODE_TYPES), "tipe node duplikat"
    assert len(set(REL_TYPES)) == len(REL_TYPES), "tipe relation duplikat"
    assert set(EDGE_LEGALITY) == set(REL_TYPES), "tabel legalitas tidak lengkap"

    known = set(NODE_TYPES)
    for rel_type, spec in EDGE_LEGALITY.items():
        assert spec.src_types <= known, f"src tak dikenal pada relation {rel_type}"
        assert spec.dst_types <= known, f"dst tak dikenal pada relation {rel_type}"
        assert spec.src_types, f"relation {rel_type} tanpa src"
        assert spec.dst_types, f"relation {rel_type} tanpa dst"

    assert ILLICIT_CAPABLE_NODE_TYPES <= known
    assert FINANCIAL_NODE_TYPES <= known
    assert set(GT_COLUMNS) == {"gt_illicit", "gt_operator_id", "gt_ecosystem"}
    assert len(FEATURE_COLUMNS) == 8, "SRS §5.3 mendefinisikan 8 kolom feat_*"

    # Setiap tipe node harus bisa di-parse balik dari node_id-nya.
    for node_type in NODE_TYPES:
        sample = f"{node_type}_{1:0{NODE_ID_DIGITS}d}"
        assert node_type_of(sample) == node_type, f"parse gagal untuk {sample}"


_self_check()
