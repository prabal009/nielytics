"""Validated GeoJSON vector exports from explicitly declared WGS84 inputs."""

from .aggregation import (
    aggregate_hazards_by_region,
    compare_hazard_regions,
    detect_hazard_hotspots,
    generate_hazard_geojson,
    get_district_hazard_summary,
    get_state_hazard_summary,
)
from .boundaries import (
    INDIA_STATE_REFERENCES,
    get_state_reference,
    haversine_distance_km,
    point_in_bbox,
    point_in_polygon,
)
from .coordinates import validate_coordinates
from .geojson import points_to_geojson, regions_to_geojson, to_geojson, tracks_to_geojson
from .india_names import (
    INDIAN_STATES_AND_UTS,
    normalize_district_name,
    normalize_state_name,
)
from .map_layers import get_hazard_locations, get_hazard_map_layer, get_regional_hazard_data

__all__ = [
    "INDIAN_STATES_AND_UTS",
    "INDIA_STATE_REFERENCES",
    "aggregate_hazards_by_region",
    "compare_hazard_regions",
    "detect_hazard_hotspots",
    "generate_hazard_geojson",
    "get_district_hazard_summary",
    "get_hazard_locations",
    "get_hazard_map_layer",
    "get_regional_hazard_data",
    "get_state_hazard_summary",
    "get_state_reference",
    "haversine_distance_km",
    "normalize_district_name",
    "normalize_state_name",
    "point_in_bbox",
    "point_in_polygon",
    "points_to_geojson",
    "regions_to_geojson",
    "to_geojson",
    "tracks_to_geojson",
    "validate_coordinates",
]
