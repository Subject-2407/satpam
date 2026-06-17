// Lapisan API SATPAM: fungsi tipis per-endpoint yang dipakai halaman/hook.
// Referensi kontrak: docs/API.md. Semua data dummy/simulasi.

import { API_BASE_URL, http, qs } from "./http";
import type {
  AlertNode,
  AnalysisResult,
  AuditLogNode,
  BlacklistCandidateStatus,
  DashboardSummary,
  EarlyWarning,
  GraphNode,
  HealthResponse,
  ListEnvelope,
  NeighborhoodResponse,
  PathSearchInput,
  PathSearchResponse,
  ScoringRule,
  SubmitReportInput,
  SubmitReportResponse,
  TokenResponse,
  VerificationStatus,
} from "../types/api";

export { API_BASE_URL };

interface ListQuery {
  limit?: number;
  offset?: number;
}

// ── Health & Auth ────────────────────────────────────────────────────────────
export const getHealth = () => http.get<HealthResponse>("/health");

export function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password });
  return http.postForm<TokenResponse>("/api/auth/token", form);
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getDashboardSummary = (topEntities = 5) =>
  http.get<DashboardSummary>(`/api/dashboard/summary${qs({ top_entities: topEntities })}`);

// ── Reports ───────────────────────────────────────────────────────────────────
export const submitReport = (input: SubmitReportInput) =>
  http.post<SubmitReportResponse>("/api/reports", input);

export const listReports = (
  params: ListQuery & { status?: string; category_hint?: string; search?: string } = {},
) => http.get<ListEnvelope<GraphNode>>(`/api/reports${qs(params)}`);

export const getReport = (reportId: string) =>
  http.get<{ report: GraphNode }>(`/api/reports/${encodeURIComponent(reportId)}`);

// ── Entities ──────────────────────────────────────────────────────────────────
export const listEntities = (
  params: ListQuery & {
    type?: string;
    risk_level?: string;
    verification_status?: string;
    search?: string;
  } = {},
) => http.get<ListEnvelope<GraphNode>>(`/api/entities${qs(params)}`);

export const getEntity = (nodeType: string, nodeId: string) =>
  http.get<{ entity: GraphNode }>(
    `/api/entities/${encodeURIComponent(nodeType)}/${encodeURIComponent(nodeId)}`,
  );

// ── Graph & Analysis ────────────────────────────────────────────────────────────
export const getNeighborhood = (nodeType: string, nodeId: string, depth = 3, limit = 150) =>
  http.get<NeighborhoodResponse>(
    `/api/graph/neighborhood/${encodeURIComponent(nodeType)}/${encodeURIComponent(nodeId)}${qs({ depth, limit })}`,
  );

export const pathSearch = (input: PathSearchInput) =>
  http.post<PathSearchResponse>("/api/analysis/path-search", input);

export const getAnalysis = (nodeType: string, nodeId: string, depth = 3, limit = 250) =>
  http.get<AnalysisResult>(
    `/api/analysis/${encodeURIComponent(nodeType)}/${encodeURIComponent(nodeId)}${qs({ depth, limit })}`,
  );

// ── Alerts / Early Warning ──────────────────────────────────────────────────────
export const getEarlyWarnings = () =>
  http.get<{ alerts: EarlyWarning[] }>("/api/alerts/early-warnings");

export const listAlerts = (params: ListQuery & { status?: string; priority?: string } = {}) =>
  http.get<ListEnvelope<AlertNode>>(`/api/alerts${qs(params)}`);

export const updateAlertStatus = (alertId: string, status: string, note?: string) =>
  http.patch<{ alert: AlertNode }>(`/api/alerts/${encodeURIComponent(alertId)}/status`, { status, note });

// ── Verification Cases ──────────────────────────────────────────────────────────
export const listVerificationCases = (
  params: ListQuery & { status?: string; risk_level?: string } = {},
) => http.get<ListEnvelope<GraphNode>>(`/api/verification-cases${qs(params)}`);

export const getVerificationCase = (caseId: string) =>
  http.get<{ case: GraphNode }>(`/api/verification-cases/${encodeURIComponent(caseId)}`);

export const updateVerificationCase = (
  caseId: string,
  body: { status: VerificationStatus; decisionNote?: string; reviewerId?: string },
) => http.patch<{ case: GraphNode }>(`/api/verification-cases/${encodeURIComponent(caseId)}`, body);

// ── Blacklist Candidates ────────────────────────────────────────────────────────
export const listBlacklistCandidates = (
  params: ListQuery & { type?: string; status?: string } = {},
) => http.get<ListEnvelope<GraphNode>>(`/api/blacklist-candidates${qs(params)}`);

export const getBlacklistCandidate = (candidateId: string) =>
  http.get<{ candidate: GraphNode }>(`/api/blacklist-candidates/${encodeURIComponent(candidateId)}`);

export const decideBlacklistCandidate = (
  candidateId: string,
  body: { status: BlacklistCandidateStatus; decisionNote?: string },
) =>
  http.patch<{ candidate: GraphNode }>(
    `/api/blacklist-candidates/${encodeURIComponent(candidateId)}/decision`,
    body,
  );

// ── Traffic & Crawler Intelligence ──────────────────────────────────────────────
export const listTrafficEvents = (params: ListQuery & { event_type?: string } = {}) =>
  http.get<ListEnvelope<GraphNode>>(`/api/traffic-events${qs(params)}`);

export const listCrawlerFindings = (params: ListQuery & { finding_type?: string } = {}) =>
  http.get<ListEnvelope<GraphNode>>(`/api/crawler-findings${qs(params)}`);

// ── Rules ────────────────────────────────────────────────────────────────────
export const listRules = () => http.get<{ rules: ScoringRule[] }>("/api/rules");

export const updateRule = (ruleId: string, weight: number) =>
  http.patch<{ ruleId: string; title: string; oldWeight: number; weight: number }>(
    `/api/rules/${encodeURIComponent(ruleId)}`,
    { weight },
  );

// ── Audit logs ───────────────────────────────────────────────────────────────
export const listAuditLogs = (
  params: ListQuery & { action?: string; target_type?: string } = {},
) => http.get<ListEnvelope<AuditLogNode>>(`/api/audit-logs${qs(params)}`);

// ── Export ───────────────────────────────────────────────────────────────────
export function exportAnalysisUrl(
  nodeType: string,
  nodeId: string,
  format: "json" | "markdown" = "json",
) {
  return `${API_BASE_URL}/api/export/analysis/${encodeURIComponent(nodeType)}/${encodeURIComponent(nodeId)}${qs({ format })}`;
}

export const getExportMarkdown = (nodeType: string, nodeId: string) =>
  http.getText(exportAnalysisUrl(nodeType, nodeId, "markdown").replace(API_BASE_URL, ""));
