# NIElytics Library Audit & Improvement Roadmap (v2.0)

## Executive Summary
This document records the baseline architectural audit of the `nielytics` library (v0.1.0) and establishes the engineering specifications for the v2.0 upgrade (`0.2.0.dev1`). NIElytics is designed as an analytical computing engine for climate and disaster risk intelligence across India.

---

## 1. Baseline Findings & Severity Matrix

| Component | Current State (v0.1.0) | Gap / Deficiency | Severity | Target Solution (v2.0) |
|---|---|---|---|---|
| **Packaging & Dependencies** | Flat dependency structure; heavy visual/spatial packages unbundled | Heavy installs forced or missing optional boundaries | **Medium** | Grouped optional dependencies (`visualization`, `geospatial`, `climate`, `advanced-statistics`, `dev`, `all`) with graceful fallbacks. |
| **Data Ingestion** | CSV, JSON, Parquet, Excel only | Cannot read standard climate text files (`.tsv`, `.txt`, `.dat`), GeoJSON attributes, NetCDF (`.nc`), Shapefiles | **High** | Generalized tabular text loader, GeoJSON table extractor, NetCDF & Shapefile adapters with `OptionalDependencyError`. |
| **Data Quality & Units** | Basic missing-value dropping/filling | No unit conversions (C/F/K, mm/inch, km/h/knots); no comprehensive data quality reporting | **High** | `convert_units` engine; `data_quality_report` verifying completeness, missingness, numeric bounds, outlier prevalence. |
| **Statistical Methods** | Mean, std, median, basic rolling/z-score | Missing nonparametric trend tests (Mann-Kendall, Theil-Sen), robust slope, classical time-series decomposition | **High** | Mann-Kendall trend test with tie-correction, Theil-Sen robust estimator, additive/multiplicative time-series decomposition. |
| **Hazard: Heatwave** | Fixed threshold exceedance only | Lacks official India Meteorological Department (IMD) criteria (plains/hilly/coastal departures), percentile-based indicators | **Critical** | `imd_heatwave_classification` adhering to IMD departure & absolute limits; percentile heat spell analysis. |
| **Hazard: Flood** | Basic wet spell & sum | Lacks IMD rainfall classifications (Light to Extremely Heavy), multi-day accumulation analysis, river discharge tracking | **High** | `imd_rainfall_classification`, rolling multi-day accumulation (2, 3, 5, 7 days), discharge exceedance. |
| **Hazard: Drought** | Simple dry spell & cumulative deficit | Missing meteorological standard Standardized Precipitation Index (SPI) | **Critical** | Scientific Standardized Precipitation Index (SPI-1, 3, 6, 12) via Gamma distribution parameter fitting and standard normal transform. |
| **Hazard: Landslide** | Antecedent rainfall rolling sum | Missing compound antecedent trigger indicators (saturation + burst) and terrain screening proxies | **Medium** | `rainfall_trigger_indicator` (multi-day antecedent + trigger rain threshold), slope/elevation screening. |
| **Hazard: Cyclone** | Distance and basic wind speed | Lacks official IMD classification scale, wind speed conversions (knots, km/h, m/s), coastline landfall proximity | **High** | Official IMD scale (Depression to Super Cyclone), wind unit converters, coastline landfall detection. |
| **Geospatial & India** | Generic lat/lon distance | No normalization for historical/alternate Indian state/district spellings; no built-in state boundaries or GeoJSON exporter | **Critical** | Canonical 36 Indian State/UT dictionary, historical rename mapping (Orissa->Odisha, etc.), GeoJSON FeatureCollection generator. |
| **Multi-Hazard Analysis** | Single-hazard silos | No compound hazard co-occurrence analysis (e.g. heat+drought, rain+flood, rain+landslide) or transparent composite index | **High** | `MultiHazardAnalyzer` with compound event detection and transparent, explainable composite indicators. |
| **Insight Derivation** | Raw metrics only | No deterministic automated summary derivation; risk of hallucinated or ad-hoc interpretations | **High** | Deterministic `InsightEngine` emitting structured JSON insights (anomalies, spikes, trend significance) without LLMs. |
| **Unified Facade** | Disjoint classes | Requires multiple separate imports and boilerplate to run end-to-end multi-hazard workflows | **Medium** | `ClimateAnalytics` facade class providing unified dataset registration, execution, and export. |
| **Forecasting & Projections**| Absent | No temperature forecasting, backtesting, uncertainty intervals, or climate scenario projections | **Critical** | Complete `nielytics.forecasting` package with leakage-free backtesting, prediction intervals, and CMIP6 scenario projections. |

---

## 2. Architectural Principles for v2.0
1. **Core Zero-Bloat**: Core remains operational on pure `numpy`, `pandas`, and `scipy`. Optional heavy libraries (`plotly`, `geopandas`, `xarray`, `scikit-learn`) are deferred and protected by `OptionalDependencyError`.
2. **Strict JSON Serializable Boundary**: All analysis results expose `.to_dict()` returning strictly compliant JSON types (no `NaN`, `Infinity`, or raw NumPy types).
3. **Deterministic & Explainable**: Scientific methodologies follow official standards (IMD, WMO, IPCC) with transparent math, explicit warnings, and no stochastic hallucinations.
