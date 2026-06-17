import type {
  DashboardAlert,
  DashboardEntity,
  DashboardVerificationCase,
  SummaryMetric,
} from "../types/dashboard";

export const summaryMetrics: SummaryMetric[] = [
  {
    key: "totalReports",
    label: "Total Reports",
    value: "128",
    helper: "Laporan dummy masuk",
  },
  {
    key: "totalEntities",
    label: "Total Entities",
    value: "412",
    helper: "Node simulasi terdeteksi",
  },
  {
    key: "highRiskEntities",
    label: "High Risk Entities",
    value: "34",
    helper: "Terindikasi high/critical",
  },
  {
    key: "earlyWarningAlerts",
    label: "Early Warning Alerts",
    value: "16",
    helper: "Perlu verifikasi awal",
  },
  {
    key: "pendingVerification",
    label: "Pending Verification",
    value: "21",
    helper: "Menunggu review analis",
  },
  {
    key: "blacklistCandidates",
    label: "Blacklist Candidates",
    value: "9",
    helper: "Rekomendasi review",
  },
];

export const recentAlerts: DashboardAlert[] = [
  {
    id: "alert-001",
    alertType: "Similar Entity Alert",
    entity: "promo-demo.test",
    riskLevel: "high",
    status: "needs_review",
    createdAt: "2026-06-10 09:20",
  },
  {
    id: "alert-002",
    alertType: "Payment Fan-in Alert",
    entity: "1234****9999",
    riskLevel: "critical",
    status: "unreviewed",
    createdAt: "2026-06-10 10:05",
  },
  {
    id: "alert-003",
    alertType: "Crawler Finding Simulation",
    entity: "bonus-risk-sim.test",
    riskLevel: "medium",
    status: "simulation_only",
    createdAt: "2026-06-10 11:15",
  },
];

export const highRiskEntities: DashboardEntity[] = [
  {
    id: "entity-001",
    entity: "bonus-risk-sim.test",
    type: "domain",
    riskLevel: "critical",
    confidence: 88,
    verificationStatus: "needs_review",
  },
  {
    id: "entity-002",
    entity: "0812****1111",
    type: "phone",
    riskLevel: "high",
    confidence: 81,
    verificationStatus: "unreviewed",
  },
  {
    id: "entity-003",
    entity: "id.demo.satpamapp",
    type: "apk",
    riskLevel: "high",
    confidence: 76,
    verificationStatus: "verified_risk",
  },
];

export const verificationQueue: DashboardVerificationCase[] = [
  {
    id: "verify-001",
    caseId: "CASE-SIM-001",
    relatedEntity: "promo-demo.test",
    riskLevel: "high",
    status: "needs_review",
    reviewer: "Analyst Prototype",
  },
  {
    id: "verify-002",
    caseId: "CASE-SIM-002",
    relatedEntity: "9876****0000",
    riskLevel: "critical",
    status: "unreviewed",
    reviewer: "Unassigned",
  },
  {
    id: "verify-003",
    caseId: "CASE-SIM-003",
    relatedEntity: "pinjol-simulasi.example",
    riskLevel: "medium",
    status: "escalated",
    reviewer: "Analyst Prototype",
  },
];
