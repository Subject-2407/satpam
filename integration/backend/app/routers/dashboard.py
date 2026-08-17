"""
Endpoint ringkasan dashboard utama.

Menyediakan agregat untuk halaman utama (FR-066) dan daftar entitas berisiko
tinggi (FR-067). Semua angka berasal dari data dummy/simulasi.

simulation only.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth import Role, require_roles
from app.database import get_driver
from app.routers._common import repo_or_503

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/summary")
async def dashboard_summary(
    top_entities: int = Query(default=5, ge=1, le=50),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """
    Ringkasan dashboard: jumlah laporan, entitas, alert, verification case, dan
    blacklist candidate; breakdown risk level; status breakdown; serta entitas
    berisiko tertinggi. Bahasa indikatif — bukan vonis.
    """
    repo = repo_or_503(driver)
    summary = await repo.dashboard_summary(top_entities_limit=top_entities)
    return {"simulationOnly": True, **summary}
