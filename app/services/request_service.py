"""DNS service request validation and rate-limiting.

No Azure SDK calls here — Azure interactions live in DnsService.
"""

import re
import time
from collections import defaultdict
from ipaddress import AddressValueError, IPv4Address, IPv6Address

# 2 requests per 24 h per source IP; move to DB in a later milestone.
_RATE_LIMIT_MAX = 2
_RATE_LIMIT_WINDOW = 86400  # seconds

# Zones that must stay in Micetro / go through manual approval.
BLACKLISTED_DOMAINS: tuple[str, ...] = (
    "unilever.com.cn",
)

_rate_store: dict[str, list[float]] = defaultdict(list)


class RequestService:
    """Validates DNS change requests and enforces submission rate-limits."""

    _MAX_LABEL_LEN = 63
    _MAX_FQDN_LEN = 253

    def validate_label(self, label: str) -> list[str]:
        """Return validation error messages for a DNS label or hostname."""
        if not label:
            return ["Label is required."]
        errs: list[str] = []
        if "*" in label:
            errs.append("Wildcard characters (*) are not permitted.")
        if len(label) > self._MAX_FQDN_LEN:
            errs.append(f"Exceeds maximum FQDN length of {self._MAX_FQDN_LEN} characters.")
        if label != "@":
            for seg in label.split("."):
                if len(seg) > self._MAX_LABEL_LEN:
                    errs.append(f"Label segment '{seg[:20]}…' exceeds 63 characters.")
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9.\-]*$', label):
                errs.append("Only a–z, 0–9, hyphens, and dots are allowed.")
        return errs

    def validate_ipv4(self, value: str) -> list[str]:
        """Return errors if value is not a valid IPv4 address."""
        try:
            IPv4Address(value.strip())
            return []
        except (AddressValueError, ValueError):
            return [f"'{value}' is not a valid IPv4 address."]

    def validate_ipv6(self, value: str) -> list[str]:
        """Return errors if value is not a valid IPv6 address."""
        try:
            IPv6Address(value.strip())
            return []
        except (AddressValueError, ValueError):
            return [f"'{value}' is not a valid IPv6 address."]

    def is_blacklisted(self, zone: str) -> bool:
        """Return True if the zone must remain in Micetro."""
        z = zone.lower().rstrip(".")
        return any(z == b or z.endswith(f".{b}") for b in BLACKLISTED_DOMAINS)

    def is_rate_limited(self, client_ip: str) -> bool:
        """Return True if the IP has hit its 24 h submission quota."""
        now = time.time()
        _rate_store[client_ip] = [
            ts for ts in _rate_store[client_ip] if now - ts < _RATE_LIMIT_WINDOW
        ]
        return len(_rate_store[client_ip]) >= _RATE_LIMIT_MAX

    def record_request(self, client_ip: str) -> None:
        """Log a successful submission timestamp against the source IP."""
        _rate_store[client_ip].append(time.time())
