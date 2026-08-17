"""Tes penjaga kontrak `models/loader.py`.

Sasaran tes ini bukan membuktikan loader "berjalan" — itu sudah terlihat dari
skrip eksperimen. Sasarannya adalah menangkap empat kelas kesalahan yang **tidak
memunculkan error apa pun** kalau terjadi, sehingga hanya akan ketahuan setelah
angka hasil terlanjur dipakai:

1.  Kolom `gt_*` atau `rule_*` menyelundup menjadi fitur model. Ini aturan
    keras yang tidak boleh dilanggar.
2.  Urutan node antara `HeteroData` dan bentuk rata bergeser, sehingga baseline
    dan GNN diam-diam dinilai atas node yang berbeda.
3.  `edge_type` ternomori menurut urutan store `HeteroData` (27 nilai) bukan
    menurut `rel_type` (8 nilai), sehingga R-GCN memakai jumlah bobot relasi
    yang salah.
4.  Loss menyentuh node `val`/`test`. Ini aturan keras yang tidak boleh
    dilanggar.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models import loader as loader_module  # noqa: E402
from models.loader import (  # noqa: E402
    ENTITY_TYPES,
    FEATURE_COLUMNS,
    NODE_TYPES,
    REL_TYPES,
    load_seed,
)

DATA_ROOT = REPO_ROOT / "data" / "synthetic"
DEV_SEED = 42
ALL_SEEDS = (42, 43, 44, 45, 46, 47)


def _require_seed(seed: int) -> None:
    if not (DATA_ROOT / f"seed_{seed}").is_dir():
        pytest.skip(f"data seed {seed} belum ada")


@pytest.fixture(scope="module")
def data():
    _require_seed(DEV_SEED)
    return load_seed(DEV_SEED, DATA_ROOT)


# --------------------------------------------------------------------------
# 1. Anti-kebocoran: kolom jawaban dan kolom rule tidak boleh jadi fitur
# --------------------------------------------------------------------------


def test_feature_allowlist_has_no_answer_or_rule_columns():
    """Allowlist fitur tidak boleh memuat kolom jawaban maupun keluaran rule."""
    for name in FEATURE_COLUMNS:
        assert not name.startswith("gt_"), f"{name} adalah kolom jawaban"
        assert not name.startswith("rule_"), f"{name} adalah keluaran rule engine"
        assert name.startswith("feat_"), f"{name} bukan kolom fitur"


def test_feature_matrix_width_matches_allowlist(data):
    assert data.x.size(1) == len(FEATURE_COLUMNS) == 8


def test_features_are_not_derivable_from_ground_truth(data):
    """Tak satu pun kolom fitur boleh berkorelasi sempurna dengan `gt_illicit`.

    Korelasi |r| = 1 berarti kolom itu sebenarnya jawaban yang disalin, bukan
    fitur teramati. Ambang dipasang longgar (0,99) karena korelasi kuat memang
    diharapkan — yang dilarang adalah kolom yang identik dengan jawaban.
    """
    gt = data.y_gt.numpy().astype(float)
    x = data.x.numpy()
    for column, name in enumerate(FEATURE_COLUMNS):
        values = x[:, column]
        if values.std() < 1e-12:
            continue
        correlation = abs(float(np.corrcoef(values, gt)[0, 1]))
        assert correlation < 0.99, f"{name} nyaris identik dengan gt_illicit (r={correlation:.4f})"


def test_rule_score_is_not_inside_features(data):
    """`rule_score` harus terpisah dari `x`, bukan salah satu kolomnya."""
    rule = data.rule_score.numpy()
    x = data.x.numpy()
    for column, name in enumerate(FEATURE_COLUMNS):
        assert not np.allclose(x[:, column], rule), f"{name} sama dengan rule_score"


# --------------------------------------------------------------------------
# 2. Kontrak urutan node: HeteroData dan bentuk rata harus sejajar
# --------------------------------------------------------------------------


def test_type_blocks_are_contiguous_and_ordered(data):
    """Blok tipe harus berurutan sesuai urutan `NODE_TYPES`."""
    node_type = data.node_type.numpy()
    cursor = 0
    for type_id, name in enumerate(NODE_TYPES):
        count = data.hetero[name].num_nodes
        assert data.type_offset[name] == cursor
        assert (node_type[cursor : cursor + count] == type_id).all()
        cursor += count
    assert cursor == data.num_nodes


def test_hetero_features_match_flat_features(data):
    """`x` per tipe di HeteroData harus irisan persis dari `x` bentuk rata."""
    for name in NODE_TYPES:
        start = data.type_offset[name]
        stop = start + data.hetero[name].num_nodes
        assert np.array_equal(data.hetero[name].x.numpy(), data.x[start:stop].numpy())


def test_hetero_edges_map_back_to_same_global_pairs(data):
    """Edge HeteroData (indeks lokal) harus memetakan ke pasangan global yang sama.

    Ini cek paling penting untuk konsistensi kedua representasi: kalau offset
    tipe salah, edge akan menunjuk node lain tanpa error apa pun.
    """
    from_hetero: set[tuple[int, int, str]] = set()
    for src_type, rel, dst_type in data.hetero.edge_types:
        store = data.hetero[(src_type, rel, dst_type)]
        src = store.edge_index[0].numpy() + data.type_offset[src_type]
        dst = store.edge_index[1].numpy() + data.type_offset[dst_type]
        from_hetero.update(zip(src.tolist(), dst.tolist(), [rel] * len(src)))

    # Bentuk rata memuat relasi balik; bandingkan hanya arah maju.
    forward = data.edge_type.numpy() < len(REL_TYPES)
    src = data.edge_index[0].numpy()[forward]
    dst = data.edge_index[1].numpy()[forward]
    rel = data.edge_type.numpy()[forward]
    from_flat = {
        (int(a), int(b), REL_TYPES[int(r)]) for a, b, r in zip(src, dst, rel)
    }
    assert from_hetero == from_flat


def test_node_index_contract_is_bijective(data):
    assert len(data.node_ids) == data.num_nodes
    assert len(data.index_of) == data.num_nodes
    for position, node_id in enumerate(data.node_ids):
        assert data.index_of[node_id] == position


# --------------------------------------------------------------------------
# 3. edge_type dinomori per rel_type, bukan per store HeteroData
# --------------------------------------------------------------------------


def test_edge_type_count_is_eight_not_twenty_seven(data):
    """Delapan relasi dasar memekar jadi 27 triplet, tapi bobot tetap 8/16.

    Kalau `to_homogeneous()` dipakai apa adanya, `edge_type` akan bernilai 0..26
    dan R-GCN mengalokasikan 27 bobot relasi — menyalahi kontrak jumlah relasi.
    """
    assert len(data.hetero.edge_types) == 27
    assert data.num_relations == 2 * len(REL_TYPES) == 16
    assert int(data.edge_type.max()) == 15
    assert set(np.unique(data.edge_type.numpy()).tolist()) == set(range(16))


def test_reverse_edges_mirror_forward_edges(data):
    """Setiap relasi balik `r + 8` harus persis kebalikan relasi maju `r`."""
    src = data.edge_index[0].numpy()
    dst = data.edge_index[1].numpy()
    rel = data.edge_type.numpy()
    for r in range(len(REL_TYPES)):
        forward = rel == r
        backward = rel == r + len(REL_TYPES)
        assert forward.sum() == backward.sum()
        assert np.array_equal(src[forward], dst[backward])
        assert np.array_equal(dst[forward], src[backward])


def test_no_reverse_option_halves_edges(data):
    without = load_seed(DEV_SEED, DATA_ROOT, add_reverse=False)
    assert without.num_relations == len(REL_TYPES) == 8
    assert without.edge_index.size(1) * 2 == data.edge_index.size(1)


# --------------------------------------------------------------------------
# 4. Split temporal dan batas loss
# --------------------------------------------------------------------------


def test_loss_mask_never_touches_val_or_test(data):
    """Loss dilarang dihitung atas node val/test. Ini aturan keras yang tidak
    boleh dilanggar."""
    assert not bool((data.loss_mask & data.val_mask).any())
    assert not bool((data.loss_mask & data.test_mask).any())
    assert bool((data.loss_mask <= data.train_mask).all())


def test_loss_mask_excludes_report_and_victim(data):
    """`report`/`victim` selalu `gt_illicit=0`; melatih di atasnya hanya derau."""
    node_type = data.node_type.numpy()
    entity_ids = {NODE_TYPES.index(name) for name in ENTITY_TYPES}
    for index in np.flatnonzero(data.loss_mask.numpy()):
        assert node_type[index] in entity_ids


def test_splits_partition_all_nodes(data):
    total = data.train_mask.sum() + data.val_mask.sum() + data.test_mask.sum()
    assert int(total) == data.num_nodes


def test_random_split_is_rejected(tmp_path):
    """Loader harus menolak `split` yang diacak, bukan hanya memercayainya.

    Tanpa cek ini, kebocoran berupa random split akan lolos tanpa jejak sama
    sekali karena tidak ada yang error. Ini termasuk aturan keras yang tidak
    boleh dilanggar.
    """
    _require_seed(DEV_SEED)
    source = DATA_ROOT / f"seed_{DEV_SEED}"
    target = tmp_path / f"seed_{DEV_SEED}"
    target.mkdir(parents=True)

    nodes = pd.read_csv(source / "nodes.csv")
    rng = np.random.default_rng(0)
    nodes["split"] = rng.permutation(nodes["split"].to_numpy())
    nodes.to_csv(target / "nodes.csv", index=False)
    for name in ("edges.csv", "weak_labels.csv"):
        (target / name).write_bytes((source / name).read_bytes())

    with pytest.raises(AssertionError, match="temporal"):
        load_seed(DEV_SEED, tmp_path)


def test_temporal_ranges_do_not_overlap_across_splits(data):
    """train harus seluruhnya mendahului val, dan val mendahului test."""
    nodes = pd.read_csv(DATA_ROOT / f"seed_{DEV_SEED}" / "nodes.csv")
    when = pd.to_datetime(nodes["first_seen_at"], format="ISO8601", utc=True)
    bounds = {
        name: (when[nodes["split"] == name].min(), when[nodes["split"] == name].max())
        for name in ("train", "val", "test")
    }
    assert bounds["train"][1] <= bounds["val"][0]
    assert bounds["val"][1] <= bounds["test"][0]


# --------------------------------------------------------------------------
# 5. Praproses fitur
# --------------------------------------------------------------------------


def test_standardization_is_fit_on_train_only(data):
    """Rata-rata fitur pada node train harus ~0; pada test tidak dipaksa 0.

    Kalau statistik dihitung dari seluruh graph, rata-rata pada test juga akan
    mendekati nol — dan itu tanda kebocoran praproses.
    """
    x = data.x.numpy()
    train = data.train_mask.numpy()
    binary = FEATURE_COLUMNS.index("feat_is_qris")
    for column, name in enumerate(FEATURE_COLUMNS):
        if column == binary:
            continue
        # Per tipe node, bukan global: standardisasi dilakukan per tipe.
        for type_id, type_name in enumerate(NODE_TYPES):
            rows = train & (data.node_type.numpy() == type_id)
            if rows.sum() < 2:
                continue
            values = x[rows, column]
            assert abs(float(values.mean())) < 1e-4, (
                f"{name} pada {type_name} tidak terpusat di train"
            )


def test_binary_feature_stays_binary(data):
    column = FEATURE_COLUMNS.index("feat_is_qris")
    values = data.x.numpy()[:, column]
    assert set(np.unique(values).tolist()) <= {0.0, 1.0}


def test_features_are_finite(data):
    assert np.isfinite(data.x.numpy()).all()


def test_log1p_tames_transaction_amount(data):
    """`feat_txn_amount_sum` mencapai 3,48e9 mentah; setelah log1p dan
    standardisasi ia harus berada pada orde yang sama dengan fitur lain."""
    column = FEATURE_COLUMNS.index("feat_txn_amount_sum")
    assert abs(float(data.x.numpy()[:, column].max())) < 50.0


# --------------------------------------------------------------------------
# 6. Label
# --------------------------------------------------------------------------


def test_weak_and_gt_labels_are_distinct(data):
    """Weak label dan ground truth tidak boleh sama — kalau sama, rule engine
    sudah mereproduksi jawaban dan seluruh eksperimen jadi sirkular."""
    assert not np.array_equal(data.y_weak.numpy(), data.y_gt.numpy())


def test_labels_are_binary(data):
    assert set(np.unique(data.y_weak.numpy()).tolist()) <= {0, 1}
    assert set(np.unique(data.y_gt.numpy()).tolist()) <= {0, 1}


def test_rule_score_is_normalized(data):
    values = data.rule_score.numpy()
    assert values.min() >= 0.0
    assert values.max() <= 1.0


def test_report_and_victim_have_no_positive_ground_truth(data):
    """Dasar keputusan mengecualikan kedua tipe dari metrik utama.

    Bila asumsi ini berubah pada seed baru, tes ini gagal dan keputusan cakupan
    evaluasi harus ditinjau ulang, bukan dibiarkan diam-diam salah.
    """
    node_type = data.node_type.numpy()
    gt = data.y_gt.numpy()
    for name in ("report", "victim"):
        rows = node_type == NODE_TYPES.index(name)
        assert gt[rows].sum() == 0, f"{name} kini punya gt_illicit=1"


# --------------------------------------------------------------------------
# 7. Konsistensi lintas seed
# --------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.parametrize("seed", ALL_SEEDS)
def test_every_seed_loads_with_identical_shape(seed):
    _require_seed(seed)
    loaded = load_seed(seed, DATA_ROOT)
    assert loaded.x.size(1) == len(FEATURE_COLUMNS)
    assert loaded.num_relations == 16
    assert len(loaded.hetero.edge_types) == 27
    assert loaded.num_nodes == 5000
    assert bool((loaded.loss_mask <= loaded.train_mask).all())


def test_forbidden_prefixes_are_enforced(monkeypatch):
    """Menambahkan kolom terlarang ke allowlist harus gagal keras.

    Ini menjaga kesalahan paling mungkin di masa depan: seseorang menambah kolom
    ke `FEATURE_COLUMNS` tanpa menyadari isinya jawaban.
    """
    _require_seed(DEV_SEED)
    monkeypatch.setattr(
        loader_module, "FEATURE_COLUMNS", FEATURE_COLUMNS + ("gt_illicit",)
    )
    with pytest.raises((AssertionError, ValueError)):
        load_seed(DEV_SEED, DATA_ROOT)
