import { NavLink } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { isAtLeast } from "../lib/format";
import { NAV_ITEMS } from "../routes/navigation";

export function Sidebar() {
  const { user } = useAuth();
  const items = NAV_ITEMS.filter((item) => isAtLeast(user?.role, item.minRole));

  return (
    <aside className="flex w-full shrink-0 flex-col border-r border-slate-200 bg-white px-3 py-4 md:w-64">
      <div className="flex items-center gap-2 px-3 pb-4">
        <ShieldCheck className="text-blue-700" size={22} aria-hidden="true" />
        <div>
          <p className="text-lg font-semibold leading-tight text-slate-950">SATPAM</p>
          <p className="text-xs text-slate-500">Analyst Dashboard</p>
        </div>
      </div>
      <nav
        className="flex gap-1 overflow-x-auto md:flex-col md:overflow-visible"
        aria-label="Primary navigation"
      >
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex min-w-fit items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                }`
              }
            >
              <Icon size={17} aria-hidden="true" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <p className="mt-auto hidden px-3 pt-4 text-[11px] leading-relaxed text-slate-400 md:block">
        Prototype simulasi. Output indikatif, bukan vonis. Keputusan akhir melalui human verification.
      </p>
    </aside>
  );
}
