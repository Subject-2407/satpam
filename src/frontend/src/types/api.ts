// Tipe data API SATPAM — diselaraskan dengan docs/API.md (versi 0.1.0-week1).
// Semua data bersifat dummy/simulasi.

// ── Enum dasar ──────────────────────────────────────────────────────────────
export type Role = "public_reporter" | "analyst" | "supervisor" | "admin";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type Confidence = "low" | "medium" | "high";

export type VerificationStatus =
  | "unreviewed"
  | "needs_review"
  | "verified_risk"
  | "false_positive"
  | "escalated"
  | "closed";

export type AlertStatus = "new" | "reviewed" | "escalated" | "false_positive";

export type BlacklistCandidateStatus =
  | "not_candidate"
  | "blacklist_candidate"
  | "needs_more_evidence"
  | "rejected_candidate"
  | "false_positive"
  | "confirmed_blacklist"
  | "recommended_for_blocking"
  | "escalated";

export type CategoryHint =
  | "judol"
  | "pinjol_illegal"
  | "cross_ecosystem"
  | "payment_flow"
  | "traffic_crawler"
  | "benign";

export type PathAlgorithm = "BFS" | "UCS" | "BIDIRECTIONAL" | "A_STAR";

export type Priority = "low" | "medium" | "high" | "critical";

// Daftar node type yang diizinkan (lihat docs/API.md → Node Types).
export const NODE_TYPES = [
  "Report",
  "Victim",
  "URL",
  "Domain",
  "LinkShortener",
  "SocialMediaAccount",
  "PhoneNumber",
  "BankAccount",
  "EWallet",
  "QRISMerchant",
  "APK",
  "Keyword",
  "Transaction",
  "TrafficEvent",
  "CrawlerFinding",
  "BlacklistEntity",
  "BlacklistCandidate",
  "BlacklistDecision",
  "Cluster",
  "Evidence",
  "RiskAssessment",
  "VerificationCase",
  "Recommendation",
  "Alert",
  "User",
  "AuditLog",
] as const;

export type NodeType = (typeof NODE_TYPES)[number];

// Entitas indikator yang dipakai pencarian & dashboard.
export const INDICATOR_NODE_TYPES = [
  "URL",
  "Domain",
  "LinkShortener",
  "SocialMediaAccount",
  "PhoneNumber",
  "BankAccount",
  "EWallet",
  "QRISMerchant",
  "APK",
  "Keyword",
] as const;

// ── Auth ────────────────────────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: Role;
  user_id: string;
}

// ── Bentuk objek standar ─────────────────────────────────────────────────────
export interface NodeRef {
  type: string;
  id: string;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  source?: string;
  createdAt?: string;
  updatedAt?: string;
  confidence?: Confidence;
  riskScore?: number;
  riskLevel?: RiskLevel;
  verificationStatus?: VerificationStatus;
  labels?: string[];
  // Properti khusus per tipe node dibiarkan terbuka.
  [key: string]: unknown;
}

export interface GraphRelationship {
  id: string;
  type: string;
  from: NodeRef;
  to: NodeRef;
  source?: string;
  confidence?: Confidence;
  weight?: number;
}

export interface TriggeredRule {
  ruleId: string;
  title: string;
  weight: number;
  evidence?: string;
}

export interface RecommendationItem {
  actionType: string;
  priority: Priority;
  reason: string;
}

export interface RiskAssessment {
  subject: NodeRef;
  score: number;
  level: RiskLevel;
  confidence: Confidence;
  triggeredRules: TriggeredRule[];
  explanation: string;
  recommendations: RecommendationItem[];
}

export interface EvidencePath {
  nodes: Array<GraphNode | NodeRef>;
  relationships: Array<GraphRelationship | string>;
  cost: number;
  riskScore: number;
  explanation: string;
}

export interface EarlyWarning {
  id: string;
  alertType: string;
  subject: NodeRef;
  priority: Priority;
  reason: string;
  ruleIds: string[];
  evidenceNodeIds: string[];
  simulationOnly: boolean;
}

export interface AnalysisResult {
  assessment: RiskAssessment | null;
  evidencePath: EvidencePath | null;
  earlyWarnings: EarlyWarning[];
  blacklistCandidate: GraphNode | null;
}

// ── List envelope (paginated) ────────────────────────────────────────────────
export interface ListEnvelope<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

// ── Health ───────────────────────────────────────────────────────────────────
export interface HealthResponse {
  status: "healthy" | "degraded";
  neo4j: "connected" | "error";
  timestamp: string;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export interface DashboardSummary {
  simulationOnly: boolean;
  totals: {
    reports: number;
    entities: number;
    alerts: number;
    verificationCases: number;
    blacklistCandidates: number;
  };
  entitiesByRiskLevel: Partial<Record<RiskLevel, number>>;
  alertsByStatus: Partial<Record<AlertStatus, number>>;
  verificationCasesByStatus: Partial<Record<VerificationStatus, number>>;
  blacklistCandidatesByStatus: Partial<Record<BlacklistCandidateStatus, number>>;
  topRiskEntities: GraphNode[];
}

// ── Reports ───────────────────────────────────────────────────────────────────
export interface ReportBankAccountInput {
  bankName: string;
  accountAlias: string;
  maskedAccountNumber: string;
}

export interface ReportAppInput {
  appName: string;
  packageName: string;
}

export interface SubmitReportInput {
  description: string;
  categoryHint: CategoryHint;
  source?: string;
  urls?: string[];
  phoneNumbers?: string[];
  bankAccounts?: ReportBankAccountInput[];
  apps?: ReportAppInput[];
}

export interface SubmitReportResponse {
  reportId: string;
  status: string;
  message: string;
  extractedEntities: number;
  nodesMerged: number;
  relationshipsMerged: number;
  analysis: AnalysisResult;
}

// ── Graph ─────────────────────────────────────────────────────────────────────
export interface NeighborhoodResponse {
  root: NodeRef;
  algorithm: string;
  maxDepth: number;
  nodeCount: number;
  nodes: GraphNode[];
  relationships: GraphRelationship[];
}

export interface PathSearchInput {
  nodeType: string;
  nodeId: string;
  algorithm?: PathAlgorithm;
  maxDepth?: number;
  limit?: number;
}

export interface PathSearchResponse {
  algorithm: string;
  path: EvidencePath | null;
}

// ── Alert node (persisted) ─────────────────────────────────────────────────────
export interface AlertNode {
  id: string;
  type: "Alert";
  label: string;
  alertType: string;
  subjectType: string;
  subjectId: string;
  priority: Priority;
  reason: string;
  ruleIds: string[];
  evidenceNodeIds: string[];
  simulationOnly: boolean;
  status: AlertStatus;
  verificationStatus?: VerificationStatus;
  createdAt?: string;
  updatedAt?: string;
}

// ── Rules ─────────────────────────────────────────────────────────────────────
export interface ScoringRule {
  ruleId: string;
  title: string;
  weight: number;
  editableInPrototype: boolean;
}

// ── Audit log node ──────────────────────────────────────────────────────────────
export interface AuditLogNode {
  id: string;
  type: "AuditLog";
  actorId: string;
  actorRole: Role;
  action: string;
  targetId: string;
  targetType: string;
  oldValue?: string;
  newValue?: string;
  note?: string;
  timestamp: string;
}

// ── Export ───────────────────────────────────────────────────────────────────
export interface ExportAnalysisResponse {
  generatedAt: string;
  simulationOnly: boolean;
  disclaimer: string;
  entity: NodeRef;
  analysis: AnalysisResult;
}
