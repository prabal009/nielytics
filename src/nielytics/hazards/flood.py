"""Rainfall-based flood proxies; recorded floods require independent event data."""
from __future__ import annotations

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
