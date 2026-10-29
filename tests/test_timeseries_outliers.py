"""Consumer-visible time-series and outlier behavior on synthetic measurements."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from nielytics.core.outliers import detect_outliers, outlier_report
from nielytics.core.timeseries import calculate_anomalies, missing_dates, rolling_mean
from nielytics.exceptions import ValidationError


def test_rolling_observations_and_missing_calendar_dates():
    frame = pd.DataFrame({"day": ["2025-01-04", "2025-01-01", "2025-01-02"],
                          "v": [4., 1., None]})
    original = frame.copy(deep=True)
    result = rolling_mean(frame, "day", "v", window=2, min_periods=1)
    assert result["value"].iloc[0] == 1
    assert result["rolling_mean"].iloc[1] == 1
    assert result["rolling_mean"].iloc[2] == 4
    assert missing_dates(frame, "day", "v") == ["2025-01-03"]
    assert_frame_equal(frame, original)


def test_monthly_anomalies_have_explicit_baseline_and_missing_month():
    frame = pd.DataFrame({"day": ["2024-01-01", "2024-01-02", "2025-01-01",
                                   "2025-02-01"], "v": [10., 14., 20., 8.]})
    result = calculate_anomalies(frame, "day", "v", baseline_start="2024-01-01",
                                 baseline_end="2024-12-31")
    assert result["baseline"].iloc[2] == 12
    assert result["anomaly"].iloc[2] == 8
    assert pd.isna(result["anomaly"].iloc[3])
    with pytest.raises(ValidationError, match="baseline"):
        calculate_anomalies(frame, "day", "v", baseline_start="2020-01-01",
                            baseline_end="2020-12-31")


def test_duplicate_dates_are_not_silently_counted_twice():
    frame = pd.DataFrame({"day": ["2025-01-01"] * 2, "v": [1, 2]})
    with pytest.raises(ValidationError, match="duplicate"):
        rolling_mean(frame, "day", "v", window=2)


def test_outlier_masks_keep_null_and_original_rows():
    frame = pd.DataFrame({"v": [10., 10., 10., 10., 100., None]}, index=[2, 3, 4, 5, 6, 7])
    before = frame.copy(deep=True)
    assert detect_outliers(frame, "v", method="iqr").tolist() == [False] * 4 + [True, False]
    assert outlier_report(frame, "v")["indices"] == [6]
    assert detect_outliers(frame, "v", method="percentile").iloc[4]
    assert not detect_outliers(frame, "v", method="modified_zscore").any()
    assert_frame_equal(frame, before)
    with pytest.raises(ValidationError):
        detect_outliers(frame, "v", method="percentile", threshold=0.5)
