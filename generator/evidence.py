"""LANGKAH 4 — penaburan jejak bukti (edge) di atas ground truth yang sudah final.

Setiap fungsi `_sow_g*` di modul ini mewujudkan satu aturan generatif (G1-G8)
dan mencantumkan sumbernya di docstring. Tidak ada aturan generatif di luar
kedelapan itu; wiring latar untuk node sah dan penerbitan laporan diberi tanda
eksplisit sebagai **bukan** aturan generatif supaya tidak ada yang
mengutipnya sebagai temuan bersitasi.

Modul ini membaca keanggotaan operator dan tidak pernah mengubahnya. Arahnya
satu jalan: label -> bukti. Tidak ada skor yang dihitung di sini, dan tidak
ada apa pun yang diimpor dari `rules/` — ini aturan keras yang tidak boleh
dilanggar.

Dua penjaga struktural yang penting:

1. `EdgeSink.add()` menolak keras triple `(src_type, rel_type, dst_type)` yang
   tidak sah menurut kontrak tipe edge yang berlaku. Melanggar kontrak itu
   adalah bug program, bukan noise data, jadi ia melempar exception
   alih-alih diam-diam menulis edge cacat.
2. Aliran dana `transferred_to` tidak pernah diterbitkan antar node bersisi
   ekosistem berbeda. Ini tuntutan catatan validitas G7 (PPATK Oktober 2023
   belum menemukan aliran dana judol langsung ke pinjol) dan diperiksa ulang
   oleh `validate.py`.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np

from generator.config import GeneratorParams, IntRange
from generator.operators import OperatorPlan, OperatorSpec
from generator.population import Population
from generator.records import EdgeRecord, NodeRecord
from generator.schema import is_legal_edge
from generator.timeline import Timeline
from generator.weights import sample_weight


class EdgeSink:
    """Penampung edge yang menjaga kontrak tipe edge dan mencegah duplikat.

    Waktu edge dihitung otomatis: sebuah edge tidak bisa ada sebelum kedua
    ujungnya ada, jadi `first_seen_at` diambil di dalam jendela hidup bersama
    keduanya. Aturan-aturan di bawah tidak perlu mengurusnya sendiri, dan
    hasilnya konsisten untuk seluruh graph.
    """

    def __init__(
        self,
        params: GeneratorParams,
        rng: np.random.Generator,
        timeline: Timeline,
    ) -> None:
        self._params = params
        self._rng = rng
        self._timeline = timeline
        self._edges: list[EdgeRecord] = []
        self._seen: set[tuple[str, str, str]] = set()

    def add(
        self,
        src: NodeRecord,
        dst: NodeRecord,
        rel_type: str,
        rule_tag: str,
        first_seen_at: datetime | None = None,
    ) -> bool:
        """Terbitkan satu edge. Mengembalikan False bila duplikat atau self-loop.

        **Bobotnya tidak bisa ditentukan pemanggil.** Ia dihitung `weights.py`
        dari tipe relasinya. Sebelumnya tiap aturan memilih tier bobotnya
        sendiri, dan karena aturan G1-G8 hanya berlaku pada node operator
        sementara edge latar hanya pada node sah, bobot berubah menjadi salinan
        label. Menghapus parameternya membuat kebocoran itu tidak bisa kembali.

        Raises:
            ValueError: bila triple tipenya tidak sah menurut kontrak tipe
                edge. Ini bug program — aturan generatif tidak boleh
                melanggar kontrak.
        """
        if src.node_id == dst.node_id:
            return False

        if not is_legal_edge(src.node_type, rel_type, dst.node_type):
            raise ValueError(
                f"triple edge melanggar kontrak §5.2: "
                f"({src.node_type}) -{rel_type}-> ({dst.node_type}) "
                f"pada {src.node_id} -> {dst.node_id}, aturan {rule_tag}"
            )

        key = (src.node_id, dst.node_id, rel_type)
        if key in self._seen:
            return False
        self._seen.add(key)

        self._edges.append(
            EdgeRecord(
                src_id=src.node_id,
                dst_id=dst.node_id,
                rel_type=rel_type,
                weight=sample_weight(self._params, self._rng, rel_type),
                first_seen_at=first_seen_at or self._edge_time(src, dst),
                rule_tag=rule_tag,
            )
        )
        return True

    def add_transfer(
        self,
        src: NodeRecord,
        dst: NodeRecord,
        rule_tag: str,
    ) -> bool:
        """Terbitkan `transferred_to`, menolak aliran dana lintas-ekosistem.

        Penjaga catatan validitas G7: berbagi infrastruktur antar sisi judol dan
        pinjol boleh, aliran dana langsung antar keduanya tidak. Node sah tidak
        punya `side`, jadi transfer yang melibatkannya selalu lolos.
        """
        if src.side and dst.side and src.side != dst.side:
            return False
        return self.add(src, dst, "transferred_to", rule_tag)

    def _edge_time(self, src: NodeRecord, dst: NodeRecord) -> datetime:
        """Waktu edge di dalam jendela hidup bersama kedua ujungnya."""
        earliest = max(src.first_seen_at, dst.first_seen_at)
        latest = min(src.last_seen_at, dst.last_seen_at)
        if latest <= earliest:
            return earliest
        return self._timeline.sample_between(self._rng, earliest, latest)

    def edges(self) -> list[EdgeRecord]:
        return self._edges

    def tag_counts(self) -> dict[str, int]:
        """Jumlah edge per aturan, untuk diagnostik build."""
        counts: dict[str, int] = {}
        for edge in self._edges:
            counts[edge.rule_tag] = counts.get(edge.rule_tag, 0) + 1
        return dict(sorted(counts.items()))


def sow_all(
    params: GeneratorParams,
    rng: np.random.Generator,
    timeline: Timeline,
    plan: OperatorPlan,
    population: Population,
) -> list[EdgeRecord]:
    """Taburkan seluruh jejak bukti dan kembalikan daftar edge.

    Urutan pemanggilan tidak mengubah keanggotaan operator apa pun; ia hanya
    memengaruhi edge mana yang lebih dulu mengklaim pasangan (src, dst, rel)
    yang sama.
    """
    sink = EdgeSink(params, rng, timeline)

    for operator in plan.operators:
        members = _MemberIndex(population, operator)
        _sow_g6_shared_phone(params, rng, sink, operator, members)
        _sow_g1_qris_deposits(params, rng, sink, operator, members)
        _sow_g3_fictitious_merchants(params, rng, sink, operator, members)
        _sow_g2_mule_layering(params, rng, sink, operator, members)
        _sow_g4_domain_rotation(params, rng, sink, operator, members, population)
        _sow_g5_social_promotion(params, rng, sink, operator, members)
        _sow_g7_cross_ecosystem_sharing(params, rng, sink, operator, members)

    _sow_legit_background(params, rng, sink, population)
    _sow_g8_victims(params, rng, sink, plan, population)
    _sow_reports(params, rng, sink, population)

    return sink.edges()


class _MemberIndex:
    """Indeks node satu operator, dikelompokkan per tipe dan per sisi."""

    def __init__(self, population: Population, operator: OperatorSpec) -> None:
        self.operator = operator
        self.all = population.of_operator(operator.operator_id)
        self.by_type: dict[str, list[NodeRecord]] = {}
        for node in self.all:
            self.by_type.setdefault(node.node_type, []).append(node)

    def of(self, *node_types: str) -> list[NodeRecord]:
        result: list[NodeRecord] = []
        for node_type in node_types:
            result.extend(self.by_type.get(node_type, []))
        return result

    def sides(self) -> tuple[str, ...]:
        """Sisi ekosistem yang benar-benar ada pada operator ini.

        Operator satu ekosistem mengembalikan satu sisi, sehingga aturan yang
        mengulang per sisi berperilaku sama seperti sebelumnya untuknya.
        """
        found = {node.side for node in self.all if node.side}
        return tuple(sorted(found))

    def side(self, side: str, *node_types: str) -> list[NodeRecord]:
        """Node yang benar-benar milik satu sisi ekosistem.

        Node `shared_infra` ikut terbawa lewat sisinya sendiri — ia tetap punya
        satu `side` yang pasti. Tautan ke sisi seberang **hanya** diterbitkan
        `_sow_g7_cross_ecosystem_sharing`, sehingga jumlah titik sambung antar
        sisi terkendali dan bisa dihitung.

        Sebelumnya fungsi ini mengembalikan node satu sisi **ditambah seluruh**
        node `shared_infra`, dan itu sumber masalahnya: bersama G5 dan G6 yang
        juga tidak memandang sisi, kedua sisi operator `both` saling terjalin
        rapat sampai tidak ada dua operasi yang bisa dibedakan. Terukur pada
        seed 42: sisi judol dan pinjol berbagi 1 nomor kontak dan 4-7 promotor.
        """
        return [node for node in self.of(*node_types) if node.side == side]

    def accounts(self) -> list[NodeRecord]:
        return self.of("bank_account", "ewallet")

    def qris_accounts(self) -> list[NodeRecord]:
        return [node for node in self.of("ewallet") if node.feat_is_qris == 1]


# ---------------------------------------------------------------------------
# Aturan generatif G1-G8
# ---------------------------------------------------------------------------


def _sow_g1_qris_deposits(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    operator: OperatorSpec,
    members: _MemberIndex,
) -> None:
    """G1 — deposit judol mengalir lewat QRIS pada porsi yang dominan.

    Aturan generatif G1, sumber PPATK 23 Juli 2026: operator judol memakai QRIS untuk
    ~80% deposit, dengan frekuensi tinggi dan nominal kecil.

    Wujudnya pada graph: di antara edge `uses_account` milik sisi judol,
    sekitar `g1_qris_share` mengarah ke `ewallet` ber-`feat_is_qris=1`, sisanya
    ke `bank_account`. Sisi frekuensi dan nominalnya sudah tertanam di
    `feat_txn_count` / `feat_txn_amount_sum` oleh `features.py`.
    """
    if operator.ecosystem == "pinjol":
        return

    #: Hanya sisi judol yang memakai kanal QRIS menurut G1. Kolam rekeningnya
    #: juga dibatasi sisi yang sama supaya domain judol tidak berakhir memakai
    #: rekening sisi pinjol — tautan lintas sisi hanya boleh dari G7.
    qris = [node for node in members.qris_accounts() if node.side == "judol"]
    banks = members.side("judol", "bank_account")
    if not qris and not banks:
        return

    sources = [
        node
        for node in members.side("judol", "domain", "apk")
        if not node.hard_negative
    ]
    for source in sources:
        for _ in range(_draw(rng, params.legit_uses_account_per_domain)):
            use_qris = qris and rng.random() < params.g1_qris_share
            pool = qris if use_qris else (banks or qris)
            if not pool:
                continue
            sink.add(
                source,
                _pick(rng, pool),
                "uses_account",
                "G1",
            )


def _sow_g2_mule_layering(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    operator: OperatorSpec,
    members: _MemberIndex,
) -> None:
    """G2 — rekening penampung berlapis, sebagian rekening dormant yang diambil alih.

    Aturan generatif G2, sumber PPATK: rekening penampung berupa proxy account hasil
    jual-beli rekening; sebagian rekening dormant yang diambil alih.

    Wujudnya pada graph: dana dari rekening pengumpul dialirkan ke rekening
    konsolidasi lewat `transferred_to`, dan rekening dormant lebih disukai
    sebagai tujuan konsolidasi — itulah gunanya rekening dibeli. Waktu
    `first_seen_at` rekening dormant sudah diatur `population.py`.

    Seluruh aliran di sini dibatasi satu sisi ekosistem oleh
    `EdgeSink.add_transfer` (catatan validitas G7).
    """
    for side in members.sides():
        accounts = [node for node in members.accounts() if node.side == side]
        if len(accounts) < 2:
            continue

        consolidation = [node for node in accounts if node.dormant]
        if not consolidation:
            consolidation = [_pick(rng, accounts)]

        for account in accounts:
            if account in consolidation or account.hard_negative:
                continue
            for _ in range(_draw(rng, params.g2_layering_transfers)):
                sink.add_transfer(
                    account,
                    _pick(rng, consolidation + accounts),
                    "G2",
                )


def _sow_g3_fictitious_merchants(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    operator: OperatorSpec,
    members: _MemberIndex,
) -> None:
    """G3 — merchant e-wallet/QRIS fiktif atas nama UMKM.

    Aturan generatif G3, sumber PPATK 23 Juli 2026.

    Aturan ini terutama bersifat atribut node dan sudah terwujud sebagai
    `feat_is_qris` di `features.py`. Jejak strukturalnya di sini: merchant
    fiktif itu terdaftar memakai nomor kontak yang dikuasai operator, jadi
    `phone --uses_account--> ewallet`. Tidak ada nama, identitas, atau nomor
    nyata yang disimpan — hanya keterhubungannya (UU PDP 27/2022).
    """
    for side in members.sides():
        phones = members.side(side, "phone")
        merchants = [node for node in members.qris_accounts() if node.side == side]
        if not phones or not merchants:
            continue

        for merchant in merchants:
            if merchant.hard_negative:
                continue
            sink.add(
                _pick(rng, phones),
                merchant,
                "uses_account",
                "G3",
            )


def _sow_g4_domain_rotation(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    operator: OperatorSpec,
    members: _MemberIndex,
    population: Population,
) -> None:
    """G4 — domain dirotasi berkala, domain lama mengarahkan ke domain baru.

    Aturan generatif G4, sumber Komdigi/TrustPositif.

    Keanggotaan dan waktu rantai rotasinya sudah ditetapkan `population.py`;
    di sini rantai itu diterbitkan sebagai edge `redirects_to` antar anggota
    yang berurutan. Waktu edge otomatis jatuh saat domain penerus muncul,
    karena `EdgeSink` mengambil waktu di jendela hidup bersama kedua ujungnya.
    """
    chains = population.rotation_chains()
    for chain_id, chain_members in chains.items():
        if not chain_id.startswith(f"{operator.operator_id}_"):
            continue
        for older, newer in zip(chain_members, chain_members[1:]):
            sink.add(older, newer, "redirects_to", "G4")


def _sow_g5_social_promotion(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    operator: OperatorSpec,
    members: _MemberIndex,
) -> None:
    """G5 — promosi lewat banyak akun media sosial otomatis.

    Aturan generatif G5, sumber kerja sama Komdigi-Meta: promosi via ribuan akun media
    sosial otomatis.

    Wujudnya pada graph: fan-in besar `social_account --promotes--> domain/apk`.
    Akun promosi juga menautkan diri ke APK operator dan ke nomor kontaknya,
    karena itulah isi kontennya.

    Jaringan promosi dibatasi per sisi ekosistem. Sebelumnya promotor dipilih
    dari seluruh akun operator tanpa memandang sisi, sehingga satu akun promosi
    biasa bisa mempromosikan domain judol **dan** pinjol sekaligus — padahal
    berbagi jaringan promosi antar sisi seharusnya khusus milik G7 dan hanya
    untuk node yang memang ditandai dipakai bersama.
    """
    for side in members.sides():
        promoters = members.side(side, "social_account")
        targets = members.side(side, "domain", "apk")
        if not promoters or not targets:
            continue

        for target in targets:
            if target.hard_negative:
                continue
            count = min(_draw(rng, params.g5_promoters_per_target), len(promoters))
            chosen = rng.permutation(len(promoters))[:count]
            for index in chosen:
                promoter = promoters[int(index)]
                sink.add(promoter, target, "promotes", "G5")
                if (
                    target.node_type == "apk"
                    and rng.random() < params.g5_apk_link_prob
                ):
                    sink.add(
                        promoter, target, "linked_to_apk", "G5")

        phones = members.side(side, "phone")
        if not phones:
            continue
        for promoter in promoters:
            if promoter.hard_negative:
                continue
            if rng.random() < params.legit_contacts_prob_social:
                sink.add(
                    promoter, _pick(rng, phones), "contacts", "G5")


def _sow_g6_shared_phone(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    operator: OperatorSpec,
    members: _MemberIndex,
) -> None:
    """G6 — satu nomor kontak dipakai lintas beberapa domain operator yang sama.

    Aturan generatif G6, sumber PPATK.

    Inilah motif yang paling membedakan klaster operator dari klaster usaha
    sah: bukan jumlah edge-nya, melainkan berapa banyak domain yang bermuara ke
    satu nomor yang sama. Karena itu penaburannya dijalankan lebih dulu, agar
    nomor bersama sudah terbentuk sebelum aturan lain memakai node yang sama.

    Nomor kontak dibatasi per sisi ekosistem. G7 menyebut yang dibagi antar sisi
    adalah rekening mule, APK distributor, dan jaringan promosi — **bukan** nomor
    kontak. Karena itu `phone` tidak pernah ditandai `shared_infra`, dan di sini
    ia hanya melayani domain sisinya sendiri. Sebelumnya nomor dipilih lintas
    seluruh domain operator, dan itulah yang membuat kedua sisi operator `both`
    tidak bisa dibedakan satu dari yang lain.
    """
    for side in members.sides():
        phones = members.side(side, "phone")
        domains = members.side(side, "domain")
        if not phones or len(domains) < 2:
            continue

        for phone in phones:
            if phone.hard_negative:
                # Nomor cadangan yang jarang dipakai: jejaknya sengaja ditekan
                # sesuai kebijakan noise wajib, tetapi tidak sampai nol agar ia
                # tetap mungkin dipelajari.
                count = _draw(rng, params.hard_negative_kept_edges)
            else:
                count = _draw(rng, params.g6_domains_per_shared_phone)
            count = min(count, len(domains))

            chosen = rng.permutation(len(domains))[:count]
            for index in chosen:
                domain = domains[int(index)]
                if domain.hard_negative:
                    continue
                sink.add(domain, phone, "contacts", "G6")

        # Nomor kontak operator juga dipakai membuka rekening penampung.
        accounts = [node for node in members.accounts() if node.side == side]
        if not accounts:
            continue
        for phone in phones:
            if phone.hard_negative:
                continue
            for _ in range(_draw(rng, params.legit_uses_account_per_phone)):
                sink.add(
                    phone,
                    _pick(rng, accounts),
                    "uses_account",
                    "G6",
                )


def _sow_g7_cross_ecosystem_sharing(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    operator: OperatorSpec,
    members: _MemberIndex,
) -> None:
    """G7 — operator lintas-ekosistem berbagi infrastruktur, bukan aliran dana.

    Aturan generatif G7, sumber Menkominfo 13 Juni 2024, dibatasi pernyataan PPATK
    Oktober 2023: operator lintas-ekosistem berbagi rekening mule, APK
    distributor, dan jaringan promosi antara operasi judol dan pinjol ilegal,
    **tanpa** aliran dana langsung judol->pinjol.

    Inilah novelty utama SATPAM, jadi bentuknya harus tepat:

    - **Yang diterbitkan** adalah tautan infrastruktur — satu rekening yang
      sama dipakai domain kedua sisi (`uses_account`), satu APK yang sama
      ditautkan dari domain kedua sisi (`linked_to_apk`), satu akun promosi
      yang sama mempromosikan domain kedua sisi (`promotes`).
    - **Yang tidak pernah diterbitkan** adalah `transferred_to` antara node
      sisi judol dan node sisi pinjol. Fungsi ini bahkan tidak menerbitkan
      transfer sama sekali, dan `EdgeSink.add_transfer` menolaknya seandainya
      aturan lain mencoba.

    Node korban bersama pada G8 tidak melanggar batasan itu: dana bergerak
    *dari* korban ke kedua sisi, bukan antar kedua sisi.
    """
    if not operator.is_cross_ecosystem:
        return

    shared = [node for node in members.all if node.shared_infra]
    if not shared:
        return

    domains_by_side = {
        side: [node for node in members.of("domain") if node.side == side]
        for side in ("judol", "pinjol")
    }

    for node in shared:
        if node.hard_negative:
            continue
        for side, domains in domains_by_side.items():
            if not domains:
                continue
            partner = _pick(rng, domains)

            if node.node_type in ("bank_account", "ewallet"):
                sink.add(partner, node, "uses_account", "G7")
            elif node.node_type == "apk":
                sink.add(partner, node, "linked_to_apk", "G7")
            elif node.node_type == "social_account":
                sink.add(node, partner, "promotes", "G7")


def _sow_g8_victims(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    plan: OperatorPlan,
    population: Population,
) -> None:
    """G8 — sebagian korban judol menjadi korban pinjol ilegal juga.

    Aturan generatif G8, sumber PPATK (Natsir Kongah).

    Wujudnya pada graph: node `victim` menyetor ke rekening sisi judol, dan
    sebagian dari mereka (`g8_shared_victim_share`) juga menyetor ke rekening
    sisi pinjol milik operator lain atau sisi lain dari operator yang sama.

    Ini **tidak** melanggar catatan validitas G7. Korban adalah simpul bersama,
    dan dana bergerak dari korban ke masing-masing sisi — tidak ada satu pun
    edge yang mengalirkan dana dari rekening judol ke rekening pinjol.
    """
    victims = population.of_type("victim")
    if not victims:
        return

    accounts_by_side: dict[str, list[NodeRecord]] = {"judol": [], "pinjol": []}
    for operator in plan.operators:
        for node in population.of_operator(operator.operator_id):
            if node.node_type in ("bank_account", "ewallet") and node.side:
                accounts_by_side[node.side].append(node)

    legit_accounts = [
        node
        for node in population.legit()
        if node.node_type in ("bank_account", "ewallet")
    ]

    for victim in victims:
        # Sebagian korban hanya bertransaksi dengan pihak sah — mereka yang
        # menjaga agar `victim` tidak otomatis berarti terhubung ke operator.
        if not accounts_by_side["judol"] or rng.random() < 0.45:
            for _ in range(_draw(rng, params.legit_transfers_per_victim)):
                if legit_accounts:
                    sink.add_transfer(
                        victim,
                        _pick(rng, legit_accounts),
                        "background",
                    )
            continue

        for _ in range(_draw(rng, params.legit_transfers_per_victim)):
            sink.add_transfer(
                victim,
                _pick(rng, accounts_by_side["judol"]),
                "G8",
            )

        if (
            accounts_by_side["pinjol"]
            and rng.random() < params.g8_shared_victim_share
        ):
            sink.add_transfer(
                victim,
                _pick(rng, accounts_by_side["pinjol"]),
                "G8",
            )


# ---------------------------------------------------------------------------
# Wiring latar — BUKAN aturan generatif
# ---------------------------------------------------------------------------


def _sow_legit_background(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    population: Population,
) -> None:
    """Wiring klaster usaha sah. **Bukan** aturan generatif dan tanpa sitasi.

    Node sah dikelompokkan menjadi "usaha": beberapa domain, nomor kontak,
    rekening, akun promosi, kadang satu APK — lalu ditautkan di dalam
    kelompoknya. Tujuannya membuat kerapatan lokal node sah sebanding dengan
    klaster operator, sehingga `feat_degree_in/out` tidak menjadi penanda kelas.

    Bedanya dengan klaster operator ada pada motifnya, bukan jumlahnya: usaha
    sah tidak punya rantai rotasi domain (G4), tidak berbagi infrastruktur
    lintas ekosistem (G7), dan penggunaan nomor kontak bersamanya jauh lebih
    sempit daripada G6 — meski tidak nol, karena perusahaan sah dengan dua atau
    tiga situs itu hal biasa.
    """
    businesses = _partition_legit_businesses(params, rng, population)

    for domains, phones, accounts, socials, apks in businesses:
        for domain in domains:
            for phone in phones:
                if rng.random() < 0.8:
                    sink.add(domain, phone, "contacts", "background")
            for _ in range(_draw(rng, params.legit_uses_account_per_domain)):
                if accounts:
                    sink.add(
                        domain,
                        _pick(rng, accounts),
                        "uses_account",
                        "background",
                    )
            for apk in apks:
                if rng.random() < params.legit_linked_apk_prob_domain:
                    sink.add(
                        domain, apk, "linked_to_apk", "background")

        # Sasaran promosi mencakup APK, bukan hanya domain. Tanpa ini APK sah
        # nyaris tak pernah dipromosikan sementara APK operator dipromosikan
        # ramai-ramai oleh G5, dan derajat APK sendirian membelah kelas.
        promote_targets = domains + apks
        for social in socials:
            for _ in range(_draw(rng, params.legit_promotes_per_social)):
                if promote_targets:
                    target = _pick(rng, promote_targets)
                    sink.add(
                        social,
                        target,
                        "promotes",
                        "background",
                    )
            if phones and rng.random() < params.legit_contacts_prob_social:
                sink.add(
                    social, _pick(rng, phones), "contacts", "background")
            for apk in apks:
                if rng.random() < params.legit_linked_apk_prob_social:
                    sink.add(
                        social, apk, "linked_to_apk", "background")

        for phone in phones:
            for _ in range(_draw(rng, params.legit_uses_account_per_phone)):
                if accounts:
                    sink.add(
                        phone,
                        _pick(rng, accounts),
                        "uses_account",
                        "background",
                    )

        for apk in apks:
            for _ in range(_draw(rng, params.legit_contacts_per_apk)):
                if phones:
                    sink.add(
                        apk, _pick(rng, phones), "contacts", "background")
            for _ in range(_draw(rng, params.legit_uses_account_per_apk)):
                if accounts:
                    sink.add(
                        apk,
                        _pick(rng, accounts),
                        "uses_account",
                        "background",
                    )

        if len(domains) > 1 and rng.random() < params.legit_redirects_prob_domain:
            sink.add(
                domains[0], domains[1], "redirects_to", "background")

    _sow_legit_shared_services(params, rng, sink, population)
    _sow_legit_transfers(params, rng, sink, population)


def _sow_legit_shared_services(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    population: Population,
) -> None:
    """Nomor kontak layanan bersama di sisi sah. **Bukan** aturan generatif.

    Sebagian domain sah memakai nomor kontak di luar usahanya sendiri — agensi,
    penyedia hosting, layanan pelanggan pihak ketiga. Akibatnya sebagian kecil
    nomor sah menjadi hub berderajat tinggi.

    Ekor itu perlu. Tanpanya, derajat nomor kontak sah terkumpul rapat di sekitar
    nilai rendah sementara seluruh nomor operator adalah hub G6, dan derajat
    sendirian membelah kelas pada AUC 0,94 walaupun selisih rata-ratanya cuma
    1,7 kali. Yang tetap menjadi pembeda adalah motif G6-nya: berapa banyak
    domain bermuara ke satu nomor yang sama.
    """
    domains = [node for node in population.legit() if node.node_type == "domain"]
    phones = [node for node in population.legit() if node.node_type == "phone"]
    if not domains or not phones:
        return

    for domain in domains:
        if rng.random() >= params.legit_shared_phone_share:
            continue
        sink.add(
            domain, _pick(rng, phones), "contacts", "background")


def _partition_legit_businesses(
    params: GeneratorParams,
    rng: np.random.Generator,
    population: Population,
) -> list[tuple[list[NodeRecord], ...]]:
    """Bagi seluruh node sah menjadi klaster usaha secara berimbang.

    Pembagian berbasis "ambil sekian dari kolam sampai habis" sempat membuat
    usaha yang dibentuk lebih awal kebagian banyak dan yang belakangan tidak
    kebagian apa pun — bias sistematis yang menciptakan dua populasi node sah
    dengan kerapatan sangat berbeda. Karena itu jumlah usaha ditetapkan lebih
    dulu dari kolam domain, lalu setiap kolam lain dibagi rata ke seluruh usaha
    dengan sedikit variasi. Semua node terpakai dan kerapatannya seragam.
    """
    pools = {
        node_type: _shuffled(
            rng, [node for node in population.legit() if node.node_type == node_type]
        )
        for node_type in (
            "domain",
            "phone",
            "bank_account",
            "ewallet",
            "apk",
            "social_account",
        )
    }

    domain_groups: list[list[NodeRecord]] = []
    cursor = 0
    domains = pools["domain"]
    while cursor < len(domains):
        size = _draw(rng, params.legit_domains_per_business)
        domain_groups.append(domains[cursor : cursor + size])
        cursor += size
    if not domain_groups:
        return []

    shares = {
        node_type: _spread(rng, len(pool), len(domain_groups))
        for node_type, pool in pools.items()
        if node_type != "domain"
    }

    businesses: list[tuple[list[NodeRecord], ...]] = []
    cursors = {node_type: 0 for node_type in shares}
    for index, group in enumerate(domain_groups):

        def slice_of(node_type: str) -> list[NodeRecord]:
            start = cursors[node_type]
            count = shares[node_type][index]
            cursors[node_type] = start + count
            return pools[node_type][start : start + count]

        businesses.append(
            (
                group,
                slice_of("phone"),
                slice_of("bank_account") + slice_of("ewallet"),
                slice_of("social_account"),
                slice_of("apk"),
            )
        )
    return businesses


def _spread(rng: np.random.Generator, total: int, buckets: int) -> list[int]:
    """Sebar `total` node ke `buckets` usaha: rata, plus sisa dibagi acak."""
    if buckets <= 0:
        return []
    base = total // buckets
    counts = [base] * buckets
    for index in rng.permutation(buckets)[: total - base * buckets]:
        counts[int(index)] += 1
    return counts


def _sow_legit_transfers(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    population: Population,
) -> None:
    """Aliran dana antar rekening sah. **Bukan** aturan generatif."""
    accounts = [
        node
        for node in population.legit()
        if node.node_type in ("bank_account", "ewallet")
    ]
    if len(accounts) < 2:
        return
    for account in accounts:
        for _ in range(_draw(rng, params.legit_transfers_per_account)):
            sink.add_transfer(
                account, _pick(rng, accounts), "background")


def _sow_reports(
    params: GeneratorParams,
    rng: np.random.Generator,
    sink: EdgeSink,
    population: Population,
) -> None:
    """Laporan masuk dan sasaran yang disebutnya. **Bukan** aturan generatif.

    Node `report` menyebut node lain lewat `mentions`, dan node `victim`
    mengajukan laporan lewat `reported`. Bobot pemilihan sasaran itulah yang
    membuat `feat_report_count` bermakna:

    - node operator lebih sering dilaporkan,
    - node hard negative hampir tidak pernah — itu memang arti "nyaris tanpa
      jejak" pada kebijakan noise wajib,
    - node hard positive ikut terkena laporan keliru, yang merupakan satu-satunya
      jalan kebijakan noise wajib membuat node sah bertipe `phone` tampak
      mencurigakan, sebab nomor telepon tidak punya teks untuk dicocokkan
      kata kunci.
    """
    reports = population.of_type("report")
    victims = population.of_type("victim")
    if not reports:
        return

    targets = [
        node
        for node in population.nodes
        if node.node_type not in ("report", "victim")
    ]
    if not targets:
        return

    weights = np.array(
        [_mention_weight(params, node) for node in targets], dtype=float
    )
    weights /= weights.sum()

    for report in reports:
        count = min(_draw(rng, params.mentions_per_report), len(targets))
        chosen = rng.choice(len(targets), size=count, replace=False, p=weights)
        for index in chosen:
            sink.add(
                report,
                targets[int(index)],
                "mentions",
                "background",
            )

    if victims:
        for victim in victims:
            count = min(_draw(rng, params.reports_per_victim), len(reports))
            chosen = rng.permutation(len(reports))[:count]
            for index in chosen:
                sink.add(
                    victim,
                    reports[int(index)],
                    "reported",
                    "background",
                )


def _mention_weight(params: GeneratorParams, node: NodeRecord) -> float:
    """Bobot peluang sebuah node disebut laporan."""
    if node.hard_negative:
        return params.mention_weight_hard_negative
    if node.hard_positive:
        return params.mention_weight_hard_positive
    if node.is_illicit:
        return params.mention_weight_illicit
    return params.mention_weight_legit


# ---------------------------------------------------------------------------
# Bantuan kecil
# ---------------------------------------------------------------------------


def _draw(rng: np.random.Generator, bounds: IntRange) -> int:
    """Bilangan bulat acak di rentang inklusif."""
    low, high = bounds
    return int(rng.integers(low, high + 1))




def _pick(rng: np.random.Generator, pool: list[NodeRecord]) -> NodeRecord:
    """Satu node acak dari kolam."""
    return pool[int(rng.integers(0, len(pool)))]


def _shuffled(rng: np.random.Generator, nodes: list[NodeRecord]) -> list[NodeRecord]:
    """Salinan teracak, agar pembagian klaster tidak mengikuti urutan node_id."""
    return [nodes[int(i)] for i in rng.permutation(len(nodes))]
