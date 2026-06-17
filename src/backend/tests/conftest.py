import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock

from app.main import app
from app.auth import SEED_USERS, create_access_token
from app.database import get_driver
from app.repositories.neo4j_repo import ENTITY_SEARCH_LABELS


@pytest.fixture
def mock_neo4j_driver():
    """Driver Neo4j yang di-mock — verify_connectivity tidak raise exception."""
    driver = AsyncMock()
    driver.verify_connectivity = AsyncMock(return_value=None)
    driver.close = AsyncMock(return_value=None)
    return driver


def auth_headers(role: str) -> dict:
    """Bearer header untuk seed user dengan role tertentu."""
    email = {
        "public_reporter": "reporter@satpam.test",
        "analyst": "analyst@satpam.test",
        "supervisor": "supervisor@satpam.test",
        "admin": "admin@satpam.test",
    }[role]
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}


class FakeRepository:
    """
    Repository in-memory yang meniru Neo4jRepository untuk test tanpa Neo4j.

    Store: dict[(label, id)] -> props. Hanya method yang dipakai endpoint baru
    yang diimplementasikan.
    """

    def __init__(self, store: dict | None = None) -> None:
        self.store = store if store is not None else {}

    async def check_connectivity(self) -> bool:
        return True

    async def merge_node(self, node_type, node_id, props):
        node = dict(props)
        node["id"] = node_id
        node.setdefault("type", node_type)
        node.setdefault("verificationStatus", "unreviewed")
        self.store[(node_type, node_id)] = node
        return node

    async def get_node(self, node_type, node_id):
        node = self.store.get((node_type, node_id))
        return dict(node) if node else None

    async def update_node_properties(self, node_type, node_id, props):
        node = self.store.get((node_type, node_id))
        if not node:
            return None
        node.update({k: v for k, v in props.items() if v is not None})
        return dict(node)

    def _matches(self, node, filters, search, search_fields):
        for k, v in (filters or {}).items():
            if v is None:
                continue
            if node.get(k) != v:
                return False
        if search and search_fields:
            q = search.lower()
            if not any(q in str(node.get(f, "")).lower() for f in search_fields):
                return False
        return True

    async def list_nodes(
        self,
        node_type,
        *,
        filters=None,
        search=None,
        search_fields=None,
        order_by="createdAt",
        descending=True,
        limit=50,
        offset=0,
    ):
        items = [
            dict(node)
            for (label, _), node in self.store.items()
            if label == node_type and self._matches(node, filters, search, search_fields)
        ]
        items.sort(key=lambda n: str(n.get(order_by, "")), reverse=descending)
        total = len(items)
        return {
            "items": items[offset : offset + limit],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def search_entities(
        self,
        *,
        node_type=None,
        risk_level=None,
        verification_status=None,
        search=None,
        limit=50,
        offset=0,
    ):
        labels = [node_type] if node_type else list(ENTITY_SEARCH_LABELS)
        fields = ["id", "label", "normalizedUrl", "domainName", "keyword", "appName"]
        items = []
        for (label, _), node in self.store.items():
            if label not in labels:
                continue
            if risk_level and node.get("riskLevel") != risk_level:
                continue
            if verification_status and node.get("verificationStatus") != verification_status:
                continue
            if search and not any(search.lower() in str(node.get(f, "")).lower() for f in fields):
                continue
            items.append(dict(node))
        items.sort(key=lambda n: n.get("riskScore", 0), reverse=True)
        total = len(items)
        return {
            "items": items[offset : offset + limit],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def upsert_alert(self, alert):
        key = ("Alert", alert["id"])
        if key in self.store:
            existing = self.store[key]
            for k, v in alert.items():
                if k not in {"status", "verificationStatus"}:
                    existing[k] = v
        else:
            self.store[key] = dict(alert)
        return dict(self.store[key])

    async def write_audit_log(self, **kwargs):
        audit_id = f"audit-{uuid.uuid4().hex[:12]}"
        node = {
            "id": audit_id,
            "type": "AuditLog",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actorId": kwargs.get("actor_id"),
            "actorRole": kwargs.get("actor_role"),
            "action": kwargs.get("action"),
            "targetId": kwargs.get("target_id"),
            "targetType": kwargs.get("target_type"),
            "oldValue": kwargs.get("old_value"),
            "newValue": kwargs.get("new_value"),
            "note": kwargs.get("note"),
        }
        self.store[("AuditLog", audit_id)] = node
        return node

    async def reset_all(self):
        count = len(self.store)
        self.store.clear()
        return count

    async def get_all_graph(self, node_limit=1000, relationship_limit=5000):
        return {"nodes": [dict(n) for n in self.store.values()], "relationships": []}

    async def get_neighborhood(self, node_type, node_id, depth=3, limit=150):
        node = self.store.get((node_type, node_id))
        if not node:
            return {"nodes": [], "relationships": []}
        return {"nodes": [dict(node)], "relationships": []}

    async def dashboard_summary(self, *, top_entities_limit=5):
        def _count(label):
            return sum(1 for (lbl, _) in self.store if lbl == label)

        def _by_status(label):
            out = {}
            for (lbl, _), node in self.store.items():
                if lbl == label:
                    key = node.get("status", "unknown")
                    out[key] = out.get(key, 0) + 1
            return out

        entity_nodes = [
            dict(node)
            for (lbl, _), node in self.store.items()
            if lbl in ENTITY_SEARCH_LABELS
        ]
        entities_by_risk = {level: 0 for level in ("critical", "high", "medium", "low")}
        for node in entity_nodes:
            key = node.get("riskLevel", "unknown")
            entities_by_risk[key] = entities_by_risk.get(key, 0) + 1

        ranked = sorted(
            (n for n in entity_nodes if n.get("riskScore") is not None),
            key=lambda n: n.get("riskScore", 0),
            reverse=True,
        )
        return {
            "totals": {
                "reports": _count("Report"),
                "entities": len(entity_nodes),
                "alerts": _count("Alert"),
                "verificationCases": _count("VerificationCase"),
                "blacklistCandidates": _count("BlacklistCandidate"),
            },
            "entitiesByRiskLevel": entities_by_risk,
            "alertsByStatus": _by_status("Alert"),
            "verificationCasesByStatus": _by_status("VerificationCase"),
            "blacklistCandidatesByStatus": _by_status("BlacklistCandidate"),
            "topRiskEntities": ranked[:top_entities_limit],
        }


@pytest.fixture
def fake_store():
    return {}


@pytest.fixture
async def fake_repo_client(monkeypatch, fake_store):
    """
    Client dengan Neo4jRepository di-patch ke FakeRepository in-memory.

    Driver tetap di-override agar tidak None (lewat guard 503). Patch dilakukan
    di app.routers._common (dipakai semua endpoint baru via repo_or_503).
    """
    import app.routers._common as common

    monkeypatch.setattr(common, "Neo4jRepository", lambda _driver: FakeRepository(fake_store))
    app.dependency_overrides[get_driver] = lambda: object()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_driver, None)


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
