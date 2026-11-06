"""Demonstrate backend service consumption of NIElytics with strict JSON serializability."""

import json
import pandas as pd
from nielytics import ClimateAnalytics


def simulate_backend_endpoint(hazard_type: str, state_query: str) -> str:
    """Simulates an API endpoint returning strictly valid JSON HTTP responses."""
    analytics = ClimateAnalytics(offline=True)

    # Ingest synthetic multi-source climate feed
    sample_feed = pd.DataFrame({
        "timestamp": ["2023-05-18", "2023-05-19", "2023-05-20", "2023-05-21"],
        "region": ["Orissa", "Orissa", "Pondicherry", "Pondicherry"],  # Historical names
        "tmax": [45.2, 46.5, 41.0, 39.5],
        "rainfall": [0.0, 0.0, 25.0, 65.0],
    })

    # Register heatwave feed
    analytics.register_dataset(
        hazard="heatwave",
        data=sample_feed,
        schema={
            "date_column": "timestamp",
            "value_column": "tmax",
            "state_column": "region",
            "metric": "tmax",
            "source_unit": "C",
            "target_unit": "C",
        },
    )

    # Register flood/rainfall feed
    analytics.register_dataset(
        hazard="flood",
        data=sample_feed,
        schema={
            "date_column": "timestamp",
            "value_column": "rainfall",
            "state_column": "region",
            "metric": "rainfall",
            "source_unit": "mm",
            "target_unit": "mm",
        },
    )

    # Execute hazard analysis for the queried state (e.g. "orissa")
    analysis_res = analytics.analyze(hazard=hazard_type, region=state_query)

    # Derive deterministic insights across session
    insights_res = analytics.get_insights()

    # Formulate API response payload
    response_payload = {
        "status": "success",
        "query": {"hazard": hazard_type, "region": state_query},
        "analysis": analysis_res.to_dict(),
        "insights": insights_res.to_dict(),
    }

    # Strict JSON serialization guarantee (allow_nan=False)
    serialized_response = json.dumps(response_payload, indent=2, allow_nan=False)
    return serialized_response


def main() -> None:
    print("=== Backend Integration Consumer Demo ===")
    json_response = simulate_backend_endpoint(hazard_type="heatwave", state_query="Orissa")
    print("Serialized API Response (First 800 characters):")
    print(json_response[:800] + "\n...")

    # Validate that consumer can parse response without errors
    parsed = json.loads(json_response)
    assert parsed["status"] == "success"
    print("\nVerified strict JSON response parsing successfully.")


if __name__ == "__main__":
    main()
