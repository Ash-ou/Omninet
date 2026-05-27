"""Tests des routes UI statiques."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def _login(username: str = "admin", password: str = "admin") -> str:
    """Helper: login et retourne un token JWT."""
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_ui_index_returns_html() -> None:
    response = client.get("/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()


def test_ui_index_includes_security_headers() -> None:
    response = client.get("/ui")
    assert response.status_code == 200

    csp = response.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "no-referrer"
    assert (
        response.headers.get("permissions-policy")
        == "geolocation=(), camera=(), microphone=()"
    )


def test_ui_dashboard_contains_ui2_counters() -> None:
    """Le dashboard UI2 expose les compteurs attendus."""
    response = client.get("/ui")
    assert response.status_code == 200
    html = response.text

    assert 'id="refresh-dashboard"' in html
    assert 'id="count-alerts-new"' in html
    assert 'id="count-alerts-ack"' in html
    assert 'id="count-events-total"' in html
    assert 'id="count-endpoints-total"' in html


def test_ui_alerts_returns_html() -> None:
    response = client.get("/ui/alerts")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()


def test_ui_alerts_contains_filter_and_auto_refresh_controls() -> None:
    """La page alertes UI2 expose le filtre status et l'auto-refresh."""
    response = client.get("/ui/alerts")
    assert response.status_code == 200
    html = response.text

    assert 'id="alert-status-filter"' in html
    assert '<option value="new">' in html
    assert '<option value="acknowledged">' in html
    assert '<option value="resolved">' in html
    assert 'id="alerts-auto-refresh"' in html


def test_ui_events_returns_html() -> None:
    response = client.get("/ui/events")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()


def test_ui_endpoints_returns_html() -> None:
    response = client.get("/ui/endpoints")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()


def test_ui_settings_returns_html() -> None:
    response = client.get("/ui/settings")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()
    assert "Paramètres" in response.text


def test_ui_admin_users_returns_html() -> None:
    response = client.get("/ui/admin/users")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()


def test_ui_scans_returns_html() -> None:
    response = client.get("/ui/scans")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()


def test_ui_scans_contains_simulation_form_fields() -> None:
    """La page scans UI2 expose les champs du scan simulé."""
    response = client.get("/ui/scans")
    assert response.status_code == 200
    html = response.text

    assert 'id="scan-form"' in html
    assert 'id="scan-endpoint-id"' in html
    assert 'id="scan-target"' in html
    assert 'id="scan-type"' in html
    assert 'id="scan-severity"' in html
    assert 'id="scan-result"' in html


def test_ui_styles_asset_returns_css() -> None:
    response = client.get("/ui/assets/styles.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert len(response.text) > 0


def test_ui_javascript_asset_returns_js() -> None:
    response = client.get("/ui/assets/app.js")
    assert response.status_code == 200
    content_type = response.headers["content-type"]
    assert (
        "application/javascript" in content_type
        or "text/javascript" in content_type
    )
    assert len(response.text) > 0


def test_protected_endpoints_rejected_without_token() -> None:
    protected_calls = [
        ("get", "/alerts"),
        ("get", "/events"),
        ("get", "/telemetry/endpoints"),
        (
            "post",
            "/telemetry/heartbeat",
            {
                "endpoint_id": "ep-ui-auth-001",
                "hostname": "ui-auth-host",
                "ip_address": "10.10.10.10",
            },
        ),
    ]

    for method, path, *payload in protected_calls:
        if method == "post":
            response = client.post(path, json=payload[0])
        else:
            response = client.get(path)
        assert response.status_code == 401


def test_login_then_access_protected_endpoints() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    agent_headers = {"X-Agent-Token": settings.AGENT_TOKEN}

    alerts_resp = client.get("/alerts", headers=headers)
    assert alerts_resp.status_code == 200
    assert isinstance(alerts_resp.json(), list)

    events_resp = client.get("/events", headers=headers)
    assert events_resp.status_code == 200
    assert isinstance(events_resp.json(), list)

    heartbeat_resp = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-ui-auth-002",
            "hostname": "ui-auth-host-ok",
            "ip_address": "10.10.10.11",
        },
        headers=agent_headers,
    )
    assert heartbeat_resp.status_code == 200
    heartbeat_data = heartbeat_resp.json()
    assert heartbeat_data["status"] == "accepted"
    assert heartbeat_data["endpoint_id"] == "ep-ui-auth-002"

    endpoints_resp = client.get("/telemetry/endpoints", headers=headers)
    assert endpoints_resp.status_code == 200
    assert isinstance(endpoints_resp.json(), list)


def test_ui2_alerts_status_filter_api_flow() -> None:
    """Le flux API derrière le filtre status UI2 renvoie des statuts cohérents."""
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    event_resp = client.post(
        "/events",
        json={
            "endpoint_id": "ep-ui2-filter-001",
            "event_type": "intrusion_detected",
            "severity": "critical",
            "source": "ui2-filter-test",
            "description": "Critical event for status filter",
        },
        headers=headers,
    )
    assert event_resp.status_code == 201

    alerts_resp = client.get("/alerts", headers=headers)
    assert alerts_resp.status_code == 200
    created_alert = next(
        a
        for a in alerts_resp.json()
        if a["description"] == "Critical event for status filter"
    )

    ack_resp = client.post(
        f"/alerts/{created_alert['alert_id']}/acknowledge",
        headers=headers,
    )
    assert ack_resp.status_code == 200

    filtered_resp = client.get(
        "/alerts",
        params={"status": "acknowledged"},
        headers=headers,
    )
    assert filtered_resp.status_code == 200
    filtered = filtered_resp.json()
    assert isinstance(filtered, list)
    assert all(item["status"] == "acknowledged" for item in filtered)


def test_ui2_scan_simulated_invalid_payload_returns_422() -> None:
    """Le POST /events du scan simulé échoue sur payload invalide."""
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/events",
        json={
            "endpoint_id": "",
            "event_type": "scan_port",
            "severity": "medium",
            "source": "ui-scan-tool",
            "description": "UI simulated port scan on 10.0.0.99",
            "details": {"target": "10.0.0.99", "simulated": True},
        },
        headers=headers,
    )
    assert response.status_code == 422
