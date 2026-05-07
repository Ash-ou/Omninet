"""Schemas Pydantic pour le module d'audit."""

from pydantic import BaseModel


class AuditEntry(BaseModel):
    """Entrée d'audit représentant une action sensible tracée."""

    id: str
    timestamp: str
    username: str | None = None
    action: str
    resource: str
    details: dict | None = None
    ip_address: str | None = None
