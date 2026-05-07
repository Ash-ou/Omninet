"""Dépendances d'authentification agent pour Omninet."""

import hmac

from fastapi import Header, HTTPException, status

from app.audit.service import log_action
from app.core.config import settings


def get_current_agent(x_agent_token: str | None = Header(default=None)) -> dict[str, str]:
    """Valide l'authentification d'un agent via X-Agent-Token.

    Args:
        x_agent_token: Valeur du header HTTP ``X-Agent-Token``.

    Returns:
        Un dict minimal représentant l'acteur agent.

    Raises:
        HTTPException: 401 si le token est manquant ou invalide.
    """
    if x_agent_token is None:
        log_action(
            username=None,
            action="agent_auth_failed",
            resource="telemetry/heartbeat",
            details={"reason": "missing_token"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent token missing or invalid",
        )

    if not hmac.compare_digest(x_agent_token, settings.AGENT_TOKEN):
        log_action(
            username=None,
            action="agent_auth_failed",
            resource="telemetry/heartbeat",
            details={"reason": "invalid_token"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent token missing or invalid",
        )

    log_action(
        username="agent",
        action="agent_auth_success",
        resource="telemetry/heartbeat",
        details={"agent_id": "unknown"},
    )

    return {"agent_id": "unknown", "actor": "agent"}
