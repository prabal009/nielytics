"""Local, non-mutating dataset loading with explicit error categories."""

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pandas as pd

from nielytics.core.cleaner import parse_dates as _parse_dates
from nielytics.exceptions import (
    DataLoadError,
    OptionalDependencyError,
    UnsupportedFormatError,
    ValidationError,
)

_FORMATS = {
    "csv": "csv", "xls": "excel", "xlsx": "excel", "xlsm": "excel",
    "excel": "excel", "json": "json", "parquet": "parquet", "pq": "parquet",
}
DateColumns = str | Sequence[Any] | Mapping[Any, str | None]


def load_dataset(
    source: pd.DataFrame | str | os.PathLike[str],
    *,
    format: str | None = None,
    parse_dates: DateColumns | None = None,
    encoding: str = "utf-8",
    **kwargs: Any,
) -> pd.DataFrame:
    """Copy a DataFrame or read a local CSV, Excel, JSON, or Parquet file.

    File extensions select the reader unless ``format`` is supplied. Reader
    keyword arguments are forwarded to pandas. Date parsing accepts a column
    name, a sequence of names, or a mapping from names to date format strings.
    Names are never standardized implicitly. URLs and directories are rejected.
    Excel and Parquet require separately installed pandas reader engines.
    """
    selected_format = None
    if format is not None:
        if not isinstance(format, str) or format.lower().lstrip(".") not in _FORMATS:
            raise UnsupportedFormatError(f"Unsupported dataset format: {format!r}")
        selected_format = _FORMATS[format.lower().lstrip(".")]
    if isinstance(source, pd.DataFrame):
        if format is not None or kwargs:
            raise ValidationError("File format and reader options do not apply to DataFrame sources.")
        frame = source.copy(deep=True)
    else:
        if not isinstance(source, (str, os.PathLike)):
            raise ValidationError("source must be a DataFrame or a local file path.")
        try:
            raw_path = os.fspath(source)
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise ValidationError("source must be a non-empty text path.")
            if urlsplit(raw_path).scheme or raw_path.startswith("//"):
                raise ValidationError("Only local file paths are supported; URLs are not allowed.")
            path = Path(raw_path).expanduser()
            if not path.is_file():
                raise DataLoadError(f"Dataset path is not an existing file: {path}")
        except (OSError, ValueError) as exc:
            if isinstance(exc, ValidationError):
                raise
            raise DataLoadError(f"Invalid dataset path: {source!r}") from exc
        if selected_format is None:
            selected_format = _FORMATS.get(path.suffix.lower().lstrip("."))
        if selected_format is None:
            raise UnsupportedFormatError(f"Unsupported dataset extension: {path.suffix!r}")
        try:
            if selected_format == "csv":
                frame = pd.read_csv(path, encoding=encoding, **kwargs)
            elif selected_format == "excel":
                frame = pd.read_excel(path, **kwargs)
            elif selected_format == "json":
                # Use the same explicit date-conversion contract for all formats.
                options = {"convert_dates": False, **kwargs}
                frame = pd.read_json(path, encoding=encoding, **options)
            else:
                frame = pd.read_parquet(path, **kwargs)
        except ImportError as exc:
            raise OptionalDependencyError(f"Loading {selected_format} requires an optional reader dependency: {exc}") from exc
        except Exception as exc:
            raise DataLoadError(f"Could not load {selected_format} dataset {path}: {exc}") from exc
        if not isinstance(frame, pd.DataFrame):
            raise DataLoadError("Reader options must produce a single DataFrame, not sheets or chunks.")
        frame = frame.copy(deep=True)
    if parse_dates is not None:
        if isinstance(parse_dates, Mapping):
            for column, date_format in parse_dates.items():
                frame = _parse_dates(frame, [column], format=date_format)
        elif isinstance(parse_dates, (str, Sequence)):
            frame = _parse_dates(frame, parse_dates)
        else:
            raise ValidationError("parse_dates must be a column name, sequence, or format mapping.")
    return frame


def load_csv(source: str | os.PathLike[str], **kwargs: Any) -> pd.DataFrame:
    """Load a local CSV file; options follow :func:`load_dataset`."""
    return load_dataset(source, format="csv", **kwargs)


def load_excel(source: str | os.PathLike[str], **kwargs: Any) -> pd.DataFrame:
    """Load one local Excel worksheet; options follow :func:`load_dataset`."""
    return load_dataset(source, format="excel", **kwargs)


def load_json(source: str | os.PathLike[str], **kwargs: Any) -> pd.DataFrame:
    """Load a local JSON file; options follow :func:`load_dataset`."""
    return load_dataset(source, format="json", **kwargs)


def load_parquet(source: str | os.PathLike[str], **kwargs: Any) -> pd.DataFrame:
    """Load a local Parquet file; options follow :func:`load_dataset`."""
    return load_dataset(source, format="parquet", **kwargs)
