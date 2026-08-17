import { titleCase } from "../lib/format";
import type { Confidence } from "../types/api";

const confidenceStyles: Record<Confidence, string> = {
  low: "border-slate-200 bg-slate-50 text-slate-600",
  medium: "border-blue-200 bg-blue-50 text-blue-700",
  high: "border-indigo-200 bg-indigo-50 text-indigo-700",
};

export function ConfidenceBadge({ confidence }: { confidence?: Confidence | null }) {
  if (!confidence) return <span className="text-slate-400">—</span>;
  return (
    <span
      className={`inline-flex rounded-md border px-2 py-1 text-xs font-medium capitalize ${confidenceStyles[confidence]}`}
    >
      {confidence}
    </span>
  );
}

// Badge netral untuk tipe node/entitas.
export function NodeTypeBadge({ type }: { type?: string | null }) {
  if (!type) return <span className="text-slate-400">—</span>;
  return (
    <span className="inline-flex whitespace-nowrap rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium text-slate-600">
      {titleCase(type)}
    </span>
  );
}

// Label "Simulation Only" yang dipakai pada data traffic/crawler & hasil analisis.
export function SimulationBadge({ className = "" }: { className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-md border border-cyan-200 bg-cyan-50 px-2 py-1 text-xs font-semibold text-cyan-700 ${className}`}
    >
      Simulation Only
    </span>
  );
}
