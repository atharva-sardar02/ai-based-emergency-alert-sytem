"""Backfill script to extract coordinates from existing alerts' raw_payload."""
import json
import logging
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Alert
from app.utils.geo_utils import extract_point_from_geometry, validate_coordinates

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def extract_coords_from_raw_payload(alert: Alert) -> tuple:
    """
    Extract coordinates from alert's raw_payload.
    
    Returns:
        (latitude, longitude) or (None, None)
    """
    if not alert.raw_payload:
        return (None, None)
    
    try:
        payload = json.loads(alert.raw_payload)
        
        # Try different extraction methods based on source
        if alert.source == "NWS":
            # NWS provides GeoJSON with geometry
            geometry = payload.get('geometry')
            if geometry:
                coords = extract_point_from_geometry(geometry)
                if coords:
                    return coords
        
        elif alert.source == "USGS_Earthquakes":
            # USGS provides GeoJSON with geometry
            geometry = payload.get('geometry')
            if geometry:
                coords = extract_point_from_geometry(geometry)
                if coords:
                    return coords
        
        elif alert.source == "NASA_FIRMS":
            # FIRMS provides latitude/longitude directly
            lat_str = payload.get('latitude', '')
            lon_str = payload.get('longitude', '')
            try:
                latitude = float(lat_str) if lat_str else None
                longitude = float(lon_str) if lon_str else None
                if validate_coordinates(latitude, longitude):
                    return (latitude, longitude)
            except (ValueError, TypeError):
                pass
        
        elif alert.source == "USGS_NWIS":
            # NWIS has coordinates in sourceInfo.geoLocation.geogLocation
            source_info = payload.get('sourceInfo', {})
            geo_location = source_info.get('geoLocation', {})
            geog_location = geo_location.get('geogLocation', {})
            if geog_location:
                try:
                    lat = geog_location.get('latitude')
                    lon = geog_location.get('longitude')
                    if lat is not None and lon is not None:
                        latitude = float(lat)
                        longitude = float(lon)
                        if validate_coordinates(latitude, longitude):
                            return (latitude, longitude)
                except (ValueError, TypeError):
                    pass
        
        # WMATA typically doesn't have point coordinates (area-based)
        
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        logger.debug(f"Error extracting coords from alert {alert.id}: {e}")
    
    return (None, None)


def backfill_alert_coordinates(db: Session, alert_id: int = None):
    """
    Backfill coordinates for alerts that don't have them.
    
    Args:
        db: Database session
        alert_id: Optional specific alert ID to update
    """
    if alert_id:
        alerts = db.query(Alert).filter(Alert.id == alert_id).all()
    else:
        # Get all alerts without coordinates
        alerts = db.query(Alert).filter(
            (Alert.latitude.is_(None)) | (Alert.longitude.is_(None))
        ).all()
    
    updated = 0
    failed = 0
    
    logger.info(f"Processing {len(alerts)} alerts...")
    
    for alert in alerts:
        try:
            latitude, longitude = extract_coords_from_raw_payload(alert)
            
            if latitude is not None and longitude is not None:
                alert.latitude = latitude
                alert.longitude = longitude
                updated += 1
                
                if updated % 10 == 0:
                    db.commit()
                    logger.info(f"Updated {updated} alerts so far...")
            else:
                failed += 1
        
        except Exception as e:
            logger.error(f"Error processing alert {alert.id}: {e}")
            failed += 1
            continue
    
    # Final commit
    try:
        db.commit()
        logger.info(f"Successfully updated {updated} alerts with coordinates")
        if failed > 0:
            logger.info(f"{failed} alerts could not be updated (no coordinates in payload)")
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing updates: {e}")
        raise


if __name__ == "__main__":
    """CLI entry point for backfilling coordinates."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill coordinates for existing alerts")
    parser.add_argument("--alert-id", type=int, help="Update specific alert ID only")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        backfill_alert_coordinates(db, args.alert_id)
        
        # Print summary
        total = db.query(Alert).count()
        with_coords = db.query(Alert).filter(
            Alert.latitude.isnot(None),
            Alert.longitude.isnot(None)
        ).count()
        
        print(f"\nSummary:")
        print(f"   Total alerts: {total}")
        print(f"   Alerts with coordinates: {with_coords}")
        print(f"   Alerts without coordinates: {total - with_coords}")
        
    finally:
        db.close()

