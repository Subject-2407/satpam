# Evidence subgraph — social_account_00004

- **Seed**: 42
- **Tipe node**: social_account
- **Skor risiko model (mlScore)**: 0.9697
- **Skor rule-based**: 0.3500
- **Jumlah entitas terkait pada subgraph**: 11

## Relasi paling berkontribusi terhadap skor

Diurutkan menurut bobot `edge mask` GNNExplainer, dinormalkan ke skor
tertinggi = 1,000. Arah relasi mengikuti kontrak SRS §5.2.

| # | Dari | Relasi | Ke | Kontribusi |
|---:|---|---|---|---:|
| 1 | `phone_00001` | uses_account | `ewallet_00002` | 1.000 |
| 2 | `phone_00001` | uses_account | `bank_account_00002` | 0.979 |
| 3 | `social_account_00004` | promotes | `domain_00003` | 0.969 |
| 4 | `social_account_00004` | contacts | `phone_00001` | 0.961 |
| 5 | `social_account_00001` | contacts | `phone_00001` | 0.953 |
| 6 | `phone_00001` | uses_account | `bank_account_00001` | 0.945 |
| 7 | `phone_00001` | uses_account | `ewallet_00003` | 0.941 |
| 8 | `social_account_00002` | promotes | `domain_00003` | 0.926 |
| 9 | `domain_00003` | contacts | `phone_00001` | 0.925 |
| 10 | `domain_00003` | redirects_to | `domain_00004` | 0.923 |
| 11 | `social_account_00007` | promotes | `domain_00003` | 0.905 |
| 12 | `social_account_00009` | promotes | `domain_00003` | 0.898 |

> Penjelasan ini menerangkan **mengapa model memberi skor tinggi**, bukan
> bukti hukum. Keputusan akhir tetap pada analis manusia (SRS KT-06).
