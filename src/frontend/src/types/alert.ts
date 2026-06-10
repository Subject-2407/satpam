import type { RiskLevel } from "./dashboard";

export interface AlertRecord {
  id: string;
  alertType: string;
  entity: string;
  riskLevel: RiskLevel;
  status: "unreviewed" | "needs_review" | "simulation_only";
  createdAt: string;
}
