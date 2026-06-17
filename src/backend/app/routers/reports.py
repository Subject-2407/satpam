import uuid
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_driver
from app.repositories.neo4j_repo import Neo4jRepository
from app.services.ai_engine.analysis import analyze_entity
from app.services.ai_engine.artifacts import build_analysis_artifacts
from app.services.ai_engine.graph_builder import (
    ReportGraphInput,
    build_report_graph,
    graph_build_result_to_graph,
)

router = APIRouter(prefix="/api", tags=["reports"])


class BankAccountInput(BaseModel):
    bankName: str
    accountAlias: str
    maskedAccountNumber: str


class AppInput(BaseModel):
    appName: str
    packageName: str


class ReportCreateRequest(BaseModel):
    source: str = "user_report"
    description: str
    categoryHint: Literal[
        "judol", "pinjol_illegal", "cross_ecosystem", "payment_flow", "traffic_crawler", "benign"
    ]
    urls: Optional[List[str]] = None
    phoneNumbers: Optional[List[str]] = None
    bankAccounts: Optional[List[BankAccountInput]] = None
    apps: Optional[List[AppInput]] = None


class ReportCreateResponse(BaseModel):
    reportId: str
    status: str
    message: str
    extractedEntities: int = 0
    nodesMerged: int = 0
    relationshipsMerged: int = 0
    analysis: dict[str, Any] | None = None


@router.post("/reports", response_model=ReportCreateResponse, status_code=201)
async def create_report(
    body: ReportCreateRequest,
    current_user: dict = Depends(get_current_user),
    driver=Depends(get_driver),
):
    """
    Process a dummy report through the AI engine and persist the graph.

    The pipeline is: extraction -> normalization -> graph build -> scoring ->
    risk artifacts. High/critical results open review artifacts only; no final
    blacklist or blocking action is produced automatically.
    """
    if driver is None:
        raise HTTPException(status_code=503, detail="Database tidak tersedia")

    report_id = f"report-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    build_result = build_report_graph(
        ReportGraphInput(
            report_id=report_id,
            source=body.source,
            description=body.description,
            category_hint=body.categoryHint,
            submitted_by=current_user["id"],
            submitted_by_role=current_user["role"],
            urls=body.urls or [],
            phone_numbers=body.phoneNumbers or [],
            bank_accounts=[item.model_dump() for item in (body.bankAccounts or [])],
            apps=[item.model_dump() for item in (body.apps or [])],
            created_at=now,
        )
    )
    if build_result.extraction.guardrail_violations:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Input prototype harus memakai data dummy/simulasi.",
                "violations": build_result.extraction.guardrail_violations,
            },
        )

    graph = graph_build_result_to_graph(build_result)
    report_key = ("Report", report_id)
    report_analysis = analyze_entity(graph, report_key)

    artifact_nodes: list[dict[str, Any]] = []
    artifact_relationships = []
    nodes, relationships = build_analysis_artifacts(report_analysis, created_at=now)
    artifact_nodes.extend(nodes)
    artifact_relationships.extend(relationships)

    for key in list(graph.nodes):
        if key == report_key:
            continue
        entity_analysis = analyze_entity(graph, key)
        if entity_analysis.assessment.level in {"high", "critical"} or entity_analysis.blacklist_candidate:
            nodes, relationships = build_analysis_artifacts(entity_analysis, created_at=now)
            artifact_nodes.extend(nodes)
            artifact_relationships.extend(relationships)

    repo = Neo4jRepository(driver)
    nodes_merged = 0
    relationships_merged = 0
    try:
        for node in list(graph.nodes.values()) + artifact_nodes:
            await repo.merge_node(str(node["type"]), str(node["id"]), node)
            nodes_merged += 1

        for relationship in build_result.relationships + artifact_relationships:
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
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gagal memproses laporan: {exc}")

    return ReportCreateResponse(
        reportId=report_id,
        status=graph.nodes[report_key].get("status", "auto_triaged"),
        message="Laporan dummy diterima, diekstrak, dianalisis, dan siap direview",
        extractedEntities=len(build_result.extraction.entities),
        nodesMerged=nodes_merged,
        relationshipsMerged=relationships_merged,
        analysis=report_analysis.as_dict(),
    )

