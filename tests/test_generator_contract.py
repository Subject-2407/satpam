"""Tes kontrak generator: bentuk kolom, invariant, dan aturan struktural.

Tes ini menjalankan generator berskala kecil supaya cepat, lalu memeriksa hal
yang tidak bergantung pada skala: bentuk kolom, invariant ground truth,
legalitas edge, konsistensi fitur turunan, dan penjaga G7. Angka target
(jumlah node/edge/operator) hanya berlaku pada skala penuh, jadi diuji terpisah
dan ditandai lambat.

Yang dijaga di sini adalah hal-hal yang kalau rusak akan diam-diam membatalkan
hasil eksperimen, bukan gagal dengan berisik.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from generator import validate
from generator.build import generate
from generator.config import OFFICIAL_SEEDS, GeneratorParams
from generator.schema import (
    ECOSYSTEMS,
    EDGES_COLUMNS,
    NODE_ID_RE,
    NODE_TYPES,
    NODES_COLUMNS,
    REL_TYPES,
    SPLITS,
    is_legal_edge,
)
from generator.timeline import age_days

#: Skala kecil agar tes cepat; cukup untuk seluruh cek bentuk data.
SMALL_NODES = 900


@pytest.fixture(scope="module")
def small_result():
    """Satu kali jalan generator berskala kecil, dipakai bersama seluruh tes."""
    params = dataclasses.replace(
        GeneratorParams(), seed=42, n_nodes_target=SMALL_NODES
    )
    return generate(params)


def test_validator_lolos_tanpa_pelanggaran(small_result):
    """Validator internal tidak boleh menemukan pelanggaran kontrak."""
    assert small_result.validation.ok, small_result.validation.summary()


def test_kolom_persis_kontrak(small_result):
    """Kolom nodes.csv dan edges.csv harus tepat dan berurutan sesuai kontrak."""
    node_row = small_result.population.nodes[0].to_csv_row(small_result.timeline)
    edge_row = small_result.edges[0].to_csv_row(small_result.timeline)
    assert tuple(node_row) == NODES_COLUMNS
    assert tuple(edge_row) == EDGES_COLUMNS


def test_medan_internal_tidak_bocor_ke_csv(small_result):
    """Flag noise dan sisi ekosistem tidak boleh muncul di berkas keluaran.

    `side` khususnya: kalau ia bocor, model bisa membaca sisi ekosistem langsung
    dan seluruh klaim lintas-ekosistem jadi tidak bermakna.
    """
    row = small_result.population.nodes[0].to_csv_row(small_result.timeline)
    for leaked in (
        "hard_negative",
        "hard_positive",
        "side",
        "shared_infra",
        "dormant",
        "rotation_chain",
        "rotation_index",
    ):
        assert leaked not in row
    edge_row = small_result.edges[0].to_csv_row(small_result.timeline)
    assert "rule_tag" not in edge_row


def test_node_id_unik_dan_sesuai_format(small_result):
    """Format `{type}_{5 digit}` dan keunikan global."""
    nodes = small_result.population.nodes
    assert len({node.node_id for node in nodes}) == len(nodes)
    for node in nodes:
        match = NODE_ID_RE.match(node.node_id)
        assert match is not None, node.node_id
        assert match.group("node_type") == node.node_type


def test_invariant_ground_truth(small_result):
    """`gt_operator_id` kosong tepat ketika `gt_illicit=0`."""
    for node in small_result.population.nodes:
        assert node.gt_illicit in (0, 1)
        assert node.gt_ecosystem in ECOSYSTEMS
        assert node.node_type in NODE_TYPES
        assert node.split in SPLITS
        assert bool(node.gt_operator_id) == bool(node.gt_illicit), node.node_id
        assert (node.gt_ecosystem == "none") == (node.gt_illicit == 0), node.node_id
        if node.node_type in ("report", "victim"):
            assert node.gt_illicit == 0, node.node_id


def test_edge_selalu_type_legal(small_result):
    """Setiap triple (src_type, rel_type, dst_type) harus sah.

    Termasuk edge palsu yang disengaja: triple liar akan membuat edge store
    palsu di `HeteroData` PyG di sisi model.
    """
    by_id = {node.node_id: node for node in small_result.population.nodes}
    for edge in small_result.edges:
        assert edge.rel_type in REL_TYPES
        src, dst = by_id[edge.src_id], by_id[edge.dst_id]
        assert is_legal_edge(src.node_type, edge.rel_type, dst.node_type), (
            f"{src.node_type} -{edge.rel_type}-> {dst.node_type}"
        )
        assert edge.src_id != edge.dst_id
        assert 0.0 <= edge.weight <= 1.0
        assert edge.first_seen_at >= max(src.first_seen_at, dst.first_seen_at)


def test_tidak_ada_edge_menggantung_atau_duplikat(small_result):
    ids = {node.node_id for node in small_result.population.nodes}
    keys = set()
    for edge in small_result.edges:
        assert edge.src_id in ids and edge.dst_id in ids
        key = (edge.src_id, edge.dst_id, edge.rel_type)
        assert key not in keys, key
        keys.add(key)


def test_penjaga_g7_tanpa_aliran_dana_lintas_ekosistem(small_result):
    """Penjaga catatan validitas G7 — inti klaim novelty.

    PPATK (Oktober 2023) belum menemukan aliran dana judol langsung ke pinjol,
    jadi generator hanya boleh memodelkan infrastruktur dan korban bersama.
    Edge palsu ikut terikat aturan ini karena ia terbit di berkas yang
    dipublikasikan.
    """
    by_id = {node.node_id: node for node in small_result.population.nodes}
    for edge in small_result.edges:
        if edge.rel_type != "transferred_to":
            continue
        src, dst = by_id[edge.src_id], by_id[edge.dst_id]
        if src.side and dst.side:
            assert src.side == dst.side, (
                f"aliran dana lintas-ekosistem {edge.src_id}({src.side}) -> "
                f"{edge.dst_id}({dst.side}) dari aturan {edge.rule_tag}"
            )


def test_fitur_turunan_cocok_dengan_daftar_edge(small_result):
    """`feat_degree_*` dan `feat_report_count` harus cocok dengan edge FINAL.

    Gagal di sini berarti `features.recompute_derived_features()` dijalankan
    sebelum `noise.apply()`, sehingga `nodes.csv` dan `edges.csv` saling
    bertentangan.
    """
    degree_in: dict[str, int] = {}
    degree_out: dict[str, int] = {}
    report_count: dict[str, int] = {}
    for edge in small_result.edges:
        degree_out[edge.src_id] = degree_out.get(edge.src_id, 0) + 1
        degree_in[edge.dst_id] = degree_in.get(edge.dst_id, 0) + 1
        if edge.rel_type == "mentions":
            report_count[edge.dst_id] = report_count.get(edge.dst_id, 0) + 1

    for node in small_result.population.nodes:
        assert node.feat_degree_in == degree_in.get(node.node_id, 0), node.node_id
        assert node.feat_degree_out == degree_out.get(node.node_id, 0), node.node_id
        assert node.feat_report_count == report_count.get(node.node_id, 0), node.node_id


def test_nol_struktural_fitur(small_result):
    """Fitur yang tidak bermakna untuk sebuah tipe harus bernilai 0."""
    from generator.features import CONTENT_NODE_TYPES
    from generator.schema import FINANCIAL_NODE_TYPES

    for node in small_result.population.nodes:
        assert 0.0 <= node.feat_kw_score <= 1.0
        assert node.feat_is_qris in (0, 1)
        if node.node_type != "ewallet":
            assert node.feat_is_qris == 0, node.node_id
        if node.node_type not in FINANCIAL_NODE_TYPES:
            assert node.feat_txn_count == 0, node.node_id
            assert node.feat_txn_amount_sum == 0, node.node_id
        if node.node_type not in CONTENT_NODE_TYPES:
            assert node.feat_kw_score == 0, node.node_id
        if node.feat_txn_count == 0:
            assert node.feat_txn_amount_sum == 0, node.node_id
        assert node.feat_age_days == age_days(node.first_seen_at, node.last_seen_at)


def test_split_temporal_bukan_acak(small_result):
    """Split harus bisa dihitung ulang dari ambang `first_seen_at`.

    Ini aturan keras yang tidak boleh dilanggar: split acak per-node akan
    gagal di sini.
    """
    report = small_result.split_report
    for node in small_result.population.nodes:
        if node.first_seen_at <= report.train_threshold:
            expected = "train"
        elif node.first_seen_at <= report.val_threshold:
            expected = "val"
        else:
            expected = "test"
        assert node.split == expected, node.node_id


def test_setiap_split_punya_positif(small_result):
    """Tanpa positif di sebuah split, AUPRC di sana tidak bermakna."""
    assert not small_result.split_report.splits_without_positives


def test_generator_deterministik():
    """Seed yang sama harus menghasilkan keluaran yang identik."""
    params = dataclasses.replace(
        GeneratorParams(), seed=42, n_nodes_target=SMALL_NODES
    )
    first, second = generate(params), generate(params)
    assert first.population.nodes == second.population.nodes
    assert first.edges == second.edges

    other = generate(dataclasses.replace(params, seed=43))
    assert first.population.nodes != other.population.nodes


def test_validator_menangkap_pelanggaran_g7(small_result):
    """Validator harus benar-benar menyalak, bukan sekadar ada.

    Sebuah edge `transferred_to` lintas-sisi disuntikkan; validator wajib
    menolaknya.
    """
    by_id = {node.node_id: node for node in small_result.population.nodes}
    judol = next(
        (n for n in small_result.population.nodes if n.side == "judol"), None
    )
    pinjol = next(
        (n for n in small_result.population.nodes if n.side == "pinjol"), None
    )
    if judol is None or pinjol is None:
        pytest.skip("skala kecil ini tidak menghasilkan kedua sisi ekosistem")

    from generator.records import EdgeRecord

    tainted = list(small_result.edges) + [
        EdgeRecord(
            src_id=judol.node_id,
            dst_id=pinjol.node_id,
            rel_type="transferred_to",
            weight=0.9,
            first_seen_at=small_result.timeline.end,
            rule_tag="uji",
        )
    ]
    result = validate.ValidationResult()
    validate._check_g7_sides_in_memory(result, small_result.population, tainted)
    assert not result.ok
    assert any("G7" in message for message in result.errors)


@pytest.mark.slow
@pytest.mark.parametrize("seed", OFFICIAL_SEEDS)
def test_skala_penuh_patuh_target_srs(seed):
    """Skala penuh harus memenuhi angka target untuk tiap seed.

    Lambat (sekitar sepuluh detik per seed). Jalankan dengan:
        pytest tests/test_generator_contract.py -m slow
    """
    result = generate(dataclasses.replace(GeneratorParams(), seed=seed))
    assert result.validation.ok, result.validation.summary()

    population = result.population
    illicit = population.illicit()
    legit = population.legit()

    assert len(population.nodes) == 5_000
    low, high = result.params.n_edges_target
    assert low <= len(result.edges) <= high, len(result.edges)

    ratio_low, ratio_high = result.params.anomaly_ratio
    assert ratio_low <= len(illicit) / len(population.nodes) <= ratio_high

    op_low, op_high = result.params.n_operators
    assert op_low <= result.plan.n_operators <= op_high

    both_low, both_high = result.params.n_both_operators
    assert both_low <= result.plan.ecosystem_counts()["both"] <= both_high

    hn_low, hn_high = result.params.hard_negative_share
    hn = sum(node.hard_negative for node in illicit) / len(illicit)
    assert hn_low <= hn <= hn_high, hn

    hp_low, hp_high = result.params.hard_positive_share
    hp = sum(node.hard_positive for node in legit) / len(legit)
    assert hp_low <= hp <= hp_high, hp


def test_bobot_edge_ditentukan_hanya_oleh_tipe_relasi(small_result):
    """`weight` harus jatuh di rentang tier tipe relasinya, tanpa kecuali.

    Termasuk edge palsu. Kalau edge palsu punya rentang bobot sendiri, ia
    bisa disaring hanya dengan mengambang bobot dan noise edge-salah kehilangan
    maksudnya.
    """
    from generator.weights import tier_bounds

    params = small_result.params
    for edge in small_result.edges:
        low, high = tier_bounds(params, edge.rel_type)
        assert low <= edge.weight <= high, (
            f"{edge.src_id}-{edge.rel_type}->{edge.dst_id} bobot {edge.weight} "
            f"di luar tier {params.weight_tier_of_relation[edge.rel_type]} "
            f"[{low}, {high}]; aturan {edge.rule_tag}"
        )


@pytest.mark.slow
def test_bobot_edge_tidak_membocorkan_kelas():
    """Bobot tidak boleh membedakan kelas di luar apa yang sudah diberi rel_type.

    Semula tiap aturan generatif memilih tier bobotnya sendiri. Karena aturan
    G1-G8 hanya berlaku pada node operator sementara edge latar hanya pada node
    sah, bobot berubah menjadi salinan label: rata-rata bobot per node sendirian
    memisahkan kelas pada AUC 0,795 — lebih bocor daripada fitur mana pun di
    `nodes.csv`.

    Diuji **di dalam** tiap tipe relasi. Perbandingan lintas relasi memang tidak
    netral, tetapi selisihnya sudah sepenuhnya terbaca dari kolom `rel_type`
    yang memang bagian kontrak data.

    Butuh skala penuh: pada 1.200 node hanya ada sekitar 66 node ilegal, sehingga
    edge antar dua node ilegal terlalu sedikit untuk satu tipe relasi pun.
    """
    result = generate(dataclasses.replace(GeneratorParams(), seed=42))
    by_id = {node.node_id: node for node in result.population.nodes}
    per_relation: dict[str, tuple[list[float], list[float]]] = {}
    for edge in result.edges:
        src, dst = by_id[edge.src_id], by_id[edge.dst_id]
        bucket = per_relation.setdefault(edge.rel_type, ([], []))
        if src.gt_illicit and dst.gt_illicit:
            bucket[0].append(edge.weight)
        elif not src.gt_illicit and not dst.gt_illicit:
            bucket[1].append(edge.weight)

    checked = 0
    for rel_type, (illicit, legit) in sorted(per_relation.items()):
        if len(illicit) < 20 or len(legit) < 20:
            continue
        checked += 1
        score = _auc(illicit, legit)
        assert 0.35 <= score <= 0.65, (
            f"bobot pada relasi {rel_type} membedakan kelas: AUC {score:.3f}"
        )
    assert checked >= 3, "terlalu sedikit relasi yang bisa diuji; tes tidak bermakna"


def test_bobot_edge_palsu_tidak_bisa_dibedakan(small_result):
    """Edge palsu tidak boleh dikenali dari bobotnya saja."""
    false_weights = [
        edge.weight for edge in small_result.edges if edge.rule_tag == "false_link"
    ]
    real_weights = [
        edge.weight for edge in small_result.edges if edge.rule_tag != "false_link"
    ]
    if len(false_weights) < 20:
        pytest.skip("terlalu sedikit edge palsu pada skala ini")
    score = _auc(false_weights, real_weights)
    assert 0.35 <= score <= 0.65, (
        f"edge palsu bisa dipisahkan dari bobotnya: AUC {score:.3f}; "
        f"noise edge-salah §6.4 jadi trivial disaring"
    )


@pytest.mark.slow
def test_tidak_ada_fitur_yang_membelah_kelas_sendirian():
    """Tidak boleh ada satu fitur pun yang sendirian hampir menjawab tugasnya.

    Fitur dengan AUC di atas 0,85 berarti ambang sederhana sudah mengalahkan
    segalanya dan perbandingan antar-metode jadi tidak bermakna. Batas 0,85
    dipilih longgar: yang dijaga adalah tidak adanya kebocoran yang merusak,
    bukan angka tertentu. Nilai terukur saat tes ini ditulis: 0,37–0,73.
    """
    subsets = {
        "feat_degree_in": None,
        "feat_degree_out": None,
        "feat_age_days": None,
        "feat_report_count": None,
        "feat_txn_count": ("bank_account", "ewallet"),
        "feat_txn_amount_sum": ("bank_account", "ewallet"),
        "feat_is_qris": ("ewallet",),
        "feat_kw_score": ("domain", "social_account", "apk"),
    }
    result = generate(dataclasses.replace(GeneratorParams(), seed=42))

    for name, types in subsets.items():
        keep = (
            (lambda node: True)
            if types is None
            else (lambda node, types=types: node.node_type in types)
        )
        positive = [
            getattr(node, name) for node in result.population.illicit() if keep(node)
        ]
        negative = [
            getattr(node, name) for node in result.population.legit() if keep(node)
        ]
        score = _auc(positive, negative)
        assert 0.15 <= score <= 0.85, f"{name} membelah kelas sendirian: AUC {score:.3f}"


def _auc(positive: list[float], negative: list[float]) -> float:
    """AUC Mann-Whitney dengan rank rata-rata untuk nilai kembar."""
    values = np.concatenate(
        [np.asarray(positive, dtype=float), np.asarray(negative, dtype=float)]
    )
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    sorted_values = values[order]
    index = 0
    while index < len(sorted_values):
        end = index
        while end + 1 < len(sorted_values) and sorted_values[end + 1] == sorted_values[index]:
            end += 1
        ranks[order[index : end + 1]] = (index + end) / 2 + 1
        index = end + 1
    n_positive = len(positive)
    return (
        ranks[:n_positive].sum() - n_positive * (n_positive + 1) / 2
    ) / (n_positive * len(negative))
