import json
import numpy as np
import pandas as pd
import pytest

from nielytics.hazards import (
    CycloneAnalyzer,
    DroughtAnalyzer,
    FloodAnalyzer,
    HeatwaveAnalyzer,
    LandslideAnalyzer,
    MultiHazardAnalyzer,
)


def test_heatwave_imd_classification_and_percentiles():
    dates = pd.date_range("2023-05-01", periods=10, freq="D").strftime("%Y-%m-%d")
    # Plains: normal is 40.0. Departures: 45 is +5 (heatwave), 47 is severe, 38 is no heatwave
    temps = [38.0, 42.0, 45.0, 46.0, 47.5, 41.0, 39.0, 44.5, 45.5, 37.0]
    df = pd.DataFrame({"date": dates, "tmax": temps})
    analyzer = HeatwaveAnalyzer(df, unit="C")

    imd_res = analyzer.imd_heatwave_classification(normal_tmax=40.0, terrain="plains")
    assert imd_res.feature == "imd_heatwave_classification"
    payload = imd_res.to_dict()
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload

    counts = imd_res.data["counts"]
    assert counts["heatwave"] > 0
    assert counts["severe_heatwave"] > 0

    freq_res = analyzer.historical_heatwave_frequency(threshold_c=45.0)
    assert freq_res.feature == "historical_heatwave_frequency"
    assert "annual_frequencies" in freq_res.data


def test_flood_imd_rainfall_and_accumulation():
    dates = pd.date_range("2023-07-01", periods=8, freq="D").strftime("%Y-%m-%d")
    # IMD categories: 0=no rain, 10=light, 35=moderate, 75=heavy, 150=very heavy, 220=extremely heavy
    rain = [0.0, 10.0, 35.0, 75.0, 150.0, 220.0, 5.0, 0.0]
    df = pd.DataFrame({"date": dates, "rainfall": rain})
    analyzer = FloodAnalyzer(df, unit="mm")

    imd_res = analyzer.imd_rainfall_classification()
    assert imd_res.feature == "imd_rainfall_classification"
    counts = imd_res.data["category_counts"]
    assert counts["heavy"] == 1
    assert counts["very_heavy"] == 1
    assert counts["extremely_heavy"] == 1
    assert counts["moderate"] == 1

    accum_res = analyzer.multi_day_accumulation(windows=[2, 3])
    assert "2_day" in accum_res.data["windows"]
    assert accum_res.data["windows"]["2_day"]["max_accumulation_mm"] > 200.0


def test_drought_standardized_precipitation_index():
    # 24 months of synthetic rainfall
    dates = pd.date_range("2021-01-01", periods=24, freq="MS").strftime("%Y-%m-%d")
    rain = [50.0, 40.0, 30.0, 0.0, 10.0, 150.0, 250.0, 200.0, 100.0, 20.0, 10.0, 5.0] * 2
    df = pd.DataFrame({"date": dates, "rainfall": rain})
    analyzer = DroughtAnalyzer(df, unit="mm")

    spi_res = analyzer.standardized_precipitation_index(scale_months=3)
    assert spi_res.feature == "spi_3"
    records = spi_res.data["records"]
    assert len(records) > 0
    assert "spi" in records[0]
    assert "category" in records[0]
    assert -4.0 <= records[0]["spi"] <= 4.0

    seasonal = analyzer.seasonal_rainfall_anomaly(monsoon_months=[6, 7, 8, 9])
    assert seasonal.feature == "seasonal_monsoon_anomaly"
    assert len(seasonal.data["seasons"]) == 2


def test_landslide_trigger_and_slope_screening():
    dates = pd.date_range("2023-08-01", periods=10, freq="D").strftime("%Y-%m-%d")
    rain = [20.0, 50.0, 60.0, 70.0, 10.0, 5.0, 0.0, 0.0, 0.0, 0.0]
    slope = [25.0] * 10
    df = pd.DataFrame({"date": dates, "rainfall": rain, "slope": slope})
    analyzer = LandslideAnalyzer(df, rainfall_unit="mm", slope_unit="degrees")

    trig = analyzer.rainfall_trigger_indicator(
        antecedent_window_days=3,
        antecedent_threshold_mm=80.0,
        trigger_rainfall_threshold_mm=50.0,
    )
    assert trig.feature == "landslide_rainfall_trigger_indicator"
    assert trig.data["trigger_events_count"] >= 1

    slope_scr = analyzer.slope_elevation_screening(min_slope_degrees=20.0)
    assert slope_scr.data["steep_terrain_days"] == 10


def test_cyclone_imd_scale_and_landfall():
    times = [
        "2023-11-15T00:00:00Z",
        "2023-11-15T06:00:00Z",
        "2023-11-15T12:00:00Z",
        "2023-11-15T18:00:00Z",
    ]
    # Cyclone with peak wind 140 km/h -> Very Severe Cyclonic Storm
    df = pd.DataFrame({
        "storm_id": ["STORM_01"] * 4,
        "time": times,
        "latitude": [18.0, 18.5, 19.0, 19.5],
        "longitude": [86.0, 85.8, 85.5, 85.2],
        "wind": [70.0, 100.0, 140.0, 90.0],
        "pressure": [995.0, 985.0, 965.0, 980.0],
    })
    analyzer = CycloneAnalyzer(df, wind_unit="km/h", pressure_unit="hPa")

    imd_res = analyzer.imd_cyclone_classification()
    assert imd_res.data["category_counts"]["Very Severe Cyclonic Storm"] == 1

    landfall = analyzer.landfall_analysis(proximity_threshold_km=100.0)
    assert landfall.feature == "cyclone_landfall_analysis"
    assert landfall.data["storms"][0]["closest_coast_distance_km"] < 150.0

    converted = analyzer.convert_wind_units(from_unit="km/h", to_unit="knots")
    assert converted["wind"].iloc[0] == pytest.approx(70.0 / 1.852, abs=0.1)


def test_multi_hazard_analyzer():
    dates = pd.date_range("2023-05-01", periods=5, freq="D").strftime("%Y-%m-%d")
    heat_df = pd.DataFrame({"date": dates, "tmax": [41.0, 42.0, 38.0, 43.0, 39.0]})
    drought_df = pd.DataFrame({"date": dates, "rainfall": [0.0, 0.0, 15.0, 0.0, 5.0]})

    res = MultiHazardAnalyzer.compare_heat_and_drought(
        heat_df, drought_df, temp_threshold_c=40.0, rain_threshold_mm=1.0,
    )
    assert res.feature == "compound_heat_drought"
    assert res.data["compound_event_days"] == 3  # days 0, 1, 3 meet both conditions

    # Composite indicator
    comp = MultiHazardAnalyzer.composite_hazard_indicator(
        {"heat_risk": 45.0, "flood_risk": 200.0, "drought_risk": 0.8},
        weights={"heat_risk": 0.4, "flood_risk": 0.4, "drought_risk": 0.2},
    )
    assert comp.feature == "composite_hazard_indicator"
    assert 0.0 <= comp.data["composite_score"] <= 100.0
    assert "mathematical_formula" in comp.data
