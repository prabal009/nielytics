"""Backend-facing imports and strict JSON analysis responses."""

import json

import pandas as pd
import pytest

from nielytics import (
    AnalysisResult,
    CycloneAnalyzer,
    Dataset,
    DroughtAnalyzer,
    FloodAnalyzer,
    HeatwaveAnalyzer,
    LandslideAnalyzer,
    plot_bar,
    plot_geographic,
    plot_line,
)
from nielytics.core.visualization import (
    plot_bar as core_plot_bar,
)
from nielytics.core.visualization import (
    plot_geographic as core_plot_geographic,
)
from nielytics.core.visualization import (
    plot_line as core_plot_line,
)


def test_all_five_analyzers_are_root_importable_with_backend_results():
    daily = pd.DataFrame({"date": ["2025-01-01", "2025-01-02"],
                          "tmax": [40., 42.], "rainfall": [0., 20.],
                          "slope": [30., 30.]})
    storms = pd.DataFrame({"storm_id": ["demo"], "time": ["2025-01-01T00:00:00Z"],
                           "latitude": [12.], "longitude": [77.], "wind": [70.],
                           "pressure": [990.]})
    results = [
        HeatwaveAnalyzer(daily, unit="C").extreme_heat_days(threshold_c=40),
        FloodAnalyzer(daily, unit="mm").extreme_rainfall_days(threshold_mm=15),
        DroughtAnalyzer(daily, unit="mm").dry_spell_duration(minimum_days=1),
        CycloneAnalyzer(storms, wind_unit="km/h", pressure_unit="hPa").cyclone_intensity(),
        LandslideAnalyzer(daily, rainfall_unit="mm", slope_unit="degrees")
        .antecedent_rainfall(window_days=1),
    ]
    assert all(json.loads(json.dumps(item.to_dict(), allow_nan=False))["status"] == "success"
               for item in results)


def test_root_charts_are_existing_implementations():
    assert (plot_line, plot_bar, plot_geographic) == (
        core_plot_line, core_plot_bar, core_plot_geographic,
    )
    frame = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    assert Dataset(frame).summary().loc["y", "mean"] == 3.5
    assert list(plot_line(frame, "x", "y").data[0].y) == [3, 4]


def test_result_rejects_non_json_and_preserves_data():
    result = AnalysisResult(
        feature="synthetic_indicator",
        data={"value": 4, "unknown": None},
        metadata={"units": "mm", "source": "synthetic"},
        warnings=["Not an official warning."],
    )
    payload = result.to_dict()
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload
    payload["data"]["value"] = -1
    assert result.to_dict()["data"]["value"] == 4
    with pytest.raises(ValueError):
        AnalysisResult("invalid", {"value": float("nan")}, {}).to_dict()
