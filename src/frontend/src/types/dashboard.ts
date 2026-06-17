export type RiskLevel = "low" | "medium" | "high" | "critical";

export type DashboardMetricKey =
  | "totalReports"
  | "totalEntities"
  | "highRiskEntities"
  | "earlyWarningAlerts"
  | "pendingVerification"
  | "blacklistCandidates";

export interface SummaryMetric {
  key: DashboardMetricKey;
  label: string;
  value: string;
  helper: string;
}

export interface DashboardAlert {
  id: string;
  alertType: string;
  entity: string;
  riskLevel: RiskLevel;
  status: "unreviewed" | "needs_review" | "simulation_only";
  createdAt: string;
}

export interface DashboardEntity {
  id: string;
  entity: string;
  type: string;
  riskLevel: RiskLevel;
  confidence: number;
  verificationStatus: "unreviewed" | "needs_review" | "verified_risk";
}

export interface DashboardVerificationCase {
  id: string;
  caseId: string;
  relatedEntity: string;
  riskLevel: RiskLevel;
  status: "unreviewed" | "needs_review" | "escalated";
  reviewer: string;
}
