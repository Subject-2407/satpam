# Fixture — data palsu untuk pengembangan

> **`fake_annotations.csv` DILARANG dipakai untuk hasil resmi.**
>
> Label dan `confidence_mean` di berkas itu **dikarang**, tidak berasal dari
> anotator mana pun, dan sengaja tidak berkorelasi dengan `gt_illicit`. Angka
> apa pun yang dihasilkan darinya tidak berarti apa-apa selain "kodenya jalan".

## Untuk apa berkas ini ada

Modul `models/feedback.py` dan `experiments/ablation.py` harus bisa ditulis dan
diuji **sebelum** `human_annotations.csv` sungguhan selesai dianotasi. Fixture ini
memungkinkan pengujian mekanisme propagasi — konvergensi, arah tanda, penjagaan
kebocoran, urutan denoise — tanpa menunggu.

## Skemanya sengaja identik dengan berkas sungguhan

Kolomnya persis sama dengan `data/synthetic/seed_42/human_annotations_majority.csv`
yang dihasilkan `python -m annotation.build merge --seed 42`:

```
node_id, label, confidence_mean, agreement, n_annotators
```

Karena identik, beralih ke data sungguhan hanya perlu mengganti `--annotations`,
tanpa mengubah satu baris kode pun.

## Isi

20 baris, seluruhnya `node_id` **sungguhan** dari `seed_42` pada
`split=train` dan enam tipe entitas — supaya propagasi benar-benar melintasi
graph nyata, bukan graph karangan. Dipilih menyebar sepanjang derajat:

| Kelompok | Derajat | Guna dalam pengujian |
|---|---:|---|
| 5 node hub | 46–54 | Propagasi menjangkau jauh; menampakkan bias derajat |
| 5 node menengah | 18 | Perilaku umum |
| 5 node kecil | 10 | |
| 2 node renggang | 2 | |
| 3 node terisolasi | 0 | **Invarian**: skor akhir wajib sama persis dengan skor awal |

Label: 9 bernilai 1 dan 11 bernilai 0. `confidence_mean` menyebar 0,15–0,99
supaya bobot rendah dan tinggi sama-sama teruji. `agreement` bernilai 1,000 (12
baris) dan 0,667 (8 baris) supaya saringan `--min-agreement` teruji.

## Penjaga

`experiments/ablation.py` menolak menulis ke direktori hasil resmi bila berkas
anotasinya berada di bawah `tests/`, dan setiap baris keluaran membawa kolom
`annotation_source` beserta `is_fixture`. Lihat `_guard_official_output` di skrip
tersebut.
