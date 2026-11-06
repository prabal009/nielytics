"""Demonstrate multi-source climate data ingestion, unit conversion, and state name normalization."""

import json
import pandas as pd
from nielytics import DatasetHarmonizer, HarmonizationSchema


def main() -> None:
    print("=== NIElytics Multi-Source Data Harmonization ===")

    # Raw multi-source sample with historical state names and Fahrenheit temperatures
    raw_incoming = pd.DataFrame({
        "obs_date": ["2023-05-10", "2023-05-11", "2023-05-12", "2023-05-13"],
        "state_name": ["Orissa", "Pondicherry", "Mysore", "Uttaranchal"],
        "district_name": ["Bhubaneswar", "Puducherry", "Bangalore", "Dehradun"],
        "max_temperature_f": [104.0, 98.6, 89.6, 95.0],
        "latitude": [20.29, 11.94, 12.97, 30.31],
        "longitude": [85.82, 79.80, 77.59, 78.03],
    })

    print(f"Raw incoming records: {len(raw_incoming)}")

    schema = HarmonizationSchema(
        date_column="obs_date",
        value_column="max_temperature_f",
        state_column="state_name",
        district_column="district_name",
        latitude_column="latitude",
        longitude_column="longitude",
        hazard="heatwave",
        metric="tmax",
        source_unit="F",
        target_unit="C",  # Automatically converts Fahrenheit to Celsius
        source="SYNTHETIC_STATION_NETWORK",
        data_quality="verified",
    )

    harmonizer = DatasetHarmonizer(schema)
    result = harmonizer.harmonize(raw_incoming)

    # Convert back to clean DataFrame
    df_clean = DatasetHarmonizer.to_dataframe(result)
    print("\nHarmonized DataFrame:")
    print(df_clean[["date", "state", "district", "value", "unit"]].to_string(index=False))

    # Verify state normalization: "Orissa" -> "Odisha", "Mysore" -> "Karnataka"
    assert "Odisha" in df_clean["state"].values
    assert "Karnataka" in df_clean["state"].values
    assert "Bengaluru Urban" in df_clean["district"].values

    print("\nHarmonization Transformation Report:")
    print(json.dumps(result.data["report"], indent=2))


if __name__ == "__main__":
    main()
