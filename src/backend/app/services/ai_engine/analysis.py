from __future__ import annotations

from app.services.ai_engine.alerts import detect_early_warnings
from app.services.ai_engine.graph import InMemoryGraph
from app.services.ai_engine.models import AnalysisResult, NodeKey, RiskAssessment
from app.services.ai_engine.scoring import (
    apply_assessment_to_node,
    score_entity,
    score_path,
    should_create_blacklist_candidate,
)
from app.services.ai_engine.search import bfs_evidence_path


def analyze_entity(
    graph: InMemoryGraph,
    key: NodeKey,
    *,
    max_depth: int = 3,
) -> AnalysisResult:
    assessment = score_entity(graph, key, max_depth=min(max_depth, 3))
    graph.nodes[key] = apply_assessment_to_node(graph.nodes[key], assessment)

    evidence_path = bfs_evidence_path(graph, key, max_depth=max_depth)
    if evidence_path:
        evidence_path.risk_score = score_path(graph, evidence_path)

    candidate = should_create_blacklist_candidate(graph, key, assessment, evidence_path)
    warnings = [
        warning
        for warning in detect_early_warnings(graph, {key: assessment})
        if warning.subject.key == key
    ]
    return AnalysisResult(
        assessment=assessment,
        evidence_path=evidence_path,
        warnings=warnings,
        blacklist_candidate=candidate,
    )


def analyze_graph(graph: InMemoryGraph) -> dict[NodeKey, RiskAssessment]:
    assessments: dict[NodeKey, RiskAssessment] = {}
    for key in graph.all_entity_keys():
        assessment = score_entity(graph, key)
        assessments[key] = assessment
        graph.nodes[key] = apply_assessment_to_node(graph.nodes[key], assessment)
    return assessments

