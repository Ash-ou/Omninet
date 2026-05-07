"""Tests pour le module d'alertes."""

from fastapi.testclient import TestClient
from app.main import app
from app.alerts import service as alert_service
from app.events import service as event_service

client = TestClient(app)


def _clean_state() -> None:
    """Nettoie l'etat en memoire entre les tests."""
    with alert_service._lock:
        alert_service._alerts.clear()
        alert_service._recent_events.clear()
    with event_service._lock:
        event_service._events.clear()


def _login(username: str, password: str) -> str:
    """Helper: login et retourne le token."""
    response = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    return response.json()["access_token"]


def _create_event(token: str, severity: str) -> dict:
    """Helper: cree un event et retourne la reponse JSON."""
    return client.post(
        "/events",
        json={
            "endpoint_id": "ep-001",
            "event_type": "normal_traffic",
            "severity": severity,
            "source": "firewall-01",
            "description": "Trafic normal",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def _create_event_with_type(
    token: str, severity: str, event_type: str, endpoint_id: str = "ep-001"
) -> dict:
    """Helper: cree un event avec type personnalise."""
    return client.post(
        "/events",
        json={
            "endpoint_id": endpoint_id,
            "event_type": event_type,
            "severity": severity,
            "source": "firewall-01",
            "description": f"Event: {event_type}",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def _create_event_with_details(
    token: str, severity: str, details: dict, endpoint_id: str = "ep-001"
) -> dict:
    """Helper: cree un event avec details personnalises."""
    return client.post(
        "/events",
        json={
            "endpoint_id": endpoint_id,
            "event_type": "port_scan",
            "severity": severity,
            "source": "scanner-01",
            "description": "Port scan detected",
            "details": details,
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def test_alert_created_from_critical_event() -> None:
    """Un event critical doit generer une alerte automatiquement."""
    _clean_state()
    token = _login("admin", "admin")
    event_resp = _create_event(token, "critical")
    assert event_resp.status_code == 201

    alerts_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
    alert = alerts[0]
    assert alert["severity"] == "critical"
    assert alert["status"] == "new"
    assert "[CRITICAL]" in alert["title"]


def test_no_alert_from_low_event() -> None:
    """Un event low ne doit pas generer d'alerte."""
    _clean_state()
    token = _login("admin", "admin")
    # Compter les alertes existantes
    before_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    before_count = len(before_resp.json())

    # Utiliser un type normal qui ne declenche aucune regle
    event_resp = _create_event_with_type(token, "low", "normal_traffic")
    assert event_resp.status_code == 201

    after_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert after_resp.status_code == 200
    after_count = len(after_resp.json())
    assert after_count == before_count


def test_list_alerts() -> None:
    """GET /alerts retourne 200 avec la liste des alertes."""
    _clean_state()
    token = _login("admin", "admin")
    # Creer un event critical pour avoir au moins une alerte
    _create_event(token, "critical")

    response = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_acknowledge_by_admin() -> None:
    """Un admin peut reconnaitre une alerte."""
    _clean_state()
    token = _login("admin", "admin")
    _create_event(token, "critical")

    # Recuperer la premiere alerte
    alerts_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    alert_id = alerts_resp.json()[0]["alert_id"]

    # Acknowledge
    ack_resp = client.post(
        f"/alerts/{alert_id}/acknowledge",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ack_resp.status_code == 200
    data = ack_resp.json()
    assert data["status"] == "acknowledged"
    assert data["acknowledged_by"] == "admin"
    assert data["acknowledged_at"] is not None


def test_acknowledge_by_analyst_forbidden() -> None:
    """Un analyst ne peut pas reconnaitre une alerte (403)."""
    _clean_state()
    admin_token = _login("admin", "admin")
    _create_event(admin_token, "critical")

    alerts_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {admin_token}"}
    )
    alert_id = alerts_resp.json()[0]["alert_id"]

    analyst_token = _login("analyst", "analyst")
    ack_resp = client.post(
        f"/alerts/{alert_id}/acknowledge",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert ack_resp.status_code == 403


def test_acknowledge_nonexistent() -> None:
    """Reconnaitre une alerte inexistante retourne 404."""
    _clean_state()
    token = _login("admin", "admin")
    ack_resp = client.post(
        "/alerts/nonexistent-id/acknowledge",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ack_resp.status_code == 404


def test_filter_alerts_by_status() -> None:
    """Le filtre par statut fonctionne correctement."""
    _clean_state()
    token = _login("admin", "admin")
    _create_event(token, "critical")

    # Recuperer une alerte et l'acknowledger
    alerts_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    alert_id = alerts_resp.json()[0]["alert_id"]

    client.post(
        f"/alerts/{alert_id}/acknowledge",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Filtrer par status acknowledged
    ack_resp = client.get(
        "/alerts",
        params={"status": "acknowledged"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ack_resp.status_code == 200
    ack_alerts = ack_resp.json()
    assert len(ack_alerts) >= 1
    assert all(a["status"] == "acknowledged" for a in ack_alerts)

    # Filtrer par status new (ne doit pas inclure l'alerte ack)
    new_resp = client.get(
        "/alerts",
        params={"status": "new"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert new_resp.status_code == 200
    new_alerts = new_resp.json()
    assert all(a["status"] == "new" for a in new_alerts)
    assert not any(a["alert_id"] == alert_id for a in new_alerts)


def test_intrusion_low_creates_alert() -> None:
    """Un event intrusion avec severity low doit generer une alerte (regle 3)."""
    _clean_state()
    token = _login("admin", "admin")
    before_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    before_count = len(before_resp.json())

    # Creer un event avec type contenant "intrusion"
    event_resp = _create_event_with_type(token, "low", "intrusion_detected")
    assert event_resp.status_code == 201

    after_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert after_resp.status_code == 200
    after_alerts = after_resp.json()
    assert len(after_alerts) == before_count + 1

    # Trouver la nouvelle alerte (celle avec intrusion)
    new_alerts = [a for a in after_alerts if "intrusion_detected" in a.get("title", "")]
    assert len(new_alerts) >= 1
    new_alert = new_alerts[0]
    assert "Suspicious" in new_alert["title"]
    assert new_alert["severity"] == "low"
    # Verifier que les regles sont tracees dans details
    assert new_alert["details"] is not None
    assert "triggered_rules" in new_alert["details"]
    assert "suspicious_event_type" in new_alert["details"]["triggered_rules"]


def test_medium_flood_creates_alert() -> None:
    """3 events medium du meme endpoint en 5 min doit generer alerte flood (regle 2)."""
    _clean_state()
    token = _login("admin", "admin")
    endpoint_id = "ep-flood-test"

    before_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    before_count = len(before_resp.json())

    # Creer 3 events medium du meme endpoint
    for i in range(3):
        event_resp = _create_event_with_type(
            token, "medium", "suspicious_activity", endpoint_id
        )
        assert event_resp.status_code == 201

    after_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert after_resp.status_code == 200
    after_alerts = after_resp.json()
    after_count = len(after_alerts)

    # Doit avoir au moins une alerte de flood en plus
    assert after_count >= before_count + 1

    # Verifier qu'une alerte de type flood existe
    flood_alerts = [a for a in after_alerts if "FLOOD" in a.get("title", "")]
    assert len(flood_alerts) >= 1
    flood_alert = flood_alerts[0]
    assert flood_alert["details"] is not None
    assert "triggered_rules" in flood_alert["details"]
    assert "medium_flood" in flood_alert["details"]["triggered_rules"]


def test_two_medium_events_no_flood() -> None:
    """2 events medium du meme endpoint ne doit pas generer alerte flood."""
    _clean_state()
    token = _login("admin", "admin")
    endpoint_id = "ep-no-flood"

    before_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    before_count = len(before_resp.json())

    # Creer seulement 2 events medium
    for i in range(2):
        event_resp = _create_event_with_type(
            token, "medium", "suspicious_activity", endpoint_id
        )
        assert event_resp.status_code == 201

    after_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert after_resp.status_code == 200
    after_alerts = after_resp.json()
    after_count = len(after_alerts)

    # Pas d'alerte flood pour seulement 2 events
    flood_alerts = [a for a in after_alerts if "FLOOD" in a.get("title", "")]
    assert len(flood_alerts) == 0

    # Le nombre d'alertes ne doit pas avoir augmente a cause du flood
    # (mais peut avoir augmente pour d'autres raisons)
    assert after_count == before_count


def test_normal_low_no_alert() -> None:
    """Un event normal avec severity low ne doit pas generer d'alerte."""
    _clean_state()
    token = _login("admin", "admin")
    before_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    before_count = len(before_resp.json())

    # Creer un event low avec type normal (pas intrusion/exploit/malware)
    event_resp = _create_event_with_type(token, "low", "normal_traffic")
    assert event_resp.status_code == 201

    after_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert after_resp.status_code == 200
    after_count = len(after_resp.json())
    assert after_count == before_count


def test_sensitive_port_scan_creates_alert() -> None:
    """Un scan detectant des ports sensibles (22, 3389, 445) doit generer alerte (regle 4)."""
    _clean_state()
    token = _login("admin", "admin")
    before_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    before_count = len(before_resp.json())

    # Creer un event de scan avec port 22 (SSH)
    details = {"ports": [{"port": 22, "state": "open"}, {"port": 80, "state": "open"}]}
    event_resp = _create_event_with_details(token, "low", details)
    assert event_resp.status_code == 201

    after_resp = client.get(
        "/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert after_resp.status_code == 200
    after_alerts = after_resp.json()
    after_count = len(after_alerts)
    assert after_count >= before_count + 1

    # Verifier qu'une alerte pour port sensible existe
    port_alerts = [a for a in after_alerts if "Sensitive port scan" in a.get("title", "")]
    assert len(port_alerts) >= 1
    port_alert = port_alerts[0]
    assert port_alert["details"] is not None
    assert "triggered_rules" in port_alert["details"]
    assert "sensitive_port_scan" in port_alert["details"]["triggered_rules"]
    assert port_alert["severity"] == "high"


def test_resolve_alert_by_admin() -> None:
    """Admin peut résoudre une alerte."""
    _clean_state()
    token = _login("admin", "admin")

    # Créer une alerte via event critical
    event_resp = _create_event(token, "critical")
    assert event_resp.status_code == 201
    event_data = event_resp.json()

    # Récupérer l'alerte créée
    alerts_resp = client.get("/alerts", headers={"Authorization": f"Bearer {token}"})
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["alert_id"]

    # Résoudre l'alerte
    resolve_resp = client.post(
        f"/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resolve_resp.status_code == 200
    resolved = resolve_resp.json()
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] is not None
    assert resolved["resolved_by"] == "admin"


def test_resolve_alert_by_analyst_forbidden() -> None:
    """Analyst ne peut pas résoudre une alerte (403)."""
    _clean_state()
    admin_token = _login("admin", "admin")

    # Créer une alerte
    _create_event(admin_token, "critical")
    alerts_resp = client.get("/alerts", headers={"Authorization": f"Bearer {admin_token}"})
    alert_id = alerts_resp.json()[0]["alert_id"]

    # Analyst tente de résoudre
    analyst_token = _login("analyst", "analyst")
    resolve_resp = client.post(
        f"/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resolve_resp.status_code == 403


def test_resolve_nonexistent_alert() -> None:
    """Résoudre une alerte inexistante retourne 404."""
    _clean_state()
    token = _login("admin", "admin")

    resolve_resp = client.post(
        "/alerts/nonexistent-id/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resolve_resp.status_code == 404


def test_full_alert_lifecycle() -> None:
    """Cycle complet: new -> acknowledged -> resolved."""
    _clean_state()
    token = _login("admin", "admin")

    # Créer alerte
    _create_event(token, "critical")
    alerts_resp = client.get("/alerts", headers={"Authorization": f"Bearer {token}"})
    alert_id = alerts_resp.json()[0]["alert_id"]

    # Acknowledge
    ack_resp = client.post(
        f"/alerts/{alert_id}/acknowledge",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acknowledged"

    # Resolve
    resolve_resp = client.post(
        f"/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resolve_resp.status_code == 200
    resolved = resolve_resp.json()
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] is not None
    assert resolved["resolved_by"] == "admin"
    assert resolved["acknowledged_at"] is not None  # Conserve l'ack
