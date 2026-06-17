import { DataTable, type DataTableColumn } from "../components/DataTable";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { mockAlerts } from "../data/mockAlerts";
import type { AlertRecord } from "../types/alert";

const columns: DataTableColumn<AlertRecord>[] = [
  { key: "alertType", header: "Alert Type", render: (row) => row.alertType },
  { key: "entity", header: "Entity", render: (row) => <span className="font-medium">{row.entity}</span> },
  { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
  { key: "createdAt", header: "Created At", render: (row) => row.createdAt },
];

export function EarlyWarningPage() {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-semibold text-slate-950">Early Warning</h2>
        <p className="mt-2 text-sm text-slate-600">
          Terindikasi risiko dan rekomendasi review dari data dummy. Simulation only.
        </p>
      </div>
      <DataTable columns={columns} data={mockAlerts} getRowKey={(row) => row.id} />
    </div>
  );
}
