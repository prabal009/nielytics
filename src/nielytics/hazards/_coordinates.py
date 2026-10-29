"""Explicit station coordinates for non-spatial daily hazard time series."""
from __future__ import annotations

from nielytics.exceptions import ValidationError

from ._common import threshold


def location(latitude: float | None, longitude: float | None) -> dict[str, float] | None:
    """Return a validated EPSG:4326 station point or no location."""
    if (latitude is None) != (longitude is None):
        raise ValidationError("latitude and longitude must both be provided or both omitted")
    if latitude is None:
        return None
    lat = threshold(latitude, "latitude")
    lon = threshold(longitude, "longitude")
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValidationError("latitude/longitude out of range")
    return {"latitude": lat, "longitude": lon}
