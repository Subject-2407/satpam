"""Tes penjaga: lembar kerja anotator tidak boleh memuat petunjuk jawaban.

Anotasi manusia hanya bernilai kalau ia penilaian mandiri. Kalau lembar kerja
memuat `rule_score`, anotasi berubah menjadi persetujuan atas rule engine dan
kesepakatan antar-anotator mengukur kepatuhan pada rule, bukan penilaian. Kalau
lembar kerja memuat nama strata, sebagian jawaban langsung tersirat.

Yang dijaga:

1. `annotation/` tidak mengimpor `generator/` — lewat `generate()` seluruh kolom
   jawaban bisa diakses.
2. `annotation/` tidak pernah menyebut nama kolom jawaban.
3. Lembar kerja hasil tidak memuat skor rule, level rule, daftar aturan, kolom
   jawaban, maupun nama strata.
4. Urutan tampilan **bukan** urutan bergilir strata. Urutan itu membuat posisi
   1, 7, 13, ... berasal dari strata yang sama, sehingga strata bisa disimpulkan
   dari posisi.
5. Ketiga anotator menerima himpunan node yang sama tetapi urutan berbeda —
   syarat agar kappa bermakna.
"""

from __future__ import annotations

import ast
import csv
import dataclasses
from pathlib import Path

import pytest

from annotation.sampling import STRATA_ORDER, build_sample, read_weak_labels
from annotation.worksheet import annotator_order, write_worksheet
from generator.build import generate, write_output
from generator.config import GeneratorParams
from rules.build import build_weak_labels, write_weak_labels
from rules.graph import RuleGraph
from rules.loader import load_edges, load_nodes

REPO_ROOT = Path(__file__).resolve().parent.parent
ANNOTATION_DIR = REPO_ROOT / "annotation"

#: Paket yang tidak boleh diimpor dari `annotation/`.
FORBIDDEN_MODULES = {"generator"}

#: Nama kolom jawaban.
FORBIDDEN_COLUMNS = ("gt_illicit", "gt_operator_id", "gt_ecosystem")

#: Istilah yang tidak boleh muncul di lembar kerja anotator.
FORBIDDEN_IN_WORKSHEET = (
    "gt_illicit",
    "gt_operator_id",
    "gt_ecosystem",
    "rule_score",
    "rule_level",
    "triggered_rules",
    "hard negative",
    "hard positive",
    "strata",
    "stratum",
    "proksi",
    "critical",
    "weak_label",
)

SMALL_NODES = 1_200
ANNOTATORS = ("A1", "A2", "A3")


def _python_files() -> list[Path]:
    return sorted(ANNOTATION_DIR.rglob("*.py"))


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    """Bangun data kecil, jalankan rule engine, lalu susun paket anotasi."""
    root = tmp_path_factory.mktemp("annotation")
    result = generate(
        dataclasses.replace(GeneratorParams(), seed=42, n_nodes_target=SMALL_NODES)
    )
    assert result.validation.ok, result.validation.summary()
    seed_dir = write_output(result, root)

    _, assessments, _, _ = build_weak_labels(seed_dir)
    write_weak_labels(seed_dir, assessments)

    graph = RuleGraph.build(
        load_nodes(seed_dir / "nodes.csv"), load_edges(seed_dir / "edges.csv")
    )
    sample = build_sample(graph, read_weak_labels(seed_dir / "weak_labels.csv"), total=60)

    output_dir = seed_dir / "annotation"
    output_dir.mkdir(parents=True, exist_ok=True)
    packets = {}
    for annotator_id in ANNOTATORS:
        order = annotator_order(sample, annotator_id, ANNOTATORS)
        worksheet, answers = write_worksheet(
            output_dir, graph, sample, annotator_id, order
        )
        packets[annotator_id] = (worksheet, answers, order)
    return result, graph, sample, packets


def test_annotation_does_not_import_generator():
    """annotation/ tidak boleh mengimpor generator/."""
    violations: list[str] = []
    for py_file in _python_files():
        tree = ast.parse(py_file.read_text(encoding="utf-8-sig"), filename=str(py_file))
        relative = py_file.relative_to(REPO_ROOT)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                        violations.append(f"{relative}:{node.lineno} import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")[0]
                if module in FORBIDDEN_MODULES:
                    violations.append(f"{relative}:{node.lineno} from {node.module}")
    assert not violations, "annotation/ mengimpor generator/:\n" + "\n".join(violations)


def test_annotation_never_names_ground_truth_columns():
    """Nama kolom jawaban tidak boleh muncul di mana pun dalam annotation/."""
    violations: list[str] = []
    for py_file in _python_files():
        relative = py_file.relative_to(REPO_ROOT)
        for number, line in enumerate(
            py_file.read_text(encoding="utf-8-sig").splitlines(), start=1
        ):
            for column in FORBIDDEN_COLUMNS:
                if column in line:
                    violations.append(f"{relative}:{number} menyebut {column}")
    assert not violations, "annotation/ menyebut kolom jawaban:\n" + "\n".join(violations)


def _node_blocks(worksheet: Path) -> str:
    """Bagian lembar kerja yang dihasilkan dari data, tanpa prosa instruksi.

    Instruksi sengaja menyebut nama berkas yang tidak boleh dibuka anotator
    (`weak_labels.csv`), jadi memindainya dengan daftar istilah terlarang akan
    selalu memberi positif palsu. Yang berisiko membocorkan jawaban adalah blok
    per-node yang dirakit dari data, dan itulah yang diperiksa di sini.
    """
    text = worksheet.read_text(encoding="utf-8")
    fence = text.index("```text")
    return text[fence:]


def test_worksheet_leaks_nothing(prepared):
    """Blok node tidak boleh memuat skor rule, kolom jawaban, atau nama strata."""
    _, _, _, packets = prepared
    for annotator_id, (worksheet, _, _) in packets.items():
        blocks = _node_blocks(worksheet).lower()
        for token in FORBIDDEN_IN_WORKSHEET:
            assert token.lower() not in blocks, (
                f"worksheet_{annotator_id}.md memuat istilah terlarang {token!r} "
                f"di dalam blok node"
            )


def test_worksheet_instructions_forbid_opening_answer_files(prepared):
    """Instruksi harus menyebut berkas yang tidak boleh dibuka.

    Lembar kerja mandiri, tetapi `nodes.csv` tetap ada di disk anotator dan
    memuat kolom jawaban. Mencegah orang membukanya adalah soal prosedur, dan
    prosedur itu harus tertulis.
    """
    _, _, _, packets = prepared
    for annotator_id, (worksheet, _, _) in packets.items():
        text = worksheet.read_text(encoding="utf-8")
        header = text[: text.index("```text")]
        assert "nodes.csv" in header, f"instruksi {annotator_id} tidak melarang nodes.csv"
        assert "weak_labels.csv" in header


def test_worksheet_does_not_leak_actual_ground_truth_values(prepared):
    """Nilai `gt_operator_id` tidak boleh muncul di lembar kerja.

    Cek berbeda dari yang sebelumnya: yang dicari bukan nama kolomnya, melainkan
    nilainya. Kalau id operator seperti `OP_03` sampai tertulis, keanggotaan
    jaringan langsung terbaca.
    """
    result, _, _, packets = prepared
    operator_ids = {
        node.gt_operator_id for node in result.population.nodes if node.gt_operator_id
    }
    assert operator_ids, "data uji tidak punya operator; tes ini tidak bermakna"
    for annotator_id, (worksheet, _, _) in packets.items():
        text = worksheet.read_text(encoding="utf-8")
        for operator_id in operator_ids:
            assert operator_id not in text, (
                f"worksheet_{annotator_id}.md memuat id operator {operator_id}"
            )


def test_display_order_is_not_the_stratum_round_robin(prepared):
    """Urutan tampilan tidak boleh sama dengan urutan bergilir strata.

    Urutan bergilir membuat posisi 1, 7, 13, ... berasal dari strata yang sama.
    Anotator yang menyadarinya bisa menyimpulkan strata dari posisi.
    """
    _, _, sample, packets = prepared
    a5_order = sample.ordered()
    for annotator_id, (_, _, order) in packets.items():
        assert order != a5_order, (
            f"urutan tampilan {annotator_id} sama dengan annotation_order; "
            f"strata bisa disimpulkan dari posisi"
        )

    # Uji lebih kuat: pada urutan bergilir, strata pada posisi i dan i+6 sama.
    # Urutan tampilan tidak boleh punya sifat itu secara sistematis.
    for annotator_id, (_, _, order) in packets.items():
        stride = len(STRATA_ORDER)
        matched = sum(
            1
            for index in range(len(order) - stride)
            if sample.stratum_of[order[index]]
            == sample.stratum_of[order[index + stride]]
        )
        share = matched / max(len(order) - stride, 1)
        assert share < 0.6, (
            f"urutan tampilan {annotator_id} masih berpola strata "
            f"(kecocokan langkah-{stride}: {share:.2f})"
        )


def test_all_annotators_get_same_items_in_different_order(prepared):
    """Item identik agar kappa bermakna; urutan berbeda agar kelelahan tersebar."""
    _, _, sample, packets = prepared
    orders = {name: order for name, (_, _, order) in packets.items()}
    expected = set(sample.node_ids)
    for name, order in orders.items():
        assert set(order) == expected, f"{name} tidak menerima himpunan node yang sama"
        assert len(order) == len(expected), f"{name} punya node ganda"
    names = sorted(orders)
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            assert orders[first] != orders[second], (
                f"urutan {first} dan {second} identik"
            )


def test_answers_file_matches_worksheet_order(prepared):
    """Baris berkas jawaban harus urut sama dengan lembar kerja."""
    _, _, _, packets = prepared
    for annotator_id, (_, answers, order) in packets.items():
        with answers.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert [row["node_id"] for row in rows] == order
        assert all(row["annotator_id"] == annotator_id for row in rows)
        assert all(row["label"] == "" for row in rows), "label harus kosong"
        assert all(row["confidence"] == "" for row in rows)


def test_sample_only_contains_annotatable_types_with_neighbors(prepared):
    """Sampel hanya tipe infrastruktur, dan setiap node punya tetangga.

    Propagasi feedback menyebar lewat edge; anotasi pada node terisolasi
    tidak menyebar ke mana pun.
    """
    from annotation.sampling import ANNOTATABLE_NODE_TYPES

    _, graph, sample, _ = prepared
    for node_id in sample.node_ids:
        node = graph.nodes[node_id]
        assert node.node_type in ANNOTATABLE_NODE_TYPES, node_id
        assert graph.degree(node_id) >= 1, f"{node_id} tidak punya tetangga"


def test_sampling_is_deterministic(prepared):
    """Sampel dan urutan A5 harus sama pada pemanggilan ulang."""
    _, graph, sample, _ = prepared
    weak = {
        node_id: (signal.rule_score, signal.rule_level)
        for node_id, signal in sample.signals.items()
    }
    again = build_sample(graph, weak, total=len(sample.node_ids))
    assert again.node_ids == sample.node_ids
    assert again.order_of == sample.order_of
    assert again.stratum_of == sample.stratum_of
