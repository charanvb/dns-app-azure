"""
DNS record type definitions and constraints.

Edit this file to:
- Change placeholder text shown in the form
- Block or unblock a record type
- Update descriptions shown to users
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RecordTypeSpec:
    """Everything the portal needs to know about a DNS record type."""

    name: str
    description: str        # shown to users in tooltips/hints
    value_label: str        # column header / field label
    value_placeholder: str  # example text shown in empty input
    multi_value: bool       # True only for TXT (multiple strings per record set)
    blocked: bool           # True = cannot be created/modified through this portal
    blocked_reason: str     # why it is blocked (shown to users)


RECORD_TYPES: dict[str, RecordTypeSpec] = {
    "A": RecordTypeSpec(
        name="A",
        description="Maps a hostname to an IPv4 address.",
        value_label="IPv4 Address",
        value_placeholder="e.g. 203.0.113.10",
        multi_value=False,
        blocked=False,
        blocked_reason="",
    ),
    "AAAA": RecordTypeSpec(
        name="AAAA",
        description="Maps a hostname to an IPv6 address.",
        value_label="IPv6 Address",
        value_placeholder="e.g. 2001:db8::1",
        multi_value=False,
        blocked=False,
        blocked_reason="",
    ),
    "CNAME": RecordTypeSpec(
        name="CNAME",
        description="Alias — points one hostname to another. Cannot share a label with any other record type.",
        value_label="Target Hostname",
        value_placeholder="e.g. target.example.com",
        multi_value=False,
        blocked=False,
        blocked_reason="",
    ),
    "TXT": RecordTypeSpec(
        name="TXT",
        description="Stores arbitrary text (SPF, DMARC, domain verification, etc.).",
        value_label="Text Value(s)",
        value_placeholder='e.g. v=spf1 include:example.com -all',
        multi_value=True,  # each TXT record set can hold multiple strings
        blocked=False,
        blocked_reason="",
    ),
    "MX": RecordTypeSpec(
        name="MX",
        description="Mail exchange — routes inbound email.",
        value_label="Mail Exchange",
        value_placeholder="e.g. mail.example.com",
        multi_value=False,
        blocked=True,
        blocked_reason="Email-related changes must be reviewed by the Messaging team.",
    ),
    "SRV": RecordTypeSpec(
        name="SRV",
        description="Service locator record.",
        value_label="Target",
        value_placeholder="e.g. svc.example.com",
        multi_value=False,
        blocked=False,
        blocked_reason="",
    ),
    "NS": RecordTypeSpec(
        name="NS",
        description="Name server delegation.",
        value_label="Name Server",
        value_placeholder="e.g. ns1.example.com",
        multi_value=False,
        blocked=True,
        blocked_reason="NS changes require DNS admin approval — raise a manual request.",
    ),
}

# Record types that can be created/modified through the self-service portal.
ALLOWED_CREATE_TYPES: list[str] = [t for t, s in RECORD_TYPES.items() if not s.blocked]

# CNAME exclusivity: a CNAME cannot coexist with ANY other record type at the same label.
CNAME_EXCLUSIVE: bool = True
