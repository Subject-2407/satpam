"""
Tests untuk GET /health endpoint menggunakan httpx AsyncClient.
Dirancang agar lulus tanpa koneksi Neo4j asli (dependency override).
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import get_driver


async def test_health_returns_200(client):
    """GET /health selalu mengembalikan HTTP 200."""
    response = await client.get("/health")
    assert response.status_code == 200


async def test_health_schema_has_required_fields(client):
    """Response /health wajib mengandung status, neo4j, dan timestamp."""
    response = await client.get("/health")
    data = response.json()
    assert "status" in data
    assert "neo4j" in data
    assert "timestamp" in data


async def test_health_neo4j_connected(client):
    """Mock driver tersedia + verify_connectivity sukses → status healthy."""
    response = await client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["neo4j"] == "connected"


async def test_health_neo4j_unavailable(client_no_neo4j):
    """Tanpa driver (None) → status degraded, HTTP 200 tetap dikembalikan."""
    response = await client_no_neo4j.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["neo4j"] == "error"


async def test_health_neo4j_error_still_200():
    """verify_connectivity raise Exception → status degraded, HTTP 200."""
    broken = AsyncMock()
    broken.verify_connectivity = AsyncMock(side_effect=Exception("connection refused"))

    app.dependency_overrides[get_driver] = lambda: broken
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            response = await c.get("/health")
    finally:
        app.dependency_overrides.pop(get_driver, None)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["neo4j"] == "error"


async def test_health_timestamp_is_iso_format(client):
    """Field timestamp harus berformat ISO 8601 yang dapat di-parse."""
    response = await client.get("/health")
    data = response.json()
    parsed = datetime.fromisoformat(data["timestamp"])
    assert parsed is not None
