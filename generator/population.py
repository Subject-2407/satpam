"""LANGKAH 2 — materialisasi node dari rencana operator.

Modul ini mengubah `OperatorPlan` (langkah 1) menjadi daftar node konkret
ber-`node_id`, lengkap dengan `gt_illicit`, `gt_operator_id`, dan
`gt_ecosystem`. Nilai ground truth itu **disalin** dari rencana, tidak dihitung
ulang dan tidak disimpulkan dari apa pun: keanggotaan operator sudah final
sejak langkah 1.

Yang diputuskan di sini selain identitas node:

- **Waktu.** `first_seen_at` / `last_seen_at` tiap node. Termasuk pengaturan
  waktu yang dituntut aturan G2 (rekening dormant) dan G4 (rotasi domain),
  karena keduanya adalah aturan tentang *kapan* sesuatu muncul. Penerbitan
  edge-nya tetap urusan `evidence.py`.
- **Flag noise wajib.** `hard_negative` untuk node ilegal yang nyaris tanpa
  jejak, `hard_positive` untuk node sah yang tampak mencurigakan.
- **Sisi ekosistem (G7).** Tiap node operator diberi `side` judol/pinjol, dan
  sebagian ditandai `shared_infra`. Ini yang membuat penjaga G7 bisa bekerja:
  berbagi infrastruktur boleh, aliran dana lintas-sisi tidak.

Flag-flag di atas adalah **medan internal** dan tidak pernah ditulis ke
`nodes.csv`; pengamannya ada di `NodeRecord.to_csv_row()` di `records.py`.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from generator.apportion import largest_remainder
from generator.config import GeneratorParams
from generator.ids import IdAllocator, sort_key
from generator.operators import OperatorPlan, OperatorSpec
from generator.records import NodeRecord
from generator.schema import ILLICIT_CAPABLE_NODE_TYPES, NODE_TYPES
from generator.timeline import Timeline


@dataclass
class Population:
    """Seluruh node hasil langkah 2 beserta indeks yang dibutuhkan hilir."""

    nodes: tuple[NodeRecord, ...]
    notes: tuple[str, ...] = ()
    _by_id: dict[str, NodeRecord] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self._by_id:
            self._by_id = {node.node_id: node for node in self.nodes}
        if len(self._by_id) != len(self.nodes):
            raise ValueError("ada node_id duplikat di populasi")

    def get(self, node_id: str) -> NodeRecord:
        return self._by_id[node_id]

    def of_type(self, node_type: str) -> list[NodeRecord]:
        return [node for node in self.nodes if node.node_type == node_type]

    def illicit(self) -> list[NodeRecord]:
        return [node for node in self.nodes if node.is_illicit]

    def legit(self) -> list[NodeRecord]:
        return [node for node in self.nodes if not node.is_illicit]

    def of_operator(self, operator_id: str) -> list[NodeRecord]:
        return [node for node in self.nodes if node.gt_operator_id == operator_id]

    def of_operator_type(self, operator_id: str, node_type: str) -> list[NodeRecord]:
        return [
            node
            for node in self.nodes
            if node.gt_operator_id == operator_id and node.node_type == node_type
        ]

    def rotation_chains(self) -> dict[str, list[NodeRecord]]:
        """Rantai rotasi G4, tiap rantai terurut menurut posisinya."""
        chains: dict[str, list[NodeRecord]] = {}
        for node in self.nodes:
            if node.in_rotation_chain:
                chains.setdefault(node.rotation_chain, []).append(node)
        for members in chains.values():
            members.sort(key=lambda node: node.rotation_index)
        return chains

    def type_counts(self) -> dict[str, int]:
        counts = {node_type: 0 for node_type in NODE_TYPES}
        for node in self.nodes:
            counts[node.node_type] += 1
        return counts

    def counts_summary(self) -> dict[str, int]:
        """Ringkasan untuk `manifest.counts` dan diagnostik build."""
        illicit = self.illicit()
        return {
            "nodes": len(self.nodes),
            "illicit_nodes": len(illicit),
            "hard_negatives": sum(node.hard_negative for node in illicit),
            "hard_positives": sum(node.hard_positive for node in self.legit()),
            "dormant_accounts": sum(node.dormant for node in self.nodes),
            "shared_infra_nodes": sum(node.shared_infra for node in self.nodes),
            "rotation_chains": len(self.rotation_chains()),
        }


def build_population(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    plan: OperatorPlan,
    allocator: IdAllocator,
) -> Population:
    """Materialisasi seluruh node: anggota operator lalu latar yang sah.

    Args:
        plan: Hasil langkah 1. Ground truth di sini hanya disalin, tidak
            dihitung ulang.
        allocator: Penerbit `node_id`; dibagi bersama seluruh generator supaya
            tidak ada id yang tabrakan.
    """
    notes: list[str] = []
    nodes: list[NodeRecord] = []

    for operator in plan.operators:
        nodes.extend(
            _build_operator_nodes(params, rng, timeline, operator, allocator)
        )

    nodes.extend(
        _build_legit_nodes(params, rng, timeline, plan, allocator, notes)
    )

    _flag_hard_negatives(params, rng, timeline, nodes, plan)
    _flag_hard_positives(params, rng, nodes, notes)

    nodes.sort(key=lambda node: sort_key(node.node_id))
    return Population(nodes=tuple(nodes), notes=tuple(notes))


# ---------------------------------------------------------------------------
# Node anggota operator
# ---------------------------------------------------------------------------


def _build_operator_nodes(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    operator: OperatorSpec,
    allocator: IdAllocator,
) -> list[NodeRecord]:
    """Materialisasi seluruh node satu operator."""
    nodes: list[NodeRecord] = []

    for node_type, count in sorted(operator.node_type_counts.items()):
        for _ in range(count):
            first_seen = timeline.sample_between(
                rng, operator.birth, operator.activity_end
            )
            node = NodeRecord(
                node_id=allocator.new_id(node_type),
                node_type=node_type,
                first_seen_at=first_seen,
                last_seen_at=first_seen,  # disetel ulang di bawah
                gt_illicit=1,
                gt_operator_id=operator.operator_id,
                gt_ecosystem=operator.ecosystem,
            )
            nodes.append(node)

    _assign_sides(params, rng, operator, nodes)
    _apply_dormant_accounts(params, rng, timeline, operator, nodes)
    _apply_rotation_chains(params, rng, timeline, operator, nodes)
    _assign_illicit_last_seen(params, rng, timeline, operator, nodes)
    return nodes


def _assign_sides(
    params: GeneratorParams,
    rng: np.random.Generator,
    operator: OperatorSpec,
    nodes: list[NodeRecord],
) -> None:
    """G7 — bagi node operator ke sisi judol/pinjol, tandai yang dipakai bersama.

    Aturan generatif G7: operator lintas-ekosistem berbagi rekening mule, APK
    distributor, dan jaringan promosi antara operasi judol dan pinjol ilegal,
    **tanpa** aliran dana langsung judol->pinjol (merujuk pernyataan PPATK
    Oktober 2023).

    Cara membedakan keduanya di sini:

    - Berbagi infrastruktur ditandai `shared_infra`. `evidence.py` boleh
      menautkan node ini ke domain milik sisi mana pun lewat `uses_account`,
      `promotes`, `contacts`, dan `linked_to_apk`. Satu rekening dipakai dua
      operasi memang persis yang dimaksud G7.
    - Aliran dana tidak boleh lintas-sisi. Setiap node tetap punya satu `side`
      yang pasti, termasuk node `shared_infra`, dan `transferred_to` hanya
      diterbitkan antar node bersisi sama. `validate.py` menegakkan ini.

    Untuk operator satu ekosistem, semua node bersisi sama dengan ekosistemnya
    dan tidak ada yang ditandai `shared_infra`.

    Pembagian dilakukan berimbang **per tipe node**, bukan lewat koin per node.
    Koin per node sempat membuat satu sisi kebagian jauh lebih sedikit
    (mis. 15 lawan 7), dan sisi yang kurus bisa kehabisan domain atau rekening
    sehingga operasinya tidak lagi utuh — padahal G7 justru bertumpu pada
    adanya dua operasi yang sama-sama berjalan.
    """
    if not operator.is_cross_ecosystem:
        for node in nodes:
            node.side = operator.ecosystem
        return

    #: Tipe yang masuk akal dipakai bersama dua operasi sekaligus.
    shareable = {"bank_account", "ewallet", "apk", "social_account"}

    by_type: dict[str, list[NodeRecord]] = {}
    for node in nodes:
        by_type.setdefault(node.node_type, []).append(node)

    for node_type, members in sorted(by_type.items()):
        order = rng.permutation(len(members))
        # Sisi awal diacak agar tipe berjumlah ganjil tidak selalu menguntungkan
        # sisi yang sama.
        flip = int(rng.random() < 0.5)
        for position, index in enumerate(order):
            node = members[int(index)]
            node.side = "judol" if (position + flip) % 2 == 0 else "pinjol"
            if node_type in shareable:
                node.shared_infra = bool(rng.random() < params.g7_shared_infra_share)


def _apply_dormant_accounts(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    operator: OperatorSpec,
    nodes: list[NodeRecord],
) -> None:
    """G2 — sebagian rekening penampung adalah rekening dormant yang diambil alih.

    Aturan generatif G2, sumber PPATK: rekening penampung berupa proxy account
    hasil jual-beli rekening; sebagian rekening dormant yang diambil alih.

    Wujudnya pada data: `first_seen_at` rekening jauh **sebelum** operatornya
    lahir — rekening itu sudah ada lama, lalu baru dipakai. Node seperti ini
    juga yang menahan agar `feat_age_days` tidak menjadi penanda kelas yang
    rapi, karena umurnya justru panjang.
    """
    accounts = [node for node in nodes if node.node_type == "bank_account"]
    for account in accounts:
        if rng.random() >= params.g2_dormant_account_share:
            continue
        idle_low, idle_high = params.g2_dormant_idle_days
        idle_days = int(rng.integers(idle_low, idle_high + 1))
        account.dormant = True
        account.first_seen_at = timeline.add_days(operator.birth, -idle_days)


def _apply_rotation_chains(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    operator: OperatorSpec,
    nodes: list[NodeRecord],
) -> None:
    """G4 — susun rantai rotasi domain dan atur waktu kemunculannya.

    Aturan generatif G4, sumber Komdigi/TrustPositif: domain dirotasi berkala;
    domain lama `redirects_to` domain baru.

    Di sini hanya *waktu* dan keanggotaan rantainya yang ditetapkan: anggota
    rantai muncul berurutan dengan jeda `g4_rotation_gap_days`. Edge
    `redirects_to`-nya diterbitkan `evidence.py` dari metadata rantai ini.

    Bila jendela aktif operator terlalu sempit untuk seluruh jeda, jeda
    dipadatkan proporsional alih-alih menabrak batas jendela.

    Rantai tidak boleh melintasi sisi ekosistem. Satu rantai rotasi adalah satu
    operasi yang mengganti domainnya sendiri; kalau anggotanya bercampur, akan
    ada edge `redirects_to` yang menyambungkan domain judol ke domain pinjol dan
    kedua sisi operator `both` berhenti bisa dibedakan. Tautan antar sisi hanya
    boleh datang dari infrastruktur bersama G7.
    """
    chain_index = 0
    for side in sorted({node.side for node in nodes if node.side}):
        chain_index = _build_rotation_chains_for_side(
            params, rng, timeline, operator, nodes, side, chain_index
        )


def _build_rotation_chains_for_side(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    operator: OperatorSpec,
    nodes: list[NodeRecord],
    side: str,
    chain_index: int,
) -> int:
    """Susun rantai rotasi G4 untuk satu sisi ekosistem. Kembalikan nomor rantai."""
    domains = [
        node for node in nodes if node.node_type == "domain" and node.side == side
    ]
    if len(domains) < 2:
        return chain_index

    order = list(rng.permutation(len(domains)))
    rotated_count = int(round(len(domains) * params.g4_rotated_domain_share))
    if rotated_count < 2:
        return chain_index

    pool = [domains[i] for i in order[:rotated_count]]
    cursor = 0

    while len(pool) - cursor >= 2:
        low, high = params.g4_rotation_chain_len
        length = int(rng.integers(low, high + 1))
        length = min(length, len(pool) - cursor)
        if length < 2:
            break

        members = pool[cursor : cursor + length]
        cursor += length
        chain_index += 1
        chain_id = f"{operator.operator_id}_chain{chain_index:02d}"

        gap_low, gap_high = params.g4_rotation_gap_days
        gaps = [
            float(rng.integers(gap_low, gap_high + 1)) for _ in range(length - 1)
        ]

        window_days = (
            operator.activity_end - operator.birth
        ).total_seconds() / 86_400.0
        total_gap = sum(gaps)
        if total_gap > window_days > 0:
            scale = window_days / total_gap
            gaps = [gap * scale for gap in gaps]
            total_gap = sum(gaps)

        # Rantai tidak boleh mulai sebelum operatornya lahir. Kalau jendela
        # aktif tetap tidak cukup, rantai dimulai tepat di kelahiran operator.
        latest_start = timeline.add_days(operator.activity_end, -total_gap)
        if latest_start <= operator.birth:
            start = operator.birth
        else:
            start = timeline.sample_between(rng, operator.birth, latest_start)

        moment = start
        for position, member in enumerate(members):
            if position > 0:
                moment = timeline.add_days(moment, gaps[position - 1])
            member.rotation_chain = chain_id
            member.rotation_index = position
            member.first_seen_at = moment

    return chain_index


def _assign_illicit_last_seen(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    operator: OperatorSpec,
    nodes: list[NodeRecord],
) -> None:
    """Tetapkan `last_seen_at` node operator.

    Tiga perlakuan:

    - Domain yang punya penerus dalam rantai rotasi G4 mati tak lama setelah
      penerusnya muncul — itulah arti rotasi. Masa tumpang tindihnya diatur
      `rotation_overlap_days`.
    - Node operator yang masih aktif hidup sampai akhir rentang simulasi.
    - Node operator yang sudah berhenti mati di sekitar `activity_end`, dengan
      ekor beberapa hari karena infrastruktur tidak mati serentak.
    """
    successors: dict[str, NodeRecord] = {}
    chains: dict[str, list[NodeRecord]] = {}
    for node in nodes:
        if node.in_rotation_chain:
            chains.setdefault(node.rotation_chain, []).append(node)
    for members in chains.values():
        members.sort(key=lambda node: node.rotation_index)
        for current, following in zip(members, members[1:]):
            successors[current.node_id] = following

    overlap_low, overlap_high = params.rotation_overlap_days
    tail_low, tail_high = params.illicit_lifespan_tail_days

    for node in nodes:
        successor = successors.get(node.node_id)
        if successor is not None:
            overlap = int(rng.integers(overlap_low, overlap_high + 1))
            candidate = timeline.add_days(successor.first_seen_at, overlap)
        elif operator.still_active:
            candidate = timeline.sample_between(
                rng, node.first_seen_at, timeline.end
            )
            # Sebagian besar infrastruktur operator aktif masih hidup di akhir.
            if rng.random() < 0.7:
                candidate = timeline.end
        else:
            tail = int(rng.integers(tail_low, tail_high + 1))
            candidate = timeline.add_days(operator.activity_end, tail)

        node.last_seen_at = max(candidate, node.first_seen_at)


# ---------------------------------------------------------------------------
# Node latar yang sah
# ---------------------------------------------------------------------------


def _build_legit_nodes(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    plan: OperatorPlan,
    allocator: IdAllocator,
    notes: list[str],
) -> list[NodeRecord]:
    """Materialisasi node sah sebagai latar graph.

    `gt_illicit=0`, `gt_operator_id` kosong, `gt_ecosystem='none'` — persis
    seperti yang dituntut kontrak untuk node di luar jaringan pelaku.
    """
    legit_counts = _apportion_legit_counts(params, plan, notes)
    nodes: list[NodeRecord] = []

    for node_type in NODE_TYPES:
        for _ in range(legit_counts[node_type]):
            first_seen = timeline.sample(rng)
            nodes.append(
                NodeRecord(
                    node_id=allocator.new_id(node_type),
                    node_type=node_type,
                    first_seen_at=first_seen,
                    last_seen_at=_legit_last_seen(params, rng, timeline, first_seen),
                    gt_illicit=0,
                    gt_operator_id="",
                    gt_ecosystem="none",
                )
            )
    return nodes


def _legit_last_seen(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    first_seen: datetime,
) -> datetime:
    """Umur node sah, sengaja dibuat bertumpang tindih dengan node ilegal.

    Kalau seluruh node sah berumur panjang sementara node ilegal berumur pendek
    karena ditertibkan, `feat_age_days` sendirian sudah memisahkan kedua kelas
    dan seluruh angka AUPRC jadi tidak berarti. Karena itu sebagian node sah
    juga dibuat mati muda.
    """
    if rng.random() < params.legit_still_up_prob:
        return timeline.end

    low, high = params.legit_lifespan_frac
    lifespan_days = float(rng.uniform(low, high)) * timeline.total_days
    return max(timeline.add_days(first_seen, lifespan_days), first_seen)


def _apportion_legit_counts(
    params: GeneratorParams,
    plan: OperatorPlan,
    notes: list[str],
) -> dict[str, int]:
    """Hitung jumlah node sah per tipe: target keseluruhan dikurangi node ilegal.

    `node_type_mix` menyatakan komposisi seluruh graph, jadi node ilegal yang
    sudah dibuat langkah 1 ikut mengisi kuota tipenya masing-masing.
    """
    node_types = list(NODE_TYPES)
    weights = np.array(
        [params.node_type_mix[node_type] for node_type in node_types], dtype=float
    )
    totals = dict(
        zip(node_types, largest_remainder(weights, params.n_nodes_target))
    )
    illicit_totals = plan.node_type_totals()

    counts: dict[str, int] = {}
    overflow: list[str] = []
    for node_type in node_types:
        available = totals[node_type] - illicit_totals.get(node_type, 0)
        if available < 0:
            overflow.append(f"{node_type} ({-available} node)")
            available = 0
        counts[node_type] = available

    if overflow:
        notes.append(
            "node ilegal melewati kuota tipenya sehingga total node melebihi "
            f"n_nodes_target: {', '.join(overflow)}"
        )

    shortfall = params.n_nodes_target - plan.n_illicit_planned - sum(counts.values())
    if shortfall > 0:
        # Tambal ke tipe yang porsinya terbesar agar total tetap tepat.
        for node_type in sorted(
            node_types, key=lambda t: -params.node_type_mix[t]
        ):
            if shortfall <= 0:
                break
            counts[node_type] += 1
            shortfall -= 1

    return counts


# ---------------------------------------------------------------------------
# Noise wajib — penandaan
# ---------------------------------------------------------------------------


def _flag_hard_negatives(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    nodes: list[NodeRecord],
    plan: OperatorPlan,
) -> None:
    """Tandai 15–20% node ilegal sebagai nyaris tanpa jejak.

    Dua pembatasan pada siapa yang boleh terpilih:

    - `phone` hanya boleh terpilih bila operatornya punya sedikitnya dua nomor,
      sehingga selalu ada nomor yang tetap menjadi simpul bersama G6. Mula-mula
      `phone` dikecualikan sepenuhnya, tetapi akibatnya seluruh nomor operator
      menjadi hub G6 penuh tanpa kekecualian — populasinya jadi terlalu seragam
      dan derajatnya sendirian membelah kelas pada AUC 0,94. Operator dengan
      nomor cadangan yang jarang dipakai justru hal yang wajar.
    - Domain anggota rantai rotasi hanya boleh terpilih bila ia yang terakhir
      dalam rantai. Domain di tengah rantai punya penerus dan pendahulu, jadi
      jejaknya tidak mungkin ditekan tanpa membatalkan G4. Domain terakhir
      justru kandidat paling wajar: ia yang paling baru dipasang.

    Pemilihannya dibobot ke arah node yang paling baru muncul di dalam masa
    hidup operatornya (`hard_negative_recency_bias`), karena infrastruktur baru
    memang belum punya jejak.
    """
    illicit = [node for node in nodes if node.is_illicit]
    if not illicit:
        return

    low, high = params.hard_negative_share
    target = int(round(len(illicit) * float(rng.uniform(low, high))))
    if target <= 0:
        return

    chains: dict[str, int] = {}
    for node in illicit:
        if node.in_rotation_chain:
            chains[node.rotation_chain] = max(
                chains.get(node.rotation_chain, -1), node.rotation_index
            )

    phones_per_operator: dict[str, int] = {}
    for node in illicit:
        if node.node_type == "phone":
            phones_per_operator[node.gt_operator_id] = (
                phones_per_operator.get(node.gt_operator_id, 0) + 1
            )

    operators = plan.by_id()
    eligible: list[NodeRecord] = []
    weights: list[float] = []
    for node in illicit:
        if node.node_type == "phone" and phones_per_operator[node.gt_operator_id] < 2:
            continue
        if node.in_rotation_chain and node.rotation_index != chains[node.rotation_chain]:
            continue

        operator = operators[node.gt_operator_id]
        window = (operator.activity_end - operator.birth).total_seconds()
        if window > 0:
            recency = (
                node.first_seen_at - operator.birth
            ).total_seconds() / window
        else:
            recency = 1.0
        recency = float(np.clip(recency, 0.0, 1.0))

        eligible.append(node)
        weights.append(1.0 + params.hard_negative_recency_bias * recency)

    if not eligible:
        return

    target = min(target, len(eligible))
    probabilities = np.array(weights, dtype=float)
    probabilities /= probabilities.sum()
    chosen = rng.choice(
        len(eligible), size=target, replace=False, p=probabilities
    )
    for index in chosen:
        eligible[int(index)].hard_negative = True


def _flag_hard_positives(
    params: GeneratorParams,
    rng: np.random.Generator,
    nodes: list[NodeRecord],
    notes: list[str],
) -> None:
    """Tandai 3–5% node sah sebagai tampak mencurigakan.

    Jumlahnya dihitung dari **seluruh** node sah sesuai target itu, tetapi yang
    boleh terpilih hanya tipe infrastruktur: `report` atau `victim` yang
    "tampak mencurigakan" tidak ada artinya. Akibatnya porsi terhadap subset
    infrastruktur sedikit lebih tinggi daripada angka targetnya, dan itu memang
    disengaja.
    """
    legit = [node for node in nodes if not node.is_illicit]
    if not legit:
        return

    low, high = params.hard_positive_share
    target = int(round(len(legit) * float(rng.uniform(low, high))))
    if target <= 0:
        return

    eligible = [
        node for node in legit if node.node_type in ILLICIT_CAPABLE_NODE_TYPES
    ]
    if not eligible:
        return

    if target > len(eligible):
        notes.append(
            f"target hard positive ({target}) melebihi node sah bertipe "
            f"infrastruktur ({len(eligible)}); dipangkas"
        )
        target = len(eligible)

    chosen = rng.choice(len(eligible), size=target, replace=False)
    for index in chosen:
        eligible[int(index)].hard_positive = True
