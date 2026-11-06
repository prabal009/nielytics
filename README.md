# NIElytics (v2.0 Development Tree)

[![CI](https://github.com/prabal009/nielytics/actions/workflows/ci.yml/badge.svg)](https://github.com/prabal009/nielytics/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Development Tree](https://img.shields.io/badge/version-0.2.0.dev1-green.svg)](https://github.com/prabal009/nielytics)

**NIElytics** is an independent, high-performance computational Python analytics engine purpose-built for **ClimateLens India** (SDG 13 - Climate Action). It provides scientific hazard analytics, multi-source climate data harmonization, India-specific administrative geospatial aggregations, explainable multi-hazard composite indicators, deterministic insight generation, operational weather temperature forecasting, and long-term CMIP6 climate scenario projections.

> **Release & Distribution Notice**:
> The `0.1.0` package published on PyPI represents the initial release foundation and remains untouched. All advanced v2.0 capabilities documented here are hosted directly in the active GitHub development tree (`0.2.0.dev1`) at [`https://github.com/prabal009/nielytics.git`](https://github.com/prabal009/nielytics.git).

---

## Key Capabilities (v2.0)

### 1. Unified Facade (`ClimateAnalytics`)
Single-point orchestration managing data ingestion, schema harmonization, hazard routing, multi-hazard co-occurrence, and automated insight generation:
```python
from nielytics import ClimateAnalytics

analytics = ClimateAnalytics(offline=True)
analytics.register_dataset(hazard="heatwave", data="datasets/heatwave_sample.csv")
result = analytics.analyze(hazard="heatwave", region="Punjab", start_year=2020, end_year=2024)
print(result.to_dict())
```

### 2. Multi-Source Climate Harmonization (`nielytics.harmonization`)
- Standardized `StandardClimateRecord` and `HarmonizationSchema`.
- Ingests tabular text (`.csv`, `.tsv`, `.txt`, `.dat`), GeoJSON (`.geojson`), NetCDF (`.nc`), and Shapefiles (`.shp`).
- Automatic unit conversion across physical dimensions (Temperature: `C`, `F`, `K`; Precipitation: `mm`, `cm`, `inch`; Wind: `km/h`, `m/s`, `knots`; Pressure: `hPa`, `bar`, `atm`).
- Canonical name normalization for all 36 Indian States/UTs and key districts.
- Comprehensive transformation reporting (accepted rows, dropped rows, conversion logs).

### 3. India-Specific Geospatial Engine (`nielytics.geospatial`)
- Normalization mapping covering all 28 Indian States and 8 Union Territories with historical alias resolution ("Orissa" -> "Odisha", "Pondicherry" -> "Puducherry", "Mysore" -> "Karnataka", "Uttaranchal" -> "Uttarakhand", etc.).
- Reference coordinates, centroids, and bounding boxes for all 36 Indian States/UTs.
- Pure Python ray-casting point-in-polygon algorithm with optional Shapely acceleration.
- Spatial hazard clustering and hotspot detection using great-circle Haversine metrics.
- RFC 7946-compliant GeoJSON FeatureCollection generator for Leaflet, Mapbox, and deck.gl.

### 4. Advanced Scientific Hazard Indicators (`nielytics.hazards`)
- **Heatwave**: Official India Meteorological Department (IMD) criteria (plains departure >= 4.5°C or actual >= 45°C; severe at departure >= 6.5°C or actual >= 47°C; hilly/coastal criteria); baseline percentile indicators (e.g. 90th percentile heat spells).
- **Flood**: Official IMD rainfall classifications (Light 0.1–15.5 mm, Moderate 15.6–64.4 mm, Heavy 64.5–115.5 mm, Very Heavy 115.6–204.4 mm, Extremely Heavy >= 204.5 mm); multi-day accumulation analysis (2, 3, 5, 7 days); river discharge exceedance tracking.
- **Drought**: Scientific Standardized Precipitation Index (SPI-1, SPI-3, SPI-6, SPI-12) via 2-parameter Gamma distribution fitting and standard normal transform; Southwest monsoon seasonal anomaly analysis.
- **Landslide**: Compound trigger conditions combining multi-day antecedent saturation with extreme daily trigger rainfall; terrain slope and elevation screening.
- **Cyclone**: Official IMD cyclone intensity scale (Depression to Super Cyclonic Storm); wind speed unit conversions; coastline landfall proximity detection; seasonal trend breakdown (Pre-monsoon Apr–May vs Post-monsoon Oct–Dec).
- **Multi-Hazard Analytics**: Compound heat-drought episodes; rainfall-flood and rainfall-landslide correlations; regional multi-hazard overlap exposure matrix; fully transparent, weighted composite hazard indicator.

### 5. Temperature Forecasting & Climate Projections (`nielytics.forecasting`)
- **Short-Term Operational Forecasting (1 to 14 days)**:
  - Strict leakage-free feature engineering (cyclical day-of-year harmonics, strictly past lags $[t, t-1, t-2, t-6, t-13]$, trailing rolling stats, historical climatology).
  - Direct multi-step autoregressive Ridge regression models.
  - Expanding-window chronological backtesting with MAE, RMSE, MBE, MedAE, and skill scores vs persistence and climatology.
  - Calibrated empirical 80% and 95% prediction intervals.
  - Operational NWP weather forecast provider adapter with local ground-truth rolling bias correction.
  - Integration with `HeatwaveAnalyzer` to estimate daily heatwave exceedance risk probabilities.
- **Long-Term Climate Projections (2030 to 2050+)**:
  - Mode A: Theil-Sen robust historical trend extrapolation with non-linear caveat warnings.
  - Mode B: Standardized CMIP6 scenario projections (IPCC AR6 South Asia regional warming ranges for SSP1-2.6, SSP2-4.5, SSP5-8.5).
- **Safe Persistence**:
  - Pure JSON-based model and artifact serialization (zero pickle/joblib).

### 6. Deterministic Insight Engine (`nielytics.insights`)
- Derive structured, explainable findings directly from computed metrics:
  - Top anomalies and regional hazard spikes.
  - Statistically significant trends via Mann-Kendall test ($p < 0.05$).
  - Compound hazard co-occurrences.
  - Data quality and sample size insufficiency warnings ($N < 30$, missingness $> 20\%$).
- 100% deterministic rule engine; zero external LLM dependencies, zero hallucinations.

---

## Installation

### From GitHub (Latest v2 Development Tree)
```bash
python3 -m pip install "git+https://github.com/prabal009/nielytics.git"
```

### Local Editable Install (for Development)
```bash
git clone https://github.com/prabal009/nielytics.git
cd nielytics
python3 -m pip install -e '.[dev]'
```

### Optional Dependency Extras
NIElytics features zero-bloat core architecture running on pure `numpy`, `pandas`, and `scipy`. Heavy optional libraries can be installed via explicit extras:
```bash
pip install -e '.[visualization]'        # Plotly and Matplotlib
pip install -e '.[geospatial]'           # GeoPandas, Shapely, PyProj
pip install -e '.[climate]'              # xarray, netCDF4
pip install -e '.[advanced-statistics]'  # statsmodels, scikit-learn
pip install -e '.[all]'                  # Full suite of all optional extras
```

---

## Quick Start Examples

### 1. Ingest & Harmonize Messy Multi-Source Data
```python
import pandas as pd
from nielytics import DatasetHarmonizer, HarmonizationSchema

raw_data = pd.DataFrame({
    "date": ["2023-05-01", "2023-05-02"],
    "state": ["Orissa", "Pondicherry"],       # Historical state names
    "city": ["Bhubaneswar", "Pondicherry"],
    "temp_f": [104.0, 95.0],                  # Temperatures in Fahrenheit
    "lat": [20.29, 11.94],
    "lon": [85.82, 79.80],
})

schema = HarmonizationSchema(
    date_column="date",
    value_column="temp_f",
    state_column="state",
    district_column="city",
    latitude_column="lat",
    longitude_column="lon",
    hazard="heatwave",
    metric="tmax",
    source_unit="F",
    target_unit="C",  # Automatically converted to Celsius
)

harmonizer = DatasetHarmonizer(schema)
result = harmonizer.harmonize(raw_data)
df_clean = DatasetHarmonizer.to_dataframe(result)

# States normalized to official GoI standards: "Odisha", "Puducherry"
print(df_clean[["date", "state", "value", "unit"]])
```

### 2. Operational Temperature Forecasting & Heatwave Risk
```python
import pandas as pd
from nielytics import TemperatureForecaster

df = pd.read_csv("examples/sample_daily_temperature.csv")

forecaster = TemperatureForecaster(horizons=[1, 3, 7])
forecaster.fit(df, date_column="date", target_column="tmax")

# 7-day ahead forecast with 80% and 95% uncertainty intervals
forecast_res = forecaster.predict(horizon=7)

# Estimate daily probability of exceeding 40°C heatwave threshold
risk_res = forecaster.forecast_heatwave_risk(forecast_res, threshold_c=40.0)
print(risk_res.to_dict()["data"]["daily_risk"])
```

### 3. Long-Term CMIP6 Climate Projections
```python
from nielytics import ClimateProjectionEngine

engine = ClimateProjectionEngine()
projections = engine.project_cmip6_scenarios(
    baseline_temperature_c=28.5,
    target_years=[2030, 2040, 2050],
    scenarios=["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"],
)
print(projections.to_dict()["data"]["scenarios"])
```

---

## Documentation & Guides
- [API Reference](docs/api_reference.md)
- [Installation Guide & System Setup](docs/INSTALLATION.md)
- [Backend Integration Contract & JSON Schemas](docs/BACKEND_INTEGRATION.md)
- [Climate Hazard Methodology](docs/CLIMATE_METHODOLOGY.md)
- [Data Harmonization Specification](docs/DATA_HARMONIZATION.md)
- [Temperature Forecasting Architecture](docs/TEMPERATURE_FORECASTING.md)
- [Forecast Model Evaluation & Skill Metrics](docs/FORECAST_MODEL_EVALUATION.md)
- [Climate Scenario Projections](docs/CLIMATE_PROJECTIONS.md)
- [Library Audit & Improvement Roadmap](docs/IMPROVEMENT_AUDIT.md)
- [Version 0.2.0 Changelog](docs/CHANGELOG.md)

---

## License
MIT License. See [LICENSE](LICENSE) for details.
