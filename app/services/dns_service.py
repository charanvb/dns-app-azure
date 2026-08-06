"""DNS management service — thin wrapper over dns_engine for the web app."""

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

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


# Cache zones for 1 hour (3600 seconds) - DNS zones don't change frequently
@lru_cache(maxsize=10)
def _get_cached_zones(subscription_id: str, resource_group: str, cache_key: int) -> list[DnsZone]:
    """Internal cached zone fetcher. cache_key changes every 1 hour."""
    client = DnsManagementClient(DefaultAzureCredential(), subscription_id)
    result = []
    for zone in client.zones.list_by_resource_group(resource_group):
        zt = zone.zone_type
        zone_type = zt.value if hasattr(zt, "value") else (str(zt) if zt else "Public")
        result.append(DnsZone(
            name=zone.name,
            resource_group=zone.id.split("/")[4],
            zone_type=zone_type,
            record_set_count=zone.number_of_record_sets or 0,
        ))
    return result


class DnsService:
    """Public API for DNS operations used by the web app.

    All Azure SDK calls are delegated to dns_engine.executor.
    """

    def __init__(self, subscription_id: str) -> None:
        if not subscription_id:
            raise ValueError("DNS_SUBSCRIPTION_ID is not configured.")
        self._subscription_id = subscription_id
        self._client: DnsManagementClient = DnsManagementClient(
            DefaultAzureCredential(), subscription_id
        )

    def list_zones_by_resource_group(self, resource_group: str) -> list[DnsZone]:
        """Return all DNS zones in the given resource group (CACHED for 5 minutes)."""
        if not resource_group:
            raise ValueError("DNS_RESOURCE_GROUP is not configured.")
        
        # Cache key changes every 5 minutes (300 seconds)
        import time
        cache_key = int(time.time() // 300)
        
        return _get_cached_zones(self._subscription_id, resource_group, cache_key)

    def list_records_by_zone(
        self,
        resource_group: str,
        zone: str,
        top: int = 100,
        search_suffix: str | None = None,
    ) -> tuple[list[DnsRecord], bool]:
        """Return up to `top` records and whether more exist (is_limited)."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[DnsService] list_records_by_zone - rg={resource_group}, zone={zone}, top={top}, search={search_suffix}")
        
        # Azure DNS API max limit is 1000 per request
        AZURE_MAX_LIMIT = 1000
        
        if search_suffix:
            # OPTIMIZED SEARCH: Load ALL records once, then filter in memory
            # Fast enough for most zones (<10k records = ~2-3 seconds)
            logger.info("[DnsService] Using optimized search mode - loading all records and filtering")
            term = search_suffix.lower()
            
            # Load ALL records from Azure (no top limit)
            logger.info("[DnsService] Loading all records from Azure...")
            all_records = executor.list_zone_records(
                self._client, resource_group, zone, top=None
            )
            logger.info(f"[DnsService] Loaded {len(all_records)} total records from Azure")
            
            # Filter by searching in name AND value
            matched_records = []
            for rs in all_records:
                # Search in record name
                name_match = term in (rs.name or "").lower()
                
                # Search in record values
                value_match = False
                rt = (rs.type or "").split("/")[-1]
                
                if rt == "A" and rs.a_records:
                    value_match = any(term in (r.ipv4_address or "").lower() for r in rs.a_records)
                elif rt == "AAAA" and rs.aaaa_records:
                    value_match = any(term in (r.ipv6_address or "").lower() for r in rs.aaaa_records)
                elif rt == "CNAME" and rs.cname_record:
                    value_match = term in (rs.cname_record.cname or "").lower()
                elif rt == "TXT" and rs.txt_records:
                    for txt_rec in rs.txt_records:
                        if any(term in (v or "").lower() for v in (txt_rec.value or [])):
                            value_match = True
                            break
                
                if name_match or value_match:
                    matched_records.append(rs)
            
            logger.info(f"[DnsService] Search complete: {len(matched_records)} matches found")
            is_limited = len(matched_records) > top
            raw = matched_records[:top]
        else:
            # Cap at Azure's maximum limit of 1000
            fetch_top = min(top + 1, AZURE_MAX_LIMIT)
            logger.info(f"[DnsService] Using direct mode - loading top={fetch_top} records (capped at {AZURE_MAX_LIMIT})")
            raw = executor.list_zone_records(
                self._client, resource_group, zone, top=fetch_top
            )
            logger.info(f"[DnsService] Loaded {len(raw)} raw records from Azure")
            # If we got the max limit, there might be more
            is_limited = len(raw) >= AZURE_MAX_LIMIT or len(raw) > top
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
        
        logger.info(f"[DnsService] Returning {len(records)} records, is_limited={is_limited}")
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
