import { LogOut, ShieldCheck, UserRound } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ROLE_LABELS } from "../lib/format";

export function Topbar() {
  const { user, signOut } = useAuth();

  return (
    <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="text-blue-700" size={22} aria-hidden="true" />
            <h1 className="text-xl font-semibold text-slate-950">SATPAM</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">Search-based AI Threat Prevention and Mapping</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md border border-cyan-200 bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700">
            Simulation Only
          </span>
          <span className="rounded-md border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
            Human Verification Required
          </span>
          {user && (
            <span className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
              <UserRound size={14} aria-hidden="true" />
              {ROLE_LABELS[user.role]}
            </span>
          )}
          <button
            type="button"
            onClick={signOut}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          >
            <LogOut size={14} aria-hidden="true" /> Keluar
          </button>
        </div>
      </div>
    </header>
  );
}
