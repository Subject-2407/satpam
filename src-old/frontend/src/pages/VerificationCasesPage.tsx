import { useState } from "react";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { AsyncBoundary } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useApi, useMutation } from "../hooks/useApi";
import { listVerificationCases, updateVerificationCase } from "../services/api";
import { isAtLeast, nodeStr, safeLabel } from "../lib/format";
import type { GraphNode, RiskLevel, VerificationStatus } from "../types/api";

const ALL_STATUSES: VerificationStatus[] = [
  "unreviewed",
  "needs_review",
  "verified_risk",
  "false_positive",
  "escalated",
  "closed",
];
const LIMIT = 20;
const selectClass =
  "rounded-md border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

function caseStatus(node: GraphNode): string | undefined {
  return nodeStr(node, "status") ?? node.verificationStatus;
}

export function VerificationCasesPage() {
  const [status, setStatus] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [offset, setOffset] = useState(0);
  const [active, setActive] = useState<GraphNode | null>(null);

  const { data, loading, error, refetch } = useApi(
    () =>
      listVerificationCases({
        status: status || undefined,
        risk_level: riskLevel || undefined,
        limit: LIMIT,
        offset,
      }),
    [status, riskLevel, offset],
  );

  const columns: DataTableColumn<GraphNode>[] = [
    { key: "caseId", header: "Case ID", render: (row) => <span className="font-medium">{row.id}</span> },
    {
      key: "entity",
      header: "Related Entity",
      render: (row) => safeLabel(nodeStr(row, "subjectId") ?? row.label ?? "—"),
    },
    { key: "risk", header: "Risk Level", render: (row) => <RiskBadge level={row.riskLevel} /> },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={caseStatus(row)} /> },
    { key: "reviewer", header: "Reviewer", render: (row) => nodeStr(row, "reviewerId") ?? "—" },
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
        title="Verification Cases"
        description="Antrian review manusia. Analyst memberi keputusan awal; status closed hanya untuk Supervisor/Admin."
      />

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
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={riskLevel}
          onChange={(e) => {
            setOffset(0);
            setRiskLevel(e.target.value);
          }}
          className={selectClass}
        >
          <option value="">Semua risk level</option>
          {(["low", "medium", "high", "critical"] as RiskLevel[]).map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      <AsyncBoundary
        loading={loading}
        error={error}
        onRetry={refetch}
        isEmpty={!!data && data.items.length === 0}
        emptyMessage="Tidak ada verification case."
      >
        {data && (
          <>
            <DataTable columns={columns} data={data.items} getRowKey={(row) => row.id} />
            <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={setOffset} />
          </>
        )}
      </AsyncBoundary>

      <CaseReviewModal node={active} onClose={() => setActive(null)} onUpdated={refetch} />
    </div>
  );
}

function CaseReviewModal({
  node,
  onClose,
  onUpdated,
}: {
  node: GraphNode | null;
  onClose: () => void;
  onUpdated: () => void;
}) {
  const { user } = useAuth();
  const canClose = isAtLeast(user?.role, "supervisor");
  const [status, setStatus] = useState<VerificationStatus>("verified_risk");
  const [note, setNote] = useState("");
  const mutation = useMutation(updateVerificationCase);

  // Analyst tidak boleh memilih "closed".
  const options = ALL_STATUSES.filter((s) => s !== "closed" || canClose);

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
      title="Review Verification Case"
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
            <span className="text-sm font-semibold text-slate-900">{node.id}</span>
            <RiskBadge level={node.riskLevel} />
            <StatusBadge status={caseStatus(node)} />
          </div>
          {nodeStr(node, "decisionNote") && (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
              Catatan terakhir: {nodeStr(node, "decisionNote")}
            </p>
          )}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Keputusan / status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as VerificationStatus)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {options.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            {!canClose && (
              <p className="mt-1 text-xs text-slate-400">
                Status <strong>closed</strong> hanya tersedia untuk Supervisor/Admin.
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Catatan verifikasi</label>
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
