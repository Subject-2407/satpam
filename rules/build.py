"""Penulis `weak_labels.csv`.

Pemakaian:

    python -m rules.build --seed 42
    python -m rules.build --all-seeds
    python -m rules.build --seed 42 --tier srs-only     # ablasi tanpa R-X1/R-X2
    python -m rules.build --seed 42 --max-depth 1
    python -m rules.build --seed 42 --dry-run

Membaca `nodes.csv` dan `edges.csv` yang sudah ada di `data/synthetic/seed_{N}/`
lalu menulis `weak_labels.csv` di direktori yang sama.

Keluaran ini **hanya untuk pelatihan** — ini aturan keras yang tidak boleh
dilanggar. Dilarang menghitung metrik terhadapnya.

Modul ini tidak mengimpor apa pun dari `generator/` dan tidak membaca kolom
jawaban. Karena itu ia juga tidak bisa — dan tidak boleh — melaporkan seberapa
tepat labelnya; pengukuran itu ada di `tests/test_weak_labels_are_weak.py` yang
berada di luar paket ini.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from rules.graph import RuleGraph
from rules.loader import load_edges, load_nodes
from rules.scoring import (
    ALL_TIERS,
    DEFAULT_CONTEXT_LIMIT,
    DEFAULT_MAX_DEPTH,
    LEGACY_MAX_DEPTH,
    RULES,
    SRS_TIER_ONLY,
    RuleAssessment,
    score_graph,
)

#: Kolom `weak_labels.csv`, urut.
WEAK_LABELS_COLUMNS: tuple[str, ...] = (
    "node_id",
    "rule_score",
    "rule_level",
    "triggered_rules",
)

DEFAULT_DATA_ROOT = Path("data/synthetic")
OFFICIAL_SEEDS: tuple[int, ...] = (42, 43, 44, 45, 46)


def build_weak_labels(
    directory: Path,
    tiers: tuple[str, ...] = ALL_TIERS,
    max_depth: int = DEFAULT_MAX_DEPTH,
    context_limit: int = DEFAULT_CONTEXT_LIMIT,
):
    """Muat graph sebuah seed lalu skor seluruh node-nya."""
    graph = RuleGraph.build(
        load_nodes(directory / "nodes.csv"),
        load_edges(directory / "edges.csv"),
    )
    assessments, calibration, matches = score_graph(
        graph, tiers=tiers, max_depth=max_depth, context_limit=context_limit
    )
    return graph, assessments, calibration, matches


def write_weak_labels(directory: Path, assessments: list[RuleAssessment]) -> Path:
    """Tulis `weak_labels.csv` dengan kolom yang sudah ditetapkan."""
    path = directory / "weak_labels.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(WEAK_LABELS_COLUMNS), lineterminator="\n"
        )
        writer.writeheader()
        for assessment in assessments:
            row = {
                "node_id": assessment.node_id,
                "rule_score": assessment.score,
                "rule_level": assessment.level,
                "triggered_rules": assessment.triggered_rules,
            }
            if tuple(row) != WEAK_LABELS_COLUMNS:
                raise AssertionError(
                    f"baris weak_labels.csv tidak cocok kontrak §5.3: {tuple(row)}"
                )
            writer.writerow(row)
    return path


def write_audit(
    directory: Path,
    calibration,
    matches: dict[str, dict[str, str]],
    assessments: list[RuleAssessment],
    tiers: tuple[str, ...],
    max_depth: int,
) -> Path:
    """Tulis `weak_labels_audit.json` — asal-usul dan ambang tiap aturan.

    Bukan bagian format `weak_labels.csv`, jadi berkas terpisah. Isinya yang
    membuat klaim "tiap aturan bisa ditelusuri ke sumber asalnya" bisa
    diperiksa orang lain tanpa membaca kode.
    """
    levels: dict[str, int] = {}
    for assessment in assessments:
        levels[assessment.level] = levels.get(assessment.level, 0) + 1

    payload = {
        "rules_version": "1.0.0",
        "adapted_from": (
            "src-old/backend/app/services/ai_engine/scoring.py "
            "(SATPAM v1.0, ditulis sebelum generator ada)"
        ),
        "tiers_active": list(tiers),
        "max_depth": max_depth,
        "inherited_from_v1": {
            "score_cap": 100,
            "level_thresholds": {"critical": 80, "high": 60, "medium": 35},
            "context_limit": DEFAULT_CONTEXT_LIMIT,
            "count_floors": {"R-009": 2, "R-003": 3, "R-015": 4},
        },
        "changed_from_v1": {
            "context_max_depth": {
                "v1": LEGACY_MAX_DEPTH,
                "here": DEFAULT_MAX_DEPTH,
                "reason": (
                    "graph v1.0 berisi 10-80 entitas per tipe; pada 5.000 node "
                    "konteks 2-hop membuat 89,6% node menjadi critical dan "
                    "aturannya berhenti membedakan apa pun. Dipilih dengan "
                    "kriteria bebas ground truth (sebaran level tidak degenerate)"
                ),
            }
        },
        "calibrated_thresholds": calibration.as_dict(),
        "rules": {
            rule_id: {
                "title": rule.title,
                "weight": rule.weight,
                "srs_6_3_row": rule.srs_rule or None,
                "citation": rule.citation,
                "legacy_rule": rule.legacy_rule,
                "tier": rule.tier,
                "nodes_matched": len(matches.get(rule_id, {})),
            }
            for rule_id, rule in RULES.items()
            if rule.tier in tiers
        },
        "level_distribution": levels,
    }
    path = directory / "weak_labels_audit.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return path


def _print_report(
    seed: int,
    assessments: list[RuleAssessment],
    calibration,
    matches: dict[str, dict[str, str]],
) -> None:
    total = len(assessments)
    levels: dict[str, int] = {}
    for assessment in assessments:
        levels[assessment.level] = levels.get(assessment.level, 0) + 1

    print(f"  node dinilai    {total:,}")
    print("  sebaran level   ", end="")
    print(
        ", ".join(
            f"{name} {levels.get(name, 0)} ({levels.get(name, 0) / max(total, 1) * 100:.1f}%)"
            for name in ("low", "medium", "high", "critical")
        )
    )
    fired = {rule_id: len(found) for rule_id, found in matches.items()}
    print("  node cocok/aturan")
    for rule_id in sorted(fired):
        rule = RULES[rule_id]
        tag = rule.srs_rule or "tier legacy"
        print(
            f"    {rule_id:6} {tag:12} bobot {rule.weight:>2}  "
            f"{fired[rule_id]:>5} node cocok"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rules.build",
        description="Rule engine SATPAM — menulis weak_labels.csv (pelatihan saja).",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--all-seeds", action="store_true")
    parser.add_argument(
        "--data-root", type=Path, default=DEFAULT_DATA_ROOT, help="akar data seed"
    )
    parser.add_argument(
        "--tier",
        choices=("all", "srs-only"),
        default="all",
        help="'srs-only' mematikan R-X1/R-X2 yang tidak punya baris §6.3 (ablasi)",
    )
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    tiers = ALL_TIERS if args.tier == "all" else SRS_TIER_ONLY
    seeds = list(OFFICIAL_SEEDS) if args.all_seeds else [args.seed]
    failures = 0

    for seed in seeds:
        directory = args.data_root / f"seed_{seed}"
        if not (directory / "nodes.csv").is_file():
            print(f"\nseed {seed}: {directory} belum berisi nodes.csv — dilewati")
            failures += 1
            continue

        print(f"\nseed {seed} (tier {args.tier}, max_depth {args.max_depth})")
        graph, assessments, calibration, matches = build_weak_labels(
            directory, tiers=tiers, max_depth=args.max_depth
        )
        _print_report(seed, assessments, calibration, matches)

        if args.dry_run:
            print("  -> dry-run, berkas tidak ditulis")
            continue

        path = write_weak_labels(directory, assessments)
        audit = write_audit(
            directory, calibration, matches, assessments, tiers, args.max_depth
        )
        print(f"  -> ditulis {path.name} dan {audit.name}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
