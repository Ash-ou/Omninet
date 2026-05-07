"""Routes FastAPI pour le module de corrélation."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin
from app.auth.router import get_current_user
from app.correlation.schemas import CorrelatedGroup
from app.correlation.service import get_correlated_groups

router = APIRouter(tags=["correlation"])


@router.get("/groups", response_model=list[CorrelatedGroup])
def list_correlated_groups(
    _user: dict = Depends(get_current_user),
) -> list[CorrelatedGroup]:
    """Liste les groupes d'événements corrélés.

    Args:
        _user: Utilisateur authentifié (injecté par Depends).

    Returns:
        Liste des groupes corrélés.
    """
    return get_correlated_groups()


@router.post("/rebuild", status_code=status.HTTP_202_ACCEPTED)
def rebuild_correlation(
    _admin: dict = Depends(get_current_admin),
) -> dict[str, str]:
    """Force le recalcul de la corrélation depuis les événements existants.

    Args:
        _admin: Admin authentifié (injecté par Depends).

    Returns:
        Message de confirmation.
    """
    # La corrélation est calculée à la volée, pas de cache à invalider
    groups = get_correlated_groups()
    return {
        "status": "rebuilt",
        "groups_found": str(len(groups)),
    }
