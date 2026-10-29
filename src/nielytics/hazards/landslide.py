"""Antecedent rainfall and slope screening; not a validated landslide model."""
from __future__ import annotations

from datetime import date, timedelta

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
    threshold,
    warnings_for,
)
from ._coordinates import location

_CAVEAT = "Rainfall and slope screening is not a validated landslide prediction or an event record."


class LandslideAnalyzer:
    """Screen daily rain (mm) and measured terrain slope (degrees) jointly."""

    def __init__(self, data: pd.DataFrame, *, date_column: str = "date",
                 rainfall_column: str = "rainfall", slope_column: str = "slope",
                 rainfall_unit: str, slope_unit: str,
                 latitude: float | None = None, longitude: float | None = None) -> None:
        if rainfall_unit != "mm" or slope_unit != "degrees":
            raise ValidationError("supported rainfall_unit='mm', slope_unit='degrees' only")
        self.date_column, self.rainfall_column, self.slope_column = date_column, rainfall_column, slope_column
        self._data = daily(data, date_column, {rainfall_column: (0, None), slope_column: (0, 90)})
        self.location = location(latitude, longitude)

    def _antecedent(self, window_days: int) -> list[dict]:
        """Strict prior-day sums, never including the assessment day's rainfall."""
        windows = complete_rolling(self._data, self.date_column, self.rainfall_column, window_days)
        known_dates = set(self._data[self.date_column].dt.date)
        records = []
        for window in windows:
            assessment_day = date.fromisoformat(window["end"]) + timedelta(days=1)
            if assessment_day in known_dates:
                records.append({"date": assessment_day.isoformat(),
                                "antecedent_mm": window["total"]})
        return records

    def antecedent_rainfall(self, *, window_days: int) -> AnalysisResult:
        """Rainfall in the preceding N consecutive complete days, per observed day."""
        window = positive_int(window_days, "window_days")
        records = self._antecedent(window)
        return result("antecedent_rainfall", {"days": records},
                      metadata(self._data, self.date_column, {"antecedent_rainfall": "mm"},
                               window_days=window, method="complete previous N days, excluding assessment day",
                               location=self.location),
                      warnings_for(self._data, self.date_column, (self.rainfall_column,)), _CAVEAT)

    def susceptibility_indicators(self, *, window_days: int,
                                  rainfall_threshold_mm: float,
                                  slope_threshold_degrees: float) -> AnalysisResult:
        """Mark days meeting both caller-supplied antecedent rain and slope cutoffs.

        This is a transparent screening indicator, not a probability/risk score.
        Missing slope or antecedent observations produce unknown, not low risk.
        """
        window = positive_int(window_days, "window_days")
        rain_cutoff = threshold(rainfall_threshold_mm, "rainfall_threshold_mm", minimum=0)
        slope_cutoff = threshold(slope_threshold_degrees, "slope_threshold_degrees", minimum=0)
        if slope_cutoff > 90:
            raise ValidationError("slope_threshold_degrees must not exceed 90")
        antecedent = {item["date"]: item["antecedent_mm"] for item in self._antecedent(window)}
        days = []
        unknown_dates = []
        for day, slope in self._data[[self.date_column, self.slope_column]].itertuples(index=False, name=None):
            key = day.date().isoformat()
            if key not in antecedent or pd.isna(slope):
                unknown_dates.append(key)
                continue
            rain = antecedent[key]
            days.append({"date": key, "antecedent_mm": rain, "slope_degrees": float(slope),
                         "meets_thresholds": bool(rain >= rain_cutoff and slope >= slope_cutoff)})
        return result("landslide_susceptibility_indicator",
                      {"days": days, "unknown_days": len(unknown_dates), "unknown_dates": unknown_dates},
                      metadata(self._data, self.date_column,
                               {"antecedent_rainfall": "mm", "slope": "degrees"},
                               window_days=window, rainfall_threshold_mm=rain_cutoff,
                               slope_threshold_degrees=slope_cutoff,
                               method="both user cutoffs met; no calibrated predictive validity",
                               location=self.location),
                      warnings_for(self._data, self.date_column,
                                   (self.rainfall_column, self.slope_column)), _CAVEAT)

    def landslide_frequency(self, events: pd.DataFrame, *, event_date_column: str = "date") -> AnalysisResult:
        """Count independent caller-provided historical landslide records per year."""
        records = frame(events, (event_date_column,))
        records[event_date_column] = dates(records[event_date_column], daily=True)
        counts = records[event_date_column].dt.year.value_counts().sort_index()
        return result("recorded_landslide_frequency",
                      {"years": [{"year": int(year), "events": int(count)} for year, count in counts.items()]},
                      {"kind": "historical_recorded_events", "units": {"count": "events"},
                       "period": {"start": records[event_date_column].min().date().isoformat(),
                                  "end": records[event_date_column].max().date().isoformat()},
                       "method": "counts of supplied records; not an exhaustive catalog"},
                      [], "Historical event records are not live landslide warnings.")
