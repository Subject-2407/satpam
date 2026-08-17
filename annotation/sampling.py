"""Pengambilan sampel node untuk anotasi manual — enam strata, non-overlap.

Sampel **tidak** acak murni. Empat dari enam strata sengaja membidik kasus sulit,
karena di situlah penilaian manusia paling bernilai di atas rule engine.

| Strata | Definisi | Maksud |
|---|---|---|
| S1 | `critical` dan >=2 aturan menyala pada node itu sendiri | kalibrasi saat rule paling yakin |
| S2 | `low`, 0 aturan pada dirinya, tidak ada tetangga `critical` | sisi lain kalibrasi |
| S3 | skor dalam +-5 dari ambang level 35/60/80 | di ambang, penilaian manusia menentukan |
| S4 | jejak sendiri tipis (<=1 aturan), derajat rendah, tapi ada tetangga bermasalah | wilayah hard negative |
| S5 | jejak sendiri kuat (>=2 aturan) tapi lingkungannya renggang | rule mungkin salah arah |
| S6 | sisanya, acak berstrata per tipe node | jangkar agar set tidak seluruhnya adversarial |

**Batas kejujuran soal S4 dan S5.** Hard negative dan hard positive tidak
mungkin diidentifikasi tanpa kolom jawaban — sifat ilegalnya hanya ada di kolom
yang modul ini tidak boleh baca. Yang bisa dilakukan adalah membidik wilayahnya.
Hasil pengukuran di seed 42 menentukan bentuk kedua definisi:

- **Hard negative punya satu tanda teramati: derajat rendah.** Median derajatnya
  4 berbanding 9 untuk node ilegal biasa, karena definisi hard negative dalam
  data sintetis memang menekan jejaknya. Seluruh 49 di antaranya punya
  sedikitnya satu tetangga bermasalah. Definisi awal yang mensyaratkan **>=2**
  tetangga bermasalah justru menyingkirkan mereka dan hanya menjaring 9 dari
  49; definisi sekarang menjaring 14 dari 49.
- **Hard positive tidak punya proksi teramati sama sekali.** Terukur derajat
  median 8 berbanding 7 untuk node sah biasa, aturan-sendiri 0 berbanding 0,
  tetangga bermasalah 3 berbanding 3. Praktis tak terbedakan — dan memang
  begitu hard positive dirancang. Karena itu S5 **tidak** diklaim sebagai
  proksi hard positive; namanya menyebut apa yang benar-benar dideteksinya.
  Hard positive akan masuk set anotasi lewat jangkar acak S6 pada laju
  populasinya, bukan dibidik.

Definisi S4 dan S5 diperiksa terhadap kolom jawaban **saat perancangan** untuk
memastikan proksinya benar-benar mengumpulkan kasus sulit. Yang dijalankan tetap
hanya sinyal teramati, sehingga pemilih yang sama bisa dipakai pada data tanpa
label. Konsekuensinya sampel ini terarah, bukan acak, dan kurva A5 menunjukkan
nilai per anotasi *yang dipilih dengan baik* — bukan per anotasi acak. Itu perlu
dinyatakan sebagai batasan bila hasilnya dipakai untuk pelaporan.

Dua batasan lain:

- **Hanya enam tipe infrastruktur.** `report` dan `victim` bukan calon anggota
  jaringan pelaku menurut definisi peran mereka, jadi menanyakannya membuang
  tenaga.
- **Node harus punya tetangga.** Propagasi feedback menyebar lewat edge;
  anotasi pada node terisolasi tidak menyebar ke mana pun.

Modul ini tidak mengimpor apa pun dari `generator/` dan tidak membaca kolom
jawaban.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from rules.graph import RuleGraph
from rules.scoring import calibrate, find_matches

#: Tipe node yang dianotasi. `report` dan `victim` dikecualikan — lihat docstring.
ANNOTATABLE_NODE_TYPES: tuple[str, ...] = (
    "domain",
    "phone",
    "bank_account",
    "ewallet",
    "apk",
    "social_account",
)

#: Ambang level rule engine, dipakai strata S3 untuk mencari kasus di batas.
LEVEL_BOUNDARIES: tuple[int, ...] = (35, 60, 80)

#: Lebar jendela "di ambang" untuk S3.
BOUNDARY_WINDOW: int = 5

#: Urutan pelaporan strata.
STRATA_ORDER: tuple[str, ...] = ("S1", "S2", "S3", "S4", "S5", "S6")

#: Urutan **klaim** strata: node diklaim strata pertama yang cocok, sehingga tidak
#: ada node masuk dua strata sekaligus.
#:
#: Berbeda dari urutan pelaporan, dan itu disengaja. S3 sangat melimpah (1.270
#: kandidat) sementara S5 sangat langka (68). Kalau S3 mengklaim lebih dulu, ia
#: menyerap habis kandidat S5 dan strata yang paling sengaja dibidik justru
#: kelaparan. Strata langka mengklaim lebih dulu.
CLAIM_ORDER: tuple[str, ...] = ("S1", "S5", "S4", "S2", "S3", "S6")

#: Keterangan strata — hanya untuk manifest koordinator, **bukan** lembar kerja.
STRATA_LABELS: dict[str, str] = {
    "S1": "rule yakin positif (critical, >=2 aturan pada node sendiri)",
    "S2": "rule yakin negatif (low, tanpa aturan sendiri, tanpa tetangga critical)",
    "S3": "di ambang batas level (skor +-5 dari 35/60/80)",
    "S4": "jejak sendiri tipis, derajat rendah, ada tetangga bermasalah "
    "(membidik wilayah hard negative)",
    "S5": "jejak sendiri kuat tapi lingkungan renggang",
    "S6": "jangkar acak berstrata tipe node",
}

#: Batas derajat "rendah" untuk S4. Diturunkan dari sebaran teramati: median
#: derajat node ilegal biasa 9, hard negative 4. Batas 4 memisahkan keduanya
#: tanpa perlu tahu label.
S4_MAX_DEGREE: int = 4

#: Batas porsi tetangga bermasalah untuk S5 — lingkungan disebut renggang bila
#: kurang dari seperempat tetangganya punya aturan menyala.
S5_MAX_NEIGHBOR_SHARE: float = 0.25

#: Seed pengambilan sampel, dipisah dari seed data agar keduanya tidak terkait.
DEFAULT_SAMPLING_SEED: int = 2026


@dataclass(frozen=True)
class NodeSignals:
    """Sinyal teramati per node yang dipakai menentukan strata."""

    node_id: str
    node_type: str
    rule_score: float
    rule_level: str
    own_matches: int
    neighbor_own_matches: int
    neighbor_critical: int
    degree: int

    @property
    def boundary_distance(self) -> float:
        return min(abs(self.rule_score - edge) for edge in LEVEL_BOUNDARIES)


@dataclass
class AnnotationSample:
    """Hasil pengambilan sampel."""

    node_ids: tuple[str, ...]
    stratum_of: dict[str, str]
    order_of: dict[str, int]
    pool_sizes: dict[str, int]
    target_sizes: dict[str, int]
    notes: tuple[str, ...] = ()
    signals: dict[str, NodeSignals] = field(default_factory=dict, repr=False)

    def by_stratum(self) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {name: [] for name in STRATA_ORDER}
        for node_id in self.node_ids:
            grouped[self.stratum_of[node_id]].append(node_id)
        return grouped

    def ordered(self) -> list[str]:
        """Node menurut `annotation_order` — prefiks apa pun tetap berimbang strata."""
        return sorted(self.node_ids, key=lambda node_id: self.order_of[node_id])


def read_weak_labels(path: Path) -> dict[str, tuple[float, str]]:
    """Baca `rule_score` dan `rule_level` dari `weak_labels.csv`.

    Dipakai **hanya** untuk memilih node. Nilainya tidak pernah masuk lembar
    kerja anotator.
    """
    result: dict[str, tuple[float, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            result[row["node_id"]] = (float(row["rule_score"]), row["rule_level"])
    return result


def collect_signals(
    graph: RuleGraph,
    weak_labels: dict[str, tuple[float, str]],
) -> dict[str, NodeSignals]:
    """Hitung sinyal teramati tiap node.

    `own_matches` dihitung ulang lewat `rules.scoring.find_matches` karena
    kolom `triggered_rules` pada `weak_labels.csv` mencampur aturan yang menyala
    pada node itu sendiri dengan yang menyala pada tetangganya — padahal
    perbedaan itulah yang membedakan strata S4 dari S5.
    """
    matches = find_matches(graph, calibrate(graph))
    own_count: dict[str, int] = {}
    for found in matches.values():
        for node_id in found:
            own_count[node_id] = own_count.get(node_id, 0) + 1

    signals: dict[str, NodeSignals] = {}
    for node_id, node in graph.nodes.items():
        score, level = weak_labels.get(node_id, (0.0, "low"))
        neighbors = graph.adjacent(node_id)
        signals[node_id] = NodeSignals(
            node_id=node_id,
            node_type=node.node_type,
            rule_score=score,
            rule_level=level,
            own_matches=own_count.get(node_id, 0),
            neighbor_own_matches=sum(
                1 for other in neighbors if own_count.get(other, 0) >= 1
            ),
            neighbor_critical=sum(
                1
                for other in neighbors
                if weak_labels.get(other, (0.0, "low"))[1] == "critical"
            ),
            degree=graph.degree(node_id),
        )
    return signals


def _matches_stratum(signal: NodeSignals, stratum: str) -> bool:
    """Apakah sebuah node memenuhi syarat satu strata."""
    if stratum == "S1":
        return signal.rule_level == "critical" and signal.own_matches >= 2
    if stratum == "S2":
        return (
            signal.rule_level == "low"
            and signal.own_matches == 0
            and signal.neighbor_critical == 0
        )
    if stratum == "S3":
        return signal.boundary_distance <= BOUNDARY_WINDOW
    if stratum == "S4":
        return (
            signal.own_matches <= 1
            and signal.degree <= S4_MAX_DEGREE
            and signal.neighbor_own_matches >= 1
        )
    if stratum == "S5":
        return (
            signal.own_matches >= 2
            and signal.neighbor_own_matches
            <= S5_MAX_NEIGHBOR_SHARE * max(signal.degree, 1)
        )
    return stratum == "S6"


def _stratum_of(signal: NodeSignals) -> str:
    """Strata pertama yang mengklaim node ini menurut `CLAIM_ORDER`."""
    for stratum in CLAIM_ORDER:
        if _matches_stratum(signal, stratum):
            return stratum
    return "S6"


def build_sample(
    graph: RuleGraph,
    weak_labels: dict[str, tuple[float, str]],
    total: int = 150,
    sampling_seed: int = DEFAULT_SAMPLING_SEED,
    exclude: frozenset[str] | set[str] | None = None,
) -> AnnotationSample:
    """Susun sampel anotasi berstrata.

    Args:
        total: Jumlah node yang dianotasi (target 100-150).
        sampling_seed: Seed pengambilan sampel, terpisah dari seed data.
        exclude: Node yang tidak boleh terpilih, biasanya node yang sudah
            dianotasi pada ronde sebelumnya. Ronde lanjutan harus memakai node
            baru, karena menilai ulang node yang sama terkontaminasi ingatan
            ronde pertama dan kesepakatannya tidak lagi bermakna.

    Kekurangan kandidat pada sebuah strata **tidak** ditutupi diam-diam:
    kuotanya dialihkan ke strata yang masih punya kandidat dan pengalihannya
    dicatat di `notes`. Penyusutan kolam akibat `exclude` juga dicatat di sana,
    karena strata sempit seperti S5 bisa kehabisan kandidat setelah satu ronde.
    """
    rng = np.random.default_rng(sampling_seed)
    signals = collect_signals(graph, weak_labels)
    blocked = frozenset(exclude or ())

    pools: dict[str, list[str]] = {name: [] for name in STRATA_ORDER}
    removed = 0
    for node_id, signal in signals.items():
        if signal.node_type not in ANNOTATABLE_NODE_TYPES:
            continue
        if signal.degree < 1:
            continue
        if node_id in blocked:
            removed += 1
            continue
        pools[_stratum_of(signal)].append(node_id)
    for candidates in pools.values():
        candidates.sort()

    pool_sizes = {name: len(candidates) for name, candidates in pools.items()}
    targets, notes = _allocate_targets(total, pool_sizes)
    if removed:
        notes = [
            f"{removed} node dikeluarkan karena sudah dianotasi pada ronde "
            f"sebelumnya; ukuran kolam di atas sudah memperhitungkannya",
            *notes,
        ]

    chosen: dict[str, list[str]] = {}
    for name in STRATA_ORDER:
        candidates = pools[name]
        take = targets[name]
        if take <= 0:
            chosen[name] = []
            continue
        if name == "S6":
            chosen[name] = _sample_by_type(rng, candidates, signals, take)
        else:
            picks = rng.permutation(len(candidates))[:take]
            chosen[name] = sorted(candidates[int(index)] for index in picks)

    stratum_of = {
        node_id: name for name, members in chosen.items() for node_id in members
    }
    order_of = _round_robin_order(chosen, signals)

    return AnnotationSample(
        node_ids=tuple(sorted(stratum_of)),
        stratum_of=stratum_of,
        order_of=order_of,
        pool_sizes=pool_sizes,
        target_sizes=targets,
        notes=tuple(notes),
        signals=signals,
    )


def _allocate_targets(
    total: int, pool_sizes: dict[str, int]
) -> tuple[dict[str, int], list[str]]:
    """Bagi `total` rata ke enam strata, alihkan kuota strata yang kurang."""
    base = total // len(STRATA_ORDER)
    targets = {name: base for name in STRATA_ORDER}
    for index in range(total - base * len(STRATA_ORDER)):
        targets[STRATA_ORDER[index]] += 1

    notes: list[str] = []
    shortfall = 0
    for name in STRATA_ORDER:
        available = pool_sizes[name]
        if targets[name] > available:
            notes.append(
                f"strata {name} hanya punya {available} kandidat dari target "
                f"{targets[name]}; {targets[name] - available} kuota dialihkan"
            )
            shortfall += targets[name] - available
            targets[name] = available

    while shortfall > 0:
        room = [
            name
            for name in STRATA_ORDER
            if pool_sizes[name] - targets[name] > 0
        ]
        if not room:
            notes.append(
                f"{shortfall} kuota tidak bisa dialihkan; seluruh strata sudah habis"
            )
            break
        for name in room:
            if shortfall <= 0:
                break
            targets[name] += 1
            shortfall -= 1

    return targets, notes


def _sample_by_type(
    rng: np.random.Generator,
    candidates: list[str],
    signals: dict[str, NodeSignals],
    take: int,
) -> list[str]:
    """Ambil sampel S6 berimbang antar tipe node."""
    by_type: dict[str, list[str]] = {}
    for node_id in candidates:
        by_type.setdefault(signals[node_id].node_type, []).append(node_id)

    types = sorted(by_type)
    if not types:
        return []

    quota = {node_type: take // len(types) for node_type in types}
    for index in range(take - sum(quota.values())):
        quota[types[index % len(types)]] += 1

    picked: list[str] = []
    leftover = 0
    for node_type in types:
        pool = by_type[node_type]
        want = min(quota[node_type], len(pool))
        leftover += quota[node_type] - want
        picks = rng.permutation(len(pool))[:want]
        picked.extend(pool[int(index)] for index in picks)

    if leftover > 0:
        remaining = sorted(set(candidates) - set(picked))
        picks = rng.permutation(len(remaining))[:leftover]
        picked.extend(remaining[int(index)] for index in picks)

    return sorted(picked)


def _round_robin_order(
    chosen: dict[str, list[str]],
    signals: dict[str, NodeSignals],
) -> dict[str, int]:
    """Urutan anotasi: bergilir antar strata, di dalam strata skor menurun.

    Dua sifat yang dituntut ablasi A5, yang mengukur performa pada 10, 25,
    50, 100, dan 150 anotasi pertama:

    1. **Tiap prefiks berimbang strata.** Kalau urutannya menumpuk satu strata di
       depan, kurva A5 mengukur keberuntungan urutan alih-alih nilai per anotasi.
       Karena itu bergilir antar strata.

    2. **Node paling mencurigakan lebih dulu di dalam strata masing-masing.**
       Urutan acak di dalam strata sempat membuat 10 dan 25 anotasi pertama tidak
       memuat satu pun node positif, sehingga ujung bawah kurva A5 mendatar
       bukan karena metodenya. Mengurutkan menurun berdasarkan skor rule juga
       lebih realistis: analis dengan kuota 10 review memang membuka yang paling
       berisiko lebih dulu.

    Sepenuhnya deterministik — tanpa keacakan, sehingga urutan yang sama selalu
    dihasilkan dari sampel yang sama.
    """
    queues: dict[str, list[str]] = {}
    for name, members in chosen.items():
        queues[name] = sorted(
            members,
            key=lambda node_id: (-signals[node_id].rule_score, node_id),
        )

    order: dict[str, int] = {}
    position = 0
    while any(queues.values()):
        for name in STRATA_ORDER:
            if not queues[name]:
                continue
            order[queues[name].pop(0)] = position
            position += 1
    return order
