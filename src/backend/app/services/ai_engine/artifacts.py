from __future__ import annotations

import json
from typing import Any

from app.services.ai_engine.models import AnalysisResult, GraphRelationship, NodeRef, now_iso
from app.services.ai_engine.normalization import stable_entity_id, stable_relationship_id


def _base_node(
    node_id: str,
    node_type: str,
    label: str,
    source: str,
    now: str,
    **props: Any,
) -> dict[str, Any]:
    payload = {
        "id": node_id,
        "type": node_type,
        "label": label,
        "source": source,
        "createdAt": now,
        "updatedAt": now,
        "confidence": props.pop("confidence", "medium"),
        "riskScore": props.pop("riskScore", 0),
        "riskLevel": props.pop("riskLevel", "low"),
        "verificationStatus": props.pop("verificationStatus", "unreviewed"),
    }
    payload.update(props)
    return payload


def _rel(rel_type: str, from_ref: NodeRef, to_ref: NodeRef, source: str, now: str) -> GraphRelationship:
    return GraphRelationship(
        id=stable_relationship_id(rel_type, from_ref.type, from_ref.id, to_ref.type, to_ref.id),
        type=rel_type,
        from_ref=from_ref,
        to_ref=to_ref,
        source=source,
        confidence="medium",
        weight=1.0,
        properties={
            "evidenceId": None,
            "firstSeenAt": now,
            "lastSeenAt": now,
            "createdAt": now,
        },
    )


def build_analysis_artifacts(
    result: AnalysisResult,
    *,
    source: str = "satpam_ai_engine",
    created_at: str | None = None,
) -> tuple[list[dict[str, Any]], list[GraphRelationship]]:
    now = created_at or now_iso()
    nodes: list[dict[str, Any]] = []
    relationships: list[GraphRelationship] = []
    subject = result.assessment.subject

    risk_id = stable_entity_id(
        "risk",
        f"{subject.type}:{subject.id}:{result.assessment.score}:{','.join(hit.rule_id for hit in result.assessment.rule_hits)}",
    )
    risk_node = _base_node(
        risk_id,
        "RiskAssessment",
        f"Risk assessment {subject.id}",
        source,
        now,
        riskScore=result.assessment.score,
        riskLevel=result.assessment.level,
        confidence=result.assessment.confidence,
        score=result.assessment.score,
        level=result.assessment.level,
        explanation=result.assessment.explanation,
        triggeredRules=[hit.rule_id for hit in result.assessment.rule_hits],
        ruleHits=json.dumps([hit.as_dict() for hit in result.assessment.rule_hits]),
        evidencePath=json.dumps(result.evidence_path.as_dict() if result.evidence_path else None),
    )
    nodes.append(risk_node)
    risk_ref = NodeRef.from_node(risk_node)
    relationships.append(_rel("HAS_RISK_ASSESSMENT", subject, risk_ref, source, now))

    for recommendation in result.assessment.recommendations:
        rec_id = stable_entity_id(
            "rec",
            f"{risk_id}:{recommendation.action_type}:{recommendation.priority}",
        )
        rec_node = _base_node(
            rec_id,
            "Recommendation",
            recommendation.action_type,
            source,
            now,
            actionType=recommendation.action_type,
            priority=recommendation.priority,
            reason=recommendation.reason,
        )
        nodes.append(rec_node)
        relationships.append(_rel("HAS_RECOMMENDATION", risk_ref, NodeRef.from_node(rec_node), source, now))

    should_open_case = result.assessment.level in {"high", "critical"}
    if result.blacklist_candidate:
        candidate_id = stable_entity_id(
            "candidate",
            f"{subject.type}:{subject.id}:{result.assessment.score}",
        )
        candidate_node = _base_node(
            candidate_id,
            "BlacklistCandidate",
            f"Kandidat review {subject.id}",
            source,
            now,
            riskScore=result.assessment.score,
            riskLevel=result.assessment.level,
            verificationStatus="needs_review",
            entityId=subject.id,
            entityType=subject.type,
            candidateReason=result.blacklist_candidate.candidate_reason,
            recommendedAction=result.blacklist_candidate.recommended_action,
            status="blacklist_candidate",
            ruleIds=result.blacklist_candidate.rule_ids,
        )
        nodes.append(candidate_node)
        relationships.append(
            _rel("FLAGGED_AS_CANDIDATE", subject, NodeRef.from_node(candidate_node), source, now)
        )
        should_open_case = True

    if should_open_case:
        case_id = stable_entity_id("case", f"{subject.type}:{subject.id}:{risk_id}")
        case_node = _base_node(
            case_id,
            "VerificationCase",
            f"Verification case {subject.id}",
            source,
            now,
            riskScore=result.assessment.score,
            riskLevel=result.assessment.level,
            verificationStatus="needs_review",
            status="needs_review",
            reviewerId="unassigned",
            decisionNote="Menunggu review analis. Tidak ada blacklist final otomatis.",
            subjectType=subject.type,
            subjectId=subject.id,
        )
        nodes.append(case_node)
        relationships.append(_rel("OPENED_CASE", risk_ref, NodeRef.from_node(case_node), source, now))

    return nodes, relationships

