# NIElytics commands and usage

Run shell commands below from the project root (the directory containing `pyproject.toml`). These instructions are for Linux/bash. Core analytics, all ten visualization categories, five input-driven hazard analyzers, four verified provider sources, and EPSG:4326 GeoJSON exporters are implemented. A configured `ClimateAnalytics` facade, forecasts, and official disaster warnings are not.

## 1. Create and activate an environment

Keep the environment on your Linux home filesystem, not the removable drive: this project drive rejected virtual-environment symlinks during setup.

```bash
python3 --version
mkdir -p "$HOME/.venvs"
python3 -m venv --copies "$HOME/.venvs/nielytics"
source "$HOME/.venvs/nielytics/bin/activate"
python -m pip install -e '.[dev]'
```

Python 3.11 or newer is required. `-e` installs the complete local runtime dependency set in editable mode; `dev` adds testing/build tools. Excel, Parquet, visualization, and geospatial dependencies are included in the standard install. Installation needs network access for dependencies; ordinary usage and tests are offline.

NIElytics 0.1.0 is published on [PyPI](https://pypi.org/project/nielytics/0.1.0/). Teammates can install all currently implemented runtime features in their own activated Python 3.11+ environment without cloning this repository:

```bash
python -m pip install nielytics
```

Use `python -m pip install nielytics==0.1.0` to pin this release. The editable command above is for developing this checkout; it also installs development tools.

For later terminal sessions, activate the existing environment (do not recreate it):

```bash
source "$HOME/.venvs/nielytics/bin/activate"
python -c 'import nielytics; print(nielytics.__version__); print(nielytics.__file__)'
```

A previous session created `/tmp/nielytics-core-20261029`. If it still exists, it can be activated instead, but temporary environments may disappear after reboot. That environment last contained an installed wheel; run `python -m pip install -e '.[dev]'` to switch it to editable source before development tests.


## 2. Run tests

```bash
# Entire offline test suite
python -m pytest -q

# Detailed test names
python -m pytest -v

# One module
python -m pytest tests/test_loader.py -v
python -m pytest tests/test_cleaner.py -v
python -m pytest tests/test_profiler.py -v
python -m pytest tests/test_statistics.py -v
python -m pytest tests/test_dataset.py -v
python -m pytest tests/test_visualization.py -v

# Stop at the first failure
python -m pytest -x -v

# Select tests by name
python -m pytest -k serialization -v

# Check source, tests, and examples without changing files
python -m ruff check src tests examples
```

Run `python -m pytest -q` for the current offline test count; do not infer endpoint availability or official classification from a green suite. The normal suite makes no live provider requests.

## 3. Run the working example

```bash
python examples/basic_analysis.py
```

It uses explicitly synthetic data, parses dates, removes a duplicate, fills one missing value, and prints strict JSON plus a statistical table. Expected cleaned values: `[10.0, 20.0, 15.0]`; mean: `15.0`; sample variance: `25.0`. It asserts that the original dataset still has four rows.

### Display every supported graph

```bash
# Export nine offline interactive HTML files and one geographic PNG:
python examples/visualization_gallery.py --output-dir charts

# Explicitly open the nine HTML charts in your browser:
python examples/visualization_gallery.py --output-dir charts --show
```

Open `charts/geographic.png` in an image viewer. The example uses synthetic generic measurements, not verified climate data. Re-running replaces files with the same names. No server, dashboard, external API, or basemap download is involved.
### Run all five input-driven hazard indicators

```bash
python examples/climate_indicators.py
```

The example builds synthetic temperature, rainfall, terrain and storm data, computes an indicator for each of heat, flood-related rainfall, drought-related dry spells, cyclone track distance, and rainfall/slope landslide susceptibility, and exports a synthetic point to GeoJSON. Its JSON is **not** a provider response, forecast, validated risk prediction, or official warning. Methods are documented in [API reference](docs/api_reference.md).

### Explicit historical provider request

```python
from nielytics.climate.providers import HTTPClient, fetch_historical_weather

# Real historical modeled/reanalysis provider data; requires network access.
client = HTTPClient(timeout=15, retries=2)
result = fetch_historical_weather(12.2958, 76.6394, \"2025-01-01\", \"2025-01-03\", client=client)
records = result.to_dict()[\"data\"][\"records\"]
print(records, result.to_dict()[\"metadata\"])
```

No credential is required by sampled public endpoints; verify licensing/attribution for your intended use. For deterministic offline processing, pass an `HTTPClient` with `cache_dir` and explicit TTL, then set `offline=True` for later requests. See [data sources](docs/DATA_SOURCES.md). No request happens on import.

Creating a figure does **not** display it: this is required by the master prompt for backend safety. For your own DataFrame (or `dataset.frame`), use:

```python
import pandas as pd
from nielytics.core.visualization import (
    plot_line, plot_bar, plot_histogram, plot_box, plot_scatter,
    plot_correlation, plot_timeseries, plot_distribution, plot_seasonal,
    plot_geographic,
)

# Synthetic data. Replace with your own columns; units are never inferred.
frame = pd.DataFrame({
    "date": pd.date_range("2025-01-01", periods=4, freq="MS"),
    "sample": [1, 2, 3, 4], "value": [4., 8., 5., 7.],
    "longitude": [76., 77., 78., 79.], "latitude": [12., 13., 14., 15.],
})
line = plot_line(frame, "sample", "value")
bar = plot_bar(frame, "sample", "value")
histogram = plot_histogram(frame, "value", bins=10)
box = plot_box(frame, columns=["value"])
scatter = plot_scatter(frame, "sample", "value")
correlation = plot_correlation(frame[["sample", "value"]])
timeseries = plot_timeseries(frame, "date", "value")
distribution = plot_distribution(frame, "value", bins=10)
seasonal = plot_seasonal(frame, "date", "value", aggregation="mean")
geographic = plot_geographic(frame, value="value")

line.show(renderer="browser")  # Explicit interactive display on a desktop.
line.write_html("line.html", include_plotlyjs=True, auto_open=False)
chart_json = line.to_json()    # Chart specification, not table records.
geographic.savefig("locations.png", dpi=150, bbox_inches="tight")
```

The first nine functions return Plotly figures; `plot_geographic` returns a Matplotlib figure. All accept `title=`. Histograms show counts; distributions show probability density, not a fitted KDE. Seasonal charts aggregate each calendar month across years, leaving absent months missing. Time-series plots sort dates but do not interpolate or infer missing dates. Line plots retain input order.

For supplied boundaries or tracks, install `geospatial`, load your local vector file with `geopandas.read_file(...)`, and pass its GeoDataFrame to `plot_geographic(gdf, value="your_numeric_column")`. A known CRS is required and is transformed to EPSG:4326. Points, multipoints, lines, multilines, polygons, and multipolygons are supported; geometry plotting is not hazard detection or GeoJSON generation.

**If nothing appears:** a terminal does not render returned figures. Call `.show(renderer="browser")` explicitly, or open the saved HTML. On SSH/headless machines use export and open the files on your desktop; do not expect GUI windows. Notebook users can display the returned Plotly figure using their notebook's configured renderer; HTML export avoids notebook renderer dependencies. Geographic figures use `.savefig()`, not Plotly's `.show()`. Plotly static PNG/PDF export additionally requires its optional Kaleido/Chrome setup; the gallery deliberately uses HTML instead.

Missing optional packages raise `OptionalDependencyError`; activate the same environment used for installation. Invalid columns, dates, numeric values, or coordinates raise `ValidationError`. Missing statistical observations are reported rather than silently treated as zero. See the API reference for each missing-data policy.

## 4. Try the library interactively

Start Python from the activated terminal:

```bash
python
```

Paste this Python code (or save it in your own `.py` script and run `python your_script.py`):

```python
import json
import pandas as pd
from nielytics import Dataset

# Synthetic generic measurements, not actual weather observations.
original = Dataset(pd.DataFrame({
    "date": ["2025-01-01", "2025-01-02", "2025-01-02", "2025-01-03"],
    "value": [10.0, 20.0, 20.0, None],
}))

print(original.missing_report())
print(original.profile())

cleaned = (
    original.parse_dates("date")
    .remove_duplicates()
    .fill_missing(columns=["value"], strategy="mean")
)

print(cleaned.frame)
print(cleaned.summary())                 # sample variance, ddof=1
print(cleaned.summary(ddof=0))           # population variance
print(cleaned.history)
print(original.frame)                   # unchanged

payload = {"profile": cleaned.profile(), "records": cleaned.to_records()}
print(json.dumps(payload, allow_nan=False, indent=2))
```

Use `exit()` to leave Python. Cleaning returns a **new** Dataset: keep the returned value. On mixed tables, explicitly select numeric columns for mean/median filling. Missing observations are not automatically zero, and statistical filling is not a climate-quality guarantee.

## 5. Load your own files

The following are Python examples; replace filenames and column names with your own. Relative paths are resolved from your terminal's current directory.

```python
from nielytics import Dataset

csv_data = Dataset("measurements.csv", parse_dates=["date"], encoding="utf-8")
excel_data = Dataset("measurements.xlsx", sheet_name="Sheet1")
json_data = Dataset("measurements.json")
parquet_data = Dataset("measurements.parquet")

# Explicit source date format:
dated = Dataset("measurements.csv", parse_dates={"date": "%d/%m/%Y"})

# Explicit column-name normalization and string cleanup:
cleaned = csv_data.standardize_columns().clean_text()

# Explicit dtype conversion:
converted = cleaned.convert_types({"value": "float64"})
```

CSV and JSON support configurable encodings. Excel/Parquet need their optional reader dependencies. Load one Excel sheet at a time; this API returns one DataFrame, not a dictionary of sheets. Legacy `.xls` may need the separate `xlrd` reader (`python -m pip install xlrd`). URLs are not supported by the current local-file loader.

## 6. Use statistical functions directly

```python
from nielytics.core.statistics import (
    correlation_matrix, covariance_matrix, frequency_distribution,
    grouped_summary, modes, quantiles, summarize,
)

# `cleaned` is the Dataset from section 4.
frame = cleaned.frame
print(summarize(frame, columns=["value"]))
print(quantiles(frame, columns=["value"], q=[0.25, 0.5, 0.95]))
print(modes(frame, columns=["value"]))
print(correlation_matrix(frame))
print(covariance_matrix(frame))
print(frequency_distribution(frame, "value"))

grouped = frame.assign(region=["A", "A", "B"])
print(grouped_summary(grouped, by="region", columns=["value"]))
```

Statistics skip missing values; sample variance/std use `ddof=1`. Insufficient observations and constant-column correlations can yield missing values. No unit conversion or scientific hazard classification happens implicitly.

For irregular daily series and exploratory outlier flags:

```python
from nielytics.core.timeseries import rolling_mean, missing_dates, calculate_anomalies
from nielytics.core.outliers import detect_outliers

# Synthetic measurements, not climate observations. Windows count observed rows.
daily = pd.DataFrame({"date": ["2024-01-01", "2024-01-02", "2025-01-01"],
                      "value": [10., 14., 20.]})
print(rolling_mean(daily, "date", "value", window=2))
print(missing_dates(daily, "date", "value"))
print(calculate_anomalies(daily, "date", "value",
                          baseline_start="2024-01-01", baseline_end="2024-12-31"))
print(detect_outliers(daily, "value", method="iqr"))
```

An anomaly needs baseline observations in the matching calendar month; unsupported months remain null. Outlier masks never delete rows.

## 7. Save results or hand them to a backend

```python
import json
from pathlib import Path

# These commands write files in the current directory, replacing them if present.
cleaned.frame.to_csv("cleaned_measurements.csv", index=False)
Path("analysis_results.json").write_text(
    json.dumps({"profile": cleaned.profile(), "records": cleaned.to_records()},
               allow_nan=False, indent=2),
    encoding="utf-8",
)
```

`profile()` and `to_records()` are JSON-compatible. Records omit the DataFrame index, use ISO dates with millisecond precision, and encode missing/nonfinite values as null. Raw DataFrames and arbitrary history parameter objects need explicit serialization. Table records are **not GeoJSON**.

Teammates can use the same Python imports within their backend; they own routing, authentication, storage, and frontend rendering. See [INTEGRATION_CONTRACT.md](INTEGRATION_CONTRACT.md).

## 8. Handle library errors

```python
from nielytics import Dataset, NIElyticsError

try:
    data = Dataset("measurements.csv", parse_dates=["date"])
except NIElyticsError as error:
    print(type(error).__name__, str(error))
```

Subtypes: `ValidationError`, `DataLoadError`, `UnsupportedFormatError`, and `OptionalDependencyError`. Do not expose internal paths/error details directly to untrusted application users.

## 9. Build and install distributable artifacts

```bash
python -m build
```

For version 0.1.0 this produces `dist/nielytics-0.1.0-py3-none-any.whl` and `dist/nielytics-0.1.0.tar.gz`. To check the wheel in your environment:

```bash
python -m pip install --force-reinstall --no-deps dist/nielytics-0.1.0-py3-none-any.whl
python examples/basic_analysis.py
```

`--no-deps` assumes dependencies were installed in section 1. This replaces the editable installation with the built copy. Restore editable development afterward:

```bash
python -m pip install -e '.[dev]'
```

Release 0.1.0's wheel and source distribution passed `twine check --strict` and were uploaded to PyPI. The published wheel was downloaded from PyPI into an existing virtual environment and successfully exercised with `examples/basic_analysis.py`. Installing from PyPI uses the published release, not uncommitted changes in this checkout.

## 10. Finish your session

```bash
deactivate
```

If imports fail, activate the correct environment and reinstall the local project using that environment's `python -m pip`. If pytest finds no tests, run it from the project root. For complete function contracts, see [docs/api_reference.md](docs/api_reference.md).
