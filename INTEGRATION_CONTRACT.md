# NIElytics integration contract — 0.1.0

## Supported Python interface

Install the local package with `pip install /path/to/nielytics`. Import `Dataset`, all ten plotting functions, `AnalysisResult`, `HeatwaveAnalyzer`, `FloodAnalyzer`, `DroughtAnalyzer`, `CycloneAnalyzer`, and `LandslideAnalyzer` from `nielytics`. Import provider functions from `nielytics.climate.providers` and vector exporters from `nielytics.geospatial`. No API server, database, authentication, import-time network acquisition, or automatic chart display is included.

Inputs: a local CSV/Excel/JSON/Parquet path or a pandas DataFrame. `parse_dates` explicitly identifies date columns; encoding defaults to UTF-8. Preserve source column names unless calling `standardize_columns`. Input units are caller-owned: no assumptions or conversions are made. A DataFrame should contain scalar cells with unique column names.

Outputs: `frame`, `summary()`, and `missing_report()` return pandas DataFrames; `profile()` returns JSON-compatible dictionaries; `to_records()` returns a list of JSON-compatible dictionaries. Cleaning methods return new Dataset instances; `history` records operations and row counts. Records omit the DataFrame index; dates use ISO strings (millisecond precision), missing and nonfinite values become null. Numerical summaries retain pandas missing values until explicitly serialized. Nested mutable cell values are subject to pandas copy limitations.

Catch `NIElyticsError` at the backend boundary; its subtypes are `ValidationError`, `DataLoadError`, `UnsupportedFormatError`, and `OptionalDependencyError`. The backend decides HTTP status codes and error JSON. Library functions do not create routes or response objects. Native failures for unsupported provider-specific reader keyword arguments may retain their underlying cause.

See `examples/basic_analysis.py` for an executable backend-style call and `docs/api_reference.md` for function contracts. Pin `nielytics==0.1.0` once distributing built artifacts; test an upgrade before changing versions. This pre-1.0 interface may change with documented releases.

## Chart interface

Install `/path/to/nielytics[visualization]`, adding `geospatial` for GeoDataFrame inputs. Import the ten plotting functions from `nielytics.core.visualization`; pass a DataFrame or `dataset.frame`. Nine general functions return Plotly Figures: serialize with `figure.to_json()` or export self-contained HTML with `figure.write_html(path, include_plotlyjs=True, auto_open=False)`. Chart JSON is a Plotly specification, not table JSON or GeoJSON. Backend teammates choose the renderer.

`plot_geographic` returns a Matplotlib Figure for supplied longitude/latitude points or CRS-bearing GeoDataFrames; serialize to PNG/SVG using `figure.savefig(path_or_buffer, format=...)`. It validates coordinates and reprojects supplied geometry, but does not acquire boundaries or derive hazard maps. No library plotting call invokes `show()`, launches a browser, or downloads a basemap. Caller code explicitly displays or exports figures.

Inputs remain unchanged. Missing-value policies and row-count metadata are documented in `docs/api_reference.md`; no unknown measurement unit is inferred. Invalid inputs raise `ValidationError`; missing optional plotting packages raise `OptionalDependencyError`. See `examples/visualization_gallery.py` for all chart categories, using explicitly synthetic data.

## Indicator responses and climate inputs

Each hazard analyzer accepts explicitly named columns and units in caller-supplied DataFrames. Input observations must not silently acquire unknown units, dates, or geographic meaning. Analyzer methods return `AnalysisResult`; `.to_dict()` produces independent strict JSON containing `status: 'success'`, `feature`, `data`, `metadata`, `warnings`, and `errors`. Missing indicators remain null/explicitly warned, not zero risk. An exception is raised for invalid/unsupported inputs, not returned as a fabricated success response. See [API reference](docs/api_reference.md) for each method's required fields and accepted units.

Provider requests are **explicit** through `HTTPClient` and `fetch_historical_weather`, `fetch_river_discharge`, `fetch_nasa_power_data`, and `load_ibtracs` in `nielytics.climate.providers`. Provider responses use the same `AnalysisResult` schema with `data['records']`, source, retrieval time, units, data type, coverage/period, and limitations in metadata. Dates for daily data use `YYYY-MM-DD`; IBTrACS observation times are UTC timestamps. Historical/reanalysis weather and modeled discharge are not direct ground measurements, hazard declarations, live alerts, or forecasts. The specified NASA COOLR URL returned HTTP 404; do not infer landslide coverage from a failed service. See [data sources](docs/DATA_SOURCES.md) for access evidence and catalog status.

Use `HTTPClient(timeout=20, retries=2, cache_dir=None, ttl_seconds=86400, offline=False)` to select transport policy. No disk cache is enabled by default; offline mode needs cached responses, and expired entries require explicit opt-in. Inject an opener for deterministic backend/offline workflows. Provider failures raise `ProviderError`, `ResponseError`, or `OfflineCacheError` (all from `nielytics.climate.providers`); bad parameters raise `ValidationError`. Callers must catch exceptions and choose their own error response and HTTP status.

## Geospatial contract

`points_to_geojson`, `tracks_to_geojson`, `regions_to_geojson`, and `to_geojson` in `nielytics.geospatial` return JSON-safe FeatureCollections for supplied vector data. Explicit `crs='EPSG:4326'` is required, coordinates are `[longitude, latitude]`, and permitted geometries are Point, MultiPoint, LineString, MultiLineString, Polygon, and MultiPolygon. Supply `source`, `period`, `units`, `method`, and `limitations`; no missing observations, boundaries, landfalls, or inundation extents are invented. Keep raster/grid data separate. Map functions `get_hazard_map_layer`, `get_hazard_locations`, and `get_regional_hazard_data` work on supplied features, not arbitrary geographic region names or a source registry. No `ClimateAnalytics` facade or automatic region lookup exists; unsupported operations should be rejected by your backend.

Teammates own routes, authorization, persistence, user filters, map rendering, and deployment. Installation is local or from a wheel; the interface is pre-1.0 and should be pinned/tested before upgrades.
