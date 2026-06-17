import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Loader2, Route as RouteIcon, Search } from "lucide-react";
import { EvidencePathCard } from "../components/AnalysisView";
import { GraphCanvas } from "../components/GraphCanvas";
import { IndicativeNote, PageHeader } from "../components/PageHeader";
import { ErrorState, LoadingState } from "../components/States";
import { useApi, useMutation } from "../hooks/useApi";
import { getNeighborhood, pathSearch } from "../services/api";
import { RISK_COLORS, RISK_ORDER } from "../lib/risk";
import { titleCase } from "../lib/format";
import { NODE_TYPES, type NodeRef, type PathAlgorithm } from "../types/api";

const ALGORITHMS: PathAlgorithm[] = ["BFS", "UCS", "BIDIRECTIONAL", "A_STAR"];

const inputClass =
  "rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

interface Query {
  nodeType: string;
  nodeId: string;
  depth: number;
  limit: number;
}

export function GraphExplorerPage() {
  const [params] = useSearchParams();

  const [form, setForm] = useState<Query>({
    nodeType: params.get("type") ?? "Report",
    nodeId: params.get("id") ?? "",
    depth: 2,
    limit: 150,
  });
  const [query, setQuery] = useState<Query | null>(
    params.get("id") ? { nodeType: params.get("type") ?? "Report", nodeId: params.get("id") ?? "", depth: 2, limit: 150 } : null,
  );
  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<(NodeRef & { label?: string }) | null>(null);
  const [algorithm, setAlgorithm] = useState<PathAlgorithm>("BFS");

  const { data, loading, error, refetch } = useApi(
    () => (query ? getNeighborhood(query.nodeType, query.nodeId, query.depth, query.limit) : Promise.resolve(null)),
    [query?.nodeType, query?.nodeId, query?.depth, query?.limit],
  );

  const pathMutation = useMutation(pathSearch);
  const [pathResult, setPathResult] = useState<Awaited<ReturnType<typeof pathSearch>> | null>(null);

  const presentTypes = useMemo(() => {
    const set = new Set<string>();
    data?.nodes.forEach((n) => set.add(n.type));
    return [...set].sort();
  }, [data]);

  function toggleType(type: string) {
    setHiddenTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  async function runPathSearch() {
    if (!query) return;
    setPathResult(null);
    try {
      const res = await pathMutation.mutate({
        nodeType: query.nodeType,
        nodeId: query.nodeId,
        algorithm,
        maxDepth: query.depth,
      });
      setPathResult(res);
    } catch {
      /* error ditangani oleh mutation state */
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Graph Explorer"
        description="Visualisasi neighborhood graph (BFS) dari sebuah entitas. Maks 200 node ditampilkan. Semua data simulasi."
      />

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!form.nodeId.trim()) return;
          setSelected(null);
          setPathResult(null);
          setQuery({ ...form, nodeId: form.nodeId.trim() });
        }}
        className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4"
      >
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Node type</label>
          <select
            value={form.nodeType}
            onChange={(e) => setForm((f) => ({ ...f, nodeType: e.target.value }))}
            className={inputClass}
          >
            {NODE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div className="min-w-48 flex-1">
          <label className="mb-1 block text-xs font-medium text-slate-500">Node ID</label>
          <input
            value={form.nodeId}
            onChange={(e) => setForm((f) => ({ ...f, nodeId: e.target.value }))}
            placeholder="mis. report-001 / domain-001"
            className={`${inputClass} w-full`}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Depth</label>
          <select
            value={form.depth}
            onChange={(e) => setForm((f) => ({ ...f, depth: Number(e.target.value) }))}
            className={inputClass}
          >
            {[1, 2, 3, 4, 5].map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          className="inline-flex items-center gap-1.5 rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
        >
          <Search size={15} aria-hidden="true" /> Muat graph
        </button>
      </form>

      {!query && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white px-4 py-12 text-center text-sm text-slate-500">
          Masukkan node type dan node ID lalu klik <strong>Muat graph</strong> untuk menampilkan neighborhood.
          Anda juga bisa membuka graph dari halaman detail entitas.
        </div>
      )}

      {query && (
        <div className="grid gap-4 lg:grid-cols-[1fr,300px]">
          <div className="space-y-3">
            {loading && <LoadingState label="Memuat neighborhood…" />}
            {error && <ErrorState message={error} onRetry={refetch} />}
            {data && (
              <>
                <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500">
                  <span>
                    Root: <strong className="text-slate-800">{data.root.id}</strong>
                  </span>
                  <span>·</span>
                  <span>{data.nodeCount} node</span>
                  <span>·</span>
                  <span>{data.relationships.length} relasi</span>
                </div>
                <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
                  <GraphCanvas
                    nodes={data.nodes}
                    relationships={data.relationships}
                    rootId={data.root.id}
                    hiddenTypes={hiddenTypes}
                    onSelectNode={setSelected}
                  />
                </div>
                {/* Legend */}
                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                  {RISK_ORDER.map((level) => (
                    <span key={level} className="inline-flex items-center gap-1.5">
                      <span
                        className="inline-block h-3 w-3 rounded-full"
                        style={{ backgroundColor: RISK_COLORS[level] }}
                      />
                      {titleCase(level)}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Side panel */}
          <aside className="space-y-4">
            {presentTypes.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <h3 className="mb-2 text-sm font-semibold text-slate-900">Filter tipe node</h3>
                <div className="space-y-1.5">
                  {presentTypes.map((type) => (
                    <label key={type} className="flex items-center gap-2 text-sm text-slate-600">
                      <input
                        type="checkbox"
                        checked={!hiddenTypes.has(type)}
                        onChange={() => toggleType(type)}
                        className="rounded border-slate-300"
                      />
                      {type}
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="mb-2 text-sm font-semibold text-slate-900">Node terpilih</h3>
              {selected ? (
                <div className="space-y-2 text-sm">
                  <p className="font-medium text-slate-800">{selected.label ?? selected.id}</p>
                  <p className="text-slate-500">{selected.type}</p>
                  <Link
                    to={`/entities/${encodeURIComponent(selected.type)}/${encodeURIComponent(selected.id)}`}
                    className="inline-block text-sm font-medium text-blue-700 hover:underline"
                  >
                    Buka detail entitas →
                  </Link>
                </div>
              ) : (
                <p className="text-sm text-slate-400">Klik sebuah node untuk melihat detail.</p>
              )}
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="mb-2 text-sm font-semibold text-slate-900">Path search</h3>
              <div className="flex items-center gap-2">
                <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value as PathAlgorithm)} className={`${inputClass} flex-1`}>
                  {ALGORITHMS.map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={runPathSearch}
                  disabled={pathMutation.loading}
                  className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                >
                  {pathMutation.loading ? (
                    <Loader2 size={14} className="animate-spin" aria-hidden="true" />
                  ) : (
                    <RouteIcon size={14} aria-hidden="true" />
                  )}
                  Jalankan
                </button>
              </div>
              {pathMutation.error && <p className="mt-2 text-xs text-red-600">{pathMutation.error}</p>}
            </div>
          </aside>
        </div>
      )}

      {pathResult && (
        <section className="space-y-3">
          <IndicativeNote />
          <h3 className="text-base font-semibold text-slate-950">Evidence Path ({pathResult.algorithm})</h3>
          <EvidencePathCard path={pathResult.path} />
        </section>
      )}
    </div>
  );
}
