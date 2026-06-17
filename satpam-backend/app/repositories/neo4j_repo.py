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
