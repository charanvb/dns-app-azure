"""FastAPI application factory and entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.routers import health

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

    app.include_router(health.router)

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def index(request: Request) -> HTMLResponse:
        """Render the landing page."""
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
