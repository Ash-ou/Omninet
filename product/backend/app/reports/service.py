"""Logique métier pour les rapports et KPI (stockage en mémoire)."""

import csv
import io
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

# Imports des services existants pour accéder aux données en mémoire
from app.events import service as events_service
from app.alerts import service as alerts_service
from app.discovery import service as discovery_service
from app.telemetry import service as telemetry_service


# ============================
# Fonctions d'export (CSV/JSON)
# ============================

def export_events_json() -> list[dict[str, Any]]:
    """Exporte tous les événements au format JSON.

    Returns:
        list[dict[str, Any]]: Liste des événements sous forme de dictionnaires.
    """
    with events_service._lock:
        return list(events_service._events)


def export_events_csv() -> str:
    """Exporte tous les événements au format CSV.

    Returns:
        str: Contenu CSV avec headers.
    """
    with events_service._lock:
        events = list(events_service._events)

    if not events:
        return "event_id,endpoint_id,event_type,severity,source,description,details,timestamp,status\n"

    output = io.StringIO()
    fieldnames = [
        "event_id",
        "endpoint_id",
        "event_type",
        "severity",
        "source",
        "description",
        "details",
        "timestamp",
        "status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for event in events:
        # Convertir details en string si présent
        row = event.copy()
        if row.get("details") is not None:
            row["details"] = str(row["details"])
        writer.writerow(row)

    return output.getvalue()


def export_alerts_json() -> list[dict[str, Any]]:
    """Exporte toutes les alertes au format JSON.

    Returns:
        list[dict[str, Any]]: Liste des alertes sous forme de dictionnaires.
    """
    with alerts_service._lock:
        return list(alerts_service._alerts)


def export_alerts_csv() -> str:
    """Exporte toutes les alertes au format CSV.

    Returns:
        str: Contenu CSV avec headers.
    """
    with alerts_service._lock:
        alerts = list(alerts_service._alerts)

    if not alerts:
        return "alert_id,event_id,endpoint_id,severity,title,description,status,created_at,acknowledged_at,acknowledged_by,resolved_at,resolved_by,details\n"

    output = io.StringIO()
    fieldnames = [
        "alert_id",
        "event_id",
        "endpoint_id",
        "severity",
        "title",
        "description",
        "status",
        "created_at",
        "acknowledged_at",
        "acknowledged_by",
        "resolved_at",
        "resolved_by",
        "details",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for alert in alerts:
        # Convertir details en string si présent
        row = alert.copy()
        if row.get("details") is not None:
            row["details"] = str(row["details"])
        writer.writerow(row)

    return output.getvalue()


def export_scans_json() -> list[dict[str, Any]]:
    """Exporte tous les scans au format JSON.

    Returns:
        list[dict[str, Any]]: Liste des scans sous forme de dictionnaires.
    """
    with discovery_service._lock:
        scans = [scan.model_dump() for scan in discovery_service._scans.values()]

    # Convertir les datetimes en ISO format pour JSON
    for scan in scans:
        for key, value in scan.items():
            if isinstance(value, datetime):
                scan[key] = value.isoformat()

    return scans


def export_scans_csv() -> str:
    """Exporte tous les scans au format CSV.

    Returns:
        str: Contenu CSV avec headers.
    """
    with discovery_service._lock:
        scans = [scan.model_dump() for scan in discovery_service._scans.values()]

    if not scans:
        return "scan_id,target,scan_type,status,started_at,completed_at,results,error\n"

    output = io.StringIO()
    fieldnames = [
        "scan_id",
        "target",
        "scan_type",
        "status",
        "started_at",
        "completed_at",
        "results",
        "error",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for scan in scans:
        # Convertir results en string si présent
        row = scan.copy()
        if row.get("results") is not None:
            row["results"] = str(row["results"])
        writer.writerow(row)

    return output.getvalue()


# ============================
# Fonctions KPI pour le dashboard
# ============================

def get_kpi_summary() -> dict:
    """Calcule le résumé des KPI pour le dashboard SOC.

    Returns:
        Dictionnaire contenant les KPI calculés.
    """
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    # Comptages de base
    with events_service._lock:
        total_events = len(events_service._events)
        events_last_24h = sum(
            1 for e in events_service._events
            if datetime.fromisoformat(e["timestamp"]) > last_24h
        )
        # Top 5 sources d'événements
        source_counter = Counter(e.get("source", "unknown") for e in events_service._events)
        top_sources = [
            {"source": source, "count": count}
            for source, count in source_counter.most_common(5)
        ]
        # Timeline des événements (semaine calendaire: Lun→Dim)
        monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        events_timeline = [0] * 7
        for e in events_service._events:
            ts = datetime.fromisoformat(e["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            diff = ts - monday
            if 0 <= diff.days < 7:
                events_timeline[diff.days] += 1
        # Total scans
        total_scans = sum(
            1 for e in events_service._events
            if "scan" in e.get("event_type", "").lower()
        )

    with alerts_service._lock:
        total_alerts = len(alerts_service._alerts)
        # Alertes par sévérité
        severity_counter = Counter(a.get("severity", "unknown") for a in alerts_service._alerts)
        alerts_by_severity = dict(severity_counter)
        # Alertes par statut
        status_counter = Counter(
            a.get("status", "unknown").value if hasattr(a.get("status"), 'value') else a.get("status")
            for a in alerts_service._alerts
        )
        alerts_by_status = dict(status_counter)
        # Timeline des alertes (semaine calendaire: Lun→Dim)
        alerts_timeline = [0] * 7
        for a in alerts_service._alerts:
            raw = a.get("created_at") or a.get("timestamp")
            if raw is None:
                continue
            ts = datetime.fromisoformat(raw) if isinstance(raw, str) else raw
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            diff = ts - monday
            if 0 <= diff.days < 7:
                alerts_timeline[diff.days] += 1

    with telemetry_service._lock:
        total_endpoints = len(telemetry_service._endpoints)

    return {
        "total_events": total_events,
        "total_alerts": total_alerts,
        "total_endpoints": total_endpoints,
        "total_scans": total_scans,
        "alerts_by_severity": alerts_by_severity,
        "alerts_by_status": alerts_by_status,
        "events_last_24h": events_last_24h,
        "events_timeline": events_timeline,
        "alerts_timeline": alerts_timeline,
        "top_sources": top_sources,
    }
