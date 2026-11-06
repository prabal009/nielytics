import numpy as np
import pandas as pd
import pytest

from nielytics.core.statistics import (
    linear_regression,
    mann_kendall_test,
    theil_sen_slope,
    z_score,
)
from nielytics.core.timeseries import (
    decompose_timeseries,
    detect_anomalies,
)


def test_z_score_calculation_and_constant():
    df = pd.DataFrame({"a": [10.0, 20.0, 30.0], "b": [5.0, 5.0, 5.0]})
    res = z_score(df)
    assert res["a"].iloc[1] == pytest.approx(0.0)
    assert res["a"].iloc[0] == pytest.approx(-1.0)
    assert res["a"].iloc[2] == pytest.approx(1.0)
    # constant column yields 0.0
    assert (res["b"] == 0.0).all()


def test_linear_regression_metrics_and_ci():
    x = np.arange(10, dtype=float)
    y = 2.0 * x + 5.0
    df = pd.DataFrame({"x": x, "y": y})
    reg = linear_regression(df, "x", "y")
    assert reg["slope"] == pytest.approx(2.0, abs=1e-4)
    assert reg["intercept"] == pytest.approx(5.0, abs=1e-4)
    assert reg["r_squared"] == pytest.approx(1.0, abs=1e-4)
    assert reg["p_value"] < 1e-4
    assert reg["slope_ci_lower"] <= 2.0 <= reg["slope_ci_upper"]


def test_theil_sen_slope_with_outlier():
    # Outlier at index 5 should not distort robust Theil-Sen slope
    x = np.arange(11, dtype=float)
    y = 3.0 * x + 1.0
    y[5] += 100.0  # single severe outlier
    df = pd.DataFrame({"x": x, "y": y})
    ts = theil_sen_slope(df, "y", "x")
    assert ts["slope"] == pytest.approx(3.0, abs=0.1)


def test_mann_kendall_test_trends():
    # Strictly increasing
    inc = [1.0, 2.0, 3.5, 4.0, 6.0, 7.5, 8.0, 10.0, 12.0, 15.0]
    res_inc = mann_kendall_test(inc)
    assert res_inc["s"] > 0
    assert res_inc["p_value"] < 0.05
    assert res_inc["trend"] == "increasing"

    # Strictly decreasing
    dec = [15.0, 12.0, 10.0, 8.0, 7.5, 6.0, 4.0, 3.5, 2.0, 1.0]
    res_dec = mann_kendall_test(dec)
    assert res_dec["s"] < 0
    assert res_dec["p_value"] < 0.05
    assert res_dec["trend"] == "decreasing"

    # Constant / flat (with ties)
    flat = [5.0] * 10
    res_flat = mann_kendall_test(flat)
    assert res_flat["s"] == 0
    assert res_flat["trend"] == "no_trend"


def test_decompose_timeseries():
    dates = pd.date_range("2020-01-01", periods=20, freq="D")
    vals = [10.0, 12.0, 10.0, 8.0] * 5  # period 4
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": vals})
    decomp = decompose_timeseries(df, "date", "value", period=4, model="additive")
    assert len(decomp) == 20
    assert "trend" in decomp.columns
    assert "seasonal" in decomp.columns
    assert "residual" in decomp.columns


def test_detect_anomalies():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    vals = [20.0] * 9 + [100.0]  # last one is extreme anomaly
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": vals})
    anom = detect_anomalies(df, "date", "value", threshold=2.5)
    assert anom.iloc[-1]["is_anomaly"]
    assert not anom.iloc[0]["is_anomaly"]
