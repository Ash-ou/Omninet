# ──────────────────────────────────────────────
# Omninet — Backend FastAPI (serveur-soc)
# ──────────────────────────────────────────────
FROM python:3.12-slim

# Éviter les prompts interactifs de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installer curl pour le healthcheck Docker Compose
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copier les dépendances d'abord (cache Docker)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code backend (pour que app/ soit dans /app/app/)
COPY backend/ .

# Copier le frontend au niveau racine du filesystem
# main.py utilise: Path(__file__).resolve().parents[2] / "frontend" = /frontend
COPY frontend/ /frontend/

# Utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/sh appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /frontend
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
