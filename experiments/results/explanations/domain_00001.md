# Evidence subgraph — domain_00001

- **Seed**: 42
- **Tipe node**: domain
- **Skor risiko model (mlScore)**: 0.9999
- **Skor rule-based**: 0.3500
- **Jumlah entitas terkait pada subgraph**: 16

## Relasi paling berkontribusi terhadap skor

Diurutkan menurut bobot `edge mask` GNNExplainer, dinormalkan ke skor
tertinggi = 1,000. Arah relasi mengikuti kontrak SRS §5.2.

| # | Dari | Relasi | Ke | Kontribusi |
|---:|---|---|---|---:|
| 1 | `domain_00003` | redirects_to | `domain_00004` | 1.000 |
| 2 | `domain_00004` | redirects_to | `domain_00001` | 0.956 |
| 3 | `social_account_00006` | promotes | `domain_00004` | 0.687 |
| 4 | `social_account_00007` | promotes | `domain_00004` | 0.574 |
| 5 | `social_account_00009` | promotes | `domain_00004` | 0.467 |
| 6 | `report_00622` | mentions | `domain_00004` | 0.415 |
| 7 | `report_00297` | mentions | `domain_00004` | 0.407 |
| 8 | `social_account_00005` | promotes | `domain_00004` | 0.376 |
| 9 | `social_account_00066` | linked_to_apk | `apk_00008` | 0.278 |
| 10 | `social_account_00057` | promotes | `domain_00017` | 0.275 |
| 11 | `report_00059` | mentions | `ewallet_00019` | 0.273 |
| 12 | `social_account_01184` | promotes | `domain_00109` | 0.272 |

> Penjelasan ini menerangkan **mengapa model memberi skor tinggi**, bukan
> bukti hukum. Keputusan akhir tetap pada analis manusia (SRS KT-06).
