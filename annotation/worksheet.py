"""Penyusun lembar kerja anotator.

Menghasilkan satu paket per anotator: berkas Markdown yang bisa dibaca langsung
plus berkas CSV untuk diisi. Semuanya mandiri — anotator tidak perlu membuka
`nodes.csv` atau `edges.csv` sama sekali, sehingga tidak ada alasan menyentuh
berkas yang memuat kolom jawaban.

**Yang sengaja TIDAK ditampilkan:**

- `rule_score`, `rule_level`, `triggered_rules` — skor rule dipakai untuk
  *memilih* node, bukan untuk ditunjukkan. Menampilkannya akan mengubah anotasi
  manusia menjadi persetujuan atas rule engine, dan kesepakatan antar-anotator
  akan mengukur kepatuhan pada rule alih-alih penilaian mandiri.
- Seluruh kolom `gt_*`.
- **Nama strata.** Ini yang paling mudah terlewat: menulis "membidik wilayah
  hard negative" di lembar kerja sama saja dengan membocorkan jawaban. Strata
  hanya ada di manifest koordinator.

Urutan tampilan diacak berbeda untuk tiap anotator — item sama, urutan beda —
agar efek kelelahan tidak menghantam node yang sama pada ketiganya. Kappa tidak
terpengaruh karena himpunan itemnya identik.
"""

from __future__ import annotations

import csv
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from annotation.sampling import AnnotationSample
from rules.graph import RuleGraph
from rules.loader import RuleNode

#: Kolom berkas jawaban. `note` bukan bagian kontrak kolom yang digabungkan
#: dan dibuang saat penggabungan; ia dipertahankan sebagai bahan kutipan
#: kualitatif.
ANSWER_COLUMNS: tuple[str, ...] = (
    "node_id",
    "annotator_id",
    "label",
    "confidence",
    "annotated_at",
    "note",
)

#: Nama tipe node dalam bahasa manusia.
TYPE_NAMES: dict[str, str] = {
    "domain": "domain / situs",
    "phone": "nomor kontak",
    "bank_account": "rekening bank",
    "ewallet": "e-wallet / merchant QRIS",
    "apk": "aplikasi (APK)",
    "social_account": "akun media sosial",
    "report": "laporan masuk",
    "victim": "korban / pelapor",
}

#: Nama relasi dalam bahasa manusia, per arah.
REL_NAMES: dict[str, str] = {
    "promotes": "mempromosikan",
    "contacts": "memakai kontak",
    "uses_account": "memakai rekening",
    "transferred_to": "mengirim dana ke",
    "mentions": "menyebut",
    "reported": "melaporkan",
    "linked_to_apk": "menautkan APK",
    "redirects_to": "mengalihkan ke",
}

#: Batas jumlah tetangga yang ditampilkan per node.
MAX_NEIGHBORS_SHOWN: int = 12

#: Tipe yang punya `feat_kw_score` bermakna.
CONTENT_TYPES: frozenset[str] = frozenset({"domain", "social_account", "apk"})

#: Tipe yang punya `feat_txn_*` bermakna.
FINANCIAL_TYPES: frozenset[str] = frozenset({"bank_account", "ewallet", "victim"})


@dataclass
class Percentiles:
    """Posisi relatif sebuah nilai di dalam populasi tipe node yang sama.

    Ditampilkan agar anotator punya patokan: "412 transaksi" tidak bermakna
    tanpa tahu itu tinggi atau biasa untuk tipe tersebut.
    """

    by_type: dict[tuple[str, str], list[float]]

    @classmethod
    def build(cls, nodes: list[RuleNode]) -> Percentiles:
        fields = (
            "feat_txn_count",
            "feat_txn_amount_sum",
            "mean_ticket",
            "feat_report_count",
            "feat_kw_score",
            "feat_age_days",
            "degree_total",
        )
        table: dict[tuple[str, str], list[float]] = {}
        for node in nodes:
            for field_name in fields:
                value = float(getattr(node, field_name))
                # Nilai transaksi hanya dibandingkan dengan node yang memang
                # bertransaksi; kalau tidak, seluruh node nol akan menggeser
                # persentilnya menjadi tak bermakna.
                if field_name in ("feat_txn_count", "feat_txn_amount_sum", "mean_ticket"):
                    if node.feat_txn_count <= 0:
                        continue
                table.setdefault((node.node_type, field_name), []).append(value)
        for values in table.values():
            values.sort()
        return cls(by_type=table)

    def rank(self, node: RuleNode, field_name: str) -> float | None:
        """Persentil sebuah nilai, atau None bila populasinya tidak ada."""
        values = self.by_type.get((node.node_type, field_name))
        if not values:
            return None
        value = float(getattr(node, field_name))
        position = float(np.searchsorted(values, value, side="right"))
        return position / len(values) * 100.0

    def size(self, node_type: str, field_name: str) -> int:
        return len(self.by_type.get((node_type, field_name), ()))


def _bar(percentile: float | None, width: int = 10) -> str:
    """Bilah teks sederhana untuk persentil."""
    if percentile is None:
        return " " * width
    filled = int(round(percentile / 100.0 * width))
    return "▓" * filled + "░" * (width - filled)


def _rupiah(value: float) -> str:
    return f"Rp {value:,.0f}".replace(",", ".")


def _attribute_lines(
    node: RuleNode, percentiles: Percentiles
) -> list[str]:
    """Baris atribut node, hanya yang bermakna untuk tipenya."""
    lines: list[str] = []

    def row(label: str, value: str, field_name: str | None = None) -> None:
        if field_name is None:
            lines.append(f"    {label:<24} {value}")
            return
        rank = percentiles.rank(node, field_name)
        if rank is None:
            lines.append(f"    {label:<24} {value}")
            return
        lines.append(
            f"    {label:<24} {value:<18} {_bar(rank)}  persentil {rank:>3.0f}"
        )

    if node.node_type == "ewallet":
        row("Merchant QRIS", "ya" if node.feat_is_qris else "tidak")

    if node.node_type in FINANCIAL_TYPES:
        if node.feat_txn_count > 0:
            row("Jumlah transaksi", f"{node.feat_txn_count:,.0f}", "feat_txn_count")
            row("Total nominal", _rupiah(node.feat_txn_amount_sum))
            row("Nominal rata-rata", _rupiah(node.mean_ticket), "mean_ticket")
        else:
            row("Jumlah transaksi", "0")
    else:
        row("Jumlah transaksi", "—  (tidak berlaku untuk tipe ini)")

    if node.node_type in CONTENT_TYPES:
        row("Skor kata kunci promo", f"{node.feat_kw_score:.2f}", "feat_kw_score")
    else:
        row("Skor kata kunci promo", "—  (tidak berlaku untuk tipe ini)")

    row("Disebut laporan", f"{node.feat_report_count:,.0f}", "feat_report_count")
    row("Derajat masuk / keluar", f"{node.feat_degree_in:.0f} / {node.feat_degree_out:.0f}")
    return lines


def _neighbor_summary(graph: RuleGraph, neighbor: RuleNode) -> str:
    """Ringkasan singkat satu node tetangga, sesuai tipenya."""
    parts: list[str] = []
    if neighbor.node_type == "domain":
        phones = graph.targets(neighbor.node_id, "contacts", node_type="phone")
        parts.append(f"kw {neighbor.feat_kw_score:.2f}")
        parts.append(f"umur {neighbor.feat_age_days:.0f}h")
        if phones:
            parts.append(f"{len(phones)} nomor kontak")
    elif neighbor.node_type == "phone":
        domains = graph.sources(neighbor.node_id, "contacts", node_type="domain")
        parts.append(f"kontak bagi {len(domains)} domain")
        parts.append(f"umur {neighbor.feat_age_days:.0f}h")
    elif neighbor.node_type in ("bank_account", "ewallet"):
        if neighbor.feat_is_qris:
            parts.append("QRIS")
        if neighbor.feat_txn_count > 0:
            parts.append(f"txn {neighbor.feat_txn_count:.0f}")
            parts.append(f"tiket {_rupiah(neighbor.mean_ticket)}")
        else:
            parts.append("tanpa transaksi")
    elif neighbor.node_type == "apk":
        parts.append(f"kw {neighbor.feat_kw_score:.2f}")
        parts.append(f"umur {neighbor.feat_age_days:.0f}h")
    elif neighbor.node_type == "social_account":
        promoted = graph.targets(neighbor.node_id, "promotes")
        parts.append(f"kw {neighbor.feat_kw_score:.2f}")
        parts.append(f"mempromosikan {len(promoted)}")
    elif neighbor.node_type == "victim":
        parts.append(f"{neighbor.feat_txn_count:.0f} transaksi")
    elif neighbor.node_type == "report":
        mentioned = graph.targets(neighbor.node_id, "mentions")
        parts.append(f"menyebut {len(mentioned)} entitas")
    if neighbor.feat_report_count > 0:
        parts.append(f"disebut {neighbor.feat_report_count:.0f} laporan")
    return " · ".join(parts)


def _neighbor_lines(graph: RuleGraph, node_id: str) -> list[str]:
    """Baris tetangga, terkuat lebih dulu."""
    entries: list[tuple[float, str]] = []

    for edge in graph.in_edges(node_id):
        other = graph.nodes.get(edge.src_id)
        if other is None:
            continue
        entries.append(
            (
                edge.weight,
                f"    ← {REL_NAMES.get(edge.rel_type, edge.rel_type):<16} "
                f"{other.node_id:<22} w {edge.weight:.2f}   "
                f"{_neighbor_summary(graph, other)}",
            )
        )
    for edge in graph.out_edges(node_id):
        other = graph.nodes.get(edge.dst_id)
        if other is None:
            continue
        entries.append(
            (
                edge.weight,
                f"    → {REL_NAMES.get(edge.rel_type, edge.rel_type):<16} "
                f"{other.node_id:<22} w {edge.weight:.2f}   "
                f"{_neighbor_summary(graph, other)}",
            )
        )

    entries.sort(key=lambda item: -item[0])
    lines = [text for _, text in entries[:MAX_NEIGHBORS_SHOWN]]
    if len(entries) > MAX_NEIGHBORS_SHOWN:
        lines.append(
            f"    ... {len(entries) - MAX_NEIGHBORS_SHOWN} tetangga lain "
            f"(bobot lebih rendah)"
        )
    if not lines:
        lines.append("    (tidak ada tetangga)")
    return lines


def render_node(
    graph: RuleGraph,
    node_id: str,
    percentiles: Percentiles,
    position: int,
    total: int,
) -> str:
    """Satu blok tampilan untuk satu node."""
    node = graph.nodes[node_id]
    rule = "═" * 72
    thin = "─" * 72

    header = [
        rule,
        f"  [ {position} / {total} ]   {node.node_id}",
        rule,
        "",
        f"  Tipe              {TYPE_NAMES.get(node.node_type, node.node_type)}",
        f"  Pertama terlihat  {node.first_seen_at.date()}"
        f"        Terakhir  {node.last_seen_at.date()}",
        f"  Umur              {node.feat_age_days:.0f} hari",
        "",
        f"  ATRIBUT{'':<36}posisi di antara node tipe sama",
    ]
    neighbor_count = graph.degree(node_id)
    body = [
        "",
        f"  TETANGGA ({neighbor_count})",
    ]
    footer = [
        "",
        thin,
        "  Apakah node ini bagian dari jaringan ilegal?",
        "",
        "    label       [ ]   0 = tidak   1 = ya",
        "    confidence  [ ]   0,0 (menebak)  …  1,0 (yakin sekali)",
        "    catatan     [                                                    ]",
        rule,
        "",
    ]

    lines = (
        header
        + _attribute_lines(node, percentiles)
        + body
        + _neighbor_lines(graph, node_id)
        + footer
    )
    return "\n".join(lines)


def _instructions(annotator_id: str, total: int) -> str:
    """Bagian pembuka lembar kerja."""
    return "\n".join(
        [
            f"# Lembar Kerja Anotasi — anotator {annotator_id}",
            "",
            f"{total} node. Perkiraan waktu 60–90 menit.",
            "",
            "## Pertanyaan yang dijawab",
            "",
            "Untuk tiap node: **apakah entitas ini bagian dari jaringan judi online",
            "atau pinjaman online ilegal?**",
            "",
            "- `label` — `1` bila menurut Anda ya, `0` bila tidak.",
            "- `confidence` — seberapa yakin, `0,0` sampai `1,0`. Tebakan murni",
            "  berarti `0,0`; yakin sekali berarti `1,0`. **Jangan** memaksa diri",
            "  yakin: confidence rendah adalah jawaban yang sah dan berguna.",
            "- `catatan` — opsional, satu kalimat alasan bila ada yang menarik.",
            "",
            "## Cara mengisi",
            "",
            f"Isi berkas `answers_{annotator_id}.csv`. Urutan barisnya sama dengan",
            "urutan node di lembar ini, jadi bisa dikerjakan dari atas ke bawah.",
            "",
            "## Aturan kerja",
            "",
            "1. **Bekerja sendiri.** Jangan berdiskusi dengan anotator lain sampai",
            "   ketiga berkas jawaban selesai. Perbandingan dilakukan setelahnya, dan",
            "   nilai kesepakatan antar-anotator hanya bermakna bila ketiganya menilai",
            "   secara mandiri.",
            "2. **Jangan membuka berkas lain** di folder data — khususnya `nodes.csv`",
            "   dan `weak_labels.csv`. Lembar ini sudah memuat seluruh bukti yang",
            "   dibutuhkan. Keduanya memuat informasi yang akan membatalkan nilai",
            "   anotasi Anda.",
            "3. **Tidak ada jawaban yang dianggap benar di muka.** Sebagian node memang",
            "   dibuat ambigu. Kalau ragu, jawab sesuai dugaan terbaik dan turunkan",
            "   confidence-nya.",
            "",
            "## Cara membaca tampilan",
            "",
            "- **persentil** menunjukkan posisi nilai itu di antara node bertipe sama.",
            "  Persentil 90 berarti lebih tinggi dari 90% node sejenis.",
            "- **w** pada baris tetangga adalah kekuatan bukti tautan, 0 sampai 1.",
            "- **←** berarti node lain mengarah ke node yang dinilai;",
            "  **→** berarti node yang dinilai mengarah ke node lain.",
            "- **kw** adalah skor kemiripan kata kunci promosi, 0 sampai 1.",
            "- Atribut bertanda `—` tidak berlaku untuk tipe node tersebut.",
            "",
            "---",
            "",
            "```text",
        ]
    )


def write_worksheet(
    directory: Path,
    graph: RuleGraph,
    sample: AnnotationSample,
    annotator_id: str,
    order: list[str],
) -> tuple[Path, Path]:
    """Tulis lembar kerja Markdown dan berkas jawaban untuk satu anotator."""
    percentiles = Percentiles.build(list(graph.nodes.values()))
    total = len(order)

    blocks = [
        render_node(graph, node_id, percentiles, position, total)
        for position, node_id in enumerate(order, start=1)
    ]
    text = _instructions(annotator_id, total) + "\n" + "\n".join(blocks) + "```\n"

    worksheet_path = directory / f"worksheet_{annotator_id}.md"
    worksheet_path.write_text(text, encoding="utf-8")

    answers_path = directory / f"answers_{annotator_id}.csv"
    with answers_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(ANSWER_COLUMNS), lineterminator="\n"
        )
        writer.writeheader()
        for node_id in order:
            writer.writerow(
                {
                    "node_id": node_id,
                    "annotator_id": annotator_id,
                    "label": "",
                    "confidence": "",
                    "annotated_at": "",
                    "note": "",
                }
            )
    return worksheet_path, answers_path


def annotator_order(
    sample: AnnotationSample,
    annotator_id: str,
    annotators: tuple[str, ...],
) -> list[str]:
    """Urutan tampilan untuk satu anotator — teracak, berbeda untuk tiap orang.

    **Tidak seorang pun anotator memakai `annotation_order`.** Urutan itu
    bergilir antar strata, sehingga node pada posisi 1, 7, 13, ... semuanya
    berasal dari strata yang sama. Anotator yang menyadari polanya bisa
    menyimpulkan strata dari posisi, dan strata adalah petunjuk jawaban untuk
    sebagian node. `annotation_order` hanya hidup di manifest koordinator, dan
    ablasi A5 memakainya di sisi model — urutan tampilan tidak ada hubungannya
    dengan itu.

    Urutan berbeda per anotator juga menjaga agar efek kelelahan tidak
    menghantam node yang sama pada ketiganya. Himpunan itemnya identik, jadi
    kappa tidak terpengaruh.
    """
    base = sorted(sample.node_ids)
    # crc32, bukan hash() bawaan: hash string diacak ulang setiap proses Python
    # (PYTHONHASHSEED), sehingga urutan lembar kerja tidak akan bisa direproduksi.
    seed = zlib.crc32(annotator_id.encode("utf-8"))
    rng = np.random.default_rng(seed)
    return [base[int(index)] for index in rng.permutation(len(base))]
