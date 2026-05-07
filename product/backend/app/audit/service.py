"""Logique métier du module d'audit (stockage en mémoire, thread-safe)."""

import threading
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.audit.schemas import AuditEntry

# Stockage en mémoire thread-safe
_entries: list[dict] = []
_lock = threading.Lock()

_REDACTED_VALUE = "[REDACTED]"
_MAX_STRING_LENGTH = 500
_SENSITIVE_KEY_PARTS = (
    "token",
    "password",
    "secret",
    "authorization",
    "api_key",
    "key",
)


def _is_sensitive_key(key: str) -> bool:
    """Détermine si une clé doit être redacted (case-insensitive)."""
    key_lower = key.lower()
    return any(part in key_lower for part in _SENSITIVE_KEY_PARTS)


def _truncate_string(value: str) -> str:
    """Limite la taille d'une string pour éviter des logs volumineux."""
    if len(value) <= _MAX_STRING_LENGTH:
        return value
    return f"{value[:_MAX_STRING_LENGTH]}...[TRUNCATED]"


def _sanitize_value(value: Any) -> Any:
    """Sanitize récursivement une valeur de details."""
    if isinstance(value, str):
        return _truncate_string(value)

    if isinstance(value, Mapping):
        sanitized_dict: dict[str, Any] = {}
        for key, nested_value in value.items():
            key_as_str = str(key)
            if _is_sensitive_key(key_as_str):
                sanitized_dict[key_as_str] = _REDACTED_VALUE
            else:
                sanitized_dict[key_as_str] = _sanitize_value(nested_value)
        return sanitized_dict

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_sanitize_value(item) for item in value]

    return value


def _sanitize_details(details: dict | None) -> dict | None:
    """Sanitize les détails d'audit avant stockage."""
    if details is None:
        return None
    return _sanitize_value(details)


def log_action(
    username: str | None,
    action: str,
    resource: str,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AuditEntry:
    """Enregistre une action sensible dans le journal d'audit.

    Args:
        username: Nom de l'utilisateur ayant effectué l'action (ou None).
        action: Type d'action (ex: "login", "acknowledge_alert").
        resource: Ressource concernée (ex: "auth", "alerts").
        details: Détails optionnels de l'action (jamais de mot de passe ou token).
        ip_address: Adresse IP de la requête (optionnelle).

    Returns:
        L'entrée d'audit créée.
    """
    entry_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    sanitized_details = _sanitize_details(details)

    entry: dict = {
        "id": entry_id,
        "timestamp": timestamp,
        "username": username,
        "action": action,
        "resource": resource,
        "details": sanitized_details,
        "ip_address": ip_address,
    }

    with _lock:
        _entries.append(entry)

    return AuditEntry(**entry)


def get_all_entries(limit: int = 200) -> list[AuditEntry]:
    """Récupère toutes les entrées d'audit, les plus récentes d'abord.

    Args:
        limit: Nombre maximum d'entrées à retourner.

    Returns:
        Liste des entrées d'audit triées par ordre décroissant.
    """
    with _lock:
        sorted_entries = sorted(
            _entries, key=lambda e: e["timestamp"], reverse=True
        )
        return [AuditEntry(**e) for e in sorted_entries[:limit]]


def get_entries_by_user(username: str, limit: int = 100) -> list[AuditEntry]:
    """Récupère les entrées d'audit pour un utilisateur donné.

    Args:
        username: Nom de l'utilisateur à filtrer.
        limit: Nombre maximum d'entrées à retourner.

    Returns:
        Liste des entrées d'audit de l'utilisateur, les plus récentes d'abord.
    """
    with _lock:
        filtered = [e for e in _entries if e["username"] == username]
        sorted_entries = sorted(
            filtered, key=lambda e: e["timestamp"], reverse=True
        )
        return [AuditEntry(**e) for e in sorted_entries[:limit]]


def get_entries_by_action(action: str, limit: int = 100) -> list[AuditEntry]:
    """Récupère les entrées d'audit pour une action donnée.

    Args:
        action: Type d'action à filtrer.
        limit: Nombre maximum d'entrées à retourner.

    Returns:
        Liste des entrées d'audit pour l'action, les plus récentes d'abord.
    """
    with _lock:
        filtered = [e for e in _entries if e["action"] == action]
        sorted_entries = sorted(
            filtered, key=lambda e: e["timestamp"], reverse=True
        )
        return [AuditEntry(**e) for e in sorted_entries[:limit]]
