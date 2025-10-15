"""USGS Earthquake ingestion."""
import httpx
import json
import logging
from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta

from app.services.ingest_base import BaseIngestionService
from app.settings import settings
from app.utils.time_utils import parse_datetime, utc_now, time_window_start

logger = logging.getLogger(__name__)


class IngestUSGSEarthquakes(BaseIngestionService):
    """Ingest earthquake data from USGS."""
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.source_name = "USGS_Earthquakes"
        self.base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    async def fetch_raw_data(self) -> Any:
        """Fetch earthquake data from USGS API."""
        try:
            # Build query parameters based on TEST_MODE
            params = {
                'format': 'geojson',
                'orderby': 'time',
                'starttime': time_window_start(hours_ago=48).isoformat()
            }
            
            if settings.TEST_MODE:
                # Global earthquakes M4.5+ for testing
                params['minmagnitude'] = 4.5
                logger.info("Fetching global earthquakes M4.5+ (TEST_MODE)")
            else:
                # Local to Alexandria
                params.update({
                    'latitude': settings.ALEXANDRIA_CENTER_LAT,
                    'longitude': settings.ALEXANDRIA_CENTER_LON,
                    'maxradiuskm': settings.RADIUS_KM,
                    'minmagnitude': 0
                })
                logger.info(f"Fetching earthquakes near Alexandria")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers={"User-Agent": "Alexandria-EAS/0.1"}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching USGS earthquake data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching USGS earthquake data: {e}", exc_info=True)
            return None
    
    def extract_items(self, raw_data: Any) -> List[Any]:
        """Extract features from USGS GeoJSON response."""
        if not raw_data or 'features' not in raw_data:
            return []
        # Limit to 30 most recent
        return raw_data['features'][:30]
    
    def normalize_item(self, raw_item: Any) -> Optional[Dict[str, Any]]:
        """Normalize USGS earthquake to common schema."""
        try:
            props = raw_item.get('properties', {})
            
            # Extract magnitude and place
            magnitude = props.get('mag')
            place = props.get('place', 'Unknown location')
            mag_display = f"M{magnitude}" if magnitude is not None else "M?"
            
            # Map magnitude to severity
            if magnitude is not None:
                if magnitude >= 6.0:
                    severity = "Severe"
                elif magnitude >= 4.5:
                    severity = "Moderate"
                else:
                    severity = "Minor"
            else:
                severity = "Minor"
            
            # Parse time
            time_ms = props.get('time')
            if time_ms:
                effective_at = datetime.fromtimestamp(time_ms / 1000.0).replace(tzinfo=None)
                from datetime import timezone as tz
                effective_at = effective_at.replace(tzinfo=tz.utc)
            else:
                effective_at = utc_now()
            
            # Build normalized alert
            normalized = {
                'source': self.source_name,
                'provider_id': raw_item.get('id'),  # USGS provides unique IDs
                'title': f"{mag_display} Earthquake — {place}"[:500],
                'summary': f"Magnitude {magnitude if magnitude is not None else '?'} earthquake detected.",
                'event_type': 'Earthquake',
                'severity': severity,
                'urgency': 'Immediate',
                'area': place[:500],
                'effective_at': effective_at,
                'expires_at': None,
                'url': props.get('url'),
                'raw_payload': json.dumps(raw_item)
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing USGS earthquake item: {e}", exc_info=True)
            return None


# CLI entry point for testing
if __name__ == "__main__":
    import asyncio
    from app.database import SessionLocal
    
    async def test_ingest():
        db = SessionLocal()
        try:
            service = IngestUSGSEarthquakes(db)
            count = await service.run()
            print(f"Ingested {count} new earthquake alerts")
        finally:
            db.close()
    
    asyncio.run(test_ingest())

