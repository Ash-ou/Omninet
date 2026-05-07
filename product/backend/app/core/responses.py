"""Réponses API standardisées pour Omninet.

Fournit des classes et constantes pour formater les erreurs de manière cohérente.
"""

from __future__ import annotations

from fastapi import status
from fastapi.responses import JSONResponse


# Codes d'erreur courants
class ErrorCode:
    """Codes d'erreur standardisés pour l'API."""

    AUTH_FAILED = "AUTH_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def create_error_response(
    message: str,
    error_code: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    """Crée une réponse d'erreur standardisée.

    Args:
        message: Message d'erreur descriptif.
        error_code: Code d'erreur (utiliser les constantes de ErrorCode).
        status_code: Code HTTP de la réponse.

    Returns:
        JSONResponse avec le format standardisé.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": message,
            "code": error_code,
            "status": status_code,
        },
    )


# Raccourcis pour les erreurs courantes
def auth_failed_response(message: str = "Authentification échouée") -> JSONResponse:
    """Réponse pour erreur d'authentification."""
    return create_error_response(
        message=message,
        error_code=ErrorCode.AUTH_FAILED,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def validation_error_response(message: str = "Erreur de validation") -> JSONResponse:
    """Réponse pour erreur de validation."""
    return create_error_response(
        message=message,
        error_code=ErrorCode.VALIDATION_ERROR,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def not_found_response(resource: str = "Ressource") -> JSONResponse:
    """Réponse pour ressource non trouvée."""
    return create_error_response(
        message=f"{resource} non trouvé",
        error_code=ErrorCode.NOT_FOUND,
        status_code=status.HTTP_404_NOT_FOUND,
    )


def rate_limited_response(message: str = "Trop de requêtes") -> JSONResponse:
    """Réponse pour rate limiting."""
    return create_error_response(
        message=message,
        error_code=ErrorCode.RATE_LIMITED,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


def forbidden_response(message: str = "Accès interdit") -> JSONResponse:
    """Réponse pour accès interdit."""
    return create_error_response(
        message=message,
        error_code=ErrorCode.FORBIDDEN,
        status_code=status.HTTP_403_FORBIDDEN,
    )
