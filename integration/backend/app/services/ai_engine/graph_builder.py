from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.ai_engine.extractor import extract_report_entities
from app.services.ai_engine.graph import InMemoryGraph, graph_from_dataset
from app.services.ai_engine.models import (
    ExtractionResult,
    GraphBuildResult,
    GraphRelationship,
    NodeRef,
    now_iso,
)
from app.services.ai_engine.normalization import stable_relationship_id


@dataclass
class ReportGraphInput:
    report_id: str
    source: str
    description: str
    category_hint: str
    submitted_by: str | None = None
    submitted_by_role: str | None = None
    urls: list[str] | None = None
    phone_numbers: list[str] | None = None
    bank_accounts: list[dict[str, Any]] | None = None
    apps: list[dict[str, Any]] | None = None
    created_at: str | None = None


def _base_props(props: dict[str, Any], *, now: str) -> dict[str, Any]:
    merged = dict(props)
    merged.setdefault("createdAt", now)
    merged.setdefault("updatedAt", now)
    merged.setdefault("firstSeenAt", now)
    merged.setdefault("lastSeenAt", now)
    merged.setdefault("confidence", "medium")
    merged.setdefault("riskScore", 0)
    merged.setdefault("riskLevel", "low")
    merged.setdefault("verificationStatus", "unreviewed")
    return merged


def _relationship(
    rel_type: str,
    from_node: dict[str, Any],
    to_node: dict[str, Any],
    *,
    source: str,
    confidence: str = "medium",
    weight: float = 1.0,
    now: str,
) -> GraphRelationship:
    from_ref = NodeRef.from_node(from_node)
    to_ref = NodeRef.from_node(to_node)
    return GraphRelationship(
        id=stable_relationship_id(rel_type, from_ref.type, from_ref.id, to_ref.type, to_ref.id),
        type=rel_type,
        from_ref=from_ref,
        to_ref=to_ref,
        source=source,
        confidence=confidence,  # type: ignore[arg-type]
        weight=weight,
        properties={
            "evidenceId": None,
            "firstSeenAt": now,
            "lastSeenAt": now,
            "createdAt": now,
        },
    )


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for node in nodes:
        key = (str(node["type"]), str(node["id"]))
        if key in merged:
            merged[key].update({k: v for k, v in node.items() if v not in (None, "", [])})
        else:
            merged[key] = dict(node)
    return list(merged.values())


def _dedupe_relationships(relationships: list[GraphRelationship]) -> list[GraphRelationship]:
    merged: dict[str, GraphRelationship] = {}
    for relationship in relationships:
        merged[relationship.id] = relationship
    return list(merged.values())


def _entities_by_type(nodes: list[dict[str, Any]], node_type: str) -> list[dict[str, Any]]:
    return [node for node in nodes if node.get("type") == node_type]


def build_report_graph(report: ReportGraphInput) -> GraphBuildResult:
    now = report.created_at or now_iso()
    extraction = extract_report_entities(
        report.description,
        source=report.source,
        category_hint=report.category_hint,
        urls=report.urls,
        phone_numbers=report.phone_numbers,
        bank_accounts=report.bank_accounts,
        apps=report.apps,
    )

    report_node = _base_props(
        {
            "id": report.report_id,
            "type": "Report",
            "label": f"Laporan {report.category_hint.replace('_', ' ').title()}",
            "source": report.source,
            "description": report.description,
            "categoryHint": report.category_hint,
            "status": "auto_triaged" if extraction.entities else "new",
            "submittedBy": report.submitted_by,
            "submittedByRole": report.submitted_by_role,
        },
        now=now,
    )

    nodes = [report_node]
    nodes.extend(_base_props(entity.properties, now=now) for entity in extraction.entities)
    nodes = _dedupe_nodes(nodes)

    relationships: list[GraphRelationship] = []
    for node in nodes:
        if node["type"] == "Report":
            continue
        rel_type = "CONTAINS_KEYWORD" if node["type"] == "Keyword" else "MENTIONS"
        relationships.append(
            _relationship(rel_type, report_node, node, source=report.source, weight=1.0, now=now)
        )

    urls = _entities_by_type(nodes, "URL")
    domains = _entities_by_type(nodes, "Domain")
    phones = _entities_by_type(nodes, "PhoneNumber")
    bank_accounts = _entities_by_type(nodes, "BankAccount")
    ewallets = _entities_by_type(nodes, "EWallet")
    qris = _entities_by_type(nodes, "QRISMerchant")
    apks = _entities_by_type(nodes, "APK")
    keywords = _entities_by_type(nodes, "Keyword")
    socials = _entities_by_type(nodes, "SocialMediaAccount")

    domain_by_name = {node.get("domainName"): node for node in domains}
    for url in urls:
        domain = domain_by_name.get(url.get("domain"))
        if domain:
            relationships.append(
                _relationship("REDIRECTS_TO", url, domain, source=report.source, weight=1.0, now=now)
            )

    for domain in domains:
        for phone in phones:
            relationships.append(
                _relationship("CONTACTS", domain, phone, source=report.source, weight=1.2, now=now)
            )

    for phone in phones:
        for account in bank_accounts + ewallets + qris:
            relationships.append(
                _relationship("USES_ACCOUNT", phone, account, source=report.source, weight=1.4, now=now)
            )

    for url in urls:
        for apk in apks:
            relationships.append(
                _relationship("LINKED_TO_APK", url, apk, source=report.source, weight=1.2, now=now)
            )

    for domain in domains:
        for apk in apks:
            relationships.append(
                _relationship("LINKED_TO_APK", domain, apk, source=report.source, weight=1.2, now=now)
            )

    permission_keywords = [
        keyword for keyword in keywords if keyword.get("category") == "apk_permission"
    ]
    for apk in apks:
        for keyword in permission_keywords:
            relationships.append(
                _relationship(
                    "REQUESTS_PERMISSION",
                    apk,
                    keyword,
                    source=report.source,
                    weight=1.2,
                    now=now,
                )
            )

    for social in socials:
        for url in urls:
            relationships.append(
                _relationship("PROMOTES", social, url, source=report.source, weight=1.2, now=now)
            )

    return GraphBuildResult(
        nodes=nodes,
        relationships=_dedupe_relationships(relationships),
        extraction=extraction,
    )


def dataset_to_graph(dataset: dict[str, Any]) -> InMemoryGraph:
    return graph_from_dataset(dataset)


def graph_build_result_to_graph(result: GraphBuildResult) -> InMemoryGraph:
    return InMemoryGraph(nodes=result.nodes, relationships=result.relationship_dicts())

