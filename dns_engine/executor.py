"""
Azure DNS API execution layer.

ALL DnsManagementClient calls are here — nowhere else.
Services and routers call these functions; they never touch the SDK directly.
"""

import json

from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import (
    AaaaRecord,
    ARecord,
    CnameRecord,
    RecordSet,
    TxtRecord,
)


# ── Record listing ────────────────────────────────────────────────────────────

def list_zone_records(
    client: DnsManagementClient,
    resource_group: str,
    zone: str,
    top: int = 100,
    recordsetnamesuffix: str | None = None,
) -> list:
    """Return up to `top` record sets from a zone, excluding SOA and NS."""
    kwargs: dict = {
        "resource_group_name": resource_group,
        "zone_name": zone,
        "top": top,
    }
    if recordsetnamesuffix:
        kwargs["recordsetnamesuffix"] = recordsetnamesuffix

    return [
        rs
        for rs in client.record_sets.list_by_dns_zone(**kwargs)
        if (rs.type or "").split("/")[-1] not in ("SOA", "NS")
    ]


def get_record_set(
    client: DnsManagementClient,
    resource_group: str,
    zone: str,
    label: str,
    record_type: str,
) -> RecordSet | None:
    """Fetch a specific record set. Returns None if the record does not exist."""
    try:
        return client.record_sets.get(resource_group, zone, label, record_type.upper())
    except Exception:
        return None


# ── Record mutation ───────────────────────────────────────────────────────────

def create_or_update_record(
    client: DnsManagementClient,
    resource_group: str,
    zone: str,
    label: str,
    record_type: str,
    value: str,
    ttl: int = 300,
) -> None:
    """Create or overwrite a DNS record set.

    For TXT records, `value` may be a JSON array string
    (e.g. '["v=spf1 ...", "other string"]') or a plain string.
    """
    rs = RecordSet(ttl=ttl)
    rt = record_type.upper()

    if rt == "A":
        rs.a_records = [ARecord(ipv4_address=value.strip())]
    elif rt == "AAAA":
        rs.aaaa_records = [AaaaRecord(ipv6_address=value.strip())]
    elif rt == "CNAME":
        rs.cname_record = CnameRecord(cname=value.strip())
    elif rt == "TXT":
        try:
            values = json.loads(value) if value.lstrip().startswith("[") else [value]
        except Exception:
            values = [value]
        rs.txt_records = [TxtRecord(value=[str(v) for v in values if str(v).strip()])]
    else:
        raise ValueError(f"Record type '{record_type}' is not supported for self-service.")

    client.record_sets.create_or_update(
        resource_group_name=resource_group,
        zone_name=zone,
        relative_record_set_name=label,
        record_type=rt,
        parameters=rs,
    )


def delete_record_set(
    client: DnsManagementClient,
    resource_group: str,
    zone: str,
    label: str,
    record_type: str,
) -> None:
    """Delete an entire record set (all values for that label + type)."""
    client.record_sets.delete(
        resource_group_name=resource_group,
        zone_name=zone,
        relative_record_set_name=label,
        record_type=record_type.upper(),
    )
