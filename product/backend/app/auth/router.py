"""Routes FastAPI pour l'authentification."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import schemas
from app.auth.rate_limit import build_login_rate_limit_key, login_rate_limiter
from app.auth.service import authenticate_user, generate_token_for_user, get_user_from_token
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
