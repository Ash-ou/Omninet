"""Service Discovery — exécution de scans réseau non destructifs."""

from __future__ import annotations

import socket
import subprocess
import threading
from datetime import datetime, timezone

from app.discovery.schemas import ScanRequest, ScanResponse, ScanResult, ScanStatus, ScanType

# --- Stockage mémoire thread-safe ---
_scans: dict[str, ScanResponse] = {}
_lock = threading.Lock()

# Ports communs pour les scans port/service
COMMON_PORTS = [22, 80, 443, 8080, 3306, 5432, 8443]


def launch_scan(request: ScanRequest) -> ScanResponse:
    """Lance un scan réseau en arrière-plan.

    Args:
        request: La requête de scan validée.

    Returns:
        Un ScanResponse avec status pending/running.
    """
    scan = ScanResponse(
        target=request.target,
        scan_type=request.scan_type,
        status=ScanStatus.PENDING,
    )

    with _lock:
        _scans[scan.scan_id] = scan

    # Exécution en thread pour ne pas bloquer l'API
    thread = threading.Thread(
        target=_execute_scan,
        args=(scan.scan_id, request),
        daemon=True,
    )
    thread.start()

    # Retour immédiat avec le scan en cours
    with _lock:
        current = _scans[scan.scan_id]
    return current


def get_scan(scan_id: str) -> ScanResponse | None:
    """Récupère un scan par son ID.

    Args:
        scan_id: L'identifiant du scan.

    Returns:
        Le ScanResponse ou None si inexistant.
    """
    with _lock:
        scan = _scans.get(scan_id)
        if scan is None:
            return None
        # Retourner une copie pour éviter les modifications concurrentes
        return ScanResponse(**scan.model_dump())


def get_all_scans() -> list[ScanResponse]:
    """Récupère tous les scans.

    Returns:
        Liste de tous les ScanResponse.
    """
    with _lock:
        return [ScanResponse(**s.model_dump()) for s in _scans.values()]


def get_scan_results(scan_id: str) -> ScanResponse | None:
    """Récupère les résultats d'un scan par son ID.

    Args:
        scan_id: L'identifiant du scan.

    Returns:
        Le ScanResponse ou None si inexistant.
    """
    return get_scan(scan_id)


def _execute_scan(scan_id: str, request: ScanRequest) -> None:
    """Exécute le scan en arrière-plan et met à jour le statut.

    Args:
        scan_id: L'identifiant du scan.
        request: La requête de scan.
    """
    with _lock:
        scan = _scans[scan_id]
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)

    try:
        if request.scan_type == ScanType.PING:
            results = _run_ping(request.target)
        elif request.scan_type == ScanType.PORT:
            results = _run_port_scan(request.target, request.ports)
        elif request.scan_type == ScanType.SERVICE:
            results = _run_service_scan(request.target, request.ports)
        else:
            raise ValueError(f"Unknown scan type: {request.scan_type}")

        with _lock:
            scan = _scans[scan_id]
            scan.results = results
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.now(timezone.utc)

    except Exception as exc:  # noqa: BLE001
        with _lock:
            scan = _scans[scan_id]
            scan.status = ScanStatus.FAILED
            scan.error = str(exc)
            scan.completed_at = datetime.now(timezone.utc)


def _run_ping(target: str) -> list[ScanResult]:
    """Exécute un ping non destructif.

    Args:
        target: La cible du ping.

    Returns:
        Liste de ScanResult avec le RTT.

    Raises:
        RuntimeError: Si le ping échoue.
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", target],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            # Extraire le RTT depuis la sortie ping
            latency = _extract_rtt(result.stdout)
            return [ScanResult(state="open", latency_ms=latency)]
        else:
            return [ScanResult(state="closed")]

    except subprocess.TimeoutExpired:
        return [ScanResult(state="filtered")]


def _extract_rtt(output: str) -> float | None:
    """Extrait le temps de réponse RTT depuis la sortie de ping.

    Args:
        output: La sortie stdout de la commande ping.

    Returns:
        Le RTT en millisecondes ou None.
    """
    # Chercher le pattern "time=X.XX ms" ou "time=X ms"
    import re

    match = re.search(r"time[=<](\d+\.?\d*)\s*ms", output)
    if match:
        return float(match.group(1))
    return None


def _run_port_scan(target: str, ports: list[int] | None) -> list[ScanResult]:
    """Scanne les ports d'une cible.

    Args:
        target: La cible du scan.
        ports: Liste de ports à scanner (ou ports communs si None).

    Returns:
        Liste de ScanResult par port.
    """
    ports_to_scan = ports or COMMON_PORTS
    results: list[ScanResult] = []

    for port in ports_to_scan:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            conn_result = sock.connect_ex((target, port))
            if conn_result == 0:
                results.append(ScanResult(port=port, protocol="tcp", state="open"))
            else:
                results.append(ScanResult(port=port, protocol="tcp", state="closed"))
            sock.close()
        except (socket.error, OSError):
            results.append(ScanResult(port=port, protocol="tcp", state="filtered"))

    return results


def _run_service_scan(target: str, ports: list[int] | None) -> list[ScanResult]:
    """Tente d'identifier les services sur les ports ouverts.

    Args:
        target: La cible du scan.
        ports: Liste de ports à scanner (ou ports communs si None).

    Returns:
        Liste de ScanResult avec service et banner si disponible.
    """
    ports_to_scan = ports or COMMON_PORTS
    results: list[ScanResult] = []

    for port in ports_to_scan:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            conn_result = sock.connect_ex((target, port))

            if conn_result == 0:
                # Tenter de lire un banner
                banner = _grab_banner(sock)
                service = _guess_service(port, banner)
                results.append(
                    ScanResult(
                        port=port,
                        protocol="tcp",
                        state="open",
                        service=service,
                        banner=banner,
                    )
                )
            else:
                results.append(ScanResult(port=port, protocol="tcp", state="closed"))

            sock.close()
        except (socket.error, OSError):
            results.append(ScanResult(port=port, protocol="tcp", state="filtered"))

    return results


def _grab_banner(sock: socket.socket) -> str | None:
    """Tente de lire un banner depuis un socket ouvert.

    Args:
        sock: Le socket connecté.

    Returns:
        Le banner lu ou None.
    """
    try:
        sock.settimeout(3)
        data = sock.recv(1024)
        if data:
            return data.decode("utf-8", errors="replace").strip()
    except (socket.timeout, socket.error, OSError):
        pass
    return None


def _guess_service(port: int, banner: str | None) -> str:
    """Devine le service basé sur le port et le banner.

    Args:
        port: Le numéro de port.
        banner: Le banner lu (optionnel).

    Returns:
        Le nom du service deviné.
    """
    well_known: dict[int, str] = {
        22: "ssh",
        80: "http",
        443: "https",
        3306: "mysql",
        5432: "postgresql",
        8080: "http-proxy",
        8443: "https-alt",
    }

    if banner:
        banner_lower = banner.lower()
        if "ssh" in banner_lower:
            return "ssh"
        if "http" in banner_lower or "html" in banner_lower:
            return "http"
        if "mysql" in banner_lower:
            return "mysql"
        if "postgres" in banner_lower:
            return "postgresql"

    return well_known.get(port, "unknown")
