"""Logique metier du module d'alertes (stockage en memoire).

Le moteur de regles de detection est dans le module rules.py.
Ce module gere le cycle de vie des alertes (creation, consultation,
reconnaissance, resolution).
"""

import threading
from datetime import datetime, timezone
from uuid import uuid4

from app.alerts.rules import evaluate_rules, record_event, _recent_events
from app.alerts.schemas import AlertResponse, AlertStatus

# Stockage en memoire thread-safe
_alerts: list[dict] = []
_lock = threading.Lock()


def create_alert_from_event(
    event_id: str,
    endpoint_id: str,
    severity: str,
    source: str,
    description: str,
    details: dict | None = None,
    event_type: str = "unknown",
    timestamp: str | None = None,
) -> AlertResponse | None:
    """Cree une alerte a partir d'un evenement de securite.

    Args:
        event_id: Identifiant de l'evenement source.
        endpoint_id: Identifiant du endpoint concerne.
        severity: Niveau de severite.
        source: Source de l'evenement.
        description: Description de l'evenement.
        details: Details optionnels.
        event_type: Type de l'evenement.
        timestamp: Timestamp de l'evenement.

    Returns:
        L'alerte creee ou None si aucune regle declenchee.
    """
    # Enregistrer l'evenement pour la detection de flood
    event_data = {
        "event_id": event_id,
        "endpoint_id": endpoint_id,
        "severity": severity,
        "event_type": event_type,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
    record_event(event_data)

    # Evaluer les regles
    triggered_rules = evaluate_rules(
        event_id=event_id,
        endpoint_id=endpoint_id,
        severity=severity,
        source=source,
        event_type=event_type,
        description=description,
        details=details,
        timestamp=timestamp,
    )

    # Si aucune regle declenchee, pas d'alerte
    if not triggered_rules:
        return None

    # Determiner le titre et la severite de l'alerte
    if "medium_flood" in triggered_rules:
        alert_severity = "medium"
        title = f"[FLOOD] Multiple medium events from {endpoint_id}"
    elif "suspicious_event_type" in triggered_rules:
        alert_severity = severity
        title = f"[{severity.upper()}] Suspicious: {event_type}"
    elif "sensitive_port_scan" in triggered_rules:
        alert_severity = "high"
        title = f"[HIGH] Sensitive port scan detected"
    else:
        alert_severity = severity
        title = f"[{severity.upper()}] {source}"

    alert_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    alert: dict = {
        "alert_id": alert_id,
        "event_id": event_id,
        "endpoint_id": endpoint_id,
        "severity": alert_severity,
        "title": title,
        "description": description,
        "status": AlertStatus.NEW,
        "created_at": now,
        "acknowledged_at": None,
        "acknowledged_by": None,
        "resolved_at": None,
        "resolved_by": None,
        "details": {
            **(details or {}),
            "triggered_rules": triggered_rules,
        },
    }

    with _lock:
        _alerts.append(alert)

    return AlertResponse(**alert)


def get_all_alerts(status: str | None = None, limit: int = 100) -> list[AlertResponse]:
    """Recupere toutes les alertes avec filtre optionnel par statut.

    Args:
        status: Filtre par statut (new, acknowledged, resolved).
        limit: Nombre maximum d'alertes a retourner.

    Returns:
        Liste des alertes correspondantes.
    """
    with _lock:
        filtered = _alerts
        if status:
            filtered = [a for a in _alerts if a["status"].value == status]
        return [AlertResponse(**a) for a in filtered[:limit]]


def acknowledge_alert(alert_id: str, username: str) -> AlertResponse | None:
    """Marque une alerte comme reconnue par un utilisateur.

    Args:
        alert_id: Identifiant de l'alerte.
        username: Nom de l'utilisateur qui reconnait l'alerte.

    Returns:
        L'alerte mise a jour ou None si non trouvee.
    """
    now = datetime.now(timezone.utc).isoformat()

    with _lock:
        for alert in _alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = AlertStatus.ACKNOWLEDGED
                alert["acknowledged_at"] = now
                alert["acknowledged_by"] = username
                return AlertResponse(**alert)

    return None


def resolve_alert(alert_id: str, username: str) -> AlertResponse | None:
    """Marque une alerte comme résolue par un utilisateur.

    Args:
        alert_id: Identifiant de l'alerte.
        username: Nom de l'utilisateur qui résout l'alerte.

    Returns:
        L'alerte mise à jour ou None si non trouvée.
    """
    now = datetime.now(timezone.utc).isoformat()

    with _lock:
        for alert in _alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = AlertStatus.RESOLVED
                alert["resolved_at"] = now
                alert["resolved_by"] = username
                return AlertResponse(**alert)

    return None
