from app.services.ai_engine.extractor import extract_report_entities


def test_extract_report_entities_detects_core_entities():
    result = extract_report_entities(
        "Promo bonus slot diarahkan ke https://bonus-alpha.test/promo, "
        "kontak WA +62-812-0000-1101 dan transfer ke 1234****9001. "
        "APK id.demo.danacepat meminta izin kontak dan SMS.",
        category_hint="judol",
        bank_accounts=[
            {
                "bankName": "Bank Dummy",
                "accountAlias": "Rekening Promo",
                "maskedAccountNumber": "1234****9001",
            }
        ],
        apps=[{"appName": "DanaCepat Demo", "packageName": "id.demo.danacepat"}],
    )

    assert result.is_valid
    entity_types = {entity.entity_type for entity in result.entities}
    assert {"URL", "Domain", "PhoneNumber", "BankAccount", "APK", "Keyword"} <= entity_types
    assert any(entity.properties["domainName"] == "bonus-alpha.test" for entity in result.by_type("Domain"))
    assert any(entity.properties["normalizedNumber"] == "+6281200001101" for entity in result.by_type("PhoneNumber"))
    assert any("READ_CONTACTS" in entity.properties["requestedPermissions"] for entity in result.by_type("APK"))


def test_extractor_rejects_non_dummy_domain():
    result = extract_report_entities(
        "Contoh link tidak aman untuk prototype: https://example-real.com/promo",
        category_hint="judol",
    )

    assert not result.is_valid
    assert result.guardrail_violations

