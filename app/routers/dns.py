"""DNS zones router — renders the zone listing page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.dns_service import DnsService

router = APIRouter(prefix="/zones", tags=["dns"])
_templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse, summary="List DNS zones")
async def list_zones(request: Request) -> HTMLResponse:
    """Render DNS zones fetched from Azure via Managed Identity."""
    zones = []
    error: str | None = None

    try:
        service = DnsService(settings.dns_subscription_id)
        zones = service.list_zones_by_resource_group(settings.dns_resource_group)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    return _templates.TemplateResponse(
        "zones.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "zones": zones,
            "error": error,
        },
    )
