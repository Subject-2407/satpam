// Helper format & masking. SATPAM tidak boleh menampilkan link ilegal sebagai
// anchor aktif; identifier sensitif ditampilkan sebagai teks biasa.

import type { Role } from "../types/api";

export function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function titleCase(value?: string | null): string {
  if (!value) return "—";
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// Tampilkan label yang aman: hilangkan skema URL agar tidak terlihat seperti
// link yang bisa diklik. Nilai tetap apa adanya (sudah masked dari backend).
export function safeLabel(value?: string | null): string {
  if (!value) return "—";
  return value.replace(/^https?:\/\//i, "").replace(/^hxxps?:\/\//i, "");
}

export const ROLE_LABELS: Record<Role, string> = {
  public_reporter: "Public Reporter",
  analyst: "Analyst",
  supervisor: "Supervisor",
  admin: "Admin",
};

// Hak akses ringkas untuk gating UI (selaras dengan docs/API.md).
const ROLE_RANK: Record<Role, number> = {
  public_reporter: 0,
  analyst: 1,
  supervisor: 2,
  admin: 3,
};

export function isAtLeast(role: Role | undefined, min: Role): boolean {
  if (!role) return false;
  return ROLE_RANK[role] >= ROLE_RANK[min];
}

// Baca properti string opsional dari objek node yang bertipe terbuka.
export function nodeStr(node: Record<string, unknown>, key: string): string | undefined {
  const value = node[key];
  if (typeof value === "string" && value.length > 0) return value;
  if (typeof value === "number") return String(value);
  return undefined;
}
