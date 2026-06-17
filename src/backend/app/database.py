from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import settings

_driver: AsyncDriver | None = None


async def init_driver() -> None:
    global _driver
    try:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    except Exception as exc:
        print(f"[WARN] Neo4j driver init failed: {exc}")
        _driver = None


async def close_driver() -> None:
    global _driver
    if _driver:
        try:
            await _driver.close()
        except Exception:
            pass
        _driver = None


def get_driver() -> AsyncDriver | None:
    return _driver
