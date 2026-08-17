from __future__ import annotations

from app.services.ai_engine.graph import InMemoryGraph, endpoint_key
from app.services.ai_engine.models import EarlyWarning, NodeKey, RiskAssessment, node_ref_from_key
from app.services.ai_engine.normalization import stable_hash
from app.services.ai_engine.scoring import should_create_blacklist_candidate


def _alert_id(alert_type: str, key: NodeKey) -> str:
    return f"alert-{stable_hash(f'{alert_type}:{key[0]}:{key[1]}', 12)}"


def _warning(
    alert_type: str,
    key: NodeKey,
    priority: str,
    reason: str,
    rule_ids: list[str],
    evidence_node_ids: list[str] | None = None,
) -> EarlyWarning:
    return EarlyWarning(
        id=_alert_id(alert_type, key),
        alert_type=alert_type,
        subject=node_ref_from_key(key),
        priority=priority,  # type: ignore[arg-type]
        reason=reason,
        rule_ids=rule_ids,
        evidence_node_ids=evidence_node_ids or [key[1]],
        simulation_only=True,
    )


def detect_early_warnings(
    graph: InMemoryGraph,
    assessments: dict[NodeKey, RiskAssessment] | None = None,
) -> list[EarlyWarning]:
    warnings: dict[str, EarlyWarning] = {}

    for key, node in graph.nodes.items():
        node_type = node.get("type")

        if node_type == "TrafficEvent":
            request_count = int(node.get("requestCount") or 0)
            event_type = str(node.get("eventType", "")).upper()
            if "SPIKE" in event_type or request_count >= 50:
                for rel_id in graph.outgoing.get(key, []):
                    relationship = graph.get_relationship(rel_id) or {}
                    if relationship.get("type") == "OBSERVED_TRAFFIC_TO":
                        target = endpoint_key(relationship["to"])
                        warning = _warning(
                            "Traffic Spike Alert",
                            target,
                            "high",
                            "Traffic log simulasi menunjukkan lonjakan request ke domain/URL dummy.",
                            ["R-011"],
                            [node["id"], target[1]],
                        )
                        warnings[warning.id] = warning

        if node_type == "CrawlerFinding":
            finding_type = str(node.get("findingType", "")).upper()
            matched_keywords = node.get("matchedKeywords", []) or []
            if "REDIRECT" in finding_type or len(matched_keywords) >= 2:
                for rel_id in graph.outgoing.get(key, []):
                    relationship = graph.get_relationship(rel_id) or {}
                    if relationship.get("type") in {"FOUND_ENTITY", "HAS_REDIRECT_EVENT", "CRAWLED_FROM"}:
                        target = endpoint_key(relationship["to"])
                        warning = _warning(
                            "Suspicious Redirect Alert",
                            target,
                            "high",
                            "Crawler/scraper dummy menemukan redirect atau keyword promosi berisiko.",
                            ["R-012", "R-013"],
                            [node["id"], target[1]],
                        )
                        warnings[warning.id] = warning

        if node_type == "BankAccount":
            incoming_victims = set()
            outgoing_transfer = False
            for rel_id in graph.incoming.get(key, []):
                relationship = graph.get_relationship(rel_id) or {}
                if relationship.get("type") == "TRANSFERRED_TO":
                    source = endpoint_key(relationship["from"])
                    if source[0] == "Victim":
                        incoming_victims.add(source[1])
            for rel_id in graph.outgoing.get(key, []):
                relationship = graph.get_relationship(rel_id) or {}
                if relationship.get("type") == "TRANSFERRED_TO":
                    outgoing_transfer = True
            if len(incoming_victims) >= 2:
                warning = _warning(
                    "Payment Fan-in Alert",
                    key,
                    "high",
                    f"Rekening menerima transfer dari {len(incoming_victims)} korban dummy.",
                    ["R-004"],
                    [key[1], *sorted(incoming_victims)],
                )
                warnings[warning.id] = warning
            if incoming_victims and outgoing_transfer:
                warning = _warning(
                    "Fast Transfer Alert",
                    key,
                    "medium",
                    "Ada pola masuk-keluar dana simulasi pada rekening kolektor.",
                    ["R-008"],
                    [key[1]],
                )
                warnings[warning.id] = warning

        if node_type == "APK":
            permissions = {str(item).upper() for item in node.get("requestedPermissions", [])}
            if permissions & {"READ_CONTACTS", "READ_SMS", "ACCESS_FINE_LOCATION"}:
                warning = _warning(
                    "Suspicious APK Permission Alert",
                    key,
                    "high",
                    "APK dummy meminta permission sensitif dan perlu review.",
                    ["R-007"],
                    [key[1]],
                )
                warnings[warning.id] = warning

    if assessments:
        for key, assessment in assessments.items():
            candidate = should_create_blacklist_candidate(graph, key, assessment)
            if candidate:
                warning = _warning(
                    "Blacklist Candidate Alert",
                    key,
                    assessment.level,
                    "Entitas high/critical otomatis masuk kandidat review, bukan blacklist final.",
                    candidate.rule_ids,
                    [key[1]],
                )
                warnings[warning.id] = warning

    return sorted(
        warnings.values(),
        key=lambda item: ({"critical": 0, "high": 1, "medium": 2, "low": 3}[item.priority], item.id),
    )

