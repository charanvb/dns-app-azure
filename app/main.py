"""FastAPI application factory and entry point."""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.routers import dns, health, requests
from app.routers.api import health as api_health, zones as api_zones, requests as api_requests

templates = Jinja2Templates(directory="templates")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise Azure DNS Self Service Portal",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Gzip compression for better performance
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Mount new JSON API routes (Phase 1)
    app.include_router(api_health.router)
    app.include_router(api_zones.router)
    app.include_router(api_requests.router)

    # Keep existing template-based routes for backward compatibility
    app.include_router(health.router)
    app.include_router(dns.router)
    app.include_router(requests.router)

    # Serve React static files (production)
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

        @app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
        async def serve_react_app(full_path: str):
            """Serve React SPA for all non-API routes."""
            # Let API routes pass through
            if full_path.startswith("api/") or full_path in ["docs", "redoc", "openapi.json"]:
                return None
            
            # Serve index.html for React routing
            index_file = frontend_dist / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            
            return HTMLResponse("Frontend not built. Run 'npm run build' in frontend/", status_code=404)
    else:
        # Fallback to old template-based index page
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def index(request: Request) -> HTMLResponse:
            """Render the landing page (fallback when React not built)."""
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "app_name": settings.app_name,
                    "app_version": settings.app_version,
                    "environment": settings.environment,
                },
            )

    return app


app = create_app()
