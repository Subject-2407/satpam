import type { EntityRecord } from "../types/entity";

export const mockEntities: EntityRecord[] = [
  {
    id: "entity-001",
    entity: "promo-demo.test",
    type: "domain",
    riskLevel: "high",
    confidence: 84,
    verificationStatus: "needs_review",
  },
  {
    id: "entity-002",
    entity: "0812****1111",
    type: "phone",
    riskLevel: "high",
    confidence: 80,
    verificationStatus: "unreviewed",
  },
  {
    id: "entity-003",
    entity: "1234****9999",
    type: "bank_account",
    riskLevel: "critical",
    confidence: 91,
    verificationStatus: "needs_review",
  },
  {
    id: "entity-004",
    entity: "id.demo.satpamapp",
    type: "apk",
    riskLevel: "medium",
    confidence: 67,
    verificationStatus: "verified_risk",
  },
  {
    id: "entity-005",
    entity: "pinjol-simulasi.example",
    type: "domain",
    riskLevel: "medium",
    confidence: 62,
    verificationStatus: "false_positive",
  },
];
