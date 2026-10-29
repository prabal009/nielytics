"""GeoJSON exports of caller-supplied WGS84 coordinates, not hazard extents.

Input records use ``geometry: {type, coordinates}`` (GeoJSON shape), plus
optional ``properties`` and ``provenance`` mappings. Shorthand records may use
``coordinates`` with one of the specialized exporters; points also accept
``longitude`` and ``latitude``. GeoPandas and projected coordinates are not
accepted: pass explicitly declared EPSG:4326 coordinate arrays instead.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from itertools import pairwise
from typing import Any

from nielytics.exceptions import ValidationError

from .coordinates import _require_wgs84, validate_coordinates

__all__ = ["points_to_geojson", "regions_to_geojson", "to_geojson", "tracks_to_geojson"]

_GEOMETRIES = frozenset({
    "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon",
})
_NOTE = "Only supplied geometries are exported; no hazard extent, impact or risk is inferred."
_GEO_NOTE = (
    "Planar topology checks only; antimeridian crossings are not split "
    "or geodesically validated."
)


def _array(value: Any, label: str) -> list[Any]:
    if isinstance(value, (str, bytes, Mapping, AbstractSet)) or not isinstance(value, Iterable):
        raise ValidationError(f"{label} must be a coordinate array")
    try:
        return list(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} must be a coordinate array") from exc


def _position(value: Any) -> list[float]:
    parts = _array(value, "position")
    if len(parts) != 2:
        raise ValidationError("each position must contain exactly [longitude, latitude]")
    return list(validate_coordinates(parts[0], parts[1], crs="EPSG:4326"))


def _positions(value: Any, *, minimum: int, label: str) -> list[list[float]]:
    items = [_position(item) for item in _array(value, label)]
    if len(items) < minimum:
        raise ValidationError(f"{label} must contain at least {minimum} positions")
    if minimum == 2:
        if len(set(map(tuple, items))) < 2:
            raise ValidationError("a line must contain at least two distinct positions")
        if any(left == right for left, right in pairwise(items)):
            raise ValidationError("a line must not contain zero-length segments")
    return items


def _orientation(a: list[float], b: list[float], c: list[float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: list[float], b: list[float], p: list[float]) -> bool:
    return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
            and _orientation(a, b, p) == 0)


def _intersects(a: list[float], b: list[float], c: list[float], d: list[float]) -> bool:
    ab_c, ab_d = _orientation(a, b, c), _orientation(a, b, d)
    cd_a, cd_b = _orientation(c, d, a), _orientation(c, d, b)
    return ((ab_c == 0 and _on_segment(a, b, c))
            or (ab_d == 0 and _on_segment(a, b, d))
            or (cd_a == 0 and _on_segment(c, d, a))
            or (cd_b == 0 and _on_segment(c, d, b))
            or ((ab_c > 0) != (ab_d > 0) and (cd_a > 0) != (cd_b > 0)))


def _ring(value: Any) -> list[list[float]]:
    points = _positions(value, minimum=3, label="polygon ring")
    if points[0] != points[-1]:
        points.append(points[0].copy())
    if len(points) < 4 or len(set(map(tuple, points[:-1]))) < 3:
        raise ValidationError("polygon ring must have three distinct vertices")
    if len(set(map(tuple, points[:-1]))) != len(points) - 1:
        raise ValidationError("polygon ring contains a repeated vertex")
    if sum(a[0] * b[1] - b[0] * a[1]
           for a, b in pairwise(points)) == 0:
        raise ValidationError("polygon ring has zero planar area")
    size = len(points) - 1
    for i in range(size):
        for j in range(i + 2, size):
            if i == 0 and j == size - 1:
                continue  # closing and opening edges share the first vertex
            if _intersects(points[i], points[i + 1], points[j], points[j + 1]):
                raise ValidationError("polygon ring intersects itself")
    return points


def _inside(point: list[float], ring: list[list[float]]) -> bool:
    """Strict planar point-in-ring check; a point on the boundary is outside."""
    x, y = point
    inside = False
    for a, b in pairwise(ring):
        if _on_segment(a, b, point):
            return False
        if (a[1] > y) != (b[1] > y):
            crossing = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x < crossing:
                inside = not inside
    return inside


def _rings_intersect(left: list[list[float]], right: list[list[float]]) -> bool:
    return any(_intersects(a, b, c, d)
               for a, b in pairwise(left)
               for c, d in pairwise(right))


def _polygon(value: Any) -> list[list[list[float]]]:
    rings = [_ring(item) for item in _array(value, "polygon")]
    if not rings:
        raise ValidationError("polygon must have an exterior ring")
    for index, hole in enumerate(rings[1:], start=1):
        if not _inside(hole[0], rings[0]) or _rings_intersect(hole, rings[0]):
            raise ValidationError("polygon hole must lie strictly within the exterior ring")
        for other in rings[1:index]:
            if (_rings_intersect(hole, other) or _inside(hole[0], other)
                    or _inside(other[0], hole)):
                raise ValidationError("polygon holes must not overlap or nest")
    return rings


def _geometry(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError("geometry must be a GeoJSON geometry mapping")
    kind = value.get("type")
    if not isinstance(kind, str) or kind not in _GEOMETRIES:
        raise ValidationError("unsupported GeoJSON geometry type")
    if "coordinates" not in value or set(value) != {"type", "coordinates"}:
        raise ValidationError("geometry must have only type and coordinates")
    coordinates = value["coordinates"]
    if kind == "Point":
        parsed = _position(coordinates)
    elif kind == "MultiPoint":
        parsed = _positions(coordinates, minimum=1, label="multipoint")
    elif kind == "LineString":
        parsed = _positions(coordinates, minimum=2, label="line")
    elif kind == "MultiLineString":
        parsed = [_positions(item, minimum=2, label="line")
                  for item in _array(coordinates, "multiline")]
        if not parsed:
            raise ValidationError("multiline must contain at least one line")
    elif kind == "Polygon":
        parsed = _polygon(coordinates)
    else:
        parsed = [_polygon(item) for item in _array(coordinates, "multipolygon")]
        if not parsed:
            raise ValidationError("multipolygon must contain at least one polygon")
        for index, polygon in enumerate(parsed):
            for other in parsed[:index]:
                if (any(_rings_intersect(polygon[0], ring) for ring in other)
                        or any(_rings_intersect(other[0], ring) for ring in polygon)
                        or (_inside(polygon[0][0], other[0])
                            and not any(_inside(polygon[0][0], hole) for hole in other[1:]))
                        or (_inside(other[0][0], polygon[0])
                            and not any(_inside(other[0][0], hole) for hole in polygon[1:]))):
                    raise ValidationError("multipolygon members must not overlap")
    return {"type": kind, "coordinates": parsed}


def _strict_json(value: Any) -> Any:
    """Isolate caller metadata; reject nonfinite, non-JSON values and keys."""
    def check_keys(item: Any) -> None:
        if isinstance(item, Mapping):
            if any(not isinstance(key, str) for key in item):
                raise ValidationError("GeoJSON object keys must be strings")
            for child in item.values():
                check_keys(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check_keys(child)
    try:
        check_keys(value)
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ValidationError("GeoJSON properties and metadata must be strict JSON-compatible") from exc


def _metadata(source: str, period: str | None, units: str | None,
              method: str, limitations: Sequence[str]) -> dict[str, Any]:
    if not isinstance(source, str) or not source.strip():
        raise ValidationError("source must identify the actual source of the supplied coordinates")
    if not isinstance(method, str) or not method.strip():
        raise ValidationError("method must describe how supplied coordinates were produced")
    if period is not None and (not isinstance(period, str) or not period.strip()):
        raise ValidationError("period must be a nonempty string or None (unknown)")
    if units is not None and (not isinstance(units, str) or not units.strip()):
        raise ValidationError("units must be a nonempty string or None (unknown)")
    if (isinstance(limitations, (str, bytes)) or not isinstance(limitations, Sequence)
            or any(not isinstance(item, str) or not item.strip() for item in limitations)):
        raise ValidationError("limitations must be a sequence of nonempty strings")
    return {"source": source, "period": period, "units": units, "method": method,
            "limitations": [*limitations, _NOTE, _GEO_NOTE], "crs": "EPSG:4326"}


def _records(data: Iterable[Mapping[str, Any]] | Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    if isinstance(data, Mapping):
        if set(data) != {"type", "features"} or data["type"] != "FeatureCollection":
            raise ValidationError("FeatureCollection input must have only type and features")
        data = data["features"]
    if isinstance(data, (Mapping, str, bytes)):
        raise ValidationError("features must be an iterable of feature records, not a mapping")
    try:
        iterator = iter(data)
    except TypeError as exc:
        raise ValidationError("features must be an iterable of feature records") from exc
    for record in iterator:
        if not isinstance(record, Mapping):
            raise ValidationError("each feature must be a record mapping")
        yield record


def _convert(data: Iterable[Mapping[str, Any]] | Mapping[str, Any], *, allowed: frozenset[str],
             shorthand: str | None, crs: str | None, source: str,
             period: str | None, units: str | None, method: str,
             limitations: Sequence[str]) -> dict[str, Any]:
    _require_wgs84(crs)
    metadata = _metadata(source, period, units, method, limitations)
    features = []
    for record in _records(data):
        if "crs" in record:
            _require_wgs84(record["crs"])
        if "type" in record and record["type"] != "Feature":
            raise ValidationError("feature type must be 'Feature'")
        if "geometry" in record:
            geo = record["geometry"]
        elif shorthand == "Point" and "longitude" in record and "latitude" in record:
            geo = {"type": "Point", "coordinates": [record["longitude"], record["latitude"]]}
        elif shorthand is not None and "coordinates" in record:
            geo = {"type": shorthand, "coordinates": record["coordinates"]}
        else:
            raise ValidationError("feature requires an explicit GeoJSON geometry")
        geometry = _geometry(geo)
        if geometry["type"] not in allowed:
            raise ValidationError("geometry type is not supported by this exporter")
        properties = _strict_json(record.get("properties", {}))
        if not isinstance(properties, dict):
            raise ValidationError("feature properties must be a mapping")
        if "provenance" in record and "provenance" in properties:
            raise ValidationError("feature provenance must have only one declaration")
        feature_provenance = _strict_json(record.get("provenance", properties.pop("provenance", {})))
        if not isinstance(feature_provenance, dict):
            raise ValidationError("feature provenance must be a mapping")
        if "crs" in feature_provenance:
            _require_wgs84(feature_provenance["crs"])
        provenance = {key: metadata[key] for key in ("source", "period", "units", "method", "limitations")}
        provenance.update(feature_provenance)
        _metadata(provenance["source"], provenance["period"], provenance["units"],
                  provenance["method"], provenance["limitations"])
        if "limitations" in feature_provenance:
            provenance["limitations"] = [*provenance["limitations"], _NOTE, _GEO_NOTE]
        properties["provenance"] = provenance
        feature = {"type": "Feature", "geometry": geometry, "properties": properties}
        if "id" in record:
            identifier = record["id"]
            if isinstance(identifier, bool) or not isinstance(identifier, (str, int, float)):
                raise ValidationError("feature id must be a string or finite number")
            feature["id"] = _strict_json(identifier)
        features.append(feature)
    return _strict_json({"type": "FeatureCollection", "features": features, "metadata": metadata})


def to_geojson(features: Iterable[Mapping[str, Any]] | Mapping[str, Any], *, crs: str | None = None,
               source: str, period: str | None = None, units: str | None = None,
               method: str = "direct coordinate export",
               limitations: Sequence[str] = ()) -> dict[str, Any]:
    """Export six vector geometry types as a strict-JSON FeatureCollection.

    Require explicit ``crs='EPSG:4326'`` and actual supplied geometries.
    Input may be feature records or a FeatureCollection containing only ``type``
    and ``features``; feature identifiers are preserved.
    Properties and provenance must be JSON values; None for period/units means
    unknown, not a claimed observation interval or measurement unit. Open
    polygon rings are closed on output; self-crossings, invalid holes and
    overlapping multipart polygon components are rejected with conservative
    planar checks (touching components may also be rejected). This does not
    split antimeridian-crossing geometries, measure geographic distances/areas,
    or generate extents; large climate rasters must use a different format.
    """
    return _convert(features, allowed=_GEOMETRIES, shorthand=None, crs=crs,
                    source=source, period=period, units=units, method=method,
                    limitations=limitations)


def points_to_geojson(points: Iterable[Mapping[str, Any]] | Mapping[str, Any], *, crs: str | None = None,
                      source: str, period: str | None = None, units: str | None = None,
                      method: str = "direct coordinate export",
                      limitations: Sequence[str] = ()) -> dict[str, Any]:
    """Export supplied Point/MultiPoint records; points may use lon/lat shorthand."""
    return _convert(points, allowed=frozenset({"Point", "MultiPoint"}), shorthand="Point",
                    crs=crs, source=source, period=period, units=units,
                    method=method, limitations=limitations)


def tracks_to_geojson(tracks: Iterable[Mapping[str, Any]] | Mapping[str, Any], *, crs: str | None = None,
                      source: str, period: str | None = None, units: str | None = None,
                      method: str = "direct coordinate export",
                      limitations: Sequence[str] = ()) -> dict[str, Any]:
    """Export supplied LineString/MultiLineString tracks, not inferred paths."""
    return _convert(tracks, allowed=frozenset({"LineString", "MultiLineString"}),
                    shorthand="LineString", crs=crs, source=source, period=period,
                    units=units, method=method, limitations=limitations)


def regions_to_geojson(regions: Iterable[Mapping[str, Any]] | Mapping[str, Any], *, crs: str | None = None,
                       source: str, period: str | None = None, units: str | None = None,
                       method: str = "direct coordinate export",
                       limitations: Sequence[str] = ()) -> dict[str, Any]:
    """Export supplied Polygon/MultiPolygon boundaries; never infer hazard extents."""
    return _convert(regions, allowed=frozenset({"Polygon", "MultiPolygon"}),
                    shorthand="Polygon", crs=crs, source=source, period=period,
                    units=units, method=method, limitations=limitations)
