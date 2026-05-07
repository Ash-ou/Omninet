from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_returns_200() -> None:
    """GET / retourne le nom et la version de l'API."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Omninet"
    assert data["version"] == "0.1.0"


def test_health_returns_200() -> None:
    """GET /health retourne un statut ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "omninet-api"
