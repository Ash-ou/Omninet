"""Router pour le module Reports.

Fournit les endpoints d'export des événements, alertes et scans
aux formats JSON et CSV, ainsi que les KPI pour le dashboard.
"""

import csv
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response

from app.auth.router import get_current_user
from app.reports import service
from app.reports.schemas import KPISummaryResponse

router = APIRouter(tags=["reports"])


def _get_current_user_with_reports_access(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Vérifie que l'utilisateur a accès aux rapports (admin ou analyst)."""
    return current_user


@router.get("/events")
async def get_events_report(
    format: str = Query(..., description="Format d'export: json ou csv"),
    _user: dict[str, Any] = Depends(_get_current_user_with_reports_access),
) -> Response:
    """Exporte les événements au format demandé.

    Args:
        format: Format d'export (json ou csv).

    Returns:
        Response: Réponse avec le contenu exporté.
    """
    if format not in ("json", "csv"):
        return JSONResponse(
            status_code=422,
            content={"detail": "Format invalide. Utilisez 'json' ou 'csv'."},
        )

    if format == "json":
        data = service.export_events_json()
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": "attachment; filename=events.json",
                "Content-Type": "application/json",
            },
        )

    csv_content = service.export_events_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=events.csv",
            "Content-Type": "text/csv",
        },
    )


@router.get("/alerts")
async def get_alerts_report(
    format: str = Query(..., description="Format d'export: json ou csv"),
    _user: dict[str, Any] = Depends(_get_current_user_with_reports_access),
) -> Response:
    """Exporte les alertes au format demandé.

    Args:
        format: Format d'export (json ou csv).

    Returns:
        Response: Réponse avec le contenu exporté.
    """
    if format not in ("json", "csv"):
        return JSONResponse(
            status_code=422,
            content={"detail": "Format invalide. Utilisez 'json' ou 'csv'."},
        )

    if format == "json":
        data = service.export_alerts_json()
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": "attachment; filename=alerts.json",
                "Content-Type": "application/json",
            },
        )

    csv_content = service.export_alerts_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=alerts.csv",
            "Content-Type": "text/csv",
        },
    )


@router.get("/scans")
async def get_scans_report(
    format: str = Query(..., description="Format d'export: json ou csv"),
    _user: dict[str, Any] = Depends(_get_current_user_with_reports_access),
) -> Response:
    """Exporte les scans au format demandé.

    Args:
        format: Format d'export (json ou csv).

    Returns:
        Response: Réponse avec le contenu exporté.
    """
    if format not in ("json", "csv"):
        return JSONResponse(
            status_code=422,
            content={"detail": "Format invalide. Utilisez 'json' ou 'csv'."},
        )

    if format == "json":
        data = service.export_scans_json()
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": "attachment; filename=scans.json",
                "Content-Type": "application/json",
            },
        )

    csv_content = service.export_scans_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=scans.csv",
            "Content-Type": "text/csv",
        },
    )


@router.get(
    "/kpi",
    response_model=KPISummaryResponse,
    status_code=200,
    summary="Récupérer les KPI du dashboard SOC",
    description="Retourne un résumé des indicateurs clés de performance (KPI) pour le dashboard SOC.",
)
async def get_kpi(current_user: dict = Depends(get_current_user)) -> KPISummaryResponse:
    """Endpoint pour récupérer les KPI du dashboard.

    Args:
        current_user: Utilisateur authentifié (injecté par dépendance).

    Returns:
        KPISummaryResponse contenant les KPI calculés.
    """
    kpi_data = service.get_kpi_summary()
    return KPISummaryResponse(**kpi_data)
