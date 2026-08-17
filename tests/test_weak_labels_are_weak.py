"""Tes penjaga: `weak_labels.csv` harus benar-benar LEMAH.

Ini penjaga premis penelitian, bukan penjaga kebenaran kode. `weak_labels.csv`
dipakai untuk pelatihan. Ini aturan keras yang tidak boleh dilanggar. Kalau ia
terlalu dekat dengan ground truth, maka:

- weak supervision berhenti menjadi lemah dan menjadi supervisi hampir sempurna,
- propagasi feedback tidak punya apa pun untuk diperbaiki,
- kurva "perbaikan per jumlah anotasi" (ablasi A5) mendatar bukan karena
  metodenya, melainkan karena labelnya sudah nyaris benar sejak awal.

Batas 0,85 AUPRC disepakati sebagai titik berhenti: di atas itu label bukan
lemah lagi dan keputusan harus diambil manusia.

Tes ini berada di **luar** paket `rules/` karena ia perlu membaca kolom ground
truth, yang tidak boleh disentuh rule engine.
"""

from __future__ import annotations

import csv
import dataclasses

import numpy as np
import pytest

from generator.build import generate, write_output
from generator.config import GeneratorParams
from rules.build import build_weak_labels, write_weak_labels
from rules.scoring import ALL_TIERS, SRS_TIER_ONLY

#: Batas AUPRC yang disepakati sebagai titik berhenti.
AUPRC_CEILING = 0.85

#: Skala kecil agar tes cepat.
SMALL_NODES = 1_200


def average_precision(y_true: list[int], y_score: list[float]) -> float:
    """AUPRC. Nilai skor kembar diproses sebagai satu ambang, seperti sklearn.

    Penanganan nilai kembar penting di sini: skor rule aditif hanya punya
    belasan nilai berbeda, jadi memperlakukan tiap baris sebagai ambang
    tersendiri akan melebih-lebihkan hasilnya.
    """
    truth = np.asarray(y_true, dtype=float)
    score = np.asarray(y_score, dtype=float)
    order = np.argsort(-score, kind="mergesort")
    truth, score = truth[order], score[order]

    positives = truth.sum()
    if positives == 0:
        return float("nan")

    result = 0.0
    previous_recall = 0.0
    true_positives = 0.0
    index = 0
    while index < len(truth):
        end = index
        while end + 1 < len(score) and score[end + 1] == score[index]:
            end += 1
        true_positives += truth[index : end + 1].sum()
        precision = true_positives / (end + 1)
        recall = true_positives / positives
        result += (recall - previous_recall) * precision
        previous_recall = recall
        index = end + 1
    return result


def _score_seed(directory, n_nodes: int):
    """Bangun satu seed, tulis berkasnya, lalu jalankan rule engine di atasnya."""
    params = dataclasses.replace(GeneratorParams(), seed=42, n_nodes_target=n_nodes)
    result = generate(params)
    assert result.validation.ok, result.validation.summary()
    output_dir = write_output(result, directory)

    _, assessments, _, matches = build_weak_labels(output_dir)
    write_weak_labels(output_dir, assessments)

    with (output_dir / "weak_labels.csv").open(encoding="utf-8", newline="") as handle:
        weak = {row["node_id"]: row for row in csv.DictReader(handle)}

    nodes = {node.node_id: node for node in result.population.nodes}
    return result, nodes, weak, assessments, matches


@pytest.fixture(scope="module")
def scored(tmp_path_factory):
    """Skala kecil dan cepat — untuk cek bentuk keluaran saja.

    Angka AUPRC pada skala ini **tidak** dipakai menilai apa pun: ambang aturan
    dikalibrasi terhadap persentil sebaran teramati, dan pada 1.200 node
    sampelnya terlalu tipis sehingga rule engine bahkan jatuh di bawah laju
    dasar. Penilaian kekuatan label dilakukan pada skala penuh di `scored_full`.
    """
    return _score_seed(tmp_path_factory.mktemp("weak_small"), SMALL_NODES)


@pytest.fixture(scope="module")
def scored_full(tmp_path_factory):
    """Skala penuh 5.000 node — satu-satunya skala yang menilai kekuatan label."""
    return _score_seed(tmp_path_factory.mktemp("weak_full"), 5_000)


def test_weak_labels_cover_every_node(scored):
    """Setiap node harus punya baris; loader orang B tidak boleh kehilangan node."""
    result, nodes, weak, _, _ = scored
    assert set(weak) == set(nodes)


def test_weak_labels_columns_match_contract(scored):
    """Kolom `weak_labels.csv` harus tepat sesuai kontrak skema."""
    from rules.build import WEAK_LABELS_COLUMNS

    _, _, weak, _, _ = scored
    first = next(iter(weak.values()))
    assert tuple(first) == WEAK_LABELS_COLUMNS


def test_rule_level_domain_valid(scored):
    """`rule_level` hanya boleh salah satu dari empat nilai yang ditentukan."""
    _, _, weak, _, _ = scored
    assert {row["rule_level"] for row in weak.values()} <= {
        "low",
        "medium",
        "high",
        "critical",
    }
    for row in weak.values():
        score = float(row["rule_score"])
        assert 0.0 <= score <= 100.0


@pytest.mark.slow
def test_weak_labels_stay_weak(scored_full):
    """AUPRC rule_score terhadap ground truth harus di bawah batas 0,85.

    Di atas batas ini `weak_labels.csv` bukan label lemah lagi, dan seluruh
    premis weak supervision beserta ablasi feedback runtuh.

    Diuji pada skala penuh: ambang aturan dikalibrasi terhadap persentil sebaran
    teramati, dan kalibrasi itu butuh cukup data untuk bermakna.
    """
    _, nodes, weak, _, _ = scored_full
    ids = sorted(weak)
    truth = [nodes[node_id].gt_illicit for node_id in ids]
    score = [float(weak[node_id]["rule_score"]) for node_id in ids]

    auprc = average_precision(truth, score)
    baseline = sum(truth) / len(truth)

    assert auprc < AUPRC_CEILING, (
        f"weak_labels.csv terlalu dekat dengan ground truth: AUPRC {auprc:.3f} "
        f"melewati batas {AUPRC_CEILING}. Label ini tidak lemah lagi"
    )
    # Sisi lain: rule engine juga tidak boleh sama sekali tak berguna, sebab
    # baseline B1 yang lebih lemah dari semestinya justru memperbagus GNN
    # secara semu. Ini aturan keras yang tidak boleh dilanggar.
    assert auprc > baseline, (
        f"rule engine tidak lebih baik dari menebak: AUPRC {auprc:.3f} "
        f"terhadap laju dasar {baseline:.3f}"
    )


@pytest.mark.slow
def test_noise_6_4_defeats_the_rules(scored_full):
    """Noise yang disengaja harus benar-benar mengecoh rule engine.

    Node hard negative dibangun agar tampak bersih dan hard positive agar tampak
    mencurigakan. Kalau rule engine tidak tertipu keduanya, mekanisme noise ini
    tidak berfungsi dan label lemah akan terlalu rapi.
    """
    result, _, weak, _, _ = scored_full
    hard_negatives = [
        node for node in result.population.illicit() if node.hard_negative
    ]
    hard_positives = [node for node in result.population.legit() if node.hard_positive]

    if hard_negatives:
        missed = sum(
            1
            for node in hard_negatives
            if weak[node.node_id]["rule_level"] in ("low", "medium")
        )
        assert missed > 0, (
            "tidak satu pun hard negative lolos dari rule engine; §6.4 tidak bekerja"
        )
    if hard_positives:
        flagged = sum(
            1
            for node in hard_positives
            if weak[node.node_id]["rule_level"] in ("high", "critical")
        )
        assert flagged > 0, (
            "tidak satu pun hard positive tertandai rule engine; §6.4 tidak bekerja"
        )


def test_tier_ablation_changes_result(scored):
    """Ablasi tier harus benar-benar mengubah skor, bukan sekadar tersedia.

    R-X1 dan R-X2 bukan bagian dari daftar tier resmi, jadi laporan hasil harus
    bisa menampilkan skor rule dengan dan tanpa keduanya.
    """
    result, _, _, assessments_all, _ = scored
    directory = None
    for candidate in (result.output_dir,):
        if candidate is not None:
            directory = candidate
    assert directory is not None

    _, assessments_srs, _, _ = build_weak_labels(directory, tiers=SRS_TIER_ONLY)
    by_id_all = {item.node_id: item.score for item in assessments_all}
    by_id_srs = {item.node_id: item.score for item in assessments_srs}

    assert set(by_id_all) == set(by_id_srs)
    assert any(by_id_all[key] != by_id_srs[key] for key in by_id_all), (
        "mematikan tier legacy tidak mengubah skor apa pun; ablasi tidak berfungsi"
    )
    assert ALL_TIERS != SRS_TIER_ONLY
