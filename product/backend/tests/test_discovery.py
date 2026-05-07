"""Tests pour le module Discovery."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(username: str, password: str) -> str:
    """Helper: login et retourne le token."""
    response = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    return response.json()["access_token"]


def test_launch_ping_scan_valid() -> None:
    """POST /discovery/scans avec ping valide retourne 201."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["target"] == "127.0.0.1"
    assert data["scan_type"] == "ping"
    assert data["status"] in ("pending", "running")
    assert "scan_id" in data


def test_launch_port_scan_valid() -> None:
    """POST /discovery/scans avec port scan valide retourne 201."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "port", "ports": [80, 443]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["scan_type"] == "port"
    assert data["status"] in ("pending", "running", "completed")


def test_launch_service_scan_valid() -> None:
    """POST /discovery/scans avec service scan valide retourne 201."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "service", "ports": [80]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["scan_type"] == "service"


def test_scan_invalid_target_ip() -> None:
    """POST /discovery/scans avec IP invalide retourne 422."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "999.999.999.999", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_scan_invalid_target_text() -> None:
    """POST /discovery/scans avec texte invalide retourne 422."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "rm -rf /", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_scan_invalid_target_empty() -> None:
    """POST /discovery/scans avec target vide retourne 422."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_scan_invalid_port_range() -> None:
    """POST /discovery/scans avec port hors range retourne 422."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "port", "ports": [99999]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_scan_invalid_scan_type() -> None:
    """POST /discovery/scans avec scan_type invalide retourne 422."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "nmap"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_get_scan_by_id() -> None:
    """GET /discovery/scans/{scan_id} retourne 200."""
    token = _login("admin", "admin")

    # Créer un scan
    create_resp = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    scan_id = create_resp.json()["scan_id"]

    # Le récupérer
    get_resp = client.get(
        f"/discovery/scans/{scan_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["scan_id"] == scan_id


def test_get_nonexistent_scan() -> None:
    """GET /discovery/scans/{scan_id} inexistant retourne 404."""
    token = _login("admin", "admin")
    response = client.get(
        "/discovery/scans/nonexistent-id",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_list_scans() -> None:
    """GET /discovery/scans retourne 200 avec la liste."""
    token = _login("admin", "admin")

    # Créer au moins un scan
    client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/discovery/scans",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_analyst_can_list_scans() -> None:
    """Un analyste peut lister les scans (200)."""
    admin_token = _login("admin", "admin")

    # Créer un scan avec admin
    client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Lister avec analyst
    analyst_token = _login("analyst", "analyst")
    response = client.get(
        "/discovery/scans",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert response.status_code == 200


def test_analyst_cannot_create_scan() -> None:
    """Un analyste ne peut pas lancer de scan (403)."""
    analyst_token = _login("analyst", "analyst")
    response = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert response.status_code == 403


def test_analyst_cannot_create_port_scan() -> None:
    """Un analyste ne peut pas lancer de port scan (403)."""
    analyst_token = _login("analyst", "analyst")
    response = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "port"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert response.status_code == 403


def test_unauthenticated_access_forbidden() -> None:
    """Accès sans token retourne 401."""
    response = client.get("/discovery/scans")
    assert response.status_code == 401

    response = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
    )
    assert response.status_code == 401


def test_ping_scan_on_localhost_completes() -> None:
    """Un ping réel sur 127.0.0.1 doit se terminer avec status completed."""
    token = _login("admin", "admin")

    create_resp = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    scan_id = create_resp.json()["scan_id"]

    # Attendre que le scan se termine (max 10s)
    for _ in range(20):
        time.sleep(0.5)
        get_resp = client.get(
            f"/discovery/scans/{scan_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        status = get_resp.json()["status"]
        if status in ("completed", "failed"):
            break

    assert status == "completed", f"Scan ended with status: {status}"
    data = get_resp.json()
    assert data["results_count"] >= 1
    assert data["started_at"] is not None
    assert data["completed_at"] is not None


def test_port_scan_on_localhost_completes() -> None:
    """Un port scan réel sur 127.0.0.1 doit se terminer."""
    token = _login("admin", "admin")

    create_resp = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "port", "ports": [80, 443]},
        headers={"Authorization": f"Bearer {token}"},
    )
    scan_id = create_resp.json()["scan_id"]

    # Attendre que le scan se termine
    for _ in range(20):
        time.sleep(0.5)
        get_resp = client.get(
            f"/discovery/scans/{scan_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        status = get_resp.json()["status"]
        if status in ("completed", "failed"):
            break

    assert status == "completed", f"Scan ended with status: {status}"
    data = get_resp.json()
    assert data["results_count"] == 2
    # Vérifier que chaque résultat a un port et un state
    for result in data["results"]:
        assert "port" in result
        assert "state" in result


def test_scan_response_has_results_count() -> None:
    """Le champ results_count est présent dans la réponse."""
    token = _login("admin", "admin")

    create_resp = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = create_resp.json()
    assert "results_count" in data
    assert isinstance(data["results_count"], int)


def test_fqdn_target_accepted() -> None:
    """Un FQDN valide est accepté comme target."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "example.com", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


def test_ipv6_target_accepted() -> None:
    """Une IPv6 valide est acceptée comme target."""
    token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": "::1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


def test_get_scan_results_port_scan_completes() -> None:
    """GET /discovery/scans/{scan_id}/results retourne les résultats après completion."""
    token = _login("admin", "admin")

    # Lancer un port scan
    create_resp = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "port", "ports": [80, 443]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    scan_id = create_resp.json()["scan_id"]

    # Attendre que le scan se termine (max 10s)
    status = "pending"
    for _ in range(20):
        time.sleep(0.5)
        get_resp = client.get(
            f"/discovery/scans/{scan_id}/results",
            headers={"Authorization": f"Bearer {token}"},
        )
        status = get_resp.json()["status"]
        if status in ("completed", "failed"):
            break

    assert status == "completed", f"Scan ended with status: {status}"
    data = get_resp.json()

    # Vérifier les champs de la réponse
    assert data["scan_id"] == scan_id
    assert data["target"] == "127.0.0.1"
    assert data["scan_type"] == "port"
    assert data["results_count"] == 2
    assert len(data["results"]) == 2


def test_get_scan_results_format() -> None:
    """Les résultats ont le format ScanResult attendu."""
    token = _login("admin", "admin")

    create_resp = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "port", "ports": [80]},
        headers={"Authorization": f"Bearer {token}"},
    )
    scan_id = create_resp.json()["scan_id"]

    # Attendre completion
    for _ in range(20):
        time.sleep(0.5)
        get_resp = client.get(
            f"/discovery/scans/{scan_id}/results",
            headers={"Authorization": f"Bearer {token}"},
        )
        if get_resp.json()["status"] in ("completed", "failed"):
            break

    data = get_resp.json()
    assert len(data["results"]) >= 1

    # Vérifier le format de chaque résultat
    for result in data["results"]:
        assert "port" in result
        assert "protocol" in result
        assert "state" in result
        assert result["state"] in ("open", "closed", "filtered")
        assert result["protocol"] == "tcp"
        assert isinstance(result["port"], int)


def test_get_scan_results_not_found() -> None:
    """GET /discovery/scans/{scan_id}/results inexistant retourne 404."""
    token = _login("admin", "admin")
    response = client.get(
        "/discovery/scans/nonexistent-id/results",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_get_scan_results_partial_while_running() -> None:
    """GET /discovery/scans/{scan_id}/results retourne status + résultats partiels."""
    token = _login("admin", "admin")

    # Lancer un scan avec plusieurs ports pour avoir du temps
    create_resp = client.post(
        "/discovery/scans",
        json={
            "target": "127.0.0.1",
            "scan_type": "port",
            "ports": [80, 443, 8080, 3306, 5432],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    scan_id = create_resp.json()["scan_id"]

    # Interroger immédiatement — le scan est probablement encore en cours
    resp = client.get(
        f"/discovery/scans/{scan_id}/results",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_id"] == scan_id
    assert data["status"] in ("pending", "running", "completed")

    # Si le scan est terminé, vérifier les résultats
    if data["status"] == "completed":
        assert data["results_count"] == 5
        assert len(data["results"]) == 5


def test_analyst_can_get_scan_results() -> None:
    """Un analyste peut récupérer les résultats d'un scan (200)."""
    admin_token = _login("admin", "admin")

    create_resp = client.post(
        "/discovery/scans",
        json={"target": "127.0.0.1", "scan_type": "ping"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    scan_id = create_resp.json()["scan_id"]

    analyst_token = _login("analyst", "analyst")
    response = client.get(
        f"/discovery/scans/{scan_id}/results",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert response.status_code == 200


def test_unauthenticated_scan_results_forbidden() -> None:
    """Accès sans token à /scans/{id}/results retourne 401."""
    response = client.get("/discovery/scans/some-id/results")
    assert response.status_code == 401
