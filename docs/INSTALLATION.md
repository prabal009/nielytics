# NIElytics Installation & Environment Setup Guide

## 1. System Requirements
- **Operating Systems**: Linux (Ubuntu, Debian, Kali Linux, Arch), macOS, Windows 10/11 (WSL2 recommended).
- **Python Version**: Python 3.11, 3.12, or 3.13.
- **Base Dependencies**: `numpy>=1.26`, `pandas>=2.2,<3`, `scipy>=1.12`.

---

## 2. Installation Options

### Option A: Install from GitHub Development Tree
To install the latest development tree directly from GitHub:
```bash
python3 -m pip install "git+https://github.com/prabal009/nielytics.git"
```

### Option B: Local Editable Clone
For active development, run:
```bash
git clone https://github.com/prabal009/nielytics.git
cd nielytics
python3 -m pip install -e '.[dev]'
```

---

## 3. Optional Dependency Extras
NIElytics enforces a zero-bloat core philosophy. Specialized features can be enabled with targeted extras:

| Extra Group | Packages | Functionality |
|---|---|---|
| `excel` | `openpyxl>=3.1` | Excel file loading (`.xlsx`, `.xls`) |
| `parquet` | `pyarrow>=15` | Fast columnar Parquet file ingestion |
| `visualization` | `plotly>=5.24`, `matplotlib>=3.9` | Interactive HTML and static figure charts |
| `geospatial` | `geopandas>=1.0`, `shapely>=2.0`, `pyproj>=3.6` | Shapefile loading and vector operations |
| `climate` | `xarray>=2024.1`, `netCDF4>=1.6` | Gridded NetCDF climate dataset loading |
| `advanced-statistics` | `statsmodels>=0.14`, `scikit-learn>=1.4` | Specialized machine learning estimators |
| `dev` | `pytest>=8`, `pytest-cov>=4`, `ruff>=0.9`, `build>=1.2` | Development, linting, and testing |
| `all` | All of the above | Full optional battery |

```bash
# Example: Install visualization and geospatial extras
pip install -e '.[visualization,geospatial]'
```

---

## 4. Kali Linux / Linux Native Filesystems Note
When developing on external removable drives (e.g. exFAT / FAT32 USB storage) where filesystem symlinks are not supported by the kernel:
1. Create your virtual environment on a native ext4 / btrfs mount point:
   ```bash
   python3 -m venv --copies ~/.virtualenvs/nielytics
   source ~/.virtualenvs/nielytics/bin/activate
   pip install -e '.[dev]'
   ```
2. Run tests directly:
   ```bash
   PYTHONPATH=src pytest
   ```
