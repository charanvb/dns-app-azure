"""FastAPI application factory and entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.auth.middleware import LoginRequiredMiddleware
from app.config import settings
from app.routers import auth, home, health, zones, requests


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise Azure DNS Self Service Portal",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Same-origin, server-rendered app — no cross-origin credentialed requests needed.
    # (allow_origins="*" + allow_credentials=True is an invalid/insecure combination.)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Login gate must run *inside* SessionMiddleware so request.session is populated
    # first. Middleware added later wraps outer, so add this before SessionMiddleware.
    app.add_middleware(LoginRequiredMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        same_site="lax",
        https_only=(settings.environment == "production"),
    )

    # Include routers
    app.include_router(auth.router)
    app.include_router(home.router)
    app.include_router(health.router)
    app.include_router(zones.router)
    app.include_router(requests.router)

    return app


app = create_app()

