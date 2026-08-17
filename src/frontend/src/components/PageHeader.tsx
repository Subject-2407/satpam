import { Info } from "lucide-react";
import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
}

export function PageHeader({ title, description, eyebrow, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        {eyebrow && <p className="text-sm font-semibold text-blue-700">{eyebrow}</p>}
        <h2 className="mt-0.5 text-2xl font-semibold text-slate-950">{title}</h2>
        {description && <p className="mt-2 max-w-3xl text-sm text-slate-600">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

// Banner disclaimer indikatif untuk halaman hasil analisis.
export function IndicativeNote({ children }: { children?: ReactNode }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <Info size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
      <p>
        {children ??
          "Hasil bersifat indikatif dan memerlukan verifikasi manusia. Bukan vonis, tidak memicu pemblokiran nyata. Semua data simulasi."}
      </p>
    </div>
  );
}
