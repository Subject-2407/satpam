# Evidence subgraph — domain_00007

- **Seed**: 42
- **Tipe node**: domain
- **Skor risiko model (mlScore)**: 1.0000
- **Skor rule-based**: 1.0000
- **Jumlah entitas terkait pada subgraph**: 22

## Relasi paling berkontribusi terhadap skor

Diurutkan menurut bobot `edge mask` GNNExplainer, dinormalkan ke skor
tertinggi = 1,000. Arah relasi mengikuti kontrak SRS §5.2.

| # | Dari | Relasi | Ke | Kontribusi |
|---:|---|---|---|---:|
| 1 | `domain_00008` | redirects_to | `domain_00007` | 1.000 |
| 2 | `domain_00007` | uses_account | `ewallet_00006` | 0.246 |
| 3 | `social_account_00468` | promotes | `domain_00524` | 0.228 |
| 4 | `apk_00183` | contacts | `phone_00070` | 0.225 |
| 5 | `social_account_00815` | promotes | `domain_00478` | 0.224 |
| 6 | `victim_00392` | reported | `report_00629` | 0.224 |
| 7 | `social_account_01300` | promotes | `domain_00532` | 0.222 |
| 8 | `report_00081` | mentions | `social_account_01053` | 0.221 |
| 9 | `social_account_01289` | promotes | `domain_00508` | 0.221 |
| 10 | `report_00182` | mentions | `social_account_00457` | 0.220 |
| 11 | `report_00509` | mentions | `domain_00432` | 0.220 |
| 12 | `domain_00243` | contacts | `phone_00450` | 0.219 |

> Penjelasan ini menerangkan **mengapa model memberi skor tinggi**, bukan
> bukti hukum. Keputusan akhir tetap pada analis manusia (SRS KT-06).
