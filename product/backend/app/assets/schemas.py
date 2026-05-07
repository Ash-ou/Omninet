"""Schemas Pydantic pour le module Assets."""

from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    """Représentation d'un actif consolidé dans l'inventaire."""

    asset_id: str = Field(..., description="Identifiant unique de l'actif (IP)")
    ip_address: str = Field(..., description="Adresse IP de l'actif")
    hostname: str | None = Field(None, description="Nom d'hôte")
    os_info: str | None = Field(None, description="Système d'exploitation")
    agent_version: str | None = Field(None, description="Version de l'agent")
    last_seen: str = Field(..., description="Dernière activité (heartbeat ou scan)")
    status: str = Field(..., description="Statut de l'actif")
    open_ports: list[int] = Field(default_factory=list, description="Ports ouverts détectés")
    services: list[str] = Field(default_factory=list, description="Services détectés")
    first_discovered: str = Field(..., description="Date de première découverte")
    last_scanned: str | None = Field(None, description="Date du dernier scan")
