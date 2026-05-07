"""Routes FastAPI pour le module d'alertes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.alerts import schemas
from app.alerts import service
from app.audit.service import log_action
from app.auth.dependencies import get_current_admin
from app.auth.router import get_current_user

router = APIRouter()


@router.get("", response_model=list[schemas.AlertResponse])
def list_alerts(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=1000),
    _user: dict = Depends(get_current_user),
) -> list[schemas.AlertResponse]:
    """Liste les alertes avec filtre optionnel par statut.

    Args:
        status_filter: Filtre par statut (new, acknowledged, resolved).
        limit: Nombre maximum d'alertes.
        _user: Utilisateur authentifie.

    Returns:
        Liste des alertes correspondantes.
    """
    return service.get_all_alerts(status=status_filter, limit=limit)


@router.post("/{alert_id}/acknowledge", response_model=schemas.AlertResponse)
def acknowledge_alert(
    alert_id: str,
    admin: dict = Depends(get_current_admin),
) -> schemas.AlertResponse:
    """Reconnait une alerte (admin uniquement).

    Args:
        alert_id: Identifiant de l'alerte.
        admin: Utilisateur admin authentifie.

    Returns:
        L'alerte mise a jour avec statut acknowledged.

    Raises:
        HTTPException 404 si l'alerte n'existe pas.
    """
    result = service.acknowledge_alert(alert_id=alert_id, username=admin["username"])
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte introuvable",
        )
    log_action(
        username=admin["username"],
        action="acknowledge_alert",
        resource="alerts",
        details={"alert_id": alert_id},
    )
    return result


@router.post("/{alert_id}/resolve", response_model=schemas.AlertResponse)
def resolve_alert(
    alert_id: str,
    admin: dict = Depends(get_current_admin),
) -> schemas.AlertResponse:
    """Résout une alerte (admin uniquement).

    Args:
        alert_id: Identifiant de l'alerte.
        admin: Utilisateur admin authentifié.

    Returns:
        L'alerte mise à jour avec statut resolved.

    Raises:
        HTTPException 404 si l'alerte n'existe pas.
    """
    result = service.resolve_alert(alert_id=alert_id, username=admin["username"])
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte introuvable",
        )
    log_action(
        username=admin["username"],
        action="resolve_alert",
        resource="alerts",
        details={"alert_id": alert_id},
    )
    return result
