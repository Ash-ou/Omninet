"""Schemas Pydantic pour le module de corrélation."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class CorrelatedGroup(BaseModel):
    """Groupe d'événements corrélés."""

    group_id: str = Field(..., description="Identifiant unique du groupe")
    event_type: str = Field(..., description="Type d'événement")
    source: str = Field(..., description="Source de l'événement")
    endpoint_id: str = Field(..., description="ID de l'endpoint")
    count: int = Field(..., ge=1, description="Nombre d'événements dans le groupe")
    first_seen: datetime = Field(..., description="Premier événement vu")
    last_seen: datetime = Field(..., description="Dernier événement vu")
    severity: str = Field(..., description="Sévérité la plus élevée du groupe")
    event_ids: List[str] = Field(..., description="Liste des IDs d'événements du groupe")
