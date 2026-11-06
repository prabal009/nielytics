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
    "tsv": "text", "txt": "text", "dat": "text", "text": "text",
    "geojson": "geojson",
    "nc": "netcdf", "nc4": "netcdf", "netcdf": "netcdf",
    "shp": "shapefile", "shapefile": "shapefile",
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
            elif selected_format == "text":
                sep = kwargs.pop("sep", kwargs.pop("delimiter", None))
                if sep is None and path.suffix.lower() == ".tsv":
                    sep = "\t"
                if sep is not None:
                    frame = pd.read_csv(path, sep=sep, encoding=encoding, **kwargs)
                else:
                    frame = pd.read_csv(path, sep=None, engine="python", encoding=encoding, **kwargs)
            elif selected_format == "geojson":
                import json as _json
                with open(path, "r", encoding=encoding) as f:
                    gj = _json.load(f)
                if not isinstance(gj, dict):
                    raise DataLoadError(f"Invalid GeoJSON content in {path}")
                features = gj.get("features", [])
                if not isinstance(features, list):
                    raise DataLoadError(f"GeoJSON does not contain a valid features array in {path}")
                rows = []
                for feat in features:
                    props = feat.get("properties", {}) or {}
                    row = dict(props)
                    geom = feat.get("geometry")
                    if geom and isinstance(geom, dict):
                        coords = geom.get("coordinates")
                        geom_type = geom.get("type", "")
                        if geom_type == "Point" and isinstance(coords, (list, tuple)) and len(coords) >= 2:
                            if "longitude" not in row and "lon" not in row:
                                row["longitude"] = float(coords[0])
                            if "latitude" not in row and "lat" not in row:
                                row["latitude"] = float(coords[1])
                        row["geometry"] = geom
                    rows.append(row)
                frame = pd.DataFrame(rows)
            elif selected_format == "netcdf":
                try:
                    import xarray as xr
                    ds = xr.open_dataset(path, **kwargs)
                    frame = ds.to_dataframe().reset_index()
                except ImportError:
                    try:
                        import netCDF4  # noqa: F401
                        nc = netCDF4.Dataset(path)
                        data = {}
                        for var_name, var in nc.variables.items():
                            arr = var[:]
                            if getattr(arr, "ndim", 0) == 1:
                                data[var_name] = arr
                        frame = pd.DataFrame(data)
                    except ImportError as exc:
                        raise OptionalDependencyError(
                            "Loading NetCDF datasets requires 'xarray' or 'netCDF4'; install with pip install '.[climate]'"
                        ) from exc
            elif selected_format == "shapefile":
                try:
                    import geopandas as gpd
                    gdf = gpd.read_file(path, **kwargs)
                    frame = pd.DataFrame(gdf)
                except ImportError as exc:
                    raise OptionalDependencyError(
                        "Loading Shapefiles requires 'geopandas'; install with pip install '.[geospatial]'"
                    ) from exc
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

def load_text(source: str | os.PathLike[str], delimiter: str | None = None, **kwargs: Any) -> pd.DataFrame:
    """Load a delimited or tabular text file (.txt, .tsv, .dat)."""
    if delimiter is not None:
        kwargs["sep"] = delimiter
    return load_dataset(source, format="text", **kwargs)


def load_geojson_table(source: str | os.PathLike[str], **kwargs: Any) -> pd.DataFrame:
    """Extract properties and coordinates from a GeoJSON FeatureCollection into a DataFrame."""
    return load_dataset(source, format="geojson", **kwargs)


def load_netcdf(source: str | os.PathLike[str], **kwargs: Any) -> pd.DataFrame:
    """Load NetCDF dataset as a DataFrame using xarray or netCDF4."""
    return load_dataset(source, format="netcdf", **kwargs)


def load_shapefile(source: str | os.PathLike[str], **kwargs: Any) -> pd.DataFrame:
    """Load Shapefile as a DataFrame using geopandas."""
    return load_dataset(source, format="shapefile", **kwargs)
