"""USGS NWIS (National Water Information System) ingestion."""
import httpx
import json
import logging
from typing import Any, List, Dict, Optional

from app.services.ingest_base import BaseIngestionService
from app.settings import settings
from app.utils.time_utils import parse_datetime, utc_now

logger = logging.getLogger(__name__)


class IngestNWIS(BaseIngestionService):
    """Ingest river gauge data from USGS NWIS."""
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.source_name = "USGS_NWIS"
        self.base_url = "https://waterservices.usgs.gov/nwis/iv/"
    
    async def fetch_raw_data(self) -> Any:
        """Fetch river gauge data from USGS NWIS API."""
        try:
            # Get configured sites
            sites = ",".join(settings.NWIS_SITES)
            
            params = {
                'format': 'json',
                'sites': sites,
                'parameterCd': '00065,00060',  # Gage height and discharge
            }
            
            logger.info(f"Fetching NWIS data for sites: {sites}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers={"User-Agent": "Alexandria-EAS/0.1"}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching NWIS data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching NWIS data: {e}", exc_info=True)
            return None
    
    def extract_items(self, raw_data: Any) -> List[Any]:
        """Extract time series from NWIS JSON response."""
        if not raw_data or 'value' not in raw_data or 'timeSeries' not in raw_data['value']:
            return []
        return raw_data['value']['timeSeries']
    
    def normalize_item(self, raw_item: Any) -> Optional[Dict[str, Any]]:
        """Normalize NWIS gauge reading to common schema."""
        try:
            # Extract site info
            source_info = raw_item.get('sourceInfo', {})
            site_name = source_info.get('siteName', 'USGS Site')
            site_code = source_info.get('siteCode', [{}])[0].get('value', 'unknown')
            
            # Extract variable info
            variable = raw_item.get('variable', {})
            variable_name = variable.get('variableName', 'Water Parameter')
            
            # Get latest value
            values = raw_item.get('values', [{}])[0].get('value', [])
            if not values:
                return None
            
            latest = values[-1]
            value = latest.get('value', 'N/A')
            timestamp = latest.get('dateTime')
            
            effective_at = parse_datetime(timestamp) if timestamp else utc_now()
            
            # Build normalized alert
            normalized = {
                'source': self.source_name,
                'provider_id': f"{site_code}_{variable.get('variableCode', [{}])[0].get('value', 'param')}",
                'title': f"River {variable_name} — {site_name}"[:500],
                'summary': f"Latest reading: {value}",
                'event_type': 'River Level',
                'severity': 'Moderate',
                'urgency': 'Expected',
                'area': site_name[:500],
                'effective_at': effective_at,
                'expires_at': None,
                'url': f"https://waterdata.usgs.gov/monitoring-location/{site_code}",
                'raw_payload': json.dumps(raw_item)
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing NWIS item: {e}", exc_info=True)
            return None


# CLI entry point for testing
if __name__ == "__main__":
    import asyncio
    from app.database import SessionLocal
    
    async def test_ingest():
        db = SessionLocal()
        try:
            service = IngestNWIS(db)
            count = await service.run()
            print(f"Ingested {count} new NWIS alerts")
        finally:
            db.close()
    
    asyncio.run(test_ingest())

