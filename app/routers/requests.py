"""DNS requests router."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings

router = APIRouter(tags=["Web UI"])
templates = Jinja2Templates(directory="templates")


@router.get("/request", response_class=HTMLResponse, include_in_schema=False)
async def request_page(request: Request) -> HTMLResponse:
    """Render the DNS request page."""
    return templates.TemplateResponse(
        "request.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
        },
    )
