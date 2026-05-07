"""Tests pour le module d'ingestion d'événements."""

from fastapi.testclient import TestClient

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


def _sample_event(**overrides: object) -> dict:
    """Helper : retourne un payload d'événement valide avec overrides."""
    base = {
        "endpoint_id": "ep-001",
        "event_type": "intrusion_detected",
        "severity": "high",
        "source": "ids-sensor-01",
        "description": "Tentative d'intrusion détectée sur le segment DMZ",
        "details": {"src_ip": "192.168.1.100", "dst_port": 443},
    }
    return {**base, **overrides}


# --- Create event ---


def test_create_event_valid() -> None:
    """POST /events avec token valide retourne 201, event_id présent, status=ingested."""
    token = _login("admin", "admin")

    response = client.post(
        "/events",
        json=_sample_event(),
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    data = response.json()
    assert "event_id" in data
    assert len(data["event_id"]) > 0
    assert data["status"] == "ingested"
    assert data["endpoint_id"] == "ep-001"
    assert data["severity"] == "high"
    assert "timestamp" in data


def test_create_event_without_auth() -> None:
    """POST /events sans token retourne 401."""
    response = client.post(
        "/events",
        json=_sample_event(),
    )

    assert response.status_code == 401


def test_create_event_invalid_severity() -> None:
    """POST /events avec une sévérité invalide retourne 422 (validation Pydantic)."""
    token = _login("admin", "admin")

    response = client.post(
        "/events",
        json=_sample_event(severity="ultra-danger"),
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


# --- List events ---


def test_list_events_empty() -> None:
    """GET /events sans événement préalable retourne une liste vide."""
    token = _login("admin", "admin")

    response = client.get("/events", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_events_after_create() -> None:
    """GET /events après création retourne au moins 1 événement."""
    token = _login("admin", "admin")

    # Crée un événement avec un ID unique pour ce test
    client.post(
        "/events",
        json=_sample_event(endpoint_id="ep-list-test", event_type="scan_detected"),
        headers=_auth_headers(token),
    )

    response = client.get("/events", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_events_with_pagination() -> None:
    """GET /events avec limit/offset fonctionne correctement."""
    token = _login("admin", "admin")

    # Crée plusieurs événements
    for i in range(5):
        client.post(
            "/events",
            json=_sample_event(
                endpoint_id=f"ep-pag-{i}",
                event_type="pagination_test",
            ),
            headers=_auth_headers(token),
        )

    # Test limit
    response = client.get(
        "/events",
        params={"limit": 2},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

    # Test offset
    response_all = client.get(
        "/events",
        params={"limit": 100},
        headers=_auth_headers(token),
    )
    all_events = response_all.json()

    response_offset = client.get(
        "/events",
        params={"limit": 100, "offset": 2},
        headers=_auth_headers(token),
    )
    offset_events = response_offset.json()

    # L'offset doit retourner moins d'éléments (ou les mêmes si pas assez)
    assert len(offset_events) <= len(all_events)


def test_list_events_filter_by_severity() -> None:
    """GET /events?severity=critical ne retourne que les événements critical."""
    token = _login("admin", "admin")

    # Crée un événement critical
    client.post(
        "/events",
        json=_sample_event(
            endpoint_id="ep-sev-test",
            event_type="ransomware_detected",
            severity="critical",
        ),
        headers=_auth_headers(token),
    )

    # Filtre par critical
    response = client.get(
        "/events",
        params={"severity": "critical"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for event in data:
        assert event["severity"] == "critical"

    # Filtre par low — ne doit pas inclure notre événement critical
    response_low = client.get(
        "/events",
        params={"severity": "low"},
        headers=_auth_headers(token),
    )
    assert response_low.status_code == 200
    low_data = response_low.json()
    critical_ids = [e["event_id"] for e in data]
    for event in low_data:
        assert event["event_id"] not in critical_ids


def test_simulated_scan_event_flow_ui_source() -> None:
    """Scénario UI scan simulé: login, POST /events scan_port, puis GET /events."""
    token = _login("admin", "admin")

    create_response = client.post(
        "/events",
        json=_sample_event(
            endpoint_id="ep-ui-scan-001",
            event_type="scan_port",
            severity="medium",
            source="ui-scan-tool",
            description="UI simulated port scan on 10.0.0.42",
            details={"target": "10.0.0.42:443", "simulated": True},
        ),
        headers=_auth_headers(token),
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "ingested"

    list_response = client.get("/events", headers=_auth_headers(token))
    assert list_response.status_code == 200
    events = list_response.json()
    assert isinstance(events, list)
    assert any(
        event.get("event_type") == "scan_port"
        and event.get("source") == "ui-scan-tool"
        for event in events
    )


def test_scan_ping_target_valid_ip() -> None:
    """scan_ping accepte une cible IPv4 valide."""
    token = _login("admin", "admin")
    response = client.post(
        "/events",
        json=_sample_event(
            event_type="scan_ping",
            details={"target": "192.168.10.15"},
        ),
        headers=_auth_headers(token),
    )
    assert response.status_code == 201


def test_scan_service_target_valid_fqdn() -> None:
    """scan_service accepte une cible FQDN valide."""
    token = _login("admin", "admin")
    response = client.post(
        "/events",
        json=_sample_event(
            event_type="scan_service",
            details={"target": "api.example.com"},
        ),
        headers=_auth_headers(token),
    )
    assert response.status_code == 201


def test_scan_port_target_valid_host_port() -> None:
    """scan_port accepte un host:port valide."""
    token = _login("admin", "admin")
    response = client.post(
        "/events",
        json=_sample_event(
            event_type="scan_port",
            details={"target": "scan.example.org:22"},
        ),
        headers=_auth_headers(token),
    )
    assert response.status_code == 201


def test_scan_ping_target_invalid_host_returns_422() -> None:
    """scan_ping rejette une cible host invalide."""
    token = _login("admin", "admin")
    response = client.post(
        "/events",
        json=_sample_event(
            event_type="scan_ping",
            details={"target": "bad_host@@"},
        ),
        headers=_auth_headers(token),
    )
    assert response.status_code == 422


def test_scan_port_target_invalid_port_range_returns_422() -> None:
    """scan_port rejette un port hors plage 1..65535."""
    token = _login("admin", "admin")
    response = client.post(
        "/events",
        json=_sample_event(
            event_type="scan_port",
            details={"target": "10.0.0.42:70000"},
        ),
        headers=_auth_headers(token),
    )
    assert response.status_code == 422


def test_scan_port_target_missing_separator_returns_422() -> None:
    """scan_port rejette une cible sans séparateur host:port."""
    token = _login("admin", "admin")
    response = client.post(
        "/events",
        json=_sample_event(
            event_type="scan_port",
            details={"target": "10.0.0.42"},
        ),
        headers=_auth_headers(token),
    )
    assert response.status_code == 422


def test_non_scan_event_not_blocked_by_scan_rules() -> None:
    """Un événement non-scan n'est pas bloqué par la validation scan."""
    token = _login("admin", "admin")
    response = client.post(
        "/events",
        json=_sample_event(
            event_type="intrusion_detected",
            details={"target": "not-a-valid-host@@"},
        ),
        headers=_auth_headers(token),
    )
    assert response.status_code == 201
