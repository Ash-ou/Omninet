"""Tests pour le module de télémétrie (heartbeats)."""

from fastapi.testclient import TestClient

from app.audit import service as audit_service
from app.core.config import settings
from app.main import app

client = TestClient(app)


def _login(username: str, password: str) -> str:
    """Helper : se connecte et retourne le token d'accès."""
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    """Helper : construit les headers d'autorisation."""
    return {"Authorization": f"Bearer {token}"}


def _agent_headers(token: str) -> dict[str, str]:
    """Helper : construit les headers d'authentification agent."""
    return {"X-Agent-Token": token}


# --- Heartbeat ---


def test_heartbeat_valid_agent_token() -> None:
    """POST /telemetry/heartbeat avec X-Agent-Token valide retourne 200."""

    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-001",
            "hostname": "srv-web-01",
            "ip_address": "10.0.1.50",
            "os_info": "Ubuntu 22.04 LTS",
            "agent_version": "1.0.0",
        },
        headers=_agent_headers(settings.AGENT_TOKEN),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["endpoint_id"] == "ep-001"
    assert "received_at" in data


def test_heartbeat_valid_token_creates_success_audit_without_secret() -> None:
    """Un heartbeat valide peut créer un audit success sans exposer le token."""
    before_count = len(audit_service.get_all_entries())

    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-valid-token-audit",
            "hostname": "srv-valid-token-audit",
            "ip_address": "10.0.8.12",
        },
        headers=_agent_headers(settings.AGENT_TOKEN),
    )

    assert response.status_code == 200

    entries = audit_service.get_all_entries()
    assert len(entries) >= before_count + 1

    success_entries = [
        entry
        for entry in entries
        if entry.action == "agent_auth_success" and entry.resource == "telemetry/heartbeat"
    ]
    assert success_entries

    last_success = success_entries[0]
    assert last_success.username == "agent"
    assert last_success.details == {"agent_id": "unknown"}
    assert settings.AGENT_TOKEN not in str(last_success.details)


def test_heartbeat_without_auth() -> None:
    """POST /telemetry/heartbeat sans X-Agent-Token retourne 401."""
    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-002",
            "hostname": "srv-db-01",
            "ip_address": "10.0.2.10",
        },
    )

    assert response.status_code == 401


def test_heartbeat_with_invalid_agent_token() -> None:
    """POST /telemetry/heartbeat avec X-Agent-Token invalide retourne 401."""

    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-invalid-token",
            "hostname": "srv-invalid",
            "ip_address": "10.0.9.9",
        },
        headers=_agent_headers("wrong-token"),
    )

    assert response.status_code == 401


def test_heartbeat_missing_token_creates_audit_entry_without_secret() -> None:
    """Un heartbeat sans token doit créer une entrée audit sans exposer de token."""
    before_count = len(audit_service.get_all_entries())

    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-missing-token-audit",
            "hostname": "srv-missing-token-audit",
            "ip_address": "10.0.8.10",
        },
    )

    assert response.status_code == 401

    entries = audit_service.get_all_entries()
    assert len(entries) == before_count + 1
    last_entry = entries[0]
    assert last_entry.username is None
    assert last_entry.action == "agent_auth_failed"
    assert last_entry.resource == "telemetry/heartbeat"
    assert last_entry.details == {"reason": "missing_token"}
    assert "x-agent-token" not in str(last_entry.details).lower()


def test_heartbeat_invalid_token_creates_audit_entry_without_token_value() -> None:
    """Un heartbeat avec token invalide doit auditer l'échec sans stocker le token."""
    invalid_token = "wrong-token-sensitive-value"
    before_count = len(audit_service.get_all_entries())

    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-invalid-token-audit",
            "hostname": "srv-invalid-token-audit",
            "ip_address": "10.0.8.11",
        },
        headers=_agent_headers(invalid_token),
    )

    assert response.status_code == 401

    entries = audit_service.get_all_entries()
    assert len(entries) == before_count + 1
    last_entry = entries[0]
    assert last_entry.username is None
    assert last_entry.action == "agent_auth_failed"
    assert last_entry.resource == "telemetry/heartbeat"
    assert last_entry.details == {"reason": "invalid_token"}
    assert invalid_token not in str(last_entry.details)


def test_heartbeat_with_user_bearer_only_returns_401() -> None:
    """POST /telemetry/heartbeat avec JWT user seul retourne 401."""
    token = _login("admin", "admin")

    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-user-bearer-only",
            "hostname": "srv-user-only",
            "ip_address": "10.0.5.20",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 401


def test_heartbeat_with_invalid_jwt_and_valid_agent_token_returns_200() -> None:
    """POST /telemetry/heartbeat avec JWT invalide + agent valide reste autorisé."""
    headers = {
        **_auth_headers("invalid.jwt.token"),
        **_agent_headers(settings.AGENT_TOKEN),
    }

    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-both-headers-heartbeat",
            "hostname": "srv-both-headers-heartbeat",
            "ip_address": "10.0.5.21",
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["endpoint_id"] == "ep-both-headers-heartbeat"


def test_heartbeat_minimal_fields() -> None:
    """POST /telemetry/heartbeat avec uniquement les champs obligatoires."""

    response = client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-003",
            "hostname": "srv-minimal",
            "ip_address": "10.0.3.99",
        },
        headers=_agent_headers(settings.AGENT_TOKEN),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["endpoint_id"] == "ep-003"


# --- List endpoints ---


def test_list_endpoints_empty() -> None:
    """GET /telemetry/endpoints sans heartbeat préalable retourne une liste vide."""
    # On utilise un token valide mais on ne fait pas de heartbeat avant.
    # Note : les tests précédents peuvent avoir ajouté des endpoints,
    # donc on vérifie juste que la réponse est 200 et une liste.
    token = _login("admin", "admin")

    response = client.get(
        "/telemetry/endpoints",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_endpoints_after_heartbeat() -> None:
    """GET /telemetry/endpoints après un heartbeat retourne l'endpoint avec status=alive."""
    token = _login("admin", "admin")

    # Envoie un heartbeat avec un ID unique pour ce test
    client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": "ep-test-alive",
            "hostname": "srv-test-alive",
            "ip_address": "10.0.4.1",
            "os_info": "Debian 12",
            "agent_version": "1.2.0",
        },
        headers=_agent_headers(settings.AGENT_TOKEN),
    )

    response = client.get(
        "/telemetry/endpoints",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Trouve notre endpoint dans la liste
    ep = next(e for e in data if e["endpoint_id"] == "ep-test-alive")
    assert ep["hostname"] == "srv-test-alive"
    assert ep["ip_address"] == "10.0.4.1"
    assert ep["os_info"] == "Debian 12"
    assert ep["agent_version"] == "1.2.0"
    assert ep["status"] == "alive"
    assert "last_seen" in ep


def test_list_endpoints_with_valid_token() -> None:
    """GET /telemetry/endpoints avec un token valide retourne 200."""
    token = _login("analyst", "analyst")

    response = client.get(
        "/telemetry/endpoints",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_endpoints_without_auth() -> None:
    """GET /telemetry/endpoints sans token retourne 401."""
    response = client.get("/telemetry/endpoints")
    assert response.status_code == 401


def test_list_endpoints_with_agent_token_only_returns_401() -> None:
    """GET /telemetry/endpoints avec X-Agent-Token seul retourne 401."""
    response = client.get(
        "/telemetry/endpoints",
        headers=_agent_headers(settings.AGENT_TOKEN),
    )

    assert response.status_code == 401


def test_list_endpoints_with_both_headers_uses_jwt_mechanism() -> None:
    """GET /telemetry/endpoints avec JWT valide + agent invalide reste autorisé."""
    token = _login("analyst", "analyst")
    headers = {
        **_auth_headers(token),
        **_agent_headers("invalid-agent-token"),
    }

    response = client.get("/telemetry/endpoints", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
