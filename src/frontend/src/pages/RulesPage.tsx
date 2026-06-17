import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { AsyncBoundary } from "../components/States";
import { useApi, useMutation } from "../hooks/useApi";
import { listRules, updateRule } from "../services/api";
import type { ScoringRule } from "../types/api";

function RuleRow({ rule, onSaved }: { rule: ScoringRule; onSaved: () => void }) {
  const [weight, setWeight] = useState(rule.weight);
  const mutation = useMutation(updateRule);
  const dirty = weight !== rule.weight;

  useEffect(() => setWeight(rule.weight), [rule.weight]);

  async function save() {
    try {
      await mutation.mutate(rule.ruleId, weight);
      onSaved();
    } catch {
      /* tampil di baris */
    }
  }

  return (
    <tr className="hover:bg-slate-50">
      <td className="px-4 py-3 font-mono text-xs text-slate-500">{rule.ruleId}</td>
      <td className="px-4 py-3 text-slate-700">{rule.title}</td>
      <td className="px-4 py-3">
        <input
          type="number"
          min={0}
          max={100}
          value={weight}
          disabled={!rule.editableInPrototype}
          onChange={(e) => setWeight(Math.max(0, Math.min(100, Number(e.target.value))))}
          className="w-20 rounded-md border border-slate-300 px-2 py-1 text-sm disabled:bg-slate-50 disabled:text-slate-400"
        />
      </td>
      <td className="px-4 py-3 text-right">
        {rule.editableInPrototype ? (
          <button
            type="button"
            onClick={save}
            disabled={!dirty || mutation.loading}
            className="inline-flex items-center gap-1.5 rounded-md bg-blue-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-800 disabled:opacity-40"
          >
            {mutation.loading && <Loader2 size={13} className="animate-spin" aria-hidden="true" />}
            Simpan
          </button>
        ) : (
          <span className="text-xs text-slate-400">read-only</span>
        )}
        {mutation.error && <p className="mt-1 text-xs text-red-600">{mutation.error}</p>}
      </td>
    </tr>
  );
}

export function RulesPage() {
  const { data, loading, error, refetch } = useApi(() => listRules(), []);

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Admin"
        title="Scoring Rules"
        description="Bobot rule risk scoring. Perubahan bersifat in-memory (tidak persisten setelah restart) dan dicatat ke audit log."
      />

      <AsyncBoundary loading={loading} error={error} onRetry={refetch} loadingLabel="Memuat rule…">
        {data && (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-slate-600">Rule ID</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-600">Title</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-600">Weight (0–100)</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.rules.map((rule) => (
                    <RuleRow key={rule.ruleId} rule={rule} onSaved={refetch} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </AsyncBoundary>
    </div>
  );
}
