# SATPAM Backend — API Documentation

Dokumen ini adalah referensi API backend SATPAM untuk dikonsumsi frontend.

> **SATPAM** = Search-based AI Threat Prevention and Mapping.
> **Semua data bersifat dummy/simulasi.** Sistem tidak melakukan blokir nyata,
> tidak memvonis pelaku, dan tidak memakai data korban asli. Selalu gunakan
> bahasa indikatif ("terindikasi berisiko", "perlu verifikasi"), bukan vonis.

- **Base URL (dev):** `http://localhost:8000`
- **Format:** JSON (kecuali export Markdown → `text/markdown`).
- **Versi API:** `0.1.0-week1`
- **OpenAPI/Swagger interaktif:** `GET /docs` (Swagger UI), `GET /redoc` (ReDoc), `GET /openapi.json` (spec mentah).
- **Spec tersimpan:** [`docs/openapi.json`](openapi.json) — bisa di-import ke Postman / dipakai untuk codegen client.

---

## Daftar Isi

1. [Autentikasi](#1-autentikasi)
2. [Konvensi Umum](#2-konvensi-umum)
3. [Enum & Nilai Valid](#3-enum--nilai-valid)
4. [Bentuk Objek Standar](#4-bentuk-objek-standar)
5. [Endpoint](#5-endpoint)
   - [Health](#health)
   - [Auth](#auth)
   - [Reports](#reports)
   - [Entities](#entities)
   - [Graph & Analysis](#graph--analysis)
   - [Dashboard](#dashboard)
   - [Alerts / Early Warning](#alerts--early-warning)
   - [Verification Cases](#verification-cases)
   - [Blacklist Candidates](#blacklist-candidates)
   - [Traffic & Crawler Intelligence](#traffic--crawler-intelligence)
   - [Export](#export)
   - [Rules (Scoring)](#rules-scoring)
   - [Import & Admin](#import--admin)
6. [Catatan untuk Frontend](#6-catatan-untuk-frontend)

---

## 1. Autentikasi

SATPAM memakai **JWT Bearer token** (OAuth2 password flow).

### Login

`POST /api/auth/token` — **body harus `application/x-www-form-urlencoded`** (bukan JSON), field `username` (diisi email) dan `password`.

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=analyst@satpam.test&password=analyst123"
```

Response `200`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "analyst",
  "user_id": "user-analyst-001"
}
```

Gunakan token pada semua request lain:

```
Authorization: Bearer <access_token>
```

Token salah/expired → `401`. Email/password salah → `401`.

### Akun Seed (demo only)

| Email | Password | Role |
|---|---|---|
| `reporter@satpam.test` | `reporter123` | `public_reporter` |
| `analyst@satpam.test` | `analyst123` | `analyst` |
| `supervisor@satpam.test` | `supervisor123` | `supervisor` |
| `admin@satpam.test` | `admin123` | `admin` |

### Hak Akses Role

| Role | Akses |
|---|---|
| `public_reporter` | Submit laporan saja (`POST /api/reports`) |
| `analyst` | Baca dashboard, entitas, graph, analisis, alert; verifikasi awal |
| `supervisor` | Semua analyst + keputusan final (close case, confirm blacklist) + audit log |
| `admin` | Semua + import dataset, update rule, reset data |

Akses tidak cukup → `403`.

---

## 2. Konvensi Umum

### Response list (paginated)

Semua endpoint daftar mengembalikan bentuk standar:

```json
{
  "items": [ /* array objek */ ],
  "total": 42,
  "limit": 50,
  "offset": 0,
  "hasMore": false
}
```

Query param pagination yang berlaku umum: `limit` (default 50, 1–200) dan `offset` (default 0).

### Format Error

Error memakai bentuk FastAPI standar:

```json
{ "detail": "Pesan error" }
```

Validasi body/query yang gagal (`422`) mengembalikan array detail:

```json
{ "detail": [ { "loc": ["body", "status"], "msg": "...", "type": "..." } ] }
```

Beberapa error domain memakai object pada `detail` (lihat `POST /api/reports`).

### Kode Status Umum

| Kode | Arti |
|---|---|
| `200` | OK |
| `201` | Resource dibuat (submit report, import) |
| `400` | Parameter tidak valid (mis. node label tidak diizinkan) |
| `401` | Belum login / token invalid |
| `403` | Role tidak punya akses |
| `404` | Resource tidak ditemukan |
| `422` | Validasi gagal / nilai enum tidak valid |
| `503` | Database (Neo4j) tidak tersedia |

### Path param `{node_type}`

Beberapa endpoint memakai `{node_type}/{node_id}` (bukan id saja) karena id saja
ambigu tipenya di graph multi-label. `node_type` **harus** salah satu label yang
diizinkan (lihat [Node Types](#node-types)); nilai lain → `400`.

### Privasi & Masking

Nilai sensitif (nomor HP, rekening, e-wallet, QRIS) sudah dalam bentuk **masked**
di data (`0812****1111`, `1234****9999`). Frontend **tidak boleh** menampilkan link
ilegal sebagai clickable link, dan harus menampilkan label `simulation_only` pada
data traffic/crawler.

---

## 3. Enum & Nilai Valid

**Role:** `public_reporter`, `analyst`, `supervisor`, `admin`

**Risk level (`riskLevel`):** `low`, `medium`, `high`, `critical`

**Confidence:** `low`, `medium`, `high`

**Verification status (`verificationStatus`):** `unreviewed`, `needs_review`, `verified_risk`, `false_positive`, `escalated`, `closed`

**Alert status:** `new`, `reviewed`, `escalated`, `false_positive`

**Blacklist candidate status:** `not_candidate`, `blacklist_candidate`, `needs_more_evidence`, `rejected_candidate`, `false_positive`, `confirmed_blacklist`, `recommended_for_blocking`, `escalated`
- `confirmed_blacklist` & `recommended_for_blocking` **hanya** boleh diset supervisor/admin (keputusan manusia).

**Category hint laporan:** `judol`, `pinjol_illegal`, `cross_ecosystem`, `payment_flow`, `traffic_crawler`, `benign`

**Algoritma path search:** `BFS` (default), `UCS`, `BIDIRECTIONAL`, `A_STAR`

### Node Types

`Report`, `Victim`, `URL`, `Domain`, `LinkShortener`, `SocialMediaAccount`, `PhoneNumber`, `BankAccount`, `EWallet`, `QRISMerchant`, `APK`, `Keyword`, `Transaction`, `TrafficEvent`, `CrawlerFinding`, `BlacklistEntity`, `BlacklistCandidate`, `BlacklistDecision`, `Cluster`, `Evidence`, `RiskAssessment`, `VerificationCase`, `Recommendation`, `Alert`, `User`, `AuditLog`

Entitas indikator (dipakai pencarian & dashboard): `URL`, `Domain`, `LinkShortener`, `SocialMediaAccount`, `PhoneNumber`, `BankAccount`, `EWallet`, `QRISMerchant`, `APK`, `Keyword`

### Relationship Types

`REPORTED`, `MENTIONS`, `CONTAINS_KEYWORD`, `REDIRECTS_TO`, `PROMOTES`, `CONTACTS`, `USES_ACCOUNT`, `TRANSFERRED_TO`, `OBSERVED_TRAFFIC_TO`, `HAS_REDIRECT_EVENT`, `CRAWLED_FROM`, `FOUND_ENTITY`, `LINKED_TO_APK`, `REQUESTS_PERMISSION`, `SIMILAR_TO`, `PART_OF_CLUSTER`, `BLACKLISTED_AS`, `FLAGGED_AS_CANDIDATE`, `DECIDED_AS`, `HAS_EVIDENCE`, `HAS_RISK_ASSESSMENT`, `HAS_RECOMMENDATION`, `OPENED_CASE`, `REVIEWED_BY`, `AUDITED_BY`

---

## 4. Bentuk Objek Standar

### Node

Setiap node minimal memuat properti standar berikut (plus properti khusus per tipe):

```json
{
  "id": "keyword-pinjaman-cepat-cair",
  "type": "Keyword",
  "label": "pinjaman cepat cair",
  "source": "dummy_user_report",
  "createdAt": "2026-06-18T00:00:00Z",
  "updatedAt": "2026-06-18T00:00:00Z",
  "confidence": "medium",
  "riskScore": 0,
  "riskLevel": "low",
  "verificationStatus": "unreviewed",
  "labels": ["Keyword"]
}
```

### Relationship (edge)

```json
{
  "id": "rel-mentions-743313b971b6",
  "type": "MENTIONS",
  "from": { "type": "Report", "id": "report-001" },
  "to": { "type": "URL", "id": "url-bonus-slot-demo-test-promo" },
  "source": "dummy_user_report",
  "confidence": "medium",
  "weight": 1.0
}
```

### RiskAssessment (`assessment`)

```json
{
  "subject": { "type": "Report", "id": "report-001" },
  "score": 100,
  "level": "critical",
  "confidence": "high",
  "triggeredRules": [
    { "ruleId": "R-001", "title": "Domain/URL mengandung keyword judol", "weight": 15, "evidence": "..." }
  ],
  "explanation": "Skor 100/100 (critical) ... tetap perlu human verification.",
  "recommendations": [
    { "actionType": "prioritaskan_verifikasi", "priority": "critical", "reason": "..." }
  ]
}
```

### EvidencePath

```json
{
  "nodes": [ /* array Node (atau {type,id} bila tak ada lookup) */ ],
  "relationships": [ /* array Relationship atau string id */ ],
  "cost": 3.0,
  "riskScore": 88,
  "explanation": "..."
}
```

### EarlyWarning

```json
{
  "id": "alert-...",
  "alertType": "Cross Ecosystem Alert",
  "subject": { "type": "Domain", "id": "domain-001" },
  "priority": "high",
  "reason": "...",
  "ruleIds": ["R-010"],
  "evidenceNodeIds": ["..."],
  "simulationOnly": true
}
```

---

## 5. Endpoint

Ringkasan (role minimum):

| Method | Path | Role |
|---|---|---|
| GET | `/health` | Public |
| POST | `/api/auth/token` | Public |
| POST | `/api/reports` | Authenticated (semua role) |
| GET | `/api/reports` | Analyst+ |
| GET | `/api/reports/{report_id}` | Analyst+ |
| GET | `/api/entities` | Analyst+ |
| GET | `/api/entities/{node_type}/{node_id}` | Analyst+ |
| GET | `/api/graph/neighborhood/{node_type}/{node_id}` | Analyst+ |
| POST | `/api/analysis/path-search` | Analyst+ |
| GET | `/api/analysis/{node_type}/{node_id}` | Analyst+ |
| POST | `/api/analysis/rebuild` | Admin |
| GET | `/api/dashboard/summary` | Analyst+ |
| GET | `/api/alerts/early-warnings` | Analyst+ |
| GET | `/api/alerts` | Analyst+ |
| PATCH | `/api/alerts/{alert_id}/status` | Analyst+ |
| GET | `/api/verification-cases` | Analyst+ |
| GET | `/api/verification-cases/{case_id}` | Analyst+ |
| PATCH | `/api/verification-cases/{case_id}` | Analyst+ (`closed`: Supervisor+) |
| GET | `/api/blacklist-candidates` | Analyst+ |
| GET | `/api/blacklist-candidates/{candidate_id}` | Analyst+ |
| PATCH | `/api/blacklist-candidates/{candidate_id}/decision` | Analyst+ (confirm/block: Supervisor+) |
| GET | `/api/traffic-events` | Analyst+ |
| POST | `/api/traffic-events/import` | Admin |
| GET | `/api/crawler-findings` | Analyst+ |
| POST | `/api/crawler-findings/import` | Admin |
| GET | `/api/export/analysis/{node_type}/{node_id}` | Analyst+ |
| GET | `/api/rules` | Analyst+ |
| PATCH | `/api/rules/{rule_id}` | Admin |
| POST | `/api/import/dummy-data` | Admin |
| DELETE | `/api/admin/reset-dataset` | Admin |
| GET | `/api/audit-logs` | Supervisor+ |

---

### Health

#### `GET /health`

Cek status backend & koneksi Neo4j. Tidak perlu auth. Selalu `200`.

```json
{ "status": "healthy", "neo4j": "connected", "timestamp": "2026-06-18T00:00:00Z" }
```

`status`: `healthy` | `degraded` (jika Neo4j tidak tersambung). `neo4j`: `connected` | `error`.

---

### Auth

#### `POST /api/auth/token`

Lihat [Autentikasi](#1-autentikasi).

---

### Reports

#### `POST /api/reports` — Submit laporan dummy

**Role:** semua role terautentikasi (termasuk `public_reporter`).
Memproses laporan lewat AI engine: ekstraksi → normalisasi → graph build → scoring →
artifact risiko, lalu persist ke Neo4j. Hasil high/critical hanya membuka artifact
review; **tidak** ada blacklist final / blokir otomatis.

Request body (JSON):

```json
{
  "source": "dummy_user_report",
  "categoryHint": "cross_ecosystem",
  "description": "Saya diarahkan dari akun promosi ke situs bonus slot, lalu diminta menghubungi WA dan transfer. Setelah itu ditawari aplikasi pinjaman cepat cair.",
  "urls": ["https://bonus-slot-demo.test/promo"],
  "phoneNumbers": ["0812-0000-1111"],
  "bankAccounts": [
    { "bankName": "Bank Dummy", "accountAlias": "Rekening Promo 01", "maskedAccountNumber": "1234****9999" }
  ],
  "apps": [
    { "appName": "DanaCepat Demo", "packageName": "id.demo.danacepat" }
  ]
}
```

| Field | Wajib | Catatan |
|---|---|---|
| `description` | ✅ | Teks laporan |
| `categoryHint` | ✅ | Lihat [enum category hint](#3-enum--nilai-valid) |
| `source` | ❌ | Default `"user_report"` |
| `urls` | ❌ | Array string |
| `phoneNumbers` | ❌ | Array string |
| `bankAccounts` | ❌ | `{bankName, accountAlias, maskedAccountNumber}` |
| `apps` | ❌ | `{appName, packageName}` |

Response `201`:

```json
{
  "reportId": "report-1a2b3c4d5e6f",
  "status": "auto_triaged",
  "message": "Laporan dummy diterima, diekstrak, dianalisis, dan siap direview",
  "extractedEntities": 7,
  "nodesMerged": 9,
  "relationshipsMerged": 8,
  "analysis": { "assessment": { /* ... */ }, "evidencePath": null, "earlyWarnings": [], "blacklistCandidate": null }
}
```

`analysis` = objek [AnalysisResult](#riskassessment-assessment) (`{assessment, evidencePath, earlyWarnings, blacklistCandidate}`).

Error `422` (guardrail — input mengandung indikasi data nyata): `detail` berupa object:

```json
{ "detail": { "message": "Input prototype harus memakai data dummy/simulasi.", "violations": ["..."] } }
```

#### `GET /api/reports` — Daftar laporan

**Role:** Analyst+. Response: [list envelope](#response-list-paginated) berisi node `Report`.

Query: `status`, `category_hint`, `search` (cari di id/description/label), `limit`, `offset`.

#### `GET /api/reports/{report_id}` — Detail laporan

**Role:** Analyst+. `200` → `{ "report": { /* node */ } }`. Tidak ada → `404`.

---

### Entities

#### `GET /api/entities` — Cari entitas indikator

**Role:** Analyst+. Mencari lintas tipe entitas indikator (atau satu tipe), urut by
`riskScore` menurun. Response: [list envelope](#response-list-paginated).

Query: `type` (satu node type), `risk_level`, `verification_status`, `search`, `limit`, `offset`.

```
GET /api/entities?risk_level=high&search=slot&limit=20
```

#### `GET /api/entities/{node_type}/{node_id}` — Detail entitas

**Role:** Analyst+. `200` → `{ "entity": { /* node */ } }`. `node_type` tidak valid → `400`. Tidak ada → `404`.

---

### Graph & Analysis

#### `GET /api/graph/neighborhood/{node_type}/{node_id}` — Neighborhood graph (BFS)

**Role:** Analyst+. Untuk graph explorer. Query: `depth` (default 3, 0–5), `limit` (default 150, 1–1000).

Response `200`:

```json
{
  "root": { "type": "Report", "id": "report-001" },
  "algorithm": "BFS",
  "maxDepth": 2,
  "nodeCount": 9,
  "nodes": [ /* array Node */ ],
  "relationships": [ /* array Relationship */ ]
}
```

> Batas display: maks 200 node & 500 relationship (lihat performance constraint). Tidak ada node → `404`.

#### `POST /api/analysis/path-search` — Evidence path / path search

**Role:** Analyst+. Request:

```json
{ "nodeType": "Domain", "nodeId": "domain-001", "algorithm": "BFS", "maxDepth": 3, "limit": 250 }
```

| Field | Default | Catatan |
|---|---|---|
| `nodeType`, `nodeId` | — | Titik awal |
| `algorithm` | `BFS` | `BFS` \| `UCS` \| `BIDIRECTIONAL` \| `A_STAR` |
| `maxDepth` | 3 | 1–5 |
| `limit` | 250 | 1–1000 |

Response `200`:

```json
{ "algorithm": "BFS", "path": { "nodes": [], "relationships": [], "cost": 3.0, "riskScore": 88, "explanation": "..." } }
```

`path` bisa `null` jika tidak ada jalur ditemukan. Node awal tidak ada → `404`.

#### `GET /api/analysis/{node_type}/{node_id}` — Risk assessment entitas

**Role:** Analyst+. Query: `depth` (default 3, 1–5), `limit` (default 250). Response =
objek [AnalysisResult](#riskassessment-assessment):

```json
{
  "assessment": {
    "subject": { "type": "Report", "id": "report-001" },
    "score": 100, "level": "critical", "confidence": "high",
    "triggeredRules": [ { "ruleId": "R-001", "title": "...", "weight": 15, "evidence": "..." } ],
    "explanation": "Skor 100/100 (critical) ... tetap perlu human verification.",
    "recommendations": [ { "actionType": "prioritaskan_verifikasi", "priority": "critical", "reason": "..." } ]
  },
  "evidencePath": null,
  "earlyWarnings": [],
  "blacklistCandidate": null
}
```

#### `POST /api/analysis/rebuild` — Re-scoring seluruh graph

**Role:** Admin. Menghitung ulang skor semua entitas dari graph, meng-update node, dan
membuat artifact untuk entitas high/critical. Response:

```json
{
  "status": "success",
  "assessments": 42,
  "artifactNodesMerged": 8,
  "artifactRelationshipsMerged": 12,
  "earlyWarnings": [ /* array EarlyWarning */ ]
}
```

---

### Dashboard

#### `GET /api/dashboard/summary` — Ringkasan dashboard utama

**Role:** Analyst+. Agregat untuk halaman utama (jumlah laporan, entitas, alert, case,
kandidat blacklist), breakdown risk level & status, serta entitas berisiko tertinggi.

Query: `top_entities` (default 5, 1–50).

Response `200`:

```json
{
  "simulationOnly": true,
  "totals": {
    "reports": 12,
    "entities": 87,
    "alerts": 5,
    "verificationCases": 4,
    "blacklistCandidates": 3
  },
  "entitiesByRiskLevel": { "critical": 6, "high": 11, "medium": 20, "low": 50 },
  "alertsByStatus": { "new": 3, "reviewed": 2 },
  "verificationCasesByStatus": { "needs_review": 3, "verified_risk": 1 },
  "blacklistCandidatesByStatus": { "blacklist_candidate": 3 },
  "topRiskEntities": [ /* array Node terurut riskScore desc */ ]
}
```

---

### Alerts / Early Warning

#### `GET /api/alerts/early-warnings` — Hitung early warning (tidak persist)

**Role:** Analyst+. Menghitung early warning langsung dari graph saat ini.

```json
{ "alerts": [ /* array EarlyWarning */ ] }
```

#### `GET /api/alerts` — Daftar alert (persisted)

**Role:** Analyst+. Early warning dihitung ulang lalu di-`upsert` sebagai node `Alert`
(status review **dipertahankan**), lalu dikembalikan sebagai [list envelope](#response-list-paginated).

Query: `status`, `priority`, `limit`, `offset`.

Bentuk node `Alert`:

```json
{
  "id": "alert-...", "type": "Alert", "label": "Cross Ecosystem Alert",
  "alertType": "Cross Ecosystem Alert", "subjectType": "Domain", "subjectId": "domain-001",
  "priority": "high", "reason": "...", "ruleIds": ["R-010"], "evidenceNodeIds": ["..."],
  "simulationOnly": true, "status": "new", "verificationStatus": "unreviewed",
  "createdAt": "2026-06-18T00:00:00Z", "updatedAt": "2026-06-18T00:00:00Z"
}
```

#### `PATCH /api/alerts/{alert_id}/status` — Update status alert

**Role:** Analyst+. Body: `{ "status": "reviewed", "note": "sudah dicek" }`.
`status` ∈ `new|reviewed|escalated|false_positive` (selain itu → `422`). Alert tidak ada → `404`.
Mencatat audit log. Response `200` → `{ "alert": { /* node */ } }`.

---

### Verification Cases

#### `GET /api/verification-cases` — Daftar case

**Role:** Analyst+. [List envelope](#response-list-paginated). Query: `status`, `risk_level`, `limit`, `offset`.

#### `GET /api/verification-cases/{case_id}` — Detail case

**Role:** Analyst+. `200` → `{ "case": { /* node */ } }`. Tidak ada → `404`.

#### `PATCH /api/verification-cases/{case_id}` — Update status verifikasi

**Role:** Analyst+ — kecuali status `closed` yang **hanya** Supervisor/Admin.

Body:

```json
{ "status": "verified_risk", "decisionNote": "indikasi kuat", "reviewerId": "user-analyst-001" }
```

`status` ∈ [verification status](#3-enum--nilai-valid) (selain itu → `422`). `reviewerId` opsional (default user saat ini).
`closed` oleh analyst → `403`. Case tidak ada → `404`. Mencatat audit log. Response `200` → `{ "case": { /* node */ } }`.

---

### Blacklist Candidates

#### `GET /api/blacklist-candidates` — Daftar kandidat

**Role:** Analyst+. [List envelope](#response-list-paginated). Query: `type` (entityType), `status`, `limit`, `offset`.

#### `GET /api/blacklist-candidates/{candidate_id}` — Detail kandidat

**Role:** Analyst+. `200` → `{ "candidate": { /* node */ } }`. Tidak ada → `404`.

#### `PATCH /api/blacklist-candidates/{candidate_id}/decision` — Keputusan kandidat

**Role:** Analyst+ — kecuali `confirmed_blacklist` & `recommended_for_blocking` yang
**hanya** Supervisor/Admin (keputusan akhir oleh manusia).

Body:

```json
{ "status": "confirmed_blacklist", "decisionNote": "disetujui setelah review" }
```

`status` ∈ [candidate status](#3-enum--nilai-valid) (selain itu → `422`). Status final oleh analyst → `403`.
Kandidat tidak ada → `404`. Mencatat audit log. Response `200` → `{ "candidate": { /* node */ } }`.

> ⚠️ `recommended_for_blocking` adalah **rekomendasi**, bukan eksekusi blokir.

---

### Traffic & Crawler Intelligence

> Semua data WAJIB `simulationOnly: true` (divalidasi server; jika `false` → `422`).
> Frontend wajib menampilkan label `simulation_only`.

#### `GET /api/traffic-events` — Daftar traffic event

**Role:** Analyst+. [List envelope](#response-list-paginated). Query: `event_type`, `limit`, `offset`.

#### `POST /api/traffic-events/import` — Import traffic log simulasi

**Role:** Admin. Body:

```json
{
  "items": [
    {
      "id": "te-1", "label": "Traffic te-1", "source": "simulation",
      "createdAt": "2026-06-18T00:00:00Z", "eventType": "spike",
      "timestamp": "2026-06-18T00:00:00Z", "sourceAlias": "src-a",
      "destinationDomain": "dummy.example", "requestCount": 99, "simulationOnly": true
    }
  ]
}
```

Response `201`: `{ "status": "success", "merged": 1, "errors": [] }` (`status` = `partial` bila ada error per-item).

#### `GET /api/crawler-findings` — Daftar crawler finding

**Role:** Analyst+. [List envelope](#response-list-paginated). Query: `finding_type`, `limit`, `offset`.

#### `POST /api/crawler-findings/import` — Import crawler finding dummy

**Role:** Admin. Body:

```json
{
  "items": [
    {
      "id": "cf-1", "label": "Crawler cf-1", "source": "simulation",
      "createdAt": "2026-06-18T00:00:00Z", "findingType": "redirect",
      "sourceUrl": "hxxp://dummy.example/a", "contentSummary": "promosi judol dummy",
      "matchedKeywords": ["slot", "gacor"], "capturedAt": "2026-06-18T00:00:00Z", "simulationOnly": true
    }
  ]
}
```

Response `201`: `{ "status": "success", "merged": 1, "errors": [] }`.

---

### Export

#### `GET /api/export/analysis/{node_type}/{node_id}` — Export hasil analisis

**Role:** Analyst+. Query: `format` (`json` default | `markdown`), `depth` (1–5), `limit`.

`format=json` → `200`:

```json
{
  "generatedAt": "2026-06-18T00:00:00Z",
  "simulationOnly": true,
  "disclaimer": "Hasil indikatif, memerlukan verifikasi manusia. Bukan vonis, tidak memicu pemblokiran nyata. Semua data simulasi.",
  "entity": { "type": "Domain", "id": "domain-001" },
  "analysis": { /* AnalysisResult */ }
}
```

`format=markdown` → `200` dengan `Content-Type: text/markdown` (body teks Markdown siap unduh/preview). Node tidak ada → `404`.

---

### Rules (Scoring)

#### `GET /api/rules` — Daftar rule scoring

**Role:** Analyst+.

```json
{ "rules": [ { "ruleId": "R-001", "title": "Domain/URL mengandung keyword judol", "weight": 15, "editableInPrototype": true } ] }
```

#### `PATCH /api/rules/{rule_id}` — Update bobot rule

**Role:** Admin. Body: `{ "weight": 42 }` (`weight` 0–100). Bersifat **in-memory**
(tidak persisten setelah restart) dan dicatat ke audit log. Rule tidak ada → `404`.

```json
{ "ruleId": "R-001", "title": "Domain/URL mengandung keyword judol", "oldWeight": 15, "weight": 42 }
```

---

### Import & Admin

#### `POST /api/import/dummy-data` — Import dataset dummy (bulk)

**Role:** Admin. Memakai MERGE (idempoten). Body besar — struktur:

```json
{
  "metadata": { "datasetId": "...", "version": "1.0", "scope": "...", "createdAt": "2026-06-18T00:00:00Z", "simulationOnly": true, "dataPolicy": ["..."] },
  "nodes": {
    "reports": [ /* ReportNode */ ],
    "urls": [ /* URLNode */ ],
    "domains": [ /* ... */ ]
    /* koleksi lain: victims, linkShorteners, socialMediaAccounts, phoneNumbers,
       bankAccounts, eWallets, qrisMerchants, apks, keywords, transactions,
       trafficEvents, crawlerFindings, blacklistEntities, blacklistCandidates,
       blacklistDecisions, clusters, evidences, riskAssessments, verificationCases,
       recommendations, users, auditLogs */
  },
  "relationships": [
    { "id": "rel-1", "type": "MENTIONS", "from": { "type": "Report", "id": "report-1" }, "to": { "type": "URL", "id": "url-1" }, "source": "import", "confidence": "medium", "weight": 1.0, "createdAt": "2026-06-18T00:00:00Z" }
  ],
  "demoScenarios": []
}
```

Aturan node penting: `BankAccount.maskedAccountNumber` & `EWallet.maskedWalletId` wajib
mengandung `****`; `TrafficEvent`/`CrawlerFinding` wajib `simulationOnly: true`.

Response `200`:

```json
{ "status": "success", "stats": { "nodes_merged": 120, "relationships_merged": 95, "skipped": 0, "errors": [] }, "message": "Import selesai: ..." }
```

#### `DELETE /api/admin/reset-dataset` — Reset seluruh data prototype

**Role:** Admin. Menghapus semua node & relationship, lalu mencatat audit log.

```json
{ "status": "success", "deletedNodes": 215 }
```

#### `GET /api/audit-logs` — Daftar audit log

**Role:** Supervisor+. [List envelope](#response-list-paginated), terbaru lebih dulu. Query: `action`, `target_type`, `limit`, `offset`.

Bentuk node `AuditLog`:

```json
{
  "id": "audit-...", "type": "AuditLog", "actorId": "user-analyst-001", "actorRole": "analyst",
  "action": "UPDATE_VERIFICATION_STATUS", "targetId": "case-1", "targetType": "VerificationCase",
  "oldValue": "needs_review", "newValue": "verified_risk", "note": "...", "timestamp": "2026-06-18T00:00:00Z"
}
```

---

## 6. Catatan untuk Frontend

- **Alur demo utama:** login → submit/import data → dashboard summary → entity search →
  graph explorer (neighborhood) → entity detail + risk analysis → evidence path →
  early warning → verification case / blacklist candidate (human review) → export.
- **CORS** dibuka untuk semua origin pada prototype (`*`).
- Simpan token di memori/secure storage; sertakan header `Authorization: Bearer` di tiap call.
- Endpoint `{node_type}/{node_id}`: pakai `type` & `id` dari objek node yang sudah didapat
  (mis. dari hasil `/api/entities` atau neighborhood), jangan tebak.
- Tampilkan disclaimer indikatif di UI hasil analisis & export; jangan render link ilegal sebagai anchor aktif.
- Untuk client TypeScript, generate model dari [`docs/openapi.json`](openapi.json)
  (mis. `openapi-typescript`) agar tipe selalu sinkron dengan backend.

### Contoh fetch (TypeScript)

```ts
const API = "http://localhost:8000";

async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API}/api/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Login gagal");
  return res.json(); // { access_token, token_type, role, user_id }
}

async function getDashboard(token: string) {
  const res = await fetch(`${API}/api/dashboard/summary`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

---

_Dokumen ini dihasilkan untuk backend SATPAM versi `0.1.0-week1`. Bila menambah/mengubah
endpoint, perbarui dokumen ini dan ekspor ulang `docs/openapi.json`._
```