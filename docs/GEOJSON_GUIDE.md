# NIElytics GeoJSON guide

NIElytics exports **caller-supplied** vector observations and boundaries, not inferred inundation, landslide extents, landfalls, or administrative boundaries. Import converters from `nielytics.geospatial`. Supply `crs="EPSG:4326"` explicitly for coordinate arrays: the first ordinate is **longitude** (−180 to 180), the second is **latitude** (−90 to 90). Other or unknown CRS values are rejected; reproject upstream before exporting. Large raster/gridded fields should stay in their native grid format, not be expanded into millions of GeoJSON polygons.

```python
import json
from nielytics.geospatial import points_to_geojson, tracks_to_geojson

# Synthetic demo coordinates; these are not confirmed disaster locations.
points = points_to_geojson(
    [{"longitude": 76.6, "latitude": 12.3,
      "properties": {"value": 40.0, "indicator": "temperature_threshold_exceeded"}}],
    crs="EPSG:4326", source="synthetic demonstration", period="2025-05-01",
    units="°C", method="caller-supplied threshold",
    limitations=["Not an official heatwave declaration."],
)
tracks = tracks_to_geojson(
    [{"coordinates": [[76.6, 12.3], [77.0, 13.0]],
      "properties": {"storm_id": "SYNTHETIC-01"}}],
    crs="EPSG:4326", source="synthetic demonstration",
    limitations=["Not a verified storm track or landfall."],
)
json.dumps({"points": points, "tracks": tracks}, allow_nan=False)
```

`to_geojson` accepts supplied Feature geometries of type Point, MultiPoint, LineString, MultiLineString, Polygon, or MultiPolygon. `regions_to_geojson` accepts caller-supplied Polygon/MultiPolygon coordinates; boundaries are never generated from point values. Polygon rings must be valid and closed. `get_hazard_map_layer` labels a supplied FeatureCollection by hazard without converting indicators into predictions. Each collection includes source, period, units, processing method, and limitations in metadata. Map renderers are owned by downstream applications; the library only supplies JSON-compatible data.
