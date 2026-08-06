"""FastAPI application factory and entry point."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.routers.api import health as api_health, zones as api_zones, requests as api_requests


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

    # Mount JSON API routes
    app.include_router(api_health.router)
    app.include_router(api_zones.router)
    app.include_router(api_requests.router)

    # Serve React static files
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    
    if frontend_dist.exists():
        # Mount static assets (CSS, JS, images)
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

        @app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
        async def serve_react_app(full_path: str):
            """Serve React SPA for all non-API routes."""
            # Let API routes and docs pass through
            if full_path.startswith("api/"):
                return None
            
            # Serve index.html for React client-side routing
            index_file = frontend_dist / "index.html"
            return FileResponse(index_file)
    else:
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def index():
            """Error page when React frontend is not built."""
            return HTMLResponse(
                """
                <html>
                    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h1>⚠️ Frontend Not Built</h1>
                        <p>Run <code>npm run build</code> in the <code>frontend/</code> directory.</p>
                        <p><a href="/api/docs">API Documentation</a></p>
                    </body>
                </html>
                """,
                status_code=503
            )

    return app


app = create_app()
