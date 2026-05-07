"""Tests pour le module de rapports et KPI."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Client de test FastAPI."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers d'authentification avec token admin."""
    from app.auth.service import create_access_token
    token = create_access_token({"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


class TestReportsEvents:
    """Tests pour l'export des événements."""

    def test_export_events_json(self, client, auth_headers):
        """Test export JSON des événements."""
        response = client.get("/reports/events?format=json", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_export_events_csv(self, client, auth_headers):
        """Test export CSV des événements."""
        response = client.get("/reports/events?format=csv", headers=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_events_empty(self, client, auth_headers):
        """Test export avec données vides."""
        response = client.get("/reports/events?format=json", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestReportsAlerts:
    """Tests pour l'export des alertes."""

    def test_export_alerts_json(self, client, auth_headers):
        """Test export JSON des alertes."""
        response = client.get("/reports/alerts?format=json", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_export_alerts_csv(self, client, auth_headers):
        """Test export CSV des alertes."""
        response = client.get("/reports/alerts?format=csv", headers=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]


class TestReportsScans:
    """Tests pour l'export des scans."""

    def test_export_scans_json(self, client, auth_headers):
        """Test export JSON des scans."""
        response = client.get("/reports/scans?format=json", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_export_scans_csv(self, client, auth_headers):
        """Test export CSV des scans."""
        response = client.get("/reports/scans?format=csv", headers=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_scans_empty(self, client, auth_headers):
        """Test export scans avec données vides."""
        response = client.get("/reports/scans?format=json", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestReportsAuth:
    """Tests d'authentification pour les rapports."""

    def test_without_auth(self, client):
        """Test accès sans token."""
        response = client.get("/reports/events?format=json")
        assert response.status_code == 401

    def test_with_analyst_auth(self, client):
        """Test accès avec utilisateur analyst."""
        from app.auth.service import create_access_token
        token = create_access_token({"sub": "analyst", "role": "analyst"})
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/reports/events?format=json", headers=headers)
        assert response.status_code == 200


class TestReportsInvalidFormat:
    """Tests pour les formats invalides."""

    def test_invalid_format_returns_422(self, client, auth_headers):
        """Test format invalide."""
        response = client.get("/reports/events?format=xml", headers=auth_headers)
        assert response.status_code == 422

    def test_missing_format(self, client, auth_headers):
        """Test format manquant."""
        response = client.get("/reports/events", headers=auth_headers)
        assert response.status_code == 422


class TestKPIEndpoint:
    """Tests pour l'endpoint KPI."""

    def test_get_kpi_summary_success(self, client, auth_headers):
        """Test que l'endpoint GET /reports/kpi retourne 200 avec les clés attendues."""
        response = client.get("/reports/kpi", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Vérifier les clés principales
        expected_keys = {
            "total_events",
            "total_alerts",
            "total_endpoints",
            "total_scans",
            "alerts_by_severity",
            "alerts_by_status",
            "events_last_24h",
            "top_sources",
        }
        assert expected_keys.issubset(set(data.keys())), \
            f"Clés manquantes: {expected_keys - set(data.keys())}"

        # Vérifier les types
        assert isinstance(data["total_events"], int)
        assert isinstance(data["total_alerts"], int)
        assert isinstance(data["total_endpoints"], int)
        assert isinstance(data["total_scans"], int)
        assert isinstance(data["alerts_by_severity"], dict)
        assert isinstance(data["alerts_by_status"], dict)
        assert isinstance(data["events_last_24h"], int)
        assert isinstance(data["top_sources"], list)

    def test_get_kpi_unauthorized(self, client):
        """Test que l'endpoint GET /reports/kpi retourne 401 sans token."""
        response = client.get("/reports/kpi")
        assert response.status_code == 401

    def test_get_kpi_with_data(self, client, auth_headers):
        """Test que l'endpoint KPI reflète correctement les données."""
        # Créer quelques événements et alertes via les API
        from app.events.service import create_event
        from app.events.schemas import EventCreate, EventSeverity
        from app.alerts.service import create_alert_from_event

        # Créer un événement avec sévérité high pour déclencher une alerte
        event_data = EventCreate(
            endpoint_id="ep-test-001",
            event_type="test_event",
            severity=EventSeverity.HIGH,
            source="test",
            description="Test event for KPI",
        )
        event = create_event(event_data)

        # Créer une alerte basée sur l'événement
        create_alert_from_event(
            event_id=event.event_id,
            endpoint_id="ep-test-001",
            severity="high",
            source="test",
            description="Test alert",
            event_type="test_event",
        )

        # Récupérer les KPI
        response = client.get("/reports/kpi", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total_events"] >= 1
        assert data["total_alerts"] >= 1
