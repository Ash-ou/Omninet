"""Routes FastAPI pour le module Discovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin, get_current_user
from app.discovery import schemas, service

router = APIRouter()


@router.post(
    "/scans",
    response_model=schemas.ScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lancer un scan réseau",
)
def create_scan(
    request: schemas.ScanRequest,
    _current_user: dict = Depends(get_current_admin),
) -> schemas.ScanResponse:
    """Lance un scan réseau non destructif.

    Réservé aux administrateurs.

    Args:
        request: La requête de scan (target, scan_type, ports).
        _current_user: Utilisateur authentifié (admin uniquement).

    Returns:
        Les informations du scan lancé.
    """
    return service.launch_scan(request)


@router.get(
    "/scans",
    response_model=list[schemas.ScanResponse],
    summary="Lister tous les scans",
)
def list_scans(
    _current_user: dict = Depends(get_current_user),
) -> list[schemas.ScanResponse]:
    """Retourne la liste de tous les scans.

    Accessible aux administrateurs et analystes.

    Args:
        _current_user: Utilisateur authentifié.

    Returns:
        Liste de tous les scans.
    """
    return service.get_all_scans()


@router.get(
    "/scans/{scan_id}/results",
    response_model=schemas.ScanResultsResponse,
    summary="Récupérer les résultats d'un scan",
)
def get_scan_results(
    scan_id: str,
    _current_user: dict = Depends(get_current_user),
) -> schemas.ScanResultsResponse:
    """Retourne les résultats détaillés d'un scan spécifique.

    Accessible aux administrateurs et analystes.
    Si le scan n'est pas terminé, retourne le statut et les résultats partiels.

    Args:
        scan_id: L'identifiant du scan.
        _current_user: Utilisateur authentifié.

    Returns:
        Les résultats du scan avec statut.

    Raises:
        HTTPException 404 si le scan n'existe pas.
    """
    scan = service.get_scan_results(scan_id)
    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan '{scan_id}' not found",
        )
    return schemas.ScanResultsResponse(
        scan_id=scan.scan_id,
        target=scan.target,
        scan_type=scan.scan_type,
        status=scan.status,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        results=scan.results,
        error=scan.error,
    )


@router.get(
    "/scans/{scan_id}",
    response_model=schemas.ScanResponse,
    summary="Récupérer un scan",
)
def get_scan(
    scan_id: str,
    _current_user: dict = Depends(get_current_user),
) -> schemas.ScanResponse:
    """Retourne les détails d'un scan spécifique.

    Accessible aux administrateurs et analystes.

    Args:
        scan_id: L'identifiant du scan.
        _current_user: Utilisateur authentifié.

    Returns:
        Les détails du scan.

    Raises:
        HTTPException 404 si le scan n'existe pas.
    """
    scan = service.get_scan(scan_id)
    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan '{scan_id}' not found",
        )
    return scan
