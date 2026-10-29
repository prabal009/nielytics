"""Non-mutating Plotly charts with explicit missing-observation accounting.

Plotly is loaded only when a chart is built. Charts never infer measurement
units or launch a viewer. ``layout.meta`` records input/used/omitted row counts,
missing observations, and the missing-data policy. Omission emits UserWarning.
"""

from __future__ import annotations

import warnings
from collections.abc import Hashable, Iterable
from numbers import Integral, Number
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from nielytics.exceptions import OptionalDependencyError, ValidationError

from .geographic import plot_geographic
from .statistics import _selected_columns, _validate_frame, correlation_matrix

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

__all__ = [
    "plot_bar",
    "plot_box",
    "plot_correlation",
    "plot_distribution",
    "plot_geographic",
    "plot_histogram",
    "plot_line",
    "plot_scatter",
    "plot_seasonal",
    "plot_timeseries",
]


def _plotly() -> Any:
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise OptionalDependencyError(
            "Plotting requires Plotly; install with pip install '.[visualization]'"
        ) from exc
    return go


def _frame(frame: pd.DataFrame) -> None:
    _validate_frame(frame)
    if frame.empty:
        raise ValidationError("frame must contain observations")


def _numeric(frame: pd.DataFrame, columns: list[Hashable]) -> None:
    _selected_columns(frame, columns)
    for column in columns:
        values = frame[column].to_numpy(dtype=float, na_value=np.nan)
        if np.isinf(values).any():
            raise ValidationError(f"column contains infinite values: {column!r}")


def _values(series: pd.Series) -> list[Any]:
    # Explicit None keeps nullable pandas values serializable and line gaps visible.
    return [None if pd.isna(value) else value for value in series]


def _metadata(
    frame: pd.DataFrame, columns: list[Hashable], *, policy: str,
    used_rows: int | None = None,
) -> dict[str, Any]:
    selected = frame.loc[:, columns]
    missing = selected.isna()
    missing_count = int(missing.to_numpy().sum())
    used = len(frame) if used_rows is None else used_rows
    if missing_count and policy != "retain gaps":
        warnings.warn(
            f"{missing_count} missing observations excluded ({policy}); "
            "see figure.layout.meta for counts.",
            UserWarning, stacklevel=3,
        )
    return {
        "input_rows": len(frame), "used_rows": used,
        "omitted_rows": len(frame) - used,
        "missing_observations": missing_count,
        "rows_with_missing": int(missing.any(axis=1).sum()),
        "missing_policy": policy,
        "columns": [str(column) for column in columns],
        "missing_by_column": [int(missing[column].sum()) for column in columns],
    }


def _finish(
    figure: Figure, *, title: str | None, x: str, y: str,
    metadata: dict[str, Any],
) -> Figure:
    if title is not None and not isinstance(title, str):
        raise ValidationError("title must be a string or None")
    figure.update_layout(title=title, xaxis_title=x, yaxis_title=y, meta=metadata)
    return figure


def _xy(frame: pd.DataFrame, x: Hashable, y: Hashable) -> None:
    _frame(frame)
    _selected_columns(frame, [x], numeric=False)
    _numeric(frame, [y])
    if frame[x].isna().any():
        raise ValidationError(f"x column contains missing values: {x!r}")
    if is_numeric_dtype(frame[x].dtype):
        _numeric(frame, [x])
    elif any(isinstance(value, Number) and not np.isfinite(value) for value in frame[x]):
        raise ValidationError(f"x column contains infinite values: {x!r}")
    if not frame[y].notna().any():
        raise ValidationError("no usable numeric observations")


def plot_line(
    frame: pd.DataFrame, x: Hashable, y: Hashable, *, title: str | None = None,
) -> Figure:
    """Plot rows in input order, retaining missing y as gaps; missing x is invalid."""
    _xy(frame, x, y)
    go = _plotly()
    figure = go.Figure(go.Scatter(
        x=_values(frame[x]), y=_values(frame[y]), mode="lines", connectgaps=False,
        name=str(y),
    ))
    return _finish(figure, title=title, x=str(x), y=str(y), metadata=_metadata(
        frame, list(dict.fromkeys([x, y])), policy="retain gaps",
    ))


def plot_bar(
    frame: pd.DataFrame, x: Hashable, y: Hashable, *, title: str | None = None,
) -> Figure:
    """Plot one bar per row without aggregation; missing y stays missing."""
    _xy(frame, x, y)
    go = _plotly()
    figure = go.Figure(go.Bar(x=_values(frame[x]), y=_values(frame[y]), name=str(y)))
    return _finish(figure, title=title, x=str(x), y=str(y), metadata=_metadata(
        frame, list(dict.fromkeys([x, y])), policy="retain gaps",
    ))


def _histogram(
    frame: pd.DataFrame, column: Hashable, bins: int, title: str | None,
    *, density: bool,
) -> Figure:
    _frame(frame)
    _numeric(frame, [column])
    if isinstance(bins, bool) or not isinstance(bins, Integral) or bins < 1:
        raise ValidationError("bins must be a positive integer")
    values = frame[column].dropna()
    if values.empty:
        raise ValidationError("no usable numeric observations")
    go = _plotly()
    figure = go.Figure(go.Histogram(
        x=values.to_numpy(dtype=float), nbinsx=int(bins),
        histnorm="probability density" if density else None, name=str(column),
    ))
    metadata = _metadata(frame, [column], policy="omit missing values", used_rows=len(values))
    metadata.update({"bins": int(bins), "normalization": "probability density" if density else "count"})
    return _finish(figure, title=title, x=str(column),
                   y="Probability density" if density else "Count", metadata=metadata)


def plot_histogram(
    frame: pd.DataFrame, column: Hashable, *, bins: int = 20, title: str | None = None,
) -> Figure:
    """Plot counts, omitting missing values with warning/counts; bins is Plotly's target."""
    return _histogram(frame, column, bins, title, density=False)


def plot_distribution(
    frame: pd.DataFrame, column: Hashable, *, bins: int = 20, title: str | None = None,
) -> Figure:
    """Plot a probability-density histogram (area one), not a KDE.

    Missing values are omitted with a warning/counts. ``bins`` is Plotly's target
    bin count; Plotly may adjust bin edges to convenient boundaries.
    """
    return _histogram(frame, column, bins, title, density=True)


def plot_box(
    frame: pd.DataFrame, columns: Iterable[Hashable] | Hashable | None = None,
    *, title: str | None = None,
) -> Figure:
    """Plot selected real numeric columns; None selects all real numeric columns.

    Missing values are omitted independently per column with warning/counts.
    Columns with no observations are retained as empty traces if others are usable.
    """
    _frame(frame)
    selected = _selected_columns(frame, columns)
    if not selected:
        raise ValidationError("at least one real numeric column is required")
    _numeric(frame, selected)
    usable = frame.loc[:, selected].notna().any(axis=1)
    if not usable.any():
        raise ValidationError("no usable numeric observations")
    go = _plotly()
    figure = go.Figure()
    for column in selected:
        figure.add_trace(go.Box(y=frame[column].dropna().to_numpy(dtype=float), name=str(column)))
    return _finish(figure, title=title, x="Column", y="Value", metadata=_metadata(
        frame, selected, policy="omit missing values per column", used_rows=int(usable.sum()),
    ))


def plot_scatter(
    frame: pd.DataFrame, x: Hashable, y: Hashable, *, title: str | None = None,
) -> Figure:
    """Plot complete numeric x/y pairs, warning and counting omitted rows."""
    _frame(frame)
    _selected_columns(frame, [x], numeric=False)
    _selected_columns(frame, [y], numeric=False)
    selected = list(dict.fromkeys([x, y]))
    _numeric(frame, selected)
    usable = frame.loc[:, selected].notna().all(axis=1)
    if not usable.any():
        raise ValidationError("no complete numeric pairs")
    go = _plotly()
    figure = go.Figure(go.Scatter(
        x=frame.loc[usable, x].to_numpy(dtype=float),
        y=frame.loc[usable, y].to_numpy(dtype=float), mode="markers", name=str(y),
    ))
    return _finish(figure, title=title, x=str(x), y=str(y), metadata=_metadata(
        frame, selected, policy="omit incomplete pairs", used_rows=int(usable.sum()),
    ))


def plot_correlation(
    frame: pd.DataFrame, *, method: str = "pearson", title: str | None = None,
) -> Figure:
    """Plot pairwise-complete numeric correlations; undefined cells remain missing.

    Methods are pearson, spearman and kendall. Non-real-numeric columns are not
    selected. Metadata includes pairwise sample counts; correlation is not causation.
    """
    _frame(frame)
    if not isinstance(method, str) or method not in ("pearson", "spearman", "kendall"):
        raise ValidationError("method must be 'pearson', 'spearman', or 'kendall'")
    selected = _selected_columns(frame, None)
    if not selected:
        raise ValidationError("at least one real numeric column is required")
    _numeric(frame, selected)
    matrix = correlation_matrix(frame, method=method)
    if not np.isfinite(matrix.to_numpy()).any():
        raise ValidationError("no defined correlations")
    present = frame.loc[:, selected].notna().astype(np.int64)
    metadata = _metadata(frame, selected, policy="pairwise complete observations",
                         used_rows=int(present.any(axis=1).sum()))
    metadata.update({"method": method, "pairwise_counts": (present.T @ present).to_numpy().tolist(),
                     "limitation": "Correlation is not causation."})
    go = _plotly()
    labels = [str(column) for column in selected]
    figure = go.Figure(go.Heatmap(
        z=matrix.to_numpy(), x=labels, y=labels, zmin=-1, zmax=1,
        zmid=0, colorscale="RdBu", colorbar={"title": "Correlation"},
    ))
    return _finish(figure, title=title, x="Column", y="Column", metadata=metadata)


def _dates(frame: pd.DataFrame, date_column: Hashable, value_column: Hashable) -> pd.Series:
    _frame(frame)
    _selected_columns(frame, [date_column], numeric=False)
    _numeric(frame, [value_column])
    dates = frame[date_column]
    if dates.isna().any():
        raise ValidationError("date column must not contain missing dates")
    if is_numeric_dtype(dates.dtype) or any(isinstance(value, Number) for value in dates):
        raise ValidationError("numeric dates are not supported; provide date strings or timestamps")
    try:
        parsed = pd.to_datetime(dates, errors="raise", format="mixed")
        # Require a single comparable datetime dtype, not mixed time zones.
        _ = parsed.dt
    except (ValueError, TypeError, AttributeError, OverflowError) as exc:
        raise ValidationError("date column must contain valid, consistently zoned dates") from exc
    if parsed.isna().any():
        raise ValidationError("date column must not contain missing dates")
    if not frame[value_column].notna().any():
        raise ValidationError("no usable numeric observations")
    return parsed


def plot_timeseries(
    frame: pd.DataFrame, date_column: Hashable, value_column: Hashable,
    *, title: str | None = None,
) -> Figure:
    """Plot strictly parsed dates in stable chronological order.

    Duplicate dates and missing-value gaps remain. No frequency, resampling or
    missing timestamps are inferred. Numeric/missing dates are rejected.
    """
    dates = _dates(frame, date_column, value_column)
    order = np.argsort(dates.to_numpy(), kind="stable")
    go = _plotly()
    figure = go.Figure(go.Scatter(
        x=_values(dates.iloc[order]), y=_values(frame[value_column].iloc[order]),
        mode="lines", connectgaps=False, name=str(value_column),
    ))
    return _finish(figure, title=title, x=str(date_column), y=str(value_column),
                   metadata=_metadata(frame, [value_column], policy="retain gaps"))


def plot_seasonal(
    frame: pd.DataFrame, date_column: Hashable, value_column: Hashable,
    *, aggregation: str = "mean", title: str | None = None,
) -> Figure:
    """Aggregate observations by calendar month across years (not annual means).

    Mean, sum and median skip missing values with warning/counts. All twelve
    months are shown; absent/all-missing months stay missing (sum uses min_count=1).
    No units or frequency are inferred, and duplicate dates remain observations.
    """
    if not isinstance(aggregation, str) or aggregation not in ("mean", "sum", "median"):
        raise ValidationError("aggregation must be 'mean', 'sum', or 'median'")
    dates = _dates(frame, date_column, value_column)
    grouped = frame[value_column].groupby(dates.dt.month.to_numpy())
    result = (grouped.sum(min_count=1) if aggregation == "sum"
              else grouped.agg(aggregation)).reindex(range(1, 13))
    if np.isinf(result.to_numpy(dtype=float, na_value=np.nan)).any():
        raise ValidationError("seasonal aggregation produced infinite values")
    metadata = _metadata(frame, [value_column], policy="omit missing values in aggregation",
                         used_rows=int(frame[value_column].notna().sum()))
    metadata.update({"aggregation": aggregation,
                     "monthly_counts": grouped.count().reindex(range(1, 13), fill_value=0).tolist()})
    go = _plotly()
    figure = go.Figure(go.Scatter(
        x=list(range(1, 13)), y=_values(result), mode="lines+markers",
        connectgaps=False, name=str(value_column),
    ))
    figure.update_xaxes(tickmode="array", tickvals=list(range(1, 13)))
    return _finish(figure, title=title, x=f"{date_column} (month)",
                   y=str(value_column), metadata=metadata)
