"""Ablation A1–A3 dan kurva A5.

| # | Kondisi | Cara |
|---|---|---|
| A1 | R-GCN tanpa feedback | `extra_mask=None` |
| A2 | R-GCN + feedback langsung | anotasi manusia, tanpa propagasi |
| A3 | R-GCN + feedback + propagasi | anotasi + pseudo-label yang di-denoise |
| A4 | Tanpa relation typing | **tidak di sini** — sudah selesai sebagai B4 di `train.py` |
| A5 | Performa vs jumlah anotasi | A2 dan A3 pada anggaran 10/25/50/100/150 |

A5 dijalankan **dua garis** (A2 dan A3 berdampingan) supaya grafiknya menampilkan
nilai *marginal* propagasi per anotasi, bukan sekadar performa naik seiring
jumlah anotasi.

Skrip ini sengaja terpisah dari `train.py`: tabel utama tidak boleh ikut berubah
setiap kali ablation dijalankan ulang.

Cara pakai:

    # pengembangan, memakai fixture palsu
    python experiments/ablation.py --annotations tests/fixtures/fake_annotations.csv

    # data sungguhan — cukup ganti path, tidak ada kode yang perlu diubah
    python experiments/ablation.py
    python experiments/ablation.py --annotations data/synthetic/seed_42/human_annotations_majority.csv

Berkas anotasi sungguhan dihasilkan orang A lewat
`python -m annotation.build merge --seed 42`.

---

**Anotasi lebih dari satu ronde.** Sejak ronde kedua, `--annotation-manifest`
menentukan dari mana urutan A5 dibaca. Manifest ini **wajib berasal dari ronde
yang sama** dengan berkas anotasinya: urutan diperlakukan sebagai petunjuk dan
bukan saringan, sehingga manifest yang salah ronde tidak menggugurkan data
maupun memunculkan galat — ia hanya melempar seluruh anotasi ronde lain ke
belakang antrean, dan prefiks A5 kecil jadi mewakili satu ronde saja.

Tiga lengan yang memisahkan pengaruh **mutu** anotasi dari pengaruh
**jumlahnya**; ronde kedua kebetulan menyumbang jumlah node latih yang hampir
sama dengan ronde pertama, sehingga lengan kedua menahan jumlah tetap dan hanya
mengubah mutu. `--results-dir` wajib dibedakan — nama berkas keluarannya tetap,
jadi tanpa itu lengan ketiga menimpa dua lengan sebelumnya:

    D=data/synthetic/seed_42

    # ronde 1 saja, N latih 104, kappa 0,177
    python experiments/ablation.py \
        --annotations $D/human_annotations_majority_anotasi_ronde1.csv \
        --annotation-manifest $D/anotasi_ronde1/sample_manifest.json \
        --results-dir experiments/results/anotasi_ronde1

    # ronde 2 saja, N latih 103, kappa 0,542, mengisolasi mutu
    python experiments/ablation.py \
        --annotations $D/human_annotations_majority_anotasi_ronde2.csv \
        --annotation-manifest $D/anotasi_ronde2/sample_manifest.json \
        --results-dir experiments/results/anotasi_ronde2

    # gabungan, N latih 207, mengisolasi jumlah
    python experiments/ablation.py \
        --annotations $D/human_annotations_majority.csv \
        --annotation-manifest $D/sample_manifest_merged.json \
        --budgets 10 25 50 100 150 200 \
        --results-dir experiments/results/anotasi_gabungan

Kurva A5 lengan pertama dan kedua **jangan disatukan menjadi satu garis**.
Keduanya punya mutu label yang berbeda, sehingga sumbu X gabungannya tidak
mengukur satu besaran pun.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.feedback import (  # noqa: E402
    build_propagation_matrix,
    propagate_feedback,
    read_annotations,
    to_supervision,
)
from models.loader import load_seed  # noqa: E402
from models.metrics import METRIC_COLUMNS, evaluate  # noqa: E402
from models.rgcn import train_rgcn  # noqa: E402

DEFAULT_BUDGETS = (10, 25, 50, 100, 150)
RESULTS_DIR = REPO_ROOT / "experiments" / "results"

#: Subdirektori tempat hasil dari fixture palsu dibuang, agar tidak pernah
#: tercampur dengan hasil resmi.
FIXTURE_SUBDIR = "_fixture_smoke"


def default_annotation_path(seed: int, data_root: Path) -> Path:
    return data_root / f"seed_{seed}" / "human_annotations_majority.csv"


def is_fixture(path: Path) -> bool:
    """Berkas anotasi palsu dikenali dari letaknya di bawah `tests/`."""
    try:
        path.resolve().relative_to(REPO_ROOT / "tests")
    except ValueError:
        return False
    return True


def guard_official_output(annotations: Path, results_dir: Path) -> Path:
    """Cegah hasil dari data palsu mendarat di direktori hasil resmi.

    Fixture di `tests/fixtures/` ada untuk menguji mekanisme, bukan menghasilkan
    angka. Kalau ia dipakai sementara tujuan penulisan adalah direktori resmi,
    keluaran dialihkan ke subdirektori terpisah dan diberi peringatan keras —
    bukan diblokir, supaya pengembangan tetap bisa jalan.
    """
    if not is_fixture(annotations):
        return results_dir
    redirected = results_dir / FIXTURE_SUBDIR
    print("=" * 78)
    print("PERINGATAN: anotasi berasal dari fixture palsu di tests/.")
    print(f"  {annotations}")
    print("  Label di berkas itu dikarang dan tidak berarti apa-apa.")
    print(f"  Keluaran dialihkan ke {redirected} agar tidak tercampur hasil resmi.")
    print("=" * 78)
    return redirected


def default_manifest_path(seed: int, data_root: Path) -> Path:
    return data_root / f"seed_{seed}" / "anotasi_ronde1" / "sample_manifest.json"


def merged_manifest_path(seed: int, data_root: Path) -> Path:
    """Manifest gabungan lintas-ronde, keluaran `annotation.build merge`."""
    return data_root / f"seed_{seed}" / "sample_manifest_merged.json"


def read_annotation_order(path: Path) -> list[str] | None:
    """Urutan `annotation_order` dari sebuah `sample_manifest.json`, bila ada.

    Orang A merancang urutan ini agar tiap prefiks A5 tetap berimbang strata dan
    tidak kosong dari positif (`a5_prefix_note` di manifest). Menyubsampel acak
    sendiri akan merusak sifat itu dan membuat kurva A5 berderau tanpa perlu.

    ⚠️ **Manifestnya harus berasal dari ronde yang sama dengan berkas anotasi.**
    `read_annotations` memperlakukan urutan sebagai petunjuk, bukan saringan,
    sehingga node yang tidak tercantum tidak hilang — tetapi seluruhnya
    terlempar ke belakang antrean. Memakai manifest ronde pertama atas anotasi
    gabungan karena itu tidak menggugurkan data, melainkan membuat prefiks A5
    kecil berisi ronde pertama saja. Kurvanya tetap terbentuk dan tampak wajar,
    padahal yang diukur bukan pengaruh jumlah anotasi. Pemanggilnya wajib
    memeriksa cakupan; lihat peringatan di `main`.
    """
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    nodes = manifest.get("nodes")
    if not nodes:
        return None
    ordered = sorted(nodes, key=lambda row: row.get("annotation_order", 0))
    return [row["node_id"] for row in ordered]


def evaluate_run(prob: np.ndarray, data, *, condition: str, **extra) -> list[dict]:
    """Metrik terhadap `gt_illicit`, dua cakupan."""
    y_gt = data.y_gt.numpy()
    rows = []
    for scope in ("entity", "all"):
        mask = data.eval_mask("test", scope).numpy()
        metrics = evaluate(y_gt[mask], prob[mask])
        rows.append(
            {
                "condition": condition,
                "scope": scope,
                **{name: metrics[name] for name in METRIC_COLUMNS},
                **extra,
            }
        )
    return rows


def run_condition(
    data,
    args: argparse.Namespace,
    *,
    condition: str,
    supervision=None,
) -> tuple[list[dict], dict]:
    """Latih R-GCN pada satu kondisi ablation dan evaluasi.

    Diulang `args.repeats` kali dengan inisialisasi acak berbeda. Ablation ini
    hanya punya satu seed data (anotasi cuma ada untuk seed 42), sehingga tanpa
    pengulangan tidak ada cara membedakan selisih antar-kondisi dari derau
    inisialisasi. Satu baris CSV per pengulangan; agregasi dilakukan saat
    pelaporan.
    """
    rows: list[dict] = []
    scores: list[float] = []
    started = time.perf_counter()

    for repeat in range(args.repeats):
        torch_seed = args.seed + repeat
        result = train_rgcn(
            data,
            epochs=args.epochs,
            patience=args.patience,
            torch_seed=torch_seed,
            extra_labels=None if supervision is None else supervision.extra_labels,
            extra_mask=None if supervision is None else supervision.extra_mask,
        )
        info = {
            "repeat_seed": torch_seed,
            "best_epoch": result.best_epoch,
            "val_auprc_weak": result.best_selection_score,
            "n_supervised": (
                0
                if supervision is None
                else supervision.diagnostics["n_supervised_total"]
            ),
        }
        run_rows = evaluate_run(result.prob, data, condition=condition, **info)
        rows.extend(run_rows)
        scores.append(run_rows[0]["auprc"])

    elapsed = time.perf_counter() - started
    array = np.asarray(scores)
    summary = {
        "auprc_mean": float(array.mean()),
        "auprc_std": float(array.std()),
        "n_supervised": rows[0]["n_supervised"],
    }
    spread = f" +/-{array.std():.4f}" if args.repeats > 1 else ""
    print(
        f"  {condition:24} AUPRC(test,entity)={array.mean():.4f}{spread}"
        f"  supervisi tambahan={summary['n_supervised']:5}  {elapsed:.0f}s"
    )
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data" / "synthetic")
    parser.add_argument(
        "--annotations",
        type=Path,
        default=None,
        help="baku: data/synthetic/seed_{SEED}/human_annotations_majority.csv",
    )
    parser.add_argument(
        "--annotation-manifest",
        type=Path,
        default=None,
        help="manifest sumber urutan A5. Baku: anotasi_ronde1/sample_manifest.json. "
        "Untuk anotasi gabungan beberapa ronde pakai sample_manifest_merged.json; "
        "untuk ronde tunggal pakai manifest ronde itu, contoh "
        "anotasi_ronde2/sample_manifest.json",
    )
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--budgets", type=int, nargs="+", default=list(DEFAULT_BUDGETS))
    parser.add_argument("--pseudo-threshold", type=float, default=0.5)
    parser.add_argument("--min-agreement", type=float, default=None)
    parser.add_argument("--max-hops", type=int, default=3, help="SRS §7.3: 3")
    parser.add_argument("--epsilon", type=float, default=1e-3, help="SRS §7.3")
    parser.add_argument(
        "--normalize-by-degree",
        action="store_true",
        help="diagnostik: normalisasi derajat, di luar rumus §7.3",
    )
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="ulangi tiap kondisi dengan init acak berbeda; wajib >1 agar "
        "selisih antar-kondisi bisa dibedakan dari derau (ablation single-seed)",
    )
    parser.add_argument("--skip-a5", action="store_true")
    args = parser.parse_args()

    annotations_path = args.annotations or default_annotation_path(
        args.seed, args.data_root
    )
    if not annotations_path.is_file():
        raise SystemExit(
            f"berkas anotasi tidak ada: {annotations_path}\n"
            f"Hasilkan dengan: python -m annotation.build merge --seed {args.seed}\n"
            f"Atau uji mekanismenya dengan: "
            f"--annotations tests/fixtures/fake_annotations.csv"
        )

    fixture = is_fixture(annotations_path)
    results_dir = guard_official_output(annotations_path, args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    data = load_seed(args.seed, args.data_root)
    manifest_path = args.annotation_manifest or default_manifest_path(
        args.seed, args.data_root
    )
    order = read_annotation_order(manifest_path)
    stamp = {
        "seed": args.seed,
        "annotation_source": str(annotations_path),
        "annotation_manifest": str(manifest_path),
        "is_fixture": fixture,
    }

    print(f"\n=== seed {args.seed} | anotasi: {annotations_path.name} ===")
    if order is None:
        print(f"  {manifest_path.name} tidak ada; urutan A5 memakai urutan berkas")
    else:
        print(f"  urutan A5 dari: {manifest_path}  ({len(order)} node)")

    gabungan = merged_manifest_path(args.seed, args.data_root)
    if args.annotation_manifest is None and gabungan.is_file():
        print(
            f"  PERHATIAN: ada {gabungan.name} tapi yang dipakai manifest baku. Bila\n"
            f"  berkas anotasinya hasil penggabungan beberapa ronde, jalankan ulang\n"
            f"  dengan --annotation-manifest {gabungan}"
        )

    annotations = read_annotations(
        annotations_path, data, min_agreement=args.min_agreement, order=order
    )
    print(
        f"  anotasi lolos saringan: {len(annotations)} "
        f"(positif {annotations.n_positive}); tersaring {annotations.dropped}"
    )

    # Gejala manifest salah ronde: sebagian besar anotasi tidak tercantum di
    # urutan, sehingga seluruhnya terlempar ke belakang antrean dan prefiks A5
    # kecil hanya berisi ronde yang manifestnya terpakai. Kurvanya tetap
    # terbentuk dan tidak ada galat apa pun — karena itu diperiksa di sini.
    di_luar = annotations.dropped.get("di_luar_urutan_manifest_tetap_dipakai", 0)
    if order is not None and di_luar:
        print(
            f"  PERHATIAN: {di_luar} dari {len(annotations)} anotasi tidak tercantum\n"
            f"  di {manifest_path.name}. Seluruhnya diletakkan di belakang antrean,\n"
            f"  sehingga prefiks A5 kecil tidak mewakili keseluruhan anotasi. Periksa\n"
            f"  apakah manifestnya cocok dengan ronde asal berkas anotasi."
        )
    if len(annotations) == 0:
        raise SystemExit("tidak ada anotasi yang lolos saringan — ablation tidak bermakna")

    # Matriks propagasi tidak bergantung anotasi, jadi dibangun sekali dan
    # dipakai ulang di seluruh kondisi dan seluruh anggaran A5.
    matrix = build_propagation_matrix(
        data, normalize_by_degree=args.normalize_by_degree
    )
    propagation = propagate_feedback(
        data,
        annotations,
        max_hops=args.max_hops,
        epsilon=args.epsilon,
        matrix=matrix,
    )
    print(
        f"  propagasi: {propagation.hops_run} hop, konvergen={propagation.converged}, "
        f"max|dS| per hop={[round(x, 4) for x in propagation.delta_history]}"
    )

    supervision_a2 = to_supervision(data, annotations, None)
    supervision_a3 = to_supervision(
        data, annotations, propagation, pseudo_threshold=args.pseudo_threshold
    )

    # --- A1..A3 ---
    print("\n--- A1-A3 ---")
    rows: list[dict] = []
    diagnostics: dict = {
        "propagation": propagation.diagnostics,
        "delta_history": propagation.delta_history,
        "converged": propagation.converged,
        "hops_run": propagation.hops_run,
        "supervision_a2": supervision_a2.diagnostics,
        "supervision_a3": supervision_a3.diagnostics,
        **stamp,
    }

    for condition, supervision in (
        ("A1_tanpa_feedback", None),
        ("A2_feedback_langsung", supervision_a2),
        ("A3_feedback_propagasi", supervision_a3),
    ):
        run_rows, _ = run_condition(data, args, condition=condition, supervision=supervision)
        rows.extend({**row, **stamp} for row in run_rows)

    pd.DataFrame(rows).to_csv(results_dir / "ablation_a1a3.csv", index=False)

    # --- A5 ---
    if not args.skip_a5:
        # Anggaran bermakna "berapa node yang direview analis", jadi dihitung
        # terhadap jumlah baris di berkas anotasi — BUKAN terhadap jumlah yang
        # lolos saringan train/entity. Memangkas ke angka pasca-saringan pernah
        # membuat anggaran 150 menjadi 104, lalu menyisakan 71 anotasi terpakai:
        # sebuah titik kurva yang tidak mewakili anggaran mana pun.
        available = len(pd.read_csv(annotations_path))
        budgets = sorted({min(b, available) for b in args.budgets})
        if budgets != sorted(set(args.budgets)):
            print(
                f"\n  catatan: berkas hanya memuat {available} anotasi, "
                f"anggaran dipangkas menjadi {budgets}"
            )
        print("\n--- A5: performa vs jumlah anotasi ---")
        curve: list[dict] = []
        for budget in budgets:
            subset = read_annotations(
                annotations_path,
                data,
                budget=budget,
                min_agreement=args.min_agreement,
                order=order,
            )
            subset_prop = propagate_feedback(
                data, subset, max_hops=args.max_hops, epsilon=args.epsilon, matrix=matrix
            )
            conditions = (
                ("A2_feedback_langsung", to_supervision(data, subset, None)),
                (
                    "A3_feedback_propagasi",
                    to_supervision(
                        data, subset, subset_prop, pseudo_threshold=args.pseudo_threshold
                    ),
                ),
            )
            for condition, supervision in conditions:
                print(f"  anggaran {budget:3} | {condition}")
                run_rows, _ = run_condition(
                    data, args, condition=condition, supervision=supervision
                )
                curve.extend(
                    {
                        **row,
                        "budget": budget,
                        "n_annotations_used": len(subset),
                        "n_annotations_positive": subset.n_positive,
                        **stamp,
                    }
                    for row in run_rows
                )
        pd.DataFrame(curve).to_csv(results_dir / "ablation_a5.csv", index=False)

    with (results_dir / "ablation_diagnostics.json").open("w", encoding="utf-8") as handle:
        json.dump(diagnostics, handle, indent=2, default=str)

    _print_report(pd.DataFrame(rows), results_dir, fixture)


def _print_report(rows: pd.DataFrame, results_dir: Path, fixture: bool) -> None:
    print("\n" + "=" * 78)
    print("ABLATION A1-A3 - test, 6 tipe entitas, terhadap gt_illicit")
    print("=" * 78)
    table = rows[rows["scope"] == "entity"]
    grouped = table.groupby("condition", sort=False).agg(
        auprc_mean=("auprc", "mean"),
        auprc_std=("auprc", "std"),
        recall50=("recall_at_50", "mean"),
        recall100=("recall_at_100", "mean"),
        n_supervised=("n_supervised", "first"),
        n=("auprc", "size"),
    )
    print(
        f"{'kondisi':26}{'AUPRC':>18}{'Recall@50':>12}{'Recall@100':>12}{'supervisi':>11}"
    )
    print("-" * 78)
    for condition, row in grouped.iterrows():
        std = 0.0 if pd.isna(row["auprc_std"]) else row["auprc_std"]
        print(
            f"{condition:26}{row['auprc_mean']:>10.4f} +/-{std:.4f}"
            f"{row['recall50']:>12.4f}{row['recall100']:>12.4f}"
            f"{int(row['n_supervised']):>11}"
        )

    # Selisih antar-kondisi hanya bermakna bila melebihi sebaran akibat init
    # acak. Dinyatakan eksplisit supaya tidak dibaca sebagai efek nyata.
    baseline = grouped.iloc[0]
    widest = float(grouped["auprc_std"].fillna(0.0).max())
    print(
        f"\nSebaran terlebar akibat init acak: +/-{widest:.4f} "
        f"({int(grouped['n'].iloc[0])} pengulangan per kondisi)."
    )
    for condition, row in grouped.iloc[1:].iterrows():
        diff = row["auprc_mean"] - baseline["auprc_mean"]
        verdict = "DI DALAM derau" if abs(diff) <= 2 * widest else "di luar derau"
        print(f"  {condition:26} selisih vs A1 = {diff:+.4f}  -> {verdict}")
    if fixture:
        print("\nANGKA DI ATAS TIDAK BERARTI APA-APA - anotasinya palsu.")
        print("Yang diuji di sini adalah mekanismenya, bukan hasilnya.")
    print(f"\nHasil ditulis ke {results_dir}")


if __name__ == "__main__":
    main()
