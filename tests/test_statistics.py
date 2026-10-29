"""Deterministic examples for the public descriptive statistics API."""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from nielytics.core.statistics import (
    correlation_matrix,
    covariance_matrix,
    frequency_distribution,
    grouped_summary,
    modes,
    quantiles,
    summarize,
)
from nielytics.exceptions import ValidationError


def test_summary_known_values_and_sample_population_ddof():
    frame = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0], "label": list("abcd")})
    result = summarize(frame)
    assert result.index.tolist() == ["value"]
    assert result.columns.tolist() == [
        "count", "mean", "median", "variance", "std", "min", "max",
        "q25", "q75", "skew", "kurtosis",
    ]
    assert result.loc["value"].tolist() == pytest.approx([
        4, 2.5, 2.5, 5 / 3, np.sqrt(5 / 3), 1, 4, 1.75, 3.25, 0, -1.2,
    ])
    assert summarize(frame, ddof=0).loc["value", "variance"] == pytest.approx(1.25)


def test_summary_skips_missing_and_handles_constant_and_nullable():
    frame = pd.DataFrame({
        "partial": [1.0, np.nan, 3.0, np.nan],
        "constant": [5.0] * 4,
        "null": pd.Series([pd.NA] * 4, dtype="Float64"),
    })
    result = summarize(frame)
    assert result.loc["partial", "count"] == 2
    assert result.loc["partial", "mean"] == 2
    assert result.loc["partial", "variance"] == 2
    assert result.loc["constant", "std"] == 0
    assert result.loc["constant", "skew"] == 0
    assert result.loc["null", "count"] == 0
    assert pd.isna(result.loc["null", "mean"])
    assert pd.isna(summarize(pd.DataFrame({"x": [1.0]})).loc["x", "variance"])
    assert pd.isna(summarize(frame, ddof=10).loc["partial", "variance"])


@pytest.mark.parametrize("ddof", [-1, 1.5, True, "1", None])
@pytest.mark.parametrize("function", [summarize, covariance_matrix, grouped_summary])
def test_invalid_ddof_is_predictable(ddof, function):
    frame = pd.DataFrame({"x": [1, 2], "group": ["a", "a"]})
    kwargs = {"by": "group"} if function is grouped_summary else {}
    with pytest.raises(ValidationError, match="ddof"):
        function(frame, ddof=ddof, **kwargs)


@pytest.mark.parametrize("function", [summarize, quantiles])
@pytest.mark.parametrize("columns", [["absent"], ["text"], ["flag"], ["complex"], ["x", "x"]])
def test_numeric_selections_are_validated(function, columns):
    frame = pd.DataFrame({"x": [1], "text": ["a"], "flag": [True], "complex": [1j]})
    with pytest.raises(ValidationError):
        function(frame, columns=columns)


def test_default_numeric_selection_excludes_boolean_and_complex():
    frame = pd.DataFrame({"x": [1, 2], "flag": [True, False], "complex": [1j, 2j]})
    assert summarize(frame).index.tolist() == ["x"]
    assert correlation_matrix(frame).columns.tolist() == ["x"]
    assert covariance_matrix(frame).columns.tolist() == ["x"]


@pytest.mark.parametrize("method", ["pearson", "spearman", "kendall"])
def test_correlations_known_values_and_pairwise_missing(method):
    frame = pd.DataFrame({
        "x": [1.0, 2.0, 3.0, np.nan],
        "y": [2.0, 4.0, 6.0, 8.0],
        "reverse": [3.0, 2.0, 1.0, np.nan],
    })
    result = correlation_matrix(frame, method=method)
    assert result.loc["x", "y"] == pytest.approx(1)
    assert result.loc["x", "reverse"] == pytest.approx(-1)


def test_pearson_constant_is_undefined_and_invalid_method_rejected():
    frame = pd.DataFrame({"x": [1, 2, 3], "constant": [3, 3, 3]})
    assert pd.isna(correlation_matrix(frame).loc["x", "constant"])
    with pytest.raises(ValidationError, match="method"):
        correlation_matrix(frame, method="unsupported")


@pytest.mark.parametrize("ddof, expected", [(0, 2.0), (1, 4.0)])
def test_covariance_honors_ddof_for_pairwise_missing(ddof, expected):
    frame = pd.DataFrame({"x": [1.0, 3.0, np.nan], "y": [2.0, 6.0, 10.0]})
    result = covariance_matrix(frame, ddof=ddof)
    assert result.loc["x", "y"] == pytest.approx(expected)
    assert result.loc["y", "x"] == pytest.approx(expected)
    assert result.loc["y", "y"] == pytest.approx(32 / (3 - ddof))
    assert pd.isna(covariance_matrix(frame, ddof=2).loc["x", "y"])


def test_grouped_summary_includes_missing_groups_and_excludes_group_columns():
    frame = pd.DataFrame({"group": [1.0, 1.0, 2.0, np.nan], "x": [1.0, 3.0, 8.0, 10.0]})
    result = grouped_summary(frame, "group")
    assert result.index.names == ["group", "column"]
    assert result.index.get_level_values("column").tolist() == ["x", "x", "x"]
    assert result.loc[(1.0, "x"), "mean"] == 2
    assert result.loc[(1.0, "x"), "variance"] == 2
    assert result[result.index.get_level_values("group").isna()]["mean"].iloc[0] == 10


def test_grouped_summary_multiple_keys_and_explicit_columns():
    frame = pd.DataFrame({"a": ["u", "u", "v"], "b": [1, 1, 2], "x": [2, 4, 8]})
    result = grouped_summary(frame, ["a", "b"], columns=["x"], ddof=0)
    assert result.index.names == ["a", "b", "column"]
    assert result.loc[("u", 1, "x"), "variance"] == 1
    for by in ([], None, "missing"):
        with pytest.raises(ValidationError):
            grouped_summary(frame, by)
    with pytest.raises(ValidationError):
        grouped_summary(frame, "a", columns=["a"])


def test_frequency_distribution_counts_missing_and_denominators():
    frame = pd.DataFrame({"label": ["a", "a", "b", None]})
    result = frequency_distribution(frame, "label")
    assert result["count"].sum() == 4
    assert result.loc["a", "count"] == 2
    assert result.loc["a", "proportion"] == 0.5
    assert result.loc[result.index.isna(), "count"].iloc[0] == 1
    dropped = frequency_distribution(frame, "label", dropna=True)
    assert dropped.loc["a", "proportion"] == pytest.approx(2 / 3)
    with pytest.raises(ValidationError):
        frequency_distribution(frame, "missing")


def test_quantiles_order_scalar_and_skipping_missing():
    frame = pd.DataFrame({"x": [1.0, 2.0, np.nan, 3.0, 4.0], "text": list("abcde")})
    result = quantiles(frame, q=[0.75, 0.25, 0.5])
    assert result.index.tolist() == [0.75, 0.25, 0.5]
    assert result["x"].tolist() == [3.25, 1.75, 2.5]
    assert quantiles(frame, q=0.5).loc[0.5, "x"] == 2.5


@pytest.mark.parametrize("q", [[-0.1], [1.1], [np.nan], [np.inf], [True], ["0.5"], None])
def test_quantiles_reject_invalid_probabilities(q):
    with pytest.raises(ValidationError):
        quantiles(pd.DataFrame({"x": [1, 2]}), q=q)


def test_modes_preserves_ties_and_supports_categorical_columns():
    frame = pd.DataFrame({"x": [1.0, 1.0, 2.0, 2.0, np.nan], "label": ["a", "a", "b", None, None]})
    result = modes(frame)
    assert result["x"].tolist() == [1.0, 2.0]
    assert result.loc[0, "label"] == "a"
    assert pd.isna(result.loc[1, "label"])
    assert modes(frame, columns=["label"]).columns.tolist() == ["label"]
    with pytest.raises(ValidationError):
        modes(frame, columns=["missing"])


def test_empty_frames_and_all_null_statistics():
    empty = pd.DataFrame({"x": pd.Series(dtype=float), "group": pd.Series(dtype=str)})
    assert summarize(empty).loc["x", "count"] == 0
    assert pd.isna(summarize(empty).loc["x", "mean"])
    assert correlation_matrix(empty).isna().all().all()
    assert covariance_matrix(empty).isna().all().all()
    assert grouped_summary(empty, "group").empty
    assert frequency_distribution(empty, "group").empty
    assert quantiles(empty)["x"].isna().all()
    assert modes(empty).empty
    no_columns = pd.DataFrame()
    assert summarize(no_columns).empty
    assert quantiles(no_columns).empty
    assert correlation_matrix(no_columns).empty
    assert covariance_matrix(no_columns).empty
    null = pd.DataFrame({"x": [np.nan, np.nan]})
    assert modes(null).empty
    assert quantiles(null).isna().all().all()


def test_functions_do_not_mutate_input():
    frame = pd.DataFrame({"x": [1.0, np.nan, 3.0], "group": ["a", "a", "b"]})
    original = frame.copy(deep=True)
    summarize(frame)
    correlation_matrix(frame)
    covariance_matrix(frame)
    grouped_summary(frame, "group")
    frequency_distribution(frame, "group")
    quantiles(frame)
    modes(frame)
    assert_frame_equal(frame, original)


@pytest.mark.parametrize("function", [summarize, correlation_matrix, covariance_matrix, quantiles, modes])
def test_frame_validation(function):
    with pytest.raises(ValidationError):
        function([1, 2, 3])
    with pytest.raises(ValidationError):
        function(pd.DataFrame([[1, 2]], columns=["x", "x"]))


def test_frequency_distribution_omits_unobserved_categories():
    frame = pd.DataFrame({"category": pd.Categorical(["a"], categories=["a", "b"])})
    result = frequency_distribution(frame, "category")
    assert result.index.tolist() == ["a"]
    assert result["count"].tolist() == [1]
    assert result["proportion"].tolist() == [1.0]
