"""
Endpoint administrasi: reset dataset prototype & audit log.

simulation only — reset hanya menghapus data dummy prototype.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import Role, require_roles
from app.database import get_driver
from app.routers._common import paginated, repo_or_503

router = APIRouter(prefix="/api", tags=["admin"])


@router.delete("/admin/reset-dataset")
async def reset_dataset(
    current_user: dict = Depends(require_roles(Role.ADMIN)),
    driver=Depends(get_driver),
):
    """
    Hapus seluruh node & relationship prototype (admin only). Setelah reset,
    sebuah audit log dibuat sebagai jejak aksi.
    """
    repo = repo_or_503(driver)
    deleted = await repo.reset_all()
    await repo.write_audit_log(
        actor_id=current_user["id"],
        actor_role=current_user["role"],
        action="RESET_DATASET",
        target_id="*",
        target_type="Dataset",
        old_value=deleted,
        new_value=0,
        note="Reset seluruh dataset prototype (simulasi).",
    )
    return {"status": "success", "deletedNodes": deleted}


@router.get("/audit-logs")
async def list_audit_logs(
    action: Optional[str] = Query(default=None),
    target_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: dict = Depends(require_roles(Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Daftar audit log (supervisor/admin), terbaru lebih dulu."""
    repo = repo_or_503(driver)
    result = await repo.list_nodes(
        "AuditLog",
        filters={"action": action, "targetType": target_type},
        order_by="timestamp",
        limit=limit,
        offset=offset,
    )
    return paginated(result)
