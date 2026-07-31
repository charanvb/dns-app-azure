"""
DNS Engine — Azure DNS execution and validation.

Package layout
--------------
record_types.py  Type definitions, constraints, placeholder text
validators.py    Input validation (IPv4, IPv6, hostname, label, blacklist)
executor.py      All Azure DnsManagementClient calls

Import from this package rather than calling the Azure SDK directly from
routers or services.
"""

from dns_engine.record_types import RECORD_TYPES, ALLOWED_CREATE_TYPES
from dns_engine.validators import (
    BLACKLISTED_DOMAINS,
    is_blacklisted,
    validate_label,
    validate_record_value,
    validate_ipv4,
    validate_ipv6,
    validate_hostname,
)
from dns_engine.executor import (
    list_zone_records,
    get_record_set,
    create_or_update_record,
    delete_record_set,
)

__all__ = [
    "RECORD_TYPES",
    "ALLOWED_CREATE_TYPES",
    "BLACKLISTED_DOMAINS",
    "is_blacklisted",
    "validate_label",
    "validate_record_value",
    "validate_ipv4",
    "validate_ipv6",
    "validate_hostname",
    "list_zone_records",
    "get_record_set",
    "create_or_update_record",
    "delete_record_set",
]
