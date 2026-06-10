import { DataTable, type DataTableColumn } from "../components/DataTable";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { mockEntities } from "../data/mockEntities";
import type { EntityRecord } from "../types/entity";

const columns: DataTableColumn<EntityRecord>[] = [
  { key: "entity", header: "Entity", render: (row) => <span className="font-medium">{row.entity}</span> },
  { key: "type", header: "Type", render: (row) => row.type },
  { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
  { key: "confidence", header: "Confidence", render: (row) => `${row.confidence}%` },
  { key: "status", header: "Verification Status", render: (row) => <StatusBadge status={row.verificationStatus} /> },
];

export function EntitiesPage() {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-semibold text-slate-950">Entities</h2>
        <p className="mt-2 text-sm text-slate-600">Daftar entitas dummy dengan nilai sensitif yang sudah dimasking.</p>
      </div>
      <DataTable columns={columns} data={mockEntities} getRowKey={(row) => row.id} />
    </div>
  );
}
