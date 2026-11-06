import json

from nielytics.insights import InsightEngine
from nielytics.models.schemas import AnalysisResult


def test_insight_engine_derivation_and_json():
    # Synthetic analysis results
    res_agg = AnalysisResult(
        feature="regional_hazard_aggregation",
        data={
            "regions": {
                "Odisha": {"event_count": 15, "hazards": ["cyclone", "flood"], "date_range": ["2023-01-01", "2023-12-31"]},
                "Punjab": {"event_count": 3, "hazards": ["heatwave"], "date_range": ["2023-05-01", "2023-06-30"]},
            }
        },
        metadata={},
    )

    res_trend = AnalysisResult(
        feature="historical_heatwave_frequency",
        data={
            "trend_analysis": {
                "trend": "increasing",
                "p_value": 0.005,
                "tau": 0.65,
                "z": 2.8,
            }
        },
        metadata={},
    )

    res_compound = AnalysisResult(
        feature="compound_heat_drought",
        data={
            "region": "Karnataka",
            "compound_event_days": 8,
        },
        metadata={},
    )

    quality_rep = {
        "total_rows": 20,  # Below 30
        "missingness": {"rainfall": {"missing_percentage": 25.0}},  # > 20%
    }

    engine = InsightEngine()
    insights_res = engine.generate_insights(
        [res_agg, res_trend, res_compound],
        data_quality_report=quality_rep,
    )

    assert insights_res.feature == "deterministic_insights"
    payload = insights_res.to_dict()
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload

    insights = insights_res.data["insights"]
    categories = [ins["category"] for ins in insights]

    assert "data_insufficiency" in categories
    assert "top_anomaly" in categories
    assert "trend_significance" in categories
    assert "compound_overlap" in categories

    top_anomaly = next(ins for ins in insights if ins["category"] == "top_anomaly")
    assert "Odisha" in top_anomaly["headline"]
