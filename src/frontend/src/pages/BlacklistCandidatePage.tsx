import { useState } from "react";
import { ShieldAlert } from "lucide-react";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { ConfidenceBadge, NodeTypeBadge } from "../components/Badges";
import { AsyncBoundary } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useApi, useMutation } from "../hooks/useApi";
import { decideBlacklistCandidate, listBlacklistCandidates } from "../services/api";
import { isAtLeast, nodeStr, safeLabel } from "../lib/format";
import type { BlacklistCandidateStatus, Confidence, GraphNode } from "../types/api";

// Status yang hanya boleh diset Supervisor/Admin (keputusan akhir manusia).
const SUPERVISOR_ONLY: BlacklistCandidateStatus[] = ["confirmed_blacklist", "recommended_for_blocking"];

const ANALYST_STATUSES: BlacklistCandidateStatus[] = [
  "blacklist_candidate",
  "needs_more_evidence",
  "rejected_candidate",
  "false_positive",
  "escalated",
];

const FILTER_STATUSES: BlacklistCandidateStatus[] = [...ANALYST_STATUSES, ...SUPERVISOR_ONLY, "not_candidate"];
const LIMIT = 20;
const selectClass =
  "rounded-md border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

function candidateStatus(node: GraphNode): string | undefined {
  return nodeStr(node, "status");
}
function candidateType(node: GraphNode): string | undefined {
  return nodeStr(node, "entityType") ?? node.type;
}

export function BlacklistCandidatePage() {
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [active, setActive] = useState<GraphNode | null>(null);

  const { data, loading, error, refetch } = useApi(
    () =>
      listBlacklistCandidates({
        type: type || undefined,
        status: status || undefined,
        limit: LIMIT,
        offset,
      }),
    [type, status, offset],
  );

  const columns: DataTableColumn<GraphNode>[] = [
    {
      key: "entity",
      header: "Entity",
      render: (row) => <span className="font-medium">{safeLabel(nodeStr(row, "entityId") ?? row.label ?? row.id)}</span>,
    },
    { key: "type", header: "Type", render: (row) => <NodeTypeBadge type={candidateType(row)} /> },
    { key: "score", header: "Risk Score", render: (row) => row.riskScore ?? nodeStr(row, "riskScore") ?? "—" },
    {
      key: "confidence",
      header: "Confidence",
      render: (row) => <ConfidenceBadge confidence={row.confidence as Confidence | undefined} />,
    },
    { key: "status", header: "Review Status", render: (row) => <StatusBadge status={candidateStatus(row)} /> },
    {
      key: "action",
      header: "",
      render: (row) => (
        <button
          type="button"
          onClick={() => setActive(row)}
          className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
        >
          Review
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Blacklist Candidate"
        description="Kandidat blacklist adalah rekomendasi review, bukan keputusan final."
      />

      <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
        <ShieldAlert size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
        <p>
          Blacklist Candidate adalah status rekomendasi review, bukan keputusan final dan bukan aksi blokir
          otomatis. Status <strong>confirmed_blacklist</strong> dan <strong>recommended_for_blocking</strong> hanya
          dapat diberikan Supervisor/Admin.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <select
          value={status}
          onChange={(e) => {
            setOffset(0);
            setStatus(e.target.value);
          }}
          className={selectClass}
        >
          <option value="">Semua status</option>
          {FILTER_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <AsyncBoundary
        loading={loading}
        error={error}
        onRetry={refetch}
        isEmpty={!!data && data.items.length === 0}
        emptyMessage="Tidak ada kandidat blacklist."
      >
        {data && (
          <>
            <DataTable columns={columns} data={data.items} getRowKey={(row) => row.id} />
            <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={setOffset} />
          </>
        )}
      </AsyncBoundary>

      <CandidateDecisionModal node={active} onClose={() => setActive(null)} onUpdated={refetch} />
    </div>
  );
}

function CandidateDecisionModal({
  node,
  onClose,
  onUpdated,
}: {
  node: GraphNode | null;
  onClose: () => void;
  onUpdated: () => void;
}) {
  const { user } = useAuth();
  const canFinalize = isAtLeast(user?.role, "supervisor");
  const options = canFinalize ? [...ANALYST_STATUSES, ...SUPERVISOR_ONLY] : ANALYST_STATUSES;
  const [status, setStatus] = useState<BlacklistCandidateStatus>("needs_more_evidence");
  const [note, setNote] = useState("");
  const mutation = useMutation(decideBlacklistCandidate);

  async function handleSave() {
    if (!node) return;
    try {
      await mutation.mutate(node.id, { status, decisionNote: note.trim() || undefined });
      onUpdated();
      onClose();
    } catch {
      /* tampil di modal */
    }
  }

  return (
    <Modal
      open={!!node}
      title="Keputusan Kandidat Blacklist"
      onClose={onClose}
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={mutation.loading}
            className="rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-60"
          >
            {mutation.loading ? "Menyimpan…" : "Simpan keputusan"}
          </button>
        </>
      }
    >
      {node && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-900">
              {safeLabel(nodeStr(node, "entityId") ?? node.label ?? node.id)}
            </span>
            <NodeTypeBadge type={candidateType(node)} />
            <StatusBadge status={candidateStatus(node)} />
          </div>
          {nodeStr(node, "candidateReason") && (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
              {nodeStr(node, "candidateReason")}
            </p>
          )}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Keputusan</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as BlacklistCandidateStatus)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {options.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            {!canFinalize && (
              <p className="mt-1 text-xs text-slate-400">
                <strong>confirmed_blacklist</strong> / <strong>recommended_for_blocking</strong> hanya untuk
                Supervisor/Admin.
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Catatan keputusan</label>
            <textarea
              rows={3}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          {mutation.error && <p className="text-sm text-red-600">{mutation.error}</p>}
        </div>
      )}
    </Modal>
  );
}
