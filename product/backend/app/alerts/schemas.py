"""Schemas Pydantic pour le module d'alertes."""

from typing import Any

from enum import Enum

from pydantic import BaseModel


class AlertStatus(str, Enum):
    """Statuts possibles d'une alerte."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertResponse(BaseModel):
    """Reponse apres creation ou recuperation d'une alerte."""

    alert_id: str
    event_id: str
    endpoint_id: str
    severity: str
    title: str
    description: str
    status: AlertStatus = AlertStatus.NEW
    created_at: str
    acknowledged_at: str | None = None
    acknowledged_by: str | None = None
    resolved_at: str | None = None
    resolved_by: str | None = None
    details: dict[str, Any] | None = None
