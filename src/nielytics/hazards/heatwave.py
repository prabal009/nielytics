"""Daily extreme-heat indicators, not official heatwave classifications."""
from __future__ import annotations

from math import isfinite

import pandas as pd

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._common import daily, metadata, period, positive_int, result, spells, threshold, warnings_for
from ._coordinates import location

_CAVEAT = "Temperature threshold exceedance is not an official heatwave declaration."


class HeatwaveAnalyzer:
    """Analyze daily maximum temperature in explicitly supplied degrees Celsius."""

    def __init__(self, data: pd.DataFrame, *, date_column: str = "date",
                 temperature_column: str = "tmax", unit: str,
                 latitude: float | None = None, longitude: float | None = None) -> None:
        if unit != "C":
            raise ValidationError("temperature unit must be 'C' (degrees Celsius)")
        self.date_column, self.temperature_column = date_column, temperature_column
        self._data = daily(data, date_column, {temperature_column: (None, None)})
        self.location = location(latitude, longitude)

    def extreme_heat_days(self, *, threshold_c: float) -> AnalysisResult:
        """Count observed days whose daily maximum is at least ``threshold_c``."""
        cutoff = threshold(threshold_c, "threshold_c")
        records = self._data[self._data[self.temperature_column] >= cutoff]
        days = records[self.date_column].dt.date.astype(str).tolist()
        return result("extreme_heat_days", {"count": len(days), "dates": days},
                      metadata(self._data, self.date_column, {"temperature": "C"},
                               threshold_c=cutoff, location=self.location),
                      warnings_for(self._data, self.date_column, (self.temperature_column,)), _CAVEAT)

    def heat_spell_duration(self, *, threshold_c: float, minimum_days: int = 3) -> AnalysisResult:
        """Find heat-like episodes; gaps and missing temperatures terminate spells."""
        cutoff = threshold(threshold_c, "threshold_c")
        days = positive_int(minimum_days, "minimum_days")
        episodes = spells(self._data, self.date_column, self.temperature_column,
                          cutoff, above=True, minimum_days=days)
        return result("heat_spell_duration", {"episodes": episodes, "count": len(episodes)},
                      metadata(self._data, self.date_column, {"temperature": "C"},
                               threshold_c=cutoff, minimum_days=days, location=self.location),
                      warnings_for(self._data, self.date_column, (self.temperature_column,)), _CAVEAT)

    def temperature_anomaly(self, *, baseline_start: str | None = None,
                            baseline_end: str | None = None, start: str | None = None,
                            end: str | None = None) -> AnalysisResult:
        """Compare observed maxima with the explicitly selected baseline mean.

        This is an unadjusted mean-temperature difference, not a day-of-year
        climatological anomaly; supply a representative baseline for inference.
        """
        if baseline_start is None or baseline_end is None:
            raise ValidationError("explicit baseline_start and baseline_end are required")
        baseline = period(self._data, self.date_column, baseline_start, baseline_end)
        if baseline.empty or baseline[self.temperature_column].notna().sum() < 2:
            raise ValidationError("baseline requires at least two observed temperatures")
        if start is None or end is None:
            raise ValidationError("explicit comparison start and end are required")
        observed = period(self._data, self.date_column, start, end)
        if observed.empty or not observed[self.temperature_column].notna().any():
            raise ValidationError("comparison period requires observed temperatures")
        reference = float(baseline[self.temperature_column].mean())
        average = float(observed[self.temperature_column].mean())
        anomaly = average - reference
        if not all(isfinite(value) for value in (reference, average, anomaly)):
            raise ValidationError("temperature anomaly exceeds finite numeric range")
        meta = metadata(observed, self.date_column, {"temperature": "C", "anomaly": "C"},
                        baseline_period={"start": baseline_start, "end": baseline_end},
                        method="difference of observed period means; no seasonal adjustment",
                        location=self.location)
        warning = "Unadjusted baseline mean may not represent seasonal temperature climatology."
        return result("temperature_anomaly", {"baseline_mean_c": reference,
                       "observed_mean_c": average, "anomaly_c": anomaly,
                       "observed_days": int(observed[self.temperature_column].count())},
                      meta, [warning, *warnings_for(self._data, self.date_column,
                                                    (self.temperature_column,))], _CAVEAT)

    def imd_heatwave_classification(
        self,
        normal_tmax: float | None = None,
        terrain: str = "plains",
    ) -> AnalysisResult:
        """Classify days according to official India Meteorological Department (IMD) heatwave criteria.

        Supports terrains: 'plains', 'hilly', and 'coastal'.
        Evaluates departures from normal when `normal_tmax` is provided, as well
        as absolute maximum temperature criteria.
        """
        if terrain not in ("plains", "hilly", "coastal"):
            raise ValidationError("terrain must be 'plains', 'hilly', or 'coastal'.")
        if normal_tmax is not None and (normal_tmax < -20.0 or normal_tmax > 60.0):
            raise ValidationError("normal_tmax must be a realistic temperature in degrees Celsius.")

        classified_days: list[dict[str, Any]] = []
        counts = {"no_heatwave": 0, "heatwave": 0, "severe_heatwave": 0}

        for _, row in self._data.iterrows():
            val = row[self.temperature_column]
            d_str = row[self.date_column].strftime("%Y-%m-%d")
            if pd.isna(val):
                continue
            tmax = float(val)
            classification = "no_heatwave"

            if terrain == "plains":
                # Absolute thresholds
                if tmax >= 47.0:
                    classification = "severe_heatwave"
                elif tmax >= 45.0:
                    classification = "heatwave"
                elif normal_tmax is not None and tmax >= 40.0:
                    dep = tmax - normal_tmax
                    if dep >= 6.5:
                        classification = "severe_heatwave"
                    elif dep >= 4.5:
                        classification = "heatwave"
            elif terrain == "hilly":
                if normal_tmax is not None and tmax >= 30.0:
                    dep = tmax - normal_tmax
                    if dep >= 6.5:
                        classification = "severe_heatwave"
                    elif dep >= 4.5:
                        classification = "heatwave"
                elif tmax >= 35.0:
                    classification = "heatwave"
            else:  # coastal
                if normal_tmax is not None and tmax >= 37.0:
                    dep = tmax - normal_tmax
                    if dep >= 6.5:
                        classification = "severe_heatwave"
                    elif dep >= 4.5:
                        classification = "heatwave"
                elif tmax >= 40.0:
                    classification = "heatwave"

            counts[classification] += 1
            if classification != "no_heatwave":
                classified_days.append({
                    "date": d_str,
                    "tmax": tmax,
                    "classification": classification,
                    "departure": float(round(tmax - normal_tmax, 2)) if normal_tmax is not None else None,
                })

        meta = metadata(
            self._data,
            self.date_column,
            {"temperature": "C"},
            standard="India Meteorological Department (IMD)",
            terrain=terrain,
            normal_tmax=normal_tmax,
            location=self.location,
        )
        warning = "IMD heatwave criteria require at least two stations meeting conditions in a subdivision for official declaration."
        return result(
            "imd_heatwave_classification",
            {
                "total_days": len(self._data),
                "counts": counts,
                "events": classified_days,
            },
            meta,
            [warning, *warnings_for(self._data, self.date_column, (self.temperature_column,))],
            _CAVEAT,
        )

    def percentile_heatwave_indicators(
        self,
        baseline_start: str,
        baseline_end: str,
        percentile: float = 90.0,
        consecutive_days: int = 3,
    ) -> AnalysisResult:
        """Detect heat spells where maximum temperature exceeds a historical baseline percentile."""
        if not (0.0 < percentile < 100.0):
            raise ValidationError("percentile must be between 0 and 100 exclusive.")
        base = period(self._data, self.date_column, baseline_start, baseline_end)
        if len(base) < 10:
            raise ValidationError("baseline requires at least 10 observations for percentile calculation.")
        threshold_c = float(base[self.temperature_column].quantile(percentile / 100.0))
        return self.heat_spell_duration(threshold_c=threshold_c, minimum_days=consecutive_days)

    def historical_heatwave_frequency(self, threshold_c: float = 40.0) -> AnalysisResult:
        """Calculate annual event frequencies and long-term trend of extreme heat days."""
        cutoff = threshold(threshold_c, "threshold_c")
        df = self._data.copy()
        df["year"] = df[self.date_column].dt.year
        annual_counts = df[df[self.temperature_column] >= cutoff].groupby("year").size().to_dict()
        all_years = sorted(df["year"].unique())
        counts_series = [int(annual_counts.get(y, 0)) for y in all_years]

        from nielytics.core.statistics import mann_kendall_test
        trend_res = None
        if len(counts_series) >= 3:
            trend_res = mann_kendall_test(counts_series)

        return result(
            "historical_heatwave_frequency",
            {
                "threshold_c": cutoff,
                "years": all_years,
                "annual_frequencies": dict(zip([str(y) for y in all_years], counts_series)),
                "trend_analysis": trend_res,
            },
            metadata(self._data, self.date_column, {"temperature": "C"}, threshold_c=cutoff, location=self.location),
            warnings_for(self._data, self.date_column, (self.temperature_column,)),
            _CAVEAT,
        )

    def regional_heat_summary(
        self,
        data: pd.DataFrame | None = None,
        state_column: str = "state",
        district_column: str | None = None,
    ) -> AnalysisResult:
        """Aggregate heatwave metrics across Indian States or Districts."""
        from nielytics.geospatial.aggregation import aggregate_hazards_by_region
        source_df = data if data is not None else self._data
        return aggregate_hazards_by_region(
            source_df,
            region_type="state" if district_column is None else "district",
            region_column=state_column if district_column is None else district_column,
            hazard_column="hazard" if "hazard" in source_df.columns else self.temperature_column,
            value_column=self.temperature_column,
            date_column=self.date_column,
        )
