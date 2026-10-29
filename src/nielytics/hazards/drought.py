"""Rainfall deficit and dry-spell proxies, not drought declarations."""
from __future__ import annotations

from math import isfinite

import pandas as pd

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._common import daily, metadata, period, positive_int, result, spells, threshold, warnings_for
from ._coordinates import location

_CAVEAT = "Rainfall deficit or a dry spell alone is not an official drought declaration."


class DroughtAnalyzer:
    """Analyze daily precipitation in explicitly supplied millimeters."""

    def __init__(self, data: pd.DataFrame, *, date_column: str = "date",
                 rainfall_column: str = "rainfall", unit: str,
                 latitude: float | None = None, longitude: float | None = None) -> None:
        if unit != "mm":
            raise ValidationError("rainfall unit must be 'mm'")
        self.date_column, self.rainfall_column = date_column, rainfall_column
        self._data = daily(data, date_column, {rainfall_column: (0, None)})
        self.location = location(latitude, longitude)

    def dry_spell_duration(self, *, threshold_mm: float = 0.0,
                           minimum_days: int = 3) -> AnalysisResult:
        """Consecutive observed days with rain <= threshold; gaps break spells."""
        cutoff = threshold(threshold_mm, "threshold_mm", minimum=0)
        days = positive_int(minimum_days, "minimum_days")
        episodes = spells(self._data, self.date_column, self.rainfall_column,
                          cutoff, above=False, minimum_days=days)
        return result("dry_spell_duration", {"episodes": episodes, "count": len(episodes)},
                      metadata(self._data, self.date_column, {"rainfall": "mm"},
                               threshold_mm=cutoff, minimum_days=days, location=self.location),
                      warnings_for(self._data, self.date_column, (self.rainfall_column,)), _CAVEAT)

    def rainfall_deficit(self, *, baseline_start: str | None = None,
                         baseline_end: str | None = None, start: str | None = None,
                         end: str | None = None) -> AnalysisResult:
        """Observed daily mean below an explicit reference-period daily mean.

        No seasonal adjustment: comparability of seasons and baseline
        representativeness are the caller's responsibility. Not SPI.
        """
        if baseline_start is None or baseline_end is None:
            raise ValidationError("explicit baseline_start and baseline_end are required")
        baseline = period(self._data, self.date_column, baseline_start, baseline_end)
        if baseline.empty or baseline[self.rainfall_column].notna().sum() < 2:
            raise ValidationError("baseline requires at least two observed rainfall values")
        if start is None or end is None:
            raise ValidationError("explicit comparison start and end are required")
        observed = period(self._data, self.date_column, start, end)
        if observed.empty or not observed[self.rainfall_column].notna().any():
            raise ValidationError("comparison period requires observed rainfall")
        reference = float(baseline[self.rainfall_column].mean())
        mean = float(observed[self.rainfall_column].mean())
        difference = reference - mean
        percent = 100 * (difference / reference) if reference > 0 else None
        if not all(isfinite(value) for value in (reference, mean, difference)) or (
            percent is not None and not isfinite(percent)
        ):
            raise ValidationError("rainfall deficit exceeds finite numeric range")
        warnings = ["Unadjusted daily means require comparable seasons and a representative baseline.",
                    *warnings_for(self._data, self.date_column, (self.rainfall_column,))]
        if reference == 0:
            warnings.append("Baseline precipitation is zero; percentage deficit is undefined.")
        if difference < 0:
            warnings.append("Negative deficit indicates rainfall surplus relative to the baseline.")
        return result("rainfall_deficit", {"baseline_mean_mm_per_day": reference,
                       "observed_mean_mm_per_day": mean, "deficit_mm_per_day": difference,
                       "deficit_percent": percent,
                       "observed_days": int(observed[self.rainfall_column].count())},
                      metadata(observed, self.date_column, {"rainfall": "mm", "daily_mean": "mm/day"},
                               baseline_period={"start": baseline_start, "end": baseline_end},
                               method="difference of observed daily means; no seasonal adjustment",
                               location=self.location),
                      warnings, _CAVEAT)
