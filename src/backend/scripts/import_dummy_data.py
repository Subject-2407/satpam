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
