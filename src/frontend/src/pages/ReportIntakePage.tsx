import { useState } from "react";
import { CheckCircle2, Loader2, Plus, Trash2 } from "lucide-react";
import { RiskAssessmentCard } from "../components/AnalysisView";
import { IndicativeNote, PageHeader } from "../components/PageHeader";
import { useAuth } from "../context/AuthContext";
import { useMutation } from "../hooks/useApi";
import { submitReport } from "../services/api";
import { ApiError } from "../services/http";
import { isAtLeast } from "../lib/format";
import type { CategoryHint, SubmitReportResponse } from "../types/api";

const CATEGORY_HINTS: { value: CategoryHint; label: string }[] = [
  { value: "judol", label: "Judi Online" },
  { value: "pinjol_illegal", label: "Pinjol Ilegal" },
  { value: "cross_ecosystem", label: "Cross Ecosystem" },
  { value: "payment_flow", label: "Payment Flow" },
  { value: "traffic_crawler", label: "Traffic / Crawler" },
  { value: "benign", label: "Benign" },
];

const inputClass =
  "w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";
const labelClass = "mb-1 block text-sm font-medium text-slate-700";

interface BankRow {
  bankName: string;
  accountAlias: string;
  maskedAccountNumber: string;
}
interface AppRow {
  appName: string;
  packageName: string;
}

function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((v) => v.trim())
    .filter(Boolean);
}

export function ReportIntakePage() {
  const { user } = useAuth();
  const canSeeAnalysis = isAtLeast(user?.role, "analyst");

  const [description, setDescription] = useState("");
  const [categoryHint, setCategoryHint] = useState<CategoryHint>("cross_ecosystem");
  const [source, setSource] = useState("dummy_user_report");
  const [urls, setUrls] = useState("");
  const [phones, setPhones] = useState("");
  const [banks, setBanks] = useState<BankRow[]>([]);
  const [apps, setApps] = useState<AppRow[]>([]);

  const [result, setResult] = useState<SubmitReportResponse | null>(null);
  const [violations, setViolations] = useState<string[]>([]);

  const submit = useMutation(submitReport);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setResult(null);
    setViolations([]);
    try {
      const payload = {
        description: description.trim(),
        categoryHint,
        source: source.trim() || undefined,
        urls: splitLines(urls),
        phoneNumbers: splitLines(phones),
        bankAccounts: banks.filter((b) => b.bankName || b.accountAlias || b.maskedAccountNumber),
        apps: apps.filter((a) => a.appName || a.packageName),
      };
      const res = await submit.mutate(payload);
      setResult(res);
    } catch (err) {
      if (err instanceof ApiError && err.detail && typeof err.detail === "object") {
        const detail = (err.detail as { detail?: { violations?: string[] } }).detail;
        if (detail?.violations) setViolations(detail.violations);
      }
    }
  }

  function resetForm() {
    setDescription("");
    setUrls("");
    setPhones("");
    setBanks([]);
    setApps([]);
    setResult(null);
    setViolations([]);
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Report Intake"
        description="Kirim laporan dummy untuk diekstrak menjadi entitas dan dianalisis. Gunakan data simulasi — bukan data nyata."
      />

      {result ? (
        <div className="space-y-5">
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-5">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="text-emerald-600" size={20} aria-hidden="true" />
              <h3 className="text-base font-semibold text-emerald-900">{result.message}</h3>
            </div>
            <dl className="mt-4 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-xs uppercase tracking-wide text-emerald-700/70">Report ID</dt>
                <dd className="font-medium text-emerald-900">{result.reportId}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-emerald-700/70">Status</dt>
                <dd className="font-medium text-emerald-900">{result.status}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-emerald-700/70">Entitas diekstrak</dt>
                <dd className="font-medium text-emerald-900">{result.extractedEntities}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-emerald-700/70">Node / Relasi</dt>
                <dd className="font-medium text-emerald-900">
                  {result.nodesMerged} / {result.relationshipsMerged}
                </dd>
              </div>
            </dl>
          </div>

          {canSeeAnalysis && result.analysis?.assessment && (
            <section className="space-y-3">
              <IndicativeNote />
              <h3 className="text-base font-semibold text-slate-950">Analisis awal laporan</h3>
              <RiskAssessmentCard assessment={result.analysis.assessment} />
            </section>
          )}

          <button
            type="button"
            onClick={resetForm}
            className="rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
          >
            Kirim laporan lain
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="max-w-3xl space-y-5">
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="space-y-4">
              <div>
                <label className={labelClass} htmlFor="description">
                  Deskripsi laporan <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="description"
                  required
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Contoh: Diarahkan dari akun promosi ke situs bonus slot, diminta transfer, lalu ditawari aplikasi pinjaman cepat cair."
                  className={inputClass}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className={labelClass} htmlFor="category">
                    Kategori dugaan <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="category"
                    value={categoryHint}
                    onChange={(e) => setCategoryHint(e.target.value as CategoryHint)}
                    className={inputClass}
                  >
                    {CATEGORY_HINTS.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={labelClass} htmlFor="source">
                    Source
                  </label>
                  <input
                    id="source"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className={labelClass} htmlFor="urls">
                    URL / domain (satu per baris)
                  </label>
                  <textarea
                    id="urls"
                    rows={3}
                    value={urls}
                    onChange={(e) => setUrls(e.target.value)}
                    placeholder="https://bonus-slot-demo.test/promo"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass} htmlFor="phones">
                    Nomor WhatsApp (satu per baris)
                  </label>
                  <textarea
                    id="phones"
                    rows={3}
                    value={phones}
                    onChange={(e) => setPhones(e.target.value)}
                    placeholder="0812-0000-1111"
                    className={inputClass}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Bank accounts */}
          <RepeatableSection
            title="Rekening bank"
            onAdd={() => setBanks((b) => [...b, { bankName: "", accountAlias: "", maskedAccountNumber: "" }])}
          >
            {banks.map((row, i) => (
              <div key={i} className="grid items-end gap-2 sm:grid-cols-[1fr,1fr,1fr,auto]">
                <input
                  placeholder="Nama bank"
                  value={row.bankName}
                  onChange={(e) => setBanks((b) => b.map((r, idx) => (idx === i ? { ...r, bankName: e.target.value } : r)))}
                  className={inputClass}
                />
                <input
                  placeholder="Alias rekening"
                  value={row.accountAlias}
                  onChange={(e) => setBanks((b) => b.map((r, idx) => (idx === i ? { ...r, accountAlias: e.target.value } : r)))}
                  className={inputClass}
                />
                <input
                  placeholder="1234****9999"
                  value={row.maskedAccountNumber}
                  onChange={(e) => setBanks((b) => b.map((r, idx) => (idx === i ? { ...r, maskedAccountNumber: e.target.value } : r)))}
                  className={inputClass}
                />
                <RemoveButton onClick={() => setBanks((b) => b.filter((_, idx) => idx !== i))} />
              </div>
            ))}
          </RepeatableSection>

          {/* Apps */}
          <RepeatableSection title="APK / aplikasi" onAdd={() => setApps((a) => [...a, { appName: "", packageName: "" }])}>
            {apps.map((row, i) => (
              <div key={i} className="grid items-end gap-2 sm:grid-cols-[1fr,1fr,auto]">
                <input
                  placeholder="Nama aplikasi"
                  value={row.appName}
                  onChange={(e) => setApps((a) => a.map((r, idx) => (idx === i ? { ...r, appName: e.target.value } : r)))}
                  className={inputClass}
                />
                <input
                  placeholder="id.demo.danacepat"
                  value={row.packageName}
                  onChange={(e) => setApps((a) => a.map((r, idx) => (idx === i ? { ...r, packageName: e.target.value } : r)))}
                  className={inputClass}
                />
                <RemoveButton onClick={() => setApps((a) => a.filter((_, idx) => idx !== i))} />
              </div>
            ))}
          </RepeatableSection>

          {submit.error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              <p>{submit.error}</p>
              {violations.length > 0 && (
                <ul className="mt-1 list-inside list-disc">
                  {violations.map((v, i) => (
                    <li key={i}>{v}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={submit.loading}
            className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-60"
          >
            {submit.loading && <Loader2 size={16} className="animate-spin" aria-hidden="true" />}
            Kirim laporan
          </button>
        </form>
      )}
    </div>
  );
}

function RepeatableSection({
  title,
  onAdd,
  children,
}: {
  title: string;
  onAdd: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        <button
          type="button"
          onClick={onAdd}
          className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
        >
          <Plus size={14} aria-hidden="true" /> Tambah
        </button>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function RemoveButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 text-slate-400 hover:bg-red-50 hover:text-red-600"
      aria-label="Hapus baris"
    >
      <Trash2 size={15} />
    </button>
  );
}
