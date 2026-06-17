import { useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";
import { ConfidenceBadge, NodeTypeBadge } from "../components/Badges";
import { AsyncBoundary } from "../components/States";
import { useApi } from "../hooks/useApi";
import { listEntities } from "../services/api";
import { safeLabel } from "../lib/format";
import { INDICATOR_NODE_TYPES, type Confidence, type GraphNode } from "../types/api";

const RISK_LEVELS = ["low", "medium", "high", "critical"];
const VERIFICATION_STATUSES = [
  "unreviewed",
  "needs_review",
  "verified_risk",
  "false_positive",
  "escalated",
  "closed",
];
const LIMIT = 25;

const columns: DataTableColumn<GraphNode>[] = [
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
  {
    key: "status",
    header: "Verification",
    render: (row) => <StatusBadge status={row.verificationStatus} />,
  },
];

const selectClass =
  "rounded-md border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

export function EntitiesPage() {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("");
  const [offset, setOffset] = useState(0);

  const { data, loading, error, refetch } = useApi(
    () =>
      listEntities({
        search: search || undefined,
        type: type || undefined,
        risk_level: riskLevel || undefined,
        verification_status: verificationStatus || undefined,
        limit: LIMIT,
        offset,
      }),
    [search, type, riskLevel, verificationStatus, offset],
  );

  function resetAndSet<T>(setter: (v: T) => void) {
    return (value: T) => {
      setOffset(0);
      setter(value);
    };
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Entities"
        description="Daftar entitas indikator dari graph simulasi, terurut berdasarkan risk score. Nilai sensitif sudah dimasking."
      />

      <div className="flex flex-wrap items-center gap-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setOffset(0);
            setSearch(searchInput.trim());
          }}
          className="flex items-center gap-2"
        >
          <div className="relative">
            <Search size={15} className="absolute left-2.5 top-2.5 text-slate-400" aria-hidden="true" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Cari entitas…"
              className="w-56 rounded-md border border-slate-300 py-2 pl-8 pr-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
          <button
            type="submit"
            className="rounded-md bg-blue-700 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-800"
          >
            Cari
          </button>
        </form>

        <select value={type} onChange={(e) => resetAndSet(setType)(e.target.value)} className={selectClass}>
          <option value="">Semua tipe</option>
          {INDICATOR_NODE_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        <select
          value={riskLevel}
          onChange={(e) => resetAndSet(setRiskLevel)(e.target.value)}
          className={selectClass}
        >
          <option value="">Semua risk level</option>
          {RISK_LEVELS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        <select
          value={verificationStatus}
          onChange={(e) => resetAndSet(setVerificationStatus)(e.target.value)}
          className={selectClass}
        >
          <option value="">Semua verifikasi</option>
          {VERIFICATION_STATUSES.map((s) => (
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
        emptyMessage="Tidak ada entitas yang cocok dengan filter."
      >
        {data && (
          <>
            <DataTable columns={columns} data={data.items} getRowKey={(row) => `${row.type}:${row.id}`} />
            <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={setOffset} />
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}
