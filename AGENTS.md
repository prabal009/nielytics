# NIElytics development instructions

Read the entire `NIElytics_MASTER_PROMPT.md` before changing project scope. It is the authoritative specification; this file is a concise guide, not a replacement.

## Ownership and scientific boundaries
- Build only the reusable Python `nielytics` library, tests, docs, and standalone examples. Teammates own ClimateLens India frontend, backend routes, map UI, authentication, databases, and deployment. No servers, dashboards, or application infrastructure.
- Cover five hazards incrementally: heatwaves, floods, droughts, rainfall-triggered landslides, and tropical cyclones.
- Temperature extremes are not official heatwave declarations; rainfall/discharge indicators are not confirmed flooding; rainfall deficits/SPI are not declared drought; susceptibility is not a confirmed landslide or validated prediction; cyclone exposure is not damage. Correlation is not causation. Missing hazards are not zero risk.

## Architecture and implementation
- Python 3.11+, `src/nielytics`, Hatchling, NumPy/Pandas/SciPy. Heavy visualization, geospatial, and climate dependencies must be optional.
- Implement core loading/cleaning/profiling/statistics first, then time series and visualization, climate algorithms, data connectors, standardization, geospatial output, integration facade, and advanced analysis/reporting. Keep each milestone runnable. Do not create empty placeholder modules.
- Preserve existing work. Validate parameters, dates, columns, units, and coordinates. Do not infer unknown units. Do not silently delete observations or mutate caller data. Return structured results, never only printed text.
- Public functions need type hints, useful docstrings, predictable exceptions, tests, and documentation. No import-time network calls or GUI launch. Avoid global application state and unnecessary abstractions.

## External integrations (required future milestones)
- Use only the specified endpoints: Open-Meteo historical `https://archive-api.open-meteo.com/v1/archive`; flood `https://flood-api.open-meteo.com/v1/flood`; NASA POWER `https://power.larc.nasa.gov/api/temporal/daily/point`; NASA COOLR `https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer`; NASA catalog `https://data.nasa.gov/dataset/global-landslide-catalog-export`; NOAA NI IBTrACS `https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv`.
- Verify actual endpoints, response schemas, coverage, units, missing-value conventions, licensing, and authentication before implementing a connector. Record evidence and failures honestly. Never invent endpoints or secrets. Use public access where available; if authentication is required, read credentials from documented environment variables and explain how to obtain them.
- Discover ArcGIS layers and query capabilities from metadata; respect pagination/limits. Preserve IBTrACS IDs, units, and chronological timestamps.
- Connectors require configurable timeouts, bounded retries/backoff, rate-limit handling, dependency injection, provenance, retrieval time, coverage, and explicit offline/cache expiration policies.
- Distinguish historical/reanalysis/modeled data, current observations, and forecasts. Historical catalogs are not live warning feeds.
- All geographic outputs must support conversion to appropriate map-ready structures. GeoJSON uses EPSG:4326 and longitude/latitude order. Support points, multipart points, tracks, polygons, and multipart geometries when implemented. Keep large grids/raster data separate. Attach source, period, units, method, and limitations.
- Define schemas before implementing ClimateAnalytics. Unsupported coverage or operations must raise explicit errors, never synthesize data. No unimplemented APIs in working examples.

## Verification and handoff
- Use a virtual environment, never system-wide installs. Pytest normal suite is deterministic/offline; live checks are explicit opt-in. Test real numerical results, missing data, invalid inputs, nonmutation, serialization, optional dependency failures, and backend-style imports.
- Run affected tests and a real installed-package example for every milestone. Do not claim unexecuted verification. Update README, API docs, INTEGRATION_CONTRACT.md, source documentation, and team handoff as capabilities land.
- Keep a clear implemented/pending distinction. No credentials, destructive changes, unrelated files, or remote pushes. Confirm competition rules on prebuilt libraries separately.
