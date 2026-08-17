"""Propagasi feedback analis ke tetangga graph.

**Diadaptasi dari:** P. Kadam, "Enhancing Financial Fraud Detection with
Human-in-the-Loop Feedback and Feedback Propagation," in *Proc. ICMLA*, 2024.
arXiv:2411.05859. https://arxiv.org/abs/2411.05859

Modul ini adalah adaptasi metode Kadam ke domain judol/pinjol ilegal, **bukan
klaim kebaruan** — atribusi ini dinyatakan eksplisit agar posisinya tetap jujur
dan dapat dipertahankan. Kadam sudah melakukan hampir seluruhnya, termasuk basis
teknologinya: SME menganotasi node dengan skor `isFraud` 0–100, skor itu
dipropagasikan iteratif hingga n-hop dengan diskonto berbasis bobot edge dan
cosine similarity, dan iterasi berhenti saat perubahan skor maksimum turun di
bawah ambang.

**Satu-satunya pembeda yang sah, dan jangan dibesar-besarkan:** Kadam memakai
hasil propagasi sebagai **skor akhir** properti node. SATPAM memakainya sebagai
**pseudo-label lemah yang di-denoise lalu masuk ke training loop R-GCN** — jadi
propagasi di sini menghasilkan supervisi, bukan prediksi.

---

Rumus propagasi:

    S_j^(h) = S_j^(h-1) + Σ_i S_i^(h-1) × (W_ij / max W) × sim(i, j)

`W_ij` bobot edge, `sim` cosine similarity fitur node. Berhenti saat
`max|ΔS| < ε` atau `h > 3`.

Dua penyimpangan sadar dari Kadam, keduanya disetujui manusia dan wajib
disebutkan bila hasilnya dilaporkan:

**D1 — Skor awal bertanda.** Kadam memakai skor SME 0–100 dengan 0 berarti
bersih. Anotasi SATPAM berupa `label` biner ditambah `confidence`, sehingga
dipetakan menjadi `S⁰ = +confidence` untuk label 1 dan `−confidence` untuk
label 0. Alasannya praktis: pada anotasi ronde kedua, 82 dari 103 yang boleh
dipakai melatih berlabel 0, sehingga konvensi positif-saja akan membuang sekitar
80% kerja anotator. Rumus di atas tidak bergantung tanda, jadi ini tetap di
dalam kontrak.

Alasan kedua baru terukur setelah ablasi 20 pengulangan, dan lebih menentukan:
manfaat komponen ini justru datang dari label negatif. Dari 124 label pelatihan
yang benar-benar berubah karena umpan balik, 116 berarah 1 → 0 dan 94,8% di
antaranya benar terhadap ground truth. Rule engine menandai 40,2% node latih
sebagai positif sementara laju sebenarnya 6,3%, sehingga kesalahan dominannya
adalah positif palsu — dan itulah yang dikoreksi anotator. Konvensi positif-saja
akan membuang persis bagian yang bekerja.

Catatan koreksi: versi dokumentasi sebelumnya menulis "94 dari 104 anotasi
berlabel 0". Angka itu keliru. 94 adalah jumlah ground truth negatif di antara
104 anotasi ronde pertama; yang berlabel 0 oleh anotator hanya 20. Selain salah,
angka itu berasal dari kolom jawaban, sehingga pembelaan D1 terbaca seolah
keputusan desain dibuat sambil melihat `gt_illicit` — yang dilarang aturan
proyek. Angka pengganti di atas seluruhnya berasal dari label anotator, kecuali
persentase ketepatan yang memang merupakan hasil evaluasi.

**D2 — Cosine similarity dijepit non-negatif.** Fitur sudah distandardisasi
sehingga cosine berada di [−1, 1]. Digabung dengan skor bertanda, cosine negatif
akan **membalik** arah bukti — node yang dinilai bersalah justru akan memilih
tetangganya bersih. Similaritas dimaksudkan sebagai *diskon*, bukan pembalik
tanda, jadi dipakai `max(0, cos)`. Akibat penting yang membuat modul ini aman:
seluruh entri matriks propagasi menjadi tak-negatif, sehingga tanda bukti tidak
pernah terbalik oleh mekanismenya sendiri.

---

Penjagaan kebocoran. Anotasi maupun pseudo-label pada node `val`/`test` tidak
pernah menjadi label pelatihan — `to_supervision` menjepitnya, dan `train_rgcn`
menjepitnya sekali lagi. Propagasi sendiri **boleh melintas** node `val`/`test`:
yang dipakai hanya fitur dan edge-nya, yang pada setelan transductive memang
terlihat, dan label mereka tidak pernah disentuh. Ini didokumentasikan
terang karena terlihat mencurigakan bila ditemukan tanpa penjelasan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch

from .loader import SatpamData

#: Kolom `human_annotations_majority.csv` (keluaran `annotation.build merge`).
#: Bukan bagian skema kontrak asli, tetapi disediakan orang A justru agar orang B
#: tidak mengarang aturan agregasi sendiri — jadi berkas inilah yang dipakai.
MAJORITY_COLUMNS: tuple[str, ...] = (
    "node_id",
    "label",
    "confidence_mean",
    "agreement",
    "n_annotators",
)

#: Kolom `human_annotations.csv` (skema kontrak asli, satu baris per anotator).
#: Dibaca hanya bila berkas mayoritas tidak tersedia.
CONTRACT_COLUMNS: tuple[str, ...] = (
    "node_id",
    "annotator_id",
    "label",
    "confidence",
)

#: Batas hop maksimum untuk propagasi.
DEFAULT_MAX_HOPS: int = 3

#: Ambang konvergensi `max|ΔS| < ε`.
DEFAULT_EPSILON: float = 1e-3

#: Ambang magnitudo agar skor propagasi layak menjadi pseudo-label.
DEFAULT_PSEUDO_THRESHOLD: float = 0.5


@dataclass
class AnnotationSet:
    """Anotasi manusia yang sudah dipetakan ke indeks graph.

    Hanya memuat anotasi yang **lolos seluruh saringan**: node dikenal, berada di
    `split=train`, bertipe entitas, dan (bila diminta) memenuhi ambang
    kesepakatan antar-anotator. Jumlah yang tersaring tercatat di `dropped` agar
    penyusutan jumlah anotasi tidak pernah terjadi diam-diam.
    """

    index: np.ndarray  # indeks global node, [n]
    label: np.ndarray  # 0/1, [n]
    confidence: np.ndarray  # 0..1, [n]
    agreement: np.ndarray | None
    node_ids: list[str]
    source: str
    dropped: dict[str, int] = field(default_factory=dict)

    def __len__(self) -> int:
        return int(self.index.size)

    @property
    def n_positive(self) -> int:
        return int(self.label.sum())


@dataclass
class PropagationResult:
    """Hasil propagasi beserta jejak konvergensinya."""

    score: np.ndarray  # S akhir, [N]
    seed_score: np.ndarray  # S^(0), [N]
    hops_run: int
    converged: bool
    delta_history: list[float]
    diagnostics: dict = field(default_factory=dict)


@dataclass
class SupervisionResult:
    """Label tambahan siap disuapkan ke `train_rgcn`."""

    extra_labels: torch.Tensor  # [N] long 0/1
    extra_mask: torch.Tensor  # [N] bool
    diagnostics: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# Pembacaan anotasi
# --------------------------------------------------------------------------


def read_annotations(
    path: Path | str,
    data: SatpamData,
    *,
    budget: int | None = None,
    min_agreement: float | None = None,
    order: list[str] | None = None,
) -> AnnotationSet:
    """Baca anotasi manusia dan petakan ke indeks graph.

    Menerima dua bentuk berkas dan mengenalinya dari kolom: berkas mayoritas
    (`human_annotations_majority.csv`, satu baris per node) atau berkas skema
    kontrak asli (`human_annotations.csv`, satu baris per anotator per node).
    Bentuk kedua diagregasi dengan suara terbanyak dan rata-rata `confidence`, meniru
    apa yang dilakukan `annotation.build merge`.

    Args:
        budget: ambil hanya `budget` anotasi pertama, untuk ablation A5. Urutan
            yang dipakai adalah `order` bila diberikan — pada data sungguhan itu
            `annotation_order` dari `sample_manifest.json`, yang sudah dirancang
            orang A agar tiap prefiks tetap berimbang strata dan tidak kosong
            dari positif. **Jangan menyubsampel acak sendiri.**
        min_agreement: buang anotasi dengan kesepakatan antar-anotator di bawah
            ambang ini. Bagian pertama dari proses denoise.
    """
    path = Path(path)
    frame = pd.read_csv(path)

    if "confidence_mean" in frame.columns:
        source = "majority"
        _require(frame, MAJORITY_COLUMNS, path.name)
        table = frame.rename(columns={"confidence_mean": "confidence"})
    elif "annotator_id" in frame.columns:
        source = "contract"
        _require(frame, CONTRACT_COLUMNS, path.name)
        table = _aggregate_contract(frame)
    else:
        raise ValueError(
            f"{path.name} tidak dikenali: butuh kolom `confidence_mean` "
            f"(berkas mayoritas) atau `annotator_id` (kontrak §5.3)"
        )

    if not table["label"].isin([0, 1]).all():
        raise ValueError(f"{path.name} memuat label selain 0/1")
    if not table["confidence"].between(0.0, 1.0).all():
        raise ValueError(f"{path.name} memuat confidence di luar 0..1")

    dropped: dict[str, int] = {}

    if order is not None:
        # `order` adalah **petunjuk urutan, bukan saringan.** Anotasi yang tidak
        # tercantum di dalamnya diletakkan di belakang, bukan dibuang: membuang
        # diam-diam pernah membuat 19 dari 20 anotasi lenyap tanpa jejak saat
        # berkas anotasi dan `sample_manifest.json` berasal dari sampel berbeda.
        rank = {node_id: i for i, node_id in enumerate(order)}
        table = table.copy()
        table["_rank"] = table["node_id"].map(rank).fillna(len(rank) + 1)
        table = table.sort_values(["_rank", "node_id"], kind="stable").drop(columns="_rank")
        # Bukan penyusutan — dicatat dengan nama yang menyatakan itu, supaya
        # tidak tertukar dengan anotasi yang benar-benar dibuang.
        dropped["di_luar_urutan_manifest_tetap_dipakai"] = int(
            (~table["node_id"].isin(rank)).sum()
        )
    if budget is not None:
        before = len(table)
        table = table.head(budget)
        dropped["di_luar_anggaran"] = before - len(table)

    if min_agreement is not None and "agreement" in table.columns:
        before = len(table)
        table = table[table["agreement"] >= min_agreement]
        dropped["kesepakatan_rendah"] = before - len(table)

    # --- pemetaan ke indeks graph, lalu tiga saringan kebocoran/cakupan ---
    mapped = table["node_id"].map(data.index_of)
    dropped["node_tak_dikenal"] = int(mapped.isna().sum())
    table = table[mapped.notna()].copy()
    index = mapped[mapped.notna()].to_numpy(dtype=np.int64)

    train = data.train_mask.numpy()
    entity = data.entity_mask.numpy()

    keep_train = train[index]
    dropped["bukan_split_train"] = int((~keep_train).sum())
    table, index = table[keep_train], index[keep_train]

    keep_entity = entity[index]
    dropped["bukan_tipe_entitas"] = int((~keep_entity).sum())
    table, index = table[keep_entity], index[keep_entity]

    return AnnotationSet(
        index=index,
        label=table["label"].to_numpy(dtype=np.int64),
        confidence=table["confidence"].to_numpy(dtype=np.float64),
        agreement=(
            table["agreement"].to_numpy(dtype=np.float64)
            if "agreement" in table.columns
            else None
        ),
        node_ids=table["node_id"].tolist(),
        source=f"{path.name} ({source})",
        dropped=dropped,
    )


def _aggregate_contract(frame: pd.DataFrame) -> pd.DataFrame:
    """Agregasi berkas kontrak menjadi satu baris per node."""
    grouped = frame.groupby("node_id", sort=False)
    votes = grouped["label"].mean()
    return pd.DataFrame(
        {
            "node_id": votes.index,
            # Suara terbanyak; seri diselesaikan ke 1 mengikuti `majority_label`
            # di `annotation/agreement.py`, agar konsisten dengan orang A.
            "label": (votes >= 0.5).astype(int).to_numpy(),
            "confidence": grouped["confidence"].mean().to_numpy(),
            "agreement": grouped["label"]
            .apply(lambda s: max((s == 1).mean(), (s == 0).mean()))
            .to_numpy(),
            "n_annotators": grouped.size().to_numpy(),
        }
    )


def _require(frame: pd.DataFrame, needed: tuple[str, ...], label: str) -> None:
    missing = [name for name in needed if name not in frame.columns]
    if missing:
        raise ValueError(f"{label} kekurangan kolom: {missing}")


# --------------------------------------------------------------------------
# Propagasi
# --------------------------------------------------------------------------


def seed_scores(data: SatpamData, annotations: AnnotationSet) -> np.ndarray:
    """Skor awal `S⁰` bertanda (D1).

    `+confidence` untuk label 1, `−confidence` untuk label 0, nol untuk node
    tanpa anotasi. Besarnya keyakinan anotator langsung menjadi besarnya bukti.
    """
    score = np.zeros(data.num_nodes, dtype=np.float64)
    sign = np.where(annotations.label == 1, 1.0, -1.0)
    score[annotations.index] = sign * annotations.confidence
    return score


def build_propagation_matrix(
    data: SatpamData, *, normalize_by_degree: bool = False
) -> sp.csr_matrix:
    """Susun matriks `M` dengan `M[j, i] = (W_ij / max W) × max(0, cos(x_i, x_j))`.

    Seluruh entri tak-negatif berkat D2, dan itulah yang menjamin propagasi tidak
    pernah membalik tanda bukti.

    Args:
        normalize_by_degree: bagi tiap baris dengan jumlahnya sehingga total
            bobot masuk tiap node menjadi 1. **Bukan bagian rumus aslinya** —
            disediakan sebagai diagnostik untuk mengukur seberapa besar bias
            derajat yang ditimbulkan bentuk aditif rumus aslinya.
    """
    src = data.edge_index[0].numpy()
    dst = data.edge_index[1].numpy()
    weight = data.edge_weight.numpy().astype(np.float64)

    max_weight = float(weight.max())
    if max_weight <= 0:
        raise ValueError("seluruh bobot edge nol, propagasi tidak bermakna")

    x = data.x.numpy().astype(np.float64)
    norm = np.linalg.norm(x, axis=1)
    norm[norm < 1e-12] = 1.0  # node berfitur nol: cosine tak terdefinisi -> 0
    unit = x / norm[:, None]
    cosine = np.einsum("ij,ij->i", unit[src], unit[dst])
    similarity = np.maximum(cosine, 0.0)  # D2

    value = (weight / max_weight) * similarity
    matrix = sp.csr_matrix((value, (dst, src)), shape=(data.num_nodes, data.num_nodes))

    if normalize_by_degree:
        row_sum = np.asarray(matrix.sum(axis=1)).ravel()
        row_sum[row_sum < 1e-12] = 1.0
        matrix = sp.diags(1.0 / row_sum) @ matrix

    return matrix.tocsr()


def propagate_feedback(
    data: SatpamData,
    annotations: AnnotationSet,
    *,
    max_hops: int = DEFAULT_MAX_HOPS,
    epsilon: float = DEFAULT_EPSILON,
    normalize_by_degree: bool = False,
    matrix: sp.csr_matrix | None = None,
) -> PropagationResult:
    """Propagasikan skor anotasi ke tetangga.

    Iterasi `S^(h) = S^(h-1) + M @ S^(h-1)`, berhenti saat `max|ΔS| < ε` atau
    `h > max_hops`.

    > **Catatan penting tentang konvergensi.** Rumus di atas bersifat **aditif tanpa
    > normalisasi derajat**, sehingga jumlah baris `M` sama dengan total bobot
    > tetangga dan dapat jauh melebihi 1 untuk node berderajat tinggi. Akibatnya
    > `max|ΔS|` umumnya **membesar**, bukan mengecil, dan ambang `ε` tidak pernah
    > tercapai — yang menghentikan iterasi dalam praktik adalah batas `h > 3`.
    > Ini sifat rumusnya, bukan cacat implementasi.
    >
    > `normalize_by_degree=True` **tidak** memperbaiki hal itu. Ia menahan jumlah
    > baris `M` pada 1 dan menghapus bias derajat (korelasi log|S| terhadap log
    > derajat turun dari +0,195 menjadi −0,078 pada seed 42), tetapi iterasinya
    > tetap divergen karena bentuk pembaruannya aditif: `S ← S + MS = (I + M)S`
    > punya radius spektral di atas 1 berapa pun normalisasi pada `M`. Terukur
    > pada seed 42 dengan 104 anotasi, `max|ΔS|` tetap membesar 0,900 → 0,957 →
    > 1,580 dan `converged` tetap `False`. Kontraksi baru diperoleh dengan bentuk
    > teredam seperti `S ← (1−α)S⁰ + αMS`, dan itu **di luar rumus aslinya** sehingga
    > butuh persetujuan manusia lebih dulu. Selisih kedua mode tetap dicatat di
    > `diagnostics` agar besar bias derajat dapat dilaporkan, bukan disembunyikan.
    """
    if matrix is None:
        matrix = build_propagation_matrix(data, normalize_by_degree=normalize_by_degree)

    seed = seed_scores(data, annotations)
    score = seed.copy()
    delta_history: list[float] = []
    converged = False
    hops_run = 0

    for hop in range(1, max_hops + 1):
        delta = matrix @ score
        max_delta = float(np.abs(delta).max()) if delta.size else 0.0
        delta_history.append(max_delta)
        score = score + delta
        hops_run = hop
        if max_delta < epsilon:
            converged = True
            break

    row_sum = np.asarray(matrix.sum(axis=1)).ravel()
    reached = int((np.abs(score) > 1e-12).sum())
    diagnostics = {
        "n_annotations": len(annotations),
        "n_seed_nonzero": int((np.abs(seed) > 1e-12).sum()),
        "n_reached": reached,
        "amplification": reached / max(len(annotations), 1),
        "max_abs_seed": float(np.abs(seed).max()) if seed.size else 0.0,
        "max_abs_score": float(np.abs(score).max()),
        "matrix_row_sum_max": float(row_sum.max()),
        "matrix_row_sum_mean": float(row_sum.mean()),
        "normalize_by_degree": normalize_by_degree,
        "epsilon": epsilon,
        "max_hops": max_hops,
    }
    return PropagationResult(
        score=score,
        seed_score=seed,
        hops_run=hops_run,
        converged=converged,
        delta_history=delta_history,
        diagnostics=diagnostics,
    )


# --------------------------------------------------------------------------
# Denoise -> supervisi
# --------------------------------------------------------------------------


def to_supervision(
    data: SatpamData,
    annotations: AnnotationSet,
    propagation: PropagationResult | None = None,
    *,
    pseudo_threshold: float = DEFAULT_PSEUDO_THRESHOLD,
) -> SupervisionResult:
    """Ubah anotasi (dan propagasinya) menjadi `extra_labels` + `extra_mask`.

    Tanpa `propagation` ini adalah **A2** (feedback langsung). Dengan
    `propagation` ini adalah **A3** (feedback + propagasi).

    Urutan denoise berikut, dan urutannya penting:

    1. **Anotasi langsung selalu menang.** Penilaian manusia tidak pernah ditimpa
       nilai hasil propagasi, berapa pun besar skor propagasinya.
    2. Pseudo-label dari propagasi dipakai hanya bila `|S| ≥ pseudo_threshold`.
       Di bawah itu bukti dianggap terlalu tipis dan node mempertahankan weak
       label-nya.
    3. Node `val`/`test` dan tipe non-entitas dibuang. `read_annotations` sudah
       menyaring anotasi langsung; di sini saringan yang sama dikenakan pada
       hasil propagasi, yang bisa menjangkau ke mana saja.
    """
    train = data.train_mask.numpy()
    entity = data.entity_mask.numpy()
    eligible = train & entity

    labels = np.zeros(data.num_nodes, dtype=np.int64)
    mask = np.zeros(data.num_nodes, dtype=bool)

    n_pseudo = 0
    if propagation is not None:
        score = propagation.score
        strong = np.abs(score) >= pseudo_threshold
        pseudo = strong & eligible
        labels[pseudo] = (score[pseudo] > 0).astype(np.int64)
        mask |= pseudo
        n_pseudo = int(pseudo.sum())

    # Langkah 1 dijalankan **setelah** pseudo-label, sehingga anotasi langsung
    # menimpa nilai propagasi pada node yang sama, bukan sebaliknya.
    direct = annotations.index
    labels[direct] = annotations.label
    mask[direct] = True

    overridden = 0
    if propagation is not None and direct.size:
        overridden = int((np.abs(propagation.score[direct]) >= pseudo_threshold).sum())

    diagnostics = {
        "n_direct": len(annotations),
        "n_direct_positive": annotations.n_positive,
        "n_pseudo_before_override": n_pseudo,
        "n_pseudo_overridden_by_direct": overridden,
        "n_supervised_total": int(mask.sum()),
        "n_supervised_positive": int(labels[mask].sum()),
        "pseudo_threshold": pseudo_threshold,
        "annotation_source": annotations.source,
        "dropped": dict(annotations.dropped),
    }
    return SupervisionResult(
        extra_labels=torch.tensor(labels, dtype=torch.long),
        extra_mask=torch.tensor(mask, dtype=torch.bool),
        diagnostics=diagnostics,
    )
