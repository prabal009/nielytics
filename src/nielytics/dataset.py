"""Convenient dataset facade; transformations return independent datasets."""
from __future__ import annotations

from copy import deepcopy
from os import PathLike
from typing import Any

import pandas as pd

from .core import cleaner, profiler, statistics
from .core.loader import load_dataset


class Dataset:
    """Load a local table or copy a DataFrame.

    ``load_options`` are passed to :func:`core.loader.load_dataset`. The public
    ``frame`` property returns a defensive copy. As with pandas deep copies,
    mutable Python objects nested inside object-dtype cells are not isolated;
    use scalar tabular values. Cleaning never modifies this instance.
    """

    def __init__(self, source: pd.DataFrame | str | PathLike[str], **load_options: Any) -> None:
        self._frame = load_dataset(source, **load_options)
        self._history: list[dict[str, Any]] = []

    @property
    def frame(self) -> pd.DataFrame:
        """Return an independent table (subject to pandas object-cell semantics)."""
        return self._frame.copy(deep=True)

    @property
    def history(self) -> list[dict[str, Any]]:
        """Return cleaning operations and row counts, in execution order."""
        return deepcopy(self._history)

    def profile(self) -> dict[str, Any]:
        """Return a JSON-compatible dataset profile."""
        return profiler.profile_dataset(self._frame)

    def missing_report(self) -> pd.DataFrame:
        """Return per-column missing counts and percentages."""
        return cleaner.missing_report(self._frame)

    def summary(self, *, columns: list[str] | None = None, ddof: int = 1) -> pd.DataFrame:
        """Summarize numeric columns, skipping missing values; sample variance by default."""
        return statistics.summarize(self._frame, columns=columns, ddof=ddof)

    def _clean(self, operation: str, **options: Any) -> Dataset:
        frame = getattr(cleaner, operation)(self._frame, **options)
        result = Dataset(frame)
        result._history = self.history + [{
            "operation": operation,
            "parameters": deepcopy(options),
            "rows_before": len(self._frame),
            "rows_after": len(frame),
        }]
        return result

    def remove_duplicates(self, *, subset: list[str] | None = None,
                          keep: str | bool = "first") -> Dataset:
        """Explicitly remove duplicates in a new dataset, retaining original indices."""
        return self._clean("remove_duplicates", subset=subset, keep=keep)

    def fill_missing(self, *, columns: list[str] | None = None,
                     strategy: str = "mean", value: Any = None) -> Dataset:
        """Fill selected columns using mean, median, mode, or an explicit constant."""
        return self._clean("fill_missing", columns=columns, strategy=strategy, value=value)

    def standardize_columns(self) -> Dataset:
        """Normalize names explicitly; ambiguous collisions raise ValidationError."""
        return self._clean("standardize_columns")

    def clean_text(self, *, columns: list[str] | None = None) -> Dataset:
        """Strip surrounding whitespace without changing non-string values."""
        return self._clean("clean_text", columns=columns)

    def convert_types(self, mapping: dict[str, Any]) -> Dataset:
        """Convert explicitly named column types; failed conversions raise errors."""
        return self._clean("convert_types", mapping=mapping)

    def parse_dates(self, columns: str | list[str], *, format: str | None = None) -> Dataset:
        """Parse dates explicitly without coercing invalid observations to missing."""
        return self._clean("parse_dates", columns=columns, format=format)

    def to_records(self) -> list[dict[str, Any]]:
        """Return JSON-safe records: ISO dates and null for missing/nonfinite values.

        Pandas' JSON conversion defines scalar encoding and millisecond date
        precision. The index is deliberately omitted. This is tabular output,
        not a geographic or climate schema.
        """
        import json

        return json.loads(self._frame.to_json(orient="records", date_format="iso"))
