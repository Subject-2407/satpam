from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import Role, require_roles
from app.database import get_driver
from app.repositories.neo4j_repo import Neo4jRepository
from app.services.ai_engine.alerts import detect_early_warnings
from app.services.ai_engine.analysis import analyze_entity
from app.services.ai_engine.artifacts import build_analysis_artifacts
from app.services.ai_engine.graph import InMemoryGraph
from app.services.ai_engine.models import AnalysisResult
from app.services.ai_engine.scoring import RULES
from app.services.ai_engine.search import (
    a_star_search,
    bfs_evidence_path,
    bfs_neighborhood,
    bidirectional_search,
    uniform_cost_search,
)

router = APIRouter(prefix="/api", tags=["ai-engine"])


class PathSearchRequest(BaseModel):
    nodeType: str
    nodeId: str
    algorithm: Literal["BFS", "UCS", "BIDIRECTIONAL", "A_STAR"] = "BFS"
    maxDepth: int = Field(default=3, ge=1, le=5)
    limit: int = Field(default=250, ge=1, le=1000)


def _repo_or_503(driver) -> Neo4jRepository:
    if driver is None:
        raise HTTPException(status_code=503, detail="Database tidak tersedia")
    return Neo4jRepository(driver)


async def _neighborhood_graph(
    repo: Neo4jRepository,
    node_type: str,
    node_id: str,
    depth: int,
    limit: int,
) -> InMemoryGraph:
    payload = await repo.get_neighborhood(node_type, node_id, depth=depth, limit=limit)
    if not payload["nodes"]:
        raise HTTPException(status_code=404, detail="Node tidak ditemukan")
    return InMemoryGraph(nodes=payload["nodes"], relationships=payload["relationships"])


@router.get("/entities/{node_type}/{node_id}")
async def get_entity_detail(
    node_type: str,
    node_id: str,
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    repo = _repo_or_503(driver)
    try:
        node = await repo.get_node(node_type, node_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not node:
        raise HTTPException(status_code=404, detail="Node tidak ditemukan")
    return {"entity": node}


@router.get("/graph/neighborhood/{node_type}/{node_id}")
async def get_graph_neighborhood(
    node_type: str,
    node_id: str,
    depth: int = Query(default=3, ge=0, le=5),
    limit: int = Query(default=150, ge=1, le=1000),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    repo = _repo_or_503(driver)
    try:
        graph = await _neighborhood_graph(repo, node_type, node_id, depth, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return bfs_neighborhood(graph, (node_type, node_id), max_depth=depth, limit=limit)


@router.post("/analysis/path-search")
async def run_path_search(
    body: PathSearchRequest,
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    repo = _repo_or_503(driver)
    try:
        graph = await _neighborhood_graph(
            repo,
            body.nodeType,
            body.nodeId,
            body.maxDepth,
            body.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    start = (body.nodeType, body.nodeId)
    if body.algorithm == "BFS":
        path = bfs_evidence_path(graph, start, max_depth=body.maxDepth, limit=body.limit)
    elif body.algorithm == "UCS":
        path = uniform_cost_search(graph, start, max_depth=body.maxDepth, limit=body.limit)
    elif body.algorithm == "BIDIRECTIONAL":
        targets = set(graph.keys_by_type("BlacklistEntity"))
        path = bidirectional_search(graph, start, targets, max_depth=body.maxDepth, limit=body.limit)
    else:
        path = a_star_search(graph, start, max_depth=body.maxDepth, limit=body.limit)

    return {
        "algorithm": body.algorithm,
        "path": path.as_dict(graph.get_node, graph.get_relationship) if path else None,
    }


@router.get("/analysis/{node_type}/{node_id}")
async def get_risk_analysis(
    node_type: str,
    node_id: str,
    depth: int = Query(default=3, ge=1, le=5),
    limit: int = Query(default=250, ge=1, le=1000),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    repo = _repo_or_503(driver)
    try:
        graph = await _neighborhood_graph(repo, node_type, node_id, depth, limit)
        result = analyze_entity(graph, (node_type, node_id), max_depth=depth)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result.as_dict()


@router.get("/alerts/early-warnings")
async def list_early_warnings(
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    repo = _repo_or_503(driver)
    payload = await repo.get_all_graph()
    graph = InMemoryGraph(nodes=payload["nodes"], relationships=payload["relationships"])
    assessments = {}
    for key in graph.all_entity_keys():
        try:
            result = analyze_entity(graph, key)
            assessments[key] = result.assessment
        except KeyError:
            continue
    return {"alerts": [warning.as_dict() for warning in detect_early_warnings(graph, assessments)]}


@router.post("/analysis/rebuild")
async def rebuild_analysis_artifacts(
    _current_user: dict = Depends(require_roles(Role.ADMIN)),
    driver=Depends(get_driver),
):
    repo = _repo_or_503(driver)
    payload = await repo.get_all_graph()
    graph = InMemoryGraph(nodes=payload["nodes"], relationships=payload["relationships"])

    analysis_results: list[AnalysisResult] = []
    for key in list(graph.all_entity_keys()):
        result = analyze_entity(graph, key)
        analysis_results.append(result)
        await repo.update_node_properties(
            key[0],
            key[1],
            {
                "riskScore": result.assessment.score,
                "riskLevel": result.assessment.level,
                "confidence": result.assessment.confidence,
                "verificationStatus": "needs_review"
                if result.assessment.level in {"high", "critical"}
                else graph.nodes[key].get("verificationStatus", "unreviewed"),
            },
        )

    artifact_nodes = []
    artifact_relationships = []
    for result in analysis_results:
        if result.assessment.level in {"high", "critical"} or result.blacklist_candidate:
            nodes, relationships = build_analysis_artifacts(result)
            artifact_nodes.extend(nodes)
            artifact_relationships.extend(relationships)

    nodes_merged = 0
    relationships_merged = 0
    for node in artifact_nodes:
        await repo.merge_node(str(node["type"]), str(node["id"]), node)
        nodes_merged += 1
    for relationship in artifact_relationships:
        props = relationship.as_dict()
        from_data = props.pop("from")
        to_data = props.pop("to")
        rel_type = props.pop("type")
        merged = await repo.merge_relationship(
            from_type=from_data["type"],
            from_id=from_data["id"],
            to_type=to_data["type"],
            to_id=to_data["id"],
            rel_type=rel_type,
            props=props,
        )
        if merged is not None:
            relationships_merged += 1

    warnings = detect_early_warnings(graph, {result.assessment.subject.key: result.assessment for result in analysis_results})
    return {
        "status": "success",
        "assessments": len(analysis_results),
        "artifactNodesMerged": nodes_merged,
        "artifactRelationshipsMerged": relationships_merged,
        "earlyWarnings": [warning.as_dict() for warning in warnings],
    }


@router.get("/rules")
async def list_scoring_rules(
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
):
    return {
        "rules": [
            {
                "ruleId": rule.rule_id,
                "title": rule.title,
                "weight": rule.weight,
                "editableInPrototype": False,
            }
            for rule in RULES.values()
        ]
    }

