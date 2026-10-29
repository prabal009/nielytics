"""Explicit WGS84 longitude/latitude validation for GeoJSON exporters."""

from __future__ import annotations

import math
from numbers import Real

from nielytics.exceptions import ValidationError

__all__ = ["validate_coordinates"]


def _require_wgs84(crs: str | None) -> None:
    """Require an explicit CRS; this module never silently reprojects coordinates."""
    if not isinstance(crs, str) or crs.strip().upper() != "EPSG:4326":
        raise ValidationError("crs must explicitly be 'EPSG:4326'; reprojection is not supported")


def validate_coordinates(
    longitude: Real, latitude: Real, *, crs: str | None = None
) -> tuple[float, float]:
    """Return finite WGS84 ``(longitude, latitude)`` in GeoJSON order.

    The caller must declare ``crs='EPSG:4326'``. Projected coordinates,
    numeric strings, missing values, booleans and extra dimensions are not
    accepted. No coordinate transformation or location inference takes place.
    """
    _require_wgs84(crs)
    if any(isinstance(value, bool) or not isinstance(value, Real)
           for value in (longitude, latitude)):
        raise ValidationError("longitude and latitude must be real numeric coordinates")
    try:
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValidationError("longitude must be in [-180, 180] and latitude in [-90, 90]")
        lon, lat = float(longitude), float(latitude)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError("longitude and latitude must be finite real coordinates") from exc
    if not math.isfinite(lon) or not math.isfinite(lat):
        raise ValidationError("longitude and latitude must be finite")
    return lon, lat
