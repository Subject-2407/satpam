"""Uji satu perbaikan yang sah: rata-rata prediksi lintas inisialisasi acak.

**Latar belakang.** Pengukuran derau pada 2026-07-30 menunjukkan R-GCN yang
dilatih atas data identik, hanya berbeda bobot awal, menghasilkan AUPRC yang
berayun 0,6318–0,6782 pada seed 42 (lebar 0,046). Ayunan sebesar itu adalah
kelemahan nyata: angka yang dilaporkan sebagian ditentukan undian, bukan model.

**Yang diuji.** Merata-ratakan probabilitas dari `n_init` model dengan bobot
awal berbeda — teknik baku pengurangan varians, bukan penyetelan
hyperparameter. Tidak ada satu pun parameter yang dipilih dengan melihat hasil,
sehingga protokol puritan tetap utuh: `gt_illicit` tetap hanya dibaca saat
evaluasi.

**Kejujuran perbandingan.** Seluruh model neural (R-GCN, MLP, GCN homogen) dan
XGBoost diperlakukan sama — semuanya di-ensemble dengan jumlah anggota yang
sama. Meng-ensemble R-GCN saja lalu membandingkannya dengan baseline sekali
jalan adalah perbandingan yang tidak setara. Rule-based bersifat deterministik
sehingga tidak punya varians inisialisasi; skornya sama persis.

**Pelaporan.** Skrip ini menulis angka sekali-jalan **dan** angka ensemble
berdampingan. Keduanya dilaporkan apa adanya — bukan hanya yang menang.

    python experiments/ensemble.py                 # 6 seed, 5 inisialisasi
    python experiments/ensemble.py --seeds 42 --n-init 3    # cepat
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.baselines import (  # noqa: E402
    build_neighbor_features,
    score_rule_based,
    train_gcn_homogeneous,
    train_mlp,
    train_xgb_graph,
)
from models.loader import load_seed  # noqa: E402
from models.metrics import METRIC_COLUMNS, evaluate  # noqa: E402
from models.rgcn import train_rgcn  # noqa: E402

DEFAULT_SEEDS = (42, 43, 44, 45, 46, 47)
RESULTS_DIR = REPO_ROOT / "experiments" / "results"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--n-init", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data" / "synthetic")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    started = time.perf_counter()

    for seed in args.seeds:
        print(f"\n=== seed {seed} ===")
        data = load_seed(seed, args.data_root)
        y_gt = data.y_gt.numpy()
        features = build_neighbor_features(data)

        # Kumpulkan prediksi tiap anggota ensemble.
        members: dict[str, list[np.ndarray]] = {
            "rgcn": [],
            "mlp": [],
            "gcn_homogeneous": [],
            "xgb_graph": [],
        }
        for k in range(args.n_init):
            torch_seed = seed + k
            members["rgcn"].append(
                train_rgcn(
                    data, epochs=args.epochs, patience=args.patience, torch_seed=torch_seed
                ).prob
            )
            members["mlp"].append(
                train_mlp(
                    data, epochs=args.epochs, patience=args.patience, torch_seed=torch_seed
                ).prob
            )
            members["gcn_homogeneous"].append(
                train_gcn_homogeneous(
                    data, epochs=args.epochs, patience=args.patience, torch_seed=torch_seed
                ).prob
            )
            members["xgb_graph"].append(
                train_xgb_graph(
                    data, features=features, seed=torch_seed, patience=args.patience
                ).prob
            )
            print(f"  init {k + 1}/{args.n_init} selesai")

        # Rule-based deterministik: satu skor, tidak punya varians inisialisasi.
        members["rule_based"] = [score_rule_based(data)]

        for model_name, predictions in members.items():
            stack = np.stack(predictions)
            for scope in ("entity", "all"):
                mask = data.eval_mask("test", scope).numpy()

                # Sekali jalan: anggota pertama, yaitu torch_seed == seed —
                # persis konfigurasi yang menghasilkan tabel hasil utama.
                single = evaluate(y_gt[mask], stack[0][mask])
                # Sebaran antar-inisialisasi, untuk menunjukkan besar deraunya.
                per_init = [evaluate(y_gt[mask], p[mask])["auprc"] for p in stack]
                # Ensemble: rata-rata probabilitas.
                ensemble = evaluate(y_gt[mask], stack.mean(axis=0)[mask])

                rows.append(
                    {
                        "seed": seed,
                        "model": model_name,
                        "scope": scope,
                        "n_init": len(stack),
                        "auprc_single": single["auprc"],
                        "auprc_init_mean": float(np.mean(per_init)),
                        "auprc_init_std": float(np.std(per_init)),
                        "auprc_ensemble": ensemble["auprc"],
                        "gain_vs_single": ensemble["auprc"] - single["auprc"],
                        "gain_vs_init_mean": ensemble["auprc"] - float(np.mean(per_init)),
                        **{f"ens_{name}": ensemble[name] for name in METRIC_COLUMNS},
                    }
                )

    frame = pd.DataFrame(rows)
    frame.to_csv(args.results_dir / "ensemble_results.csv", index=False)

    print("\n" + "=" * 78)
    print("ENSEMBLE INISIALISASI - test, 6 tipe entitas, terhadap gt_illicit")
    print("=" * 78)
    entity = frame[frame["scope"] == "entity"]
    summary = entity.groupby("model", sort=False).agg(
        single_mean=("auprc_single", "mean"),
        single_std=("auprc_single", "std"),
        ens_mean=("auprc_ensemble", "mean"),
        ens_std=("auprc_ensemble", "std"),
        init_std=("auprc_init_std", "mean"),
    )
    order = ["rgcn", "gcn_homogeneous", "xgb_graph", "mlp", "rule_based"]
    print(f"{'model':18}{'sekali jalan':>20}{'ensemble':>20}{'selisih':>10}{'derau init':>12}")
    print("-" * 78)
    for name in order:
        if name not in summary.index:
            continue
        row = summary.loc[name]
        print(
            f"{name:18}{row['single_mean']:>11.4f} +/-{row['single_std']:.4f}"
            f"{row['ens_mean']:>11.4f} +/-{row['ens_std']:.4f}"
            f"{row['ens_mean'] - row['single_mean']:>+10.4f}"
            f"{row['init_std']:>12.4f}"
        )
    print(f"\nSelesai dalam {time.perf_counter() - started:.0f} detik.")
    print(f"Hasil ditulis ke {args.results_dir / 'ensemble_results.csv'}")


if __name__ == "__main__":
    main()
