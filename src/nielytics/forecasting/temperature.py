"""Central TemperatureForecaster orchestrator with backtesting, uncertainty, and heatwave risk integration."""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from .baselines import SeasonalClimatologyBaseline
from .evaluation import run_chronological_backtest
from .features import extract_feature_vector
from .models import DirectMultiStepForecaster
from .serialization import load_forecaster_artifacts, save_forecaster_artifacts
from .uncertainty import HorizonUncertaintyCalibrator


class TemperatureForecaster:
    """Operational temperature forecaster with strict chronological leakage barriers and uncertainty intervals."""

    def __init__(self, horizons: list[int] | None = None, alpha: float = 1.0) -> None:
        self.horizons = sorted(horizons or [1, 3, 7, 14])
        self.alpha = float(alpha)
        self.forecaster: DirectMultiStepForecaster | None = None
        self.climatology: SeasonalClimatologyBaseline | None = None
        self.uncertainty_calibrator: HorizonUncertaintyCalibrator | None = None
        self._fitted_series: np.ndarray | None = None
        self._fitted_dates: pd.DatetimeIndex | None = None
        self._date_col: str = "date"
        self._target_col: str = "tmax"

    def fit(
        self,
        data: pd.DataFrame,
        date_column: str = "date",
        target_column: str = "tmax",
    ) -> TemperatureForecaster:
        """Fit seasonal climatology and direct horizon autoregressive models."""
        if date_column not in data.columns or target_column not in data.columns:
            raise ValidationError(f"Columns {date_column!r} and {target_column!r} must be in data.")

        df = data[[date_column, target_column]].dropna().copy()
        df[date_column] = pd.to_datetime(df[date_column]).dt.normalize()
        df = df.sort_values(date_column).drop_duplicates(subset=[date_column]).reset_index(drop=True)

        if len(df) < 30:
            raise ValidationError(f"TemperatureForecaster requires at least 30 daily observations (got {len(df)}).")

        self._date_col = date_column
        self._target_col = target_column
        self._fitted_dates = pd.DatetimeIndex(df[date_column])
        self._fitted_series = df[target_column].to_numpy(dtype=float)

        # 1. Fit Climatology
        self.climatology = SeasonalClimatologyBaseline().fit(self._fitted_dates, self._fitted_series)

        # 2. Build feature matrices for direct forecasting
        n = len(self._fitted_series)
        X_dict: dict[int, list[np.ndarray]] = {h: [] for h in self.horizons}
        y_dict: dict[int, list[float]] = {h: [] for h in self.horizons}

        for origin_idx in range(14, n):
            for h in self.horizons:
                if origin_idx + h < n:
                    target_date = self._fitted_dates[origin_idx + h]
                    x_vec = extract_feature_vector(
                        self._fitted_series,
                        origin_idx,
                        target_date,
                        self.climatology.doy_means,
                        horizon=h,
                    )
                    X_dict[h].append(x_vec)
                    y_dict[h].append(self._fitted_series[origin_idx + h])

        # Ensure all horizons have data
        X_np: dict[int, np.ndarray] = {}
        y_np: dict[int, np.ndarray] = {}
        for h in self.horizons:
            if len(y_dict[h]) == 0:
                raise ValidationError(f"Insufficient historical samples to train horizon {h} days.")
            X_np[h] = np.array(X_dict[h])
            y_np[h] = np.array(y_dict[h])

        # 3. Fit Forecaster
        self.forecaster = DirectMultiStepForecaster(horizons=self.horizons, alpha=self.alpha)
        self.forecaster.fit(X_np, y_np)

        # 4. Calibrate uncertainty using training residuals
        residuals_by_horizon: dict[int, np.ndarray] = {}
        for h in self.horizons:
            preds = self.forecaster.models[h].predict(X_np[h])
            residuals_by_horizon[h] = preds - y_np[h]

        self.uncertainty_calibrator = HorizonUncertaintyCalibrator(confidence_levels=[0.80, 0.95])
        self.uncertainty_calibrator.fit_residuals(residuals_by_horizon)

        return self

    def backtest(
        self,
        horizons: list[int] | None = None,
        min_train_periods: int = 60,
        step_days: int = 1,
    ) -> AnalysisResult:
        """Run leakage-free chronological backtesting with baseline skill evaluation."""
        if self._fitted_series is None or self._fitted_dates is None:
            raise ValidationError("Forecaster must be fitted before running backtest.")

        eval_horizons = sorted(horizons or self.horizons)
        res_dict = run_chronological_backtest(
            self._fitted_dates,
            self._fitted_series,
            horizons=eval_horizons,
            min_train_periods=min_train_periods,
            step_days=step_days,
        )

        return AnalysisResult(
            feature="forecast_chronological_backtest",
            data={
                "evaluated_horizons": eval_horizons,
                "horizon_evaluations": res_dict,
            },
            metadata={
                "method": "Expanding-window chronological backtesting",
                "units": {"temperature": "C"},
            },
            warnings=["Backtest skill scores assess past verification and do not guarantee future accuracy under regime shifts."],
        )

    def predict(
        self,
        horizon: int = 7,
        interval_levels: list[float] | None = None,
    ) -> AnalysisResult:
        """Generate point forecasts and calibrated prediction intervals up to `horizon` days ahead."""
        if (
            self.forecaster is None
            or self.climatology is None
            or self.uncertainty_calibrator is None
            or self._fitted_series is None
            or self._fitted_dates is None
        ):
            raise ValidationError("Forecaster must be fitted before predict.")

        if horizon < 1:
            raise ValidationError("horizon must be a positive integer.")

        levels = interval_levels or [0.80, 0.95]
        self.uncertainty_calibrator.confidence_levels = levels
        origin_idx = len(self._fitted_series) - 1
        last_date = self._fitted_dates[-1]

        predictions: list[dict[str, Any]] = []
        for step in range(1, horizon + 1):
            target_date = last_date + pd.DateOffset(days=step)
            # Find nearest available direct model horizon
            closest_h = min(self.horizons, key=lambda h: abs(h - step))

            x_vec = extract_feature_vector(
                self._fitted_series,
                origin_idx,
                target_date,
                self.climatology.doy_means,
                horizon=step,
            )
            point_pred = self.forecaster.predict_horizon(closest_h, x_vec)
            intervals = self.uncertainty_calibrator.get_intervals(point_pred, horizon=step)

            predictions.append({
                "step_day": step,
                "target_date": target_date.strftime("%Y-%m-%d"),
                "predicted_tmax_c": float(round(point_pred, 2)),
                "uncertainty_intervals": intervals,
            })

        return AnalysisResult(
            feature="temperature_forecast",
            data={
                "forecast_origin_date": last_date.strftime("%Y-%m-%d"),
                "horizon_days": horizon,
                "predictions": predictions,
            },
            metadata={
                "model_type": "DirectMultiStepForecaster (L2 Ridge)",
                "units": {"temperature": "C"},
            },
            warnings=["Weather forecasts exhibit error growth with lead time; intervals reflect empirical validation uncertainty."],
        )

    def forecast_heatwave_risk(
        self,
        forecast_result: AnalysisResult,
        threshold_c: float = 40.0,
    ) -> AnalysisResult:
        """Estimate the predicted probability of exceeding an extreme heat threshold per forecast step."""
        predictions = forecast_result.data.get("predictions", [])
        risk_assessments: list[dict[str, Any]] = []

        for p in predictions:
            pred_t = p["predicted_tmax_c"]
            d_str = p["target_date"]
            step = p["step_day"]

            # Estimate standard deviation from 95% interval or heuristic
            int_95 = p.get("uncertainty_intervals", {}).get("95%", {})
            if int_95:
                # 95% width is ~ 3.92 * sigma
                width = int_95["upper"] - int_95["lower"]
                sigma = max(0.5, width / 3.92)
            else:
                sigma = 1.5 * np.sqrt(step)

            # P(T >= threshold) = 1 - CDF((threshold - pred_t) / sigma)
            z_score = (threshold_c - pred_t) / sigma
            prob_exceed = float(round(1.0 - stats.norm.cdf(z_score), 4))

            risk_level = "High" if prob_exceed >= 0.50 else ("Moderate" if prob_exceed >= 0.20 else "Low")

            risk_assessments.append({
                "step_day": step,
                "target_date": d_str,
                "predicted_tmax_c": pred_t,
                "threshold_c": threshold_c,
                "exceedance_probability": prob_exceed,
                "risk_level": risk_level,
            })

        return AnalysisResult(
            feature="heatwave_forecast_risk",
            data={
                "threshold_c": threshold_c,
                "daily_risk": risk_assessments,
            },
            metadata={"units": {"temperature": "C", "probability": "fraction"}},
            warnings=["Forecast heatwave probabilities are screening indicators, not official IMD alerts."],
        )

    def save(self, filepath: str | os.PathLike[str]) -> None:
        """Persist model parameters and baseline tables to a safe JSON file."""
        if self.forecaster is None or self.climatology is None:
            raise ValidationError("Cannot save un-fitted forecaster.")

        models_data = {}
        for h, m in self.forecaster.models.items():
            models_data[str(h)] = [float(w) for w in m.weights] if m.weights is not None else []

        payload = {
            "horizons": self.horizons,
            "alpha": self.alpha,
            "doy_means": self.climatology.doy_means,
            "overall_mean": self.climatology.overall_mean,
            "horizon_weights": models_data,
            "last_observations": [float(v) for v in self._fitted_series[-30:]] if self._fitted_series is not None else [],
            "last_dates": [d.strftime("%Y-%m-%d") for d in self._fitted_dates[-30:]] if self._fitted_dates is not None else [],
        }
        save_forecaster_artifacts(payload, filepath)

    @classmethod
    def load(cls, filepath: str | os.PathLike[str]) -> TemperatureForecaster:
        """Restore a trained TemperatureForecaster from safe JSON persistence."""
        payload = load_forecaster_artifacts(filepath)
        forecaster_obj = cls(
            horizons=payload.get("horizons", [1, 3, 7]),
            alpha=payload.get("alpha", 1.0),
        )

        clim = SeasonalClimatologyBaseline()
        clim.doy_means = {int(k): float(v) for k, v in payload.get("doy_means", {}).items()}
        clim.overall_mean = float(payload.get("overall_mean", 0.0))
        forecaster_obj.climatology = clim

        direct_forecaster = DirectMultiStepForecaster(horizons=forecaster_obj.horizons, alpha=forecaster_obj.alpha)
        from .models import ClosedFormRidgeRegressor
        for h_str, weights_list in payload.get("horizon_weights", {}).items():
            h_int = int(h_str)
            reg = ClosedFormRidgeRegressor(alpha=forecaster_obj.alpha)
            reg.weights = np.array(weights_list, dtype=float)
            direct_forecaster.models[h_int] = reg

        forecaster_obj.forecaster = direct_forecaster
        forecaster_obj.uncertainty_calibrator = HorizonUncertaintyCalibrator()
        if payload.get("last_observations"):
            forecaster_obj._fitted_series = np.array(payload["last_observations"], dtype=float)
            forecaster_obj._fitted_dates = pd.DatetimeIndex(payload["last_dates"])
        return forecaster_obj
