import type { VerificationCase } from "../types/verification";

export const mockVerificationCases: VerificationCase[] = [
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
    relatedEntity: "1234****9999",
    riskLevel: "critical",
    status: "unreviewed",
    reviewer: "Unassigned",
  },
  {
    id: "verify-003",
    caseId: "CASE-SIM-003",
    relatedEntity: "id.demo.satpamapp",
    riskLevel: "medium",
    status: "verified_risk",
    reviewer: "Analyst Prototype",
  },
  {
    id: "verify-004",
    caseId: "CASE-SIM-004",
    relatedEntity: "0856****2222",
    riskLevel: "low",
    status: "false_positive",
    reviewer: "Analyst Prototype",
  },
  {
    id: "verify-005",
    caseId: "CASE-SIM-005",
    relatedEntity: "bonus-risk-sim.test",
    riskLevel: "high",
    status: "escalated",
    reviewer: "Supervisor Prototype",
  },
];
