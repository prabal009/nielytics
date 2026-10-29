"""Offline synthetic data: not real climate observations."""
import json

import pandas as pd

from nielytics import Dataset


def main() -> None:
    original = Dataset(pd.DataFrame({
        "date": ["2025-01-01", "2025-01-02", "2025-01-02", "2025-01-03"],
        "value": [10.0, 20.0, 20.0, None],
    }))
    cleaned = (original.parse_dates("date")
               .remove_duplicates()
               .fill_missing(columns=["value"], strategy="mean"))
    assert original.frame.shape[0] == 4
    assert cleaned.frame["value"].tolist() == [10.0, 20.0, 15.0]
    payload = {
        "synthetic": True,
        "profile": cleaned.profile(),
        "records": cleaned.to_records(),
        "cleaning_history": cleaned.history,
    }
    print(json.dumps(payload, allow_nan=False, indent=2))
    print(cleaned.summary().to_string())


if __name__ == "__main__":
    main()
