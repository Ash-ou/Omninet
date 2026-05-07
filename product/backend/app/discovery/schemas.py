"""Schemas Pydantic pour le module Discovery."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator


class ScanType(str, Enum):
    """Types de scan supportés."""

    PING = "ping"
    PORT = "port"
    SERVICE = "service"


class ScanStatus(str, Enum):
    """Statuts possibles d'un scan."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanRequest(BaseModel):
    """Requête de lancement de scan."""

    target: str = Field(..., min_length=1, max_length=253)
    scan_type: ScanType
    ports: list[int] | None = Field(default=None, max_length=100)

    @field_validator("target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        """Valide que la cible est une IP ou un FQDN sûr."""
        value = value.strip()

        # IPv4
        ipv4_pattern = re.compile(
            r"^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$"
        )
        # IPv6 (forme complète ou compressée)
        ipv6_pattern = re.compile(r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$")
        # FQDN
        fqdn_pattern = re.compile(
            r"^(?=.{1,253}$)"
            r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+"
            r"[a-zA-Z]{2,}$"
        )

        if ipv4_pattern.match(value) or ipv6_pattern.match(value) or fqdn_pattern.match(value):
            return value

        raise ValueError(
            f"Target '{value}' is not a valid IPv4, IPv6, or FQDN"
        )

    @field_validator("ports")
    @classmethod
    def validate_ports(cls, value: list[int] | None) -> list[int] | None:
        """Valide que les ports sont dans la plage valide."""
        if value is None:
            return None
        for port in value:
            if port < 1 or port > 65535:
                raise ValueError(f"Port {port} is out of range (1-65535)")
        return value


class ScanState(str, Enum):
    """États possibles d'un port/service scanné."""

    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"


class ScanResult(BaseModel):
    """Résultat individuel d'un scan."""

    port: int | None = None
    protocol: str = "tcp"
    state: str = ""
    service: str | None = None
    banner: str | None = None
    latency_ms: float | None = None


class ScanResultsResponse(BaseModel):
    """Réponse dédiée pour les résultats d'un scan."""

    scan_id: str
    target: str
    scan_type: ScanType
    status: ScanStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    results: list[ScanResult] = Field(default_factory=list)
    error: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def results_count(self) -> int:
        """Nombre de résultats."""
        return len(self.results)


class ScanResponse(BaseModel):
    """Réponse contenant les informations d'un scan."""

    scan_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    target: str
    scan_type: ScanType
    status: ScanStatus = ScanStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    results: list[ScanResult] = Field(default_factory=list)
    error: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def results_count(self) -> int:
        """Nombre de résultats."""
        return len(self.results)
