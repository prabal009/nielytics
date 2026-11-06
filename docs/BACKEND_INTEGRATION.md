# Backend Integration Contract & JSON Schemas

## 1. Overview & Serialization Contract
All analysis methods across `nielytics` return instances of `AnalysisResult`. Every `AnalysisResult` exposes the `.to_dict()` method, which guarantees **strict JSON compliance**:
- Zero `NaN`, `+Infinity`, `-Infinity`, or un-coerced NumPy scalar types.
- Missing values are explicitly represented as JSON `null`.
- Timestamps and dates are formatted as ISO 8601 strings (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`).
- Safe to serialize with `json.dumps(result.to_dict(), allow_nan=False)`.

---

## 2. Standard Top-Level Envelope Schema
```json
{
  "status": "success",
  "feature": "imd_heatwave_classification",
  "data": {
    "total_days": 10,
    "counts": {
      "no_heatwave": 7,
      "heatwave": 2,
      "severe_heatwave": 1
    },
    "events": [
      {
        "date": "2023-05-15",
        "tmax": 45.2,
        "classification": "heatwave",
        "departure": 5.2
      }
    ]
  },
  "metadata": {
    "standard": "India Meteorological Department (IMD)",
    "terrain": "plains",
    "normal_tmax": 40.0,
    "units": {"temperature": "C"}
  },
  "warnings": [
    "IMD heatwave criteria require at least two stations meeting conditions in a subdivision for official declaration."
  ],
  "caveat": "Temperature threshold exceedance is not an official heatwave declaration."
}
```

---

## 3. Standalone Python Backend Integration Snippet
Backend API controllers (e.g., FastAPI, Flask, Django, Node.js sub-processes) can invoke NIElytics and return standard responses:

```python
from fastapi import FastAPI, HTTPException
import pandas as pd
from nielytics import ClimateAnalytics, ValidationError

app = FastAPI(title="ClimateLens India API")
analytics = ClimateAnalytics(offline=True)

# Register dataset on server boot
analytics.register_dataset(
    hazard="heatwave",
    data="datasets/historical_temperature.csv",
    schema={"date_column": "date", "value_column": "tmax", "state_column": "state"},
)

@app.get("/api/v1/hazards/heatwave/{region}")
def get_heatwave_profile(region: str, start_year: int = 2015, end_year: int = 2024):
    try:
        result = analytics.analyze(
            hazard="heatwave",
            region=region,
            start_year=start_year,
            end_year=end_year,
        )
        # Directly return strictly compliant JSON dictionary
        return result.to_dict()
    except ValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")
```
