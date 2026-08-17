# Kunci Koordinator, Studi Responden SATPAM

> **Jangan diperlihatkan kepada responden.** Berkas ini sengaja dipisah
> dari HTML materi: kalau kuncinya ikut di dalam berkas yang dibuka
> responden, ia dapat ditemukan hanya dengan menggulir ke bawah.

Seed data: 42. Enam kasus, urutan tetap di kedua varian.

## Pemetaan panel ke metode

| # | Node | Entitas di HTML | Varian A: A | Varian A: B | Varian B: A | Varian B: B |
|---:|---|---|---|---|---|---|
| 1 | `domain_00007` | Entitas #00007 | rule-based | evidence subgraph | evidence subgraph | rule-based |
| 2 | `ewallet_00030` | Entitas #00030 | evidence subgraph | rule-based | rule-based | evidence subgraph |
| 3 | `domain_00001` | Entitas #00001 | evidence subgraph | rule-based | rule-based | evidence subgraph |
| 4 | `social_account_00004` | Entitas #00004 | rule-based | evidence subgraph | evidence subgraph | rule-based |
| 5 | `bank_account_00013` | Entitas #00013 | evidence subgraph | rule-based | rule-based | evidence subgraph |
| 6 | `victim_00056` | Entitas #00056 | rule-based | evidence subgraph | evidence subgraph | rule-based |

Varian B adalah cermin penuh varian A. Bagikan kedua varian ke separuh
responden masing-masing agar efek posisi kiri/kanan terhapus di tingkat
agregat. Buat dua Google Form terpisah, karena arti "Penjelasan A" berbeda
antara kedua varian, jadi nilainya tidak boleh tercampur dalam satu kolom.

## Kasus 6 adalah kontrol negatif: `victim_00056`

Node ini ber-`gt_illicit = 0`, artinya ia korban, bukan pelaku. Kedua sistem
tetap memberinya skor maksimum (rule-based 100/critical, R-GCN 1,0000).

Alasan model menandainya hanya satu relasi: `transferred_to` ke
`ewallet_00030` dengan kontribusi 1,000, dan `ewallet_00030` itu justru
kasus nomor 2 di studi ini. Sebelas relasi sisanya jatuh rata di sekitar
0,30, artinya praktis tidak menyumbang apa pun.

Nilainya untuk bagian etika: risiko positif palsu atas korban kini punya
satu kasus konkret yang bisa ditunjukkan secara empiris.

## Kepala kasus menyebutkan jenis entitas, konsekuensinya untuk kasus 6

Judul kasus 6 di HTML berbunyi "Korban pelapor #00056", sehingga responden
sudah tahu ini korban sebelum membaca satu penjelasan pun. Ini keputusan
yang sengaja diubah dari rancangan awal yang menyembunyikan jenisnya, karena
tanpa jenis entitas, "Entitas #00056" tidak bermakna apa pun bagi orang awam,
dan studi ini jadi mengukur kemampuan menerka, bukan kejelasan penjelasan.
Ini juga lebih dekat ke kenyataan: seorang analis sungguhan di dashboard
juga langsung melihat jenis entitas.

**Konsekuensinya, pertanyaan yang diukur bergeser.** Semula: "apakah
penjelasan membuat responden MENYADARI ini korban?" Sekarang, karena
jenisnya sudah diketahui lebih dulu: "meski sudah tahu ini korban, apakah
salah satu penjelasan tetap terbaca meyakinkan seolah bukti pelaku,
sementara yang lain justru terasa janggal atau tidak cocok dengan fakta
bahwa entitas ini korban?"

**Yang layak diamati dari jawaban responden**, dengan pertanyaan baru itu:

- Panel rule-based menyodorkan daftar temuan generik tanpa nama pihak lain,
  salah satunya "Menerima setoran uang dari beberapa korban yang berbeda"
  (R-G8). Dibaca oleh seseorang yang sudah tahu subjeknya korban, kalimat
  itu janggal, karena bagaimana bisa korban "menerima setoran dari korban
  lain"? Pertanyaannya: apakah responden menangkap kejanggalan ini, atau
  tetap memberi nilai kepercayaan tinggi karena kalimatnya terdengar teknis
  dan meyakinkan?
- Panel subgraph menulis relasi teratasnya sebagai kalimat konkret: "Korban
  pelapor #00056 mengirim uang ke E-wallet #00030", satu transfer, dan itu
  memang persis pola korban penipuan (mengirim uang sekali ke rekening
  pelaku). Pertanyaannya: apakah pola bukti yang tipis ini (1 relasi kuat,
  11 relasi lemah di sekitar 0,30) membuat responden menilai
  kepercayaannya lebih rendah dibanding rule-based, sesuatu yang seharusnya
  terjadi kalau subgraph benar-benar membantu analis mengenali bukti yang
  tipis?

Kalau nilai kepercayaan panel rule-based tetap tinggi meski responden sudah
tahu ini korban, itu justru temuan penting untuk bagian etika: bukti bahwa
penjelasan berbasis aturan bisa terdengar meyakinkan walau menuduh pihak
yang salah. Ini alasan kuat kenapa keputusan akhir wajib tetap di tangan
manusia, bukan otomatis dari skor.

## Dua catatan lain yang mempengaruhi tafsir hasil

1. **Lima kasus pertama seluruhnya `gt_illicit = 1`.** Kalau responden
   menyimpulkan bahwa semua kasus memang pelaku, nilai kepercayaan akan
   naik semu. Jangan menyebut proporsi kasus benar/salah sebelum sesi
   selesai.
2. **Kasus 3 (`domain_00001`) dan kasus 4 (`social_account_00004`) punya
   keluaran rule-based yang persis identik**, sama-sama dua temuan yang
   sama, padahal jenis entitas dan bukti subgraph-nya berbeda total. Ini
   bahan kuat: rule-based tidak dapat membedakan dua entitas yang oleh
   model dinilai lewat jalur bukti yang sama sekali lain.

## Terjemahan istilah, untuk menelusuri balik ke data

Materi responden memakai bahasa awam. Padanan teknisnya:

| Di HTML | Di data |
|---|---|
| Situs web #NNNNN | `domain_NNNNN` |
| Nomor telepon #NNNNN | `phone_NNNNN` |
| Rekening bank #NNNNN | `bank_account_NNNNN` |
| E-wallet / QRIS #NNNNN | `ewallet_NNNNN` |
| Aplikasi HP #NNNNN | `apk_NNNNN` |
| Akun media sosial #NNNNN | `social_account_NNNNN` |
| Laporan warga #NNNNN | `report_NNNNN` |
| Korban pelapor #NNNNN | `victim_NNNNN` |

| Di HTML | rel_type (lihat `generator/schema.py`) |
|---|---|
| mempromosikan | `promotes` |
| memakai nomor kontak | `contacts` |
| memakai rekening | `uses_account` |
| mengirim uang ke | `transferred_to` |
| menyebut | `mentions` |
| melaporkan lewat | `reported` |
| menyebarkan aplikasi | `linked_to_apk` |
| mengalihkan pengunjung ke | `redirects_to` |

| Di HTML | Kode aturan |
|---|---|
| Sering menerima pembayaran QRIS bernilai kecil, pola khas setoran judi online | `R-G1` |
| Rekening lama yang tiba-tiba aktif kembali, atau uang dipindah berlapis-lapis sehingga asalnya sulit dilacak | `R-G2` |
| Satu akun pembayaran QRIS dipakai bergantian oleh beberapa pihak berbeda | `R-G3` |
| Termasuk dalam rantai situs yang saling mengalihkan pengunjung, cara pelaku pindah alamat setiap kali diblokir | `R-G4` |
| Dipromosikan serentak oleh banyak akun media sosial | `R-G5` |
| Satu nomor telepon yang sama dipakai untuk beberapa situs sekaligus | `R-G6` |
| Menjadi penghubung antara dua kelompok situs yang tampak tidak berkaitan | `R-G7` |
| Menerima setoran uang dari beberapa korban yang berbeda | `R-G8` |
| Banyak disebut di laporan yang masuk dari warga | `R-X1` |
| Terhubung ke sangat banyak pihak lain dibanding rata-rata | `R-X2` |

Batang "seberapa berat" pada panel rule-based adalah bobot aturan dibagi
bobot tertinggi (25). Batang pada panel subgraph adalah kontribusi edge
mask GNNExplainer, sudah ternormalkan dari 0 sampai 1 di `experiments/explain.py`.
Keduanya digambar dengan gaya sama supaya perbandingannya adil.
