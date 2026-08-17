# SATPAM (Prototype Awal)

Prototype awal sistem graph intelligence untuk deteksi, pemetaan, dan
prioritisasi risiko ekosistem judi online dan pinjaman online ilegal.

## Struktur

| Folder | Isi |
|---|---|
| `src/backend` | Backend FastAPI: routing, scoring, integrasi Neo4j. Lihat `docs/API.md` dan `docs/openapi.json` untuk referensi endpoint. |
| `src/frontend` | Frontend React + Vite + TypeScript, visualisasi graph dengan Cytoscape. |
| `src/engine` | Skema dataset dummy dan validator (`tools/validate_dataset.py`). |

## Menjalankan backend

```bash
cd src/backend
pip install -r requirements.txt
cp .env.example .env
docker compose up -d
uvicorn app.main:app --reload
```

Tes: `pytest` di dalam `src/backend`.

## Menjalankan frontend

```bash
cd src/frontend
npm install
npm run dev
```
