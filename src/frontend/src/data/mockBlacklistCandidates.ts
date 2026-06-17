import type { BlacklistCandidate } from "../types/blacklist";

export const mockBlacklistCandidates: BlacklistCandidate[] = [
  {
    id: "candidate-001",
    entity: "bonus-risk-sim.test",
    type: "domain",
    riskLevel: "critical",
    riskScore: 92,
    confidence: 88,
    reviewStatus: "blacklist_candidate",
  },
  {
    id: "candidate-002",
    entity: "1234****9999",
    type: "bank_account",
    riskLevel: "high",
    riskScore: 84,
    confidence: 79,
    reviewStatus: "needs_more_evidence",
  },
  {
    id: "candidate-003",
    entity: "0812****1111",
    type: "phone",
    riskLevel: "high",
    riskScore: 78,
    confidence: 74,
    reviewStatus: "escalated",
  },
  {
    id: "candidate-004",
    entity: "pinjol-simulasi.example",
    type: "domain",
    riskLevel: "medium",
    riskScore: 54,
    confidence: 61,
    reviewStatus: "rejected_candidate",
  },
];
