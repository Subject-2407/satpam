import {
  Bell,
  FileText,
  GitBranch,
  LayoutDashboard,
  ListChecks,
  ShieldAlert,
  UsersRound,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const menuItems = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Report Intake", path: "/report-intake", icon: FileText },
  { label: "Graph Explorer", path: "/graph-explorer", icon: GitBranch },
  { label: "Entities", path: "/entities", icon: UsersRound },
  { label: "Early Warning", path: "/early-warning", icon: Bell },
  { label: "Verification Cases", path: "/verification-cases", icon: ListChecks },
  { label: "Blacklist Candidate", path: "/blacklist-candidate", icon: ShieldAlert },
];

export function Sidebar() {
  return (
    <aside className="flex w-full shrink-0 flex-col border-r border-slate-200 bg-white px-3 py-4 md:w-64">
      <div className="px-3 pb-4">
        <p className="text-lg font-semibold text-slate-950">SATPAM</p>
        <p className="text-xs text-slate-500">Analyst Dashboard</p>
      </div>
      <nav className="flex gap-1 overflow-x-auto md:flex-col md:overflow-visible" aria-label="Primary navigation">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex min-w-fit items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                }`
              }
            >
              <Icon size={17} aria-hidden="true" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
