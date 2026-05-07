"""Routes FastAPI pour la télémétrie des endpoints."""

from fastapi import APIRouter, Depends

from app.auth.agent_dependencies import get_current_agent
from app.auth.router import get_current_user
from app.telemetry import schemas
from app.telemetry.service import get_all_endpoints, register_heartbeat

router = APIRouter()


@router.post("/heartbeat", response_model=schemas.HeartbeatResponse)
def heartbeat(
    body: schemas.HeartbeatRequest,
    _agent: dict[str, str] = Depends(get_current_agent),
) -> schemas.HeartbeatResponse:
    """Reçoit un heartbeat d'un endpoint.

    Args:
        body: Les données du heartbeat.
        _agent: L'agent authentifié (injecté par la dépendance).

    Returns:
        Une confirmation de réception.
    """
    return register_heartbeat(body)


@router.get("/endpoints", response_model=list[schemas.EndpointStatus])
def list_endpoints(
    _user: dict = Depends(get_current_user),
) -> list[schemas.EndpointStatus]:
    """Liste tous les endpoints enregistrés avec leur statut.

    Args:
        _user: L'utilisateur authentifié (injecté par la dépendance).

    Returns:
        La liste des endpoints avec leur statut alive/stale.
    """
    return get_all_endpoints()
