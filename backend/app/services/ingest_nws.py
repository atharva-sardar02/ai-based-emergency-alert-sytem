"""NWS (National Weather Service) alert ingestion."""
import httpx
import json
import logging
from typing import Any, List, Dict, Optional
from datetime import datetime

from app.services.ingest_base import BaseIngestionService
from app.settings import settings
from app.utils.time_utils import parse_datetime, utc_now
from app.utils.geo_utils import extract_point_from_geometry

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
    
    async def _prepare_zone_cache(self, items: List[Any]) -> Dict[str, tuple]:
        """Prepare zone coordinates cache for all items."""
        zone_urls = set()
        for item in items:
            props = item.get('properties', {})
            affected_zones = props.get('affectedZones', [])
            if affected_zones:
                zone_urls.add(affected_zones[0])  # Use first zone URL
        
        if zone_urls:
            logger.info(f"Fetching coordinates for {len(zone_urls)} zones...")
            return await self._fetch_zone_coordinates_batch(list(zone_urls))
        return {}
    
    async def run(self) -> int:
        """
        Run the full ingestion pipeline with zone coordinate caching.
        
        Returns:
            Number of new alerts inserted
        """
        try:
            logger.info(f"Starting ingestion for {self.source_name}")
            
            # Fetch raw data
            raw_data = await self.fetch_raw_data()
            if not raw_data:
                logger.warning(f"No raw data fetched from {self.source_name}")
                return 0
            
            # Extract items
            items = self.extract_items(raw_data)
            if not items:
                logger.warning(f"No items extracted from {self.source_name}")
                return 0
            
            # Prepare zone coordinates cache
            zone_coords_cache = await self._prepare_zone_cache(items)
            if zone_coords_cache:
                logger.info(f"Cached coordinates for {len(zone_coords_cache)} zones")
            
            # Normalize and insert
            new_count = 0
            for item in items:
                normalized = self.normalize_item(item, zone_coords_cache=zone_coords_cache)
                if normalized:
                    alert = self.upsert_alert(normalized)
                    if alert:
                        new_count += 1
            
            logger.info(f"Ingestion complete for {self.source_name}: {new_count} new alerts")
            return new_count
            
        except Exception as e:
            logger.error(f"Ingestion failed for {self.source_name}: {e}", exc_info=True)
            return 0
    
    async def _fetch_zone_coordinates_batch(self, zone_urls: List[str]) -> Dict[str, tuple]:
        """
        Fetch zone geometries from NWS zones API in batch.
        
        Args:
            zone_urls: List of zone URLs to fetch
        
        Returns:
            Dictionary mapping zone URLs to (latitude, longitude) tuples
        """
        zone_coords = {}
        if not zone_urls:
            return zone_coords
        
        # Fetch up to 5 zones in parallel (to avoid rate limiting)
        async def fetch_one(url: str):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        url,
                        headers={"User-Agent": "Alexandria-EAS/0.1"}
                    )
                    response.raise_for_status()
                    zone_data = response.json()
                    
                    # Extract geometry from zone
                    geometry = zone_data.get('geometry')
                    if geometry:
                        coords = extract_point_from_geometry(geometry)
                        if coords:
                            return (url, coords)
            except Exception as e:
                logger.debug(f"Error fetching zone coordinates from {url}: {e}")
            return None
        
        # Fetch zones in batches of 5
        import asyncio
        for i in range(0, len(zone_urls), 5):
            batch = zone_urls[i:i+5]
            results = await asyncio.gather(*[fetch_one(url) for url in batch], return_exceptions=True)
            for result in results:
                if result and isinstance(result, tuple):
                    zone_coords[result[0]] = result[1]
        
        return zone_coords
    
    def normalize_item(self, raw_item: Any, zone_coords_cache: Dict[str, tuple] = None) -> Optional[Dict[str, Any]]:
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
            
            # Extract coordinates from GeoJSON geometry
            latitude = None
            longitude = None
            geometry = raw_item.get('geometry')
            if geometry:
                coords = extract_point_from_geometry(geometry)
                if coords:
                    latitude, longitude = coords
            
            # Fallback 1: If no geometry in alert, try using zone coordinates from cache
            if (latitude is None or longitude is None) and props.get('affectedZones'):
                affected_zones = props.get('affectedZones', [])
                if affected_zones and zone_coords_cache:
                    # Try first zone URL
                    zone_url = affected_zones[0]
                    if zone_url in zone_coords_cache:
                        latitude, longitude = zone_coords_cache[zone_url]
                        logger.debug(f"Extracted coordinates from zone cache: ({latitude}, {longitude})")
            
            # Fallback 2: If still no coordinates, use area center based on TEST_MODE
            if latitude is None or longitude is None:
                if settings.TEST_MODE:
                    # For TEST_MODE (Virginia-wide), use Virginia center
                    # Virginia approximate center: 37.5°N, 79.0°W
                    latitude = 37.5
                    longitude = -79.0
                else:
                    # For Alexandria-specific mode, use Alexandria center
                    latitude = settings.ALEXANDRIA_CENTER_LAT
                    longitude = settings.ALEXANDRIA_CENTER_LON
                logger.debug(f"NWS alert has no geometry, using fallback coordinates: ({latitude}, {longitude})")
            
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
                'raw_payload': json.dumps(raw_item),
                'latitude': latitude,
                'longitude': longitude
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

