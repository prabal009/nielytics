"""Offline map layers created only from caller-supplied vector observations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from nielytics.exceptions import ValidationError

from .geojson import points_to_geojson, regions_to_geojson, to_geojson

__all__ = ["get_hazard_locations", "get_hazard_map_layer", "get_regional_hazard_data"]

_HAZARDS = frozenset({"heatwave", "flood", "drought", "landslide", "cyclone"})


def _validate_hazard(hazard: str) -> None:
    if not isinstance(hazard, str) or hazard not in _HAZARDS:
        raise ValidationError(f"hazard must be one of {', '.join(sorted(_HAZARDS))}")


def get_hazard_map_layer(
    hazard: str, features: Iterable[Mapping[str, Any]] | Mapping[str, Any], *, crs: str | None = None,
    source: str, period: str | None = None, units: str | None = None,
    method: str = "direct coordinate export", limitations: Sequence[str] = (),
) -> dict[str, Any]:
    """Return a map-ready FeatureCollection for *actual supplied* hazard features.

    Geometry records require ``geometry: {type, coordinates}``; explicit
    ``crs='EPSG:4326'`` is mandatory. The hazard is a caller-supplied category,
    not an assessed event, prediction, alert, or inferred spatial extent.
    Raster/gridded data are intentionally not converted to vector polygons.
    """
    _validate_hazard(hazard)
    layer = to_geojson(features, crs=crs, source=source,
                       period=period, units=units, method=method,
                       limitations=limitations)
    layer["metadata"]["hazard"] = hazard
    return layer


def get_hazard_locations(
    hazard: str, points: Iterable[Mapping[str, Any]] | Mapping[str, Any], *, crs: str | None = None,
    source: str, period: str | None = None, units: str | None = None,
    method: str = "direct coordinate export", limitations: Sequence[str] = (),
) -> dict[str, Any]:
    """Return only supplied Point/MultiPoint hazard locations; never geocode data."""
    _validate_hazard(hazard)
    layer = points_to_geojson(points, crs=crs, source=source,
                              period=period, units=units, method=method,
                              limitations=limitations)
    layer["metadata"]["hazard"] = hazard
    return layer


def get_regional_hazard_data(
    hazard: str, regions: Iterable[Mapping[str, Any]] | Mapping[str, Any], *, crs: str | None = None,
    source: str, period: str | None = None, units: str | None = None,
    method: str = "direct coordinate export", limitations: Sequence[str] = (),
) -> dict[str, Any]:
    """Return real supplied Polygon/MultiPolygon regions and their attributes.

    Regional indicators require independently supplied boundaries. This
    operation does not infer flood inundation, storm swaths, or other extents.
    """
    _validate_hazard(hazard)
    layer = regions_to_geojson(regions, crs=crs, source=source,
                               period=period, units=units, method=method,
                               limitations=limitations)
    layer["metadata"]["hazard"] = hazard
    return layer
