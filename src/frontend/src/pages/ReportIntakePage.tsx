const futureFields = [
  "Deskripsi laporan",
  "URL/domain",
  "Nomor WhatsApp",
  "Rekening bank",
  "E-wallet",
  "QRIS",
  "APK/package name",
  "Kategori dugaan",
];

export function ReportIntakePage() {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-semibold text-slate-950">Report Intake</h2>
        <p className="mt-2 text-sm text-slate-600">Form laporan dummy akan dibuat pada tahap berikutnya.</p>
      </div>

      <section className="rounded-lg border border-dashed border-slate-300 bg-white p-5">
        <h3 className="text-base font-semibold text-slate-950">Future Dummy Report Fields</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {futureFields.map((field) => (
            <div key={field} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
              {field}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
