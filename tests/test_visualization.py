"""Consumer-visible chart data, missingness, coordinates, and isolation."""

import builtins
import json

import numpy as np
import pandas as pd
import pytest

from nielytics.exceptions import OptionalDependencyError, ValidationError

pytest.importorskip("plotly")
from nielytics.core import visualization as viz


def test_timeseries_orders_dates_preserves_gaps_and_input():
    frame = pd.DataFrame({"date": ["2025-03-01", "2025-01-01", "2025-02-01"],
                          "value": [3., 1., np.nan]})
    original = frame.copy(deep=True)
    figure = viz.plot_timeseries(frame, "date", "value")
    assert list(pd.to_datetime(figure.data[0].x).month) == [1, 2, 3]
    values = list(figure.data[0].y)
    assert values[0] == 1 and values[2] == 3
    assert values[1] is None or pd.isna(values[1])
    assert not figure.data[0].connectgaps
    pd.testing.assert_frame_equal(frame, original)
    assert json.loads(figure.to_json())["data"][0]["type"] == "scatter"


def test_seasonal_aggregates_years_without_zero_filling():
    frame = pd.DataFrame({"date": ["2024-01-01", "2025-01-01", "2025-03-01"],
                          "value": [2., 6., 9.]})
    figure = viz.plot_seasonal(frame, "date", "value")
    values = list(figure.data[0].y)
    assert values[0] == 4 and values[2] == 9
    assert values[1] is None or pd.isna(values[1])
    summed = viz.plot_seasonal(frame, "date", "value", aggregation="sum")
    assert summed.data[0].y[0] == 8
    assert summed.data[0].y[1] is None or pd.isna(summed.data[0].y[1])


def test_correlation_has_expected_signed_values():
    frame = pd.DataFrame({"a": [1., 2., 3.], "b": [6., 4., 2.]})
    figure = viz.plot_correlation(frame)
    np.testing.assert_allclose(np.asarray(figure.data[0].z, dtype=float), [[1, -1], [-1, 1]])


def test_missing_histogram_observations_are_reported():
    frame = pd.DataFrame({"v": [1., None, 3.]})
    with pytest.warns(UserWarning):
        figure = viz.plot_histogram(frame, "v")
    assert list(figure.data[0].x) == [1., 3.]


@pytest.mark.parametrize("bad", [0, -1, True, 2.5])
def test_invalid_bin_counts(bad):
    with pytest.raises(ValidationError):
        viz.plot_histogram(pd.DataFrame({"v": [1., 2.]}), "v", bins=bad)


@pytest.mark.parametrize("dates", [["nonsense"], [None], [12345]])
def test_invalid_dates(dates):
    with pytest.raises(ValidationError):
        viz.plot_timeseries(pd.DataFrame({"d": dates, "v": [1.]}), "d", "v")


@pytest.mark.parametrize("values", [[np.inf], ["text"], [None]])
def test_unusable_measurements(values):
    with pytest.raises(ValidationError):
        viz.plot_line(pd.DataFrame({"x": [1], "v": values}), "x", "v")


def test_missing_optional_plotly_has_actionable_exception(monkeypatch):
    original_import = builtins.__import__

    def without_plotly(name, *args, **kwargs):
        if name == "plotly" or name.startswith("plotly."):
            raise ImportError("Unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_plotly)
    with pytest.raises(OptionalDependencyError):
        viz.plot_line(pd.DataFrame({"x": [1], "y": [2]}), "x", "y")


def test_geographic_points_preserve_longitude_latitude_order():
    pytest.importorskip("matplotlib")
    frame = pd.DataFrame({"longitude": [76., 80.], "latitude": [12., 20.]})
    original = frame.copy(deep=True)
    figure = viz.plot_geographic(frame)
    np.testing.assert_allclose(figure.axes[0].collections[0].get_offsets(), [[76, 12], [80, 20]])
    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("lon,lat", [(181, 10), (10, 91), (np.nan, 10)])
def test_invalid_geographic_coordinates(lon, lat):
    pytest.importorskip("matplotlib")
    with pytest.raises(ValidationError):
        viz.plot_geographic(pd.DataFrame({"longitude": [lon], "latitude": [lat]}))


def test_geographic_reprojects_without_mutating_input():
    gpd = pytest.importorskip("geopandas")
    pytest.importorskip("matplotlib")
    frame = gpd.GeoDataFrame({"v": [3.]}, geometry=gpd.points_from_xy([77.], [13.]),
                             crs="EPSG:4326").to_crs(3857)
    original = frame.copy(deep=True)
    figure = viz.plot_geographic(frame, value="v")
    np.testing.assert_allclose(figure.axes[0].collections[0].get_offsets(), [[77, 13]])
    pd.testing.assert_frame_equal(frame, original)
    with pytest.raises(ValidationError):
        viz.plot_geographic(frame.set_crs(None, allow_override=True))


def test_geographic_renders_all_supported_geometry_families():
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import (
        LineString,
        MultiLineString,
        MultiPoint,
        MultiPolygon,
        Point,
        Polygon,
    )

    triangle = Polygon([(77, 13), (78, 13), (77, 14)])
    geometries = [
        Point(77, 13), MultiPoint([(77, 13), (78, 13)]),
        LineString([(77, 13), (78, 14)]),
        MultiLineString([[(77, 13), (78, 14)], [(79, 14), (80, 15)]]),
        triangle, MultiPolygon([triangle, Polygon([(79, 13), (80, 13), (79, 14)])]),
    ]
    for geometry in geometries:
        figure = viz.plot_geographic(gpd.GeoDataFrame(
            geometry=[geometry], crs="EPSG:4326",
        ))
        assert figure.axes[0].collections, type(geometry).__name__
        assert figure.nielytics_metadata["geometry_crs"] == "EPSG:4326"
