"""
Endpoint verification case (human verification workflow).

Setiap perubahan status dicatat ke audit log. Penutupan case (closed) hanya
boleh dilakukan supervisor/admin sesuai prinsip keputusan akhir oleh manusia.

simulation only — semua case berasal dari data dummy/simulasi.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import Role, require_roles
from app.database import get_driver
from app.routers._common import paginated, repo_or_503

router = APIRouter(prefix="/api", tags=["verification"])

# Status verifikasi yang valid.
VERIFICATION_STATUSES = {
    "unreviewed",
    "needs_review",
    "verified_risk",
    "false_positive",
    "escalated",
    "closed",
}
# Status yang hanya boleh diset oleh supervisor/admin.
SUPERVISOR_ONLY_STATUSES = {"closed"}


class VerificationUpdate(BaseModel):
    status: str
    decisionNote: Optional[str] = None
    reviewerId: Optional[str] = None


@router.get("/verification-cases")
async def list_verification_cases(
    status: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Daftar verification case dengan filter status/risk level."""
    repo = repo_or_503(driver)
    result = await repo.list_nodes(
        "VerificationCase",
        filters={"status": status, "riskLevel": risk_level},
        order_by="createdAt",
        limit=limit,
        offset=offset,
    )
    return paginated(result)


@router.get("/verification-cases/{case_id}")
async def get_verification_case(
    case_id: str,
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Detail satu verification case."""
    repo = repo_or_503(driver)
    node = await repo.get_node("VerificationCase", case_id)
    if not node:
        raise HTTPException(status_code=404, detail="Verification case tidak ditemukan")
    return {"case": node}


@router.patch("/verification-cases/{case_id}")
async def update_verification_case(
    case_id: str,
    body: VerificationUpdate,
    current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Update status verifikasi dan catatan reviewer; dicatat ke audit log."""
    if body.status not in VERIFICATION_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Status verifikasi tidak valid. Pilihan: {sorted(VERIFICATION_STATUSES)}",
        )
    if body.status in SUPERVISOR_ONLY_STATUSES and current_user["role"] not in (
        Role.SUPERVISOR,
        Role.ADMIN,
    ):
        raise HTTPException(
            status_code=403,
            detail=f"Status '{body.status}' hanya boleh diset oleh supervisor/admin",
        )

    repo = repo_or_503(driver)
    existing = await repo.get_node("VerificationCase", case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Verification case tidak ditemukan")

    old_status = existing.get("status")
    now = datetime.now(timezone.utc).isoformat()
    props = {
        "status": body.status,
        "verificationStatus": body.status,
        "updatedAt": now,
        "reviewerId": body.reviewerId or current_user["id"],
    }
    if body.decisionNote is not None:
        props["decisionNote"] = body.decisionNote

    updated = await repo.update_node_properties("VerificationCase", case_id, props)
    await repo.write_audit_log(
        actor_id=current_user["id"],
        actor_role=current_user["role"],
        action="UPDATE_VERIFICATION_STATUS",
        target_id=case_id,
        target_type="VerificationCase",
        old_value=old_status,
        new_value=body.status,
        note=body.decisionNote,
    )
    return {"case": updated}
