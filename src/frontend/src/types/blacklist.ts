import type { RiskLevel } from "./dashboard";

export type BlacklistCandidateStatus =
  | "blacklist_candidate"
  | "needs_more_evidence"
  | "rejected_candidate"
  | "false_positive"
  | "escalated";

export interface BlacklistCandidate {
  id: string;
  entity: string;
  type: "domain" | "phone" | "bank_account" | "ewallet" | "apk";
  riskLevel: RiskLevel;
  riskScore: number;
  confidence: number;
  reviewStatus: BlacklistCandidateStatus;
}
