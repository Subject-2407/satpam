import { DataTable, type DataTableColumn } from "../components/DataTable";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { mockBlacklistCandidates } from "../data/mockBlacklistCandidates";
import type { BlacklistCandidate } from "../types/blacklist";

const columns: DataTableColumn<BlacklistCandidate>[] = [
  { key: "entity", header: "Entity", render: (row) => <span className="font-medium">{row.entity}</span> },
  { key: "type", header: "Type", render: (row) => row.type },
  { key: "score", header: "Risk Score", render: (row) => `${row.riskScore}` },
  { key: "confidence", header: "Confidence", render: (row) => `${row.confidence}%` },
  { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
  { key: "status", header: "Review Status", render: (row) => <StatusBadge status={row.reviewStatus} /> },
];

export function BlacklistCandidatePage() {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-semibold text-slate-950">Blacklist Candidate</h2>
        <p className="mt-2 text-sm text-slate-600">
          Kandidat blacklist adalah rekomendasi review, bukan keputusan final.
        </p>
      </div>

      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
        Blacklist Candidate adalah status rekomendasi review, bukan keputusan final dan bukan aksi blokir otomatis.
      </div>

      <DataTable columns={columns} data={mockBlacklistCandidates} getRowKey={(row) => row.id} />
    </div>
  );
}
