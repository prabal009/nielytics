import json
import numpy as np
import pandas as pd
import pytest

from nielytics.forecasting import (
    ClimateProjectionEngine,
    ClosedFormRidgeRegressor,
    OperationalForecastAdapter,
    PersistenceBaseline,
    SeasonalClimatologyBaseline,
    TemperatureForecaster,
    TrendSeasonalityBaseline,
    compute_metrics,
    compute_skill_score,
)


def test_baselines_and_metrics():
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    y = np.array([20.0, 21.0, 22.0, 21.5, 20.5, 23.0, 22.5, 24.0, 23.5, 25.0])

    pers = PersistenceBaseline().fit(y)
    assert pers.predict(3).tolist() == [25.0, 25.0, 25.0]

    clim = SeasonalClimatologyBaseline().fit(dates, y)
    clim_pred = clim.predict(dates[:2])
    assert len(clim_pred) == 2

    trend_base = TrendSeasonalityBaseline().fit(dates, y)
    t_pred = trend_base.predict(dates[-2:])
    assert len(t_pred) == 2

    # Metrics
    m = compute_metrics(np.array([10.0, 20.0]), np.array([12.0, 19.0]))
    assert m["mae"] == 1.5
    assert m["mbe"] == 0.5
    assert compute_skill_score(mae_model=1.0, mae_baseline=2.0) == 0.5


def test_closed_form_ridge_regressor():
    X = np.array([[1.0, 1.0], [1.0, 2.0], [1.0, 3.0], [1.0, 4.0]])
    y = np.array([3.0, 5.0, 7.0, 9.0])  # y = 1 + 2*x
    model = ClosedFormRidgeRegressor(alpha=0.01).fit(X, y)
    preds = model.predict(X)
    np.testing.assert_allclose(preds, y, atol=0.1)


def test_temperature_forecaster_fit_predict_save_load(tmp_path):
    # 120 days of synthetic temperatures
    dates = pd.date_range("2023-01-01", periods=120, freq="D")
    tmax = 25.0 + 10.0 * np.sin(2.0 * np.pi * np.arange(120) / 365.25) + np.random.default_rng(42).normal(0, 1.0, 120)
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "tmax": tmax})

    forecaster = TemperatureForecaster(horizons=[1, 3, 7], alpha=1.0)
    forecaster.fit(df, date_column="date", target_column="tmax")

    # Predict
    pred_res = forecaster.predict(horizon=7)
    assert pred_res.feature == "temperature_forecast"
    payload = pred_res.to_dict()
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload

    predictions = pred_res.data["predictions"]
    assert len(predictions) == 7
    first_step = predictions[0]
    assert "predicted_tmax_c" in first_step
    assert "uncertainty_intervals" in first_step
    assert "80%" in first_step["uncertainty_intervals"]
    assert "95%" in first_step["uncertainty_intervals"]

    int_95 = first_step["uncertainty_intervals"]["95%"]
    assert int_95["lower"] <= first_step["predicted_tmax_c"] <= int_95["upper"]

    # Heatwave risk forecast
    risk_res = forecaster.forecast_heatwave_risk(pred_res, threshold_c=30.0)
    assert risk_res.feature == "heatwave_forecast_risk"
    assert len(risk_res.data["daily_risk"]) == 7
    assert 0.0 <= risk_res.data["daily_risk"][0]["exceedance_probability"] <= 1.0

    # Backtest
    bt_res = forecaster.backtest(horizons=[1, 3], min_train_periods=60, step_days=5)
    assert bt_res.feature == "forecast_chronological_backtest"
    assert "horizon_1d" in bt_res.data["horizon_evaluations"]

    # Save and Load
    model_path = tmp_path / "forecaster.json"
    forecaster.save(model_path)
    loaded_forecaster = TemperatureForecaster.load(model_path)
    loaded_pred = loaded_forecaster.predict(horizon=3)
    assert len(loaded_pred.data["predictions"]) == 3


def test_operational_forecast_bias_correction():
    dates = pd.date_range("2023-06-01", periods=10, freq="D").strftime("%Y-%m-%d")
    nwp_df = pd.DataFrame({"date": dates, "tmax_nwp": [32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0]})
    # Ground truth is consistently 2 degrees cooler
    ground_df = pd.DataFrame({"date": dates[:7], "tmax_obs": [30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0]})

    corrected = OperationalForecastAdapter.apply_bias_correction(
        nwp_df,
        ground_df,
        forecast_val_col="tmax_nwp",
        ground_val_col="tmax_obs",
        rolling_days=5,
    )
    assert "tmax_corrected" in corrected.columns
    # NWP was +2, so corrected should subtract 2
    assert corrected["tmax_corrected"].iloc[0] == pytest.approx(30.0, abs=0.1)


def test_climate_projection_engine():
    engine = ClimateProjectionEngine()

    # Mode A: Trend extrapolation
    dates = pd.date_range("2010-01-01", periods=10, freq="YE").strftime("%Y-%m-%d")
    # Linear warming +0.03 deg/year
    tmax = 30.0 + 0.03 * np.arange(10)
    df = pd.DataFrame({"date": dates, "tmax": tmax})

    trend_proj = engine.project_trend_extrapolation(df, target_years=[2030, 2040, 2050])
    assert trend_proj.feature == "climate_trend_extrapolation"
    assert len(trend_proj.data["projections"]) == 3
    assert trend_proj.data["projections"][0]["projected_annual_mean_c"] > 30.0

    # Mode B: CMIP6 Scenarios
    cmip_proj = engine.project_cmip6_scenarios(
        baseline_temperature_c=25.0,
        target_years=[2030, 2040, 2050],
        scenarios=["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"],
    )
    assert cmip_proj.feature == "cmip6_climate_projections"
    scenarios = cmip_proj.data["scenarios"]
    assert "SSP1-2.6" in scenarios
    assert "SSP2-4.5" in scenarios
    assert "SSP5-8.5" in scenarios

    ssp5_proj = scenarios["SSP5-8.5"]["projections"]
    # 2050 warming in SSP5-8.5 should be higher than SSP1-2.6
    assert ssp5_proj[2]["projected_absolute_temperature_c"] > scenarios["SSP1-2.6"]["projections"][2]["projected_absolute_temperature_c"]
