# Evidence subgraph — ewallet_00030

- **Seed**: 42
- **Tipe node**: ewallet
- **Skor risiko model (mlScore)**: 1.0000
- **Skor rule-based**: 1.0000
- **Jumlah entitas terkait pada subgraph**: 20

## Relasi paling berkontribusi terhadap skor

Diurutkan menurut bobot `edge mask` GNNExplainer, dinormalkan ke skor
tertinggi = 1,000. Arah relasi mengikuti kontrak SRS §5.2.

| # | Dari | Relasi | Ke | Kontribusi |
|---:|---|---|---|---:|
| 1 | `ewallet_00030` | transferred_to | `bank_account_00023` | 1.000 |
| 2 | `ewallet_00030` | transferred_to | `ewallet_00031` | 0.818 |
| 3 | `domain_00035` | uses_account | `ewallet_00030` | 0.553 |
| 4 | `domain_00036` | uses_account | `ewallet_00030` | 0.502 |
| 5 | `bank_account_00094` | transferred_to | `bank_account_00178` | 0.499 |
| 6 | `bank_account_00089` | transferred_to | `ewallet_00331` | 0.497 |
| 7 | `report_00493` | mentions | `bank_account_00001` | 0.496 |
| 8 | `social_account_01169` | promotes | `domain_00540` | 0.495 |
| 9 | `report_00522` | mentions | `ewallet_00173` | 0.492 |
| 10 | `social_account_00257` | linked_to_apk | `apk_00156` | 0.488 |
| 11 | `phone_00201` | uses_account | `ewallet_00420` | 0.487 |
| 12 | `ewallet_00194` | transferred_to | `ewallet_00084` | 0.487 |

> Penjelasan ini menerangkan **mengapa model memberi skor tinggi**, bukan
> bukti hukum. Keputusan akhir tetap pada analis manusia (SRS KT-06).
