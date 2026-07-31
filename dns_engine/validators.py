"""
DNS input validation rules.

All validation logic lives here so it can be shared between
the web app and any standalone scripts.
"""

import re
from ipaddress import AddressValueError, IPv4Address, IPv6Address

# Zones managed via Micetro or requiring manual approval.
# Add zone names here to prevent self-service changes.
BLACKLISTED_DOMAINS: tuple[str, ...] = (
    "unilever.com.cn",
)


# ── Label validation ──────────────────────────────────────────────────────────

def validate_label(label: str) -> list[str]:
    """Return a list of error messages for a DNS label. Empty list = valid."""
    if not label:
        return ["Label is required."]
    errors: list[str] = []
    if "*" in label:
        errors.append("Wildcards (*) are not permitted.")
    if len(label) > 253:
        errors.append("Exceeds maximum FQDN length of 253 characters.")
    if label != "@":
        for seg in label.split("."):
            if len(seg) > 63:
                errors.append(f"Label segment '{seg[:20]}' exceeds 63 characters.")
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9.\-]*$", label):
            errors.append("Only a–z, 0–9, hyphens and dots are allowed.")
    return errors


# ── Value validation ──────────────────────────────────────────────────────────

def validate_ipv4(value: str) -> str | None:
    """Return an error message, or None if the value is a valid IPv4 address."""
    try:
        IPv4Address(value.strip())
        return None
    except (AddressValueError, ValueError):
        return (
            f"'{value}' is not a valid IPv4 address. "
            "A records require an IPv4 address (e.g. 203.0.113.10)."
        )


def validate_ipv6(value: str) -> str | None:
    """Return an error message, or None if the value is a valid IPv6 address."""
    try:
        IPv6Address(value.strip())
        return None
    except (AddressValueError, ValueError):
        return (
            f"'{value}' is not a valid IPv6 address. "
            "AAAA records require an IPv6 address (e.g. 2001:db8::1)."
        )


def validate_hostname(value: str) -> str | None:
    """Return an error message, or None if the value is a valid hostname."""
    v = value.strip()
    if not v:
        return "CNAME target is required."
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-zA-Z]{2,}$", v):
        return (
            f"'{v}' is not a valid hostname. "
            "CNAME must point to a fully qualified domain name (e.g. target.example.com)."
        )
    return None


def validate_record_value(record_type: str, value: str) -> str | None:
    """Validate a record value against its type's constraints."""
    rt = record_type.upper()
    if rt == "A":
        return validate_ipv4(value)
    if rt == "AAAA":
        return validate_ipv6(value)
    if rt == "CNAME":
        return validate_hostname(value)
    if rt == "TXT":
        if not value.strip():
            return "TXT value cannot be empty."
        return None
    return None


# ── Zone blacklist ────────────────────────────────────────────────────────────

def is_blacklisted(zone: str) -> bool:
    """Return True if the zone must be managed via Micetro or manual approval."""
    z = zone.lower().rstrip(".")
    return any(z == b or z.endswith(f".{b}") for b in BLACKLISTED_DOMAINS)
