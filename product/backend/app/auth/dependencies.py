"""Dépendances d'authentification réutilisables pour Omninet."""

from fastapi import Depends, HTTPException, status

from app.auth.router import get_current_user


def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dépendance qui vérifie que l'utilisateur est admin.

    Args:
        current_user: Utilisateur authentifié (injecté par get_current_user).

    Returns:
        Le dict utilisateur si admin.

    Raises:
        HTTPException 403 si le rôle n'est pas 'admin'.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
