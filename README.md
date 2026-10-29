# NIElytics

Independent Python analytics library for ClimateLens India (SDG 13). This repository implements core analytics and optional visualization, not a frontend, backend, or operational disaster service.

For step-by-step setup, every testing/build command, and practical Python examples, see [Commands and usage](COMMANDS_AND_USAGE.md).

## Implemented library capabilities (0.1.0 development tree)

- Installable `src` package; Python 3.11+.
- Local CSV, Excel, JSON, Parquet and DataFrame loading with explicit date parsing.
- Non-mutating `Dataset` cleaning and operation history.
- Missing-value reports, JSON-compatible profiling, descriptive/grouped statistics, correlations and covariance.
- JSON-safe table records and a standalone synthetic-data integration example.
- Explicit rolling means, missing-date detection, monthly baseline anomalies, and descriptive outlier masks.
- Optional line, bar, histogram, box, scatter, correlation, time-series, distribution, seasonal, and geographic figures; explicit display/export, never automatic GUI launch.

## Install

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/python examples/basic_analysis.py
```

For filesystems that do not support virtual-environment symlinks (some removable drives), put the environment on a native filesystem instead, e.g. `python3 -m venv --copies /tmp/nielytics-env`, then use that environment's Python. `/tmp` is temporary; choose a persistent native-filesystem location for ongoing work.

NIElytics 0.1.0 is published on [PyPI](https://pypi.org/project/nielytics/0.1.0/). Install the current release with `python -m pip install nielytics`, or install this checkout with `python -m pip install /path/to/nielytics`. Core analytics, Excel and Parquet readers, visualization, and geospatial plotting dependencies are included in the standard install. Development dependencies are not.

## Quick start

```python
import pandas as pd
from nielytics import Dataset

# Synthetic demonstration, not climate observations.
data = Dataset(pd.DataFrame({"value": [10.0, 20.0, None]}))
cleaned = data.fill_missing(columns=["value"], strategy="mean")
print(cleaned.summary())
payload = {"profile": cleaned.profile(), "records": cleaned.to_records()}
```

`Dataset("measurements.csv", parse_dates=["date"])` loads a local file. Source data and existing Dataset instances are preserved; cleaning returns a new Dataset. The `frame` and `history` properties return copies. Pandas deep copies do not recursively isolate mutable objects inside cells: use scalar table values.

Statistics skip missing values. Variance/std default to sample statistics (`ddof=1`); insufficient data produces missing results, not invented zeroes. No unit conversion or climate interpretation is implicit. `to_records()` omits the index, encodes dates as ISO strings at millisecond precision, and maps missing/nonfinite values to JSON null.

## Display and export graphs

```bash
python -m pip install -e .
python examples/visualization_gallery.py --output-dir charts
# Explicitly open interactive charts in your browser:
python examples/visualization_gallery.py --output-dir charts --show
```

The gallery uses synthetic measurements and writes nine interactive HTML charts plus a geographic PNG. Open the HTML files in a browser; they embed Plotly and work offline. Functions in `nielytics.core.visualization` return figures, not windows. Use `fig.show()` explicitly for Plotly, `fig.write_html(...)`/`fig.to_json()` for export, and `fig.savefig(...)` for geographic Matplotlib figures. See [Commands and usage](COMMANDS_AND_USAGE.md) for all ten function calls and display troubleshooting.

## Architecture and limitations

`nielytics` is one installable package. `Dataset`, ten plotting functions, `AnalysisResult`, and the five hazard analyzers are importable from the package root. Internal modules remain available under `nielytics.core`, `nielytics.hazards`, `nielytics.climate.providers`, and `nielytics.geospatial`. Optional plotting dependencies are imported on use, not on core import.

Heat, rainfall/flood, drought, landslide and cyclone analyzers return explicitly labeled **indicators** from caller-provided inputs. They do not issue official declarations or validated predictions. Climate connectors require explicit calls, preserve provider attribution, and distinguish historical modeled data from event catalogs. The NASA COOLR service URL returned HTTP 404; catalog access and provider coverage are documented in [data sources](docs/DATA_SOURCES.md). No live alert or forecast feed is claimed. Unsupported provider fields and regions are not fabricated. See [API reference](docs/api_reference.md), [integration contract](INTEGRATION_CONTRACT.md), [GeoJSON guide](docs/GEOJSON_GUIDE.md), and [team handoff](docs/TEAM_HANDOFF.md).

The full long-term master specification includes advanced comparisons, automatic insights, reporting, and an optional configured facade; these are **not implemented**. External licensing and competition rules on prebuilt libraries require separate confirmation. Teammates own routing, authentication, storage, and display.

## Synthetic hazard and map example

```sh
python examples/climate_indicators.py
```

The output contains five JSON-compatible indicator results and an EPSG:4326 GeoJSON point; all measurements are synthetic demonstrations, not provider observations. For real historical provider data, call the connectors explicitly using `nielytics.climate.providers` and check the source metadata. See [commands and usage](COMMANDS_AND_USAGE.md).

## Release preparation

NIElytics is distributed under the [MIT license](LICENSE). Release 0.1.0's wheel and source distribution passed Twine's strict checks and were uploaded to PyPI. The published wheel was downloaded into an existing virtual environment and successfully exercised with `examples/basic_analysis.py`.

For future releases, use a virtual environment. Run `python -m pytest`, `python -m ruff check src tests examples`, the installed-package examples, and `python -m build` before validating and uploading the new distributions.
