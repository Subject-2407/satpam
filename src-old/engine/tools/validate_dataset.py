"""Lightweight validator for the SATPAM week-1 dummy dataset.

This script intentionally avoids external dependencies. It checks the contract
that matters before week-2 implementation starts: basic structure, unique node
IDs, relationship references, and dummy-data guardrails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ENGINE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ENGINE_ROOT / "data" / "dummy_dataset_week1.json"

NODE_SECTIONS: dict[str, str] = {
    "reports": "Report",
    "victims": "Victim",
    "urls": "URL",
    "domains": "Domain",
    "linkShorteners": "LinkShortener",
    "socialMediaAccounts": "SocialMediaAccount",
    "phoneNumbers": "PhoneNumber",
    "bankAccounts": "BankAccount",
    "eWallets": "EWallet",
    "qrisMerchants": "QRISMerchant",
    "apks": "APK",
    "keywords": "Keyword",
    "transactions": "Transaction",
    "trafficEvents": "TrafficEvent",
    "crawlerFindings": "CrawlerFinding",
    "blacklistEntities": "BlacklistEntity",
    "blacklistCandidates": "BlacklistCandidate",
    "blacklistDecisions": "BlacklistDecision",
    "clusters": "Cluster",
    "evidences": "Evidence",
    "riskAssessments": "RiskAssessment",
    "verificationCases": "VerificationCase",
    "recommendations": "Recommendation",
    "users": "User",
    "auditLogs": "AuditLog",
}

SAFE_DOMAIN_SUFFIXES = (".test", ".example")
FORBIDDEN_PHRASES = (
    "terbukti pelaku",
    "pelaku terbukti",
    "confirmed perpetrator",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def get_hostname(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    return (parsed.hostname or "").lower()


def is_safe_domain(domain: str) -> bool:
    lowered = domain.lower()
    return lowered.endswith(SAFE_DOMAIN_SUFFIXES)


def collect_nodes(dataset: dict[str, Any], errors: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    nodes = dataset.get("nodes")
    if not isinstance(nodes, dict):
        fail(errors, "Missing or invalid nodes object.")
        return {}

    index: dict[tuple[str, str], dict[str, Any]] = {}
    global_ids: set[str] = set()

    for section, expected_type in NODE_SECTIONS.items():
        values = nodes.get(section)
        if not isinstance(values, list):
            fail(errors, f"Missing node section: {section}.")
            continue

        for item in values:
            if not isinstance(item, dict):
                fail(errors, f"Node in {section} is not an object.")
                continue

            node_id = item.get("id")
            node_type = item.get("type")
            if not node_id or not isinstance(node_id, str):
                fail(errors, f"Node in {section} has missing id.")
                continue

            if node_id in global_ids:
                fail(errors, f"Duplicate node id: {node_id}.")
            global_ids.add(node_id)

            if node_type != expected_type:
                fail(errors, f"Node {node_id} has type {node_type}, expected {expected_type}.")

            index[(expected_type, node_id)] = item

    return index


def validate_metadata(dataset: dict[str, Any], errors: list[str]) -> None:
    metadata = dataset.get("metadata")
    if not isinstance(metadata, dict):
        fail(errors, "Missing metadata object.")
        return

    if metadata.get("scope") != "week_1_foundation":
        fail(errors, "metadata.scope must be week_1_foundation.")

    if metadata.get("simulationOnly") is not True:
        fail(errors, "metadata.simulationOnly must be true.")

    policies = set(metadata.get("dataPolicy", []))
    required = {
        "dummy_data_only",
        "safe_test_domains_only",
        "masked_payment_identifiers",
        "simulation_traffic_and_crawler_only",
        "human_verification_required",
    }
    missing = sorted(required - policies)
    if missing:
        fail(errors, f"metadata.dataPolicy missing: {', '.join(missing)}.")


def validate_guardrails(nodes: dict[tuple[str, str], dict[str, Any]], errors: list[str]) -> None:
    for (node_type, node_id), node in nodes.items():
        text_fields = [
            str(value).lower()
            for value in node.values()
            if isinstance(value, str)
        ]
        for phrase in FORBIDDEN_PHRASES:
            if any(phrase in value for value in text_fields):
                fail(errors, f"Node {node_id} contains forbidden phrase: {phrase}.")

        if node_type == "Domain":
            domain = str(node.get("domainName", ""))
            if not is_safe_domain(domain):
                fail(errors, f"Domain {node_id} must end with .test or .example: {domain}.")

        if node_type == "URL":
            raw_url = str(node.get("rawUrl", ""))
            normalized_url = str(node.get("normalizedUrl", ""))
            hostnames = [get_hostname(raw_url), get_hostname(normalized_url)]
            for hostname in hostnames:
                if not hostname or not is_safe_domain(hostname):
                    fail(errors, f"URL {node_id} must use .test or .example: {raw_url}.")

        if node_type == "PhoneNumber":
            number = str(node.get("normalizedNumber", ""))
            if "0000" not in number:
                fail(errors, f"PhoneNumber {node_id} must use dummy 0000 pattern.")

        if node_type == "BankAccount":
            masked = str(node.get("maskedAccountNumber", ""))
            if "****" not in masked:
                fail(errors, f"BankAccount {node_id} must be masked with ****.")

        if node_type == "EWallet":
            masked = str(node.get("maskedWalletId", ""))
            if "****" not in masked:
                fail(errors, f"EWallet {node_id} must be masked with ****.")

        if node_type in {"TrafficEvent", "CrawlerFinding"} and node.get("simulationOnly") is not True:
            fail(errors, f"{node_type} {node_id} must set simulationOnly true.")


def validate_relationships(
    dataset: dict[str, Any],
    nodes: dict[tuple[str, str], dict[str, Any]],
    errors: list[str],
) -> int:
    relationships = dataset.get("relationships")
    if not isinstance(relationships, list):
        fail(errors, "Missing or invalid relationships array.")
        return 0

    relationship_ids: set[str] = set()

    for relationship in relationships:
        if not isinstance(relationship, dict):
            fail(errors, "Relationship item is not an object.")
            continue

        rel_id = relationship.get("id")
        if not rel_id or not isinstance(rel_id, str):
            fail(errors, "Relationship missing id.")
            continue

        if rel_id in relationship_ids:
            fail(errors, f"Duplicate relationship id: {rel_id}.")
        relationship_ids.add(rel_id)

        for side in ("from", "to"):
            endpoint = relationship.get(side)
            if not isinstance(endpoint, dict):
                fail(errors, f"Relationship {rel_id} missing {side} endpoint.")
                continue

            key = (endpoint.get("type"), endpoint.get("id"))
            if key not in nodes:
                fail(errors, f"Relationship {rel_id} references missing {side} node: {key}.")

        evidence_id = relationship.get("evidenceId")
        if evidence_id and not any(node_id == evidence_id for _, node_id in nodes):
            fail(errors, f"Relationship {rel_id} references missing evidenceId: {evidence_id}.")

    return len(relationship_ids)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SATPAM week-1 dummy dataset.")
    parser.add_argument(
        "dataset",
        nargs="?",
        default=str(DEFAULT_DATASET),
        help="Path to dataset JSON file.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    errors: list[str] = []

    try:
        dataset = load_json(dataset_path)
    except OSError as exc:
        print(f"Failed to read dataset: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 1

    validate_metadata(dataset, errors)
    nodes = collect_nodes(dataset, errors)
    validate_guardrails(nodes, errors)
    relationship_count = validate_relationships(dataset, nodes, errors)

    if errors:
        print("SATPAM dataset validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    node_count = len(nodes)
    scenario_count = len(dataset.get("demoScenarios", []))
    print("SATPAM dataset validation passed.")
    print(f"Dataset: {dataset_path}")
    print(f"Nodes: {node_count}")
    print(f"Relationships: {relationship_count}")
    print(f"Demo scenarios: {scenario_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
