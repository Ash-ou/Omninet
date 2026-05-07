from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.alerts.router import router as alerts_router
from app.assets.router import router as assets_router
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.correlation.router import router as correlation_router
from app.discovery.router import router as discovery_router
from app.events.router import router as events_router
from app.reports.router import router as reports_router
from app.telemetry.router import router as telemetry_router


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def create_app() -> FastAPI:
    """Factory pour l'application FastAPI."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Omninet — Plateforme de cybersurveillance réseau orientée SOC.",
    )

    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response

    @app.get("/")
    def root() -> dict[str, str]:
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "omninet-api"}

    @app.get("/ui", response_class=FileResponse)
    def ui_index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/ui/alerts", response_class=FileResponse)
    def ui_alerts() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "alerts.html")

    @app.get("/ui/events", response_class=FileResponse)
    def ui_events() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "events.html")

    @app.get("/ui/endpoints", response_class=FileResponse)
    def ui_endpoints() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "endpoints.html")

    @app.get("/ui/scans", response_class=FileResponse)
    def ui_scans() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "scans.html")

    app.mount(
        "/ui/assets",
        StaticFiles(directory=FRONTEND_DIR / "assets"),
        name="ui-assets",
    )

    # --- Routes authentification ---
    app.include_router(auth_router, prefix="/auth")

    # --- Routes télémétrie ---
    app.include_router(telemetry_router, prefix="/telemetry")

    # --- Routes événements ---
    app.include_router(events_router, prefix="/events")

    # --- Routes alertes ---
    app.include_router(alerts_router, prefix="/alerts")

    # --- Routes audit ---
    app.include_router(audit_router, prefix="/audit")

    # --- Routes discovery ---
    app.include_router(discovery_router, prefix="/discovery")

    # --- Routes assets ---
    app.include_router(assets_router, prefix="/assets")

    # --- Routes corrélation ---
    app.include_router(correlation_router, prefix="/correlation")

    # --- Routes rapports/KPI ---
    app.include_router(reports_router, prefix="/reports")

    return app


app = create_app()
