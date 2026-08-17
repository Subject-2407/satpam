"""Lembar bandingan pasca-ronde: tiga jawaban berdampingan per node.

Dipakai pada langkah 3 ronde kalibrasi, saat ketiga anotator duduk bersama
membahas selisih. Tanpa alat ini perbandingan dikerjakan dengan membuka tiga
berkas CSV berdampingan, dan diskusinya habis untuk mencari baris.

**Umpan baliknya sesama manusia, bukan kunci jawaban.** Berkas ini tidak pernah
membaca kolom `gt_*` maupun skor rule, dan `assert_no_leak` menjaganya sama
seperti pada `webform.py`. Nama lengkap kolom jawaban sengaja tidak ditulis di
mana pun dalam paket ini, dan `test_annotation_never_names_ground_truth_columns`
menjaga aturan itu. Latihan dengan umpan balik benar/salah tidak
disediakan dengan sengaja: anotasi masuk jalur pelatihan model, sehingga
anotator yang disetel terhadap ground truth akan membuat labelnya menjadi
salinan berderau dari jawaban, dan itu membatalkan perbandingan model.

Node diurutkan dari yang paling banyak diperselisihkan, karena di situlah
kriteria yang belum disepakati akan ketahuan.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from annotation.webform import assert_no_leak, build_payload
from annotation.worksheet import Percentiles
from rules.graph import RuleGraph


def read_answers(directory: Path, annotators: tuple[str, ...]) -> dict[str, dict]:
    """Baca `answers_{ID}.csv` tiap anotator menjadi peta node_id -> jawaban."""
    hasil: dict[str, dict] = {}
    for annotator_id in annotators:
        path = directory / f"answers_{annotator_id}.csv"
        if not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                label = (row.get("label") or "").strip()
                if not label:
                    continue
                hasil.setdefault(row["node_id"], {})[annotator_id] = {
                    "label": label,
                    "confidence": (row.get("confidence") or "").strip(),
                    "note": (row.get("note") or "").strip(),
                }
    return hasil


def summarize(answers: dict[str, dict], annotators: tuple[str, ...]) -> dict:
    """Ringkasan kasar untuk kepala halaman. Bukan pengganti `agreement.py`."""
    bulat = beda = 0
    porsi: dict[str, list[int]] = {a: [] for a in annotators}
    for per_node in answers.values():
        labels = [v["label"] for v in per_node.values()]
        if len(set(labels)) <= 1:
            bulat += 1
        else:
            beda += 1
        for annotator_id, v in per_node.items():
            if v["label"] in ("0", "1"):
                porsi[annotator_id].append(int(v["label"]))
    return {
        "dinilai": len(answers),
        "bulat": bulat,
        "beda": beda,
        "porsi_ya": {
            a: (sum(v) / len(v) if v else None) for a, v in porsi.items()
        },
    }


def build_debrief(
    graph: RuleGraph,
    node_ids: list[str],
    answers: dict[str, dict],
    annotators: tuple[str, ...],
) -> tuple[list[dict], dict]:
    """Susun payload lembar bandingan, node berselisih lebih dulu."""
    percentiles = Percentiles.build(list(graph.nodes.values()))
    payload = build_payload(graph, node_ids, percentiles)
    assert_no_leak(payload)

    def selisih(node_id: str) -> int:
        return len({v["label"] for v in answers.get(node_id, {}).values()})

    for rekam in payload:
        rekam["jawaban"] = [
            {"anotator": a, **answers.get(rekam["id"], {}).get(a, {})}
            for a in annotators
        ]
        rekam["berselisih"] = selisih(rekam["id"]) > 1
    payload.sort(key=lambda r: (not r["berselisih"], r["id"]))
    return payload, summarize(answers, annotators)


def write_debrief(
    directory: Path,
    graph: RuleGraph,
    node_ids: list[str],
    annotators: tuple[str, ...],
) -> Path:
    answers = read_answers(directory, annotators)
    if not answers:
        raise FileNotFoundError(
            f"tidak ada jawaban terisi di {directory}. "
            f"Jalankan ronde kalibrasi lebih dulu."
        )
    payload, ringkas = build_debrief(graph, node_ids, answers, annotators)
    path = directory / "debrief.html"
    path.write_text(
        _TEMPLATE.format(
            data=json.dumps(payload, ensure_ascii=False),
            ringkas=json.dumps(ringkas, ensure_ascii=False),
        ),
        encoding="utf-8",
    )
    return path


_TEMPLATE = """<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lembar bandingan anotasi</title>
<style>
  :root {{
    --bg:#fff; --fg:#1b1b1b; --muted:#6b6b6b; --line:#dcdcdc; --card:#fafafa;
    --accent:#1f4e79; --warn:#8a5a00; --ok:#1d6b3f;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#16181c; --fg:#e8e8e8; --muted:#9a9a9a; --line:#33363c;
      --card:#1e2126; --accent:#7fb0e0; --warn:#d9a441; --ok:#6fcf97;
    }}
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--fg);
    font:15px/1.5 system-ui,"Segoe UI",sans-serif}}
  header{{position:sticky;top:0;background:var(--bg);
    border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}}
  main{{max-width:980px;margin:0 auto;padding:16px}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:8px;
    padding:16px;margin-bottom:16px}}
  .card.beda{{border-left:4px solid var(--warn)}}
  h2{{margin:0 0 4px;font-size:19px}}
  .sub{{color:var(--muted);font-size:13px;margin-bottom:10px}}
  table{{width:100%;border-collapse:collapse;font-size:14px}}
  td,th{{padding:4px 6px;border-bottom:1px solid var(--line);
    vertical-align:top;text-align:left}}
  td.k{{color:var(--muted);width:32%}}
  .nb{{font-size:13px;padding:2px 0;color:var(--muted)}}
  .jw td{{font-size:14px}}
  .ya{{color:var(--warn);font-weight:600}}
  .tidak{{color:var(--ok);font-weight:600}}
  .tag{{font-size:12px;color:var(--muted)}}
  .pill{{font-size:13px;color:var(--muted);margin-right:14px}}
  details{{margin-top:8px}}
  summary{{cursor:pointer;color:var(--accent);font-size:14px}}
</style>
</head>
<body>
<header id="head"></header>
<main id="isi"></main>
<script>
const NODES = {data};
const R = {ringkas};

const porsi = Object.entries(R.porsi_ya).map(([a, v]) =>
  a + " " + (v === null ? "-" : Math.round(v * 100) + "%")).join(", ");
document.getElementById("head").innerHTML =
  "<span class='pill'><b>" + R.dinilai + "</b> node dinilai</span>" +
  "<span class='pill'>bulat <b>" + R.bulat + "</b></span>" +
  "<span class='pill'>berselisih <b>" + R.beda + "</b></span>" +
  "<span class='pill'>porsi Ya per anotator: " + porsi + "</span>";

const kelas = (l) => l === "1" ? "ya" : (l === "0" ? "tidak" : "tag");
const teks = (l) => l === "1" ? "Ya" : (l === "0" ? "Tidak" : l || "-");

document.getElementById("isi").innerHTML = NODES.map((n) => {{
  const attr = n.atribut.map((r) =>
    "<tr><td class='k'>" + r.label + "</td><td>" + r.value
    + "</td><td class='tag'>" + (r.band || "") + "</td><td class='tag'>"
    + (r.typical || "") + "</td></tr>").join("");
  const nb = n.tetangga.map((t) =>
    "<div class='nb'>" + (t.arah === "masuk" ? "\\u2190" : "\\u2192") + " "
    + t.rel + " &middot; " + t.id + " &middot; w " + t.w.toFixed(2)
    + " &middot; " + t.ringkas + "</div>").join("");
  const jw = n.jawaban.map((j) =>
    "<tr><td class='k'>" + j.anotator + "</td><td class='" + kelas(j.label)
    + "'>" + teks(j.label) + "</td><td>" + (j.confidence || "-")
    + "</td><td class='tag'>" + (j.note || "") + "</td></tr>").join("");
  return "<div class='card" + (n.berselisih ? " beda" : "") + "'>"
    + "<h2>" + n.id + (n.berselisih ? " &mdash; berselisih" : "") + "</h2>"
    + "<div class='sub'>" + n.tipe + " &middot; pertama terlihat " + n.pertama
    + "</div>"
    + "<table class='jw'><tr><th>Anotator</th><th>Jawaban</th>"
    + "<th>Keyakinan</th><th>Bukti dan catatan</th></tr>" + jw + "</table>"
    + "<details><summary>Tampilkan bukti node</summary>"
    + "<table>" + attr + "</table>"
    + "<div class='sub' style='margin-top:10px'>TETANGGA (" + n.n_tetangga
    + (n.n_tetangga_khas === null ? "" : ", khas " + n.n_tetangga_khas)
    + ")</div>" + nb + "</details></div>";
}}).join("");
</script>
</body>
</html>
"""
