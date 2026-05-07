"""Logique métier pour la télémétrie des endpoints."""

import threading
from datetime import datetime, timezone

from app.telemetry import schemas

# --- Stockage en mémoire thread-safe ---
_endpoints: dict[str, dict] = {}
_lock = threading.Lock()


def register_heartbeat(data: schemas.HeartbeatRequest) -> schemas.HeartbeatResponse:
    """Enregistre un heartbeat reçu d'un endpoint.

    Args:
        data: Les données du heartbeat.

    Returns:
        Une confirmation de réception avec le timestamp UTC.
    """
    now = datetime.now(timezone.utc)

    with _lock:
        _endpoints[data.endpoint_id] = {
            "endpoint_id": data.endpoint_id,
            "hostname": data.hostname,
            "ip_address": data.ip_address,
            "os_info": data.os_info,
            "agent_version": data.agent_version,
            "last_seen": now,
        }

    return schemas.HeartbeatResponse(
        endpoint_id=data.endpoint_id,
        received_at=now.isoformat(),
        status="accepted",
    )


def get_all_endpoints(stale_threshold_seconds: int = 300) -> list[schemas.EndpointStatus]:
    """Retourne la liste de tous les endpoints avec leur statut.

    Un endpoint est considéré "stale" si son dernier heartbeat remonte
    à plus de stale_threshold_seconds.

    Args:
        stale_threshold_seconds: Seuil en secondes pour marquer un endpoint comme stale.

    Returns:
        La liste des endpoints avec leur statut alive ou stale.
    """
    now = datetime.now(timezone.utc)

    with _lock:
        results = []
        for ep in _endpoints.values():
            delta = (now - ep["last_seen"]).total_seconds()
            status = "stale" if delta > stale_threshold_seconds else "alive"
            results.append(
                schemas.EndpointStatus(
                    endpoint_id=ep["endpoint_id"],
                    hostname=ep["hostname"],
                    ip_address=ep["ip_address"],
                    last_seen=ep["last_seen"].isoformat(),
                    status=status,
                    os_info=ep["os_info"],
                    agent_version=ep["agent_version"],
                )
            )
        return results
