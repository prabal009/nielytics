"""Five offline synthetic hazard indicators; no real observations or warnings."""

import json

import pandas as pd

from nielytics import (
    CycloneAnalyzer,
    DroughtAnalyzer,
    FloodAnalyzer,
    HeatwaveAnalyzer,
    LandslideAnalyzer,
)
from nielytics.geospatial import points_to_geojson


def main() -> None:
    # Synthetic demonstration only: neither provider data nor official declarations.
    dates = pd.date_range("2025-05-01", periods=6, freq="D")
    rainfall = pd.DataFrame({"date": dates, "rainfall": [0., 0., 0., 42., 55., 4.]})
    temperature = pd.DataFrame({"date": dates, "tmax": [39., 41., 42., 43., 36., 35.]})
    terrain = rainfall.assign(slope=[30., 30., 30., 30., 30., 30.])
    storms = pd.DataFrame({
        "storm_id": ["SYNTHETIC-1", "SYNTHETIC-1"],
        "time": ["2025-05-01T00:00:00Z", "2025-05-01T06:00:00Z"],
        "latitude": [12.3, 12.7], "longitude": [76.6, 77.0],
        "wind": [65., 75.], "pressure": [995., 985.],
    })
    indicators = [
        HeatwaveAnalyzer(temperature, unit="C").heat_spell_duration(
            threshold_c=40., minimum_days=3),
        FloodAnalyzer(rainfall, unit="mm").cumulative_rainfall(window_days=3),
        DroughtAnalyzer(rainfall, unit="mm").dry_spell_duration(
            threshold_mm=1., minimum_days=3),
        CycloneAnalyzer(storms, wind_unit="km/h", pressure_unit="hPa").track_distance(),
        LandslideAnalyzer(terrain, rainfall_unit="mm", slope_unit="degrees")
        .susceptibility_indicators(window_days=2, rainfall_threshold_mm=70.,
                                   slope_threshold_degrees=25.),
    ]
    layer = points_to_geojson(
        [{"longitude": 76.6, "latitude": 12.3,
          "properties": {"type": "synthetic_input_location"}}],
        crs="EPSG:4326", source="synthetic demonstration", period="2025-05-01",
        limitations=["This point is not a confirmed hazard location."],
    )
    payload = {"synthetic": True, "indicators": [item.to_dict() for item in indicators],
               "map_layer": layer}
    print(json.dumps(payload, allow_nan=False, indent=2))


if __name__ == "__main__":
    main()
