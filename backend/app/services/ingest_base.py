"""Base class for ingestion services."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Alert
from app.utils.dedupe import generate_natural_key
from app.utils.time_utils import parse_datetime, utc_now

logger = logging.getLogger(__name__)


class BaseIngestionService(ABC):
    """
    Abstract base class for alert ingestion services.
    
    Each source (NWS, USGS, etc.) should implement this interface.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.source_name = self.__class__.__name__.replace("Ingest", "")
    
    @abstractmethod
    async def fetch_raw_data(self) -> Any:
        """
        Fetch raw data from the external source.
        
        Returns:
            Raw data (JSON, CSV, etc.)
        """
        pass
    
    @abstractmethod
    def normalize_item(self, raw_item: Any) -> Optional[Dict[str, Any]]:
        """
        Normalize a raw item to the common alert schema.
        
        Args:
            raw_item: Raw data item from source
        
        Returns:
            Dictionary with normalized fields or None if invalid:
            {
                'source': str,
                'provider_id': Optional[str],
                'title': str,
                'summary': Optional[str],
                'event_type': Optional[str],
                'severity': Optional[str],
                'urgency': Optional[str],
                'area': Optional[str],
                'effective_at': datetime,
                'expires_at': Optional[datetime],
                'url': Optional[str],
                'raw_payload': str (JSON)
            }
        """
        pass
    
    def upsert_alert(self, normalized: Dict[str, Any]) -> Optional[Alert]:
        """
        Insert alert into database, handling duplicates.
        
        Args:
            normalized: Normalized alert data
        
        Returns:
            Alert object if inserted, None if duplicate
        """
        try:
            # Generate natural key
            natural_key = generate_natural_key(
                source=normalized['source'],
                provider_id=normalized.get('provider_id'),
                title=normalized.get('title'),
                area=normalized.get('area'),
                effective_at=normalized.get('effective_at')
            )
            
            # Create alert object
            alert = Alert(
                natural_key=natural_key,
                source=normalized['source'],
                provider_id=normalized.get('provider_id'),
                title=normalized['title'],
                summary=normalized.get('summary'),
                event_type=normalized.get('event_type'),
                severity=normalized.get('severity'),
                urgency=normalized.get('urgency'),
                area=normalized.get('area'),
                effective_at=normalized['effective_at'],
                expires_at=normalized.get('expires_at'),
                url=normalized.get('url'),
                raw_payload=normalized.get('raw_payload')
            )
            
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            logger.info(f"Inserted new alert: {alert.id} from {alert.source}")
            return alert
            
        except IntegrityError as e:
            # Duplicate natural_key - ignore
            self.db.rollback()
            logger.debug(f"Duplicate alert ignored: {natural_key}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error inserting alert: {e}", exc_info=True)
            return None
    
    async def run(self) -> int:
        """
        Run the full ingestion pipeline: fetch -> normalize -> upsert.
        
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
            
            # Normalize and insert
            new_count = 0
            items = self.extract_items(raw_data)
            
            for item in items:
                normalized = self.normalize_item(item)
                if normalized:
                    alert = self.upsert_alert(normalized)
                    if alert:
                        new_count += 1
            
            logger.info(f"Ingestion complete for {self.source_name}: {new_count} new alerts")
            return new_count
            
        except Exception as e:
            logger.error(f"Ingestion failed for {self.source_name}: {e}", exc_info=True)
            return 0
    
    @abstractmethod
    def extract_items(self, raw_data: Any) -> List[Any]:
        """
        Extract individual items from raw data response.
        
        Args:
            raw_data: Raw data from fetch_raw_data()
        
        Returns:
            List of individual items to normalize
        """
        pass

