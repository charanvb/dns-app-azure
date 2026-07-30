"""DNS management service — all azure-mgmt-dns SDK calls live here."""

from dataclasses import dataclass

from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import (
    AaaaRecord,
    ARecord,
    CnameRecord,
    RecordSet,
    TxtRecord,
)


@dataclass
class DnsZone:
    """Lightweight DNS zone data transfer object."""

    name: str
    resource_group: str
    zone_type: str
    record_set_count: int


class DnsService:
    """Encapsulates all Azure DNS SDK interactions.

    Uses DefaultAzureCredential — resolves to Managed Identity on
    Container Apps and to az login / env vars in local development.
    """

    def __init__(self, subscription_id: str) -> None:
        if not subscription_id:
            raise ValueError("DNS_SUBSCRIPTION_ID is not configured.")
        self._client = DnsManagementClient(DefaultAzureCredential(), subscription_id)

    def list_zones_by_resource_group(self, resource_group: str) -> list[DnsZone]:
        """Return all DNS zones in the given resource group."""
        if not resource_group:
            raise ValueError("DNS_RESOURCE_GROUP is not configured.")
        result = []
        for zone in self._client.zones.list_by_resource_group(resource_group):
            zt = zone.zone_type
            zone_type = zt.value if hasattr(zt, "value") else (str(zt) if zt else "Public")
            result.append(
                DnsZone(
                    name=zone.name,
                    resource_group=zone.id.split("/")[4],
                    zone_type=zone_type,
                    record_set_count=zone.number_of_record_sets or 0,
                )
            )
        return result

    def create_or_update_record(
        self,
        resource_group: str,
        zone: str,
        label: str,
        record_type: str,
        value: str,
        ttl: int = 300,
    ) -> None:
        """Create or overwrite a single-value DNS record set."""
        rs = RecordSet(ttl=ttl)
        rt = record_type.upper()
        if rt == "A":
            rs.a_records = [ARecord(ipv4_address=value)]
        elif rt == "AAAA":
            rs.aaaa_records = [AaaaRecord(ipv6_address=value)]
        elif rt == "CNAME":
            rs.cname_record = CnameRecord(cname=value)
        elif rt == "TXT":
            rs.txt_records = [TxtRecord(value=[value])]
        else:
            raise ValueError(f"Unsupported record type for direct implementation: {record_type}")

        self._client.record_sets.create_or_update(
            resource_group_name=resource_group,
            zone_name=zone,
            relative_record_set_name=label,
            record_type=rt,
            parameters=rs,
        )

    def delete_record(
        self,
        resource_group: str,
        zone: str,
        label: str,
        record_type: str,
    ) -> None:
        """Delete a DNS record set."""
        self._client.record_sets.delete(
            resource_group_name=resource_group,
            zone_name=zone,
            relative_record_set_name=label,
            record_type=record_type.upper(),
        )
