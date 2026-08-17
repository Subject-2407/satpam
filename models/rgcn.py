"""Model utama SATPAM — R-GCN heterogen 2 lapis.

Hiperparameter berikut dipakai apa adanya: hidden 64, dropout 0,5, Adam
lr 0,01 weight decay 5e-4, weighted cross-entropy dengan bobot kelas berbanding
terbalik dengan frekuensi, 200 epoch, early stopping patience 30 atas val AUPRC.

Dua hal yang perlu diketahui sebelum membaca kode:

**Delapan bobot relasi, bukan 27.** `HeteroData` mengunci relasi pada pasangan
tipe node, sehingga delapan `rel_type` memekar menjadi 27 triplet pada
data nyata. R-GCN memakai bobot terpisah per *relation* dan
delapan adalah kompromi yang dipilih, jadi model ini bekerja pada bentuk rata
dari `loader.py` dengan `edge_type` 0..7 (0..15 bila relasi balik ikut). Lihat
`loader._build_flat` untuk alasan `to_homogeneous()` tidak dipakai.

**Label pelatihan hanya dari rule engine.** Loss dihitung atas `y_weak`
(turunan `weak_labels.csv`), dan early stopping juga memakai weak label di split
val. `gt_illicit` tidak pernah menyentuh pelatihan maupun pemilihan model —
model selection adalah bagian dari pelatihan, jadi memakai `gt` di situ akan
menyelundupkan ground truth lewat pintu belakang. Ini varian puritan yang
dipilih tim: klaim yang dihasilkan menjadi "R-GCN dilatih hanya dari label rule
yang precision-nya 0,14, tetapi mengungguli rule engine itu sendiri terhadap
ground truth".
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import RGCNConv

from .loader import NODE_TYPES, SatpamData
from .metrics import evaluate


class RGCN(nn.Module):
    """R-GCN 2 lapis dengan encoder masukan per tipe node.

    Kedelapan tipe node memakai delapan kolom `feat_*` yang sama, tetapi
    sebagian kolom mati secara struktural pada tipe tertentu — `feat_txn_count`
    selalu nol untuk `domain`, `feat_is_qris` hanya bermakna untuk `ewallet`.
    Encoder `Linear` terpisah per tipe membuat model bisa menafsirkan kolom yang
    sama secara berbeda menurut tipe, alih-alih dipaksa memakai satu proyeksi
    untuk semuanya. Biayanya hanya sekitar 4.600 parameter.

    Kepala klasifikasi dipisahkan dari lapisan konvolusi supaya embedding node
    tetap bisa diambil untuk analisis dan supaya logit punya satu titik keluar
    yang jelas untuk temperature scaling dan GNNExplainer.
    """

    def __init__(
        self,
        in_dim: int,
        num_relations: int,
        *,
        hidden_dim: int = 64,
        num_classes: int = 2,
        dropout: float = 0.5,
        num_bases: int | None = None,
        node_types: tuple[str, ...] = NODE_TYPES,
        conv_cls: type = RGCNConv,
    ) -> None:
        """Args:
        conv_cls: lapisan konvolusi yang dipakai. Baku `RGCNConv`.

            `FastRGCNConv` dipakai **hanya** oleh `experiments/explain.py`:
            `RGCNConv` memecah edge menurut tipe relasi lalu memanggil
            `propagate` sekali per relasi, sehingga edge mask GNNExplainer
            (berukuran seluruh edge) tidak cocok dengan potongan per-relasi dan
            PyG gagal dengan `AssertionError`. `FastRGCNConv` memproses seluruh
            edge dalam satu panggilan sehingga kompatibel.

            Keduanya **secara matematis setara** dan bentuk parameternya identik
            (`weight`, `root`, `bias`), jadi `state_dict` model terlatih dapat
            dimuat langsung ke kembarannya — selisih keluaran terukur 2,4e-07.
            Bedanya hanya jejak memori versus kecepatan.
        """
        super().__init__()
        self.node_types = node_types
        self.dropout = dropout

        self.encoders = nn.ModuleList(
            [nn.Linear(in_dim, hidden_dim) for _ in node_types]
        )
        self.conv1 = conv_cls(hidden_dim, hidden_dim, num_relations, num_bases=num_bases)
        self.conv2 = conv_cls(hidden_dim, hidden_dim, num_relations, num_bases=num_bases)
        self.head = nn.Linear(hidden_dim, num_classes)

    def encode(
        self, x: torch.Tensor, node_type: torch.Tensor, edge_index: torch.Tensor,
        edge_type: torch.Tensor,
    ) -> torch.Tensor:
        """Hasilkan embedding node sebelum kepala klasifikasi."""
        h = x.new_zeros((x.size(0), self.encoders[0].out_features))
        for type_id, encoder in enumerate(self.encoders):
            rows = node_type == type_id
            if bool(rows.any()):
                h[rows] = encoder(x[rows])

        h = F.dropout(F.relu(h), p=self.dropout, training=self.training)
        h = F.relu(self.conv1(h, edge_index, edge_type))
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = self.conv2(h, edge_index, edge_type)
        return h

    def forward(
        self, x: torch.Tensor, node_type: torch.Tensor, edge_index: torch.Tensor,
        edge_type: torch.Tensor,
    ) -> torch.Tensor:
        return self.head(F.relu(self.encode(x, node_type, edge_index, edge_type)))

    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


@dataclass
class TrainResult:
    """Keluaran satu kali pelatihan."""

    model: RGCN
    prob: np.ndarray  # [N] probabilitas kelas 1 untuk seluruh graph
    logit: np.ndarray  # [N, 2] logit mentah, untuk temperature scaling
    best_epoch: int
    best_selection_score: float
    history: list[dict] = field(default_factory=list)
    num_parameters: int = 0


def class_weights(y: torch.Tensor, mask: torch.Tensor, num_classes: int = 2) -> torch.Tensor:
    """Bobot kelas berbanding terbalik dengan frekuensi.

    Dihitung **hanya** atas node yang masuk loss, karena bobot harus mencerminkan
    ketimpangan yang benar-benar dilihat fungsi loss, bukan ketimpangan seluruh
    graph.
    """
    labels = y[mask]
    counts = torch.bincount(labels, minlength=num_classes).float()
    # Kelas yang tidak muncul diberi bobot 0 agar tidak menghasilkan pembagian
    # dengan nol; loss tidak akan pernah memakainya.
    weights = torch.where(
        counts > 0, labels.numel() / (num_classes * counts), torch.zeros_like(counts)
    )
    return weights


def train_rgcn(
    data: SatpamData,
    *,
    hidden_dim: int = 64,
    dropout: float = 0.5,
    lr: float = 0.01,
    weight_decay: float = 5e-4,
    epochs: int = 200,
    patience: int = 30,
    num_bases: int | None = None,
    torch_seed: int = 0,
    num_relations: int | None = None,
    edge_index: torch.Tensor | None = None,
    edge_type: torch.Tensor | None = None,
    extra_labels: torch.Tensor | None = None,
    extra_mask: torch.Tensor | None = None,
    verbose: bool = False,
) -> TrainResult:
    """Latih R-GCN dan kembalikan probabilitas untuk seluruh graph.

    Loss dihitung **hanya** atas `data.loss_mask` (train ∧ 6 tipe entitas) dengan
    label `data.y_weak`. Node `val`/`test` tetap ikut message passing — setelan
    transductive yang memang diizinkan — tetapi tidak pernah masuk loss.

    Args:
        num_relations, edge_index, edge_type: penimpaan struktur graph, dipakai
            ablation A4 (tanpa relation typing) yang menjalankan model yang sama
            atas satu tipe relasi saja.
        extra_labels, extra_mask: supervisi tambahan untuk ablation A2/A3
            (feedback propagation). Node pada `extra_mask` ikut dihitung loss-nya
            memakai `extra_labels`. Kosongkan untuk A1 (tanpa feedback).

    Returns:
        `TrainResult`. `prob` mencakup seluruh node, penyaringan ke split dan
        cakupan tipe dilakukan saat evaluasi.
    """
    torch.manual_seed(torch_seed)

    if edge_index is None:
        edge_index = data.edge_index
    if edge_type is None:
        edge_type = data.edge_type
    if num_relations is None:
        num_relations = data.num_relations

    model = RGCN(
        in_dim=data.x.size(1),
        num_relations=num_relations,
        hidden_dim=hidden_dim,
        dropout=dropout,
        num_bases=num_bases,
        node_types=data.node_type_names,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    loss_mask = data.loss_mask
    train_labels = data.y_weak
    if extra_mask is not None:
        if extra_labels is None:
            raise ValueError("extra_mask diberikan tanpa extra_labels")
        # Node feedback tidak boleh menyeberang ke val/test: supervisi tambahan
        # hanya sah bila node-nya memang ada di split train.
        extra_mask = extra_mask & data.train_mask & data.entity_mask
        train_labels = torch.where(extra_mask, extra_labels, train_labels)
        loss_mask = loss_mask | extra_mask

    weights = class_weights(train_labels, loss_mask)

    # Early stopping memakai weak label di split val, bukan `gt_illicit`.
    selection_mask = data.val_mask & data.entity_mask
    selection_labels = data.y_weak[selection_mask].numpy()

    best_score = -np.inf
    best_state: dict | None = None
    best_epoch = -1
    history: list[dict] = []

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(data.x, data.node_type, edge_index, edge_type)
        loss = F.cross_entropy(logits[loss_mask], train_labels[loss_mask], weight=weights)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            eval_logits = model(data.x, data.node_type, edge_index, edge_type)
            prob = F.softmax(eval_logits, dim=1)[:, 1]
        score = float(
            evaluate(selection_labels, prob[selection_mask].numpy())["auprc"]
        )

        history.append(
            {"epoch": epoch, "loss": float(loss.detach()), "val_auprc_weak": score}
        )
        if score > best_score:
            best_score = score
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
        elif epoch - best_epoch >= patience:
            if verbose:
                print(f"    early stopping di epoch {epoch} (terbaik {best_epoch})")
            break

        if verbose and epoch % 20 == 0:
            print(f"    epoch {epoch:3d} loss={float(loss):.4f} val_auprc_weak={score:.4f}")

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    with torch.no_grad():
        final_logits = model(data.x, data.node_type, edge_index, edge_type)
        final_prob = F.softmax(final_logits, dim=1)[:, 1]

    return TrainResult(
        model=model,
        prob=final_prob.numpy(),
        logit=final_logits.numpy(),
        best_epoch=best_epoch,
        best_selection_score=best_score,
        history=history,
        num_parameters=model.num_parameters(),
    )
