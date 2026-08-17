"""Orkestrator generator — menjalankan langkah 1 sampai 9 dan menulis berkas.

Pemakaian:

    python -m generator.build --seed 42
    python -m generator.build --all-seeds
    python -m generator.build --seed 42 --nodes 400        # smoke test cepat
    python -m generator.build --validate-only data/synthetic/seed_42

Urutan langkahnya mengikat dan alasannya ada di masing-masing modul:

    1. operators.plan_operators()          GROUND TRUTH DITANAM DI SINI
    2. population.build_population()       node + waktu + flag noise
    3. features.assign_planted_features()  fitur yang di-sample per kelas
    4. evidence.sow_all()                  edge menurut aturan G1..G8
    5. noise.apply()                       buang 10%, tambah palsu 2%
    6. features.recompute_derived_*()      fitur turunan dari edge FINAL
    7. split.assign_temporal_split()       persentil first_seen_at
    8. validate.run_all()                  gagal = tidak menulis apa pun
    9. tulis nodes.csv, edges.csv, manifest.json

Langkah 6 harus setelah langkah 5, dan langkah 8 harus sebelum langkah 9. Dua
urutan itu yang menjaga `nodes.csv` dan `edges.csv` tidak pernah saling
bertentangan, dan berkas cacat tidak pernah sampai ke tangan orang lain.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from generator import evidence, features, noise, split as split_module, validate
from generator.config import GENERATOR_VERSION, OFFICIAL_SEEDS, GeneratorParams
from generator.ids import IdAllocator
from generator.operators import OperatorPlan, plan_operators
from generator.population import Population, build_population
from generator.records import EdgeRecord
from generator.schema import EDGES_COLUMNS, NODES_COLUMNS
from generator.timeline import Timeline

#: Direktori keluaran bawaan; tiap seed mendapat subdirektori sendiri.
DEFAULT_OUTPUT_ROOT = Path("data/synthetic")

#: Akhiran baris CSV dipatok agar keluaran di Windows dan Linux identik.
CSV_LINE_TERMINATOR = "\n"


@dataclasses.dataclass
class BuildResult:
    """Hasil satu kali jalan generator."""

    params: GeneratorParams
    timeline: Timeline
    plan: OperatorPlan
    population: Population
    edges: list[EdgeRecord]
    noise_report: noise.NoiseReport
    split_report: split_module.SplitReport
    validation: validate.ValidationResult
    output_dir: Path | None


def generate(params: GeneratorParams) -> BuildResult:
    """Jalankan langkah 1–8 untuk satu seed. Tidak menulis berkas apa pun."""
    rng = np.random.default_rng(params.seed)
    timeline = Timeline.from_params(params)
    allocator = IdAllocator()

    plan = plan_operators(params, rng, timeline)
    population = build_population(params, rng, timeline, plan, allocator)
    features.assign_planted_features(params, rng, population.nodes)
    edges = evidence.sow_all(params, rng, timeline, plan, population)
    edges, noise_report = noise.apply(
        params, rng, timeline, list(population.nodes), edges
    )
    features.recompute_derived_features(population.nodes, edges)
    split_report = split_module.assign_temporal_split(params, timeline, population.nodes)

    validation = validate.run_all(
        params, timeline, plan, population, edges, noise_report, split_report
    )

    return BuildResult(
        params=params,
        timeline=timeline,
        plan=plan,
        population=population,
        edges=edges,
        noise_report=noise_report,
        split_report=split_report,
        validation=validation,
        output_dir=None,
    )


def write_output(result: BuildResult, output_root: Path) -> Path:
    """Tulis `nodes.csv`, `edges.csv`, dan `manifest.json` (langkah 9).

    Raises:
        RuntimeError: bila validasi belum lolos. Berkas cacat tidak boleh
            sampai ke tangan orang lain.
    """
    if not result.validation.ok:
        raise RuntimeError(
            "validasi tidak lolos, berkas tidak ditulis:\n"
            + result.validation.summary()
        )

    output_dir = output_root / f"seed_{result.params.seed}"
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(
        output_dir / "nodes.csv",
        NODES_COLUMNS,
        (node.to_csv_row(result.timeline) for node in result.population.nodes),
    )
    _write_csv(
        output_dir / "edges.csv",
        EDGES_COLUMNS,
        (edge.to_csv_row(result.timeline) for edge in result.edges),
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(_build_manifest(result), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    result.output_dir = output_dir
    return output_dir


def _write_csv(path: Path, columns: tuple[str, ...], rows) -> None:
    """Tulis CSV dengan urutan kolom kontrak dan akhiran baris yang dipatok."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(columns), lineterminator=CSV_LINE_TERMINATOR
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _build_manifest(result: BuildResult) -> dict[str, object]:
    """Susun `manifest.json` sesuai kontrak keluaran.

    Diagnostik split dan noise ditaruh **di dalam `params`**, bukan sebagai kunci
    baru di level atas — struktur manifest yang disepakati tidak disentuh sama
    sekali (opsi yang disetujui).
    """
    params = result.params
    population = result.population
    illicit = population.illicit()

    manifest_params = params.to_manifest_params()
    manifest_params["split_diagnostics"] = result.split_report.as_dict(result.timeline)
    manifest_params["noise"] = result.noise_report.as_dict()
    manifest_params["edges_by_rule"] = _edges_by_rule(result.edges)
    manifest_params["node_counts_by_type"] = population.type_counts()
    manifest_params["population_flags"] = population.counts_summary()
    manifest_params["timeline"] = {
        "start": result.timeline.to_iso(result.timeline.start),
        "end": result.timeline.to_iso(result.timeline.end),
        "total_days": result.timeline.total_days,
    }
    if result.plan.scale_notes:
        manifest_params["scale_notes"] = list(result.plan.scale_notes)
    if population.notes:
        manifest_params["population_notes"] = list(population.notes)
    if result.validation.warnings:
        manifest_params["validation_warnings"] = list(result.validation.warnings)

    return {
        "seed": params.seed,
        "generated_at": _now_iso(params.timezone_offset_hours),
        "generator_version": GENERATOR_VERSION,
        "counts": {
            "nodes": len(population.nodes),
            "edges": len(result.edges),
            "illicit_nodes": len(illicit),
        },
        "anomaly_ratio": round(len(illicit) / max(len(population.nodes), 1), 6),
        "n_operators": result.plan.n_operators,
        "ecosystem_split": result.plan.ecosystem_counts(),
        "params": manifest_params,
    }


def _edges_by_rule(edges: list[EdgeRecord]) -> dict[str, int]:
    """Jumlah edge per aturan generatif, untuk memeriksa tiap aturan benar aktif."""
    counts: dict[str, int] = {}
    for edge in edges:
        counts[edge.rule_tag] = counts.get(edge.rule_tag, 0) + 1
    return dict(sorted(counts.items()))


def _now_iso(offset_hours: int) -> str:
    """Waktu sekarang untuk `manifest.generated_at`.

    Ini satu-satunya nilai di seluruh keluaran yang tidak ditentukan seed, jadi
    dua kali jalan atas seed yang sama menghasilkan berkas identik kecuali medan
    ini. Itu memang niatnya: ia catatan provenance, bukan bagian dari data.
    """
    return (
        datetime.now(timezone(timedelta(hours=offset_hours)))
        .replace(microsecond=0)
        .isoformat()
    )


# ---------------------------------------------------------------------------
# Antarmuka baris perintah
# ---------------------------------------------------------------------------


def _print_report(result: BuildResult) -> None:
    """Ringkasan satu seed ke stdout."""
    population = result.population
    illicit = population.illicit()
    flags = population.counts_summary()
    split_report = result.split_report

    print(f"  node            {len(population.nodes):,}")
    print(f"  edge            {len(result.edges):,}")
    print(
        f"  ilegal          {len(illicit):,} "
        f"({len(illicit) / max(len(population.nodes), 1):.4f})"
    )
    print(
        f"  operator        {result.plan.n_operators} "
        f"{result.plan.ecosystem_counts()}"
    )
    print(
        f"  noise §6.4      buang {result.noise_report.drop_share_actual:.3f}, "
        f"palsu {result.noise_report.false_share_actual:.3f}, "
        f"hard neg {flags['hard_negatives']}, hard pos {flags['hard_positives']}"
    )
    for name in ("train", "val", "test"):
        total = split_report.counts.get(name, 0)
        positives = split_report.illicit_counts.get(name, 0)
        print(
            f"  split {name:<6}    {total:>5} node, {positives:>4} positif "
            f"({positives / max(total, 1) * 100:.2f}%)"
        )
    print(f"  validasi        {result.validation.summary()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m generator.build",
        description="Generator data sintetik SATPAM dengan planted ground truth.",
    )
    parser.add_argument("--seed", type=int, default=42, help="seed generator")
    parser.add_argument(
        "--all-seeds",
        action="store_true",
        help=f"jalankan seluruh seed resmi {OFFICIAL_SEEDS}",
    )
    parser.add_argument(
        "--nodes",
        type=int,
        default=None,
        help="jumlah node target; pakai nilai kecil untuk smoke test",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=f"direktori akar keluaran (bawaan {DEFAULT_OUTPUT_ROOT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="jalankan dan validasi tanpa menulis berkas",
    )
    parser.add_argument(
        "--validate-only",
        type=Path,
        default=None,
        metavar="DIR",
        help="hanya validasi direktori keluaran yang sudah ada",
    )
    args = parser.parse_args(argv)

    if args.validate_only is not None:
        print(f"Memvalidasi {args.validate_only}")
        result = validate.validate_directory(args.validate_only)
        print(result.summary())
        return 0 if result.ok else 1

    seeds = list(OFFICIAL_SEEDS) if args.all_seeds else [args.seed]
    failures = 0

    for seed in seeds:
        overrides: dict[str, object] = {"seed": seed}
        if args.nodes is not None:
            overrides["n_nodes_target"] = args.nodes
        params = dataclasses.replace(GeneratorParams(), **overrides)

        print(f"\nseed {seed}")
        result = generate(params)
        _print_report(result)

        if not result.validation.ok:
            failures += 1
            print("  -> validasi GAGAL, berkas tidak ditulis")
            continue
        if args.dry_run:
            print("  -> dry-run, berkas tidak ditulis")
            continue

        output_dir = write_output(result, args.out)
        print(f"  -> ditulis ke {output_dir}")

    if failures:
        print(f"\n{failures} dari {len(seeds)} seed gagal validasi")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
