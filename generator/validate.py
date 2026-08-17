"""LANGKAH 8 — pemeriksaan keluaran generator terhadap kontrak data.

Validator ini adalah syarat lolos: `build.py` tidak menulis berkas apa pun bila
ada satu saja pelanggaran. Tujuannya supaya kesalahan muncul di sini, bukan
berupa CSV cacat yang baru ketahuan berhari-hari kemudian di tangan orang lain.

**Dua tingkat keparahan.** `ERROR` untuk pelanggaran kontrak data — kolom,
tipe, edge menggantung, invariant ground truth, konsistensi fitur. `WARNING`
untuk penyimpangan dari angka target skala populasi dan noise wajib, yang
memang tidak berlaku saat generator dijalankan berskala kecil untuk smoke
test. Pada skala penuh (`n_nodes_target >= 5000`) penyimpangan target ikut
dijadikan ERROR.

**Dua mode.** Keduanya memeriksa baris CSV yang benar-benar akan ditulis, bukan
objek di memori, sehingga yang divalidasi persis yang diterbitkan:

- `run_all()` — dipanggil `build.py` sebelum menulis. Selain cek kontrak, ia
  bisa memeriksa hal yang hanya terlihat dari medan internal: penjaga G7 penuh
  per sisi ekosistem, porsi hard negative/positive, dan jumlah operator.
- `validate_directory()` — memeriksa direktori keluaran yang sudah ada, untuk
  dipakai orang lain tanpa menjalankan generator. Mode ini tidak bisa melihat
  `side`, jadi penjaga G7-nya versi yang lebih lemah: tidak ada `transferred_to`
  antara node `gt_ecosystem='judol'` dan `gt_ecosystem='pinjol'`. Kasus dua sisi
  di dalam satu operator `both` tidak terjangkau dari CSV, dan keterbatasan itu
  dilaporkan eksplisit agar tidak disalahsangka sudah diperiksa.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar. Ia memeriksa bentuk data, bukan menilai risiko.
"""

from __future__ import annotations

import csv
import dataclasses
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

from generator.config import GeneratorParams
from generator.features import CONTENT_NODE_TYPES
from generator.noise import NoiseReport
from generator.operators import OperatorPlan
from generator.population import Population
from generator.records import EdgeRecord
from generator.schema import (
    ECOSYSTEMS,
    EDGES_COLUMNS,
    FINANCIAL_NODE_TYPES,
    NODE_ID_RE,
    NODE_TYPES,
    NODES_COLUMNS,
    REL_TYPES,
    SPLITS,
    is_legal_edge,
)
from generator.split import SplitReport
from generator.timeline import Timeline, age_days

#: Ambang skala penuh; di bawah ini target skala populasi dan noise jadi
#: peringatan saja.
FULL_SCALE_NODES: int = 5_000

#: Toleransi pembandingan nilai pecahan hasil baca-tulis CSV.
FLOAT_TOLERANCE: float = 1e-6


@dataclass
class ValidationResult:
    """Kumpulan pelanggaran dan peringatan beserta daftar cek yang dijalankan."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks_run: list[str] = field(default_factory=list)
    checks_skipped: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def ran(self, name: str) -> None:
        self.checks_run.append(name)

    def skipped(self, name: str, reason: str) -> None:
        self.checks_skipped.append(f"{name} ({reason})")

    def summary(self) -> str:
        lines = [
            f"{len(self.checks_run)} cek dijalankan, "
            f"{len(self.errors)} pelanggaran, {len(self.warnings)} peringatan"
        ]
        for message in self.errors:
            lines.append(f"  PELANGGARAN  {message}")
        for message in self.warnings:
            lines.append(f"  peringatan   {message}")
        for name in self.checks_skipped:
            lines.append(f"  dilewati     {name}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pintu masuk
# ---------------------------------------------------------------------------


def run_all(
    params: GeneratorParams,
    timeline: Timeline,
    plan: OperatorPlan,
    population: Population,
    edges: Sequence[EdgeRecord],
    noise_report: NoiseReport,
    split_report: SplitReport,
) -> ValidationResult:
    """Validasi lengkap sebelum berkas ditulis (dipanggil `build.py`)."""
    node_rows = [node.to_csv_row(timeline) for node in population.nodes]
    edge_rows = [edge.to_csv_row(timeline) for edge in edges]

    result = validate_rows(node_rows, edge_rows, params)
    _check_g7_sides_in_memory(result, population, edges)
    _check_noise_shares(result, params, noise_report)
    _check_population_ratios(result, params, plan, population)
    _check_split_report(result, params, split_report)
    return result


def validate_directory(directory: str | Path) -> ValidationResult:
    """Validasi direktori keluaran yang sudah ada, tanpa menjalankan generator."""
    directory = Path(directory)
    result = ValidationResult()

    nodes_path = directory / "nodes.csv"
    edges_path = directory / "edges.csv"
    manifest_path = directory / "manifest.json"

    for path in (nodes_path, edges_path, manifest_path):
        if not path.is_file():
            result.error(f"berkas wajib tidak ada: {path.name}")
    if not result.ok:
        return result

    node_rows = _read_csv(nodes_path)
    edge_rows = _read_csv(edges_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    params = _params_from_manifest(manifest)
    result = validate_rows(node_rows, edge_rows, params)
    _check_manifest(result, manifest, node_rows, edge_rows)
    _check_g7_ecosystems_in_rows(result, node_rows, edge_rows)
    result.skipped(
        "penjaga G7 per sisi ekosistem",
        "kolom `side` medan internal, tidak ada di CSV; "
        "kasus dua sisi dalam satu operator `both` tidak terjangkau dari berkas",
    )
    return result


# ---------------------------------------------------------------------------
# Cek kontrak data atas baris CSV
# ---------------------------------------------------------------------------


def validate_rows(
    node_rows: list[dict[str, object]],
    edge_rows: list[dict[str, object]],
    params: GeneratorParams,
) -> ValidationResult:
    """Seluruh cek kontrak data atas baris yang akan (atau sudah) ditulis."""
    result = ValidationResult()

    _check_columns(result, node_rows, NODES_COLUMNS, "nodes.csv")
    _check_columns(result, edge_rows, EDGES_COLUMNS, "edges.csv")
    if not result.ok:
        # Tanpa kolom yang benar, cek lanjutan hanya akan menghasilkan derau.
        result.skipped("cek isi", "kolom belum sesuai kontrak")
        return result

    nodes = _parse_nodes(result, node_rows)
    _check_node_ids(result, nodes)
    _check_node_enums(result, nodes)
    _check_gt_invariants(result, nodes)
    _check_node_times(result, nodes)
    _check_feature_domains(result, nodes)
    _check_edges(result, nodes, edge_rows)
    _check_derived_features(result, nodes, edge_rows)
    _check_split_assignment(result, nodes, params)
    _check_targets(result, nodes, edge_rows, params)
    return result


def _check_columns(
    result: ValidationResult,
    rows: list[dict[str, object]],
    expected: tuple[str, ...],
    label: str,
) -> None:
    """Kolom harus tepat sama dan berurutan seperti kontraknya."""
    result.ran(f"kolom {label} sesuai §5.3")
    if not rows:
        result.error(f"{label}: tidak ada baris sama sekali")
        return
    actual = tuple(rows[0])
    if actual != expected:
        result.error(
            f"{label}: kolom tidak sesuai kontrak §5.3\n"
            f"    diharapkan: {expected}\n"
            f"    didapat   : {actual}"
        )


@dataclass
class _Node:
    """Baris `nodes.csv` yang sudah di-parse."""

    node_id: str
    node_type: str
    first_seen_at: datetime
    last_seen_at: datetime
    features: dict[str, float]
    gt_illicit: int
    gt_operator_id: str
    gt_ecosystem: str
    split: str


def _parse_nodes(
    result: ValidationResult, rows: list[dict[str, object]]
) -> list[_Node]:
    """Ubah baris mentah menjadi bentuk terurai; galat parse jadi pelanggaran."""
    result.ran("nilai kolom nodes.csv bisa diurai")
    nodes: list[_Node] = []
    for row in rows:
        try:
            nodes.append(
                _Node(
                    node_id=str(row["node_id"]),
                    node_type=str(row["node_type"]),
                    first_seen_at=Timeline.from_iso(str(row["first_seen_at"])),
                    last_seen_at=Timeline.from_iso(str(row["last_seen_at"])),
                    features={
                        name: float(row[name])  # type: ignore[arg-type]
                        for name in NODES_COLUMNS
                        if name.startswith("feat_")
                    },
                    gt_illicit=int(row["gt_illicit"]),  # type: ignore[arg-type]
                    gt_operator_id=str(row["gt_operator_id"]),
                    gt_ecosystem=str(row["gt_ecosystem"]),
                    split=str(row["split"]),
                )
            )
        except (ValueError, KeyError, TypeError) as exc:
            result.error(f"baris nodes.csv gagal diurai ({row.get('node_id')}): {exc}")
    return nodes


def _check_node_ids(result: ValidationResult, nodes: list[_Node]) -> None:
    """Format `node_id` dan keunikan globalnya."""
    result.ran("format dan keunikan node_id")
    seen: set[str] = set()
    duplicates: list[str] = []
    malformed: list[str] = []
    mismatched: list[str] = []

    for node in nodes:
        if node.node_id in seen:
            duplicates.append(node.node_id)
        seen.add(node.node_id)

        match = NODE_ID_RE.match(node.node_id)
        if match is None:
            malformed.append(node.node_id)
        elif match.group("node_type") != node.node_type:
            mismatched.append(node.node_id)

    if duplicates:
        result.error(f"node_id duplikat ({len(duplicates)}): {duplicates[:5]}")
    if malformed:
        result.error(
            f"node_id tidak sesuai format {{type}}_{{5 digit}} "
            f"({len(malformed)}): {malformed[:5]}"
        )
    if mismatched:
        result.error(
            f"prefiks node_id tidak sama dengan node_type "
            f"({len(mismatched)}): {mismatched[:5]}"
        )


def _check_node_enums(result: ValidationResult, nodes: list[_Node]) -> None:
    """Nilai kolom kategorikal harus di dalam domain yang dikontrakkan."""
    result.ran("domain nilai node_type, gt_ecosystem, split")
    for label, valid, getter in (
        ("node_type", set(NODE_TYPES), lambda n: n.node_type),
        ("gt_ecosystem", set(ECOSYSTEMS), lambda n: n.gt_ecosystem),
        ("split", set(SPLITS), lambda n: n.split),
    ):
        bad = sorted({getter(node) for node in nodes} - valid)
        if bad:
            result.error(f"{label}: nilai di luar kontrak: {bad}")

    bad_illicit = sorted({node.gt_illicit for node in nodes} - {0, 1})
    if bad_illicit:
        result.error(f"gt_illicit bukan 0/1: {bad_illicit}")


def _check_gt_invariants(result: ValidationResult, nodes: list[_Node]) -> None:
    """Invariant ground truth.

    `gt_operator_id` wajib kosong tepat ketika `gt_illicit=0`, dan
    `gt_ecosystem='none'` wajib berpasangan dengan keadaan yang sama.
    """
    result.ran("invariant ground truth §5.3")
    bad_operator = [
        node.node_id
        for node in nodes
        if bool(node.gt_operator_id) != bool(node.gt_illicit)
    ]
    bad_ecosystem = [
        node.node_id
        for node in nodes
        if (node.gt_ecosystem == "none") != (node.gt_illicit == 0)
    ]
    bad_report_victim = [
        node.node_id
        for node in nodes
        if node.node_type in ("report", "victim") and node.gt_illicit == 1
    ]

    if bad_operator:
        result.error(
            f"gt_operator_id harus kosong tepat ketika gt_illicit=0 "
            f"({len(bad_operator)}): {bad_operator[:5]}"
        )
    if bad_ecosystem:
        result.error(
            f"gt_ecosystem='none' harus berpasangan dengan gt_illicit=0 "
            f"({len(bad_ecosystem)}): {bad_ecosystem[:5]}"
        )
    if bad_report_victim:
        result.error(
            f"node report/victim tidak boleh gt_illicit=1 "
            f"({len(bad_report_victim)}): {bad_report_victim[:5]}"
        )


def _check_node_times(result: ValidationResult, nodes: list[_Node]) -> None:
    """Urutan waktu dan kecocokan `feat_age_days` dengan selisihnya."""
    result.ran("urutan waktu node dan feat_age_days")
    bad_order = [
        node.node_id for node in nodes if node.last_seen_at < node.first_seen_at
    ]
    bad_age = [
        node.node_id
        for node in nodes
        if abs(
            node.features["feat_age_days"]
            - age_days(node.first_seen_at, node.last_seen_at)
        )
        > FLOAT_TOLERANCE
    ]
    if bad_order:
        result.error(
            f"last_seen_at lebih awal dari first_seen_at "
            f"({len(bad_order)}): {bad_order[:5]}"
        )
    if bad_age:
        result.error(
            f"feat_age_days tidak sama dengan last_seen_at - first_seen_at "
            f"({len(bad_age)}): {bad_age[:5]}"
        )


def _check_feature_domains(result: ValidationResult, nodes: list[_Node]) -> None:
    """Batas nilai fitur dan nol struktural yang dituntut kontrak."""
    result.ran("batas nilai fitur dan nol struktural §5.3")
    problems: dict[str, list[str]] = {}

    def note(label: str, node_id: str) -> None:
        problems.setdefault(label, []).append(node_id)

    for node in nodes:
        feats = node.features
        if not 0.0 <= feats["feat_kw_score"] <= 1.0:
            note("feat_kw_score di luar [0, 1]", node.node_id)
        if feats["feat_is_qris"] not in (0.0, 1.0):
            note("feat_is_qris bukan 0/1", node.node_id)
        if node.node_type != "ewallet" and feats["feat_is_qris"] != 0.0:
            note("feat_is_qris tidak nol pada tipe selain ewallet", node.node_id)
        if node.node_type not in FINANCIAL_NODE_TYPES and (
            feats["feat_txn_count"] != 0.0 or feats["feat_txn_amount_sum"] != 0.0
        ):
            note("feat_txn_* tidak nol pada node non-finansial", node.node_id)
        if node.node_type not in CONTENT_NODE_TYPES and feats["feat_kw_score"] != 0.0:
            note("feat_kw_score tidak nol pada tipe tanpa konten", node.node_id)
        if feats["feat_txn_count"] == 0.0 and feats["feat_txn_amount_sum"] != 0.0:
            note("feat_txn_amount_sum tidak nol padahal feat_txn_count nol", node.node_id)
        if any(value < 0.0 for value in feats.values()):
            note("ada nilai fitur negatif", node.node_id)

    for label, ids in problems.items():
        result.error(f"{label} ({len(ids)}): {ids[:5]}")


def _check_edges(
    result: ValidationResult,
    nodes: list[_Node],
    edge_rows: list[dict[str, object]],
) -> None:
    """Kontrak atas `edges.csv`: tipe relasi, legalitas triple, integritas."""
    result.ran("kontrak edges.csv §5.2")
    by_id = {node.node_id: node for node in nodes}

    bad_rel: set[str] = set()
    dangling: list[str] = []
    illegal: list[str] = []
    bad_weight: list[str] = []
    self_loops: list[str] = []
    early: list[str] = []
    bad_time: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    duplicates: list[str] = []

    for row in edge_rows:
        src_id, dst_id = str(row["src_id"]), str(row["dst_id"])
        rel_type = str(row["rel_type"])
        label = f"{src_id}-{rel_type}->{dst_id}"

        if rel_type not in REL_TYPES:
            bad_rel.add(rel_type)

        key = (src_id, dst_id, rel_type)
        if key in seen:
            duplicates.append(label)
        seen.add(key)

        if src_id == dst_id:
            self_loops.append(label)

        try:
            weight = float(row["weight"])  # type: ignore[arg-type]
            if not 0.0 <= weight <= 1.0:
                bad_weight.append(label)
        except (ValueError, TypeError):
            bad_weight.append(label)

        src, dst = by_id.get(src_id), by_id.get(dst_id)
        if src is None or dst is None:
            dangling.append(label)
            continue

        if not is_legal_edge(src.node_type, rel_type, dst.node_type):
            illegal.append(f"({src.node_type}) -{rel_type}-> ({dst.node_type}) {label}")

        try:
            first_seen = Timeline.from_iso(str(row["first_seen_at"]))
        except ValueError:
            bad_time.append(label)
            continue
        if first_seen < max(src.first_seen_at, dst.first_seen_at):
            early.append(label)

    if bad_rel:
        result.error(f"rel_type di luar kontrak §5.2: {sorted(bad_rel)}")
    if dangling:
        result.error(
            f"edge menunjuk node_id yang tidak ada di nodes.csv "
            f"({len(dangling)}): {dangling[:5]}"
        )
    if illegal:
        result.error(
            f"triple (src_type, rel_type, dst_type) melanggar §5.2 "
            f"({len(illegal)}): {illegal[:5]}"
        )
    if bad_weight:
        result.error(f"weight di luar [0, 1] ({len(bad_weight)}): {bad_weight[:5]}")
    if self_loops:
        result.error(f"edge self-loop ({len(self_loops)}): {self_loops[:5]}")
    if duplicates:
        result.error(
            f"edge duplikat pada (src_id, dst_id, rel_type) "
            f"({len(duplicates)}): {duplicates[:5]}"
        )
    if bad_time:
        result.error(f"first_seen_at edge gagal diurai ({len(bad_time)}): {bad_time[:5]}")
    if early:
        result.error(
            f"edge muncul sebelum salah satu ujungnya ada "
            f"({len(early)}): {early[:5]}"
        )


def _check_derived_features(
    result: ValidationResult,
    nodes: list[_Node],
    edge_rows: list[dict[str, object]],
) -> None:
    """`feat_degree_*` dan `feat_report_count` harus cocok dengan `edges.csv`.

    Cek ini yang membuat kedua berkas tidak bisa saling bertentangan. Siapa pun
    yang menghitung ulang derajat dari `edges.csv` harus mendapat angka yang
    identik dengan kolomnya — kalau tidak, `noise.py` dan `features.py`
    dijalankan dengan urutan yang salah.
    """
    result.ran("feat_degree_* dan feat_report_count cocok dengan edges.csv")
    degree_in: dict[str, int] = {}
    degree_out: dict[str, int] = {}
    report_count: dict[str, int] = {}

    for row in edge_rows:
        src_id, dst_id = str(row["src_id"]), str(row["dst_id"])
        degree_out[src_id] = degree_out.get(src_id, 0) + 1
        degree_in[dst_id] = degree_in.get(dst_id, 0) + 1
        if str(row["rel_type"]) == "mentions":
            report_count[dst_id] = report_count.get(dst_id, 0) + 1

    mismatches: list[str] = []
    for node in nodes:
        expected = {
            "feat_degree_in": float(degree_in.get(node.node_id, 0)),
            "feat_degree_out": float(degree_out.get(node.node_id, 0)),
            "feat_report_count": float(report_count.get(node.node_id, 0)),
        }
        for name, value in expected.items():
            if abs(node.features[name] - value) > FLOAT_TOLERANCE:
                mismatches.append(
                    f"{node.node_id}.{name}={node.features[name]} "
                    f"tapi edges.csv memberi {value}"
                )

    if mismatches:
        result.error(
            f"fitur turunan tidak cocok dengan edges.csv "
            f"({len(mismatches)}): {mismatches[:5]}"
        )


def _check_split_assignment(
    result: ValidationResult,
    nodes: list[_Node],
    params: GeneratorParams,
) -> None:
    """Kolom `split` harus persis hasil persentil `first_seen_at`.

    Persentil dihitung ulang di sini dari `first_seen_at`. Titik acuannya tidak
    penting: pergeseran acuan menggeser ambang sebesar hal yang sama, jadi
    perbandingannya tidak berubah.
    """
    result.ran("split sesuai persentil first_seen_at §5.4")
    if not nodes:
        return

    offsets = np.array(
        [node.first_seen_at.timestamp() for node in nodes], dtype=float
    )
    train_cut = float(np.percentile(offsets, params.split_train_pct))
    val_cut = float(np.percentile(offsets, params.split_val_pct))

    mismatches: list[str] = []
    counts = {name: 0 for name in SPLITS}
    illicit_counts = {name: 0 for name in SPLITS}

    for node, offset in zip(nodes, offsets):
        expected = (
            "train" if offset <= train_cut else "val" if offset <= val_cut else "test"
        )
        if node.split != expected:
            mismatches.append(f"{node.node_id}: {node.split} seharusnya {expected}")
        counts[node.split] = counts.get(node.split, 0) + 1
        if node.gt_illicit:
            illicit_counts[node.split] = illicit_counts.get(node.split, 0) + 1

    if mismatches:
        result.error(
            f"kolom split tidak sesuai persentil §5.4 "
            f"({len(mismatches)}): {mismatches[:5]}"
        )

    empty = [name for name in SPLITS if illicit_counts.get(name, 0) == 0]
    if empty:
        result.error(
            f"split tanpa node positif sama sekali: {empty}. "
            f"AUPRC di split itu tidak bermakna (ATURAN KERAS #4)"
        )

    for name in SPLITS:
        total = counts.get(name, 0)
        positives = illicit_counts.get(name, 0)
        if 0 < positives < 20:
            result.warn(
                f"split '{name}' hanya punya {positives} node positif dari {total}; "
                f"metrik di split ini akan berderau tinggi"
            )


def _check_targets(
    result: ValidationResult,
    nodes: list[_Node],
    edge_rows: list[dict[str, object]],
    params: GeneratorParams,
) -> None:
    """Angka target skala populasi. ERROR pada skala penuh, peringatan pada skala kecil."""
    result.ran("angka target §6.2")
    full_scale = params.n_nodes_target >= FULL_SCALE_NODES
    report = result.error if full_scale else result.warn
    scale_note = "" if full_scale else " (skala dikecilkan, target §6.2 tidak berlaku)"

    illicit = [node for node in nodes if node.gt_illicit == 1]
    ratio = len(illicit) / len(nodes) if nodes else 0.0
    low, high = params.anomaly_ratio
    if not low <= ratio <= high:
        report(
            f"anomaly ratio {ratio:.4f} di luar target §6.2 [{low}, {high}]{scale_note}"
        )

    edge_low, edge_high = params.n_edges_target
    if not edge_low <= len(edge_rows) <= edge_high:
        report(
            f"jumlah edge {len(edge_rows):,} di luar target §6.2 "
            f"[{edge_low:,}, {edge_high:,}]{scale_note}"
        )

    operators = {node.gt_operator_id for node in illicit}
    op_low, op_high = params.n_operators
    if not op_low <= len(operators) <= op_high:
        report(
            f"jumlah operator {len(operators)} di luar target §6.2 "
            f"[{op_low}, {op_high}]{scale_note}"
        )

    both = {node.gt_operator_id for node in illicit if node.gt_ecosystem == "both"}
    both_low, both_high = params.n_both_operators
    if not both_low <= len(both) <= both_high:
        report(
            f"jumlah operator lintas-ekosistem {len(both)} di luar target §6.2 "
            f"[{both_low}, {both_high}]{scale_note}"
        )

    # Satu operator harus punya satu ekosistem yang konsisten.
    ecosystem_of: dict[str, set[str]] = {}
    for node in illicit:
        ecosystem_of.setdefault(node.gt_operator_id, set()).add(node.gt_ecosystem)
    inconsistent = {
        operator: sorted(values)
        for operator, values in ecosystem_of.items()
        if len(values) > 1
    }
    if inconsistent:
        result.error(f"operator dengan gt_ecosystem tidak konsisten: {inconsistent}")


# ---------------------------------------------------------------------------
# Cek yang butuh medan internal (hanya mode memori)
# ---------------------------------------------------------------------------


def _check_g7_sides_in_memory(
    result: ValidationResult,
    population: Population,
    edges: Sequence[EdgeRecord],
) -> None:
    """PENJAGA G7 penuh — tidak ada aliran dana antar sisi ekosistem.

    Ini penjaga aturan generatif G7: PPATK (Oktober 2023) menyatakan belum
    menemukan aliran dana judol langsung ke pinjol, jadi generator hanya boleh
    memodelkan infrastruktur dan korban bersama. Cek ini memakai medan internal
    `side`, sehingga ia juga menjangkau dua sisi di dalam satu operator `both` —
    kasus yang tidak terlihat dari `gt_ecosystem` di CSV.

    Edge palsu ikut diperiksa: ia terbit di berkas yang dipublikasikan.
    """
    result.ran("penjaga G7 per sisi ekosistem (medan internal)")
    by_id = {node.node_id: node for node in population.nodes}
    violations: list[str] = []

    for edge in edges:
        if edge.rel_type != "transferred_to":
            continue
        src, dst = by_id.get(edge.src_id), by_id.get(edge.dst_id)
        if src is None or dst is None:
            continue
        if src.side and dst.side and src.side != dst.side:
            violations.append(
                f"{edge.src_id}({src.side}) -> {edge.dst_id}({dst.side}) "
                f"[{edge.rule_tag}]"
            )

    if violations:
        result.error(
            f"PELANGGARAN G7 — aliran dana lintas-ekosistem "
            f"({len(violations)}): {violations[:5]}. "
            f"Ini membatalkan klaim novelty lintas-ekosistem (KT-02)"
        )


def _check_noise_shares(
    result: ValidationResult,
    params: GeneratorParams,
    report: NoiseReport,
) -> None:
    """Porsi noise wajib yang benar-benar diterapkan."""
    result.ran("porsi noise §6.4")
    if abs(report.drop_share_actual - params.edge_drop_share) > 0.005:
        result.error(
            f"porsi edge dibuang {report.drop_share_actual:.4f} menyimpang dari "
            f"target §6.4 {params.edge_drop_share}"
        )
    if abs(report.false_share_actual - params.false_edge_share) > 0.005:
        result.error(
            f"porsi edge palsu {report.false_share_actual:.4f} menyimpang dari "
            f"target §6.4 {params.false_edge_share}"
        )
    if report.false_edge_attempts_failed:
        result.warn(
            f"{report.false_edge_attempts_failed} edge palsu gagal dibuat; "
            f"kombinasi tipe kemungkinan sudah penuh"
        )
    if report.isolated_nodes_after:
        result.warn(
            f"{report.isolated_nodes_after} node kehilangan seluruh edge-nya "
            f"setelah penghapusan acak §6.4"
        )


def _check_population_ratios(
    result: ValidationResult,
    params: GeneratorParams,
    plan: OperatorPlan,
    population: Population,
) -> None:
    """Porsi hard negative/positive dan catatan pemangkasan skala."""
    result.ran("porsi hard negative dan hard positive §6.4")
    full_scale = params.n_nodes_target >= FULL_SCALE_NODES
    report = result.error if full_scale else result.warn

    illicit = population.illicit()
    legit = population.legit()

    if illicit:
        share = sum(node.hard_negative for node in illicit) / len(illicit)
        low, high = params.hard_negative_share
        if not low <= share <= high:
            report(
                f"porsi hard negative {share:.4f} di luar target §6.4 [{low}, {high}]"
            )
    if legit:
        share = sum(node.hard_positive for node in legit) / len(legit)
        low, high = params.hard_positive_share
        if not low <= share <= high:
            report(
                f"porsi hard positive {share:.4f} di luar target §6.4 [{low}, {high}]"
            )

    for note in plan.scale_notes:
        result.warn(f"pemangkasan skala: {note}")
    for note in population.notes:
        result.warn(f"catatan populasi: {note}")


def _check_split_report(
    result: ValidationResult,
    params: GeneratorParams,
    report: SplitReport,
) -> None:
    """Sebaran split terhadap persentil target."""
    result.ran("sebaran split terhadap persentil §5.4")
    total = sum(report.counts.values())
    if total == 0:
        return
    expected = {
        "train": params.split_train_pct / 100.0,
        "val": (params.split_val_pct - params.split_train_pct) / 100.0,
        "test": (100.0 - params.split_val_pct) / 100.0,
    }
    for name, share in expected.items():
        actual = report.counts.get(name, 0) / total
        if abs(actual - share) > 0.01:
            result.error(
                f"porsi node split '{name}' {actual:.4f} menyimpang dari §5.4 {share:.4f}"
            )


# ---------------------------------------------------------------------------
# Cek berbasis berkas
# ---------------------------------------------------------------------------


def _check_g7_ecosystems_in_rows(
    result: ValidationResult,
    node_rows: list[dict[str, object]],
    edge_rows: list[dict[str, object]],
) -> None:
    """Penjaga G7 versi CSV — tidak ada transfer judol <-> pinjol.

    Versi yang bisa diperiksa tanpa medan internal, dan justru versi inilah yang
    dilihat pembaca luar saat membuka `edges.csv`.
    """
    result.ran("penjaga G7 antar gt_ecosystem (berbasis berkas)")
    ecosystem_of = {
        str(row["node_id"]): str(row["gt_ecosystem"]) for row in node_rows
    }
    violations = []
    for row in edge_rows:
        if str(row["rel_type"]) != "transferred_to":
            continue
        src = ecosystem_of.get(str(row["src_id"]))
        dst = ecosystem_of.get(str(row["dst_id"]))
        if {src, dst} == {"judol", "pinjol"}:
            violations.append(f"{row['src_id']}({src}) -> {row['dst_id']}({dst})")
    if violations:
        result.error(
            f"PELANGGARAN G7 — transfer langsung judol <-> pinjol "
            f"({len(violations)}): {violations[:5]}"
        )


def _check_manifest(
    result: ValidationResult,
    manifest: dict[str, object],
    node_rows: list[dict[str, object]],
    edge_rows: list[dict[str, object]],
) -> None:
    """Kunci wajib `manifest.json` dan kecocokannya dengan berkas CSV."""
    result.ran("kunci manifest.json §5.3 dan kecocokan hitungan")
    required = ("seed", "generated_at", "generator_version", "counts", "params")
    missing = [key for key in required if key not in manifest]
    if missing:
        result.error(f"manifest.json kekurangan kunci wajib: {missing}")

    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        result.error("manifest.counts bukan objek")
        return

    illicit = sum(1 for row in node_rows if str(row["gt_illicit"]) == "1")
    for key, actual in (
        ("nodes", len(node_rows)),
        ("edges", len(edge_rows)),
        ("illicit_nodes", illicit),
    ):
        if key not in counts:
            result.error(f"manifest.counts kekurangan '{key}'")
        elif int(counts[key]) != actual:
            result.error(
                f"manifest.counts.{key}={counts[key]} tidak sama dengan "
                f"isi berkas ({actual})"
            )


def _read_csv(path: Path) -> list[dict[str, object]]:
    """Baca CSV sebagai daftar dict yang mempertahankan urutan kolom."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _params_from_manifest(manifest: dict[str, object]) -> GeneratorParams:
    """Bangun `GeneratorParams` dari `manifest.params` untuk mode berkas.

    Kunci yang tidak dikenal diabaikan supaya manifest dari versi generator yang
    berbeda tetap bisa divalidasi; kunci diagnostik yang ditambahkan `build.py`
    (`split_diagnostics`, `noise`) juga tersaring di sini.

    Distribusi ber-NamedTuple tidak direkonstruksi — di manifest ia tersimpan
    sebagai objek dan nilai bawaannya dipakai. Tidak masalah: cek di modul ini
    hanya memerlukan parameter rentang, ambang persentil, dan porsi noise.
    """
    raw = manifest.get("params")
    if not isinstance(raw, dict):
        return GeneratorParams()

    valid = {item.name for item in dataclasses.fields(GeneratorParams)}
    kwargs: dict[str, object] = {}
    for key, value in raw.items():
        if key not in valid:
            continue
        current = getattr(GeneratorParams(), key)
        if isinstance(current, tuple) and isinstance(value, list):
            kwargs[key] = tuple(value)
        elif isinstance(current, dict) and isinstance(value, dict):
            kwargs[key] = value
        elif isinstance(current, (int, float, str)) and isinstance(
            value, (int, float, str)
        ):
            kwargs[key] = type(current)(value)
    try:
        return GeneratorParams(**kwargs)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return GeneratorParams()
