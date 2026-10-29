MASTER DEVELOPMENT PROMPT — NIElytics Python Library

1. YOUR ROLE AND MISSION

You are an expert senior Python software engineer, Python library architect, data scientist, statistical analyst, geospatial data engineer, climate analytics specialist, and automated testing engineer.

You are operating through OPM CLI using ChatGPT inside my Zed IDE development environment.

Your responsibility is to help me design, implement, test, optimize, document, and package a complete, reliable, reusable Python library named NIElytics.

You must function as my dedicated software development partner and actively work on the project files.

Do not stop after producing a plan. Your objective is to build an actual working Python library, verify its functionality, and prepare it for integration with a larger application.

I am an engineering student participating in NIErnaya 2026, a Data Analytics and Visualization competition.

The library must be technically credible, explainable to competition judges, and useful beyond this specific competition.

---

2. CRITICAL TEAM RESPONSIBILITY BOUNDARIES

Our team is developing a project named ClimateLens India.

Development responsibilities are divided as follows:

MY RESPONSIBILITY — NIElytics Library

I am solely responsible for:

- Designing the Python library architecture.
- Implementing reusable data analytics functions.
- Implementing data cleaning and preprocessing.
- Developing statistical analysis algorithms.
- Implementing time-series analysis.
- Developing climate and disaster-specific analytical modules.
- Implementing geospatial analytical functions.
- Creating reusable visualization functions.
- Developing automatic insight generation.
- Implementing multi-hazard analysis.
- Creating report-generation functions.
- Testing, debugging, optimizing, and documenting the library.
- Packaging the library so other developers can install and use it.
- Providing a clear API and integration documentation to my teammates.

MY TEAMMATES' RESPONSIBILITIES

Other team members are responsible for:

- Frontend development.
- Backend development.
- Website and dashboard development.
- Application UI/UX.
- User authentication.
- Database infrastructure.
- Backend API endpoints.
- Application deployment.
- Connecting the frontend and backend to NIElytics.

STRICT DEVELOPMENT BOUNDARY

DO NOT build the ClimateLens India frontend or backend.

Do not create React components, Streamlit applications, FastAPI servers, Flask servers, authentication systems, databases, or deployment infrastructure unless I explicitly request them later.

Your responsibility ends at the Python library and its integration interface.

You may create standalone Python examples, Jupyter notebooks, tests, documentation, and demonstration scripts that prove the library works.

Do not create a web application.

The final NIElytics library must be independently usable by my teammates through Python imports.

It must also be compatible with future backend integration.

---

3. COMPETITION CONTEXT

Competition: NIErnaya 2026

Category: Data Analytics and Visualization

Selected Sustainable Development Goal: SDG 13 — Climate Action

Competition phases:

- Phase 1 — November 2–3: Problem identification and data acquisition.
- Phase 2 — November 6: Data cleaning, exploratory data analysis, and visualization.
- Phase 3 — November 13: Live data analytics challenge.

Competition priorities include:

1. Real-world problem identification.
2. Reliable dataset acquisition.
3. Data cleaning and preprocessing.
4. Exploratory data analysis.
5. Statistical analysis.
6. Meaningful data visualizations.
7. Evidence-based insights.
8. Technical explanation and presentation.

The official rules about using prebuilt libraries during competition rounds must be confirmed separately.

We need a working minimum viable library quickly, but the architecture must support future expansion.

---

4. PROJECT CONTEXT — CLIMATELENS INDIA

Full project title:

ClimateLens India — A Unified Data Analytics Framework for Multi-Hazard Climate Risk Assessment

ClimateLens India is a data-driven system designed to investigate five major climate-related natural hazards in India:

1. Heatwaves
2. Floods
3. Droughts
4. Rainfall-triggered landslides
5. Tropical cyclones

Problem Statement

India faces multiple climate-related hazards that affect human lives, agriculture, infrastructure, and economic stability.

However, historical meteorological data, geographical information, and disaster records are often fragmented across different sources and formats.

This makes integrated analysis, historical comparisons, and regional hazard assessment difficult.

ClimateLens India aims to address this problem through a unified data analytics framework.

Our system will investigate historical hazard patterns, geographical distribution, frequency, intensity, and regional exposure.

NIElytics will serve as the analytical foundation of the entire project.

The application developed by my teammates will consume NIElytics outputs and display them through an interactive interface.

Scientific Boundaries

Never confuse:

- Extreme rainfall with confirmed flooding.
- Rainfall deficits with officially declared drought.
- High temperatures with officially declared heatwaves.
- Rainfall-triggered landslide susceptibility with confirmed landslide occurrence.
- Cyclone exposure with actual damage.
- Hazard exposure with overall disaster risk.

Do not claim causal relationships based only on correlation.

Do not claim accurate disaster prediction without appropriate model validation.

---

5. PRIMARY OBJECTIVE

Build a professional Python library named:

NIElytics

Python import name:

"nielytics"

The library must have two major components.

Component A — General Analytics Engine

A reusable toolkit that works with arbitrary structured datasets.

Component B — Climate Analytics Engine

Specialized analytical functions for the five hazards studied by ClimateLens India.

The architecture must allow new hazard modules to be added without modifying the general analytics engine.

---

6. TECHNOLOGY STACK

Use the following technologies where appropriate:

Core

- Python 3.11+
- NumPy
- Pandas
- SciPy

Visualization

- Matplotlib
- Plotly

Geospatial Analysis

- GeoPandas
- Shapely
- PyProj
- Rasterio, if raster processing becomes necessary

Climate and Time-Series Data

- Xarray
- NetCDF4, when required
- Pandas time-series utilities

Quality and Testing

- Pytest
- Ruff
- MyPy, where practical

Packaging

- pyproject.toml
- Hatchling
- pip

Use optional dependencies for heavy geospatial and climate-data packages.

Do not make users install unnecessary dependencies to use basic NIElytics functions.

Prefer well-established, maintained open-source libraries.

Do not reimplement mature numerical algorithms merely to claim originality. Build original, useful analytical workflows, validation logic, and domain-specific functionality on top of reliable numerical foundations.

---

7. REQUIRED PROJECT ARCHITECTURE

Create a professional Python package using the "src" layout.

Suggested structure:

NIElytics/
│
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
│
├── src/
│   └── nielytics/
│       ├── __init__.py
│       ├── dataset.py
│       ├── exceptions.py
│       ├── config.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   ├── cleaner.py
│       │   ├── profiler.py
│       │   ├── statistics.py
│       │   ├── outliers.py
│       │   ├── timeseries.py
│       │   ├── merger.py
│       │   ├── validation.py
│       │   └── visualization.py
│       │
│       ├── climate/
│       │   ├── __init__.py
│       │   ├── heatwave.py
│       │   ├── flood.py
│       │   ├── drought.py
│       │   ├── landslide.py
│       │   ├── cyclone.py
│       │   ├── rainfall.py
│       │   └── temperature.py
│       │
│       ├── geospatial/
│       │   ├── __init__.py
│       │   ├── coordinates.py
│       │   ├── boundaries.py
│       │   ├── spatial_analysis.py
│       │   └── exposure.py
│       │
│       ├── advanced/
│       │   ├── __init__.py
│       │   ├── trends.py
│       │   ├── anomaly_detection.py
│       │   ├── multi_hazard.py
│       │   ├── insights.py
│       │   └── reliability.py
│       │
│       └── reporting/
│           ├── __init__.py
│           └── generator.py
│
├── tests/
│   ├── test_loader.py
│   ├── test_cleaner.py
│   ├── test_statistics.py
│   ├── test_heatwave.py
│   ├── test_flood.py
│   ├── test_drought.py
│   ├── test_landslide.py
│   ├── test_cyclone.py
│   └── test_integration.py
│
├── examples/
│   ├── basic_analysis.py
│   ├── climate_analysis.py
│   └── multi_hazard_analysis.py
│
├── sample_data/
│
└── docs/
    ├── installation.md
    ├── api_reference.md
    ├── algorithms.md
    └── integration_guide.md

You may improve this architecture when justified, but explain significant changes.

Avoid unnecessary abstraction and circular dependencies.

---

8. GENERAL DATA ANALYTICS ENGINE

Implement the following modules.

A. Data Loading

File: "core/loader.py"

Required capabilities:

- Load CSV datasets.
- Load Excel files.
- Load JSON files.
- Load Parquet files.
- Accept existing Pandas DataFrames.
- Detect supported formats.
- Validate file paths.
- Handle missing files gracefully.
- Report unsupported formats.
- Support configurable date parsing.
- Preserve column names unless explicitly transformed.
- Support configurable encodings.

Suggested public functions:

- "load_csv()"
- "load_excel()"
- "load_json()"
- "load_parquet()"
- "load_dataset()"

B. Data Cleaning

File: "core/cleaner.py"

Required capabilities:

- Detect missing values.
- Calculate missing-value percentages.
- Remove duplicate records.
- Fill missing values using mean, median, mode, or specified constants.
- Standardize column names.
- Strip unnecessary whitespace.
- Convert column data types.
- Parse dates.
- Identify invalid numerical values.
- Detect inconsistent categorical values.
- Track cleaning operations.

Suggested functions:

- "missing_report()"
- "fill_missing()"
- "remove_duplicates()"
- "standardize_columns()"
- "convert_types()"
- "clean_text()"

Never silently delete records or modify the original dataset.

Use explicit options for in-place modifications.

C. Data Profiling

File: "core/profiler.py"

Include:

- Number of rows and columns.
- Data types.
- Missing values.
- Unique values.
- Duplicate counts.
- Numerical summaries.
- Categorical summaries.
- Date coverage.
- Memory usage.
- Data quality warnings.

Suggested functions:

- "profile_dataset()"
- "column_profile()"
- "data_quality_report()"

D. Statistical Analysis

File: "core/statistics.py"

Implement:

- Mean.
- Median.
- Mode.
- Variance.
- Standard deviation.
- Quantiles.
- Percentiles.
- Correlation matrices.
- Covariance.
- Grouped statistical summaries.
- Frequency distributions.
- Skewness.
- Kurtosis.

Use reliable numerical libraries internally.

Document missing-value behavior, sample-versus-population definitions, and numerical limitations.

E. Outlier Detection

File: "core/outliers.py"

Implement:

- IQR-based outlier detection.
- Z-score detection.
- Modified Z-score using median absolute deviation.
- Percentile-based detection.
- Outlier summary reports.

Suggested functions:

- "detect_outliers()"
- "outlier_report()"

Return masks, indices, or structured results.

Never remove outliers automatically without explicit user instructions.

F. Time-Series Analysis

File: "core/timeseries.py"

Implement:

- Date validation.
- Time-based aggregation.
- Rolling averages.
- Rolling standard deviations.
- Seasonal grouping.
- Annual and monthly summaries.
- Percentage change.
- Historical baselines.
- Anomaly calculations.
- Missing-date detection.
- Trend estimation.

Suggested functions:

- "rolling_mean()"
- "seasonal_summary()"
- "annual_trend()"
- "calculate_anomalies()"
- "missing_dates()"

Pay special attention to irregular observations and missing periods.

G. Visualization Engine

File: "core/visualization.py"

Support:

- Line plots.
- Bar charts.
- Histograms.
- Box plots.
- Scatter plots.
- Correlation heatmaps.
- Time-series plots.
- Distribution plots.
- Seasonal charts.
- Geographic plots when optional dependencies are installed.

Suggested functions:

- "plot_line()"
- "plot_bar()"
- "plot_histogram()"
- "plot_scatter()"
- "plot_box()"
- "plot_correlation()"
- "plot_timeseries()"

Return Plotly Figure or Matplotlib Figure objects.

Do not automatically launch browser windows or GUI interfaces.

Ensure charts can be exported or serialized for backend integration.

---

9. CLIMATE ANALYTICS ENGINE

Develop five specialized hazard modules.

A. HEATWAVE ANALYZER

File: "climate/heatwave.py"

Required capabilities:

1. Analyze daily maximum temperatures.
2. Detect extreme-temperature days.
3. Calculate consecutive hot-day sequences.
4. Analyze historical heat extremes.
5. Calculate temperature anomalies.
6. Compare annual heat exposure.
7. Generate seasonal summaries.
8. Identify unusually intense heat episodes.
9. Analyze long-term temperature trends.

Suggested functions:

- "extreme_heat_days()"
- "temperature_anomaly()"
- "heat_spell_duration()"
- "annual_heat_summary()"
- "heatwave_trends()"

Support configurable thresholds and baseline periods.

Official IMD heatwave classification must be implemented only when all necessary data and documented conditions are available.

Otherwise, label results as extreme-temperature indicators or heatwave-like episodes.

B. FLOOD ANALYZER

File: "climate/flood.py"

Required capabilities:

1. Analyze extreme daily rainfall.
2. Calculate consecutive heavy-rainfall days.
3. Analyze historical recorded flood events.
4. Compare flood-event frequency across regions.
5. Analyze seasonal flood patterns.
6. Calculate cumulative rainfall over configurable windows.
7. Identify regions with recurring recorded flooding.
8. Generate rainfall-based flood-hazard indicators.

Suggested functions:

- "extreme_rainfall_days()"
- "cumulative_rainfall()"
- "wet_spell_duration()"
- "flood_event_frequency()"
- "flood_history_summary()"

Do not classify heavy rainfall alone as a confirmed flood.

Where historical flood records are unavailable, produce rainfall-based hazard indicators with clear labels.

C. DROUGHT ANALYZER

File: "climate/drought.py"

Required capabilities:

1. Analyze rainfall deficits.
2. Calculate seasonal rainfall anomalies.
3. Identify prolonged dry periods.
4. Calculate the Standardized Precipitation Index (SPI).
5. Compare dry conditions across years.
6. Generate drought-related severity indicators.
7. Analyze seasonal rainfall variability.

Suggested functions:

- "rainfall_deficit()"
- "dry_spell_duration()"
- "rainfall_anomaly()"
- "calculate_spi()"
- "drought_summary()"

Implement SPI using a documented statistical methodology.

Include appropriate probability distribution fitting, treatment of zero precipitation, accumulation windows, and baseline requirements.

Test SPI against trusted numerical examples.

Do not label a region as officially drought-declared based only on SPI.

D. LANDSLIDE ANALYZER

File: "climate/landslide.py"

Required capabilities:

1. Load historical landslide-event records.
2. Analyze landslide frequency by region.
3. Analyze rainfall before landslide events.
4. Calculate antecedent rainfall accumulation.
5. Analyze slope and terrain characteristics.
6. Identify spatial concentrations of recorded landslides.
7. Compare seasonal landslide patterns.
8. Produce preliminary landslide susceptibility indicators where suitable data exists.

Suggested functions:

- "landslide_frequency()"
- "antecedent_rainfall()"
- "landslide_hotspots()"
- "slope_analysis()"
- "susceptibility_indicators()"

Use geospatial processing where necessary.

Do not claim validated landslide predictions without appropriate event data and independent evaluation.

E. CYCLONE ANALYZER

File: "climate/cyclone.py"

Required capabilities:

1. Load historical cyclone-track datasets.
2. Analyze cyclone frequency by year.
3. Analyze storm intensity.
4. Calculate track distances.
5. Analyze seasonal cyclone occurrence.
6. Identify historical landfall locations.
7. Compare cyclone activity across regions.
8. Generate storm-track visualizations.

Suggested functions:

- "cyclone_frequency()"
- "cyclone_intensity()"
- "track_distance()"
- "landfall_statistics()"
- "cyclone_seasonality()"

Use geographic distance calculations appropriate for latitude and longitude.

Do not assume that a cyclone passing near a region necessarily caused damage.

---

10. ADVANCED ANALYTICS

A. Multi-Hazard Comparison

File: "advanced/multi_hazard.py"

Develop a framework for comparing different climate hazards across common regions and time periods.

Features:

- Hazard-specific indicators.
- Regional comparisons.
- Normalization of comparable metrics.
- Multi-hazard exposure matrices.
- Historical exposure comparisons.
- Geographic overlap analysis.
- Transparent methodology.

Suggested functions:

- "compare_hazards()"
- "hazard_exposure_matrix()"
- "normalize_indicators()"
- "regional_hazard_summary()"

Do not combine fundamentally different hazard measurements into a single risk score without a documented methodology.

Keep individual hazard scores available.

Handle missing hazards explicitly rather than treating missing values as zero risk.

B. Automatic Insight Generator

File: "advanced/insights.py"

Develop a rule-based analytical insight engine.

It should identify:

- Significant descriptive changes.
- Unusually high or low observations.
- Strong correlations.
- Seasonal patterns.
- Regional differences.
- Missing-data limitations.
- Unusual historical extremes.
- Changes in hazard frequency.

Each insight must contain:

- A human-readable statement.
- Supporting numerical evidence.
- Data period.
- Relevant location.
- Calculation method.
- Any important limitations.

Avoid unsupported causal claims.

Do not require external LLM APIs for basic insight generation.

C. Data Reliability Engine

File: "advanced/reliability.py"

Include:

- Missing observation coverage.
- Duplicate-date detection.
- Unit validation.
- Date consistency.
- Geographic coordinate validation.
- Invalid or implausible measurements.
- Inconsistent temporal granularity.
- Historical baseline sufficiency.
- Data source tracking.
- Quality warnings.

This is a high-priority differentiating feature.

---

11. DATASET AND INPUT DESIGN

The library must accept multiple types of input data.

Examples:

- CSV.
- Excel.
- JSON.
- Parquet.
- Pandas DataFrames.
- GeoJSON through optional geospatial dependencies.
- NetCDF through optional climate-data dependencies.

Climate datasets may contain:

- Date.
- State.
- District.
- Latitude.
- Longitude.
- Maximum temperature.
- Minimum temperature.
- Rainfall.
- Humidity.
- Event type.
- Event date.
- Cyclone identifier.
- Wind speed.
- Terrain slope.
- Elevation.

Do not assume every dataset contains every field.

Implement configurable column mapping.

Example:

column_map = {
    "DATE": "date",
    "TMAX": "max_temperature",
    "RAIN": "rainfall",
    "DISTRICT": "district"
}

Support explicit unit conversion.

Use a consistent internal representation of dates, coordinates, and units.

Do not silently assume units when metadata is missing.

---

12. PUBLIC API DESIGN

The library must provide a clean, stable, understandable public API.

Design a "Dataset" class for general analytics.

Also design specialized analyzers for climate datasets.

Target usage example:

from nielytics import Dataset

data = Dataset("sample.csv")

print(data.profile())
print(data.missing_report())
print(data.summary())

cleaned = data.remove_duplicates()

print(cleaned.summary())

Climate example:

from nielytics.climate import (
    HeatwaveAnalyzer,
    DroughtAnalyzer
)

heat = HeatwaveAnalyzer(
    temperature_data,
    date_column="date",
    temperature_column="tmax"
)

heat_result = heat.extreme_heat_days(
    threshold=40
)

drought = DroughtAnalyzer(
    rainfall_data,
    date_column="date",
    rainfall_column="rainfall"
)

drought_result = drought.rainfall_anomaly()

These examples represent the desired API.

Implement the classes and functions before claiming these examples work.

Design result objects that can be consumed by backend developers.

Prefer structured Python dictionaries, Pandas DataFrames, dataclasses, or typed result models.

Ensure outputs are serializable when needed.

Avoid returning only printed text.

---

13. BACKEND INTEGRATION REQUIREMENTS

This is especially important because my teammates are developing the backend.

NIElytics must be:

- Importable as a normal Python package.
- Independent of the frontend and backend frameworks.
- Free from application-specific global state.
- Usable in scripts and backend services.
- Deterministic for the same inputs and configuration.
- Designed with predictable exceptions.
- Documented with clear input and output contracts.
- Compatible with data serialization.
- Suitable for processing datasets without launching graphical windows.

Provide an integration guide explaining:

1. How teammates install NIElytics.
2. How to import its modules.
3. Which input formats are supported.
4. Which functions to call.
5. What outputs are returned.
6. How to convert results to JSON-compatible structures.
7. How to obtain chart objects.
8. How errors are handled.
9. Which dependencies are optional.
10. How to upgrade package versions.

Do not implement API endpoints.

Your job is to provide the library that their backend will call.

---

14. REPORT GENERATION

Implement an optional reporting module.

Features:

- Dataset summary.
- Missing-data analysis.
- Cleaning history.
- Statistical results.
- Hazard-specific findings.
- Charts.
- Regional comparisons.
- Data sources.
- Methodology.
- Limitations.

Support HTML output first.

PDF export can be an optional future enhancement.

Do not build a dashboard or website.

---

15. TESTING REQUIREMENTS

Use Pytest.

Create unit tests for all important functions.

Test:

- Correct numerical results.
- Empty datasets.
- Missing columns.
- Invalid data types.
- Duplicate observations.
- Missing dates.
- Incorrect units.
- Unsupported file formats.
- Constant-valued columns.
- Zero variance.
- Incorrect geographic coordinates.
- Irregular time series.
- Insufficient historical records.
- Invalid thresholds.
- Missing optional dependencies.

Create synthetic datasets for testing.

Use trusted reference values where possible.

Never present synthetic datasets as real climate observations.

Include integration tests that simulate a backend importing NIElytics and consuming its outputs.

Run tests after implementing each module.

Fix failures before proceeding.

---

16. PERFORMANCE REQUIREMENTS

The library should efficiently handle typical competition datasets.

Use:

- Vectorized NumPy and Pandas operations.
- Efficient grouping and aggregation.
- Appropriate memory usage.
- Reusable calculations.
- Optional chunked processing for large CSV files.

Avoid unnecessary Python loops over individual DataFrame rows.

Do not optimize prematurely.

Benchmark representative operations and report actual measurements rather than invented performance claims.

---

17. DOCUMENTATION REQUIREMENTS

Create comprehensive documentation.

README.md

Include:

- Project overview.
- Purpose.
- Features.
- Installation.
- Quick start.
- Supported formats.
- Basic examples.
- Climate examples.
- Testing instructions.
- Limitations.

API Reference

Document each public function with:

- Purpose.
- Parameters.
- Accepted types.
- Return values.
- Exceptions.
- Usage examples.

Algorithms Documentation

Explain:

- IQR.
- Z-score.
- Temperature anomalies.
- Rolling averages.
- Rainfall anomalies.
- SPI.
- Trend estimation.
- Cyclone track distances.
- Multi-hazard normalization.

Integration Guide

Explain how frontend/backend teammates can consume NIElytics without modifying the library.

---

18. DEVELOPMENT PRIORITY

Do not attempt to build every module simultaneously.

Follow this implementation order.

Phase A — Working Foundation

Highest priority:

1. Initialize Python package.
2. Configure pyproject.toml.
3. Implement dataset loading.
4. Implement cleaning.
5. Implement profiling.
6. Implement statistical analysis.
7. Implement time-series analysis.
8. Implement basic visualization.
9. Implement input validation.
10. Add unit tests.

This phase must produce a pip-installable working package.

Phase B — First Climate Modules

Implement:

1. Heatwave analysis.
2. Rainfall analysis.
3. Drought analysis.

Use these to demonstrate the library on real datasets.

Phase C — Remaining Hazards

Implement:

1. Flood analysis.
2. Cyclone analysis.
3. Landslide analysis.

Add optional geospatial dependencies where necessary.

Phase D — Advanced Features

Implement:

1. Multi-hazard comparison.
2. Automatic insight generation.
3. Data reliability analysis.
4. Report generation.

Phase E — Final Integration Preparation

1. Finalize the public API.
2. Improve error handling.
3. Run all tests.
4. Verify package installation.
5. Write integration documentation.
6. Create example scripts.
7. Prepare a handoff guide for my teammates.

Prioritize correctness and working functionality over feature count.

---

19. CODING AND WORKFLOW INSTRUCTIONS FOR OPM

You are operating inside my development environment.

Before modifying files:

1. Inspect the current workspace.
2. Identify existing project files.
3. Determine whether the repository is empty or already initialized.
4. Preserve existing useful work.
5. Check the installed Python version and dependencies.
6. Present a concise implementation plan.

Then begin implementation.

For every development milestone:

1. Explain what will be built.
2. Create or update the necessary files.
3. Implement complete working code.
4. Add tests.
5. Execute relevant tests if the environment permits.
6. Diagnose and fix errors.
7. Update documentation.
8. Summarize what was completed.
9. Identify remaining work.

Do not provide only code snippets when you can directly create the project files.

Do not claim that code works unless it has actually been tested.

Do not invent successful terminal results.

Do not install unnecessary system-wide dependencies.

Use a virtual environment.

Ask for confirmation before destructive operations, replacing significant existing code, or installing unexpected dependencies.

Do not access secrets, credentials, or unrelated files.

Do not push code to remote repositories without my permission.

Keep changes focused on NIElytics.

---

20. QUALITY STANDARDS

The final package must satisfy the following:

- Clean modular architecture.
- Correct statistical calculations.
- Reusable functions.
- Consistent naming conventions.
- Type hints for public APIs.
- Meaningful docstrings.
- Input validation.
- Helpful exception messages.
- Reproducible results.
- Proper missing-data handling.
- Explicit units.
- Data provenance.
- Automated tests.
- Clear documentation.
- pip-installable package.
- Stable backend integration interface.
- No unnecessary frontend/backend code.

Use meaningful algorithms rather than unnecessary complexity.

When a feature is scientifically uncertain, explain the limitation rather than inventing a result.

---

21. EXPECTED FINAL DELIVERABLES

At the end of development, I expect:

1. A complete NIElytics Python package.
2. All implemented general analytics modules.
3. Implemented climate hazard modules.
4. Automated unit tests.
5. Integration tests.
6. Package configuration.
7. Installation instructions.
8. API documentation.
9. Algorithm explanations.
10. Example datasets and scripts.
11. Backend integration guide.
12. A clear list of completed and incomplete features.
13. Instructions for publishing the package later, if desired.

The final library must work independently.

My teammates must be able to install it and call its functions without needing to understand its internal implementation.

---

22. VERY IMPORTANT — DO NOT BUILD THE APPLICATION

Remember:

I AM ONLY BUILDING NIElytics.

My teammates are building the ClimateLens India frontend and backend.

Do not spend development time building:

- A website.
- A frontend.
- A backend server.
- REST API endpoints.
- A database.
- User authentication.
- Deployment infrastructure.
- A complete dashboard application.

Only implement the analytical Python library, its tests, documentation, and integration examples.

The library may generate chart objects and analytical results, but displaying them in the final application is my teammates' responsibility.

---

23. FIRST TASK — START NOW

Begin by examining the current workspace and establishing the NIElytics project.

Then:

1. Show me the final proposed architecture.
2. Identify the minimum viable library that can be completed before NIErnaya Phase 1.
3. Create the project structure.
4. Configure the Python package.
5. Implement the core "Dataset" class.
6. Implement data loading, profiling, cleaning, and basic statistics.
7. Write tests for these features.
8. Run the tests and fix errors.
9. Create a working usage example.
10. Explain how my teammates will eventually integrate the library.

After completing this first milestone, continue module by module, prioritizing correctness and test coverage.

Do not attempt to generate the entire project in one enormous response. Build it incrementally, write real files, run tests, and maintain a working package throughout development.

Your ultimate goal is to help me create a technically impressive, reusable, scientifically responsible Python library that powers ClimateLens India and demonstrates strong software engineering and data analytics skills at NIErnaya 2026.

START WITH WORKSPACE INSPECTION AND THE CORE NIElytics PACKAGE.
IElytics — Additional API, Geospatial and Team Integration Requirements

24. CRITICAL REQUIREMENT: CLIMATE DATA SOURCE INTEGRATION

Extend the original NIElytics development specification to support external climate APIs, historical disaster datasets, and map-ready geospatial outputs.

This is an additional requirement, not a replacement for the original master prompt.

Preserve all previously defined functionality, architecture, development priorities, scientific safeguards, and team responsibility boundaries.

Main Objective

NIElytics must serve as the independent climate-data acquisition, processing, analytics, and geospatial output library for ClimateLens India.

The project covers five hazards:

1. Heatwaves
2. Floods
3. Droughts
4. Landslides
5. Cyclones

The library must obtain suitable historical or current data where available, process it, perform relevant analysis, and return standardized outputs that my teammates can display on an interactive map of India.

My responsibility is exclusively NIElytics. My teammates will implement the frontend, backend, map interface, API routes, database, and deployment.

Do not build any of those application components.

---

25. REQUIRED EXTERNAL DATA SOURCES

Implement modular connectors for the following providers.

A. Open-Meteo Historical Weather API

Purpose:

- Heatwave analysis
- Temperature anomalies
- Rainfall analysis
- Drought-related indicators
- Extreme rainfall analysis

API endpoint:

"https://archive-api.open-meteo.com/v1/archive"

Documentation:

"https://open-meteo.com/en/docs/historical-weather-api"

Support parameters including:

- Latitude
- Longitude
- Start date
- End date
- Daily maximum temperature
- Daily minimum temperature
- Daily precipitation
- Time zone

Example:

"https://archive-api.open-meteo.com/v1/archive?latitude=12.2958&longitude=76.6394&start_date=2025-01-01&end_date=2025-12-31&daily=temperature_2m_max,precipitation_sum&timezone=Asia%2FKolkata"

Implement:

- "fetch_historical_weather()"
- "fetch_temperature_data()"
- "fetch_rainfall_data()"

Check API usage restrictions and attribution requirements.

B. Open-Meteo Flood API

Purpose:

- River discharge estimates
- Historical and forecast river discharge, where supported
- River-discharge anomaly analysis
- Hydrological indicators relevant to flood conditions

Endpoint:

"https://flood-api.open-meteo.com/v1/flood"

Documentation:

"https://open-meteo.com/en/docs/flood-api"

Implement:

- "fetch_river_discharge()"
- "analyze_discharge_anomalies()"

Do not treat modeled discharge as a confirmed flood event or inundation extent.

Label forecast and historical observations distinctly.

C. NASA POWER API

Purpose:

- Rainfall analysis
- Drought indicators
- Temperature analysis
- Historical meteorological comparisons

Endpoint:

"https://power.larc.nasa.gov/api/temporal/daily/point"

Documentation:

"https://power.larc.nasa.gov/"

Support:

- Latitude
- Longitude
- Start date
- End date
- Precipitation parameters
- Temperature parameters

Implement:

- "fetch_nasa_power_data()"
- "fetch_nasa_precipitation()"

Validate returned units, missing-value conventions, and temporal coverage.

D. NASA Landslide Data

Primary sources:

NASA COOLR:

"https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer"

NASA Global Landslide Catalog:

"https://data.nasa.gov/dataset/global-landslide-catalog-export"

Purpose:

- Historical landslide locations
- Landslide event dates
- Geographic coordinates
- Historical event distributions
- Landslide hotspot analysis

Implement:

- "fetch_landslide_events()"
- "load_landslide_catalog()"
- "filter_landslides_by_region()"
- "landslide_events_to_geojson()"

For ArcGIS services, discover available layers and query capabilities from service metadata rather than assuming a fixed layer identifier.

Support pagination when available.

Respect server-imposed result limits.

Handle missing coordinates and incomplete event records.

Do not claim that historical landslide records represent live landslide warnings.

E. NOAA IBTrACS Cyclone Data

Official source:

"https://www.ncei.noaa.gov/products/international-best-track-archive"

North Indian Ocean CSV:

"https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv"

Purpose:

- Historical cyclone locations
- Cyclone tracks
- Storm intensity
- Cyclone frequency
- Seasonal patterns
- Historical landfall analysis

Implement:

- "load_ibtracs()"
- "get_cyclone_tracks()"
- "cyclone_frequency()"
- "cyclone_tracks_to_geojson()"
- "get_cyclone_intensity()"

Support filtering by:

- Year
- Date range
- Storm identifier
- Basin
- Geographic bounding box

Correctly parse IBTrACS metadata and units.

Preserve storm identifiers and observation timestamps.

Use chronological ordering when constructing storm tracks.

Do not treat a storm-track intersection with a coastline as a verified landfall without a documented landfall methodology.

F. Optional Indian Government Sources

Design future-compatible connectors or import adapters for:

- India Meteorological Department (IMD)
- ISRO / NRSC Bhuvan
- Geological Survey of India (GSI)
- Other authoritative Indian disaster datasets

Do not assume these organizations provide unrestricted public APIs.

If direct API access is unavailable, support documented CSV, GeoJSON, Shapefile, or raster imports.

Do not invent endpoints, credentials, or datasets.

---

26. API CONNECTOR ARCHITECTURE

Extend the package structure:

src/nielytics/
│
├── data_sources/
│   ├── __init__.py
│   ├── base.py
│   ├── open_meteo.py
│   ├── open_meteo_flood.py
│   ├── nasa_power.py
│   ├── nasa_landslides.py
│   ├── noaa_ibtracs.py
│   └── local_files.py
│
├── geospatial/
│   ├── __init__.py
│   ├── geojson.py
│   ├── boundaries.py
│   ├── coordinates.py
│   ├── spatial_analysis.py
│   ├── map_layers.py
│   └── exposure.py
│
└── integration/
    ├── __init__.py
    ├── schemas.py
    ├── serializers.py
    └── facade.py

Reuse existing modules if they already implement these responsibilities.

Avoid duplicate functionality.

Connector Requirements

Every connector must:

1. Validate request parameters.
2. Support configurable timeouts.
3. Handle HTTP errors.
4. Handle rate limiting.
5. Use bounded retries with backoff.
6. Parse provider-specific responses.
7. Convert results into standardized structures.
8. Preserve source metadata.
9. Record observation periods.
10. Validate units and coordinates.
11. Support local caching when appropriate.
12. Allow dependency injection or mocking for tests.
13. Fail with meaningful exceptions.
14. Respect provider terms, attribution, and licensing.

Never embed private API keys in source code.

Use environment variables for credentials if needed.

Do not require credentials for public endpoints.

Never make network calls automatically when the package is imported.

---

27. STANDARDIZED CLIMATE DATA MODEL

Different providers use different field names and formats.

NIElytics must normalize them into a consistent internal representation.

Recommended fields:

hazard_type
source
source_dataset
observation_time
latitude
longitude
region_id
region_name
measurement
measurement_value
measurement_unit
geometry
quality_flag

Not every dataset will contain every field.

Use documented optional fields and hazard-specific schemas.

Preserve original raw data where appropriate.

Coordinate Requirements

- Use EPSG:4326 for GeoJSON.
- Store longitude and latitude consistently.
- Follow GeoJSON coordinate order: longitude, latitude.
- Validate coordinate ranges.
- Reproject geometries when necessary.
- Handle missing and invalid coordinates.

Time Requirements

- Support ISO 8601 timestamps.
- Preserve source time-zone information where available.
- Use UTC for timestamped events when practical.
- Preserve daily observation dates separately from timestamps.
- Do not mix daily observations and instantaneous events without explicit aggregation.

Units

Standardize or explicitly document:

- Temperature: °C
- Rainfall: mm
- River discharge: m³/s
- Wind speed: documented source units, with optional conversion
- Distance: km
- Elevation: m

Do not silently infer missing units.

---

28. MAP-READY GEOSPATIAL OUTPUTS

The frontend team will display an interactive map of India.

NIElytics must produce data that the frontend can consume through the backend.

Support:

Heatwaves

- Point measurements
- Regional heatwave indicators
- Temperature anomalies
- Grid-cell values
- Region-level choropleth data

Floods

- River-discharge observation points
- Historical flood-event locations
- Flood-inundation polygons when genuine extent data exists
- Rainfall-based indicators clearly distinguished from confirmed floods

Droughts

- Regional rainfall anomalies
- SPI indicators
- Drought-related choropleth layers
- Seasonal comparisons

Landslides

- Historical landslide event markers
- Event clusters
- Recorded-event density
- Susceptibility polygons or rasters only when supported by suitable data

Cyclones

- Storm-track lines
- Historical storm observation points
- Storm intensity attributes
- Documented landfall points

Required GeoJSON Geometry Types

Support:

- Point
- MultiPoint
- LineString
- MultiLineString
- Polygon
- MultiPolygon

Implement:

- "to_geojson()"
- "points_to_geojson()"
- "tracks_to_geojson()"
- "regions_to_geojson()"
- "get_hazard_map_layer()"
- "get_hazard_locations()"
- "get_regional_hazard_data()"

Return valid GeoJSON FeatureCollections for vector layers.

For large gridded climate datasets, provide separate raster or grid-oriented outputs instead of converting millions of cells into GeoJSON polygons.

Include metadata for source, period, units, processing method, and limitations alongside the layer.

---

29. UNIFIED BACKEND INTEGRATION INTERFACE

Design a stable, documented facade that teammates can call.

Target usage:

from nielytics.integration import ClimateAnalytics

analytics = ClimateAnalytics()

result = analytics.get_hazard_map_layer(
    hazard="cyclone",
    start_date="2020-01-01",
    end_date="2025-12-31",
    region="India"
)

This is a target API specification, not an existing implementation.

Implement it only after defining the required data-source configuration and schemas.

Required Public Operations

- "get_hazard_map_layer()"
- "get_hazard_summary()"
- "get_hazard_timeseries()"
- "compare_regions()"
- "get_available_hazards()"
- "get_data_coverage()"
- "get_source_metadata()"

These operations should support preloaded datasets and configured data providers.

Do not assume every source supports every requested date, location, or geographic resolution.

Return a clear coverage or unsupported-operation error when necessary.

Recommended Response Contract

{
  "hazard": "cyclone",
  "region": "India",
  "period": {
    "start": "2020-01-01",
    "end": "2025-12-31"
  },
  "data": {
    "type": "FeatureCollection",
    "features": []
  },
  "metadata": {
    "source": "NOAA IBTrACS",
    "geometry_crs": "EPSG:4326",
    "data_type": "historical",
    "units": {},
    "coverage": {},
    "limitations": []
  }
}

This JSON is an illustrative schema only.

Actual implementations must populate it with real processed data and meaningful metadata.

Use stable field names and consistent error behavior.

---

30. IMPORTANT: TEAM INTEGRATION CONTRACT

The NIElytics package must remain independent of the frontend and backend.

My Responsibility

I implement:

- Climate data connectors.
- Data normalization.
- Climate analytics.
- Geospatial processing.
- GeoJSON generation.
- Map-layer data preparation.
- Public Python APIs.
- Documentation.
- Tests.

Teammates' Responsibility

They implement:

- Backend routes.
- API authentication.
- Frontend components.
- Interactive map rendering.
- User-facing filters.
- Database integration.
- Hosting and deployment.

Integration Agreement

Before finalizing public APIs, define and document:

1. Supported hazard names.
2. Date-filter formats.
3. Geographic identifiers.
4. Input schemas.
5. Output schemas.
6. Error structures.
7. Map geometry types.
8. Units.
9. Data coverage limitations.
10. Version compatibility.

Produce a document named:

"INTEGRATION_CONTRACT.md"

This document must be understandable to teammates who have not worked on NIElytics internals.

---

31. OFFLINE SUPPORT AND RELIABILITY

The library must support both online and offline workflows.

Online Mode

Fetch data from supported APIs when explicitly requested.

Offline Mode

Load previously downloaded datasets or cached responses.

Requirements:

- Avoid unnecessary repeated requests.
- Cache with explicit expiration or refresh policies.
- Record when data was retrieved.
- Distinguish cached historical data from fresh observations.
- Support deterministic offline tests.
- Provide useful errors when network access is unavailable.

Do not promise live data for sources that publish only historical datasets.

Do not promise real-time alerts or disaster forecasting.

---

32. INTEGRATION TESTING

Create tests covering:

- Successful provider response parsing.
- HTTP timeout.
- Rate limiting.
- Invalid coordinates.
- Missing dates.
- Empty responses.
- Missing required fields.
- Invalid provider values.
- GeoJSON validity.
- Coordinate ordering.
- Cyclone track chronological ordering.
- Landslide event conversion.
- Serialization.
- Source metadata.
- Offline cached-data processing.
- Backend-style library calls.

Mock external network requests for automated unit tests.

Create optional live integration tests that run only when explicitly enabled.

Do not make the normal test suite depend on external API availability.

---

33. REQUIRED INTEGRATION DOCUMENTATION

Create:

"docs/DATA_SOURCES.md"

Explain:

- Each data provider.
- Endpoint or download location.
- Authentication requirements.
- Supported parameters.
- Geographic coverage.
- Historical coverage.
- Data freshness.
- Licensing and attribution.
- Limitations.

"docs/GEOJSON_GUIDE.md"

Explain:

- Supported geometries.
- Coordinate reference system.
- Output examples.
- Map layer properties.
- Handling large datasets.

"INTEGRATION_CONTRACT.md"

Explain:

- Stable Python API.
- Input schemas.
- Response schemas.
- Error handling.
- Installation.
- Usage examples.

"docs/TEAM_HANDOFF.md"

Explain exactly how the backend developers can use NIElytics.

Include working examples for all five hazards where data is available.

---

34. DEVELOPMENT ORDER FOR THIS EXTENSION

Implement incrementally.

Milestone 1 — Data Connectors

1. Open-Meteo historical weather.
2. NASA POWER.
3. NOAA IBTrACS.
4. NASA landslide catalog.
5. Open-Meteo Flood API.

Milestone 2 — Standardization

1. Common schemas.
2. Units.
3. Coordinates.
4. Date handling.
5. Data provenance.

Milestone 3 — Geospatial Output

1. Point GeoJSON.
2. Cyclone track LineStrings.
3. Regional polygon data.
4. Hazard map-layer generation.

Milestone 4 — Backend Integration Contract

1. Stable facade.
2. JSON-compatible results.
3. Error schemas.
4. Documentation.
5. Integration tests.

Milestone 5 — Final Verification

1. Run all unit tests.
2. Run integration tests.
3. Test package installation.
4. Validate example GeoJSON outputs.
5. Test all five hazards with available sample data.
6. Document any unavailable or unsupported functionality.

Do not claim that a provider or feature works unless verified.

---

35. FINAL INSTRUCTIONS TO OPM

Read this extension together with the original NIElytics master prompt.

Treat both documents as one development specification.

Preserve the original project architecture unless improvements are justified.

Inspect the current repository before making changes.

Identify existing implementations and avoid duplicating them.

Prioritize working, tested modules over unfinished features.

Do not build frontend or backend application code.

Your objective is to deliver a robust, installable NIElytics library that supplies reliable climate analytics and map-ready outputs to the ClimateLens India backend.

Begin by reviewing the existing project and producing a concise implementation plan for these additional integration requirements. Then implement the first unfinished milestone, write tests, run them, and report verified results.
