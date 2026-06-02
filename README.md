# SATPAM Proposal Slide Deck

Deck proposal ini dibuat untuk presentasi 10 menit tentang **SATPAM (Search-based AI Threat Prevention and Mapping)**, yaitu sistem AI-assisted berbasis graph intelligence untuk membantu pencegahan, deteksi, pemetaan, dan prioritisasi aktivitas mencurigakan terkait ekosistem judi online dan pinjol ilegal.

## Struktur Deck

1. **Title** - memperkenalkan SATPAM dan positioning sebagai sistem graph intelligence.
2. **Background / Urgency** - menunjukkan skala masalah dan mengapa pendekatan single-entity tidak cukup.
3. **Existing System and Gap** - membandingkan sistem existing dengan celah yang diisi SATPAM.
4. **Problem Statement** - merumuskan masalah dalam bentuk pertanyaan desain sistem.
5. **Proposed Solution: SATPAM** - menjelaskan alur solusi dari input data hingga dashboard dan verifikasi manusia.
6. **System Architecture** - menampilkan arsitektur konseptual sistem.
7. **Method / Workflow** - menjelaskan pipeline metode: ingestion, extraction, graph build, AI search, scoring, explainability.
8. **Innovation / Novelty** - merangkum inovasi dalam matriks gap-versus-kapabilitas.
9. **Benefits and Roadmap** - merangkum manfaat dan rencana implementasi prototype.
10. **Closing and References** - menutup dengan thesis utama dan referensi ringkas.

## File yang Dibuat

- `slides_outline.md` - outline 10 slide dengan claim dan proof object.
- `speaker_notes.md` - naskah narasi 10 menit dalam Bahasa Indonesia.
- `references.md` - daftar referensi gaya IEEE.
- `visuals/` - Mermaid diagram, SVG source icons, dan PNG icon assets untuk PPTX.
- `generate_ppt.py` - generator PowerPoint berbasis `python-pptx`.
- `final_proposal_satpam.pptx` - deck final 16:9.

## Catatan Desain

Deck memakai tema **dark blue cybersecurity** dengan aksen cyan, mint, amber, dan red alert. Slide dibuat visual-heavy dengan teks ringkas, diagram editable berbasis shape PowerPoint, ikon line-art konsisten, dan transisi fade antar-slide melalui OOXML.

## Cara Regenerasi

Jalankan:

```bash
python generate_ppt.py
```

Script akan membuat ulang folder `visuals/` jika diperlukan dan menghasilkan `final_proposal_satpam.pptx`.
