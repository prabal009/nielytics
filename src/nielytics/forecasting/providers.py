"""Operational NWP forecast provider adapters and local observation bias correction."""

from __future__ import annotations

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError


class OperationalForecastAdapter:
    """Ingests operational NWP weather forecasts and applies localized ground-truth bias correction."""

    def __init__(self, offline: bool = True) -> None:
        self.offline = offline

    @staticmethod
    def apply_bias_correction(
        forecast_df: pd.DataFrame,
        ground_truth_df: pd.DataFrame,
        forecast_val_col: str = "tmax_nwp",
        ground_val_col: str = "tmax_obs",
        date_col: str = "date",
        rolling_days: int = 7,
    ) -> pd.DataFrame:
        """Adjust operational NWP predictions using the rolling mean error against recent ground observations."""
        if forecast_val_col not in forecast_df.columns:
            raise ValidationError(f"Forecast column {forecast_val_col!r} not found in forecast_df.")
        if ground_val_col not in ground_truth_df.columns:
            raise ValidationError(f"Ground truth column {ground_val_col!r} not found in ground_truth_df.")

        f_copy = forecast_df.copy()
        g_copy = ground_truth_df.copy()

        f_copy[date_col] = pd.to_datetime(f_copy[date_col]).dt.normalize()
        g_copy[date_col] = pd.to_datetime(g_copy[date_col]).dt.normalize()

        # Compute overlap
        merged = pd.merge(f_copy, g_copy, on=date_col, how="inner").sort_values(date_col)
        if len(merged) == 0:
            # No overlap; cannot calculate bias
            f_copy["bias_correction"] = 0.0
            f_copy["tmax_corrected"] = f_copy[forecast_val_col]
            return f_copy

        # Calculate error: NWP - Ground
        recent_overlap = merged.tail(rolling_days)
        bias = float(np.mean(recent_overlap[forecast_val_col] - recent_overlap[ground_val_col]))

        f_copy["bias_correction"] = float(round(-bias, 2))
        f_copy["tmax_corrected"] = f_copy[forecast_val_col] - bias
        f_copy["tmax_corrected"] = f_copy["tmax_corrected"].apply(lambda v: float(round(v, 2)))
        return f_copy
