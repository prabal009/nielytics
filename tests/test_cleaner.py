import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from nielytics.core.cleaner import (
    clean_text,
    convert_types,
    fill_missing,
    missing_report,
    parse_dates,
    remove_duplicates,
    standardize_columns,
)
from nielytics.exceptions import ValidationError


def test_missing_report_including_empty_frame():
    frame = pd.DataFrame({"a": [1, None], "b": [None, None]})
    before = frame.copy(deep=True)
    report = missing_report(frame)
    assert report.loc["a", "missing_count"] == 1
    assert report.loc["a", "missing_percent"] == 50
    assert report.loc["b", "missing_percent"] == 100
    assert_frame_equal(frame, before)
    empty = missing_report(frame.iloc[:0])
    assert (empty == 0).all().all()


@pytest.mark.parametrize("strategy,expected", [("mean", 3.0), ("median", 3.0), ("mode", 1.0), ("constant", 7.0)])
def test_fill_strategies_do_not_mutate(strategy, expected):
    frame = pd.DataFrame({"n": [1.0, np.nan, 5.0], "text": [" a ", None, "b"]})
    before = frame.copy(deep=True)
    result = fill_missing(frame, columns="n", strategy=strategy, value=7)
    assert result.loc[1, "n"] == expected
    assert_frame_equal(frame, before)
    assert result is not frame
    assert result["text"].equals(frame["text"])


@pytest.mark.parametrize("strategy", ["mean", "median", "mode"])
def test_all_null_statistical_fill_is_rejected(strategy):
    with pytest.raises(ValidationError, match="all-null"):
        fill_missing(pd.DataFrame({"a": [np.nan]}), strategy=strategy)


@pytest.mark.parametrize("strategy", ["mean", "median"])
def test_nonnumeric_statistical_fill_is_rejected(strategy):
    with pytest.raises(ValidationError, match="numeric"):
        fill_missing(pd.DataFrame({"a": ["x", None]}), strategy=strategy)


def test_invalid_fill_strategy_and_constant():
    frame = pd.DataFrame({"a": [1, None]})
    with pytest.raises(ValidationError):
        fill_missing(frame, strategy="magic")
    with pytest.raises(ValidationError):
        fill_missing(frame, strategy="constant")
    result = fill_missing(frame, strategy="constant", value=0)
    assert result.loc[1, "a"] == 0


@pytest.mark.parametrize("operation", [
    lambda f: fill_missing(f, columns=["absent"]),
    lambda f: remove_duplicates(f, subset=["absent"]),
    lambda f: convert_types(f, {"absent": "int64"}),
    lambda f: clean_text(f, columns=["absent"]),
    lambda f: parse_dates(f, ["absent"]),
])
def test_missing_columns_are_rejected(operation):
    with pytest.raises(ValidationError, match="not found"):
        operation(pd.DataFrame({"a": [1]}))


def test_duplicate_removal_preserves_indices_and_input():
    frame = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "y", "z"]}, index=[4, 5, 6])
    before = frame.copy(deep=True)
    assert remove_duplicates(frame, subset="a").index.tolist() == [4, 6]
    assert remove_duplicates(frame, subset="a", keep="last").index.tolist() == [5, 6]
    assert remove_duplicates(frame, subset="a", keep=False).index.tolist() == [6]
    assert_frame_equal(frame, before)
    with pytest.raises(ValidationError):
        remove_duplicates(frame, keep="invalid")
    with pytest.raises(ValidationError):
        remove_duplicates(frame, subset=[])


def test_standardization_and_collisions():
    frame = pd.DataFrame({" First Name ": ["A"], "Total ($)": [2]})
    before = frame.copy(deep=True)
    assert standardize_columns(frame).columns.tolist() == ["first_name", "total"]
    assert_frame_equal(frame, before)
    with pytest.raises(ValidationError, match="duplicate"):
        standardize_columns(pd.DataFrame([[1, 2]], columns=["A B", "a-b"]))
    with pytest.raises(ValidationError, match="empty"):
        standardize_columns(pd.DataFrame({"!!!": [1]}))


def test_type_conversion_and_invalid_values():
    frame = pd.DataFrame({"n": ["1", "2"]})
    before = frame.copy(deep=True)
    result = convert_types(frame, {"n": "int64"})
    assert result["n"].tolist() == [1, 2]
    assert_frame_equal(frame, before)
    with pytest.raises(ValidationError):
        convert_types(pd.DataFrame({"n": ["bad"]}), {"n": "int64"})


def test_text_cleaning_preserves_nonstrings_and_missing():
    frame = pd.DataFrame({"text": [" a b ", None, 4], "n": [1, 2, 3]})
    before = frame.copy(deep=True)
    result = clean_text(frame)
    assert result["text"].tolist() == ["a b", None, 4]
    assert_frame_equal(frame, before)
    assert result["n"].equals(frame["n"])


def test_dates_explicit_format_errors_and_no_mutation():
    frame = pd.DataFrame({"Date Name": ["31/12/2025", None]})
    before = frame.copy(deep=True)
    result = parse_dates(frame, "Date Name", format="%d/%m/%Y")
    assert result.loc[0, "Date Name"] == pd.Timestamp("2025-12-31")
    assert pd.isna(result.loc[1, "Date Name"])
    assert_frame_equal(frame, before)
    with pytest.raises(ValidationError):
        parse_dates(pd.DataFrame({"d": ["not a date"]}), ["d"])


@pytest.mark.parametrize("operation", [missing_report, fill_missing, remove_duplicates, standardize_columns, clean_text])
def test_cleaners_reject_nonframes(operation):
    with pytest.raises(ValidationError):
        operation([1, 2])
