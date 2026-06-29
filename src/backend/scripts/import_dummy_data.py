#!/usr/bin/env python3
"""
Import dataset dummy SATPAM ke backend yang sedang berjalan (via HTTP API admin).

Skrip ini login sebagai admin, lalu POST dataset ke `/api/import/dummy-data`
(MERGE — aman diulang tanpa duplikat). Dengan flag --rebuild, skrip juga memanggil
`/api/analysis/rebuild` agar skor risiko langsung dihitung dan tersimpan ke node
(tanpa ini semua entitas masih riskScore 0 / low).

Hanya memakai stdlib (urllib) — tidak butuh dependency tambahan.

Contoh:
    python src/backend/scripts/import_dummy_data.py --rebuild
    python src/backend/scripts/import_dummy_data.py --base-url http://localhost:8000
    python src/backend/scripts/import_dummy_data.py --dataset path/ke/dataset.json --reset
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Default dataset relatif terhadap root repo (../../engine/data dari folder skrip ini)
DEFAULT_DATASET = Path(__file__).resolve().parents[2] / "engine" / "data" / "dummy_dataset_week1.json"


def build_high_risk_payload() -> dict:
    """
    Klaster dummy "Mega Jackpot" — entitas baru yang sengaja dirancang memicu banyak
    rule scoring sekaligus, sehingga setelah `--rebuild` muncul sebagai high/critical.

    Skor TIDAK ditulis manual: angka tinggi dihitung oleh engine dari struktur graf
    (terhubung blacklist critical, APK izin sensitif, nomor di banyak laporan, rekening
    fan-in + transfer cepat, lonjakan traffic, lintas judol-pinjol). Tetap explainable.
    """
    ts = "2026-06-12T09:00:00+07:00"  # createdAt dasar

    def node(**kw):
        kw.setdefault("source", "dummy_high_risk_demo")
        kw.setdefault("createdAt", ts)
        kw.setdefault("riskScore", 0)
        kw.setdefault("riskLevel", "low")
        kw.setdefault("verificationStatus", "unreviewed")
        return kw

    def rel(rid, rtype, ftype, fid, ttype, tid, first=None):
        edge = {
            "id": rid, "type": rtype,
            "from": {"type": ftype, "id": fid},
            "to": {"type": ttype, "id": tid},
            "source": "dummy_high_risk_demo", "confidence": "high",
            "weight": 1, "createdAt": ts,
        }
        if first:
            edge["firstSeenAt"] = first
        return edge

    nodes = {
        "reports": [node(
            id="report-mega-001", type="Report", label="Laporan Klaster Mega Jackpot",
            description="Pelapor dummy melihat promo slot gacor bonus maxwin di mega-jackpot.test, "
                        "diarahkan ke APK pinjaman cepat MegaPinjam dan diminta transfer ke rekening kolektor simulasi.",
            categoryHint="cross_ecosystem",
        )],
        "victims": [
            node(id="victim-mega-1", type="Victim", label="Pelapor Demo M1", alias="Pelapor Demo M1", riskExposureLevel="high"),
            node(id="victim-mega-2", type="Victim", label="Pelapor Demo M2", alias="Pelapor Demo M2", riskExposureLevel="high"),
        ],
        "domains": [node(
            id="domain-mega-jackpot-test", type="Domain", label="Mega Jackpot Slot Gacor Maxwin",
            domainName="mega-jackpot.test", category="judol", categoryHint="judol",
            description="Domain dummy promo slot gacor bonus maxwin lintas judol dan pinjol.",
        )],
        "phoneNumbers": [node(
            id="phone-wa-mega", type="PhoneNumber", label="+62-812-0000-9999",
            normalizedNumber="+6281200009999", countryCode="+62", reportCount=5,
        )],
        "bankAccounts": [node(
            id="bank-mega-collector", type="BankAccount", label="Bank Dummy 9999****0001",
            bankName="Bank Dummy", accountAlias="Rekening Kolektor Mega", maskedAccountNumber="9999****0001",
        )],
        "eWallets": [node(
            id="ewallet-mega", type="EWallet", label="E-Wallet Dummy 0899****0009",
            provider="DompetDummy", walletAlias="Wallet Mega", maskedWalletId="0899****0009",
        )],
        "apks": [node(
            id="apk-mega-pinjam", type="APK", label="MegaPinjam Cepat",
            appName="MegaPinjam Cepat", packageName="id.demo.megapinjam",
            requestedPermissions=["READ_SMS", "READ_CONTACTS", "ACCESS_FINE_LOCATION"],
        )],
        "keywords": [node(
            id="keyword-mega-gacor", type="Keyword", label="slot gacor maxwin",
            keyword="slot gacor maxwin", category="judol_promo", weight=30,
        )],
        "trafficEvents": [node(
            id="traffic-mega-001", type="TrafficEvent", label="Traffic mega-jackpot.test",
            eventType="TRAFFIC_SPIKE", timestamp=ts, sourceAlias="lab-client-m",
            destinationDomain="mega-jackpot.test", requestCount=150, simulationOnly=True,
        )],
        "blacklistEntities": [node(
            id="blacklist-mega-001", type="BlacklistEntity", label="Blacklist dummy Mega Jackpot",
            entityType="Domain", entityId="domain-mega-jackpot-test", severity="critical",
            reason="Domain dummy terhubung ke APK pinjol dan rekening kolektor dalam skenario demo high-risk.",
        )],
    }

    relationships = [
        rel("rel-mega-01", "REPORTED", "Victim", "victim-mega-1", "Report", "report-mega-001"),
        rel("rel-mega-02", "MENTIONS", "Report", "report-mega-001", "Domain", "domain-mega-jackpot-test"),
        rel("rel-mega-03", "MENTIONS", "Report", "report-mega-001", "PhoneNumber", "phone-wa-mega"),
        rel("rel-mega-04", "BLACKLISTED_AS", "Domain", "domain-mega-jackpot-test", "BlacklistEntity", "blacklist-mega-001"),
        rel("rel-mega-05", "LINKED_TO_APK", "Domain", "domain-mega-jackpot-test", "APK", "apk-mega-pinjam"),
        rel("rel-mega-06", "CONTAINS_KEYWORD", "Domain", "domain-mega-jackpot-test", "Keyword", "keyword-mega-gacor"),
        rel("rel-mega-07", "OBSERVED_TRAFFIC_TO", "TrafficEvent", "traffic-mega-001", "Domain", "domain-mega-jackpot-test"),
        rel("rel-mega-08", "CONTACTS", "Domain", "domain-mega-jackpot-test", "PhoneNumber", "phone-wa-mega"),
        rel("rel-mega-09", "USES_ACCOUNT", "PhoneNumber", "phone-wa-mega", "BankAccount", "bank-mega-collector"),
        rel("rel-mega-10", "TRANSFERRED_TO", "Victim", "victim-mega-1", "BankAccount", "bank-mega-collector", first="2026-06-12T09:00:00+07:00"),
        rel("rel-mega-11", "TRANSFERRED_TO", "Victim", "victim-mega-2", "BankAccount", "bank-mega-collector", first="2026-06-12T09:01:00+07:00"),
        rel("rel-mega-12", "TRANSFERRED_TO", "BankAccount", "bank-mega-collector", "EWallet", "ewallet-mega", first="2026-06-12T09:05:00+07:00"),
    ]

    return {
        "metadata": {
            "datasetId": "satpam-high-risk-demo-v1",
            "version": "0.1.0",
            "scope": "demo_high_risk_cluster",
            "createdAt": ts,
            "simulationOnly": True,
            "dataPolicy": ["dummy_data_only", "safe_test_domains_only", "masked_payment_identifiers",
                           "simulation_traffic_and_crawler_only", "human_verification_required"],
        },
        "nodes": nodes,
        "relationships": relationships,
    }


def _request(method: str, url: str, *, token: str | None = None, data: bytes | None = None,
             content_type: str | None = None) -> dict:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"[ERROR] {method} {url} -> HTTP {exc.code}\n{detail[:2000]}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"[ERROR] Tidak bisa menghubungi {url}: {exc.reason}\n"
                         f"Pastikan backend berjalan (uvicorn ... --port 8000).")


def login(base_url: str, username: str, password: str) -> str:
    form = urllib.parse.urlencode({"username": username, "password": password}).encode()
    res = _request("POST", f"{base_url}/api/auth/token", data=form,
                   content_type="application/x-www-form-urlencoded")
    token = res.get("access_token")
    if not token:
        raise SystemExit(f"[ERROR] Login gagal, respons tidak berisi access_token: {res}")
    return token


def main() -> int:
    parser = argparse.ArgumentParser(description="Import dataset dummy SATPAM via API admin.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="URL backend (default: %(default)s)")
    parser.add_argument("--username", default="admin@satpam.test", help="Email admin (default: %(default)s)")
    parser.add_argument("--password", default="admin123", help="Password admin (default: %(default)s)")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET,
                        help="Path file dataset JSON (default: src/engine/data/dummy_dataset_week1.json)")
    parser.add_argument("--reset", action="store_true",
                        help="Hapus seluruh dataset lebih dulu (DELETE /api/admin/reset-dataset)")
    parser.add_argument("--skip-extra-high-risk", action="store_true",
                        help="Jangan tambahkan klaster dummy high-risk 'Mega Jackpot' (default: ditambahkan)")
    parser.add_argument("--rebuild", action="store_true",
                        help="Jalankan /api/analysis/rebuild setelah import (hitung & simpan skor risiko)")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    if not args.dataset.is_file():
        raise SystemExit(f"[ERROR] Dataset tidak ditemukan: {args.dataset}")

    print(f"[1/4] Login admin di {base_url} ...")
    token = login(base_url, args.username, args.password)
    print("      OK")

    if args.reset:
        print("[2/4] Reset dataset (DELETE /api/admin/reset-dataset) ...")
        _request("DELETE", f"{base_url}/api/admin/reset-dataset", token=token)
        print("      OK")
    else:
        print("[2/4] Reset dilewati (pakai --reset untuk mulai bersih)")

    print(f"[3/4] Import dataset: {args.dataset.name} ...")
    payload = args.dataset.read_text(encoding="utf-8").encode("utf-8")
    res = _request("POST", f"{base_url}/api/import/dummy-data", token=token,
                   data=payload, content_type="application/json")
    print(f"      status={res.get('status')} | {res.get('message')}")
    errors = (res.get("stats") or {}).get("errors") or []
    for err in errors[:10]:
        print(f"      ! {err}")

    if not args.skip_extra_high_risk:
        print("      + klaster high-risk 'Mega Jackpot' ...")
        extra = json.dumps(build_high_risk_payload()).encode("utf-8")
        eres = _request("POST", f"{base_url}/api/import/dummy-data", token=token,
                        data=extra, content_type="application/json")
        print(f"        {eres.get('message')}")
        for err in ((eres.get("stats") or {}).get("errors") or [])[:10]:
            print(f"        ! {err}")

    if args.rebuild:
        print("[4/4] Rebuild analisis (POST /api/analysis/rebuild) ...")
        rb = _request("POST", f"{base_url}/api/analysis/rebuild", token=token, data=b"")
        print(f"      assessments={rb.get('assessments')} "
              f"artifactNodes={rb.get('artifactNodesMerged')} "
              f"earlyWarnings={len(rb.get('earlyWarnings') or [])}")
    else:
        print("[4/4] Rebuild dilewati — jalankan ulang dengan --rebuild agar skor risiko terisi "
              "(tanpa ini semua entitas tetap low).")

    print("\nSelesai. Buka frontend (http://localhost:5173) untuk melihat hasil.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
