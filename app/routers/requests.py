"""DNS service request router — form render and submission."""

import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.dns_service import DnsService
from app.services.request_service import BLACKLISTED_DOMAINS, RequestService

router = APIRouter(prefix="/request", tags=["request"])
_templates = Jinja2Templates(directory="templates")
_svc = RequestService()


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting Container Apps forwarding headers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("", response_class=HTMLResponse, summary="DNS change request form")
async def request_form(request: Request) -> HTMLResponse:
    """Render the DNS service request form with live zone list."""
    zones = []
    try:
        zones = DnsService(settings.dns_subscription_id).list_zones_by_resource_group(
            settings.dns_resource_group
        )
    except Exception:
        pass

    return _templates.TemplateResponse(
        "request.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "zones": zones,
            "blacklisted_json": json.dumps(list(BLACKLISTED_DOMAINS)),
        },
    )


@router.post("", response_class=HTMLResponse, summary="Submit DNS change request")
async def submit_request(request: Request) -> HTMLResponse:
    """Validate, rate-limit, and record a submitted DNS change request."""
    client_ip = _get_client_ip(request)
    form = await request.form()

    action = form.get("action", "")
    zone = form.get("zone", "")
    label = form.get("label", "")
    record_type = form.get("record_type", "")
    value = form.get("value", "")

    # ── Server-side validation ────────────────────────────────────────────
    errors: list[str] = []

    if not zone:
        errors.append("Please select a DNS zone.")
    elif _svc.is_blacklisted(zone):
        errors.append(f"Zone '{zone}' must be managed via Micetro.")

    errors.extend(_svc.validate_label(label))

    if record_type == "A":
        errors.extend(_svc.validate_ipv4(value))
    elif record_type == "AAAA":
        errors.extend(_svc.validate_ipv6(value))
    elif not value:
        errors.append("Record value is required.")

    if errors:
        zones = []
        try:
            zones = DnsService(settings.dns_subscription_id).list_zones_by_resource_group(
                settings.dns_resource_group
            )
        except Exception:
            pass
        return _templates.TemplateResponse(
            "request.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "environment": settings.environment,
                "zones": zones,
                "blacklisted_json": json.dumps(list(BLACKLISTED_DOMAINS)),
                "errors": errors,
            },
            status_code=422,
        )

    return _templates.TemplateResponse(
        "confirmation.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "action": action,
            "zone": zone,
            "label": label,
            "record_type": record_type,
            "value": value,
            "ttl": form.get("ttl", "300"),
        },
    )
