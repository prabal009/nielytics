"""Strict leakage-free time-series feature engineering for temperature forecasting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError


def build_lag_features_at_origin(
    series: np.ndarray,
    origin_idx: int,
) -> dict[str, float]:
    """Extract strictly historical lag and rolling statistics at forecast origin index T (inclusive).

    All statistics are computed over data points <= origin_idx.
    """
    if origin_idx < 13:
        raise ValidationError(f"origin_idx must be at least 13 to compute all lagged features (got {origin_idx}).")

    y_T = float(series[origin_idx])
    y_T1 = float(series[origin_idx - 1])
    y_T2 = float(series[origin_idx - 2])
    y_T6 = float(series[origin_idx - 6])
    y_T13 = float(series[origin_idx - 13])

    past_7 = series[origin_idx - 6 : origin_idx + 1]
    past_14 = series[origin_idx - 13 : origin_idx + 1]

    mean_7 = float(np.mean(past_7))
    std_7 = float(np.std(past_7, ddof=1)) if len(past_7) > 1 else 0.0
    min_7 = float(np.min(past_7))
    max_7 = float(np.max(past_7))
    mean_14 = float(np.mean(past_14))

    return {
        "lag_0": y_T,
        "lag_1": y_T1,
        "lag_2": y_T2,
        "lag_6": y_T6,
        "lag_13": y_T13,
        "roll_mean_7": mean_7,
        "roll_std_7": std_7,
        "roll_min_7": min_7,
        "roll_max_7": max_7,
        "roll_mean_14": mean_14,
    }


def build_target_calendar_features(target_date: pd.Timestamp) -> dict[str, float]:
    """Compute cyclical harmonic encodings for the future target date."""
    doy = float(target_date.dayofyear)
    month = float(target_date.month)
    sin_doy = float(np.sin(2.0 * np.pi * doy / 365.25))
    cos_doy = float(np.cos(2.0 * np.pi * doy / 365.25))
    sin_month = float(np.sin(2.0 * np.pi * month / 12.0))
    cos_month = float(np.cos(2.0 * np.pi * month / 12.0))
    return {
        "sin_doy": sin_doy,
        "cos_doy": cos_doy,
        "sin_month": sin_month,
        "cos_month": cos_month,
    }


def extract_feature_vector(
    series: np.ndarray,
    origin_idx: int,
    target_date: pd.Timestamp,
    climatology_doy_means: dict[int, float],
    horizon: int = 1,
) -> np.ndarray:
    """Construct complete leakage-free feature vector for predicting target_date at step horizon."""
    lag_feats = build_lag_features_at_origin(series, origin_idx)
    cal_feats = build_target_calendar_features(target_date)
    doy_val = int(target_date.dayofyear)
    clim_mean = float(climatology_doy_means.get(doy_val, lag_feats["roll_mean_14"]))

    features = [
        1.0,  # intercept
        lag_feats["lag_0"],
        lag_feats["lag_1"],
        lag_feats["lag_2"],
        lag_feats["lag_6"],
        lag_feats["lag_13"],
        lag_feats["roll_mean_7"],
        lag_feats["roll_std_7"],
        lag_feats["roll_min_7"],
        lag_feats["roll_max_7"],
        lag_feats["roll_mean_14"],
        cal_feats["sin_doy"],
        cal_feats["cos_doy"],
        cal_feats["sin_month"],
        cal_feats["cos_month"],
        clim_mean,
        float(horizon),
    ]
    return np.array(features, dtype=float)
