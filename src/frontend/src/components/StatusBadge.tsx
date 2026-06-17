import { titleCase } from "../lib/format";

// Gaya per status — mencakup verification status, alert status, dan blacklist
// candidate status (lihat docs/API.md). String tak dikenal memakai gaya default.
const statusStyles: Record<string, string> = {
  // Verification
  unreviewed: "border-slate-200 bg-slate-50 text-slate-700",
  needs_review: "border-blue-200 bg-blue-50 text-blue-700",
  verified_risk: "border-emerald-200 bg-emerald-50 text-emerald-700",
  false_positive: "border-slate-200 bg-white text-slate-600",
  escalated: "border-amber-200 bg-amber-50 text-amber-700",
  closed: "border-slate-200 bg-slate-100 text-slate-600",
  // Alert
  new: "border-blue-200 bg-blue-50 text-blue-700",
  reviewed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  // Blacklist candidate
  not_candidate: "border-slate-200 bg-white text-slate-500",
  blacklist_candidate: "border-red-200 bg-red-50 text-red-700",
  needs_more_evidence: "border-purple-200 bg-purple-50 text-purple-700",
  rejected_candidate: "border-slate-200 bg-white text-slate-600",
  confirmed_blacklist: "border-red-300 bg-red-100 text-red-800",
  recommended_for_blocking: "border-orange-200 bg-orange-50 text-orange-700",
  // Lain
  simulation_only: "border-cyan-200 bg-cyan-50 text-cyan-700",
};

const DEFAULT_STYLE = "border-slate-200 bg-slate-50 text-slate-700";

export function StatusBadge({ status }: { status?: string | null }) {
  if (!status) return <span className="text-slate-400">—</span>;
  const style = statusStyles[status] ?? DEFAULT_STYLE;
  return (
    <span className={`inline-flex whitespace-nowrap rounded-md border px-2 py-1 text-xs font-semibold ${style}`}>
      {titleCase(status)}
    </span>
  );
}
