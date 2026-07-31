"""DNS management service — thin wrapper over dns_engine for the web app."""

from dataclasses import dataclass, field

from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient

import dns_engine.executor as executor


@dataclass
class DnsZone:
    """DNS zone data transfer object."""

    name: str
    resource_group: str
    zone_type: str
    record_set_count: int


@dataclass
class DnsRecord:
    """DNS record data transfer object."""

    name: str
    record_type: str
    ttl: int
    value: str
    raw_values: list = field(default_factory=list)  # individual TXT strings


class DnsService:
    """Public API for DNS operations used by the web app.

    All Azure SDK calls are delegated to dns_engine.executor.
    """

    def __init__(self, subscription_id: str) -> None:
        if not subscription_id:
            raise ValueError("DNS_SUBSCRIPTION_ID is not configured.")
        self._client: DnsManagementClient = DnsManagementClient(
            DefaultAzureCredential(), subscription_id
        )

    def list_zones_by_resource_group(self, resource_group: str) -> list[DnsZone]:
        """Return all DNS zones in the given resource group."""
        if not resource_group:
            raise ValueError("DNS_RESOURCE_GROUP is not configured.")
        result = []
        for zone in self._client.zones.list_by_resource_group(resource_group):
            zt = zone.zone_type
            zone_type = zt.value if hasattr(zt, "value") else (str(zt) if zt else "Public")
            result.append(DnsZone(
                name=zone.name,
                resource_group=zone.id.split("/")[4],
                zone_type=zone_type,
                record_set_count=zone.number_of_record_sets or 0,
            ))
        return result

    def list_records_by_zone(
        self,
        resource_group: str,
        zone: str,
        top: int = 100,
        search_suffix: str | None = None,
    ) -> tuple[list[DnsRecord], bool]:
        """Return up to `top` records and whether more exist (is_limited)."""
        if search_suffix:
            # Search: load ALL records from Azure then filter by substring on name.
            raw = executor.list_zone_records(
                self._client, resource_group, zone, top=None
            )
            term = search_suffix.lower()
            raw = [rs for rs in raw if term in (rs.name or "").lower()]
            is_limited = len(raw) > 100
            raw = raw[:100]
        else:
            raw = executor.list_zone_records(
                self._client, resource_group, zone, top=top + 1
            )
            is_limited = len(raw) > top
            raw = raw[:top]

        records = []
        for rs in raw:
            rt = (rs.type or "").split("/")[-1]
            raw_values: list = []
            if rt == "TXT" and rs.txt_records:
                for txt_rec in rs.txt_records:
                    raw_values.extend(txt_rec.value or [])
            records.append(DnsRecord(
                name=rs.name,
                record_type=rt,
                ttl=rs.ttl or 300,
                value=self._extract_value(rs),
                raw_values=raw_values,
            ))
        return records, is_limited

    def create_or_update_record(
        self, resource_group: str, zone: str, label: str,
        record_type: str, value: str, ttl: int = 300,
    ) -> None:
        executor.create_or_update_record(
            self._client, resource_group, zone, label, record_type, value, ttl
        )

    def delete_record(
        self, resource_group: str, zone: str, label: str, record_type: str,
    ) -> None:
        executor.delete_record_set(self._client, resource_group, zone, label, record_type)

    @staticmethod
    def _extract_value(rs) -> str:
        if rs.a_records:
            return ", ".join(r.ipv4_address for r in rs.a_records)
        if rs.aaaa_records:
            return ", ".join(r.ipv6_address for r in rs.aaaa_records)
        if rs.cname_record:
            return rs.cname_record.cname or ""
        if rs.txt_records:
            # Show each TXT string as a separate item so they don't blur together.
            all_vals = [v for t in rs.txt_records for v in (t.value or [])]
            return " | ".join(all_vals)
        if rs.mx_records:
            return ", ".join(f"{m.preference} {m.exchange}" for m in rs.mx_records)
        if rs.srv_records:
            return ", ".join(f"{s.priority} {s.weight} {s.port} {s.target}" for s in rs.srv_records)
        return ""
