"""Pemuat data sintetik SATPAM ke `HeteroData` PyTorch Geometric.

Modul ini adalah satu-satunya pintu masuk data untuk seluruh Bagian B (model dan
eksperimen). Semua baseline dan R-GCN membaca lewat sini supaya indeks node,
praproses fitur, dan definisi mask persis sama — kalau tidak, perbandingan
antar-model bisa diam-diam salah sejajar dan hasilnya tidak berarti.

Tiga hal yang dijaga keras di sini, masing-masing berhubungan dengan aturan
yang membatalkan validitas penelitian kalau dilanggar:

1.  **Kolom `gt_*` tidak pernah menjadi fitur.** `FEATURE_COLUMNS` berupa
    allowlist, dan `_verify_no_leakage` gagal keras bila ada kolom di luar
    daftar itu masuk `x`. Kolom baru apa pun yang muncul di `nodes.csv` otomatis
    *tidak* terbaca sebagai fitur, bukan otomatis terbaca.

2.  **`rule_score` juga bukan fitur.** Keluaran rule engine hanya boleh menjadi
    target pelatihan, tidak boleh menjadi masukan. Kalau ia masuk `x`, R-GCN
    sebagian hanya membaca ulang skor rule dan perbandingan terhadap baseline
    B1 kehilangan artinya.

3.  **Statistik standardisasi dihitung hanya dari `split == "train"`.** Memakai
    seluruh graph untuk menghitung mean/std adalah kebocoran halus yang mudah
    terlewat karena tidak pernah memunculkan error.

Protokol label mengikuti keputusan tim (varian puritan yang dipilih): loss dihitung
**hanya** atas `weak_labels.csv`, dan `gt_illicit` tidak pernah menyentuh
pelatihan maupun model selection. `gt_illicit` hanya dibaca skrip evaluasi.
Karena itu `y_weak` dan `y_gt` disimpan sebagai atribut terpisah dengan nama
yang sengaja dibuat tidak mungkin tertukar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import HeteroData

# --------------------------------------------------------------------------
# Kontrak skema — disalin manual dari definisi skema data, bukan diimpor dari
# `generator/` atau `rules/`. Duplikasi ini disengaja: modul ini harus tetap
# jalan tanpa bergantung pada kode milik orang lain.
# --------------------------------------------------------------------------

#: Delapan tipe node. **Urutan ini adalah kontrak.** Indeks global
#: node disusun menurut urutan tipe di sini, jadi mengubahnya akan mengacaukan
#: seluruh hasil yang sudah tersimpan.
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

#: Delapan tipe relasi. Urutan menentukan `edge_type` 0..7.
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

#: Tipe node yang menjadi target klasifikasi. `report` dan `victim` dikecualikan
#: karena `gt_illicit = 0` untuk 100% node kedua tipe itu — 1.200 node atau 24%
#: graph yang tidak mungkin salah. Keduanya tetap ada di graph sebagai konteks
#: message passing, tetapi tidak masuk loss maupun metrik utama.
ENTITY_TYPES: tuple[str, ...] = (
    "domain",
    "phone",
    "bank_account",
    "ewallet",
    "apk",
    "social_account",
)

#: Delapan kolom fitur. Allowlist — lihat butir 1 di docstring modul.
FEATURE_COLUMNS: tuple[str, ...] = (
    "feat_degree_in",
    "feat_degree_out",
    "feat_age_days",
    "feat_report_count",
    "feat_txn_count",
    "feat_txn_amount_sum",
    "feat_is_qris",
    "feat_kw_score",
)

#: Kolom dengan ekor sangat panjang; `feat_txn_amount_sum` mencapai 3,48e9
#: sementara tujuh kolom lain berorde satuan sampai ratusan. Tanpa `log1p`
#: kolom ini menenggelamkan sisanya begitu distandardisasi.
LOG1P_COLUMNS: frozenset[str] = frozenset({"feat_txn_count", "feat_txn_amount_sum"})

#: Kolom biner, dibiarkan 0/1 tanpa standardisasi supaya tetap terbaca sebagai
#: penanda dan tidak berubah menjadi nilai pecahan yang tak bermakna.
BINARY_COLUMNS: frozenset[str] = frozenset({"feat_is_qris"})

#: Tingkat `rule_level` yang dianggap positif untuk label lemah.
#:
#: Ambang ini dipilih **a-priori** dari semantik rule engine — `high` dan
#: `critical` adalah tingkat yang memang dirancang masuk antrean triage analis
#: — dan sengaja *tidak* dipilih dengan mencari F1 terbaik terhadap
#: `gt_illicit`. Menyetel ambang dengan melihat `gt` akan menyelundupkan ground
#: truth ke dalam pelatihan sebagai hyperparameter.
WEAK_POSITIVE_LEVELS: tuple[str, ...] = ("high", "critical")

#: Urutan tingkat rule, dipakai memvalidasi nilai yang terbaca.
RULE_LEVELS: tuple[str, ...] = ("low", "medium", "high", "critical")

#: Prefiks kolom yang dilarang mutlak menjadi fitur.
FORBIDDEN_FEATURE_PREFIXES: tuple[str, ...] = ("gt_", "rule_", "split", "triggered_")

DEFAULT_DATA_ROOT = Path("data/synthetic")


# --------------------------------------------------------------------------
# Wadah keluaran
# --------------------------------------------------------------------------


@dataclass
class SatpamData:
    """Satu seed data SATPAM dalam dua representasi yang saling konsisten.

    Kedua representasi dibangun dari **satu urutan node yang sama**, jadi
    indeks baris `x` dan indeks node di `hetero` selalu dapat
    dipertukarkan lewat `type_offset`.

    Representasi kanonik (`hetero`)
        `HeteroData` dengan 27 store `(src_type, rel, dst_type)` — pemetaan
        setia dari skema data. Terarah, **tanpa** reverse edge. Dipakai
        GNNExplainer dan integrasi dashboard.

    Representasi rata (`x`, `edge_index`, `edge_type`, ...)
        Bentuk yang dimakan `RGCNConv`. `edge_type` bernilai 0..7 menurut
        `REL_TYPES`, ditambah 8..15 untuk relasi balik bila `add_reverse=True`.
        Ini yang dipakai R-GCN dan seluruh baseline.

    Kenapa `hetero` tidak memuat reverse edge padahal bentuk rata memuatnya:
    `hetero` berperan sebagai cermin skema apa adanya, sementara reverse edge
    adalah keputusan pemodelan. Menaruh keduanya di satu tempat akan membuat
    "apa yang ada di data" dan "apa yang dipakai model" tidak lagi bisa
    dibedakan.
    """

    seed: int

    # Representasi kanonik
    hetero: HeteroData

    # Representasi rata untuk RGCNConv
    x: torch.Tensor  # [N, 8] float32, sudah dipraproses
    node_type: torch.Tensor  # [N] long, indeks ke NODE_TYPES
    edge_index: torch.Tensor  # [2, E] long, indeks global
    edge_type: torch.Tensor  # [E] long, 0..7 (atau 0..15 dengan reverse)
    edge_weight: torch.Tensor  # [E] float32, kolom `weight` dari edges.csv

    # Label pelatihan — HANYA dari rule engine
    y_weak: torch.Tensor  # [N] long 0/1, dari rule_level
    rule_score: torch.Tensor  # [N] float32 0..1, rule_score/100

    # Label evaluasi — HANYA untuk skrip evaluasi, dilarang masuk loss
    y_gt: torch.Tensor  # [N] long 0/1, dari gt_illicit

    # Mask split (mencakup seluruh 8 tipe)
    train_mask: torch.Tensor
    val_mask: torch.Tensor
    test_mask: torch.Tensor

    # Mask cakupan tipe
    entity_mask: torch.Tensor  # 6 tipe entitas, cakupan metrik utama

    # Satu-satunya mask yang boleh dipakai menghitung loss
    loss_mask: torch.Tensor  # train_mask & entity_mask

    # Kontrak indeks
    node_ids: list[str]
    index_of: dict[str, int]
    type_offset: dict[str, int]  # indeks global awal tiap blok tipe

    # Metadata
    node_type_names: tuple[str, ...]
    rel_type_names: tuple[str, ...]  # panjang 8 atau 16 bila add_reverse
    feature_names: tuple[str, ...]
    add_reverse: bool
    manifest: dict

    # Diagnostik, ikut ditulis ke hasil eksperimen supaya bisa diaudit
    stats: dict

    @property
    def num_nodes(self) -> int:
        return self.x.size(0)

    @property
    def num_relations(self) -> int:
        """Jumlah bobot relasi yang perlu dialokasikan `RGCNConv`."""
        return len(self.rel_type_names)

    def eval_mask(self, split: str, scope: str = "entity") -> torch.Tensor:
        """Mask untuk menghitung metrik.

        Args:
            split: `train`, `val`, atau `test`.
            scope: `entity` untuk 6 tipe utama (tabel utama), `all` untuk
                seluruh 8 tipe (kolom pendamping).
        """
        base = {
            "train": self.train_mask,
            "val": self.val_mask,
            "test": self.test_mask,
        }[split]
        if scope == "entity":
            return base & self.entity_mask
        if scope == "all":
            return base
        raise ValueError(f"scope tidak dikenal: {scope!r} (pilih 'entity' atau 'all')")


# --------------------------------------------------------------------------
# Pemuat utama
# --------------------------------------------------------------------------


def load_seed(
    seed: int,
    data_root: Path | str = DEFAULT_DATA_ROOT,
    *,
    add_reverse: bool = True,
    weak_positive_levels: tuple[str, ...] = WEAK_POSITIVE_LEVELS,
    verify_split: bool = True,
) -> SatpamData:
    """Baca satu seed dan bangun kedua representasi graph.

    Args:
        seed: nomor seed, mis. 42.
        data_root: direktori induk berisi `seed_{seed}/`.
        add_reverse: tambahkan relasi balik sebagai tipe relasi terpisah pada
            bentuk rata. Wajib untuk hasil yang bermakna — tanpa ini
            `social_account` (kelompok positif terbesar) hanya bisa menerima
            pesan dari `report --mentions-->`, karena `promotes`, `contacts`,
            dan `linked_to_apk` seluruhnya berarah keluar. Disediakan sebagai
            flag agar bisa diablasi.
        weak_positive_levels: tingkat `rule_level` yang dihitung positif.
        verify_split: cek ulang bahwa kolom `split` benar-benar hasil persentil
            temporal 70/85 atas `first_seen_at`, bukan acak.

    Returns:
        `SatpamData` siap pakai untuk R-GCN maupun baseline.
    """
    seed_dir = Path(data_root) / f"seed_{seed}"
    if not seed_dir.is_dir():
        raise FileNotFoundError(f"direktori seed tidak ada: {seed_dir}")

    nodes = _read_nodes(seed_dir / "nodes.csv")
    edges = _read_edges(seed_dir / "edges.csv")
    weak = _read_weak_labels(seed_dir / "weak_labels.csv")
    manifest = _read_manifest(seed_dir / "manifest.json")

    # Urutan node adalah kontrak: menurut blok tipe (urutan NODE_TYPES), lalu
    # `node_id` di dalam tipe. Satu urutan ini melayani HeteroData, bentuk rata,
    # MLP, XGBoost, dan join ke weak_labels sekaligus.
    nodes = _order_nodes(nodes)
    node_ids: list[str] = nodes["node_id"].tolist()
    index_of = {node_id: i for i, node_id in enumerate(node_ids)}
    type_offset, type_count = _type_blocks(nodes)

    if verify_split:
        _verify_temporal_split(nodes)

    features, feature_stats = _build_features(nodes)
    _verify_no_leakage(nodes, features)

    labels = _build_labels(nodes, weak, weak_positive_levels)
    masks = _build_masks(nodes)

    hetero = _build_hetero(
        nodes=nodes,
        edges=edges,
        features=features,
        labels=labels,
        masks=masks,
        index_of=index_of,
        type_offset=type_offset,
        type_count=type_count,
    )
    flat = _build_flat(edges=edges, index_of=index_of, add_reverse=add_reverse)

    rel_names = (
        REL_TYPES + tuple(f"rev_{name}" for name in REL_TYPES)
        if add_reverse
        else REL_TYPES
    )

    stats = {
        "seed": seed,
        "num_nodes": len(nodes),
        "num_edges_directed": len(edges),
        "num_edges_flat": int(flat["edge_index"].size(1)),
        "num_relations": len(rel_names),
        "num_canonical_edge_types": len(hetero.edge_types),
        "weak_positive_levels": list(weak_positive_levels),
        "weak_label_coverage": labels["weak_coverage"],
        "weak_positive_rate_loss_nodes": float(
            labels["y_weak"][masks["loss_mask"]].float().mean()
        ),
        "gt_positive_rate_test_entity": float(
            labels["y_gt"][masks["test_mask"] & masks["entity_mask"]].float().mean()
        ),
        "loss_nodes": int(masks["loss_mask"].sum()),
        "feature_stats": feature_stats,
    }

    return SatpamData(
        seed=seed,
        hetero=hetero,
        x=features,
        node_type=_node_type_ids(nodes),
        edge_index=flat["edge_index"],
        edge_type=flat["edge_type"],
        edge_weight=flat["edge_weight"],
        y_weak=labels["y_weak"],
        rule_score=labels["rule_score"],
        y_gt=labels["y_gt"],
        train_mask=masks["train_mask"],
        val_mask=masks["val_mask"],
        test_mask=masks["test_mask"],
        entity_mask=masks["entity_mask"],
        loss_mask=masks["loss_mask"],
        node_ids=node_ids,
        index_of=index_of,
        type_offset=type_offset,
        node_type_names=NODE_TYPES,
        rel_type_names=rel_names,
        feature_names=FEATURE_COLUMNS,
        add_reverse=add_reverse,
        manifest=manifest,
        stats=stats,
    )


# --------------------------------------------------------------------------
# Pembacaan berkas
# --------------------------------------------------------------------------


def _read_nodes(path: Path) -> pd.DataFrame:
    needed = (
        "node_id",
        "node_type",
        "first_seen_at",
        "split",
        "gt_illicit",
        *FEATURE_COLUMNS,
    )
    frame = pd.read_csv(path)
    _require_columns(frame, needed, path.name)

    unknown = set(frame["node_type"]) - set(NODE_TYPES)
    if unknown:
        raise ValueError(f"{path.name} memuat node_type di luar SRS §5.1: {sorted(unknown)}")
    if frame["node_id"].duplicated().any():
        dupes = frame.loc[frame["node_id"].duplicated(), "node_id"].head(5).tolist()
        raise ValueError(f"{path.name} memuat node_id ganda, contoh: {dupes}")
    unknown_split = set(frame["split"]) - {"train", "val", "test"}
    if unknown_split:
        raise ValueError(f"{path.name} memuat split tak dikenal: {sorted(unknown_split)}")
    return frame


def _read_edges(path: Path) -> pd.DataFrame:
    needed = ("src_id", "dst_id", "rel_type", "weight")
    frame = pd.read_csv(path)
    _require_columns(frame, needed, path.name)
    unknown = set(frame["rel_type"]) - set(REL_TYPES)
    if unknown:
        raise ValueError(f"{path.name} memuat rel_type di luar SRS §5.2: {sorted(unknown)}")
    return frame


def _read_weak_labels(path: Path) -> pd.DataFrame:
    """Baca keluaran rule engine.

    `triggered_rules` sengaja tidak dibaca. Ia berguna untuk analisis kualitatif,
    tetapi di modul ini tidak ada tempat yang boleh memakainya, dan kolom yang
    tidak dibaca tidak bisa bocor menjadi fitur.
    """
    needed = ("node_id", "rule_score", "rule_level")
    frame = pd.read_csv(path, usecols=list(needed))
    _require_columns(frame, needed, path.name)
    unknown = set(frame["rule_level"]) - set(RULE_LEVELS)
    if unknown:
        raise ValueError(f"{path.name} memuat rule_level tak dikenal: {sorted(unknown)}")
    return frame


def _read_manifest(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_columns(frame: pd.DataFrame, needed: tuple[str, ...], label: str) -> None:
    missing = [column for column in needed if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} kekurangan kolom: {missing}")


# --------------------------------------------------------------------------
# Urutan node dan blok tipe
# --------------------------------------------------------------------------


def _order_nodes(nodes: pd.DataFrame) -> pd.DataFrame:
    """Urutkan menurut blok tipe lalu `node_id`, sesuai kontrak indeks."""
    rank = {name: i for i, name in enumerate(NODE_TYPES)}
    ordered = nodes.assign(_type_rank=nodes["node_type"].map(rank))
    ordered = ordered.sort_values(["_type_rank", "node_id"], kind="stable")
    return ordered.drop(columns="_type_rank").reset_index(drop=True)


def _type_blocks(nodes: pd.DataFrame) -> tuple[dict[str, int], dict[str, int]]:
    """Hitung indeks global awal dan jumlah node tiap tipe.

    Karena `_order_nodes` sudah menyusun node menurut blok tipe, setiap tipe
    menempati rentang indeks yang berurutan. Ini yang membuat indeks lokal
    HeteroData dan indeks global bentuk rata hanya berbeda satu offset.
    """
    offset: dict[str, int] = {}
    count: dict[str, int] = {}
    cursor = 0
    for name in NODE_TYPES:
        n = int((nodes["node_type"] == name).sum())
        offset[name] = cursor
        count[name] = n
        cursor += n

    # Pastikan blok benar-benar berurutan, bukan sekadar berjumlah benar.
    positions = np.arange(len(nodes))
    for name in NODE_TYPES:
        if count[name] == 0:
            continue
        rows = positions[(nodes["node_type"] == name).to_numpy()]
        expected = np.arange(offset[name], offset[name] + count[name])
        if not np.array_equal(rows, expected):
            raise AssertionError(f"blok tipe {name!r} tidak berurutan setelah pengurutan")
    return offset, count


def _node_type_ids(nodes: pd.DataFrame) -> torch.Tensor:
    rank = {name: i for i, name in enumerate(NODE_TYPES)}
    return torch.tensor(
        nodes["node_type"].map(rank).to_numpy(dtype=np.int64), dtype=torch.long
    )


# --------------------------------------------------------------------------
# Verifikasi split temporal
# --------------------------------------------------------------------------


def _verify_temporal_split(nodes: pd.DataFrame, count_tolerance: float = 0.01) -> None:
    """Pastikan kolom `split` benar-benar temporal, bukan acak.

    Split ini mengikat pada persentil temporal 70/85. Generator sudah
    menuliskannya, tetapi memercayai kolom itu tanpa cek berarti split acak bisa
    lolos tanpa jejak sama sekali.

    Cek dilakukan atas **urutan waktu antar-split**, bukan dengan membangun
    ulang peringkat lalu membandingkan node per node. Alasannya: beberapa node
    bisa berbagi `first_seen_at` yang sama tepat di batas persentil, dan node
    seri seperti itu boleh jatuh ke sisi mana pun tergantung tie-break yang
    dipakai generator. Perbandingan per-node akan memberi alarm palsu di situ,
    sementara cek batas di bawah tetap menangkap split acak — split acak
    membuat rentang waktu ketiga bagian saling tumpang tindih total.
    """
    when = pd.to_datetime(nodes["first_seen_at"], format="ISO8601", utc=True)
    n = len(nodes)

    expected = {"train": 0.70, "val": 0.15, "test": 0.15}
    bounds: dict[str, tuple[pd.Timestamp, pd.Timestamp]] = {}
    for name, share in expected.items():
        rows = (nodes["split"] == name).to_numpy()
        actual = rows.sum() / n
        if abs(actual - share) > count_tolerance:
            raise AssertionError(
                f"porsi split {name!r} = {actual:.4f}, seharusnya {share:.2f} "
                f"(SRS §5.4 persentil 70/85)"
            )
        bounds[name] = (when[rows].min(), when[rows].max())

    for earlier, later in (("train", "val"), ("val", "test")):
        if bounds[earlier][1] > bounds[later][0]:
            raise AssertionError(
                f"rentang waktu {earlier!r} melewati awal {later!r} "
                f"({bounds[earlier][1]} > {bounds[later][0]}). "
                f"Split tampak tidak temporal — split acak dilarang (SRS §8.4)."
            )


# --------------------------------------------------------------------------
# Fitur
# --------------------------------------------------------------------------


def _build_features(nodes: pd.DataFrame) -> tuple[torch.Tensor, dict]:
    """Susun matriks fitur `[N, 8]`: `log1p` untuk kolom berekor panjang, lalu
    standardisasi per tipe node dengan statistik dari `split == "train"` saja.

    Standardisasi dilakukan **per tipe** karena skala tiap kolom berbeda jauh
    antar tipe — `feat_degree_in` rata-rata 9,8 pada `ewallet` tetapi 0 pada
    `victim`. Satu mean/std global akan membuat perbedaan antar-node di dalam
    satu tipe hampir hilang.

    Statistik diambil hanya dari `train` karena memakai seluruh graph berarti
    informasi distribusi val/test ikut masuk ke praproses — kebocoran yang
    tidak pernah memunculkan error, jadi harus dicegah di sini.

    Semua 8 kolom dipertahankan untuk setiap tipe, termasuk kolom yang mati
    (selalu nol) pada tipe tertentu. Memangkas kolom mati per tipe akan membuat
    bentuk matriks berbeda antar seed, karena kolom yang mati di seed 42 bisa
    hidup di seed 44.
    """
    raw = nodes.loc[:, list(FEATURE_COLUMNS)].to_numpy(dtype=np.float64)

    if not np.isfinite(raw).all():
        bad = [FEATURE_COLUMNS[j] for j in range(raw.shape[1]) if not np.isfinite(raw[:, j]).all()]
        raise ValueError(f"kolom fitur memuat NaN/inf: {bad}")

    for j, name in enumerate(FEATURE_COLUMNS):
        if name in LOG1P_COLUMNS:
            if (raw[:, j] < 0).any():
                raise ValueError(f"{name} memuat nilai negatif, log1p tidak berlaku")
            raw[:, j] = np.log1p(raw[:, j])

    is_train = (nodes["split"] == "train").to_numpy()
    node_type = nodes["node_type"].to_numpy()
    out = np.zeros_like(raw)
    dead: dict[str, list[str]] = {}

    for type_name in NODE_TYPES:
        rows = node_type == type_name
        if not rows.any():
            continue
        fit_rows = rows & is_train
        if not fit_rows.any():
            # Tidak seharusnya terjadi pada data ini, tapi jangan sampai diam
            # lalu menghasilkan angka yang tampak wajar.
            raise ValueError(f"tipe {type_name!r} tidak punya node train untuk standardisasi")

        for j, name in enumerate(FEATURE_COLUMNS):
            column = raw[rows, j]
            if name in BINARY_COLUMNS:
                out[rows, j] = column
                continue
            mean = raw[fit_rows, j].mean()
            std = raw[fit_rows, j].std()
            if std < 1e-8:
                # Kolom konstan pada tipe ini (umumnya selalu nol). Dipusatkan
                # saja; membagi dengan std akan meledak.
                out[rows, j] = column - mean
                dead.setdefault(type_name, []).append(name)
            else:
                out[rows, j] = (column - mean) / std

    stats = {
        "log1p_columns": sorted(LOG1P_COLUMNS),
        "standardized_per_node_type": True,
        "fit_on_split": "train",
        "constant_columns_per_type": dead,
    }
    return torch.as_tensor(out, dtype=torch.float32), stats


def _verify_no_leakage(nodes: pd.DataFrame, features: torch.Tensor) -> None:
    """Gagal keras bila ada kolom terlarang bisa masuk fitur.

    Cek ini menargetkan kesalahan yang paling mungkin terjadi saat kode diubah
    nanti: seseorang menambahkan kolom ke `FEATURE_COLUMNS` tanpa menyadari
    kolom itu memuat jawaban atau skor rule.
    """
    for name in FEATURE_COLUMNS:
        for prefix in FORBIDDEN_FEATURE_PREFIXES:
            if name.startswith(prefix):
                raise AssertionError(
                    f"kolom {name!r} dilarang menjadi fitur (prefiks {prefix!r})"
                )
    if features.size(1) != len(FEATURE_COLUMNS):
        raise AssertionError(
            f"lebar matriks fitur {features.size(1)} tidak sama dengan "
            f"{len(FEATURE_COLUMNS)} kolom pada allowlist"
        )
    if features.size(0) != len(nodes):
        raise AssertionError("jumlah baris fitur tidak sama dengan jumlah node")


# --------------------------------------------------------------------------
# Label dan mask
# --------------------------------------------------------------------------


def _build_labels(
    nodes: pd.DataFrame,
    weak: pd.DataFrame,
    weak_positive_levels: tuple[str, ...],
) -> dict:
    """Susun label lemah (pelatihan) dan ground truth (evaluasi) terpisah."""
    unknown = set(weak_positive_levels) - set(RULE_LEVELS)
    if unknown:
        raise ValueError(f"weak_positive_levels tak dikenal: {sorted(unknown)}")

    merged = nodes.loc[:, ["node_id"]].merge(weak, on="node_id", how="left")
    if len(merged) != len(nodes):
        raise AssertionError("join weak_labels menghasilkan jumlah baris berbeda")

    missing = int(merged["rule_level"].isna().sum())
    level = merged["rule_level"].fillna("low")
    score = merged["rule_score"].fillna(0.0).to_numpy(dtype=np.float64)
    if (score < 0).any() or (score > 100).any():
        raise ValueError("rule_score di luar rentang 0..100")

    y_weak = level.isin(weak_positive_levels).to_numpy().astype(np.int64)
    gt = nodes["gt_illicit"].to_numpy()
    if not np.isin(gt, [0, 1]).all():
        raise ValueError("gt_illicit memuat nilai selain 0/1")

    return {
        "y_weak": torch.as_tensor(y_weak, dtype=torch.long),
        "rule_score": torch.as_tensor(score / 100.0, dtype=torch.float32),
        "y_gt": torch.as_tensor(gt.astype(np.int64), dtype=torch.long),
        "weak_coverage": 1.0 - missing / len(nodes),
    }


def _build_masks(nodes: pd.DataFrame) -> dict:
    split = nodes["split"].to_numpy()
    node_type = nodes["node_type"].to_numpy()

    train_mask = torch.as_tensor(split == "train", dtype=torch.bool)
    val_mask = torch.as_tensor(split == "val", dtype=torch.bool)
    test_mask = torch.as_tensor(split == "test", dtype=torch.bool)
    entity_mask = torch.as_tensor(np.isin(node_type, ENTITY_TYPES), dtype=torch.bool)

    overlap = (train_mask & val_mask) | (train_mask & test_mask) | (val_mask & test_mask)
    if bool(overlap.any()):
        raise AssertionError("mask split saling tumpang tindih")
    if not bool((train_mask | val_mask | test_mask).all()):
        raise AssertionError("ada node tanpa split")

    return {
        "train_mask": train_mask,
        "val_mask": val_mask,
        "test_mask": test_mask,
        "entity_mask": entity_mask,
        # Loss hanya atas node train DAN tipe entitas. `report`/`victim`
        # memiliki weak label (bahkan sebagian `critical`) padahal `gt_illicit`
        # selalu 0 — melatih di atasnya hanya mengajarkan derau untuk tipe yang
        # tidak pernah dinilai.
        "loss_mask": train_mask & entity_mask,
    }


# --------------------------------------------------------------------------
# Representasi kanonik: HeteroData
# --------------------------------------------------------------------------


def _build_hetero(
    *,
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    features: torch.Tensor,
    labels: dict,
    masks: dict,
    index_of: dict[str, int],
    type_offset: dict[str, int],
    type_count: dict[str, int],
) -> HeteroData:
    """Bangun `HeteroData` dengan store `(src_type, rel, dst_type)`.

    Delapan `rel_type` memekar menjadi 27 triplet kanonik pada data
    nyata, karena `HeteroData` mengunci relasi pada pasangan tipe — misalnya
    `transferred_to` muncul sebagai enam triplet berbeda. Semuanya
    dipertahankan di sini; pengerucutan kembali ke delapan bobot relasi
    dilakukan pada bentuk rata (lihat `_build_flat`), karena R-GCN memakai
    bobot terpisah per *relation*, bukan per triplet.
    """
    data = HeteroData()

    for type_name in NODE_TYPES:
        start = type_offset[type_name]
        stop = start + type_count[type_name]
        store = data[type_name]
        store.x = features[start:stop]
        store.num_nodes = type_count[type_name]
        store.y_weak = labels["y_weak"][start:stop]
        store.rule_score = labels["rule_score"][start:stop]
        store.y_gt = labels["y_gt"][start:stop]
        store.train_mask = masks["train_mask"][start:stop]
        store.val_mask = masks["val_mask"][start:stop]
        store.test_mask = masks["test_mask"][start:stop]
        store.loss_mask = masks["loss_mask"][start:stop]
        store.node_ids = nodes["node_id"].to_numpy()[start:stop].tolist()

    node_type_of = dict(zip(nodes["node_id"], nodes["node_type"]))
    src_type = edges["src_id"].map(node_type_of)
    dst_type = edges["dst_id"].map(node_type_of)
    if src_type.isna().any() or dst_type.isna().any():
        raise ValueError("edges.csv merujuk node_id yang tidak ada di nodes.csv")

    src_global = edges["src_id"].map(index_of).to_numpy(dtype=np.int64)
    dst_global = edges["dst_id"].map(index_of).to_numpy(dtype=np.int64)
    offsets = np.array([type_offset[t] for t in NODE_TYPES], dtype=np.int64)
    type_rank = {name: i for i, name in enumerate(NODE_TYPES)}
    src_local = src_global - offsets[src_type.map(type_rank).to_numpy(dtype=np.int64)]
    dst_local = dst_global - offsets[dst_type.map(type_rank).to_numpy(dtype=np.int64)]
    weight = edges["weight"].to_numpy(dtype=np.float32)

    # Dikelompokkan lewat tiga kolom terpisah, bukan satu kolom berisi tuple:
    # groupby atas kolom bertipe tuple perilakunya berbeda antar versi pandas.
    frame = pd.DataFrame(
        {
            "src_type": src_type.to_numpy(),
            "rel_type": edges["rel_type"].to_numpy(),
            "dst_type": dst_type.to_numpy(),
            "src_local": src_local,
            "dst_local": dst_local,
            "weight": weight,
        }
    )
    for key, group in frame.groupby(["src_type", "rel_type", "dst_type"], sort=True):
        store = data[tuple(key)]
        store.edge_index = torch.as_tensor(
            np.stack(
                [
                    group["src_local"].to_numpy(dtype=np.int64),
                    group["dst_local"].to_numpy(dtype=np.int64),
                ]
            ),
            dtype=torch.long,
        )
        # `torch.tensor` (bukan `as_tensor`) agar selalu menyalin: array hasil
        # `to_numpy()` pandas bisa berupa view read-only, dan torch tidak
        # mendukung tensor non-writable.
        store.edge_weight = torch.tensor(
            group["weight"].to_numpy(dtype=np.float32), dtype=torch.float32
        )

    return data


# --------------------------------------------------------------------------
# Representasi rata untuk RGCNConv
# --------------------------------------------------------------------------


def _build_flat(*, edges: pd.DataFrame, index_of: dict[str, int], add_reverse: bool) -> dict:
    """Bangun `(edge_index, edge_type, edge_weight)` dengan indeks global.

    `edge_type` dipetakan dari `rel_type` menurut urutan `REL_TYPES`, jadi
    bernilai 0..7 — bukan menurut urutan store `HeteroData`. Ini sengaja tidak
    memakai `HeteroData.to_homogeneous()`, karena metode itu menomori
    `edge_type` menurut urutan 27 store dan akan menghasilkan 27 bobot relasi,
    bukan delapan seperti definisi skema relasi aslinya.

    Relasi balik ditambahkan sebagai tipe relasi terpisah (8..15), mengikuti
    R-GCN asli Schlichtkrull dkk. yang memodelkan relasi invers secara eksplisit
    ketimbang membuat graph tak-berarah. Self-loop tidak ditambahkan karena
    `RGCNConv(root_weight=True)` sudah menyediakan bobot akar.
    """
    rel_id = {name: i for i, name in enumerate(REL_TYPES)}
    # Cek dangling dilakukan sebelum konversi ke int64: setelah dikonversi, node
    # yang tidak ditemukan sudah berubah menjadi error pandas yang tidak jelas.
    src_mapped = edges["src_id"].map(index_of)
    dst_mapped = edges["dst_id"].map(index_of)
    if src_mapped.isna().any() or dst_mapped.isna().any():
        missing = pd.concat(
            [
                edges.loc[src_mapped.isna(), "src_id"],
                edges.loc[dst_mapped.isna(), "dst_id"],
            ]
        ).unique()[:5]
        raise ValueError(
            f"edges.csv merujuk node_id yang tidak ada di nodes.csv, contoh: {list(missing)}"
        )
    src = src_mapped.to_numpy(dtype=np.int64)
    dst = dst_mapped.to_numpy(dtype=np.int64)
    rel = edges["rel_type"].map(rel_id).to_numpy(dtype=np.int64)
    weight = edges["weight"].to_numpy(dtype=np.float32)

    if add_reverse:
        edge_index = np.concatenate(
            [np.stack([src, dst]), np.stack([dst, src])], axis=1
        )
        edge_type = np.concatenate([rel, rel + len(REL_TYPES)])
        edge_weight = np.concatenate([weight, weight])
    else:
        edge_index = np.stack([src, dst])
        edge_type = rel
        edge_weight = weight

    expected = 2 * len(REL_TYPES) if add_reverse else len(REL_TYPES)
    if edge_type.min() < 0 or edge_type.max() >= expected:
        raise AssertionError(
            f"edge_type di luar rentang [0,{expected}): "
            f"min={edge_type.min()} max={edge_type.max()}"
        )

    # `torch.tensor` agar selalu menyalin: tanpa `add_reverse`, array di atas
    # masih berupa view read-only dari pandas dan torch menolaknya.
    return {
        "edge_index": torch.tensor(edge_index, dtype=torch.long),
        "edge_type": torch.tensor(edge_type, dtype=torch.long),
        "edge_weight": torch.tensor(edge_weight, dtype=torch.float32),
    }


# --------------------------------------------------------------------------
# Pemeriksaan cepat dari command line
# --------------------------------------------------------------------------


def _summary(data: SatpamData) -> str:
    lines = [
        f"seed {data.seed}: {data.num_nodes} node, "
        f"{data.stats['num_edges_directed']} edge terarah "
        f"-> {data.stats['num_edges_flat']} edge bentuk rata, "
        f"{data.num_relations} relasi",
        f"  triplet kanonik HeteroData : {data.stats['num_canonical_edge_types']}",
        f"  node untuk loss            : {data.stats['loss_nodes']} "
        f"(train & 6 tipe entitas)",
        f"  positif weak di node loss  : {data.stats['weak_positive_rate_loss_nodes']:.4f}",
        f"  positif gt di test entitas : {data.stats['gt_positive_rate_test_entity']:.4f}",
        f"  cakupan weak label         : {data.stats['weak_label_coverage']:.4f}",
    ]
    for split in ("train", "val", "test"):
        entity = int(data.eval_mask(split, "entity").sum())
        every = int(data.eval_mask(split, "all").sum())
        lines.append(f"  {split:5} : entitas={entity:5}  semua={every:5}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Periksa pemuatan satu seed atau lebih.")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42])
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--no-reverse", action="store_true")
    args = parser.parse_args()

    for seed_value in args.seeds:
        loaded = load_seed(
            seed_value, args.data_root, add_reverse=not args.no_reverse
        )
        print(_summary(loaded))
        print()
