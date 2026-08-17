"""Tes penjaga `models/feedback.py` — propagasi feedback.

Empat kelas kesalahan yang disasar, semuanya **tidak memunculkan error** bila
terjadi sehingga hanya akan ketahuan setelah angkanya terlanjur dipakai
sebagai hasil:

1. Tanda bukti terbalik saat propagasi (D2 gagal menjepit cosine negatif).
2. Anotasi atau pseudo-label pada node `val`/`test` bocor menjadi label pelatihan.
3. Nilai propagasi menimpa penilaian manusia (urutan denoise terbalik).
4. Anotasi menyusut diam-diam saat disaring.

Ditambah: sitasi Kadam wajib ada di kode.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models import feedback as feedback_module  # noqa: E402
from models.feedback import (  # noqa: E402
    AnnotationSet,
    build_propagation_matrix,
    propagate_feedback,
    read_annotations,
    seed_scores,
    to_supervision,
)
from models.loader import load_seed  # noqa: E402

DATA_ROOT = REPO_ROOT / "data" / "synthetic"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "fake_annotations.csv"
DEV_SEED = 42


@pytest.fixture(scope="module")
def data():
    if not (DATA_ROOT / f"seed_{DEV_SEED}").is_dir():
        pytest.skip(f"data seed {DEV_SEED} belum ada")
    return load_seed(DEV_SEED, DATA_ROOT)


@pytest.fixture(scope="module")
def annotations(data):
    return read_annotations(FIXTURE, data)


@pytest.fixture(scope="module")
def matrix(data):
    return build_propagation_matrix(data)


# --------------------------------------------------------------------------
# Sitasi Kadam wajib ada di kode
# --------------------------------------------------------------------------


def test_kadam_citation_present_in_module():
    """Sitasi Kadam wajib ada di kode, diverifikasi lewat grep."""
    source = Path(feedback_module.__file__).read_text(encoding="utf-8")
    assert "2411.05859" in source, "nomor arXiv Kadam tidak ada di modul"
    assert "Kadam" in source
    assert "ICMLA" in source
    assert feedback_module.__doc__ is not None
    assert "2411.05859" in feedback_module.__doc__, "sitasi harus di docstring modul"


# --------------------------------------------------------------------------
# D1 — skor awal bertanda
# --------------------------------------------------------------------------


def test_seed_scores_are_signed_by_label(data, annotations):
    score = seed_scores(data, annotations)
    for position, index in enumerate(annotations.index):
        expected = annotations.confidence[position]
        if annotations.label[position] == 1:
            assert score[index] == pytest.approx(expected)
        else:
            assert score[index] == pytest.approx(-expected)


def test_unannotated_nodes_start_at_zero(data, annotations):
    score = seed_scores(data, annotations)
    others = np.setdiff1d(np.arange(data.num_nodes), annotations.index)
    assert np.all(score[others] == 0.0)


# --------------------------------------------------------------------------
# D2 — cosine dijepit, tanda tidak boleh terbalik
# --------------------------------------------------------------------------


def test_propagation_matrix_is_non_negative(matrix):
    """Jaminan inti D2: tanpa entri negatif, mekanisme tidak bisa membalik bukti."""
    assert matrix.data.size == 0 or matrix.data.min() >= 0.0


def test_clamping_actually_bites(data):
    """Pastikan D2 bukan sekadar formalitas — banyak edge memang bercosine negatif.

    Kalau suatu saat fitur berubah sehingga tidak ada cosine negatif, tes ini
    gagal dan keputusan D2 perlu ditinjau ulang, bukan dibiarkan jadi kode mati.
    """
    src = data.edge_index[0].numpy()
    dst = data.edge_index[1].numpy()
    x = data.x.numpy()
    norm = np.linalg.norm(x, axis=1)
    norm[norm < 1e-12] = 1.0
    unit = x / norm[:, None]
    cosine = np.einsum("ij,ij->i", unit[src], unit[dst])
    assert (cosine < 0).sum() > 0, "tidak ada cosine negatif; D2 jadi tidak relevan"


def test_positive_only_seeds_never_produce_negative_scores(data, annotations, matrix):
    positive = annotations.label == 1
    subset = AnnotationSet(
        index=annotations.index[positive],
        label=annotations.label[positive],
        confidence=annotations.confidence[positive],
        agreement=None,
        node_ids=[],
        source="uji",
    )
    result = propagate_feedback(data, subset, matrix=matrix)
    assert result.score.min() >= -1e-12


def test_negative_only_seeds_never_produce_positive_scores(data, annotations, matrix):
    negative = annotations.label == 0
    subset = AnnotationSet(
        index=annotations.index[negative],
        label=annotations.label[negative],
        confidence=annotations.confidence[negative],
        agreement=None,
        node_ids=[],
        source="uji",
    )
    result = propagate_feedback(data, subset, matrix=matrix)
    assert result.score.max() <= 1e-12


def test_isolated_nodes_keep_their_seed_score(data, annotations, matrix):
    """Node tanpa edge tidak menerima apa pun; skornya wajib tak berubah."""
    degree = np.bincount(data.edge_index[1].numpy(), minlength=data.num_nodes)
    result = propagate_feedback(data, annotations, matrix=matrix)
    isolated = [i for i in annotations.index if degree[i] == 0]
    assert isolated, "fixture harus memuat node terisolasi agar invarian ini teruji"
    for index in isolated:
        assert result.score[index] == pytest.approx(result.seed_score[index])


# --------------------------------------------------------------------------
# Aturan henti propagasi
# --------------------------------------------------------------------------


def test_propagation_stops_at_max_hops(data, annotations, matrix):
    result = propagate_feedback(data, annotations, max_hops=3, matrix=matrix)
    assert result.hops_run <= 3
    assert len(result.delta_history) == result.hops_run


def test_propagation_stops_early_when_epsilon_reached(data, annotations, matrix):
    """Dengan epsilon sangat besar, iterasi wajib berhenti di hop pertama."""
    result = propagate_feedback(data, annotations, epsilon=1e9, matrix=matrix)
    assert result.converged
    assert result.hops_run == 1


# --------------------------------------------------------------------------
# Denoise — anotasi langsung selalu menang
# --------------------------------------------------------------------------


def test_direct_annotation_always_beats_propagated_value(data, annotations, matrix):
    """Uji adversarial: tiap label sengaja dibuat melawan arah propagasinya.

    Versi non-adversarial tidak cukup — pada data nyata konflik bisa saja tidak
    pernah terjadi, sehingga cabang override tidak pernah dieksekusi dan tesnya
    hampa.
    """
    propagation = propagate_feedback(data, annotations, matrix=matrix)
    flipped = np.where(propagation.score[annotations.index] > 0, 0, 1).astype(np.int64)
    adversarial = AnnotationSet(
        index=annotations.index,
        label=flipped,
        confidence=annotations.confidence,
        agreement=None,
        node_ids=annotations.node_ids,
        source="uji-konflik",
    )
    supervision = to_supervision(data, adversarial, propagation, pseudo_threshold=0.5)
    labels = supervision.extra_labels.numpy()

    conflicts = 0
    for position, index in enumerate(adversarial.index):
        if abs(propagation.score[index]) < 0.5:
            continue
        propagated = 1 if propagation.score[index] > 0 else 0
        human = int(adversarial.label[position])
        if propagated == human:
            continue
        conflicts += 1
        assert labels[index] == human, f"nilai propagasi menimpa manusia di {index}"
    assert conflicts > 0, "tidak ada konflik yang teruji — tes menjadi hampa"


def test_higher_threshold_yields_fewer_pseudo_labels(data, annotations, matrix):
    propagation = propagate_feedback(data, annotations, matrix=matrix)
    counts = [
        to_supervision(
            data, annotations, propagation, pseudo_threshold=t
        ).diagnostics["n_supervised_total"]
        for t in (0.25, 0.5, 1.0, 2.0)
    ]
    assert counts == sorted(counts, reverse=True)
    assert counts[-1] >= len(annotations), "anotasi langsung tidak boleh ikut tersaring"


# --------------------------------------------------------------------------
# Anti-kebocoran
# --------------------------------------------------------------------------


def test_supervision_never_touches_val_or_test(data, annotations, matrix):
    propagation = propagate_feedback(data, annotations, matrix=matrix)
    supervision = to_supervision(data, annotations, propagation, pseudo_threshold=0.25)
    mask = supervision.extra_mask
    assert not bool((mask & data.val_mask).any())
    assert not bool((mask & data.test_mask).any())
    assert not bool((mask & ~data.entity_mask).any())


def test_annotations_on_val_or_test_are_filtered_out(data, tmp_path):
    """Anotasi yang jatuh pada node val/test wajib dibuang, bukan dipakai."""
    rows = np.flatnonzero((data.val_mask | data.test_mask).numpy() & data.entity_mask.numpy())
    node_ids = [data.node_ids[i] for i in rows[:8]]
    path = tmp_path / "leak.csv"
    pd.DataFrame(
        {
            "node_id": node_ids,
            "label": [1] * len(node_ids),
            "confidence_mean": [0.9] * len(node_ids),
            "agreement": [1.0] * len(node_ids),
            "n_annotators": [3] * len(node_ids),
        }
    ).to_csv(path, index=False)

    loaded = read_annotations(path, data)
    assert len(loaded) == 0
    assert loaded.dropped["bukan_split_train"] == len(node_ids)


@pytest.mark.slow
def test_extra_label_hook_is_actually_wired(data):
    """Buktikan `extra_labels` mengubah pelatihan, bukan no-op diam-diam."""
    from models.rgcn import train_rgcn

    base = train_rgcn(data, epochs=40, patience=40, torch_seed=42)
    rows = np.flatnonzero(data.loss_mask.numpy())[:800]
    labels = data.y_weak.numpy().copy()
    labels[rows] = 1 - labels[rows]
    mask = np.zeros(data.num_nodes, dtype=bool)
    mask[rows] = True
    flipped = train_rgcn(
        data,
        epochs=40,
        patience=40,
        torch_seed=42,
        extra_labels=torch.tensor(labels),
        extra_mask=torch.tensor(mask),
    )
    assert float(np.abs(base.prob - flipped.prob).mean()) > 1e-4


@pytest.mark.slow
def test_supervision_outside_train_has_exactly_zero_effect(data):
    """`train_rgcn` wajib menjepit supervisi di luar train ∧ entity."""
    from models.rgcn import train_rgcn

    base = train_rgcn(data, epochs=40, patience=40, torch_seed=42)
    rows = np.flatnonzero((data.test_mask & data.entity_mask).numpy())[:400]
    labels = data.y_weak.numpy().copy()
    labels[rows] = 1 - labels[rows]
    mask = np.zeros(data.num_nodes, dtype=bool)
    mask[rows] = True
    leaked = train_rgcn(
        data,
        epochs=40,
        patience=40,
        torch_seed=42,
        extra_labels=torch.tensor(labels),
        extra_mask=torch.tensor(mask),
    )
    assert float(np.abs(base.prob - leaked.prob).max()) == 0.0


# --------------------------------------------------------------------------
# Penyaringan tidak boleh diam-diam
# --------------------------------------------------------------------------


def test_agreement_filter_is_recorded(data):
    strict = read_annotations(FIXTURE, data, min_agreement=0.7)
    loose = read_annotations(FIXTURE, data)
    assert len(strict) < len(loose)
    assert strict.dropped["kesepakatan_rendah"] == len(loose) - len(strict)


def test_budget_takes_a_prefix(data):
    full = read_annotations(FIXTURE, data)
    subset = read_annotations(FIXTURE, data, budget=10)
    assert len(subset) == 10
    assert subset.dropped["di_luar_anggaran"] == len(full) - 10


def test_order_hint_does_not_silently_drop_annotations(data):
    """`order` adalah petunjuk urutan, bukan saringan.

    Regresi: versi awal membuang anotasi yang tidak tercantum di `order`,
    sehingga 19 dari 20 anotasi fixture lenyap tanpa jejak ketika berkas anotasi
    dan `sample_manifest.json` berasal dari sampel berbeda.
    """
    full = read_annotations(FIXTURE, data)
    with_order = read_annotations(FIXTURE, data, order=["domain_00300", "phone_00174"])
    assert len(with_order) == len(full)
    assert with_order.node_ids[:2] == ["domain_00300", "phone_00174"]
