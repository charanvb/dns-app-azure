"""DNS management service — all azure-mgmt-dns SDK calls live here."""

from dataclasses import dataclass

from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient


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
