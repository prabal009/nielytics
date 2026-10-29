"""Non-mutating descriptive outlier masks; never remove observations."""

from __future__ import annotations

from collections.abc import Hashable
from numbers import Real

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError

from .statistics import _selected_columns


def detect_outliers(frame: pd.DataFrame, column: Hashable, *, method: str = "iqr",
                    threshold: float | None = None) -> pd.Series:
    """Return a boolean mask aligned with input rows; missing values are False.

    ``iqr`` uses Q1/Q3 ± 1.5 IQR; ``zscore`` uses population standard
    deviation and absolute z > 3; ``modified_zscore`` uses 0.6745 times
    deviation from median / MAD > 3.5; ``percentile`` uses the 1st and 99th
    quantiles. Override threshold with a positive IQR multiplier, z cutoff,
    modified-z cutoff, or percentile tail fraction in (0, 0.5).
    Constant samples or zero MAD yield no flags; no score is fabricated.
    These are exploratory flags, not evidence that readings are erroneous.
    """
    _selected_columns(frame, [column])
    defaults = {"iqr": 1.5, "zscore": 3.0, "modified_zscore": 3.5,
                "percentile": 0.01}
    if method not in defaults:
        raise ValidationError("method must be iqr, zscore, modified_zscore, or percentile")
    cutoff = defaults[method] if threshold is None else threshold
    if (isinstance(cutoff, bool) or not isinstance(cutoff, Real) or
            not np.isfinite(cutoff) or cutoff <= 0 or
            (method == "percentile" and cutoff >= 0.5)):
        raise ValidationError("threshold must be positive and finite (percentile < 0.5)")
    values = frame[column]
    finite = values.notna() & np.isfinite(values.to_numpy(dtype=float, na_value=np.nan))
    if (values.notna() & ~finite).any():
        raise ValidationError("outlier analysis requires finite observations")
    clean = values.loc[finite].astype(float)
    result = pd.Series(False, index=frame.index, name=f"{column}_outlier")
    if clean.empty:
        return result
    if method == "iqr":
        q1, q3 = clean.quantile([0.25, 0.75])
        scale = q3 - q1
        flags = (clean < q1 - cutoff * scale) | (clean > q3 + cutoff * scale)
    elif method == "zscore":
        scale = clean.std(ddof=0)
        flags = (clean - clean.mean()).abs() / scale > cutoff if scale else clean.ne(clean)
    elif method == "modified_zscore":
        center = clean.median()
        scale = (clean - center).abs().median()
        flags = 0.6745 * (clean - center).abs() / scale > cutoff if scale else clean.ne(clean)
    else:
        lower, upper = clean.quantile([cutoff, 1 - cutoff])
        flags = (clean < lower) | (clean > upper)
    result.loc[finite] = flags.to_numpy(dtype=bool)
    return result


def outlier_report(frame: pd.DataFrame, column: Hashable, *, method: str = "iqr",
                   threshold: float | None = None) -> dict[str, object]:
    """Summarize flagged and missing rows without deleting or modifying them."""
    flags = detect_outliers(frame, column, method=method, threshold=threshold)
    return {"column": str(column), "method": method, "threshold": threshold,
            "total_rows": len(frame), "missing_rows": int(frame[column].isna().sum()),
            "outlier_count": int(flags.sum()), "indices": flags.index[flags].tolist()}
