# Changelog

All notable changes to the NIElytics repository are documented in this file.

## [0.2.0.dev1] - Active GitHub Development Tree (v2.0)

### Added
- **Unified Facade**: Added `ClimateAnalytics` high-level orchestration class in `nielytics.facade`.
- **Data Harmonization**:
  - Created `nielytics.harmonization` package with `DatasetHarmonizer`, `HarmonizationSchema`, and `StandardClimateRecord`.
  - Added support for text (`.tsv`, `.txt`, `.dat`), GeoJSON (`.geojson`), NetCDF (`.nc`), and Shapefile (`.shp`) loaders.
  - Added physical unit conversion (`cleaner.convert_units`) across temperature, precipitation, wind speed, and pressure.
  - Added `cleaner.data_quality_report` and `Dataset.quality_report`.
- **Advanced Statistics & Time-Series**:
  - Implemented `z_score`, `linear_regression` (with Student-t CI), `theil_sen_slope` (robust nonparametric trend), and `mann_kendall_test` (with tie-corrected variance).
  - Implemented classical `decompose_timeseries` (additive and multiplicative) and `detect_anomalies`.
- **India-Specific Geospatial Engine**:
  - Implemented `nielytics.geospatial.india_names` canonical mapping for all 36 Indian States/UTs and key districts with historical alias resolution ("Orissa" -> "Odisha", "Pondicherry" -> "Puducherry", "Mysore" -> "Karnataka", etc.).
  - Added reference centroids and bounding boxes for all 36 States/UTs in `boundaries.py`.
  - Added pure-Python ray-casting point-in-polygon algorithm.
  - Added `aggregate_hazards_by_region`, `get_state_hazard_summary`, `get_district_hazard_summary`, `detect_hazard_hotspots`, `compare_hazard_regions`, and `generate_hazard_geojson`.
- **Enhanced 5-Hazard Analyzers**:
  - Heatwave: added `imd_heatwave_classification` (official IMD criteria for plains, hilly, coastal), `percentile_heatwave_indicators`, and `historical_heatwave_frequency`.
  - Flood: added `imd_rainfall_classification` (IMD Light to Extremely Heavy categories), `multi_day_accumulation`, `rainfall_anomalies`, and `discharge_analysis`.
  - Drought: added `standardized_precipitation_index` (SPI-1, 3, 6, 12 via Gamma distribution fitting), `seasonal_rainfall_anomaly`, and `historical_drought_frequency`.
  - Landslide: added compound `rainfall_trigger_indicator` (antecedent saturation + daily trigger) and `slope_elevation_screening`.
  - Cyclone: added `imd_cyclone_classification` (IMD intensity scale), `convert_wind_units`, `landfall_analysis`, `regional_cyclone_exposure`, and `seasonal_cyclone_trend`.
  - Multi-Hazard: added `MultiHazardAnalyzer` with compound heat-drought overlap, rainfall-flood correlation, rainfall-landslide correlation, cross-hazard exposure matrix, and transparent composite hazard indicator.
- **Deterministic Insight Engine**:
  - Created `nielytics.insights` package with `InsightEngine` and `Insight` schema producing rule-based explainable findings without external LLMs.
- **Forecasting & Climate Projections**:
  - Created `nielytics.forecasting` package with `TemperatureForecaster` and `ClimateProjectionEngine`.
  - Strict leakage-free feature engineering and direct multi-step Ridge regressors.
  - Chronological expanding-window backtesting and baseline skill scores.
  - Calibrated empirical 80% and 95% prediction intervals.
  - Operational NWP weather forecast provider adapter with local ground-truth rolling bias correction.
  - Heatwave risk exceedance probability forecasting.
  - CMIP6 scenario projections (SSP1-2.6, SSP2-4.5, SSP5-8.5) and Theil-Sen trend extrapolation.
  - Safe JSON persistence (zero pickle/joblib).
- **CI / GitHub Automation**:
  - Added `.github/workflows/ci.yml` running multi-version Python testing (3.11, 3.12, 3.13) and Ruff linting.

### Changed
- Packaging: updated `pyproject.toml` to version `0.2.0.dev1`.
- Cleanly split heavy dependencies (`openpyxl`, `pyarrow`, `plotly`, `geopandas`, `xarray`, `netCDF4`, `statsmodels`, `scikit-learn`) into optional groups with graceful `OptionalDependencyError` fallbacks.
- Verified 100% strict JSON serialization for all `AnalysisResult.to_dict()` payloads.

---

## [0.1.0] - 2025-10-29 (PyPI Legacy Foundation)
- Initial foundation release with basic `Dataset`, basic 5 hazard analyzers, and Plotly visualization helpers.
