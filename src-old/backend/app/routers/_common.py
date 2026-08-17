"""
Helper bersama untuk router SATPAM.

simulation only — semua operasi bekerja dengan data dummy/simulasi.
"""

from __future__ import annotations

from fastapi import HTTPException

from app.repositories.neo4j_repo import Neo4jRepository

ANALYST_ROLES = ("analyst", "supervisor", "admin")


def repo_or_503(driver) -> Neo4jRepository:
    """Kembalikan Neo4jRepository atau raise 503 bila driver tidak tersedia."""
    if driver is None:
        raise HTTPException(status_code=503, detail="Database tidak tersedia")
    return Neo4jRepository(driver)


def paginated(result: dict) -> dict:
    """Bentuk response list standar: items + metadata pagination."""
    total = result.get("total", 0)
    limit = result.get("limit", 0) or 0
    offset = result.get("offset", 0)
    return {
        "items": result.get("items", []),
        "total": total,
        "limit": limit,
        "offset": offset,
        "hasMore": (offset + limit) < total,
    }
