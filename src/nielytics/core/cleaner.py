"""Explicit, non-mutating DataFrame cleaning operations."""

import re
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd
from pandas.api.types import is_numeric_dtype

from nielytics.exceptions import ValidationError


def _validate_frame(frame: pd.DataFrame) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise ValidationError("Expected a pandas DataFrame.")
    if not frame.columns.is_unique:
        raise ValidationError("DataFrame column names must be unique.")


def _columns(frame: pd.DataFrame, columns: Sequence[Any] | str | None) -> list[Any]:
    _validate_frame(frame)
    if columns is None:
        return list(frame.columns)
    try:
        selected = [columns] if isinstance(columns, str) else list(columns)
    except TypeError as exc:
        raise ValidationError("columns must be a column name or a sequence of names.") from exc
    try:
        missing = [column for column in selected if column not in frame.columns]
    except (TypeError, ValueError) as exc:
        raise ValidationError("Column names must be valid DataFrame labels.") from exc
    if missing:
        raise ValidationError(f"Columns not found: {missing!r}")
    return selected


def missing_report(frame: pd.DataFrame) -> pd.DataFrame:
    """Return missing counts and percentages (0–100), indexed by column.

    Empty frames have zero missing counts and percentages.
    """
    _validate_frame(frame)
    counts = frame.isna().sum()
    percentages = counts / len(frame) * 100 if len(frame) else counts.astype(float)
    return pd.DataFrame({"missing_count": counts, "missing_percent": percentages})


def fill_missing(
    frame: pd.DataFrame,
    *,
    columns: Sequence[Any] | str | None = None,
    strategy: str = "mean",
    value: Any = None,
) -> pd.DataFrame:
    """Fill selected columns using mean, median, mode, or a constant.

    All columns are selected by default. Mean and median require numeric
    columns. Statistical strategies reject all-null columns; mode ties use
    the first mode returned by pandas. Constant filling requires a non-null
    scalar value. The input is never changed.
    """
    selected = _columns(frame, columns)
    if strategy not in ("mean", "median", "mode", "constant"):
        raise ValidationError(f"Unsupported fill strategy: {strategy!r}")
    if strategy == "constant" and (not pd.api.types.is_scalar(value) or pd.isna(value)):
        raise ValidationError("Constant filling requires a non-null scalar value.")
    result = frame.copy(deep=True)
    for column in selected:
        series = frame[column]
        if strategy in ("mean", "median") and not is_numeric_dtype(series.dtype):
            raise ValidationError(f"Column {column!r} must be numeric for {strategy} filling.")
        if strategy != "constant" and not series.notna().any():
            raise ValidationError(f"Cannot calculate {strategy} for all-null column {column!r}.")
        if strategy == "mean":
            replacement = series.mean()
        elif strategy == "median":
            replacement = series.median()
        elif strategy == "mode":
            replacement = series.mode(dropna=True).iloc[0]
        else:
            replacement = value
        try:
            result[column] = series.fillna(replacement)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValidationError(f"Cannot fill column {column!r}: {exc}") from exc
    return result


def remove_duplicates(
    frame: pd.DataFrame,
    *,
    subset: Sequence[Any] | str | None = None,
    keep: str | bool = "first",
) -> pd.DataFrame:
    """Return a copy without duplicate rows, preserving surviving indices."""
    selected = _columns(frame, subset)
    if keep is not False and keep not in ("first", "last"):
        raise ValidationError("keep must be 'first', 'last', or False.")
    if subset is not None and not selected:
        raise ValidationError("subset must contain at least one column.")
    try:
        return frame.drop_duplicates(subset=selected if subset is not None else None, keep=keep).copy(deep=True)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Cannot remove duplicates: {exc}") from exc


def standardize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return lowercase, underscore-separated column names; reject collisions.

    Names are converted to strings, whitespace is stripped, non-word runs
    become underscores, and leading/trailing underscores are removed.
    """
    _validate_frame(frame)
    names = [re.sub(r"\W+", "_", str(column).strip().lower()).strip("_") for column in frame.columns]
    if any(not name for name in names):
        raise ValidationError("Standardization would create an empty column name.")
    if len(set(names)) != len(names):
        raise ValidationError("Standardization would create duplicate column names.")
    result = frame.copy(deep=True)
    result.columns = names
    return result


def convert_types(frame: pd.DataFrame, mapping: Mapping[Any, Any]) -> pd.DataFrame:
    """Return a copy with explicitly mapped pandas dtypes, raising on failure."""
    if not isinstance(mapping, Mapping):
        raise ValidationError("mapping must map column names to dtypes.")
    _columns(frame, list(mapping))
    try:
        return frame.astype(dict(mapping), copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"Cannot convert column types: {exc}") from exc


def clean_text(
    frame: pd.DataFrame, *, columns: Sequence[Any] | str | None = None
) -> pd.DataFrame:
    """Strip surrounding whitespace from string cells, preserving other values."""
    selected = _columns(frame, columns)
    result = frame.copy(deep=True)
    for column in selected:
        if frame[column].map(lambda item: isinstance(item, str)).any():
            result[column] = frame[column].map(lambda item: item.strip() if isinstance(item, str) else item)
    return result


def parse_dates(
    frame: pd.DataFrame,
    columns: Sequence[Any] | str,
    *,
    format: str | None = None,
) -> pd.DataFrame:
    """Parse selected columns with pandas, raising instead of coercing bad dates."""
    if columns is None:
        raise ValidationError("Date columns must be specified explicitly.")
    selected = _columns(frame, columns)
    result = frame.copy(deep=True)
    for column in selected:
        try:
            result[column] = pd.to_datetime(frame[column], format=format, errors="raise")
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValidationError(f"Cannot parse dates in column {column!r}: {exc}") from exc
    return result
