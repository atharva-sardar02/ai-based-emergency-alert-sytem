"""WMATA (Washington Metropolitan Area Transit Authority) incident ingestion."""
import httpx
import json
import logging
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
    
    def extract_items(self, raw_data: Any) -> List[Any]:
        """Extract incidents from WMATA JSON response."""
        if not raw_data or 'Incidents' not in raw_data:
            return []
        return raw_data['Incidents']
    
    def normalize_item(self, raw_item: Any) -> Optional[Dict[str, Any]]:
        """Normalize WMATA incident to common schema."""
        try:
            # WMATA provides incident data
            incident_id = raw_item.get('IncidentID')
            incident_type = raw_item.get('IncidentType', 'Transit Incident')
            description = raw_item.get('Description', '')
            lines_affected = raw_item.get('LinesAffected', 'Metro')
            
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
                'raw_payload': json.dumps(raw_item)
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

