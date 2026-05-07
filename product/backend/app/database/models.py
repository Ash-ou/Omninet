"""Modèles SQLAlchemy pour la persistance des données Omninet."""

import json
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class User(Base):
    """Modèle utilisateur pour l'authentification."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="analyst")

    # Relations
    audit_entries = relationship("AuditEntry", back_populates="user")


class Event(Base):
    """Modèle pour les événements de sécurité."""

    __tablename__ = "events"

    event_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    endpoint_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), default="ingested")

    # Relations
    alerts = relationship("Alert", back_populates="event")


class Alert(Base):
    """Modèle pour les alertes de sécurité."""

    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    event_id = Column(String, ForeignKey("events.event_id"), nullable=True)
    endpoint_id = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="new")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(50), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)

    # Relations
    event = relationship("Event", back_populates="alerts")


class AuditEntry(Base):
    """Modèle pour les entrées d'audit."""

    __tablename__ = "audit_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    username = Column(String(50), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource = Column(String(50), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Clé étrangère vers l'utilisateur (optionnelle)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="audit_entries")


class Endpoint(Base):
    """Modèle pour les endpoints (agents) surveillés."""

    __tablename__ = "endpoints"

    endpoint_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    hostname = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)
    os_info = Column(String(200), nullable=True)
    agent_version = Column(String(50), nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow, index=True)


class Scan(Base):
    """Modèle pour les scans de découverte."""

    __tablename__ = "scans"

    scan_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    target = Column(String(100), nullable=False, index=True)
    scan_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

    # Relations
    results = relationship("ScanResult", back_populates="scan", cascade="all, delete-orphan")


class ScanResult(Base):
    """Modèle pour les résultats de scan."""

    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey("scans.scan_id"), nullable=False, index=True)
    port = Column(Integer, nullable=False)
    protocol = Column(String(10), nullable=False)
    state = Column(String(20), nullable=False)
    service = Column(String(100), nullable=True)
    banner = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)

    # Relations
    scan = relationship("Scan", back_populates="results")


class Asset(Base):
    """Modèle pour les assets (actifs) découverts."""

    __tablename__ = "assets"

    asset_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    ip_address = Column(String(45), nullable=False, index=True)
    hostname = Column(String(100), nullable=True)
    os_info = Column(String(200), nullable=True)
    agent_version = Column(String(50), nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), default="active")
    open_ports = Column(JSON, nullable=True)
    services = Column(JSON, nullable=True)
    first_discovered = Column(DateTime, default=datetime.utcnow)
    last_scanned = Column(DateTime, default=datetime.utcnow)


class CorrelatedGroup(Base):
    """Modèle pour les groupes d'événements corrélés."""

    __tablename__ = "correlated_groups"

    group_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    event_type = Column(String(50), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    endpoint_id = Column(String(50), nullable=False, index=True)
    count = Column(Integer, default=1)
    first_seen = Column(DateTime, default=datetime.utcnow, index=True)
    last_seen = Column(DateTime, default=datetime.utcnow, index=True)
    severity = Column(String(20), nullable=False)
    event_ids = Column(JSON, nullable=True)  # Liste des event_id corrélés
