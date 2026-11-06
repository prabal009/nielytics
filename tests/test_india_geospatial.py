import json
import pandas as pd
import pytest

from nielytics.geospatial import (
    aggregate_hazards_by_region,
    compare_hazard_regions,
    detect_hazard_hotspots,
    generate_hazard_geojson,
    get_district_hazard_summary,
    get_state_hazard_summary,
    get_state_reference,
    normalize_district_name,
    normalize_state_name,
    point_in_polygon,
)


def test_india_state_and_district_normalization():
    assert normalize_state_name("Orissa") == "Odisha"
    assert normalize_state_name("odisha") == "Odisha"
    assert normalize_state_name("Uttaranchal") == "Uttarakhand"
    assert normalize_state_name("Pondicherry") == "Puducherry"
    assert normalize_state_name("Mysore") == "Karnataka"
    assert normalize_state_name("Madras") == "Tamil Nadu"
    assert normalize_state_name("United Provinces") == "Uttar Pradesh"
    assert normalize_state_name("NCT of Delhi") == "Delhi"
    assert normalize_state_name("Jammu & Kashmir") == "Jammu and Kashmir"
    assert normalize_state_name("Nonexistent State") is None

    assert normalize_district_name("bangalore") == "Bengaluru Urban"
    assert normalize_district_name("gurgaon") == "Gurugram"
    assert normalize_district_name("calcutta") == "Kolkata"
    assert normalize_district_name("allahabad") == "Prayagraj"


def test_state_references_and_polygon():
    odisha_ref = get_state_reference("Odisha")
    assert odisha_ref is not None
    assert 20.0 <= odisha_ref["centroid"][0] <= 22.0

    # Test point-in-polygon with a simple triangle
    triangle = [(0.0, 0.0), (5.0, 0.0), (0.0, 5.0)]
    assert point_in_polygon(1.0, 1.0, triangle)
    assert not point_in_polygon(10.0, 10.0, triangle)


def test_regional_hazard_aggregation_and_summary():
    data = pd.DataFrame({
        "state": ["Orissa", "Odisha", "Karnataka", "Karnataka", "Delhi"],
        "district": ["Bhubaneswar", "Cuttack", "Bangalore", "Mysore", "New Delhi"],
        "hazard": ["flood", "cyclone", "drought", "drought", "heatwave"],
        "value": [120.0, 150.0, -1.8, -2.1, 45.5],
        "date": ["2023-08-01", "2023-08-02", "2023-05-10", "2023-05-11", "2023-06-01"],
    })

    res = aggregate_hazards_by_region(data, region_type="state")
    assert res.feature == "regional_hazard_aggregation"
    payload = res.to_dict()
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload

    regions = res.data["regions"]
    assert "Odisha" in regions
    assert regions["Odisha"]["event_count"] == 2
    assert "Karnataka" in regions
    assert regions["Karnataka"]["event_count"] == 2

    # State summary
    state_res = get_state_hazard_summary(data, state="orissa")
    assert state_res.data["state"] == "Odisha"
    assert state_res.data["summary"]["event_count"] == 2

    # District summary
    dist_res = get_district_hazard_summary(data, district="bangalore", state="Karnataka")
    assert dist_res.data["district"] == "Bengaluru Urban"
    assert dist_res.data["summary"]["event_count"] == 1


def test_hotspot_detection_and_comparison():
    data = pd.DataFrame({
        "latitude": [12.97, 12.98, 12.96, 28.61],
        "longitude": [77.59, 77.60, 77.58, 77.20],
        "state": ["Karnataka", "Karnataka", "Karnataka", "Delhi"],
    })

    hotspots = detect_hazard_hotspots(data, min_events=3, radius_km=30.0)
    assert hotspots.data["hotspot_count"] == 1
    assert hotspots.data["hotspots"][0]["event_count"] == 3

    comp = compare_hazard_regions(data, regions=["Karnataka", "Delhi", "Goa"])
    assert comp.feature == "regional_hazard_comparison"
    assert "Karnataka" in comp.data["comparison"]
    assert "Delhi" in comp.data["comparison"]
    assert "Goa" in comp.data["comparison"]


def test_generate_hazard_geojson():
    data = pd.DataFrame({
        "latitude": [19.07, 28.61],
        "longitude": [72.87, 77.20],
        "name": ["Mumbai", "Delhi"],
        "temp": [32.0, 42.0],
    })
    gj = generate_hazard_geojson(data)
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) == 2
    assert gj["features"][0]["geometry"]["coordinates"] == [72.87, 19.07]
    assert gj["features"][0]["properties"]["name"] == "Mumbai"
    assert json.loads(json.dumps(gj, allow_nan=False)) == gj
