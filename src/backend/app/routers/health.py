from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.database import get_driver
from app.repositories.neo4j_repo import Neo4jRepository

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(driver=Depends(get_driver)):
    """
    Cek status backend dan koneksi Neo4j.

    Selalu mengembalikan HTTP 200. Status "degraded" berarti Neo4j tidak tersedia.
    """
    neo4j_status = "error"
    if driver is not None:
        repo = Neo4jRepository(driver)
        if await repo.check_connectivity():
            neo4j_status = "connected"

    overall = "healthy" if neo4j_status == "connected" else "degraded"
    return {
        "status": overall,
        "neo4j": neo4j_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
