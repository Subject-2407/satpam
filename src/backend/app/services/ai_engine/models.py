from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Literal


NodeKey = tuple[str, str]
RiskLevel = Literal["low", "medium", "high", "critical"]
ConfidenceLevel = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class NodeRef:
    type: str
    id: str

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "NodeRef":
        return cls(type=str(node["type"]), id=str(node["id"]))

    @property
    def key(self) -> NodeKey:
        return (self.type, self.id)

    def as_dict(self) -> dict[str, str]:
        return {"type": self.type, "id": self.id}


@dataclass
class ExtractedEntity:
    entity_type: str
    value: str
    normalized_value: str
    confidence: ConfidenceLevel
    properties: dict[str, Any] = field(default_factory=dict)

    def node_key(self) -> NodeKey:
        return (self.entity_type, str(self.properties["id"]))


@dataclass
class ExtractionResult:
    entities: list[ExtractedEntity] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    guardrail_violations: list[str] = field(default_factory=list)

    def by_type(self, entity_type: str) -> list[ExtractedEntity]:
        return [item for item in self.entities if item.entity_type == entity_type]

    @property
    def is_valid(self) -> bool:
        return not self.guardrail_violations


@dataclass
class GraphRelationship:
    id: str
    type: str
    from_ref: NodeRef
    to_ref: NodeRef
    source: str
    confidence: ConfidenceLevel = "medium"
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = dict(self.properties)
        payload.update(
            {
                "id": self.id,
                "type": self.type,
                "from": self.from_ref.as_dict(),
                "to": self.to_ref.as_dict(),
                "source": self.source,
                "confidence": self.confidence,
                "weight": self.weight,
            }
        )
        return payload


@dataclass
class GraphBuildResult:
    nodes: list[dict[str, Any]]
    relationships: list[GraphRelationship]
    extraction: ExtractionResult

    def relationship_dicts(self) -> list[dict[str, Any]]:
        return [relationship.as_dict() for relationship in self.relationships]


@dataclass
class EvidencePath:
    nodes: list[NodeRef] = field(default_factory=list)
    relationships: list[str] = field(default_factory=list)
    cost: float = 0.0
    risk_score: int = 0
    explanation: str = ""

    @property
    def length(self) -> int:
        return max(0, len(self.nodes) - 1)

    def as_dict(
        self,
        node_lookup: Callable[[NodeKey], dict[str, Any] | None] | None = None,
        relationship_lookup: Callable[[str], dict[str, Any] | None] | None = None,
    ) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        for node_ref in self.nodes:
            node = node_lookup(node_ref.key) if node_lookup else None
            nodes.append(node or node_ref.as_dict())

        relationships: list[dict[str, Any] | str] = []
        for rel_id in self.relationships:
            rel = relationship_lookup(rel_id) if relationship_lookup else None
            relationships.append(rel or rel_id)

        return {
            "nodes": nodes,
            "relationships": relationships,
            "cost": round(self.cost, 3),
            "riskScore": self.risk_score,
            "explanation": self.explanation,
        }


@dataclass
class RuleHit:
    rule_id: str
    title: str
    weight: int
    evidence: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "ruleId": self.rule_id,
            "title": self.title,
            "weight": self.weight,
            "evidence": self.evidence,
        }


@dataclass
class Recommendation:
    action_type: str
    priority: RiskLevel
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "actionType": self.action_type,
            "priority": self.priority,
            "reason": self.reason,
        }


@dataclass
class RiskAssessment:
    subject: NodeRef
    score: int
    level: RiskLevel
    confidence: ConfidenceLevel
    rule_hits: list[RuleHit] = field(default_factory=list)
    explanation: str = ""
    recommendations: list[Recommendation] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject.as_dict(),
            "score": self.score,
            "level": self.level,
            "confidence": self.confidence,
            "triggeredRules": [hit.as_dict() for hit in self.rule_hits],
            "explanation": self.explanation,
            "recommendations": [item.as_dict() for item in self.recommendations],
        }


@dataclass
class EarlyWarning:
    id: str
    alert_type: str
    subject: NodeRef
    priority: RiskLevel
    reason: str
    rule_ids: list[str] = field(default_factory=list)
    evidence_node_ids: list[str] = field(default_factory=list)
    simulation_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "alertType": self.alert_type,
            "subject": self.subject.as_dict(),
            "priority": self.priority,
            "reason": self.reason,
            "ruleIds": self.rule_ids,
            "evidenceNodeIds": self.evidence_node_ids,
            "simulationOnly": self.simulation_only,
        }


@dataclass
class BlacklistCandidateDraft:
    subject: NodeRef
    status: Literal["blacklist_candidate"] = "blacklist_candidate"
    candidate_reason: str = ""
    recommended_action: str = "prioritaskan_verifikasi_analis"
    rule_ids: list[str] = field(default_factory=list)
    evidence_path: EvidencePath | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject.as_dict(),
            "status": self.status,
            "candidateReason": self.candidate_reason,
            "recommendedAction": self.recommended_action,
            "ruleIds": self.rule_ids,
            "evidencePath": self.evidence_path.as_dict() if self.evidence_path else None,
        }


@dataclass
class AnalysisResult:
    assessment: RiskAssessment
    evidence_path: EvidencePath | None = None
    warnings: list[EarlyWarning] = field(default_factory=list)
    blacklist_candidate: BlacklistCandidateDraft | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "assessment": self.assessment.as_dict(),
            "evidencePath": self.evidence_path.as_dict()
            if self.evidence_path
            else None,
            "earlyWarnings": [item.as_dict() for item in self.warnings],
            "blacklistCandidate": self.blacklist_candidate.as_dict()
            if self.blacklist_candidate
            else None,
        }


def node_ref_from_key(key: NodeKey) -> NodeRef:
    return NodeRef(type=key[0], id=key[1])


def as_node_refs(keys: Iterable[NodeKey]) -> list[NodeRef]:
    return [node_ref_from_key(key) for key in keys]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
