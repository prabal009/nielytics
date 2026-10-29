"""Offline numerical and scientific-boundary tests for five hazard analyzers."""
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from nielytics.exceptions import ValidationError
from nielytics.hazards import (
    CycloneAnalyzer,
    DroughtAnalyzer,
    FloodAnalyzer,
    HeatwaveAnalyzer,
    LandslideAnalyzer,
)


def test_heat_episodes_anomaly_baseline_and_nonmutation():
    original = pd.DataFrame({"date": ["2020-01-06", "2020-01-01", "2020-01-02",
                                      "2020-01-03", "2020-01-05"],
                             "tmax": [43.0, 38.0, 40.0, 41.0, 42.0]})
    before = original.copy(deep=True)
    analyzer = HeatwaveAnalyzer(original, unit="C", latitude=25, longitude=78)
    episodes = analyzer.heat_spell_duration(threshold_c=40, minimum_days=2).to_dict()
    assert episodes["data"]["episodes"] == [
        {"start": "2020-01-02", "end": "2020-01-03", "days": 2, "peak": 41.0},
        {"start": "2020-01-05", "end": "2020-01-06", "days": 2, "peak": 43.0},
    ]
    assert episodes["metadata"]["location"] == {"latitude": 25.0, "longitude": 78.0}
    assert episodes["metadata"]["threshold_c"] == 40
    assert episodes["metadata"]["period"] == {"start": "2020-01-01", "end": "2020-01-06"}
    assert "official heatwave" in episodes["warnings"][0]
    assert analyzer.extreme_heat_days(threshold_c=40).data["count"] == 4
    anomaly = analyzer.temperature_anomaly(baseline_start="2020-01-01", baseline_end="2020-01-02",
                                           start="2020-01-05", end="2020-01-06")
    assert anomaly.data["baseline_mean_c"] == 39
    assert anomaly.data["anomaly_c"] == 3.5
    assert_frame_equal(original, before)
    with pytest.raises(ValidationError, match="baseline"):
        analyzer.temperature_anomaly(baseline_start="2020-01-01", baseline_end="2020-01-01")


def test_flood_complete_windows_wet_spell_and_recorded_events_separate():
    data = pd.DataFrame({"date": ["2020-06-01", "2020-06-02", "2020-06-03",
                                  "2020-06-05", "2020-06-06"],
                         "rainfall": pd.Series([10, 20, pd.NA, 30, 40], dtype="Float64")})
    before = data.copy(deep=True)
    analyzer = FloodAnalyzer(data, unit="mm")
    totals = analyzer.cumulative_rainfall(window_days=2).to_dict()
    assert [item["total"] for item in totals["data"]["windows"]] == [30, 70]
    assert [item["end"] for item in totals["data"]["windows"]] == ["2020-06-02", "2020-06-06"]
    assert any("Missing calendar dates" in warning for warning in totals["warnings"])
    assert any("Missing measurements" in warning for warning in totals["warnings"])
    assert analyzer.wet_spell_duration(threshold_mm=15).data["episodes"] == [
        {"start": "2020-06-05", "end": "2020-06-06", "days": 2, "peak": 40.0}
    ]
    events = pd.DataFrame({"date": ["2020-06-01", "2020-07-02", "2021-01-01"]})
    events_before = events.copy(deep=True)
    recorded = analyzer.flood_event_frequency(events).to_dict()
    assert recorded["metadata"]["kind"] == "historical_recorded_events"
    assert recorded["data"]["years"] == [{"year": 2020, "events": 2},
                                             {"year": 2021, "events": 1}]
    assert totals["metadata"]["kind"] == "proxy_indicator"
    assert_frame_equal(data, before)
    assert_frame_equal(events, events_before)


def test_drought_deficit_dry_spell_and_zero_baseline():
    data = pd.DataFrame({"date": pd.date_range("2020-07-01", periods=5),
                         "rainfall": [5, 5, 0, 0, 0]})
    analyzer = DroughtAnalyzer(data, unit="mm")
    deficit = analyzer.rainfall_deficit(baseline_start="2020-07-01", baseline_end="2020-07-02",
                                       start="2020-07-03", end="2020-07-05").to_dict()
    assert deficit["data"]["deficit_mm_per_day"] == 5
    assert deficit["data"]["deficit_percent"] == 100
    dry = analyzer.dry_spell_duration(minimum_days=3).to_dict()
    assert dry["data"]["episodes"][0]["days"] == 3
    assert dry["data"]["episodes"][0]["peak"] == 0
    zero = DroughtAnalyzer(pd.DataFrame({"date": pd.date_range("2021-01-01", periods=3),
                                          "rainfall": [0, 0, 4]}), unit="mm")
    baseline = zero.rainfall_deficit(baseline_start="2021-01-01", baseline_end="2021-01-02",
                                     start="2021-01-03", end="2021-01-03")
    assert baseline.to_dict()["data"]["deficit_percent"] is None
    assert any("undefined" in warning for warning in baseline.warnings)


def test_cyclone_ordered_track_distance_intensity_and_nearest_observation():
    data = pd.DataFrame({"storm_id": ["A", "A", "B", "A"],
                         "time": ["2020-06-01T12:00:00", "2020-06-01T00:00:00",
                                  "2021-01-01T00:00:00", "2020-06-02T00:00:00"],
                         "latitude": [0, 0, 10, 0], "longitude": [1, 0, 70, 2],
                         "wind": [80, 50, None, 70], "pressure": [980, 990, None, 985]})
    before = data.copy(deep=True)
    analyzer = CycloneAnalyzer(data, wind_unit="km/h", pressure_unit="hPa")
    tracks = analyzer.track_distance().to_dict()
    assert tracks["data"]["storms"][0]["distance_km"] == pytest.approx(222.39, abs=0.02)
    assert tracks["data"]["storms"][0]["segments_km"] == pytest.approx([111.195, 111.195], abs=0.02)
    assert tracks["data"]["storms"][1]["distance_km"] == 0
    intensity = analyzer.cyclone_intensity().to_dict()["data"]["storms"]
    assert intensity[0]["max_wind_kmh"] == 80
    assert intensity[0]["min_pressure_hpa"] == 980
    assert intensity[1]["max_wind_kmh"] is None
    assert analyzer.cyclone_frequency().data["years"] == [
        {"year": 2020, "storms": 1}, {"year": 2021, "storms": 1}]
    proximity = analyzer.proximity(latitude=0, longitude=0, radius_km=120).to_dict()
    assert proximity["data"]["storms"][0]["closest_observed_km"] == 0
    assert proximity["data"]["storms"][0]["within_radius"] is True
    assert proximity["metadata"]["method"].startswith("nearest sampled")
    assert_frame_equal(data, before)


def test_landslide_excludes_assessment_day_and_flags_missing_history_unknown():
    data = pd.DataFrame({"date": pd.date_range("2020-08-01", periods=4),
                         "rainfall": [10, 20, 30, 40], "slope": [10, 20, 30, 40]})
    before = data.copy(deep=True)
    analyzer = LandslideAnalyzer(data, rainfall_unit="mm", slope_unit="degrees")
    rain = analyzer.antecedent_rainfall(window_days=2).to_dict()["data"]["days"]
    assert rain == [{"date": "2020-08-03", "antecedent_mm": 30.0},
                    {"date": "2020-08-04", "antecedent_mm": 50.0}]
    screened = analyzer.susceptibility_indicators(window_days=2,
                                                   rainfall_threshold_mm=30,
                                                   slope_threshold_degrees=25).to_dict()
    assert [day["meets_thresholds"] for day in screened["data"]["days"]] == [True, True]
    assert screened["data"]["unknown_days"] == 2
    assert "not a validated landslide prediction" in screened["warnings"][0]
    assert_frame_equal(data, before)
    events = pd.DataFrame({"date": ["2020-08-01", "2020-08-01", "2021-09-01"]})
    events_before = events.copy(deep=True)
    assert analyzer.landslide_frequency(events).data["years"] == [
        {"year": 2020, "events": 2}, {"year": 2021, "events": 1}]
    assert_frame_equal(events, events_before)


@pytest.mark.parametrize("analyzer,unit", [(HeatwaveAnalyzer, "C"),
                                             (FloodAnalyzer, "mm"), (DroughtAnalyzer, "mm")])
def test_daily_validation_rejects_duplicate_dates_missing_dates_bad_units(analyzer, unit):
    measure = "tmax" if analyzer is HeatwaveAnalyzer else "rainfall"
    with pytest.raises(ValidationError, match="duplicate"):
        analyzer(pd.DataFrame({"date": ["2020-01-01"] * 2, measure: [1, 2]}), unit=unit)
    with pytest.raises(ValidationError, match="dates cannot be missing"):
        analyzer(pd.DataFrame({"date": [None], measure: [1]}), unit=unit)
    with pytest.raises(ValidationError, match="not numeric values"):
        analyzer(pd.DataFrame({"date": ["2020-01-01", 1], measure: [1, 2]}), unit=unit)
    with pytest.raises(ValidationError, match="observed value"):
        analyzer(pd.DataFrame({"date": ["2020-01-01"], measure: [float("nan")]}), unit=unit)
    with pytest.raises(ValidationError, match="unit"):
        analyzer(pd.DataFrame({"date": ["2020-01-01"], measure: [1]}), unit="unspecified")
    with pytest.raises(ValidationError, match="latitude and longitude"):
        analyzer(pd.DataFrame({"date": ["2020-01-01"], measure: [1]}), unit=unit, latitude=20)


def test_missing_measurement_ends_spells_and_gap_does_not_forge_zero_rain():
    data = pd.DataFrame({"date": ["2020-01-01", "2020-01-02", "2020-01-04",
                                  "2020-01-05", "2020-01-06"],
                         "rainfall": [0.0, None, 0.0, 0.0, 0.0]})
    drought = DroughtAnalyzer(data, unit="mm")
    assert drought.dry_spell_duration(minimum_days=3).data["episodes"] == [
        {"start": "2020-01-04", "end": "2020-01-06", "days": 3, "peak": 0.0}]
    assert FloodAnalyzer(data, unit="mm").cumulative_rainfall(window_days=3).data["windows"] == [
        {"start": "2020-01-04", "end": "2020-01-06", "total": 0.0}]
    slope_data = data.assign(slope=30.0)
    indicator = LandslideAnalyzer(slope_data, rainfall_unit="mm", slope_unit="degrees")
    assert indicator.antecedent_rainfall(window_days=2).data["days"] == [
        {"date": "2020-01-06", "antecedent_mm": 0.0}]


def test_invalid_numeric_and_cyclone_track_boundaries():
    rain = pd.DataFrame({"date": ["2020-01-01"], "rainfall": [-1]})
    with pytest.raises(ValidationError, match="at least"):
        FloodAnalyzer(rain, unit="mm")
    with pytest.raises(ValidationError, match="slope"):
        LandslideAnalyzer(rain.assign(rainfall=1, slope=91), rainfall_unit="mm", slope_unit="degrees")
    with pytest.raises(ValidationError, match="infinity"):
        HeatwaveAnalyzer(pd.DataFrame({"date": ["2020-01-01"], "tmax": [float("inf")]}), unit="C")
    storm = pd.DataFrame({"storm_id": ["A", "A"], "time": ["2020-01-01"] * 2,
                          "latitude": [0, 1], "longitude": [0, 1],
                          "wind": [20, 30], "pressure": [990, 980]})
    with pytest.raises(ValidationError, match="duplicate timestamp"):
        CycloneAnalyzer(storm, wind_unit="km/h", pressure_unit="hPa")
    with pytest.raises(ValidationError, match="latitude"):
        CycloneAnalyzer(storm.iloc[:1].assign(latitude=91), wind_unit="km/h", pressure_unit="hPa")
    with pytest.raises(ValidationError, match="pressure"):
        CycloneAnalyzer(storm.iloc[:1].assign(pressure=0), wind_unit="km/h", pressure_unit="hPa")
    with pytest.raises(ValidationError, match="radius_km"):
        CycloneAnalyzer(storm.iloc[:1], wind_unit="km/h", pressure_unit="hPa").proximity(
            latitude=0, longitude=0, radius_km=-1)


@pytest.mark.parametrize("bad_date", ["today", "01/02/2020", "20200102", "2020-02-30"])
def test_hazards_reject_ambiguous_relative_or_invalid_daily_dates(bad_date):
    source = pd.DataFrame({"date": [bad_date], "rainfall": [12.0]})
    before = source.copy(deep=True)
    with pytest.raises(ValidationError, match="date"):
        FloodAnalyzer(source, unit="mm")
    assert_frame_equal(source, before)


def test_hazard_timezones_and_relative_cyclone_timestamps_are_rejected():
    with pytest.raises(ValidationError, match="UTC-naive"):
        DroughtAnalyzer(pd.DataFrame({"date": ["2020-01-01T00:00:00+05:30"],
                                      "rainfall": [1.0]}), unit="mm")
    track = pd.DataFrame({"storm_id": ["A"], "time": ["today"], "latitude": [0.0],
                          "longitude": [0.0], "wind": [20.0], "pressure": [990.0]})
    with pytest.raises(ValidationError, match="ISO date/time"):
        CycloneAnalyzer(track, wind_unit="km/h", pressure_unit="hPa")


def test_comparison_periods_require_explicit_iso_calendar_bounds():
    source = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=4),
                           "rainfall": [2.0, 4.0, 0.0, 0.0],
                           "tmax": [35.0, 37.0, 40.0, 42.0]})
    before = source.copy(deep=True)
    drought = DroughtAnalyzer(source, unit="mm")
    heat = HeatwaveAnalyzer(source, unit="C")
    for method in (drought.rainfall_deficit, heat.temperature_anomaly):
        with pytest.raises(ValidationError, match="baseline"):
            method()
        with pytest.raises(ValidationError, match="comparison"):
            method(baseline_start="2020-01-01", baseline_end="2020-01-02")
        for invalid in ("today", "01/02/2020", "2020-01-03T00:00:00", 20200103):
            with pytest.raises(ValidationError, match="ISO calendar dates"):
                method(baseline_start="2020-01-01", baseline_end="2020-01-02",
                       start=invalid, end="2020-01-04")
        with pytest.raises(ValidationError, match="period start"):
            method(baseline_start="2020-01-02", baseline_end="2020-01-01",
                   start="2020-01-03", end="2020-01-04")
    assert_frame_equal(source, before)


def test_landslide_unknown_dates_distinguish_missing_history_and_slope():
    source = pd.DataFrame({"date": ["2020-01-01", "2020-01-02", "2020-01-03",
                                     "2020-01-05", "2020-01-06"],
                           "rainfall": [10.0, 20.0, None, 4.0, 5.0],
                           "slope": [30.0, 30.0, 30.0, 30.0, None]})
    before = source.copy(deep=True)
    result = LandslideAnalyzer(source, rainfall_unit="mm", slope_unit="degrees").susceptibility_indicators(
        window_days=1, rainfall_threshold_mm=10, slope_threshold_degrees=30)
    assert result.data["days"] == [
        {"date": "2020-01-02", "antecedent_mm": 10.0,
         "slope_degrees": 30.0, "meets_thresholds": True},
        {"date": "2020-01-03", "antecedent_mm": 20.0,
         "slope_degrees": 30.0, "meets_thresholds": True},
    ]
    assert result.data["unknown_days"] == 3
    assert result.data["unknown_dates"] == ["2020-01-01", "2020-01-05", "2020-01-06"]
    assert_frame_equal(source, before)


def test_antecedent_rainfall_ignores_slope_gaps_and_handles_last_pandas_date():
    data = pd.DataFrame({"date": ["2262-04-10", "2262-04-11"],
                         "rainfall": [4.0, 5.0], "slope": [None, 30.0]})
    before = data.copy(deep=True)
    rainfall = LandslideAnalyzer(data, rainfall_unit="mm",
                                 slope_unit="degrees").antecedent_rainfall(window_days=1)
    assert rainfall.data["days"] == [{"date": "2262-04-11", "antecedent_mm": 4.0}]
    assert rainfall.metadata["units"] == {"antecedent_rainfall": "mm"}
    assert not any("Missing measurements" in warning for warning in rainfall.warnings)
    assert_frame_equal(data, before)


def test_cyclone_timestamps_dateline_and_missing_intensity_remain_explicit():
    source = pd.DataFrame({"storm_id": ["A", "A"],
                           "time": ["2020-01-02T12:00:00", "2020-01-02T00:00:00"],
                           "latitude": [0.0, 0.0], "longitude": [-179.0, 179.0],
                           "wind": [None, None], "pressure": [None, None]})
    before = source.copy(deep=True)
    cyclone = CycloneAnalyzer(source, wind_unit="km/h", pressure_unit="hPa")
    track = cyclone.track_distance().data["storms"][0]
    assert track["distance_km"] == pytest.approx(222.39, abs=0.02)
    assert cyclone.cyclone_intensity().data["storms"][0]["max_wind_kmh"] is None
    assert cyclone.cyclone_intensity().data["storms"][0]["min_pressure_hpa"] is None
    assert cyclone.proximity(latitude=0, longitude=179, radius_km=0).data["storms"][0][
        "closest_observed_time"] == "2020-01-02T00:00:00"
    assert_frame_equal(source, before)


def test_cyclone_timezone_offsets_are_normalized_to_utc():
    source = pd.DataFrame({
        "storm_id": ["A", "A"],
        "time": ["2020-01-01T05:30:00+05:30", "2020-01-01T01:00:00Z"],
        "latitude": [0., 0.], "longitude": [0., 1.],
        "wind": [20., 30.], "pressure": [990., 980.],
    })
    result = CycloneAnalyzer(source, wind_unit="km/h", pressure_unit="hPa").proximity(
        latitude=0, longitude=0, radius_km=1)
    assert result.data["storms"][0]["closest_observed_time"] == "2020-01-01T00:00:00"


@pytest.mark.parametrize("analyzer", [FloodAnalyzer, LandslideAnalyzer])
def test_recorded_event_dates_reject_ambiguous_string_without_mutation(analyzer):
    source = pd.DataFrame({"date": ["2020-06-01"], "rainfall": [1.0], "slope": [30.0]})
    kwargs = ({"unit": "mm"} if analyzer is FloodAnalyzer else
              {"rainfall_unit": "mm", "slope_unit": "degrees"})
    instance = analyzer(source, **kwargs)
    events = pd.DataFrame({"date": ["01/02/2020"]})
    before = events.copy(deep=True)
    with pytest.raises(ValidationError, match="ISO"):
        if analyzer is FloodAnalyzer:
            instance.flood_event_frequency(events)
        else:
            instance.landslide_frequency(events)
    assert_frame_equal(events, before)


def test_large_finite_rainfall_keeps_percentage_finite_or_rejects_unrepresentable_sum():
    data = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=3),
                         "rainfall": [1e307, 1e307, 0.0]})
    drought = DroughtAnalyzer(data, unit="mm")
    deficit = drought.rainfall_deficit(baseline_start="2020-01-01",
                                      baseline_end="2020-01-02",
                                      start="2020-01-03", end="2020-01-03")
    assert deficit.to_dict()["data"]["deficit_percent"] == 100.0
    rain = pd.DataFrame({"date": ["2020-01-01", "2020-01-02"],
                         "rainfall": [1e308, 1e308]})
    with pytest.raises(ValidationError, match="finite numeric range"):
        FloodAnalyzer(rain, unit="mm").cumulative_rainfall(window_days=2)
    temperatures = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=3),
                                 "tmax": [-1e308, -1e308, 1e308]})
    with pytest.raises(ValidationError, match="finite numeric range"):
        HeatwaveAnalyzer(temperatures, unit="C").temperature_anomaly(
            baseline_start="2020-01-01", baseline_end="2020-01-02",
            start="2020-01-03", end="2020-01-03")
