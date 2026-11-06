"""Climatological and naive baseline forecasting models."""

from __future__ import annotations

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError


class PersistenceBaseline:
    """Persistence baseline: forecasts the most recent observed value indefinitely."""

    def __init__(self) -> None:
        self.last_value: float | None = None

    def fit(self, y: np.ndarray) -> PersistenceBaseline:
        if len(y) == 0:
            raise ValidationError("Cannot fit PersistenceBaseline on empty series.")
        self.last_value = float(y[-1])
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if self.last_value is None:
            raise ValidationError("PersistenceBaseline must be fitted before predict.")
        return np.full(horizon, self.last_value, dtype=float)


class SeasonalClimatologyBaseline:
    """Day-of-year seasonal climatology baseline: forecasts the historical mean for each calendar day."""

    def __init__(self) -> None:
        self.doy_means: dict[int, float] = {}
        self.overall_mean: float = 0.0

    def fit(self, dates: pd.DatetimeIndex, y: np.ndarray) -> SeasonalClimatologyBaseline:
        if len(y) == 0 or len(dates) != len(y):
            raise ValidationError("Dates and target array must have equal non-zero lengths.")
        df = pd.DataFrame({"doy": dates.dayofyear, "y": y})
        means = df.groupby("doy")["y"].mean().to_dict()
        self.doy_means = {int(k): float(v) for k, v in means.items()}
        self.overall_mean = float(np.mean(y))
        return self

    def predict(self, future_dates: pd.DatetimeIndex) -> np.ndarray:
        if not self.doy_means:
            raise ValidationError("SeasonalClimatologyBaseline must be fitted before predict.")
        preds = [self.doy_means.get(int(d), self.overall_mean) for d in future_dates.dayofyear]
        return np.array(preds, dtype=float)


class TrendSeasonalityBaseline:
    """Harmonic regression baseline fitting linear trend plus annual sinusoidal cycles."""

    def __init__(self) -> None:
        self.weights: np.ndarray | None = None
        self.t0: int = 0

    def fit(self, dates: pd.DatetimeIndex, y: np.ndarray) -> TrendSeasonalityBaseline:
        n = len(y)
        if n < 4:
            raise ValidationError("TrendSeasonalityBaseline requires at least 4 observations.")
        t = np.arange(n, dtype=float)
        self.t0 = n
        doy = dates.dayofyear.to_numpy(dtype=float)
        sin_doy = np.sin(2.0 * np.pi * doy / 365.25)
        cos_doy = np.cos(2.0 * np.pi * doy / 365.25)
        # Design matrix [1, t, sin, cos]
        X = np.column_stack([np.ones(n), t, sin_doy, cos_doy])
        # OLS fit
        self.weights, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        return self

    def predict(self, future_dates: pd.DatetimeIndex) -> np.ndarray:
        if self.weights is None:
            raise ValidationError("TrendSeasonalityBaseline must be fitted before predict.")
        h = len(future_dates)
        t_fut = self.t0 + np.arange(h, dtype=float)
        doy = future_dates.dayofyear.to_numpy(dtype=float)
        sin_doy = np.sin(2.0 * np.pi * doy / 365.25)
        cos_doy = np.cos(2.0 * np.pi * doy / 365.25)
        X_fut = np.column_stack([np.ones(h), t_fut, sin_doy, cos_doy])
        return X_fut @ self.weights
