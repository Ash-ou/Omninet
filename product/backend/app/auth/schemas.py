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
