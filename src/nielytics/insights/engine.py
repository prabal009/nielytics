"""Deterministic Insight Generation Engine deriving explainable climate risk observations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from nielytics.models.schemas import AnalysisResult


@dataclass(frozen=True)
class Insight:
    """A deterministic, explainable climate insight derived from analytical indicators."""

    category: str  # top_anomaly, frequency_spike, compound_overlap, trend_significance, data_insufficiency
    headline: str
    description: str
    metrics: dict[str, Any]
    geographic_scope: str | None = None
    date_range: list[str] | None = None
    confidence: str = "high"  # high, medium, low
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert insight to strictly JSON-compliant dictionary."""
        d = asdict(self)
        return d


class InsightEngine:
    """Generates deterministic, mathematically grounded insights from indicator results without external LLMs."""

    def __init__(self) -> None:
        pass

    def generate_insights(
        self,
        analysis_results: list[AnalysisResult] | dict[str, AnalysisResult],
        data_quality_report: dict[str, Any] | None = None,
    ) -> AnalysisResult:
        """Derive rule-based insights from a collection of AnalysisResult objects."""
        insights: list[Insight] = []
        res_list = list(analysis_results.values()) if isinstance(analysis_results, dict) else analysis_results

        # 1. Data Insufficiency check
        if data_quality_report is not None:
            total_rows = data_quality_report.get("total_rows", 0)
            if total_rows < 30:
                insights.append(Insight(
                    category="data_insufficiency",
                    headline="Sample Size Below Climatological Minimum",
                    description=f"Dataset contains only {total_rows} observations, below the 30-period threshold recommended for robust climatological statistics.",
                    metrics={"total_rows": total_rows, "recommended_minimum": 30},
                    confidence="high",
                    limitations=["Small sample sizes increase variance in extreme value estimations."],
                ))
            missingness = data_quality_report.get("missingness", {})
            for col, stats in missingness.items():
                pct = stats.get("missing_percentage", 0.0)
                if pct > 20.0:
                    insights.append(Insight(
                        category="data_insufficiency",
                        headline=f"Elevated Missing Data in {col}",
                        description=f"Column '{col}' exhibits {pct:.1f}% missingness, potentially biasing period aggregations.",
                        metrics={"column": col, "missing_percentage": pct},
                        confidence="high",
                        limitations=["Missing observations may obscure acute hazard events."],
                    ))

        # 2. Inspect individual AnalysisResults
        for res in res_list:
            feat = res.feature
            data = res.data

            # Check for Regional Aggregation / Top Anomaly
            if feat == "regional_hazard_aggregation":
                regions = data.get("regions", {})
                if regions:
                    # Find region with highest event count
                    top_reg, top_data = max(regions.items(), key=lambda item: item[1].get("event_count", 0))
                    count = top_data.get("event_count", 0)
                    if count > 0:
                        insights.append(Insight(
                            category="top_anomaly",
                            headline=f"Highest Hazard Concentration in {top_reg}",
                            description=f"{top_reg} recorded the highest frequency of hazard occurrences ({count} events) across evaluated regions.",
                            metrics={"region": top_reg, "event_count": count, "hazards": top_data.get("hazards", [])},
                            geographic_scope=top_reg,
                            date_range=top_data.get("date_range"),
                            confidence="high",
                            limitations=["Reflects observed records; station density variations may bias regional reporting."],
                        ))

            # Check for Trend Significance (Mann-Kendall)
            if feat == "historical_heatwave_frequency":
                trend = data.get("trend_analysis")
                if trend and trend.get("trend") in ("increasing", "decreasing"):
                    dir_str = trend["trend"]
                    p_val = trend.get("p_value", 1.0)
                    insights.append(Insight(
                        category="trend_significance",
                        headline=f"Statistically Significant {dir_str.title()} Heatwave Trend",
                        description=f"Mann-Kendall test detected a statistically significant {dir_str} trend in annual extreme heat occurrences (p = {p_val:.4f}).",
                        metrics={"trend": dir_str, "p_value": p_val, "tau": trend.get("tau"), "z": trend.get("z")},
                        confidence="high" if p_val < 0.01 else "medium",
                        limitations=["Trend reflects observed historical period and does not guarantee linear continuation."],
                    ))

            # Check for IMD Severe Heatwaves
            if feat == "imd_heatwave_classification":
                counts = data.get("counts", {})
                sev = counts.get("severe_heatwave", 0)
                hw = counts.get("heatwave", 0)
                if sev > 0:
                    insights.append(Insight(
                        category="frequency_spike",
                        headline=f"Severe Heatwave Thresholds Exceeded ({sev} Days)",
                        description=f"IMD criteria identified {sev} days meeting severe heatwave conditions (departures >= 6.5°C or actual tmax >= 47°C).",
                        metrics={"severe_heatwave_days": sev, "heatwave_days": hw},
                        confidence="high",
                        limitations=["Official IMD heatwave declarations require multiple stations within a meteorological subdivision."],
                    ))

            # Check for IMD Extreme Rainfall
            if feat == "imd_rainfall_classification":
                counts = data.get("category_counts", {})
                ext = counts.get("extremely_heavy", 0)
                vh = counts.get("very_heavy", 0)
                if ext > 0:
                    insights.append(Insight(
                        category="frequency_spike",
                        headline=f"Extremely Heavy Rainfall Recorded ({ext} Days)",
                        description=f"{ext} days recorded daily precipitation >= 204.5 mm (IMD Extremely Heavy category), creating acute flash flood risks.",
                        metrics={"extremely_heavy_days": ext, "very_heavy_days": vh},
                        confidence="high",
                        limitations=["Point gauge rainfall does not directly measure hydrological flood inundation extent."],
                    ))

            # Check for Drought SPI extremes
            if feat and feat.startswith("spi_"):
                records = data.get("records", [])
                ext_dry = [r for r in records if r.get("spi", 0.0) <= -2.0]
                if ext_dry:
                    insights.append(Insight(
                        category="top_anomaly",
                        headline="Extremely Severe Drought Periods Detected (SPI <= -2.0)",
                        description=f"Standardized Precipitation Index identified {len(ext_dry)} multi-month periods under extreme meteorological drought conditions.",
                        metrics={"extreme_drought_periods": len(ext_dry), "most_severe_spi": min(r["spi"] for r in ext_dry)},
                        confidence="high",
                        limitations=["SPI tracks meteorological precipitation deficits; hydrological and agricultural impacts depend on local storage."],
                    ))

            # Check for Compound Heat & Drought
            if feat == "compound_heat_drought":
                c_days = data.get("compound_event_days", 0)
                if c_days > 0:
                    insights.append(Insight(
                        category="compound_overlap",
                        headline=f"Compound Heat-Drought Co-occurrence ({c_days} Days)",
                        description=f"{c_days} days experienced concurrent extreme heat and rainfall deficit, significantly increasing compound climate stress.",
                        metrics={"compound_days": c_days, "region": data.get("region")},
                        geographic_scope=data.get("region"),
                        confidence="high",
                        limitations=["Compound indicators flag simultaneous threshold exceedance; biological heat stress also depends on humidity."],
                    ))

            # Check for Multi-hazard Overlap
            if feat == "regional_multi_hazard_overlap":
                matrix = data.get("matrix", {})
                multi_exposed = [reg for reg, info in matrix.items() if info.get("multi_hazard_exposed")]
                if multi_exposed:
                    insights.append(Insight(
                        category="compound_overlap",
                        headline=f"Multi-Hazard Exposure Identified in {len(multi_exposed)} Regions",
                        description=f"Regions including {', '.join(multi_exposed[:3])} exhibit documented exposure to two or more concurrent hazards.",
                        metrics={"multi_hazard_regions_count": len(multi_exposed), "sample_regions": multi_exposed[:5]},
                        confidence="high",
                        limitations=["Cross-hazard exposure matrix reflects ingested catalog records."],
                    ))

        return AnalysisResult(
            feature="deterministic_insights",
            data={
                "total_insights": len(insights),
                "insights": [ins.to_dict() for ins in insights],
            },
            metadata={"rule_engine": "deterministic_v2"},
            warnings=["Insights are deterministically derived from computed metrics; verify against ground truth."],
        )
