"""Logique métier d'authentification."""

import bcrypt

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token

# --- Users en mémoire pour le MVP ---
# Les mots de passe sont hashés au démarrage du service.
_USERS: dict[str, dict[str, str]] = {}


def _hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt.

    Args:
        password: Le mot de passe en clair.

    Returns:
        Le hash bcrypt sous forme de chaîne.
    """
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash bcrypt.

    Args:
        plain_password: Le mot de passe en clair.
        hashed_password: Le hash bcrypt stocké.

    Returns:
        True si le mot de passe correspond, False sinon.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def _init_default_users() -> None:
    """Initialise les utilisateurs par défaut avec des mots de passe hashés."""
    _USERS.clear()
    _USERS[settings.ADMIN_USERNAME] = {
        "username": settings.ADMIN_USERNAME,
        "role": "admin",
        "hashed_password": _hash_password(settings.ADMIN_PASSWORD),
    }
    _USERS[settings.ANALYST_USERNAME] = {
        "username": settings.ANALYST_USERNAME,
        "role": "analyst",
        "hashed_password": _hash_password(settings.ANALYST_PASSWORD),
    }


# Initialisation au chargement du module
_init_default_users()


def authenticate_user(username: str, password: str) -> dict | None:
    """Vérifie les identifiants d'un utilisateur.

    Args:
        username: Le nom d'utilisateur.
        password: Le mot de passe en clair.

    Returns:
        Un dict avec username et role si authentification réussie, None sinon.
    """
    user = _USERS.get(username)
    if user is None:
        return None
    if not _verify_password(password, user["hashed_password"]):
        return None
    return {"username": user["username"], "role": user["role"]}


def generate_token_for_user(username: str, role: str) -> str:
    """Génère un token JWT pour un utilisateur authentifié.

    Args:
        username: Le nom d'utilisateur.
        role: Le rôle de l'utilisateur.

    Returns:
        Le token JWT sous forme de chaîne.
    """
    return create_access_token(data={"sub": username, "role": role})


def get_user_from_token(token: str) -> dict | None:
    """Décode un token JWT et retourne les informations de l'utilisateur.

    Args:
        token: Le token JWT.

    Returns:
        Un dict avec username et role si le token est valide, None sinon.
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    username = payload.get("sub")
    role = payload.get("role")
    if username is None or role is None:
        return None
    return {"username": username, "role": role}
