"""
Integration test untuk endpoint backend SATPAM (MVP + medium priority).

Memakai FakeRepository in-memory (lihat conftest.py) sehingga tidak butuh Neo4j.
Fokus: happy path, kontrol akses (401/403), validasi (422), dan not found (404).
"""

import pytest

from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Reports listing
# ---------------------------------------------------------------------------


async def test_list_reports_requires_auth(fake_repo_client):
    resp = await fake_repo_client.get("/api/reports")
    assert resp.status_code == 401


async def test_list_reports_forbidden_for_reporter(fake_repo_client):
    resp = await fake_repo_client.get("/api/reports", headers=auth_headers("public_reporter"))
    assert resp.status_code == 403


async def test_list_reports_happy_path(fake_repo_client, fake_store):
    fake_store[("Report", "report-1")] = {
        "id": "report-1",
        "type": "Report",
        "status": "needs_review",
        "description": "laporan judol dummy",
        "createdAt": "2026-06-18T00:00:00Z",
    }
    resp = await fake_repo_client.get(
        "/api/reports", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "report-1"


async def test_list_reports_status_filter(fake_repo_client, fake_store):
    fake_store[("Report", "r1")] = {"id": "r1", "type": "Report", "status": "new", "createdAt": "a"}
    fake_store[("Report", "r2")] = {"id": "r2", "type": "Report", "status": "closed", "createdAt": "b"}
    resp = await fake_repo_client.get(
        "/api/reports?status=closed", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "r2"


async def test_get_report_detail_404(fake_repo_client):
    resp = await fake_repo_client.get(
        "/api/reports/nope", headers=auth_headers("analyst")
    )
    assert resp.status_code == 404


async def test_get_report_detail_happy(fake_repo_client, fake_store):
    fake_store[("Report", "report-9")] = {"id": "report-9", "type": "Report", "status": "new"}
    resp = await fake_repo_client.get(
        "/api/reports/report-9", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    assert resp.json()["report"]["id"] == "report-9"


# ---------------------------------------------------------------------------
# Entity search
# ---------------------------------------------------------------------------


async def test_search_entities_happy(fake_repo_client, fake_store):
    fake_store[("Domain", "dom-1")] = {
        "id": "dom-1",
        "type": "Domain",
        "domainName": "judolxyz",
        "riskLevel": "high",
        "riskScore": 70,
        "verificationStatus": "needs_review",
    }
    fake_store[("URL", "url-1")] = {
        "id": "url-1",
        "type": "URL",
        "riskLevel": "low",
        "riskScore": 10,
    }
    resp = await fake_repo_client.get(
        "/api/entities?risk_level=high", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "dom-1"


async def test_search_entities_text(fake_repo_client, fake_store):
    fake_store[("Domain", "dom-1")] = {"id": "dom-1", "type": "Domain", "domainName": "judolxyz", "riskScore": 5}
    resp = await fake_repo_client.get(
        "/api/entities?search=judol", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_search_entities_unauthorized(fake_repo_client):
    resp = await fake_repo_client.get("/api/entities")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


async def test_list_alerts_happy(fake_repo_client, fake_store):
    fake_store[("Alert", "alert-1")] = {
        "id": "alert-1",
        "type": "Alert",
        "alertType": "Traffic Spike Alert",
        "priority": "high",
        "status": "new",
        "createdAt": "2026-06-18T00:00:00Z",
    }
    resp = await fake_repo_client.get("/api/alerts", headers=auth_headers("analyst"))
    assert resp.status_code == 200
    data = resp.json()
    assert any(a["id"] == "alert-1" for a in data["items"])


async def test_patch_alert_status_invalid(fake_repo_client, fake_store):
    fake_store[("Alert", "alert-1")] = {"id": "alert-1", "type": "Alert", "status": "new"}
    resp = await fake_repo_client.patch(
        "/api/alerts/alert-1/status",
        json={"status": "bogus"},
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 422


async def test_patch_alert_status_404(fake_repo_client):
    resp = await fake_repo_client.patch(
        "/api/alerts/missing/status",
        json={"status": "reviewed"},
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 404


async def test_patch_alert_status_happy(fake_repo_client, fake_store):
    fake_store[("Alert", "alert-1")] = {"id": "alert-1", "type": "Alert", "status": "new"}
    resp = await fake_repo_client.patch(
        "/api/alerts/alert-1/status",
        json={"status": "reviewed", "note": "sudah dicek"},
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 200
    assert resp.json()["alert"]["status"] == "reviewed"
    # audit log tercatat
    assert any(label == "AuditLog" for (label, _) in fake_store)


# ---------------------------------------------------------------------------
# Verification cases
# ---------------------------------------------------------------------------


async def test_list_verification_cases(fake_repo_client, fake_store):
    fake_store[("VerificationCase", "case-1")] = {
        "id": "case-1",
        "type": "VerificationCase",
        "status": "needs_review",
        "createdAt": "x",
    }
    resp = await fake_repo_client.get(
        "/api/verification-cases", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_patch_verification_case_happy(fake_repo_client, fake_store):
    fake_store[("VerificationCase", "case-1")] = {
        "id": "case-1",
        "type": "VerificationCase",
        "status": "needs_review",
    }
    resp = await fake_repo_client.patch(
        "/api/verification-cases/case-1",
        json={"status": "verified_risk", "decisionNote": "indikasi kuat"},
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 200
    assert resp.json()["case"]["status"] == "verified_risk"


async def test_patch_verification_closed_requires_supervisor(fake_repo_client, fake_store):
    fake_store[("VerificationCase", "case-1")] = {
        "id": "case-1",
        "type": "VerificationCase",
        "status": "needs_review",
    }
    resp = await fake_repo_client.patch(
        "/api/verification-cases/case-1",
        json={"status": "closed"},
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 403

    resp2 = await fake_repo_client.patch(
        "/api/verification-cases/case-1",
        json={"status": "closed"},
        headers=auth_headers("supervisor"),
    )
    assert resp2.status_code == 200


async def test_patch_verification_invalid_status(fake_repo_client, fake_store):
    fake_store[("VerificationCase", "case-1")] = {"id": "case-1", "type": "VerificationCase", "status": "new"}
    resp = await fake_repo_client.patch(
        "/api/verification-cases/case-1",
        json={"status": "bogus"},
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Blacklist candidates
# ---------------------------------------------------------------------------


async def test_list_blacklist_candidates(fake_repo_client, fake_store):
    fake_store[("BlacklistCandidate", "cand-1")] = {
        "id": "cand-1",
        "type": "BlacklistCandidate",
        "entityType": "Domain",
        "status": "blacklist_candidate",
        "createdAt": "x",
    }
    resp = await fake_repo_client.get(
        "/api/blacklist-candidates", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_confirmed_blacklist_forbidden_for_analyst(fake_repo_client, fake_store):
    fake_store[("BlacklistCandidate", "cand-1")] = {
        "id": "cand-1",
        "type": "BlacklistCandidate",
        "status": "blacklist_candidate",
    }
    resp = await fake_repo_client.patch(
        "/api/blacklist-candidates/cand-1/decision",
        json={"status": "confirmed_blacklist"},
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 403


async def test_confirmed_blacklist_allowed_for_supervisor(fake_repo_client, fake_store):
    fake_store[("BlacklistCandidate", "cand-1")] = {
        "id": "cand-1",
        "type": "BlacklistCandidate",
        "status": "blacklist_candidate",
        "verificationStatus": "needs_review",
    }
    resp = await fake_repo_client.patch(
        "/api/blacklist-candidates/cand-1/decision",
        json={"status": "confirmed_blacklist", "decisionNote": "disetujui"},
        headers=auth_headers("supervisor"),
    )
    assert resp.status_code == 200
    assert resp.json()["candidate"]["status"] == "confirmed_blacklist"


async def test_blacklist_candidate_404(fake_repo_client):
    resp = await fake_repo_client.get(
        "/api/blacklist-candidates/missing", headers=auth_headers("analyst")
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Traffic & crawler intel
# ---------------------------------------------------------------------------


async def test_list_traffic_events(fake_repo_client, fake_store):
    fake_store[("TrafficEvent", "te-1")] = {
        "id": "te-1",
        "type": "TrafficEvent",
        "eventType": "SPIKE",
        "createdAt": "x",
    }
    resp = await fake_repo_client.get(
        "/api/traffic-events", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_import_traffic_events_admin_only(fake_repo_client):
    payload = {
        "items": [
            {
                "id": "te-1",
                "label": "Traffic te-1",
                "source": "simulation",
                "createdAt": "2026-06-18T00:00:00Z",
                "eventType": "spike",
                "timestamp": "2026-06-18T00:00:00Z",
                "sourceAlias": "src-a",
                "destinationDomain": "dummy.example",
                "requestCount": 99,
                "simulationOnly": True,
            }
        ]
    }
    resp = await fake_repo_client.post(
        "/api/traffic-events/import", json=payload, headers=auth_headers("analyst")
    )
    assert resp.status_code == 403

    resp2 = await fake_repo_client.post(
        "/api/traffic-events/import", json=payload, headers=auth_headers("admin")
    )
    assert resp2.status_code == 201
    assert resp2.json()["merged"] == 1


async def test_import_traffic_rejects_non_simulation(fake_repo_client):
    payload = {
        "items": [
            {
                "id": "te-2",
                "label": "Traffic te-2",
                "source": "simulation",
                "createdAt": "2026-06-18T00:00:00Z",
                "eventType": "spike",
                "timestamp": "2026-06-18T00:00:00Z",
                "sourceAlias": "src-a",
                "destinationDomain": "dummy.example",
                "requestCount": 1,
                "simulationOnly": False,
            }
        ]
    }
    resp = await fake_repo_client.post(
        "/api/traffic-events/import", json=payload, headers=auth_headers("admin")
    )
    assert resp.status_code == 422


async def test_import_crawler_findings_admin(fake_repo_client):
    payload = {
        "items": [
            {
                "id": "cf-1",
                "label": "Crawler cf-1",
                "source": "simulation",
                "createdAt": "2026-06-18T00:00:00Z",
                "findingType": "redirect",
                "sourceUrl": "hxxp://dummy.example/a",
                "contentSummary": "promosi judol dummy",
                "matchedKeywords": ["slot", "gacor"],
                "capturedAt": "2026-06-18T00:00:00Z",
                "simulationOnly": True,
            }
        ]
    }
    resp = await fake_repo_client.post(
        "/api/crawler-findings/import", json=payload, headers=auth_headers("admin")
    )
    assert resp.status_code == 201
    assert resp.json()["merged"] == 1


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


async def test_export_analysis_404(fake_repo_client):
    resp = await fake_repo_client.get(
        "/api/export/analysis/Domain/missing", headers=auth_headers("analyst")
    )
    assert resp.status_code == 404


async def test_export_analysis_json(fake_repo_client, fake_store):
    fake_store[("Domain", "dom-1")] = {
        "id": "dom-1",
        "type": "Domain",
        "domainName": "dummy.example",
        "createdAt": "x",
    }
    resp = await fake_repo_client.get(
        "/api/export/analysis/Domain/dom-1?format=json", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulationOnly"] is True
    assert data["entity"]["id"] == "dom-1"


async def test_export_analysis_markdown(fake_repo_client, fake_store):
    fake_store[("Domain", "dom-1")] = {
        "id": "dom-1",
        "type": "Domain",
        "domainName": "dummy.example",
        "createdAt": "x",
    }
    resp = await fake_repo_client.get(
        "/api/export/analysis/Domain/dom-1?format=markdown",
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 200
    assert "Laporan Analisis Risiko" in resp.text


# ---------------------------------------------------------------------------
# Admin: reset & audit logs
# ---------------------------------------------------------------------------


async def test_reset_dataset_admin_only(fake_repo_client, fake_store):
    fake_store[("Report", "r1")] = {"id": "r1", "type": "Report"}
    resp = await fake_repo_client.delete(
        "/api/admin/reset-dataset", headers=auth_headers("analyst")
    )
    assert resp.status_code == 403

    resp2 = await fake_repo_client.delete(
        "/api/admin/reset-dataset", headers=auth_headers("admin")
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "success"


async def test_audit_logs_supervisor(fake_repo_client, fake_store):
    fake_store[("AuditLog", "audit-1")] = {
        "id": "audit-1",
        "type": "AuditLog",
        "action": "UPDATE_ALERT_STATUS",
        "timestamp": "2026-06-18T00:00:00Z",
    }
    resp = await fake_repo_client.get(
        "/api/audit-logs", headers=auth_headers("supervisor")
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_audit_logs_forbidden_for_analyst(fake_repo_client):
    resp = await fake_repo_client.get(
        "/api/audit-logs", headers=auth_headers("analyst")
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------


async def test_dashboard_summary_requires_auth(fake_repo_client):
    resp = await fake_repo_client.get("/api/dashboard/summary")
    assert resp.status_code == 401


async def test_dashboard_summary_forbidden_for_reporter(fake_repo_client):
    resp = await fake_repo_client.get(
        "/api/dashboard/summary", headers=auth_headers("public_reporter")
    )
    assert resp.status_code == 403


async def test_dashboard_summary_happy(fake_repo_client, fake_store):
    fake_store[("Report", "r1")] = {"id": "r1", "type": "Report", "status": "needs_review"}
    fake_store[("Domain", "dom-1")] = {
        "id": "dom-1",
        "type": "Domain",
        "riskLevel": "critical",
        "riskScore": 90,
    }
    fake_store[("URL", "url-1")] = {
        "id": "url-1",
        "type": "URL",
        "riskLevel": "low",
        "riskScore": 12,
    }
    fake_store[("Alert", "alert-1")] = {"id": "alert-1", "type": "Alert", "status": "new"}
    fake_store[("VerificationCase", "case-1")] = {
        "id": "case-1",
        "type": "VerificationCase",
        "status": "needs_review",
    }

    resp = await fake_repo_client.get(
        "/api/dashboard/summary", headers=auth_headers("analyst")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulationOnly"] is True
    assert data["totals"]["reports"] == 1
    assert data["totals"]["entities"] == 2
    assert data["totals"]["alerts"] == 1
    assert data["totals"]["verificationCases"] == 1
    assert data["entitiesByRiskLevel"]["critical"] == 1
    assert data["entitiesByRiskLevel"]["low"] == 1
    # entitas berisiko tertinggi terurut menurun (FR-067)
    assert data["topRiskEntities"][0]["id"] == "dom-1"


# ---------------------------------------------------------------------------
# Rules update
# ---------------------------------------------------------------------------


async def test_patch_rule_weight_admin(client_no_neo4j):
    # driver None → endpoint tetap update bobot in-memory, lewati audit
    resp = await client_no_neo4j.patch(
        "/api/rules/R-001",
        json={"weight": 42},
        headers=auth_headers("admin"),
    )
    assert resp.status_code == 200
    assert resp.json()["weight"] == 42


async def test_patch_rule_weight_forbidden(client_no_neo4j):
    resp = await client_no_neo4j.patch(
        "/api/rules/R-001",
        json={"weight": 10},
        headers=auth_headers("analyst"),
    )
    assert resp.status_code == 403


async def test_patch_rule_weight_404(client_no_neo4j):
    resp = await client_no_neo4j.patch(
        "/api/rules/R-999",
        json={"weight": 10},
        headers=auth_headers("admin"),
    )
    assert resp.status_code == 404
