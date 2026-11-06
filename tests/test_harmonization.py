import json
import numpy as np
import pandas as pd
import pytest

from nielytics.harmonization import DatasetHarmonizer, HarmonizationSchema


def test_harmonization_pipeline_and_name_normalization():
    raw_data = pd.DataFrame({
        "timestamp": ["2023-05-01", "2023-05-02", "2023-05-03", "invalid_date", "2023-05-05"],
        "region_name": ["Orissa", "Pondicherry", "Mysore", "Delhi", "Unknown Territory"],
        "city": ["Bhubaneswar", "Pondicherry", "Bangalore", "New Delhi", "Nowhere"],
        "temp_f": [104.0, 95.0, 86.0, 100.0, np.nan],
        "lat": [20.29, 11.94, 12.97, 28.61, 999.0],  # 999 is invalid latitude
        "lon": [85.82, 79.80, 77.59, 77.20, 77.0],
    })

    schema = HarmonizationSchema(
        date_column="timestamp",
        value_column="temp_f",
        state_column="region_name",
        district_column="city",
        latitude_column="lat",
        longitude_column="lon",
        hazard="heatwave",
        metric="tmax",
        source_unit="F",
        target_unit="C",
        source="IMD_SYNTHETIC",
        data_quality="verified",
        observation_type="ground_station",
    )

    harmonizer = DatasetHarmonizer(schema)
    res = harmonizer.harmonize(raw_data)

    assert res.feature == "dataset_harmonization"
    payload = res.to_dict()
    # Verify JSON serializability
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload

    records = res.data["records"]
    assert len(records) == 3  # row 3 (invalid_date) and row 4 (nan temp and invalid lat) dropped

    # Check state normalization
    assert records[0]["state"] == "Odisha"
    assert records[1]["state"] == "Puducherry"
    assert records[2]["state"] == "Karnataka"

    # Check district normalization
    assert records[2]["district"] == "Bengaluru Urban"

    # Check temperature conversion from F to C: 104 F -> 40.0 C, 86 F -> 30.0 C
    assert records[0]["value"] == pytest.approx(40.0, abs=0.1)
    assert records[2]["value"] == pytest.approx(30.0, abs=0.1)

    # Check transformation report
    report = res.data["report"]
    assert report["total_input_rows"] == 5
    assert report["harmonized_rows"] == 3
    assert report["dropped_rows"] == 2
    assert "conversions_applied" in report

    # Check to_dataframe
    df_harmonized = DatasetHarmonizer.to_dataframe(res)
    assert len(df_harmonized) == 3
    assert "hazard" in df_harmonized.columns
