"""Non-mutating descriptive statistics using pandas.

Missing values are skipped. Variance and standard deviation default to sample
statistics (``ddof=1``); use ``ddof=0`` for population statistics. Undefined
statistics remain NaN, including insufficient samples and constant-column
correlations. Floating-point precision follows pandas and NumPy.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from numbers import Integral, Real
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype

from nielytics.exceptions import ValidationError

_SUMMARY_COLUMNS = [
    "count", "mean", "median", "variance", "std", "min", "max",
    "q25", "q75", "skew", "kurtosis",
]


def _validate_frame(frame: pd.DataFrame) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise ValidationError("frame must be a pandas DataFrame")
    if not frame.columns.is_unique:
        raise ValidationError("column labels must be unique")


def _validate_ddof(ddof: int) -> None:
    if isinstance(ddof, bool) or not isinstance(ddof, Integral) or ddof < 0:
        raise ValidationError("ddof must be a nonnegative integer")


def _is_real_numeric(series: pd.Series) -> bool:
    return (
        is_numeric_dtype(series.dtype)
        and not is_bool_dtype(series.dtype)
        and not is_complex_dtype(series.dtype)
    )


def _selected_columns(
    frame: pd.DataFrame,
    columns: Iterable[Hashable] | Hashable | None,
    *,
    numeric: bool = True,
) -> list[Hashable]:
    _validate_frame(frame)
    if columns is None:
        return [c for c in frame.columns if not numeric or _is_real_numeric(frame[c])]
    if isinstance(columns, (str, bytes)):
        selected = [columns]
    else:
        try:
            selected = list(columns)  # type: ignore[arg-type]
        except TypeError:
            selected = [columns]
    try:
        if len(set(selected)) != len(selected):
            raise ValidationError("selected columns must be unique")
        for column in selected:
            if column not in frame.columns:
                raise ValidationError(f"unknown column: {column!r}")
            if numeric and not _is_real_numeric(frame[column]):
                raise ValidationError(f"column must be real numeric: {column!r}")
    except TypeError as exc:
        raise ValidationError("column labels must be hashable") from exc
    return selected


def summarize(
    frame: pd.DataFrame,
    *,
    columns: Iterable[Hashable] | None = None,
    ddof: int = 1,
) -> pd.DataFrame:
    """Summarize real numeric columns, skipping missing values.

    Rows are column names; count excludes missing values. ``ddof`` controls
    variance/std denominators (N - ddof). Skew and Fisher excess kurtosis use
    pandas' unbiased estimators; undefined results are NaN. Boolean and complex
    columns are not selected automatically and cannot be selected explicitly.
    """
    _validate_ddof(ddof)
    selected = _selected_columns(frame, columns)
    records = []
    for column in selected:
        values = frame[column]
        records.append([
            values.count(), values.mean(), values.median(), values.var(ddof=ddof),
            values.std(ddof=ddof), values.min(), values.max(),
            values.quantile(0.25), values.quantile(0.75), values.skew(), values.kurt(),
        ])
    return pd.DataFrame(
        records, index=pd.Index(selected, name="column", tupleize_cols=False),
        columns=_SUMMARY_COLUMNS,
    )


def correlation_matrix(frame: pd.DataFrame, *, method: str = "pearson") -> pd.DataFrame:
    """Return pairwise-complete real-numeric correlations.

    ``method`` is Pearson linear, Spearman rank, or Kendall rank correlation.
    Constant or insufficient observations produce NaN as in pandas; no missing
    values are filled. SciPy is used by pandas for Kendall correlation.
    """
    selected = _selected_columns(frame, None)
    if method not in ("pearson", "spearman", "kendall"):
        raise ValidationError("method must be 'pearson', 'spearman', or 'kendall'")
    return frame.loc[:, selected].corr(method=method)


def covariance_matrix(frame: pd.DataFrame, *, ddof: int = 1) -> pd.DataFrame:
    """Return pairwise-complete covariance with denominator N - ddof.

    Each cell uses only rows observed in both columns. Unlike pandas versions
    that ignore ddof when missing values occur, this applies ddof to every pair.
    A nonpositive denominator yields NaN.
    """
    _validate_ddof(ddof)
    selected = _selected_columns(frame, None)
    result = pd.DataFrame(np.nan, index=selected, columns=selected, dtype=float)
    for left_index, left in enumerate(selected):
        for right_index in range(left_index, len(selected)):
            right = selected[right_index]
            valid = frame[left].notna() & frame[right].notna()
            count = int(valid.sum())
            if count <= ddof:
                continue
            x = frame.loc[valid, left].astype(float)
            y = frame.loc[valid, right].astype(float)
            value = ((x - x.mean()) * (y - y.mean())).sum(skipna=False) / (count - ddof)
            result.iat[left_index, right_index] = value
            result.iat[right_index, left_index] = value
    return result


def grouped_summary(
    frame: pd.DataFrame,
    by: Hashable | Iterable[Hashable],
    *,
    columns: Iterable[Hashable] | None = None,
    ddof: int = 1,
) -> pd.DataFrame:
    """Summarize numeric columns per group, including missing group keys.

    Rows have a MultiIndex of grouping keys followed by ``column``. Grouping
    columns are excluded from automatic numeric selection. Groups retain first
    appearance order; unobserved categorical groups are omitted. Missing values
    in measurements are skipped, with the same ddof semantics as ``summarize``.
    """
    _validate_ddof(ddof)
    if by is None:
        raise ValidationError("by must name at least one grouping column")
    groups = _selected_columns(frame, by, numeric=False)
    if not groups:
        raise ValidationError("by must name at least one grouping column")
    selected = _selected_columns(frame, columns)
    if columns is None:
        selected = [column for column in selected if column not in groups]
    records: list[list[Any]] = []
    keys: list[tuple[Any, ...]] = []
    grouper = groups[0] if len(groups) == 1 else groups
    for key, group in frame.groupby(grouper, dropna=False, observed=True, sort=False):
        key_tuple = (key,) if len(groups) == 1 else key
        summary = summarize(group, columns=selected, ddof=ddof)
        for column, row in summary.iterrows():
            keys.append((*key_tuple, column))
            records.append(row.tolist())
    index = pd.MultiIndex.from_tuples(keys, names=[*groups, "column"])
    return pd.DataFrame(records, index=index, columns=_SUMMARY_COLUMNS)


def frequency_distribution(
    frame: pd.DataFrame, column: Hashable, *, dropna: bool = False,
) -> pd.DataFrame:
    """Return descending counts and proportions, indexed by observed values.

    Missing values are included by default; with ``dropna=True`` they are also
    excluded from the proportion denominator. Empty input produces no rows.
    """
    selected = _selected_columns(frame, [column], numeric=False)
    if not isinstance(dropna, bool):
        raise ValidationError("dropna must be a boolean")
    counts = frame[selected[0]].value_counts(dropna=dropna)
    counts = counts[counts > 0]
    result = counts.rename("count").to_frame()
    total = counts.sum()
    result["proportion"] = counts / total if total else 0.0
    result.index.name = column
    return result


def quantiles(
    frame: pd.DataFrame,
    *,
    q: Iterable[float] | float = (0.25, 0.5, 0.75),
    columns: Iterable[Hashable] | None = None,
) -> pd.DataFrame:
    """Return linear-interpolated numeric quantiles, skipping missing values.

    Rows are probabilities in [0, 1], in requested order. A scalar probability
    still returns a DataFrame with one row; empty/all-null columns yield NaN.
    """
    selected = _selected_columns(frame, columns)
    if isinstance(q, Real) and not isinstance(q, bool):
        probabilities = [q]
    else:
        try:
            probabilities = list(q)  # type: ignore[arg-type]
        except TypeError as exc:
            raise ValidationError("q must contain probabilities between 0 and 1") from exc
    for probability in probabilities:
        if (
            isinstance(probability, bool) or not isinstance(probability, Real)
            or not np.isfinite(probability) or not 0 <= probability <= 1
        ):
            raise ValidationError("q must contain finite probabilities between 0 and 1")
    result = frame.loc[:, selected].quantile(probabilities, interpolation="linear")
    result.index.name = "q"
    return result


def modes(
    frame: pd.DataFrame, *, columns: Iterable[Hashable] | None = None,
) -> pd.DataFrame:
    """Return all tied modes for selected columns, numeric or categorical.

    Missing values are skipped. Each column's modes occupy successive rows;
    columns with fewer modes are padded with missing values, as in pandas.
    """
    selected = _selected_columns(frame, columns, numeric=False)
    return frame.loc[:, selected].mode(dropna=True)
