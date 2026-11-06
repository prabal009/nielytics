"""Explicit daily time-series calculations; no interpolation or zero filling."""

from __future__ import annotations

from collections.abc import Hashable
from numbers import Integral

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError

from .statistics import _selected_columns


def _series(frame: pd.DataFrame, date: Hashable, value: Hashable) -> pd.DataFrame:
    """Validate unique daily dates and finite measurements, then sort a copy."""
    _selected_columns(frame, [date], numeric=False)
    _selected_columns(frame, [value])
    dates = frame[date]
    if pd.api.types.is_numeric_dtype(dates.dtype) or dates.isna().any():
        raise ValidationError("date must contain nonmissing dates, not numeric epochs")
    try:
        parsed = pd.to_datetime(dates, errors="raise", format="mixed")
        if parsed.isna().any() or (parsed != parsed.dt.normalize()).any():
            raise ValidationError("date must contain daily dates without time components")
    except (ValueError, TypeError, AttributeError, OverflowError) as exc:
        raise ValidationError("date must contain consistently zoned daily dates") from exc
    if parsed.duplicated().any():
        raise ValidationError("duplicate dates require explicit aggregation before analysis")
    values = frame[value].to_numpy(dtype=float, na_value=np.nan)
    if np.isinf(values).any():
        raise ValidationError("value contains infinite observations")
    return pd.DataFrame({"date": parsed.to_numpy(), "value": values}).sort_values("date").reset_index(drop=True)


def rolling_mean(frame: pd.DataFrame, date: Hashable, value: Hashable, *,
                 window: int, min_periods: int | None = None) -> pd.DataFrame:
    """Return dated rolling mean over observations, not elapsed calendar days.

    Missing observations do not contribute; no dates or values are imputed.
    ``min_periods`` defaults to the full window. For calendar-day windows,
    first reindex explicitly and choose a missing-date policy.
    """
    if isinstance(window, bool) or not isinstance(window, Integral) or window < 1:
        raise ValidationError("window must be a positive integer")
    if min_periods is not None and (isinstance(min_periods, bool) or
                                    not isinstance(min_periods, Integral) or
                                    not 1 <= min_periods <= window):
        raise ValidationError("min_periods must be between 1 and window")
    result = _series(frame, date, value)
    result["rolling_mean"] = result["value"].rolling(
        window=int(window), min_periods=int(min_periods or window)).mean()
    return result


def missing_dates(frame: pd.DataFrame, date: Hashable, value: Hashable,
                  *, start: str | None = None, end: str | None = None) -> list[str]:
    """List absent calendar dates within the observed or explicitly bounded interval."""
    result = _series(frame, date, value)
    if result.empty and (start is None or end is None):
        raise ValidationError("empty series requires both start and end")
    try:
        first = pd.Timestamp(start) if start is not None else result["date"].min()
        last = pd.Timestamp(end) if end is not None else result["date"].max()
        if pd.isna(first) or pd.isna(last) or first > last:
            raise ValidationError("start and end must be ordered dates")
        expected = pd.date_range(first, last, freq="D")
        absent = expected.difference(pd.DatetimeIndex(result["date"]))
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError("start and end must be valid ordered dates") from exc
    return [item.date().isoformat() for item in absent]


def calculate_anomalies(frame: pd.DataFrame, date: Hashable, value: Hashable, *,
                        baseline_start: str, baseline_end: str) -> pd.DataFrame:
    """Subtract baseline calendar-month means; missing baseline months stay null.

    Baseline bounds are inclusive and must contain at least one finite reading.
    The output includes the actual monthly baseline used for every row. This
    describes anomalies only, not a hazard classification or prediction.
    """
    result = _series(frame, date, value)
    try:
        start = pd.Timestamp(baseline_start)
        end = pd.Timestamp(baseline_end)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError("baseline bounds must be valid dates") from exc
    if start > end:
        raise ValidationError("baseline bounds must be ordered")
    selected = result.loc[result["date"].between(start, end)]
    if not selected["value"].notna().any():
        raise ValidationError("baseline has no observed measurements")
    means = selected.groupby(selected["date"].dt.month)["value"].mean()
    result["baseline"] = result["date"].dt.month.map(means)
    result["anomaly"] = result["value"] - result["baseline"]
    return result


def decompose_timeseries(
    frame: pd.DataFrame,
    date: Hashable,
    value: Hashable,
    *,
    period: int = 365,
    model: str = "additive",
) -> pd.DataFrame:
    """Decompose time series into trend, seasonal, and residual components.

    Uses centered moving average for trend estimation and cyclic detrended
    averaging for seasonal components.
    """
    if isinstance(period, bool) or not isinstance(period, Integral) or period < 2:
        raise ValidationError("period must be an integer >= 2.")
    if model not in ("additive", "multiplicative"):
        raise ValidationError("model must be 'additive' or 'multiplicative'.")

    series = _series(frame, date, value)
    if len(series) < period:
        raise ValidationError(f"decompose_timeseries requires at least {period} observations (got {len(series)}).")

    vals = series["value"]
    if model == "multiplicative" and (vals <= 0).any():
        raise ValidationError("multiplicative decomposition requires strictly positive values.")

    trend = vals.rolling(window=period, center=True, min_periods=period).mean()

    if model == "additive":
        detrended = vals - trend
    else:
        detrended = vals / trend

    cycle_key = np.arange(len(series)) % period
    seasonal_means = detrended.groupby(cycle_key).transform("mean")
    cycle_mean = detrended.groupby(cycle_key).mean().mean()

    if model == "additive":
        seasonal = seasonal_means - cycle_mean
        residual = vals - trend - seasonal
    else:
        seasonal = seasonal_means / cycle_mean
        residual = vals / (trend * seasonal)

    return pd.DataFrame({
        "date": series["date"],
        "value": vals,
        "trend": trend,
        "seasonal": seasonal,
        "residual": residual,
    })


def detect_anomalies(
    frame: pd.DataFrame,
    date: Hashable,
    value: Hashable,
    *,
    baseline_start: str | None = None,
    baseline_end: str | None = None,
    method: str = "z_score",
    threshold: float = 3.0,
) -> pd.DataFrame:
    """Detect anomalies relative to climatological baseline or historical mean.

    Returns a DataFrame with date, value, baseline, anomaly departure, z_score,
    and boolean is_anomaly flag.
    """
    if method not in ("z_score", "zscore"):
        raise ValidationError("Currently supported anomaly detection method is 'z_score'.")
    if threshold <= 0:
        raise ValidationError("threshold must be a positive number.")

    if baseline_start is not None and baseline_end is not None:
        res = calculate_anomalies(frame, date, value, baseline_start=baseline_start, baseline_end=baseline_end)
    else:
        res = _series(frame, date, value)
        base_val = float(res["value"].mean())
        res["baseline"] = base_val
        res["anomaly"] = res["value"] - base_val

    anom = res["anomaly"]
    std_val = float(anom.std(ddof=1)) if len(anom) > 1 else 0.0
    if std_val > 1e-12:
        z_scores = (anom - anom.mean()) / std_val
    else:
        z_scores = pd.Series(0.0, index=res.index)

    res["z_score"] = z_scores
    res["is_anomaly"] = z_scores.abs() > threshold
    return res
