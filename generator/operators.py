"""LANGKAH 1 — perencanaan operator jaringan. **Ground truth ditanam di sini.**

Ini satu-satunya modul yang memutuskan ada berapa jaringan pelaku, seberapa
besar masing-masing, ekosistem apa yang dijalankannya, dan kapan ia hidup.
Keputusan itulah yang nantinya menjadi `gt_illicit`, `gt_operator_id`, dan
`gt_ecosystem` di `nodes.csv`.

Urutan ini mengikat: keanggotaan operator ditetapkan lebih dulu, jejak bukti
ditaburkan sesudahnya. Karena itu modul ini:

- tidak melihat satu pun fitur node,
- tidak melihat satu pun edge,
- tidak memanggil apa pun yang menghitung skor.

Label tidak boleh menjadi akibat dari bukti. Bukti-lah yang menjadi akibat
dari label. Kalau arah itu terbalik, seluruh eksperimen jadi sirkular dan
klaim "GNN mengungguli rule-based" mustahil dibuktikan — ini aturan keras yang
tidak boleh dilanggar.

Modul ini tidak mengimpor apa pun dari `rules/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from generator.apportion import largest_remainder
from generator.config import GeneratorParams
from generator.schema import ILLICIT_CAPABLE_NODE_TYPES
from generator.timeline import Timeline

#: Format `gt_operator_id` (kontraknya hanya mensyaratkan string).
OPERATOR_ID_TEMPLATE = "OP_{:02d}"


@dataclass(frozen=True)
class OperatorSpec:
    """Rencana satu jaringan pelaku. Isinya adalah ground truth.

    Attributes:
        operator_id: Nilai untuk kolom `gt_operator_id`.
        ecosystem: Nilai untuk kolom `gt_ecosystem` — `judol`, `pinjol`, atau
            `both`. Operator `both` adalah tempat klaim novelty lintas-ekosistem
            diuji.
        size: Jumlah node anggota jaringan ini.
        node_type_counts: Rincian `size` per tipe node.
        birth: Waktu operator mulai beroperasi.
        activity_end: Waktu operator berhenti; sama dengan akhir rentang
            simulasi bila `still_active`.
        still_active: True bila operator belum berhenti sampai akhir rentang.
            Operator inilah penyumbang node positif di split `val`/`test`.
    """

    operator_id: str
    ecosystem: str
    size: int
    node_type_counts: dict[str, int]
    birth: datetime
    activity_end: datetime
    still_active: bool

    def __post_init__(self) -> None:
        if self.ecosystem not in ("judol", "pinjol", "both"):
            raise ValueError(f"ekosistem operator tidak sah: {self.ecosystem!r}")
        if sum(self.node_type_counts.values()) != self.size:
            raise ValueError(
                f"{self.operator_id}: rincian tipe "
                f"({sum(self.node_type_counts.values())}) tidak sama dengan "
                f"size ({self.size})"
            )
        if self.activity_end < self.birth:
            raise ValueError(f"{self.operator_id}: activity_end sebelum birth")

    @property
    def is_cross_ecosystem(self) -> bool:
        """True bila operator menjalankan judol dan pinjol sekaligus (G7)."""
        return self.ecosystem == "both"


@dataclass(frozen=True)
class OperatorPlan:
    """Hasil langkah 1: seluruh rencana jaringan pelaku."""

    operators: tuple[OperatorSpec, ...]
    n_illicit_planned: int
    anomaly_ratio_planned: float
    scale_notes: tuple[str, ...] = ()

    @property
    def n_operators(self) -> int:
        return len(self.operators)

    def ecosystem_counts(self) -> dict[str, int]:
        """Hitungan operator per ekosistem, untuk `manifest.ecosystem_split`."""
        counts = {"judol": 0, "pinjol": 0, "both": 0}
        for operator in self.operators:
            counts[operator.ecosystem] += 1
        return counts

    def node_type_totals(self) -> dict[str, int]:
        """Total node ilegal per tipe di seluruh operator."""
        totals = {node_type: 0 for node_type in sorted(ILLICIT_CAPABLE_NODE_TYPES)}
        for operator in self.operators:
            for node_type, count in operator.node_type_counts.items():
                totals[node_type] += count
        return totals

    def by_id(self) -> dict[str, OperatorSpec]:
        return {operator.operator_id: operator for operator in self.operators}


def plan_operators(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
) -> OperatorPlan:
    """Susun rencana operator — ini tempat ground truth ditetapkan.

    Args:
        params: Parameter generator untuk jumlah operator, anomaly ratio, dan
            jumlah operator lintas-ekosistem.
        rng: Satu-satunya sumber keacakan generator.
        timeline: Rentang simulasi 18 bulan.

    Returns:
        `OperatorPlan` berisi rencana tiap operator. Belum ada `node_id`, belum
        ada fitur, belum ada edge — semuanya urusan langkah berikutnya.
    """
    notes: list[str] = []

    n_illicit = _draw_illicit_total(params, rng)
    n_operators = _draw_operator_count(params, rng, n_illicit, notes)
    sizes = _split_sizes(params, rng, n_illicit, n_operators)
    ecosystems = _assign_ecosystems(params, rng, n_operators, notes)
    pairs = _pair_sizes_with_ecosystems(rng, sizes, ecosystems)

    operators: list[OperatorSpec] = []
    for index, (size, ecosystem) in enumerate(pairs, start=1):
        birth, activity_end, still_active = _draw_activity_window(
            params, rng, timeline
        )
        operators.append(
            OperatorSpec(
                operator_id=OPERATOR_ID_TEMPLATE.format(index),
                ecosystem=ecosystem,
                size=size,
                node_type_counts=_apportion_node_types(params, size, ecosystem),
                birth=birth,
                activity_end=activity_end,
                still_active=still_active,
            )
        )

    planned_total = sum(operator.size for operator in operators)
    return OperatorPlan(
        operators=tuple(operators),
        n_illicit_planned=planned_total,
        anomaly_ratio_planned=planned_total / params.n_nodes_target,
        scale_notes=tuple(notes),
    )


# ---------------------------------------------------------------------------
# Bagian dalam
# ---------------------------------------------------------------------------


def _draw_illicit_total(params: GeneratorParams, rng: np.random.Generator) -> int:
    """Jumlah node ilegal dari anomaly ratio target (4–6% dari total node)."""
    low, high = params.anomaly_ratio
    ratio = float(rng.uniform(low, high))
    return max(1, round(params.n_nodes_target * ratio))


def _draw_operator_count(
    params: GeneratorParams,
    rng: np.random.Generator,
    n_illicit: int,
    notes: list[str],
) -> int:
    """Jumlah operator target (10–14), dipangkas bila skala dikecilkan.

    Pada skala penuh (~5.000 node) rentang target selalu muat. Pemangkasan
    hanya terjadi saat generator dijalankan dengan `--nodes` kecil untuk smoke
    test; catatan pemangkasan dikembalikan agar `build.py` bisa melaporkannya
    dan `validate.py` tahu rentang target tidak berlaku untuk jalan itu.
    """
    low, high = params.n_operators
    drawn = int(rng.integers(low, high + 1))

    feasible = n_illicit // params.min_operator_size
    if feasible < drawn:
        clamped = max(1, feasible)
        notes.append(
            f"jumlah operator dipangkas dari {drawn} ke {clamped}: hanya ada "
            f"{n_illicit} node ilegal dengan min_operator_size="
            f"{params.min_operator_size}, jadi rentang §6.2 ({low}–{high}) "
            f"tidak muat pada skala ini"
        )
        return clamped
    return drawn


def _split_sizes(
    params: GeneratorParams,
    rng: np.random.Generator,
    n_illicit: int,
    n_operators: int,
) -> list[int]:
    """Bagi node ilegal ke antar-operator, timpang tapi tidak ada yang kerdil.

    Setiap operator dijamin mendapat `min_operator_size` lebih dulu; sisanya
    dibagi lewat Dirichlet sehingga ada operator besar dan operator kecil.
    """
    base = min(params.min_operator_size, n_illicit // n_operators)
    sizes = [base] * n_operators
    remainder = n_illicit - base * n_operators

    if remainder > 0:
        weights = rng.dirichlet([params.operator_size_concentration] * n_operators)
        extra = largest_remainder(weights, remainder)
        sizes = [size + add for size, add in zip(sizes, extra)]

    assert sum(sizes) == n_illicit, (sizes, n_illicit)
    return sizes


def _assign_ecosystems(
    params: GeneratorParams,
    rng: np.random.Generator,
    n_operators: int,
    notes: list[str],
) -> list[str]:
    """Tetapkan ekosistem tiap operator (target: 2–3 operator `both`)."""
    low, high = params.n_both_operators
    n_both = int(rng.integers(low, high + 1))

    if n_both > n_operators:
        notes.append(
            f"jumlah operator `both` dipangkas dari {n_both} ke {n_operators}: "
            f"total operator lebih sedikit dari target §6.2"
        )
        n_both = n_operators

    n_single = n_operators - n_both
    n_judol = round(n_single * params.judol_share_of_single_ecosystem)
    n_pinjol = n_single - n_judol

    ecosystems = ["both"] * n_both + ["judol"] * n_judol + ["pinjol"] * n_pinjol
    rng.shuffle(ecosystems)
    return ecosystems


def _pair_sizes_with_ecosystems(
    rng: np.random.Generator,
    sizes: list[int],
    ecosystems: list[str],
) -> list[tuple[int, str]]:
    """Pasangkan ukuran dengan ekosistem; operator `both` dapat ukuran terbesar.

    Bukan klaim empiris, melainkan batasan konstruksi: operator lintas-ekosistem
    menjalankan **dua** operasi sekaligus, jadi ia harus punya cukup materi agar
    kedua sisinya sama-sama utuh — masing-masing sedikitnya satu domain dan satu
    akun finansial. Tanpa batasan ini, operator `both` berukuran kecil bisa
    kebagian satu domain saja, satu sisinya kosong, dan aturan G7 tidak punya
    apa pun untuk digambarkan.

    Ukuran sisa dibagikan acak ke operator judol/pinjol agar tidak ada kaitan
    sistematis antara ekosistem dan ukuran di luar yang disengaja di atas.
    """
    descending = sorted(sizes, reverse=True)
    both_positions = [i for i, eco in enumerate(ecosystems) if eco == "both"]
    other_positions = [i for i, eco in enumerate(ecosystems) if eco != "both"]

    paired: list[tuple[int, str]] = [(0, "")] * len(ecosystems)
    for offset, position in enumerate(both_positions):
        paired[position] = (descending[offset], "both")

    remaining = descending[len(both_positions) :]
    shuffled = [remaining[int(i)] for i in rng.permutation(len(remaining))]
    for size, position in zip(shuffled, other_positions):
        paired[position] = (size, ecosystems[position])

    return paired


def _draw_activity_window(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
) -> tuple[datetime, datetime, bool]:
    """Tentukan kapan satu operator lahir dan sampai kapan ia beroperasi.

    Sebagian operator dibiarkan masih aktif sampai akhir rentang simulasi.
    Merekalah yang akan menaburkan node baru di persentil akhir `first_seen_at`,
    yaitu yang menjadi split `val` dan `test`. Tanpa operator yang masih aktif,
    `test` bisa nyaris tanpa node positif dan AUPRC di sana jadi tidak
    bermakna.
    """
    birth = timeline.sample(rng, 0.0, params.operator_birth_max_frac)
    still_active = bool(rng.random() < params.operator_still_active_prob)

    if still_active:
        return birth, timeline.end, True

    lifespan_low, lifespan_high = params.operator_lifespan_frac
    lifespan_days = float(rng.uniform(lifespan_low, lifespan_high)) * timeline.total_days
    activity_end = timeline.add_days(birth, lifespan_days)
    return birth, activity_end, activity_end >= timeline.end


def _apportion_node_types(
    params: GeneratorParams,
    size: int,
    ecosystem: str,
) -> dict[str, int]:
    """Bagi `size` node satu operator ke tipe-tipe sesuai komposisinya.

    Memakai metode sisa terbesar agar hasilnya deterministik, lalu memastikan
    komposisinya memenuhi syarat minimum: minimal satu domain, satu akun
    finansial, dan satu akun promosi — tanpa itu aturan G1, G5, dan G6 tidak
    punya tempat bekerja.

    Operator lintas-ekosistem butuh dua kali lipat dari syarat itu untuk domain
    dan akun finansial, karena kedua sisinya harus sama-sama utuh (G7).
    """
    node_types = sorted(params.operator_node_type_mix)
    weights = np.array(
        [params.operator_node_type_mix[node_type] for node_type in node_types],
        dtype=float,
    )
    counts = dict(zip(node_types, largest_remainder(weights, size)))
    _ensure_minimum_composition(counts, cross_ecosystem=ecosystem == "both")
    return counts


def _ensure_minimum_composition(
    counts: dict[str, int],
    cross_ecosystem: bool = False,
) -> None:
    """Pastikan komposisi operator memenuhi syarat minimum, di tempat.

    Kekurangan diambil dari tipe yang jumlahnya paling banyak, supaya total
    `size` tidak berubah. Bila operator terlalu kecil untuk memenuhi syarat,
    komposisinya dibiarkan apa adanya — lebih baik begitu daripada mengubah
    `size` secara diam-diam.
    """
    per_side = 2 if cross_ecosystem else 1
    required: tuple[tuple[tuple[str, ...], int], ...] = (
        (("domain",), per_side),
        (("social_account",), 1),
        (("bank_account", "ewallet"), per_side),  # akun finansial
    )

    for group, minimum in required:
        while sum(counts.get(node_type, 0) for node_type in group) < minimum:
            donor = max(
                counts,
                key=lambda node_type: (
                    counts[node_type] if node_type not in group else -1,
                    node_type,
                ),
            )
            if counts[donor] <= 1:
                return
            counts[donor] -= 1
            counts[group[0]] = counts.get(group[0], 0) + 1
