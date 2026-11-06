# NIElytics API Reference (v2.0)

## Top-Level Exports (`nielytics`)

### Facade & Orchestration
- `ClimateAnalytics(data_directory=None, offline=True)`
  - `register_dataset(hazard, data, schema=None, **kwargs) -> AnalysisResult`
  - `analyze(hazard, region=None, start_year=None, end_year=None, method=None, **kwargs) -> AnalysisResult`
  - `compare_hazards(hazards=None, region=None) -> AnalysisResult`
  - `get_insights() -> AnalysisResult`
  - `get_geospatial_summary(hazard=None, region_type="state") -> AnalysisResult`
  - `to_geojson(hazard=None) -> dict`

### Core Data & Profiling
- `Dataset(source, **load_options)`
  - `convert_units(column, from_unit, to_unit) -> Dataset`
  - `quality_report() -> dict`
  - `detect_outliers(columns=None, method="zscore", threshold=None) -> pd.DataFrame`
  - `summary(columns=None, ddof=1) -> pd.DataFrame`
  - `missing_report() -> pd.DataFrame`
  - `profile() -> dict`
  - `to_records() -> list[dict]`
  - `clean_text()`, `fill_missing()`, `parse_dates()`, `remove_duplicates()`, `standardize_columns()`, `convert_types()`

### Harmonization (`nielytics.harmonization`)
- `StandardClimateRecord(date, state, district, latitude, longitude, hazard, metric, value, unit, source, data_quality, observation_type, extra)`
- `HarmonizationSchema(date_column, value_column, state_column, district_column, latitude_column, longitude_column, hazard, metric, source_unit, target_unit, source, data_quality, observation_type, temporal_resolution, column_mapping)`
- `DatasetHarmonizer(schema=None)`
  - `harmonize(data, schema=None, **kwargs) -> AnalysisResult`
  - `to_dataframe(analysis_result) -> pd.DataFrame`

### Geospatial Engine (`nielytics.geospatial`)
- `normalize_state_name(name: str) -> str | None`
- `normalize_district_name(district: str, state: str | None = None) -> str | None`
- `aggregate_hazards_by_region(data, region_type="state", ...) -> AnalysisResult`
- `get_state_hazard_summary(data, state, ...) -> AnalysisResult`
- `get_district_hazard_summary(data, district, state=None, ...) -> AnalysisResult`
- `detect_hazard_hotspots(data, latitude_column, longitude_column, min_events=3, radius_km=50.0) -> AnalysisResult`
- `compare_hazard_regions(data, regions, region_type="state", ...) -> AnalysisResult`
- `generate_hazard_geojson(data, latitude_column, longitude_column, properties=None) -> dict`
- `get_state_reference(state_name: str) -> dict | None`
- `point_in_polygon(lon, lat, polygon) -> bool`
- `point_in_bbox(lon, lat, bbox) -> bool`
- `haversine_distance_km(lat1, lon1, lat2, lon2) -> float`

### Hazard Analyzers (`nielytics.hazards`)
- `HeatwaveAnalyzer(data, date_column="date", temperature_column="tmax", unit="C", latitude=None, longitude=None)`
  - `extreme_heat_days(threshold_c) -> AnalysisResult`
  - `heat_spell_duration(threshold_c, minimum_days=3) -> AnalysisResult`
  - `temperature_anomaly(baseline_start, baseline_end, start, end) -> AnalysisResult`
  - `imd_heatwave_classification(normal_tmax=None, terrain="plains") -> AnalysisResult`
  - `percentile_heatwave_indicators(baseline_start, baseline_end, percentile=90.0, consecutive_days=3) -> AnalysisResult`
  - `historical_heatwave_frequency(threshold_c=40.0) -> AnalysisResult`
  - `regional_heat_summary(state_column="state") -> AnalysisResult`

- `FloodAnalyzer(data, date_column="date", rainfall_column="rainfall", unit="mm", latitude=None, longitude=None)`
  - `extreme_rainfall_days(threshold_mm) -> AnalysisResult`
  - `cumulative_rainfall(window_days) -> AnalysisResult`
  - `wet_spell_duration(threshold_mm, minimum_days=2) -> AnalysisResult`
  - `flood_event_frequency(events, event_date_column="date") -> AnalysisResult`
  - `imd_rainfall_classification() -> AnalysisResult`
  - `multi_day_accumulation(windows=[2, 3, 5, 7]) -> AnalysisResult`
  - `rainfall_anomalies(baseline_start, baseline_end) -> AnalysisResult`
  - `discharge_analysis(discharge_data=None, discharge_column="discharge", threshold_m3s=None) -> AnalysisResult`
  - `regional_flood_summary(state_column="state") -> AnalysisResult`

- `DroughtAnalyzer(data, date_column="date", rainfall_column="rainfall", unit="mm", latitude=None, longitude=None)`
  - `dry_spell_duration(threshold_mm=0.0, minimum_days=3) -> AnalysisResult`
  - `rainfall_deficit(baseline_start, baseline_end, start, end) -> AnalysisResult`
  - `standardized_precipitation_index(scale_months=3, baseline_start=None, baseline_end=None) -> AnalysisResult`
  - `seasonal_rainfall_anomaly(monsoon_months=[6, 7, 8, 9]) -> AnalysisResult`
  - `historical_drought_frequency() -> AnalysisResult`

- `LandslideAnalyzer(data, date_column="date", rainfall_column="rainfall", slope_column="slope", rainfall_unit="mm", slope_unit="degrees")`
  - `antecedent_rainfall(window_days) -> AnalysisResult`
  - `susceptibility_indicators(window_days, rainfall_threshold_mm, slope_threshold_degrees) -> AnalysisResult`
  - `landslide_frequency(events, event_date_column="date") -> AnalysisResult`
  - `rainfall_trigger_indicator(antecedent_window_days=3, antecedent_threshold_mm=100.0, trigger_rainfall_threshold_mm=50.0) -> AnalysisResult`
  - `slope_elevation_screening(min_slope_degrees=15.0, elevation_column=None, min_elevation_m=None) -> AnalysisResult`
  - `regional_landslide_summary(state_column="state") -> AnalysisResult`

- `CycloneAnalyzer(data, storm_id_column="storm_id", time_column="time", latitude_column="latitude", longitude_column="longitude", wind_column="wind", pressure_column="pressure", wind_unit="km/h", pressure_unit="hPa")`
  - `cyclone_intensity() -> AnalysisResult`
  - `track_distance() -> AnalysisResult`
  - `closest_approach(latitude, longitude) -> AnalysisResult`
  - `cyclone_frequency() -> AnalysisResult`
  - `proximity(latitude, longitude, radius_km) -> AnalysisResult`
  - `imd_cyclone_classification() -> AnalysisResult`
  - `convert_wind_units(from_unit="km/h", to_unit="knots") -> pd.DataFrame`
  - `landfall_analysis(coastline_points=None, proximity_threshold_km=50.0) -> AnalysisResult`
  - `regional_cyclone_exposure(target_lat, target_lon, radius_km=300.0) -> AnalysisResult`
  - `seasonal_cyclone_trend() -> AnalysisResult`

- `MultiHazardAnalyzer`
  - `compare_heat_and_drought(heat_data, drought_data, ...) -> AnalysisResult`
  - `compare_rainfall_and_flood(rainfall_data, flood_events, ...) -> AnalysisResult`
  - `compare_rainfall_and_landslides(rainfall_data, landslide_events, ...) -> AnalysisResult`
  - `regional_multi_hazard_overlap(hazard_datasets, region_type="state") -> AnalysisResult`
  - `composite_hazard_indicator(hazard_metrics, weights=None, normalization="min_max") -> AnalysisResult`

### Forecasting & Projections (`nielytics.forecasting`)
- `TemperatureForecaster(horizons=[1, 3, 7, 14], alpha=1.0)`
  - `fit(data, date_column="date", target_column="tmax") -> TemperatureForecaster`
  - `backtest(horizons=None, min_train_periods=60, step_days=1) -> AnalysisResult`
  - `predict(horizon=7, interval_levels=[0.80, 0.95]) -> AnalysisResult`
  - `forecast_heatwave_risk(forecast_result, threshold_c=40.0) -> AnalysisResult`
  - `save(filepath: str | Path) -> None`
  - `load(filepath: str | Path) -> TemperatureForecaster`
- `ClimateProjectionEngine`
  - `project_trend_extrapolation(historical_data, date_column="date", target_column="tmax", target_years=[2030, 2040, 2050]) -> AnalysisResult`
  - `project_cmip6_scenarios(baseline_temperature_c, target_years=[2030, 2040, 2050], scenarios=["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]) -> AnalysisResult`
- `OperationalForecastAdapter`
  - `apply_bias_correction(forecast_df, ground_truth_df, ...) -> pd.DataFrame`

### Deterministic Insight Engine (`nielytics.insights`)
- `InsightEngine`
  - `generate_insights(analysis_results, data_quality_report=None) -> AnalysisResult`
- `Insight(category, headline, description, metrics, geographic_scope, date_range, confidence, limitations)`

### Result Schema
- `AnalysisResult(feature, data, metadata, warnings)`
  - `to_dict() -> dict[str, Any]` (strictly JSON compliant; `allow_nan=False` guaranteed)
