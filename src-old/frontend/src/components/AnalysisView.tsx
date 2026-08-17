import { ArrowRight } from "lucide-react";
import { RiskBadge, PriorityBadge } from "./RiskBadge";
import { ConfidenceBadge, SimulationBadge } from "./Badges";
import { safeLabel, titleCase } from "../lib/format";
import type {
  EarlyWarning,
  EvidencePath,
  GraphNode,
  NodeRef,
  RiskAssessment,
} from "../types/api";

function isGraphNode(value: GraphNode | NodeRef): value is GraphNode {
  return "label" in value || "riskLevel" in value;
}

export function RiskAssessmentCard({ assessment }: { assessment: RiskAssessment | null }) {
  if (!assessment) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
        Belum ada risk assessment untuk entitas ini.
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-baseline gap-1">
          <span className="text-3xl font-semibold text-slate-950">{assessment.score}</span>
          <span className="text-sm text-slate-400">/100</span>
        </div>
        <RiskBadge level={assessment.level} />
        <span className="inline-flex items-center gap-1 text-sm text-slate-500">
          Confidence: <ConfidenceBadge confidence={assessment.confidence} />
        </span>
      </div>

      {assessment.explanation && (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm leading-relaxed text-slate-700">
          {assessment.explanation}
        </p>
      )}

      {assessment.triggeredRules?.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-slate-900">Rule yang aktif</h4>
          <ul className="space-y-2">
            {assessment.triggeredRules.map((rule) => (
              <li
                key={rule.ruleId}
                className="flex items-start justify-between gap-3 rounded-md border border-slate-200 px-3 py-2"
              >
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    <span className="text-slate-400">{rule.ruleId}</span> · {rule.title}
                  </p>
                  {rule.evidence && <p className="mt-0.5 text-xs text-slate-500">{rule.evidence}</p>}
                </div>
                <span className="shrink-0 rounded-md bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">
                  +{rule.weight}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {assessment.recommendations?.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-slate-900">Rekomendasi tindakan</h4>
          <ul className="space-y-2">
            {assessment.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 rounded-md border border-slate-200 px-3 py-2">
                <PriorityBadge priority={rec.priority} />
                <div>
                  <p className="text-sm font-medium text-slate-800">{titleCase(rec.actionType)}</p>
                  <p className="text-xs text-slate-500">{rec.reason}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function EvidencePathCard({ path }: { path: EvidencePath | null }) {
  if (!path) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
        Tidak ada evidence path ditemukan.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="text-slate-500">
          Cost: <strong className="text-slate-800">{path.cost}</strong>
        </span>
        <span className="text-slate-500">
          Risk score: <strong className="text-slate-800">{path.riskScore}</strong>
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {path.nodes.map((node, i) => {
          const label = isGraphNode(node) ? safeLabel(node.label ?? node.id) : safeLabel(node.id);
          return (
            <span key={i} className="flex items-center gap-2">
              <span className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs">
                <span className="font-medium text-slate-800">{label}</span>
                <span className="ml-1 text-slate-400">{node.type}</span>
              </span>
              {i < path.nodes.length - 1 && <ArrowRight size={14} className="text-slate-400" aria-hidden="true" />}
            </span>
          );
        })}
      </div>

      {path.explanation && <p className="text-sm leading-relaxed text-slate-600">{path.explanation}</p>}
    </div>
  );
}

export function EarlyWarningList({ warnings }: { warnings: EarlyWarning[] }) {
  if (!warnings || warnings.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
        Tidak ada early warning untuk entitas ini.
      </div>
    );
  }
  return (
    <ul className="space-y-2">
      {warnings.map((w) => (
        <li key={w.id} className="rounded-lg border border-slate-200 bg-white p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-900">{w.alertType}</span>
            <PriorityBadge priority={w.priority} />
            {w.simulationOnly && <SimulationBadge />}
          </div>
          <p className="mt-1 text-sm text-slate-600">{w.reason}</p>
          {w.ruleIds?.length > 0 && (
            <p className="mt-1 text-xs text-slate-400">Rule: {w.ruleIds.join(", ")}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
