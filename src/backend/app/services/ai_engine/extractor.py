from __future__ import annotations

import re
from typing import Any

from app.services.ai_engine.models import ExtractedEntity, ExtractionResult
from app.services.ai_engine.normalization import (
    display_label_from_url,
    domain_from_url,
    is_safe_demo_domain,
    normalize_domain,
    normalize_masked_account,
    normalize_package_name,
    normalize_phone,
    normalize_url,
    stable_entity_id,
)


URL_RE = re.compile(r"https?://[^\s<>()\"']+", re.IGNORECASE)
SAFE_DOMAIN_RE = re.compile(
    r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)*\.(?:test|example)(?:/[^\s<>()\"']*)?",
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"(?:\+?62|0|62)[\s.-]?8(?:[\s.-]?\d){8,12}")
MASKED_ACCOUNT_RE = re.compile(r"\b\d{3,6}\*{4}\d{3,6}\b")
PACKAGE_RE = re.compile(r"\b(?:[a-z][a-z0-9_]*\.){2,}[a-z][a-z0-9_]*\b", re.IGNORECASE)
SOCIAL_HANDLE_RE = re.compile(r"(?<!\w)@([a-zA-Z0-9_]{3,32})")


KEYWORD_CATALOG: tuple[dict[str, Any], ...] = (
    {"keyword": "bonus slot", "category": "judol", "weight": 20},
    {"keyword": "slot gacor", "category": "judol", "weight": 25},
    {"keyword": "maxwin", "category": "judol", "weight": 20},
    {"keyword": "depo kecil", "category": "judol", "weight": 15},
    {"keyword": "cair cepat", "category": "pinjol_illegal", "weight": 20},
    {"keyword": "pinjaman cepat cair", "category": "pinjol_illegal", "weight": 25},
    {"keyword": "tanpa ojk", "category": "pinjol_illegal", "weight": 30},
    {"keyword": "tanpa bi checking", "category": "pinjol_illegal", "weight": 20},
    {"keyword": "sebar data", "category": "pinjol_illegal", "weight": 20},
    {"keyword": "izin kontak", "category": "apk_permission", "weight": 20},
    {"keyword": "permission kontak", "category": "apk_permission", "weight": 20},
    {"keyword": "akses sms", "category": "apk_permission", "weight": 20},
    {"keyword": "izin sms", "category": "apk_permission", "weight": 20},
    {"keyword": "akses lokasi", "category": "apk_permission", "weight": 15},
    {"keyword": "transfer admin", "category": "payment", "weight": 15},
    {"keyword": "rekening dummy", "category": "payment", "weight": 10},
    {"keyword": "edukasi finansial", "category": "benign", "weight": 0},
)


def _append_unique(entities: list[ExtractedEntity], entity: ExtractedEntity) -> None:
    key = (entity.entity_type, entity.normalized_value)
    if any((item.entity_type, item.normalized_value) == key for item in entities):
        return
    entities.append(entity)


def _infer_domain_category(domain: str, text: str, category_hint: str | None) -> str:
    lowered = f"{domain} {text} {category_hint or ''}".lower()
    if any(token in lowered for token in ("slot", "bonus", "maxwin", "gacor")):
        return "judol_promo"
    if any(token in lowered for token in ("pinjol", "cair", "pinjam", "dana")):
        return "pinjol_illegal"
    if category_hint in {"cross_ecosystem", "traffic_crawler", "payment_flow"}:
        return category_hint
    if category_hint == "benign":
        return "benign_education"
    return "unknown"


def _keyword_node(keyword: str, category: str, weight: int, source: str) -> ExtractedEntity:
    node_id = stable_entity_id("keyword", keyword)
    return ExtractedEntity(
        entity_type="Keyword",
        value=keyword,
        normalized_value=keyword.lower(),
        confidence="medium",
        properties={
            "id": node_id,
            "type": "Keyword",
            "label": keyword,
            "source": source,
            "keyword": keyword,
            "category": category,
            "weight": weight,
        },
    )


def _permission_keywords_from_text(text: str) -> list[str]:
    lowered = text.lower()
    permissions: list[str] = []
    if "kontak" in lowered or "contact" in lowered:
        permissions.append("READ_CONTACTS")
    if "sms" in lowered:
        permissions.append("READ_SMS")
    if "lokasi" in lowered or "location" in lowered:
        permissions.append("ACCESS_FINE_LOCATION")
    return permissions


def extract_report_entities(
    description: str,
    *,
    source: str = "dummy_user_report",
    category_hint: str | None = None,
    urls: list[str] | None = None,
    phone_numbers: list[str] | None = None,
    bank_accounts: list[dict[str, Any]] | None = None,
    apps: list[dict[str, Any]] | None = None,
) -> ExtractionResult:
    """Extract entities from a dummy SATPAM report.

    Guardrail: URL/domain entities are accepted only for .test or .example
    domains so the prototype does not store real suspicious links.
    """

    text = description or ""
    result = ExtractionResult()
    entities: list[ExtractedEntity] = []

    raw_urls = set(urls or [])
    raw_urls.update(URL_RE.findall(text))
    for domain_match in SAFE_DOMAIN_RE.findall(text):
        if not domain_match.lower().startswith(("http://", "https://")):
            raw_urls.add(f"https://{domain_match}")

    for raw_url in sorted(raw_urls):
        normalized = normalize_url(raw_url)
        domain = domain_from_url(normalized)
        if not is_safe_demo_domain(domain):
            result.guardrail_violations.append(
                f"URL/domain harus dummy .test atau .example: {raw_url}"
            )
            continue

        url_id = stable_entity_id("url", normalized)
        _append_unique(
            entities,
            ExtractedEntity(
                entity_type="URL",
                value=raw_url,
                normalized_value=normalized,
                confidence="high",
                properties={
                    "id": url_id,
                    "type": "URL",
                    "label": display_label_from_url(normalized),
                    "source": source,
                    "rawUrl": raw_url,
                    "normalizedUrl": normalized,
                    "domain": domain,
                },
            ),
        )

        domain_id = stable_entity_id("domain", domain)
        _append_unique(
            entities,
            ExtractedEntity(
                entity_type="Domain",
                value=domain,
                normalized_value=domain,
                confidence="high",
                properties={
                    "id": domain_id,
                    "type": "Domain",
                    "label": domain,
                    "source": source,
                    "domainName": domain,
                    "category": _infer_domain_category(domain, text, category_hint),
                },
            ),
        )

    raw_phones = set(phone_numbers or [])
    raw_phones.update(match.group(0) for match in PHONE_RE.finditer(text))
    for raw_phone in sorted(raw_phones):
        normalized = normalize_phone(raw_phone)
        if not normalized or len(re.sub(r"\D", "", normalized)) < 10:
            continue
        phone_id = stable_entity_id("phone", normalized)
        _append_unique(
            entities,
            ExtractedEntity(
                entity_type="PhoneNumber",
                value=raw_phone,
                normalized_value=normalized,
                confidence="medium",
                properties={
                    "id": phone_id,
                    "type": "PhoneNumber",
                    "label": normalized,
                    "source": source,
                    "normalizedNumber": normalized,
                    "countryCode": "+62" if normalized.startswith("+62") else "",
                    "reportCount": 1,
                },
            ),
        )

    explicit_accounts = bank_accounts or []
    for account in explicit_accounts:
        masked = normalize_masked_account(str(account.get("maskedAccountNumber", "")))
        if not masked or "****" not in masked:
            result.guardrail_violations.append("Rekening harus disamarkan dengan ****.")
            continue
        account_id = stable_entity_id("bank", masked)
        _append_unique(
            entities,
            ExtractedEntity(
                entity_type="BankAccount",
                value=masked,
                normalized_value=masked,
                confidence="medium",
                properties={
                    "id": account_id,
                    "type": "BankAccount",
                    "label": f"{account.get('bankName', 'Bank Dummy')} {masked}",
                    "source": source,
                    "bankName": account.get("bankName", "Bank Dummy"),
                    "accountAlias": account.get("accountAlias", "Rekening Dummy"),
                    "maskedAccountNumber": masked,
                },
            ),
        )

    for match in MASKED_ACCOUNT_RE.finditer(text):
        masked = normalize_masked_account(match.group(0))
        account_id = stable_entity_id("bank", masked)
        _append_unique(
            entities,
            ExtractedEntity(
                entity_type="BankAccount",
                value=masked,
                normalized_value=masked,
                confidence="medium",
                properties={
                    "id": account_id,
                    "type": "BankAccount",
                    "label": f"Bank Dummy {masked}",
                    "source": source,
                    "bankName": "Bank Dummy",
                    "accountAlias": "Rekening Dummy",
                    "maskedAccountNumber": masked,
                },
            ),
        )

    permission_keywords = _permission_keywords_from_text(text)
    explicit_apps = apps or []
    package_names = {normalize_package_name(str(item.get("packageName", ""))) for item in explicit_apps}
    package_names.update(
        normalize_package_name(match.group(0))
        for match in PACKAGE_RE.finditer(text)
        if not normalize_domain(match.group(0)).endswith((".test", ".example"))
    )
    app_name_by_package = {
        normalize_package_name(str(item.get("packageName", ""))): str(item.get("appName", "APK Dummy"))
        for item in explicit_apps
    }
    for package_name in sorted(item for item in package_names if item):
        apk_id = stable_entity_id("apk", package_name)
        app_name = app_name_by_package.get(package_name, "APK Dummy")
        _append_unique(
            entities,
            ExtractedEntity(
                entity_type="APK",
                value=package_name,
                normalized_value=package_name,
                confidence="medium",
                properties={
                    "id": apk_id,
                    "type": "APK",
                    "label": app_name,
                    "source": source,
                    "appName": app_name,
                    "packageName": package_name,
                    "requestedPermissions": permission_keywords,
                },
            ),
        )

    for handle in SOCIAL_HANDLE_RE.findall(text):
        username = handle.lower()
        social_id = stable_entity_id("social", username)
        _append_unique(
            entities,
            ExtractedEntity(
                entity_type="SocialMediaAccount",
                value=f"@{handle}",
                normalized_value=username,
                confidence="low",
                properties={
                    "id": social_id,
                    "type": "SocialMediaAccount",
                    "label": f"@{username}",
                    "source": source,
                    "platform": "DummySocial",
                    "username": username,
                    "profileUrl": f"https://social.example/{username}",
                },
            ),
        )

    lowered = text.lower()
    for item in KEYWORD_CATALOG:
        if item["keyword"] in lowered:
            _append_unique(
                entities,
                _keyword_node(item["keyword"], item["category"], item["weight"], source),
            )

    if category_hint == "judol" and not any(
        item.entity_type == "Keyword" and item.properties.get("category") == "judol"
        for item in entities
    ):
        _append_unique(entities, _keyword_node("indikasi judol", "judol", 10, source))
    if category_hint == "pinjol_illegal" and not any(
        item.entity_type == "Keyword" and item.properties.get("category") == "pinjol_illegal"
        for item in entities
    ):
        _append_unique(
            entities,
            _keyword_node("indikasi pinjol ilegal", "pinjol_illegal", 10, source),
        )

    result.entities = entities
    if not entities:
        result.warnings.append("Tidak ada entitas graph utama yang terdeteksi dari laporan.")
    return result

