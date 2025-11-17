"""Geographic utility functions for coordinate extraction and validation."""
import json
import logging
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)


def validate_coordinates(latitude: Optional[float], longitude: Optional[float]) -> bool:
    """
    Validate latitude and longitude are within valid ranges.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
    
    Returns:
        True if coordinates are valid, False otherwise
    """
    if latitude is None or longitude is None:
        return False
    
    # Latitude must be between -90 and 90
    if not (-90 <= latitude <= 90):
        return False
    
    # Longitude must be between -180 and 180
    if not (-180 <= longitude <= 180):
        return False
    
    return True


def extract_point_from_geometry(geometry: Any) -> Optional[Tuple[float, float]]:
    """
    Extract coordinates from GeoJSON geometry.
    
    Supports:
    - Point: [lon, lat]
    - Polygon: Returns centroid of first ring
    - MultiPolygon: Returns centroid of first polygon's first ring
    
    Args:
        geometry: GeoJSON geometry object or dict
    
    Returns:
        Tuple of (latitude, longitude) or None if unable to extract
    """
    if not geometry:
        return None
    
    # If it's a string, try to parse as JSON
    if isinstance(geometry, str):
        try:
            geometry = json.loads(geometry)
        except (json.JSONDecodeError, TypeError):
            return None
    
    # If it's a dict, extract coordinates
    if isinstance(geometry, dict):
        geom_type = geometry.get('type', '').lower()
        coords = geometry.get('coordinates')
        
        if not coords:
            return None
        
        if geom_type == 'point':
            # Point: [longitude, latitude]
            if isinstance(coords, list) and len(coords) >= 2:
                lon, lat = coords[0], coords[1]
                if validate_coordinates(lat, lon):
                    return (lat, lon)
        
        elif geom_type == 'polygon':
            # Polygon: [[[lon, lat], [lon, lat], ...]]
            # Use first coordinate of first ring as representative point
            if isinstance(coords, list) and len(coords) > 0:
                ring = coords[0]
                if isinstance(ring, list) and len(ring) > 0:
                    first_point = ring[0]
                    if isinstance(first_point, list) and len(first_point) >= 2:
                        lon, lat = first_point[0], first_point[1]
                        if validate_coordinates(lat, lon):
                            return (lat, lon)
            
            # Alternative: calculate centroid (simplified - just average of first ring)
            try:
                total_lat = 0
                total_lon = 0
                count = 0
                ring = coords[0]
                for point in ring:
                    if isinstance(point, list) and len(point) >= 2:
                        lon, lat = point[0], point[1]
                        if validate_coordinates(lat, lon):
                            total_lat += lat
                            total_lon += lon
                            count += 1
                
                if count > 0:
                    return (total_lat / count, total_lon / count)
            except Exception as e:
                logger.debug(f"Error calculating polygon centroid: {e}")
        
        elif geom_type == 'multipolygon':
            # MultiPolygon: [[[[lon, lat], ...]]]
            # Use first polygon's first ring
            if isinstance(coords, list) and len(coords) > 0:
                first_polygon = coords[0]
                return extract_point_from_geometry({'type': 'Polygon', 'coordinates': first_polygon})
    
    # If it's a list, assume it's coordinates directly [lon, lat]
    if isinstance(geometry, list):
        if len(geometry) >= 2:
            lon, lat = geometry[0], geometry[1]
            if validate_coordinates(lat, lon):
                return (lat, lon)
    
    return None


def calculate_polygon_centroid(coordinates: Any) -> Optional[Tuple[float, float]]:
    """
    Calculate centroid of a polygon using simple averaging.
    
    Args:
        coordinates: Polygon coordinates (list of rings, where each ring is a list of [lon, lat] points)
    
    Returns:
        Tuple of (latitude, longitude) or None
    """
    if not coordinates or not isinstance(coordinates, list):
        return None
    
    try:
        # Get first ring (outer boundary)
        ring = coordinates[0] if isinstance(coordinates, list) else []
        
        total_lat = 0
        total_lon = 0
        count = 0
        
        for point in ring:
            if isinstance(point, list) and len(point) >= 2:
                lon, lat = float(point[0]), float(point[1])
                if validate_coordinates(lat, lon):
                    total_lat += lat
                    total_lon += lon
                    count += 1
        
        if count > 0:
            return (total_lat / count, total_lon / count)
        
    except Exception as e:
        logger.debug(f"Error calculating centroid: {e}")
    
    return None







