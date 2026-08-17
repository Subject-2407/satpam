# Pertanyaan Google Form: Studi Responden SATPAM

Salin ke Google Form. Buat dua Form terpisah (atau dua tautan), satu untuk
varian A dan satu untuk varian B. Nilai dari kedua varian tidak boleh
tercampur dalam satu kolom karena arti "Penjelasan A" berbeda di antara
keduanya. Lihat `kunci_koordinator.md`.

## Bagian pembuka

- **Kode responden**, jawaban pendek. Cukup inisial dan angka, jangan nama.
- Sisipkan tautan berkas materi (`materi_studi.html` untuk Form varian A,
  `materi_studi_varian_b.html` untuk Form varian B).

## Per kasus (ulangi untuk kasus 1 sampai 6)

Untuk tiap kasus, enam pertanyaan skala linear 1 sampai 5 (1 = sangat kurang,
5 = sangat baik):

| Pertanyaan | Untuk |
|---|---|
| Kasus N, Penjelasan A: seberapa mudah dipahami? | kejelasan |
| Kasus N, Penjelasan A: seberapa meyakinkan? | kepercayaan |
| Kasus N, Penjelasan A: seberapa cukup informasinya? | kecukupan |
| Kasus N, Penjelasan B: seberapa mudah dipahami? | kejelasan |
| Kasus N, Penjelasan B: seberapa meyakinkan? | kepercayaan |
| Kasus N, Penjelasan B: seberapa cukup informasinya? | kecukupan |

Tambahkan satu paragraf opsional per kasus: "Ada yang membingungkan atau
justru sangat membantu di kasus ini?" untuk kutipan kualitatif singkat.

## Bagian penutup

- Paragraf opsional: "Masukan umum di luar keenam kasus?"

## Waktu penyelesaian, jangan sampai terlewat

Rancangan studi ini meminta waktu penyelesaian ikut diukur. Google Form hanya
mencatat waktu kirim, bukan durasi pengerjaan. Pilih salah satu:

1. Koordinator mencatat waktu mulai dan selesai tiap responden secara
   manual (paling sederhana bila sesinya diawasi).
2. Tambahkan pertanyaan "jam mulai" di awal Form dan bandingkan dengan
   waktu kirim otomatis.

Bila akhirnya tidak diukur, catat itu sebagai keterbatasan supaya tidak
hilang tanpa disebut.

## Menyalin hasil untuk analisis

Ekspor Form ke CSV, lalu susun ulang ke bentuk `lembar_penilaian.csv`:
kolom `responden_id, varian, kasus, metode, kejelasan, kepercayaan,
kecukupan, komentar`. Satu kasus menjadi dua baris, satu untuk
`rule_based`, satu untuk `gnn`, menurut kunci di `kunci_koordinator.md`.
