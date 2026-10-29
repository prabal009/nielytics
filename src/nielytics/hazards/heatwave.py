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
