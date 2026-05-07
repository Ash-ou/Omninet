"""Service Assets — consolidation de l'inventaire depuis telemetry et discovery."""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from app.assets.schemas import AssetResponse
from app.discovery import schemas as discovery_schemas
from app.discovery import service as discovery_service
from app.telemetry import service as telemetry_service


# --- Stockage mémoire thread-safe pour l'inventaire ---
_inventory: dict[str, AssetResponse] = {}
_lock = threading.Lock()


def build_inventory() -> list[AssetResponse]:
    """Construit l'inventaire consolidé des actifs.

    Agrège les données de télémétrie (heartbeats) et de discovery (scans).
    Un asset = une IP unique. Les données sont fusionnées :
    - last_seen = max(heartbeat, scan)
    - open_ports = union des ports ouverts détectés
    - services = union des services détectés

    Returns:
        La liste complète des AssetResponse consolidés.
    """
    global _inventory  # noqa: PLW0603

    endpoints = telemetry_service.get_all_endpoints()
    scans = discovery_service.get_all_scans()

    new_inventory: dict[str, dict] = {}

    # --- Phase 1 : intégrer les endpoints telemetry ---
    for ep in endpoints:
        ip = ep.ip_address
        if ip not in new_inventory:
            new_inventory[ip] = {
                "ip_address": ip,
                "hostname": ep.hostname,
                "os_info": ep.os_info,
                "agent_version": ep.agent_version,
                "last_seen": ep.last_seen,
                "status": ep.status,
                "open_ports": set(),
                "services": set(),
                "first_discovered": ep.last_seen,
                "last_scanned": None,
            }
        else:
            existing = new_inventory[ip]
            # Mettre à jour avec les données les plus récentes
            if _is_newer(ep.last_seen, existing["last_seen"]):
                existing["hostname"] = ep.hostname or existing["hostname"]
                existing["os_info"] = ep.os_info or existing["os_info"]
                existing["agent_version"] = ep.agent_version or existing["agent_version"]
                existing["last_seen"] = ep.last_seen
                existing["status"] = ep.status
                existing["first_discovered"] = min(
                    existing["first_discovered"], ep.last_seen
                )

    # --- Phase 2 : intégrer les résultats de scans ---
    for scan in scans:
        if scan.status != discovery_schemas.ScanStatus.COMPLETED:
            continue

        ip = scan.target
        scan_time = (
            scan.completed_at.isoformat()
            if scan.completed_at
            else datetime.now(timezone.utc).isoformat()
        )

        if ip not in new_inventory:
            new_inventory[ip] = {
                "ip_address": ip,
                "hostname": None,
                "os_info": None,
                "agent_version": None,
                "last_seen": scan_time,
                "status": "discovered",
                "open_ports": set(),
                "services": set(),
                "first_discovered": scan_time,
                "last_scanned": scan_time,
            }
        else:
            existing = new_inventory[ip]
            existing["last_scanned"] = scan_time
            # last_seen = max(heartbeat, scan)
            if _is_newer(scan_time, existing["last_seen"]):
                existing["last_seen"] = scan_time
            existing["first_discovered"] = min(
                existing["first_discovered"], scan_time
            )

        # Extraire ports ouverts et services
        for result in scan.results:
            if result.state == "open":
                if result.port is not None:
                    new_inventory[ip]["open_ports"].add(result.port)
                if result.service:
                    new_inventory[ip]["services"].add(result.service)

    # --- Phase 3 : convertir en AssetResponse ---
    assets = []
    for ip, data in new_inventory.items():
        asset = AssetResponse(
            asset_id=ip,
            ip_address=data["ip_address"],
            hostname=data["hostname"],
            os_info=data["os_info"],
            agent_version=data["agent_version"],
            last_seen=data["last_seen"],
            status=data["status"],
            open_ports=sorted(data["open_ports"]),
            services=sorted(data["services"]),
            first_discovered=data["first_discovered"],
            last_scanned=data["last_scanned"],
        )
        assets.append(asset)

    # Trier par IP pour un ordre stable
    assets.sort(key=lambda a: a.ip_address)

    with _lock:
        _inventory = {a.asset_id: a for a in assets}

    return assets


def get_asset(asset_id: str) -> AssetResponse | None:
    """Récupère un asset par son ID.

    Args:
        asset_id: L'identifiant de l'actif (adresse IP).

    Returns:
        L'AssetResponse ou None si inexistant.
    """
    with _lock:
        return _inventory.get(asset_id)


def _is_newer(timestamp_a: str, timestamp_b: str) -> bool:
    """Compare deux timestamps ISO et retourne True si A est plus récent que B.

    Args:
        timestamp_a: Premier timestamp ISO.
        timestamp_b: Second timestamp ISO.

    Returns:
        True si A est plus récent.
    """
    try:
        dt_a = datetime.fromisoformat(timestamp_a)
        dt_b = datetime.fromisoformat(timestamp_b)
        return dt_a > dt_b
    except (ValueError, TypeError):
        return timestamp_a > timestamp_b
