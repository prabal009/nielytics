"""Chronological backtesting and verification metrics for temperature forecasting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError


def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Compute verification metrics: MAE, RMSE, MBE, MedAE."""
    if len(actual) == 0 or len(actual) != len(predicted):
        raise ValidationError("actual and predicted must be non-empty and of identical length.")
    errors = predicted - actual
    abs_errors = np.abs(errors)
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    mbe = float(np.mean(errors))
    medae = float(np.median(abs_errors))
    return {
        "mae": float(round(mae, 4)),
        "rmse": float(round(rmse, 4)),
        "mbe": float(round(mbe, 4)),
        "medae": float(round(medae, 4)),
        "count": len(actual),
    }


def compute_skill_score(mae_model: float, mae_baseline: float) -> float:
    """Compute baseline-relative forecast skill score (1 - MAE_model / MAE_baseline)."""
    if mae_baseline <= 1e-12:
        return 0.0
    skill = 1.0 - (mae_model / mae_baseline)
    return float(round(skill, 4))


def run_chronological_backtest(
    dates: pd.DatetimeIndex,
    series: np.ndarray,
    horizons: list[int] | None = None,
    min_train_periods: int = 60,
    step_days: int = 1,
) -> dict[str, Any]:
    """Execute expanding-window chronological backtesting without future data leakage."""
    target_horizons = sorted(horizons or [1, 3, 7])
    n = len(series)
    max_h = max(target_horizons)

    if n < min_train_periods + max_h + 10:
        raise ValidationError(
            f"Backtesting requires at least {min_train_periods + max_h + 10} observations (got {n})."
        )

    from .baselines import PersistenceBaseline, SeasonalClimatologyBaseline
    from .features import extract_feature_vector
    from .models import DirectMultiStepForecaster

    actuals: dict[int, list[float]] = {h: [] for h in target_horizons}
    preds_model: dict[int, list[float]] = {h: [] for h in target_horizons}
    preds_pers: dict[int, list[float]] = {h: [] for h in target_horizons}
    preds_clim: dict[int, list[float]] = {h: [] for h in target_horizons}

    # Evaluate origins
    for origin_idx in range(min_train_periods, n - max_h, step_days):
        train_dates = dates[: origin_idx + 1]
        train_y = series[: origin_idx + 1]

        # Fit baselines
        pers = PersistenceBaseline().fit(train_y)
        clim = SeasonalClimatologyBaseline().fit(train_dates, train_y)

        # Build training design matrix for direct models using available origins <= origin_idx
        X_train_dict: dict[int, list[np.ndarray]] = {h: [] for h in target_horizons}
        y_train_dict: dict[int, list[float]] = {h: [] for h in target_horizons}

        for hist_origin in range(14, origin_idx):
            for h in target_horizons:
                if hist_origin + h <= origin_idx:
                    fut_date = dates[hist_origin + h]
                    x_vec = extract_feature_vector(series, hist_origin, fut_date, clim.doy_means, horizon=h)
                    X_train_dict[h].append(x_vec)
                    y_train_dict[h].append(series[hist_origin + h])

        # Train forecaster
        try:
            forecaster = DirectMultiStepForecaster(horizons=target_horizons)
            X_dict_np = {h: np.array(X_train_dict[h]) for h in target_horizons}
            y_dict_np = {h: np.array(y_train_dict[h]) for h in target_horizons}
            forecaster.fit(X_dict_np, y_dict_np)
        except (ValueError, np.linalg.LinAlgError):
            continue

        # Predict for each horizon
        for h in target_horizons:
            target_idx = origin_idx + h
            target_date = dates[target_idx]
            y_true = float(series[target_idx])

            x_vec_test = extract_feature_vector(series, origin_idx, target_date, clim.doy_means, horizon=h)
            pred_val = forecaster.predict_horizon(h, x_vec_test)

            actuals[h].append(y_true)
            preds_model[h].append(pred_val)
            preds_pers[h].append(float(pers.predict(h)[-1]))
            preds_clim[h].append(float(clim.predict(pd.DatetimeIndex([target_date]))[0]))

    # Compute metrics per horizon
    results_by_horizon: dict[str, Any] = {}
    for h in target_horizons:
        y_act = np.array(actuals[h])
        y_pred = np.array(preds_model[h])
        y_p = np.array(preds_pers[h])
        y_c = np.array(preds_clim[h])

        if len(y_act) == 0:
            continue

        m_model = compute_metrics(y_act, y_pred)
        m_pers = compute_metrics(y_act, y_p)
        m_clim = compute_metrics(y_act, y_c)

        skill_vs_clim = compute_skill_score(m_model["mae"], m_clim["mae"])
        skill_vs_pers = compute_skill_score(m_model["mae"], m_pers["mae"])

        results_by_horizon[f"horizon_{h}d"] = {
            "model_metrics": m_model,
            "persistence_metrics": m_pers,
            "climatology_metrics": m_clim,
            "skill_score_vs_climatology": skill_vs_clim,
            "skill_score_vs_persistence": skill_vs_pers,
            "validation_samples": len(y_act),
        }

    return results_by_horizon
