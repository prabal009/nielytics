"""Rainfall deficit and dry-spell proxies, not drought declarations."""
from __future__ import annotations

from math import isfinite
from typing import Any

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

    def standardized_precipitation_index(
        self,
        scale_months: int = 3,
        baseline_start: str | None = None,
        baseline_end: str | None = None,
    ) -> AnalysisResult:
        """Compute Standardized Precipitation Index (SPI) across rolling multi-month accumulations.

        Fits a two-parameter Gamma distribution to rolling non-zero rainfall totals
        and maps cumulative probability to the standard normal distribution.
        Recommended minimum sample size is 30 periods.
        """
        import numpy as np
        from scipy import stats

        if scale_months < 1:
            raise ValidationError("scale_months must be an integer >= 1.")

        df = self._data.copy()
        df["year_month"] = df[self.date_column].dt.to_period("M")
        monthly = df.groupby("year_month")[self.rainfall_column].sum().reset_index()
        monthly["date"] = monthly["year_month"].dt.to_timestamp()
        monthly = monthly.sort_values("date").reset_index(drop=True)

        monthly["rolling_rain"] = monthly[self.rainfall_column].rolling(
            window=scale_months, min_periods=scale_months
        ).sum()

        valid = monthly.dropna(subset=["rolling_rain"]).copy()
        if len(valid) < 3:
            raise ValidationError(f"SPI-{scale_months} requires at least 3 multi-month accumulation periods.")

        warnings: list[str] = []
        if len(valid) < 30:
            warnings.append(f"Sample size ({len(valid)}) is under 30 multi-month periods; SPI estimates may have higher sampling variance.")

        # Select calibration sample
        if baseline_start is not None and baseline_end is not None:
            calib_mask = valid["date"].between(pd.Timestamp(baseline_start), pd.Timestamp(baseline_end))
            calib_data = valid.loc[calib_mask, "rolling_rain"].to_numpy(dtype=float)
            if len(calib_data) < 3:
                calib_data = valid["rolling_rain"].to_numpy(dtype=float)
                warnings.append("Baseline period contained fewer than 3 periods; falling back to full series.")
        else:
            calib_data = valid["rolling_rain"].to_numpy(dtype=float)

        # Fit Gamma distribution
        pos_calib = calib_data[calib_data > 0]
        zero_count = int(np.sum(calib_data <= 0))
        total_calib = len(calib_data)
        q_zero = zero_count / total_calib if total_calib > 0 else 0.0

        if len(pos_calib) >= 3:
            # Fit Gamma with floc=0
            shape_a, _, scale_s = stats.gamma.fit(pos_calib, floc=0)
        else:
            # Fallback Gaussian
            shape_a, scale_s = None, None

        records: list[dict[str, Any]] = []
        for _, row in valid.iterrows():
            val = float(row["rolling_rain"])
            d_str = row["date"].strftime("%Y-%m")

            if shape_a is not None and scale_s is not None and scale_s > 0:
                if val <= 0:
                    h_prob = q_zero
                else:
                    g_prob = float(stats.gamma.cdf(val, a=shape_a, scale=scale_s))
                    h_prob = q_zero + (1.0 - q_zero) * g_prob
            else:
                # Fallback Gaussian CDF
                m_val, s_val = float(np.mean(calib_data)), float(np.std(calib_data, ddof=1)) or 1.0
                h_prob = float(stats.norm.cdf(val, loc=m_val, scale=s_val))

            # Clamp probability
            h_prob = max(1e-6, min(1.0 - 1e-6, h_prob))
            spi_val = float(stats.norm.ppf(h_prob))

            # Classification
            if spi_val >= 2.0:
                cat = "Extremely wet"
            elif spi_val >= 1.5:
                cat = "Very wet"
            elif spi_val >= 1.0:
                cat = "Moderately wet"
            elif spi_val > -1.0:
                cat = "Near normal"
            elif spi_val > -1.5:
                cat = "Moderately dry"
            elif spi_val > -2.0:
                cat = "Severely dry"
            else:
                cat = "Extremely dry"

            records.append({
                "date": d_str,
                "rolling_rain_mm": float(round(val, 2)),
                "spi": float(round(spi_val, 3)),
                "category": cat,
            })

        dry_episodes = [r for r in records if r["spi"] <= -1.0]
        meta = metadata(
            self._data,
            self.date_column,
            {"rainfall": "mm", "spi": "dimensionless"},
            scale_months=scale_months,
            baseline_period={"start": baseline_start, "end": baseline_end} if baseline_start else "full_series",
            location=self.location,
        )
        warning = "Standardized Precipitation Index (SPI) is a meteorological drought indicator, not an agricultural soil moisture measurement."
        return result(
            f"spi_{scale_months}",
            {
                "scale_months": scale_months,
                "total_periods": len(records),
                "drought_periods_count": len(dry_episodes),
                "records": records,
            },
            meta,
            [warning, *warnings, *warnings_for(self._data, self.date_column, (self.rainfall_column,))],
            _CAVEAT,
        )

    def seasonal_rainfall_anomaly(self, monsoon_months: list[int] | None = None) -> AnalysisResult:
        """Analyze Southwest Monsoon season (June–September) precipitation deficit."""
        months = monsoon_months or [6, 7, 8, 9]
        df = self._data.copy()
        df["month"] = df[self.date_column].dt.month
        df["year"] = df[self.date_column].dt.year

        monsoon = df[df["month"].isin(months)]
        annual_monsoon = monsoon.groupby("year")[self.rainfall_column].sum()
        if len(annual_monsoon) == 0:
            raise ValidationError("No observations found within the specified monsoon months.")

        long_term_mean = float(annual_monsoon.mean())
        annual_results: list[dict[str, Any]] = []

        for yr, total in annual_monsoon.items():
            f_tot = float(total)
            dep = f_tot - long_term_mean
            dep_pct = float(round(dep / long_term_mean * 100, 2)) if long_term_mean > 0 else 0.0
            annual_results.append({
                "year": int(yr),
                "monsoon_rainfall_mm": float(round(f_tot, 2)),
                "departure_mm": float(round(dep, 2)),
                "departure_percentage": dep_pct,
                "classification": "Deficient" if dep_pct < -20.0 else ("Excess" if dep_pct > 20.0 else "Normal"),
            })

        return result(
            "seasonal_monsoon_anomaly",
            {
                "long_term_monsoon_mean_mm": float(round(long_term_mean, 2)),
                "seasons": annual_results,
            },
            metadata(self._data, self.date_column, {"rainfall": "mm"}, monsoon_months=months, location=self.location),
            warnings_for(self._data, self.date_column, (self.rainfall_column,)),
            _CAVEAT,
        )

    def historical_drought_frequency(self) -> AnalysisResult:
        """Compute frequency of meteorological drought periods over observed years using SPI-3."""
        spi_res = self.standardized_precipitation_index(scale_months=3)
        records = spi_res.data["records"]
        dry_records = [r for r in records if r["spi"] <= -1.0]
        by_year: dict[str, int] = {}
        for r in dry_records:
            yr = r["date"].split("-")[0]
            by_year[yr] = by_year.get(yr, 0) + 1

        return result(
            "historical_drought_frequency",
            {
                "total_drought_months": len(dry_records),
                "annual_drought_frequency": by_year,
            },
            metadata(self._data, self.date_column, {"drought": "count"}, location=self.location),
            warnings_for(self._data, self.date_column, (self.rainfall_column,)),
            _CAVEAT,
        )
