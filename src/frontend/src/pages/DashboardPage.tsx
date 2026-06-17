import { AlertTriangle, Database, FileText, ListChecks, ShieldAlert, UsersRound } from "lucide-react";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { SummaryCard } from "../components/SummaryCard";
import {
  highRiskEntities,
  recentAlerts,
  summaryMetrics,
  verificationQueue,
} from "../data/mockDashboard";
import type { DashboardAlert, DashboardEntity, DashboardVerificationCase } from "../types/dashboard";

const metricIcons = [FileText, Database, UsersRound, AlertTriangle, ListChecks, ShieldAlert];

const alertColumns: DataTableColumn<DashboardAlert>[] = [
  { key: "alertType", header: "Alert Type", render: (row) => row.alertType },
  { key: "entity", header: "Entity", render: (row) => <span className="font-medium">{row.entity}</span> },
  { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
];

const entityColumns: DataTableColumn<DashboardEntity>[] = [
  { key: "entity", header: "Entity", render: (row) => <span className="font-medium">{row.entity}</span> },
  { key: "type", header: "Type", render: (row) => row.type },
  { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
  { key: "confidence", header: "Confidence", render: (row) => `${row.confidence}%` },
  { key: "status", header: "Verification Status", render: (row) => <StatusBadge status={row.verificationStatus} /> },
];

const verificationColumns: DataTableColumn<DashboardVerificationCase>[] = [
  { key: "caseId", header: "Case ID", render: (row) => <span className="font-medium">{row.caseId}</span> },
  { key: "entity", header: "Related Entity", render: (row) => row.relatedEntity },
  { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
  { key: "reviewer", header: "Reviewer", render: (row) => row.reviewer },
];

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-blue-700">Prototype Dashboard</p>
        <h2 className="mt-1 text-2xl font-semibold text-slate-950">Ringkasan Risiko SATPAM</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Semua angka berasal dari mock data. Output bersifat indikatif, membutuhkan verifikasi manusia, dan tidak
          memicu pemblokiran otomatis.
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {summaryMetrics.map((metric, index) => (
          <SummaryCard
            key={metric.key}
            label={metric.label}
            value={metric.value}
            helper={metric.helper}
            icon={metricIcons[index]}
          />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-slate-950">Recent Alerts</h3>
          <DataTable columns={alertColumns} data={recentAlerts} getRowKey={(row) => row.id} />
        </div>
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-slate-950">High Risk Entities</h3>
          <DataTable columns={entityColumns} data={highRiskEntities} getRowKey={(row) => row.id} />
        </div>
      </section>

      <section className="space-y-3">
        <h3 className="text-base font-semibold text-slate-950">Verification Queue</h3>
        <DataTable columns={verificationColumns} data={verificationQueue} getRowKey={(row) => row.id} />
      </section>
    </div>
  );
}
