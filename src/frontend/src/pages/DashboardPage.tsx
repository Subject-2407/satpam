import { Link } from "react-router-dom";
import { AlertTriangle, Database, FileText, ListChecks, ShieldAlert, UsersRound } from "lucide-react";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { PageHeader } from "../components/PageHeader";
import { RiskBadge } from "../components/RiskBadge";
import { ConfidenceBadge, NodeTypeBadge } from "../components/Badges";
import { SummaryCard } from "../components/SummaryCard";
import { AsyncBoundary } from "../components/States";
import { useApi } from "../hooks/useApi";
import { getDashboardSummary } from "../services/api";
import { safeLabel, titleCase } from "../lib/format";
import type { Confidence, GraphNode } from "../types/api";

const topEntityColumns: DataTableColumn<GraphNode>[] = [
  {
    key: "entity",
    header: "Entity",
    render: (row) => (
      <Link
        to={`/entities/${encodeURIComponent(row.type)}/${encodeURIComponent(row.id)}`}
        className="font-medium text-blue-700 hover:underline"
      >
        {safeLabel(row.label ?? row.id)}
      </Link>
    ),
  },
  { key: "type", header: "Type", render: (row) => <NodeTypeBadge type={row.type} /> },
  { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
  { key: "score", header: "Score", render: (row) => row.riskScore ?? "—" },
  {
    key: "confidence",
    header: "Confidence",
    render: (row) => <ConfidenceBadge confidence={row.confidence as Confidence | undefined} />,
  },
];

function Distribution({ title, data }: { title: string; data: Record<string, number | undefined> }) {
  const entries = Object.entries(data).filter(([, v]) => typeof v === "number");
  const total = entries.reduce((sum, [, v]) => sum + (v ?? 0), 0);
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-slate-400">Tidak ada data.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {entries.map(([key, value]) => {
            const pct = total > 0 ? Math.round(((value ?? 0) / total) * 100) : 0;
            return (
              <li key={key}>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">{titleCase(key)}</span>
                  <span className="font-semibold text-slate-900">{value}</span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-blue-500" style={{ width: `${pct}%` }} />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export function DashboardPage() {
  const { data, loading, error, refetch } = useApi(() => getDashboardSummary(8), []);

  const totals = data?.totals;
  const highRisk =
    (data?.entitiesByRiskLevel.high ?? 0) + (data?.entitiesByRiskLevel.critical ?? 0);
  const pendingVerification =
    (data?.verificationCasesByStatus.needs_review ?? 0) +
    (data?.verificationCasesByStatus.unreviewed ?? 0);

  const cards = [
    { label: "Total Reports", value: totals?.reports ?? 0, helper: "Laporan dummy masuk", icon: FileText },
    { label: "Total Entities", value: totals?.entities ?? 0, helper: "Node simulasi di graph", icon: Database },
    { label: "High Risk Entities", value: highRisk, helper: "Terindikasi high/critical", icon: UsersRound },
    { label: "Early Warning Alerts", value: totals?.alerts ?? 0, helper: "Perlu verifikasi awal", icon: AlertTriangle },
    { label: "Pending Verification", value: pendingVerification, helper: "Menunggu review analis", icon: ListChecks },
    { label: "Blacklist Candidates", value: totals?.blacklistCandidates ?? 0, helper: "Rekomendasi review", icon: ShieldAlert },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Prototype Dashboard"
        title="Ringkasan Risiko SATPAM"
        description="Agregat dari graph simulasi. Output bersifat indikatif, membutuhkan verifikasi manusia, dan tidak memicu pemblokiran otomatis."
      />

      <AsyncBoundary loading={loading} error={error} onRetry={refetch} loadingLabel="Memuat ringkasan dashboard…">
        {data && (
          <div className="space-y-6">
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {cards.map((card) => (
                <SummaryCard
                  key={card.label}
                  label={card.label}
                  value={card.value}
                  helper={card.helper}
                  icon={card.icon}
                />
              ))}
            </section>

            <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
              <Distribution title="Entitas per Risk Level" data={data.entitiesByRiskLevel} />
              <Distribution title="Alert per Status" data={data.alertsByStatus} />
              <Distribution title="Verification per Status" data={data.verificationCasesByStatus} />
              <Distribution title="Blacklist Candidate" data={data.blacklistCandidatesByStatus} />
            </section>

            <section className="space-y-3">
              <h3 className="text-base font-semibold text-slate-950">High Risk Entities</h3>
              <DataTable
                columns={topEntityColumns}
                data={data.topRiskEntities ?? []}
                getRowKey={(row) => `${row.type}:${row.id}`}
                emptyMessage="Belum ada entitas berisiko tinggi."
              />
            </section>
          </div>
        )}
      </AsyncBoundary>
    </div>
  );
}
