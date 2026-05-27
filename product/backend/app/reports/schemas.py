"""Schemas Pydantic pour les rapports et KPI."""

from typing import Any

from pydantic import BaseModel


class KPISummaryResponse(BaseModel):
    """Résumé des KPI pour le dashboard SOC."""

    total_events: int
    total_alerts: int
    total_endpoints: int
    total_scans: int
    alerts_by_severity: dict[str, int]
    alerts_by_status: dict[str, int]
    events_last_24h: int
    events_timeline: list[int]
    alerts_timeline: list[int]
    top_sources: list[dict[str, Any]]
