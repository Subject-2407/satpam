import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";

// Akun seed demo (lihat docs/API.md). Hanya untuk prototype/simulasi.
const SEED_ACCOUNTS = [
  { label: "Analyst", email: "analyst@satpam.test", password: "analyst123" },
  { label: "Supervisor", email: "supervisor@satpam.test", password: "supervisor123" },
  { label: "Admin", email: "admin@satpam.test", password: "admin123" },
  { label: "Public Reporter", email: "reporter@satpam.test", password: "reporter123" },
];

export function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("analyst@satpam.test");
  const [password, setPassword] = useState("analyst123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signIn(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login gagal.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mb-3 inline-flex items-center gap-2">
            <ShieldCheck className="text-blue-700" size={26} aria-hidden="true" />
            <span className="text-2xl font-semibold text-slate-950">SATPAM</span>
          </div>
          <p className="text-sm text-slate-500">Search-based AI Threat Prevention and Mapping</p>
          <div className="mt-3 flex justify-center gap-2">
            <span className="rounded-md border border-cyan-200 bg-cyan-50 px-2.5 py-1 text-xs font-semibold text-cyan-700">
              Simulation Only
            </span>
            <span className="rounded-md border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
              Human Verification Required
            </span>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>

          {error && (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-60"
          >
            {loading && <Loader2 className="animate-spin" size={16} aria-hidden="true" />}
            Masuk
          </button>

          <div className="border-t border-slate-100 pt-3">
            <p className="mb-2 text-xs font-medium text-slate-500">Akun demo (klik untuk isi otomatis):</p>
            <div className="flex flex-wrap gap-2">
              {SEED_ACCOUNTS.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => {
                    setEmail(acc.email);
                    setPassword(acc.password);
                  }}
                  className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                >
                  {acc.label}
                </button>
              ))}
            </div>
          </div>
        </form>
        <p className="mt-4 text-center text-xs text-slate-400">
          Prototype akademik. Seluruh data bersifat dummy/simulasi.
        </p>
      </div>
    </div>
  );
}
