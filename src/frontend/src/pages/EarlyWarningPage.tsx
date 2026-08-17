import { useState } from "react";
import { Link } from "react-router-dom";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { PriorityBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { SimulationBadge } from "../components/Badges";
import { AsyncBoundary } from "../components/States";
import { useApi, useMutation } from "../hooks/useApi";
import { listAlerts, updateAlertStatus } from "../services/api";
import { formatDateTime, safeLabel } from "../lib/format";
import type { AlertNode, AlertStatus } from "../types/api";

const ALERT_STATUSES: AlertStatus[] = ["new", "reviewed", "escalated", "false_positive"];
const LIMIT = 20;
const selectClass =
  "rounded-md border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

export function EarlyWarningPage() {
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [offset, setOffset] = useState(0);
  const [active, setActive] = useState<AlertNode | null>(null);

  const { data, loading, error, refetch } = useApi(
    () =>
      listAlerts({
        status: status || undefined,
        priority: priority || undefined,
        limit: LIMIT,
        offset,
      }),
    [status, priority, offset],
  );

  const columns: DataTableColumn<AlertNode>[] = [
    { key: "alertType", header: "Alert Type", render: (row) => <span className="font-medium">{row.alertType}</span> },
    {
      key: "entity",
      header: "Entity",
      render: (row) =>
        row.subjectType && row.subjectId ? (
          <Link
            to={`/entities/${encodeURIComponent(row.subjectType)}/${encodeURIComponent(row.subjectId)}`}
            className="text-blue-700 hover:underline"
          >
            {safeLabel(row.subjectId)}
          </Link>
        ) : (
          "—"
        ),
    },
    { key: "priority", header: "Priority", render: (row) => <PriorityBadge priority={row.priority} /> },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
    { key: "createdAt", header: "Created At", render: (row) => formatDateTime(row.createdAt) },
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
        title="Early Warning"
        description="Daftar alert terindikasi risiko dari graph simulasi. Tandai status review — semua bersifat indikatif dan perlu verifikasi."
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
          {ALERT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={priority}
          onChange={(e) => {
            setOffset(0);
            setPriority(e.target.value);
          }}
          className={selectClass}
        >
          <option value="">Semua prioritas</option>
          {["low", "medium", "high", "critical"].map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <SimulationBadge className="ml-auto" />
      </div>

      <AsyncBoundary
        loading={loading}
        error={error}
        onRetry={refetch}
        isEmpty={!!data && data.items.length === 0}
        emptyMessage="Tidak ada alert."
      >
        {data && (
          <>
            <DataTable columns={columns} data={data.items} getRowKey={(row) => row.id} />
            <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={setOffset} />
          </>
        )}
      </AsyncBoundary>

      <AlertReviewModal alert={active} onClose={() => setActive(null)} onUpdated={refetch} />
    </div>
  );
}

function AlertReviewModal({
  alert,
  onClose,
  onUpdated,
}: {
  alert: AlertNode | null;
  onClose: () => void;
  onUpdated: () => void;
}) {
  const [status, setStatus] = useState<AlertStatus>("reviewed");
  const [note, setNote] = useState("");
  const mutation = useMutation(updateAlertStatus);

  async function handleSave() {
    if (!alert) return;
    try {
      await mutation.mutate(alert.id, status, note.trim() || undefined);
      onUpdated();
      onClose();
    } catch {
      /* error ditampilkan di modal */
    }
  }

  return (
    <Modal
      open={!!alert}
      title="Review Alert"
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
            {mutation.loading ? "Menyimpan…" : "Simpan status"}
          </button>
        </>
      }
    >
      {alert && (
        <div className="space-y-4">
          <div>
            <p className="text-sm font-semibold text-slate-900">{alert.alertType}</p>
            <p className="mt-1 text-sm text-slate-600">{alert.reason}</p>
          </div>
          <div className="flex flex-wrap gap-2 text-sm">
            <PriorityBadge priority={alert.priority} />
            <StatusBadge status={alert.status} />
            {alert.simulationOnly && <SimulationBadge />}
          </div>
          {alert.ruleIds?.length > 0 && (
            <p className="text-xs text-slate-500">Rule: {alert.ruleIds.join(", ")}</p>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Status baru</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as AlertStatus)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {ALERT_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Catatan (opsional)</label>
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
