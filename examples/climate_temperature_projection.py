"""Demonstrate long-term climate projections under CMIP6 scenarios and historical trend extrapolation."""

import json
import numpy as np
import pandas as pd
from nielytics import ClimateProjectionEngine


def main() -> None:
    print("=== NIElytics Climate Scenario Projections (CMIP6 & Trend) ===")

    engine = ClimateProjectionEngine()

    # 1. Mode A: Robust historical trend extrapolation (Theil-Sen slope)
    years = np.arange(2005, 2025)
    # Annual mean maximum temperature with +0.025°C/year warming trend
    annual_tmax = 30.5 + 0.025 * (years - 2005) + np.random.default_rng(42).normal(0, 0.2, len(years))
    dates = [f"{y}-07-01" for y in years]
    df_hist = pd.DataFrame({"date": dates, "tmax": annual_tmax})

    trend_proj = engine.project_trend_extrapolation(
        df_hist,
        date_column="date",
        target_column="tmax",
        target_years=[2030, 2040, 2050],
    )
    print("Mode A: Empirical Historical Trend Extrapolation:")
    print(f" Historical Theil-Sen slope: {trend_proj.data['historical_slope_c_per_year']}°C/year")
    for proj in trend_proj.data["projections"]:
        print(f" - Year {proj['target_year']}: Projected Mean = {proj['projected_annual_mean_c']}°C (Delta: {proj['delta_from_historical_latest_c']:+.2f}°C)")

    # 2. Mode B: Standardized IPCC AR6 CMIP6 Projections for South Asia
    baseline_temp = 31.0  # Regional baseline mean maximum temperature
    cmip_proj = engine.project_cmip6_scenarios(
        baseline_temperature_c=baseline_temp,
        target_years=[2030, 2040, 2050],
        scenarios=["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"],
    )

    print("\nMode B: Standardized IPCC AR6 South Asia CMIP6 Projections:")
    for sc_name, sc_data in cmip_proj.data["scenarios"].items():
        print(f"\nScenario: {sc_name} ({sc_data['description']})")
        for p in sc_data["projections"]:
            print(
                f" - {p['target_year']}: Warming Anomaly = +{p['warming_anomaly_mid_c']}°C "
                f"[Range: +{p['warming_anomaly_range_c'][0]}°C to +{p['warming_anomaly_range_c'][1]}°C] "
                f"-> Absolute Projected Temp = {p['projected_absolute_temperature_c']}°C"
            )


if __name__ == "__main__":
    main()
