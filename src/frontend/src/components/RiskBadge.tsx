import type { Priority, RiskLevel } from "../types/api";

const riskStyles: Record<RiskLevel, string> = {
  low: "border-emerald-200 bg-emerald-50 text-emerald-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  critical: "border-red-200 bg-red-50 text-red-700",
};

export function RiskBadge({ level }: { level?: RiskLevel | null }) {
  if (!level) return <span className="text-slate-400">—</span>;
  return (
    <span
      className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold capitalize ${riskStyles[level]}`}
    >
      {level}
    </span>
  );
}

// Prioritas alert memakai skala yang sama dengan risk level.
export function PriorityBadge({ priority }: { priority?: Priority | null }) {
  return <RiskBadge level={priority ?? null} />;
}
