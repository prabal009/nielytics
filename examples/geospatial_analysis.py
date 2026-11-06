"""Demonstrate India administrative hazard aggregation, hotspot detection, and GeoJSON export."""

import json
import pandas as pd
from nielytics.geospatial import (
    aggregate_hazards_by_region,
    detect_hazard_hotspots,
    generate_hazard_geojson,
    get_state_hazard_summary,
    normalize_state_name,
)


def main() -> None:
    print("=== NIElytics India Geospatial Analysis ===")

    # Sample hazard event catalog across Indian states
    events_df = pd.DataFrame({
        "state": ["Orissa", "Odisha", "Karnataka", "Karnataka", "West Bengal", "Delhi"],
        "district": ["Cuttack", "Bhubaneswar", "Bangalore", "Mysore", "Kolkata", "New Delhi"],
        "hazard": ["cyclone", "flood", "drought", "drought", "cyclone", "heatwave"],
        "value": [140.0, 180.0, -1.8, -2.1, 120.0, 46.5],
        "date": ["2023-05-15", "2023-08-10", "2023-06-01", "2023-06-15", "2023-05-20", "2023-06-10"],
        "latitude": [20.46, 20.29, 12.97, 12.29, 22.57, 28.61],
        "longitude": [85.88, 85.82, 77.59, 76.63, 88.36, 77.20],
    })

    # 1. State-level hazard aggregation
    agg_res = aggregate_hazards_by_region(events_df, region_type="state")
    print(f"Aggregated {agg_res.data['total_regions']} unique normalized Indian regions.")
    for state, info in agg_res.data["regions"].items():
        print(f" - {state}: {info['event_count']} events (Hazards: {info['hazards']})")

    # 2. State-specific profile
    odisha_profile = get_state_hazard_summary(events_df, state="orissa")
    print(f"\nOdisha Hazard Profile: {odisha_profile.data['summary']}")

    # 3. Spatial hotspot detection (clustering within 50 km)
    hotspots = detect_hazard_hotspots(events_df, min_events=2, radius_km=50.0)
    print(f"\nDetected {hotspots.data['hotspot_count']} spatial hazard hotspots.")

    # 4. RFC 7946 GeoJSON export for mapping
    geojson = generate_hazard_geojson(events_df, properties=["state", "hazard", "value"])
    print(f"Generated GeoJSON FeatureCollection with {len(geojson['features'])} features.")
    print(json.dumps(geojson["features"][0], indent=2))


if __name__ == "__main__":
    main()
