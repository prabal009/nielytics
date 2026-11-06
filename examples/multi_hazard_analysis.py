"""Demonstrate compound climate hazard co-occurrence and explainable composite indicators."""

import json
import pandas as pd
from nielytics import MultiHazardAnalyzer


def main() -> None:
    print("=== NIElytics Multi-Hazard Analytics ===")

    dates = pd.date_range("2023-05-01", periods=10, freq="D").strftime("%Y-%m-%d")
    heat_df = pd.DataFrame({
        "date": dates,
        "tmax": [38.0, 42.0, 44.5, 45.0, 46.2, 41.0, 39.0, 43.0, 45.5, 37.0],
    })
    drought_df = pd.DataFrame({
        "date": dates,
        "rainfall": [0.0, 0.0, 0.0, 0.0, 0.2, 5.0, 20.0, 0.0, 0.0, 2.0],
    })

    # 1. Compound heat-drought episodes
    compound_res = MultiHazardAnalyzer.compare_heat_and_drought(
        heat_df,
        drought_df,
        region="Rajasthan",
        temp_threshold_c=42.0,
        rain_threshold_mm=0.5,
    )
    print(f"Compound heat-drought events identified: {compound_res.data['compound_event_days']} days.")
    for ev in compound_res.data["events"]:
        print(f" - {ev['date']}: Max Temp {ev['tmax_c']}°C, Rainfall {ev['rainfall_mm']} mm")

    # 2. Regional multi-hazard exposure overlap matrix
    heat_catalog = pd.DataFrame({"state": ["Rajasthan", "Punjab", "Delhi"]})
    flood_catalog = pd.DataFrame({"state": ["Odisha", "Assam", "Kerala"]})
    cyclone_catalog = pd.DataFrame({"state": ["Odisha", "West Bengal", "Andhra Pradesh"]})

    matrix_res = MultiHazardAnalyzer.regional_multi_hazard_overlap(
        {"heatwave": heat_catalog, "flood": flood_catalog, "cyclone": cyclone_catalog},
        region_type="state",
    )
    print("\nMulti-Hazard Regional Matrix:")
    for state, info in matrix_res.data["matrix"].items():
        if info["multi_hazard_exposed"]:
            print(f" [!] {state}: {info['hazard_count']} hazards ({info['hazards']})")

    # 3. Transparent Composite Risk Indicator
    composite = MultiHazardAnalyzer.composite_hazard_indicator(
        hazard_metrics={"extreme_heat_days": 18.0, "spi_deficit": 1.9, "flood_accumulation_mm": 280.0},
        weights={"extreme_heat_days": 0.35, "spi_deficit": 0.35, "flood_accumulation_mm": 0.30},
    )
    print("\nExplainable Composite Hazard Score:")
    print(f" Score: {composite.data['composite_score']} / 100")
    print(f" Formula: {composite.data['mathematical_formula']}")
    print(f" Normalized Metrics: {composite.data['normalized_metrics']}")


if __name__ == "__main__":
    main()
