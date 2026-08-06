"""DNS requests router."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.config import settings
from app.models import User

router = APIRouter(tags=["Web UI"])
templates = Jinja2Templates(directory="templates")


@router.get("/request", response_class=HTMLResponse, include_in_schema=False)
async def request_page(request: Request, user: User = Depends(get_current_user)) -> HTMLResponse:
    """Render the DNS request page."""
    return templates.TemplateResponse(
        "request.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "user": user,
        },
    )
