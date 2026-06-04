# Perbedaan SATPAM dengan Jurnal Acuan

## Ringkasan Utama

Jurnal-jurnal acuan mendukung komponen tertentu dari SATPAM, seperti web scraping, text mining, graph database, knowledge graph, explainable fraud detection, dan human-in-the-loop.

Perbedaan utama SATPAM adalah sistem ini menggabungkan berbagai komponen tersebut menjadi satu konsep sistem terpadu untuk konteks judol dan pinjol ilegal di Indonesia.

SATPAM tidak hanya mendeteksi satu domain, satu konten, atau satu rekening. SATPAM memetakan hubungan antar entitas seperti laporan masyarakat, domain, URL, nomor WhatsApp, rekening bank, QRIS, e-wallet, APK, blacklist, dan pola transaksi simulasi ke dalam satu graph risiko.

## Tabel Perbandingan

| Acuan | Fokus jurnal | Perbedaan SATPAM |
|---|---|---|
| Detecting Hidden Illegal Online Gambling on .go.id Domains Using Web Scraping Algorithms | Deteksi domain atau situs judi online tersembunyi menggunakan web scraping | SATPAM tidak berhenti pada deteksi domain. Domain dihubungkan dengan nomor WhatsApp, rekening, APK, laporan masyarakat, dan blacklist dalam graph risiko. |
| Detecting Online Gambling Promotions on Indonesian Twitter Using Text Mining Algorithm | Deteksi promosi judi online di media sosial menggunakan text mining | SATPAM memakai konten promosi sebagai salah satu pintu masuk, lalu mengekstrak entitas dan menelusuri jaringan risikonya. |
| Enhancing Fraud Detection in Banking by Integration of Graph Databases with Machine Learning | Fraud detection di sektor banking dengan graph database dan machine learning | SATPAM berfokus pada ekosistem gabungan digital dan finansial: judol, pinjol ilegal, domain, APK, rekening, QRIS, e-wallet, dan laporan korban. |
| A Survey on Cybersecurity Knowledge Graph Construction | Konsep umum pembangunan cybersecurity knowledge graph | SATPAM menerapkan konsep graph secara spesifik untuk ekosistem judol-pinjol ilegal, dengan evidence path yang dapat dibaca analis. |
| TINKER: A Framework for Open Source Cyberthreat Intelligence | Framework open-source cyber threat intelligence | SATPAM bukan hanya CTI umum. SATPAM mengubah laporan publik, crawler finding, rekening, nomor WhatsApp, domain, dan APK menjadi graph risiko yang terstruktur. |
| AttacKG: Constructing Technique Knowledge Graph from Cyber Threat Intelligence Reports | Knowledge graph dari laporan cyber threat intelligence | SATPAM tidak fokus pada teknik serangan siber, tetapi pada relasi bukti seperti laporan -> domain -> WhatsApp -> rekening -> APK. |
| SEFraud: Graph-based Self-Explainable Fraud Detection | Explainable fraud detection berbasis graph | SATPAM menjelaskan risiko melalui evidence path, rule-based scoring, dan alasan risiko yang bisa diverifikasi analis. |
| Enhancing Financial Fraud Detection with Human-in-the-Loop Feedback and Feedback Propagation | Deteksi fraud dengan feedback dan verifikasi manusia | SATPAM menjadikan human verification sebagai prinsip inti. Sistem hanya memberi kandidat prioritas, bukan melakukan auto-blocking. |

## Novelty SATPAM

1. **Integrasi lintas ekosistem**

   SATPAM menyatukan entitas digital dan finansial dalam satu graph, bukan menganalisis domain, konten, rekening, dan APK secara terpisah.

2. **Spesifik untuk konteks judol-pinjol ilegal Indonesia**

   Banyak jurnal membahas fraud, cybersecurity, atau deteksi konten secara umum. SATPAM diarahkan khusus pada masalah judi online dan pinjaman online ilegal yang melibatkan banyak kanal.

3. **Graph search sebagai inti analisis**

   SATPAM menggunakan pendekatan search-based AI seperti BFS untuk menemukan jalur bukti terdekat dan koneksi antar entitas.

4. **Evidence path yang mudah dijelaskan**

   Output SATPAM bukan hanya label berisiko, tetapi jalur alasan seperti laporan -> domain -> nomor WhatsApp -> rekening -> APK.

5. **Risk scoring berbasis relasi**

   Skor risiko tidak hanya dihitung dari karakteristik satu entitas, tetapi juga dari hubungan entitas tersebut dengan laporan, blacklist, transaksi simulasi, domain, dan APK.

6. **Human-in-the-loop sejak desain awal**

   SATPAM tidak melakukan pemblokiran otomatis. Sistem hanya memberi prioritas dan penjelasan untuk diverifikasi oleh analis manusia.

7. **Decision-support, bukan sistem penindakan**

   SATPAM diposisikan sebagai alat bantu analisis untuk melengkapi kerja lembaga seperti Komdigi, OJK, IASC, PPATK, dan aparat penegak hukum.

## Kalimat Siap Pakai untuk Presentasi

Jurnal-jurnal acuan umumnya membahas satu sisi tertentu, seperti web scraping, text mining, graph fraud detection, knowledge graph, explainability, atau human-in-the-loop.

SATPAM berbeda karena mengintegrasikan prinsip-prinsip tersebut ke dalam satu sistem decision-support yang spesifik untuk ekosistem judol-pinjol ilegal Indonesia.

Output SATPAM bukan hanya hasil deteksi, tetapi graph risiko, evidence path, risk score, prioritas kasus, dan verifikasi manusia sebelum tindakan lanjut.

## Kesimpulan

Dengan demikian, kontribusi SATPAM bukan sekadar mendeteksi judi online atau pinjol ilegal, tetapi membangun sistem graph intelligence yang mampu memetakan hubungan antar entitas, menjelaskan alasan risiko, dan membantu analis menentukan prioritas secara lebih terstruktur.
