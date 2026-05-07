"""Schemas Pydantic pour le module de télémétrie."""

from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    """Requête de heartbeat envoyée par un endpoint."""

    endpoint_id: str = Field(..., min_length=1, max_length=100, description="Identifiant unique de l'endpoint")
    hostname: str = Field(..., min_length=1, max_length=255, description="Nom d'hôte de la machine")
    ip_address: str = Field(..., min_length=7, max_length=45, description="Adresse IP de l'endpoint (IPv6 max)")
    os_info: str | None = Field(None, max_length=255, description="Informations sur le système d'exploitation")
    agent_version: str | None = Field(None, max_length=50, description="Version de l'agent Omninet")


class HeartbeatResponse(BaseModel):
    """Réponse confirmant la réception d'un heartbeat."""

    endpoint_id: str
    received_at: str
    status: str = "accepted"


class EndpointStatus(BaseModel):
    """Statut d'un endpoint tel que vu par le système de télémétrie."""

    endpoint_id: str
    hostname: str
    ip_address: str
    last_seen: str
    status: str = Field(..., pattern=r"^(alive|stale)$")
    os_info: str | None = None
    agent_version: str | None = None
