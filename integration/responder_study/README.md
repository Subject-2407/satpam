# Studi Responden

Materi statis untuk membandingkan dua bentuk penjelasan risiko: rule-based
(daftar aturan yang menyala) dan evidence subgraph GNNExplainer.

Studi ini tidak menunggu dashboard. Materinya dibangun langsung dari berkas
di disk, tanpa API maupun Docker, sehingga celah mount Docker pada endpoint
`criticalSubgraph` (lihat `integration/README.md`) tidak relevan di sini.

---

## Berkas

| Berkas | Untuk | Catatan |
|---|---|---|
| `materi_studi.html` | **Varian A**, separuh responden | 1,46 MB, satu berkas, buka langsung di browser |
| `materi_studi_varian_b.html` | **Varian B**, separuh lainnya | Cermin penuh varian A |
| `kuesioner_google_form.md` | Pertanyaan siap disalin ke Google Form | Jawaban dikumpulkan lewat Form, bukan kertas |
| `lembar_penilaian.csv` | Bentuk data untuk analisis; tempat ekspor Form disusun ulang | **Wajib di-commit** begitu terisi |
| `kunci_koordinator.md` | Kunci panel A/B + terjemahan istilah + catatan tafsir | **Jangan diperlihatkan responden** |
| `build_materi.py` | Membangun ulang semuanya | |

Kedua HTML di-gitignore: ukurannya besar dan dapat dibangkitkan ulang persis.
`lembar_penilaian.csv` tidak di-gitignore.

## HTML ini murni lembar soal

Tidak ada kode responden, tanggal, penanda varian, kolom waktu, maupun kolom
komentar di halaman. Semua itu ada di Google Form. Yang dicetak hanya keenam
kasus dan pilihan nilainya.

> **Satu hal perlu diperhatikan:** rancangan awal meminta waktu penyelesaian
> ikut diukur, dan Google Form hanya mencatat waktu kirim, bukan durasi.
> Koordinator perlu mencatat manual per sesi, atau menambahkan pertanyaan
> "jam mulai" di awal Form.

## Membangun ulang

```bash
# Prasyarat: artefak GNNExplainer keenam kasus harus ada lebih dulu.
# Berkas kontrak ditulis ulang tiap jalan, jadi keenam node WAJIB disebut sekaligus.
python experiments/explain.py --seed 42 --nodes \
    domain_00007 ewallet_00030 domain_00001 social_account_00004 \
    bank_account_00013 victim_00056

python integration/responder_study/build_materi.py
```

Sumber yang dibaca:

| Panel | Sumber |
|---|---|
| Rule-based | `data/synthetic/seed_42/weak_labels.csv` + bobot dari `rules.scoring.RULES` |
| Evidence subgraph | tabel relasi di `experiments/results/explanations/{node}.md` |

Rule engine v1 di `integration/backend/` tidak dipakai: ia buta terhadap skema
data saat ini dan selalu mengembalikan skor 0 dengan `triggeredRules` kosong
(lihat `integration/README.md`).

### Kenapa gambarnya digambar ulang, bukan memakai `.png` dari eksperimen

Berkas `explanations/*.png` isinya benar, tapi matplotlib mencetak teks ke
dalam piksel gambar, dan teks itu memuat:

- judul `Evidence subgraph, victim_00056`, yaitu `node_id` mentah yang justru
  sudah disembunyikan dari HTML
- keterangan `tebal garis = kontribusi terhadap skor (GNNExplainer)`, yang
  menyebut nama metodenya sehingga responden langsung tahu panel mana yang
  "AI" dan seluruh blinding batal
- label simpul dan sisi berupa `social_account_01405` dan `transferred_to`,
  yaitu jargon yang sudah diterjemahkan di tabelnya

Kebocoran ini mustahil tertangkap pemeriksaan teks HTML, karena teksnya ada di
dalam gambar, bukan di markup. Ia ketemu saat memeriksa `draw_case()` di
`experiments/explain.py`.

Yang digambar ulang hanya tampilannya: simpul dilabeli `#00030` saja dan
diwarnai per jenis dengan legenda di bawah gambar, entitas yang dibahas merah
dan lebih besar, label sisi bahasa Indonesia, tanpa judul dan tanpa nama
metode. Isi penjelasannya (sisi mana yang penting, seberapa besar
kontribusinya) tetap sepenuhnya keluaran GNNExplainer, dibaca apa adanya dari
tabel di `.md`. Berkas `.png` dari eksperimen tetap ada dan tetap dipakai
sebagai artefak teknis untuk lampiran laporan.

---

## Menjalankan sesi

1. Buat **dua Google Form terpisah** dari `kuesioner_google_form.md`, satu
   untuk varian A, satu untuk varian B. Arti "Penjelasan A" berbeda di antara
   kedua varian, jadi nilainya tidak boleh tercampur dalam satu kolom.
2. Bagikan **varian A ke separuh responden, varian B ke separuh lainnya**,
   tiap orang dengan tautan Form yang cocok. Kalau jumlahnya ganjil, catat
   pembagiannya, jangan diseragamkan.
3. Responden membaca HTML di layar dan mengisi Form. Bisa juga dicetak dulu (CSS
   cetak sudah disiapkan: A4, satu kasus per halaman).
4. Ekspor Form, susun ulang ke bentuk `lembar_penilaian.csv` memakai
   `kunci_koordinator.md`. Satu kasus menjadi dua baris, satu per metode.
5. Jangan menyebut berapa kasus yang benar/salah sebelum sesi selesai.

Kolom CSV: `responden_id, varian, kasus, metode, kejelasan, kepercayaan,
kecukupan, komentar`.

`metode` dan `varian` adalah tambahan di luar rancangan awal, dan keduanya
mencegah kegagalan data yang tidak bergejala. Tanpa `metode`, tidak ada cara
tahu nilai 4 itu untuk rule-based atau subgraph, sehingga perbandingannya
tidak dapat dihitung sama sekali. Tanpa `varian`, kunci A/B yang salah
diterapkan akan menukar seluruh nilai satu responden tanpa tanda apa pun.

---

## Enam kasus

Lima pertama dipilih berdasarkan selisih skor terbesar antara model dan
rule-based (lihat `experiments/results/main_results_raw.csv`), karena di
situlah perbandingan dua bentuk penjelasan menjadi bermakna. Kasus keenam
adalah kontrol negatif.

| # | Kasus | Jenis | Rule-based | Kenapa dipilih |
|---:|---|---|---|---|
| 1 | `domain_00007` | domain | 100 / critical | Kedua sistem sama-sama yakin, jangkar pembanding |
| 2 | `ewallet_00030` | ewallet | 100 / critical | Sama seperti di atas |
| 3 | `domain_00001` | domain | 35 / medium | Dilewatkan rule-based, ditangkap model lewat rantai rotasi domain |
| 4 | `social_account_00004` | social_account | 35 / medium | Dilewatkan rule-based, ditangkap model lewat nomor kontak bersama |
| 5 | `bank_account_00013` | bank_account | 55 / medium | Selisih skor besar |
| 6 | `victim_00056` | victim | 100 / critical | Kontrol negatif, `gt_illicit = 0`, ia korban |

---

## Tujuh hal yang menjaga studi ini tetap sah

1. **Label panel netral.** "Penjelasan A" dan "Penjelasan B", bukan "rule-based"
   dan "GNN". Mengacak posisi tapi tetap memberi label metode hampir tidak
   mengontrol bias, karena responden akan condong ke apa pun yang berlabel "AI".

2. **Posisi kiri/kanan tetap, tidak diacak saat dibuka.** Kalau diacak per
   muat, tiap responden melihat tata letak berbeda dan jawabannya tidak dapat
   dibandingkan. Komposisi varian A seimbang 3 lawan 3, dan pola urutannya
   sengaja tidak berselang-seling rapi, karena pola seperti "R, G, R, G, ..."
   mudah ditebak, dan begitu responden menebak satu kasus ia tahu semuanya.

3. **Skor angka dibuang dari kedua panel.** Kalau ditampilkan, responden akan
   membandingkan "0,9999" lawan "35/100" dan menilai angkanya, bukan
   penjelasannya. Baris skor di berkas `.md` disaring keluar secara khusus.

4. **Kekuatan bukti digambar sebagai batang, dengan gaya sama di kedua panel.**
   Panel subgraph punya angka kontribusi. Kalau panel rule-based hanya diberi
   daftar nama tanpa indikator kekuatan, perbandingannya tidak adil. Batang
   juga jauh lebih terbaca bagi orang awam daripada angka desimal.

5. **Jenis entitas dicantumkan di kepala kasus** (misalnya "E-wallet / QRIS
   #00030"). Keputusan ini sempat kebalikannya, lihat catatan tafsir di bawah,
   karena ia mengubah apa yang bisa diukur dari kasus 6.

6. **Gambar digambar ulang, bukan memakai `explanations/*.png`.** Gambar dari
   eksperimen mencetak teks ke dalam pikselnya, dan teks itu menyebut nama
   metodenya (`GNNExplainer`) serta `node_id` mentah, sehingga blinding butir 1
   batal total. Isi penjelasannya tetap sama, hanya tampilannya yang dibuat
   versi awam. Lihat catatan di bawah.

7. **Kunci A/B di luar HTML.** Kalau ikut di dalam berkas yang dibuka responden,
   ia dapat ditemukan hanya dengan menggulir ke bawah.

Diverifikasi atas kedua berkas keluaran: tidak ada `gt_*`, tidak ada kata
"rule-based" atau "GNN", tidak ada `mlScore` maupun skor 0–100, tidak ada
`node_id` mentah, tidak ada istilah "node"/"graph"/`transferred_to` dan
sebangsanya, dan struktur HTML-nya lolos parser tanpa tag menggantung.

## Bahasa disederhanakan untuk responden awam

Responden adalah mahasiswa, bukan analis. Seluruh istilah teknis diterjemahkan
lewat tiga tabel di `build_materi.py` (`ENTITY_LABEL`, `RELATION_LABEL`,
`RULE_PLAIN`), dan padanan teknisnya didaftar lengkap di `kunci_koordinator.md`
supaya hasilnya tetap dapat ditelusuri balik ke data.

| Di data | Di materi responden |
|---|---|
| `social_account_00006` | Akun media sosial #00006 |
| `transferred_to` | mengirim uang ke |
| `redirects_to` | mengalihkan pengunjung ke |
| R-X2 "Node sangat sentral pada graph" | "Terhubung ke sangat banyak pihak lain dibanding rata-rata" |
| R-G1 "Kanal QRIS dengan frekuensi tinggi dan nominal kecil" | "Sering menerima pembayaran QRIS bernilai kecil, pola khas setoran judi online" |

Terjemahan ditaruh di `build_materi.py`, bukan dengan mengubah
`rules/scoring.py`, karena judul aturan di berkas itu dipakai di tempat lain
juga. Bila ada aturan baru ditambahkan ke `rules/scoring.py`, judul teknis
aslinya tetap dipakai sebagai cadangan dan skripnya mencetak peringatan,
supaya aturan itu tidak hilang diam-diam dari materi.

Pengantarnya juga menjelaskan konteksnya: bahwa ini sistem pemetaan jaringan
judol dan pinjol ilegal, bahwa pelaku beroperasi sebagai jaringan yang saling
terhubung dan berpindah alamat saat diblokir, dan karena itu yang perlu
dilihat adalah jaringannya, bukan satu situs per satu situs.

Isi pengantar, berurutan:

1. **Ringkasan satu kalimat** tentang apa yang akan dilakukan.
2. **Konteks** sistem pemetaan jaringan judol dan pinjol ilegal.
3. **Definisi "entitas"** plus tabel kedelapan jenisnya dalam bahasa
   sehari-hari, karena tanpa ini judul kasus "E-wallet / QRIS #00030" tidak
   bermakna.
4. **Langkah pengerjaan** dalam empat butir.
5. **Contoh cara mengerjakan**, kasus tiruan dengan dua panel mini
   berdampingan, ditandai jelas "bukan bagian penilaian", lengkap dengan
   petunjuk apa yang perlu diperhatikan.
6. **Empat hal yang perlu diketahui** sebelum mulai.

Kolom kekuatan bukti diberi judul "Pengaruh ke penilaian" di kedua panel,
menggantikan "Seberapa berat" dan "Seberapa menentukan" yang ambigu. Di bawah
tiap tabel ada satu baris penjelas: semakin panjang batangnya, semakin besar
andil hal itu dalam membuat sistem menilai entitas berisiko.

Keterangan gambar menyebut eksplisit bahwa **bulatan merah paling besar adalah
entitas yang sedang dibahas**, warna lain menunjukkan jenisnya (ada legenda di
dalam gambar), dan garis lebih tebal berarti pengaruhnya lebih besar.

---

## Tiga catatan yang mempengaruhi tafsir hasil

**1. Jenis entitas kini ditampilkan, dan itu menggeser apa yang kasus 6 ukur.**

Versi sebelumnya menyembunyikan jenis entitas (judul hanya "Entitas #00056")
supaya kasus 6 tidak langsung terbaca sebagai korban. Diubah karena tanpa
jenisnya, "Entitas #00030" tidak bermakna apa pun bagi orang awam, dan studi
ini jadi mengukur kemampuan menerka alih-alih kejelasan penjelasan.

Konsekuensinya perlu dicatat: pada kasus 6, responden sudah tahu entitas itu
korban pelapor sebelum membaca apa pun. Yang diukur bergeser, dan versi
barunya justru lebih dekat ke kenyataan, karena analis sungguhan juga melihat
jenis entitas di dashboard-nya.

Pertanyaan yang sekarang diamati: meski sudah tahu ini korban, apakah daftar
temuan rule-based tetap terbaca meyakinkan sebagai bukti pelaku? Panel
rule-based tidak memuat satu pun nama entitas, ia hanya menyodorkan lima
temuan umum, salah satunya "Menerima setoran uang dari beberapa korban yang
berbeda", yang untuk seorang korban justru terbalik artinya. Panel subgraph
sebaliknya menulis dasarnya sebagai kalimat terbaca, "Korban pelapor #00056
mengirim uang ke E-wallet / QRIS #00030", dan gambarnya memperlihatkan hanya
satu panah tebal keluar dari bulatan merah.

Kalau responden memberi nilai kepercayaan tinggi pada panel rule-based di
kasus ini, itu temuan kuat untuk bagian etika: penjelasan yang tidak menyebut
entitas apa pun tetap terasa meyakinkan walau menuding orang yang salah.

**2. Kasus 6 terhubung ke kasus 2.** Relasi teratas
`victim_00056 -> transferred_to -> ewallet_00030` (kontribusi 1,000) menunjuk
ke entitas kasus nomor 2. Responden yang mengerjakan berurutan bisa
mengaitkan keduanya. Ini kaitan nyata di data, bukan artefak, tapi catat bila
terjadi.

**3. Lima kasus pertama seluruhnya `gt_illicit = 1`.** Kalau responden
menyimpulkan semua kasus memang pelaku, nilai kepercayaan akan naik semu.

Satu temuan yang sudah terlihat sebelum sesi dijalankan dan layak dicatat:
kasus 3 dan kasus 4 punya keluaran rule-based yang persis identik, sama-sama
35/medium dengan `R-G4;R-G5`, padahal jenis entitas dan bukti subgraph-nya
berbeda total. Rule-based tidak dapat membedakan dua entitas yang oleh model
dinilai lewat jalur bukti yang sama sekali lain.
