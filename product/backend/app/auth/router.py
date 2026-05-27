"""Routes FastAPI pour l'authentification."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import schemas
from app.auth.rate_limit import build_login_rate_limit_key, login_rate_limiter
from app.auth.service import (
    authenticate_user,
    create_user,
    delete_user,
    generate_token_for_user,
    get_user_from_token,
    list_users,
    update_user,
)
from app.audit.service import log_action
from app.core.responses import ErrorCode

router = APIRouter()

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Dépendance FastAPI qui extrait et valide le token JWT.

    Args:
        credentials: Les credentials HTTP Bearer.

    Returns:
        Un dict avec username et role de l'utilisateur.

    Raises:
        HTTPException 401 si le token est invalide ou manquant.
    """
    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/login", response_model=schemas.Token)
def login(body: schemas.LoginRequest, request: Request) -> schemas.Token:
    """Authentifie un utilisateur et retourne un token JWT.

    Args:
        body: Les identifiants de connexion.

    Returns:
        Un token d'accès.

    Raises:
        HTTPException 401 si les identifiants sont incorrects.
    """
    client_ip = request.client.host if request.client is not None else "unknown"
    rate_limit_key = build_login_rate_limit_key(client_ip, body.username)

    if login_rate_limiter.is_limited(rate_limit_key):
        log_action(
            username=body.username,
            action="login_rate_limited",
            resource="auth",
            details={"success": False, "ip": client_ip},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives de connexion. Réessayez dans 60 secondes.",
        )

    user = authenticate_user(body.username, body.password)
    if user is None:
        login_rate_limiter.register_attempt(rate_limit_key)
        log_action(
            username=body.username,
            action="login_failed",
            resource="auth",
            details={"success": False},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )

    login_rate_limiter.reset(rate_limit_key)
    log_action(
        username=user["username"],
        action="login",
        resource="auth",
        details={"success": True},
    )
    token = generate_token_for_user(user["username"], user["role"])
    return schemas.Token(access_token=token, token_type="bearer")


@router.get("/me", response_model=schemas.UserResponse)
def me(user: dict = Depends(get_current_user)) -> schemas.UserResponse:
    """Retourne les informations de l'utilisateur connecté.

    Args:
        user: L'utilisateur courant (injecté par la dépendance get_current_user).

    Returns:
        Les informations de l'utilisateur (username, role).
    """
    return schemas.UserResponse(username=user["username"], role=user["role"])


# ─── Admin: user management ───


def _require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Vérifie que l'utilisateur est admin.

    Args:
        user: L'utilisateur courant.

    Returns:
        L'utilisateur admin.

    Raises:
        HTTPException 403 si l'utilisateur n'est pas admin.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return user


@router.get("/admin/users", response_model=list[schemas.UserAdminResponse])
def admin_list_users(admin: dict = Depends(_require_admin)) -> list[schemas.UserAdminResponse]:
    """Liste tous les utilisateurs (admin uniquement).

    Args:
        admin: Utilisateur admin authentifié.

    Returns:
        Liste des utilisateurs.
    """
    return [schemas.UserAdminResponse(**u) for u in list_users()]


@router.post("/admin/users", response_model=schemas.UserAdminResponse, status_code=201)
def admin_create_user(
    body: schemas.CreateUserRequest,
    admin: dict = Depends(_require_admin),
) -> schemas.UserAdminResponse:
    """Crée un nouvel utilisateur (admin uniquement).

    Args:
        body: Données du nouvel utilisateur.
        admin: Utilisateur admin authentifié.

    Returns:
        L'utilisateur créé.

    Raises:
        HTTPException 409 si le nom d'utilisateur existe déjà.
    """
    user = create_user(username=body.username, password=body.password, role=body.role)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce nom d'utilisateur existe déjà",
        )
    log_action(
        username=admin["username"],
        action="create_user",
        resource="auth",
        details={"created_username": body.username, "role": body.role},
    )
    return schemas.UserAdminResponse(**user)


@router.put("/admin/users/{username}", response_model=schemas.UserAdminResponse)
def admin_update_user(
    username: str,
    body: schemas.UpdateUserRequest,
    admin: dict = Depends(_require_admin),
) -> schemas.UserAdminResponse:
    """Met à jour un utilisateur (admin uniquement).

    Args:
        username: Nom de l'utilisateur à modifier.
        body: Champs à modifier (password, role).
        admin: Utilisateur admin authentifié.

    Returns:
        L'utilisateur mis à jour.

    Raises:
        HTTPException 404 si l'utilisateur n'existe pas.
    """
    user = update_user(username=username, password=body.password, role=body.role)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )
    log_action(
        username=admin["username"],
        action="update_user",
        resource="auth",
        details={"updated_username": username, "role": body.role, "password_changed": body.password is not None},
    )
    return schemas.UserAdminResponse(**user)


@router.delete("/admin/users/{username}", status_code=204)
def admin_delete_user(
    username: str,
    admin: dict = Depends(_require_admin),
) -> None:
    """Supprime un utilisateur (admin uniquement).

    Args:
        username: Nom de l'utilisateur à supprimer.
        admin: Utilisateur admin authentifié.

    Raises:
        HTTPException 404 si l'utilisateur n'existe pas.
        HTTPException 403 si l'utilisateur tente de se supprimer lui-même.
    """
    if username == admin["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez pas supprimer votre propre compte",
        )
    if not delete_user(username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )
    log_action(
        username=admin["username"],
        action="delete_user",
        resource="auth",
        details={"deleted_username": username},
    )
