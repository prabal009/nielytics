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


def z_score(
    frame: pd.DataFrame,
    columns: Iterable[Hashable] | None = None,
    *,
    ddof: int = 1,
) -> pd.DataFrame:
    """Compute z-scores ((x - mean) / std) for real numeric columns.

    Columns with zero sample variance or single observations yield 0.0.
    Missing values remain NaN. Returns a non-mutating copy.
    """
    _validate_ddof(ddof)
    selected = _selected_columns(frame, columns)
    result = pd.DataFrame(index=frame.index)
    for col in selected:
        series = frame[col].astype(float)
        mean = series.mean()
        std = series.std(ddof=ddof)
        if pd.isna(std) or std < 1e-12:
            col_z = series.where(series.isna(), 0.0)
        else:
            col_z = (series - mean) / std
        result[col] = col_z
    return result


def linear_regression(
    frame: pd.DataFrame,
    x_col: Hashable,
    y_col: Hashable,
    *,
    confidence_level: float = 0.95,
) -> dict[str, Any]:
    """Ordinary least squares linear regression with Student-t confidence intervals.

    Returns a strictly JSON-serializable dictionary with slope, intercept,
    r-squared, p-value, standard error, and slope confidence bounds.
    """
    from scipy import stats

    _selected_columns(frame, [x_col, y_col])
    if not (0.0 < confidence_level < 1.0):
        raise ValidationError("confidence_level must be between 0 and 1 exclusive.")

    valid = frame[[x_col, y_col]].dropna()
    x = valid[x_col].to_numpy(dtype=float)
    y = valid[y_col].to_numpy(dtype=float)

    if len(x) < 3:
        raise ValidationError("linear_regression requires at least 3 valid observations.")

    res = stats.linregress(x, y)
    n = len(x)
    df = n - 2
    t_crit = float(stats.t.ppf((1.0 + confidence_level) / 2.0, df=df))
    slope_err = float(res.stderr) if res.stderr is not None else 0.0
    moe = t_crit * slope_err

    return {
        "slope": float(round(res.slope, 6)),
        "intercept": float(round(res.intercept, 6)),
        "r_value": float(round(res.rvalue, 6)),
        "r_squared": float(round(res.rvalue ** 2, 6)),
        "p_value": float(round(res.pvalue, 6)),
        "std_err": float(round(slope_err, 6)),
        "slope_ci_lower": float(round(res.slope - moe, 6)),
        "slope_ci_upper": float(round(res.slope + moe, 6)),
        "confidence_level": float(confidence_level),
        "n_observations": int(n),
    }


def theil_sen_slope(
    frame: pd.DataFrame,
    y_col: Hashable,
    x_col: Hashable | None = None,
    *,
    alpha: float = 0.95,
) -> dict[str, Any]:
    """Compute robust nonparametric Theil-Sen trend slope and confidence bounds.

    Resistant to up to 29% outliers. If `x_col` is None, integer row indices are used.
    """
    from scipy import stats

    _selected_columns(frame, [y_col])
    if x_col is not None:
        _selected_columns(frame, [x_col])
        valid = frame[[x_col, y_col]].dropna()
        x = valid[x_col].to_numpy(dtype=float)
        y = valid[y_col].to_numpy(dtype=float)
    else:
        valid_y = frame[y_col].dropna()
        x = np.arange(len(valid_y), dtype=float)
        y = valid_y.to_numpy(dtype=float)

    if len(y) < 3:
        raise ValidationError("theil_sen_slope requires at least 3 valid observations.")

    res = stats.theilslopes(y, x, alpha=alpha)
    return {
        "slope": float(round(res.slope, 6)),
        "intercept": float(round(res.intercept, 6)),
        "slope_ci_lower": float(round(res.low_slope, 6)),
        "slope_ci_upper": float(round(res.high_slope, 6)),
        "alpha": float(alpha),
        "n_observations": len(y),
    }


def mann_kendall_test(
    series: Any,
    *,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Nonparametric Mann-Kendall trend test with tie correction.

    Calculates Kendall's S statistic, variance with tie adjustment, standard normal
    test statistic Z, two-tailed p-value, and trend classification.
    """
    from scipy import stats

    if isinstance(series, pd.DataFrame):
        raise ValidationError("mann_kendall_test requires a 1D Series or Sequence.")
    if isinstance(series, pd.Series):
        clean = series.dropna().to_numpy(dtype=float)
    else:
        arr = np.asarray(series, dtype=float)
        clean = arr[np.isfinite(arr)]

    n = len(clean)
    if n < 3:
        raise ValidationError("mann_kendall_test requires at least 3 valid observations.")

    i_idx, j_idx = np.triu_indices(n, k=1)
    pair_diffs = clean[j_idx] - clean[i_idx]
    s = int(np.sum(np.sign(pair_diffs)))

    # Tie correction for variance
    _, counts = np.unique(clean, return_counts=True)
    tie_term = int(np.sum(counts * (counts - 1) * (2 * counts + 5)))
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0

    if var_s <= 0:
        sigma_s = 1.0
    else:
        sigma_s = float(np.sqrt(var_s))

    if s > 0:
        z = (s - 1.0) / sigma_s
    elif s == 0:
        z = 0.0
    else:
        z = (s + 1.0) / sigma_s

    p_value = float(2.0 * (1.0 - stats.norm.cdf(abs(z))))
    total_pairs = n * (n - 1) / 2.0
    tau = float(s / total_pairs) if total_pairs > 0 else 0.0

    if p_value < alpha:
        trend = "increasing" if z > 0 else "decreasing"
    else:
        trend = "no_trend"

    return {
        "s": int(s),
        "z": float(round(z, 4)),
        "p_value": float(round(p_value, 6)),
        "tau": float(round(tau, 4)),
        "variance_s": float(round(var_s, 4)),
        "trend": trend,
        "alpha": float(alpha),
        "n_observations": int(n),
    }
