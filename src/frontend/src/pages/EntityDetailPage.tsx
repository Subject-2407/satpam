import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Download, GitBranch, Loader2 } from "lucide-react";
import { EarlyWarningList, EvidencePathCard, RiskAssessmentCard } from "../components/AnalysisView";
import { ConfidenceBadge, NodeTypeBadge, SimulationBadge } from "../components/Badges";
import { IndicativeNote, PageHeader } from "../components/PageHeader";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { AsyncBoundary } from "../components/States";
import { useApi, useMutation } from "../hooks/useApi";
import { getAnalysis, getEntity, getExportMarkdown } from "../services/api";
import { formatDateTime, safeLabel, titleCase } from "../lib/format";
import type { Confidence, GraphNode } from "../types/api";

// Properti standar yang sudah ditampilkan terpisah — disembunyikan dari grid generik.
const HIDDEN_PROPS = new Set([
  "id",
  "type",
  "label",
  "labels",
  "riskScore",
  "riskLevel",
  "confidence",
  "verificationStatus",
  "createdAt",
  "updatedAt",
]);

function PropertyGrid({ node }: { node: GraphNode }) {
  const extras = Object.entries(node).filter(
    ([key, value]) =>
      !HIDDEN_PROPS.has(key) &&
      (typeof value === "string" || typeof value === "number" || typeof value === "boolean"),
  );

  const base: [string, string][] = [
    ["Source", String(node.source ?? "—")],
    ["Created", formatDateTime(node.createdAt)],
    ["Updated", formatDateTime(node.updatedAt)],
  ];

  return (
    <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
      {base.map(([k, v]) => (
        <div key={k}>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{k}</dt>
          <dd className="text-sm text-slate-800">{v}</dd>
        </div>
      ))}
      {extras.map(([key, value]) => (
        <div key={key}>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{titleCase(key)}</dt>
          <dd className="break-words text-sm text-slate-800">{safeLabel(String(value))}</dd>
        </div>
      ))}
    </dl>
  );
}

export function EntityDetailPage() {
  const { nodeType = "", nodeId = "" } = useParams();

  const entityQuery = useApi(() => getEntity(nodeType, nodeId), [nodeType, nodeId]);
  const analysisQuery = useApi(() => getAnalysis(nodeType, nodeId), [nodeType, nodeId]);

  const exportMd = useMutation(async () => {
    const md = await getExportMarkdown(nodeType, nodeId);
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `satpam-analysis-${nodeType}-${nodeId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  });

  const entity = entityQuery.data?.entity;

  return (
    <div className="space-y-6">
      <Link to="/entities" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800">
        <ArrowLeft size={15} aria-hidden="true" /> Kembali ke Entities
      </Link>

      <AsyncBoundary
        loading={entityQuery.loading}
        error={entityQuery.error}
        onRetry={entityQuery.refetch}
        loadingLabel="Memuat detail entitas…"
      >
        {entity && (
          <>
            <PageHeader
              title={safeLabel(entity.label ?? entity.id)}
              eyebrow={titleCase(entity.type)}
              actions={
                <>
                  <Link
                    to={`/graph-explorer?type=${encodeURIComponent(entity.type)}&id=${encodeURIComponent(entity.id)}`}
                    className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    <GitBranch size={15} aria-hidden="true" /> Lihat di Graph
                  </Link>
                  <button
                    type="button"
                    onClick={() => exportMd.mutate().catch(() => undefined)}
                    disabled={exportMd.loading}
                    className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                  >
                    {exportMd.loading ? (
                      <Loader2 size={15} className="animate-spin" aria-hidden="true" />
                    ) : (
                      <Download size={15} aria-hidden="true" />
                    )}
                    Export Markdown
                  </button>
                </>
              }
            />

            {exportMd.error && <p className="text-sm text-red-600">{exportMd.error}</p>}

            <div className="flex flex-wrap items-center gap-2">
              <NodeTypeBadge type={entity.type} />
              <RiskBadge level={entity.riskLevel} />
              <ConfidenceBadge confidence={entity.confidence as Confidence | undefined} />
              <StatusBadge status={entity.verificationStatus} />
            </div>

            <section className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="mb-3 text-base font-semibold text-slate-950">Properti entitas</h3>
              <PropertyGrid node={entity} />
            </section>

            <IndicativeNote />

            <div className="grid gap-6 xl:grid-cols-2">
              <section className="space-y-3">
                <h3 className="text-base font-semibold text-slate-950">Risk Assessment</h3>
                <AsyncBoundary
                  loading={analysisQuery.loading}
                  error={analysisQuery.error}
                  onRetry={analysisQuery.refetch}
                  loadingLabel="Menghitung analisis…"
                >
                  <RiskAssessmentCard assessment={analysisQuery.data?.assessment ?? null} />
                </AsyncBoundary>
              </section>

              <section className="space-y-3">
                <h3 className="text-base font-semibold text-slate-950">Evidence Path</h3>
                <AsyncBoundary
                  loading={analysisQuery.loading}
                  error={analysisQuery.error}
                  onRetry={analysisQuery.refetch}
                  loadingLabel="Menghitung evidence path…"
                >
                  <EvidencePathCard path={analysisQuery.data?.evidencePath ?? null} />
                </AsyncBoundary>
              </section>
            </div>

            <section className="space-y-3">
              <h3 className="text-base font-semibold text-slate-950">Early Warnings</h3>
              {!analysisQuery.loading && !analysisQuery.error && (
                <EarlyWarningList warnings={analysisQuery.data?.earlyWarnings ?? []} />
              )}
            </section>
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}
