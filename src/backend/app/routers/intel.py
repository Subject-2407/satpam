"""
Endpoint traffic event & crawler finding (intelligence simulasi).

Semua data WAJIB simulationOnly=True — divalidasi oleh model node. Import hanya
untuk admin. Tidak ada monitoring trafik atau crawling nyata.

simulation only.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import Role, require_roles
from app.database import get_driver
from app.models.nodes import CrawlerFindingNode, TrafficEventNode
from app.routers._common import paginated, repo_or_503

router = APIRouter(prefix="/api", tags=["intel"])


class TrafficImportRequest(BaseModel):
    items: List[TrafficEventNode]


class CrawlerImportRequest(BaseModel):
    items: List[CrawlerFindingNode]


async def _import_nodes(repo, node_label: str, nodes) -> dict:
    merged = 0
    errors: list[str] = []
    for node in nodes:
        props = node.model_dump(mode="json", exclude_none=True)
        node_id = props.get("id")
        if not node_id:
            errors.append(f"{node_label}: node tanpa id diabaikan")
            continue
        try:
            await repo.merge_node(node_label, node_id, props)
            merged += 1
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"{node_label}/{node_id}: {exc}")
    return {
        "status": "success" if not errors else "partial",
        "merged": merged,
        "errors": errors,
    }


@router.get("/traffic-events")
async def list_traffic_events(
    event_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Daftar traffic event simulasi."""
    repo = repo_or_503(driver)
    result = await repo.list_nodes(
        "TrafficEvent",
        filters={"eventType": event_type},
        order_by="createdAt",
        limit=limit,
        offset=offset,
    )
    return paginated(result)


@router.post("/traffic-events/import", status_code=201)
async def import_traffic_events(
    body: TrafficImportRequest,
    _current_user: dict = Depends(require_roles(Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Import traffic log simulasi (admin). simulationOnly wajib True."""
    repo = repo_or_503(driver)
    return await _import_nodes(repo, "TrafficEvent", body.items)


@router.get("/crawler-findings")
async def list_crawler_findings(
    finding_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Daftar crawler finding dummy."""
    repo = repo_or_503(driver)
    result = await repo.list_nodes(
        "CrawlerFinding",
        filters={"findingType": finding_type},
        order_by="createdAt",
        limit=limit,
        offset=offset,
    )
    return paginated(result)


@router.post("/crawler-findings/import", status_code=201)
async def import_crawler_findings(
    body: CrawlerImportRequest,
    _current_user: dict = Depends(require_roles(Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Import crawler finding dummy (admin). simulationOnly wajib True."""
    repo = repo_or_503(driver)
    return await _import_nodes(repo, "CrawlerFinding", body.items)
