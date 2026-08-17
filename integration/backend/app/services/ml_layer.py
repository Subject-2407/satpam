"""
Lapisan ML aditif untuk response API.

> **Prinsip integrasi: aditif, bukan destruktif.** Field lama (`riskScore`,
> `explanation`, `triggeredRules`) tidak ditimpa. Field baru (`mlScore`,
> `mlConfidence`, `criticalSubgraph`) ditambahkan terpisah.

Modul ini adalah **satu-satunya** tempat field ML disisipkan ke response.
Alasannya: bila penyisipan tersebar di beberapa router, sangat mudah salah satu
di antaranya menimpa `riskScore` atau `triggeredRules` tanpa ada yang sadar.

## Dari mana angkanya

`mlScore` dan `mlConfidence` sudah menjadi **properti node di Neo4j**, ditulis
oleh `integration/import_synthetic.py` dari `experiments/results/predictions.csv`
(skor R-GCN sungguhan milik orang B, bukan dummy). Modul ini hanya membacanya
kembali dan menyusunnya menjadi blok yang rapi — backend tidak perlu bergantung
pada `experiments/` saat runtime.

`mlConfidence` diturunkan dari entropi prediksi; skor prioritas antrean
review adalah `1 - mlConfidence`.

## `criticalSubgraph` — masih placeholder

GNNExplainer adalah domain orang B: ia yang punya `data.hetero`,
bobot model terlatih, dan `torch_geometric.explain`. Bagian C **tidak** menulis
ulang logikanya. Untuk sekarang nilainya selalu `None`, dan `load_critical_subgraphs()`
di bawah adalah titik sambungnya — lihat TODO di sana.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

# Properti ML yang ditulis import_synthetic.py ke Neo4j.
ML_PROPERTY_KEYS: tuple[str, ...] = (
    "mlScore",
    "mlConfidence",
    "mlModel",
    "mlSeed",
    "mlScoreMlp",
    "mlScoreXgbGraph",
    "mlScoreGcnHomogeneous",
)

# Properti yang tidak boleh keluar lewat API dalam keadaan apa pun.
#
# Saat ini `import_synthetic.py` sudah menolak mengirimnya, jadi baris ini adalah
# pertahanan lapis kedua: bila suatu saat ada yang mengimpor ground truth lewat
# jalur lain (Neo4j Browser, skrip ad-hoc, dump lama), response API tetap bersih.
# Ground truth yang terlihat responden akan membatalkan studi responden.
FORBIDDEN_RESPONSE_KEYS: tuple[str, ...] = ("gt_", "groundTruth", "gtIllicit")

# Berkas keluaran GNNExplainer orang B, bila sudah ada.
_SUBGRAPH_ENV = "SATPAM_CRITICAL_SUBGRAPH_PATH"


def _default_subgraph_path() -> Path | None:
    """Lokasi bawaan `critical_subgraphs.json`, atau `None` bila tak terjangkau.

    Path ini hanya bermakna saat backend dijalankan langsung dari dalam repo
    (`uvicorn app.main:app` dari `integration/backend/`). Di dalam container,
    `docker-compose.yml` me-mount **hanya** `integration/backend` ke `/app`,
    sehingga `experiments/results/` tidak ada sama sekali di sana dan jumlah
    parent-nya lebih pendek. Untuk Docker, mount direktori itu dan arahkan lewat
    `SATPAM_CRITICAL_SUBGRAPH_PATH`.

    Dihitung lewat fungsi, bukan konstanta modul, dan mengembalikan `None`
    alih-alih melempar `IndexError`. Versi pertama modul ini memakai
    `parents[4]` sebagai konstanta tingkat modul dan itu membuat **seluruh
    backend gagal start di dalam container** — bukan sekadar fitur ini yang mati,
    tapi `import app.main` yang runtuh. Jangan kembalikan ke bentuk konstanta.
    """
    here = Path(__file__).resolve()
    if len(here.parents) <= 4:
        return None
    return here.parents[4] / "experiments" / "results" / "critical_subgraphs.json"


def strip_forbidden(node: dict[str, Any]) -> dict[str, Any]:
    """Buang properti ground truth bila entah bagaimana ada di node."""
    return {
        key: value
        for key, value in node.items()
        if not (key.startswith(FORBIDDEN_RESPONSE_KEYS[0]) or key in FORBIDDEN_RESPONSE_KEYS[1:])
    }


def load_critical_subgraphs(path: Path | None = None) -> dict[str, Any]:
    """Muat `criticalSubgraph` per node hasil GNNExplainer, bila berkasnya ada.

    TODO(orang B): berkas ini belum dihasilkan. Yang dibutuhkan
    Bagian C adalah satu JSON berisi objek dengan bentuk:

        {
          "seed": 42,
          "model": "rgcn",
          "subgraphs": {
            "domain_00042": {
              "nodes": ["domain_00042", "phone_00013", "bank_account_00007"],
              "edges": [
                {"src": "domain_00042", "dst": "phone_00013",
                 "relType": "contacts", "importance": 0.83}
              ]
            }
          }
        }

    `relType` memakai nama relasi kontrak v2 (huruf kecil), bukan label
    Neo4j — pemetaannya sudah ada di `integration/schema_map.py`. `importance`
    adalah bobot edge mask GNNExplainer, 0–1.

    Simpan ke `experiments/results/critical_subgraphs.json`, atau arahkan lewat
    variabel lingkungan `SATPAM_CRITICAL_SUBGRAPH_PATH`. Begitu berkas itu ada,
    tidak ada kode lain yang perlu diubah: `ml_block()` langsung menyajikannya.

    Catatan: `data.hetero` sengaja dibangun tanpa reverse edge dan memang
    diperuntukkan untuk GNNExplainer serta dashboard,
    jadi subgraph-nya akan cocok dengan arah relasi di Neo4j.
    """
    if path is not None:
        source: Path | None = path
    else:
        from_env = os.environ.get(_SUBGRAPH_ENV)
        source = Path(from_env) if from_env else _default_subgraph_path()
    if source is None or not source.exists():
        return {}
    # Dibaca sekali per (path, mtime): begitu orang B menaruh berkasnya, backend
    # memuatnya tanpa restart, tapi tidak mem-parse JSON di setiap request.
    return _read_subgraphs(str(source), source.stat().st_mtime_ns)


@lru_cache(maxsize=4)
def _read_subgraphs(path_str: str, _mtime_ns: int) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path_str).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    subgraphs = payload.get("subgraphs")
    return subgraphs if isinstance(subgraphs, dict) else {}


def ml_block(node: dict[str, Any] | None, node_id: str) -> dict[str, Any]:
    """Blok field ML untuk satu node.

    Selalu mengembalikan ketiga kunci walau nilainya `None`, supaya
    frontend dapat mengandalkan bentuk response yang tetap.
    """
    properties = node or {}
    block: dict[str, Any] = {
        "mlScore": properties.get("mlScore"),
        "mlConfidence": properties.get("mlConfidence"),
        # Placeholder — lihat load_critical_subgraphs().
        "criticalSubgraph": load_critical_subgraphs().get(node_id),
    }
    if block["criticalSubgraph"] is None:
        block["criticalSubgraphStatus"] = "not_available"
        block["criticalSubgraphNote"] = (
            "GNNExplainer belum menghasilkan berkasnya. Bagian C tidak "
            "menulis ulang logika penjelasan model; ini menunggu keluaran orang B."
        )
    else:
        block["criticalSubgraphStatus"] = "available"

    alternatives = {
        key: properties[key]
        for key in ("mlScoreMlp", "mlScoreXgbGraph", "mlScoreGcnHomogeneous")
        if properties.get(key) is not None
    }
    if alternatives:
        block["mlBaselineScores"] = alternatives
    if properties.get("mlModel"):
        block["mlModel"] = properties["mlModel"]
    if properties.get("mlSeed") is not None:
        block["mlSeed"] = properties["mlSeed"]
    if block["mlConfidence"] is not None:
        # Skor prioritas antrean review = entropi prediksi.
        block["mlUncertainty"] = round(1.0 - float(block["mlConfidence"]), 6)
    return block
