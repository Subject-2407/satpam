import { useState } from "react";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { AsyncBoundary } from "../components/States";
import { useApi } from "../hooks/useApi";
import { listAuditLogs } from "../services/api";
import { formatDateTime, ROLE_LABELS } from "../lib/format";
import type { AuditLogNode } from "../types/api";

const LIMIT = 25;

const columns: DataTableColumn<AuditLogNode>[] = [
  { key: "ts", header: "Waktu", render: (row) => formatDateTime(row.timestamp) },
  {
    key: "actor",
    header: "Aktor",
    render: (row) => (
      <div>
        <p className="text-slate-800">{row.actorId}</p>
        <p className="text-xs text-slate-400">{ROLE_LABELS[row.actorRole] ?? row.actorRole}</p>
      </div>
    ),
  },
  { key: "action", header: "Action", render: (row) => <span className="font-medium">{row.action}</span> },
  {
    key: "target",
    header: "Target",
    render: (row) => (
      <div>
        <p className="text-slate-800">{row.targetId}</p>
        <p className="text-xs text-slate-400">{row.targetType}</p>
      </div>
    ),
  },
  {
    key: "change",
    header: "Perubahan",
    render: (row) =>
      row.oldValue || row.newValue ? (
        <span className="text-xs text-slate-600">
          <span className="text-slate-400">{row.oldValue ?? "—"}</span> → {row.newValue ?? "—"}
        </span>
      ) : (
        "—"
      ),
  },
];

export function AuditLogPage() {
  const [action, setAction] = useState("");
  const [offset, setOffset] = useState(0);

  const { data, loading, error, refetch } = useApi(
    () => listAuditLogs({ action: action.trim() || undefined, limit: LIMIT, offset }),
    [action, offset],
  );

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Supervisor"
        title="Audit Logs"
        description="Riwayat aksi penting pada prototype (update verifikasi, keputusan kandidat, perubahan rule, reset data). Terbaru lebih dulu."
      />

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setOffset(0);
        }}
        className="flex items-center gap-2"
      >
        <input
          value={action}
          onChange={(e) => {
            setOffset(0);
            setAction(e.target.value);
          }}
          placeholder="Filter action… (mis. UPDATE_VERIFICATION_STATUS)"
          className="w-80 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </form>

      <AsyncBoundary
        loading={loading}
        error={error}
        onRetry={refetch}
        isEmpty={!!data && data.items.length === 0}
        emptyMessage="Tidak ada audit log."
      >
        {data && (
          <>
            <DataTable columns={columns} data={data.items} getRowKey={(row) => row.id} />
            <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={setOffset} />
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}
