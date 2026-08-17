"""Instrumen anotasi berbasis peramban — satu berkas HTML mandiri per anotator.

Menggantikan pasangan `worksheet_{ID}.md` + `answers_{ID}.csv` yang diisi tangan.
Keluarannya CSV dengan kolom `ANSWER_COLUMNS` yang sama persis, sehingga
`annotation.build merge` tidak perlu diubah sama sekali.

**Kenapa ada.** Ronde pertama menghasilkan presisi anotator 0,119 dan Fleiss'
kappa 0,177. Sebab utamanya bukan kurangnya usaha, melainkan instrumen yang
membiarkan tiga kebiasaan buruk:

1. Pertanyaannya tidak punya ambang, sehingga ragu berubah menjadi "ya".
2. `confidence` dipakai sebagai kadar kecurigaan, bukan keyakinan atas jawaban,
   sehingga makin yakin justru makin salah.
3. Setiap atribut yang ditampilkan adalah indikator risiko, tidak ada satu pun
   yang bisa dibaca meringankan, sehingga node biasa tidak pernah terlihat biasa.

Aturan yang di lembar Markdown hanya berupa paragraf panduan di sini ditegakkan
mesin: `confidence` hanya empat tombol berpatokan kata, catatan wajib diisi
sebelum label 1 boleh dipilih, tombol lewati tersedia untuk node yang benar-benar
tidak bisa dinilai, dan porsi label 1 milik anotator sendiri terpampang tanpa
menyebut arah mana yang salah.

**Yang sengaja TIDAK ditanam di berkas.** Data node tertanam mentah sebagai JSON,
jadi siapa pun yang membuka Inspect Element melihat isinya. `assert_no_leak`
gagal keras bila `gt_*`, `rule_score`, `rule_level`, `triggered_rules`, atau nama
strata ikut terbawa. Daftar itu sama dengan yang dijaga `worksheet.py`, hanya di
sini penjagaannya wajib eksplisit karena payload-nya berupa data terstruktur,
bukan teks yang sudah dirender.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from annotation.sampling import AnnotationSample
from annotation.worksheet import (
    ANSWER_COLUMNS,
    CONTENT_TYPES,
    FINANCIAL_TYPES,
    MAX_NEIGHBORS_SHOWN,
    REL_NAMES,
    TYPE_NAMES,
    Percentiles,
    _neighbor_summary,
    _rupiah,
)
from rules.graph import RuleGraph
from rules.loader import RuleNode

#: Substring yang tidak boleh muncul di payload JSON, apa pun bentuknya.
FORBIDDEN: tuple[str, ...] = (
    "gt_",
    "rule_score",
    "rule_level",
    "triggered_rules",
    "stratum",
    "strata",
    "hard negative",
)

#: Empat pilihan `confidence`, berpatokan kata. Nilai numeriknya tetap masuk
#: kolom float, jadi kontrak datanya tidak berubah.
CONFIDENCE_CHOICES: tuple[tuple[str, float, str], ...] = (
    ("Yakin", 0.9, "bisa menyebut bukti, atau bisa menyebut ketiadaan bukti, dengan jelas"),
    ("Condong", 0.7, "ada arah, tapi ada yang mengganjal"),
    ("Ragu", 0.5, "dua sisi sama kuat"),
    ("Menebak", 0.3, "tidak punya dasar"),
)

#: Kategori bukti yang wajib dipilih sebelum label 1 dapat disimpan.
#:
#: Ronde pertama membiarkan catatan bersifat opsional, dan hasilnya 13 catatan
#: dari 450 penilaian. Tanpa gesekan apa pun, 81% node dilabeli positif. Syarat
#: "tunjuk dulu apa yang meyakinkan Anda" karena itu dipertahankan, hanya
#: bentuknya diubah dari mengetik menjadi memilih supaya tidak memberatkan.
#:
#: Kategorinya sengaja kualitatif dan tidak memuat ambang apa pun. Menurunkannya
#: dari pita persentil akan membuat anotasi menjadi persetujuan atas rule engine
#: dan merusak independensinya terhadap baseline B1.
EVIDENCE_CHIPS: tuple[str, ...] = (
    "Jejak pada entitas ini sendiri",
    "Pola tetangga langsung",
    "Banyaknya laporan yang menyebut",
    "Pola transaksi atau nominal",
    "Aliran dana dari node korban",
    "Umur atau pola kemunculan",
    "Lainnya (jelaskan di catatan)",
)

#: Pita verbal untuk persentil. Menggantikan bilah yang selalu terlihat berisi.
BANDS: tuple[tuple[float, str], ...] = (
    (25.0, "di bawah kebanyakan"),
    (75.0, "biasa"),
    (95.0, "di atas kebanyakan"),
    (100.1, "ekstrem"),
)


def band_of(percentile: float | None) -> str:
    if percentile is None:
        return ""
    for edge, name in BANDS:
        if percentile < edge:
            return name
    return BANDS[-1][1]


def _typical(percentiles: Percentiles, node_type: str, field: str) -> float | None:
    """Nilai khas (median) sebuah atribut di antara node bertipe sama.

    Inilah bagian yang membuat tampilan dua arah. Tanpa pembanding, "3 laporan"
    hanya bisa dibaca sebagai banyak; dengan pembanding "khas 1", angka yang
    sama bisa dibaca sebagai agak di atas biasa dan tidak lebih dari itu.
    """
    values = percentiles.by_type.get((node_type, field))
    if not values:
        return None
    return float(statistics.median(values))


def _format_value(node: RuleNode, field: str) -> str:
    if field in ("feat_txn_amount_sum", "mean_ticket"):
        return _rupiah(float(getattr(node, field)))
    if field == "feat_kw_score":
        return f"{float(getattr(node, field)):.2f}"
    return f"{float(getattr(node, field)):,.0f}".replace(",", ".")


def _attributes(node: RuleNode, percentiles: Percentiles) -> list[dict]:
    """Atribut node beserta pembandingnya, hanya yang bermakna untuk tipenya."""
    rows: list[dict] = []

    def add(label: str, field: str | None, value: str, note: str = "") -> None:
        if field is None:
            rows.append({"label": label, "value": value, "band": "", "typical": note})
            return
        rank = percentiles.rank(node, field)
        typical = _typical(percentiles, node.node_type, field)
        rows.append({
            "label": label,
            "value": value,
            "band": band_of(rank),
            "typical": "" if typical is None else f"khas {_fmt_typical(field, typical)}",
        })

    if node.node_type == "ewallet":
        add("Merchant QRIS", None, "ya" if node.feat_is_qris else "tidak")

    if node.node_type in FINANCIAL_TYPES:
        if node.feat_txn_count > 0:
            add("Jumlah transaksi", "feat_txn_count", _format_value(node, "feat_txn_count"))
            add("Total nominal", None, _rupiah(node.feat_txn_amount_sum))
            add("Nominal rata-rata", "mean_ticket", _rupiah(node.mean_ticket))
        else:
            add("Jumlah transaksi", None, "0")

    if node.node_type in CONTENT_TYPES:
        add("Skor kata kunci promo", "feat_kw_score", _format_value(node, "feat_kw_score"))

    add("Disebut laporan", "feat_report_count", _format_value(node, "feat_report_count"))
    add("Umur", "feat_age_days", f"{node.feat_age_days:.0f} hari")
    add("Derajat masuk / keluar", None,
        f"{node.feat_degree_in:.0f} / {node.feat_degree_out:.0f}")
    return rows


def _fmt_typical(field: str, value: float) -> str:
    if field in ("feat_txn_amount_sum", "mean_ticket"):
        return _rupiah(value)
    if field == "feat_kw_score":
        return f"{value:.2f}"
    if field == "feat_age_days":
        return f"{value:.0f} hari"
    return f"{value:,.0f}".replace(",", ".")


def _neighbors(graph: RuleGraph, node_id: str) -> list[dict]:
    entries: list[tuple[float, dict]] = []
    for edge in graph.in_edges(node_id):
        other = graph.nodes.get(edge.src_id)
        if other is not None:
            entries.append((edge.weight, {
                "arah": "masuk", "rel": REL_NAMES.get(edge.rel_type, edge.rel_type),
                "id": other.node_id, "w": round(edge.weight, 2),
                "ringkas": _neighbor_summary(graph, other),
            }))
    for edge in graph.out_edges(node_id):
        other = graph.nodes.get(edge.dst_id)
        if other is not None:
            entries.append((edge.weight, {
                "arah": "keluar", "rel": REL_NAMES.get(edge.rel_type, edge.rel_type),
                "id": other.node_id, "w": round(edge.weight, 2),
                "ringkas": _neighbor_summary(graph, other),
            }))
    entries.sort(key=lambda item: -item[0])
    return [item for _, item in entries[:MAX_NEIGHBORS_SHOWN]]


def _typical_degree(graph: RuleGraph) -> dict[str, float]:
    """Jumlah tetangga khas per tipe node.

    Daftar tujuh tetangga tidak berarti apa-apa sampai diketahui bahwa node
    sejenis biasanya punya empat.
    """
    per_type: dict[str, list[int]] = {}
    for node in graph.nodes.values():
        per_type.setdefault(node.node_type, []).append(graph.degree(node.node_id))
    return {t: float(statistics.median(v)) for t, v in per_type.items() if v}


def build_payload(
    graph: RuleGraph, order: list[str], percentiles: Percentiles
) -> list[dict]:
    """Susun rekaman node yang aman ditanam di berkas HTML."""
    typical_degree = _typical_degree(graph)
    payload: list[dict] = []
    for node_id in order:
        node = graph.nodes[node_id]
        total = graph.degree(node_id)
        payload.append({
            "id": node.node_id,
            "tipe": TYPE_NAMES.get(node.node_type, node.node_type),
            "pertama": str(node.first_seen_at.date()),
            "terakhir": str(node.last_seen_at.date()),
            "atribut": _attributes(node, percentiles),
            "tetangga": _neighbors(graph, node_id),
            "n_tetangga": total,
            "n_tetangga_khas": typical_degree.get(node.node_type),
        })
    return payload


def assert_no_leak(payload: list[dict]) -> None:
    """Gagal keras bila kolom jawaban atau nama strata ikut terbawa.

    Dijalankan atas JSON yang sudah diserialisasi, bukan atas objeknya, supaya
    kebocoran yang bersembunyi di dalam string ringkasan tetap tertangkap.
    """
    blob = json.dumps(payload, ensure_ascii=False).lower()
    found = [needle for needle in FORBIDDEN if needle in blob]
    if found:
        raise AssertionError(
            f"payload anotasi memuat penanda terlarang {found}. "
            f"Berkas tidak ditulis. Periksa kembali build_payload()."
        )


def render_html(annotator_id: str, payload: list[dict]) -> str:
    """Bungkus payload menjadi satu berkas HTML mandiri."""
    data = json.dumps(payload, ensure_ascii=False)
    choices = json.dumps(
        [{"nama": n, "nilai": v, "arti": a} for n, v, a in CONFIDENCE_CHOICES],
        ensure_ascii=False,
    )
    columns = json.dumps(list(ANSWER_COLUMNS))
    chips = json.dumps(list(EVIDENCE_CHIPS), ensure_ascii=False)
    return _TEMPLATE.format(
        annotator_id=annotator_id, data=data, choices=choices, columns=columns,
        chips=chips,
    )


def write_webform(
    directory: Path,
    graph: RuleGraph,
    sample: AnnotationSample,
    annotator_id: str,
    order: list[str],
) -> Path:
    """Tulis `form_{ID}.html` untuk satu anotator."""
    percentiles = Percentiles.build(list(graph.nodes.values()))
    payload = build_payload(graph, order, percentiles)
    assert_no_leak(payload)
    path = directory / f"form_{annotator_id}.html"
    path.write_text(render_html(annotator_id, payload), encoding="utf-8")
    return path


# Template ditaruh di akhir agar bagian Python di atas tetap terbaca. Kurung
# kurawal CSS dan JS digandakan karena berkas ini dilewatkan str.format.
_TEMPLATE = """<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Anotasi SATPAM - {annotator_id}</title>
<style>
  :root {{
    --bg: #ffffff; --fg: #1b1b1b; --muted: #6b6b6b; --line: #dcdcdc;
    --card: #fafafa; --accent: #1f4e79; --warn: #8a5a00; --ok: #1d6b3f;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #16181c; --fg: #e8e8e8; --muted: #9a9a9a; --line: #33363c;
      --card: #1e2126; --accent: #7fb0e0; --warn: #d9a441; --ok: #6fcf97;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5
    system-ui, "Segoe UI", sans-serif; }}
  header {{ position: sticky; top: 0; background: var(--bg); border-bottom: 1px
    solid var(--line); padding: 10px 16px; display: flex; gap: 16px;
    align-items: center; flex-wrap: wrap; z-index: 5; }}
  header b {{ color: var(--accent); }}
  .spacer {{ flex: 1; }}
  main {{ max-width: 860px; margin: 0 auto; padding: 16px; }}
  .card {{ background: var(--card); border: 1px solid var(--line);
    border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
  h2 {{ margin: 0 0 4px; font-size: 20px; }}
  .sub {{ color: var(--muted); font-size: 13px; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  td {{ padding: 4px 6px; border-bottom: 1px solid var(--line);
    vertical-align: top; }}
  td.k {{ color: var(--muted); width: 34%; }}
  td.v {{ font-variant-numeric: tabular-nums; }}
  td.b {{ width: 26%; color: var(--muted); font-size: 13px; }}
  .band-ekstrem, .band-di-atas-kebanyakan {{ color: var(--warn); }}
  .nb {{ font-size: 13px; padding: 3px 0; border-bottom: 1px dotted var(--line);
    display: flex; gap: 8px; }}
  .nb .ar {{ width: 16px; color: var(--muted); }}
  .nb .rel {{ width: 130px; color: var(--muted); }}
  .nb .nid {{ width: 165px; }}
  .nb .w {{ width: 60px; font-variant-numeric: tabular-nums; }}
  .nb .rk {{ flex: 1; color: var(--muted); }}
  button {{ font: inherit; padding: 8px 14px; border: 1px solid var(--line);
    background: var(--bg); color: var(--fg); border-radius: 6px;
    cursor: pointer; }}
  button:hover {{ border-color: var(--accent); }}
  button.sel {{ background: var(--accent); color: #fff; border-color:
    var(--accent); }}
  .row {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
    margin: 10px 0; }}
  .row .lab {{ width: 130px; color: var(--muted); font-size: 14px; }}
  textarea {{ width: 100%; min-height: 60px; font: inherit; padding: 8px;
    border: 1px solid var(--line); border-radius: 6px; background: var(--bg);
    color: var(--fg); }}
  .hint {{ font-size: 13px; color: var(--muted); margin-top: 6px; }}
  .hint.block {{ color: var(--warn); }}
  .pill {{ font-size: 13px; color: var(--muted); }}
  .done {{ color: var(--ok); }}
  .panduan {{ font-size: 14px; }}
  .panduan li {{ margin-bottom: 6px; }}
  .conf {{ display: flex; flex-direction: column; gap: 2px; align-items:
    flex-start; }}
  .conf small {{ color: var(--muted); font-size: 11px; }}
</style>
</head>
<body>
<header>
  <span>Anotator <b>{annotator_id}</b></span>
  <span class="pill" id="maju"></span>
  <span class="pill" id="porsi"></span>
  <span class="spacer"></span>
  <button id="bantuan">Panduan</button>
  <button id="unduh">Unduh CSV</button>
</header>
<main>
  <div class="card panduan" id="panduan">
    <h2>Yang dinilai</h2>
    <p>Untuk tiap node: <b>apakah entitas ini bagian dari jaringan judi online
      atau pinjaman online ilegal?</b></p>
    <p>Mayoritas entitas di graf seperti ini sah. Sampel yang Anda nilai sengaja
      diperkaya kasus sulit, jadi porsinya lebih tinggi daripada keadaan
      sebenarnya, tetapi tetap minoritas.</p>
    <p><b>Aturan yang kalian sepakati sendiri pada ronde kalibrasi:</b> beri
      label 1 bila <b>lebih dari satu variabel saling bebas menunjuk ke arah
      yang sama</b>, dan tidak ada penjelasan wajar yang lebih sederhana untuk
      pola itu. Bila hanya satu variabel yang menonjol sementara yang lain biasa
      saja, jawabannya 0. Rinciannya ada di <b>RUBRIK_KALIBRASI.md</b> bagian
      4.2 dan 4.3.</p>

    <h2>Lima langkah untuk tiap node</h2>
    <ol>
      <li><b>Baca atribut node itu sendiri lebih dulu.</b> Abaikan daftar
        tetangga untuk sementara.</li>
      <li><b>Bandingkan tiap nilai dengan kolom <i>khas</i>.</b> Nilai yang
        setara dengan khas tidak mengatakan apa-apa. Yang perlu diperhatikan
        hanya yang menyimpang jelas.</li>
      <li><b>Baru lihat tetangganya</b>, dan tanyakan apakah ia menambah sesuatu
        yang belum terlihat pada node itu sendiri.</li>
      <li><b>Sebelum menekan Ya, ucapkan dalam satu kalimat apa yang meyakinkan
        Anda.</b> Kalau kalimat itu tidak terbentuk, jawabannya Tidak.</li>
      <li><b>Isi keyakinan untuk jawaban yang Anda pilih</b>, ke arah mana pun.
        Jawaban Tidak yang mantap berhak diberi "Yakin".</li>
    </ol>
    <p>Sekitar 30 sampai 60 detik per node sudah cukup. Kerjakan dalam dua atau
      tiga sesi, jangan sekali duduk.</p>

    <h2>Empat jebakan ronde sebelumnya</h2>
    <ul>
      <li><b>"Masih perlu diteliti" itu jawaban Tidak, bukan Ya.</b> Ragu adalah
        ketiadaan bukti, bukan bukti.</li>
      <li><b>Menarik tidak sama dengan ilegal.</b> Satu atribut yang menonjol,
        berdiri sendiri, belum cukup.</li>
      <li><b>Tetangga yang mencurigakan tidak membuat node ini bersalah.</b>
        Hampir setiap node di graf ini bertetangga dengan sesuatu yang bisa
        dicurigai.</li>
      <li><b>Ya bukan jawaban yang lebih aman.</b> Ya yang keliru sama
        merugikannya dengan Tidak yang keliru.</li>
    </ul>

    <h2>Aturan kerja</h2>
    <ul>
      <li>Baca <b>TIPOLOGI_JUDOL_PINJOL.md</b> lebih dulu, sekitar 15 menit.
        Boleh dibuka lagi kapan saja selama menilai. Ingat, isinya sumber
        pertanyaan yang lebih tepat, bukan daftar periksa: hampir tiap modus
        operandi di sana punya padanan sah yang jauh lebih umum.</li>
      <li>Bekerja sendiri sampai ketiga berkas selesai. Nilai kesepakatan hanya
        bermakna bila ketiganya menilai terpisah.</li>
      <li>Jangan membuka berkas lain di folder data. Halaman ini sudah memuat
        seluruh bukti yang dibutuhkan.</li>
      <li><b>Lewati</b> node yang benar-benar tidak bisa dinilai. Tebakan paksa
        lebih merugikan daripada kekosongan.</li>
    </ul>
    <div class="row"><button id="mulai" class="sel">Mulai</button></div>
  </div>

  <div id="area" hidden>
    <div class="card">
      <h2 id="nid"></h2>
      <div class="sub" id="meta"></div>
      <table id="attr"></table>
      <div class="sub" style="margin-top:14px" id="nbhead"></div>
      <div id="nbs"></div>
    </div>

    <div class="card">
      <div class="row">
        <span class="lab">Bagian jaringan ilegal?</span>
        <button data-lab="0">Tidak (0)</button>
        <button data-lab="1">Ya (1)</button>
        <button id="lewati">Lewati</button>
      </div>
      <div class="hint" style="margin-top:-4px">Ragu berarti Tidak. Ya hanya
        bila Anda bisa mengucapkan alasannya dalam satu kalimat.</div>
      <div class="row" id="confrow"><span class="lab">Keyakinan</span></div>
      <div id="buktibox" hidden>
        <span class="lab" style="display:block;margin-bottom:4px">Apa yang
          meyakinkan Anda? (pilih minimal satu)</span>
        <div class="row" id="buktirow"></div>
      </div>
      <div>
        <span class="lab" style="display:block;margin-bottom:4px">Catatan
          (opsional)</span>
        <textarea id="note" placeholder="Boleh dikosongkan. Isi bila ada yang
tidak tertampung oleh pilihan di atas."></textarea>
        <div class="hint" id="hint"></div>
      </div>
      <div class="row">
        <button id="prev">&larr; Sebelumnya</button>
        <button id="next">Berikutnya &rarr;</button>
        <span class="spacer"></span>
        <span class="pill" id="status"></span>
      </div>
    </div>
  </div>
</main>
<script>
const NODES = {data};
const CONF = {choices};
const COLS = {columns};
const CHIPS = {chips};
const AID = "{annotator_id}";
const KEY = "satpam-anotasi-" + AID;

let jawab = {{}};
try {{ jawab = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{}}
let i = 0;

const $ = (s) => document.querySelector(s);

function simpan() {{
  try {{ localStorage.setItem(KEY, JSON.stringify(jawab)); }} catch (e) {{}}
}}

function cur() {{ return NODES[i]; }}
function ans() {{
  const id = cur().id;
  if (!jawab[id]) jawab[id] = {{label: null, confidence: null, note: "",
    bukti: [], annotated_at: ""}};
  if (!jawab[id].bukti) jawab[id].bukti = [];
  return jawab[id];
}}

function bandClass(b) {{
  return b ? "band-" + b.replace(/ /g, "-") : "";
}}

function gambar() {{
  const n = cur(), a = ans();
  $("#nid").textContent = n.id;
  $("#meta").textContent = n.tipe + " \\u00b7 pertama terlihat " + n.pertama
    + " \\u00b7 terakhir " + n.terakhir;

  $("#attr").innerHTML = n.atribut.map((r) =>
    "<tr><td class='k'>" + r.label + "</td><td class='v'>" + r.value
    + "</td><td class='b " + bandClass(r.band) + "'>" + (r.band || "")
    + "</td><td class='b'>" + (r.typical || "") + "</td></tr>").join("");

  let kh = n.n_tetangga_khas;
  $("#nbhead").textContent = "TETANGGA (" + n.n_tetangga + ")"
    + (kh === null ? "" : "  \\u00b7  khas untuk tipe ini: " + kh);
  $("#nbs").innerHTML = n.tetangga.map((t) =>
    "<div class='nb'><span class='ar'>" + (t.arah === "masuk" ? "\\u2190" : "\\u2192")
    + "</span><span class='rel'>" + t.rel + "</span><span class='nid'>" + t.id
    + "</span><span class='w'>w " + t.w.toFixed(2) + "</span><span class='rk'>"
    + t.ringkas + "</span></div>").join("")
    || "<div class='nb'>(tidak ada tetangga)</div>";

  document.querySelectorAll("[data-lab]").forEach((b) =>
    b.classList.toggle("sel", String(a.label) === b.dataset.lab));
  $("#lewati").classList.toggle("sel", a.label === "lewati");
  document.querySelectorAll("[data-conf]").forEach((b) =>
    b.classList.toggle("sel", String(a.confidence) === b.dataset.conf));
  $("#note").value = a.note || "";

  // Kotak bukti hanya muncul untuk label Ya. Jawaban Tidak tidak perlu
  // dibebani apa pun, karena putusan negatiflah yang ronde pertama nyaris
  // tidak pernah keluar.
  $("#buktibox").hidden = a.label !== "1";
  document.querySelectorAll("[data-bukti]").forEach((b) =>
    b.classList.toggle("sel", a.bukti.indexOf(b.dataset.bukti) >= 0));

  const perlu = a.label === "1" && a.bukti.length === 0;
  $("#hint").textContent = perlu
    ? "Pilih minimal satu bukti sebelum label Ya dapat disimpan."
    : "";
  $("#hint").className = "hint" + (perlu ? " block" : "");
  $("#status").textContent = lengkap(a) ? "tersimpan" : "belum lengkap";
  $("#status").className = "pill" + (lengkap(a) ? " done" : "");
  $("#maju").textContent = "Node " + (i + 1) + " dari " + NODES.length
    + " \\u00b7 selesai " + NODES.filter((x) => lengkap(jawab[x.id])).length;
  porsi();
}}

function lengkap(a) {{
  if (!a) return false;
  if (a.label === "lewati") return true;
  if (a.label !== "0" && a.label !== "1") return false;
  if (a.confidence === null) return false;
  if (a.label === "1" && (!a.bukti || a.bukti.length === 0)) return false;
  return true;
}}

// Porsi label 1 ditampilkan apa adanya, tanpa menyebut arah mana yang keliru.
function porsi() {{
  const isi = Object.values(jawab).filter((a) => a.label === "0" || a.label === "1");
  if (isi.length < 20) {{ $("#porsi").textContent = ""; return; }}
  const satu = isi.filter((a) => a.label === "1").length;
  $("#porsi").textContent = "Porsi jawaban Ya sejauh ini: "
    + Math.round(satu / isi.length * 100) + "% (" + satu + " dari " + isi.length + ")";
}}

function stempel(a) {{
  if (a.label !== null) a.annotated_at = new Date().toISOString().slice(0, 19) + "Z";
}}

$("#confrow").insertAdjacentHTML("beforeend", CONF.map((c) =>
  "<button data-conf='" + c.nilai + "' class='conf'><span>" + c.nama
  + "</span><small>" + c.arti + "</small></button>").join(""));

$("#buktirow").innerHTML = CHIPS.map((c) =>
  "<button data-bukti=\\"" + c + "\\">" + c + "</button>").join("");
document.querySelectorAll("[data-bukti]").forEach((b) => b.onclick = () => {{
  const a = ans(), k = b.dataset.bukti, at = a.bukti.indexOf(k);
  if (at >= 0) a.bukti.splice(at, 1); else a.bukti.push(k);
  stempel(a); simpan(); gambar();
}});

document.querySelectorAll("[data-lab]").forEach((b) => b.onclick = () => {{
  const a = ans(); a.label = b.dataset.lab;
  if (a.label !== "1") a.bukti = [];
  stempel(a); simpan(); gambar();
}});
$("#lewati").onclick = () => {{
  const a = ans(); a.label = "lewati"; a.confidence = null; a.bukti = [];
  stempel(a); simpan(); gambar();
}};
document.querySelectorAll("[data-conf]").forEach((b) => b.onclick = () => {{
  const a = ans(); a.confidence = b.dataset.conf; stempel(a); simpan(); gambar();
}});
$("#note").oninput = () => {{ const a = ans(); a.note = $("#note").value;
  simpan(); gambar(); }};
$("#prev").onclick = () => {{ if (i > 0) {{ i--; gambar(); }} }};
$("#next").onclick = () => {{ if (i < NODES.length - 1) {{ i++; gambar(); }} }};
$("#mulai").onclick = () => {{
  $("#panduan").hidden = true; $("#area").hidden = false; gambar();
}};
// Panduan bisa dibuka lagi kapan saja tanpa kehilangan posisi. Ronde pertama
// memakai lembar Markdown yang panduannya tertinggal ribuan baris di atas.
$("#bantuan").onclick = () => {{
  const buka = $("#panduan").hidden;
  $("#panduan").hidden = !buka;
  if (buka) window.scrollTo(0, 0);
}};

document.onkeydown = (e) => {{
  if (e.target.tagName === "TEXTAREA") return;
  if (e.key === "ArrowRight") $("#next").click();
  if (e.key === "ArrowLeft") $("#prev").click();
}};

function csv() {{
  const esc = (v) => {{
    const s = String(v === null || v === undefined ? "" : v);
    return /[",\\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }};
  const baris = [COLS.join(",")];
  for (const n of NODES) {{
    const a = jawab[n.id];
    if (!a || a.label === "lewati" || a.label === null) continue;
    // Bukti terpilih dan catatan bebas digabung ke satu kolom `note`. Kolom itu
    // bukan bagian kontrak yang dibekukan dan tetap dibuang saat merge, jadi
    // bentuk berkasnya tidak berubah sama sekali.
    const bukti = (a.bukti || []).join("; ");
    const teks = (a.note || "").trim();
    const gabung = bukti && teks ? bukti + " -- " + teks : (bukti || teks);
    baris.push([n.id, AID, a.label, a.confidence, a.annotated_at,
      gabung].map(esc).join(","));
  }}
  return baris.join("\\n") + "\\n";
}}

$("#unduh").onclick = () => {{
  const belum = NODES.filter((x) => !lengkap(jawab[x.id])).length;
  if (belum && !confirm(belum + " node belum lengkap dan tidak akan ikut "
      + "terunduh. Lanjutkan?")) return;
  const b = new Blob([csv()], {{type: "text/csv;charset=utf-8"}});
  const u = URL.createObjectURL(b);
  const a = document.createElement("a");
  a.href = u; a.download = "answers_" + AID + ".csv"; a.click();
  URL.revokeObjectURL(u);
}};
</script>
</body>
</html>
"""
