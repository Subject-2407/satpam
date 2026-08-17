"""Empat baseline wajib SATPAM.

| # | Baseline | Yang dibuktikan |
|---|---|---|
| B1 | Rule-based scoring | Pembanding utama; membuktikan nilai tambah ML |
| B2 | MLP fitur-node saja | Memisahkan kontribusi struktur graph dari sekadar fitur |
| B3 | XGBoost + neighbor aggregation | Kejujuran ilmiah; GADBench menunjukkan ini sering menang |
| B4 | GCN homogen | Membuktikan pentingnya heterogenitas relasi |

Semua baseline dilatih dengan protokol yang identik dengan R-GCN: label dari
`weak_labels.csv` saja, loss hanya atas node `train` ∧ enam tipe entitas, early
stopping atas val AUPRC yang juga dihitung terhadap weak label. Tanpa
keseragaman ini, selisih angka bisa berasal dari perbedaan protokol dan bukan
dari perbedaan model.

B3 sengaja diberi fitur yang kuat — agregasi tetangga per tipe relasi sampai dua
hop, sepadan dengan jangkauan R-GCN 2 lapis. Baseline ini wajib dijalankan
justru karena ensemble pohon sering mengalahkan GNN; melemahkannya demi
memenangkan R-GCN akan membatalkan gunanya.
"""

from __future__ import annotations

import copy

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn.functional as F
import xgboost as xgb
from torch import nn

from .loader import SatpamData
from .metrics import evaluate
from .rgcn import TrainResult, class_weights, train_rgcn

# --------------------------------------------------------------------------
# B1 — Rule-based scoring
# --------------------------------------------------------------------------


def score_rule_based(data: SatpamData) -> np.ndarray:
    """Skor rule engine apa adanya, dinormalkan ke 0..1.

    Tidak ada pelatihan: inilah sistem yang sudah ada, dan justru itu yang
    membuatnya menjadi pembanding. Skornya dievaluasi terhadap `gt_illicit`
    dengan mask yang sama seperti model lain, jadi angkanya setara.

    Perhatikan arah pemakaian yang berbeda: `rule_score` di sini adalah
    *prediksi* yang dinilai, sementara pada model lain turunannya (`y_weak`)
    adalah *label* pelatihan. Keduanya sah karena evaluasinya tetap terhadap
    `gt_illicit`.
    """
    return data.rule_score.numpy().astype(np.float64)


# --------------------------------------------------------------------------
# B2 — MLP fitur-node saja
# --------------------------------------------------------------------------


class MLP(nn.Module):
    """MLP dengan kapasitas sepadan R-GCN, tanpa message passing.

    Kedalaman dan lebarnya disamakan dengan R-GCN (dua lapis tersembunyi 64,
    dropout 0,5) supaya selisih hasilnya dapat dibaca sebagai kontribusi
    struktur graph, bukan kontribusi jumlah parameter.
    """

    def __init__(
        self,
        in_dim: int,
        *,
        hidden_dim: int = 64,
        num_classes: int = 2,
        dropout: float = 0.5,
    ) -> None:
        super().__init__()
        self.dropout = dropout
        self.fc1 = nn.Linear(in_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.head = nn.Linear(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = F.dropout(F.relu(self.fc1(x)), p=self.dropout, training=self.training)
        h = F.dropout(F.relu(self.fc2(h)), p=self.dropout, training=self.training)
        return self.head(h)


def train_mlp(
    data: SatpamData,
    *,
    hidden_dim: int = 64,
    dropout: float = 0.5,
    lr: float = 0.01,
    weight_decay: float = 5e-4,
    epochs: int = 200,
    patience: int = 30,
    torch_seed: int = 0,
    verbose: bool = False,
) -> TrainResult:
    """Latih B2 dengan protokol identik R-GCN, hanya tanpa graph."""
    torch.manual_seed(torch_seed)
    model = MLP(data.x.size(1), hidden_dim=hidden_dim, dropout=dropout)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    loss_mask = data.loss_mask
    weights = class_weights(data.y_weak, loss_mask)
    selection_mask = data.val_mask & data.entity_mask
    selection_labels = data.y_weak[selection_mask].numpy()

    best_score, best_epoch, best_state = -np.inf, -1, None
    history: list[dict] = []

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(data.x)
        loss = F.cross_entropy(logits[loss_mask], data.y_weak[loss_mask], weight=weights)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            prob = F.softmax(model(data.x), dim=1)[:, 1]
        score = float(evaluate(selection_labels, prob[selection_mask].numpy())["auprc"])

        history.append(
            {"epoch": epoch, "loss": float(loss.detach()), "val_auprc_weak": score}
        )
        if score > best_score:
            best_score, best_epoch = score, epoch
            best_state = copy.deepcopy(model.state_dict())
        elif epoch - best_epoch >= patience:
            if verbose:
                print(f"    MLP early stopping di epoch {epoch} (terbaik {best_epoch})")
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        logits = model(data.x)
        prob = F.softmax(logits, dim=1)[:, 1]

    return TrainResult(
        model=model,  # type: ignore[arg-type]
        prob=prob.numpy(),
        logit=logits.numpy(),
        best_epoch=best_epoch,
        best_selection_score=best_score,
        history=history,
        num_parameters=sum(p.numel() for p in model.parameters()),
    )


# --------------------------------------------------------------------------
# B3 — XGBoost + neighbor aggregation (XGB-Graph)
# --------------------------------------------------------------------------


def build_neighbor_features(data: SatpamData, *, two_hop: bool = True) -> np.ndarray:
    """Susun matriks fitur XGB-Graph: fitur sendiri + agregasi tetangga.

    Susunan kolom:

    - fitur sendiri (8)
    - rata-rata fitur tetangga **per tipe relasi** (n_rel × 8)
    - derajat per tipe relasi (n_rel)
    - rata-rata fitur tetangga dua hop, seluruh relasi digabung (8), bila
      `two_hop=True`

    Dua hop disertakan agar jangkauan informasinya sepadan dengan R-GCN 2 lapis.
    Memberi XGBoost jangkauan yang lebih pendek akan membuat perbandingan tidak
    adil dan mengalahkan tujuan baseline ini.

    Arah agregasi mengikuti arah message passing R-GCN: tetangga node `i` di
    bawah relasi `r` adalah himpunan `src` dengan edge `(src, i)` bertipe `r`.
    Karena bentuk rata sudah memuat relasi balik, kedua arah tetap tercakup.
    """
    x = data.x.numpy().astype(np.float64)
    n, f = x.shape
    src = data.edge_index[0].numpy()
    dst = data.edge_index[1].numpy()
    rel = data.edge_type.numpy()
    n_rel = data.num_relations

    blocks: list[np.ndarray] = [x]
    degrees = np.zeros((n, n_rel), dtype=np.float64)

    for r in range(n_rel):
        rows = rel == r
        adjacency = sp.csr_matrix(
            (np.ones(int(rows.sum())), (dst[rows], src[rows])), shape=(n, n)
        )
        degree = np.asarray(adjacency.sum(axis=1)).ravel()
        degrees[:, r] = degree
        summed = adjacency @ x
        blocks.append(summed / np.maximum(degree, 1.0)[:, None])

    blocks.append(degrees)

    if two_hop:
        pooled = sp.csr_matrix((np.ones(len(src)), (dst, src)), shape=(n, n))
        degree = np.maximum(np.asarray(pooled.sum(axis=1)).ravel(), 1.0)
        one_hop = (pooled @ x) / degree[:, None]
        blocks.append((pooled @ one_hop) / degree[:, None])

    return np.concatenate(blocks, axis=1)


def train_xgb_graph(
    data: SatpamData,
    *,
    features: np.ndarray | None = None,
    n_estimators: int = 500,
    max_depth: int = 6,
    learning_rate: float = 0.1,
    patience: int = 30,
    seed: int = 0,
) -> TrainResult:
    """Latih B3 atas fitur sendiri + agregasi tetangga.

    Early stopping memakai `aucpr` pada split val terhadap **weak label**,
    konsisten dengan model lain. `scale_pos_weight` menggantikan weighted
    cross-entropy sebagai penyeimbang kelas.
    """
    if features is None:
        features = build_neighbor_features(data)

    loss_mask = data.loss_mask.numpy()
    val_mask = (data.val_mask & data.entity_mask).numpy()
    y_weak = data.y_weak.numpy()

    n_pos = int(y_weak[loss_mask].sum())
    n_neg = int(loss_mask.sum()) - n_pos
    scale_pos_weight = (n_neg / n_pos) if n_pos > 0 else 1.0

    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="aucpr",
        early_stopping_rounds=patience,
        scale_pos_weight=scale_pos_weight,
        random_state=seed,
        n_jobs=-1,
        tree_method="hist",
    )
    model.fit(
        features[loss_mask],
        y_weak[loss_mask],
        eval_set=[(features[val_mask], y_weak[val_mask])],
        verbose=False,
    )

    prob = model.predict_proba(features)[:, 1].astype(np.float64)
    best_iteration = int(getattr(model, "best_iteration", n_estimators) or 0)
    selection = float(evaluate(y_weak[val_mask], prob[val_mask])["auprc"])

    return TrainResult(
        model=model,  # type: ignore[arg-type]
        prob=prob,
        logit=np.stack([np.log1p(-prob + 1e-12), np.log(prob + 1e-12)], axis=1),
        best_epoch=best_iteration,
        best_selection_score=selection,
        history=[],
        num_parameters=int(features.shape[1]),
    )


# --------------------------------------------------------------------------
# B4 — GCN homogen (= ablation A4, tanpa relation typing)
# --------------------------------------------------------------------------


def train_gcn_homogeneous(data: SatpamData, **kwargs) -> TrainResult:
    """Latih B4: model yang sama dengan R-GCN, seluruh relasi disamakan.

    Menurut definisi ablasi, A4 ("tanpa relation typing") **sama dengan** B4
    ("GCN homogen"), jadi keduanya satu angka dan satu jalur kode. Implementasinya
    menjalankan arsitektur R-GCN yang identik dengan `num_relations=1` dan
    seluruh `edge_type` dipaksa nol.

    Ini kontrol yang lebih ketat daripada memakai `GCNConv` terpisah: himpunan
    edge, encoder per tipe node, kapasitas, optimizer, dan protokol early
    stopping seluruhnya sama, sehingga satu-satunya yang berbeda memang hanya
    pembedaan tipe relasi. Kalau `GCNConv` dipakai, selisih hasilnya akan
    bercampur dengan perbedaan skema normalisasi.
    """
    return train_rgcn(
        data,
        num_relations=1,
        edge_type=torch.zeros_like(data.edge_type),
        **kwargs,
    )


#: Nama baseline sebagaimana ditulis ke CSV hasil.
BASELINE_NAMES: dict[str, str] = {
    "B1": "rule_based",
    "B2": "mlp",
    "B3": "xgb_graph",
    "B4": "gcn_homogeneous",
}
