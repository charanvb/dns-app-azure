"""DNS zones router — renders the zone listing page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
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


@router.get("/records", summary="List records in a zone (JSON)")
async def list_zone_records(zone: str, search: str = "", limit: int = 1000) -> JSONResponse:
    """Return up to 1000 records for the request form. Includes is_limited flag.
    
    Azure DNS API has a maximum limit of 1000 records per request.
    """
    try:
        svc = DnsService(settings.dns_subscription_id)
        search_suffix = search.strip() or None
        # Azure DNS API max limit is 1000
        records, is_limited = svc.list_records_by_zone(
            settings.dns_resource_group, zone,
            top=min(limit, 1000),  # Cap at 1000 (Azure's max)
            search_suffix=search_suffix,
        )
        return JSONResponse({
            "records": [
                {"name": r.name, "type": r.record_type, "ttl": r.ttl,
                 "value": r.value, "raw_values": r.raw_values}
                for r in records
            ],
            "total_loaded": len(records),
            "is_limited": is_limited,
        })
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"error": str(exc)}, status_code=500)


@router.post("/api/delete-record", summary="Delete a DNS record (AJAX)")
async def api_delete_record(request: Request) -> JSONResponse:
    """Delete a single record; called by multi-select batch delete in the form."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    zone        = (data.get("zone") or "").strip()
    label       = (data.get("label") or "").strip()
    record_type = (data.get("record_type") or "").strip()

    if not all([zone, label, record_type]):
        return JSONResponse({"error": "zone, label, and record_type are required"}, status_code=400)

    try:
        DnsService(settings.dns_subscription_id).delete_record(
            settings.dns_resource_group, zone, label, record_type
        )
        return JSONResponse({"success": True})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"error": str(exc)}, status_code=500)
