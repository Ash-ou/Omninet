"""Tests pour l'authentification JWT."""

import pytest
from fastapi.testclient import TestClient

from app.auth.rate_limit import login_rate_limiter
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_login_rate_limiter() -> None:
    """Réinitialise le rate limiter entre les tests."""
    login_rate_limiter.clear()


def _login(username: str, password: str) -> dict:
    """Helper : se connecte et retourne la réponse JSON."""
    return client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )


def test_login_valid_credentials() -> None:
    """POST /auth/login avec des identifiants valides retourne 200 et un token."""
    response = _login("admin", "admin")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_valid_analyst() -> None:
    """POST /auth/login avec les identifiants analyst retourne 200."""
    response = _login("analyst", "analyst")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password() -> None:
    """POST /auth/login avec un mot de passe incorrect retourne 401."""
    response = _login("admin", "wrong-password")
    assert response.status_code == 401


def test_login_unknown_user() -> None:
    """POST /auth/login avec un utilisateur inconnu retourne 401."""
    response = _login("nonexistent", "password")
    assert response.status_code == 401


def test_me_without_token() -> None:
    """GET /auth/me sans token retourne 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_valid_token() -> None:
    """GET /auth/me avec un token valide retourne 200 avec username et role."""
    login_response = _login("admin", "admin")
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_me_with_analyst_token() -> None:
    """GET /auth/me avec un token analyst retourne le role analyst."""
    login_response = _login("analyst", "analyst")
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "analyst"
    assert data["role"] == "analyst"


def test_me_with_invalid_token() -> None:
    """GET /auth/me avec un token invalide retourne 401."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token-here"},
    )
    assert response.status_code == 401


def test_health_still_public() -> None:
    """GET /health sans token retourne 200 (endpoint public)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_root_still_public() -> None:
    """GET / sans token retourne 200 (endpoint public)."""
    response = client.get("/")
    assert response.status_code == 200


def test_login_rate_limit_six_invalid_attempts_returns_429() -> None:
    """6 tentatives invalides successives => la dernière retourne 429."""
    for _ in range(5):
        response = _login("admin", "wrong-password")
        assert response.status_code == 401

    response = _login("admin", "wrong-password")
    assert response.status_code == 429
    assert "Trop de tentatives" in response.json()["detail"]


def test_login_valid_credentials_but_rate_limited_returns_429() -> None:
    """Même avec des credentials valides, un bucket limité doit retourner 429."""
    for _ in range(5):
        response = _login("admin", "wrong-password")
        assert response.status_code == 401

    response = _login("admin", "admin")
    assert response.status_code == 429


def test_login_rate_limit_window_expired_allows_new_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Après expiration de fenêtre, une nouvelle tentative redevient autorisée."""
    fake_time = [1000.0]
    monkeypatch.setattr(login_rate_limiter, "_now_fn", lambda: fake_time[0])

    for _ in range(5):
        response = _login("admin", "wrong-password")
        assert response.status_code == 401

    blocked_response = _login("admin", "wrong-password")
    assert blocked_response.status_code == 429

    fake_time[0] += 61.0
    after_window_response = _login("admin", "wrong-password")
    assert after_window_response.status_code == 401
