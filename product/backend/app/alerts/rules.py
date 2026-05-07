"""Moteur de regles de detection d'alertes.

Ce module contient les regles de detection qui analysent
les evenements de securite et determinent si une alerte
doit etre declenchee.
"""

import threading
from datetime import datetime, timedelta, timezone

# Stockage en memoire thread-safe pour l'historique des evenements recents
_recent_events: list[dict] = []
_RECENT_EVENTS_WINDOW = timedelta(minutes=5)
_lock = threading.Lock()

# Ports sensibles pour la regle de scan
_SENSITIVE_PORTS = {22, 3389, 445}


def _clean_old_events() -> None:
    """Nettoie les evenements plus vieux que la fenetre glissante."""
    now = datetime.now(timezone.utc)
    cutoff = now - _RECENT_EVENTS_WINDOW
    global _recent_events
    _recent_events = [
        e for e in _recent_events
        if datetime.fromisoformat(e["timestamp"]) > cutoff
    ]


def record_event(event_data: dict) -> None:
    """Enregistre un evenement dans l'historique recent.

    Args:
        event_data: Donnees de l'evenement avec timestamp.
    """
    with _lock:
        _clean_old_events()
        _recent_events.append(event_data)


def _check_medium_flood(endpoint_id: str) -> bool:
    """Verifie si 3+ events medium du meme endpoint en 5 min.

    Args:
        endpoint_id: Identifiant du endpoint.

    Returns:
        True si condition de flood detectee.
    """
    with _lock:
        _clean_old_events()
        medium_events = [
            e for e in _recent_events
            if e["endpoint_id"] == endpoint_id and e["severity"] == "medium"
        ]
        return len(medium_events) >= 3


def _check_intrusion_type(event_type: str) -> bool:
    """Verifie si le type d'event contient intrusion/exploit/malware.

    Args:
        event_type: Type de l'evenement.

    Returns:
        True si type suspect detecte.
    """
    keywords = ["intrusion", "exploit", "malware"]
    event_type_lower = event_type.lower()
    return any(keyword in event_type_lower for keyword in keywords)


def _check_sensitive_ports(details: dict | None) -> bool:
    """Verifie si un scan detecte des ports sensibles (22, 3389, 445).

    Args:
        details: Details de l'evenement pouvant contenir les ports scannes.

    Returns:
        True si ports sensibles detectes.
    """
    if not details:
        return False

    ports = details.get("ports", [])
    if not ports and "scan_result" in details:
        ports = details["scan_result"].get("ports", [])

    for port in ports:
        if isinstance(port, dict):
            port_num = port.get("port", port.get("number", 0))
        else:
            port_num = port
        if port_num in _SENSITIVE_PORTS:
            return True

    return False


def evaluate_rules(
    event_id: str,
    endpoint_id: str,
    severity: str,
    source: str,
    event_type: str,
    description: str,
    details: dict | None = None,
    timestamp: str | None = None,
) -> list[str]:
    """Evalue toutes les regles d'alerte pour un evenement.

    Args:
        event_id: Identifiant de l'evenement.
        endpoint_id: Identifiant du endpoint.
        severity: Niveau de severite.
        source: Source de l'evenement.
        event_type: Type de l'evenement.
        description: Description de l'evenement.
        details: Details optionnels.
        timestamp: Timestamp de l'evenement.

    Returns:
        Liste des noms de regles declenchees.
    """
    triggered = []

    # Regle 1: severity high/critical -> alerte immediate
    if severity in ("high", "critical"):
        triggered.append("high_critical_severity")

    # Regle 2: event_type contenant intrusion/exploit/malware
    if _check_intrusion_type(event_type):
        triggered.append("suspicious_event_type")

    # Regle 3: scan avec ports sensibles
    if _check_sensitive_ports(details):
        triggered.append("sensitive_port_scan")

    # Regle 4: flood detection (verifie apres enregistrement)
    if severity == "medium" and _check_medium_flood(endpoint_id):
        triggered.append("medium_flood")

    return triggered
