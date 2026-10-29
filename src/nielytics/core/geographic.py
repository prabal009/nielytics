"""Offline geographic figures with explicitly declared WGS84 coordinates."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from nielytics.exceptions import OptionalDependencyError, ValidationError

from .statistics import _selected_columns, _validate_frame

if TYPE_CHECKING:
    import geopandas as gpd
    from matplotlib.figure import Figure
    from numpy.typing import NDArray

__all__ = ["plot_geographic"]

_INSTALL_MESSAGE = (
    "Geographic plotting requires optional dependencies; "
    "install them with pip install '.[geospatial,visualization]'."
)
_GEOMETRY_TYPES = frozenset({
    "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon",
})


def _finite_column(frame: pd.DataFrame, column: Hashable) -> NDArray[np.float64]:
    _selected_columns(frame, [column])
    try:
        values = frame[column].to_numpy(dtype=float, na_value=np.nan)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"column must contain finite real numbers: {column!r}") from exc
    if not np.isfinite(values).all():
        raise ValidationError(f"column contains missing or nonfinite values: {column!r}")
    return values


def _validate_geometries(frame: gpd.GeoDataFrame) -> None:
    try:
        geometry = frame.geometry
    except AttributeError as exc:
        raise ValidationError("GeoDataFrame must have an active geometry column") from exc
    # Check emptiness separately: older GeoPandas versions include empty
    # geometries in isna(), which otherwise emits a migration warning.
    if geometry.is_empty.any():
        raise ValidationError("geometries must not be empty")
    if geometry.isna().any():
        raise ValidationError("geometries must not be missing")
    if not geometry.is_valid.all():
        raise ValidationError("geometries must be valid")
    if not geometry.geom_type.isin(_GEOMETRY_TYPES).all():
        raise ValidationError(
            "supported geometries are Point, MultiPoint, LineString, "
            "MultiLineString, Polygon, and MultiPolygon"
        )


def _project_geometries(frame: pd.DataFrame) -> gpd.GeoDataFrame:
    try:
        import geopandas as gpd
        from pyproj.exceptions import ProjError
    except ImportError as exc:
        raise OptionalDependencyError(_INSTALL_MESSAGE) from exc
    if not isinstance(frame, gpd.GeoDataFrame):
        raise ValidationError("geometry input must be a GeoDataFrame")
    _validate_geometries(frame)
    if frame.crs is None:
        raise ValidationError("GeoDataFrame must declare a CRS; no CRS is inferred")
    try:
        projected = frame.to_crs(epsg=4326)
    except (ValueError, TypeError, ProjError) as exc:
        raise ValidationError("geometries could not be reprojected to EPSG:4326") from exc
    _validate_geometries(projected)
    bounds = projected.bounds.to_numpy(dtype=float)
    if (
        not np.isfinite(bounds).all()
        or (bounds[:, [0, 2]] < -180).any()
        or (bounds[:, [0, 2]] > 180).any()
        or (bounds[:, [1, 3]] < -90).any()
        or (bounds[:, [1, 3]] > 90).any()
    ):
        raise ValidationError("projected geometry bounds must be finite and within WGS84 ranges")
    return projected


def plot_geographic(
    frame: pd.DataFrame,
    *,
    longitude: Hashable = "longitude",
    latitude: Hashable = "latitude",
    value: Hashable | None = None,
    title: str | None = None,
) -> Figure:
    """Return a non-mutating, offline Matplotlib geographic figure.

    Plain pandas frames supply real numeric longitude/latitude columns in
    explicitly assumed-by-contract WGS84 degrees: longitude in [-180, 180],
    latitude in [-90, 90]. Missing, infinite, boolean, complex, and nonnumeric
    coordinates are rejected; rows are never dropped. ``longitude`` and
    ``latitude`` are column labels, not coordinate arrays.

    GeoDataFrames instead use their active geometry and must declare a CRS.
    Point, MultiPoint, LineString, MultiLineString, Polygon, and MultiPolygon
    geometries must be valid, nonempty, and nonmissing. They are reprojected to
    EPSG:4326 without changing the input, then validated again, including their
    bounds. Longitude/latitude column arguments are ignored for GeoDataFrames.

    ``value`` optionally names a real numeric, entirely finite column for
    continuous coloring with a labeled colorbar. No units, hazard category,
    disaster risk, or causal meaning are inferred from values or locations.
    ``title`` must be a string or None. Duplicate column labels and empty frames
    are rejected. Duplicate row indices and repeated coordinates are allowed.

    The returned figure has ``nielytics_metadata`` containing ``geometry_crs``,
    ``input_count``, ``value_column``, ``units_inferred``, ``risk_inferred``, and
    ``limitations``. It uses longitude/latitude axes with equal degree scaling,
    not an equal-distance map projection, and does not split dateline-crossing
    geometries. No basemap, network request, or display call is made.

    Raises
    ------
    ValidationError
        If input data, geometries, coordinate ranges, or parameters are invalid.
    OptionalDependencyError
        If Matplotlib is unavailable, or GeoPandas/PyProj are unavailable for
        geometry input. Install with ``pip install '.[geospatial,visualization]'``.
        Optional dependencies are imported only when called; plain pandas
        coordinate frames do not require GeoPandas.
    """
    _validate_frame(frame)
    if frame.empty:
        raise ValidationError("frame must contain at least one observation")
    if title is not None and not isinstance(title, str):
        raise ValidationError("title must be a string or None")
    values = None if value is None else _finite_column(frame, value)

    # Recognize subclasses too, without importing GeoPandas for ordinary pandas
    # input. An actual GeoDataFrame necessarily already loaded its defining class.
    is_geographic = any(
        base.__name__ == "GeoDataFrame" and base.__module__.startswith("geopandas.")
        for base in type(frame).__mro__
    )
    projected = None
    if is_geographic:
        projected = _project_geometries(frame)
    else:
        lon = _finite_column(frame, longitude)
        lat = _finite_column(frame, latitude)
        if ((lon < -180) | (lon > 180)).any():
            raise ValidationError("longitude must be within [-180, 180] WGS84 degrees")
        if ((lat < -90) | (lat > 90)).any():
            raise ValidationError("latitude must be within [-90, 90] WGS84 degrees")

    try:
        from matplotlib.figure import Figure
    except ImportError as exc:
        raise OptionalDependencyError(_INSTALL_MESSAGE) from exc

    figure = Figure(layout="constrained")
    axes = figure.subplots()
    if projected is None:
        if values is None:
            axes.scatter(lon, lat)
        else:
            points = axes.scatter(lon, lat, c=values, cmap="viridis")
            figure.colorbar(points, ax=axes, label=str(value))
    else:
        try:
            if values is None:
                projected.plot(ax=axes, aspect=None)
            else:
                projected.plot(
                    ax=axes, column=values, cmap="viridis", legend=True,
                    legend_kwds={"label": str(value)}, aspect=None,
                )
        except ImportError as exc:
            raise OptionalDependencyError(_INSTALL_MESSAGE) from exc
    axes.set_xlabel("Longitude (degrees east)")
    axes.set_ylabel("Latitude (degrees north)")
    axes.set_aspect("equal", adjustable="box")
    if title is not None:
        figure.suptitle(title, wrap=True)
    figure.nielytics_metadata = {  # type: ignore[attr-defined]
        "geometry_crs": "EPSG:4326",
        "input_count": len(frame),
        "value_column": None if value is None else str(value),
        "units_inferred": False,
        "risk_inferred": False,
        "limitations": [
            "Locations and values do not establish hazards, disaster risk, or causation.",
            "Value units are not inferred or converted.",
            "Equal scaling in degrees does not preserve geographic distances or areas.",
            "Dateline-crossing geometries are not split; no basemap is included.",
        ],
    }
    return figure
