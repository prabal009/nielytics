"""Unified high-level orchestration facade for NIElytics climate analytics workflows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

from nielytics.exceptions import ValidationError
from nielytics.geospatial.aggregation import aggregate_hazards_by_region, generate_hazard_geojson
from nielytics.geospatial.india_names import normalize_state_name
from nielytics.harmonization import DatasetHarmonizer, HarmonizationSchema
from nielytics.hazards import (
    CycloneAnalyzer,
    DroughtAnalyzer,
    FloodAnalyzer,
    HeatwaveAnalyzer,
    LandslideAnalyzer,
    MultiHazardAnalyzer,
)
from nielytics.insights import InsightEngine
from nielytics.models.schemas import AnalysisResult


class ClimateAnalytics:
    """Unified high-level facade managing ingestion, harmonization, hazard analytics, and insights."""

    def __init__(self, data_directory: str | os.PathLike[str] | None = None, offline: bool = True) -> None:
        self.data_directory = Path(data_directory).expanduser() if data_directory else None
        self.offline = offline
        self._datasets: dict[str, pd.DataFrame] = {}
        self._harmonized_results: dict[str, AnalysisResult] = {}
        self._analysis_history: list[AnalysisResult] = []
        self._insight_engine = InsightEngine()

    def register_dataset(
        self,
        hazard: str,
        data: pd.DataFrame | str | os.PathLike[str],
        schema: HarmonizationSchema | dict[str, Any] | None = None,
        **loader_kwargs: Any,
    ) -> AnalysisResult:
        """Harmonize and register a dataset for a specific hazard category."""
        target_hazard = str(hazard).lower().strip()
        if isinstance(schema, dict):
            s_obj = HarmonizationSchema(hazard=target_hazard, **schema)
        elif isinstance(schema, HarmonizationSchema):
            s_obj = schema
            s_obj.hazard = target_hazard
        else:
            s_obj = HarmonizationSchema(hazard=target_hazard)

        harmonizer = DatasetHarmonizer(s_obj)
        harm_res = harmonizer.harmonize(data, **loader_kwargs)
        df_harm = DatasetHarmonizer.to_dataframe(harm_res)

        self._datasets[target_hazard] = df_harm
        self._harmonized_results[target_hazard] = harm_res
        return harm_res

    def analyze(
        self,
        hazard: str,
        region: str | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        method: str | None = None,
        **kwargs: Any,
    ) -> AnalysisResult:
        """Execute hazard analysis over a registered dataset with optional regional/temporal filtering."""
        target_hazard = str(hazard).lower().strip()
        if target_hazard not in self._datasets:
            raise ValidationError(f"No dataset registered for hazard: {hazard!r}. Call register_dataset first.")

        df = self._datasets[target_hazard].copy()

        # Regional filter
        if region:
            norm_region = normalize_state_name(region)
            if norm_region and "state" in df.columns:
                df = df[df["state"] == norm_region]
            elif "district" in df.columns:
                df = df[df["district"].str.lower() == region.lower().strip()]

        # Temporal filter
        if "date" in df.columns:
            df["_year"] = pd.to_datetime(df["date"]).dt.year
            if start_year is not None:
                df = df[df["_year"] >= start_year]
            if end_year is not None:
                df = df[df["_year"] <= end_year]
            df = df.drop(columns=["_year"])

        if len(df) == 0:
            raise ValidationError(f"No observations remain after filtering for region={region!r}, years=[{start_year}, {end_year}].")

        # Route to analyzer
        res: AnalysisResult
        if target_hazard == "heatwave":
            analyzer = HeatwaveAnalyzer(df, date_column="date", temperature_column="value", unit="C")
            if method == "percentile":
                res = analyzer.percentile_heatwave_indicators(
                    baseline_start=kwargs.get("baseline_start", "2000-01-01"),
                    baseline_end=kwargs.get("baseline_end", "2010-12-31"),
                )
            elif method == "frequency":
                res = analyzer.historical_heatwave_frequency(threshold_c=kwargs.get("threshold_c", 40.0))
            else:
                res = analyzer.imd_heatwave_classification(
                    normal_tmax=kwargs.get("normal_tmax", 40.0),
                    terrain=kwargs.get("terrain", "plains"),
                )
        elif target_hazard == "flood":
            analyzer_f = FloodAnalyzer(df, date_column="date", rainfall_column="value", unit="mm")
            if method == "accumulation":
                res = analyzer_f.multi_day_accumulation(windows=kwargs.get("windows", [2, 3, 5, 7]))
            elif method == "cumulative":
                res = analyzer_f.cumulative_rainfall(window_days=kwargs.get("window_days", 3))
            else:
                res = analyzer_f.imd_rainfall_classification()
        elif target_hazard == "drought":
            analyzer_d = DroughtAnalyzer(df, date_column="date", rainfall_column="value", unit="mm")
            if method == "deficit":
                res = analyzer_d.rainfall_deficit(
                    baseline_start=kwargs.get("baseline_start"),
                    baseline_end=kwargs.get("baseline_end"),
                    start=kwargs.get("start"),
                    end=kwargs.get("end"),
                )
            elif method == "monsoon":
                res = analyzer_d.seasonal_rainfall_anomaly(monsoon_months=kwargs.get("monsoon_months", [6, 7, 8, 9]))
            else:
                res = analyzer_d.standardized_precipitation_index(scale_months=kwargs.get("scale_months", 3))
        elif target_hazard == "landslide":
            if "slope" not in df.columns:
                df["slope"] = kwargs.get("default_slope", 25.0)
            analyzer_l = LandslideAnalyzer(df, date_column="date", rainfall_column="value", slope_column="slope", rainfall_unit="mm", slope_unit="degrees")
            if method == "antecedent":
                res = analyzer_l.antecedent_rainfall(window_days=kwargs.get("window_days", 3))
            else:
                res = analyzer_l.rainfall_trigger_indicator(
                    antecedent_window_days=kwargs.get("antecedent_window_days", 3),
                    antecedent_threshold_mm=kwargs.get("antecedent_threshold_mm", 100.0),
                    trigger_rainfall_threshold_mm=kwargs.get("trigger_rainfall_threshold_mm", 50.0),
                )
        elif target_hazard == "cyclone":
            required_cols = {"storm_id", "time", "latitude", "longitude", "wind", "pressure"}
            for rc in required_cols:
                if rc not in df.columns:
                    raise ValidationError(f"Cyclone track data requires column {rc!r}.")
            analyzer_c = CycloneAnalyzer(
                df,
                storm_id_column="storm_id",
                time_column="time",
                latitude_column="latitude",
                longitude_column="longitude",
                wind_column="wind",
                pressure_column="pressure",
                wind_unit="km/h",
                pressure_unit="hPa",
            )
            if method == "proximity":
                res = analyzer_c.proximity(
                    latitude=kwargs.get("latitude", 20.0),
                    longitude=kwargs.get("longitude", 85.0),
                    radius_km=kwargs.get("radius_km", 200.0),
                )
            elif method == "landfall":
                res = analyzer_c.landfall_analysis(proximity_threshold_km=kwargs.get("proximity_threshold_km", 50.0))
            else:
                res = analyzer_c.imd_cyclone_classification()
        else:
            raise ValidationError(f"Unsupported hazard type: {hazard!r}")

        self._analysis_history.append(res)
        return res

    def compare_hazards(self, hazards: list[str] | None = None, region: str | None = None) -> AnalysisResult:
        """Execute multi-hazard overlap and co-occurrence analysis across registered datasets."""
        selected_hazards = hazards or list(self._datasets.keys())
        sub_datasets = {h: self._datasets[h] for h in selected_hazards if h in self._datasets}
        res = MultiHazardAnalyzer.regional_multi_hazard_overlap(sub_datasets, region_type="state")
        self._analysis_history.append(res)
        return res

    def get_insights(self) -> AnalysisResult:
        """Derive deterministic insights from all executed analyses in this session."""
        return self._insight_engine.generate_insights(self._analysis_history)

    def get_geospatial_summary(self, hazard: str | None = None, region_type: str = "state") -> AnalysisResult:
        """Aggregate registered hazard observations by Indian administrative region."""
        if hazard:
            if hazard not in self._datasets:
                raise ValidationError(f"Dataset for {hazard!r} not registered.")
            df = self._datasets[hazard]
        else:
            dfs = list(self._datasets.values())
            if not dfs:
                raise ValidationError("No datasets registered.")
            df = pd.concat(dfs, ignore_index=True)

        return aggregate_hazards_by_region(df, region_type=region_type)

    def to_geojson(self, hazard: str | None = None) -> dict[str, Any]:
        """Export registered hazard locations to RFC 7946 GeoJSON FeatureCollection."""
        if hazard:
            if hazard not in self._datasets:
                raise ValidationError(f"Dataset for {hazard!r} not registered.")
            df = self._datasets[hazard]
        else:
            dfs = list(self._datasets.values())
            if not dfs:
                raise ValidationError("No datasets registered.")
            df = pd.concat(dfs, ignore_index=True)

        return generate_hazard_geojson(df)
