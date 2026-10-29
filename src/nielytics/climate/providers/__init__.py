"""Verified public climate data connectors. Network is used only when explicitly called.

All online functions accept ``client=HTTPClient(...)`` for injectable transport,
offline mode, explicit cache TTL and bounded retries; results are AnalysisResult.
No credentials or forecast APIs are supplied.
"""

from ._http import HTTPClient, OfflineCacheError, ProviderError, ResponseError
from .nasa_landslides import (
    fetch_landslide_events,
    filter_landslides_by_region,
    landslide_events_to_geojson,
    load_landslide_catalog,
)
from .nasa_power import fetch_nasa_power_data, fetch_nasa_precipitation
from .noaa_ibtracs import (
    cyclone_frequency,
    cyclone_tracks_to_geojson,
    get_cyclone_intensity,
    get_cyclone_tracks,
    load_ibtracs,
)
from .open_meteo import fetch_historical_weather, fetch_rainfall_data, fetch_temperature_data
from .open_meteo_flood import analyze_discharge_anomalies, fetch_river_discharge

__all__ = [
    "HTTPClient",
    "OfflineCacheError",
    "ProviderError",
    "ResponseError",
    "analyze_discharge_anomalies",
    "cyclone_frequency",
    "cyclone_tracks_to_geojson",
    "fetch_historical_weather",
    "fetch_landslide_events",
    "fetch_nasa_power_data",
    "fetch_nasa_precipitation",
    "fetch_rainfall_data",
    "fetch_river_discharge",
    "fetch_temperature_data",
    "filter_landslides_by_region",
    "get_cyclone_intensity",
    "get_cyclone_tracks",
    "landslide_events_to_geojson",
    "load_ibtracs",
    "load_landslide_catalog",
]
