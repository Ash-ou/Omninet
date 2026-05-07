from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_AGENT_TOKEN = "lab-agent-token-change-me"


class Settings(BaseSettings):
    """Configuration centralisée de l'application Omninet."""

    model_config = SettingsConfigDict(
        env_prefix="OMNINET_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Omninet"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # --- Auth / JWT ---
    # WARNING: ne jamais utiliser cette clé en production.
    # Toujours passer par la variable d'environnement OMNINET_SECRET_KEY.
    # Pour générer une clé sécurisée : python -c "import secrets; print(secrets.token_urlsafe(32))"
    SECRET_KEY: str  # Obligatoire - pas de valeur par défaut
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Auth agent (MVP lab) ---
    # WARNING: valeur par défaut acceptable uniquement pour le lab local.
    # En environnement réel, définir OMNINET_AGENT_TOKEN avec une valeur forte.
    AGENT_TOKEN: str = DEFAULT_AGENT_TOKEN

    # --- Utilisateurs par défaut (MVP) ---
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    ANALYST_USERNAME: str = "analyst"
    ANALYST_PASSWORD: str = "analyst"

    @model_validator(mode="after")
    def validate_agent_token_for_non_debug(self) -> "Settings":
        """Empêche l'usage du token agent par défaut hors mode debug."""
        if not self.DEBUG and self.AGENT_TOKEN == DEFAULT_AGENT_TOKEN:
            raise ValueError(
                "OMNINET_AGENT_TOKEN is using the default lab value while "
                "OMNINET_DEBUG=false. Define a strong OMNINET_AGENT_TOKEN before startup."
            )
        return self


settings = Settings()
