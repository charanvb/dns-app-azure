"""JSON API endpoints for DNS change requests."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional

from app.config import settings
from app.services.dns_service import DnsService
from app.services.request_service import RequestService
from app.services import request_history
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
            "status": "success",
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
                result["message"] = f"{record.type} record created successfully"
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
                result["message"] = f"{record.type} record updated successfully"
            elif data.action == "delete":
                executor.delete_record_set(
                    dns_client,
                    settings.dns_resource_group,
                    data.zone,
                    record.label,
                    record.type,
                )
                result["message"] = f"{record.type} record deleted successfully"
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            result["message"] = f"Failed to {data.action} {record.type} record"
        
        results.append(result)
    
    # Get client IP
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or \
                (request.client.host if request.client else "unknown")
    
    # Track request history
    try:
        request_id = request_history.save_request(
            zone=data.zone,
            action=data.action,
            records=[r.dict() for r in data.records],
            justification=data.justification,
            results=results,
            user_ip=client_ip,
        )
    except Exception:
        request_id = None  # Don't fail if history tracking fails
    
    # Count successes and errors
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    
    return JSONResponse({
        "results": results,
        "zone": data.zone,
        "action": data.action,
        "request_id": request_id,
        "summary": {
            "total": len(results),
            "successful": success_count,
            "failed": error_count,
        }
    })


@router.get("/history", summary="Get request history")
async def get_history(limit: int = 50) -> JSONResponse:
    """Get recent DNS change requests."""
    try:
        history = request_history.get_request_history(limit=min(limit, 100))
        return JSONResponse({"history": history, "count": len(history)})
    except Exception as exc:
        return JSONResponse(
            {"error": f"Failed to fetch history: {str(exc)}"},
            status_code=500,
        )


@router.get("/history/{request_id}", summary="Get specific request")
async def get_request(request_id: str) -> JSONResponse:
    """Get details of a specific request."""
    try:
        request_data = request_history.get_request_by_id(request_id)
        if not request_data:
            return JSONResponse(
                {"error": "Request not found"},
                status_code=404,
            )
        return JSONResponse(request_data)
    except Exception as exc:
        return JSONResponse(
            {"error": f"Failed to fetch request: {str(exc)}"},
            status_code=500,
        )
