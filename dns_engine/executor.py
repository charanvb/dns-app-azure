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
    top: int | None = 100,
    recordsetnamesuffix: str | None = None,
) -> list:
    """Return record sets from a zone. Pass top=None to load all records."""
    kwargs: dict = {
        "resource_group_name": resource_group,
        "zone_name": zone,
    }
    if top is not None:
        kwargs["top"] = top
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

    For TXT records, `value` may be pipe-separated or JSON array.
    For MX records, `value` format: "priority exchange" (e.g., "10 mail.example.com")
    For SRV records, `value` format: "priority weight port target" (e.g., "10 5 5060 sip.example.com")
    For CAA records, `value` format: "flags tag value" (e.g., '0 issue "letsencrypt.org"')
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
        # Support both pipe-separated (from frontend) and JSON array
        if '|' in value:
            values = [v.strip() for v in value.split('|') if v.strip()]
        else:
            try:
                values = json.loads(value) if value.lstrip().startswith("[") else [value]
            except Exception:
                values = [value]
        rs.txt_records = [TxtRecord(value=[str(v) for v in values if str(v).strip()])]
    elif rt == "MX":
        # Parse "priority exchange" format
        parts = value.strip().split(None, 1)
        if len(parts) != 2:
            raise ValueError("MX record format: 'priority exchange' (e.g., '10 mail.example.com')")
        try:
            priority = int(parts[0])
            exchange = parts[1].strip()
            if priority < 0 or priority > 65535:
                raise ValueError("MX priority must be 0-65535")
            rs.mx_records = [MxRecord(preference=priority, exchange=exchange)]
        except ValueError as e:
            raise ValueError(f"Invalid MX record: {e}")
    elif rt == "SRV":
        # Parse "priority weight port target" format
        parts = value.strip().split(None, 3)
        if len(parts) != 4:
            raise ValueError("SRV record format: 'priority weight port target' (e.g., '10 5 5060 sip.example.com')")
        try:
            priority = int(parts[0])
            weight = int(parts[1])
            port = int(parts[2])
            target = parts[3].strip()
            if not (0 <= priority <= 65535 and 0 <= weight <= 65535 and 0 <= port <= 65535):
                raise ValueError("SRV priority/weight/port must be 0-65535")
            rs.srv_records = [SrvRecord(priority=priority, weight=weight, port=port, target=target)]
        except ValueError as e:
            raise ValueError(f"Invalid SRV record: {e}")
    elif rt == "CAA":
        # Parse "flags tag value" format (value may be quoted)
        parts = value.strip().split(None, 2)
        if len(parts) != 3:
            raise ValueError("CAA record format: 'flags tag value' (e.g., '0 issue \"letsencrypt.org\"')")
        try:
            flags = int(parts[0])
            tag = parts[1].strip()
            caa_value = parts[2].strip().strip('"')
            if flags not in (0, 128):
                raise ValueError("CAA flags must be 0 or 128")
            if tag not in ('issue', 'issuewild', 'iodef'):
                raise ValueError("CAA tag must be 'issue', 'issuewild', or 'iodef'")
            rs.caa_records = [CaaRecord(flags=flags, tag=tag, value=caa_value)]
        except ValueError as e:
            raise ValueError(f"Invalid CAA record: {e}")
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
