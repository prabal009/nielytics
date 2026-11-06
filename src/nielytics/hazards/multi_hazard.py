"""Multi-hazard compound analysis and explainable composite risk indicators."""

from __future__ import annotations

from typing import Any

import pandas as pd

from nielytics.exceptions import ValidationError
from nielytics.geospatial.india_names import normalize_state_name
from nielytics.models.schemas import AnalysisResult

_CAVEAT = "Compound hazard indicators and composite scores are exploratory screening proxies, not official civil defense alerts."


class MultiHazardAnalyzer:
    """Analyze compound co-occurring climate hazards and compute explainable composite indicators."""

    @staticmethod
    def compare_heat_and_drought(
        heat_data: pd.DataFrame,
        drought_data: pd.DataFrame,
        region: str | None = None,
        date_column: str = "date",
        temp_col: str = "tmax",
        rain_col: str = "rainfall",
        temp_threshold_c: float = 40.0,
        rain_threshold_mm: float = 1.0,
    ) -> AnalysisResult:
        """Identify compound heat-drought episodes where extreme heat coincides with rainless dry conditions."""
        if temp_col not in heat_data.columns:
            raise ValidationError(f"Temperature column {temp_col!r} not found in heat_data.")
        if rain_col not in drought_data.columns:
            raise ValidationError(f"Rainfall column {rain_col!r} not found in drought_data.")

        h_df = heat_data[[date_column, temp_col]].dropna().copy()
        d_df = drought_data[[date_column, rain_col]].dropna().copy()

        h_df[date_column] = pd.to_datetime(h_df[date_column]).dt.normalize()
        d_df[date_column] = pd.to_datetime(d_df[date_column]).dt.normalize()

        merged = pd.merge(h_df, d_df, on=date_column, how="inner")
        compound_mask = (merged[temp_col] >= temp_threshold_c) & (merged[rain_col] <= rain_threshold_mm)
        compound_events = merged[compound_mask]

        records: list[dict[str, Any]] = []
        for _, row in compound_events.iterrows():
            records.append({
                "date": row[date_column].strftime("%Y-%m-%d"),
                "tmax_c": float(round(float(row[temp_col]), 2)),
                "rainfall_mm": float(round(float(row[rain_col]), 2)),
            })

        return AnalysisResult(
            feature="compound_heat_drought",
            data={
                "region": normalize_state_name(region) if region else None,
                "common_observation_days": len(merged),
                "compound_event_days": len(records),
                "temp_threshold_c": float(temp_threshold_c),
                "rain_threshold_mm": float(rain_threshold_mm),
                "events": records,
            },
            metadata={
                "hazard_pair": ["heatwave", "drought"],
                "units": {"temperature": "C", "rainfall": "mm"},
            },
            warnings=["Compound heat and drought amplify evapotranspiration deficit and wildfire susceptibility."],
        )

    @staticmethod
    def compare_rainfall_and_flood(
        rainfall_data: pd.DataFrame,
        flood_events: pd.DataFrame,
        region: str | None = None,
        rain_date_col: str = "date",
        flood_date_col: str = "date",
        rainfall_col: str = "rainfall",
        antecedent_days: int = 3,
    ) -> AnalysisResult:
        """Correlate documented flood events with preceding multi-day cumulative rainfall."""
        if rainfall_col not in rainfall_data.columns:
            raise ValidationError(f"Rainfall column {rainfall_col!r} not found.")

        r_df = rainfall_data[[rain_date_col, rainfall_col]].dropna().copy()
        r_df[rain_date_col] = pd.to_datetime(r_df[rain_date_col]).dt.normalize()
        r_df = r_df.sort_values(rain_date_col).set_index(rain_date_col)

        f_df = flood_events[[flood_date_col]].dropna().copy()
        f_df[flood_date_col] = pd.to_datetime(f_df[flood_date_col]).dt.normalize()

        correlations: list[dict[str, Any]] = []
        for _, row in f_df.iterrows():
            f_date = row[flood_date_col]
            start_date = f_date - pd.DateOffset(days=antecedent_days)
            prior_rain = r_df.loc[start_date:f_date, rainfall_col]
            tot_rain = float(prior_rain.sum()) if len(prior_rain) > 0 else 0.0

            correlations.append({
                "flood_event_date": f_date.strftime("%Y-%m-%d"),
                "antecedent_window_days": antecedent_days,
                "antecedent_rainfall_sum_mm": float(round(tot_rain, 2)),
                "rainfall_readings_count": len(prior_rain),
            })

        return AnalysisResult(
            feature="rainfall_flood_correlation",
            data={
                "region": normalize_state_name(region) if region else None,
                "total_flood_events_evaluated": len(correlations),
                "correlations": correlations,
            },
            metadata={"antecedent_days": antecedent_days},
            warnings=["Flood events are recorded catalog instances; absence of correlation may reflect missing station readings."],
        )

    @staticmethod
    def compare_rainfall_and_landslides(
        rainfall_data: pd.DataFrame,
        landslide_events: pd.DataFrame,
        region: str | None = None,
        rain_date_col: str = "date",
        landslide_date_col: str = "date",
        rainfall_col: str = "rainfall",
        antecedent_days: int = 3,
    ) -> AnalysisResult:
        """Analyze antecedent rainfall accumulation prior to documented landslide event dates."""
        if rainfall_col not in rainfall_data.columns:
            raise ValidationError(f"Rainfall column {rainfall_col!r} not found.")

        r_df = rainfall_data[[rain_date_col, rainfall_col]].dropna().copy()
        r_df[rain_date_col] = pd.to_datetime(r_df[rain_date_col]).dt.normalize()
        r_df = r_df.sort_values(rain_date_col).set_index(rain_date_col)

        l_df = landslide_events[[landslide_date_col]].dropna().copy()
        l_df[landslide_date_col] = pd.to_datetime(l_df[landslide_date_col]).dt.normalize()

        correlations: list[dict[str, Any]] = []
        for _, row in l_df.iterrows():
            l_date = row[landslide_date_col]
            start_date = l_date - pd.DateOffset(days=antecedent_days)
            prior_rain = r_df.loc[start_date:l_date, rainfall_col]
            tot_rain = float(prior_rain.sum()) if len(prior_rain) > 0 else 0.0

            correlations.append({
                "landslide_event_date": l_date.strftime("%Y-%m-%d"),
                "antecedent_window_days": antecedent_days,
                "antecedent_rainfall_sum_mm": float(round(tot_rain, 2)),
            })

        return AnalysisResult(
            feature="rainfall_landslide_correlation",
            data={
                "region": normalize_state_name(region) if region else None,
                "total_landslide_events_evaluated": len(correlations),
                "correlations": correlations,
            },
            metadata={"antecedent_days": antecedent_days},
            warnings=["Landslide triggers depend on soil saturation, geology, and terrain slope in addition to rainfall."],
        )

    @staticmethod
    def regional_multi_hazard_overlap(
        hazard_datasets: dict[str, pd.DataFrame],
        region_type: str = "state",
        region_column: str = "state",
    ) -> AnalysisResult:
        """Build a multi-hazard exposure matrix identifying regions exposed to multiple hazard types."""
        if not hazard_datasets:
            raise ValidationError("hazard_datasets dictionary cannot be empty.")

        region_hazards: dict[str, set[str]] = {}
        for hazard_name, df in hazard_datasets.items():
            if region_column in df.columns:
                for reg in df[region_column].dropna():
                    norm_reg = normalize_state_name(str(reg)) if region_type == "state" else str(reg).strip().title()
                    if norm_reg:
                        if norm_reg not in region_hazards:
                            region_hazards[norm_reg] = set()
                        region_hazards[norm_reg].add(str(hazard_name))

        matrix: dict[str, Any] = {}
        for reg, hazards in sorted(region_hazards.items()):
            matrix[reg] = {
                "hazard_count": len(hazards),
                "hazards": sorted(hazards),
                "multi_hazard_exposed": len(hazards) > 1,
            }

        return AnalysisResult(
            feature="regional_multi_hazard_overlap",
            data={
                "total_regions": len(matrix),
                "matrix": matrix,
            },
            metadata={"evaluated_hazards": sorted(hazard_datasets.keys())},
        )

    @staticmethod
    def composite_hazard_indicator(
        hazard_metrics: dict[str, float],
        weights: dict[str, float] | None = None,
        normalization: str = "min_max",
    ) -> AnalysisResult:
        """Compute an explainable, transparent composite hazard indicator score.

        Returns raw input values, normalized metrics, explicit mathematical formula,
        weights used, and the composite score scaled to [0, 100].
        """
        if not hazard_metrics:
            raise ValidationError("hazard_metrics dictionary cannot be empty.")

        keys = list(hazard_metrics.keys())
        # Default equal weighting
        if weights is None:
            w_dict = {k: 1.0 / len(keys) for k in keys}
        else:
            total_w = sum(weights.values())
            if total_w <= 0:
                raise ValidationError("Sum of weights must be positive.")
            w_dict = {k: float(weights.get(k, 0.0)) / total_w for k in keys}

        # Normalize metrics to [0, 1]
        vals = [float(hazard_metrics[k]) for k in keys]
        min_v, max_v = min(vals), max(vals)
        normalized: dict[str, float] = {}

        for k in keys:
            v = float(hazard_metrics[k])
            if max_v > min_v:
                norm_v = (v - min_v) / (max_v - min_v)
            else:
                norm_v = 0.5  # middle value when all metrics equal
            normalized[k] = float(round(norm_v, 4))

        # Weighted sum: sum(w_i * norm_i) * 100
        composite_score = sum(w_dict[k] * normalized[k] for k in keys) * 100.0

        formula = "Composite Score = 100 * SUM(weight_i * normalized_metric_i)"
        warning = (
            "Composite hazard indicator is an exploratory multi-criteria screening proxy, "
            "not an actuarial, financial, or civil defense risk certification."
        )

        return AnalysisResult(
            feature="composite_hazard_indicator",
            data={
                "composite_score": float(round(composite_score, 2)),
                "raw_metrics": {k: float(v) for k, v in hazard_metrics.items()},
                "normalized_metrics": normalized,
                "weights": {k: float(round(w, 4)) for k, w in w_dict.items()},
                "normalization_method": normalization,
                "mathematical_formula": formula,
            },
            metadata={"indicator_components": keys},
            warnings=[warning],
        )
