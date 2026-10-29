# NIElytics API reference — 0.1.0

## Dataset

`Dataset(source, **load_options)` accepts a pandas DataFrame or local path and forwards options to `load_dataset`. `frame` is a defensive pandas copy; `history` is a deep-copied list of operation dictionaries. Nested mutable object cells are not recursively copied by pandas. Use scalar cells and unique column names.

| Method | Parameters | Return |
| --- | --- | --- |
| `profile()` | none | JSON-compatible profile dictionary |
| `missing_report()` | none | per-column counts/percentages DataFrame |
| `summary()` | `columns=None`, `ddof=1` | numeric summary DataFrame |
| `remove_duplicates()` | `subset=None`, `keep='first'` (`'last'` or `False` also supported) | new Dataset |
| `fill_missing()` | `columns=None`, `strategy='mean'`, `value=None` | new Dataset |
| `standardize_columns()` | none | new Dataset with explicit normalized names |
| `clean_text()` | `columns=None` | new Dataset with surrounding whitespace stripped |
| `convert_types(mapping)` | column-to-pandas-dtype mapping | new Dataset |
| `parse_dates(columns)` | column name/list, optional `format=None` | new Dataset |
| `to_records()` | none | JSON-safe list of dictionaries; index omitted |

Cleaning errors raise `ValidationError` and leave the original Dataset unchanged. Each successful operation records its name, parameters, and before/after row counts. History parameters preserve Python types: unlike profile/records, arbitrary dtype objects in history need caller encoding for JSON.

## Loading — `nielytics.core.loader`

`load_dataset(source, *, format=None, parse_dates=None, encoding='utf-8', **kwargs) -> DataFrame`: copy an existing frame or read one local table. Format is inferred from extension or explicitly selected (`csv`, `excel`, `json`, `parquet`; extension aliases supported). `parse_dates` is a name/list or mapping of columns to date-format strings. Extra keywords go to the pandas reader. Chunk readers and multi-sheet results are rejected: this API returns one DataFrame. URLs are rejected; external connectors are not implemented.

`load_csv`, `load_excel`, `load_json`, `load_parquet`: same path/options contract, with their format selected explicitly. Example: `load_csv('data.csv', parse_dates={'date': '%Y-%m-%d'}, encoding='utf-8')`.

Missing/unreadable files and reader failures: `DataLoadError`; unsupported format: `UnsupportedFormatError`; missing reader engine: `OptionalDependencyError`; invalid parameters/date conversion: `ValidationError`. Excel and Parquet engines are optional. Original column names are preserved, subject to the source format and pandas reader behavior.

## Cleaning — `nielytics.core.cleaner`

All functions accept a DataFrame and return new frames, never modify the original, and require unique columns. Missing selections, incompatible conversions, ambiguous names, and invalid options raise `ValidationError`.

- `missing_report(frame)`: column-indexed `missing_count`, `missing_percent` (0–100); empty input percentages are zero.
- `fill_missing(frame, *, columns=None, strategy='mean', value=None)`: mean/median require numeric columns; mode uses pandas' first mode on ties; constant requires a non-null scalar. All-null statistical fills fail. Default selection is **all columns**; select numeric columns explicitly for mixed tables. Incompatible dtype fills fail instead of silently coercing.
- `remove_duplicates(frame, *, subset=None, keep='first')`: explicit row deletion, preserving surviving indices.
- `standardize_columns(frame)`: string names lowercased, whitespace stripped, non-word runs replaced by underscores, edge underscores stripped; empty names and collisions fail.
- `convert_types(frame, mapping)`: pandas dtype conversion, errors are not silently coerced.
- `clean_text(frame, *, columns=None)`: strip surrounding whitespace in string cells; preserve other values.
- `parse_dates(frame, columns, *, format=None)`: explicit pandas date conversion; invalid dates raise, missing dates stay missing.

Example: `fill_missing(frame, columns=['rainfall'], strategy='constant', value=0)` is a deliberate caller choice, not a recommended climate missing-data policy.

## Profiling — `nielytics.core.profiler`

`profile_dataset(frame) -> dict`: rows, columns, dtypes, missing counts/percentages, unique counts, duplicate count, numeric and categorical summaries, date coverage, memory bytes, and warnings. `column_profile(frame, column) -> dict` profiles one column. `data_quality_report(frame) -> dict` reports missingness, duplicates, and quality warnings. Inputs must be scalar-valued DataFrames with unique columns; unsupported inputs raise `ValidationError`. Nonfinite/missing summary values become null and dates become ISO strings, allowing `json.dumps(profile, allow_nan=False)`.

## Statistics — `nielytics.core.statistics`

Functions take a DataFrame; numeric functions select real numeric columns by default (not booleans/complex). Explicit nonnumeric or missing selections and invalid settings raise `ValidationError`. Results are pandas objects, not automatically JSON-safe.

| Function | Options | Result |
| --- | --- | --- |
| `summarize(frame)` | `columns=None`, `ddof=1` | column-indexed count/mean/median/variance/std/min/max/q25/q75/skew/kurtosis |
| `correlation_matrix(frame)` | `method='pearson'` | pairwise correlation matrix |
| `covariance_matrix(frame)` | `ddof=1` | covariance matrix |
| `grouped_summary(frame, by)` | `columns=None`, `ddof=1` | grouped summary with group/column MultiIndex |
| `frequency_distribution(frame, column)` | `dropna=False` | count/proportion table indexed by values |
| `quantiles(frame)` | `q=(.25,.5,.75)`, `columns=None` | quantile-indexed DataFrame |
| `modes(frame)` | `columns=None` | pandas modes DataFrame, retaining ties |

Example: `summarize(frame, columns=['value'], ddof=0)` requests population variance. Missing values are skipped, correlations use pairwise-complete observations, and insufficient observations/constant correlation produce missing results. Quantiles use pandas' default linear interpolation; use `q=[0.95]` for the 95th percentile. Skewness and kurtosis use pandas estimators (kurtosis is Fisher/excess). No causal inference, climate classification, or statistical significance claim follows from these summaries.

## Visualization — `nielytics.core.visualization`

Install `.[visualization]`; add `geospatial` for GeoDataFrame geometries. Pass a pandas DataFrame, or `dataset.frame`. Inputs are never mutated. All functions accept keyword-only `title: str | None = None`. No function displays a window or fetches data.

| Function | Parameters after `frame` | Result / method |
| --- | --- | --- |
| `plot_line` | `x, y` column labels | Plotly line, input order retained |
| `plot_bar` | `x, y` | Plotly bars, no implicit aggregation |
| `plot_histogram` | `column, *, bins=20` | Plotly count histogram; target bin count |
| `plot_box` | `*, columns=None` | Plotly boxes for selected real numeric columns |
| `plot_scatter` | `x, y` | Plotly numeric scatter |
| `plot_correlation` | `*, method='pearson'` | Plotly heatmap; Pearson, Spearman, or Kendall |
| `plot_timeseries` | `date_column, value_column` | Plotly line, stable chronological sort |
| `plot_distribution` | `column, *, bins=20` | Plotly probability-density histogram, not KDE |
| `plot_seasonal` | `date_column, value_column, *, aggregation='mean'` | Plotly monthly aggregation across years; mean/sum/median |
| `plot_geographic` | `*, longitude='longitude', latitude='latitude', value=None` | Matplotlib geographic figure; optional numeric color column |

Column arguments identify existing columns with unique labels. Numeric data must be real, nonboolean, finite where present. Empty/unusable inputs, invalid selections/options/dates/coordinates raise `ValidationError`; unavailable plotting dependencies raise `OptionalDependencyError`. `bins` must be a positive integer, not a boolean. Dates accept parseable strings or datetime values, not numeric epochs or missing dates. Normalize ambiguous source date formats explicitly before plotting.

Line/bar retain missing y observations; missing x is rejected. Histograms, boxes, scatter and correlations report missing observations with warnings and figure metadata rather than silently zero-filling. Correlations use pairwise-complete observations; undefined coefficients remain missing, not zero or evidence of independence. Seasonal aggregation weights observations, not years, equally; absent/all-missing months remain missing, including for sum. Time-series functions preserve duplicate timestamps and existing gaps; they do not resample, interpolate, or infer unrecorded dates. Labels preserve column names; provide units in column names or titles, since no units are inferred.

Plotly figures expose `layout.meta` with input/used/omitted row counts, missing observations and policy; correlations add pairwise counts, seasonal charts monthly counts. Export via `fig.to_json()` or `fig.write_html('chart.html', include_plotlyjs=True, auto_open=False)`. Explicit desktop display: `fig.show(renderer='browser')`. Static Plotly image export requires additional Kaleido/Chrome tooling, not needed for HTML.

Geographic plain DataFrames require complete longitude/latitude in EPSG:4326 ranges. GeoDataFrames require a known CRS and valid, nonempty geometries; coordinates are reprojected to EPSG:4326. Point, MultiPoint, LineString, MultiLineString, Polygon and MultiPolygon are supported. Optional color values must be complete finite real numbers. Export with `fig.savefig('map.png')`; `fig.nielytics_metadata` records the plotting context. The plot does not download a basemap or infer hazards; separate vector export functions below create GeoJSON from supplied data.

Executable examples for every function and explicit display/export: `examples/visualization_gallery.py` and `COMMANDS_AND_USAGE.md`.

## Unified imports and results

`from nielytics import Dataset, AnalysisResult, HeatwaveAnalyzer, FloodAnalyzer, DroughtAnalyzer, CycloneAnalyzer, LandslideAnalyzer, plot_line, plot_bar, plot_histogram, plot_box, plot_scatter, plot_correlation, plot_timeseries, plot_distribution, plot_seasonal, plot_geographic` exposes existing implementations; Plotly and Matplotlib are still loaded only when called. `AnalysisResult(feature, data, metadata, warnings=[], errors=[], status='success').to_dict()` produces independent strict JSON. Nonfinite numbers or unsupported objects raise during conversion rather than becoming plausible measurements.

## Verified climate connectors — `nielytics.climate.providers`

`HTTPClient(opener=..., timeout=20, retries=2, backoff=1, cache_dir=None, ttl_seconds=86400, offline=False, allow_expired_offline=False, sleep=..., clock=...)` controls all explicit HTTP traffic. No cache is used without `cache_dir`; offline mode requires an existing cache entry with a valid TTL unless `allow_expired_offline=True`. The injected opener enables deterministic offline tests. Catch `ProviderError`/`ResponseError`/`OfflineCacheError` for transport, schema, and cache failures, and `ValidationError` for bad inputs. Retrieval/cache metadata and units are preserved in each `AnalysisResult`.

| Function | Input / result |
| --- | --- |
| `fetch_historical_weather(latitude, longitude, start_date, end_date, *, daily=..., timezone='Asia/Kolkata', client=None)` | Explicit daily subset of max/min 2m temperature (°C), precipitation sum (mm); historical modeled/reanalysis records |
| `fetch_temperature_data(...)`, `fetch_rainfall_data(...)` | Same four positional arguments, optional `timezone` and `client`; selected temperature or precipitation records |
| `fetch_river_discharge(latitude, longitude, start_date, end_date, *, client=None)` | Past-only daily modeled discharge (m³/s); never confirmed flood |
| `analyze_discharge_anomalies(result, *, baseline_start, baseline_end)` | Baseline-relative descriptive modeled-discharge indicator |
| `fetch_nasa_power_data(latitude, longitude, start_date, end_date, *, parameters=('PRECTOTCORR','T2M_MAX'), client=None)` | NASA POWER AG daily LST precipitation (mm/day) and maximum temperature (C); provider fill sentinel becomes null |
| `fetch_nasa_precipitation(...)` | POWER daily precipitation subset; same coordinate/date arguments and optional `client` |
| `load_ibtracs(...)` | NOAA NI historical cyclone records, preserving SID, UTC time, and source winds in knots |
| `fetch_landslide_events(*, accept_terms=False, client=None)` | NASA one-time GLC export; terms acceptance is required before network retrieval |
| `load_landslide_catalog(path)` | Parse the same GLC CSV from a local file, offline |
| `filter_landslides_by_region(result, *, bbox=None, country_code=None)` | Filter catalog records by supplied WGS84 bounding box or recorded country code |
| `landslide_events_to_geojson(result)` | Export only events with valid coordinates; disclose omitted-coordinate count |

`get_cyclone_tracks`, `cyclone_frequency`, `get_cyclone_intensity`, and `cyclone_tracks_to_geojson` produce chronological storm tracks, unique-storm counts, source-specific wind maxima, and track FeatureCollections.

`YYYY-MM-DD` daily dates and valid latitude/longitude are required. Provider `data['records']` contains native JSON scalar records, including null for missing observations. Daily reanalysis is **not** a station reading; NOAA tracks and the NASA GLC are historical, not forecasts, impact inventories, or live warnings. The connectors do not provide humidity, wind-direction, pressure weather products, forecasts, or official declarations. NASA COOLR returned 404 at the specified URL and has no connector. NASA GLC is a one-time export: its page says current as of March 7, 2016 despite later-dated rows; review terms and attribution before use, and do not treat the CSV's last date as data freshness. See [data sources](DATA_SOURCES.md).

## Map-ready vector data — `nielytics.geospatial`

`validate_coordinates(longitude, latitude, *, crs)` checks finite longitude/latitude degrees. `points_to_geojson(points, *, crs, source, period=None, units=None, method='direct coordinate export', limitations=())`, `tracks_to_geojson(tracks, ...)`, `regions_to_geojson(regions, ...)`, and `to_geojson(features, ...)` return JSON-safe FeatureCollections with collection and per-feature provenance. The same metadata keywords apply to `get_hazard_map_layer(hazard, features, ...)`, `get_hazard_locations(hazard, points, ...)`, and `get_regional_hazard_data(hazard, regions, ...)`. Explicit `crs='EPSG:4326'` is required; other CRSs need reprojection before conversion. Supported geometry: Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon. Validation errors do not drop records. Boundaries and hazard extents must be supplied, never inferred from points. See [GeoJSON guide](GEOJSON_GUIDE.md).

## Core time series and outliers

`nielytics.core.timeseries.rolling_mean(frame, date, value, *, window, min_periods=None)` sorts explicit unique daily dates and returns `date`, `value`, and `rolling_mean` columns. A window counts observations, **not** elapsed days; missing values are skipped subject to `min_periods` (default full window). `missing_dates(frame, date, value, *, start=None, end=None)` returns absent daily dates as ISO strings inside the observed or explicit bounds. `calculate_anomalies(frame, date, value, *, baseline_start, baseline_end)` subtracts the baseline **calendar-month** mean; absent reference months yield missing anomalies. All reject duplicate dates, non-daily timestamps, invalid numeric values, and ambiguous/inconsistent dates with `ValidationError`, and never mutate inputs.

`nielytics.core.outliers.detect_outliers(frame, column, *, method='iqr', threshold=None)` returns a boolean Series with the original index. Methods: IQR (Q1/Q3 ± 1.5 IQR), population z-score (absolute score > 3), modified z-score (0.6745 × absolute median deviation / MAD > 3.5), and percentile tails (below 1st or above 99th percentile). Override with a positive cutoff, or a tail proportion in (0, 0.5) for percentile. Missing entries are unflagged; infinite values and invalid settings raise `ValidationError`. `outlier_report` returns counts and flagged indices. Neither method deletes observations; flags do not establish data errors.

## Hazard analyzers — `nielytics.hazards` or package root

Construct with a pandas DataFrame, explicit unit keywords, and optional date/value column names and coordinates. Columns are copied/validated; daily data must have unique dates. All methods return `AnalysisResult`; use `.to_dict()` for strict JSON. User thresholds are caller decisions, **not** official classifications.

| Analyzer (required units) | Implemented methods | Interpretation |
| --- | --- | --- |
| `HeatwaveAnalyzer(data, unit='C')` | `extreme_heat_days(threshold_c=...)`, `heat_spell_duration(threshold_c=..., minimum_days=3)`, `temperature_anomaly(baseline_start=..., baseline_end=..., start=..., end=...)` | Daily temperature threshold episodes and unadjusted period-mean difference; not an IMD declaration |
| `FloodAnalyzer(data, unit='mm')` | `extreme_rainfall_days(threshold_mm=...)`, `cumulative_rainfall(window_days=...)`, `wet_spell_duration(threshold_mm=..., minimum_days=2)`, `flood_event_frequency(events)` | Rainfall proxies; event counts require separate supplied recorded-flood data |
| `DroughtAnalyzer(data, unit='mm')` | `dry_spell_duration(threshold_mm=0, minimum_days=3)`, `rainfall_deficit(baseline_start=..., baseline_end=..., start=..., end=...)` | Dry spells and unadjusted mean deficit; no SPI or official drought declaration |
| `CycloneAnalyzer(data, wind_unit='km/h', pressure_unit='hPa')` | `track_distance()`, `cyclone_intensity()`, `cyclone_frequency()`, `proximity(latitude=..., longitude=..., radius_km=...)` | Historical track distances/intensity/proximity, not landfall or damage |
| `LandslideAnalyzer(data, rainfall_unit='mm', slope_unit='degrees')` | `antecedent_rainfall(window_days=...)`, `susceptibility_indicators(window_days=..., rainfall_threshold_mm=..., slope_threshold_degrees=...)`, `landslide_frequency(events)` | Prior-day rain/slope screening only; independent supplied event records for historical frequency |

Daily analyzers require `date` and `tmax`, `rainfall`, or `slope` columns respectively by default; rename via constructor arguments. Cyclone input defaults to `storm_id`, `time`, `latitude`, `longitude`, `wind`, `pressure` columns. All preserve missingness and report limitations. Optional `latitude`/`longitude` on daily analyzers provide observation location, not a region boundary. See `examples/climate_indicators.py` for executable synthetic data and `docs/algorithms.md` for scientific interpretation.
