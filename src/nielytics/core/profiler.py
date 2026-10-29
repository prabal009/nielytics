"""JSON-compatible, non-mutating descriptive profiles of pandas DataFrames.

Missing values are excluded from unique counts and descriptive summaries.
Undefined or non-finite numbers become JSON null; datetime coverage uses ISO
8601 strings. Numeric summaries use sample variance/standard deviation (ddof=1).
Dates are recognized from datetime dtypes, not guessed from arbitrary strings.
"""

from __future__ import annotations

from collections.abc import Hashable
from datetime import date, datetime
from numbers import Integral, Real
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

from nielytics.core.statistics import _is_real_numeric, _validate_frame, summarize
from nielytics.exceptions import ValidationError


def _json_scalar(value: Any) -> Any:
    """Convert a pandas scalar to a finite JSON scalar without losing dates."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, str):
        return value
    return str(value)


def column_profile(frame: pd.DataFrame, column: Hashable) -> dict[str, Any]:
    """Profile one named column with finite JSON scalars and ISO dates.

    ``missing`` contains count and percentage (0 to 100); ``unique`` excludes
    missing values. Only the applicable numeric, categorical, or date summary
    is populated. Categorical ties use pandas' value-count ordering. A numeric
    all-null column has null descriptive statistics and count zero.
    """
    _validate_frame(frame)
    try:
        exists = column in frame.columns
    except TypeError as exc:
        raise ValidationError("column must be a hashable label") from exc
    if not exists:
        raise ValidationError(f"unknown column: {column!r}")
    values = frame[column]
    count = len(values)
    missing = int(values.isna().sum())
    unique = int(values.nunique(dropna=True))
    warnings: list[str] = []
    if count and missing == count:
        warnings.append(f"Column {column!r} contains only missing values.")
    elif missing:
        warnings.append(f"Column {column!r} has {missing} missing values.")
    if unique == 1:
        warnings.append(f"Column {column!r} has one distinct non-missing value.")
    result: dict[str, Any] = {
        "name": str(column),
        "dtype": str(values.dtype),
        "missing": {"count": missing, "percentage": 100.0 * missing / count if count else 0.0},
        "unique": unique,
        "numeric_summary": None,
        "categorical_summary": None,
        "date_coverage": None,
        "memory_bytes": int(values.memory_usage(index=False, deep=True)),
        "warnings": warnings,
    }
    if _is_real_numeric(values):
        summary = summarize(frame, columns=[column]).iloc[0]
        result["numeric_summary"] = {str(key): _json_scalar(value) for key, value in summary.items()}
        result["numeric_summary"]["count"] = int(values.count())
        present = values.dropna()
        if len(present) and not bool(np.isfinite(present).all()):
            warnings.append(f"Column {column!r} contains non-finite numeric values.")
    elif is_datetime64_any_dtype(values.dtype):
        result["date_coverage"] = {
            "count": int(values.count()),
            "min": _json_scalar(values.min()),
            "max": _json_scalar(values.max()),
        }
    else:
        counts = values.value_counts(dropna=True)
        counts = counts[counts > 0]
        result["categorical_summary"] = {
            "count": int(values.count()),
            "unique": unique,
            "top": _json_scalar(counts.index[0]) if len(counts) else None,
            "frequency": int(counts.iloc[0]) if len(counts) else 0,
        }
    return result


def profile_dataset(frame: pd.DataFrame) -> dict[str, Any]:
    """Return dimensions, types, missingness, summaries, and quality warnings.

    All values are accepted by ``json.dumps(..., allow_nan=False)``. Column
    labels are stringified as JSON object keys; ambiguous stringified labels
    are rejected. Duplicate counts count repeated rows after their first
    occurrence. Memory usage includes the index and pandas' deep estimates.
    The source frame is never modified, including when empty or all-null.
    """
    _validate_frame(frame)
    labels = [str(column) for column in frame.columns]
    if len(set(labels)) != len(labels):
        raise ValidationError("column labels must have distinct string representations")
    result: dict[str, Any] = {
        "rows": len(frame),
        "columns": len(frame.columns),
        "dtypes": {},
        "missing": {},
        "unique": {},
        "duplicate_count": int(frame.duplicated().sum()),
        "numeric_summary": {},
        "categorical_summary": {},
        "date_coverage": {},
        "memory_bytes": int(frame.memory_usage(index=True, deep=True).sum()),
        "warnings": [],
    }
    for column, label in zip(frame.columns, labels):
        profile = column_profile(frame, column)
        for field in ("dtypes", "missing", "unique"):
            result[field][label] = profile["dtype" if field == "dtypes" else field]
        for field in ("numeric_summary", "categorical_summary", "date_coverage"):
            if profile[field] is not None:
                result[field][label] = profile[field]
        result["warnings"].extend(profile["warnings"])
    if result["duplicate_count"]:
        result["warnings"].append(f"Dataset contains {result['duplicate_count']} duplicate rows.")
    if not len(frame):
        result["warnings"].append("Dataset has no rows.")
    return result


def data_quality_report(frame: pd.DataFrame) -> dict[str, Any]:
    """Return descriptive missingness/duplicate counts and plain warnings.

    ``missing_percentage`` is the percentage of all cells missing, or zero
    when there are no cells. Warnings describe observations only; no quality
    score, domain inference, or automatic data correction is performed.
    """
    profile = profile_dataset(frame)
    total_missing = sum(value["count"] for value in profile["missing"].values())
    cells = profile["rows"] * profile["columns"]
    return {
        "rows": profile["rows"],
        "columns": profile["columns"],
        "missing": profile["missing"],
        "total_missing": total_missing,
        "missing_percentage": 100.0 * total_missing / cells if cells else 0.0,
        "duplicate_count": profile["duplicate_count"],
        "warnings": profile["warnings"],
    }
