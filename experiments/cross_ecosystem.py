"""Uji klaim kebaruan utama: apakah memodelkan judol dan pinjol sebagai satu graph membantu?

**Kenapa eksperimen ini ada.** Novelty utama SATPAM adalah *keterkaitan
lintas-ekosistem judol ↔ pinjol ilegal via infrastruktur bersama* — bukan
R-GCN, yang statusnya eksplisit "bukan klaim kebaruan, hanya backbone".
Pertanyaan yang perlu dijawab dengan bukti: "Apakah keterkaitan
lintas-ekosistem terdeteksi?"

Tabel utama membuktikan R-GCN mengungguli rule-based, tetapi itu bukti bahwa
*sistemnya bekerja* — bukan bukti bahwa *menggabungkan kedua ekosistem*
memberi nilai tambah. Tanpa eksperimen ini, klaim kebaruan utama SATPAM
berdiri tanpa dukungan empiris yang spesifik.

**Rancangan.** Dua kondisi, satu-satunya perbedaan adalah cakupan graph:

| Kondisi | Graph | Menirukan |
|---|---|---|
| `joint` | seluruh node | SATPAM: satu lembaga melihat kedua ekosistem |
| `siloed` | node ekosistem seberang dibuang | Kondisi nyata: Komdigi memantau konten judol, OJK memantau pinjol, terpisah |

Evaluasi dilakukan **hanya pada node yang ada di kedua graph**, sehingga
himpunan ujinya identik dan selisihnya murni berasal dari konteks graph yang
tersedia — bukan dari soal yang berbeda.

Dijalankan dua arah (buang pinjol, lalu buang judol) agar tidak bergantung pada
satu sisi saja. Perhatian khusus pada node `gt_ecosystem=both`: merekalah yang
memegang infrastruktur bersama, jadi merekalah yang paling seharusnya diuntungkan
oleh penggabungan.

    python experiments/cross_ecosystem.py                    # 6 seed
    python experiments/cross_ecosystem.py --seeds 42 --repeats 3
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.loader import SatpamData, load_seed  # noqa: E402
from models.metrics import evaluate  # noqa: E402
from models.rgcn import train_rgcn  # noqa: E402

DEFAULT_SEEDS = (42, 43, 44, 45, 46, 47)
RESULTS_DIR = REPO_ROOT / "experiments" / "results"


def read_ecosystem(seed: int, data: SatpamData, data_root: Path) -> np.ndarray:
    """Ambil `gt_ecosystem` sejajar urutan node loader.

    Kolom ini **hanya** dipakai untuk membangun kondisi eksperimen dan memecah
    pelaporan — tidak pernah masuk fitur maupun label pelatihan, sama seperti
    `gt_illicit`.
    """
    frame = pd.read_csv(
        data_root / f"seed_{seed}" / "nodes.csv", usecols=["node_id", "gt_ecosystem"]
    )
    lookup = dict(zip(frame["node_id"], frame["gt_ecosystem"]))
    return np.array([lookup[node_id] for node_id in data.node_ids], dtype=object)


def build_subgraph(data: SatpamData, keep: np.ndarray) -> SatpamData:
    """Bangun subgraph berisi node `keep` saja, dengan indeks dipetakan ulang.

    Edge yang salah satu ujungnya dibuang ikut hilang — itu memang inti kondisi
    `siloed`: hilangnya jembatan infrastruktur antar-ekosistem.

    `hetero` tidak ikut dibangun ulang (tidak dipakai `train_rgcn`) dan karena
    itu **tidak valid** pada objek hasil fungsi ini.
    """
    remap = np.cumsum(keep) - 1
    src = data.edge_index[0].numpy()
    dst = data.edge_index[1].numpy()
    edge_keep = keep[src] & keep[dst]

    node_ids = [n for n, k in zip(data.node_ids, keep) if k]
    keep_t = torch.tensor(keep, dtype=torch.bool)
    edge_t = torch.tensor(edge_keep, dtype=torch.bool)

    return dataclasses.replace(
        data,
        x=data.x[keep_t],
        node_type=data.node_type[keep_t],
        edge_index=torch.tensor(
            np.stack([remap[src[edge_keep]], remap[dst[edge_keep]]]), dtype=torch.long
        ),
        edge_type=data.edge_type[edge_t],
        edge_weight=data.edge_weight[edge_t],
        y_weak=data.y_weak[keep_t],
        rule_score=data.rule_score[keep_t],
        y_gt=data.y_gt[keep_t],
        train_mask=data.train_mask[keep_t],
        val_mask=data.val_mask[keep_t],
        test_mask=data.test_mask[keep_t],
        entity_mask=data.entity_mask[keep_t],
        loss_mask=data.loss_mask[keep_t],
        node_ids=node_ids,
        index_of={n: i for i, n in enumerate(node_ids)},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--repeats", type=int, default=3, help="inisialisasi per kondisi")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data" / "synthetic")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    started = time.perf_counter()

    # `drop` = ekosistem yang dibuang pada kondisi siloed; `focus` = sisi yang dinilai.
    directions = (("pinjol", "judol"), ("judol", "pinjol"))

    for seed in args.seeds:
        print(f"\n=== seed {seed} ===")
        full = load_seed(seed, args.data_root)
        ecosystem = read_ecosystem(seed, full, args.data_root)

        for drop, focus in directions:
            keep = ecosystem != drop
            siloed = build_subgraph(full, keep)
            print(
                f"  buang '{drop}' -> {int(keep.sum())}/{full.num_nodes} node, "
                f"{siloed.edge_index.size(1)}/{full.edge_index.size(1)} edge tersisa"
            )

            for condition, dataset, index in (
                ("joint", full, np.flatnonzero(keep)),
                ("siloed", siloed, np.arange(int(keep.sum()))),
            ):
                for repeat in range(args.repeats):
                    result = train_rgcn(
                        dataset,
                        epochs=args.epochs,
                        patience=args.patience,
                        torch_seed=seed + repeat,
                    )
                    prob = result.prob[index]
                    gt = full.y_gt.numpy()[keep]
                    test_entity = (
                        (full.test_mask & full.entity_mask).numpy()[keep]
                    )
                    eco_kept = ecosystem[keep]

                    # Seluruh node yang tersisa, dan khusus node lintas-ekosistem.
                    for group, mask in (
                        ("semua_tersisa", test_entity),
                        ("both_saja", test_entity & np.isin(eco_kept, ["both", "none"])),
                        (f"{focus}_saja", test_entity & np.isin(eco_kept, [focus, "none"])),
                    ):
                        if gt[mask].sum() == 0:
                            continue
                        rows.append(
                            {
                                "seed": seed,
                                "dropped_ecosystem": drop,
                                "condition": condition,
                                "group": group,
                                "repeat_seed": seed + repeat,
                                "auprc": evaluate(gt[mask], prob[mask])["auprc"],
                                "n": int(mask.sum()),
                                "n_pos": int(gt[mask].sum()),
                            }
                        )

    frame = pd.DataFrame(rows)
    frame.to_csv(args.results_dir / "cross_ecosystem.csv", index=False)

    print("\n" + "=" * 78)
    print("LINTAS-EKOSISTEM: joint vs siloed (AUPRC, test, tipe entitas)")
    print("=" * 78)
    for drop in frame["dropped_ecosystem"].unique():
        subset = frame[frame["dropped_ecosystem"] == drop]
        print(f"\n  Kondisi siloed = ekosistem '{drop}' dibuang dari graph:")
        pivot = subset.pivot_table(
            index="group", columns="condition", values="auprc", aggfunc="mean"
        )
        for group in pivot.index:
            joint = pivot.loc[group, "joint"]
            siloed = pivot.loc[group, "siloed"]
            gain = joint - siloed
            rel = f"{gain / siloed * 100:+.1f}%" if siloed > 0 else "n/a"
            print(
                f"    {group:22} siloed {siloed:.4f} -> joint {joint:.4f}"
                f"   selisih {gain:+.4f} ({rel})"
            )

    print(f"\nSelesai dalam {time.perf_counter() - started:.0f} detik.")
    print(f"Hasil ditulis ke {args.results_dir / 'cross_ecosystem.csv'}")


if __name__ == "__main__":
    main()
