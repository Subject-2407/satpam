"""Mutu deteksi per ekosistem.

Pertanyaan yang dijawab: "Apakah keterkaitan lintas-ekosistem terdeteksi? →
performa khusus pada node `gt_ecosystem=both`"

Mengukur seberapa baik tiap model memisahkan node ilegal **dari tiap ekosistem**
terhadap node sah. Untuk tiap ekosistem `e`, AUPRC dihitung pada himpunan
`{node ber-gt_ecosystem = e} ∪ {node sah}` — jadi angkanya menjawab "seberapa
mudah kelompok ini ditemukan di antara node bersih", bukan "seberapa mudah
membedakan judol dari pinjol".

Berbeda dari `cross_ecosystem.py`, yang menguji apakah **menggabungkan** kedua
ekosistem membantu (hasilnya null). Skrip ini tidak melatih
apa pun — ia membaca ulang `predictions.csv` yang sudah dihasilkan
`train.py --save-predictions`, jadi jalannya beberapa detik.

    python experiments/train.py --save-predictions   # prasyarat
    python experiments/per_ecosystem.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.loader import ENTITY_TYPES  # noqa: E402
from models.metrics import evaluate  # noqa: E402

MODEL_ORDER = ("rgcn", "gcn_homogeneous", "xgb_graph", "mlp", "rule_based")
ECOSYSTEMS = ("judol", "pinjol", "both")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data" / "synthetic")
    parser.add_argument("--results-dir", type=Path, default=REPO_ROOT / "experiments" / "results")
    args = parser.parse_args()

    predictions_path = args.results_dir / "predictions.csv"
    if not predictions_path.is_file():
        raise SystemExit(
            f"{predictions_path} tidak ada.\n"
            f"Hasilkan dulu: python experiments/train.py --save-predictions"
        )

    predictions = pd.read_csv(predictions_path)
    ecosystem_frames = []
    for seed in sorted(predictions["seed"].unique()):
        frame = pd.read_csv(
            args.data_root / f"seed_{seed}" / "nodes.csv",
            usecols=["node_id", "gt_ecosystem"],
        )
        frame["seed"] = seed
        ecosystem_frames.append(frame)
    merged = predictions.merge(pd.concat(ecosystem_frames), on=["seed", "node_id"])

    subset = merged[
        (merged["split"] == "test") & (merged["node_type"].isin(ENTITY_TYPES))
    ]

    rows: list[dict] = []
    for model in MODEL_ORDER:
        for ecosystem in ECOSYSTEMS:
            for seed in sorted(subset["seed"].unique()):
                group = subset[
                    (subset["model"] == model)
                    & (subset["seed"] == seed)
                    & (subset["gt_ecosystem"].isin([ecosystem, "none"]))
                ]
                if group["gt_illicit"].sum() == 0:
                    continue
                rows.append(
                    {
                        "model": model,
                        "ecosystem": ecosystem,
                        "seed": seed,
                        "auprc": evaluate(
                            group["gt_illicit"].to_numpy(), group["prob"].to_numpy()
                        )["auprc"],
                        "n_pos": int(group["gt_illicit"].sum()),
                    }
                )

    frame = pd.DataFrame(rows)
    frame.to_csv(args.results_dir / "per_ecosystem.csv", index=False)

    pivot = frame.pivot_table(index="model", columns="ecosystem", values="auprc")
    print("\n" + "=" * 78)
    print("AUPRC per ekosistem - test, 6 tipe entitas, rata-rata seluruh seed")
    print("positif = ekosistem itu saja; negatif = node sah ('none')")
    print("=" * 78)
    print(f"{'model':18}{'judol':>12}{'pinjol':>12}{'both':>12}{'graph/MLP pada both':>22}")
    print("-" * 78)
    mlp_both = pivot.loc["mlp", "both"] if "mlp" in pivot.index else np.nan
    for model in MODEL_ORDER:
        if model not in pivot.index:
            continue
        row = pivot.loc[model]
        ratio = row["both"] / mlp_both if mlp_both and mlp_both > 0 else np.nan
        print(
            f"{model:18}{row['judol']:>12.4f}{row['pinjol']:>12.4f}{row['both']:>12.4f}"
            f"{ratio:>22.2f}x"
        )

    print(
        "\nBacaan penting: node lintas-ekosistem TIDAK lebih mudah dideteksi daripada"
        "\nnode judol, tetapi jauh lebih bergantung pada struktur graph - bandingkan"
        "\nkolom terakhir dengan rasio yang sama pada kolom judol."
    )
    for model in ("rgcn", "gcn_homogeneous"):
        if model in pivot.index:
            print(
                f"  {model:18} judol {pivot.loc[model, 'judol'] / pivot.loc['mlp', 'judol']:.2f}x MLP"
                f"   |   both {pivot.loc[model, 'both'] / mlp_both:.2f}x MLP"
            )
    print(f"\nHasil ditulis ke {args.results_dir / 'per_ecosystem.csv'}")


if __name__ == "__main__":
    main()
