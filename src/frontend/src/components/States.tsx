import { AlertCircle, Inbox, Loader2, RefreshCw } from "lucide-react";

export function LoadingState({ label = "Memuat data…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-10 text-sm text-slate-500">
      <Loader2 className="animate-spin" size={18} aria-hidden="true" />
      {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-8 text-center">
      <AlertCircle className="text-red-600" size={22} aria-hidden="true" />
      <p className="max-w-md text-sm text-red-700">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 rounded-md border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100"
        >
          <RefreshCw size={14} aria-hidden="true" /> Coba lagi
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message = "Belum ada data." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-slate-300 bg-white px-4 py-10 text-center text-sm text-slate-500">
      <Inbox size={22} aria-hidden="true" />
      {message}
    </div>
  );
}

// Bungkus pola umum: loading → error → empty → konten.
interface AsyncBoundaryProps {
  loading: boolean;
  error: string | null;
  isEmpty?: boolean;
  onRetry?: () => void;
  emptyMessage?: string;
  loadingLabel?: string;
  children: React.ReactNode;
}

export function AsyncBoundary({
  loading,
  error,
  isEmpty,
  onRetry,
  emptyMessage,
  loadingLabel,
  children,
}: AsyncBoundaryProps) {
  if (loading) return <LoadingState label={loadingLabel} />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;
  if (isEmpty) return <EmptyState message={emptyMessage} />;
  return <>{children}</>;
}
