"""Deterministic profiling, null handling, and strict JSON compatibility."""

import json

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from nielytics.core.profiler import column_profile, data_quality_report, profile_dataset
from nielytics.exceptions import ValidationError


def test_profile_has_complete_schema_and_known_values():
    frame = pd.DataFrame({
        "amount": [1.0, 2.0, 2.0, np.nan],
        "label": ["a", "b", "b", None],
    })
    result = profile_dataset(frame)
    assert set(result) == {
        "rows", "columns", "dtypes", "missing", "unique", "duplicate_count",
        "numeric_summary", "categorical_summary", "date_coverage", "memory_bytes", "warnings",
    }
    assert result["rows"] == 4
    assert result["columns"] == 2
    assert result["dtypes"]["amount"] == "float64"
    assert result["missing"]["amount"] == {"count": 1, "percentage": 25.0}
    assert result["unique"] == {"amount": 2, "label": 2}
    assert result["duplicate_count"] == 1
    assert result["numeric_summary"]["amount"]["mean"] == pytest.approx(5 / 3)
    assert result["numeric_summary"]["amount"]["variance"] == pytest.approx(1 / 3)
    assert result["categorical_summary"]["label"] == {
        "count": 3, "unique": 2, "top": "b", "frequency": 2,
    }
    assert result["memory_bytes"] == int(frame.memory_usage(deep=True).sum())
    assert any("duplicate" in warning for warning in result["warnings"])
    assert json.loads(json.dumps(result, allow_nan=False)) == result


def test_date_coverage_is_iso_and_does_not_guess_strings():
    frame = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02", None, "2024-01-01"], utc=True),
        "text_date": ["2024-01-02", None, "2024-01-01"],
    })
    result = profile_dataset(frame)
    assert result["date_coverage"]["date"] == {
        "count": 2,
        "min": "2024-01-01T00:00:00+00:00",
        "max": "2024-01-02T00:00:00+00:00",
    }
    assert "text_date" not in result["date_coverage"]
    assert "text_date" in result["categorical_summary"]
    json.dumps(result, allow_nan=False)


def test_empty_frame_and_empty_typed_columns():
    empty = profile_dataset(pd.DataFrame())
    assert empty["rows"] == empty["columns"] == 0
    assert empty["missing"] == {}
    assert empty["duplicate_count"] == 0
    assert empty["warnings"]
    json.dumps(empty, allow_nan=False)
    typed = pd.DataFrame({
        "number": pd.Series(dtype=float),
        "label": pd.Series(dtype="string"),
        "date": pd.Series(dtype="datetime64[ns]"),
    })
    result = profile_dataset(typed)
    assert result["numeric_summary"]["number"]["count"] == 0
    assert result["numeric_summary"]["number"]["mean"] is None
    assert result["missing"]["number"] == {"count": 0, "percentage": 0.0}
    assert result["categorical_summary"]["label"]["top"] is None
    assert result["date_coverage"]["date"] == {"count": 0, "min": None, "max": None}
    json.dumps(result, allow_nan=False)


def test_all_null_nullable_columns_and_constants():
    frame = pd.DataFrame({
        "number": pd.Series([pd.NA, pd.NA], dtype="Float64"),
        "integer": pd.Series([pd.NA, pd.NA], dtype="Int64"),
        "label": pd.Series([pd.NA, pd.NA], dtype="string"),
        "date": pd.to_datetime([None, None]),
        "constant": [7, 7],
    })
    result = profile_dataset(frame)
    for column in ("number", "integer"):
        assert result["numeric_summary"][column]["count"] == 0
        assert result["numeric_summary"][column]["mean"] is None
        assert result["unique"][column] == 0
        assert result["missing"][column]["percentage"] == 100
    assert result["date_coverage"]["date"]["min"] is None
    assert result["categorical_summary"]["label"]["frequency"] == 0
    assert result["numeric_summary"]["constant"]["variance"] == 0
    assert any("only missing" in warning for warning in result["warnings"])
    assert any("one distinct" in warning for warning in result["warnings"])
    json.dumps(result, allow_nan=False)


def test_nonfinite_values_are_json_null_and_warned_about():
    frame = pd.DataFrame({"number": [1.0, np.inf, -np.inf, np.nan]})
    result = profile_dataset(frame)
    assert result["numeric_summary"]["number"]["min"] is None
    assert result["numeric_summary"]["number"]["max"] is None
    assert result["numeric_summary"]["number"]["mean"] is None
    assert any("non-finite" in warning for warning in result["warnings"])
    json.dumps(result, allow_nan=False)


def test_categorical_unobserved_categories_and_scalar_types():
    frame = pd.DataFrame({
        "category": pd.Categorical([None, None], categories=["unobserved"]),
        "boolean": pd.Series([True, pd.NA], dtype="boolean"),
        "timedelta": pd.to_timedelta(["1 day", "1 day"]),
    })
    result = profile_dataset(frame)
    assert result["categorical_summary"]["category"]["top"] is None
    assert result["categorical_summary"]["category"]["frequency"] == 0
    assert result["categorical_summary"]["boolean"]["top"] is True
    json.dumps(result, allow_nan=False)


def test_single_column_profile_and_validation():
    frame = pd.DataFrame({"x": [1.0, 2.0, np.nan]})
    result = column_profile(frame, "x")
    assert result["name"] == "x"
    assert result["numeric_summary"]["mean"] == 1.5
    assert result["missing"]["count"] == 1
    assert result["categorical_summary"] is None
    assert result["date_coverage"] is None
    json.dumps(result, allow_nan=False)
    with pytest.raises(ValidationError, match="unknown column"):
        column_profile(frame, "missing")
    with pytest.raises(ValidationError):
        column_profile(frame, [])


def test_quality_report_counts_cells_without_mutation():
    frame = pd.DataFrame({"x": [1.0, 1.0, np.nan], "label": ["a", "a", None]})
    original = frame.copy(deep=True)
    quality = data_quality_report(frame)
    assert quality["total_missing"] == 2
    assert quality["missing_percentage"] == pytest.approx(100 / 3)
    assert quality["duplicate_count"] == 1
    assert quality["missing"]["label"]["count"] == 1
    assert quality["warnings"]
    profile_dataset(frame)
    column_profile(frame, "x")
    assert_frame_equal(frame, original)
    json.dumps(quality, allow_nan=False)
    assert data_quality_report(pd.DataFrame())["missing_percentage"] == 0


def test_non_string_labels_and_ambiguous_labels():
    result = profile_dataset(pd.DataFrame({1: [1, 2]}))
    assert result["unique"] == {"1": 2}
    json.dumps(result, allow_nan=False)
    with pytest.raises(ValidationError, match="string representations"):
        profile_dataset(pd.DataFrame([[1, 2]], columns=[1, "1"]))


@pytest.mark.parametrize("function", [profile_dataset, data_quality_report])
def test_invalid_frames_have_predictable_errors(function):
    with pytest.raises(ValidationError):
        function([1, 2])
    with pytest.raises(ValidationError):
        function(pd.DataFrame([[1, 2]], columns=["x", "x"]))
