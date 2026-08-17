"""
Endpoint pencarian entitas indikator.

simulation only — semua entitas adalah data dummy/simulasi.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import Role, require_roles
from app.database import get_driver
from app.routers._common import paginated, repo_or_503

router = APIRouter(prefix="/api", tags=["entities"])


@router.get("/entities")
async def search_entities(
    type: Optional[str] = Query(default=None, description="Filter satu tipe node entitas"),
    risk_level: Optional[str] = Query(default=None, description="low|medium|high|critical"),
    verification_status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, description="Cari pada id/value entitas"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """
    Cari entitas indikator lintas tipe (atau satu tipe), dengan filter risk level,
    verification status, dan teks. Hasil diurutkan berdasarkan risk score menurun.
    """
    repo = repo_or_503(driver)
    try:
        result = await repo.search_entities(
            node_type=type,
            risk_level=risk_level,
            verification_status=verification_status,
            search=search,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return paginated(result)
