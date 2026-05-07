"""Schemas Pydantic pour le module d'ingestion d'événements."""

from enum import Enum
import ipaddress
import re

from pydantic import BaseModel, Field, model_validator


_FQDN_LABEL_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")


def _is_valid_ip(value: str) -> bool:
    """Vérifie si la valeur est une IPv4 ou IPv6 valide."""
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _is_valid_fqdn(value: str) -> bool:
    """Validation FQDN raisonnable pour l'usage scan simulé."""
    candidate = value.rstrip(".")
    if not candidate or len(candidate) > 253:
        return False

    labels = candidate.split(".")
    if len(labels) < 2:
        return False

    return all(_FQDN_LABEL_RE.match(label) for label in labels)


def _is_valid_host(value: str) -> bool:
    """Host valide: IPv4/IPv6 ou FQDN."""
    return _is_valid_ip(value) or _is_valid_fqdn(value)


class EventSeverity(str, Enum):
    """Niveaux de sévérité d'un événement de sécurité."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCreate(BaseModel):
    """Données d'entrée pour créer un événement."""

    endpoint_id: str = Field(..., min_length=1, max_length=100)
    event_type: str = Field(..., min_length=1, max_length=100)
    severity: EventSeverity
    source: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    details: dict | None = None

    @model_validator(mode="after")
    def validate_scan_target(self) -> "EventCreate":
        """Validation conditionnelle des cibles pour les événements de scan."""
        scan_target_types = {"scan_ping", "scan_service", "scan_port"}
        if self.event_type not in scan_target_types:
            return self

        target = None
        if self.details is not None:
            target = self.details.get("target")

        if not isinstance(target, str) or not target.strip():
            raise ValueError("details.target doit être une chaîne non vide pour les events scan")

        target = target.strip()

        if self.event_type in {"scan_ping", "scan_service"}:
            if not _is_valid_host(target):
                raise ValueError("details.target doit être une IP ou un FQDN valide")
            return self

        # scan_port: format host:port avec host IP/FQDN valide et port 1..65535
        if ":" not in target:
            raise ValueError("details.target doit être au format host:port")

        host, port_str = target.rsplit(":", 1)
        host = host.strip()
        port_str = port_str.strip()

        if not _is_valid_host(host):
            raise ValueError("host invalide dans details.target")

        if not port_str.isdigit():
            raise ValueError("port invalide dans details.target")

        port = int(port_str)
        if port < 1 or port > 65535:
            raise ValueError("port hors plage dans details.target")

        return self


class EventResponse(BaseModel):
    """Réponse après ingestion d'un événement."""

    event_id: str
    endpoint_id: str
    event_type: str
    severity: str
    source: str
    description: str
    details: dict | None = None
    timestamp: str
    status: str = "ingested"
