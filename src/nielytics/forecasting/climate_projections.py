"""Long-term climate scenario projections (CMIP6 / IPCC AR6) and robust trend extrapolation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from nielytics.core.statistics import theil_sen_slope
from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

_IPCC_AR6_SOUTH_ASIA_ANOMALIES = {
    "SSP1-2.6": {
        "description": "Very low GHG emissions; CO2 net-zero around 2050 (Paris Agreement target)",
        "anomalies_c": {
            2030: {"mid": 1.3, "range": [1.1, 1.6]},
            2040: {"mid": 1.5, "range": [1.3, 1.8]},
            2050: {"mid": 1.6, "range": [1.4, 2.0]},
        },
    },
    "SSP2-4.5": {
        "description": "Intermediate GHG emissions; emissions hover around current levels before declining after 2050",
        "anomalies_c": {
            2030: {"mid": 1.4, "range": [1.2, 1.7]},
            2040: {"mid": 1.9, "range": [1.6, 2.2]},
            2050: {"mid": 2.4, "range": [2.0, 2.8]},
        },
    },
    "SSP5-8.5": {
        "description": "Very high GHG emissions; fossil-fueled development without additional climate policy",
        "anomalies_c": {
            2030: {"mid": 1.6, "range": [1.3, 1.9]},
            2040: {"mid": 2.3, "range": [1.9, 2.7]},
            2050: {"mid": 3.3, "range": [2.7, 3.9]},
        },
    },
}


class ClimateProjectionEngine:
    """Estimates long-term multi-decadal climate warming trajectories across standardized IPCC AR6 CMIP6 scenarios."""

    def __init__(self) -> None:
        pass

    def project_trend_extrapolation(
        self,
        historical_data: pd.DataFrame,
        date_column: str = "date",
        target_column: str = "tmax",
        target_years: list[int] | None = None,
    ) -> AnalysisResult:
        """Mode A: Extrapolate robust historical Theil-Sen warming slope to future target years."""
        years_to_project = sorted(target_years or [2030, 2040, 2050])
        df = historical_data[[date_column, target_column]].dropna().copy()
        df[date_column] = pd.to_datetime(df[date_column])
        df["year"] = df[date_column].dt.year

        annual = df.groupby("year")[target_column].mean().reset_index()
        if len(annual) < 5:
            raise ValidationError("Trend extrapolation requires at least 5 years of historical data.")

        # Compute robust slope per year
        ts = theil_sen_slope(annual, y_col=target_column, x_col="year")
        slope = ts["slope"]
        intercept = ts["intercept"]
        last_year = int(annual["year"].max())
        last_val = float(annual.loc[annual["year"] == last_year, target_column].iloc[0])

        projections: list[dict[str, Any]] = []
        for yr in years_to_project:
            proj_val = intercept + slope * yr
            delta = proj_val - last_val
            projections.append({
                "target_year": int(yr),
                "projected_annual_mean_c": float(round(proj_val, 2)),
                "delta_from_historical_latest_c": float(round(delta, 2)),
            })

        warning = (
            "Empirical linear trend extrapolation assumes past warming rate continues unchanged; "
            "it does not account for non-linear feedback loops, mitigation policies, or emission pathways."
        )

        return AnalysisResult(
            feature="climate_trend_extrapolation",
            data={
                "historical_slope_c_per_year": float(round(slope, 4)),
                "historical_latest_year": last_year,
                "historical_latest_mean_c": float(round(last_val, 2)),
                "projections": projections,
            },
            metadata={
                "method": "Theil-Sen robust slope extrapolation",
                "units": {"temperature": "C"},
            },
            warnings=[warning],
        )

    def project_cmip6_scenarios(
        self,
        baseline_temperature_c: float,
        target_years: list[int] | None = None,
        scenarios: list[str] | None = None,
    ) -> AnalysisResult:
        """Mode B: Project temperature anomaly ranges under standardized IPCC AR6 South Asia CMIP6 scenarios."""
        target_years_list = sorted(target_years or [2030, 2040, 2050])
        scenarios_list = scenarios or ["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]

        for sc in scenarios_list:
            if sc not in _IPCC_AR6_SOUTH_ASIA_ANOMALIES:
                raise ValidationError(f"Unsupported scenario: {sc!r}. Available: {list(_IPCC_AR6_SOUTH_ASIA_ANOMALIES.keys())}")

        results: dict[str, Any] = {}
        for sc in scenarios_list:
            sc_info = _IPCC_AR6_SOUTH_ASIA_ANOMALIES[sc]
            sc_proj = []
            for yr in target_years_list:
                if yr in sc_info["anomalies_c"]:
                    anom = sc_info["anomalies_c"][yr]
                    mid_temp = baseline_temperature_c + anom["mid"]
                    low_temp = baseline_temperature_c + anom["range"][0]
                    high_temp = baseline_temperature_c + anom["range"][1]
                    sc_proj.append({
                        "target_year": int(yr),
                        "warming_anomaly_mid_c": anom["mid"],
                        "warming_anomaly_range_c": anom["range"],
                        "projected_absolute_temperature_c": float(round(mid_temp, 2)),
                        "projected_range_c": [float(round(low_temp, 2)), float(round(high_temp, 2))],
                    })
            results[sc] = {
                "description": sc_info["description"],
                "projections": sc_proj,
            }

        warning = (
            "Climate projections represent multi-decadal ensemble climatological shifts (IPCC AR6 WGI Chapter 11/12), "
            "not deterministic daily weather forecasts."
        )

        return AnalysisResult(
            feature="cmip6_climate_projections",
            data={
                "baseline_temperature_c": float(round(baseline_temperature_c, 2)),
                "scenarios": results,
            },
            metadata={
                "reference_standard": "IPCC Sixth Assessment Report (AR6) - South Asia Regional Climatology",
                "units": {"temperature": "C"},
            },
            warnings=[warning],
        )
