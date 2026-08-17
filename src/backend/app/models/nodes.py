"""
Node models untuk SATPAM. Semua data bersifat dummy/simulasi — tidak ada data asli.

Model mengikuti schema di src/engine/schema/dataset.schema.json dan
graph_ontology.json (requiredProperties per node type).
Enforced constraints:
  - TrafficEvent.simulationOnly wajib True
  - CrawlerFinding.simulationOnly wajib True
  - BankAccount.maskedAccountNumber wajib mengandung "****"
  - EWallet.maskedWalletId wajib mengandung "****"
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.base import BaseNode, ConfidenceLevel, RiskLevel, VerificationStatus
from app.models.relationships import RelationshipModel


# ---------------------------------------------------------------------------
# Typed node models
# ---------------------------------------------------------------------------


class ReportNode(BaseNode):
    type: Literal["Report"] = "Report"
    description: str
    status: Literal["new", "auto_triaged", "needs_review", "closed"] = "new"
    categoryHint: Literal[
        "judol", "pinjol_illegal", "cross_ecosystem", "payment_flow", "traffic_crawler", "benign"
    ]


class VictimNode(BaseNode):
    type: Literal["Victim"] = "Victim"
    alias: str
    riskExposureLevel: Literal["low", "medium", "high"]


class URLNode(BaseNode):
    type: Literal["URL"] = "URL"
    rawUrl: str
    normalizedUrl: str
    domain: str


class DomainNode(BaseNode):
    type: Literal["Domain"] = "Domain"
    domainName: str
    category: str


class LinkShortenerNode(BaseNode):
    type: Literal["LinkShortener"] = "LinkShortener"
    shortUrl: str
    provider: str


class SocialMediaAccountNode(BaseNode):
    type: Literal["SocialMediaAccount"] = "SocialMediaAccount"
    platform: str
    username: str
    profileUrl: str


class PhoneNumberNode(BaseNode):
    type: Literal["PhoneNumber"] = "PhoneNumber"
    normalizedNumber: str
    countryCode: str
    reportCount: int = Field(default=0, ge=0)


class BankAccountNode(BaseNode):
    type: Literal["BankAccount"] = "BankAccount"
    bankName: str
    accountAlias: str
    maskedAccountNumber: str

    @field_validator("maskedAccountNumber")
    @classmethod
    def must_be_masked(cls, v: str) -> str:
        if "****" not in v:
            raise ValueError("maskedAccountNumber harus mengandung '****' (data disamarkan)")
        return v


class EWalletNode(BaseNode):
    type: Literal["EWallet"] = "EWallet"
    provider: str
    walletAlias: str
    maskedWalletId: str

    @field_validator("maskedWalletId")
    @classmethod
    def must_be_masked(cls, v: str) -> str:
        if "****" not in v:
            raise ValueError("maskedWalletId harus mengandung '****' (data disamarkan)")
        return v


class QRISMerchantNode(BaseNode):
    type: Literal["QRISMerchant"] = "QRISMerchant"
    merchantAlias: str
    merchantCategory: str


class APKNode(BaseNode):
    type: Literal["APK"] = "APK"
    appName: str
    packageName: str
    requestedPermissions: List[str] = []


class KeywordNode(BaseNode):
    type: Literal["Keyword"] = "Keyword"
    keyword: str
    category: str
    weight: int = Field(default=0, ge=0, le=100)


class TransactionNode(BaseNode):
    type: Literal["Transaction"] = "Transaction"
    amount: int = Field(ge=0)
    timestamp: datetime
    channel: str
    transactionType: str


class TrafficEventNode(BaseNode):
    """Log trafik simulasi — simulation_only wajib True."""

    type: Literal["TrafficEvent"] = "TrafficEvent"
    eventType: str
    timestamp: datetime
    sourceAlias: str
    destinationDomain: str
    requestCount: int = Field(default=0, ge=0)
    simulationOnly: Literal[True] = True

    @field_validator("simulationOnly")
    @classmethod
    def enforce_simulation(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("TrafficEvent.simulationOnly harus True — tidak ada data trafik nyata")
        return v


class CrawlerFindingNode(BaseNode):
    """Temuan crawler dummy — simulation_only wajib True."""

    type: Literal["CrawlerFinding"] = "CrawlerFinding"
    findingType: str
    sourceUrl: str
    contentSummary: str
    matchedKeywords: List[str] = []
    capturedAt: datetime
    simulationOnly: Literal[True] = True

    @field_validator("simulationOnly")
    @classmethod
    def enforce_simulation(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("CrawlerFinding.simulationOnly harus True — tidak ada crawling nyata")
        return v


class BlacklistEntityNode(BaseNode):
    type: Literal["BlacklistEntity"] = "BlacklistEntity"
    entityType: str
    reason: str
    severity: Literal["low", "medium", "high", "critical"]
    entityId: Optional[str] = None


class ClusterNode(BaseNode):
    type: Literal["Cluster"] = "Cluster"
    name: str
    clusterType: str


class BlacklistCandidateNode(BaseNode):
    type: Literal["BlacklistCandidate"] = "BlacklistCandidate"
    entityId: str
    candidateReason: str
    recommendedAction: str
    status: str


class BlacklistDecisionNode(BaseNode):
    type: Literal["BlacklistDecision"] = "BlacklistDecision"
    decision: str
    reviewerId: str
    decisionNote: str
    decidedAt: datetime


class EvidenceNode(BaseNode):
    type: Literal["Evidence"] = "Evidence"
    evidenceType: str
    contentSummary: str


class RiskAssessmentNode(BaseNode):
    type: Literal["RiskAssessment"] = "RiskAssessment"
    score: int = Field(ge=0, le=100)
    level: Literal["low", "medium", "high", "critical"]
    explanation: str


class VerificationCaseNode(BaseNode):
    type: Literal["VerificationCase"] = "VerificationCase"
    status: str
    reviewerId: str
    decisionNote: str


class RecommendationNode(BaseNode):
    type: Literal["Recommendation"] = "Recommendation"
    actionType: str
    priority: str
    reason: str


class GraphUserNode(BaseNode):
    """User node dalam graph (bukan auth user) — merepresentasikan aktor/reviewer dalam data."""

    type: Literal["User"] = "User"
    name: str
    role: str
    status: str


class AuditLogNode(BaseNode):
    type: Literal["AuditLog"] = "AuditLog"
    actorId: str
    action: str
    targetId: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Container for bulk import payload
# ---------------------------------------------------------------------------


class NodesContainer(BaseModel):
    """Semua koleksi node dalam satu dataset dummy SATPAM."""

    model_config = ConfigDict(extra="forbid")

    reports: List[ReportNode] = []
    victims: List[VictimNode] = []
    urls: List[URLNode] = []
    domains: List[DomainNode] = []
    linkShorteners: List[LinkShortenerNode] = []
    socialMediaAccounts: List[SocialMediaAccountNode] = []
    phoneNumbers: List[PhoneNumberNode] = []
    bankAccounts: List[BankAccountNode] = []
    eWallets: List[EWalletNode] = []
    qrisMerchants: List[QRISMerchantNode] = []
    apks: List[APKNode] = []
    keywords: List[KeywordNode] = []
    transactions: List[TransactionNode] = []
    trafficEvents: List[TrafficEventNode] = []
    crawlerFindings: List[CrawlerFindingNode] = []
    blacklistEntities: List[BlacklistEntityNode] = []
    blacklistCandidates: List[BlacklistCandidateNode] = []
    blacklistDecisions: List[BlacklistDecisionNode] = []
    clusters: List[ClusterNode] = []
    evidences: List[EvidenceNode] = []
    riskAssessments: List[RiskAssessmentNode] = []
    verificationCases: List[VerificationCaseNode] = []
    recommendations: List[RecommendationNode] = []
    users: List[GraphUserNode] = []
    auditLogs: List[AuditLogNode] = []


class DatasetMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    datasetId: str
    version: str
    scope: str
    createdAt: datetime
    simulationOnly: bool
    dataPolicy: List[str]


class DemoScenario(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: str
    seedReportIds: List[str] = []


class DummyDataImportRequest(BaseModel):
    """Payload untuk endpoint POST /api/import/dummy-data."""

    metadata: DatasetMetadata
    nodes: NodesContainer
    relationships: List[RelationshipModel] = []
    demoScenarios: List[DemoScenario] = []


# ---------------------------------------------------------------------------
# Import response models
# ---------------------------------------------------------------------------


class ImportStats(BaseModel):
    nodes_merged: int = 0
    relationships_merged: int = 0
    skipped: int = 0
    errors: List[str] = []


class ImportResponse(BaseModel):
    status: str
    stats: ImportStats
    message: str
