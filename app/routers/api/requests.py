"""JSON API endpoints for DNS change requests."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional

from app.config import settings
from app.services.dns_service import DnsService
from app.services.request_service import RequestService
from dns_engine import executor

router = APIRouter(prefix="/api/requests", tags=["api-requests"])
_svc = RequestService()


class DNSRecordInput(BaseModel):
    """Input model for a single DNS record."""
    type: str = Field(..., description="Record type (A, AAAA, CNAME, TXT, etc.)")
    label: str = Field(..., description="Record label/name")
    value: str = Field(..., description="Record value")
    ttl: int = Field(300, ge=60, le=86400, description="Time to live in seconds")


class DNSRequestInput(BaseModel):
    """Input model for DNS change request."""
    zone: str = Field(..., description="Target DNS zone")
    action: str = Field(..., pattern="^(create|modify|delete)$", description="Action to perform")
    records: List[DNSRecordInput] = Field(..., min_items=1, max_items=5)
    justification: str = Field(..., min_length=20, description="Business justification")


@router.post("", summary="Submit DNS change request")
async def submit_request(data: DNSRequestInput, request: Request) -> JSONResponse:
    """Validate and execute DNS changes."""
    
    # Validate zone not blacklisted
    if _svc.is_blacklisted(data.zone):
        return JSONResponse(
            {"error": f"Zone '{data.zone}' must be managed via Micetro."},
            status_code=422,
        )
    
    # Get DNS service
    try:
        dns_service = DnsService(settings.dns_subscription_id)
        dns_client = dns_service._client
    except Exception as exc:
        return JSONResponse(
            {"error": f"Failed to initialize DNS client: {str(exc)}"},
            status_code=500,
        )
    
    # Execute each record change
    results = []
    for record in data.records:
        result = {
            "type": record.type,
            "label": record.label,
            "value": record.value,
            "ttl": record.ttl,
            "error": None,
        }
        
        try:
            if data.action == "create":
                executor.create_or_update_record(
                    dns_client,
                    settings.dns_resource_group,
                    data.zone,
                    record.label,
                    record.type,
                    record.value,
                    record.ttl,
                )
            elif data.action == "modify":
                executor.create_or_update_record(
                    dns_client,
                    settings.dns_resource_group,
                    data.zone,
                    record.label,
                    record.type,
                    record.value,
                    record.ttl,
                )
            elif data.action == "delete":
                executor.delete_record(
                    dns_client,
                    settings.dns_resource_group,
                    data.zone,
                    record.label,
                    record.type,
                )
        except Exception as exc:
            result["error"] = str(exc)
        
        results.append(result)
    
    # Log to console (Phase 4: replace with DB logging)
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or \
                (request.client.host if request.client else "unknown")
    
    return JSONResponse({
        "results": results,
        "zone": data.zone,
        "action": data.action,
    })
