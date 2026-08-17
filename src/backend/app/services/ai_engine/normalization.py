from __future__ import annotations

import hashlib
import re
from urllib.parse import quote, unquote, urlparse, urlunparse


SAFE_DOMAIN_SUFFIXES = (".test", ".example")


def stable_hash(value: str, length: int = 10) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def safe_slug(value: str, max_length: int = 48) -> str:
    value = unquote(str(value)).lower().strip()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        value = "unknown"
    return value[:max_length].strip("-") or "unknown"


def stable_entity_id(prefix: str, value: str) -> str:
    slug = safe_slug(value)
    digest = stable_hash(str(value).lower().strip(), 8)
    if len(slug) <= 34:
        return f"{prefix}-{slug}"
    return f"{prefix}-{slug[:34]}-{digest}"


def stable_relationship_id(rel_type: str, from_type: str, from_id: str, to_type: str, to_id: str) -> str:
    raw = f"{rel_type}|{from_type}:{from_id}|{to_type}:{to_id}"
    return f"rel-{safe_slug(rel_type, 18)}-{stable_hash(raw, 12)}"


def normalize_domain(value: str) -> str:
    raw = str(value).strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        parsed = urlparse(raw)
        raw = parsed.hostname or raw
    raw = raw.split("/")[0].split("?")[0].split("#")[0]
    raw = raw.strip(" .")
    if raw.startswith("www."):
        raw = raw[4:]
    return raw


def is_safe_demo_domain(domain: str) -> bool:
    normalized = normalize_domain(domain)
    return bool(normalized) and normalized.endswith(SAFE_DOMAIN_SUFFIXES)


def normalize_url(value: str) -> str:
    raw = str(value).strip().strip(".,;)]}\"'")
    if not raw:
        return ""
    if not re.match(r"^[a-z][a-z0-9+.-]*://", raw, flags=re.IGNORECASE):
        raw = f"https://{raw}"

    parsed = urlparse(raw)
    scheme = (parsed.scheme or "https").lower()
    hostname = (parsed.hostname or "").lower()
    path = quote(unquote(parsed.path or ""), safe="/:@")
    if path != "/":
        path = path.rstrip("/")
    query = parsed.query
    return urlunparse((scheme, hostname, path, "", query, ""))


def domain_from_url(value: str) -> str:
    normalized = normalize_url(value)
    return normalize_domain(urlparse(normalized).hostname or "")


def normalize_phone(value: str) -> str:
    raw = str(value).strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    elif digits.startswith("620"):
        digits = "62" + digits[3:]
    if digits.startswith("62"):
        return f"+{digits}"
    return f"+{digits}"


def mask_identifier(value: str, left: int = 4, right: int = 4) -> str:
    raw = re.sub(r"\s+", "", str(value).strip())
    if "****" in raw:
        return raw
    chars = re.sub(r"\D", "", raw)
    if len(chars) <= left + right:
        return raw
    return f"{chars[:left]}****{chars[-right:]}"


def normalize_masked_account(value: str) -> str:
    return mask_identifier(value, left=4, right=4)


def normalize_package_name(value: str) -> str:
    return str(value).strip().lower()


def display_label_from_url(value: str) -> str:
    normalized = normalize_url(value)
    parsed = urlparse(normalized)
    label = parsed.hostname or normalized
    if parsed.path and parsed.path != "/":
        label += parsed.path
    return label

