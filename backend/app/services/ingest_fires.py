"""NASA FIRMS (Fire Information for Resource Management System) ingestion."""
import httpx
import json
import logging
from typing import Any, List, Dict, Optional
from datetime import datetime, timezone

from app.services.ingest_base import BaseIngestionService
from app.settings import settings
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class IngestFires(BaseIngestionService):
    """Ingest fire detection data from NASA FIRMS."""
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.source_name = "NASA_FIRMS"
        self.base_url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    
    async def fetch_raw_data(self) -> Any:
        """Fetch fire detection data from NASA FIRMS API."""
        # Check if API key is configured
        if not settings.FIRMS_API_KEY:
            logger.warning("FIRMS_API_KEY not configured, skipping FIRMS ingestion")
            return None
        
        try:
            # Determine bbox based on TEST_MODE
            if settings.TEST_MODE:
                # Larger area for testing (Virginia)
                bbox = {
                    "minLon": -83.5,
                    "minLat": 36.5,
                    "maxLon": -75.0,
                    "maxLat": 39.5
                }
                logger.info("Fetching FIRMS data for Virginia (TEST_MODE)")
            else:
                # Alexandria bounding box
                bbox = settings.ALEXANDRIA_BBOX
                logger.info(f"Fetching FIRMS data for Alexandria")
            
            # Build URL: /api/area/csv/{MAP_KEY}/{source}/{area}/{dayRange}/{date}
            url = f"{self.base_url}/{settings.FIRMS_API_KEY}/VIIRS_SNPP_NRT/{bbox['minLon']},{bbox['minLat']},{bbox['maxLon']},{bbox['maxLat']}/7"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Alexandria-EAS/0.1"}
                )
                
                if response.status_code == 404:
                    logger.info("No fire detections in the area (404 from FIRMS)")
                    return None
                
                response.raise_for_status()
                return response.text  # CSV format
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching FIRMS data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching FIRMS data: {e}", exc_info=True)
            return None
    
    def extract_items(self, raw_data: Any) -> List[Any]:
        """Extract fire detections from CSV response."""
        if not raw_data or not isinstance(raw_data, str):
            return []
        
        try:
            lines = raw_data.strip().split('\n')
            if len(lines) < 2:  # Header + at least one data row
                return []
            
            header = lines[0].split(',')
            rows = []
            
            for line in lines[1:]:
                values = line.split(',')
                if len(values) != len(header):
                    continue
                
                row_dict = {}
                for i, col_name in enumerate(header):
                    row_dict[col_name.strip()] = values[i].strip() if i < len(values) else ""
                
                rows.append(row_dict)
            
            logger.info(f"Parsed {len(rows)} fire detection records from FIRMS")
            return rows[:50]  # Limit to 50 most recent
            
        except Exception as e:
            logger.error(f"Error parsing FIRMS CSV: {e}", exc_info=True)
            return []
    
    def normalize_item(self, raw_item: Any) -> Optional[Dict[str, Any]]:
        """Normalize FIRMS fire detection to common schema."""
        try:
            # Extract coordinates (already in lat/lon format)
            latitude_str = raw_item.get('latitude', '')
            longitude_str = raw_item.get('longitude', '')
            latitude = None
            longitude = None
            
            # Try to convert to float
            try:
                if latitude_str:
                    latitude = float(latitude_str)
                if longitude_str:
                    longitude = float(longitude_str)
            except (ValueError, TypeError):
                pass
            
            # Validate coordinates
            from app.utils.geo_utils import validate_coordinates
            if not validate_coordinates(latitude, longitude):
                latitude = None
                longitude = None
            
            brightness = raw_item.get('bright_ti4', '')
            confidence = raw_item.get('confidence', '')
            acq_date = raw_item.get('acq_date', '')
            acq_time = raw_item.get('acq_time', '')
            
            # Parse acquisition time
            if acq_date and acq_time:
                try:
                    # acq_time is in HHMM format
                    time_str = str(acq_time).zfill(4)  # Pad with zeros
                    hour = time_str[:2]
                    minute = time_str[2:4]
                    dt_string = f"{acq_date}T{hour}:{minute}:00Z"
                    effective_at = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
                except Exception:
                    effective_at = utc_now()
            else:
                effective_at = utc_now()
            
            # Map confidence to severity
            conf_lower = str(confidence).lower()
            if 'high' in conf_lower or 'h' == conf_lower:
                severity = "Severe"
            elif 'nominal' in conf_lower or 'n' == conf_lower:
                severity = "Moderate"
            else:
                severity = "Minor"
            
            # Create title
            title = f"Thermal Anomaly Detected"
            if brightness:
                title += f" (Brightness: {brightness}K)"
            
            # Location description
            location = f"Lat: {latitude}, Lon: {longitude}"
            
            # Build normalized alert
            normalized = {
                'source': self.source_name,
                'provider_id': f"{latitude_str}_{longitude_str}_{acq_date}_{acq_time}",  # Composite ID
                'title': title[:500],
                'summary': f"Fire or thermal anomaly detected via satellite. Confidence: {confidence}. Location: {location}",
                'event_type': 'Fire',
                'severity': severity,
                'urgency': 'Immediate',
                'area': location[:500],
                'effective_at': effective_at,
                'expires_at': None,
                'url': "https://firms.modaps.eosdis.nasa.gov/map/",
                'raw_payload': json.dumps(raw_item),
                'latitude': latitude,
                'longitude': longitude
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing FIRMS item: {e}", exc_info=True)
            return None


# CLI entry point for testing
if __name__ == "__main__":
    import asyncio
    from app.database import SessionLocal
    
    async def test_ingest():
        db = SessionLocal()
        try:
            service = IngestFires(db)
            count = await service.run()
            print(f"Ingested {count} new fire detections")
        finally:
            db.close()
    
    asyncio.run(test_ingest())

