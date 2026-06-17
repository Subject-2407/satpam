import type { RiskLevel } from "../types/api";

// Warna konsisten per risk level (dipakai di graph & legenda).
export const RISK_COLORS: Record<RiskLevel, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#dc2626",
};

export const RISK_ORDER: RiskLevel[] = ["low", "medium", "high", "critical"];

export function riskColor(level?: RiskLevel | null): string {
  if (level && level in RISK_COLORS) return RISK_COLORS[level];
  return "#94a3b8"; // slate-400 untuk yang tidak diketahui
}
