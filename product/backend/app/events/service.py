"""Logique métier pour l'ingestion d'événements de sécurité (stockage en mémoire)."""

import threading
from datetime import datetime, timezone
from uuid import uuid4

from app.events.schemas import EventCreate, EventResponse

# Stockage en mémoire thread-safe
_events: list[dict] = []
_lock = threading.Lock()


def create_event(data: EventCreate) -> EventResponse:
    """Crée un événement et le stocke en mémoire.

    Args:
        data: Les données de l'événement à créer.

    Returns:
        L'événement créé avec son ID unique et son timestamp.
    """
    event_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    severity = data.severity.value if hasattr(data.severity, "value") else data.severity

    event = {
        "event_id": event_id,
        "endpoint_id": data.endpoint_id,
        "event_type": data.event_type,
        "severity": severity,
        "source": data.source,
        "description": data.description,
        "details": data.details,
        "timestamp": timestamp,
        "status": "ingested",
    }

    with _lock:
        _events.append(event)

    return EventResponse(**event)


def get_all_events(
    limit: int = 100, offset: int = 0
) -> list[EventResponse]:
    """Retourne tous les événements avec pagination (les plus récents d'abord).

    Args:
        limit: Nombre maximum d'événements à retourner.
        offset: Nombre d'événements à sauter.

    Returns:
        La liste paginée des événements, triés par timestamp décroissant.
    """
    with _lock:
        sorted_events = sorted(
            _events, key=lambda e: e["timestamp"], reverse=True
        )
        return [
            EventResponse(**e) for e in sorted_events[offset : offset + limit]
        ]


def get_events_by_severity(
    severity: str, limit: int = 100
) -> list[EventResponse]:
    """Filtre les événements par niveau de sévérité.

    Args:
        severity: Le niveau de sévérité à filtrer.
        limit: Nombre maximum d'événements à retourner.

    Returns:
        La liste des événements correspondant à la sévérité demandée.
    """
    with _lock:
        filtered = [e for e in _events if e["severity"] == severity]
        sorted_events = sorted(
            filtered, key=lambda e: e["timestamp"], reverse=True
        )
        return [EventResponse(**e) for e in sorted_events[:limit]]
