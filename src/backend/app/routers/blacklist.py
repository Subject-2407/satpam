"""
Endpoint blacklist candidate.

Prinsip etika (lihat CLAUDE.md / SRS):
- `blacklist_candidate` boleh dibuat otomatis oleh sistem.
- `confirmed_blacklist` HANYA boleh diset oleh supervisor/admin (keputusan manusia).
- `recommended_for_blocking` adalah rekomendasi, BUKAN eksekusi blokir.

simulation only — semua kandidat berasal dari data dummy/simulasi.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import Role, require_roles
from app.database import get_driver
from app.routers._common import paginated, repo_or_503

router = APIRouter(prefix="/api", tags=["blacklist"])

# Status kandidat blacklist yang valid (lihat CLAUDE.md).
CANDIDATE_STATUSES = {
    "not_candidate",
    "blacklist_candidate",
    "needs_more_evidence",
    "rejected_candidate",
    "false_positive",
    "confirmed_blacklist",
    "recommended_for_blocking",
    "escalated",
}
# Keputusan final yang hanya boleh diambil supervisor/admin (review manusia).
HUMAN_DECISION_STATUSES = {"confirmed_blacklist", "recommended_for_blocking"}


class CandidateDecision(BaseModel):
    status: str
    decisionNote: Optional[str] = None


@router.get("/blacklist-candidates")
async def list_blacklist_candidates(
    type: Optional[str] = Query(default=None, description="Filter entityType kandidat"),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Daftar kandidat blacklist dengan filter tipe entitas/status."""
    repo = repo_or_503(driver)
    result = await repo.list_nodes(
        "BlacklistCandidate",
        filters={"entityType": type, "status": status},
        order_by="createdAt",
        limit=limit,
        offset=offset,
    )
    return paginated(result)


@router.get("/blacklist-candidates/{candidate_id}")
async def get_blacklist_candidate(
    candidate_id: str,
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Detail satu kandidat blacklist."""
    repo = repo_or_503(driver)
    node = await repo.get_node("BlacklistCandidate", candidate_id)
    if not node:
        raise HTTPException(status_code=404, detail="Kandidat blacklist tidak ditemukan")
    return {"candidate": node}


@router.patch("/blacklist-candidates/{candidate_id}/decision")
async def decide_blacklist_candidate(
    candidate_id: str,
    body: CandidateDecision,
    current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """
    Update keputusan kandidat blacklist. Status final (confirmed_blacklist /
    recommended_for_blocking) hanya boleh diambil supervisor/admin. Dicatat ke
    audit log.
    """
    if body.status not in CANDIDATE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Status kandidat tidak valid. Pilihan: {sorted(CANDIDATE_STATUSES)}",
        )
    if body.status in HUMAN_DECISION_STATUSES and current_user["role"] not in (
        Role.SUPERVISOR,
        Role.ADMIN,
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Keputusan '{body.status}' hanya boleh diambil supervisor/admin "
                "(keputusan akhir oleh manusia)."
            ),
        )

    repo = repo_or_503(driver)
    existing = await repo.get_node("BlacklistCandidate", candidate_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Kandidat blacklist tidak ditemukan")

    old_status = existing.get("status")
    now = datetime.now(timezone.utc).isoformat()
    # Status final menandai entitas sudah lewat review manusia.
    verification_status = (
        "verified_risk" if body.status in HUMAN_DECISION_STATUSES else existing.get("verificationStatus", "needs_review")
    )
    props = {
        "status": body.status,
        "verificationStatus": verification_status,
        "decidedBy": current_user["id"],
        "decidedAt": now,
        "updatedAt": now,
    }
    if body.decisionNote is not None:
        props["decisionNote"] = body.decisionNote

    updated = await repo.update_node_properties("BlacklistCandidate", candidate_id, props)
    await repo.write_audit_log(
        actor_id=current_user["id"],
        actor_role=current_user["role"],
        action="UPDATE_BLACKLIST_DECISION",
        target_id=candidate_id,
        target_type="BlacklistCandidate",
        old_value=old_status,
        new_value=body.status,
        note=body.decisionNote,
    )
    return {"candidate": updated}
