"""Input checks and complete-day calculations shared by hazard indicators."""
from __future__ import annotations

import re
from numbers import Integral, Real

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_complex_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

_ISO_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2})?)?\Z"
)
_ISO_DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def frame(data: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValidationError("data must be a nonempty pandas DataFrame")
    if not data.columns.is_unique:
        raise ValidationError("column labels must be unique")
    if len(set(columns)) != len(columns):
        raise ValidationError("column names must be distinct")
    for column in columns:
        if not isinstance(column, str) or column not in data.columns:
            raise ValidationError(f"missing column: {column!r}")
    return data.loc[:, list(columns)].copy()


def dates(values: pd.Series, *, daily: bool) -> pd.Series:
    nonmissing = values.dropna()
    if (is_numeric_dtype(values.dtype) or is_bool_dtype(values.dtype)
            or nonmissing.map(lambda value: isinstance(value, (bool, Real))).any()):
        raise ValidationError("dates must be dates or ISO date/time strings, not numeric values")
    if nonmissing.map(
        lambda value: isinstance(value, str) and _ISO_TIMESTAMP.fullmatch(value) is None
    ).any():
        raise ValidationError("dates must be ISO date/time strings or date objects")
    try:
        parsed = pd.to_datetime(values, errors="raise", format="mixed", utc=not daily)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError("invalid date or timestamp") from exc
    if parsed.isna().any():
        raise ValidationError("dates cannot be missing")
    if not daily and isinstance(parsed.dtype, pd.DatetimeTZDtype):
        return parsed.dt.tz_convert("UTC").dt.tz_localize(None)
    if isinstance(parsed.dtype, pd.DatetimeTZDtype) or not is_datetime64_any_dtype(parsed.dtype):
        raise ValidationError("daily dates must be consistent UTC-naive timestamps")
    if daily and (parsed != parsed.dt.normalize()).any():
        raise ValidationError("daily observations must have midnight dates")
    return parsed


def numeric(values: pd.Series, name: str, *, minimum: float | None = None,
            maximum: float | None = None) -> pd.Series:
    if not is_numeric_dtype(values.dtype) or is_bool_dtype(values.dtype) or is_complex_dtype(values.dtype):
        raise ValidationError(f"{name} must be real numeric")
    try:
        result = values.astype(float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"{name} must be real numeric") from exc
    if np.isinf(result.to_numpy(dtype=float, na_value=np.nan)).any():
        raise ValidationError(f"{name} must not contain infinity")
    if minimum is not None and (result.dropna() < minimum).any():
        raise ValidationError(f"{name} must be at least {minimum}")
    if maximum is not None and (result.dropna() > maximum).any():
        raise ValidationError(f"{name} must be at most {maximum}")
    return result


def daily(data: pd.DataFrame, date_column: str, measures: dict[str, tuple[float | None, float | None]]) -> pd.DataFrame:
    observations = frame(data, (date_column, *measures))
    observations[date_column] = dates(observations[date_column], daily=True)
    if observations[date_column].duplicated().any():
        raise ValidationError("duplicate daily dates require explicit aggregation before analysis")
    for name, (minimum, maximum) in measures.items():
        observations[name] = numeric(observations[name], name, minimum=minimum, maximum=maximum)
        if observations[name].isna().all():
            raise ValidationError(f"{name} requires at least one observed value")
    return observations.sort_values(date_column).reset_index(drop=True)


def positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValidationError(f"{name} must be a positive integer")
    return int(value)


def threshold(value: float, name: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
        raise ValidationError(f"{name} must be a finite real number")
    if minimum is not None and value < minimum:
        raise ValidationError(f"{name} must be at least {minimum}")
    return float(value)


def period(df: pd.DataFrame, column: str, start: str | None = None,
           end: str | None = None) -> pd.DataFrame:
    def bound(value: str | None) -> pd.Timestamp | None:
        if value is None:
            return None
        if not isinstance(value, str) or _ISO_DAY.fullmatch(value) is None:
            raise ValidationError("period bounds must be ISO calendar dates (YYYY-MM-DD)")
        try:
            stamp = pd.Timestamp(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("period bounds must be valid ISO dates") from exc
        if pd.isna(stamp) or stamp.tzinfo is not None or stamp != stamp.normalize():
            raise ValidationError("period bounds must be UTC-naive calendar dates")
        return stamp

    first, last = bound(start), bound(end)
    if first is not None and last is not None and first > last:
        raise ValidationError("period start must not exceed end")
    mask = pd.Series(True, index=df.index)
    if first is not None:
        mask &= df[column] >= first
    if last is not None:
        mask &= df[column] <= last
    return df.loc[mask].copy()


def warnings_for(df: pd.DataFrame, date_column: str, measures: tuple[str, ...]) -> list[str]:
    messages: list[str] = []
    if (df[date_column].diff().dropna() > pd.Timedelta(days=1)).any():
        messages.append("Missing calendar dates are not interpolated; spells and windows break at gaps.")
    if df.loc[:, list(measures)].isna().any().any():
        messages.append("Missing measurements are not treated as zero; incomplete days or windows are excluded.")
    return messages


def metadata(df: pd.DataFrame, date_column: str, units: dict[str, str],
             *, kind: str = "proxy_indicator", **details: object) -> dict:
    return {"kind": kind, "period": {"start": df[date_column].min().date().isoformat(),
                                         "end": df[date_column].max().date().isoformat()},
            "units": units, **details}


def result(feature: str, data: dict, meta: dict, warnings: list[str], caveat: str) -> AnalysisResult:
    return AnalysisResult(feature=feature, data=data, metadata=meta, warnings=[caveat, *warnings])


def spells(df: pd.DataFrame, date_column: str, value_column: str,
           cutoff: float, *, above: bool, minimum_days: int) -> list[dict]:
    """Consecutive observed complete calendar days satisfying a threshold."""
    candidate = (df[value_column] >= cutoff if above else df[value_column] <= cutoff).fillna(False)
    episode: list[dict] = []
    current: list[tuple[pd.Timestamp, float]] = []
    for day, value, qualifies in zip(df[date_column], df[value_column], candidate):
        if current and (not qualifies or day - current[-1][0] != pd.Timedelta(days=1)):
            if len(current) >= minimum_days:
                episode.append({"start": current[0][0].date().isoformat(),
                                "end": current[-1][0].date().isoformat(),
                                "days": len(current),
                                "peak": float(max(v for _, v in current) if above else min(v for _, v in current))})
            current = []
        if qualifies:
            current.append((day, float(value)))
    if len(current) >= minimum_days:
        episode.append({"start": current[0][0].date().isoformat(),
                        "end": current[-1][0].date().isoformat(), "days": len(current),
                        "peak": float(max(v for _, v in current) if above else min(v for _, v in current))})
    return episode


def complete_rolling(df: pd.DataFrame, date_column: str, value_column: str,
                     window: int) -> list[dict]:
    """Only windows of consecutive observed days with all finite measurements."""
    sums = df[value_column].rolling(window, min_periods=window).sum()
    rows = []
    for index in range(window - 1, len(df)):
        first = index - window + 1
        if df[date_column].iloc[index] - df[date_column].iloc[first] != pd.Timedelta(days=window - 1):
            continue
        total = sums.iloc[index]
        if pd.isna(total):
            if df[value_column].iloc[first:index + 1].notna().all():
                raise ValidationError("complete rainfall total exceeds finite numeric range")
            continue
        if not np.isfinite(total):
            raise ValidationError("complete rainfall total exceeds finite numeric range")
        rows.append({"start": df[date_column].iloc[first].date().isoformat(),
                     "end": df[date_column].iloc[index].date().isoformat(),
                     "total": float(total)})
    return rows
