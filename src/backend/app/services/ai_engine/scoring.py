from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.services.ai_engine.graph import InMemoryGraph, endpoint_key
from app.services.ai_engine.models import (
    BlacklistCandidateDraft,
    EvidencePath,
    NodeKey,
    Recommendation,
    RiskAssessment,
    RiskLevel,
    RuleHit,
    node_ref_from_key,
)
from app.services.ai_engine.search import bfs_evidence_path


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    title: str
    weight: int


RULES: dict[str, RuleDefinition] = {
    "R-001": RuleDefinition("R-001", "Domain/URL mengandung keyword judol", 15),
    "R-002": RuleDefinition("R-002", "Teks atau keyword mengarah ke pinjol ilegal", 15),
    "R-003": RuleDefinition("R-003", "Nomor WhatsApp muncul di banyak laporan", 25),
    "R-004": RuleDefinition("R-004", "Rekening menerima banyak transfer korban dummy", 25),
    "R-005": RuleDefinition("R-005", "Entitas terhubung ke blacklist dummy", 35),
    "R-006": RuleDefinition("R-006", "Domain/URL mengarah ke APK mencurigakan", 20),
    "R-007": RuleDefinition("R-007", "APK meminta permission sensitif", 20),
    "R-008": RuleDefinition("R-008", "Dana simulasi keluar cepat dari rekening kolektor", 20),
    "R-009": RuleDefinition("R-009", "Akun promosi menyebarkan banyak URL", 20),
    "R-010": RuleDefinition("R-010", "Indikasi lintas ekosistem judol dan pinjol", 20),
    "R-011": RuleDefinition("R-011", "Traffic simulasi menunjukkan lonjakan request", 15),
    "R-012": RuleDefinition("R-012", "Crawler dummy menemukan redirect chain", 15),
    "R-013": RuleDefinition("R-013", "Keyword promosi dan kontak/payment muncul bersama", 25),
    "R-014": RuleDefinition("R-014", "Kategori laporan atau cluster memperkuat indikasi", 10),
    "R-015": RuleDefinition("R-015", "Node punya koneksi graph tinggi", 10),
}

SCORE_CAP = 100
BLACKLIST_CANDIDATE_TYPES = {
    "URL",
    "Domain",
    "LinkShortener",
    "SocialMediaAccount",
    "PhoneNumber",
    "BankAccount",
    "EWallet",
    "QRISMerchant",
    "APK",
}


def risk_level(score: int) -> RiskLevel:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def confidence_for(rule_hits: list[RuleHit], score: int) -> str:
    signal_count = len(rule_hits)
    if score >= 80 or signal_count >= 4:
        return "high"
    if score >= 35 or signal_count >= 2:
        return "medium"
    return "low"


def _hit(rule_id: str, evidence: str, weight: int | None = None) -> RuleHit:
    rule = RULES[rule_id]
    return RuleHit(
        rule_id=rule.rule_id,
        title=rule.title,
        weight=rule.weight if weight is None else weight,
        evidence=evidence,
    )


def _node_text(node: dict[str, Any]) -> str:
    values = [
        node.get("label"),
        node.get("description"),
        node.get("domainName"),
        node.get("normalizedUrl"),
        node.get("rawUrl"),
        node.get("category"),
        node.get("categoryHint"),
        node.get("keyword"),
        node.get("appName"),
        node.get("packageName"),
    ]
    return " ".join(str(value).lower() for value in values if value)


def _context_keys(graph: InMemoryGraph, key: NodeKey, max_depth: int = 2) -> set[NodeKey]:
    return graph.neighborhood_keys(key, max_depth=max_depth, limit=250)


def _relationships_in_context(graph: InMemoryGraph, keys: set[NodeKey]) -> list[dict[str, Any]]:
    return [
        relationship
        for relationship in graph.relationships.values()
        if endpoint_key(relationship["from"]) in keys and endpoint_key(relationship["to"]) in keys
    ]


def _nodes_in_context(graph: InMemoryGraph, keys: set[NodeKey]) -> list[dict[str, Any]]:
    return [graph.nodes[key] for key in keys if key in graph.nodes]


def _has_relationship_type(graph: InMemoryGraph, keys: set[NodeKey], rel_type: str) -> bool:
    return any(relationship.get("type") == rel_type for relationship in _relationships_in_context(graph, keys))


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _incoming_transfer_victims(graph: InMemoryGraph, key: NodeKey) -> set[str]:
    victims: set[str] = set()
    for rel_id in graph.incoming.get(key, []):
        relationship = graph.get_relationship(rel_id) or {}
        if relationship.get("type") != "TRANSFERRED_TO":
            continue
        from_key = endpoint_key(relationship["from"])
        if from_key[0] == "Victim":
            victims.add(from_key[1])
    return victims


def _has_fast_outgoing_transfer(graph: InMemoryGraph, key: NodeKey) -> bool:
    incoming_times: list[datetime] = []
    outgoing_times: list[datetime] = []
    for rel_id in graph.incoming.get(key, []):
        relationship = graph.get_relationship(rel_id) or {}
        if relationship.get("type") == "TRANSFERRED_TO":
            timestamp = _parse_iso(relationship.get("firstSeenAt") or relationship.get("createdAt"))
            if timestamp:
                incoming_times.append(timestamp)
    for rel_id in graph.outgoing.get(key, []):
        relationship = graph.get_relationship(rel_id) or {}
        if relationship.get("type") == "TRANSFERRED_TO":
            timestamp = _parse_iso(relationship.get("firstSeenAt") or relationship.get("createdAt"))
            if timestamp:
                outgoing_times.append(timestamp)
    for incoming in incoming_times:
        for outgoing in outgoing_times:
            delta = (outgoing - incoming).total_seconds()
            if 0 <= delta <= 10 * 60:
                return True
    return False


def _categories(nodes: list[dict[str, Any]]) -> set[str]:
    categories: set[str] = set()
    for node in nodes:
        for field in ("category", "categoryHint"):
            value = node.get(field)
            if value:
                categories.add(str(value))
        if node.get("type") == "Keyword" and node.get("category"):
            categories.add(str(node["category"]))
    return categories


def _has_contact_or_payment(nodes: list[dict[str, Any]]) -> bool:
    return any(
        node.get("type")
        in {"PhoneNumber", "BankAccount", "EWallet", "QRISMerchant"}
        for node in nodes
    )


def _traffic_spike(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    for node in nodes:
        if node.get("type") != "TrafficEvent":
            continue
        event_type = str(node.get("eventType", "")).upper()
        request_count = int(node.get("requestCount") or 0)
        if "SPIKE" in event_type or request_count >= 50:
            return node
    return None


def _crawler_redirect(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    for node in nodes:
        if node.get("type") != "CrawlerFinding":
            continue
        finding_type = str(node.get("findingType", "")).upper()
        if "REDIRECT" in finding_type:
            return node
    return None


def _sensitive_apk(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    sensitive = {"READ_CONTACTS", "READ_SMS", "ACCESS_FINE_LOCATION", "CONTACTS", "SMS"}
    for node in nodes:
        if node.get("type") != "APK":
            continue
        permissions = {str(item).upper() for item in node.get("requestedPermissions", [])}
        if permissions & sensitive:
            return node
    return None


def _blacklist_hit(graph: InMemoryGraph, keys: set[NodeKey]) -> dict[str, Any] | None:
    for relationship in _relationships_in_context(graph, keys):
        if relationship.get("type") == "BLACKLISTED_AS":
            blacklist_key = endpoint_key(relationship["to"])
            return graph.get_node(blacklist_key) or relationship
    for key in keys:
        node = graph.get_node(key) or {}
        if node.get("type") == "BlacklistEntity":
            return node
    return None


def _recommendations(level: RiskLevel, subject_type: str, rule_hits: list[RuleHit]) -> list[Recommendation]:
    if level in {"high", "critical"}:
        return [
            Recommendation(
                action_type="prioritaskan_verifikasi",
                priority=level,
                reason="Skor risiko tinggi dan perlu review analis sebelum keputusan akhir.",
            ),
            Recommendation(
                action_type="periksa_evidence_path",
                priority=level,
                reason="Jalur bukti dan rule aktif perlu dibandingkan dengan konteks laporan.",
            ),
        ]
    if level == "medium":
        return [
            Recommendation(
                action_type="monitor_dan_korelasi",
                priority="medium",
                reason="Ada beberapa sinyal risiko, tetapi belum cukup untuk eskalasi otomatis.",
            )
        ]
    return [
        Recommendation(
            action_type="arsipkan_atau_monitor_ringan",
            priority="low",
            reason="Sinyal risiko rendah pada data dummy saat ini.",
        )
    ]


def score_entity(graph: InMemoryGraph, key: NodeKey, *, max_depth: int = 2) -> RiskAssessment:
    node = graph.get_node(key)
    if not node:
        raise KeyError(f"Node not found: {key}")

    keys = _context_keys(graph, key, max_depth=max_depth)
    nodes = _nodes_in_context(graph, keys)
    text = " ".join(_node_text(item) for item in nodes)
    categories = _categories(nodes)
    rule_hits: list[RuleHit] = []

    if any(token in text for token in ("slot", "maxwin", "bonus", "gacor")):
        rule_hits.append(_hit("R-001", "Domain/URL atau keyword di sekitar node memuat istilah judol."))

    if categories & {"pinjol_illegal"} or any(
        token in text for token in ("cair cepat", "pinjaman", "tanpa ojk", "sebar data")
    ):
        rule_hits.append(_hit("R-002", "Konteks node memuat keyword pinjol ilegal."))

    phone_nodes = [item for item in nodes if item.get("type") == "PhoneNumber"]
    if any(int(item.get("reportCount") or 0) >= 3 for item in phone_nodes):
        rule_hits.append(_hit("R-003", "Nomor WhatsApp terkait muncul pada banyak laporan dummy."))

    for account_key in [candidate for candidate in keys if candidate[0] == "BankAccount"]:
        victims = _incoming_transfer_victims(graph, account_key)
        if len(victims) >= 2:
            rule_hits.append(
                _hit("R-004", f"Rekening menerima transfer dari {len(victims)} korban dummy.")
            )
            break

    blacklist = _blacklist_hit(graph, keys)
    if blacklist:
        severity = str(blacklist.get("severity", "high"))
        extra = 10 if severity == "critical" else 0
        rule_hits.append(
            _hit("R-005", f"Terhubung ke blacklist dummy severity {severity}.", weight=35 + extra)
        )

    if _has_relationship_type(graph, keys, "LINKED_TO_APK"):
        rule_hits.append(_hit("R-006", "Domain/URL dalam konteks mengarah ke APK."))

    apk = _sensitive_apk(nodes)
    if apk:
        rule_hits.append(
            _hit("R-007", f"APK {apk.get('label', apk.get('id'))} meminta permission sensitif.")
        )

    if any(_has_fast_outgoing_transfer(graph, account_key) for account_key in keys if account_key[0] == "BankAccount"):
        rule_hits.append(_hit("R-008", "Ada pola dana simulasi keluar cepat dari rekening kolektor."))

    for social_key in [candidate for candidate in keys if candidate[0] == "SocialMediaAccount"]:
        promoted_urls = {
            endpoint_key((graph.get_relationship(rel_id) or {}).get("to", {}))[1]
            for rel_id in graph.outgoing.get(social_key, [])
            if (graph.get_relationship(rel_id) or {}).get("type") == "PROMOTES"
        }
        if len(promoted_urls) >= 2:
            rule_hits.append(_hit("R-009", "Akun promosi menyebarkan beberapa URL dummy."))
            break

    if ("judol" in categories or "judol_promo" in categories or "cross_ecosystem" in categories) and (
        "pinjol_illegal" in categories or any(item.get("type") == "APK" for item in nodes)
    ):
        rule_hits.append(_hit("R-010", "Node menghubungkan sinyal judol dan pinjol/APK."))

    traffic = _traffic_spike(nodes)
    if traffic:
        rule_hits.append(
            _hit(
                "R-011",
                f"Traffic simulasi {traffic.get('id')} menunjukkan request count {traffic.get('requestCount')}.",
            )
        )

    crawler = _crawler_redirect(nodes)
    if crawler:
        rule_hits.append(_hit("R-012", f"Crawler dummy {crawler.get('id')} menemukan redirect chain."))

    keyword_nodes = [item for item in nodes if item.get("type") == "Keyword" and int(item.get("weight") or 0) > 0]
    if keyword_nodes and _has_contact_or_payment(nodes):
        rule_hits.append(
            _hit("R-013", "Keyword promosi risiko muncul bersama kontak atau payment dummy.")
        )

    category_hint = str(node.get("categoryHint") or node.get("category") or "")
    if category_hint in {"judol", "judol_promo", "pinjol_illegal", "cross_ecosystem", "traffic_crawler", "payment_flow"}:
        rule_hits.append(_hit("R-014", f"Kategori {category_hint} memperkuat prioritas review."))

    degree = graph.degree(key)
    if degree >= 4:
        rule_hits.append(_hit("R-015", f"Node memiliki degree {degree}, cukup sentral pada graph prototype."))

    raw_score = sum(hit.weight for hit in rule_hits)
    if "benign" in categories and raw_score < 40:
        raw_score = max(0, raw_score - 20)
    score = min(SCORE_CAP, raw_score)
    level = risk_level(score)
    confidence = confidence_for(rule_hits, score)
    explanation = build_explanation(score, level, confidence, rule_hits)
    assessment = RiskAssessment(
        subject=node_ref_from_key(key),
        score=score,
        level=level,
        confidence=confidence,  # type: ignore[arg-type]
        rule_hits=rule_hits,
        explanation=explanation,
    )
    assessment.recommendations = _recommendations(level, key[0], rule_hits)
    return assessment


def build_explanation(
    score: int,
    level: RiskLevel,
    confidence: str,
    rule_hits: list[RuleHit],
) -> str:
    if not rule_hits:
        return (
            f"Skor {score}/100 ({level}) dengan confidence {confidence}. "
            "Belum ada rule risiko utama yang aktif pada data dummy saat ini."
        )
    ids = ", ".join(hit.rule_id for hit in rule_hits)
    return (
        f"Skor {score}/100 ({level}) dengan confidence {confidence}. "
        f"Entitas terindikasi perlu perhatian karena rule aktif: {ids}. "
        "Hasil ini adalah rekomendasi analitik dan tetap perlu human verification."
    )


def score_path(graph: InMemoryGraph, path: EvidencePath | None) -> int:
    if not path or not path.nodes:
        return 0
    node_scores = [
        int((graph.get_node((node.type, node.id)) or {}).get("riskScore") or 0)
        for node in path.nodes
    ]
    rel_bonus = sum(
        min(10, int(float((graph.get_relationship(rel_id) or {}).get("weight") or 1) * 5))
        for rel_id in path.relationships
    )
    blacklist_bonus = 20 if any(node.type == "BlacklistEntity" for node in path.nodes) else 0
    return min(100, max(node_scores or [0]) + rel_bonus + blacklist_bonus)


def should_create_blacklist_candidate(
    graph: InMemoryGraph,
    key: NodeKey,
    assessment: RiskAssessment,
    evidence_path: EvidencePath | None = None,
) -> BlacklistCandidateDraft | None:
    if key[0] not in BLACKLIST_CANDIDATE_TYPES:
        return None
    rule_ids = [hit.rule_id for hit in assessment.rule_hits]
    qualifies = assessment.level in {"high", "critical"} and (
        assessment.score >= 75 or bool({"R-005", "R-011", "R-012", "R-013"} & set(rule_ids))
    )
    if not qualifies:
        return None
    path = evidence_path or bfs_evidence_path(graph, key, max_depth=3)
    return BlacklistCandidateDraft(
        subject=node_ref_from_key(key),
        candidate_reason=(
            f"Entitas terindikasi {assessment.level} dengan skor {assessment.score}/100; "
            "otomatis menjadi kandidat review, bukan blacklist final."
        ),
        rule_ids=rule_ids,
        evidence_path=path,
    )


def apply_assessment_to_node(node: dict[str, Any], assessment: RiskAssessment) -> dict[str, Any]:
    updated = dict(node)
    updated["riskScore"] = assessment.score
    updated["riskLevel"] = assessment.level
    updated["confidence"] = assessment.confidence
    if assessment.level in {"high", "critical"}:
        updated["verificationStatus"] = "needs_review"
    return updated

