import {
  Activity,
  Bell,
  FileText,
  GitBranch,
  LayoutDashboard,
  ListChecks,
  ScrollText,
  ShieldAlert,
  SlidersHorizontal,
  UsersRound,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { Role } from "../types/api";

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  // Role minimum yang boleh melihat menu/route ini.
  minRole: Role;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, minRole: "analyst" },
  { label: "Report Intake", path: "/report-intake", icon: FileText, minRole: "public_reporter" },
  { label: "Graph Explorer", path: "/graph-explorer", icon: GitBranch, minRole: "analyst" },
  { label: "Entities", path: "/entities", icon: UsersRound, minRole: "analyst" },
  { label: "Early Warning", path: "/early-warning", icon: Bell, minRole: "analyst" },
  { label: "Verification Cases", path: "/verification-cases", icon: ListChecks, minRole: "analyst" },
  { label: "Blacklist Candidate", path: "/blacklist-candidate", icon: ShieldAlert, minRole: "analyst" },
  { label: "Traffic & Crawler", path: "/traffic-intel", icon: Activity, minRole: "analyst" },
  { label: "Audit Logs", path: "/audit-logs", icon: ScrollText, minRole: "supervisor" },
  { label: "Scoring Rules", path: "/rules", icon: SlidersHorizontal, minRole: "admin" },
];
