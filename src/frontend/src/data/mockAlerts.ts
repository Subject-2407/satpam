import type { AlertRecord } from "../types/alert";

export const mockAlerts: AlertRecord[] = [
  {
    id: "alert-001",
    alertType: "Terindikasi risiko relasi",
    entity: "promo-demo.test",
    riskLevel: "high",
    status: "needs_review",
    createdAt: "2026-06-10 09:20",
  },
  {
    id: "alert-002",
    alertType: "Rekomendasi review transaksi simulasi",
    entity: "1234****9999",
    riskLevel: "critical",
    status: "unreviewed",
    createdAt: "2026-06-10 10:05",
  },
  {
    id: "alert-003",
    alertType: "Simulation only crawler finding",
    entity: "bonus-risk-sim.test",
    riskLevel: "medium",
    status: "simulation_only",
    createdAt: "2026-06-10 11:15",
  },
  {
    id: "alert-004",
    alertType: "Perlu verifikasi kemiripan entitas",
    entity: "0856****2222",
    riskLevel: "medium",
    status: "needs_review",
    createdAt: "2026-06-10 12:30",
  },
];
