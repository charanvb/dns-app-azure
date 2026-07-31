"""JSON API endpoints for zones — optimized for 10k+ zones."""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from functools import lru_cache
import time

from app.config import settings
from app.services.dns_service import DnsService

router = APIRouter(prefix="/api/zones", tags=["api-zones"])

# In-memory cache with extended TTL (zones don't change often)
_cache = {}
_cache_ttl = 300  # 5 minutes for zone list

@lru_cache(maxsize=1)
def _get_dns_service():
    """Cached DNS service instance."""
    return DnsService(settings.dns_subscription_id)


@router.get("/search", summary="Search DNS zones by name")
async def search_zones(
    q: str = Query("", min_length=2, description="Search query (min 2 chars)"),
    limit: int = Query(50, le=200, description="Max results to return")
) -> JSONResponse:
    """Search zones by name - optimized for 10k+ zones."""
    if len(q) < 2:
        return JSONResponse({"zones": [], "message": "Enter at least 2 characters to search"})
    
    cache_key = f"zones_all_{settings.dns_resource_group}"
    
    # Get all zones (cached)
    if cache_key in _cache:
        cached_data, cached_time = _cache[cache_key]
        if time.time() - cached_time < _cache_ttl:
            all_zones = cached_data
        else:
            all_zones = None
    else:
        all_zones = None
    
    # Fetch if not cached
    if all_zones is None:
        try:
            service = _get_dns_service()
            zones = service.list_zones_by_resource_group(settings.dns_resource_group)
            all_zones = [
                {
                    "name": zone.name,
                    "resource_group": zone.resource_group,
                    "zone_type": zone.zone_type,
                    "record_set_count": zone.record_set_count,
                }
                for zone in zones
            ]
            _cache[cache_key] = (all_zones, time.time())
        except Exception as exc:
            return JSONResponse(
                {"error": str(exc), "detail": "Failed to fetch zones"},
                status_code=500,
            )
    
    # Filter by search query
    query_lower = q.lower()
    filtered = [z for z in all_zones if query_lower in z["name"].lower()]
    
    return JSONResponse({
        "zones": filtered[:limit],
        "total_matches": len(filtered),
        "is_limited": len(filtered) > limit,
    })


@router.get("", summary="Get zones with pagination")
async def get_zones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
) -> JSONResponse:
    """Return zones with pagination - use /search for large datasets."""
    cache_key = f"zones_all_{settings.dns_resource_group}"
    
    if cache_key in _cache:
        cached_data, cached_time = _cache[cache_key]
        if time.time() - cached_time < _cache_ttl:
            all_zones = cached_data
        else:
            all_zones = None
    else:
        all_zones = None
    
    if all_zones is None:
        try:
            service = _get_dns_service()
            zones = service.list_zones_by_resource_group(settings.dns_resource_group)
            all_zones = [
                {
                    "name": zone.name,
                    "resource_group": zone.resource_group,
                    "zone_type": zone.zone_type,
                    "record_set_count": zone.record_set_count,
                }
                for zone in zones
            ]
            _cache[cache_key] = (all_zones, time.time())
        except Exception as exc:
            return JSONResponse(
                {"error": str(exc), "detail": "Failed to fetch zones"},
                status_code=500,
            )
    
    total = len(all_zones)
    paginated = all_zones[skip:skip + limit]
    
    return JSONResponse({
        "zones": paginated,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total,
    })


@router.get("/records", summary="Get records in a zone (JSON)")
async def get_zone_records(zone: str, search: str = "", limit: int = 10000) -> JSONResponse:
    """Return up to 10,000 records for a specific zone with optional search."""
    if not zone:
        return JSONResponse({"error": "zone parameter is required"}, status_code=400)
    
    try:
        service = _get_dns_service()
        search_suffix = search.strip() or None
        # Cap at 10k to prevent overload
        records, is_limited = service.list_records_by_zone(
            settings.dns_resource_group,
            zone,
            top=min(limit, 10000),
            search_suffix=search_suffix,
        )
        
        return JSONResponse({
            "records": [
                {
                    "name": r.name,
                    "type": r.record_type,
                    "ttl": r.ttl,
                    "value": r.value,
                    "raw_values": r.raw_values,
                }
                for r in records
            ],
            "total_loaded": len(records),
            "is_limited": is_limited,
        })
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@router.post("/delete-record", summary="Delete a DNS record")
async def delete_record_api(zone: str, label: str, record_type: str) -> JSONResponse:
    """Delete a single DNS record."""
    if not all([zone, label, record_type]):
        return JSONResponse(
            {"error": "zone, label, and record_type are required"},
            status_code=400,
        )
    
    try:
        service = _get_dns_service()
        service.delete_record(settings.dns_resource_group, zone, label, record_type)
        return JSONResponse({"success": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
