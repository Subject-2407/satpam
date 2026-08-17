# Evidence subgraph — victim_00056

- **Seed**: 42
- **Tipe node**: victim
- **Skor risiko model (mlScore)**: 1.0000
- **Skor rule-based**: 1.0000
- **Jumlah entitas terkait pada subgraph**: 23

## Relasi paling berkontribusi terhadap skor

Diurutkan menurut bobot `edge mask` GNNExplainer, dinormalkan ke skor
tertinggi = 1,000. Arah relasi mengikuti kontrak SRS §5.2.

| # | Dari | Relasi | Ke | Kontribusi |
|---:|---|---|---|---:|
| 1 | `victim_00056` | transferred_to | `ewallet_00030` | 1.000 |
| 2 | `report_00316` | mentions | `domain_00554` | 0.313 |
| 3 | `report_00440` | mentions | `domain_00696` | 0.307 |
| 4 | `report_00546` | mentions | `social_account_01462` | 0.306 |
| 5 | `social_account_01405` | promotes | `domain_00352` | 0.305 |
| 6 | `phone_00016` | uses_account | `ewallet_00029` | 0.303 |
| 7 | `report_00636` | mentions | `bank_account_00322` | 0.303 |
| 8 | `social_account_00672` | contacts | `phone_00215` | 0.303 |
| 9 | `report_00212` | mentions | `social_account_01418` | 0.303 |
| 10 | `ewallet_00206` | transferred_to | `bank_account_00286` | 0.302 |
| 11 | `report_00579` | mentions | `domain_00059` | 0.302 |
| 12 | `report_00344` | mentions | `ewallet_00320` | 0.301 |

> Penjelasan ini menerangkan **mengapa model memberi skor tinggi**, bukan
> bukti hukum. Keputusan akhir tetap pada analis manusia (SRS KT-06).
