"""Configuration de la base de données SQLAlchemy avec SQLite."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# URL de la base SQLite
SQLITE_URL = "sqlite:///omninet.db"

# Moteur SQLAlchemy avec configuration SQLite
engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},  # Nécessaire pour SQLite en multithread
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarative pour les modèles
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency FastAPI pour obtenir une session de base de données.

    Yields:
        Une session SQLAlchemy active.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialise la base de données en créant toutes les tables."""
    # Import des modèles pour s'assurer qu'ils sont enregistrés avec Base
    from app.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
