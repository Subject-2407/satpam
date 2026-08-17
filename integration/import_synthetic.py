"""
Impor data sintetik v2 seed 42 ke Neo4j lewat `POST /api/import/dummy-data`.

Seed 42 dipakai sebagai data demo dashboard. Endpoint impor backend memakai
MERGE, bukan CREATE, sehingga skrip ini idempoten — menjalankannya dua kali
tidak menduplikasi node maupun relationship.

## Apa yang masuk ke Neo4j

| Sumber | Menjadi |
|---|---|
| `nodes.csv` kolom identitas + `feat_*` | properti node (label v1 per `schema_map`) |
| `edges.csv` | relationship (8 tipe, padanan persis v1) |
| `weak_labels.csv` | `riskScore` (0–100), `riskLevel`, `triggeredRules` |
| `predictions.csv` | `mlScore`, `mlConfidence`, `mlScore{Mlp,XgbGraph,GcnHomogeneous}` |

## Apa yang TIDAK masuk ke Neo4j

`gt_illicit`, `gt_operator_id`, `gt_ecosystem`. `GET /api/entities/{node_type}/{node_id}`
mengembalikan node apa adanya tanpa menyaring properti, jadi ground truth di
Neo4j berarti ground truth terbit lewat API — termasuk terbaca responden studi,
yang membatalkan validitas studi itu. Pemetaannya ditulis ke
`integration/test_case_candidates.csv` (di-gitignore) untuk dipakai koordinator
memilih 5 kasus demo secara manual.

Penjagaannya aktif, bukan sekadar konvensi: setiap properti melewati
`schema_map.sanitize_properties()` yang **melempar exception** bila menemukan
prefiks `gt_`, dan dijaga `integration/tests/test_no_gt_leak.py`.

## Prinsip aditif

`riskScore`, `riskLevel`, dan `triggeredRules` diisi dari rule engine v2 orang A.
`mlScore`/`mlConfidence` adalah field **baru** yang berdiri di sampingnya — bukan
menimpanya. `riskScore` bertipe int 0–100 sementara `mlScore` float 0–1, jadi
keduanya memang tidak bisa saling menggantikan.

## Cara pakai

    # 1. Neo4j + backend hidup
    cd integration/backend && docker compose up -d

    # 2. Impor (butuh predictions.csv, lihat integration/README.md)
    python integration/import_synthetic.py --seed 42

    # 3. Tanpa skor ML, bila predictions.csv belum ada
    python integration/import_synthetic.py --seed 42 --skip-ml-scores

    # 4. Periksa payload tanpa mengirim apa pun
    python integration/import_synthetic.py --seed 42 --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ml_scores import (  # noqa: E402
    PredictionsMissingError,
    build_ml_properties,
    build_test_case_candidates,
)
from schema_map import (  # noqa: E402
    FEATURE_COLUMNS,
    NODE_TYPE_TO_V1,
    REL_TYPE_TO_V1,
    SOURCE,
    cosmetic_fields,
    sanitize_properties,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data" / "synthetic"
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_ADMIN = ("admin@satpam.test", "admin123")

# Payload dipecah supaya satu request tidak membawa 5.000 node + 18.447
# relationship sekaligus. MERGE membuat pemecahan ini aman.
NODE_BATCH = 500
REL_BATCH = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _confidence_from_weight(weight: float) -> str:
    """`ConfidenceLevel` v1 (low/medium/high) dari `weight` edge kontrak v2."""
    if weight >= 0.7:
        return "high"
    if weight >= 0.4:
        return "medium"
    return "low"


# --- Pembacaan sumber -------------------------------------------------------


def read_seed(seed: int, data_root: Path | None = None) -> dict[str, pd.DataFrame]:
    """Baca `nodes.csv`, `edges.csv`, `weak_labels.csv` untuk satu seed."""
    root = (data_root or DATA_ROOT) / f"seed_{seed}"
    if not root.is_dir():
        raise FileNotFoundError(f"{root} tidak ada — jalankan generator orang A lebih dulu")

    nodes = pd.read_csv(root / "nodes.csv")
    edges = pd.read_csv(root / "edges.csv")
    weak = pd.read_csv(root / "weak_labels.csv")

    unknown_nodes = set(nodes["node_type"]) - set(NODE_TYPE_TO_V1)
    if unknown_nodes:
        raise ValueError(f"node_type di luar skema yang dikenal: {sorted(unknown_nodes)}")
    unknown_rels = set(edges["rel_type"]) - set(REL_TYPE_TO_V1)
    if unknown_rels:
        raise ValueError(f"rel_type di luar skema yang dikenal: {sorted(unknown_rels)}")

    merged = nodes.merge(weak, on="node_id", how="left", validate="one_to_one")
    return {"nodes": merged, "edges": edges, "manifest_path": root / "manifest.json"}


# --- Pembangunan payload ----------------------------------------------------


def build_node_payload(
    row: dict[str, Any],
    ml_properties: dict[str, dict[str, Any]],
    now: str,
    seed: int,
) -> tuple[str, dict[str, Any]]:
    """Satu baris `nodes.csv` -> (nama field NodesContainer, properti node v1)."""
    node_id = str(row["node_id"])
    node_type = str(row["node_type"])
    v1_label, container_field = NODE_TYPE_TO_V1[node_type]

    rule_score = row.get("rule_score")
    rule_level = row.get("rule_level")
    triggered = row.get("triggered_rules")

    payload: dict[str, Any] = {
        "id": node_id,
        "type": v1_label,
        "label": node_id,
        "source": SOURCE,
        "createdAt": now,
        "updatedAt": now,
        "firstSeenAt": str(row["first_seen_at"]),
        "lastSeenAt": str(row["last_seen_at"]),
        "verificationStatus": "unreviewed",
        # --- rule engine v2 orang A (field lama, TIDAK ditimpa apa pun) ---
        "riskScore": int(rule_score) if pd.notna(rule_score) else 0,
        "riskLevel": str(rule_level) if pd.notna(rule_level) else "low",
        "triggeredRules": str(triggered).split(";") if pd.notna(triggered) and triggered else [],
        "confidence": _rule_confidence(rule_level),
        # --- metadata kontrak v2 ---
        "nodeTypeV2": node_type,
        "splitV2": str(row["split"]),
        "datasetSeed": int(seed),
        "simulationOnly": True,
    }
    payload = {key: value for key, value in payload.items() if value is not None}

    for column in FEATURE_COLUMNS:
        if column in row and pd.notna(row[column]):
            payload[column] = float(row[column])

    payload.update(cosmetic_fields(node_type, node_id, row))

    # --- field ML baru (aditif) ---
    payload.update(ml_properties.get(node_id, {}))

    # Penjaga: `gt_*` tidak boleh sampai ke sini.
    sanitize_properties(payload)
    return container_field, payload


def _rule_confidence(rule_level: Any) -> str:
    return {"low": "low", "medium": "medium", "high": "high", "critical": "high"}.get(
        str(rule_level), "low"
    )


def build_relationship_payload(row: dict[str, Any], now: str) -> dict[str, Any]:
    src_id, dst_id = str(row["src_id"]), str(row["dst_id"])
    rel_type_v2 = str(row["rel_type"])
    rel_type_v1 = REL_TYPE_TO_V1[rel_type_v2]
    weight = float(row["weight"])
    return {
        "id": f"{rel_type_v1}:{src_id}->{dst_id}",
        "type": rel_type_v1,
        "from": {"type": _label_of(src_id), "id": src_id},
        "to": {"type": _label_of(dst_id), "id": dst_id},
        "source": SOURCE,
        "confidence": _confidence_from_weight(weight),
        "weight": weight,
        "firstSeenAt": str(row["first_seen_at"]),
        "createdAt": now,
        "relTypeV2": rel_type_v2,
    }


def _label_of(node_id: str) -> str:
    """`domain_00042` -> `Domain`. Format node_id menjamin prefiks = node_type."""
    prefix = node_id.rsplit("_", 1)[0]
    if prefix not in NODE_TYPE_TO_V1:
        raise ValueError(f"node_id tidak mengikuti format yang diharapkan: {node_id!r}")
    return NODE_TYPE_TO_V1[prefix][0]


def _metadata(seed: int, now: str) -> dict[str, Any]:
    return {
        "datasetId": f"satpam-synthetic-seed-{seed}",
        "version": "2.0",
        "scope": "8 tipe node, 8 tipe relasi",
        "createdAt": now,
        "simulationOnly": True,
        "dataPolicy": [
            "Seluruh data sintetik; tidak ada data pribadi nyata.",
            "Ground truth gt_* sengaja TIDAK diimpor agar tidak terbit lewat API "
            "dan tidak terlihat responden studi.",
        ],
    }


def build_batches(
    frames: dict[str, pd.DataFrame],
    seed: int,
    ml_properties: dict[str, dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    """Hasilkan payload `DummyDataImportRequest` berbatch."""
    now = _now_iso()
    metadata = _metadata(seed, now)
    nodes = frames["nodes"]
    edges = frames["edges"]

    for start in range(0, len(nodes), NODE_BATCH):
        container: dict[str, list[dict[str, Any]]] = {}
        for row in nodes.iloc[start : start + NODE_BATCH].to_dict("records"):
            field, payload = build_node_payload(row, ml_properties, now, seed)
            container.setdefault(field, []).append(payload)
        yield {"metadata": metadata, "nodes": container, "relationships": []}

    # Relationship dikirim setelah seluruh node ada, karena merge_relationship
    # melewatkan edge yang salah satu ujungnya belum ada di Neo4j.
    for start in range(0, len(edges), REL_BATCH):
        chunk = [
            build_relationship_payload(row, now)
            for row in edges.iloc[start : start + REL_BATCH].to_dict("records")
        ]
        yield {"metadata": metadata, "nodes": {}, "relationships": chunk}


# --- Pengiriman -------------------------------------------------------------


def get_admin_token(base_url: str, email: str, password: str) -> str:
    import httpx

    response = httpx.post(
        f"{base_url}/api/auth/token",
        data={"username": email, "password": password},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def post_batches(base_url: str, token: str, batches: Iterator[dict[str, Any]]) -> dict[str, int]:
    import httpx

    totals = {"nodes_merged": 0, "relationships_merged": 0, "skipped": 0}
    errors: list[str] = []
    headers = {"Authorization": f"Bearer {token}"}

    with httpx.Client(timeout=180.0) as client:
        for index, batch in enumerate(batches, start=1):
            response = client.post(
                f"{base_url}/api/import/dummy-data", json=batch, headers=headers
            )
            response.raise_for_status()
            stats = response.json()["stats"]
            for key in totals:
                totals[key] += stats.get(key, 0)
            errors.extend(stats.get("errors", [])[:5])
            print(
                f"  batch {index:>3}: +{stats.get('nodes_merged', 0)} node "
                f"+{stats.get('relationships_merged', 0)} rel "
                f"({stats.get('skipped', 0)} dilewati)",
                flush=True,
            )

    if errors:
        print(f"\n{len(errors)} contoh galat pertama:")
        for message in errors[:10]:
            print(f"  - {message}")
    return totals


# --- CLI --------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--seed", type=int, default=42, help="seed demo dashboard")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--email", default=DEFAULT_ADMIN[0])
    parser.add_argument("--password", default=DEFAULT_ADMIN[1])
    parser.add_argument("--predictions", type=Path, default=None)
    parser.add_argument(
        "--skip-ml-scores",
        action="store_true",
        help="impor tanpa mlScore/mlConfidence (bila predictions.csv belum ada)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="bangun dan periksa payload tanpa menghubungi backend",
    )
    parser.add_argument(
        "--test-cases-out",
        type=Path,
        default=Path(__file__).resolve().parent / "test_case_candidates.csv",
        help="tabel gt_* untuk pemilihan kasus studi responden — lokal, di-gitignore",
    )
    args = parser.parse_args()

    print(f"Membaca data seed {args.seed} ...")
    frames = read_seed(args.seed, args.data_root)
    print(f"  {len(frames['nodes'])} node, {len(frames['edges'])} edge")

    ml_properties: dict[str, dict[str, Any]] = {}
    if args.skip_ml_scores:
        print("  skor ML dilewati (--skip-ml-scores): mlScore/mlConfidence tidak diimpor")
    else:
        try:
            ml_properties = build_ml_properties(args.seed, args.predictions)
            print(f"  skor ML untuk {len(ml_properties)} node dari predictions.csv")
        except PredictionsMissingError as exc:
            print(f"\nGAGAL: {exc}", file=sys.stderr)
            print("Atau jalankan ulang dengan --skip-ml-scores.", file=sys.stderr)
            return 1

        candidates = build_test_case_candidates(args.seed, args.predictions)
        args.test_cases_out.parent.mkdir(parents=True, exist_ok=True)
        candidates.to_csv(args.test_cases_out, index=False)
        positives = int(candidates["gt_illicit"].sum())
        print(
            f"  {args.test_cases_out.name}: {len(candidates)} baris "
            f"({positives} gt_illicit=1) — LOKAL, tidak masuk Neo4j"
        )

    batches = list(build_batches(frames, args.seed, ml_properties))
    node_count = sum(len(items) for batch in batches for items in batch["nodes"].values())
    rel_count = sum(len(batch["relationships"]) for batch in batches)
    print(f"\n{len(batches)} batch: {node_count} node, {rel_count} relationship")

    if args.dry_run:
        sample = next(
            payload
            for batch in batches
            for items in batch["nodes"].values()
            for payload in items
        )
        print("\nContoh satu node:")
        print(json.dumps(sample, indent=2, ensure_ascii=False))
        print("\n--dry-run: tidak ada yang dikirim.")
        return 0

    print(f"\nMengambil token admin dari {args.base_url} ...")
    token = get_admin_token(args.base_url, args.email, args.password)
    print("Mengirim batch ...")
    totals = post_batches(args.base_url, token, iter(batches))
    print(
        f"\nSelesai: {totals['nodes_merged']} node dan "
        f"{totals['relationships_merged']} relationship di-merge, "
        f"{totals['skipped']} dilewati."
    )
    return 0 if totals["skipped"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
