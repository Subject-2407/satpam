"""
Neo4j repository layer untuk SATPAM.

simulation only — semua operasi pada file ini bekerja dengan data dummy/simulasi.
Tidak ada data asli yang diproses atau disimpan di sini.
"""

from datetime import datetime
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
        "User",
        "AuditLog",
    }
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
        RETURN properties(n) + {{type: coalesce(n.type, labels(n)[0]), labels: labels(n)}} AS node
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
        RETURN properties(n) + {{type: coalesce(n.type, labels(n)[0]), labels: labels(n)}} AS node
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
                properties(node) + {{
                    type: coalesce(node.type, labels(node)[0]),
                    labels: labels(node)
                }}
            ] AS nodes,
            [rel IN rels |
                properties(rel) + {{
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
                properties(node) + {
                    type: coalesce(node.type, labels(node)[0]),
                    labels: labels(node)
                }
            ] AS nodes,
            [rel IN rels |
                properties(rel) + {
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
