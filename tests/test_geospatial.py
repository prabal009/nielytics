"""WGS84-only GeoJSON conversion, topology guards and scientific provenance."""

import copy
import json
from fractions import Fraction

import numpy as np
import pytest

from nielytics.exceptions import ValidationError
from nielytics.geospatial import (
    get_hazard_locations,
    get_hazard_map_layer,
    get_regional_hazard_data,
    points_to_geojson,
    regions_to_geojson,
    to_geojson,
    tracks_to_geojson,
    validate_coordinates,
)

CRS = "EPSG:4326"
RING = [[70, 10], [72, 10], [72, 12], [70, 12]]


def test_explicit_coordinate_order_and_boundaries():
    assert validate_coordinates(180, -90, crs=CRS) == (180., -90.)
    assert validate_coordinates(-180, 90, crs=CRS) == (-180., 90.)
    result = points_to_geojson([
        {"longitude": 77.1, "latitude": 28.6,
         "properties": {"temperature": 40.5},
         "provenance": {"source_dataset": "observation series"}},
    ], crs=CRS, source="station observations", period="2024-05-01", units="°C",
       method="reported station value", limitations=["Not an official heatwave declaration."])
    assert result["features"][0]["geometry"] == {
        "type": "Point", "coordinates": [77.1, 28.6],
    }
    provenance = result["features"][0]["properties"]["provenance"]
    assert provenance["source"] == "station observations"
    assert provenance["source_dataset"] == "observation series"
    assert provenance["period"] == "2024-05-01"
    assert provenance["units"] == "°C"
    assert provenance["method"] == "reported station value"
    assert provenance["limitations"][0] == "Not an official heatwave declaration."
    assert result["metadata"]["crs"] == CRS
    assert "bbox" not in result
    assert json.loads(json.dumps(result, allow_nan=False)) == result


@pytest.mark.parametrize("kind,coordinates", [
    ("Point", [77, 29]),
    ("MultiPoint", [[77, 29], [78, 30]]),
    ("LineString", [[77, 29], [78, 30]]),
    ("MultiLineString", [[[77, 29], [78, 30]], [[79, 30], [80, 31]]]),
    ("Polygon", [RING]),
    ("MultiPolygon", [[RING], [[[74, 20], [75, 20], [75, 21], [74, 21]]]]),
])
def test_six_supported_geometries_preserve_input(kind, coordinates):
    records = [{"geometry": {"type": kind, "coordinates": coordinates},
                "properties": {"id": 3}}]
    original = copy.deepcopy(records)
    result = to_geojson(records, crs=CRS, source="supplied survey")
    assert result["type"] == "FeatureCollection"
    assert result["features"][0]["geometry"]["type"] == kind
    assert result["features"][0]["properties"]["id"] == 3
    assert records == original
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    if "Polygon" in kind:
        geometry = result["features"][0]["geometry"]["coordinates"]
        rings = geometry if kind == "Polygon" else geometry[0]
        assert rings[0][0] == rings[0][-1]
        assert len(rings[0]) == 5


def test_numpy_coordinates_and_explicit_unknown_period_and_units():
    out = points_to_geojson([{"geometry": {"type": "MultiPoint",
                                              "coordinates": np.array([[74., 18.], [75., 19.]])}}],
                            crs=CRS, source="survey")
    assert out["features"][0]["geometry"]["coordinates"] == [[74, 18], [75, 19]]
    assert out["metadata"]["period"] is None
    assert out["metadata"]["units"] is None


def test_shorthand_tracks_regions_and_holes_are_distinct():
    lines = tracks_to_geojson([{"coordinates": [[70, 10], [71, 11]]}],
                              crs=CRS, source="historical track")
    assert lines["features"][0]["geometry"]["type"] == "LineString"
    hole = [[70.5, 10.5], [71, 10.5], [71, 11], [70.5, 11]]
    regions = regions_to_geojson([{"coordinates": [RING, hole]}],
                                 crs=CRS, source="survey boundary")
    rings = regions["features"][0]["geometry"]["coordinates"]
    assert rings[1][0] == rings[1][-1]
    assert len(rings) == 2


@pytest.mark.parametrize("lon,lat", [
    (None, 20), (20, None), (True, 20), (20, False), ("77", 20),
    (181, 20), (-181, 20), (70, 91), (70, -91),
    (float("nan"), 20), (float("inf"), 20), (70, -float("inf")),
    (1 + 2j, 20),
])
def test_bad_coordinates_are_rejected(lon, lat):
    with pytest.raises(ValidationError):
        validate_coordinates(lon, lat, crs=CRS)


@pytest.mark.parametrize("lon,lat", [
    (Fraction(180 * 10**30 + 1, 10**30), 20),
    (70, Fraction(90 * 10**30 + 1, 10**30)),
])
def test_out_of_range_precise_coordinates_cannot_round_into_bounds(lon, lat):
    with pytest.raises(ValidationError):
        validate_coordinates(lon, lat, crs=CRS)
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": lon, "latitude": lat}],
                          crs=CRS, source="survey")


@pytest.mark.parametrize("crs", [None, "", "EPSG:3857", "EPSG:32643", "OGC:CRS84", 4326])
def test_explicit_wgs84_is_required_for_all_entry_points(crs):
    with pytest.raises(ValidationError):
        validate_coordinates(77, 28, crs=crs)
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": 77, "latitude": 28}],
                          crs=crs, source="survey")
    with pytest.raises(ValidationError):
        to_geojson([], crs=crs, source="survey")


@pytest.mark.parametrize("geometry", [
    {"type": "Point", "coordinates": [70]},
    {"type": "Point", "coordinates": [70, 20, 5]},
    {"type": "Point", "coordinates": [70, float("nan")]},
    {"type": "Point", "coordinates": [70, 20], "crs": "EPSG:3857"},
    {"type": "GeometryCollection", "geometries": []},
    {"type": "MultiPoint", "coordinates": []},
    {"type": "LineString", "coordinates": [[70, 20]]},
    {"type": "LineString", "coordinates": [[70, 20], [70, 20]]},
    {"type": "LineString", "coordinates": [[70, 20], [70, 20], [71, 21]]},
    {"type": "MultiLineString", "coordinates": [[[70, 20], [71, 21], [71, 21]]]},
    {"type": "MultiLineString", "coordinates": []},
    {"type": "MultiLineString", "coordinates": [[[70, 20]]]},
    {"type": "Polygon", "coordinates": []},
    {"type": "Polygon", "coordinates": [[[70, 20], [71, 20]]]},
    {"type": "Polygon", "coordinates": [[[70, 20], [71, 20], [72, 20]]]},
    {"type": "Polygon", "coordinates": [[[70, 20], [72, 22], [70, 22], [72, 20]]]},
    {"type": "Polygon", "coordinates": [RING, [[90, 20], [91, 20], [91, 21]]]},
    {"type": "MultiPolygon", "coordinates": []},
])
def test_malformed_geometries_are_rejected(geometry):
    with pytest.raises(ValidationError):
        to_geojson([{"geometry": geometry}], crs=CRS, source="survey")


@pytest.mark.parametrize("properties", [
    {"value": float("inf")}, {"value": float("nan")},
    {"value": object()}, {3: "nonstring key"},
    {"value": np.int64(3)},
])
def test_metadata_and_properties_must_be_strict_json(properties):
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": 70, "latitude": 20,
                            "properties": properties}], crs=CRS, source="survey")


def test_invalid_provenance_or_unstated_source_is_rejected():
    with pytest.raises(ValidationError):
        to_geojson([], crs=CRS, source="")
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": 70, "latitude": 20,
                            "provenance": {"source": ""}}], crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": 70, "latitude": 20,
                            "provenance": {"quantity": float("nan")}}],
                          crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        to_geojson([], crs=CRS, source="survey", limitations=["valid", ""])


def test_per_feature_provenance_override_is_validated_and_isolated():
    records = [{"longitude": 70, "latitude": 20,
                "provenance": {"source": "local station", "period": "2025-06-01",
                               "limitations": ["Incomplete coverage."]}}]
    exported = points_to_geojson(records, crs=CRS, source="umbrella survey")
    provenance = exported["features"][0]["properties"]["provenance"]
    assert provenance["source"] == "local station"
    assert provenance["period"] == "2025-06-01"
    assert provenance["limitations"][0] == "Incomplete coverage."
    assert exported["metadata"]["source"] == "umbrella survey"
    assert records[0]["provenance"]["source"] == "local station"
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": 70, "latitude": 20,
                            "provenance": {"period": 2025}}], crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": 70, "latitude": 20,
                            "provenance": {"source": "local"},
                            "properties": {"provenance": {"source": "other"}}}],
                          crs=CRS, source="survey")


def test_featurecollection_input_preserves_ids_and_validates_records():
    collection = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": "site-1",
         "geometry": {"type": "Point", "coordinates": [78, 30]},
         "properties": {"observed": True}},
        {"type": "Feature", "id": 2,
         "geometry": {"type": "Point", "coordinates": [79, 31]}},
    ]}
    original = copy.deepcopy(collection)
    out = to_geojson(collection, crs=CRS, source="survey")
    assert [feature["id"] for feature in out["features"]] == ["site-1", 2]
    assert out["features"][0]["properties"]["observed"] is True
    assert out["metadata"]["source"] == "survey"
    assert collection == original
    for bad in (True, None, float("nan"), {"value": 1}):
        broken = copy.deepcopy(collection)
        broken["features"][0]["id"] = bad
        with pytest.raises(ValidationError):
            to_geojson(broken, crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        to_geojson({"type": "FeatureCollection", "features": [],
                    "metadata": {"source": "unverified"}},
                   crs=CRS, source="survey")


def test_cyclic_properties_and_conflicting_feature_crs_raise_validation_error():
    properties = {}
    properties["self"] = properties
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": 70, "latitude": 20,
                            "properties": properties}], crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        points_to_geojson([{"longitude": 70, "latitude": 20,
                            "provenance": {"crs": "EPSG:3857"}}],
                          crs=CRS, source="survey")


def test_multipart_regions_cannot_contain_overlapping_components():
    overlapping = [[RING], [[[71, 11], [73, 11], [73, 13], [71, 13]]]]
    with pytest.raises(ValidationError):
        to_geojson([{"geometry": {"type": "MultiPolygon",
                                  "coordinates": overlapping}}], crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        points_to_geojson([{"crs": "EPSG:3857", "longitude": 70, "latitude": 20}],
                          crs=CRS, source="survey")


def test_polygon_holes_and_multipolygon_islands_respect_planar_topology():
    outer = [[0, 0], [10, 0], [10, 10], [0, 10]]
    hole = [[2, 2], [8, 2], [8, 8], [2, 8]]
    island = [[3, 3], [4, 3], [4, 4], [3, 4]]
    result = regions_to_geojson([{"geometry": {
        "type": "MultiPolygon", "coordinates": [[outer, hole], [island]],
    }}], crs=CRS, source="survey")
    assert len(result["features"][0]["geometry"]["coordinates"]) == 2
    touching_hole = [[0, 3], [2, 3], [2, 5], [0, 5]]
    with pytest.raises(ValidationError):
        regions_to_geojson([{"coordinates": [outer, touching_hole]}],
                           crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        regions_to_geojson([{"geometry": {
            "type": "MultiPolygon", "coordinates": [[outer, hole], [outer]],
        }}], crs=CRS, source="survey")


def test_specialized_exporters_reject_incorrect_geometry_without_fabricating_features():
    with pytest.raises(ValidationError):
        points_to_geojson([{"geometry": {"type": "Polygon", "coordinates": [RING]}}],
                          crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        tracks_to_geojson([{"coordinates": [[70, 20]]}], crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        regions_to_geojson([{"geometry": {"type": "Point", "coordinates": [70, 20]}}],
                           crs=CRS, source="survey")


def test_map_layers_require_supplied_geometry_and_preserve_hazard_provenance():
    point = {"longitude": 78, "latitude": 30, "properties": {"rainfall": 120}}
    layer = get_hazard_locations("flood", [point], crs=CRS, source="gauge observations",
                                 units="mm", method="measured rainfall",
                                 limitations=["Rainfall alone does not confirm a flood."])
    assert layer["metadata"]["hazard"] == "flood"
    assert layer["features"][0]["properties"]["rainfall"] == 120
    assert "Rainfall alone does not confirm a flood." in layer["metadata"]["limitations"]
    area = get_regional_hazard_data("drought", [{"coordinates": [RING]}],
                                    crs=CRS, source="mapped district boundary")
    assert area["features"][0]["geometry"]["type"] == "Polygon"
    track = get_hazard_map_layer("cyclone", [{"geometry": {
        "type": "LineString", "coordinates": [[70, 20], [72, 21]],
    }}], crs=CRS, source="historical best-track")
    assert track["features"][0]["geometry"]["type"] == "LineString"
    assert json.loads(json.dumps(track, allow_nan=False)) == track
    with pytest.raises(ValidationError):
        get_hazard_map_layer("earthquake", [], crs=CRS, source="survey")
    with pytest.raises(ValidationError):
        get_hazard_map_layer("flood", [{"properties": {"value": 10}}],
                             crs=CRS, source="gauge observations")


@pytest.mark.parametrize("exporter,records", [
    (get_hazard_map_layer, [{"geometry": {"type": "Point", "coordinates": [70, 20]}}]),
    (get_hazard_locations, [{"longitude": 70, "latitude": 20}]),
    (get_regional_hazard_data, [{"coordinates": [RING]}]),
])
def test_map_layer_hazard_metadata_and_validation_precede_feature_consumption(exporter, records):
    layer = exporter("flood", records, crs=CRS, source="mapped observations")
    assert layer["metadata"]["hazard"] == "flood"
    assert layer["metadata"]["crs"] == CRS
    assert layer["features"][0]["properties"]["provenance"]["source"] == "mapped observations"
    consumed = False

    def source():
        nonlocal consumed
        consumed = True
        yield from records

    with pytest.raises(ValidationError, match="hazard"):
        exporter("earthquake", source(), crs=CRS, source="mapped observations")
    assert not consumed
