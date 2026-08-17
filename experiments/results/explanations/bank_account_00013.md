# Evidence subgraph — bank_account_00013

- **Seed**: 42
- **Tipe node**: bank_account
- **Skor risiko model (mlScore)**: 0.9979
- **Skor rule-based**: 0.5500
- **Jumlah entitas terkait pada subgraph**: 12

## Relasi paling berkontribusi terhadap skor

Diurutkan menurut bobot `edge mask` GNNExplainer, dinormalkan ke skor
tertinggi = 1,000. Arah relasi mengikuti kontrak SRS §5.2.

| # | Dari | Relasi | Ke | Kontribusi |
|---:|---|---|---|---:|
| 1 | `victim_00310` | transferred_to | `bank_account_00013` | 1.000 |
| 2 | `victim_00285` | transferred_to | `bank_account_00013` | 0.999 |
| 3 | `victim_00310` | transferred_to | `ewallet_00034` | 0.992 |
| 4 | `ewallet_00018` | transferred_to | `bank_account_00014` | 0.981 |
| 5 | `ewallet_00018` | transferred_to | `bank_account_00013` | 0.977 |
| 6 | `victim_00213` | transferred_to | `bank_account_00013` | 0.972 |
| 7 | `victim_00346` | transferred_to | `bank_account_00013` | 0.967 |
| 8 | `victim_00476` | transferred_to | `bank_account_00013` | 0.943 |
| 9 | `victim_00331` | transferred_to | `bank_account_00013` | 0.943 |
| 10 | `victim_00336` | transferred_to | `bank_account_00013` | 0.939 |
| 11 | `victim_00346` | transferred_to | `ewallet_00030` | 0.929 |
| 12 | `victim_00466` | transferred_to | `bank_account_00014` | 0.926 |

> Penjelasan ini menerangkan **mengapa model memberi skor tinggi**, bukan
> bukti hukum. Keputusan akhir tetap pada analis manusia (SRS KT-06).
