"""Logique métier pour la corrélation d'événements (stockage en mémoire)."""

import threading
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4

from app.correlation.schemas import CorrelatedGroup
from app.events.service import _events, _lock


def _parse_timestamp(ts: str) -> datetime:
    """Parse un timestamp ISO en datetime."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _get_highest_severity(severities: List[str]) -> str:
    """Retourne la sévérité la plus élevée."""
    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    highest = max(severities, key=lambda s: severity_order.get(s, 0))
    return highest


def correlate_events(
    events: Optional[List[dict]] = None,
    window_minutes: int = 10,
) -> List[CorrelatedGroup]:
    """Groupe les événements répétitifs par (event_type, source, endpoint_id).

    Args:
        events: Liste d'événements à corréler. Si None, utilise tous les événements.
        window_minutes: Fenêtre temporelle glissante en minutes.

    Returns:
        Liste des groupes corrélés avec count >= 2.
    """
    with _lock:
        events_to_correlate = events if events is not None else list(_events)

    if not events_to_correlate:
        return []

    # Trier par timestamp
    sorted_events = sorted(
        events_to_correlate,
        key=lambda e: _parse_timestamp(e["timestamp"]),
    )

    # Grouper par (event_type, source, endpoint_id)
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for event in sorted_events:
        key = (event["event_type"], event["source"], event["endpoint_id"])
        if key not in groups:
            groups[key] = []
        groups[key].append(event)

    # Créer les groupes corrélés
    correlated_groups = []
    window = timedelta(minutes=window_minutes)

    for (event_type, source, endpoint_id), group_events in groups.items():
        if len(group_events) < 2:
            continue

        # Vérifier la fenêtre temporelle
        first = _parse_timestamp(group_events[0]["timestamp"])
        last = _parse_timestamp(group_events[-1]["timestamp"])

        if last - first <= window:
            group_id = str(uuid4())
            event_ids = [e["event_id"] for e in group_events]
            severities = [e["severity"] for e in group_events]

            correlated_group = CorrelatedGroup(
                group_id=group_id,
                event_type=event_type,
                source=source,
                endpoint_id=endpoint_id,
                count=len(group_events),
                first_seen=first,
                last_seen=last,
                severity=_get_highest_severity(severities),
                event_ids=event_ids,
            )
            correlated_groups.append(correlated_group)

    return correlated_groups


def get_correlated_groups() -> List[CorrelatedGroup]:
    """Retourne les groupes corrélés depuis les événements existants.

    Returns:
        Liste des groupes corrélés.
    """
    return correlate_events()
