"""Helpers JWT pour l'authentification."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

DEFAULT_ALGORITHM = "HS256"
DEFAULT_EXPIRE_MINUTES = 30


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Crée un token JWT signé.

    Args:
        data: Les claims à encoder dans le token.
        expires_delta: Durée de validité du token.
            Par défaut, utilise ACCESS_TOKEN_EXPIRE_MINUTES de la config.

    Returns:
        Le token JWT encodé sous forme de chaîne.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict | None:
    """Décode et vérifie un token JWT.

    Args:
        token: Le token JWT à décoder.

    Returns:
        Les claims du token si valide, None sinon.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None
