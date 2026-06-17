import { DataTable, type DataTableColumn } from "../components/DataTable";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { mockVerificationCases } from "../data/mockVerificationCases";
import type { VerificationCase } from "../types/verification";

const columns: DataTableColumn<VerificationCase>[] = [
  { key: "caseId", header: "Case ID", render: (row) => <span className="font-medium">{row.caseId}</span> },
  { key: "entity", header: "Related Entity", render: (row) => row.relatedEntity },
  { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
  { key: "reviewer", header: "Reviewer", render: (row) => row.reviewer },
];

export function VerificationCasesPage() {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-semibold text-slate-950">Verification Cases</h2>
        <p className="mt-2 text-sm text-slate-600">
          Queue dummy untuk review analis. Tidak ada update status aktif pada Week 1.
        </p>
      </div>
      <DataTable columns={columns} data={mockVerificationCases} getRowKey={(row) => row.id} />
    </div>
  );
}
