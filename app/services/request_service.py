"""DNS service request validation and rate-limiting.

Validation logic is delegated to dns_engine.validators.
"""

import time
from collections import defaultdict

from dns_engine.validators import (
    BLACKLISTED_DOMAINS,
    is_blacklisted,
    validate_ipv4,
    validate_ipv6,
    validate_label,
    validate_record_value,
)

__all__ = ["RequestService", "BLACKLISTED_DOMAINS"]

_RATE_LIMIT_MAX = 2
_RATE_LIMIT_WINDOW = 86400  # 24 hours — re-enable when auth is in place

_rate_store: dict[str, list[float]] = defaultdict(list)


class RequestService:
    """Validates DNS change requests and enforces submission rate-limits."""

    def validate_label(self, label: str) -> list[str]:
        return validate_label(label)

    def validate_ipv4(self, value: str) -> list[str]:
        err = validate_ipv4(value)
        return [err] if err else []

    def validate_ipv6(self, value: str) -> list[str]:
        err = validate_ipv6(value)
        return [err] if err else []

    def validate_record_value(self, record_type: str, value: str) -> list[str]:
        err = validate_record_value(record_type, value)
        return [err] if err else []

    def is_blacklisted(self, zone: str) -> bool:
        return is_blacklisted(zone)

    def is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        _rate_store[client_ip] = [ts for ts in _rate_store[client_ip] if now - ts < _RATE_LIMIT_WINDOW]
        return len(_rate_store[client_ip]) >= _RATE_LIMIT_MAX

    def record_request(self, client_ip: str) -> None:
        _rate_store[client_ip].append(time.time())
