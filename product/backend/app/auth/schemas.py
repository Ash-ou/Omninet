"""Schemas Pydantic pour l'authentification."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Requête de connexion utilisateur."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)


class Token(BaseModel):
    """Réponse contenant le token d'accès."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Réponse contenant les informations de l'utilisateur connecté."""

    username: str
    role: str


class CreateUserRequest(BaseModel):
    """Requête de création d'utilisateur."""

    username: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=4, max_length=128)
    role: str = Field(default="analyst", pattern=r"^(admin|analyst)$")


class UpdateUserRequest(BaseModel):
    """Requête de mise à jour d'utilisateur."""

    password: str | None = Field(default=None, min_length=4, max_length=128)
    role: str | None = Field(default=None, pattern=r"^(admin|analyst)$")


class UserAdminResponse(BaseModel):
    """Réponse utilisateur pour l'administration (sans mot de passe)."""

    username: str
    role: str
