import type { RiskLevel } from "./dashboard";

export type VerificationStatus =
  | "unreviewed"
  | "needs_review"
  | "verified_risk"
  | "false_positive"
  | "escalated"
  | "closed";

export interface VerificationCase {
  id: string;
  caseId: string;
  relatedEntity: string;
  riskLevel: RiskLevel;
  status: VerificationStatus;
  reviewer: string;
}
