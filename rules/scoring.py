"""Rule engine SATPAM — baseline B1 dan penghasil `weak_labels.csv`.

Diadaptasi dari `scoring.py` sistem v1.0
(`src-old/backend/app/services/ai_engine/scoring.py`). Yang diwarisi apa adanya:

- skor aditif dengan cap 100 (`SCORE_CAP`)
- batas level `critical>=80 / high>=60 / medium>=35 / low`
- bobot per aturan (15/20/25 sesuai tier semantik sistem lama)
- ambang bilangan bulat 2/3/4 sebagai **batas bawah**
- evaluasi atas konteks tetangga `max_depth=2` dengan batas 250 node

Semuanya ditetapkan sebelum generator ada, jadi tidak mungkin tersetel ke data
yang dihasilkannya. Itulah nilai utama mengadaptasi kode lama alih-alih menulis
baru: independensinya bisa ditunjukkan, bukan cuma dijanjikan.

**Tiap aturan tier `srs_6_3` berpadanan satu-satu dengan satu aturan generatif
(G1-G8).** Tidak ada aturan yang dikarang. Dua aturan tier `legacy` tidak
berpadanan dengan aturan generatif mana pun dan provenance-nya dicantumkan
terpisah; keduanya bisa dimatikan lewat parameter `tiers` untuk ablasi.

**Kalibrasi ambang.** Ambang bilangan bulat sistem lama ditulis untuk graph
dummy berisi 10–80 entitas per tipe. Pada graph 5.000 node, ambang `>=2` menyala
untuk hampir semua node dan aturannya berhenti membedakan apa pun. Karena itu
ambang hitungan dinaikkan ke persentil sebaran teramati, dengan ambang lama
sebagai batas bawah. Kalibrasi ini **tidak menyentuh label**: ia hanya memakai
sebaran kolom yang memang dilihat rule engine, sama seperti analis yang berkata
"rekening di kuartil teratas frekuensi transaksi". Ambang hasil hitungannya
ikut dilaporkan agar bisa diaudit.

Modul ini tidak mengimpor apa pun dari `generator/` dan tidak pernah membaca
kolom jawaban.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from rules.graph import RuleGraph
from rules.loader import ACCOUNT_TYPES, RuleNode

#: Batas atas skor, diwarisi dari sistem v1.0.
SCORE_CAP = 100

#: Batas level, diwarisi dari sistem v1.0 (`risk_level`).
LEVEL_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (80, "critical"),
    (60, "high"),
    (35, "medium"),
)

#: Kedalaman konteks yang dipakai. Sistem v1.0 memakai 2; di sini 1.
#:
#: Ini satu-satunya angka warisan yang saya ubah, dan alasannya skala. Graph
#: dummy v1.0 berisi 10–80 entitas per tipe; graph ini 5.000 node dengan derajat
#: rata-rata 7, sehingga konteks 2-hop menjangkau sekitar 50 node dan hampir
#: selalu memuat beberapa pola aturan sekaligus. Sebaran level terukur:
#:
#:     depth 0 -> low 93,6%  medium  5,8%  high  0,4%  critical  0,2%
#:     depth 1 -> low 27,4%  medium 25,1%  high 18,8%  critical 28,7%
#:     depth 2 -> low  2,0%  medium  3,1%  high  5,3%  critical 89,6%
#:
#: Depth 0 dan 2 sama-sama degenerate: yang pertama membuat aturan hampir tak
#: pernah menyala, yang kedua menyebut hampir semua node kritis. Keduanya tidak
#: membedakan apa pun.
#:
#: Pemilihannya memakai kriteria **bebas ground truth** — sebaran level tidak
#: menumpuk di satu kelas — bukan dengan memaksimalkan kecocokan terhadap
#: jawaban. Kalau kedalamannya disetel ke ground truth, pengukuran "seberapa
#: lemah label ini" jadi tidak bermakna.
DEFAULT_MAX_DEPTH = 1

#: Batas jumlah node dalam konteks, diwarisi dari sistem v1.0 (`_context_keys`).
DEFAULT_CONTEXT_LIMIT = 250

#: Kedalaman konteks sistem v1.0, dicatat untuk pelaporan.
LEGACY_MAX_DEPTH = 2

#: Persentil untuk mengkalibrasi ambang hitungan ke skala graph sebenarnya.
COUNT_PERCENTILE = 90.0
VALUE_PERCENTILE = 75.0


@dataclass(frozen=True)
class RuleDefinition:
    """Satu aturan skoring beserta asal-usulnya.

    Attributes:
        srs_rule: Kode aturan generatif (G1-G8) yang menjadi dasarnya, kosong
            untuk tier `legacy`.
        citation: Sumber yang dikutip aturan generatif tersebut, atau
            provenance lain untuk tier `legacy`.
        legacy_rule: Aturan padanan di sistem v1.0 yang bobotnya diwarisi.
        tier: `srs_6_3` atau `legacy`. Dipakai untuk ablasi.
    """

    rule_id: str
    title: str
    weight: int
    srs_rule: str
    citation: str
    legacy_rule: str
    tier: str


RULES: dict[str, RuleDefinition] = {
    "R-G1": RuleDefinition(
        rule_id="R-G1",
        title="Kanal QRIS dengan frekuensi tinggi dan nominal kecil",
        weight=25,
        srs_rule="G1",
        citation="PPATK, 23 Juli 2026",
        legacy_rule="R-013",
        tier="srs_6_3",
    ),
    "R-G2": RuleDefinition(
        rule_id="R-G2",
        title="Rekening penampung: jurang dormant atau pola berlapis",
        weight=20,
        srs_rule="G2",
        citation="PPATK",
        legacy_rule="R-008",
        tier="srs_6_3",
    ),
    "R-G3": RuleDefinition(
        rule_id="R-G3",
        title="Merchant QRIS dipakai beberapa pihak berbeda",
        weight=20,
        srs_rule="G3",
        citation="PPATK, 23 Juli 2026",
        legacy_rule="R-004",
        tier="srs_6_3",
    ),
    "R-G4": RuleDefinition(
        rule_id="R-G4",
        title="Domain berada dalam rantai pengalihan",
        weight=15,
        srs_rule="G4",
        citation="Komdigi/TrustPositif",
        legacy_rule="R-012",
        tier="srs_6_3",
    ),
    "R-G5": RuleDefinition(
        rule_id="R-G5",
        title="Promosi terpusat oleh banyak akun media sosial",
        weight=20,
        srs_rule="G5",
        citation="Komdigi-Meta",
        legacy_rule="R-009",
        tier="srs_6_3",
    ),
    "R-G6": RuleDefinition(
        rule_id="R-G6",
        title="Satu nomor kontak dipakai lintas beberapa domain",
        weight=25,
        srs_rule="G6",
        citation="PPATK",
        legacy_rule="R-003",
        tier="srs_6_3",
    ),
    "R-G7": RuleDefinition(
        rule_id="R-G7",
        title="Infrastruktur menjembatani dua gugus domain terpisah",
        weight=20,
        srs_rule="G7",
        citation="Menkominfo 13 Juni 2024, dibatasi PPATK Oktober 2023",
        legacy_rule="R-010",
        tier="srs_6_3",
    ),
    "R-G8": RuleDefinition(
        rule_id="R-G8",
        title="Rekening menerima setoran dari beberapa korban berbeda",
        weight=25,
        srs_rule="G8",
        citation="PPATK (Natsir Kongah)",
        legacy_rule="R-004",
        tier="srs_6_3",
    ),
    "R-X1": RuleDefinition(
        rule_id="R-X1",
        title="Entitas banyak disebut laporan masuk",
        weight=25,
        srs_rule="",
        citation=(
            "TIDAK ada baris di SRS §6.3. Provenance: kolom feat_report_count "
            "(SRS §5.3) dan praktik penanganan laporan IASC/Satgas PASTI yang "
            "dikutip SRS §3.1; aturan padanan R-003 sistem v1.0"
        ),
        legacy_rule="R-003",
        tier="legacy",
    ),
    "R-X2": RuleDefinition(
        rule_id="R-X2",
        title="Node sangat sentral pada graph",
        weight=10,
        srs_rule="",
        citation=(
            "TIDAK ada baris di SRS §6.3. Provenance: aturan R-015 sistem v1.0 "
            "dan kolom feat_degree_in/out (SRS §5.3)"
        ),
        legacy_rule="R-015",
        tier="legacy",
    ),
}

#: Tier yang aktif secara bawaan.
ALL_TIERS: tuple[str, ...] = ("srs_6_3", "legacy")

#: Hanya aturan yang berpadanan aturan generatif G1-G8 — dipakai untuk ablasi.
SRS_TIER_ONLY: tuple[str, ...] = ("srs_6_3",)


@dataclass(frozen=True)
class RuleHit:
    """Satu aturan yang menyala pada sebuah node."""

    rule_id: str
    weight: int
    evidence: str


@dataclass(frozen=True)
class RuleAssessment:
    """Hasil skoring satu node."""

    node_id: str
    score: int
    level: str
    hits: tuple[RuleHit, ...]

    @property
    def triggered_rules(self) -> str:
        """Nilai kolom `triggered_rules`, dipisah titik koma."""
        return ";".join(hit.rule_id for hit in self.hits)


@dataclass
class Calibration:
    """Ambang hasil kalibrasi terhadap sebaran teramati.

    Seluruh isinya dihitung dari kolom yang memang dilihat rule engine. Tidak
    ada label yang disentuh, jadi kalibrasi ini tidak mengintip jawaban.
    """

    thresholds: dict[str, float] = field(default_factory=dict)

    def get(self, name: str) -> float:
        return self.thresholds[name]

    def as_dict(self) -> dict[str, float]:
        return dict(sorted(self.thresholds.items()))


def _percentile(values: list[float], percentile: float) -> float:
    """Persentil sederhana dengan interpolasi linear, tanpa dependensi luar."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (percentile / 100.0) * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def calibrate(graph: RuleGraph) -> Calibration:
    """Hitung ambang tiap aturan dari sebaran teramati.

    Ambang bilangan bulat sistem v1.0 dipakai sebagai batas bawah, supaya
    kalibrasi tidak pernah membuat aturan lebih longgar daripada aslinya.
    """
    accounts = [
        node for node in graph.nodes.values() if node.node_type in ACCOUNT_TYPES
    ]
    active_accounts = [node for node in accounts if node.feat_txn_count > 0]

    # R-G1 — "frekuensi tinggi nominal kecil" relatif populasi teramati.
    txn_high = _percentile([node.feat_txn_count for node in active_accounts], VALUE_PERCENTILE)
    ticket_low = _percentile([node.mean_ticket for node in active_accounts], 100.0 - VALUE_PERCENTILE)

    # R-G2 — jurang antara pembukaan rekening dan jejak pertamanya.
    gaps = [_dormant_gap_days(graph, node) for node in graph.nodes_of_type("bank_account")]
    dormant_gap = _percentile([gap for gap in gaps if gap > 0], COUNT_PERCENTILE)

    # Ambang hitungan; batas bawah diwarisi dari R-009 (2), R-003 (3), R-015 (4).
    merchant_users = [
        float(len(graph.sources(node.node_id, "uses_account")))
        for node in graph.nodes.values()
        if node.node_type == "ewallet"
    ]
    promoters = [
        float(len(graph.sources(node.node_id, "promotes")))
        for node in graph.nodes.values()
        if node.node_type in ("domain", "apk")
    ]
    promoted = [
        float(len(graph.targets(node.node_id, "promotes")))
        for node in graph.nodes_of_type("social_account")
    ]
    phone_domains = [
        float(len(graph.sources(node.node_id, "contacts", node_type="domain")))
        for node in graph.nodes_of_type("phone")
    ]
    victim_payers = [
        float(len(graph.sources(node.node_id, "transferred_to", node_type="victim")))
        for node in accounts
    ]
    # Sumber transfer masuk per rekening, untuk mengkalibrasi cabang layering
    # R-G2. Ambang mutlak 2 warisan R-004 menyala untuk 429 dari 450 rekening
    # pada graph ini — rekening sah pun bertransaksi 4-8 kali — sehingga
    # aturannya berhenti membedakan apa pun dan presisinya jatuh ke laju dasar.
    inflow_sources = [
        float(len(graph.sources(node.node_id, "transferred_to"))) for node in accounts
    ]
    report_counts = [node.feat_report_count for node in graph.nodes.values()]
    degrees = [node.degree_total for node in graph.nodes.values()]

    thresholds = {
        "g1_txn_count": txn_high,
        "g1_mean_ticket": ticket_low,
        "g2_dormant_gap_days": max(dormant_gap, 30.0),
        "g2_layering_sources": max(2.0, _percentile(inflow_sources, COUNT_PERCENTILE)),
        "g3_merchant_users": max(2.0, _percentile(merchant_users, COUNT_PERCENTILE)),
        "g5_promoters": max(2.0, _percentile(promoters, COUNT_PERCENTILE)),
        "g5_promoted": max(2.0, _percentile(promoted, COUNT_PERCENTILE)),
        "g6_phone_domains": max(3.0, _percentile(phone_domains, COUNT_PERCENTILE)),
        "g7_bridged_groups": 2.0,
        "g8_victim_payers": max(2.0, _percentile(victim_payers, COUNT_PERCENTILE)),
        "x1_report_count": max(3.0, _percentile(report_counts, COUNT_PERCENTILE)),
        "x2_degree": max(4.0, _percentile(degrees, COUNT_PERCENTILE)),
    }
    return Calibration(thresholds=thresholds)


def _dormant_gap_days(graph: RuleGraph, node: RuleNode) -> float:
    """Selisih hari antara pembukaan rekening dan edge paling awal yang menyentuhnya.

    Rekening yang dibeli lalu diambil alih tampak sebagai rekening lama yang
    jejaknya baru muncul belakangan (aturan generatif G2).
    """
    timestamps = [edge.first_seen_at for edge in graph.out_edges(node.node_id)]
    timestamps += [edge.first_seen_at for edge in graph.in_edges(node.node_id)]
    if not timestamps:
        return 0.0
    gap = (min(timestamps) - node.first_seen_at).total_seconds() / 86_400.0
    return max(gap, 0.0)


# ---------------------------------------------------------------------------
# Penanda per node: apakah node INI cocok dengan pola sebuah aturan
# ---------------------------------------------------------------------------


def _match_g1(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """G1 — kanal QRIS berfrekuensi tinggi bernominal kecil (PPATK 23 Jul 2026)."""
    if node.node_type not in ACCOUNT_TYPES or node.feat_is_qris != 1:
        return None
    if node.feat_txn_count < cal.get("g1_txn_count"):
        return None
    if node.mean_ticket > cal.get("g1_mean_ticket"):
        return None
    return (
        f"{node.node_id} kanal QRIS dengan {node.feat_txn_count:.0f} transaksi "
        f"dan nominal rata-rata {node.mean_ticket:,.0f}"
    )


def _match_g2(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """G2 — rekening penampung hasil jual-beli, sebagian dormant diambil alih (PPATK)."""
    if node.node_type != "bank_account":
        return None

    gap = _dormant_gap_days(graph, node)
    if gap >= cal.get("g2_dormant_gap_days"):
        return (
            f"{node.node_id} dibuka {gap:.0f} hari sebelum jejak pertamanya, "
            f"pola rekening lama yang baru dipakai"
        )

    inflow = graph.sources(node.node_id, "transferred_to")
    outflow = graph.targets(node.node_id, "transferred_to")
    if len(inflow) >= cal.get("g2_layering_sources") and outflow:
        return (
            f"{node.node_id} menerima dari {len(inflow)} sumber lalu meneruskan "
            f"ke {len(outflow)} tujuan, pola berlapis"
        )
    return None


def _match_g3(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """G3 — merchant e-wallet/QRIS fiktif atas nama UMKM (PPATK 23 Jul 2026)."""
    if node.node_type != "ewallet" or node.feat_is_qris != 1:
        return None
    users = graph.sources(node.node_id, "uses_account")
    if len(users) < cal.get("g3_merchant_users"):
        return None
    return f"merchant QRIS {node.node_id} dipakai {len(users)} pihak berbeda"


def _match_g4(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """G4 — domain dirotasi berkala, yang lama mengarahkan ke yang baru (Komdigi)."""
    if node.node_type != "domain":
        return None
    outgoing = graph.targets(node.node_id, "redirects_to")
    incoming = graph.sources(node.node_id, "redirects_to")
    if not outgoing and not incoming:
        return None
    return (
        f"{node.node_id} berada dalam rantai pengalihan "
        f"({len(incoming)} masuk, {len(outgoing)} keluar)"
    )


def _match_g5(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """G5 — promosi via ribuan akun media sosial otomatis (Komdigi-Meta)."""
    if node.node_type in ("domain", "apk"):
        promoters = graph.sources(node.node_id, "promotes")
        if len(promoters) >= cal.get("g5_promoters"):
            return f"{node.node_id} dipromosikan {len(promoters)} akun berbeda"
    if node.node_type == "social_account":
        promoted = graph.targets(node.node_id, "promotes")
        if len(promoted) >= cal.get("g5_promoted"):
            return f"{node.node_id} mempromosikan {len(promoted)} sasaran berbeda"
    return None


def _match_g6(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """G6 — satu nomor kontak dipakai lintas beberapa domain (PPATK)."""
    if node.node_type != "phone":
        return None
    domains = graph.sources(node.node_id, "contacts", node_type="domain")
    if len(domains) < cal.get("g6_phone_domains"):
        return None
    return f"{node.node_id} menjadi kontak {len(domains)} domain berbeda"


def _match_g7(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """G7 — infrastruktur dipakai bersama dua operasi (Menkominfo 13 Jun 2024).

    Operasionalisasinya memakai motif G6 sebagai kunci: satu operasi berbagi
    nomor kontak antar domain-domainnya. Jadi domain-domain yang terkait ke node
    ini dikelompokkan lewat nomor kontak bersama, lalu node dinyatakan
    infrastruktur bersama bila kelompoknya lebih dari satu — ia dipakai oleh
    dua himpunan domain yang tidak saling berbagi kontak.

    Percobaan pertama memakai uji "satu-satunya penghubung antara dua domain",
    dan itu salah arah: domain milik satu operator justru **selalu** berbagi
    nomor kontak karena G6, sehingga uji itu gagal tepat ketika klasternya padat
    dan hanya menyala pada node sah yang tetangganya kebetulan renggang.
    Presisinya 0,044 pada laju dasar 0,055 — di bawah acak.

    Catatan penting: aturan ini mendeteksi **infrastruktur** bersama, bukan
    aliran dana lintas ekosistem. Batas itu berasal dari catatan validitas
    yang merujuk pernyataan PPATK Oktober 2023.
    """
    if node.node_type not in ("bank_account", "ewallet", "apk", "social_account"):
        return None

    related = graph.sources(node.node_id, "uses_account", node_type="domain")
    related |= graph.sources(node.node_id, "linked_to_apk", node_type="domain")
    related |= graph.targets(node.node_id, "promotes", node_type="domain")
    if len(related) < 2:
        return None

    groups = _group_domains_by_contact(graph, related)
    if len(groups) < cal.get("g7_bridged_groups"):
        return None
    sizes = ", ".join(str(len(group)) for group in groups)
    return (
        f"{node.node_id} dipakai {len(groups)} kelompok domain yang tidak "
        f"berbagi nomor kontak (ukuran {sizes})"
    )


def _group_domains_by_contact(
    graph: RuleGraph, domain_ids: set[str]
) -> list[set[str]]:
    """Kelompokkan domain: dua domain sekelompok bila berbagi nomor kontak.

    Domain tanpa nomor kontak sama sekali diabaikan — tanpa kontak tidak ada
    dasar menyatakan ia bagian operasi yang mana, dan menghitungnya sebagai
    kelompok sendiri akan membuat aturan menyala karena ketiadaan data.
    """
    phones_of: dict[str, set[str]] = {}
    for domain_id in domain_ids:
        phones = graph.targets(domain_id, "contacts", node_type="phone")
        if phones:
            phones_of[domain_id] = phones

    groups: list[set[str]] = []
    group_phones: list[set[str]] = []
    for domain_id in sorted(phones_of):
        phones = phones_of[domain_id]
        merged = [
            index
            for index, existing in enumerate(group_phones)
            if existing & phones
        ]
        if not merged:
            groups.append({domain_id})
            group_phones.append(set(phones))
            continue
        target = merged[0]
        groups[target].add(domain_id)
        group_phones[target] |= phones
        for index in reversed(merged[1:]):
            groups[target] |= groups.pop(index)
            group_phones[target] |= group_phones.pop(index)
    return groups


def _match_g8(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """G8 — korban judol sebagian menjadi korban pinjol ilegal (PPATK)."""
    if node.node_type not in ACCOUNT_TYPES:
        return None
    victims = graph.sources(node.node_id, "transferred_to", node_type="victim")
    if len(victims) < cal.get("g8_victim_payers"):
        return None
    return f"{node.node_id} menerima setoran dari {len(victims)} korban berbeda"


def _match_x1(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """Tier legacy — banyak disebut laporan masuk. Bukan bagian aturan
    generatif G1-G8."""
    if node.feat_report_count < cal.get("x1_report_count"):
        return None
    return f"{node.node_id} disebut {node.feat_report_count:.0f} laporan"


def _match_x2(graph: RuleGraph, node: RuleNode, cal: Calibration) -> str | None:
    """Tier legacy — node sangat sentral. Bukan bagian aturan generatif
    G1-G8."""
    if node.degree_total < cal.get("x2_degree"):
        return None
    return f"{node.node_id} punya derajat {node.degree_total:.0f}"


#: Pemeta aturan ke fungsi pencocoknya.
MATCHERS: dict[str, Callable[[RuleGraph, RuleNode, Calibration], str | None]] = {
    "R-G1": _match_g1,
    "R-G2": _match_g2,
    "R-G3": _match_g3,
    "R-G4": _match_g4,
    "R-G5": _match_g5,
    "R-G6": _match_g6,
    "R-G7": _match_g7,
    "R-G8": _match_g8,
    "R-X1": _match_x1,
    "R-X2": _match_x2,
}


# ---------------------------------------------------------------------------
# Skoring
# ---------------------------------------------------------------------------


def risk_level(score: int) -> str:
    """Level risiko dari skor. Batasnya diwarisi dari sistem v1.0."""
    for threshold, level in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return "low"


def find_matches(
    graph: RuleGraph,
    calibration: Calibration,
    tiers: tuple[str, ...] = ALL_TIERS,
) -> dict[str, dict[str, str]]:
    """Cari, untuk tiap aturan, node mana yang cocok dengan polanya.

    Dihitung sekali lalu dipakai ulang saat menyusun konteks tiap node, sehingga
    penilaian 5.000 node tidak berarti mengulang pencocokan 5.000 kali.

    Returns:
        Pemeta `rule_id` -> (`node_id` -> keterangan bukti).
    """
    matches: dict[str, dict[str, str]] = {}
    for rule_id, rule in RULES.items():
        if rule.tier not in tiers:
            continue
        matcher = MATCHERS[rule_id]
        found: dict[str, str] = {}
        for node in graph.nodes.values():
            evidence = matcher(graph, node, calibration)
            if evidence is not None:
                found[node.node_id] = evidence
        matches[rule_id] = found
    return matches


def score_node(
    graph: RuleGraph,
    node_id: str,
    matches: dict[str, dict[str, str]],
    max_depth: int = DEFAULT_MAX_DEPTH,
    context_limit: int = DEFAULT_CONTEXT_LIMIT,
) -> RuleAssessment:
    """Skor satu node dari pola yang muncul di dalam konteks tetangganya.

    Mekanisme konteks ini diwarisi dari sistem v1.0: sebuah entitas ikut
    tertandai bila pola risiko muncul di sekitarnya, bukan hanya pada dirinya
    sendiri. Itu memang cara rule engine bekerja, dan itu juga sumber false
    positive-nya — yang justru diperlukan agar label ini tetap *lemah*.
    """
    context = graph.neighborhood(node_id, max_depth=max_depth, limit=context_limit)

    hits: list[RuleHit] = []
    for rule_id, found in matches.items():
        if not found:
            continue
        if node_id in found:
            hits.append(RuleHit(rule_id, RULES[rule_id].weight, found[node_id]))
            continue
        hit_elsewhere = next((key for key in context if key in found), None)
        if hit_elsewhere is not None:
            hits.append(
                RuleHit(
                    rule_id,
                    RULES[rule_id].weight,
                    f"dalam konteks: {found[hit_elsewhere]}",
                )
            )

    hits.sort(key=lambda hit: hit.rule_id)
    score = min(SCORE_CAP, sum(hit.weight for hit in hits))
    return RuleAssessment(
        node_id=node_id,
        score=score,
        level=risk_level(score),
        hits=tuple(hits),
    )


def score_graph(
    graph: RuleGraph,
    tiers: tuple[str, ...] = ALL_TIERS,
    max_depth: int = DEFAULT_MAX_DEPTH,
    context_limit: int = DEFAULT_CONTEXT_LIMIT,
) -> tuple[list[RuleAssessment], Calibration, dict[str, dict[str, str]]]:
    """Skor seluruh node graph.

    Returns:
        Daftar penilaian, kalibrasi ambang yang dipakai, dan pola per aturan —
        ketiganya dikembalikan agar bisa dilaporkan dan diaudit.
    """
    calibration = calibrate(graph)
    matches = find_matches(graph, calibration, tiers=tiers)
    assessments = [
        score_node(
            graph,
            node_id,
            matches,
            max_depth=max_depth,
            context_limit=context_limit,
        )
        for node_id in sorted(graph.nodes)
    ]
    return assessments, calibration, matches
