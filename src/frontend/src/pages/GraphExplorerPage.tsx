const filters = ["Entity type", "Risk level", "Verification status", "Source"];

export function GraphExplorerPage() {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-semibold text-slate-950">Graph Explorer</h2>
        <p className="mt-2 text-sm text-slate-600">
          Visualisasi graph interaktif akan ditambahkan pada tahap berikutnya.
        </p>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap gap-2">
          {filters.map((filter) => (
            <span key={filter} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
              {filter}
            </span>
          ))}
        </div>
        <div className="mt-4 flex min-h-80 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50">
          <div className="text-center">
            <p className="text-sm font-semibold text-slate-700">Graph canvas placeholder</p>
            <p className="mt-1 text-xs text-slate-500">Static only untuk Week 1. Tidak ada algorithm rendering.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
