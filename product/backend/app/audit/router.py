"""Routes FastAPI pour le module d'audit."""

from fastapi import APIRouter, Depends, Query, status

from app.audit import schemas
from app.audit import service
from app.auth.dependencies import get_current_admin

router = APIRouter()


@router.get("", response_model=list[schemas.AuditEntry])
def list_audit_entries(
    limit: int = Query(default=200, ge=1, le=1000),
    username: str | None = Query(default=None),
    action: str | None = Query(default=None),
    _admin: dict = Depends(get_current_admin),
) -> list[schemas.AuditEntry]:
    """Liste les entrées d'audit (admin uniquement).

    Args:
        limit: Nombre maximum d'entrées à retourner.
        username: Filtre optionnel par nom d'utilisateur.
        action: Filtre optionnel par type d'action.
        _admin: Utilisateur admin authentifié.

    Returns:
        Liste des entrées d'audit correspondantes.
    """
    if username:
        return service.get_entries_by_user(username=username, limit=limit)
    if action:
        return service.get_entries_by_action(action=action, limit=limit)
    return service.get_all_entries(limit=limit)
