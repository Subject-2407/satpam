# Laporan Kesepakatan Anotasi — seed 42

300 node dari 2 ronde (anotasi_ronde1, anotasi_ronde2), 900 penilaian oleh 3 anotator.

## Perbandingan antar-ronde

Kesepakatan dilaporkan **per ronde**, bukan atas gabungannya. Kappa atas
gabungan mencampur mutu anotasi sebelum dan sesudah kalibrasi menjadi satu
angka yang tidak dapat ditafsirkan sebagai apa pun.

| Ronde | n | Fleiss' kappa | Tafsir | Selang 95% | Kesepakatan | Laju label 1 |
|---|---:|---:|---|---|---:|---|
| anotasi_ronde1 | 150 | 0.177 | lemah | [0.068, 0.284] | 0.547 | 0.91 / 0.61 / 0.76 |
| anotasi_ronde2 | 150 | 0.542 | sedang | [0.413, 0.652] | 0.740 | 0.28 / 0.22 / 0.26 |

Cara membaca kolom selang: dua ronde yang selangnya **tidak beririsan**
sudah cukup untuk menyatakan kappa-nya memang berbeda. Selang yang
beririsan belum tentu berarti tidak ada beda — ia hanya berarti data
sebanyak ini belum bisa memisahkan keduanya.

⚠️ Ronde yang berbeda menilai **node yang berbeda**, sehingga
perbandingannya menanggung selisih tingkat kesulitan sampel. Rancangan
strata yang sama di setiap ronde menahan sebagian besar selisih itu,
tetapi tidak seluruhnya — sebutkan batas ini bila angkanya dipakai di naskah.

Kesepakatan yang jatuh pada strata ambigu dan tinggi pada strata yang
rule engine yakin adalah bukti kuantitatif bahwa strata ambigu memang
sulit — bukan tanda anotator bekerja sembarangan. Kappa per strata bisa
mendekati nol justru ketika kesepakatannya tinggi, bila hampir seluruh
penilaian jatuh ke satu kelas; baca kolom kesepakatan dan porsi label 1
bersama-sama, jangan kappa-nya sendirian.

## Ronde: anotasi_ronde1

150 node, 450 penilaian.

| Ukuran | Nilai | Tafsir |
|---|---|---|
| Fleiss' kappa | 0.177 | lemah |
| Selang kepercayaan 95% kappa | [0.068, 0.284] | bootstrap 4000 ulangan atas node |
| Kesepakatan mentah | 0.547 | 82/150 node dinilai bulat |
| Cohen's kappa A1-A2 | 0.177 | lemah |
| Cohen's kappa A1-A3 | 0.168 | lemah |
| Cohen's kappa A2-A3 | 0.265 | lumayan |

| Anotator | Porsi dilabeli 1 |
|---|---|
| A1 | 0.907 |
| A2 | 0.607 |
| A3 | 0.760 |

| Strata | n | Fleiss' kappa | Kesepakatan | Porsi label 1 | Keterangan |
|---|---|---|---|---|---|
| S1 | 25 | -0.010 | 0.680 | 0.880 | rule yakin positif (critical, >=2 aturan pada node sendiri) |
| S2 | 25 | 0.203 | 0.480 | 0.680 | rule yakin negatif (low, tanpa aturan sendiri, tanpa tetangga critical) |
| S3 | 25 | -0.024 | 0.560 | 0.827 | di ambang batas level (skor +-5 dari 35/60/80) |
| S4 | 25 | 0.016 | 0.320 | 0.640 | jejak sendiri tipis, derajat rendah, ada tetangga bermasalah (membidik wilayah hard negative) |
| S5 | 25 | 0.333 | 0.680 | 0.800 | jejak sendiri kuat tapi lingkungan renggang |
| S6 | 25 | 0.272 | 0.560 | 0.720 | jangkar acak berstrata tipe node |

## Ronde: anotasi_ronde2

150 node, 450 penilaian.

| Ukuran | Nilai | Tafsir |
|---|---|---|
| Fleiss' kappa | 0.542 | sedang |
| Selang kepercayaan 95% kappa | [0.413, 0.652] | bootstrap 4000 ulangan atas node |
| Kesepakatan mentah | 0.740 | 111/150 node dinilai bulat |
| Cohen's kappa A1-A2 | 0.522 | sedang |
| Cohen's kappa A1-A3 | 0.611 | kuat |
| Cohen's kappa A2-A3 | 0.489 | sedang |

| Anotator | Porsi dilabeli 1 |
|---|---|
| A1 | 0.280 |
| A2 | 0.220 |
| A3 | 0.260 |

| Strata | n | Fleiss' kappa | Kesepakatan | Porsi label 1 | Keterangan |
|---|---|---|---|---|---|
| S1 | 27 | 0.365 | 0.556 | 0.630 | rule yakin positif (critical, >=2 aturan pada node sendiri) |
| S2 | 27 | 0.211 | 0.889 | 0.049 | rule yakin negatif (low, tanpa aturan sendiri, tanpa tetangga critical) |
| S3 | 27 | 0.402 | 0.667 | 0.247 | di ambang batas level (skor +-5 dari 35/60/80) |
| S4 | 27 | -0.038 | 0.889 | 0.037 | jejak sendiri tipis, derajat rendah, ada tetangga bermasalah (membidik wilayah hard negative) |
| S5 | 15 | 0.793 | 0.867 | 0.311 | jejak sendiri kuat tapi lingkungan renggang |
| S6 | 27 | 0.376 | 0.630 | 0.272 | jangkar acak berstrata tipe node |

Pita tafsir mengikuti Landis & Koch, *Biometrics* 33(1), 1977.

## Lampiran: catatan anotator

Bahan kutipan kualitatif. Kolom `note` tidak masuk
`human_annotations.csv` karena skema §5.3 beku.

| Ronde | Node | Anotator | Catatan |
|---|---|---|---|
| anotasi_ronde1 | phone_00340 | A1 | kontak dengan umur yang tergolong baru, disebut laporan dengan persentil 97, dan sudah memiliki tetanggan domain dengan kw 0,87 yang juga tergolong baru, dan lainnya juga. |
| anotasi_ronde1 | apk_00024 | A1 | apk masih baru, tetangga salah satu kontak masih dapat dikatakan tidak mencurigakan karena hanya memiliki 1 laporan, dan tetangga lain ada yang bisa dicurigai tetapi nilai w pada apk ini masih rendah |
| anotasi_ronde1 | bank_account_00133 | A1 | bank yang masih sangat baru tetapi memiliki transaksi dan nominal yang sangat besar, dan tetangga nya yang bank account lain juga jadi acuan karena sudah memiliki tranksaksi dan nominal yang besar juga, maka dapat dicurigai sebagai pinjol illegal. |
| anotasi_ronde1 | ewallet_00019 | A1 | memiliki banyak laporan dan persentil nya yang tinggi begitupun juga dengan tetangganya |
| anotasi_ronde1 | bank_account_00022 | A1 | laporan 4 dan persentil 99 walaupun akun bank sudah lama dan hanya memiliki dikit nominal, dan tetangga phone_00017 disebut 3 laporan |
| anotasi_ronde1 | social_account_01407 | A1 | reportnya masih perlu diteliti dan w nya juga 0,54 |
| anotasi_ronde1 | ewallet_00434 | A1 | node ini terhubung langsung ke victim dengan kebanyakan victim mengirim dana ke  e-wallet ini |
| anotasi_ronde1 | social_account_00738 | A1 | masih kurang penelitian tetapi lebih menonjol ke label 0 |
| anotasi_ronde1 | ewallet_00168 | A1 | victim mengirim dana ke node ini dengan total 20 txn |
| anotasi_ronde1 | phone_00267 | A1 | masih perlu penelitian mengenai tetangganya |
| anotasi_ronde1 | apk_00107 | A1 | masih perlu diteliti node ini dan tetangga derajat keluar e wallet nya |
| anotasi_ronde1 | social_account_01353 | A1 | report masih perlu diteliti |
| anotasi_ronde1 | social_account_00933 | A1 | tetangga ada yang kw 0,81 |
| anotasi_ronde2 | ewallet_00356 | A1 | Pola transaksi atau nominal; Pola tetangga langsung; Aliran dana dari node korban |
| anotasi_ronde2 | apk_00066 | A1 | kw tetangga masih kurang tinggi dan perlu investigasi bukti lebih lanjut |
| anotasi_ronde2 | bank_account_00087 | A1 | Aliran dana dari node korban; Pola transaksi atau nominal; Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00013 | A1 | Pola transaksi atau nominal; Pola tetangga langsung; Aliran dana dari node korban |
| anotasi_ronde2 | social_account_00102 | A1 | Umur atau pola kemunculan; Banyaknya laporan yang menyebut; Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00030 | A1 | Pola tetangga langsung; Pola transaksi atau nominal; Aliran dana dari node korban; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | domain_00215 | A1 | tetangga ewalet tiketnya masih ga wajar |
| anotasi_ronde2 | ewallet_00061 | A1 | Aliran dana dari node korban; Pola transaksi atau nominal; Jejak pada entitas ini sendiri; Umur atau pola kemunculan |
| anotasi_ronde2 | phone_00364 | A1 | tetangga social_account_01381 itu perlu selidiki lagi |
| anotasi_ronde2 | bank_account_00439 | A1 | Aliran dana dari node korban; Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00090 | A1 | Pola tetangga langsung -- perlu di selidiki keterkaitan node ini dengan victim |
| anotasi_ronde2 | apk_00015 | A1 | masih perlu diselidiki tetangganya |
| anotasi_ronde2 | phone_00133 | A1 | tetangga yg kwnya tinggi perlu di cek lebih lanjut |
| anotasi_ronde2 | bank_account_00317 | A1 | perlu di cek tetangga victim nya |
| anotasi_ronde2 | ewallet_00101 | A1 | Pola transaksi atau nominal; Aliran dana dari node korban -- tetap perlu diselidiki lebih lanjut |
| anotasi_ronde2 | social_account_00547 | A1 | Jejak pada entitas ini sendiri; Umur atau pola kemunculan; Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00256 | A1 | masih perlu diselidiki, dan tetangga nya juga yg bukan QRIS |
| anotasi_ronde2 | bank_account_00011 | A1 | Aliran dana dari node korban; Pola transaksi atau nominal; Jejak pada entitas ini sendiri; Pola tetangga langsung; Umur atau pola kemunculan |
| anotasi_ronde2 | apk_00101 | A1 | Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | social_account_00848 | A1 | tetangga phonenya agak sus |
| anotasi_ronde2 | bank_account_00120 | A1 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal; Aliran dana dari node korban; Pola tetangga langsung; Umur atau pola kemunculan -- perlu dicek lebih lanjut semua tranksaksinya dan victim nya |
| anotasi_ronde2 | domain_00016 | A1 | Pola tetangga langsung; Jejak pada entitas ini sendiri; Banyaknya laporan yang menyebut; Lainnya (jelaskan di catatan) -- ada domain mengalihkan |
| anotasi_ronde2 | bank_account_00047 | A1 | Jejak pada entitas ini sendiri; Pola tetangga langsung; Aliran dana dari node korban; Pola transaksi atau nominal; Umur atau pola kemunculan |
| anotasi_ronde2 | ewallet_00038 | A1 | Jejak pada entitas ini sendiri; Aliran dana dari node korban; Banyaknya laporan yang menyebut |
| anotasi_ronde2 | bank_account_00449 | A1 | victim perlu diselidiki lagi |
| anotasi_ronde2 | domain_00670 | A1 | Pola tetangga langsung; Lainnya (jelaskan di catatan) -- domain mengalihkan |
| anotasi_ronde2 | bank_account_00422 | A1 | pola tranksaksi dan umur agak mencurigakan |
| anotasi_ronde2 | ewallet_00246 | A1 | Umur atau pola kemunculan; Pola tetangga langsung; Aliran dana dari node korban; Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | domain_00334 | A1 | Umur atau pola kemunculan; Banyaknya laporan yang menyebut; Pola tetangga langsung |
| anotasi_ronde2 | domain_00054 | A1 | Umur atau pola kemunculan; Banyaknya laporan yang menyebut; Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00114 | A1 | tetangga dengan txn dan tiket mencurigakan perlu diselidiki juga |
| anotasi_ronde2 | ewallet_00441 | A1 | tetangga agak mencurigakan |
| anotasi_ronde2 | domain_00042 | A1 | Umur atau pola kemunculan; Banyaknya laporan yang menyebut; Pola tetangga langsung; Lainnya (jelaskan di catatan) -- ada domain mengalihkan dll |
| anotasi_ronde2 | domain_00013 | A1 | ada domain mengalihkan agak bikin ragu tetapi tetangga domain umurnya lama |
| anotasi_ronde2 | bank_account_00152 | A1 | Aliran dana dari node korban; Pola tetangga langsung -- ada tetangga dengan txn dan tiket mencurigakan juga |
| anotasi_ronde2 | social_account_00286 | A1 | perlu diselidiki lebih lanjut reportnya |
| anotasi_ronde2 | phone_00106 | A1 | umur tetangga bank dengan txn dan tiket perlu dselidiki |
| anotasi_ronde2 | ewallet_00018 | A1 | Aliran dana dari node korban; Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00059 | A1 | Pola tetangga langsung; Aliran dana dari node korban -- perlu diselidiki victimnya dengan node ini |
| anotasi_ronde2 | bank_account_00200 | A1 | Pola transaksi atau nominal; Umur atau pola kemunculan |
| anotasi_ronde2 | apk_00141 | A1 | umur, report, dan pola tetangga mencurigakan tapi umurnya sudah lama |
| anotasi_ronde2 | social_account_00069 | A1 | Banyaknya laporan yang menyebut; Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00353 | A1 | Pola tetangga langsung; Aliran dana dari node korban |
| anotasi_ronde2 | domain_00007 | A1 | Jejak pada entitas ini sendiri; Umur atau pola kemunculan; Banyaknya laporan yang menyebut |
| anotasi_ronde2 | social_account_01358 | A1 | ada tetangga laporan nya banyak |
| anotasi_ronde2 | domain_00663 | A1 | Jejak pada entitas ini sendiri; Pola tetangga langsung; Lainnya (jelaskan di catatan) -- ada domain mengalihkan |
| anotasi_ronde2 | apk_00099 | A1 | Pola tetangga langsung; Lainnya (jelaskan di catatan); Jejak pada entitas ini sendiri -- kebanyakan tetangga yg mempromosukan kwnya tinggi atau ada laporan |
| anotasi_ronde2 | ewallet_00013 | A1 | Pola tetangga langsung; Aliran dana dari node korban |
| anotasi_ronde2 | ewallet_00178 | A1 | Aliran dana dari node korban; Pola transaksi atau nominal; Umur atau pola kemunculan; Pola tetangga langsung |
| anotasi_ronde2 | domain_00036 | A1 | Umur atau pola kemunculan; Jejak pada entitas ini sendiri; Pola tetangga langsung -- banyak laporan juga di tetangga |
| anotasi_ronde2 | bank_account_00136 | A1 | Aliran dana dari node korban; Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00281 | A1 | Pola transaksi atau nominal; Aliran dana dari node korban; Pola tetangga langsung |
| anotasi_ronde2 | domain_00247 | A1 | ada domain mengalihkan |
| anotasi_ronde2 | bank_account_00394 | A1 | Umur atau pola kemunculan; Pola transaksi atau nominal |
| anotasi_ronde2 | bank_account_00352 | A1 | Aliran dana dari node korban; Pola tetangga langsung |
| anotasi_ronde2 | domain_00576 | A1 | reportnya masih perlu diselidiki mengenai node ini |
| anotasi_ronde2 | phone_00020 | A1 | Umur atau pola kemunculan; Banyaknya laporan yang menyebut |
| anotasi_ronde2 | bank_account_00018 | A1 | Umur atau pola kemunculan; Aliran dana dari node korban; Pola tetangga langsung; Banyaknya laporan yang menyebut; Pola transaksi atau nominal |
| anotasi_ronde2 | domain_00534 | A1 | Lainnya (jelaskan di catatan) -- ada domain mengalihkan |
| anotasi_ronde2 | domain_00522 | A1 | Lainnya (jelaskan di catatan) -- node ini memakai ewallet dengan txn dan tiket yg mencurigakan |
| anotasi_ronde2 | ewallet_00370 | A1 | qris juga sebenarnya bisa melakukan lebih banyak tranksaksi dengan umur yg lama |
| anotasi_ronde2 | social_account_01339 | A1 | kurang bukti |
| anotasi_ronde2 | social_account_01304 | A1 | kurang bukti |
| anotasi_ronde2 | domain_00027 | A1 | tetangga bank account attributnya mencurigakan |
| anotasi_ronde2 | ewallet_00365 | A2 | Umur atau pola kemunculan; Pola transaksi atau nominal |
| anotasi_ronde2 | domain_00007 | A2 | Umur atau pola kemunculan; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00013 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal; Umur atau pola kemunculan; Pola tetangga langsung |
| anotasi_ronde2 | domain_00016 | A2 | Banyaknya laporan yang menyebut |
| anotasi_ronde2 | bank_account_00047 | A2 | Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | phone_00133 | A2 | Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00157 | A2 | Pola transaksi atau nominal |
| anotasi_ronde2 | ewallet_00246 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal; Umur atau pola kemunculan |
| anotasi_ronde2 | social_account_00943 | A2 | Jejak pada entitas ini sendiri; Umur atau pola kemunculan |
| anotasi_ronde2 | social_account_00286 | A2 | Banyaknya laporan yang menyebut |
| anotasi_ronde2 | domain_00054 | A2 | Pola tetangga langsung |
| anotasi_ronde2 | social_account_00102 | A2 | Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | phone_00020 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | bank_account_00439 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | bank_account_00011 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | social_account_01384 | A2 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00317 | A2 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | domain_00042 | A2 | Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00030 | A2 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00018 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | ewallet_00013 | A2 | Pola transaksi atau nominal; Pola tetangga langsung |
| anotasi_ronde2 | domain_00663 | A2 | Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00038 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | domain_00013 | A2 | Pola transaksi atau nominal |
| anotasi_ronde2 | bank_account_00136 | A2 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | apk_00101 | A2 | Pola transaksi atau nominal |
| anotasi_ronde2 | ewallet_00353 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | ewallet_00178 | A2 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00120 | A2 | Pola tetangga langsung; Pola transaksi atau nominal; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00305 | A2 | Pola transaksi atau nominal; Banyaknya laporan yang menyebut |
| anotasi_ronde2 | ewallet_00281 | A2 | Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | ewallet_00061 | A2 | Jejak pada entitas ini sendiri; Pola tetangga langsung; Pola transaksi atau nominal |
| anotasi_ronde2 | ewallet_00090 | A2 | Pola transaksi atau nominal; Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00439 | A3 | Jejak pada entitas ini sendiri; Lainnya (jelaskan di catatan) -- ada 1 victim yang kemuningkan terhubung |
| anotasi_ronde2 | social_account_00547 | A3 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00152 | A3 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | domain_00416 | A3 | Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00305 | A3 | Pola transaksi atau nominal; Umur atau pola kemunculan |
| anotasi_ronde2 | ewallet_00281 | A3 | Pola transaksi atau nominal; Aliran dana dari node korban; Umur atau pola kemunculan; Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00047 | A3 | Pola tetangga langsung; Aliran dana dari node korban; Pola transaksi atau nominal; Umur atau pola kemunculan |
| anotasi_ronde2 | domain_00013 | A3 | Lainnya (jelaskan di catatan); Pola tetangga langsung -- ada pola pengalihan domain juga |
| anotasi_ronde2 | domain_00007 | A3 | Pola tetangga langsung; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | ewallet_00090 | A3 | w victim masih meragukan |
| anotasi_ronde2 | bank_account_00449 | A3 | Pola transaksi atau nominal; Pola tetangga langsung |
| anotasi_ronde2 | social_account_00069 | A3 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | apk_00101 | A3 | Pola tetangga langsung; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | ewallet_00178 | A3 | Jejak pada entitas ini sendiri; Pola tetangga langsung; Pola transaksi atau nominal |
| anotasi_ronde2 | domain_00036 | A3 | Jejak pada entitas ini sendiri; Pola tetangga langsung -- ada pola mengalihkan |
| anotasi_ronde2 | phone_00258 | A3 | Pola tetangga langsung; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | domain_00016 | A3 | Pola tetangga langsung; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00352 | A3 | Aliran dana dari node korban; Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | apk_00099 | A3 | Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00013 | A3 | Aliran dana dari node korban; Jejak pada entitas ini sendiri; Pola transaksi atau nominal |
| anotasi_ronde2 | phone_00198 | A3 | Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00256 | A3 | Jejak pada entitas ini sendiri; Pola tetangga langsung; Umur atau pola kemunculan |
| anotasi_ronde2 | bank_account_00136 | A3 | Pola tetangga langsung; Pola transaksi atau nominal; Aliran dana dari node korban |
| anotasi_ronde2 | domain_00263 | A3 | Pola tetangga langsung; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | phone_00430 | A3 | Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | domain_00652 | A3 | Pola tetangga langsung |
| anotasi_ronde2 | domain_00663 | A3 | Pola tetangga langsung -- ada pola mengalihkan |
| anotasi_ronde2 | ewallet_00246 | A3 | Aliran dana dari node korban; Pola transaksi atau nominal; Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00120 | A3 | Pola transaksi atau nominal; Aliran dana dari node korban; Jejak pada entitas ini sendiri; Umur atau pola kemunculan; Pola tetangga langsung |
| anotasi_ronde2 | ewallet_00356 | A3 | Jejak pada entitas ini sendiri; Pola tetangga langsung; Pola transaksi atau nominal; Aliran dana dari node korban |
| anotasi_ronde2 | ewallet_00018 | A3 | Jejak pada entitas ini sendiri; Pola tetangga langsung; Pola transaksi atau nominal; Aliran dana dari node korban |
| anotasi_ronde2 | ewallet_00353 | A3 | Pola transaksi atau nominal; Jejak pada entitas ini sendiri; Aliran dana dari node korban |
| anotasi_ronde2 | social_account_00102 | A3 | Jejak pada entitas ini sendiri; Pola tetangga langsung |
| anotasi_ronde2 | bank_account_00011 | A3 | Pola tetangga langsung; Aliran dana dari node korban; Pola transaksi atau nominal; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | ewallet_00101 | A3 | Aliran dana dari node korban |
| anotasi_ronde2 | ewallet_00038 | A3 | Aliran dana dari node korban; Pola transaksi atau nominal; Pola tetangga langsung; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00030 | A3 | Pola tetangga langsung; Pola transaksi atau nominal; Jejak pada entitas ini sendiri; Aliran dana dari node korban |
| anotasi_ronde2 | ewallet_00061 | A3 | Pola tetangga langsung; Pola transaksi atau nominal; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | ewallet_00013 | A3 | Aliran dana dari node korban; Pola tetangga langsung; Jejak pada entitas ini sendiri |
| anotasi_ronde2 | bank_account_00018 | A3 | Pola transaksi atau nominal; Aliran dana dari node korban |
