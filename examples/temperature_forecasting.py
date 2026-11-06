"""Demonstrate operational temperature forecasting, backtesting, and heatwave risk estimation."""

import json
import numpy as np
import pandas as pd
from nielytics import TemperatureForecaster


def main() -> None:
    print("=== NIElytics Operational Temperature Forecasting ===")

    # 1. Generate synthetic daily temperature series (180 days)
    rng = np.random.default_rng(42)
    dates = pd.date_range("2023-01-01", periods=180, freq="D")
    base_signal = 28.0 + 8.0 * np.sin(2.0 * np.pi * np.arange(180) / 365.25)
    noise = rng.normal(0, 1.2, 180)
    tmax = base_signal + noise

    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "tmax": tmax})
    print(f"Training observations: {len(df)} days.")

    # 2. Fit Forecaster with direct multi-step models
    forecaster = TemperatureForecaster(horizons=[1, 3, 7], alpha=1.0)
    forecaster.fit(df, date_column="date", target_column="tmax")
    print("Fitted TemperatureForecaster with zero future-data leakage.")

    # 3. 7-Day Ahead Prediction with Calibrated Intervals
    pred_res = forecaster.predict(horizon=7)
    print("\nForecast Trajectory (Next 7 Days):")
    for step in pred_res.data["predictions"]:
        int_95 = step["uncertainty_intervals"]["95%"]
        print(
            f" Day {step['step_day']} ({step['target_date']}): "
            f"Point Forecast = {step['predicted_tmax_c']}°C "
            f"[95% CI: {int_95['lower']}°C to {int_95['upper']}°C]"
        )

    # 4. Forecast Heatwave Risk Exceedance Probability
    risk_res = forecaster.forecast_heatwave_risk(pred_res, threshold_c=36.0)
    print("\nForecast Heatwave Exceedance Risk (Threshold = 36°C):")
    for risk in risk_res.data["daily_risk"]:
        print(
            f" Day {risk['step_day']} ({risk['target_date']}): "
            f"P(T >= 36°C) = {risk['exceedance_probability'] * 100:.1f}% "
            f"[{risk['risk_level']} Risk]"
        )

    # 5. Chronological Backtest Evaluation
    bt_res = forecaster.backtest(horizons=[1, 3], min_train_periods=90, step_days=10)
    print("\nBacktest Performance Verification:")
    for h_label, h_info in bt_res.data["horizon_evaluations"].items():
        m = h_info["model_metrics"]
        skill_clim = h_info["skill_score_vs_climatology"]
        print(f" {h_label}: MAE = {m['mae']}°C, RMSE = {m['rmse']}°C, Skill vs Climatology = {skill_clim}")


if __name__ == "__main__":
    main()
