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
    """Validate and execute one or more DNS changes submitted from the request form."""
    form = await request.form()
    action = form.get("action", "")
    zone   = form.get("zone", "")

    # ── Zone validation (always) ──────────────────────────────────────────
    errors: list[str] = []
    if not zone:
        errors.append("Please select a DNS zone.")
    elif _svc.is_blacklisted(zone):
        errors.append(f"Zone '{zone}' must be managed via Micetro.")

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

    # ── Build records list ────────────────────────────────────────────────
    records_json_str = form.get("records_json", "")
    all_records: list[dict] = []

    if records_json_str:
        try:
            all_records = json.loads(records_json_str)
        except Exception:
            all_records = []

    if not all_records:
        # Single-record fallback — validate label and value individually.
        label       = form.get("label", "")
        record_type = form.get("record_type", "")
        value       = form.get("value", "")
        try:
            ttl = int(form.get("ttl", "300") or 300)
        except (ValueError, TypeError):
            ttl = 300

        single_errors: list[str] = []
        single_errors.extend(_svc.validate_label(label))
        if record_type == "A":
            single_errors.extend(_svc.validate_ipv4(value))
        elif record_type == "AAAA":
            single_errors.extend(_svc.validate_ipv6(value))
        elif not value and action != "delete":
            single_errors.append("Record value is required.")

        if single_errors:
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
                    "errors": single_errors,
                },
                status_code=422,
            )
        all_records = [{"type": record_type, "label": label, "value": value, "ttl": ttl}]

    # ── Execute every record ──────────────────────────────────────────────
    dns_svc = DnsService(settings.dns_subscription_id)
    results: list[dict] = []

    for rec in all_records:
        rec_label = str(rec.get("label", "")).strip()
        rec_type  = str(rec.get("type",  "")).strip()
        rec_value = str(rec.get("value", "")).strip()
        try:
            rec_ttl = int(rec.get("ttl", 300) or 300)
        except (ValueError, TypeError):
            rec_ttl = 300

        # Server-side value validation for non-JSON values.
        rec_error: str | None = None
        try:
            if action == "delete":
                remaining = [str(v) for v in rec.get("remaining_values", [])]
                if rec_type == "TXT" and remaining:
                    # Partial TXT delete: update record set keeping only the remaining values.
                    dns_svc.create_or_update_record(
                        settings.dns_resource_group, zone, rec_label, "TXT",
                        __import__("json").dumps(remaining), rec_ttl,
                    )
                else:
                    dns_svc.delete_record(settings.dns_resource_group, zone, rec_label, rec_type)
            else:
                dns_svc.create_or_update_record(
                    settings.dns_resource_group, zone, rec_label, rec_type, rec_value, rec_ttl
                )
        except Exception as exc:
            rec_error = str(exc)

        results.append({
            "label": rec_label,
            "type":  rec_type,
            "value": rec_value,
            "ttl":   rec_ttl,
            "error": rec_error,
        })

    return _templates.TemplateResponse(
        "confirmation.html",
        {
            "request":     request,
            "app_name":    settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "action":      action,
            "zone":        zone,
            "results":     results,
        },
    )
