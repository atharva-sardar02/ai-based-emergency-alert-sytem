"""WMATA (Washington Metropolitan Area Transit Authority) incident ingestion."""
import httpx
import json
import logging
import re
from typing import Any, List, Dict, Optional

from app.services.ingest_base import BaseIngestionService
from app.settings import settings
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class IngestWMATA(BaseIngestionService):
    """Ingest transit incidents from WMATA."""
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.source_name = "WMATA"
        self.base_url = "https://api.wmata.com"
        self._stations_cache = None  # Cache for station coordinates
    
    async def run(self) -> int:
        """
        Run the full ingestion pipeline with station coordinate caching.
        
        Returns:
            Number of new alerts inserted
        """
        try:
            logger.info(f"Starting ingestion for {self.source_name}")
            
            # Fetch and cache station coordinates first
            stations_cache = await self._fetch_stations_cache()
            
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
            
            # Normalize and insert
            new_count = 0
            for item in items:
                normalized = self.normalize_item(item, stations_cache=stations_cache)
                if normalized:
                    alert = self.upsert_alert(normalized)
                    if alert:
                        new_count += 1
            
            logger.info(f"Ingestion complete for {self.source_name}: {new_count} new alerts")
            return new_count
            
        except Exception as e:
            logger.error(f"Ingestion failed for {self.source_name}: {e}", exc_info=True)
            return 0
    
    async def fetch_raw_data(self) -> Any:
        """Fetch WMATA incidents from API."""
        # Check if API key is configured
        if not settings.WMATA_API_KEY:
            logger.warning("WMATA_API_KEY not configured, skipping WMATA ingestion")
            return None
        
        try:
            url = f"{self.base_url}/Incidents.svc/json/Incidents"
            
            logger.info("Fetching WMATA incidents")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={
                        "api_key": settings.WMATA_API_KEY,
                        "User-Agent": "Alexandria-EAS/0.1"
                    }
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching WMATA data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching WMATA data: {e}", exc_info=True)
            return None
    
    async def _fetch_stations_cache(self) -> Dict[str, Dict[str, float]]:
        """
        Fetch and cache WMATA station coordinates.
        
        Returns:
            Dictionary mapping station names to {'lat': float, 'lon': float}
        """
        if self._stations_cache is not None:
            return self._stations_cache
        
        if not settings.WMATA_API_KEY:
            return {}
        
        try:
            url = f"{self.base_url}/Rail.svc/json/jStations"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={
                        "api_key": settings.WMATA_API_KEY,
                        "User-Agent": "Alexandria-EAS/0.1"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                stations = {}
                for station in data.get('Stations', []):
                    name = station.get('Name', '').strip()
                    lat = station.get('Lat')
                    lon = station.get('Lon')
                    
                    if name and lat is not None and lon is not None:
                        # Store by full name
                        stations[name.lower()] = {'lat': lat, 'lon': lon}
                        
                        # Also store by name without common suffixes
                        name_parts = name.split('/')
                        for part in name_parts:
                            part = part.strip()
                            if part and part.lower() != name.lower():
                                stations[part.lower()] = {'lat': lat, 'lon': lon}
                
                self._stations_cache = stations
                logger.info(f"Cached {len(stations)} WMATA station coordinates")
                return stations
                
        except Exception as e:
            logger.error(f"Error fetching WMATA stations: {e}")
            return {}
    
    def _extract_station_name(self, text: str) -> Optional[str]:
        """
        Extract station name from text (description, location name, etc.).
        
        Args:
            text: Text that might contain a station name
        
        Returns:
            Station name if found, None otherwise
        """
        if not text:
            return None
        
        # Common patterns: "Station Name's", "Station Name station", etc.
        # Remove common words and extract potential station names
        text = text.strip()
        
        # Check for possessive forms like "Navy Yard's"
        match = re.search(r"([A-Z][a-zA-Z\s]+(?:'s)?)", text)
        if match:
            station_name = match.group(1).rstrip("'s").strip()
            if len(station_name) > 3:  # Filter out very short matches
                return station_name
        
        return None
    
    def _find_station_coordinates(self, station_name: str, stations_cache: Dict) -> Optional[tuple]:
        """
        Find coordinates for a station name.
        
        Args:
            station_name: Name of the station
            stations_cache: Cached station data
        
        Returns:
            Tuple of (latitude, longitude) or None
        """
        if not station_name or not stations_cache:
            return None
        
        # Try exact match (case-insensitive)
        station_lower = station_name.lower().strip()
        if station_lower in stations_cache:
            coords = stations_cache[station_lower]
            return (coords['lat'], coords['lon'])
        
        # Try partial match
        for cached_name, coords in stations_cache.items():
            if station_lower in cached_name or cached_name in station_lower:
                return (coords['lat'], coords['lon'])
        
        return None
    
    def extract_items(self, raw_data: Any) -> List[Any]:
        """Extract incidents from WMATA JSON response."""
        if not raw_data or 'Incidents' not in raw_data:
            return []
        return raw_data['Incidents']
    
    def normalize_item(self, raw_item: Any, stations_cache: Dict = None) -> Optional[Dict[str, Any]]:
        """Normalize WMATA incident to common schema."""
        try:
            # WMATA provides incident data
            incident_id = raw_item.get('IncidentID')
            incident_type = raw_item.get('IncidentType', 'Transit Incident')
            description = raw_item.get('Description', '')
            lines_affected = raw_item.get('LinesAffected', 'Metro')
            start_location = raw_item.get('StartLocationFullName')
            end_location = raw_item.get('EndLocationFullName')
            
            # Extract coordinates from station names
            latitude = None
            longitude = None
            
            if stations_cache:
                # Try StartLocationFullName first
                if start_location:
                    coords = self._find_station_coordinates(start_location, stations_cache)
                    if coords:
                        latitude, longitude = coords
                        logger.debug(f"Found coordinates from StartLocation: {start_location}")
                
                # Try EndLocationFullName if no coordinates yet
                if (latitude is None or longitude is None) and end_location:
                    coords = self._find_station_coordinates(end_location, stations_cache)
                    if coords:
                        latitude, longitude = coords
                        logger.debug(f"Found coordinates from EndLocation: {end_location}")
                
                # Try extracting from description if still no coordinates
                if latitude is None or longitude is None:
                    station_name = self._extract_station_name(description)
                    if station_name:
                        coords = self._find_station_coordinates(station_name, stations_cache)
                        if coords:
                            latitude, longitude = coords
                            logger.debug(f"Found coordinates from description: {station_name}")
            
            # Fallback to Alexandria center if no station coordinates found
            if latitude is None or longitude is None:
                latitude = settings.ALEXANDRIA_CENTER_LAT
                longitude = settings.ALEXANDRIA_CENTER_LON
                logger.debug(f"Using fallback coordinates for WMATA incident")
            
            # Map incident type to severity
            incident_lower = incident_type.lower()
            if any(word in incident_lower for word in ['delay', 'single tracking', 'disabled train']):
                severity = "Moderate"
            elif any(word in incident_lower for word in ['suspended', 'major delay', 'station closure']):
                severity = "Severe"
            else:
                severity = "Minor"
            
            # Get date/time - WMATA provides DateUpdated
            date_updated = raw_item.get('DateUpdated')
            effective_at = utc_now()  # Use current time since WMATA doesn't provide incident start time consistently
            
            # Build normalized alert
            normalized = {
                'source': self.source_name,
                'provider_id': incident_id if incident_id else None,
                'title': f"Transit Incident — {incident_type}"[:500],
                'summary': description[:5000] if description else "Metro transit incident reported.",
                'event_type': 'Transit',
                'severity': severity,
                'urgency': 'Immediate',
                'area': lines_affected[:500] if lines_affected else 'WMATA Metro',
                'effective_at': effective_at,
                'expires_at': None,
                'url': "https://wmata.com/service/status/",
                'raw_payload': json.dumps(raw_item),
                'latitude': latitude,
                'longitude': longitude
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing WMATA item: {e}", exc_info=True)
            return None


# CLI entry point for testing
if __name__ == "__main__":
    import asyncio
    from app.database import SessionLocal
    
    async def test_ingest():
        db = SessionLocal()
        try:
            service = IngestWMATA(db)
            count = await service.run()
            print(f"Ingested {count} new WMATA incidents")
        finally:
            db.close()
    
    asyncio.run(test_ingest())

