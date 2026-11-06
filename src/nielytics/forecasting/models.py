"""Autoregressive linear and regularized Ridge models for temperature forecasting."""

from __future__ import annotations

from typing import Any

import numpy as np

from nielytics.exceptions import ValidationError


class ClosedFormRidgeRegressor:
    """L2-regularized linear model solved via closed-form normal equations."""

    def __init__(self, alpha: float = 1.0) -> None:
        self.alpha = float(alpha)
        self.weights: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> ClosedFormRidgeRegressor:
        if len(X) == 0 or len(X) != len(y):
            raise ValidationError("X and y must be nonempty and of identical length.")
        n, p = X.shape
        # Regularization matrix (do not penalize intercept at col 0)
        reg = self.alpha * np.eye(p)
        reg[0, 0] = 0.0

        XtX = X.T @ X
        Xty = X.T @ y
        try:
            self.weights = np.linalg.solve(XtX + reg, Xty)
        except np.linalg.LinAlgError:
            self.weights, _, _, _ = np.linalg.lstsq(XtX + reg, Xty, rcond=None)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.weights is None:
            raise ValidationError("ClosedFormRidgeRegressor must be fitted before predict.")
        return X @ self.weights


class DirectMultiStepForecaster:
    """Direct multi-step forecaster training an independent regressor per forecast horizon."""

    def __init__(self, horizons: list[int] | None = None, alpha: float = 1.0) -> None:
        self.horizons = sorted(horizons or [1, 3, 7, 14])
        self.alpha = float(alpha)
        self.models: dict[int, ClosedFormRidgeRegressor] = {}

    def fit(
        self,
        X_dict: dict[int, np.ndarray],
        y_dict: dict[int, np.ndarray],
    ) -> DirectMultiStepForecaster:
        for h in self.horizons:
            if h not in X_dict or h not in y_dict:
                raise ValidationError(f"Missing training data for horizon {h}.")
            reg = ClosedFormRidgeRegressor(alpha=self.alpha)
            reg.fit(X_dict[h], y_dict[h])
            self.models[h] = reg
        return self

    def predict_horizon(self, horizon: int, x_vector: np.ndarray) -> float:
        if horizon not in self.models:
            raise ValidationError(f"Forecaster not trained for horizon {horizon}. Available: {self.horizons}")
        X = x_vector.reshape(1, -1)
        pred = float(self.models[horizon].predict(X)[0])
        return pred
