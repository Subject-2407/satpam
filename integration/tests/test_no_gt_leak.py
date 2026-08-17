"""
Tes penjaga Bagian C.

Fokus utamanya satu hal: **ground truth tidak boleh keluar lewat API.**
`GET /api/entities/{node_type}/{node_id}` mengembalikan node Neo4j apa adanya
tanpa menyaring properti, jadi `gt_illicit` yang ikut terimpor akan terbaca
siapa pun yang memanggil endpoint itu — termasuk responden studi, yang
membatalkan validitas studi tersebut. Kebocoran seperti ini tidak terlihat dari
luar setelah data masuk, karena itu dijaga tes, bukan sekadar konvensi.

Tes lain memastikan prinsip aditif benar-benar terjaga: field lama
(`riskScore`, `riskLevel`, `triggeredRules`) tetap ada dan tidak tertimpa oleh
field baru (`mlScore`, `mlConfidence`).

Jalankan:

    python -m pytest integration/tests -q

`pytest.ini` akar memakai `testpaths = tests`, jadi suite ini sengaja tidak ikut
terpanggil oleh `python -m pytest` biasa dan tidak mengganggu 60 tes orang B.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "integration"))
sys.path.insert(0, str(REPO_ROOT / "integration" / "backend"))

from app.services.ml_layer import (  # noqa: E402
    _default_subgraph_path,
    ml_block,
    strip_forbidden,
)
from import_synthetic import build_batches, read_seed  # noqa: E402
from ml_scores import (  # noqa: E402
    PREDICTIONS_PATH,
    build_ml_properties,
    normalized_confidence,
)
from schema_map import (  # noqa: E402
    NODE_TYPE_TO_V1,
    REL_TYPE_TO_V1,
    GroundTruthLeakError,
    sanitize_properties,
)

SEED = 42
DATA_DIR = REPO_ROOT / "data" / "synthetic" / f"seed_{SEED}"

requires_data = pytest.mark.skipif(
    not (DATA_DIR / "nodes.csv").exists(),
    reason=f"{DATA_DIR} tidak ada — jalankan generator orang A",
)
requires_predictions = pytest.mark.skipif(
    not PREDICTIONS_PATH.exists(),
    reason="predictions.csv belum dibangkitkan (lihat integration/README.md)",
)


# --- Penjaga kebocoran ground truth -----------------------------------------


@pytest.mark.parametrize(
    "key", ["gt_illicit", "gt_operator_id", "gt_ecosystem", "groundTruth", "gtIllicit"]
)
def test_sanitize_menolak_properti_ground_truth(key: str) -> None:
    with pytest.raises(GroundTruthLeakError):
        sanitize_properties({"id": "domain_00001", key: 1})


def test_sanitize_melewatkan_properti_bersih() -> None:
    props = {"id": "domain_00001", "riskScore": 55, "mlScore": 0.9, "feat_kw_score": 0.3}
    assert sanitize_properties(props) == props


@requires_data
@requires_predictions
def test_payload_impor_tidak_memuat_gt_apa_pun() -> None:
    """Tes paling penting di berkas ini: periksa payload sungguhan seed 42."""
    frames = read_seed(SEED)
    ml_properties = build_ml_properties(SEED)

    node_count = 0
    rel_count = 0
    for batch in build_batches(frames, SEED, ml_properties):
        for items in batch["nodes"].values():
            for payload in items:
                node_count += 1
                offenders = [key for key in payload if key.startswith("gt_")]
                assert not offenders, f"{payload['id']} membawa {offenders}"
        for rel in batch["relationships"]:
            rel_count += 1
            assert not [key for key in rel if key.startswith("gt_")]

    assert node_count == 5000
    assert rel_count == 18447


def test_strip_forbidden_membuang_gt_bila_entah_bagaimana_ada() -> None:
    """Pertahanan lapis kedua di sisi response, bukan hanya di sisi impor."""
    node = {"id": "domain_00001", "riskScore": 55, "gt_illicit": 1, "gtIllicit": 1}
    cleaned = strip_forbidden(node)
    assert cleaned == {"id": "domain_00001", "riskScore": 55}


# --- Kontrak data -------------------------------------------------------------


def test_kedelapan_tipe_node_dan_relasi_terpetakan() -> None:
    assert set(NODE_TYPE_TO_V1) == {
        "domain",
        "phone",
        "bank_account",
        "ewallet",
        "apk",
        "social_account",
        "report",
        "victim",
    }
    assert set(REL_TYPE_TO_V1) == {
        "promotes",
        "contacts",
        "uses_account",
        "transferred_to",
        "mentions",
        "reported",
        "linked_to_apk",
        "redirects_to",
    }


# --- Prinsip aditif -------------------------------------------------------------


@requires_data
@requires_predictions
def test_field_lama_tetap_ada_dan_tidak_tertimpa() -> None:
    frames = read_seed(SEED)
    ml_properties = build_ml_properties(SEED)
    batch = next(build_batches(frames, SEED, ml_properties))
    payloads = [item for items in batch["nodes"].values() for item in items]

    for payload in payloads:
        # Field lama rule engine v2 orang A
        assert isinstance(payload["riskScore"], int)
        assert 0 <= payload["riskScore"] <= 100
        assert payload["riskLevel"] in {"low", "medium", "high", "critical"}
        assert isinstance(payload["triggeredRules"], list)
        # Field baru berdiri di sampingnya
        assert 0.0 <= payload["mlScore"] <= 1.0
        assert 0.0 <= payload["mlConfidence"] <= 1.0

    # riskScore (int 0-100) dan mlScore (float 0-1) memang tidak dapat saling
    # menggantikan — justru itu yang membuat keduanya bisa hidup berdampingan.
    assert any(p["riskScore"] > 1 for p in payloads)


@requires_data
@requires_predictions
def test_mlscore_sama_dengan_prob_rgcn_di_predictions_csv() -> None:
    """Skor yang diimpor harus skor asli orang B, bukan hasil transformasi."""
    import pandas as pd

    predictions = pd.read_csv(PREDICTIONS_PATH)
    rgcn = predictions[(predictions["seed"] == SEED) & (predictions["model"] == "rgcn")]
    expected = dict(zip(rgcn["node_id"], rgcn["prob"]))

    ml_properties = build_ml_properties(SEED)
    assert len(ml_properties) == len(expected)
    for node_id, props in ml_properties.items():
        assert props["mlScore"] == pytest.approx(expected[node_id], abs=1e-6)
        assert props["mlModel"] == "rgcn"
        assert props["mlSeed"] == SEED


# --- mlConfidence ---------------------------------------------------------------


@pytest.mark.parametrize(
    "prob,expected",
    [(0.5, 0.0), (0.0, 1.0), (1.0, 1.0)],
)
def test_confidence_di_titik_batas(prob: float, expected: float) -> None:
    assert normalized_confidence(prob) == pytest.approx(expected, abs=1e-6)


def test_confidence_simetris_dan_monoton() -> None:
    assert normalized_confidence(0.2) == pytest.approx(normalized_confidence(0.8))
    assert normalized_confidence(0.9) > normalized_confidence(0.7) > normalized_confidence(0.6)


def test_confidence_mengikuti_entropi_biner() -> None:
    prob = 0.3
    entropy = -(prob * math.log(prob) + 0.7 * math.log(0.7))
    assert normalized_confidence(prob) == pytest.approx(1 - entropy / math.log(2), abs=1e-6)


# --- criticalSubgraph -----------------------------------------------------------


def test_critical_subgraph_masih_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sampai orang B menghasilkan berkasnya, nilainya None dan ditandai jelas."""
    monkeypatch.setenv("SATPAM_CRITICAL_SUBGRAPH_PATH", str(REPO_ROOT / "tidak-ada.json"))
    block = ml_block({"mlScore": 0.91, "mlConfidence": 0.72}, "domain_00042")
    assert block["criticalSubgraph"] is None
    assert block["criticalSubgraphStatus"] == "not_available"
    assert "GNNExplainer" in block["criticalSubgraphNote"]


def test_critical_subgraph_langsung_terpakai_begitu_berkasnya_ada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Membuktikan seam-nya benar-benar tersambung, bukan cuma niat di komentar."""
    subgraph = {
        "nodes": ["domain_00042", "phone_00013"],
        "edges": [
            {
                "src": "domain_00042",
                "dst": "phone_00013",
                "relType": "contacts",
                "importance": 0.83,
            }
        ],
    }
    path = tmp_path / "critical_subgraphs.json"
    path.write_text(
        json.dumps({"seed": 42, "model": "rgcn", "subgraphs": {"domain_00042": subgraph}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("SATPAM_CRITICAL_SUBGRAPH_PATH", str(path))

    block = ml_block({"mlScore": 0.91, "mlConfidence": 0.72}, "domain_00042")
    assert block["criticalSubgraphStatus"] == "available"
    assert block["criticalSubgraph"]["edges"][0]["relType"] == "contacts"


def test_default_subgraph_path_tidak_pernah_melempar() -> None:
    """Regresi: versi pertama memakai `parents[4]` sebagai konstanta modul.

    Di dalam container hanya `integration/backend` yang di-mount ke `/app`,
    sehingga `parents[4]` tidak ada dan `IndexError` terjadi **saat import** —
    seluruh backend gagal start, bukan cuma fitur ini yang mati. Path bawaan
    harus dihitung lewat fungsi dan boleh mengembalikan `None`.
    """
    result = _default_subgraph_path()
    assert result is None or isinstance(result, Path)


def test_ml_block_bentuknya_tetap_walau_node_tanpa_skor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Frontend harus bisa mengandalkan ketiga kunci selalu ada.

    Env var diarahkan ke berkas tak ada supaya tes ini menguji **bentuk
    response**, bukan kebetulan ada atau tidaknya keluaran orang B. Versi
    pertama tes ini tidak mengisolasi diri dan mulai gagal begitu orang B
    benar-benar menghasilkan `critical_subgraphs.json` yang memuat
    `domain_00001` — gagal karena seam-nya bekerja, bukan karena ada yang rusak.
    """
    monkeypatch.setenv("SATPAM_CRITICAL_SUBGRAPH_PATH", str(REPO_ROOT / "tidak-ada.json"))
    block = ml_block({}, "domain_00001")
    assert block["mlScore"] is None
    assert block["mlConfidence"] is None
    assert block["criticalSubgraph"] is None


@requires_data
def test_seam_menyajikan_keluaran_orang_b_yang_sungguhan() -> None:
    """Kebalikan tes di atas: bila berkasnya ada, subgraph benar-benar tersaji.

    Dijaga supaya tidak ada yang "memperbaiki" tes sebelumnya dengan cara
    mematikan seam-nya.
    """
    from app.services.ml_layer import load_critical_subgraphs

    subgraphs = load_critical_subgraphs()
    if not subgraphs:
        pytest.skip("critical_subgraphs.json belum dibangkitkan orang B")

    assert "domain_00001" in subgraphs
    block = ml_block({"mlScore": 0.9999, "mlConfidence": 0.99}, "domain_00001")
    assert block["criticalSubgraphStatus"] == "available"
    assert block["criticalSubgraph"]["edges"], "subgraph tanpa edge"
    # Nama relasi wajib memakai kontrak v2 huruf kecil, bukan label Neo4j.
    rel_types = {edge["relType"] for edge in block["criticalSubgraph"]["edges"]}
    assert rel_types <= set(REL_TYPE_TO_V1), f"relType di luar kontrak v2: {rel_types}"


def test_ml_block_menyertakan_skor_baseline_dan_uncertainty() -> None:
    block = ml_block(
        {"mlScore": 0.9, "mlConfidence": 0.6, "mlScoreGcnHomogeneous": 0.8},
        "domain_00001",
    )
    assert block["mlBaselineScores"] == {"mlScoreGcnHomogeneous": 0.8}
    assert block["mlUncertainty"] == pytest.approx(0.4)
