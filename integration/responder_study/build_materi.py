"""  """"""
Bangun materi studi responden sebagai HTML statis satu berkas.

Studi ini membandingkan dua bentuk penjelasan risiko atas entitas yang sama:
penjelasan **rule-based** (daftar aturan yang menyala) dan **evidence subgraph**
GNNExplainer. Yang dinilai responden adalah kejelasan, kepercayaan, dan
kecukupan informasi — bukan benar/salahnya penilaian sistem.

Responden adalah mahasiswa awam, bukan analis. Karena itu seluruh istilah teknis
diterjemahkan ke bahasa sehari-hari lewat tiga tabel di bawah
(`ENTITY_LABEL`, `RELATION_LABEL`, `RULE_PLAIN`). Yang dinilai adalah apakah
penjelasannya dapat dipahami; kalau bahasanya sendiri yang menghalangi, studi ini
mengukur kemampuan membaca jargon, bukan kualitas penjelasan.

## Semua sumber dibaca LANGSUNG dari disk

Tidak ada panggilan API maupun Docker. Alasannya bukan kepraktisan: endpoint
`criticalSubgraph` masih punya celah mount Docker yang belum tuntas, dan
studi ini tidak perlu menunggu itu selesai.

| Panel | Sumber |
|---|---|
| Rule-based | `data/synthetic/seed_42/weak_labels.csv` + bobot dari `rules.scoring.RULES` |
| Evidence subgraph | tabel relasi dari `experiments/results/explanations/{node}.md` |

**Rule engine v1 di backend lama sengaja TIDAK dipakai.** Ia buta terhadap data
v2 dan selalu mengembalikan skor 0 dengan `triggeredRules` kosong —
memakainya akan membuat panel rule-based kosong.

## Gambar digambar ulang di sini, dan itu perlu dijelaskan

Berkas `explanations/*.png` milik orang B **tidak dipakai**, walaupun isinya benar.
Alasannya bukan selera: matplotlib mencetak teks ke dalam piksel gambar, dan teks
itu memuat

- judul `Evidence subgraph — victim_00056`, yaitu `node_id` mentah yang justru
  sudah kami sembunyikan dari HTML, dan
- keterangan `tebal garis = kontribusi terhadap skor (GNNExplainer)` — **menyebut
  nama metodenya**, sehingga responden langsung tahu panel mana yang "AI" dan
  seluruh blinding butir 1 di bawah batal, serta
- label simpul dan sisi berupa `social_account_01405` dan `transferred_to`, yaitu
  jargon yang sudah diterjemahkan di tabelnya.

Kebocoran ini **tidak mungkin tertangkap** oleh pemeriksaan teks HTML, karena
teksnya berada di dalam gambar, bukan di markup. Ia ketemu saat memeriksa
`draw_case()` di `experiments/explain.py`, bukan dari hasil grep.

Yang digambar ulang hanya **tampilannya**. Isi penjelasannya — sisi mana yang
penting dan seberapa besar kontribusinya — tetap sepenuhnya keluaran GNNExplainer
orang B, dibaca apa adanya dari tabel di `.md`. Berkas `.png` orang B tetap ada
dan tetap dipakai sebagai artefak teknis pendukung analisis.

## Lima hal yang menjaga studi ini tetap sah

1. **Label panel netral.** Panel disebut "Penjelasan A" dan "Penjelasan B", bukan
   "rule-based" dan "GNN". Mengacak posisi tapi tetap memberi label metode hampir
   tidak mengontrol bias — responden akan condong ke apa pun berlabel "AI".

2. **Posisi kiri/kanan tetap, tidak diacak saat dibuka.** Kalau diacak per-muat,
   tiap responden melihat tata letak berbeda dan jawabannya tidak bisa
   dibandingkan. Varian A dan B adalah cerminan penuh, dibagikan separuh-separuh.

3. **Skor angka dibuang.** `mlScore` dan skor rule-based 0–100 tidak ditampilkan.
   Kalau ditampilkan, responden membandingkan "0,9999" lawan "35/100" dan menilai
   angkanya, bukan penjelasannya. Baris skor di `.md` disaring keluar.

4. **Kekuatan bukti disajikan sebagai batang, di KEDUA panel dengan gaya sama.**
   Panel subgraph punya angka kontribusi; kalau panel rule-based hanya diberi
   daftar nama tanpa indikator kekuatan, ia dihandicap dan perbandingannya tidak
   jujur. Batang juga lebih terbaca bagi orang awam
   daripada angka desimal.

5. **Jenis entitas DICANTUMKAN di kepala kasus** (mis. "E-wallet / QRIS #00030").

   Keputusan ini sempat kebalikannya. Versi sebelumnya menyembunyikan jenis
   entitas supaya kasus 6 tidak langsung terbaca sebagai korban sebelum responden
   membaca penjelasan apa pun. Diubah atas permintaan manusia, dan alasannya sah:
   tanpa jenisnya, "Entitas #00030" tidak bermakna apa pun bagi orang awam, dan
   studi ini jadi mengukur kemampuan menerka alih-alih kejelasan penjelasan.

   Konsekuensinya untuk kontrol negatif harus dinyatakan terus-terang: pada kasus
   6, responden **sudah tahu** entitas itu seorang korban pelapor sebelum membaca
   apa pun. Pertanyaan yang diukur bergeser, dan versi barunya justru lebih dekat
   ke kenyataan — seorang analis sungguhan juga melihat jenis entitasnya di
   dashboard. Yang diamati sekarang: **meski sudah tahu ini korban, apakah daftar
   temuan rule-based tetap terbaca meyakinkan sebagai bukti pelaku, sementara
   panel subgraph memperlihatkan bahwa seluruh dasarnya hanya satu transfer?**

## Yang TIDAK ada di HTML, dan kenapa

Kode responden, tanggal, penanda varian, waktu mulai/selesai, dan kolom komentar
sengaja tidak dicetak. Jawaban dikumpulkan lewat Google Form, jadi field
administratif di HTML hanya menambah kebingungan. HTML ini murni **lembar soal**.

> **Konsekuensi yang harus disadari:** studi ini meminta *waktu penyelesaian* ikut
> diukur. Google Form hanya mencatat waktu kirim, bukan durasi. Bila durasi tetap
> diinginkan, koordinator perlu mencatatnya manual per sesi atau memakai satu
> Form per kasus. Jangan sampai butir itu hilang tanpa disadari.

## Cara pakai

    python integration/responder_study/build_materi.py
"""

from __future__ import annotations

import base64
import csv
import html
import io
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from rules.scoring import RULES  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
SEED = 42
DATA_DIR = REPO_ROOT / "data" / "synthetic" / f"seed_{SEED}"
EXPLANATIONS_DIR = REPO_ROOT / "experiments" / "results" / "explanations"

# Urutan kasus TETAP — sama untuk kedua varian, hanya posisi panel yang dicermin.
# Lima kasus pertama dipilih orang B berdasarkan selisih skor terbesar;
# kasus keenam adalah kontrol negatif.
#
# `kiri` = metode yang tampil di kolom kiri pada **varian A**. Sengaja tidak
# berselang-seling rapi: pola R,G,R,G,… mudah ditebak, dan begitu responden
# menebak satu kasus ia tahu semuanya. Komposisinya tetap seimbang 3 lawan 3.
CASES: tuple[dict[str, str], ...] = (
    {"node_id": "domain_00007", "kiri": "rule"},
    {"node_id": "ewallet_00030", "kiri": "gnn"},
    {"node_id": "domain_00001", "kiri": "gnn"},
    {"node_id": "social_account_00004", "kiri": "rule"},
    {"node_id": "bank_account_00013", "kiri": "gnn"},
    # KONTROL NEGATIF — `victim_00056`, `gt_illicit = 0`.
    #
    # Kedua sistem memberinya skor maksimum (rule-based 100/critical, R-GCN
    # 1,0000) padahal ia korban, bukan pelaku. Alasan model menandainya hanya
    # satu relasi: `transferred_to` ke `ewallet_00030` — yang justru kasus nomor
    # 2 di studi ini. Sebelas relasi sisanya jatuh rata di sekitar 0,30.
    #
    # Bahan langsung untuk bab etika: risiko false positive atas korban, yang
    # diakui di atas kertas dan juga ditemukan secara empiris.
    {"node_id": "victim_00056", "kiri": "rule"},
)

# --- Terjemahan istilah teknis ke bahasa awam --------------------------------

#: Delapan tipe node dalam bahasa sehari-hari.
ENTITY_LABEL: dict[str, str] = {
    "domain": "Situs web",
    "phone": "Nomor telepon",
    "bank_account": "Rekening bank",
    "ewallet": "E-wallet / QRIS",
    "apk": "Aplikasi HP",
    "social_account": "Akun media sosial",
    "report": "Laporan warga",
    "victim": "Korban pelapor",
}

#: Delapan tipe relasi, ditulis sebagai kalimat yang bisa dibaca lurus:
#: "<dari> <relasi> <ke>".
RELATION_LABEL: dict[str, str] = {
    "promotes": "mempromosikan",
    "contacts": "memakai nomor kontak",
    "uses_account": "memakai rekening",
    "transferred_to": "mengirim uang ke",
    "mentions": "menyebut",
    "reported": "melaporkan lewat",
    "linked_to_apk": "menyebarkan aplikasi",
    "redirects_to": "mengalihkan pengunjung ke",
}

#: Judul aturan versi awam. Judul asli di `rules.scoring.RULES` ditulis untuk
#: analis ("Node sangat sentral pada graph") dan tidak dapat dipahami responden
#: awam. Terjemahan ditaruh di sini, BUKAN dengan mengubah `rules/scoring.py` —
#: berkas itu milik orang A dan judulnya dipakai juga di tempat lain.
#:
#: Bila suatu saat orang A menambah aturan baru, judul aslinya tetap dipakai
#: sebagai cadangan supaya aturan itu tidak hilang diam-diam dari materi.
RULE_PLAIN: dict[str, str] = {
    "R-G1": "Sering menerima pembayaran QRIS bernilai kecil — pola khas setoran "
    "judi online",
    "R-G2": "Rekening lama yang tiba-tiba aktif kembali, atau uang dipindah "
    "berlapis-lapis sehingga asalnya sulit dilacak",
    "R-G3": "Satu akun pembayaran QRIS dipakai bergantian oleh beberapa pihak "
    "berbeda",
    "R-G4": "Termasuk dalam rantai situs yang saling mengalihkan pengunjung — "
    "cara pelaku pindah alamat setiap kali diblokir",
    "R-G5": "Dipromosikan serentak oleh banyak akun media sosial",
    "R-G6": "Satu nomor telepon yang sama dipakai untuk beberapa situs sekaligus",
    "R-G7": "Menjadi penghubung antara dua kelompok situs yang tampak tidak "
    "berkaitan",
    "R-G8": "Menerima setoran uang dari beberapa korban yang berbeda",
    "R-X1": "Banyak disebut di laporan yang masuk dari warga",
    "R-X2": "Terhubung ke sangat banyak pihak lain dibanding rata-rata",
}

#: Versi pendek relasi untuk label di dalam gambar — kalimat penuh membuat
#: gambarnya penuh tumpang-tindih.
RELATION_SHORT: dict[str, str] = {
    "promotes": "promosi",
    "contacts": "pakai nomor",
    "uses_account": "pakai rekening",
    "transferred_to": "kirim uang",
    "mentions": "menyebut",
    "reported": "melapor",
    "linked_to_apk": "sebar aplikasi",
    "redirects_to": "alihkan ke",
}

#: Warna per jenis entitas di gambar. Entitas yang sedang dibahas ditimpa merah.
ENTITY_COLOUR: dict[str, str] = {
    "domain": "#8ecae6",
    "phone": "#b5e2b0",
    "bank_account": "#ffd6a5",
    "ewallet": "#ffb4a2",
    "apk": "#cdb4db",
    "social_account": "#a8dadc",
    "report": "#e8e8e8",
    "victim": "#f6e58d",
}

#: Merah untuk entitas yang sedang dibahas. Sama dengan warna fokus orang B
#: (`#c1121f`) supaya gambar responden dan artefak teknis tetap sewarna.
FOCUS_COLOUR = "#c1121f"

#: Bobot aturan tertinggi di `RULES`, dipakai menskalakan batang kekuatan.
MAX_RULE_WEIGHT = max(rule.weight for rule in RULES.values())

LIKERT = ("kejelasan", "kepercayaan", "kecukupan")
LIKERT_LABEL = {
    "kejelasan": "Mudah dipahami — seberapa jelas penjelasan ini bagi Anda",
    "kepercayaan": "Meyakinkan — seberapa percaya Anda pada penilaian ini",
    "kecukupan": "Cukup lengkap — cukupkah ini untuk mengambil keputusan",
}

#: Kolom untuk menampung ekspor Google Form. Bukan lembar isian lagi.
CSV_COLUMNS = (
    "responden_id",
    "varian",
    "kasus",
    "metode",
    "kejelasan",
    "kepercayaan",
    "kecukupan",
    "komentar",
)


def human_entity(node_id: str) -> str:
    """`social_account_00006` -> `Akun media sosial #00006`."""
    prefix, _, number = node_id.rpartition("_")
    label = ENTITY_LABEL.get(prefix)
    if label is None:
        return node_id
    return f"{label} #{number}"


def human_relation(rel_type: str) -> str:
    return RELATION_LABEL.get(rel_type, rel_type)


def entity_type_of(node_id: str) -> str:
    return node_id.rpartition("_")[0]


def entity_type_label(node_id: str) -> str:
    return ENTITY_LABEL.get(entity_type_of(node_id), "Entitas")


def plain_rule_title(rule_id: str) -> str:
    plain = RULE_PLAIN.get(rule_id)
    if plain:
        return plain
    definition = RULES.get(rule_id)
    return definition.title if definition else "(aturan belum diterjemahkan)"


# --- Pembacaan sumber -------------------------------------------------------


def read_rule_panel(node_id: str, weak: pd.DataFrame) -> dict[str, Any]:
    row = weak.loc[weak["node_id"] == node_id]
    if row.empty:
        raise SystemExit(f"{node_id} tidak ada di weak_labels.csv seed {SEED}")
    record = row.iloc[0]

    raw = record["triggered_rules"]
    rule_ids = [r for r in str(raw).split(";") if r] if pd.notna(raw) else []

    rules = []
    for rule_id in rule_ids:
        definition = RULES.get(rule_id)
        rules.append(
            {
                "title": plain_rule_title(rule_id),
                "weight": definition.weight if definition else None,
            }
        )
    return {"rules": rules}


_TABLE_ROW = re.compile(
    r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*([\d.]+)\s*\|$"
)


def read_gnn_panel(node_id: str) -> dict[str, Any]:
    """Panel evidence subgraph — tabel relasi dari `.md` keluaran orang B.

    Baris skor (`mlScore`, `Skor rule-based`) tidak diambil — lihat butir 3 di
    docstring modul. Gambarnya digambar ulang di sini, bukan memakai `.png`
    orang B — alasannya di docstring modul juga.
    """
    md_path = EXPLANATIONS_DIR / f"{node_id}.md"
    if not md_path.exists():
        raise SystemExit(
            f"{md_path} tidak ada. Jalankan lebih dulu:\n"
            "  python experiments/explain.py --seed 42 --nodes "
            + " ".join(case["node_id"] for case in CASES)
        )

    edges = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        match = _TABLE_ROW.match(line.strip())
        if match:
            _, src, rel, dst, importance = match.groups()
            edges.append(
                {
                    "src": src,
                    "rel": rel.strip(),
                    "dst": dst,
                    "importance": float(importance),
                }
            )
    if not edges:
        raise SystemExit(f"tidak ada baris relasi terbaca dari {md_path}")

    return {"edges": edges, "image": draw_plain_subgraph(node_id, edges)}


def draw_plain_subgraph(focus: str, edges: list[dict[str, Any]]) -> str:
    """Gambar peta hubungan versi awam. Mengembalikan PNG base64, "" bila gagal.

    Isi gambarnya sepenuhnya dari `edges` keluaran GNNExplainer orang B; yang
    dibuat di sini hanya penyajiannya:

    - simpul dilabeli `#00030` saja, diwarnai menurut jenis entitas, dengan
      legenda terpisah — nama penuh seperti "Akun media sosial #01405" saling
      tumpang-tindih kalau ditulis di dalam gambar
    - entitas yang sedang dibahas berwarna merah, lebih besar, bergaris tepi tebal
    - label sisi memakai bentuk pendek bahasa Indonesia, bukan `transferred_to`
    - **tidak ada judul dan tidak ada nama metode di dalam gambar**
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        import networkx as nx
    except ImportError:
        return ""

    graph = nx.DiGraph()
    for edge in edges:
        graph.add_edge(
            edge["src"],
            edge["dst"],
            label=RELATION_SHORT.get(edge["rel"], edge["rel"]),
            weight=edge["importance"],
        )
    if graph.number_of_nodes() == 0:
        return ""

    # seed tetap supaya gambar identik tiap kali dibangun ulang
    layout = nx.spring_layout(graph, seed=42, k=1.3, iterations=120)
    figure, axis = plt.subplots(figsize=(12, 8.6))

    colours = [
        FOCUS_COLOUR if n == focus else ENTITY_COLOUR.get(entity_type_of(n), "#dcdcdc")
        for n in graph.nodes
    ]
    sizes = [2100 if n == focus else 1000 for n in graph.nodes]
    borders = [2.4 if n == focus else 0.8 for n in graph.nodes]
    widths = [1.0 + 5.0 * graph[u][v]["weight"] for u, v in graph.edges]

    nx.draw_networkx_nodes(
        graph, layout, node_color=colours, node_size=sizes,
        edgecolors="#333333", linewidths=borders, ax=axis,
    )
    nx.draw_networkx_edges(
        graph, layout, width=widths, edge_color="#6a6a6a", arrowsize=17,
        node_size=sizes, ax=axis,
    )
    nx.draw_networkx_labels(
        graph, layout,
        labels={n: f"#{n.rpartition('_')[2]}" for n in graph.nodes},
        font_size=8,
        font_color="#111111",
        ax=axis,
    )
    nx.draw_networkx_edge_labels(
        graph, layout,
        edge_labels={(u, v): graph[u][v]["label"] for u, v in graph.edges},
        font_size=7, font_color="#444444",
        bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.75},
        ax=axis,
    )

    # Legenda: hanya jenis yang benar-benar muncul di gambar ini.
    present = sorted({entity_type_of(n) for n in graph.nodes if n != focus})
    handles = [
        Line2D(
            [0], [0], marker="o", color="none", label=ENTITY_LABEL.get(kind, kind),
            markerfacecolor=ENTITY_COLOUR.get(kind, "#dcdcdc"),
            markeredgecolor="#333333", markersize=11,
        )
        for kind in present
    ]
    handles.insert(
        0,
        Line2D(
            [0], [0], marker="o", color="none",
            label=f"{entity_type_label(focus)} yang sedang dibahas",
            markerfacecolor=FOCUS_COLOUR, markeredgecolor="#333333", markersize=14,
        ),
    )
    # Legenda ditaruh DI BAWAH gambar, bukan di dalamnya. Versi pertama memakai
    # `loc="upper left"` dan kotaknya menutupi salah satu simpul sampai tidak
    # terbaca — ketemu saat memeriksa gambarnya, bukan dari kode.
    axis.legend(
        handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.01),
        ncol=min(4, len(handles)), fontsize=9.5, frameon=False,
    )

    axis.margins(0.12)
    axis.axis("off")
    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=150)
    plt.close(figure)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


# --- Render -----------------------------------------------------------------


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _bar(fraction: float) -> str:
    """Batang kekuatan bukti. Gaya identik di kedua panel — lihat butir 4."""
    width = max(3, min(100, round(fraction * 100)))
    return f'<span class="bar"><span class="bar-fill" style="width:{width}%"></span></span>'


def render_rule_panel(panel: dict[str, Any]) -> str:
    rows = []
    for rule in panel["rules"]:
        fraction = (rule["weight"] or 0) / MAX_RULE_WEIGHT
        rows.append(
            "<tr>"
            f"<td>{_esc(rule['title'])}</td>"
            f'<td class="strength">{_bar(fraction)}</td>'
            "</tr>"
        )
    return f"""
<div class="panel">
  <p class="panel-lead">Hal-hal yang membuat sistem menilai entitas ini berisiko:</p>
  <table class="evidence">
    <thead><tr><th>Yang ditemukan</th>
    <th class="strength">Pengaruh ke penilaian</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p class="note">Semakin panjang batangnya, semakin besar andil hal itu dalam
  membuat sistem menilai entitas ini berisiko.</p>
</div>
"""


def render_gnn_panel(panel: dict[str, Any]) -> str:
    rows = []
    for edge in panel["edges"]:
        sentence = (
            f'<strong>{_esc(human_entity(edge["src"]))}</strong> '
            f'{_esc(human_relation(edge["rel"]))} '
            f'<strong>{_esc(human_entity(edge["dst"]))}</strong>'
        )
        rows.append(
            "<tr>"
            f"<td>{sentence}</td>"
            f'<td class="strength">{_bar(edge["importance"])}</td>'
            "</tr>"
        )

    image_block = ""
    if panel["image"]:
        image_block = (
            '<figure class="subgraph">'
            '<img alt="Peta hubungan antar entitas terkait" '
            f'src="data:image/png;base64,{panel["image"]}">'
            "<figcaption><strong>Bulatan merah yang paling besar adalah entitas "
            "yang sedang dibahas.</strong> Bulatan lain adalah pihak-pihak yang "
            "terhubung dengannya; warnanya menunjukkan jenisnya, lihat keterangan "
            "di dalam gambar. Garis yang lebih tebal berarti hubungan itu lebih "
            "besar pengaruhnya ke penilaian.</figcaption>"
            "</figure>"
        )

    return f"""
<div class="panel">
  {image_block}
  <p class="panel-lead">Hubungan yang membuat sistem menilai entitas ini berisiko:</p>
  <table class="evidence">
    <thead><tr><th>Yang ditemukan</th>
    <th class="strength">Pengaruh ke penilaian</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p class="note">Semakin panjang batangnya, semakin besar andil hubungan itu
  dalam membuat sistem menilai entitas ini berisiko.</p>
</div>
"""


def render_rating(case_number: int) -> str:
    rows = []
    for key in LIKERT:
        scale = "".join(
            f'<label class="tick"><span class="box"></span>{n}</label>' for n in range(1, 6)
        )
        rows.append(
            "<tr>"
            f"<th>{_esc(LIKERT_LABEL[key])}</th>"
            f'<td class="scale">{scale}</td>'
            f'<td class="scale">{scale}</td>'
            "</tr>"
        )
    return f"""
<div class="rating">
  <h3>Nilai kedua penjelasan di atas</h3>
  <p class="note">1 = sangat kurang, 5 = sangat baik. Tidak ada jawaban benar
  atau salah. Isikan pilihan Anda pada formulir online.</p>
  <table class="rating-table">
    <thead><tr><th></th><th>Penjelasan A</th><th>Penjelasan B</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div>
"""


STYLE = """
:root { --ink:#1a1a1a; --muted:#5c5c5c; --line:#c9c9c9; --bg:#fff; --accent:#f4f4f2;
  --bar:#7a7a7a; }
* { box-sizing:border-box; }
body { margin:0; padding:24px; background:var(--bg); color:var(--ink);
  font:16px/1.65 "Segoe UI", system-ui, sans-serif; max-width:1180px; }
h1 { font-size:25px; margin:0 0 6px; }
h2 { font-size:20px; margin:0; }
h3 { font-size:14px; margin:0 0 6px; text-transform:uppercase;
  letter-spacing:.06em; color:var(--muted); }
p { margin:0 0 12px; }
.sub { color:var(--muted); margin-bottom:26px; }
.intro { border-left:3px solid var(--ink); padding:0 0 0 18px; margin-bottom:34px; }
.intro p.what { font-size:17px; }
.intro ol { margin:0 0 14px; padding-left:22px; }
.intro ol li { margin-bottom:7px; }
.intro ul { margin:0; padding-left:22px; }
.intro ul li { margin-bottom:8px; }
table.glossary { border-collapse:collapse; margin:0 0 12px; font-size:14.5px; }
table.glossary td { padding:4px 14px 4px 0; vertical-align:top; }
table.glossary td:first-child { font-weight:600; white-space:nowrap; }
table.glossary td:last-child { color:var(--muted); }
.example { border:1px dashed #a8a8a8; background:#fbfbfa; margin:0 0 14px; }
.example-head { display:flex; justify-content:space-between; align-items:baseline;
  gap:14px; padding:9px 14px; border-bottom:1px dashed #a8a8a8;
  font-size:13px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); flex-wrap:wrap; }
.example-head .entity { font-size:15px; font-weight:600; text-transform:none;
  letter-spacing:0; color:var(--ink); }
.example-body { display:grid; grid-template-columns:1fr 1fr; }
.example-body > div { padding:0 14px 12px; }
.example-body > div:first-child { border-right:1px dashed #a8a8a8; }
.example-body .panel-title { padding:9px 0; border-bottom:0; font-size:13px; }
.example-note { margin:0; padding:0 14px 12px; font-size:13.5px;
  color:var(--muted); border-top:1px dashed #a8a8a8; padding-top:11px; }
.case { border:1px solid var(--line); margin-bottom:34px; }
.case-head { display:flex; justify-content:space-between; align-items:baseline;
  gap:16px; padding:13px 16px; background:var(--accent);
  border-bottom:1px solid var(--line); flex-wrap:wrap; }
.case-head .entity { font-size:17px; font-weight:600; }
.panels { display:grid; grid-template-columns:1fr 1fr; }
.panels > div:first-child { border-right:1px solid var(--line); }
.panel-title { margin:0; padding:11px 16px; font-size:15px; font-weight:700;
  text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid var(--line); }
.panel { padding:16px; }
.panel-lead { font-size:14px; color:var(--muted); margin-bottom:8px; }
table.evidence { width:100%; border-collapse:collapse; font-size:13.5px; }
table.evidence th { text-align:left; border-bottom:1px solid var(--line);
  padding:6px; font-weight:600; color:var(--muted); font-size:11.5px;
  text-transform:uppercase; letter-spacing:.04em; }
table.evidence td { padding:7px 6px; border-bottom:1px solid #eee;
  vertical-align:middle; }
th.strength, td.strength { width:104px; text-align:left; }
.bar { display:inline-block; width:88px; height:9px; background:#e6e6e6;
  border-radius:5px; overflow:hidden; vertical-align:middle; }
.bar-fill { display:block; height:100%; background:var(--bar); }
.note { font-size:13px; color:var(--muted); margin:8px 0 0; }
figure.subgraph { margin:0 0 16px; }
figure.subgraph img { width:100%; height:auto; border:1px solid var(--line); }
figure.subgraph figcaption { font-size:12px; color:var(--muted); margin-top:5px; }
.rating { border-top:2px solid var(--ink); padding:16px; }
table.rating-table { width:100%; border-collapse:collapse; }
table.rating-table th { text-align:left; font-size:14px; padding:8px;
  border-bottom:1px solid var(--line); }
table.rating-table thead th { text-align:center; text-transform:uppercase;
  font-size:12px; letter-spacing:.06em; }
table.rating-table thead th:first-child { width:44%; }
table.rating-table tbody th { font-weight:400; }
td.scale { text-align:center; padding:8px; border-bottom:1px solid #eee;
  white-space:nowrap; }
.tick { display:inline-block; margin:0 8px; font-size:14px; }
.tick .box { display:inline-block; width:14px; height:14px;
  border:1px solid var(--ink); border-radius:50%; margin-right:4px;
  vertical-align:-2px; }
.closing { border-top:1px solid var(--line); padding-top:16px; color:var(--muted);
  font-size:14px; }
@media print {
  body { padding:0; font-size:11pt; max-width:none; }
  @page { size:A4; margin:14mm; }
  .case { page-break-inside:avoid; page-break-after:always; border-color:#999; }
  .intro { page-break-after:always; }
  figure.subgraph img { max-height:76mm; width:auto; }
}
@media (max-width:820px) {
  .panels, .example-body { grid-template-columns:1fr; }
  .panels > div:first-child { border-right:0; border-bottom:1px solid var(--line); }
  .example-body > div:first-child { border-right:0; border-bottom:1px dashed #a8a8a8; }
}
"""

INTRO = """
<div class="intro">
  <p class="what"><strong>Singkatnya:</strong> Anda akan melihat 6 kasus. Tiap
  kasus menampilkan <strong>dua penjelasan</strong> tentang hal yang sama,
  berdampingan. Tugas Anda cukup satu: menilai <strong>penjelasan mana yang lebih
  mudah dipahami dan lebih meyakinkan</strong>.</p>

  <h3>Apa yang sedang diuji</h3>

  <p>Kami sedang membuat sistem yang <strong>memetakan jaringan judi online
  (judol) dan pinjaman online ilegal</strong> di Indonesia. Kuncinya begini:
  pelaku tidak bekerja sendirian. Satu operasi biasanya memakai banyak situs
  web, banyak nomor WhatsApp, banyak rekening dan e-wallet, aplikasi HP, serta
  ratusan akun media sosial untuk promosi — semuanya saling terhubung. Kalau satu
  situs diblokir, mereka pindah ke situs lain yang sudah disiapkan. Karena itu
  memeriksanya satu per satu tidak cukup; yang perlu dilihat adalah
  <strong>jaringannya</strong>.</p>

  <p>Sistem ini membantu petugas menemukan mana yang perlu diperiksa lebih dulu,
  dan yang lebih penting: <strong>menjelaskan alasannya</strong>. Penjelasan itu
  yang sedang kami uji. Sebuah sistem yang menuding tanpa bisa menjelaskan tidak
  ada gunanya bagi petugas — dan berbahaya kalau ternyata salah.</p>

  <h3>Apa itu "entitas"?</h3>

  <p><strong>Entitas</strong> adalah satu benda atau akun yang dicatat sistem ini
  sebagai bagian dari jaringan. Bentuknya bisa bermacam-macam:</p>

  <table class="glossary">
    <tbody>
      <tr><td>Situs web</td><td>alamat situs, misalnya tempat orang bertaruh</td></tr>
      <tr><td>Nomor telepon</td><td>nomor WhatsApp yang dipakai melayani korban</td></tr>
      <tr><td>Rekening bank</td><td>rekening penampung uang</td></tr>
      <tr><td>E-wallet / QRIS</td><td>akun pembayaran digital atau kode QRIS</td></tr>
      <tr><td>Aplikasi HP</td><td>aplikasi yang disebar di luar toko resmi</td></tr>
      <tr><td>Akun media sosial</td><td>akun yang menyebarkan promosi</td></tr>
      <tr><td>Laporan warga</td><td>satu laporan yang masuk dari masyarakat</td></tr>
      <tr><td>Korban pelapor</td><td>orang yang melapor karena menjadi korban</td></tr>
    </tbody>
  </table>

  <p>Tiap kasus di bawah membahas <strong>satu entitas</strong>. Jenis dan
  nomornya ditulis di judul kasus, misalnya "E-wallet / QRIS #00030". Nomornya
  hanya penanda, tidak mengandung arti.</p>

  <h3>Yang perlu Anda lakukan</h3>

  <ol>
    <li>Lihat judul kasus untuk tahu <strong>entitas apa</strong> yang dibahas.</li>
    <li>Baca <strong>Penjelasan A</strong> di kiri, lalu <strong>Penjelasan B</strong>
    di kanan. Keduanya membahas entitas yang sama, hanya cara menjelaskannya
    berbeda.</li>
    <li>Beri nilai <strong>1 sampai 5</strong> untuk <em>masing-masing</em>
    penjelasan: seberapa mudah dipahami, seberapa meyakinkan, dan seberapa cukup
    informasinya.</li>
    <li>Lanjut ke kasus berikutnya. Ada 6 kasus, perkiraan 15–20 menit.</li>
  </ol>

  <h3>Contoh cara mengerjakan</h3>

  <p class="note">Contoh di bawah ini <strong>bukan bagian penilaian</strong> —
  hanya untuk memperlihatkan bentuknya.</p>

  <div class="example">
    <div class="example-head">
      <span>Kasus contoh</span>
      <span class="entity">Situs web #00123</span>
    </div>
    <div class="example-body">
      <div>
        <p class="panel-title">Penjelasan A</p>
        <table class="evidence">
          <thead><tr><th>Yang ditemukan</th>
          <th class="strength">Pengaruh ke penilaian</th></tr></thead>
          <tbody>
            <tr><td>Dipromosikan serentak oleh banyak akun media sosial</td>
            <td class="strength"><span class="bar"><span class="bar-fill"
            style="width:80%"></span></span></td></tr>
            <tr><td>Banyak disebut di laporan yang masuk dari warga</td>
            <td class="strength"><span class="bar"><span class="bar-fill"
            style="width:45%"></span></span></td></tr>
          </tbody>
        </table>
      </div>
      <div>
        <p class="panel-title">Penjelasan B</p>
        <table class="evidence">
          <thead><tr><th>Yang ditemukan</th>
          <th class="strength">Pengaruh ke penilaian</th></tr></thead>
          <tbody>
            <tr><td><strong>Akun media sosial #00456</strong> mempromosikan
            <strong>Situs web #00123</strong></td>
            <td class="strength"><span class="bar"><span class="bar-fill"
            style="width:100%"></span></span></td></tr>
            <tr><td><strong>Situs web #00123</strong> memakai nomor kontak
            <strong>Nomor telepon #00789</strong></td>
            <td class="strength"><span class="bar"><span class="bar-fill"
            style="width:35%"></span></span></td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <p class="example-note">Perhatikan bedanya: yang satu menyebut
    <em>pola umum</em> yang ditemukan, yang lain menyebut <em>pihak-pihak tertentu
    dan kaitannya</em>. Mana yang lebih membantu Anda memahami alasan sistem
    menilai entitas ini berisiko? Itu yang kami tanyakan. Pada kasus sungguhan,
    salah satu penjelasan juga disertai gambar peta hubungan.</p>
  </div>

  <h3>Empat hal yang perlu diketahui lebih dulu</h3>

  <ul>
    <li><strong>Semua data di sini buatan.</strong> Dibuat komputer meniru pola
    kejahatan yang dilaporkan PPATK dan Komdigi. Tidak ada situs, nomor,
    rekening, atau orang sungguhan — jadi tidak ada siapa pun yang dirugikan
    oleh penilaian Anda.</li>

    <li><strong>Nomor entitas sengaja dibuat tidak bermakna</strong> (misalnya
    "#00007"). Mohon menilai dari <em>bukti yang ditampilkan</em>, karena
    nomornya memang tidak mengandung petunjuk apa pun.</li>

    <li><strong>Anda tidak perlu tahu soal teknologi.</strong> Justru itu
    intinya: kalau penjelasan hanya bisa dipahami ahli, berarti penjelasannya
    belum cukup baik.</li>

    <li><strong>Yang dinilai penjelasannya, bukan Anda.</strong> Tidak ada
    jawaban benar atau salah, dan jawaban Anda anonim. Kalau sebuah penjelasan
    membingungkan, beri nilai rendah — itu justru informasi yang kami cari.</li>
  </ul>
</div>
"""

CLOSING = """
<div class="closing">
  <p><strong>Selesai. Terima kasih banyak.</strong> Masukan Anda dipakai untuk
  memperbaiki cara sistem ini menjelaskan temuannya.</p>
</div>
"""


def build_html(variant: str, panels: dict[str, dict[str, Any]]) -> str:
    """Susun satu varian. `variant` = "A" atau "B" (B = cermin penuh A).

    Penanda varian sengaja tidak dicetak di halaman — responden tidak perlu
    tahu ada dua versi, dan kalau tahu, ia bisa menduga posisi panel bermakna.
    Koordinator membedakannya dari nama berkas.
    """
    blocks = []
    for number, case in enumerate(CASES, start=1):
        node_id = case["node_id"]
        rule_html = render_rule_panel(panels[node_id]["rule"])
        gnn_html = render_gnn_panel(panels[node_id]["gnn"])

        left_is_rule = case["kiri"] == "rule"
        if variant == "B":
            left_is_rule = not left_is_rule
        left, right = (rule_html, gnn_html) if left_is_rule else (gnn_html, rule_html)

        # Jenis entitas ikut disebut — lihat butir 5 di docstring modul, termasuk
        # konsekuensinya untuk kontrol negatif kasus 6.
        blocks.append(
            f"""
<section class="case">
  <div class="case-head">
    <h2>Kasus {number} dari {len(CASES)}</h2>
    <span class="entity">{_esc(human_entity(node_id))}</span>
  </div>
  <div class="panels">
    <div><p class="panel-title">Penjelasan A</p>{left}</div>
    <div><p class="panel-title">Penjelasan B</p>{right}</div>
  </div>
  {render_rating(number)}
</section>
"""
        )

    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Menilai Penjelasan Sistem Pemetaan Jaringan Judol dan Pinjol Ilegal</title>
<style>{STYLE}</style>
</head>
<body>
<h1>Mana penjelasan yang lebih mudah dipahami?</h1>
<p class="sub">Studi singkat tentang cara sebuah sistem menjelaskan temuannya.
Seluruh data adalah simulasi.</p>

{INTRO}
{''.join(blocks)}
{CLOSING}
</body>
</html>
"""


# --- Keluaran pendamping ----------------------------------------------------


def write_rating_sheet(path: Path) -> None:
    """Kerangka kolom untuk menampung **ekspor Google Form**.

    Bukan lembar isian: jawaban dikumpulkan lewat Form. Berkas ini ada supaya
    bentuk data untuk analisis sudah tetap sejak awal.

    Dua kolom di luar rancangan awal, keduanya mencegah kegagalan data yang
    tidak bergejala:

    - `metode` — tanpa ini tidak ada cara tahu nilai 4 itu untuk penjelasan
      rule-based atau subgraph, dan perbandingan studi tidak dapat dihitung.
      Satu kasus menghasilkan dua baris.
    - `varian` — kunci A/B berbeda antara varian A dan B. Salah menerapkan kunci
      akan menukar seluruh nilai satu responden tanpa gejala apa pun.
    """
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerow(CSV_COLUMNS)


def write_form_questions(path: Path) -> None:
    """Daftar pertanyaan siap disalin ke Google Form."""
    lines = [
        "# Pertanyaan Google Form — Studi Responden SATPAM",
        "",
        "Salin ke Google Form. **Buat dua Form terpisah** (atau dua tautan),",
        "satu untuk varian A dan satu untuk varian B — nilai dari kedua varian",
        "tidak boleh tercampur dalam satu kolom karena arti \"Penjelasan A\"",
        "berbeda di antara keduanya. Lihat `kunci_koordinator.md`.",
        "",
        "## Bagian pembuka",
        "",
        "- **Kode responden** — jawaban pendek. Cukup inisial + angka, jangan nama.",
        "- Sisipkan tautan berkas materi (`materi_studi.html` untuk Form varian A,",
        "  `materi_studi_varian_b.html` untuk Form varian B).",
        "",
        "## Per kasus (ulangi untuk kasus 1 sampai 6)",
        "",
        "Untuk tiap kasus, enam pertanyaan skala linear 1–5 (1 = sangat kurang,",
        "5 = sangat baik):",
        "",
        "| Pertanyaan | Untuk |",
        "|---|---|",
        "| Kasus N — Penjelasan A: seberapa mudah dipahami? | kejelasan |",
        "| Kasus N — Penjelasan A: seberapa meyakinkan? | kepercayaan |",
        "| Kasus N — Penjelasan A: seberapa cukup informasinya? | kecukupan |",
        "| Kasus N — Penjelasan B: seberapa mudah dipahami? | kejelasan |",
        "| Kasus N — Penjelasan B: seberapa meyakinkan? | kepercayaan |",
        "| Kasus N — Penjelasan B: seberapa cukup informasinya? | kecukupan |",
        "",
        "Tambahkan satu paragraf opsional per kasus: *\"Ada yang membingungkan",
        "atau justru sangat membantu di kasus ini?\"* — kutipan kualitatif singkat",
        "diminta sebagai bagian keluaran studi.",
        "",
        "## Bagian penutup",
        "",
        "- Paragraf opsional: *\"Masukan umum di luar keenam kasus?\"*",
        "",
        "## Waktu penyelesaian — jangan sampai terlewat",
        "",
        "Studi ini meminta **waktu penyelesaian** ikut diukur. Google Form hanya",
        "mencatat waktu kirim, bukan durasi pengerjaan. Pilih salah satu:",
        "",
        "1. Koordinator mencatat waktu mulai dan selesai tiap responden secara",
        "   manual (paling sederhana bila sesinya diawasi).",
        "2. Tambahkan pertanyaan \"jam mulai\" di awal Form dan bandingkan dengan",
        "   waktu kirim otomatis.",
        "",
        "Bila akhirnya tidak diukur, laporkan itu sebagai keterbatasan — jangan",
        "dibiarkan hilang tanpa disebut.",
        "",
        "## Menyalin hasil untuk analisis",
        "",
        "Ekspor Form ke CSV, lalu susun ulang ke bentuk `lembar_penilaian.csv`:",
        "kolom `responden_id, varian, kasus, metode, kejelasan, kepercayaan,",
        "kecukupan, komentar`. **Satu kasus menjadi dua baris** — satu untuk",
        "`rule_based`, satu untuk `gnn` — menurut kunci di",
        "`kunci_koordinator.md`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_coordinator_key(path: Path) -> None:
    """Kunci A/B — sengaja di luar HTML supaya responden tidak menemukannya."""
    label = {"rule": "rule-based", "gnn": "evidence subgraph"}
    lines = [
        "# Kunci Koordinator — Studi Responden SATPAM",
        "",
        "> **Jangan diperlihatkan kepada responden.** Berkas ini sengaja dipisah",
        "> dari HTML materi: kalau kuncinya ikut di dalam berkas yang dibuka",
        "> responden, ia dapat ditemukan hanya dengan menggulir ke bawah.",
        "",
        f"Seed data: {SEED}. Enam kasus, urutan tetap di kedua varian.",
        "",
        "## Pemetaan panel ke metode",
        "",
        "| # | Node | Entitas di HTML | Varian A: A | Varian A: B | Varian B: A | Varian B: B |",
        "|---:|---|---|---|---|---|---|",
    ]
    for number, case in enumerate(CASES, start=1):
        node_id = case["node_id"]
        _, _, num = node_id.rpartition("_")
        a_left = case["kiri"]
        a_right = "gnn" if a_left == "rule" else "rule"
        lines.append(
            f"| {number} | `{node_id}` | Entitas #{num} | {label[a_left]} "
            f"| {label[a_right]} | {label[a_right]} | {label[a_left]} |"
        )

    lines += [
        "",
        "Varian B adalah cermin penuh varian A. Bagikan kedua varian ke separuh",
        "responden masing-masing agar efek posisi kiri/kanan terhapus di tingkat",
        "agregat. Buat **dua Google Form terpisah** — arti \"Penjelasan A\" berbeda",
        "antara kedua varian, jadi nilainya tidak boleh tercampur dalam satu kolom.",
        "",
        "## Kasus 6 adalah kontrol negatif — `victim_00056`",
        "",
        "Node ini ber-`gt_illicit = 0`: ia **korban, bukan pelaku**. Kedua sistem",
        "tetap memberinya skor maksimum (rule-based 100/critical, R-GCN 1,0000).",
        "",
        "Alasan model menandainya hanya satu relasi: `transferred_to` ke",
        "`ewallet_00030` dengan kontribusi 1,000 — dan `ewallet_00030` itu justru",
        "kasus nomor 2 di studi ini. Sebelas relasi sisanya jatuh rata di sekitar",
        "0,30, artinya praktis tidak menyumbang apa pun.",
        "",
        "Nilainya untuk bab etika: risiko false positive atas korban yang",
        "diakui di atas kertas, dan yang juga ditemukan secara empiris,",
        "kini punya satu kasus konkret yang bisa ditunjukkan.",
        "",
        "## Kepala kasus MENYEBUTKAN jenis entitas — konsekuensinya untuk kasus 6",
        "",
        "Judul kasus 6 di HTML berbunyi **\"Korban pelapor #00056\"** — responden",
        "sudah tahu ini korban SEBELUM membaca satu penjelasan pun. Ini keputusan",
        "yang sengaja diubah dari rancangan awal (yang menyembunyikan jenisnya)",
        "atas permintaan manusia: tanpa jenis entitas, \"Entitas #00056\" tidak",
        "bermakna apa pun bagi orang awam, dan studi ini jadi mengukur kemampuan",
        "menerka, bukan kejelasan penjelasan. Ini juga lebih dekat ke kenyataan:",
        "seorang analis sungguhan di dashboard juga langsung melihat jenis entitas.",
        "",
        "**Konsekuensinya, pertanyaan yang diukur bergeser.** Semula: \"apakah",
        "penjelasan membuat responden MENYADARI ini korban?\" Sekarang, karena",
        "jenisnya sudah diketahui lebih dulu: \"meski sudah tahu ini korban, apakah",
        "salah satu penjelasan tetap terbaca meyakinkan seolah bukti pelaku,",
        "sementara yang lain justru terasa janggal atau tidak cocok dengan fakta",
        "bahwa entitas ini korban?\"",
        "",
        "**Yang layak diamati dari jawaban responden**, dengan pertanyaan baru itu:",
        "",
        "- Panel rule-based menyodorkan daftar temuan generik tanpa nama pihak",
        "  lain, salah satunya **\"Menerima setoran uang dari beberapa korban yang",
        "  berbeda\"** (R-G8). Dibaca oleh seseorang yang SUDAH TAHU subjeknya",
        "  korban, kalimat itu janggal — bagaimana bisa korban \"menerima setoran",
        "  dari korban lain\"? Pertanyaannya: apakah responden menangkap kejanggalan",
        "  ini, atau tetap memberi nilai kepercayaan tinggi karena kalimatnya",
        "  terdengar teknis dan meyakinkan?",
        "- Panel subgraph menulis relasi teratasnya sebagai kalimat konkret:",
        "  *\"Korban pelapor #00056 mengirim uang ke E-wallet #00030\"* — satu",
        "  transfer, dan itu memang persis pola korban penipuan (mengirim uang",
        "  sekali ke rekening pelaku). Pertanyaannya: apakah pola bukti yang tipis",
        "  ini (1 relasi kuat, 11 relasi lemah di sekitar 0,30) membuat responden",
        "  menilai kepercayaannya lebih rendah dibanding rule-based — sesuatu yang",
        "  seharusnya terjadi kalau subgraph benar-benar membantu analis mengenali",
        "  bukti yang tipis?",
        "",
        "Kalau nilai kepercayaan panel rule-based tetap tinggi meski responden",
        "sudah tahu ini korban, itu justru temuan penting untuk bab etika: bukti",
        "bahwa penjelasan berbasis aturan bisa terdengar meyakinkan walau menuduh",
        "pihak yang salah — alasan kuat kenapa keputusan akhir wajib tetap di",
        "tangan manusia, bukan otomatis dari skor.",
        "",
        "## Dua catatan lain yang mempengaruhi tafsir hasil",
        "",
        "1. **Lima kasus pertama seluruhnya `gt_illicit = 1`.** Kalau responden",
        "   menyimpulkan bahwa semua kasus memang pelaku, nilai kepercayaan akan",
        "   naik semu. Jangan menyebut proporsi kasus benar/salah sebelum sesi",
        "   selesai.",
        "2. **Kasus 3 (`domain_00001`) dan kasus 4 (`social_account_00004`) punya",
        "   keluaran rule-based yang persis identik** — sama-sama dua temuan yang",
        "   sama — padahal jenis entitas dan bukti subgraph-nya berbeda total. Ini",
        "   bahan kuat: rule-based tidak dapat membedakan dua entitas yang oleh",
        "   model dinilai lewat jalur bukti yang sama sekali lain.",
        "",
        "## Terjemahan istilah — untuk menelusuri balik ke data",
        "",
        "Materi responden memakai bahasa awam. Padanan teknisnya:",
        "",
        "| Di HTML | Di data |",
        "|---|---|",
    ]
    for prefix, human in ENTITY_LABEL.items():
        lines.append(f"| {human} #NNNNN | `{prefix}_NNNNN` |")
    lines.append("")
    lines.append("| Di HTML | rel_type |")
    lines.append("|---|---|")
    for rel, human in RELATION_LABEL.items():
        lines.append(f"| {human} | `{rel}` |")
    lines.append("")
    lines.append("| Di HTML | Kode aturan |")
    lines.append("|---|---|")
    for rule_id, plain in RULE_PLAIN.items():
        lines.append(f"| {plain} | `{rule_id}` |")
    lines += [
        "",
        "Batang \"seberapa berat\" pada panel rule-based adalah bobot aturan dibagi",
        f"bobot tertinggi ({MAX_RULE_WEIGHT}). Batang pada panel subgraph adalah",
        "kontribusi edge mask GNNExplainer, sudah ternormalkan 0–1 oleh orang B.",
        "Keduanya digambar dengan gaya sama supaya perbandingannya adil.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    weak = pd.read_csv(DATA_DIR / "weak_labels.csv")

    panels: dict[str, dict[str, Any]] = {}
    for case in CASES:
        node_id = case["node_id"]
        panels[node_id] = {
            "rule": read_rule_panel(node_id, weak),
            "gnn": read_gnn_panel(node_id),
        }

    missing_image = [n for n, p in panels.items() if not p["gnn"]["image"]]
    if missing_image:
        print(f"  PERINGATAN: gambar subgraph tidak ada untuk {missing_image}")

    untranslated = sorted(
        {
            rule_id
            for case in CASES
            for rule_id in str(
                weak.loc[weak["node_id"] == case["node_id"], "triggered_rules"].iloc[0]
            ).split(";")
            if rule_id and rule_id not in RULE_PLAIN
        }
    )
    if untranslated:
        print(
            f"  PERINGATAN: aturan belum diterjemahkan ke bahasa awam: {untranslated}\n"
            "  Materi tetap dibangun memakai judul teknis aslinya."
        )

    for variant, name in (("A", "materi_studi.html"), ("B", "materi_studi_varian_b.html")):
        path = OUT_DIR / name
        path.write_text(build_html(variant, panels), encoding="utf-8")
        print(f"  varian {variant}: {name} ({path.stat().st_size / 1_048_576:.2f} MB)")

    write_rating_sheet(OUT_DIR / "lembar_penilaian.csv")
    print(f"  kerangka analisis: lembar_penilaian.csv ({len(CSV_COLUMNS)} kolom)")

    write_form_questions(OUT_DIR / "kuesioner_google_form.md")
    print("  pertanyaan Form  : kuesioner_google_form.md")

    write_coordinator_key(OUT_DIR / "kunci_koordinator.md")
    print("  kunci A/B        : kunci_koordinator.md  (JANGAN diperlihatkan responden)")

    print(f"\n{len(CASES)} kasus, {len(CASES) * 2} baris per responden saat dianalisis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
