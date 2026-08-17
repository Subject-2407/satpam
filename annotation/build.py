"""Orkestrator alat anotasi.

Pemakaian:

    python -m annotation.build sample --seed 42
    python -m annotation.build merge  --seed 42
    python -m annotation.build merge  --seed 42 --rounds anotasi_ronde1 anotasi_ronde2

`sample` menyiapkan paket kerja untuk tiga anotator. `merge` menggabungkan
jawaban menjadi `human_annotations.csv` (lihat generator/schema.py untuk kolom
lengkapnya) plus laporan kesepakatan.

Keluaran `sample` di `data/synthetic/seed_{N}/anotasi_ronde1/`:

    worksheet_A1.md      answers_A1.csv        <- diberikan ke anotator
    worksheet_A2.md      answers_A2.csv
    worksheet_A3.md      answers_A3.csv
    sample_manifest.json                       <- KOORDINATOR SAJA, memuat strata

Keluaran `merge` di `data/synthetic/seed_{N}/`:

    human_annotations.csv            <- kontrak beku, satu baris per penilaian
    human_annotations_majority.csv   <- turunan, bukan kontrak
    agreement_report.md              <- turunan, bukan kontrak
    sample_manifest_merged.json      <- turunan, hanya bila ronde lebih dari satu

---

**Anotasi lebih dari satu ronde.** `--rounds` menerima beberapa subdirektori
sekaligus dan menggabungkannya menjadi satu berkas kontrak. Ini bukan
kemewahan: tanpa itu, menjalankan `merge --subdir anotasi_ronde2` akan menulis
ulang `human_annotations.csv` dengan jawaban ronde kedua saja dan **menghapus
hasil ronde pertama**.

Dua hal yang ditolak mentah-mentah, karena keduanya membuat angka kesepakatan
kehilangan arti:

- **node yang sama muncul di dua ronde**, suara terbanyaknya akan mencampur dua
  penilaian yang dilakukan dengan panduan berbeda
- **daftar anotator berbeda antar-ronde**, Fleiss' kappa mensyaratkan jumlah
  rater yang sama, dan suara terbanyak berubah makna bila jumlah pemilihnya
  berubah

Kesepakatan dilaporkan **per ronde**, bukan atas gabungannya. Kappa gabungan
mencampur mutu anotasi sebelum dan sesudah kalibrasi menjadi satu angka yang
tidak dapat ditafsirkan sebagai apa pun.

Modul ini tidak mengimpor apa pun dari `generator/` dan tidak membaca kolom
jawaban.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from annotation.agreement import (
    BOOTSTRAP_REPEATS,
    AgreementResult,
    bootstrap_kappa_ci,
    compute_agreement,
    interpret,
    majority_label,
)
from annotation.sampling import (
    ANNOTATABLE_NODE_TYPES,
    DEFAULT_SAMPLING_SEED,
    STRATA_LABELS,
    STRATA_ORDER,
    AnnotationSample,
    build_sample,
    read_weak_labels,
)
from annotation.debrief import write_debrief
from annotation.webform import write_webform
from annotation.worksheet import ANSWER_COLUMNS, annotator_order, write_worksheet
from rules.graph import RuleGraph
from rules.loader import load_edges, load_nodes

#: Kolom `human_annotations.csv`, urut.
HUMAN_ANNOTATIONS_COLUMNS: tuple[str, ...] = (
    "node_id",
    "annotator_id",
    "label",
    "confidence",
    "annotated_at",
)

DEFAULT_DATA_ROOT = Path("data/synthetic")
DEFAULT_ANNOTATORS: tuple[str, ...] = ("A1", "A2", "A3")
DEFAULT_TOTAL = 150


def _seed_dir(data_root: Path, seed: int) -> Path:
    return data_root / f"seed_{seed}"


def _load_graph(seed_dir: Path) -> RuleGraph:
    return RuleGraph.build(
        load_nodes(seed_dir / "nodes.csv"), load_edges(seed_dir / "edges.csv")
    )


# ---------------------------------------------------------------------------
# Perintah: sample
# ---------------------------------------------------------------------------


def _already_annotated(seed_dir: Path) -> frozenset[str]:
    """Node yang sudah pernah masuk sampel ronde mana pun pada seed ini.

    Dikumpulkan dari seluruh `sample_manifest.json` di bawah direktori seed,
    sehingga ronde ketiga otomatis menghindari node ronde pertama dan kedua
    tanpa perlu daftar yang dipelihara tangan.
    """
    seen: set[str] = set()
    for manifest in sorted(seed_dir.glob("*/sample_manifest.json")):
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for entry in payload.get("nodes", ()):
            node_id = entry.get("node_id") if isinstance(entry, dict) else entry
            if node_id:
                seen.add(str(node_id))
    return frozenset(seen)


def _filled_answer_files(
    output_dir: Path, annotators: tuple[str, ...]
) -> list[tuple[Path, int]]:
    """Berkas jawaban yang sudah memuat label, beserta jumlah barisnya.

    `write_worksheet` menulis `answers_{ID}.csv` dalam keadaan kosong, jadi
    menjalankan `sample` dua kali akan menghapus hasil anotasi yang sudah jadi.
    Pernah nyaris terjadi, dan sisa `.bak` di direktori seed 42 adalah jejaknya.
    """
    terisi: list[tuple[Path, int]] = []
    for annotator_id in annotators:
        path = output_dir / f"answers_{annotator_id}.csv"
        if not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            rows = [
                row for row in csv.DictReader(handle)
                if (row.get("label") or "").strip()
            ]
        if rows:
            terisi.append((path, len(rows)))
    return terisi


def command_sample(args: argparse.Namespace) -> int:
    seed_dir = _seed_dir(args.data_root, args.seed)
    for name in ("nodes.csv", "edges.csv", "weak_labels.csv"):
        if not (seed_dir / name).is_file():
            print(f"berkas wajib belum ada: {seed_dir / name}")
            return 1

    graph = _load_graph(seed_dir)
    weak_labels = read_weak_labels(seed_dir / "weak_labels.csv")
    sudah = _already_annotated(seed_dir)
    exclude = sudah if getattr(args, "exclude_annotated", False) else frozenset()
    if exclude:
        print(f"  {len(exclude)} node dari ronde sebelumnya dikeluarkan dari kolam")
    sample = build_sample(
        graph,
        weak_labels,
        total=args.total,
        sampling_seed=args.sampling_seed,
        exclude=exclude,
    )

    output_dir = seed_dir / getattr(args, "subdir", "anotasi_ronde1")
    output_dir.mkdir(parents=True, exist_ok=True)

    annotators = tuple(args.annotators)
    terisi = _filled_answer_files(output_dir, annotators)
    if terisi and not getattr(args, "force", False):
        print("\nberkas jawaban berikut sudah terisi dan akan tertimpa:")
        for path, jumlah in terisi:
            print(f"  {path.name}: {jumlah} baris berlabel")
        print(
            "\nPerintah dibatalkan. `sample` menulis ulang answers_{ID}.csv "
            "dalam keadaan kosong,\nsehingga menjalankannya di atas hasil "
            "anotasi yang sudah jadi akan menghapusnya.\n"
            "Salin dulu hasilnya ke tempat lain, atau jalankan dengan --force "
            "bila memang itu yang diinginkan."
        )
        return 1

    for annotator_id in annotators:
        order = annotator_order(sample, annotator_id, annotators)
        worksheet, answers = write_worksheet(
            output_dir, graph, sample, annotator_id, order
        )
        # Berkas Markdown tetap ditulis sebagai cadangan bila peramban tidak
        # tersedia. Berkas HTML yang dipakai sehari-hari, karena di situ aturan
        # instrumennya ditegakkan mesin dan bukan sekadar tertulis di panduan.
        form = write_webform(output_dir, graph, sample, annotator_id, order)
        print(f"  {annotator_id}: {form.name}, {worksheet.name}, {answers.name}")

    manifest_path = output_dir / "sample_manifest.json"
    manifest_path.write_text(
        json.dumps(_sample_manifest(args, sample, annotators), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    print()
    print(f"  {len(sample.node_ids)} node, {len(annotators)} anotator "
          f"-> {len(sample.node_ids) * len(annotators)} penilaian")
    print(f"{'strata':7} {'kandidat':>9} {'diambil':>8}  keterangan")
    grouped = sample.by_stratum()
    for name in STRATA_ORDER:
        print(
            f"{name:7} {sample.pool_sizes[name]:>9} {len(grouped[name]):>8}  "
            f"{STRATA_LABELS[name]}"
        )
    for note in sample.notes:
        print(f"  catatan: {note}")
    print()
    print(f"  manifest koordinator: {manifest_path.name}  "
          f"(JANGAN diberikan ke anotator — memuat strata)")
    return 0


def _sample_manifest(
    args: argparse.Namespace,
    sample: AnnotationSample,
    annotators: tuple[str, ...],
) -> dict[str, object]:
    """Manifest koordinator: strata, urutan A5, dan sinyal pemilihan.

    **Bukan** untuk diberikan ke anotator. Nama strata di sini setara petunjuk
    jawaban untuk sebagian node.
    """
    return {
        "seed": args.seed,
        "sampling_seed": args.sampling_seed,
        "total": len(sample.node_ids),
        "annotators": list(annotators),
        "annotatable_node_types": list(ANNOTATABLE_NODE_TYPES),
        "strata_labels": STRATA_LABELS,
        "pool_sizes": sample.pool_sizes,
        "target_sizes": sample.target_sizes,
        "notes": list(sample.notes),
        "a5_prefix_note": (
            "annotation_order bergilir antar strata dengan skor rule menurun di "
            "dalam strata, sehingga prefiks 10/25/50/100/150 untuk ablasi A5 "
            "tetap berimbang strata dan tidak kosong dari positif"
        ),
        "nodes": [
            {
                "node_id": node_id,
                "stratum": sample.stratum_of[node_id],
                "annotation_order": sample.order_of[node_id],
                "node_type": sample.signals[node_id].node_type,
                "rule_score": sample.signals[node_id].rule_score,
                "rule_level": sample.signals[node_id].rule_level,
                "own_matches": sample.signals[node_id].own_matches,
                "neighbor_own_matches": sample.signals[node_id].neighbor_own_matches,
                "degree": sample.signals[node_id].degree,
            }
            for node_id in sample.ordered()
        ],
    }


# ---------------------------------------------------------------------------
# Perintah: merge
# ---------------------------------------------------------------------------


def command_debrief(args: argparse.Namespace) -> int:
    """Lembar bandingan tiga jawaban, untuk diskusi pasca-ronde kalibrasi."""
    seed_dir = _seed_dir(args.data_root, args.seed)
    directory = seed_dir / getattr(args, "subdir", "anotasi_ronde1")
    manifest_path = directory / "sample_manifest.json"
    if not manifest_path.is_file():
        print(f"manifest belum ada: {manifest_path}")
        return 1

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    node_ids = [
        entry.get("node_id") if isinstance(entry, dict) else entry
        for entry in payload.get("nodes", ())
    ]
    graph = _load_graph(seed_dir)
    try:
        path = write_debrief(directory, graph, node_ids, tuple(args.annotators))
    except FileNotFoundError as exc:
        print(exc)
        return 1

    print(f"  {path}")
    print("  Node yang diperselisihkan diletakkan paling atas.")
    print("  Tidak memuat kolom `gt_*` maupun skor rule.")
    return 0


@dataclass
class Round:
    """Satu ronde anotasi yang sudah dibaca dan divalidasi."""

    name: str
    directory: Path
    manifest: dict
    annotators: tuple[str, ...]
    stratum_of: dict[str, str]
    filled: dict[str, list[dict[str, str]]]
    result: AgreementResult
    kappa_ci: tuple[float, float]

    @property
    def n_ratings(self) -> int:
        return sum(len(rows) for rows in self.filled.values())


def _rounds_requested(args: argparse.Namespace) -> tuple[str, ...]:
    """Subdirektori ronde yang diminta, urut sebagaimana ditulis pengguna."""
    rounds = getattr(args, "rounds", None)
    if rounds:
        return tuple(rounds)
    return (getattr(args, "subdir", "anotasi_ronde1"),)


def _read_round(seed_dir: Path, name: str) -> tuple[Round | None, list[str]]:
    """Baca satu ronde. Mengembalikan `None` bila ada masalah."""
    directory = seed_dir / name
    manifest_path = directory / "sample_manifest.json"
    if not manifest_path.is_file():
        return None, [f"{name}/sample_manifest.json belum ada — jalankan `sample` lebih dulu"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    annotators = tuple(manifest["annotators"])
    stratum_of = {row["node_id"]: row["stratum"] for row in manifest["nodes"]}
    expected = set(stratum_of)

    problems: list[str] = []
    filled: dict[str, list[dict[str, str]]] = {}
    for annotator_id in annotators:
        path = directory / f"answers_{annotator_id}.csv"
        if not path.is_file():
            problems.append(f"{name}/{path.name} belum ada")
            continue
        rows, issues = _read_answers(path, annotator_id, expected)
        problems.extend(f"{name}/{issue}" for issue in issues)
        filled[annotator_id] = rows

    if problems:
        return None, problems

    labels = {
        annotator_id: {row["node_id"]: int(row["label"]) for row in rows}
        for annotator_id, rows in filled.items()
    }
    result = compute_agreement(labels, stratum_of=stratum_of)
    return (
        Round(
            name=name,
            directory=directory,
            manifest=manifest,
            annotators=annotators,
            stratum_of=stratum_of,
            filled=filled,
            result=result,
            kappa_ci=bootstrap_kappa_ci(labels),
        ),
        [],
    )


def _cross_round_problems(rounds: list[Round]) -> list[str]:
    """Pemeriksaan yang hanya bisa dilakukan setelah seluruh ronde terbaca."""
    problems: list[str] = []
    reference = rounds[0]
    for other in rounds[1:]:
        if other.annotators != reference.annotators:
            problems.append(
                f"daftar anotator ronde '{other.name}' {list(other.annotators)} berbeda "
                f"dari ronde '{reference.name}' {list(reference.annotators)}; "
                "Fleiss' kappa dan suara terbanyak menuntut jumlah rater yang sama"
            )

    asal: dict[str, str] = {}
    bentrok: list[str] = []
    for rnd in rounds:
        for node_id in rnd.stratum_of:
            if node_id in asal:
                bentrok.append(f"{node_id} (ronde '{asal[node_id]}' dan '{rnd.name}')")
            else:
                asal[node_id] = rnd.name
    if bentrok:
        problems.append(
            f"{len(bentrok)} node dinilai di lebih dari satu ronde: "
            f"{'; '.join(bentrok[:5])}"
            + (" ..." if len(bentrok) > 5 else "")
        )
        problems.append(
            "  Suara terbanyaknya akan mencampur penilaian dari dua panduan yang "
            "berbeda. Pakai `sample --exclude-annotated` saat menyiapkan ronde "
            "lanjutan agar kolamnya tidak beririsan."
        )
    return problems


def command_merge(args: argparse.Namespace) -> int:
    seed_dir = _seed_dir(args.data_root, args.seed)
    round_names = _rounds_requested(args)

    ganda = sorted({name for name in round_names if round_names.count(name) > 1})
    if ganda:
        print(f"ronde disebut lebih dari sekali: {', '.join(ganda)}")
        return 1

    rounds: list[Round] = []
    problems: list[str] = []
    for name in round_names:
        rnd, issues = _read_round(seed_dir, name)
        problems.extend(issues)
        if rnd is not None:
            rounds.append(rnd)

    if problems:
        print("Penggabungan dibatalkan — jawaban belum siap:")
        for issue in problems:
            print(f"  {issue}")
        print()
        print("Seluruh berkas jawaban harus lengkap sebelum digabungkan. Nilai")
        print("kesepakatan hanya bermakna bila setiap anotator menilai secara mandiri.")
        return 1

    problems = _cross_round_problems(rounds)
    if problems:
        print("Penggabungan dibatalkan — ronde tidak dapat disatukan:")
        for issue in problems:
            print(f"  {issue}")
        return 1

    annotators = rounds[0].annotators
    contract_path = _write_human_annotations(seed_dir, rounds, annotators)
    majority_path = _write_majority(
        seed_dir / "human_annotations_majority.csv", rounds, annotators
    )
    report_path = _write_report(seed_dir, rounds, annotators)

    n_ratings = sum(rnd.n_ratings for rnd in rounds)
    n_nodes = sum(len(rnd.stratum_of) for rnd in rounds)
    print(f"  {contract_path.name}   {n_ratings} baris (kontrak)")
    print(f"  {majority_path.name}   turunan, bukan kontrak")
    print(f"  {report_path.name}   turunan, bukan kontrak")
    if len(rounds) > 1:
        merged_path = _write_merged_manifest(seed_dir, rounds)
        print(f"  {merged_path.name}   turunan, urutan A5 gabungan")
        for rnd in rounds:
            per_round = _write_majority(
                seed_dir / f"human_annotations_majority_{rnd.name}.csv",
                [rnd],
                annotators,
            )
            print(f"  {per_round.name}   turunan, satu ronde saja")
    print()
    print(f"  {n_nodes} node dari {len(rounds)} ronde: "
          f"{', '.join(rnd.name for rnd in rounds)}")
    print()

    for rnd in rounds:
        result = rnd.result
        awal = f"{rnd.name} " if len(rounds) > 1 else ""
        print(f"  {awal}Fleiss' kappa      {result.fleiss_kappa:.3f}  "
              f"({interpret(result.fleiss_kappa)})  "
              f"CI95 [{rnd.kappa_ci[0]:.3f}, {rnd.kappa_ci[1]:.3f}]")
        print(f"  {awal}kesepakatan mentah {result.percent_agreement:.3f}  "
              f"({result.unanimous}/{result.n_items} bulat)")
        for pair, value in result.pairwise_cohen.items():
            print(f"  {awal}Cohen {pair:8}     {value:.3f}")
        if len(rounds) > 1:
            print()

    if len(rounds) > 1:
        print("  Kesepakatan sengaja dilaporkan per ronde. Kappa atas gabungan")
        print("  mencampur mutu anotasi antar-ronde dan tidak dapat ditafsirkan.")
    return 0


def _read_answers(
    path: Path,
    annotator_id: str,
    expected: set[str],
) -> tuple[list[dict[str, str]], list[str]]:
    """Baca dan validasi satu berkas jawaban."""
    issues: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    seen: set[str] = set()
    clean: list[dict[str, str]] = []
    for number, row in enumerate(rows, start=2):
        node_id = (row.get("node_id") or "").strip()
        label = (row.get("label") or "").strip()
        confidence = (row.get("confidence") or "").strip()

        if not node_id:
            issues.append(f"{path.name}:{number} node_id kosong")
            continue
        if node_id in seen:
            issues.append(f"{path.name}:{number} node_id ganda: {node_id}")
        seen.add(node_id)
        if label not in ("0", "1"):
            issues.append(
                f"{path.name}:{number} label harus 0 atau 1, dapat {label!r} ({node_id})"
            )
            continue
        try:
            value = float(confidence.replace(",", "."))
        except ValueError:
            issues.append(
                f"{path.name}:{number} confidence tidak bisa dibaca: "
                f"{confidence!r} ({node_id})"
            )
            continue
        if not 0.0 <= value <= 1.0:
            issues.append(
                f"{path.name}:{number} confidence harus di 0..1, dapat {value} ({node_id})"
            )
            continue

        clean.append(
            {
                "node_id": node_id,
                "annotator_id": (row.get("annotator_id") or annotator_id).strip()
                or annotator_id,
                "label": label,
                "confidence": f"{value:.2f}",
                "annotated_at": (row.get("annotated_at") or "").strip(),
                "note": (row.get("note") or "").strip(),
            }
        )

    missing = expected - seen
    if missing:
        issues.append(
            f"{path.name} belum lengkap: {len(missing)} node belum dinilai "
            f"(contoh {sorted(missing)[:3]})"
        )
    unknown = seen - expected
    if unknown:
        issues.append(
            f"{path.name} memuat node di luar sampel: {sorted(unknown)[:3]}"
        )
    return clean, issues


def _fallback_timestamp(path: Path) -> str:
    """Waktu untuk `annotated_at` yang dibiarkan kosong anotator.

    Memakai waktu ubah terakhir berkas jawaban — nilai provenance yang nyata,
    dan jauh lebih baik daripada meminta orang menulis ISO8601 seratus lima
    puluh kali.
    """
    stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return stamp.astimezone().replace(microsecond=0).isoformat()


def _write_human_annotations(
    seed_dir: Path,
    rounds: list[Round],
    annotators: tuple[str, ...],
) -> Path:
    """Tulis `human_annotations.csv` dengan kolom sesuai kontrak yang dibekukan.

    Kolom `note` dari berkas kerja **tidak** ikut — skemanya sudah beku. Catatan
    anotator dipindahkan ke lampiran laporan kesepakatan. Nama rondenya juga
    tidak ikut, karena alasan yang sama; pemetaan node ke ronde tersimpan di
    `sample_manifest.json` masing-masing.

    Baris dikelompokkan per anotator, lalu per ronde sesuai urutan `--rounds`.
    Waktu cadangan diambil dari berkas jawaban **ronde yang bersangkutan** —
    dulu sempat selalu dibaca dari `annotation/`, sehingga ronde kedua mewarisi
    waktu ubah ronde pertama.
    """
    path = seed_dir / "human_annotations.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(HUMAN_ANNOTATIONS_COLUMNS),
            lineterminator="\n",
        )
        writer.writeheader()
        for annotator_id in annotators:
            for rnd in rounds:
                fallback = _fallback_timestamp(
                    rnd.directory / f"answers_{annotator_id}.csv"
                )
                for row in rnd.filled[annotator_id]:
                    out = {
                        "node_id": row["node_id"],
                        "annotator_id": row["annotator_id"],
                        "label": row["label"],
                        "confidence": row["confidence"],
                        "annotated_at": row["annotated_at"] or fallback,
                    }
                    if tuple(out) != HUMAN_ANNOTATIONS_COLUMNS:
                        raise AssertionError(
                            f"baris human_annotations.csv melanggar kontrak kolom: {tuple(out)}"
                        )
                    writer.writerow(out)
    return path


def _write_majority(
    path: Path,
    rounds: list[Round],
    annotators: tuple[str, ...],
) -> Path:
    """Tulis label suara terbanyak. **Bukan** bagian kontrak `human_annotations.csv`.

    Disediakan agar orang B tidak perlu mengarang aturan agregasi sendiri.
    `agreement` mencatat berapa anotator yang setuju, sehingga penyaringan
    kualitas bisa dilakukan di sisi model.

    Dipanggil sekali untuk gabungan seluruh ronde, lalu sekali lagi per ronde
    bila rondenya lebih dari satu. Berkas per-ronde itu yang memungkinkan
    ablasi dijalankan dengan jumlah anotasi ditahan tetap dan hanya mutunya
    yang berubah — tanpa berkas terpisah, satu-satunya cara membandingkannya
    adalah menjalankan `merge` berulang kali dan menyalin keluarannya di
    antara setiap jalan.
    """
    votes: dict[str, list[int]] = {}
    confidences: dict[str, list[float]] = {}
    for rnd in rounds:
        for annotator_id in annotators:
            for row in rnd.filled[annotator_id]:
                votes.setdefault(row["node_id"], []).append(int(row["label"]))
                confidences.setdefault(row["node_id"], []).append(
                    float(row["confidence"])
                )

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "node_id",
                "label",
                "confidence_mean",
                "agreement",
                "n_annotators",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for node_id in sorted(votes):
            ballot = votes[node_id]
            label = majority_label(ballot)
            agreeing = sum(1 for value in ballot if value == label)
            writer.writerow(
                {
                    "node_id": node_id,
                    "label": label,
                    "confidence_mean": f"{sum(confidences[node_id]) / len(ballot):.3f}",
                    "agreement": f"{agreeing / len(ballot):.3f}",
                    "n_annotators": len(ballot),
                }
            )
    return path


#: Cara membaca kappa per strata. Dipakai sekali di tiap laporan.
CATATAN_STRATA = (
    "Kesepakatan yang jatuh pada strata ambigu dan tinggi pada strata yang",
    "rule engine yakin adalah bukti kuantitatif bahwa strata ambigu memang",
    "sulit — bukan tanda anotator bekerja sembarangan. Kappa per strata bisa",
    "mendekati nol justru ketika kesepakatannya tinggi, bila hampir seluruh",
    "penilaian jatuh ke satu kelas; baca kolom kesepakatan dan porsi label 1",
    "bersama-sama, jangan kappa-nya sendirian.",
)


def _round_tables(rnd: Round, *, dengan_subjudul: bool) -> list[str]:
    """Tiga tabel satu ronde: ringkasan, laju pelabelan, kesepakatan per strata.

    `dengan_subjudul` dimatikan pada laporan gabungan, karena di sana setiap
    ronde sudah punya judulnya sendiri dan sub-judul bertingkat membuat daftar
    isinya lebih ramai daripada isinya.
    """
    result = rnd.result
    strata_labels: dict[str, str] = rnd.manifest["strata_labels"]  # type: ignore[assignment]

    lines: list[str] = []
    if dengan_subjudul:
        lines += ["## Ringkasan", ""]
    lines += [
        "| Ukuran | Nilai | Tafsir |",
        "|---|---|---|",
        f"| Fleiss' kappa | {result.fleiss_kappa:.3f} | {interpret(result.fleiss_kappa)} |",
        f"| Selang kepercayaan 95% kappa | [{rnd.kappa_ci[0]:.3f}, {rnd.kappa_ci[1]:.3f}] "
        f"| bootstrap {BOOTSTRAP_REPEATS} ulangan atas node |",
        f"| Kesepakatan mentah | {result.percent_agreement:.3f} | "
        f"{result.unanimous}/{result.n_items} node dinilai bulat |",
    ]
    for pair, value in result.pairwise_cohen.items():
        lines.append(f"| Cohen's kappa {pair} | {value:.3f} | {interpret(value)} |")

    lines.append("")
    if dengan_subjudul:
        lines += ["## Laju pelabelan per anotator", ""]
    lines += ["| Anotator | Porsi dilabeli 1 |", "|---|---|"]
    for name, rate in result.label_rate.items():
        lines.append(f"| {name} | {rate:.3f} |")

    if result.per_stratum:
        lines.append("")
        if dengan_subjudul:
            lines += ["## Kesepakatan per strata", ""]
        lines += [
            "| Strata | n | Fleiss' kappa | Kesepakatan | Porsi label 1 | Keterangan |",
            "|---|---|---|---|---|---|",
        ]
        for name in STRATA_ORDER:
            stats = result.per_stratum.get(name)
            if not stats:
                continue
            lines.append(
                f"| {name} | {stats['n_items']:.0f} | {stats['fleiss_kappa']:.3f} | "
                f"{stats['percent_agreement']:.3f} | {stats['positive_rate']:.3f} | "
                f"{strata_labels.get(name, '')} |"
            )
    return lines


def _write_report(
    seed_dir: Path,
    rounds: list[Round],
    annotators: tuple[str, ...],
) -> Path:
    """Tulis `agreement_report.md`. **Bukan** bagian kontrak `human_annotations.csv`."""
    seed = rounds[0].manifest["seed"]
    n_nodes = sum(len(rnd.stratum_of) for rnd in rounds)
    n_ratings = sum(rnd.n_ratings for rnd in rounds)
    tunggal = len(rounds) == 1

    lines = [f"# Laporan Kesepakatan Anotasi — seed {seed}", ""]

    if tunggal:
        rnd = rounds[0]
        lines += [
            f"{rnd.result.n_items} node dinilai {rnd.result.n_raters} anotator "
            f"({rnd.n_ratings} penilaian).",
            "",
        ]
        lines += _round_tables(rnd, dengan_subjudul=True)
        lines += ["", *CATATAN_STRATA]
    else:
        lines += [
            f"{n_nodes} node dari {len(rounds)} ronde "
            f"({', '.join(rnd.name for rnd in rounds)}), "
            f"{n_ratings} penilaian oleh {len(annotators)} anotator.",
            "",
            "## Perbandingan antar-ronde",
            "",
            "Kesepakatan dilaporkan **per ronde**, bukan atas gabungannya. Kappa atas",
            "gabungan mencampur mutu anotasi sebelum dan sesudah kalibrasi menjadi satu",
            "angka yang tidak dapat ditafsirkan sebagai apa pun.",
            "",
            "| Ronde | n | Fleiss' kappa | Tafsir | Selang 95% | Kesepakatan | Laju label 1 |",
            "|---|---:|---:|---|---|---:|---|",
        ]
        for rnd in rounds:
            result = rnd.result
            laju = " / ".join(f"{value:.2f}" for value in result.label_rate.values())
            lines.append(
                f"| {rnd.name} | {result.n_items} | {result.fleiss_kappa:.3f} | "
                f"{interpret(result.fleiss_kappa)} | "
                f"[{rnd.kappa_ci[0]:.3f}, {rnd.kappa_ci[1]:.3f}] | "
                f"{result.percent_agreement:.3f} | {laju} |"
            )
        lines += [
            "",
            "Cara membaca kolom selang: dua ronde yang selangnya **tidak beririsan**",
            "sudah cukup untuk menyatakan kappa-nya memang berbeda. Selang yang",
            "beririsan belum tentu berarti tidak ada beda — ia hanya berarti data",
            "sebanyak ini belum bisa memisahkan keduanya.",
            "",
            "⚠️ Ronde yang berbeda menilai **node yang berbeda**, sehingga",
            "perbandingannya menanggung selisih tingkat kesulitan sampel. Rancangan",
            "strata yang sama di setiap ronde menahan sebagian besar selisih itu,",
            "tetapi tidak seluruhnya — batas ini perlu disebutkan bila angkanya dipakai untuk pelaporan.",
            "",
            *CATATAN_STRATA,
        ]
        for rnd in rounds:
            lines += [
                "",
                f"## Ronde: {rnd.name}",
                "",
                f"{rnd.result.n_items} node, {rnd.n_ratings} penilaian.",
                "",
            ]
            lines += _round_tables(rnd, dengan_subjudul=False)

    lines += [
        "",
        "Pita tafsir mengikuti Landis & Koch, *Biometrics* 33(1), 1977.",
    ]

    notes = [
        (rnd.name, row["node_id"], row["annotator_id"], row["note"])
        for rnd in rounds
        for annotator_id in annotators
        for row in rnd.filled[annotator_id]
        if row["note"]
    ]
    if notes:
        lines += [
            "",
            "## Lampiran: catatan anotator",
            "",
            "Bahan kutipan kualitatif. Kolom `note` tidak masuk",
            "`human_annotations.csv` karena skemanya sudah dibekukan.",
            "",
        ]
        if tunggal:
            lines += ["| Node | Anotator | Catatan |", "|---|---|---|"]
            for _, node_id, annotator_id, note in notes:
                lines.append(f"| {node_id} | {annotator_id} | {note} |")
        else:
            lines += ["| Ronde | Node | Anotator | Catatan |", "|---|---|---|---|"]
            for round_name, node_id, annotator_id, note in notes:
                lines.append(
                    f"| {round_name} | {node_id} | {annotator_id} | {note} |"
                )

    lines.append("")
    path = seed_dir / "agreement_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_merged_manifest(seed_dir: Path, rounds: list[Round]) -> Path:
    """Manifest gabungan lintas-ronde. **Koordinator saja**, memuat strata.

    Gunanya satu: memberi urutan `annotation_order` global untuk kurva A5
    saat ablasi dijalankan atas gabungan beberapa ronde.

    Urutannya **berselang-seling antar-ronde**, bukan sambung-menyambung.
    Sifat yang dijaga `a5_prefix_note` adalah setiap prefiks tetap berimbang
    strata dan tidak kosong dari positif; menyambung ronde secara berurutan
    akan membuat prefiks kecil berisi satu ronde saja, sehingga kurva A5-nya
    mengukur mutu anotasi satu ronde alih-alih pengaruh jumlah anotasi.
    """
    per_round = [
        [
            dict(entry, round=rnd.name)
            for entry in sorted(
                rnd.manifest["nodes"], key=lambda row: row.get("annotation_order", 0)
            )
        ]
        for rnd in rounds
    ]
    merged: list[dict] = []
    for index in range(max(len(entries) for entries in per_round)):
        for entries in per_round:
            if index < len(entries):
                merged.append(entries[index])
    for order, entry in enumerate(merged):
        entry["annotation_order"] = order

    payload = {
        "seed": rounds[0].manifest["seed"],
        "rounds": [rnd.name for rnd in rounds],
        "total": len(merged),
        "annotators": list(rounds[0].annotators),
        "strata_labels": rounds[0].manifest["strata_labels"],
        "a5_prefix_note": (
            "urutan berselang-seling antar-ronde; setiap prefiks memuat porsi "
            "yang sebanding dari tiap ronde dan tetap berimbang strata"
        ),
        "nodes": merged,
    }
    path = seed_dir / "sample_manifest_merged.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m annotation.build",
        description="Alat bantu anotasi manual SATPAM.",
    )
    parser.add_argument("command", choices=("sample", "merge", "debrief"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--total", type=int, default=DEFAULT_TOTAL)
    parser.add_argument(
        "--sampling-seed", type=int, default=DEFAULT_SAMPLING_SEED
    )
    parser.add_argument(
        "--annotators", nargs="+", default=list(DEFAULT_ANNOTATORS)
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="izinkan `sample` menimpa berkas jawaban yang sudah terisi",
    )
    parser.add_argument(
        "--subdir",
        default="anotasi_ronde1",
        help="subdirektori keluaran di bawah direktori seed; pakai nama lain "
        "untuk ronde lanjutan agar tidak bertabrakan dengan ronde sebelumnya, "
        "contoh anotasi_ronde2",
    )
    parser.add_argument(
        "--rounds",
        nargs="+",
        default=None,
        metavar="SUBDIR",
        help="khusus `merge`: gabungkan beberapa ronde sekaligus, contoh "
        "`--rounds anotasi_ronde1 anotasi_ronde2`. Tanpa ini hanya `--subdir` "
        "yang digabung, dan hasil ronde lain akan tertimpa",
    )
    parser.add_argument(
        "--exclude-annotated",
        action="store_true",
        help="jangan pilih node yang sudah masuk sampel ronde mana pun",
    )
    args = parser.parse_args(argv)

    print(f"seed {args.seed} — {args.command}")
    if args.command == "sample":
        return command_sample(args)
    if args.command == "debrief":
        return command_debrief(args)
    return command_merge(args)


if __name__ == "__main__":
    sys.exit(main())
