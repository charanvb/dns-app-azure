"""DNS zones router."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.dns_service import DnsService

router = APIRouter(tags=["Web UI"])
templates = Jinja2Templates(directory="templates")


@router.get("/zones", response_class=HTMLResponse, include_in_schema=False)
async def zones_page(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=10, le=200, description="Zones per page"),
    search: str = Query(None, description="Search zone names"),
) -> HTMLResponse:
    """Render the DNS zones page with pagination."""
    try:
        dns_service = DnsService(subscription_id=settings.dns_subscription_id)
        all_zones = dns_service.list_zones_by_resource_group(settings.dns_resource_group)
        
        # Filter by search if provided
        if search:
            search_lower = search.lower()
            all_zones = [z for z in all_zones if search_lower in z.name.lower()]
        
        # Sort by name
        all_zones.sort(key=lambda z: z.name)
        
        # Pagination
        total_zones = len(all_zones)
        total_pages = (total_zones + per_page - 1) // per_page  # Ceiling division
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        zones = all_zones[start_idx:end_idx]
        
        has_more = end_idx < total_zones
        
        return templates.TemplateResponse(
            "zones.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "environment": settings.environment,
                "zones": zones,
                "resource_group": settings.dns_resource_group,
                "page": page,
                "per_page": per_page,
                "total_zones": total_zones,
                "total_pages": total_pages,
                "showing_start": start_idx + 1 if zones else 0,
                "showing_end": start_idx + len(zones),
                "has_more": has_more,
                "search": search or "",
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "zones.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "environment": settings.environment,
                "error": str(e),
            },
        )


@router.get("/zones/{zone_name}/records", response_class=HTMLResponse, include_in_schema=False)
async def zone_records(
    request: Request,
    zone_name: str,
    search: str = Query(None, description="Search term"),
    top: int = Query(100, description="Max records to return"),
) -> HTMLResponse:
    """Render DNS records for a specific zone (HTMX partial)."""
    try:
        dns_service = DnsService(subscription_id=settings.dns_subscription_id)
        records, is_limited = dns_service.list_records_by_zone(
            resource_group=settings.dns_resource_group,
            zone=zone_name,
            top=top,
            search_suffix=search if search else None,
        )
        
        return templates.TemplateResponse(
            "partials/records_table.html",
            {
                "request": request,
                "zone_name": zone_name,
                "records": records,
                "is_limited": is_limited,
                "search": search or "",
                "total_shown": len(records),
            },
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-danger"><i class="bi bi-x-circle"></i> Error: {str(e)}</div>',
            status_code=500,
        )

