"""Rainfall-based flood proxies; recorded floods require independent event data."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._common import (
    complete_rolling,
    daily,
    dates,
    frame,
    metadata,
    positive_int,
    result,
    spells,
    threshold,
    warnings_for,
)
from ._coordinates import location

_CAVEAT = "Rainfall indicators do not confirm flooding or inundation."


class FloodAnalyzer:
    """Analyze daily rainfall in explicitly supplied millimeters."""

    def __init__(self, data: pd.DataFrame, *, date_column: str = "date",
                 rainfall_column: str = "rainfall", unit: str,
                 latitude: float | None = None, longitude: float | None = None) -> None:
        if unit != "mm":
            raise ValidationError("rainfall unit must be 'mm'")
        self.date_column, self.rainfall_column = date_column, rainfall_column
        self._data = daily(data, date_column, {rainfall_column: (0, None)})
        self.location = location(latitude, longitude)

    def extreme_rainfall_days(self, *, threshold_mm: float) -> AnalysisResult:
        """Report observed days with rainfall greater than or equal to threshold."""
        cutoff = threshold(threshold_mm, "threshold_mm", minimum=0)
        if cutoff == 0:
            raise ValidationError("extreme rainfall threshold_mm must exceed zero")
        dates = self._data.loc[self._data[self.rainfall_column] >= cutoff,
                               self.date_column].dt.date.astype(str).tolist()
        return result("extreme_rainfall_days", {"count": len(dates), "dates": dates},
                      metadata(self._data, self.date_column, {"rainfall": "mm"},
                               threshold_mm=cutoff, location=self.location),
                      warnings_for(self._data, self.date_column, (self.rainfall_column,)), _CAVEAT)

    def cumulative_rainfall(self, *, window_days: int) -> AnalysisResult:
        """Complete daily rainfall totals over rolling calendar-day windows.

        Incomplete windows are omitted rather than treating missing as zero.
        """
        window = positive_int(window_days, "window_days")
        windows = complete_rolling(self._data, self.date_column, self.rainfall_column, window)
        return result("cumulative_rainfall", {"windows": windows},
                      metadata(self._data, self.date_column, {"rainfall": "mm"},
                               window_days=window, method="complete daily rolling sums",
                               location=self.location),
                      warnings_for(self._data, self.date_column, (self.rainfall_column,)), _CAVEAT)

    def wet_spell_duration(self, *, threshold_mm: float, minimum_days: int = 2) -> AnalysisResult:
        """Find consecutive days whose observed rain exceeds the inclusive threshold."""
        cutoff = threshold(threshold_mm, "threshold_mm", minimum=0)
        days = positive_int(minimum_days, "minimum_days")
        if cutoff == 0:
            raise ValidationError("wet spell threshold_mm must exceed zero")
        episodes = spells(self._data, self.date_column, self.rainfall_column,
                          cutoff, above=True, minimum_days=days)
        return result("wet_spell_duration", {"episodes": episodes, "count": len(episodes)},
                      metadata(self._data, self.date_column, {"rainfall": "mm"},
                               threshold_mm=cutoff, minimum_days=days, location=self.location),
                      warnings_for(self._data, self.date_column, (self.rainfall_column,)), _CAVEAT)

    def flood_event_frequency(self, events: pd.DataFrame, *,
                              event_date_column: str = "date") -> AnalysisResult:
        """Count caller-supplied independently recorded floods by event year."""
        records = frame(events, (event_date_column,))
        records[event_date_column] = dates(records[event_date_column], daily=True)
        counts = records[event_date_column].dt.year.value_counts().sort_index()
        return result("recorded_flood_frequency",
                      {"years": [{"year": int(year), "events": int(count)}
                                 for year, count in counts.items()]},
                      {"kind": "historical_recorded_events", "units": {"count": "events"},
                       "period": {"start": records[event_date_column].min().date().isoformat(),
                                  "end": records[event_date_column].max().date().isoformat()},
                       "method": "counts of supplied records; not an exhaustive catalog"},
                      [], "Historical flood event records are not live flood warnings.")

    def imd_rainfall_classification(self) -> AnalysisResult:
        """Classify daily rainfall according to official India Meteorological Department (IMD) categories.

        Categories:
        - No Rain: 0.0 mm
        - Very Light Rain: 0.1 – 2.4 mm
        - Light Rain: 2.5 – 15.5 mm
        - Moderate Rain: 15.6 – 64.4 mm
        - Heavy Rain: 64.5 – 115.5 mm
        - Very Heavy Rain: 115.6 – 204.4 mm
        - Extremely Heavy Rain: >= 204.5 mm
        """
        counts = {
            "no_rain": 0,
            "very_light": 0,
            "light": 0,
            "moderate": 0,
            "heavy": 0,
            "very_heavy": 0,
            "extremely_heavy": 0,
        }
        events: list[dict[str, Any]] = []

        for _, row in self._data.iterrows():
            val = row[self.rainfall_column]
            if pd.isna(val):
                continue
            r = float(val)
            d_str = row[self.date_column].strftime("%Y-%m-%d")

            if r <= 0.05:
                cat = "no_rain"
            elif r < 2.5:
                cat = "very_light"
            elif r <= 15.5:
                cat = "light"
            elif r <= 64.4:
                cat = "moderate"
            elif r <= 115.5:
                cat = "heavy"
            elif r <= 204.4:
                cat = "very_heavy"
            else:
                cat = "extremely_heavy"

            counts[cat] += 1
            if cat in ("heavy", "very_heavy", "extremely_heavy"):
                events.append({"date": d_str, "rainfall_mm": r, "category": cat})

        total_valid = sum(counts.values())
        percentages = {k: float(round(v / total_valid * 100, 2)) if total_valid > 0 else 0.0 for k, v in counts.items()}

        meta = metadata(
            self._data,
            self.date_column,
            {"rainfall": "mm"},
            standard="India Meteorological Department (IMD)",
            location=self.location,
        )
        warning = "IMD rainfall intensity categories describe local precipitation intensity, not inundation depth."
        return result(
            "imd_rainfall_classification",
            {
                "total_days": total_valid,
                "category_counts": counts,
                "category_percentages": percentages,
                "significant_events": events,
            },
            meta,
            [warning, *warnings_for(self._data, self.date_column, (self.rainfall_column,))],
            _CAVEAT,
        )

    def multi_day_accumulation(self, windows: list[int] | None = None) -> AnalysisResult:
        """Compute concurrent multi-day accumulation analysis across rolling day windows."""
        target_windows = windows or [2, 3, 5, 7]
        for w in target_windows:
            positive_int(w, "window")

        summary: dict[str, Any] = {}
        for w in target_windows:
            roll = complete_rolling(self._data, self.date_column, self.rainfall_column, w)
            if roll:
                max_entry = max(roll, key=lambda x: x["total"])
                summary[f"{w}_day"] = {
                    "max_accumulation_mm": float(max_entry["total"]),
                    "peak_period": {"start": max_entry["start"], "end": max_entry["end"]},
                    "mean_accumulation_mm": float(round(float(np.mean([x["total"] for x in roll])), 2)),
                    "windows_evaluated": len(roll),
                }
            else:
                summary[f"{w}_day"] = {
                    "max_accumulation_mm": None,
                    "peak_period": None,
                    "mean_accumulation_mm": None,
                    "windows_evaluated": 0,
                }

        return result(
            "multi_day_accumulation",
            {"windows": summary},
            metadata(self._data, self.date_column, {"rainfall": "mm"}, evaluated_windows=target_windows, location=self.location),
            warnings_for(self._data, self.date_column, (self.rainfall_column,)),
            _CAVEAT,
        )

    def rainfall_anomalies(self, baseline_start: str, baseline_end: str) -> AnalysisResult:
        """Calculate percentage and absolute departure from baseline rainfall."""
        from ._common import period
        base = period(self._data, self.date_column, baseline_start, baseline_end)
        if len(base) < 2:
            raise ValidationError("baseline requires at least two observed rainfall readings.")
        base_mean = float(base[self.rainfall_column].mean())
        total_mean = float(self._data[self.rainfall_column].mean())
        dep = total_mean - base_mean
        pct_dep = float(round(dep / base_mean * 100, 2)) if base_mean > 0 else None

        return result(
            "rainfall_anomalies",
            {
                "baseline_mean_mm": float(round(base_mean, 2)),
                "observed_mean_mm": float(round(total_mean, 2)),
                "departure_mm": float(round(dep, 2)),
                "departure_percentage": pct_dep,
            },
            metadata(self._data, self.date_column, {"rainfall": "mm"}, baseline={"start": baseline_start, "end": baseline_end}, location=self.location),
            warnings_for(self._data, self.date_column, (self.rainfall_column,)),
            _CAVEAT,
        )

    def discharge_analysis(
        self,
        discharge_data: pd.DataFrame | None = None,
        discharge_column: str = "discharge",
        threshold_m3s: float | None = None,
    ) -> AnalysisResult:
        """Analyze river discharge observations against extreme runoff thresholds."""
        df = discharge_data if discharge_data is not None else self._data
        if discharge_column not in df.columns:
            raise ValidationError(f"Discharge column {discharge_column!r} not found.")
        valid = df.dropna(subset=[discharge_column])
        vals = valid[discharge_column].astype(float)
        if len(vals) == 0:
            raise ValidationError("Discharge data contains no valid numeric readings.")

        mean_d = float(vals.mean())
        max_d = float(vals.max())
        cutoff = threshold_m3s if threshold_m3s is not None else float(vals.quantile(0.95))
        exceedances = int((vals >= cutoff).sum())

        return result(
            "discharge_analysis",
            {
                "mean_discharge_m3s": float(round(mean_d, 2)),
                "peak_discharge_m3s": float(round(max_d, 2)),
                "threshold_m3s": float(round(cutoff, 2)),
                "exceedance_days": exceedances,
            },
            metadata(self._data, self.date_column, {"discharge": "m3/s"}, location=self.location),
            warnings_for(self._data, self.date_column, (self.rainfall_column,)),
            _CAVEAT,
        )

    def regional_flood_summary(
        self,
        data: pd.DataFrame | None = None,
        state_column: str = "state",
        district_column: str | None = None,
    ) -> AnalysisResult:
        """Aggregate flood metrics across Indian States or Districts."""
        from nielytics.geospatial.aggregation import aggregate_hazards_by_region
        source_df = data if data is not None else self._data
        return aggregate_hazards_by_region(
            source_df,
            region_type="state" if district_column is None else "district",
            region_column=state_column if district_column is None else district_column,
            hazard_column="hazard" if "hazard" in source_df.columns else self.rainfall_column,
            value_column=self.rainfall_column,
            date_column=self.date_column,
        )
