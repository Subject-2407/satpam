import { useState } from "react";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { SimulationBadge } from "../components/Badges";
import { AsyncBoundary } from "../components/States";
import { useApi } from "../hooks/useApi";
import { listCrawlerFindings, listTrafficEvents } from "../services/api";
import { formatDateTime, nodeStr, safeLabel } from "../lib/format";
import type { GraphNode } from "../types/api";

const LIMIT = 20;
type Tab = "traffic" | "crawler";

const trafficColumns: DataTableColumn<GraphNode>[] = [
  { key: "type", header: "Event Type", render: (row) => nodeStr(row, "eventType") ?? "—" },
  { key: "source", header: "Source", render: (row) => safeLabel(nodeStr(row, "sourceAlias") ?? "—") },
  { key: "dest", header: "Destination", render: (row) => safeLabel(nodeStr(row, "destinationDomain") ?? "—") },
  { key: "count", header: "Requests", render: (row) => nodeStr(row, "requestCount") ?? "—" },
  { key: "ts", header: "Timestamp", render: (row) => formatDateTime(nodeStr(row, "timestamp")) },
  { key: "sim", header: "", render: () => <SimulationBadge /> },
];

function MatchedKeywords({ node }: { node: GraphNode }) {
  const raw = node.matchedKeywords;
  const keywords = Array.isArray(raw) ? raw.map(String) : [];
  if (keywords.length === 0) return <>—</>;
  return (
    <div className="flex flex-wrap gap-1">
      {keywords.map((k) => (
        <span key={k} className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
          {k}
        </span>
      ))}
    </div>
  );
}

const crawlerColumns: DataTableColumn<GraphNode>[] = [
  { key: "type", header: "Finding Type", render: (row) => nodeStr(row, "findingType") ?? "—" },
  { key: "source", header: "Source URL", render: (row) => safeLabel(nodeStr(row, "sourceUrl") ?? "—") },
  {
    key: "summary",
    header: "Content Summary",
    render: (row) => <span className="text-slate-600">{nodeStr(row, "contentSummary") ?? "—"}</span>,
  },
  { key: "keywords", header: "Keywords", render: (row) => <MatchedKeywords node={row} /> },
  { key: "captured", header: "Captured", render: (row) => formatDateTime(nodeStr(row, "capturedAt")) },
  { key: "sim", header: "", render: () => <SimulationBadge /> },
];

export function TrafficIntelPage() {
  const [tab, setTab] = useState<Tab>("traffic");
  const [offset, setOffset] = useState(0);

  const trafficQuery = useApi(
    () => (tab === "traffic" ? listTrafficEvents({ limit: LIMIT, offset }) : Promise.resolve(null)),
    [tab, offset],
  );
  const crawlerQuery = useApi(
    () => (tab === "crawler" ? listCrawlerFindings({ limit: LIMIT, offset }) : Promise.resolve(null)),
    [tab, offset],
  );

  const query = tab === "traffic" ? trafficQuery : crawlerQuery;

  return (
    <div className="space-y-5">
      <PageHeader
        title="Traffic & Crawler Intelligence"
        description="Sinyal trafik dan temuan crawler/scraper dummy. Seluruh data ditandai simulation only dan tidak berasal dari monitoring nyata."
      />

      <div className="flex items-center gap-2 border-b border-slate-200">
        {(["traffic", "crawler"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => {
              setTab(t);
              setOffset(0);
            }}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
              tab === t
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {t === "traffic" ? "Traffic Events" : "Crawler Findings"}
          </button>
        ))}
        <SimulationBadge className="ml-auto" />
      </div>

      <AsyncBoundary
        loading={query.loading}
        error={query.error}
        onRetry={query.refetch}
        isEmpty={!!query.data && query.data.items.length === 0}
        emptyMessage={tab === "traffic" ? "Tidak ada traffic event." : "Tidak ada crawler finding."}
      >
        {query.data && (
          <>
            <DataTable
              columns={tab === "traffic" ? trafficColumns : crawlerColumns}
              data={query.data.items}
              getRowKey={(row) => row.id}
            />
            <Pagination total={query.data.total} limit={query.data.limit} offset={query.data.offset} onChange={setOffset} />
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}
