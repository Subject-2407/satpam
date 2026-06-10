import type { RiskLevel } from "./dashboard";

export interface EntityRecord {
  id: string;
  entity: string;
  type: "domain" | "phone" | "bank_account" | "ewallet" | "qris" | "apk";
  riskLevel: RiskLevel;
  confidence: number;
  verificationStatus:
    | "unreviewed"
    | "needs_review"
    | "verified_risk"
    | "false_positive"
    | "escalated"
    | "closed";
}
