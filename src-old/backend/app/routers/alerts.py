"""
Endpoint early warning / alert.

Alert dihitung dari graph oleh AI engine lalu dipersistensikan sebagai node
Alert sehingga statusnya dapat diperbarui oleh analyst. Status hasil review
tidak tertimpa saat alert dihitung ulang.

simulation only — semua alert berasal dari data dummy/simulasi.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import Role, require_roles
from app.database import get_driver
from app.routers._common import paginated, repo_or_503
from app.services.ai_engine.alerts import detect_early_warnings
from app.services.ai_engine.analysis import analyze_entity
from app.services.ai_engine.graph import InMemoryGraph

router = APIRouter(prefix="/api", tags=["alerts"])

# Status review yang valid untuk sebuah alert.
ALERT_STATUSES = {"new", "reviewed", "escalated", "false_positive"}


class AlertStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None


def _warning_to_node(warning: dict, now: str) -> dict:
    """Konversi early warning dari engine ke properti node Alert."""
    subject = warning.get("subject", {})
    return {
        "id": warning["id"],
        "type": "Alert",
        "label": warning.get("alertType", "Alert"),
        "alertType": warning.get("alertType"),
        "subjectType": subject.get("type"),
        "subjectId": subject.get("id"),
        "priority": warning.get("priority"),
        "reason": warning.get("reason"),
        "ruleIds": warning.get("ruleIds", []),
        "evidenceNodeIds": warning.get("evidenceNodeIds", []),
        "simulationOnly": True,
        "status": "new",
        "verificationStatus": "unreviewed",
        "createdAt": now,
        "updatedAt": now,
    }


@router.get("/alerts")
async def list_alerts(
    status: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """
    Daftar alert/early warning yang dipersistensikan.

    Alert dihitung ulang dari graph saat ini dan di-upsert (status review
    dipertahankan), lalu dikembalikan dengan filter status/priority.
    """
    repo = repo_or_503(driver)
    payload = await repo.get_all_graph()
    graph = InMemoryGraph(nodes=payload["nodes"], relationships=payload["relationships"])

    assessments = {}
    for key in graph.all_entity_keys():
        try:
            assessments[key] = analyze_entity(graph, key).assessment
        except KeyError:
            continue

    now = datetime.now(timezone.utc).isoformat()
    for warning in detect_early_warnings(graph, assessments):
        await repo.upsert_alert(_warning_to_node(warning.as_dict(), now))

    result = await repo.list_nodes(
        "Alert",
        filters={"status": status, "priority": priority},
        order_by="createdAt",
        limit=limit,
        offset=offset,
    )
    return paginated(result)


@router.patch("/alerts/{alert_id}/status")
async def update_alert_status(
    alert_id: str,
    body: AlertStatusUpdate,
    current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Update status review sebuah alert dan catat ke audit log."""
    if body.status not in ALERT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Status alert tidak valid. Pilihan: {sorted(ALERT_STATUSES)}",
        )
    repo = repo_or_503(driver)
    existing = await repo.get_node("Alert", alert_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Alert tidak ditemukan")

    old_status = existing.get("status")
    now = datetime.now(timezone.utc).isoformat()
    updated = await repo.update_node_properties(
        "Alert",
        alert_id,
        {"status": body.status, "updatedAt": now, "reviewNote": body.note},
    )
    await repo.write_audit_log(
        actor_id=current_user["id"],
        actor_role=current_user["role"],
        action="UPDATE_ALERT_STATUS",
        target_id=alert_id,
        target_type="Alert",
        old_value=old_status,
        new_value=body.status,
        note=body.note,
    )
    return {"alert": updated}
