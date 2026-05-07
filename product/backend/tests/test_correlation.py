"""Tests pour le module de corrélation."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.events.service import _events, _lock
from app.correlation.service import correlate_events, get_correlated_groups

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_events():
    """Nettoie les événements avant et après chaque test."""
    with _lock:
        _events.clear()
    yield
    with _lock:
        _events.clear()


def _create_event(event_id: str, event_type: str, source: str, endpoint_id: str, severity: str = "medium") -> dict:
    """Crée un événement en mémoire pour les tests."""
    from datetime import datetime, timezone
    event = {
        "event_id": event_id,
        "endpoint_id": endpoint_id,
        "event_type": event_type,
        "severity": severity,
        "source": source,
        "description": f"Test event {event_id}",
        "details": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "ingested",
    }
    with _lock:
        _events.append(event)
    return event


def _get_auth_token(username: str = "admin", password: str = "admin") -> str:
    """Obtient un token JWT pour les tests."""
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    return response.json()["access_token"]


class TestCorrelationService:
    """Tests du service de corrélation."""

    def test_correlate_events_no_events(self):
        """Test corrélation sans événements."""
        groups = correlate_events()
        assert groups == []

    def test_correlate_events_single_event(self):
        """Test corrélation avec un seul événement (pas de groupe)."""
        _create_event("e1", "scan_port", "nmap", "ep1")
        groups = correlate_events()
        assert groups == []

    def test_correlate_events_three_same_type(self):
        """Test corrélation avec 3 événements du même type/source/endpoint."""
        _create_event("e1", "scan_port", "nmap", "ep1")
        _create_event("e2", "scan_port", "nmap", "ep1")
        _create_event("e3", "scan_port", "nmap", "ep1")

        groups = correlate_events()
        assert len(groups) == 1
        group = groups[0]
        assert group.event_type == "scan_port"
        assert group.source == "nmap"
        assert group.endpoint_id == "ep1"
        assert group.count == 3
        assert len(group.event_ids) == 3
        assert set(group.event_ids) == {"e1", "e2", "e3"}

    def test_correlate_events_different_type_not_grouped(self):
        """Test qu'un événement différent n'est pas groupé."""
        _create_event("e1", "scan_port", "nmap", "ep1")
        _create_event("e2", "scan_port", "nmap", "ep1")
        _create_event("e3", "scan_ping", "nmap", "ep1")  # Type différent

        groups = correlate_events()
        assert len(groups) == 1  # Seulement le groupe scan_port
        assert groups[0].event_type == "scan_port"
        assert groups[0].count == 2

    def test_correlate_events_different_source_not_grouped(self):
        """Test qu'un événement avec source différente n'est pas groupé."""
        _create_event("e1", "scan_port", "nmap", "ep1")
        _create_event("e2", "scan_port", "nmap", "ep1")
        _create_event("e3", "scan_port", "masscan", "ep1")  # Source différente

        groups = correlate_events()
        assert len(groups) == 1
        assert groups[0].source == "nmap"
        assert groups[0].count == 2

    def test_correlate_events_different_endpoint_not_grouped(self):
        """Test qu'un événement avec endpoint différent n'est pas groupé."""
        _create_event("e1", "scan_port", "nmap", "ep1")
        _create_event("e2", "scan_port", "nmap", "ep1")
        _create_event("e3", "scan_port", "nmap", "ep2")  # Endpoint différent

        groups = correlate_events()
        assert len(groups) == 1
        assert groups[0].endpoint_id == "ep1"
        assert groups[0].count == 2

    def test_correlate_events_time_window(self):
        """Test que la fenêtre temporelle est respectée."""
        from datetime import datetime, timezone, timedelta

        # Créer trois événements dans une fenêtre de 5 minutes (doivent être groupés)
        base_time = datetime.now(timezone.utc)
        _create_event("e1", "scan_port", "nmap", "ep1")
        with _lock:
            _events[-1]["timestamp"] = base_time.isoformat()

        _create_event("e2", "scan_port", "nmap", "ep1")
        with _lock:
            _events[-1]["timestamp"] = (base_time + timedelta(minutes=3)).isoformat()

        _create_event("e3", "scan_port", "nmap", "ep1")
        with _lock:
            _events[-1]["timestamp"] = (base_time + timedelta(minutes=5)).isoformat()

        # Fenêtre de 10 minutes : tous les 3 doivent être groupés
        groups = correlate_events(window_minutes=10)
        assert len(groups) == 1
        assert groups[0].count == 3

        # Fenêtre de 2 minutes : pas de groupe (écart de 5 min)
        groups = correlate_events(window_minutes=2)
        assert len(groups) == 0

    def test_highest_severity(self):
        """Test que la sévérité la plus élevée est retournée."""
        _create_event("e1", "scan_port", "nmap", "ep1", severity="low")
        _create_event("e2", "scan_port", "nmap", "ep1", severity="high")
        _create_event("e3", "scan_port", "nmap", "ep1", severity="medium")

        groups = correlate_events()
        assert len(groups) == 1
        assert groups[0].severity == "high"


class TestCorrelationRoutes:
    """Tests des routes de corrélation."""

    def test_list_groups_admin(self):
        """Test que l'admin peut lister les groupes."""
        token = _get_auth_token("admin", "admin")
        response = client.get(
            "/correlation/groups",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_groups_analyst(self):
        """Test que l'analyste peut lister les groupes."""
        # Créer l'utilisateur analyst d'abord
        client.post(
            "/auth/register",
            json={"username": "analyst", "password": "analyst"},
        )
        token = _get_auth_token("analyst", "analyst")
        response = client.get(
            "/correlation/groups",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_list_groups_unauthorized(self):
        """Test sans token."""
        response = client.get("/correlation/groups")
        assert response.status_code == 401

    def test_rebuild_admin(self):
        """Test que l'admin peut forcer le recalcul."""
        # Créer des événements
        _create_event("e1", "scan_port", "nmap", "ep1")
        _create_event("e2", "scan_port", "nmap", "ep1")
        _create_event("e3", "scan_port", "nmap", "ep1")

        token = _get_auth_token("admin", "admin")
        response = client.post(
            "/correlation/rebuild",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "rebuilt"
        assert int(data["groups_found"]) >= 0

    def test_rebuild_analyst_forbidden(self):
        """Test que l'analyste ne peut pas forcer le recalcul."""
        client.post(
            "/auth/register",
            json={"username": "analyst", "password": "analyst"},
        )
        token = _get_auth_token("analyst", "analyst")
        response = client.post(
            "/correlation/rebuild",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_rebuild_unauthorized(self):
        """Test sans token."""
        response = client.post("/correlation/rebuild")
        assert response.status_code == 401


class TestCorrelationIntegration:
    """Tests d'intégration de la corrélation."""

    def test_full_correlation_flow(self):
        """Test du flux complet : créer events -> rebuild -> vérifier groupe."""
        # Créer 3 événements du même type
        _create_event("e1", "scan_port", "nmap", "ep1")
        _create_event("e2", "scan_port", "nmap", "ep1")
        _create_event("e3", "scan_port", "nmap", "ep1")

        # Vérifier via le service
        groups = get_correlated_groups()
        assert len(groups) == 1
        assert groups[0].count == 3

        # Vérifier via l'API avec admin
        token = _get_auth_token("admin", "admin")
        response = client.get(
            "/correlation/groups",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["count"] == 3
        assert data[0]["event_type"] == "scan_port"

    def test_different_event_not_correlated(self):
        """Test qu'un événement différent n'apparaît pas dans le groupe."""
        _create_event("e1", "scan_port", "nmap", "ep1")
        _create_event("e2", "scan_port", "nmap", "ep1")
        _create_event("e3", "scan_port", "nmap", "ep1")
        _create_event("e4", "scan_ping", "nmap", "ep1")  # Différent

        token = _get_auth_token("admin", "admin")
        response = client.get(
            "/correlation/groups",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Un seul groupe
        assert data[0]["count"] == 3  # Pas le 4ème
