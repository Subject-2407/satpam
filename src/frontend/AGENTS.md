# AGENTS.md

## 1. Project Identity

Project name: SATPAM Frontend

SATPAM stands for Search-based AI Threat Prevention and Mapping.

This repository is only for the frontend prototype of SATPAM. SATPAM is a simulation-only academic prototype for risk analysis dashboard, graph intelligence visualization, report intake UI, early warning review, and human verification workflow.

The current task is limited to Week 1 frontend work only.

## 2. Current Week Scope

The agent must only work on:

1. Setting up a React + TypeScript + Vite frontend project.
2. Setting up Tailwind CSS.
3. Setting up React Router DOM.
4. Creating the initial dashboard layout.
5. Creating a sidebar.
6. Creating a topbar.
7. Creating a main content area.
8. Creating the initial Dashboard page using mock data.
9. Creating placeholder pages for planned frontend modules.
10. Preparing a clean folder structure for future development.

Do not implement anything outside this Week 1 scope.

## 3. Hard Scope Limit

The agent must not create or implement:

1. Backend API logic.
2. FastAPI backend files.
3. Database connection.
4. Neo4j driver or Neo4j queries.
5. Entity extraction logic.
6. Normalization logic.
7. Deduplication logic.
8. Graph builder logic.
9. BFS algorithm.
10. A* Search algorithm.
11. Dijkstra or UCS algorithm.
12. Risk scoring engine.
13. Early warning engine.
14. Blacklist decision logic.
15. Human verification backend workflow.
16. Authentication system.
17. RBAC implementation.
18. Audit log backend.
19. Real API integration.
20. Real crawler.
21. Real scraper.
22. Real traffic monitoring.
23. Real blocking mechanism.
24. Any production-grade AI or ML feature.

If a future feature is needed visually, create only a static placeholder page or dummy UI section.

## 4. Tech Stack

Use only the following frontend stack:

1. React.
2. TypeScript.
3. Vite.
4. Tailwind CSS.
5. React Router DOM.
6. Lucide React.

Do not add additional UI libraries unless explicitly requested.

Do not use:

1. Next.js.
2. Vue.
3. Angular.
4. Bootstrap.
5. Material UI.
6. Chakra UI.
7. Redux.
8. Zustand.
9. React Query.
10. Axios, unless explicitly requested.
11. Cytoscape.js in Week 1.

Cytoscape.js is planned for future graph visualization, but for Week 1 the Graph Explorer page must remain a placeholder.

## 5. Expected Folder Structure

Use this folder structure:

```text
src/
  components/
    DataTable.tsx
    RiskBadge.tsx
    Sidebar.tsx
    StatusBadge.tsx
    SummaryCard.tsx
    Topbar.tsx

  layouts/
    DashboardLayout.tsx

  pages/
    DashboardPage.tsx
    ReportIntakePage.tsx
    GraphExplorerPage.tsx
    EntitiesPage.tsx
    EarlyWarningPage.tsx
    VerificationCasesPage.tsx
    BlacklistCandidatePage.tsx

  routes/
    AppRoutes.tsx

  data/
    mockDashboard.ts
    mockEntities.ts
    mockAlerts.ts
    mockVerificationCases.ts
    mockBlacklistCandidates.ts

  types/
    dashboard.ts
    entity.ts
    alert.ts
    verification.ts
    blacklist.ts

  services/
    api.ts

  App.tsx
  main.tsx
  index.css
```

Do not create unnecessary folders.

Do not create backend-related folders such as:

```text
server/
api/
database/
neo4j/
engine/
algorithm/
```

The `src/services/api.ts` file may exist only as a future integration placeholder.

## 6. Required Pages

Create only these pages for Week 1:

1. DashboardPage.
2. ReportIntakePage.
3. GraphExplorerPage.
4. EntitiesPage.
5. EarlyWarningPage.
6. VerificationCasesPage.
7. BlacklistCandidatePage.

Do not create additional pages unless explicitly requested.

Do not create:

1. Login page.
2. Register page.
3. Admin user management page.
4. Rule editor page.
5. Full traffic intelligence page.
6. Full crawler intelligence page.
7. Export page.
8. Settings page.

## 7. Sidebar Menu

The sidebar must contain exactly these menu items:

1. Dashboard.
2. Report Intake.
3. Graph Explorer.
4. Entities.
5. Early Warning.
6. Verification Cases.
7. Blacklist Candidate.

Each menu item must route to its corresponding page.

The sidebar should make the app look like an analyst dashboard, not a public website landing page.

## 8. Topbar Requirements

The topbar must include:

1. Project label: SATPAM.
2. Subtitle or small label: Search-based AI Threat Prevention and Mapping.
3. Badge: Simulation Only.
4. Badge or text: Human Verification Required.

Do not include real user authentication controls in Week 1.

Allowed placeholder user text:

```text
Analyst Prototype
```

Do not implement real login, logout, session, or role switching.

## 9. DashboardPage Requirements

The DashboardPage must show initial mock analytics.

Required summary cards:

1. Total Reports.
2. Total Entities.
3. High Risk Entities.
4. Early Warning Alerts.
5. Pending Verification.
6. Blacklist Candidates.

Required dashboard sections:

1. Recent Alerts.
2. High Risk Entities.
3. Verification Queue.

All data must come from mock data files in `src/data`.

Do not fetch real data from an API.

## 10. ReportIntakePage Requirements

For Week 1, this page must only be a placeholder.

It may include:

1. Page title: Report Intake.
2. Short description: Form laporan dummy akan dibuat pada tahap berikutnya.
3. Static placeholder card showing future fields:
   - Deskripsi laporan.
   - URL/domain.
   - Nomor WhatsApp.
   - Rekening bank.
   - E-wallet.
   - QRIS.
   - APK/package name.
   - Kategori dugaan.

Do not implement a working submit form in Week 1.

Do not create POST request logic.

## 11. GraphExplorerPage Requirements

For Week 1, this page must only be a placeholder.

It may include:

1. Page title: Graph Explorer.
2. Placeholder graph canvas area.
3. Text: Visualisasi graph interaktif akan ditambahkan pada tahap berikutnya.
4. Static labels for planned filters:
   - Entity type.
   - Risk level.
   - Verification status.
   - Source.

Do not install Cytoscape.js in Week 1.

Do not implement graph node rendering.

Do not implement graph algorithms.

## 12. EntitiesPage Requirements

Create a simple dummy table.

Required columns:

1. Entity.
2. Type.
3. Risk Level.
4. Confidence.
5. Verification Status.

Use dummy data only.

Sensitive-looking data must be masked.

Examples:

```text
0812****1111
1234****9999
promo-demo.test
id.demo.app
```

Do not create entity detail page in Week 1.

Do not implement search, filter, or API integration unless explicitly requested.

## 13. EarlyWarningPage Requirements

Create a simple dummy table.

Required columns:

1. Alert Type.
2. Entity.
3. Risk Level.
4. Status.
5. Created At.

Use dummy data only.

Use careful wording such as:

1. Terindikasi risiko.
2. Perlu verifikasi.
3. Rekomendasi review.
4. Simulation only.

Do not implement alert status update in Week 1.

## 14. VerificationCasesPage Requirements

Create a simple dummy table.

Required columns:

1. Case ID.
2. Related Entity.
3. Risk Level.
4. Status.
5. Reviewer.

Use dummy data only.

Allowed statuses:

1. unreviewed.
2. needs_review.
3. verified_risk.
4. false_positive.
5. escalated.
6. closed.

Do not create working status update logic in Week 1.

Do not create supervisor approval logic in Week 1.

## 15. BlacklistCandidatePage Requirements

Create a simple dummy table.

Required columns:

1. Entity.
2. Type.
3. Risk Score.
4. Confidence.
5. Review Status.

Use dummy data only.

Allowed candidate statuses:

1. blacklist_candidate.
2. needs_more_evidence.
3. rejected_candidate.
4. false_positive.
5. escalated.

Do not use `confirmed_blacklist` as an automatic result.

Do not create recommended blocking action logic in Week 1.

Add a clear note:

```text
Blacklist Candidate adalah status rekomendasi review, bukan keputusan final dan bukan aksi blokir otomatis.
```

## 16. Mock Data Rules

All mock data must be fictional.

Use safe dummy values only.

Allowed examples:

```text
promo-demo.test
bonus-risk-sim.test
pinjol-simulasi.example
0812****1111
0856****2222
1234****9999
9876****0000
id.demo.satpamapp
```

Do not use:

1. Real illegal gambling domains.
2. Real illegal lending domains.
3. Real phone numbers.
4. Real bank accounts.
5. Real e-wallet IDs.
6. Real victim identities.
7. Real APK package from illegal apps.
8. Real URLs that can be clicked.

Do not make suspicious-looking URLs clickable.

## 17. UI Language Rules

The UI must use indicative and careful language.

Use these terms:

1. Terindikasi.
2. Risiko.
3. Perlu verifikasi.
4. Kandidat blacklist.
5. Rekomendasi review.
6. Human verification required.
7. Simulation only.
8. Data dummy.
9. Prototype.

Avoid these terms:

1. Terbukti pelaku.
2. Pasti ilegal.
3. Kriminal.
4. Tersangka.
5. Blokir otomatis.
6. Auto-block.
7. Confirmed without review.
8. Final blacklist otomatis.

The frontend must clearly communicate that SATPAM provides risk indication and review support, not legal judgment.

## 18. Styling Direction

Use a clean analyst dashboard style.

Preferred visual direction:

1. Modern clean dashboard.
2. Light mode.
3. Professional security/risk analysis feel.
4. Clear hierarchy.
5. Easy-to-read tables.
6. Consistent badges for risk and status.

Avoid:

1. Overly dark hacker theme.
2. Excessive animation.
3. Landing page style.
4. Marketing website style.
5. Too many colors.
6. Complex charts in Week 1.

Risk badge suggestions:

1. Low.
2. Medium.
3. High.
4. Critical.

Status badge suggestions:

1. unreviewed.
2. needs_review.
3. verified_risk.
4. false_positive.
5. escalated.
6. closed.
7. blacklist_candidate.

## 19. Component Rules

Create reusable components only when needed for Week 1.

Required reusable components:

1. Sidebar.
2. Topbar.
3. SummaryCard.
4. RiskBadge.
5. StatusBadge.
6. DataTable.

Do not overengineer components.

Do not create complex component abstractions.

Do not create a full design system.

## 20. TypeScript Rules

Use TypeScript types for mock data.

Required type files:

1. `src/types/dashboard.ts`
2. `src/types/entity.ts`
3. `src/types/alert.ts`
4. `src/types/verification.ts`
5. `src/types/blacklist.ts`

Use simple and readable types.

Do not use `any` unless there is no reasonable alternative.

Do not create complex generic types.

## 21. Service Layer Rule

Create `src/services/api.ts` only as a placeholder for future integration.

Allowed content:

1. Base API placeholder.
2. Comment explaining that real API integration will be added later.
3. Optional constant for future base URL.

Do not call real endpoints.

Do not use fetch in production-like logic for Week 1.

Do not connect to backend.

## 22. Routing Rules

Use React Router DOM.

Required routes:

```text
/
 /report-intake
 /graph-explorer
 /entities
 /early-warning
 /verification-cases
 /blacklist-candidate
```

The root route `/` must show DashboardPage.

All pages must use DashboardLayout.

## 23. Quality Checklist

Before finishing, verify:

1. The project runs with `npm run dev`.
2. There are no broken imports.
3. There are no unused required files.
4. Sidebar navigation works.
5. Dashboard loads mock data.
6. Placeholder pages render correctly.
7. No backend logic is created.
8. No graph algorithm is created.
9. No real data is used.
10. No illegal URL is clickable.
11. Sensitive-looking values are masked.
12. UI labels use careful, non-accusatory language.
13. `Simulation Only` is visible.
14. `Human Verification Required` is visible.

## 24. Expected Agent Output

When asked to implement Week 1 frontend, the agent must provide:

1. Installation commands.
2. Folder structure.
3. Code for each required file.
4. Explanation of how to run the project.
5. A short checklist of what has been completed.

The agent must not output features beyond Week 1.

## 25. Completion Definition

Week 1 frontend is complete when:

1. React + TypeScript + Vite project is ready.
2. Tailwind CSS is configured.
3. React Router DOM is configured.
4. DashboardLayout is created.
5. Sidebar is visible.
6. Topbar is visible.
7. DashboardPage displays mock summary cards and dummy sections.
8. All required placeholder pages are reachable from sidebar.
9. Mock data is separated in `src/data`.
10. Type definitions are separated in `src/types`.
11. No backend, database, graph algorithm, or real AI logic is implemented.

## 26. Final Reminder for Agent

Stay inside Week 1 scope.

Build only the frontend foundation and initial dashboard layout.

Do not attempt to complete the entire SATPAM system.

Do not create logic that belongs to backend, AI engine, graph engine, database, verification workflow, or production security system.
