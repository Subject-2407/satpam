type StatusValue =
  | "unreviewed"
  | "needs_review"
  | "verified_risk"
  | "false_positive"
  | "escalated"
  | "closed"
  | "blacklist_candidate"
  | "needs_more_evidence"
  | "rejected_candidate"
  | "simulation_only";

const statusStyles: Record<StatusValue, string> = {
  unreviewed: "border-slate-200 bg-slate-50 text-slate-700",
  needs_review: "border-blue-200 bg-blue-50 text-blue-700",
  verified_risk: "border-emerald-200 bg-emerald-50 text-emerald-700",
  false_positive: "border-slate-200 bg-white text-slate-600",
  escalated: "border-amber-200 bg-amber-50 text-amber-700",
  closed: "border-slate-200 bg-slate-100 text-slate-600",
  blacklist_candidate: "border-red-200 bg-red-50 text-red-700",
  needs_more_evidence: "border-purple-200 bg-purple-50 text-purple-700",
  rejected_candidate: "border-slate-200 bg-white text-slate-600",
  simulation_only: "border-cyan-200 bg-cyan-50 text-cyan-700",
};

const statusLabels: Record<StatusValue, string> = {
  unreviewed: "Unreviewed",
  needs_review: "Needs Review",
  verified_risk: "Verified Risk",
  false_positive: "False Positive",
  escalated: "Escalated",
  closed: "Closed",
  blacklist_candidate: "Blacklist Candidate",
  needs_more_evidence: "Needs More Evidence",
  rejected_candidate: "Rejected Candidate",
  simulation_only: "Simulation Only",
};

export function StatusBadge({ status }: { status: StatusValue }) {
  return (
    <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${statusStyles[status]}`}>
      {statusLabels[status]}
    </span>
  );
}
