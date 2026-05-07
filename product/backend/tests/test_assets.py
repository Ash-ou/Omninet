"""Tests pour le module Assets."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.assets import service as assets_service
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


def _send_heartbeat(endpoint_id: str, ip: str, hostname: str) -> None:
    """Helper : envoie un heartbeat."""
    client.post(
        "/telemetry/heartbeat",
        json={
            "endpoint_id": endpoint_id,
            "hostname": hostname,
            "ip_address": ip,
            "os_info": "Ubuntu 22.04 LTS",
            "agent_version": "1.0.0",
        },
        headers=_agent_headers(settings.AGENT_TOKEN),
    )


def _launch_port_scan(target: str, ports: list[int]) -> str:
    """Helper : lance un port scan et retourne le scan_id."""
    admin_token = _login("admin", "admin")
    response = client.post(
        "/discovery/scans",
        json={"target": target, "scan_type": "port", "ports": ports},
        headers=_auth_headers(admin_token),
    )
    return response.json()["scan_id"]


def _wait_for_scan(scan_id: str, token: str, max_retries: int = 20) -> str:
    """Attend la fin d'un scan et retourne son statut."""
    for _ in range(max_retries):
        time.sleep(0.5)
        resp = client.get(
            f"/discovery/scans/{scan_id}",
            headers=_auth_headers(token),
        )
        status = resp.json()["status"]
        if status in ("completed", "failed"):
            return status
    return "timeout"


# --- Tests de base ---


def test_heartbeat_creates_endpoint_in_inventory() -> None:
    """Un heartbeat crée un endpoint visible dans l'inventaire assets."""
    # Réinitialiser l'inventaire
    assets_service.build_inventory()

    _send_heartbeat("ep-asset-001", "10.0.10.1", "srv-web-asset")

    admin_token = _login("admin", "admin")
    response = client.get("/assets", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Trouver notre asset
    asset = next((a for a in data if a["ip_address"] == "10.0.10.1"), None)
    assert asset is not None
    assert asset["hostname"] == "srv-web-asset"
    assert asset["os_info"] == "Ubuntu 22.04 LTS"
    assert asset["agent_version"] == "1.0.0"
    assert asset["status"] == "alive"
    assert "last_seen" in asset
    assert "first_discovered" in asset


def test_port_scan_discovers_open_ports() -> None:
    """Un scan de ports découvre des ports ouverts dans l'inventaire."""
    admin_token = _login("admin", "admin")

    # Lancer un scan sur localhost
    scan_id = _launch_port_scan("127.0.0.1", [80, 443])
    status = _wait_for_scan(scan_id, admin_token)

    assert status == "completed", f"Scan ended with status: {status}"

    # Reconstruire l'inventaire
    response = client.post("/assets/rebuild", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Trouver l'asset 127.0.0.1
    asset = next((a for a in data if a["ip_address"] == "127.0.0.1"), None)
    assert asset is not None
    assert isinstance(asset["open_ports"], list)
    assert isinstance(asset["services"], list)
    assert asset["last_scanned"] is not None


def test_rebuild_aggregates_heartbeat_and_scan() -> None:
    """Rebuild agrège les données heartbeat + scan pour un même IP."""
    admin_token = _login("admin", "admin")

    # 1. Heartbeat pour une IP
    _send_heartbeat("ep-asset-agg", "10.0.10.2", "srv-agg")

    # 2. Scan sur la même IP (ne complétera pas forcément avec ports ouverts,
    #    mais l'asset sera mis à jour avec last_scanned)
    scan_id = _launch_port_scan("10.0.10.2", [80])
    _wait_for_scan(scan_id, admin_token)

    # 3. Rebuild
    response = client.post("/assets/rebuild", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()

    asset = next((a for a in data if a["ip_address"] == "10.0.10.2"), None)
    assert asset is not None
    # L'asset doit avoir les données du heartbeat
    assert asset["hostname"] == "srv-agg"
    assert asset["os_info"] == "Ubuntu 22.04 LTS"
    # Et les données du scan
    assert asset["last_scanned"] is not None


def test_list_assets_returns_consolidated_list() -> None:
    """GET /assets retourne la liste consolidée des actifs."""
    admin_token = _login("admin", "admin")

    # Créer quelques assets
    _send_heartbeat("ep-asset-list-1", "10.0.20.1", "srv-list-1")
    _send_heartbeat("ep-asset-list-2", "10.0.20.2", "srv-list-2")

    response = client.get("/assets", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    # Vérifier le format AssetResponse
    for asset in data:
        assert "asset_id" in asset
        assert "ip_address" in asset
        assert "hostname" in asset
        assert "os_info" in asset
        assert "agent_version" in asset
        assert "last_seen" in asset
        assert "status" in asset
        assert "open_ports" in asset
        assert "services" in asset
        assert "first_discovered" in asset
        assert "last_scanned" in asset


def test_get_asset_by_id_returns_detailed_asset() -> None:
    """GET /assets/{id} retourne un asset détaillé."""
    admin_token = _login("admin", "admin")

    _send_heartbeat("ep-asset-detail", "10.0.30.1", "srv-detail")

    # Rebuild pour peupler l'inventaire
    client.post("/assets/rebuild", headers=_auth_headers(admin_token))

    response = client.get(
        "/assets/10.0.30.1",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "10.0.30.1"
    assert data["ip_address"] == "10.0.30.1"
    assert data["hostname"] == "srv-detail"


def test_get_nonexistent_asset_returns_404() -> None:
    """GET /assets/{id} inexistant retourne 404."""
    admin_token = _login("admin", "admin")

    response = client.get(
        "/assets/192.168.99.99",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 404


# --- Tests RBAC ---


def test_analyst_can_list_assets() -> None:
    """Un analyste peut lister les assets (200)."""
    _send_heartbeat("ep-asset-analyst", "10.0.40.1", "srv-analyst")

    analyst_token = _login("analyst", "analyst")
    response = client.get("/assets", headers=_auth_headers(analyst_token))

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analyst_can_get_asset() -> None:
    """Un analyste peut récupérer un asset (200)."""
    _send_heartbeat("ep-asset-analyst-get", "10.0.40.2", "srv-analyst-get")

    admin_token = _login("admin", "admin")
    client.post("/assets/rebuild", headers=_auth_headers(admin_token))

    analyst_token = _login("analyst", "analyst")
    response = client.get(
        "/assets/10.0.40.2",
        headers=_auth_headers(analyst_token),
    )

    assert response.status_code == 200


def test_analyst_cannot_rebuild_inventory() -> None:
    """Un analyste ne peut pas rebuild l'inventaire (403)."""
    analyst_token = _login("analyst", "analyst")
    response = client.post(
        "/assets/rebuild",
        headers=_auth_headers(analyst_token),
    )

    assert response.status_code == 403


def test_unauthenticated_assets_forbidden() -> None:
    """Accès sans token retourne 401."""
    response = client.get("/assets")
    assert response.status_code == 401

    response = client.get("/assets/10.0.0.1")
    assert response.status_code == 401

    response = client.post("/assets/rebuild")
    assert response.status_code == 401


def test_asset_has_unique_ip() -> None:
    """Un asset est identifié par son IP unique."""
    admin_token = _login("admin", "admin")

    # Deux heartbeats avec la même IP mais des endpoint_id différents
    _send_heartbeat("ep-dup-1", "10.0.50.1", "srv-dup-first")
    _send_heartbeat("ep-dup-2", "10.0.50.1", "srv-dup-second")

    response = client.post("/assets/rebuild", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()

    # Un seul asset pour cette IP
    matching = [a for a in data if a["ip_address"] == "10.0.50.1"]
    assert len(matching) == 1
