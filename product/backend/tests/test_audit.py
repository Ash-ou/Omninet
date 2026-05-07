"""Tests pour le module d'audit (EPIC-03)."""

from fastapi.testclient import TestClient

from app.audit import service
from app.main import app

client = TestClient(app)


def _login(username: str, password: str) -> str:
    """Helper : login et retourne le token."""
    response = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    return response.json()["access_token"]


def test_login_creates_audit_entry() -> None:
    """Se logger doit créer une entrée d'audit."""
    # Compter les entrées avant
    before_count = len(service.get_all_entries())

    _login("admin", "admin")

    after_count = len(service.get_all_entries())
    assert after_count == before_count + 1

    # Vérifier la dernière entrée
    entries = service.get_all_entries()
    last_entry = entries[0]
    assert last_entry.username == "admin"
    assert last_entry.action == "login"
    assert last_entry.resource == "auth"
    assert last_entry.details == {"success": True}


def test_failed_login_creates_audit_entry() -> None:
    """Un login échoué doit créer une entrée d'audit avec login_failed."""
    before_count = len(service.get_all_entries())

    client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    after_count = len(service.get_all_entries())
    assert after_count == before_count + 1

    entries = service.get_all_entries()
    last_entry = entries[0]
    assert last_entry.username == "admin"
    assert last_entry.action == "login_failed"
    assert last_entry.resource == "auth"
    assert last_entry.details == {"success": False}


def test_list_audit_by_admin() -> None:
    """GET /audit avec un token admin retourne 200 avec des entrées."""
    token = _login("admin", "admin")

    response = client.get(
        "/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_audit_by_analyst_forbidden() -> None:
    """GET /audit avec un token analyst retourne 403."""
    token = _login("analyst", "analyst")

    response = client.get(
        "/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_list_audit_without_token() -> None:
    """GET /audit sans token retourne 401."""
    response = client.get("/audit")
    assert response.status_code == 401


def test_filter_audit_by_action() -> None:
    """Le filtre par action retourne uniquement les entrées correspondantes."""
    token = _login("admin", "admin")

    # Filtrer par action "login"
    response = client.get(
        "/audit",
        params={"action": "login"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(entry["action"] == "login" for entry in data)


def test_filter_audit_by_username() -> None:
    """Le filtre par username retourne uniquement les entrées de l'utilisateur."""
    token = _login("admin", "admin")

    response = client.get(
        "/audit",
        params={"username": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(entry["username"] == "admin" for entry in data)


def test_audit_entry_has_required_fields() -> None:
    """Une entrée d'audit doit avoir les champs requis : id, timestamp, username, action, resource."""
    token = _login("admin", "admin")

    response = client.get(
        "/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    entry = data[0]
    assert "id" in entry
    assert "timestamp" in entry
    assert "username" in entry
    assert "action" in entry
    assert "resource" in entry
    assert entry["id"] != ""
    assert entry["timestamp"] != ""


def test_acknowledge_alert_creates_audit_entry() -> None:
    """Acknowledge une alerte doit créer une entrée d'audit."""
    admin_token = _login("admin", "admin")

    # Créer un event critical pour générer une alerte
    client.post(
        "/events",
        json={
            "endpoint_id": "ep-audit-001",
            "event_type": "intrusion_detected",
            "severity": "critical",
            "source": "firewall-audit",
            "description": "Test audit acknowledge",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Récupérer la dernière alerte
    alerts_resp = client.get(
        "/alerts",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    alert_id = alerts_resp.json()[0]["alert_id"]

    # Compter les entrées audit avant acknowledge
    before_count = len(service.get_all_entries())

    # Acknowledge
    ack_resp = client.post(
        f"/alerts/{alert_id}/acknowledge",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ack_resp.status_code == 200

    after_count = len(service.get_all_entries())
    assert after_count == before_count + 1

    # Vérifier l'entrée d'audit
    entries = service.get_all_entries()
    last_entry = entries[0]
    assert last_entry.username == "admin"
    assert last_entry.action == "acknowledge_alert"
    assert last_entry.resource == "alerts"
    assert last_entry.details["alert_id"] == alert_id


def test_audit_entries_most_recent_first() -> None:
    """Les entrées d'audit doivent être retournées les plus récentes d'abord."""
    # Nettoyer les entrées existantes pour ce test
    service._entries.clear()

    service.log_action("user1", "action_a", "resource1")
    service.log_action("user2", "action_b", "resource2")
    service.log_action("user3", "action_c", "resource3")

    entries = service.get_all_entries()
    assert len(entries) == 3
    assert entries[0].action == "action_c"
    assert entries[1].action == "action_b"
    assert entries[2].action == "action_a"


def test_get_entries_by_user() -> None:
    """get_entries_by_user filtre correctement par utilisateur."""
    service._entries.clear()

    service.log_action("alice", "login", "auth")
    service.log_action("bob", "login", "auth")
    service.log_action("alice", "acknowledge_alert", "alerts")

    alice_entries = service.get_entries_by_user("alice")
    assert len(alice_entries) == 2
    assert all(e.username == "alice" for e in alice_entries)

    bob_entries = service.get_entries_by_user("bob")
    assert len(bob_entries) == 1
    assert bob_entries[0].username == "bob"


def test_get_entries_by_action() -> None:
    """get_entries_by_action filtre correctement par action."""
    service._entries.clear()

    service.log_action("admin", "login", "auth")
    service.log_action("admin", "acknowledge_alert", "alerts")
    service.log_action("analyst", "login", "auth")

    login_entries = service.get_entries_by_action("login")
    assert len(login_entries) == 2
    assert all(e.action == "login" for e in login_entries)

    ack_entries = service.get_entries_by_action("acknowledge_alert")
    assert len(ack_entries) == 1
    assert ack_entries[0].action == "acknowledge_alert"


def test_audit_limit_parameter() -> None:
    """Le paramètre limit tronque correctement les résultats."""
    service._entries.clear()

    for i in range(10):
        service.log_action(f"user{i}", "action", "resource")

    entries = service.get_all_entries(limit=5)
    assert len(entries) == 5


def test_audit_no_password_in_details() -> None:
    """Aucun mot de passe ne doit apparaître dans les détails d'audit."""
    token = _login("admin", "admin")

    response = client.get(
        "/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    for entry in data:
        if entry.get("details"):
            assert "password" not in str(entry["details"]).lower()
            assert "token" not in str(entry["details"]).lower()


def test_log_action_redacts_sensitive_details() -> None:
    """Les clés sensibles (password/token) doivent être redacted."""
    service._entries.clear()

    entry = service.log_action(
        username="admin",
        action="login",
        resource="auth",
        details={"password": "super-secret", "access_token": "abc123"},
    )

    assert entry.details == {
        "password": "[REDACTED]",
        "access_token": "[REDACTED]",
    }


def test_log_action_sanitizes_nested_list_details() -> None:
    """La sanitization doit fonctionner dans les structures imbriquées list/dict."""
    service._entries.clear()

    entry = service.log_action(
        username="analyst",
        action="bulk_import",
        resource="assets",
        details={
            "items": [
                {"name": "host-1", "api_key": "k1"},
                {"meta": {"token": "tkn", "ok": True}},
            ]
        },
    )

    assert entry.details == {
        "items": [
            {"name": "host-1", "api_key": "[REDACTED]"},
            {"meta": {"token": "[REDACTED]", "ok": True}},
        ]
    }


def test_log_action_keeps_non_sensitive_field() -> None:
    """Un champ non sensible doit être conservé."""
    service._entries.clear()

    entry = service.log_action(
        username="admin",
        action="read_dashboard",
        resource="reports",
        details={"event_type": "heartbeat", "status": "ok"},
    )

    assert entry.details == {"event_type": "heartbeat", "status": "ok"}
