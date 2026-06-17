import { Navigate, useLocation } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { isAtLeast } from "../lib/format";
import type { Role } from "../types/api";

// Gating route: harus login; opsional role minimum.
export function ProtectedRoute({
  children,
  minRole = "public_reporter",
}: {
  children: React.ReactNode;
  minRole?: Role;
}) {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!isAtLeast(user?.role, minRole)) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-12 text-center">
        <ShieldAlert className="text-amber-600" size={26} aria-hidden="true" />
        <p className="text-base font-semibold text-amber-800">Akses dibatasi</p>
        <p className="max-w-md text-sm text-amber-700">
          Halaman ini memerlukan role <strong>{minRole}</strong> atau lebih tinggi. Role Anda saat ini
          tidak memiliki akses.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
