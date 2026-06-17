import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock

from app.main import app
from app.database import get_driver


@pytest.fixture
def mock_neo4j_driver():
    """Driver Neo4j yang di-mock — verify_connectivity tidak raise exception."""
    driver = AsyncMock()
    driver.verify_connectivity = AsyncMock(return_value=None)
    driver.close = AsyncMock(return_value=None)
    return driver


@pytest.fixture
async def client(mock_neo4j_driver):
    """
    AsyncClient dengan dependency override get_driver → mock driver.

    Menggunakan FastAPI dependency_overrides agar lifespan (init_driver) tidak
    menimpa mock yang sudah disiapkan.
    """
    app.dependency_overrides[get_driver] = lambda: mock_neo4j_driver
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_driver, None)


@pytest.fixture
async def client_no_neo4j():
    """AsyncClient yang selalu menerima None sebagai driver (Neo4j tidak tersedia)."""
    app.dependency_overrides[get_driver] = lambda: None
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_driver, None)
