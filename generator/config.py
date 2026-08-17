"""Parameter generator data sintetik SATPAM.

Semua angka yang menentukan bentuk dataset dikumpulkan di satu tempat supaya
bisa di-dump apa adanya ke `manifest.params` — dataset harus bisa
direproduksi dari seed + manifest saja.

Isi modul dikelompokkan mengikuti sumbernya, dan pengelompokan itu penting:

- Bagian A — parameter target
- Bagian B — parameter aturan generatif G1..G8 (tiap field diberi
  tag aturannya)
- Bagian C — noise wajib
- Bagian D — batas persentil temporal split
- Bagian E — kalibrasi populasi dan distribusi fitur. **Bukan** aturan
  generatif dan tidak mengklaim sitasi apa pun. Angka di sini hanya mengatur
  agar kelas ilegal dan sah saling tumpang tindih; tanpa itu tugas deteksi
  jadi trivial (lihat catatan pada `legit_*` di bawah).

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang
tidak boleh dilanggar.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, NamedTuple

from generator.schema import ILLICIT_CAPABLE_NODE_TYPES, NODE_TYPES

#: Versi generator, dicatat di `manifest.generator_version`.
GENERATOR_VERSION = "1.0.0"

#: Seed resmi eksperimen (minimal 5 seed).
OFFICIAL_SEEDS: tuple[int, ...] = (42, 43, 44, 45, 46)

#: Rentang inklusif untuk nilai yang di-sample generator.
IntRange = tuple[int, int]
FloatRange = tuple[float, float]


class BetaDist(NamedTuple):
    """Distribusi Beta untuk nilai yang terbatas di [0, 1]."""

    a: float
    b: float


class GammaDist(NamedTuple):
    """Distribusi Gamma untuk hitungan tak-negatif (dibulatkan saat dipakai)."""

    shape: float
    scale: float


class LogNormalDist(NamedTuple):
    """Distribusi lognormal untuk nominal rupiah, diparameterkan via median."""

    median: float
    sigma: float


@dataclass(frozen=True)
class GeneratorParams:
    """Seluruh parameter satu kali jalan generator.

    Frozen supaya tidak ada modul hilir yang mengubah parameter di tengah
    jalan — kalau butuh varian, pakai `dataclasses.replace`.
    """

    # -----------------------------------------------------------------
    # Bagian A — parameter target
    # -----------------------------------------------------------------

    seed: int = 42

    #: Total node. Target sekitar 5.000.
    n_nodes_target: int = 5_000

    #: Target total edge (18.000-20.000). Informatif saja:
    #: jumlah edge adalah akibat dari kerapatan di Bagian B/E, bukan angka
    #: yang dipaksa. Dipakai `validate.py` hanya untuk melaporkan selisih.
    n_edges_target: IntRange = (18_000, 20_000)

    #: Jumlah operator jaringan. Target 10-14.
    n_operators: IntRange = (10, 14)

    #: Anomaly ratio terhadap TOTAL node. Target 4-6%.
    #: Contoh manifest (240 / 5.000 = 0,048) memakai denominator yang sama.
    anomaly_ratio: FloatRange = (0.04, 0.06)

    #: Jumlah operator lintas-ekosistem (`gt_ecosystem='both'`). Target 2-3.
    n_both_operators: IntRange = (2, 3)

    #: Lama rentang waktu simulasi dalam bulan. Ditetapkan 18 bulan.
    simulation_months: int = 18

    #: Awal rentang simulasi (tanggal tetap, bukan waktu sekarang — supaya
    #: seed yang sama selalu menghasilkan `first_seen_at` yang sama).
    timeline_start: str = "2025-01-01"

    #: Zona waktu yang dipakai pada seluruh kolom ISO8601 keluaran.
    timezone_offset_hours: int = 7  # WIB

    # -----------------------------------------------------------------
    # Bagian B — parameter aturan generatif
    # -----------------------------------------------------------------

    #: G1 — porsi `uses_account` operator judol yang mengarah ke e-wallet
    #: ber-QRIS. Sumber PPATK 23 Juli 2026: ~80% frekuensi deposit.
    g1_qris_share: float = 0.80

    #: G1 — hitungan transaksi node finansial operator: frekuensi tinggi.
    #: Berpasangan dengan `txn_count_legit` yang berekor panjang; lihat catatan
    #: tumpang tindih di sana.
    g1_txn_count_illicit: GammaDist = GammaDist(shape=3.5, scale=45.0)

    #: G1 — nominal per transaksi pada node finansial operator: nominal kecil.
    g1_txn_amount_illicit: LogNormalDist = LogNormalDist(median=120_000.0, sigma=0.8)

    #: G2 — porsi rekening penampung operator yang bertipe dormant diambil
    #: alih: `first_seen_at` jauh di belakang, aktivitas baru muncul terlambat.
    #: Sumber PPATK.
    g2_dormant_account_share: float = 0.30

    #: G2 — jeda minimum (hari) antara `first_seen_at` rekening dormant dan
    #: saat ia mulai dipakai operator.
    g2_dormant_idle_days: IntRange = (180, 420)

    #: G2 — banyaknya transfer dari satu rekening pengumpul ke rekening
    #: konsolidasi. Berlapis, bukan sekali kirim: "proxy account" pada aturan G2
    #: memang dipakai untuk melapis aliran dana. Setelan satu transfer per
    #: rekening sempat membuat `feat_degree_out` justru lebih tinggi di sisi sah
    #: (AUC 0,39 — terbalik), karena rekening sah bertransaksi jauh lebih sering.
    g2_layering_transfers: IntRange = (5, 10)

    #: G3 — porsi e-wallet operator yang dibuat sebagai merchant QRIS fiktif.
    #: Sumber PPATK 23 Juli 2026. Hanya struktural: tidak ada nama,
    #: identitas, atau nomor apa pun yang disimpan.
    g3_fictitious_merchant_share: float = 0.75

    #: G4 — panjang rantai rotasi domain (`redirects_to` lama -> baru).
    #: Sumber Komdigi-TrustPositif.
    g4_rotation_chain_len: IntRange = (2, 5)

    #: G4 — porsi domain operator yang masuk ke dalam rantai rotasi.
    g4_rotated_domain_share: float = 0.70

    #: G4 — jeda antar-domain dalam satu rantai rotasi (hari).
    g4_rotation_gap_days: IntRange = (14, 90)

    #: G5 — jumlah akun promosi per domain/apk operator. Sumber kerja sama
    #: Komdigi-Meta: promosi via ribuan akun media sosial otomatis.
    g5_promoters_per_target: IntRange = (4, 14)

    #: G5 — peluang akun promosi juga memuat tautan unduhan APK, di samping
    #: mempromosikannya. Semula setiap promotor selalu menerbitkan `promotes`
    #: **dan** `linked_to_apk` sekaligus, sehingga derajat APK operator praktis
    #: berlipat dua dan derajat APK sendirian membelah kelas pada AUC 0,97.
    #: Tidak setiap akun promosi memang menyertakan tautan unduhannya.
    g5_apk_link_prob: float = 0.50

    #: G6 — jumlah domain operator yang berbagi satu nomor kontak.
    #: Sumber PPATK.
    g6_domains_per_shared_phone: IntRange = (2, 5)

    #: G7 — porsi node infrastruktur operator `both` (rekening mule, APK,
    #: akun promosi) yang dipakai bersama oleh sisi judol dan sisi pinjol.
    #: Berbagi infrastruktur BOLEH; aliran dana langsung
    #: judol->pinjol DILARANG (PPATK Okt 2023) dan
    #: dijaga oleh assert di `validate.py`.
    g7_shared_infra_share: float = 0.35

    #: G8 — porsi korban sisi judol yang juga menjadi korban pinjol ilegal.
    #: Sumber PPATK (Natsir Kongah).
    g8_shared_victim_share: float = 0.20

    # -----------------------------------------------------------------
    # Bagian C — noise wajib
    # -----------------------------------------------------------------

    #: Porsi node ilegal yang dibuat nyaris tanpa jejak. Target 15-20%.
    hard_negative_share: FloatRange = (0.15, 0.20)

    #: Porsi node sah yang dibuat tampak mencurigakan. Target 3-5%.
    hard_positive_share: FloatRange = (0.03, 0.05)

    #: Porsi edge yang dihapus acak (missing evidence). Target 10%.
    edge_drop_share: float = 0.10

    #: Porsi edge palsu yang ditambahkan (false link). Target 2%.
    #: Edge palsu tetap wajib type-legal.
    false_edge_share: float = 0.02

    #: Jumlah edge yang tetap dipertahankan untuk node hard negative supaya
    #: ia tidak jadi node terisolasi yang mustahil dipelajari siapa pun.
    hard_negative_kept_edges: IntRange = (1, 2)

    #: Kemiringan pemilihan hard negative ke arah node yang paling baru muncul.
    #: Bobot = 1 + bias x recency, jadi node terbaru sekitar 3x lebih mungkin
    #: terpilih. Hard negative paling realistis memang infrastruktur yang baru
    #: dipasang dan belum mengumpulkan jejak — misalnya domain terakhir dalam
    #: rantai rotasi G4. Efek sampingnya sejalan dengan skenario early warning:
    #: sebagian hard negative jatuh ke split `val`/`test`.
    hard_negative_recency_bias: float = 2.0

    # -----------------------------------------------------------------
    # Bagian D — temporal split
    # -----------------------------------------------------------------

    #: Persentil `first_seen_at` batas atas `train`. Ditetapkan di persentil 70.
    split_train_pct: float = 70.0

    #: Persentil `first_seen_at` batas atas `val`. Ditetapkan di persentil 85.
    split_val_pct: float = 85.0

    # -----------------------------------------------------------------
    # Bagian E — kalibrasi populasi dan distribusi fitur
    #
    # BUKAN aturan generatif. Angka di sini tidak mengklaim sitasi.
    # Fungsinya menjaga agar kelas ilegal dan sah tumpang tindih: kalau node
    # sah dibiarkan hampir tanpa edge, `feat_degree_*` sendirian sudah
    # memisahkan kelas dan seluruh metrik jadi tidak bermakna.
    # -----------------------------------------------------------------

    #: Komposisi tipe node di seluruh graph. Harus berjumlah 1,0.
    #: `social_account` dominan agar konsisten dengan G5.
    node_type_mix: dict[str, float] = field(
        default_factory=lambda: {
            "domain": 0.14,
            "phone": 0.10,
            "bank_account": 0.09,
            "ewallet": 0.09,
            "apk": 0.04,
            "social_account": 0.30,
            "report": 0.14,
            "victim": 0.10,
        }
    )

    #: Komposisi tipe node di dalam satu operator. Harus berjumlah 1,0 dan
    #: hanya boleh memuat tipe pada `ILLICIT_CAPABLE_NODE_TYPES`.
    operator_node_type_mix: dict[str, float] = field(
        default_factory=lambda: {
            "domain": 0.16,
            "phone": 0.08,
            "bank_account": 0.11,
            "ewallet": 0.14,
            "apk": 0.05,
            "social_account": 0.46,
        }
    )

    #: Porsi operator judol di antara operator yang hanya satu ekosistem
    #: (sisanya pinjol). Nilai 0,70 mereproduksi contoh manifest
    #: (`judol 7, pinjol 3, both 2` pada 12 operator). Bukan aturan generatif.
    judol_share_of_single_ecosystem: float = 0.70

    #: Ukuran minimum satu operator. Di bawah ini komposisi aturan generatif tidak lagi
    #: muat: sebuah operator butuh setidaknya domain + akun finansial + akun
    #: promosi agar aturan G1/G5/G6 punya tempat bekerja.
    min_operator_size: int = 8

    #: Konsentrasi Dirichlet saat membagi node ilegal ke antar-operator.
    #: Makin kecil, makin timpang ukuran antar-operator. Dipatok 2,0 agar ada
    #: beberapa operasi besar dan banyak operasi kecil — penindakan Satgas
    #: PASTI memperlihatkan skala operasi yang sangat beragam, dan operator
    #: kecil justru yang paling sulit dideteksi.
    operator_size_concentration: float = 2.0

    #: Batas atas posisi relatif kelahiran operator di dalam rentang simulasi.
    #: Operator yang lahir terlalu dekat akhir rentang tidak punya ruang untuk
    #: rotasi domain (G4), sehingga bagian `test` kehilangan struktur.
    operator_birth_max_frac: float = 0.75

    #: Peluang sebuah operator masih aktif sampai akhir rentang simulasi.
    #: Operator yang masih aktif inilah penyumbang node positif di split
    #: `val`/`test` — tanpa mereka AUPRC pada `test` jadi tidak bermakna.
    operator_still_active_prob: float = 0.60

    #: Umur operator yang sudah berhenti, sebagai fraksi rentang simulasi.
    operator_lifespan_frac: FloatRange = (0.15, 0.60)

    #: Ekor umur node ilegal setelah operatornya berhenti (hari) — infrastruktur
    #: tidak mati tepat bersamaan dengan operatornya.
    illicit_lifespan_tail_days: IntRange = (0, 45)

    #: Lama domain lama masih hidup setelah penerusnya muncul (G4). Rotasi
    #: bukan pemutusan seketika; ada masa tumpang tindih.
    rotation_overlap_days: IntRange = (3, 30)

    #: Peluang sebuah node sah masih hidup sampai akhir rentang simulasi.
    #:
    #: Angka ini menahan kebocoran lewat `feat_age_days`. Dengan setelan awal
    #: yang longgar (0,55), umur sendirian sudah memisahkan kelas pada AUC 0,33
    #: — padahal tidak ada satu pun aturan generatif yang menyatakan node ilegal
    #: berumur lebih pendek. Itu artefak konstruksi, bukan fenomena yang
    #: dimodelkan, dan ia memberi hadiah gratis kepada semua metode sekaligus
    #: memampatkan perbandingan antar-metode.
    #:
    #: Disetel ke 0,28 sehingga AUC umur sendirian menjadi 0,491 (rerata 5 seed,
    #: rentang 0,453–0,506). Sisa sinyal yang tipis itu dibiarkan mengarah ke
    #: sisi yang wajar — node ilegal sedikit lebih muda karena rotasi G4 —
    #: bukan ke arah terbalik. Churn domain sah yang tinggi juga bukan asumsi
    #: mengada-ada: sebagian besar domain baru memang tidak bertahan setahun.
    legit_still_up_prob: float = 0.28

    #: Umur node sah yang sudah mati, sebagai fraksi rentang simulasi. Rentang
    #: dibuat lebar agar bertumpang tindih dengan umur node ilegal.
    legit_lifespan_frac: FloatRange = (0.02, 0.40)

    #: `feat_kw_score` node operator (selain hard negative).
    #:
    #: Setelan awal Beta(5,0; 2,5) lawan Beta(2,0; 6,0) hampir tidak
    #: bertumpang tindih dan membuat kata kunci sendirian mencapai AUC 0,85.
    #: Itu bertentangan dengan kenyataan di lapangan: kelemahan yang
    #: sudah terdokumentasi dari pendekatan kata kunci Mesin AIS Komdigi justru
    #: banyaknya false positive. Disetel ulang sehingga AUC-nya 0,68.
    kw_score_illicit: BetaDist = BetaDist(a=3.0, b=2.2)

    #: `feat_kw_score` node sah (dan node hard negative, yang meminjam
    #: distribusi ini justru supaya sulit dibedakan).
    kw_score_legit: BetaDist = BetaDist(a=2.2, b=3.2)

    #: Hitungan transaksi node finansial sah, berekor panjang.
    #:
    #: Ekor panjang itu wajib. Dengan Gamma(2,0; 12,0) yang semula dipakai,
    #: `feat_txn_count` sendirian mencapai AUC 0,86 — ambang sederhana sudah
    #: mengalahkan segalanya dan eksperimennya jadi tidak ada gunanya. Di
    #: lapangan pun rekening penampung judol tidak bisa dibedakan dari merchant
    #: UMKM yang ramai hanya dari jumlah transaksinya; justru itu alasan
    #: struktur graph dibutuhkan. Setelan ini menghasilkan AUC 0,72.
    txn_count_legit: GammaDist = GammaDist(shape=1.0, scale=85.0)

    #: Nominal per transaksi node finansial sah. Median diturunkan dan sebaran
    #: dilebarkan agar mencakup warung bertiket kecil sampai usaha bertiket
    #: besar. Tanpa itu `feat_txn_amount_sum` justru informatif ke arah
    #: terbalik (AUC 0,36 — total besar menandakan sah).
    txn_amount_legit: LogNormalDist = LogNormalDist(median=320_000.0, sigma=1.35)

    #: Hitungan dan nominal transaksi node `victim`.
    txn_count_victim: GammaDist = GammaDist(shape=1.8, scale=6.0)
    txn_amount_victim: LogNormalDist = LogNormalDist(median=350_000.0, sigma=1.1)

    #: Porsi e-wallet sah yang memakai QRIS — sengaja tidak nol supaya
    #: `feat_is_qris` bukan penanda kelas yang sempurna.
    legit_qris_share: float = 0.45

    #: Komposisi satu "usaha sah" — klaster latar yang menjadi pembanding
    #: klaster operator.
    #:
    #: Node sah TIDAK boleh dibiarkan sebagai taburan edge acak. Klaster
    #: operator padat, jadi kalau latarnya renggang maka `feat_degree_in/out`
    #: sendirian sudah membelah kelas dan seluruh angka AUPRC jadi bohong.
    #: Usaha sah pun nyata-nyata punya domain, nomor kontak, rekening, dan akun
    #: promosinya sendiri. Yang membedakannya dari operator bukan *banyaknya*
    #: edge melainkan *motifnya*: rekening dan nomor kontak yang dipakai lintas
    #: banyak domain (G6), rantai rotasi domain (G4), dan infrastruktur yang
    #: dibagi dua ekosistem (G7).
    #:
    #: Batas atas `legit_domains_per_business` sengaja lebih dari satu supaya
    #: "beberapa domain berbagi satu nomor" tidak menjadi pembeda yang sempurna
    #: — perusahaan sah dengan dua-tiga situs itu hal biasa.
    #:
    #: Hanya jumlah domain per usaha yang ditentukan di sini. Tipe node lain
    #: dibagi rata dari seluruh kolam node sah ke seluruh usaha oleh
    #: `evidence._partition_legit_businesses`, sehingga kerapatannya otomatis
    #: mengikuti `node_type_mix` dan tidak ada usaha yang tidak kebagian.
    legit_domains_per_business: IntRange = (1, 3)

    #: Porsi domain sah yang memakai nomor kontak di luar usahanya sendiri —
    #: agensi, hosting, layanan pelanggan pihak ketiga. Ini yang memberi ekor
    #: panjang pada derajat nomor sah; lihat catatan di
    #: `evidence._sow_legit_shared_services`.
    legit_shared_phone_share: float = 0.15

    #: Kerapatan edge latar untuk node sah, per node src yang memenuhi syarat.
    #: Angka-angka ini disetel dengan mengukur AUC derajat per tipe node; latar
    #: yang renggang membuat `feat_degree_in/out` sendirian membelah kelas.
    legit_promotes_per_social: IntRange = (4, 9)
    legit_contacts_per_domain: IntRange = (1, 3)
    legit_uses_account_per_domain: IntRange = (2, 5)
    legit_uses_account_per_phone: IntRange = (1, 3)
    legit_uses_account_per_apk: IntRange = (0, 2)
    legit_contacts_per_apk: IntRange = (0, 2)
    legit_transfers_per_account: IntRange = (4, 8)
    legit_transfers_per_victim: IntRange = (1, 3)
    legit_contacts_prob_social: float = 0.70
    legit_linked_apk_prob_social: float = 0.50
    legit_linked_apk_prob_domain: float = 0.70
    legit_redirects_prob_domain: float = 0.50

    #: Kerapatan `mentions` per node `report`.
    #:
    #: Bersama `legit_promotes_per_social` dan `legit_transfers_per_account`,
    #: angka ini disetel agar jumlah edge **pasca-noise** masuk target
    #: (18.000–20.000). Yang dihitung orang adalah baris di `edges.csv`, dan
    #: berkas itu keluaran akhir: noise memotong bersih sekitar 8% (buang
    #: 10%, tambah 2%), jadi kerapatan pra-noise harus lebih tinggi dari target.
    mentions_per_report: IntRange = (4, 8)

    #: Bobot pemilihan sasaran `mentions`: node operator lebih sering
    #: dilaporkan, hard negative hampir tidak pernah, hard positive ikut
    #: terkena laporan keliru.
    #:
    #: Bobot 6,0 yang semula dipakai membuat `feat_report_count` sendirian
    #: mencapai AUC 0,83. Laporan memang sinyal nyata dan tidak boleh dibuat
    #: netral, tetapi 0,83 dari satu kolom terlalu murah. Diturunkan ke 2,5
    #: sehingga AUC-nya sekitar 0,71.
    mention_weight_illicit: float = 2.5
    mention_weight_hard_negative: float = 0.2
    mention_weight_hard_positive: float = 1.8
    mention_weight_legit: float = 1.0

    #: Jumlah `report` yang diajukan satu `victim`.
    reports_per_victim: IntRange = (1, 2)

    #: Rentang bobot bukti (`edges.csv.weight`, berskala 0-1), per **tier
    #: observasi**. Rentangnya sengaja bertumpang tindih lebar.
    #:
    #: Setelan awal memakai tiga tier yang dipilih **per aturan generatif**:
    #: edge dari G1/G2/G4/G6/G7/G8 mendapat tier kuat, edge latar node sah
    #: mendapat tier sedang atau lemah. Akibatnya bobot praktis menjadi salinan
    #: label: median 0,671 untuk edge antar dua node ilegal berbanding 0,447
    #: untuk edge antar dua node sah, dan rata-rata bobot per node sendirian
    #: memisahkan kelas pada AUC 0,795 — lebih bocor daripada fitur mana pun.
    #:
    #: Sekarang tier ditentukan **jenis relasinya**, bukan siapa di belakangnya.
    #: Itu juga arti yang benar dari "kekuatan bukti": seberapa andal
    #: sebuah tautan teramati bergantung pada kanal pengamatannya, bukan pada
    #: sah atau tidaknya pihak yang diamati. Tautan teknis yang bisa diperiksa
    #: langsung lebih andal daripada sebutan di dalam sebuah laporan, terlepas
    #: dari siapa pemiliknya.
    weight_tier_high: FloatRange = (0.60, 1.00)
    weight_tier_mid: FloatRange = (0.35, 0.85)
    weight_tier_low: FloatRange = (0.15, 0.60)

    #: Pemeta tipe relasi ke tier bobotnya.
    #:
    #: - `high` — tautan teknis yang langsung bisa diperiksa: header pengalihan,
    #:   nomor kontak yang tercantum, kanal pembayaran yang dipakai, dan
    #:   pengajuan laporan yang faktanya tercatat.
    #: - `mid` — tautan hasil penelusuran: aliran dana, promosi, tautan unduhan.
    #: - `low` — sebutan di dalam laporan; sebuah laporan adalah klaim, bukan
    #:   bukti.
    weight_tier_of_relation: dict[str, str] = field(
        default_factory=lambda: {
            "redirects_to": "high",
            "contacts": "high",
            "uses_account": "high",
            "reported": "high",
            "transferred_to": "mid",
            "promotes": "mid",
            "linked_to_apk": "mid",
            "mentions": "low",
        }
    )

    def __post_init__(self) -> None:
        """Cek konsistensi parameter sebelum dipakai modul hilir."""
        _check_mix(self.node_type_mix, set(NODE_TYPES), "node_type_mix")
        _check_mix(
            self.operator_node_type_mix,
            set(ILLICIT_CAPABLE_NODE_TYPES),
            "operator_node_type_mix",
        )

        for name in _RANGE_FIELDS:
            low, high = getattr(self, name)
            if low > high:
                raise ValueError(f"{name}: batas bawah {low} > batas atas {high}")

        for name in _PROBABILITY_FIELDS:
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} harus di [0, 1], dapat {value}")

        for name in ("anomaly_ratio", "hard_negative_share", "hard_positive_share"):
            low, high = getattr(self, name)
            if not 0.0 <= low <= high <= 1.0:
                raise ValueError(f"{name} harus berupa rentang di [0, 1], dapat {(low, high)}")

        if not 0.0 <= self.split_train_pct < self.split_val_pct <= 100.0:
            raise ValueError(
                "batas split harus 0 <= split_train_pct < split_val_pct <= 100, "
                f"dapat {self.split_train_pct} dan {self.split_val_pct}"
            )

        _check_weight_tiers(self.weight_tier_of_relation)

        if self.simulation_months <= 0:
            raise ValueError("simulation_months harus positif")
        if self.n_nodes_target <= 0:
            raise ValueError("n_nodes_target harus positif")

    def to_manifest_params(self) -> dict[str, Any]:
        """Seluruh parameter sebagai dict JSON-safe untuk `manifest.params`.

        Ditambah `generator_version` supaya satu blok `params` cukup untuk
        merekonstruksi dataset tanpa menebak versi kode.
        """
        payload = _jsonable(dataclasses.asdict(self))
        payload["generator_version"] = GENERATOR_VERSION
        return payload


#: Field bertipe rentang (low, high) — dicek terurut oleh `__post_init__`.
_RANGE_FIELDS: tuple[str, ...] = (
    "n_edges_target",
    "n_operators",
    "anomaly_ratio",
    "n_both_operators",
    "hard_negative_share",
    "hard_positive_share",
    "hard_negative_kept_edges",
    "g2_dormant_idle_days",
    "g2_layering_transfers",
    "g4_rotation_chain_len",
    "g4_rotation_gap_days",
    "g5_promoters_per_target",
    "g6_domains_per_shared_phone",
    "weight_tier_high",
    "weight_tier_mid",
    "weight_tier_low",
    "mentions_per_report",
    "reports_per_victim",
    "legit_promotes_per_social",
    "legit_contacts_per_domain",
    "legit_uses_account_per_domain",
    "legit_uses_account_per_phone",
    "legit_uses_account_per_apk",
    "legit_contacts_per_apk",
    "legit_transfers_per_account",
    "legit_transfers_per_victim",
    "legit_domains_per_business",
    "operator_lifespan_frac",
    "illicit_lifespan_tail_days",
    "rotation_overlap_days",
    "legit_lifespan_frac",
)

#: Field bertipe probabilitas/porsi tunggal — dicek berada di [0, 1].
_PROBABILITY_FIELDS: tuple[str, ...] = (
    "g1_qris_share",
    "g2_dormant_account_share",
    "g3_fictitious_merchant_share",
    "g4_rotated_domain_share",
    "g5_apk_link_prob",
    "g7_shared_infra_share",
    "g8_shared_victim_share",
    "edge_drop_share",
    "false_edge_share",
    "legit_qris_share",
    "legit_contacts_prob_social",
    "legit_linked_apk_prob_social",
    "legit_linked_apk_prob_domain",
    "legit_redirects_prob_domain",
    "judol_share_of_single_ecosystem",
    "operator_birth_max_frac",
    "operator_still_active_prob",
    "legit_still_up_prob",
    "legit_shared_phone_share",
)


#: Nama tier bobot yang sah.
WEIGHT_TIERS: tuple[str, ...] = ("high", "mid", "low")


def _check_weight_tiers(mapping: dict[str, str]) -> None:
    """Pastikan setiap tipe relasi punya tier bobot yang dikenal.

    Diperiksa di sini, bukan saat menerbitkan edge: relasi yang belum diberi tier
    harus gagal saat parameter dibuat, bukan di tengah jalan setelah separuh
    graph terbentuk.
    """
    from generator.schema import REL_TYPES

    unknown_relations = sorted(set(mapping) - set(REL_TYPES))
    if unknown_relations:
        raise ValueError(
            f"weight_tier_of_relation memuat relasi tak dikenal: {unknown_relations}"
        )
    missing = sorted(set(REL_TYPES) - set(mapping))
    if missing:
        raise ValueError(
            f"weight_tier_of_relation belum memberi tier untuk relasi: {missing}"
        )
    bad_tiers = sorted({tier for tier in mapping.values() if tier not in WEIGHT_TIERS})
    if bad_tiers:
        raise ValueError(
            f"weight_tier_of_relation memakai tier tak dikenal: {bad_tiers}; "
            f"harus salah satu dari {list(WEIGHT_TIERS)}"
        )


def _check_mix(mix: dict[str, float], allowed: set[str], label: str) -> None:
    """Pastikan komposisi tipe node lengkap, dikenal, dan berjumlah 1,0."""
    unknown = set(mix) - allowed
    if unknown:
        raise ValueError(f"{label}: tipe node tak dikenal {sorted(unknown)}")
    missing = allowed - set(mix)
    if missing:
        raise ValueError(f"{label}: tipe node belum diberi porsi {sorted(missing)}")
    if any(value < 0 for value in mix.values()):
        raise ValueError(f"{label}: porsi negatif tidak boleh")
    total = sum(mix.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"{label}: jumlah porsi harus 1,0, dapat {total}")


def _jsonable(value: Any) -> Any:
    """Ubah struktur parameter menjadi bentuk yang aman untuk `json.dump`.

    NamedTuple distribusi diubah menjadi dict agar nama fieldnya ikut tercatat
    di manifest — `{"a": 5.0, "b": 2.5}` jauh lebih berguna dibanding `[5.0, 2.5]`
    saat orang lain membaca manifest berbulan-bulan kemudian.
    """
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if hasattr(value, "_asdict"):  # NamedTuple
        return {key: _jsonable(item) for key, item in value._asdict().items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
