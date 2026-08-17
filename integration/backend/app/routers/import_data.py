"""
Endpoint import dataset dummy ke Neo4j.

simulation only — endpoint ini hanya menerima data dummy sesuai schema SATPAM.
Hanya role admin yang dapat mengakses endpoint ini.
Menggunakan MERGE (bukan CREATE) agar import bisa dijalankan ulang tanpa duplikasi.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import Role, require_roles
from app.database import get_driver
from app.models.nodes import (
    DummyDataImportRequest,
    ImportResponse,
    ImportStats,
)
from app.repositories.neo4j_repo import Neo4jRepository

router = APIRouter(prefix="/api/import", tags=["import"])

# Pemetaan field NodesContainer -> Neo4j node label
_NODE_FIELD_TO_LABEL: list[tuple[str, str]] = [
    ("reports", "Report"),
    ("victims", "Victim"),
    ("urls", "URL"),
    ("domains", "Domain"),
    ("linkShorteners", "LinkShortener"),
    ("socialMediaAccounts", "SocialMediaAccount"),
    ("phoneNumbers", "PhoneNumber"),
    ("bankAccounts", "BankAccount"),
    ("eWallets", "EWallet"),
    ("qrisMerchants", "QRISMerchant"),
    ("apks", "APK"),
    ("keywords", "Keyword"),
    ("transactions", "Transaction"),
    ("trafficEvents", "TrafficEvent"),
    ("crawlerFindings", "CrawlerFinding"),
    ("blacklistEntities", "BlacklistEntity"),
    ("blacklistCandidates", "BlacklistCandidate"),
    ("blacklistDecisions", "BlacklistDecision"),
    ("clusters", "Cluster"),
    ("evidences", "Evidence"),
    ("riskAssessments", "RiskAssessment"),
    ("verificationCases", "VerificationCase"),
    ("recommendations", "Recommendation"),
    ("users", "User"),
    ("auditLogs", "AuditLog"),
]


@router.post("/dummy-data", response_model=ImportResponse)
async def import_dummy_data(
    payload: DummyDataImportRequest,
    current_user: dict = Depends(require_roles(Role.ADMIN)),
    driver=Depends(get_driver),
):
    """
    Import bulk dataset dummy ke Neo4j.

    - Hanya admin yang dapat mengakses endpoint ini.
    - MERGE digunakan sehingga import dapat diulang tanpa duplikasi node/relationship.
    - Semua data harus bersifat simulasi (simulationOnly metadata).
    """
    if driver is None:
        raise HTTPException(status_code=503, detail="Database tidak tersedia")

    repo = Neo4jRepository(driver)
    stats = ImportStats()

    # --- Proses semua node ---
    nodes_container = payload.nodes
    for field_name, node_label in _NODE_FIELD_TO_LABEL:
        node_list = getattr(nodes_container, field_name, [])
        for node in node_list:
            try:
                props = node.model_dump(mode="json", exclude_none=True)
                node_id: str | None = props.get("id")
                if not node_id:
                    stats.skipped += 1
                    stats.errors.append(f"{node_label}: node tanpa id diabaikan")
                    continue
                await repo.merge_node(node_label, node_id, props)
                stats.nodes_merged += 1
            except Exception as exc:
                stats.skipped += 1
                node_id_hint = getattr(node, "id", "?")
                stats.errors.append(f"{node_label}/{node_id_hint}: {exc}")

    # --- Proses semua relationship ---
    for rel in payload.relationships:
        try:
            props = rel.model_dump(mode="json", exclude_none=True, by_alias=True)
            from_data: dict = props.pop("from", {})
            to_data: dict = props.pop("to", {})
            rel_type: str = props.pop("type", "")

            result = await repo.merge_relationship(
                from_type=from_data["type"],
                from_id=from_data["id"],
                to_type=to_data["type"],
                to_id=to_data["id"],
                rel_type=rel_type,
                props=props,
            )
            if result is not None:
                stats.relationships_merged += 1
            else:
                stats.skipped += 1
                stats.errors.append(
                    f"Relationship {rel.id}: salah satu node tidak ditemukan"
                )
        except Exception as exc:
            stats.skipped += 1
            stats.errors.append(f"Relationship {rel.id}: {exc}")

    status_str = "success" if not stats.errors else "partial"
    return ImportResponse(
        status=status_str,
        stats=stats,
        message=(
            f"Import selesai: {stats.nodes_merged} node ter-merge, "
            f"{stats.relationships_merged} relationship ter-merge, "
            f"{stats.skipped} diabaikan"
        ),
    )
