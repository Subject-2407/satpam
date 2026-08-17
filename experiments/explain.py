"""GNNExplainer untuk R-GCN — menghasilkan `criticalSubgraph`.

Menjawab kebutuhan dua pihak sekaligus:

- **Dashboard orang C** — berkas kontrak `experiments/results/critical_subgraphs.json`
  dengan bentuk persis yang diminta `integration/backend/app/services/ml_layer.py`.
  Begitu berkas itu ada, `ml_block()` langsung menyajikannya tanpa perubahan kode.
- **Studi responden** — artefak terbaca manusia di
  `experiments/results/explanations/`: gambar subgraph per kasus dan ringkasan
  teks yang bisa disandingkan dengan `triggeredRules` rule-based.

Yang dihasilkan adalah **1–2 kasus contoh**, bukan seluruh 5.000 node — cukup
untuk demo dan studi responden.

---

**Dua hal yang perlu diketahui sebelum membaca kode.**

*Model dijelaskan pada bentuk rata, bukan `data.hetero`.* R-GCN dilatih atas
representasi rata (`edge_type` 0..15, termasuk relasi balik), jadi itu pula yang
harus dijelaskan — menjelaskan graph yang berbeda dari yang dipakai model akan
menghasilkan penjelasan yang tidak sahih. `data.hetero` tetap dipakai sebagai
acuan arah relasi kanonik saat menulis keluaran.

*Relasi balik dipetakan kembali ke arah maju.* Bentuk rata memuat relasi balik
(`edge_type` 8..15) yang tidak ada di Neo4j maupun di skema relasi kanonik yang
dipakai dashboard. Saat menulis keluaran, edge dengan `edge_type >= 8`
dikembalikan ke bentuk kanoniknya (src dan
dst ditukar, `rel_type = edge_type - 8`) lalu digabung dengan edge maju yang
sama. Tanpa langkah ini, dashboard akan menerima relasi yang arahnya terbalik.

Ground truth tidak pernah masuk ke sini kecuali sebagai keterangan pada artefak
internal. Berkas kontrak untuk dashboard **tidak memuat `gt_*` sama sekali** —
`ml_layer.FORBIDDEN_RESPONSE_KEYS` adalah pertahanan lapis kedua, dan responden
yang melihat ground truth akan membatalkan validitas studi respondennya.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.loader import REL_TYPES, SatpamData, load_seed  # noqa: E402
from models.rgcn import RGCN, train_rgcn  # noqa: E402

RESULTS_DIR = REPO_ROOT / "experiments" / "results"

#: Jumlah edge terpenting yang disimpan per kasus. Subgraph yang terlalu besar
#: tidak lagi menjadi penjelasan — responden harus bisa membacanya sekali lihat.
DEFAULT_TOP_EDGES = 12


def masked_rgcn_layer(
    conv,
    h: torch.Tensor,
    edge_index: torch.Tensor,
    edge_type: torch.Tensor,
    edge_mask: torch.Tensor,
    num_relations: int,
) -> torch.Tensor:
    """Replikasi matematika `RGCNConv` dengan tambahan bobot per edge.

    `RGCNConv` beragregasi `mean` **di dalam tiap relasi**, lalu menjumlahkan
    hasilnya antar-relasi, dan menambahkan bobot akar serta bias:

        out_j = Σ_r  mean_{i∈N_r(j)} ( m_ij · x_i W_r )  +  x_j W_root  +  b

    `m_ij` adalah mask edge yang dioptimalkan GNNExplainer. Penyebut rata-rata
    memakai derajat **asli** (bukan derajat setelah mask) supaya mask hanya
    meredam pesan, bukan diam-diam menaikkan bobot edge yang tersisa.
    """
    weight = conv.weight  # [num_relations, in, out]
    out = h.new_zeros((h.size(0), weight.size(2)))
    src, dst = edge_index[0], edge_index[1]

    for relation in range(num_relations):
        selected = edge_type == relation
        if not bool(selected.any()):
            continue
        src_r, dst_r = src[selected], dst[selected]
        message = (h[src_r] @ weight[relation]) * edge_mask[selected].unsqueeze(-1)

        summed = out.new_zeros(out.shape).index_add_(0, dst_r, message)
        degree = out.new_zeros(out.size(0)).index_add_(
            0, dst_r, torch.ones_like(dst_r, dtype=out.dtype)
        )
        out = out + summed / degree.clamp(min=1.0).unsqueeze(-1)

    if conv.root is not None:
        out = out + h @ conv.root
    if conv.bias is not None:
        out = out + conv.bias
    return out


def masked_forward(
    model: RGCN,
    data: SatpamData,
    edge_mask: torch.Tensor,
) -> torch.Tensor:
    """Forward pass R-GCN dengan mask edge, memakai bobot model terlatih.

    Menirukan `RGCN.forward` dalam mode evaluasi (tanpa dropout). Diverifikasi
    setara dengan model asli saat seluruh mask bernilai 1 — lihat
    `verify_masked_forward`.
    """
    hidden = model.encoders[0].out_features
    h = data.x.new_zeros((data.x.size(0), hidden))
    for type_id, encoder in enumerate(model.encoders):
        rows = data.node_type == type_id
        if bool(rows.any()):
            h = h.index_put((rows.nonzero(as_tuple=True)[0],), encoder(data.x[rows]))

    h = torch.relu(h)
    h = torch.relu(
        masked_rgcn_layer(
            model.conv1, h, data.edge_index, data.edge_type, edge_mask,
            data.num_relations,
        )
    )
    h = masked_rgcn_layer(
        model.conv2, h, data.edge_index, data.edge_type, edge_mask, data.num_relations
    )
    return model.head(torch.relu(h))


def verify_masked_forward(model: RGCN, data: SatpamData) -> float:
    """Pastikan replikasi bermask setara model asli saat mask = 1 seluruhnya.

    Tanpa cek ini, penjelasan bisa saja menerangkan model yang berbeda dari yang
    menghasilkan angka di tabel hasil — kesalahan yang tidak memunculkan error
    apa pun.
    """
    model.eval()
    with torch.no_grad():
        reference = model(data.x, data.node_type, data.edge_index, data.edge_type)
        replica = masked_forward(
            model, data, torch.ones(data.edge_index.size(1), dtype=data.x.dtype)
        )
    return float((reference - replica).abs().max())


def pick_cases_by_id(data: SatpamData, node_ids: list[str]) -> list[int]:
    """Ambil indeks node dari daftar `node_id` eksplisit.

    Dipakai untuk memilih kasus studi responden lewat
    `integration/test_case_candidates.csv` — khususnya node yang skor R-GCN dan
    rule-based-nya **berbeda jauh**, karena di situlah perbandingan dua bentuk
    penjelasan menjadi bermakna. Kasus yang kedua sistemnya sama-sama yakin
    tidak menguji apa pun.
    """
    missing = [n for n in node_ids if n not in data.index_of]
    if missing:
        raise SystemExit(f"node_id tidak ada di seed ini: {missing}")
    return [data.index_of[n] for n in node_ids]


def pick_cases(
    data: SatpamData, prob: np.ndarray, n_cases: int, prefer_true_positive: bool
) -> list[int]:
    """Pilih node yang akan dijelaskan.

    Baku: node dengan skor tertinggi di `split=test` dan bertipe entitas — persis
    node yang akan muncul paling atas di antrean review analis, sehingga
    penjelasannya relevan untuk studi responden.

    `prefer_true_positive=True` menyaring lagi ke node yang memang
    `gt_illicit=1`. Ini **hanya** memilih kasus untuk ditampilkan, tidak menyetel
    model maupun metrik apa pun; berguna agar contoh yang ditampilkan adalah
    deteksi yang benar, bukan false positive yang membingungkan pembaca.
    """
    candidates = (data.test_mask & data.entity_mask).numpy()
    if prefer_true_positive:
        candidates = candidates & (data.y_gt.numpy() == 1)
    index = np.flatnonzero(candidates)
    if index.size == 0:
        raise SystemExit("tidak ada kandidat kasus yang memenuhi syarat")
    return index[np.argsort(-prob[index])][:n_cases].tolist()


def learn_edge_mask(
    model: RGCN,
    data: SatpamData,
    node_index: int,
    *,
    epochs: int = 200,
    lr: float = 0.01,
    size_coeff: float = 0.005,
    entropy_coeff: float = 1.0,
) -> np.ndarray:
    """Optimasi mask edge GNNExplainer (Ying dkk., NeurIPS 2019, arXiv:1903.03894).

    Mencari mask `m ∈ (0,1)` per edge yang **mempertahankan prediksi model** pada
    node sasaran sambil menekan jumlah edge yang dipakai. Fungsi objektifnya
    persis rumusan asli GNNExplainer:

        min_m  −log P(ŷ | G ⊙ σ(m))  +  λ_size·Σσ(m)  +  λ_ent·H(σ(m))

    Suku `size` mendorong mask jadi jarang (penjelasan ringkas), suku entropi
    mendorong tiap nilai mask mendekati 0 atau 1 (tegas, bukan abu-abu).

    **Diimplementasikan langsung, bukan lewat `torch_geometric.explain.Explainer`.**
    Alasannya teknis dan sudah diverifikasi: `RGCNConv` memanggil `propagate()`
    sekali per tipe relasi, sehingga edge mask berukuran seluruh edge tidak cocok
    dengan potongan per-relasi dan PyG gagal (`AssertionError` di
    `message_passing.explain_message`). `FastRGCNConv` memproses seluruh edge
    sekaligus tetapi pada PyG 2.8.0.post1 rusak di bawah mode explain —
    `forward()` memanggil `propagate(..., edge_type=...)` padahal tanda tangan
    yang dihasilkan hanya menerima `edge_type_ptr`. Algoritmanya tetap sama;
    yang berbeda hanya pembungkusnya.
    """
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    with torch.no_grad():
        base = model(data.x, data.node_type, data.edge_index, data.edge_type)
        target = int(base[node_index].argmax())

    # Inisialisasi kecil dan acak, mengikuti implementasi asli.
    generator = torch.Generator().manual_seed(node_index)
    raw = (
        torch.randn(data.edge_index.size(1), generator=generator) * 0.1
    ).requires_grad_(True)
    optimizer = torch.optim.Adam([raw], lr=lr)

    for _ in range(epochs):
        optimizer.zero_grad()
        mask = torch.sigmoid(raw)
        logits = masked_forward(model, data, mask)
        log_probability = torch.log_softmax(logits[node_index], dim=-1)[target]

        size_penalty = size_coeff * mask.sum()
        clamped = mask.clamp(1e-6, 1 - 1e-6)
        entropy = -(clamped * clamped.log() + (1 - clamped) * (1 - clamped).log())
        loss = -log_probability + size_penalty + entropy_coeff * entropy.mean()

        loss.backward()
        optimizer.step()

    return torch.sigmoid(raw).detach().numpy()


def explain_node(
    model: RGCN,
    data: SatpamData,
    node_index: int,
    top_edges: int,
    explainer_epochs: int,
) -> list[dict]:
    """Jelaskan satu node, kembalikan edge terpenting dalam arah kanonik.

    Edge balik dikembalikan ke arah maju, lalu edge yang sama (maju dan balik)
    digabung dengan mengambil kepentingan tertinggi — dashboard dan Neo4j hanya
    mengenal satu arah per relasi.
    """
    mask = learn_edge_mask(model, data, node_index, epochs=explainer_epochs)

    src = data.edge_index[0].numpy()
    dst = data.edge_index[1].numpy()
    rel = data.edge_type.numpy()
    n_forward = len(REL_TYPES)

    merged: dict[tuple[int, int, int], float] = {}
    for position in np.argsort(-mask):
        importance = float(mask[position])
        if importance <= 0.0:
            break
        a, b, r = int(src[position]), int(dst[position]), int(rel[position])
        if r >= n_forward:  # relasi balik -> kembalikan ke arah kanonik
            a, b, r = b, a, r - n_forward
        key = (a, b, r)
        if importance > merged.get(key, 0.0):
            merged[key] = importance

    ordered = sorted(merged.items(), key=lambda item: -item[1])[:top_edges]
    if not ordered:
        return []

    # Dinormalkan ke 0–1 relatif terhadap edge terpenting, sesuai kontrak
    # `importance` di `ml_layer.load_critical_subgraphs`.
    peak = ordered[0][1]
    return [
        {
            "src": data.node_ids[a],
            "dst": data.node_ids[b],
            "relType": REL_TYPES[r],
            "importance": round(value / peak, 4),
        }
        for (a, b, r), value in ordered
    ]


def write_case_report(
    path: Path,
    data: SatpamData,
    node_index: int,
    prob: np.ndarray,
    edges: list[dict],
    seed: int,
) -> None:
    """Tulis ringkasan satu kasus yang bisa dibaca manusia (bahan studi responden)."""
    node_id = data.node_ids[node_index]
    node_type = data.node_type_names[int(data.node_type[node_index])]
    neighbours = {e["src"] for e in edges} | {e["dst"] for e in edges}
    neighbours.discard(node_id)

    lines = [
        f"# Evidence subgraph — {node_id}",
        "",
        f"- **Seed**: {seed}",
        f"- **Tipe node**: {node_type}",
        f"- **Skor risiko model (mlScore)**: {prob[node_index]:.4f}",
        f"- **Skor rule-based**: {float(data.rule_score[node_index]):.4f}",
        f"- **Jumlah entitas terkait pada subgraph**: {len(neighbours)}",
        "",
        "## Relasi paling berkontribusi terhadap skor",
        "",
        "Diurutkan menurut bobot `edge mask` GNNExplainer, dinormalkan ke skor",
        "tertinggi = 1,000. Arah relasi mengikuti kontrak SRS §5.2.",
        "",
        "| # | Dari | Relasi | Ke | Kontribusi |",
        "|---:|---|---|---|---:|",
    ]
    for rank, edge in enumerate(edges, start=1):
        lines.append(
            f"| {rank} | `{edge['src']}` | {edge['relType']} | `{edge['dst']}` "
            f"| {edge['importance']:.3f} |"
        )
    lines += [
        "",
        "> Penjelasan ini menerangkan **mengapa model memberi skor tinggi**, bukan",
        "> bukti hukum. Keputusan akhir tetap pada analis manusia (SRS KT-06).",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def draw_case(path: Path, data: SatpamData, node_index: int, edges: list[dict]) -> bool:
    """Gambar subgraph. Mengembalikan False bila matplotlib/networkx tidak ada."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError:
        return False

    focus = data.node_ids[node_index]
    graph = nx.DiGraph()
    for edge in edges:
        graph.add_edge(
            edge["src"], edge["dst"], label=edge["relType"], weight=edge["importance"]
        )
    if graph.number_of_nodes() == 0:
        return False

    layout = nx.spring_layout(graph, seed=42, k=1.2)
    figure, axis = plt.subplots(figsize=(11, 8))
    colours = ["#c1121f" if n == focus else "#8ecae6" for n in graph.nodes]
    sizes = [1600 if n == focus else 900 for n in graph.nodes]
    widths = [1.0 + 4.0 * graph[u][v]["weight"] for u, v in graph.edges]

    nx.draw_networkx_nodes(graph, layout, node_color=colours, node_size=sizes, ax=axis)
    nx.draw_networkx_edges(
        graph, layout, width=widths, edge_color="#5a5a5a", arrowsize=16,
        node_size=sizes, ax=axis,
    )
    nx.draw_networkx_labels(graph, layout, font_size=7, ax=axis)
    nx.draw_networkx_edge_labels(
        graph, layout,
        edge_labels={(u, v): graph[u][v]["label"] for u, v in graph.edges},
        font_size=6, ax=axis,
    )
    axis.set_title(
        f"Evidence subgraph — {focus}\n"
        f"tebal garis = kontribusi terhadap skor (GNNExplainer)",
        fontsize=11,
    )
    axis.axis("off")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-cases", type=int, default=2, help="SRS §12.3: 1-2 kasus")
    parser.add_argument("--top-edges", type=int, default=DEFAULT_TOP_EDGES)
    parser.add_argument("--explainer-epochs", type=int, default=200)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data" / "synthetic")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument(
        "--any-node",
        action="store_true",
        help="jangan batasi kasus ke node gt_illicit=1",
    )
    parser.add_argument(
        "--nodes",
        nargs="+",
        default=None,
        help="jelaskan node_id tertentu alih-alih memilih otomatis; seluruh node "
        "harus disebut sekaligus karena berkas kontrak ditulis ulang tiap jalan",
    )
    args = parser.parse_args()

    explanations_dir = args.results_dir / "explanations"
    explanations_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== seed {args.seed} ===")
    data = load_seed(args.seed, args.data_root)

    # Model dilatih ulang dengan seed yang sama seperti tabel utama, sehingga
    # bobotnya identik dengan yang menghasilkan angka pada eksperimen utama —
    # tidak perlu berkas .pt karena pelatihan deterministik dan hanya belasan
    # detik.
    print("  melatih ulang R-GCN (deterministik, sama dengan tabel utama)...")
    result = train_rgcn(
        data, epochs=args.epochs, patience=args.patience, torch_seed=args.seed
    )
    print(f"    epoch terbaik {result.best_epoch}, {result.num_parameters} parameter")

    drift = verify_masked_forward(result.model, data)
    if drift > 1e-4:
        raise AssertionError(
            f"replikasi bermask menyimpang dari model asli: {drift:.2e}"
        )
    print(f"    replikasi bermask terverifikasi, selisih maks {drift:.2e}")

    if args.nodes:
        cases = pick_cases_by_id(data, args.nodes)
    else:
        cases = pick_cases(data, result.prob, args.n_cases, not args.any_node)
    print(f"  menjelaskan {len(cases)} kasus...")

    subgraphs: dict[str, dict] = {}
    for node_index in cases:
        node_id = data.node_ids[node_index]
        edges = explain_node(
            result.model, data, node_index, args.top_edges, args.explainer_epochs
        )
        if not edges:
            print(f"    {node_id}: tidak ada edge berbobot, dilewati")
            continue

        nodes = [node_id] + [
            n
            for n in dict.fromkeys(
                [e["src"] for e in edges] + [e["dst"] for e in edges]
            )
            if n != node_id
        ]
        subgraphs[node_id] = {"nodes": nodes, "edges": edges}

        write_case_report(
            explanations_dir / f"{node_id}.md",
            data, node_index, result.prob, edges, args.seed,
        )
        drawn = draw_case(explanations_dir / f"{node_id}.png", data, node_index, edges)
        print(
            f"    {node_id}: skor {result.prob[node_index]:.4f}, "
            f"{len(edges)} edge, {len(nodes)} node"
            f"{'' if drawn else '  (gambar dilewati: matplotlib/networkx tidak ada)'}"
        )

    if not subgraphs:
        raise SystemExit("tidak ada subgraph yang dihasilkan")

    # --- berkas kontrak untuk dashboard orang C ---
    contract = {"seed": args.seed, "model": "rgcn", "subgraphs": subgraphs}
    contract_path = args.results_dir / "critical_subgraphs.json"
    with contract_path.open("w", encoding="utf-8") as handle:
        json.dump(contract, handle, indent=2, ensure_ascii=False)

    forbidden = [k for k in json.dumps(contract) .split('"') if k.startswith("gt_")]
    if forbidden:
        raise AssertionError(f"berkas kontrak memuat kunci ground truth: {forbidden}")

    print(f"\n  kontrak dashboard : {contract_path}")
    print(f"  artefak responden : {explanations_dir}")
    print(
        "\nOrang C tidak perlu mengubah kode apa pun — `ml_layer.load_critical_subgraphs()`\n"
        "membaca berkas itu langsung dari lokasi bawaannya."
    )


if __name__ == "__main__":
    main()
