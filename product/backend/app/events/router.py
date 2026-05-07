"""Routes FastAPI pour l'ingestion d'evenements de securite."""

from fastapi import APIRouter, Depends, Query

from app.alerts.service import create_alert_from_event
from app.auth.router import get_current_user
from app.events import schemas
from app.events import service

router = APIRouter()


@router.post("", response_model=schemas.EventResponse, status_code=201)
def create_event(
    body: schemas.EventCreate,
    _user: dict = Depends(get_current_user),
) -> schemas.EventResponse:
    """Ingests a new security event.

    Args:
        body: Event data.
        _user: Authenticated user (injected by dependency).

    Returns:
        The created event with its ID and timestamp.
    """
    event = service.create_event(body)

    # Evaluer les regles d'alerte via le moteur enrichi
    create_alert_from_event(
        event_id=event.event_id,
        endpoint_id=event.endpoint_id,
        severity=event.severity,
        source=event.source,
        description=event.description,
        details=event.details,
        event_type=event.event_type,
        timestamp=event.timestamp,
    )

    return event


@router.get("", response_model=list[schemas.EventResponse])
def list_events(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    severity: str | None = Query(default=None),
    _user: dict = Depends(get_current_user),
) -> list[schemas.EventResponse]:
    """Lists events with pagination and optional severity filter.

    Args:
        limit: Max number of events to return.
        offset: Number of events to skip.
        severity: Optional severity filter.
        _user: Authenticated user (injected by dependency).

    Returns:
        List of matching events.
    """
    if severity:
        return service.get_events_by_severity(severity=severity, limit=limit)
    return service.get_all_events(limit=limit, offset=offset)
