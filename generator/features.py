"""LANGKAH 3 dan 6 — pengisian kolom `feat_*`.

Delapan kolom fitur dibagi dua kelompok dengan waktu pengisian yang berbeda:

**Fitur tertanam** (langkah 3, sebelum edge dibuat) — di-sample dari distribusi
yang bergantung kelas:

- `feat_kw_score`, `feat_is_qris`, `feat_txn_count`, `feat_txn_amount_sum`

**Fitur turunan** (langkah 6, **setelah** noise wajib diterapkan) — dihitung dari
kolom lain dan dari daftar edge final:

- `feat_degree_in`, `feat_degree_out`, `feat_report_count`, `feat_age_days`

Kelompok kedua sengaja dihitung paling akhir. Siapa pun yang menghitung ulang
degree dari `edges.csv` harus mendapat angka yang identik dengan kolomnya; kalau
fitur dihitung sebelum noise, edge yang dibuang oleh noise wajib akan membuat
kolom dan berkas edge saling bertentangan. Efek sampingnya justru yang
diinginkan: noise benar-benar mengurangi sinyal yang teramati.

**Catatan penting soal tumpang tindih kelas.** Distribusi fitur di sini dipilih
supaya tidak ada satu pun fitur yang sendirian membelah kelas. Itu bukan upaya
memperbagus hasil model — justru sebaliknya. Kalau `feat_txn_count` sendirian
sudah memisahkan mule dari rekening sah, ambang sederhana akan mengalahkan
segalanya dan seluruh eksperimen tidak ada gunanya. Di lapangan pun rekening
penampung judol memang tidak bisa dibedakan dari merchant UMKM yang ramai hanya
dari jumlah transaksinya — persis itu alasan struktur graph dibutuhkan, dan
tesis SATPAM berdiri di atas kenyataan itu. Angka setelannya diverifikasi
dengan mengukur AUC tiap fitur satu per satu.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar. Distribusi di sini tidak menghitung skor risiko apa pun; ia
hanya menaburkan atribut menurut kelas yang sudah ditetapkan langkah 1.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np

from generator.config import BetaDist, GammaDist, GeneratorParams, LogNormalDist
from generator.records import EdgeRecord, NodeRecord
from generator.schema import FINANCIAL_NODE_TYPES
from generator.timeline import age_days

#: Tipe node yang punya `feat_kw_score` bermakna, yaitu yang memuat konten
#: promosi. Nomor telepon dan nomor rekening tidak bisa dicocokkan kata kunci,
#: jadi nilainya 0 — sama halnya dengan `feat_is_qris` yang hanya bermakna untuk
#: `ewallet`.
CONTENT_NODE_TYPES: frozenset[str] = frozenset({"domain", "social_account", "apk"})

#: Pembulatan nilai fitur pecahan agar hasil hitung ulang tidak berselisih.
KW_SCORE_DECIMALS: int = 4
AMOUNT_DECIMALS: int = 2


# ---------------------------------------------------------------------------
# LANGKAH 3 — fitur tertanam
# ---------------------------------------------------------------------------


def assign_planted_features(
    params: GeneratorParams,
    rng: np.random.Generator,
    nodes: Iterable[NodeRecord],
) -> None:
    """Isi fitur yang di-sample per node, di tempat.

    Pemilihan distribusi memakai `NodeRecord.apparent_illicit`, bukan
    `gt_illicit`. Di situlah noise wajib bekerja: node hard negative mengambil
    distribusi kelas sah meski ground truth-nya ilegal, dan node hard positive
    sebaliknya.
    """
    for node in nodes:
        _assign_kw_score(params, rng, node)
        _assign_qris(params, rng, node)
        _assign_transactions(params, rng, node)


def _assign_kw_score(
    params: GeneratorParams,
    rng: np.random.Generator,
    node: NodeRecord,
) -> None:
    """`feat_kw_score` — skor kemiripan kata kunci promosi, 0-1.

    Hanya bermakna untuk tipe yang memuat konten (`CONTENT_NODE_TYPES`); tipe
    lain bernilai 0. Akibatnya "tampak mencurigakan" pada node hard positive
    bertipe `phone` tidak muncul lewat fitur ini melainkan lewat laporan yang
    menyebutnya (ditangani `evidence.py`) — dan itu memang wajar, sebab nomor
    telepon tidak punya teks untuk dicocokkan.
    """
    if node.node_type not in CONTENT_NODE_TYPES:
        node.feat_kw_score = 0.0
        return

    dist = (
        params.kw_score_illicit if node.apparent_illicit else params.kw_score_legit
    )
    node.feat_kw_score = round(_sample_beta(rng, dist), KW_SCORE_DECIMALS)


def _assign_qris(
    params: GeneratorParams,
    rng: np.random.Generator,
    node: NodeRecord,
) -> None:
    """`feat_is_qris` — 0/1, hanya bermakna untuk `ewallet`.

    Porsi QRIS pada e-wallet operator memakai `g3_fictitious_merchant_share`
    (aturan generatif G3, sumber PPATK 23 Juli 2026: merchant e-wallet/QRIS
    fiktif atas nama UMKM). Porsi pada e-wallet sah sengaja tidak nol supaya QRIS bukan penanda
    kelas yang sempurna — di lapangan pun QRIS dipakai luas oleh merchant sah.
    """
    if node.node_type != "ewallet":
        node.feat_is_qris = 0
        return

    share = (
        params.g3_fictitious_merchant_share
        if node.apparent_illicit
        else params.legit_qris_share
    )
    node.feat_is_qris = int(rng.random() < share)


def _assign_transactions(
    params: GeneratorParams,
    rng: np.random.Generator,
    node: NodeRecord,
) -> None:
    """`feat_txn_count` dan `feat_txn_amount_sum` — 0 untuk non-finansial.

    Untuk node operator, bentuk distribusinya mengikuti aturan generatif G1
    (PPATK 23 Juli 2026): frekuensi tinggi dengan nominal kecil. Distribusi kelas sah
    dibuat berekor panjang supaya banyak rekening sah juga ramai — tanpa itu
    jumlah transaksi sendirian sudah membelah kelas.

    Nilai ini adalah **volume transaksi teragregasi**, bukan jumlah edge
    `transferred_to`. Edge hanya mewakili aliran yang berhasil dilacak, dan
    noise wajib memang membuang sebagian di antaranya; angka agregat tetap utuh. Itu
    juga cara statistik PPATK bekerja: nilai agregat diketahui jauh lebih
    lengkap daripada peta alirannya.
    """
    if node.node_type not in FINANCIAL_NODE_TYPES:
        node.feat_txn_count = 0.0
        node.feat_txn_amount_sum = 0.0
        return

    if node.node_type == "victim":
        count_dist: GammaDist = params.txn_count_victim
        amount_dist: LogNormalDist = params.txn_amount_victim
    elif node.apparent_illicit:
        count_dist = params.g1_txn_count_illicit
        amount_dist = params.g1_txn_amount_illicit
    else:
        count_dist = params.txn_count_legit
        amount_dist = params.txn_amount_legit

    count = max(0, int(round(_sample_gamma(rng, count_dist))))
    node.feat_txn_count = float(count)
    if count == 0:
        node.feat_txn_amount_sum = 0.0
        return

    mean_amount = _sample_lognormal(rng, amount_dist)
    node.feat_txn_amount_sum = round(count * mean_amount, AMOUNT_DECIMALS)


# ---------------------------------------------------------------------------
# LANGKAH 6 — fitur turunan, dihitung setelah noise wajib
# ---------------------------------------------------------------------------


def recompute_derived_features(
    nodes: Sequence[NodeRecord],
    edges: Sequence[EdgeRecord],
) -> None:
    """Hitung ulang fitur turunan dari daftar edge final, di tempat.

    Wajib dipanggil **setelah** `noise.apply()`. Kalau tidak, `feat_degree_*`
    akan mengacu pada edge yang sudah dibuang dan `nodes.csv` bertentangan
    dengan `edges.csv`.

    Args:
        nodes: Seluruh node; keempat fitur turunannya ditimpa.
        edges: Daftar edge final, sudah termasuk edge yang dibuang dan edge
            palsu akibat noise wajib.
    """
    degree_in: dict[str, int] = {}
    degree_out: dict[str, int] = {}
    report_count: dict[str, int] = {}

    for edge in edges:
        degree_out[edge.src_id] = degree_out.get(edge.src_id, 0) + 1
        degree_in[edge.dst_id] = degree_in.get(edge.dst_id, 0) + 1
        if edge.rel_type == "mentions":
            report_count[edge.dst_id] = report_count.get(edge.dst_id, 0) + 1

    for node in nodes:
        node.feat_degree_in = float(degree_in.get(node.node_id, 0))
        node.feat_degree_out = float(degree_out.get(node.node_id, 0))
        node.feat_report_count = float(report_count.get(node.node_id, 0))
        node.feat_age_days = age_days(node.first_seen_at, node.last_seen_at)


# ---------------------------------------------------------------------------
# Sampling distribusi
# ---------------------------------------------------------------------------


def _sample_beta(rng: np.random.Generator, dist: BetaDist) -> float:
    """Nilai Beta di [0, 1]."""
    return float(rng.beta(dist.a, dist.b))


def _sample_gamma(rng: np.random.Generator, dist: GammaDist) -> float:
    """Nilai Gamma tak-negatif."""
    return float(rng.gamma(dist.shape, dist.scale))


def _sample_lognormal(rng: np.random.Generator, dist: LogNormalDist) -> float:
    """Nilai lognormal, diparameterkan lewat median agar mudah dibaca manusia."""
    return float(rng.lognormal(mean=math.log(dist.median), sigma=dist.sigma))
