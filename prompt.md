# NIElytics — MASTER GITHUB DEVELOPMENT & IMPROVEMENT PROMPT

## ROLE

You are an autonomous senior software engineering team consisting of:

1. Python Library Architect
2. Climate Data Scientist
3. Geospatial Analysis Engineer
4. Statistical Computing Specialist
5. Data Engineering Specialist
6. Software Testing and Performance Engineer
7. Technical Documentation Engineer

Your responsibility is to comprehensively improve my existing NIElytics library and turn it into a powerful, reliable, modular Python analytics library.

**GitHub repository:**
https://github.com/prabal009/nielytics

**Project:** ClimateLens India

**Purpose:** Climate and disaster-data analysis for India, covering heatwaves, floods, droughts, landslides, and cyclones.

## ABSOLUTE RULE — GITHUB ONLY

I WILL NOT publish any further updates to PyPI.

The existing PyPI release must remain completely untouched.

All development, improvements, documentation, testing, and future maintenance must happen through my existing GitHub repository.

You must:

- Work within the existing cloned repository.
- Reuse and improve the existing code.
- Preserve working functionality.
- Use local editable installations for development.
- Support direct installation from GitHub.
- Update GitHub documentation.
- Use Git for version control.
- Commit completed, tested changes.
- Push changes to an appropriate GitHub branch when authenticated and authorized.
- Prefer a feature branch and pull request for major changes.

You must NOT:

- Publish to PyPI or TestPyPI.
- Execute `twine upload` or any publishing command.
- Request or use PyPI credentials.
- Introduce automatic package publishing workflows.
- Create a separate replacement repository.
- Force-push or overwrite unrelated changes.
- Delete working modules merely to simplify implementation.

If package version metadata needs updating, use an appropriate development version that clearly distinguishes the GitHub development tree from the old PyPI release.

The README must clearly identify GitHub as the source for the latest development version.

---

# PHASE 1 — UNDERSTAND THE ENTIRE EXISTING LIBRARY

Before making changes, inspect the actual repository.

Read all relevant files, including:

- README.md
- AGENTS.md
- pyproject.toml
- INTEGRATION_CONTRACT.md
- NIElytics_MASTER_PROMPT.md
- COMMANDS_AND_USAGE.md
- src/nielytics/
- docs/
- examples/
- tests/

Identify the existing functionality and determine its correctness.

Perform a complete audit covering:

- Code quality
- Architecture
- Mathematical correctness
- Data-processing correctness
- Climate methodology
- Error handling
- Missing functionality
- Dependencies
- Test coverage
- Documentation
- Performance
- Security
- Compatibility

Run the existing test suite before editing.

Create `docs/IMPROVEMENT_AUDIT.md`, documenting confirmed issues, evidence, severity, and recommended solutions.

Do not assume a previously reported problem exists until you have inspected the relevant implementation.

Do not stop after the audit. Continue with implementation.

---

# PHASE 2 — IMPROVE LIBRARY ARCHITECTURE

Modernize NIElytics into a modular, maintainable library.

Preserve the existing module layout wherever possible.

Organize additional functionality into logically separated components for:

- Core data structures
- Data loading
- Data cleaning
- Statistical analysis
- Time-series analysis
- Climate hazard analysis
- Geospatial operations
- Dataset harmonization
- Data validation
- Unit conversions
- Analysis result generation
- Visualization
- External data connectors

Keep public imports stable unless a change is demonstrably necessary.

Avoid circular imports, excessive abstraction, duplicated utility functions, and monolithic modules.

Use type annotations, useful docstrings, explicit exceptions, and structured logging.

Ensure importing NIElytics does not automatically trigger network requests, expensive processing, or plotting windows.

---

# PHASE 3 — ADD AND OPTIMIZE PYTHON DEPENDENCIES

Evaluate the following libraries based on actual implementation requirements.

| Library | Purpose |
|---|---|
| NumPy | Numerical calculations |
| Pandas | Tabular data processing |
| SciPy | Statistical analysis |
| Statsmodels | Statistical models and time-series methods |
| GeoPandas | Geographic data analysis |
| Shapely | Geometric operations |
| PyProj | Coordinate transformations |
| Rasterio | Raster processing |
| Xarray | Multidimensional climate datasets |
| h5netcdf / netCDF4 | Climate file support |
| Dask | Optional large-dataset processing |
| PyArrow | Parquet support |
| OpenPyXL | Excel processing |
| xlrd | Legacy Excel support |
| Plotly | Interactive charts |
| Matplotlib | Scientific visualization |
| Pandera | DataFrame schema validation |
| Pydantic | Structured integration models, if useful |
| Pint | Unit conversion |
| climate-indices | Reference implementation for appropriate climate indices |
| pymannkendall | Nonparametric trend analysis |
| scikit-learn | Optional clustering and validated ML workflows |
| pytest | Unit and integration testing |
| pytest-cov | Test coverage |
| Hypothesis | Property-based testing |
| Ruff | Linting and formatting |
| mypy | Static type analysis |

IMPORTANT:

Do not install everything blindly.

Evaluate each dependency for necessity, compatibility, maintenance status, licensing, and resource consumption.

Prefer existing Python functionality when it is sufficient.

Keep computationally heavy packages optional.

Implement appropriate optional dependency groups in `pyproject.toml`.

Suggested groups:

- excel
- parquet
- geospatial
- raster
- climate
- visualization
- advanced-statistics
- development
- all

Verify installation behavior for each group.

The application must run on Kali Linux with Python 3.11 or newer, 16 GB RAM, and no dedicated GPU.

---

# PHASE 4 — ADVANCED DATA PROCESSING

Improve the core `Dataset` abstraction without breaking its established behavior.

Support:

1. CSV files
2. XLS and XLSX files
3. JSON files
4. Parquet files
5. TXT-based tabular datasets
6. GeoJSON files
7. Shapefiles
8. NetCDF files where optional support is installed
9. Existing Pandas DataFrames

Do not promise unrestricted support for every possible schema.

Implement configurable readers, explicit schema validation, and descriptive error reporting.

## Data cleaning

Implement or improve:

- Duplicate detection and removal
- Missing-value inspection
- Configurable missing-value treatment
- Date parsing
- Column standardization
- Numeric validation
- Outlier detection
- Unit conversion
- Data-type conversion
- Dataset profiling
- Data-quality reporting

Never silently fabricate observations.

Preserve original data, transformation history, and data provenance.

## Multi-source dataset harmonization

ClimateLens India uses multiple climate datasets with different structures.

Build configurable adapters to standardize them into a shared analysis model without losing important source-specific attributes.

Support harmonization across:

- Date and time
- State
- District
- Latitude
- Longitude
- Hazard category
- Measurement value
- Measurement unit
- Source metadata
- Data quality
- Observation type

Make schema mappings configurable rather than assuming that all datasets use identical column names.

Allow users to align daily, monthly, annual, and event-based records using explicit policies.

Create reports explaining every transformation.

---

# PHASE 5 — ADVANCED STATISTICAL CAPABILITIES

Improve NIElytics beyond basic descriptive statistics.

Implement or validate:

- Mean, median, mode
- Variance and standard deviation
- Covariance and correlation
- Percentiles and quantiles
- Z-score analysis
- Rolling averages
- Moving-window summaries
- Linear regression
- Robust trend estimation
- Theil–Sen slope
- Mann–Kendall trend testing
- Seasonal trend analysis
- Time-series decomposition
- Anomaly detection
- Historical baseline comparisons
- Confidence intervals when justified

Consider autocorrelation and seasonality before interpreting statistical significance.

Document assumptions and minimum sample requirements.

Write numerical tests that compare calculated results against reliable reference implementations or analytically known outputs.

Do not present an insignificant trend as statistically significant.

---

# PHASE 6 — HEATWAVE ANALYZER IMPROVEMENTS

Enhance `HeatwaveAnalyzer` using scientifically defensible indicators.

Implement:

- Temperature anomaly calculations
- Extreme temperature detection
- Percentile-based heatwave indicators
- Consecutive hot-day detection
- Seasonal baseline comparisons
- Heat-event duration
- Historical heat-event frequency
- State-wise heat analysis
- District-wise heat analysis where appropriate observations exist

Study official India Meteorological Department methodology.

Make heatwave classification criteria configurable and clearly document whether the inputs satisfy any official definition.

Do not use an arbitrary threshold while claiming official IMD compliance.

Return structured outputs containing statistics, dates, geographic coverage, units, methodology, and warnings.

---

# PHASE 7 — FLOOD ANALYZER IMPROVEMENTS

Enhance `FloodAnalyzer`.

Implement:

- Extreme rainfall analysis
- Consecutive wet-day detection
- Multi-day rainfall accumulation
- Rainfall anomalies
- Historical flood-event statistics
- Flood-event frequency
- State-wise flood-event summaries
- District-wise flood-event summaries
- River-discharge analysis where reliable discharge data exists

Distinguish rainfall indicators from documented flooding.

Do not infer inundation boundaries from rainfall alone.

Implement spatial summaries only when valid geographic data exists.

Clearly state when an output is a proxy indicator rather than a validated flood-risk prediction.

---

# PHASE 8 — DROUGHT ANALYZER IMPROVEMENTS

Enhance `DroughtAnalyzer`.

Implement:

- Rainfall deficit calculations
- Consecutive dry-day analysis
- Seasonal rainfall anomalies
- Historical drought frequency
- Drought-area summaries
- Standardized Precipitation Index (SPI)
- Configurable SPI accumulation periods

Investigate the scientifically correct use of SPI-1, SPI-3, SPI-6, and SPI-12.

Handle zero rainfall, insufficient historical data, distribution-fitting failures, and missing observations.

Consider adding SPEI only if reliable evapotranspiration inputs and a validated method are available.

Use reference libraries to validate calculations where possible.

Never invent temperature or rainfall measurements.

---

# PHASE 9 — LANDSLIDE ANALYZER IMPROVEMENTS

Enhance `LandslideAnalyzer`.

Implement:

- Historical landslide-event analysis
- Event-density calculations
- Rainfall-triggering indicators
- Cumulative antecedent rainfall
- Landslide-event frequency
- Slope-related analysis
- Elevation-based analysis
- Geospatial event summaries
- Regional historical comparisons

Use actual slope and elevation inputs when available.

Do not invent terrain data.

Distinguish historical event density, screening indicators, and validated landslide susceptibility.

Avoid claiming accurate landslide prediction without calibration and independent validation.

---

# PHASE 10 — CYCLONE ANALYZER IMPROVEMENTS

Enhance `CycloneAnalyzer`.

Implement:

- Historical cyclone frequency
- Cyclone track analysis
- Maximum sustained wind statistics
- Cyclone intensity summaries
- Track-distance calculations
- Closest approach to a region
- Historical landfall analysis where reliable coastline and track data exist
- Regional cyclone exposure indicators
- Seasonal cyclone trends

Ensure correct wind-speed conversions.

Account for agency differences in sustained-wind averaging periods.

Use geodesic calculations where appropriate.

Do not confuse cyclone intensity with actual damage or economic loss.

---

# PHASE 11 — INDIA-SPECIFIC GEOSPATIAL ANALYSIS

This is one of the highest-priority areas.

NIElytics should provide powerful spatial processing for Indian climate datasets.

Implement:

- India state-boundary loading
- District-boundary loading
- State and district name normalization
- Spatial joins
- Coordinate reference system conversion
- Point-in-polygon operations
- Geographic distance calculations
- Event-density calculations
- Regional aggregation
- Hazard hotspot indicators
- Spatial filtering
- GeoJSON generation
- Multi-region comparison

Use caller-provided or properly licensed public boundary datasets.

Do not bundle large geographic datasets unnecessarily.

Support outputs compatible with Leaflet, Mapbox, and other frontend mapping frameworks.

Example conceptual functions:

```python
get_state_hazard_summary(...)
get_district_hazard_summary(...)
aggregate_hazards_by_region(...)
generate_hazard_geojson(...)
detect_hazard_hotspots(...)
compare_hazard_regions(...)
```

Adapt names to the existing architecture.

Make all geospatial outputs scientifically meaningful and geometrically valid.

---

# PHASE 12 — MULTI-HAZARD ANALYTICS

Implement a new high-level capability to analyze multiple hazards together.

Support:

1. Heatwave versus drought comparison.
2. Extreme rainfall versus documented flood-event comparison.
3. Rainfall versus recorded landslide-event comparison.
4. Regional overlap of multiple hazards.
5. Multi-hazard historical trend summaries.
6. Comparison of hazard frequency across regions.
7. Multi-hazard map datasets.

Do not confuse correlation with causation.

Implement normalized comparison indicators only when their underlying measurements and assumptions justify comparison.

If a composite score is offered, it must be optional and explainable.

Expose:

- Original measurements
- Normalization method
- Weights
- Geographic coverage
- Time period
- Missing-data policy
- Uncertainty and limitations

Do not market an unvalidated composite indicator as a scientifically established disaster-risk index.

---

# PHASE 13 — DATA SOURCE CONNECTORS

Inspect all existing climate-provider connectors.

Improve error handling, caching, validation, and source attribution.

Investigate reliable, openly accessible sources when relevant, including:

- IMD
- India-WRIS
- NASA POWER
- NASA Earthdata
- NOAA
- IBTrACS
- ISRO Bhuvan
- Relevant officially published Indian disaster datasets

Verify source availability, authentication requirements, geographic coverage, update frequency, terms of use, and actual data format before implementing a connector.

Do not assume every provider offers a public API.

Do not scrape restricted sites or bypass authentication.

Never embed API keys in source code.

Support offline operation using already downloaded datasets.

Provide source metadata with each result.

If an external data service is unavailable, return a meaningful error rather than simulated observations.

All automated tests must work without live network access.

---

# PHASE 14 — AUTOMATIC INSIGHT GENERATION

Implement a deterministic and explainable insight engine.

Example insights:

- The state with the largest recorded rainfall anomaly during a specified period.
- Districts with the highest documented flood-event frequency.
- Regions showing notable historical temperature trends.
- Areas containing overlapping recorded hazard events.
- States with insufficient data for meaningful conclusions.

Every insight must be derived from actual calculations.

Each insight should include supporting measurements, sources, date ranges, units, and limitations.

Do not require OpenAI, Gemini, or another LLM API.

No fabricated narratives, numbers, or percentages.

---

# PHASE 15 — HIGH-LEVEL ANALYSIS API

Create a convenient facade only after inspecting the existing result contract.

A proposed user-facing interface:

```python
from nielytics import ClimateAnalytics

analytics = ClimateAnalytics(
    data_directory="./datasets",
    offline=True,
)

analytics.register_dataset(
    hazard="drought",
    path="./datasets/drought.csv",
    schema={
        # Explicit mapping for the real dataset
    },
)

result = analytics.analyze(
    hazard="drought",
    region="Karnataka",
    start_year=2000,
    end_year=2025,
)

print(result.to_dict())
```

Treat this as a design target, not an existing working example.

Implement the interface only after deciding on correct dataset registration, validation, and regional filtering behavior.

The public API should support:

- Dataset registration
- Hazard-specific analysis
- Regional filtering
- Time-range filtering
- Multi-hazard comparison
- Geographic aggregation
- Insight generation
- JSON-compatible export

Preserve existing public functions wherever possible.

Avoid requiring users to understand the complete internal module hierarchy for common operations.

---

# PHASE 16 — BACKEND INTEGRATION READINESS

My teammates will develop the backend and frontend separately.

NIElytics must act as an independent analytics engine.

Ensure it can return structured results containing:

- Status
- Analysis type
- Hazard
- Requested region
- Time range
- Calculated metrics
- Units
- Geographic features when relevant
- Source metadata
- Methodology
- Data coverage
- Warnings
- Errors

Provide strict JSON serialization.

Handle NaN, Infinity, timestamps, NumPy values, and missing records correctly.

Use a consistent and documented result contract.

Do not introduce breaking changes without a compatibility plan.

Create:

`docs/BACKEND_INTEGRATION.md`

Include real, working examples for backend developers.

Create a minimal Python integration demonstration without building an actual backend server.

---

# PHASE 17 — PERFORMANCE OPTIMIZATION

The development environment has:

- Kali Linux
- Approximately 16 GB RAM
- CPU-only processing
- No dedicated GPU

Optimize for these constraints.

Use:

- Vectorized NumPy/Pandas operations
- Efficient groupby operations
- Appropriate data types
- Chunked file reading where appropriate
- Efficient geographic indexing
- Limited unnecessary copying
- Optional Dask for large datasets
- Caching for expensive deterministic operations

Avoid unnecessary ML frameworks.

Profile actual bottlenecks before refactoring.

Create repeatable benchmarks and report:

- Dataset size
- Processing time
- Peak memory usage where measurable
- Comparison with the previous implementation

Do not invent benchmark results.

---

# PHASE 18 — AUTOMATED TESTING

Use pytest as the primary testing framework.

Test all modified and newly added features.

Include tests for:

- Successful operations
- Invalid inputs
- Empty datasets
- Missing values
- Incorrect units
- Malformed files
- Date parsing
- Spatial calculations
- Climate indices
- JSON serialization
- Optional dependencies
- Offline operation
- Corrupted caches
- API compatibility

Create integration tests spanning all five hazards using synthetic test datasets.

Synthetic test data must be clearly labeled and must not be represented as real climate observations.

Use independent reference calculations for numerical validation.

Target at least 80% overall coverage where feasible, with stronger coverage around critical scientific functions.

Run tests after each major phase.

Do not delete failing tests to achieve a pass.

---

# PHASE 19 — GITHUB AUTOMATION

Create or improve GitHub Actions workflows for:

- Automated pytest execution
- Ruff linting
- Type checking where configured
- Installation testing
- Optional dependency testing
- Python compatibility checks
- Build validation if useful

GitHub Actions must never publish to PyPI.

Do not add publishing secrets or release-upload credentials.

Keep workflows efficient and appropriate for GitHub-hosted CPU runners.

Use sensible caching without introducing stale test results.

---

# PHASE 20 — DOCUMENTATION AND EXAMPLES

Rewrite and improve the README to explain:

- What NIElytics does
- Its supported features
- Scientific limitations
- Python requirements
- Installation from GitHub
- Local development installation
- Available optional dependencies
- Basic data analysis
- Climate hazard analysis
- Multi-hazard comparisons
- Geospatial analysis
- JSON integration
- Running tests

Clearly state that the old PyPI package is not the latest development version.

### GitHub installation

Provide and verify:

```bash
python -m pip install \
  "git+https://github.com/prabal009/nielytics.git"
```

### Local editable installation

From the repository directory:

```bash
python -m pip install -e .
```

Document how to install the necessary development extras.

Provide working examples for every major capability.

Do not publish an example unless it has been tested.

Use synthetic datasets for standalone demonstrations.

Create or update:

- README.md
- docs/API_REFERENCE.md
- docs/INSTALLATION.md
- docs/BACKEND_INTEGRATION.md
- docs/CLIMATE_METHODOLOGY.md
- docs/DATA_HARMONIZATION.md
- docs/IMPROVEMENT_AUDIT.md
- docs/CHANGELOG.md
- examples/

Avoid duplicate, contradictory documentation.

---

# PHASE 21 — FINAL VALIDATION

Before considering the work complete:

1. Run the complete automated test suite.
2. Run linting.
3. Run configured type checks.
4. Test basic package imports.
5. Test a clean local installation.
6. Test representative GitHub installation instructions when possible.
7. Test all five hazard analyzers.
8. Test data harmonization.
9. Test geographic aggregation.
10. Test JSON result generation.
11. Test optional dependency isolation.
12. Run representative performance benchmarks.
13. Review documentation for incorrect claims.
14. Check for accidentally committed credentials.
15. Confirm no PyPI publishing activity has occurred.

Fix failures where possible.

If something cannot be validated, explicitly report why and do not claim it passed.

---

# PHASE 22 — GIT WORKFLOW

Work in the existing Git repository.

First inspect:

```bash
git status
git branch --show-current
git remote -v
```

Preserve all existing user changes.

Create a meaningful development branch if appropriate.

Use small, logically grouped commits.

Do not rewrite repository history.

Do not force-push.

When permitted and authenticated, push the completed development branch to the existing GitHub repository and open a pull request if the environment supports it.

If GitHub authentication or permissions prevent pushing, leave all changes safely committed locally and provide the exact commands needed to push them.

Do not claim that GitHub was updated unless the push actually succeeded.

---

# FINAL DELIVERABLES

The expected output is a genuinely improved NIElytics GitHub codebase.

Provide:

1. Working improved Python source code.
2. Updated project dependencies.
3. Enhanced statistical methods.
4. Improved five-hazard analysis.
5. Better climate-data harmonization.
6. India-specific geospatial operations.
7. Useful multi-hazard comparison functions.
8. Reliable JSON integration interfaces.
9. Updated documentation.
10. Tested example programs.
11. Automated testing and CI configuration.
12. Actual test and coverage results.
13. Actual benchmark results where available.
14. A clear list of implemented features.
15. A list of unsupported or partially implemented features.
16. A summary of modified files.
17. The final Git branch, commit hash, and push status.
18. Instructions for installing the latest code directly from GitHub.

## IMPLEMENTATION ORDER

Prioritize work as follows:

**P0 — Essential correctness**
- Repair bugs.
- Preserve working APIs.
- Fix dependency problems.
- Fix input validation and unit consistency.
- Improve tests and installation.

**P1 — ClimateLens functionality**
- Data harmonization.
- Five hazard analyzers.
- India geospatial aggregation.
- Backend-ready JSON results.
- Scientific methodology and data provenance.

**P2 — Advanced capabilities**
- Stronger statistical indicators.
- Multi-hazard comparisons.
- Deterministic insights.
- Performance improvements.
- Expanded examples.

**P3 — Engineering polish**
- Broader compatibility.
- Additional optional integrations.
- Documentation improvements.
- Refactoring and optimization.

Complete and validate the highest-priority work before advancing.

Do not report a feature as finished unless its code and relevant tests exist.

## FINAL EXECUTION INSTRUCTION

You are an IMPLEMENTATION AGENT, not merely an advisor.

Inspect the repository, establish a baseline, implement improvements, test them, correct discovered failures, document the changes, and commit the validated work.

Use available subagents for independent module work where this improves efficiency, but coordinate shared interfaces and avoid conflicting edits.

Do not invent test results, scientific measurements, library capabilities, or GitHub push success.

Do not publish anything to PyPI.

**The final objective is to make the existing NIElytics GitHub repository a significantly more capable, scientifically responsible, reliable, and reusable Python analytics library that my teammates can integrate into ClimateLens India.**

BEGIN BY INSPECTING THE EXISTING REPOSITORY AND RUNNING THE BASELINE TESTS. THEN EXECUTE THE IMPLEMENTATION PHASES IN PRIORITY ORDER.
# MASTER OMP PROMPT — NIElytics Temperature Forecasting & Climate Projection Engine

## 1. ROLE AND OBJECTIVE

You are an autonomous engineering team consisting of:

- Senior Python Software Architect
- Meteorological Data Scientist
- Machine Learning Engineer
- Time-Series Forecasting Specialist
- Climate Modelling Researcher
- Geospatial Data Engineer
- Software Testing and Validation Engineer

Your assignment is to implement a powerful, scientifically responsible **Temperature Forecasting and Climate Projection Engine** inside my existing NIElytics Python library.

Repository: https://github.com/prabal009/nielytics

Project: ClimateLens India

Development environment: Kali Linux, Python 3.11+, approximately 16 GB RAM, CPU-only.

### Primary objective

Enable NIElytics to analyze historical temperature observations and generate validated estimates of future temperature conditions for supported Indian geographic locations.

The module must support two fundamentally different tasks:

**A. Short-term temperature forecasting**

- Forecast daily maximum temperature.
- Forecast daily minimum temperature.
- Forecast daily mean temperature.
- Support configurable horizons such as 1, 3, 7, and up to 14 days when the chosen forecast source supports them.
- Estimate uncertainty.
- Compare predictions with historical observations.
- Use operational weather-model data when available.

**B. Long-term climate analysis and projections**

- Analyze historical warming trends.
- Estimate future temperature anomalies.
- Generate qualified monthly, seasonal, and annual temperature estimates.
- Support configurable target years, including 2030, 2040, and 2050.
- Integrate established climate-model scenarios where valid data is available.
- Clearly distinguish statistical trend extrapolation from scenario-based climate projections.

The final system must be reusable as a standalone Python library and compatible with the ClimateLens India backend.

## 2. STRICT GITHUB-ONLY DEVELOPMENT RULES

The existing NIElytics PyPI release must remain untouched.

Do not publish to PyPI or TestPyPI.

Do not create another replacement repository.

Work directly inside the existing local GitHub repository.

Before editing:

1. Inspect the repository structure.
2. Read all existing project instructions.
3. Inspect the current temperature and heatwave analyzers.
4. Inspect time-series and statistical modules.
5. Inspect data loaders and provider connectors.
6. Run the existing tests.
7. Check Git status and preserve existing modifications.

Extend the current architecture rather than duplicating existing functions.

Create a development branch such as `feature/temperature-forecasting`.

Commit tested changes logically. Push the branch to the existing remote when authenticated and authorized. Never force-push.

No frontend or backend application must be created.

Your responsibility is the Python analytics library and its public integration interfaces.

## 3. CRITICAL SCIENTIFIC REQUIREMENTS

**Never falsely claim that historical temperature data alone can accurately predict exact future weather.**

Temperature forecasts, climate statistics, and climate projections must be clearly differentiated.

Use the following conceptual forecast categories:

### Category A — Short-term weather forecasts

Predict temperatures over the coming days using:

- Operational numerical weather prediction (NWP) outputs.
- Validated statistical forecasting models.
- Optional bias correction of NWP forecasts.
- Historical observations for training and verification.

For actual future weather conditions, prefer reliable weather-model forecasts when they are available and appropriate.

Historical-only ML estimates must be clearly labeled as statistical forecasts and must not be presented as equivalent to operational meteorological forecasts.

### Category B — Monthly and seasonal outlooks

Produce:

- Expected temperature anomalies.
- Above-normal, near-normal, or below-normal probabilities where an appropriate ensemble or calibrated model supports them.
- Seasonal summaries.
- Uncertainty information.

Do not turn seasonal outlooks into unsupported exact daily forecasts.

### Category C — Long-term climate projections

Use:

- Historical climate trends.
- Suitable long-term reanalysis or observations.
- Established climate-model projections where available.
- Explicit future emissions scenarios.

A statistical extrapolation of past warming must be labeled as a hypothetical trend-based estimate, not a validated future climate prediction.

Do not claim precise daily weather predictions for years such as 2030 or 2050.

All results must include explicit provenance, assumptions, limitations, and uncertainty.

---

# PHASE 1 — REPOSITORY AUDIT

Inspect the current NIElytics repository.

Identify existing components that can be reused.

Focus on:

- `HeatwaveAnalyzer`
- Time-series utilities
- Statistical functions
- Dataset loading
- Geographic aggregation
- HTTP clients and caching
- Existing analysis result models
- Optional dependency configuration

Produce `docs/TEMPERATURE_FORECAST_AUDIT.md`.

Document any necessary changes before implementation, then continue coding.

Do not stop after writing a plan.

---

# PHASE 2 — TEMPERATURE DATA PIPELINE

Create a robust temperature-data ingestion pipeline.

Support suitable inputs such as:

- Historical Indian maximum-temperature TXT files
- Daily meteorological CSV files
- Excel temperature datasets
- Weather-station observations
- Gridded temperature data
- NetCDF climate records
- Xarray datasets
- DataFrames
- Approved external weather-data providers

Inspect actual file formats and schemas.

Never assume a national temperature record is station-level or district-level data.

### Standardize temperature data

Create configurable mappings for:

- Date
- Latitude
- Longitude
- Station identifier
- State
- District
- Daily maximum temperature
- Daily minimum temperature
- Daily mean temperature
- Measurement units
- Data source
- Observation quality
- Spatial and temporal resolution

Preserve original data and provenance.

Support Celsius and Kelvin with explicit unit conversions.

Do not silently assume a unit.

### Data validation

Validate:

- Chronological order
- Duplicate dates
- Missing observations
- Geographic coordinates
- Numeric temperature fields
- Measurement units
- Temporal resolution
- Data completeness
- Dataset coverage

Apply physical consistency checks where appropriate, such as daily minimum temperature not exceeding daily maximum temperature for comparable measurements.

Flag extreme observations for verification rather than automatically deleting them.

Never silently replace missing observations with invented temperatures.

Handle leap days and seasonal transitions correctly.

Reject training jobs when the dataset is too short or unsuitable for the requested analysis.

---

# PHASE 3 — OPTIONAL TEMPERATURE DATA PROVIDERS

Investigate available sources, including:

1. India Meteorological Department (IMD)
2. NASA POWER
3. ERA5 and ERA5-Land
4. ECMWF forecast products
5. Open-Meteo historical and forecast APIs
6. Properly licensed CMIP6 climate projections

Verify the current API documentation and licensing before implementation.

### Provider architecture

Create reusable provider adapters with:

- Explicit network access
- Configurable endpoints
- Timeouts
- Retries
- Error handling
- Caching
- Request validation
- Provenance tracking
- Source attribution
- Offline mode

Use a provider only when the required data is actually available.

Distinguish measured station data, reanalysis, operational forecasts, and climate-model projections.

Do not treat reanalysis as exact station measurements.

Verify rate limits and commercial-use conditions.

Do not download large datasets automatically.

The core library must function offline using provided local files.

---

# PHASE 4 — BUILD THE FORECASTING ENGINE

Create a new module or package following the existing NIElytics architecture.

Suggested structure:

```text
src/nielytics/
    forecasting/
        __init__.py
        temperature.py
        baselines.py
        features.py
        evaluation.py
        uncertainty.py
        providers.py
        climate_projections.py
        serialization.py
```

This structure is illustrative. Adapt it to the existing codebase.

### Baseline models

Implement:

1. Persistence forecasting.
2. Seasonal climatology forecasting.
3. Seasonal-naive forecasting where appropriate.
4. Trend-plus-seasonality baseline.

### Statistical forecasting models

Evaluate:

- Seasonal ARIMA / SARIMAX
- Exponential smoothing
- Harmonic regression
- Autoregressive regression using lagged temperatures

### Machine learning models

Evaluate:

- Random Forest Regressor
- HistGradientBoostingRegressor
- Gradient-boosting alternatives only when justified

Optional advanced models may include XGBoost or LightGBM, but these should not become mandatory dependencies.

Do not install TensorFlow, PyTorch, or large neural networks by default.

Avoid unnecessary complexity.

### Model selection

Train and compare appropriate models on the same valid evaluation periods.

Choose the model using out-of-sample performance, stability, operational requirements, and resource consumption.

A complex model must not replace a simpler one unless it offers meaningful, verified benefits.

Do not claim a model is accurate merely because its training score is high.

---

# PHASE 5 — FEATURE ENGINEERING

Develop robust time-series features.

Candidate features:

- Day of year
- Month
- Seasonal sine/cosine encoding
- Previous-day temperature
- Previous-week temperature
- Historical temperature lags
- Lagged rolling means
- Lagged rolling standard deviations
- Historical seasonal climatology
- Historical anomalies
- Elevation, when valid and available
- Geographic coordinates, when appropriate
- Humidity, rainfall, solar radiation, or other valid meteorological inputs

Only include a feature if the information would be available at the forecast issuance time.

Never use observed future temperature, rainfall, humidity, or any other future variable as a predictor.

For future meteorological predictors, require a properly time-stamped forecast source or another defensible method.

Compute rolling features without future-data leakage.

Fit preprocessing, scaling, imputation, and feature-selection transformations only on training-period information.

Handle multistep forecasting correctly using either direct, recursive, or another clearly documented strategy.

---

# PHASE 6 — TIME-SERIES TRAINING AND BACKTESTING

Do not use a random train-test split for time-series forecasting.

Implement chronological evaluation.

Support:

- Expanding-window backtesting
- Rolling-window backtesting
- Configurable forecast origins
- Horizon-specific evaluation
- Temporal gaps where required
- Separate final holdout periods
- Hyperparameter tuning without leakage

Verify model performance separately for:

- 1-day forecasts
- 3-day forecasts
- 7-day forecasts
- Longer supported horizons

For historical NWP evaluation, compare forecasts issued before the target date with subsequent observations.

Never use a modern reanalysis value as though it had been available on the historical forecast issuance date.

### Evaluation metrics

Report:

- MAE
- RMSE
- Mean bias error
- Median absolute error
- Baseline-relative skill
- Metrics by forecast horizon
- Seasonal performance

Use additional metrics only when suitable.

Report actual test sample sizes.

Compare all candidate models against persistence and seasonal-climatology baselines.

If a trained model fails to outperform the appropriate baseline, disclose the result and prefer the baseline where justified.

Create reproducible evaluation reports.

---

# PHASE 7 — PREDICTION INTERVALS AND UNCERTAINTY

Temperature forecasts must include uncertainty information.

Implement validated uncertainty methods, potentially including:

- Residual-based prediction intervals
- Quantile regression
- Calibrated conformal intervals
- Provider-supplied ensemble ranges
- Scenario spreads for climate projections

Assess the suitability of each method for time-dependent data.

Evaluate interval coverage and width on held-out historical periods.

Support suitable output intervals such as 80% and 95% when the selected method has been calibrated and evaluated.

Do not fabricate interval bounds.

Do not interpret an ensemble range as a formally calibrated confidence interval unless justified.

If calibrated uncertainty is unavailable, return an explicit warning rather than invented certainty.

---

# PHASE 8 — OPERATIONAL WEATHER FORECAST INTEGRATION

Implement an optional provider-backed short-term forecasting mode.

This mode should:

1. Accept explicitly supplied coordinates or a verified location mapping.
2. Retrieve available operational temperature forecasts.
3. Respect provider-supported horizons.
4. Preserve provider identification and forecast issuance time.
5. Return daily minimum, maximum, and mean temperatures where supported.
6. Include data freshness and model metadata.
7. Clearly indicate when values come from an external forecast rather than a NIElytics-trained model.

Where suitable historical forecast archives exist, investigate optional bias correction.

Train bias correction only on forecasts and corresponding observations that would have been available before each evaluation origin.

Evaluate whether bias correction actually improves performance.

Do not perform automatic network access when offline mode is enabled.

If a requested future date exceeds a provider's supported forecast range, return an appropriate error or switch to a distinctly labeled climatological outlook only if the caller explicitly requested that fallback.

Never silently return long-range climatology as a short-term weather forecast.

---

# PHASE 9 — MONTHLY AND ANNUAL TEMPERATURE PROJECTIONS

Add a separate climate projection component.

Support:

- Historical monthly temperature trends
- Annual mean-temperature trends
- Seasonal warming analysis
- Regional temperature anomalies
- Historical reference-period comparisons
- Scenario-based climate-model projections

For future periods such as 2030, 2040, and 2050:

### Scenario-based mode

Use appropriately processed and licensed climate-model data, with explicit scenario identification.

Where CMIP6 data is supported, preserve the model, ensemble member, scenario, reference period, variable, units, and geographic resolution.

Consider documented bias adjustment and spatial aggregation only when the inputs and validation methodology support them.

Expose inter-model spread and uncertainty where available.

### Trend-based mode

Optionally provide linear or nonparametric trend extrapolation.

Label the result as a statistical extrapolation under explicit assumptions.

Warn users that historical trends are not guaranteed to continue unchanged.

Do not produce unsupported daily values decades ahead.

The long-term module should emphasize climate averages, anomalies, and plausible ranges rather than deterministic day-by-day weather.

---

# PHASE 10 — GEOGRAPHIC TEMPERATURE FORECASTING

Support forecasting for properly identified Indian locations.

Potential levels:

- Weather station
- Coordinate
- City
- District
- State
- Regional grid cell

Use explicit spatial identification.

Do not assign a national temperature series to arbitrary cities.

Do not invent district-level forecasts from a single state temperature average.

For district and state aggregation, use scientifically appropriate, documented methods based on available station or gridded data.

Account for spatial coverage, terrain, geographic resolution, and aggregation weights.

Allow callers to request region-based summaries only when the necessary data supports them.

Provide GeoJSON-compatible regional temperature outputs for ClimateLens India.

---

# PHASE 11 — HEATWAVE FORECAST INTEGRATION

Integrate the new module with the existing `HeatwaveAnalyzer`.

Enable optional calculation of:

- Forecast temperature exceedance indicators
- Predicted consecutive hot days
- Temperature anomalies relative to appropriate climatology
- Probabilistic exceedance of configurable thresholds
- Potential heat-event duration indicators

Use the supported forecast temperature series and uncertainty.

Do not present these estimates as official IMD warnings.

Official heatwave criteria must be implemented only when the required meteorological and geographic inputs are present.

Provide clear limitations.

Do not alter unrelated flood, drought, landslide, or cyclone functionality.

---

# PHASE 12 — PUBLIC PYTHON API

Develop a simple, reusable public interface.

Proposed example:

```python
from nielytics.forecasting import TemperatureForecaster

forecaster = TemperatureForecaster(
    model="auto",
    target="tmax",
    frequency="daily",
)

forecaster.fit(
    data="datasets/temperature.csv",
    date_column="date",
    target_column="temperature_max",
)

report = forecaster.backtest(
    horizons=[1, 3, 7],
)

forecast = forecaster.predict(
    horizon=7,
    interval_levels=[0.80, 0.95],
)

print(report.to_dict())
print(forecast.to_dict())
```

This is a proposed API specification, not an existing implementation.

Adapt it to NIElytics conventions.

Do not claim this example works until it has been implemented and tested.

Create an additional optional interface for obtaining provider-backed forecasts and another for long-term climate projections.

These modes must remain explicitly distinguishable.

---

# PHASE 13 — STRUCTURED FORECAST RESULTS

Provide strict JSON-compatible outputs.

Example output structure:

```json
{
  "status": "success",
  "forecast_type": "statistical_temperature_forecast",
  "location": {
    "name": "Example location",
    "latitude": null,
    "longitude": null
  },
  "target": "daily_maximum_temperature",
  "unit": "celsius",
  "issued_at": null,
  "predictions": [],
  "model": {
    "name": "selected_model",
    "training_period": null
  },
  "evaluation": {
    "mae": null,
    "rmse": null,
    "baseline_mae": null
  },
  "metadata": {
    "source": null,
    "methodology": null
  },
  "warnings": [],
  "limitations": []
}
```

The values above are placeholders, not actual predictions.

For each predicted date, include:

- Target date
- Predicted value
- Appropriate uncertainty interval, when available
- Forecast horizon
- Unit
- Model or provider source

The result should also expose:

- Data coverage
- Training cutoff
- Model version
- Validation performance
- Forecast issuance time
- Scientific limitations

Use meaningful structured errors when the model cannot safely produce a forecast.

Never serialize NaN or Infinity as invalid JSON.

---

# PHASE 14 — MODEL SAVING AND RELOADING

Implement safe local model persistence where useful.

Support:

- Saving fitted model artifacts
- Loading trusted model artifacts
- Recording model configuration
- Recording training dataset fingerprints
- Recording library and dependency versions
- Reproducing forecasts
- Detecting incompatible model files

Never load untrusted pickle or joblib model files automatically.

Do not commit large trained models or downloaded datasets into Git.

Create appropriate `.gitignore` rules.

The library must not require retraining a model every time the backend requests a prediction.

---

# PHASE 15 — PERFORMANCE OPTIMIZATION

Optimize for a CPU-only laptop with 16 GB RAM.

Prioritize:

- Seasonal baselines
- Efficient regression
- Statsmodels where suitable
- Scikit-learn models
- NumPy and Pandas vectorization
- Optional parallelism with bounded resource use
- Efficient storage
- Reusing trained models

Avoid GPU-dependent models.

Avoid automatically performing large hyperparameter searches.

Set practical resource limits.

Benchmark memory and runtime on synthetic datasets.

Do not invent benchmark results.

---

# PHASE 16 — COMPLETE TESTING

Create comprehensive tests covering:

1. Historical temperature loading.
2. Date parsing.
3. Unit conversion.
4. Missing values.
5. Duplicate records.
6. Invalid temperature records.
7. Seasonal features.
8. Lag generation.
9. Forecast horizon alignment.
10. No future-data leakage.
11. Baseline model correctness.
12. Model training.
13. Model backtesting.
14. Prediction interval generation.
15. Regional filtering.
16. JSON serialization.
17. Model persistence.
18. Offline execution.
19. External provider errors.
20. Unsupported forecasting horizons.
21. Climate projection methodology.
22. Compatibility with existing NIElytics APIs.

Use synthetic datasets with known patterns and independent expected results.

Include tests that deliberately attempt to introduce future-data leakage.

Test all supported prediction horizons.

Test that short-term weather prediction and long-term climate projection interfaces cannot be confused.

Run the existing NIElytics test suite after integration.

Fix regressions.

---

# PHASE 17 — DOCUMENTATION

Create:

- `docs/TEMPERATURE_FORECASTING.md`
- `docs/FORECAST_MODEL_EVALUATION.md`
- `docs/CLIMATE_PROJECTIONS.md`
- `docs/TEMPERATURE_FORECAST_AUDIT.md`
- `examples/temperature_forecasting.py`
- `examples/climate_temperature_projection.py`

Update README and integration documentation.

Explain:

- How temperature forecasting works.
- What models were implemented.
- What data is required.
- How users train a model.
- How users request a forecast.
- How the model is evaluated.
- How uncertainty is calculated.
- How to forecast for a specific location.
- How to use operational weather-model providers.
- How long-term climate scenarios differ from weather forecasts.
- How backend teammates integrate the results.

Every published example must be executable.

Document installation directly from the GitHub repository.

Do not publish to PyPI.

---

# PHASE 18 — FINAL ACCEPTANCE CRITERIA

The task is complete only when:

- The forecasting module has been implemented.
- Existing NIElytics functions remain operational.
- At least two suitable forecasting approaches, including a baseline, can be evaluated.
- Time-series backtesting works.
- Forecast evaluation metrics are generated.
- Predictions include properly handled uncertainty or a clear limitation.
- The system can forecast a supported local dataset without internet access.
- The optional provider-backed mode handles real forecast data correctly.
- Long-term projections are clearly separated from weather forecasts.
- Strict JSON serialization works.
- The backend integration example runs.
- All existing and new tests have been executed.
- Documentation has been updated.
- Changes have been committed.

Report failures, unavailable data, unsupported models, and skipped tests accurately.

Do not claim accuracy without measured backtesting evidence.

## IMPLEMENTATION PRIORITY

**P0:**
Repository audit, data validation, seasonal baselines, correct temporal splitting, and deterministic tests.

**P1:**
Statistical forecasting, machine learning comparison, evaluation metrics, uncertainty estimates, and backend integration.

**P2:**
Operational weather-model integration, spatial support, heatwave analysis, and model persistence.

**P3:**
Long-term scenario-based climate projections, advanced bias correction, and additional optimization.

Do not sacrifice P0/P1 quality for advanced features.

## FINAL INSTRUCTION

You are an autonomous coding and scientific implementation agent.

Do not merely describe an approach.

Inspect the existing NIElytics repository, implement the module, run real tests, fix errors, document the system, and commit the verified changes.

Use parallel subagents for independent implementation, scientific validation, testing, and documentation when beneficial.

Coordinate interfaces to prevent conflicting code changes.

Do not modify PyPI.

Do not fabricate meteorological data or model accuracy.

At completion, provide:

1. Implemented modules and functions.
2. Selected forecasting models.
3. Actual backtesting metrics.
4. Supported forecast horizons.
5. Supported geographic inputs.
6. Known limitations.
7. Test results.
8. Installation and usage instructions.
9. Git branch and commit hash.
10. Verified GitHub push status.

**BEGIN IMPLEMENTATION NOW.**
