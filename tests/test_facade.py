import json

import pandas as pd

from nielytics.facade import ClimateAnalytics


def test_climate_analytics_facade_end_to_end():
    analytics = ClimateAnalytics(offline=True)

    # 1. Register heatwave dataset
    dates = pd.date_range("2023-05-01", periods=5, freq="D").strftime("%Y-%m-%d")
    heat_df = pd.DataFrame({
        "timestamp": dates,
        "state_name": ["Punjab", "Punjab", "Punjab", "Odisha", "Odisha"],
        "temp_c": [41.0, 45.5, 47.2, 38.0, 42.0],
        "lat": [31.14, 31.14, 31.14, 20.95, 20.95],
        "lon": [75.34, 75.34, 75.34, 85.09, 85.09],
    })
    analytics.register_dataset(
        hazard="heatwave",
        data=heat_df,
        schema={
            "date_column": "timestamp",
            "value_column": "temp_c",
            "state_column": "state_name",
            "latitude_column": "lat",
            "longitude_column": "lon",
            "metric": "tmax",
            "source_unit": "C",
            "target_unit": "C",
        },
    )

    # 2. Register flood dataset
    flood_df = pd.DataFrame({
        "timestamp": dates,
        "state_name": ["Odisha", "Odisha", "Odisha", "Odisha", "Odisha"],
        "rain_mm": [50.0, 80.0, 160.0, 210.0, 10.0],
        "lat": [20.95] * 5,
        "lon": [85.09] * 5,
    })
    analytics.register_dataset(
        hazard="flood",
        data=flood_df,
        schema={
            "date_column": "timestamp",
            "value_column": "rain_mm",
            "state_column": "state_name",
            "latitude_column": "lat",
            "longitude_column": "lon",
            "metric": "rainfall",
            "source_unit": "mm",
            "target_unit": "mm",
        },
    )

    # 3. Analyze heatwave in Punjab
    hw_res = analytics.analyze(hazard="heatwave", region="Punjab")
    assert hw_res.feature == "imd_heatwave_classification"
    assert hw_res.data["counts"]["heatwave"] >= 1
    assert hw_res.data["counts"]["severe_heatwave"] >= 1

    # 4. Analyze flood in Odisha
    fl_res = analytics.analyze(hazard="flood", region="Odisha")
    assert fl_res.feature == "imd_rainfall_classification"
    assert fl_res.data["category_counts"]["extremely_heavy"] == 1

    # 5. Multi-hazard comparison
    comp_res = analytics.compare_hazards()
    assert comp_res.feature == "regional_multi_hazard_overlap"
    assert "Odisha" in comp_res.data["matrix"]
    assert comp_res.data["matrix"]["Odisha"]["multi_hazard_exposed"]

    # 6. Get insights
    insights_res = analytics.get_insights()
    assert insights_res.feature == "deterministic_insights"
    assert len(insights_res.data["insights"]) > 0

    # 7. GeoJSON export
    gj = analytics.to_geojson()
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) > 0
    assert json.loads(json.dumps(gj, allow_nan=False)) == gj
