"""Empirical prediction intervals and uncertainty quantification for forecast horizons."""

from __future__ import annotations

from typing import Any

import numpy as np

from nielytics.exceptions import ValidationError


class HorizonUncertaintyCalibrator:
    """Calibrates empirical prediction intervals per forecast horizon using historical residuals."""

    def __init__(self, confidence_levels: list[float] | None = None) -> None:
        self.confidence_levels = confidence_levels or [0.80, 0.95]
        self.horizon_stds: dict[int, float] = {}
        self.horizon_quantiles: dict[int, dict[float, tuple[float, float]]] = {}

    def fit_residuals(self, residuals_by_horizon: dict[int, np.ndarray]) -> HorizonUncertaintyCalibrator:
        for h, res in residuals_by_horizon.items():
            clean = res[np.isfinite(res)]
            if len(clean) < 3:
                std_val = 1.5 * np.sqrt(h)  # heuristic baseline error growth
            else:
                std_val = float(np.std(clean, ddof=1)) or (1.0 * np.sqrt(h))
            self.horizon_stds[h] = std_val

            q_dict = {}
            for level in self.confidence_levels:
                alpha = 1.0 - level
                if len(clean) >= 20:
                    low_q = float(np.percentile(clean, 100.0 * (alpha / 2.0)))
                    high_q = float(np.percentile(clean, 100.0 * (1.0 - alpha / 2.0)))
                else:
                    from scipy import stats
                    z = float(stats.norm.ppf(1.0 - alpha / 2.0))
                    low_q = -z * std_val
                    high_q = z * std_val
                q_dict[level] = (float(round(low_q, 3)), float(round(high_q, 3)))
            self.horizon_quantiles[h] = q_dict
        return self

    def get_intervals(
        self,
        predicted_value: float,
        horizon: int,
    ) -> dict[str, dict[str, float]]:
        """Return lower and upper bounds for calibrated confidence levels."""
        std_val = self.horizon_stds.get(horizon, 1.5 * np.sqrt(horizon))
        intervals: dict[str, dict[str, float]] = {}

        for level in self.confidence_levels:
            if horizon in self.horizon_quantiles and level in self.horizon_quantiles[horizon]:
                err_low, err_high = self.horizon_quantiles[horizon][level]
                # If error = pred - act, then act = pred - error
                # bounds: [pred - err_high, pred - err_low]
                low_b = predicted_value + err_low
                high_b = predicted_value + err_high
            else:
                from scipy import stats
                alpha = 1.0 - level
                z = float(stats.norm.ppf(1.0 - alpha / 2.0))
                low_b = predicted_value - (z * std_val)
                high_b = predicted_value + (z * std_val)

            # Ensure proper ordering
            if low_b > high_b:
                low_b, high_b = high_b, low_b

            pct_label = f"{int(level * 100)}%"
            intervals[pct_label] = {
                "lower": float(round(low_b, 2)),
                "upper": float(round(high_b, 2)),
            }
        return intervals
