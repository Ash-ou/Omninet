"""Routes FastAPI pour le module Assets."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.assets import schemas, service
from app.auth.dependencies import get_current_admin, get_current_user

router = APIRouter()


@router.get(
    "",
    response_model=list[schemas.AssetResponse],
    summary="Lister tous les actifs",
)
def list_assets(
    _current_user: dict = Depends(get_current_user),
) -> list[schemas.AssetResponse]:
    """Retourne l'inventaire consolidé des actifs.

    Accessible aux administrateurs et analystes.

    Args:
        _current_user: Utilisateur authentifié.

    Returns:
        Liste de tous les actifs consolidés.
    """
    return service.build_inventory()


@router.get(
    "/{asset_id}",
    response_model=schemas.AssetResponse,
    summary="Récupérer un actif",
)
def get_asset(
    asset_id: str,
    _current_user: dict = Depends(get_current_user),
) -> schemas.AssetResponse:
    """Retourne les détails d'un actif spécifique.

    Accessible aux administrateurs et analystes.

    Args:
        asset_id: L'identifiant de l'actif (adresse IP).
        _current_user: Utilisateur authentifié.

    Returns:
        Les détails de l'actif.

    Raises:
        HTTPException 404 si l'actif n'existe pas.
    """
    asset = service.get_asset(asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found",
        )
    return asset


@router.post(
    "/rebuild",
    response_model=list[schemas.AssetResponse],
    status_code=status.HTTP_200_OK,
    summary="Reconstruire l'inventaire",
)
def rebuild_inventory(
    _current_user: dict = Depends(get_current_admin),
) -> list[schemas.AssetResponse]:
    """Force la reconstruction de l'inventaire consolidé.

    Réservé aux administrateurs. Réagrège telemetry et discovery.

    Args:
        _current_user: Utilisateur authentifié (admin uniquement).

    Returns:
        Le nouvel inventaire consolidé.
    """
    return service.build_inventory()
