# Panduan Anotasi Manual

Cara menjalankan anotasi manusia untuk `data/synthetic/seed_42`, kriteria yang
dipakai, dan alasan sebuah ronde kalibrasi disisipkan di antara dua ronde
anotasi. Digabung dari tiga dokumen terpisah agar cara kerjanya mudah diikuti
dari satu tempat.

## 1. Apa yang dihasilkan

| Berkas | Isi |
|---|---|
| `human_annotations.csv` | Satu baris per penilaian: `node_id`, `annotator_id`, `label`, `confidence`, `annotated_at`. Kolomnya didefinisikan di `generator/schema.py`. |
| `human_annotations_majority.csv` | Label suara terbanyak per node, turunan, bukan berkas kontrak. |
| `agreement_report.md` | Kesepakatan antar-anotator (Fleiss' kappa, Cohen's kappa) per ronde. |
| `sample_manifest_merged.json` | Urutan node bila anotasi diambil dari lebih dari satu ronde. |

## 2. Cara menjalankan

```bash
# siapkan paket kerja untuk 3 anotator
python -m annotation.build sample --seed 42 --subdir anotasi_ronde1

# setelah ketiga anotator mengisi answers_A1/A2/A3.csv, gabungkan
python -m annotation.build merge --seed 42 --subdir anotasi_ronde1
```

Untuk ronde lanjutan, beri nama folder baru dan kecualikan node yang sudah
dianotasi supaya tidak dinilai dua kali:

```bash
python -m annotation.build sample --seed 42 --subdir anotasi_ronde2 \
    --exclude-annotated --sampling-seed 2027

# gabungkan beberapa ronde sekaligus jadi satu human_annotations.csv
python -m annotation.build merge --seed 42 --rounds anotasi_ronde1 anotasi_ronde2
```

Menjalankan `merge --subdir anotasi_ronde2` saja (tanpa `--rounds`) akan
menulis ulang `human_annotations.csv` hanya dengan ronde kedua dan menghapus
hasil ronde pertama. Selalu pakai `--rounds` begitu ada lebih dari satu ronde.

## 3. Cara sampel dipilih

Sampel dipilih berstrata, bukan acak murni, supaya kasus sulit ikut terwakili:

| Strata | Membidik |
|---|---|
| S1 | node yang rule engine paling yakin positif |
| S2 | node yang rule engine paling yakin negatif |
| S3 | node tepat di ambang batas level |
| S4 | jejak sendiri tipis, tapi lingkungannya bermasalah |
| S5 | jejak sendiri kuat tapi lingkungannya renggang |
| S6 | jangkar acak berstrata tipe node |

Pemilih hanya memakai kolom teramati (atribut node, struktur graph, skor rule
engine), tidak pernah kolom label. Diuji otomatis lewat
`tests/test_annotation_hides_answers.py`.

## 4. Yang tidak dilihat anotator

| Disembunyikan | Alasan |
|---|---|
| `rule_score`, `rule_level`, `triggered_rules` | Kalau ditampilkan, anotasi berubah menjadi persetujuan atas rule engine |
| Kolom `gt_*` | Itu jawabannya |
| Nama strata | Untuk sebagian node, nama strata setara petunjuk jawaban |
| Urutan bergilir strata | Urutan itu bisa dipakai menebak strata dari posisi. Urutan tampilan diacak berbeda per anotator |

## 5. Membaca laporan kesepakatan

**Fleiss' kappa** untuk tiga anotator sekaligus. **Cohen's kappa** berpasangan
untuk melihat apakah satu orang menyimpang dari dua lainnya. Pita tafsir
mengikuti Landis dan Koch (1977): di bawah 0 lebih buruk dari kebetulan,
0 sampai 0,20 lemah, 0,21 sampai 0,40 lumayan, 0,41 sampai 0,60 sedang, 0,61
sampai 0,80 kuat, di atas 0,80 hampir sempurna.

| Temuan | Tindakan |
|---|---|
| Kappa tinggi di strata mudah, jatuh di strata ambigu | Wajar. Laporkan apa adanya |
| Kappa rendah merata di semua strata | Definisi tugasnya belum jelas. Diskusikan node yang paling banyak diperdebatkan, sepakati kriteria, lalu anotasi ulang |
| Satu Cohen's kappa jauh lebih rendah dari dua lainnya | Satu anotator memahami tugas berbeda. Bicarakan sebelum menggabungkan |

Jangan menyunting jawaban supaya kappa naik. Kalau anotasi perlu diulang,
ulangi seluruhnya dan catat bahwa ada ronde tambahan beserta alasannya.

## 6. Ronde kalibrasi: kenapa dan bagaimana

Ronde pertama pada seed 42 menghasilkan Fleiss' kappa 0,177, tergolong lemah.
Dari 150 node, 121 dilabeli positif oleh suara terbanyak padahal yang benar
hanya 16. Penyebabnya bukan kurang usaha: setiap kali ketiga anotator sepakat
sebuah node bersih, mereka nyaris selalu benar, hanya saja putusan seperti itu
jarang keluar. Ambangnya yang terlalu longgar, bukan kemampuannya yang kurang.

Untuk memperbaikinya, disisipkan satu ronde kalibrasi sebelum ronde kedua:
ketiga anotator menilai 20 node yang sama, lalu berdiskusi dan menuliskan
kriteria yang menyelesaikan setiap perbedaan pendapat.

```bash
python -m annotation.build sample --seed 42 --total 20 \
    --subdir kalibrasi --exclude-annotated --sampling-seed 7

# setelah ketiganya menilai, bandingkan jawaban side-by-side
python -m annotation.build debrief --seed 42 --subdir kalibrasi
```

Hasilnya: Fleiss' kappa naik ke 0,542 pada ronde kedua, dengan anotator yang
sama dan node yang berbeda. Kalibrasi menaikkan kesepakatan; itu tidak
otomatis berarti menaikkan kebenaran, karena tiga orang tetap bisa sepakat
pada ambang yang sama-sama longgar. Kesepakatan dan kebenaran adalah dua hal
yang perlu diperiksa terpisah.

### Definisi operasional hasil kalibrasi

Sebuah node diberi label 1 bila lebih dari satu variabel yang saling bebas
menunjuk ke arah yang sama, dan tidak ada penjelasan sederhana yang lebih
masuk akal untuk pola itu. Bila hanya satu variabel yang menonjol sementara
yang lain biasa saja, jawabannya 0.

**Yang dihitung sebagai bukti**, tidak satu pun cukup sendirian:

- ketidakcocokan pada profil node itu sendiri, misalnya transaksi sedikit
  tetapi nominal rata-rata jauh di atas kebiasaan tipenya
- ketidakcocokan serupa pada tetangga dengan tautan kuat
- pernah disebut laporan, hanya menguatkan bukti lain
- umur sangat muda yang tidak sepadan dengan aktivitasnya

**Yang tidak cukup jadi bukti**, ini bagian paling menentukan karena ronde
pertama gagal justru di sini:

- satu variabel menonjol tanpa memeriksa variabel lain
- satu laporan yang berdiri sendiri
- tetangga mencurigakan dengan tautan lemah
- tetangga mencurigakan yang umurnya sudah lama, karena node yang lama
  bertahan lebih mungkin sah

### Perubahan pada instrumen ronde kedua

| Perubahan | Alasan |
|---|---|
| Label 1 baru bisa disimpan setelah minimal satu kategori bukti dipilih | Memaksa bukti dipilih dulu sebelum diputuskan |
| Keyakinan hanya empat pilihan berpatokan kata, bukan angka bebas | Ronde pertama memakai angka bebas sebagai kadar kecurigaan, jadi makin yakin justru makin salah |
| Tiap atribut diberi nilai khas tipenya sebagai pembanding | Tanpa pembanding, semua angka terbaca sebagai indikator risiko |
| Porsi jawaban Ya milik sendiri ditampilkan setelah 20 node | Satu anotator melabeli 91 persen positif tanpa menyadarinya |

## 7. Tipologi modus operandi

Bahan ini dipakai untuk melatih anotator mengenali pola yang terdokumentasi,
bukan sebagai daftar periksa. Hampir setiap pola di bawah punya padanan yang
sah dan jauh lebih umum, jadi pertanyaannya bukan "apakah pola ini ada"
melainkan "apakah ada penjelasan sah yang lebih sederhana".

**Judi online**

| Yang dilaporkan | Yang mirip tetapi sah |
|---|---|
| Deposit lewat QRIS berfrekuensi tinggi dan bernominal kecil | Ciri usaha ritel dan warung pada umumnya |
| Rekening penampung dari jual-beli rekening atau rekening lama diambil alih | Rekening baru aktif atau dipakai lagi punya banyak sebab wajar |
| Domain dirotasi berkala, domain lama mengalihkan ke domain baru | Pengalihan domain juga praktik web biasa: ganti nama, migrasi situs |
| Satu nomor kontak dipakai beberapa domain milik operator yang sama | Satu perusahaan atau agensi lazim mengelola banyak situs dengan satu kontak |
| Promosi disebar lewat banyak akun media sosial otomatis | Kampanye pemasaran sah juga memakai banyak akun dan otomatisasi |

**Keterkaitan dengan pinjaman online ilegal**

Operator di kedua ekosistem kadang berbagi infrastruktur (rekening pinjam
nama, distributor aplikasi, jaringan promosi), dan sebagian korban judi online
kemudian menjadi korban pinjaman online ilegal. Catatan penting: berbagi
penyedia layanan tidak otomatis berarti satu operator, dan lembaga berwenang
belum menemukan aliran dana langsung antara kedua ekosistem. Yang
terdokumentasi hanya infrastruktur dan korban bersama.

**Benang merahnya**: yang membedakan hampir tidak pernah satu pola saja,
melainkan beberapa sinyal yang saling bebas menunjuk arah yang sama, dan
tidak adanya penjelasan sah yang lebih sederhana.

## 8. Aturan yang berlaku sepanjang proses

1. Anotator tidak boleh membuka `nodes.csv`, `weak_labels.csv`, atau berkas
   apa pun yang memuat kolom `gt_*` maupun `rule_score`.
2. `sample_manifest.json` hanya untuk koordinator karena memuat nama strata,
   yang untuk sebagian node setara memberi jawaban.
3. Anotasi dikerjakan mandiri sampai seluruh berkas jawaban selesai, tanpa
   diskusi dan tanpa saling melihat, kecuali pada ronde kalibrasi yang memang
   dirancang untuk didiskusikan setelah penilaian mandiri selesai.
4. Node ronde kalibrasi tidak masuk `human_annotations.csv`.
