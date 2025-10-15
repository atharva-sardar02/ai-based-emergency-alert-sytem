"""NWS (National Weather Service) alert ingestion."""
import httpx
import json
import logging
from typing import Any, List, Dict, Optional
from datetime import datetime

from app.services.ingest_base import BaseIngestionService
from app.settings import settings
from app.utils.time_utils import parse_datetime, utc_now

logger = logging.getLogger(__name__)


class IngestNWS(BaseIngestionService):
    """Ingest alerts from National Weather Service API."""
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.source_name = "NWS"
        self.base_url = "https://api.weather.gov"
    
    async def fetch_raw_data(self) -> Any:
        """Fetch NWS alerts from API."""
        try:
            # Use TEST_MODE to determine scope
            if settings.TEST_MODE:
                # Virginia-wide for testing
                url = f"{self.base_url}/alerts/active?area=VA"
                logger.info("Fetching NWS alerts for Virginia (TEST_MODE)")
            else:
                # Alexandria point-based query
                url = f"{self.base_url}/alerts/active?point={settings.ALEXANDRIA_CENTER_LAT},{settings.ALEXANDRIA_CENTER_LON}"
                logger.info(f"Fetching NWS alerts for Alexandria")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Alexandria-EAS/0.1 (contact@example.com)"}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching NWS data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching NWS data: {e}", exc_info=True)
            return None
    
    def extract_items(self, raw_data: Any) -> List[Any]:
        """Extract features from NWS GeoJSON response."""
        if not raw_data or 'features' not in raw_data:
            return []
        return raw_data['features']
    
    def normalize_item(self, raw_item: Any) -> Optional[Dict[str, Any]]:
        """Normalize NWS alert to common schema."""
        try:
            props = raw_item.get('properties', {})
            
            # Required fields
            title = props.get('headline') or props.get('event') or "NWS Alert"
            effective_at = parse_datetime(
                props.get('effective') or props.get('onset') or props.get('sent')
            )
            
            if not effective_at:
                effective_at = utc_now()
            
            # Build normalized alert
            normalized = {
                'source': self.source_name,
                'provider_id': props.get('id'),  # NWS provides unique IDs
                'title': title[:500],  # Truncate to fit DB field
                'summary': props.get('description', '')[:5000] if props.get('description') else None,
                'event_type': props.get('event'),
                'severity': props.get('severity'),
                'urgency': props.get('urgency'),
                'area': props.get('areaDesc', 'Alexandria area')[:500],
                'effective_at': effective_at,
                'expires_at': parse_datetime(props.get('expires') or props.get('ends')),
                'url': props.get('id') or props.get('@id'),
                'raw_payload': json.dumps(raw_item)
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing NWS item: {e}", exc_info=True)
            return None


# CLI entry point for testing
if __name__ == "__main__":
    import asyncio
    from app.database import SessionLocal
    
    async def test_ingest():
        db = SessionLocal()
        try:
            service = IngestNWS(db)
            count = await service.run()
            print(f"Ingested {count} new NWS alerts")
        finally:
            db.close()
    
    asyncio.run(test_ingest())

