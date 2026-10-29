import json

import numpy as np
import pandas as pd
import pytest

from nielytics import Dataset, ValidationError


def test_cleaning_chain_preserves_input_and_tracks_history():
    source = pd.DataFrame({"value": [1., 1., 3., np.nan]})
    original = Dataset(source)
    source.loc[0, "value"] = 99
    cleaned = original.remove_duplicates().fill_missing(columns=["value"])
    assert original.frame["value"].iloc[0] == 1
    assert cleaned.frame["value"].tolist() == [1., 3., 2.]
    assert original.history == []
    assert [item["operation"] for item in cleaned.history] == [
        "remove_duplicates", "fill_missing"]
    assert cleaned.history[0]["rows_after"] == 3
    history = cleaned.history
    history[0]["parameters"]["keep"] = False
    assert cleaned.history[0]["parameters"]["keep"] == "first"
    frame = cleaned.frame
    frame.loc[0, "value"] = -100
    assert cleaned.frame.loc[0, "value"] == 1


def test_backend_serialization_and_statistics():
    dataset = Dataset(pd.DataFrame({
        "date": ["2025-01-01", "2025-01-02", None],
        "value": [1., 3., np.nan],
    })).parse_dates("date")
    assert dataset.summary().loc["value", "variance"] == 2
    records = dataset.to_records()
    assert records[0]["date"].startswith("2025-01-01T")
    assert records[2] == {"date": None, "value": None}
    json.dumps({"profile": dataset.profile(), "data": records}, allow_nan=False)


def test_failed_clean_does_not_change_dataset():
    dataset = Dataset(pd.DataFrame({"date": ["not a date"]}))
    with pytest.raises(ValidationError):
        dataset.parse_dates("date")
    assert dataset.history == []
    assert dataset.frame.iloc[0, 0] == "not a date"


def test_nonfinite_values_serialize_as_null():
    dataset = Dataset(pd.DataFrame({"value": [np.inf, -np.inf, np.nan]}))
    assert dataset.to_records() == [{"value": None}] * 3
