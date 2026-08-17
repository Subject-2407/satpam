"""
Pemetaan kontrak data v2 ke skema node/relationship backend v1.

Backend SATPAM (`integration/backend/`, spec di `docs-old/openapi.json`) ditulis
untuk skema v1 dengan 25 tipe node. Kontrak data v2 menyederhanakannya
menjadi 8 tipe node dan 8 tipe relasi. Modul ini satu-satunya tempat pemetaan
kedua skema itu ditulis, supaya tidak tersebar di beberapa skrip.

Semua delapan tipe node dan delapan tipe relasi v2 punya padanan persis di
`ALLOWED_NODE_LABELS` dan `ALLOWED_RELATIONSHIP_TYPES` backend v1, sehingga
tidak ada satu pun kolom kontrak data v2 yang perlu diubah.

## Dua hal yang dijaga modul ini

1. **`gt_*` tidak boleh keluar dari mesin lokal.** `GET /api/entities/{node_type}/{node_id}`
   mengembalikan node Neo4j apa adanya tanpa menyaring properti. Menempelkan
   `gt_illicit` di sana sama dengan menerbitkan kunci jawaban lewat API — dan
   responden studi dapat melihatnya, yang membatalkan validitas studi itu.
   `sanitize_properties()` menolaknya, bukan sekadar tidak menyertakannya.

2. **Tidak ada nilai yang menyerupai data pribadi nyata.** Skema v1 mewajibkan
   field kosmetik (`normalizedNumber`, `maskedAccountNumber`, `profileUrl`, …)
   yang tidak ada padanannya di kontrak v2. Field itu disintesis deterministik
   dari `node_id` dengan bentuk yang mustahil dibaca sebagai identitas nyata.
"""

from __future__ import annotations

from typing import Any

# --- Pemetaan tipe -----------------------------------------------------------

# v2 node_type -> (label Neo4j v1, nama field di NodesContainer)
NODE_TYPE_TO_V1: dict[str, tuple[str, str]] = {
    "domain": ("Domain", "domains"),
    "phone": ("PhoneNumber", "phoneNumbers"),
    "bank_account": ("BankAccount", "bankAccounts"),
    "ewallet": ("EWallet", "eWallets"),
    "apk": ("APK", "apks"),
    "social_account": ("SocialMediaAccount", "socialMediaAccounts"),
    "report": ("Report", "reports"),
    "victim": ("Victim", "victims"),
}

# v2 rel_type -> tipe relationship Neo4j v1
REL_TYPE_TO_V1: dict[str, str] = {
    "promotes": "PROMOTES",
    "contacts": "CONTACTS",
    "uses_account": "USES_ACCOUNT",
    "transferred_to": "TRANSFERRED_TO",
    "mentions": "MENTIONS",
    "reported": "REPORTED",
    "linked_to_apk": "LINKED_TO_APK",
    "redirects_to": "REDIRECTS_TO",
}

# Kolom fitur kontrak v2 yang ikut dibawa ke Neo4j. Ini masukan model, bukan
# jawaban, jadi aman tampil di API dan berguna untuk panel bukti dashboard.
FEATURE_COLUMNS: tuple[str, ...] = (
    "feat_degree_in",
    "feat_degree_out",
    "feat_age_days",
    "feat_report_count",
    "feat_txn_count",
    "feat_txn_amount_sum",
    "feat_is_qris",
    "feat_kw_score",
)

# Prefiks properti yang DILARANG masuk payload impor. Lihat docstring modul.
FORBIDDEN_PREFIXES: tuple[str, ...] = ("gt_",)

# Nama eksplisit yang dilarang, sebagai jaring kedua bila prefiks diubah orang lain.
FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {"gt_illicit", "gt_operator_id", "gt_ecosystem", "groundTruth", "gtIllicit"}
)

SOURCE = "synthetic_generator_v2"


class GroundTruthLeakError(RuntimeError):
    """Dilempar bila properti `gt_*` hampir masuk payload yang dikirim ke Neo4j.

    Sengaja berupa exception yang menghentikan impor, bukan peringatan yang
    bisa diabaikan: kebocoran ini merusak studi responden secara
    permanen dan tidak terlihat dari luar setelah data masuk.
    """


def sanitize_properties(props: dict[str, Any]) -> dict[str, Any]:
    """Kembalikan `props` bila bersih; lempar `GroundTruthLeakError` bila tidak."""
    offenders = sorted(
        key
        for key in props
        if key in FORBIDDEN_KEYS or key.startswith(FORBIDDEN_PREFIXES)
    )
    if offenders:
        raise GroundTruthLeakError(
            "Properti ground truth hampir dikirim ke Neo4j: "
            f"{', '.join(offenders)}. Ground truth hanya boleh berada di "
            "test_case_candidates.csv di mesin lokal, tidak pernah di API "
            "(responden tidak boleh melihat jawaban)."
        )
    return props


# --- Sintesis field kosmetik wajib skema v1 ---------------------------------
#
# Nilai di bawah ini TIDAK punya makna analitis. Ia hanya memenuhi field
# `required` model Pydantic v1 supaya payload lolos validasi. Bentuknya dipilih
# agar mustahil dibaca sebagai identitas nyata:
#   - domain memakai TLD `.example` yang dicadangkan RFC 2606
#   - nomor telepon dan rekening memakai awalan `SIM-` yang bukan format nyata
#     dan tidak dapat dihubungi/ditransfer
# Jangan pernah menggantinya dengan nilai yang tampak realistis.


def _sequence(node_id: str) -> str:
    """`domain_00042` -> `00042`."""
    return node_id.rsplit("_", 1)[-1]


def _risk_exposure(rule_level: str) -> str:
    """`riskExposureLevel` victim (enum v1 low/medium/high) dari rule_level.

    Diturunkan dari `weak_labels.csv` — keluaran rule engine orang A, bukan
    ground truth. Sah tampil di API: `rule_score` memang sudah kami sajikan
    sebagai `riskScore`.
    """
    return {"low": "low", "medium": "medium", "high": "high", "critical": "high"}.get(
        rule_level, "low"
    )


def cosmetic_fields(node_type: str, node_id: str, row: dict[str, Any]) -> dict[str, Any]:
    """Field `required` khas tipe yang diminta model v1 tapi tidak ada di kontrak v2."""
    seq = _sequence(node_id)
    if node_type == "domain":
        return {"domainName": f"{node_id}.example", "category": "synthetic_unclassified"}
    if node_type == "phone":
        return {
            "normalizedNumber": f"SIM-PHONE-{seq}",
            "countryCode": "+62",
            "reportCount": int(row.get("feat_report_count") or 0),
        }
    if node_type == "bank_account":
        return {
            "bankName": "SIM_BANK",
            "accountAlias": node_id,
            "maskedAccountNumber": f"****{seq}",
        }
    if node_type == "ewallet":
        is_qris = int(row.get("feat_is_qris") or 0) == 1
        return {
            "provider": "SIM_QRIS" if is_qris else "SIM_EWALLET",
            "walletAlias": node_id,
            "maskedWalletId": f"****{seq}",
        }
    if node_type == "apk":
        return {
            "appName": node_id,
            "packageName": f"sim.satpam.{node_id}",
            "requestedPermissions": [],
        }
    if node_type == "social_account":
        return {
            "platform": "SIM_SOCIAL",
            "username": node_id,
            "profileUrl": f"https://social.example/{node_id}",
        }
    if node_type == "report":
        return {
            "description": "Laporan sintetik (simulasi) — tanpa isi teks nyata.",
            # `categoryHint` adalah enum WAJIB skema v1 (judol / pinjol_illegal /
            # cross_ecosystem / payment_flow / traffic_crawler / benign) yang tidak
            # punya padanan di kontrak v2. Satu-satunya sumber informasinya adalah
            # `gt_ecosystem`, dan memakai itu berarti membocorkan ground truth.
            # Karena itu nilainya dibuat KONSTAN untuk seluruh node report: sebuah
            # konstanta tidak membawa informasi pembeda apa pun, sehingga tidak
            # dapat membimbing responden studi. JANGAN diturunkan dari gt_*.
            "categoryHint": "benign",
            "status": "new",
        }
    if node_type == "victim":
        return {
            "alias": node_id,
            "riskExposureLevel": _risk_exposure(str(row.get("rule_level") or "low")),
        }
    raise ValueError(f"node_type di luar kontrak data v2: {node_type!r}")
