"""
Neo4j repository layer untuk SATPAM.

simulation only — semua operasi pada file ini bekerja dengan data dummy/simulasi.
Tidak ada data asli yang diproses atau disimpan di sini.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from neo4j import AsyncDriver

# Label node yang diizinkan — mencegah injection melalui label name
ALLOWED_NODE_LABELS: frozenset[str] = frozenset(
    {
        "Report",
        "Victim",
        "URL",
        "Domain",
        "LinkShortener",
        "SocialMediaAccount",
        "PhoneNumber",
        "BankAccount",
        "EWallet",
        "QRISMerchant",
        "APK",
        "Keyword",
        "Transaction",
        "TrafficEvent",
        "CrawlerFinding",
        "BlacklistEntity",
        "BlacklistCandidate",
        "BlacklistDecision",
        "Cluster",
        "Evidence",
        "RiskAssessment",
        "VerificationCase",
        "Recommendation",
        "Alert",
        "User",
        "AuditLog",
    }
)

# Property key yang boleh dipakai sebagai filter/sort — mencegah injection lewat key.
ALLOWED_FILTER_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "type",
        "status",
        "verificationStatus",
        "riskLevel",
        "entityType",
        "subjectType",
        "subjectId",
        "alertType",
        "priority",
        "categoryHint",
        "actorRole",
        "action",
        "targetType",
        "eventType",
        "findingType",
        "createdAt",
        "timestamp",
        "riskScore",
        "simulationOnly",
    }
)

# Label entitas indikator yang dicari oleh endpoint pencarian entitas.
ENTITY_SEARCH_LABELS: tuple[str, ...] = (
    "URL",
    "Domain",
    "LinkShortener",
    "SocialMediaAccount",
    "PhoneNumber",
    "BankAccount",
    "EWallet",
    "QRISMerchant",
    "APK",
    "Keyword",
)

# Field teks yang dipindai saat full-text search sederhana pada entitas.
_ENTITY_SEARCH_FIELDS: tuple[str, ...] = (
    "id",
    "label",
    "normalizedUrl",
    "rawUrl",
    "domainName",
    "normalizedNumber",
    "keyword",
    "appName",
    "packageName",
    "username",
    "merchantAlias",
    "accountAlias",
    "walletAlias",
)

# Tipe relationship yang diizinkan
ALLOWED_RELATIONSHIP_TYPES: frozenset[str] = frozenset(
    {
        "REPORTED",
        "MENTIONS",
        "CONTAINS_KEYWORD",
        "REDIRECTS_TO",
        "PROMOTES",
        "CONTACTS",
        "USES_ACCOUNT",
        "TRANSFERRED_TO",
        "OBSERVED_TRAFFIC_TO",
        "HAS_REDIRECT_EVENT",
        "CRAWLED_FROM",
        "FOUND_ENTITY",
        "LINKED_TO_APK",
        "REQUESTS_PERMISSION",
        "SIMILAR_TO",
        "PART_OF_CLUSTER",
        "BLACKLISTED_AS",
        "FLAGGED_AS_CANDIDATE",
        "DECIDED_AS",
        "HAS_EVIDENCE",
        "HAS_RISK_ASSESSMENT",
        "HAS_RECOMMENDATION",
        "OPENED_CASE",
        "REVIEWED_BY",
        "AUDITED_BY",
    }
)


def _sanitize_label(label: str) -> str:
    if label not in ALLOWED_NODE_LABELS:
        raise ValueError(f"Node label '{label}' tidak diizinkan")
    return label


def _sanitize_rel_type(rel_type: str) -> str:
    if rel_type not in ALLOWED_RELATIONSHIP_TYPES:
        raise ValueError(f"Relationship type '{rel_type}' tidak diizinkan")
    return rel_type


def _sanitize_filter_key(key: str) -> str:
    if key not in ALLOWED_FILTER_KEYS:
        raise ValueError(f"Filter key '{key}' tidak diizinkan")
    return key


def _prepare_props(props: dict[str, Any]) -> dict[str, Any]:
    """Serialisasi datetime ke ISO string agar kompatibel dengan Neo4j property store."""
    result: dict[str, Any] = {}
    for k, v in props.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, list):
            result[k] = [item.isoformat() if isinstance(item, datetime) else item for item in v]
        else:
            result[k] = v
    return result


class Neo4jRepository:
    """Akses ke Neo4j graph database untuk data simulasi SATPAM."""

    def __init__(self, driver: AsyncDriver) -> None:
        self.driver = driver

    async def check_connectivity(self) -> bool:
        """Verifikasi koneksi ke Neo4j."""
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    async def create_node(self, node_type: str, props: dict[str, Any]) -> dict[str, Any]:
        """Buat node baru. Gunakan merge_node untuk mencegah duplikasi."""
        label = _sanitize_label(node_type)
        props = _prepare_props(props)
        props.setdefault("verificationStatus", "unreviewed")

        query = f"CREATE (n:`{label}`) SET n = $props RETURN n"
        async with self.driver.session() as session:
            result = await session.run(query, props=props)
            record = await result.single()
            return dict(record["n"])

    async def merge_node(
        self, node_type: str, node_id: str, props: dict[str, Any]
    ) -> dict[str, Any]:
        """
        MERGE (upsert) node berdasarkan id.

        - ON CREATE: set semua properti (termasuk verificationStatus default "unreviewed")
        - ON MATCH: update properti tanpa menghapus properti yang sudah ada
        simulation only — digunakan untuk import dataset dummy.
        """
        label = _sanitize_label(node_type)
        props = _prepare_props(props)
        props["id"] = node_id
        props.setdefault("verificationStatus", "unreviewed")

        query = f"""
        MERGE (n:`{label}` {{id: $node_id}})
        ON CREATE SET n = $props
        ON MATCH SET n += $props
        RETURN n
        """
        async with self.driver.session() as session:
            result = await session.run(query, node_id=node_id, props=props)
            record = await result.single()
            return dict(record["n"])

    async def merge_relationship(
        self,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        rel_type: str,
        props: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """
        MERGE relationship antara dua node.

        simulation only — tidak ada hubungan dengan entitas nyata.
        """
        from_label = _sanitize_label(from_type)
        to_label = _sanitize_label(to_type)
        safe_rel = _sanitize_rel_type(rel_type)
        props = _prepare_props(props)

        query = f"""
        MATCH (from:`{from_label}` {{id: $from_id}})
        MATCH (to:`{to_label}` {{id: $to_id}})
        MERGE (from)-[r:`{safe_rel}`]->(to)
        ON CREATE SET r = $props
        ON MATCH SET r += $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(
                query, from_id=from_id, to_id=to_id, props=props
            )
            record = await result.single()
            return dict(record["r"]) if record else None

    async def get_node(self, node_type: str, node_id: str) -> Optional[dict[str, Any]]:
        """Ambil satu node berdasarkan label dan id."""
        label = _sanitize_label(node_type)
        query = f"""
        MATCH (n:`{label}` {{id: $node_id}})
        RETURN n {{.*, type: coalesce(n.type, labels(n)[0]), labels: labels(n)}} AS node
        """
        async with self.driver.session() as session:
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            return dict(record["node"]) if record else None

    async def update_node_properties(
        self,
        node_type: str,
        node_id: str,
        props: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Update properti node tanpa menghapus properti lama."""
        label = _sanitize_label(node_type)
        props = _prepare_props(props)
        query = f"""
        MATCH (n:`{label}` {{id: $node_id}})
        SET n += $props
        RETURN n {{.*, type: coalesce(n.type, labels(n)[0]), labels: labels(n)}} AS node
        """
        async with self.driver.session() as session:
            result = await session.run(query, node_id=node_id, props=props)
            record = await result.single()
            return dict(record["node"]) if record else None

    async def get_neighborhood(
        self,
        node_type: str,
        node_id: str,
        depth: int = 3,
        limit: int = 150,
    ) -> dict[str, list[dict[str, Any]]]:
        """Ambil neighborhood graph kecil untuk BFS/scoring di engine."""
        label = _sanitize_label(node_type)
        depth = max(0, min(int(depth), 5))
        limit = max(1, min(int(limit), 1000))
        query = f"""
        MATCH (start:`{label}` {{id: $node_id}})
        CALL {{
            WITH start
            MATCH p=(start)-[*0..{depth}]-(n)
            RETURN collect(p)[0..$limit] AS paths
        }}
        WITH paths
        UNWIND paths AS path
        UNWIND nodes(path) AS node
        WITH paths, collect(DISTINCT node) AS nodes
        CALL {{
            WITH paths
            UNWIND paths AS path
            UNWIND relationships(path) AS rel
            RETURN collect(DISTINCT rel) AS rels
        }}
        RETURN
            [node IN nodes |
                node {{.*,
                    type: coalesce(node.type, labels(node)[0]),
                    labels: labels(node)
                }}
            ] AS nodes,
            [rel IN rels |
                rel {{.*,
                    id: coalesce(rel.id, elementId(rel)),
                    type: type(rel),
                    from: {{
                        type: coalesce(startNode(rel).type, labels(startNode(rel))[0]),
                        id: startNode(rel).id
                    }},
                    to: {{
                        type: coalesce(endNode(rel).type, labels(endNode(rel))[0]),
                        id: endNode(rel).id
                    }}
                }}
            ] AS relationships
        """
        async with self.driver.session() as session:
            result = await session.run(query, node_id=node_id, limit=limit)
            record = await result.single()
            if not record:
                return {"nodes": [], "relationships": []}
            return {
                "nodes": [dict(item) for item in record["nodes"]],
                "relationships": [dict(item) for item in record["relationships"]],
            }

    async def get_all_graph(
        self,
        node_limit: int = 1000,
        relationship_limit: int = 5000,
    ) -> dict[str, list[dict[str, Any]]]:
        """Dump graph prototype kecil untuk re-scoring dan early warning."""
        node_limit = max(1, min(int(node_limit), 10000))
        relationship_limit = max(1, min(int(relationship_limit), 50000))
        query = """
        CALL {
            MATCH (n)
            RETURN n
            LIMIT $node_limit
        }
        WITH collect(n) AS nodes
        CALL {
            MATCH ()-[r]->()
            WITH r
            LIMIT $relationship_limit
            RETURN collect(r) AS rels
        }
        RETURN
            [node IN nodes |
                node {.*,
                    type: coalesce(node.type, labels(node)[0]),
                    labels: labels(node)
                }
            ] AS nodes,
            [rel IN rels |
                rel {.*,
                    id: coalesce(rel.id, elementId(rel)),
                    type: type(rel),
                    from: {
                        type: coalesce(startNode(rel).type, labels(startNode(rel))[0]),
                        id: startNode(rel).id
                    },
                    to: {
                        type: coalesce(endNode(rel).type, labels(endNode(rel))[0]),
                        id: endNode(rel).id
                    }
                }
            ] AS relationships
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                node_limit=node_limit,
                relationship_limit=relationship_limit,
            )
            record = await result.single()
            if not record:
                return {"nodes": [], "relationships": []}
            return {
                "nodes": [dict(item) for item in record["nodes"]],
                "relationships": [dict(item) for item in record["relationships"]],
            }

    async def list_nodes(
        self,
        node_type: str,
        *,
        filters: Optional[dict[str, Any]] = None,
        search: Optional[str] = None,
        search_fields: Optional[list[str]] = None,
        order_by: str = "createdAt",
        descending: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List node dengan label tertentu, dengan filter exact-match, full-text
        search sederhana, sorting, dan pagination.

        Mengembalikan {items, total, limit, offset}. total adalah jumlah node
        yang cocok sebelum pagination.
        """
        label = _sanitize_label(node_type)
        order_key = _sanitize_filter_key(order_by)
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))

        params: dict[str, Any] = {"offset": offset, "limit": limit}
        where: list[str] = []
        for i, (key, value) in enumerate((filters or {}).items()):
            if value is None:
                continue
            safe_key = _sanitize_filter_key(key)
            pname = f"f{i}"
            where.append(f"n.`{safe_key}` = ${pname}")
            params[pname] = value

        if search and search_fields:
            params["q"] = search.lower()
            ors = [
                f"toLower(toString(coalesce(n.`{_sanitize_filter_key(f) if f in ALLOWED_FILTER_KEYS else f}`, ''))) CONTAINS $q"
                for f in search_fields
            ]
            where.append("(" + " OR ".join(ors) + ")")

        where_clause = ("WHERE " + " AND ".join(where)) if where else ""
        direction = "DESC" if descending else "ASC"
        query = f"""
        MATCH (n:`{label}`)
        {where_clause}
        WITH n ORDER BY n.`{order_key}` {direction}, n.id
        WITH collect(n) AS allNodes
        RETURN
            size(allNodes) AS total,
            [node IN allNodes[$offset..$offset + $limit] |
                node {{.*,
                    type: coalesce(node.type, labels(node)[0]),
                    labels: labels(node)
                }}
            ] AS items
        """
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            if not record:
                return {"items": [], "total": 0, "limit": limit, "offset": offset}
            return {
                "items": [dict(item) for item in record["items"]],
                "total": record["total"],
                "limit": limit,
                "offset": offset,
            }

    async def search_entities(
        self,
        *,
        node_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        verification_status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Cari entitas indikator lintas tipe (atau satu tipe bila node_type diisi),
        dengan filter risk level / verification status / teks. Hasil diurutkan
        berdasarkan riskScore menurun.
        """
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        where: list[str] = []

        if node_type:
            label = _sanitize_label(node_type)
            params["labels"] = [label]
        else:
            params["labels"] = list(ENTITY_SEARCH_LABELS)
        where.append("any(l IN labels(n) WHERE l IN $labels)")

        if risk_level:
            params["riskLevel"] = risk_level
            where.append("n.riskLevel = $riskLevel")
        if verification_status:
            params["verificationStatus"] = verification_status
            where.append("n.verificationStatus = $verificationStatus")
        if search:
            params["q"] = search.lower()
            ors = [
                f"toLower(toString(coalesce(n.`{f}`, ''))) CONTAINS $q"
                for f in _ENTITY_SEARCH_FIELDS
            ]
            where.append("(" + " OR ".join(ors) + ")")

        where_clause = "WHERE " + " AND ".join(where)
        query = f"""
        MATCH (n)
        {where_clause}
        WITH n ORDER BY coalesce(n.riskScore, 0) DESC, n.id
        WITH collect(n) AS allNodes
        RETURN
            size(allNodes) AS total,
            [node IN allNodes[$offset..$offset + $limit] |
                node {{.*,
                    type: coalesce(node.type, labels(node)[0]),
                    labels: labels(node)
                }}
            ] AS items
        """
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            if not record:
                return {"items": [], "total": 0, "limit": limit, "offset": offset}
            return {
                "items": [dict(item) for item in record["items"]],
                "total": record["total"],
                "limit": limit,
                "offset": offset,
            }

    async def dashboard_summary(self, *, top_entities_limit: int = 5) -> dict[str, Any]:
        """
        Ringkasan dashboard utama (FR-066/FR-067).

        Mengembalikan jumlah laporan, entitas indikator, alert, verification
        case, dan blacklist candidate; breakdown entitas per risk level; status
        breakdown alert/case/candidate; serta daftar entitas berisiko tertinggi.
        simulation only — semua angka berasal dari data dummy.
        """
        top_entities_limit = max(1, min(int(top_entities_limit), 50))
        entity_labels = list(ENTITY_SEARCH_LABELS)

        totals_query = """
        CALL { MATCH (r:`Report`) RETURN count(r) AS reports }
        CALL { MATCH (a:`Alert`) RETURN count(a) AS alerts }
        CALL { MATCH (v:`VerificationCase`) RETURN count(v) AS verificationCases }
        CALL { MATCH (b:`BlacklistCandidate`) RETURN count(b) AS blacklistCandidates }
        CALL {
            MATCH (e)
            WHERE any(l IN labels(e) WHERE l IN $entityLabels)
            RETURN count(e) AS entities
        }
        RETURN reports, alerts, verificationCases, blacklistCandidates, entities
        """
        risk_query = """
        MATCH (e)
        WHERE any(l IN labels(e) WHERE l IN $entityLabels)
        RETURN coalesce(e.riskLevel, 'unknown') AS key, count(e) AS count
        """
        top_query = """
        MATCH (e)
        WHERE any(l IN labels(e) WHERE l IN $entityLabels) AND e.riskScore IS NOT NULL
        WITH e ORDER BY e.riskScore DESC, e.id
        LIMIT $topLimit
        RETURN collect(
            e {.*, type: coalesce(e.type, labels(e)[0]), labels: labels(e)}
        ) AS items
        """

        async def _group_by(session, label: str) -> dict[str, int]:
            safe_label = _sanitize_label(label)
            result = await session.run(
                f"MATCH (n:`{safe_label}`) "
                "RETURN coalesce(n.status, 'unknown') AS key, count(n) AS count"
            )
            return {record["key"]: record["count"] async for record in result}

        async with self.driver.session() as session:
            result = await session.run(totals_query, entityLabels=entity_labels)
            row = await result.single()
            totals = (
                {
                    "reports": row["reports"],
                    "entities": row["entities"],
                    "alerts": row["alerts"],
                    "verificationCases": row["verificationCases"],
                    "blacklistCandidates": row["blacklistCandidates"],
                }
                if row
                else {
                    "reports": 0,
                    "entities": 0,
                    "alerts": 0,
                    "verificationCases": 0,
                    "blacklistCandidates": 0,
                }
            )

            risk_result = await session.run(risk_query, entityLabels=entity_labels)
            risk_counts = {record["key"]: record["count"] async for record in risk_result}
            entities_by_risk = {level: 0 for level in ("critical", "high", "medium", "low")}
            for key, count in risk_counts.items():
                entities_by_risk[key] = entities_by_risk.get(key, 0) + count

            alerts_by_status = await _group_by(session, "Alert")
            cases_by_status = await _group_by(session, "VerificationCase")
            candidates_by_status = await _group_by(session, "BlacklistCandidate")

            top_result = await session.run(
                top_query, entityLabels=entity_labels, topLimit=top_entities_limit
            )
            top_row = await top_result.single()
            top_entities = [dict(item) for item in top_row["items"]] if top_row else []

        return {
            "totals": totals,
            "entitiesByRiskLevel": entities_by_risk,
            "alertsByStatus": alerts_by_status,
            "verificationCasesByStatus": cases_by_status,
            "blacklistCandidatesByStatus": candidates_by_status,
            "topRiskEntities": top_entities,
        }

    async def write_audit_log(
        self,
        *,
        actor_id: str,
        actor_role: str,
        action: str,
        target_id: str,
        target_type: str,
        old_value: Any = None,
        new_value: Any = None,
        note: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Catat aksi penting ke node AuditLog. Bila node User dengan id actor ada
        di graph, hubungkan via AUDITED_BY; bila tidak, lewati tanpa gagal.
        simulation only.
        """
        from uuid import uuid4

        audit_id = f"audit-{uuid4().hex[:12]}"
        props = _prepare_props(
            {
                "id": audit_id,
                "type": "AuditLog",
                "actorId": actor_id,
                "actorRole": actor_role,
                "action": action,
                "targetId": target_id,
                "targetType": target_type,
                "oldValue": old_value,
                "newValue": new_value,
                "note": note,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "verificationStatus": "unreviewed",
            }
        )
        query = """
        CREATE (a:`AuditLog`)
        SET a = $props
        WITH a
        OPTIONAL MATCH (u:`User` {id: $actor_id})
        FOREACH (_ IN CASE WHEN u IS NULL THEN [] ELSE [1] END |
            MERGE (a)-[:`AUDITED_BY`]->(u))
        RETURN properties(a) AS node
        """
        async with self.driver.session() as session:
            result = await session.run(query, props=props, actor_id=actor_id)
            record = await result.single()
            return dict(record["node"]) if record else props

    async def upsert_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        """
        MERGE node Alert berdasarkan id. Field hasil komputasi engine selalu
        diperbarui, tetapi status review (status) dipertahankan agar keputusan
        analyst tidak tertimpa saat alert dihitung ulang.
        """
        props = _prepare_props(dict(alert))
        alert_id = props["id"]
        computed = {k: v for k, v in props.items() if k not in {"status", "verificationStatus"}}
        query = """
        MERGE (a:`Alert` {id: $alert_id})
        ON CREATE SET a = $props
        ON MATCH SET a += $computed
        RETURN properties(a) AS node
        """
        async with self.driver.session() as session:
            result = await session.run(
                query, alert_id=alert_id, props=props, computed=computed
            )
            record = await result.single()
            return dict(record["node"]) if record else props

    async def reset_all(self) -> int:
        """Hapus seluruh node dan relationship prototype. Admin only."""
        query = """
        MATCH (n)
        WITH n LIMIT 100000
        DETACH DELETE n
        RETURN count(n) AS deleted
        """
        total = 0
        async with self.driver.session() as session:
            while True:
                result = await session.run(query)
                record = await result.single()
                deleted = record["deleted"] if record else 0
                total += deleted
                if not deleted:
                    break
        return total
