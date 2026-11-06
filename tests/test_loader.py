import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from nielytics.core.loader import (
    load_csv,
    load_dataset,
    load_excel,
    load_geojson_table,
    load_json,
    load_netcdf,
    load_parquet,
    load_shapefile,
    load_text,
)
from nielytics.exceptions import (
    DataLoadError,
    OptionalDependencyError,
    UnsupportedFormatError,
    ValidationError,
)


def test_dataframe_is_copied_and_names_preserved():
    frame = pd.DataFrame({" Original Name ": [1, 2]})
    result = load_dataset(frame)
    assert_frame_equal(result, frame)
    assert result is not frame
    result.iloc[0, 0] = 99
    assert frame.iloc[0, 0] == 1


def test_dataframe_date_parsing_does_not_mutate():
    frame = pd.DataFrame({"Date Name": ["31/12/2025"]})
    before = frame.copy(deep=True)
    result = load_dataset(frame, parse_dates={"Date Name": "%d/%m/%Y"})
    assert result.loc[0, "Date Name"] == pd.Timestamp("2025-12-31")
    assert_frame_equal(frame, before)


def test_csv_encoding_reader_options_and_date_parsing(tmp_path):
    path = tmp_path / "records.CSV"
    path.write_bytes("Date Name;City\n2025-12-31;Montréal\n".encode("latin-1"))
    frame = load_dataset(path, encoding="latin-1", sep=";", parse_dates=["Date Name"])
    assert frame.columns.tolist() == ["Date Name", "City"]
    assert frame.loc[0, "City"] == "Montréal"
    assert frame.loc[0, "Date Name"] == pd.Timestamp("2025-12-31")
    assert_frame_equal(frame, load_csv(path, encoding="latin-1", sep=";", parse_dates="Date Name"))


def test_json_dates_are_explicit(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('[{"created_at":"2025-12-31","Original Name":2}]', encoding="utf-8")
    raw = load_json(path)
    assert raw.loc[0, "created_at"] == "2025-12-31"
    dated = load_json(path, parse_dates=["created_at"])
    assert dated.loc[0, "created_at"] == pd.Timestamp("2025-12-31")
    assert dated.columns.tolist() == ["created_at", "Original Name"]


def test_explicit_format_can_override_extension(tmp_path):
    path = tmp_path / "data.bin"
    path.write_text("n\n1\n", encoding="utf-8")
    assert load_dataset(path, format="csv")["n"].tolist() == [1]
    with pytest.raises(UnsupportedFormatError):
        load_dataset(path)
    with pytest.raises(UnsupportedFormatError):
        load_dataset(path, format="pickle")


def test_missing_directory_invalid_and_remote_paths(tmp_path):
    with pytest.raises(DataLoadError):
        load_dataset(tmp_path / "absent.csv")
    with pytest.raises(DataLoadError):
        load_dataset(tmp_path)
    for source in ["https://example.invalid/data.csv", "s3://bucket/data.parquet", "file:///tmp/data.csv", "//server/data.csv", "", 42]:
        with pytest.raises(ValidationError):
            load_dataset(source)


def test_read_failure_is_wrapped(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(DataLoadError) as error:
        load_json(path)
    assert error.value.__cause__ is not None


@pytest.mark.parametrize("wrapper,reader,suffix", [(load_excel, "read_excel", ".xlsx"), (load_parquet, "read_parquet", ".parquet")])
def test_optional_dependency_error(tmp_path, monkeypatch, wrapper, reader, suffix):
    path = tmp_path / ("data" + suffix)
    path.touch()

    def unavailable(*args, **kwargs):
        raise ImportError("missing optional engine")

    monkeypatch.setattr(pd, reader, unavailable)
    with pytest.raises(OptionalDependencyError, match="optional"):
        wrapper(path)


@pytest.mark.parametrize("wrapper,reader,suffix", [(load_excel, "read_excel", ".xlsx"), (load_parquet, "read_parquet", ".parquet")])
def test_optional_readers_use_common_date_contract(tmp_path, monkeypatch, wrapper, reader, suffix):
    path = tmp_path / ("data" + suffix)
    path.touch()
    original = pd.DataFrame({"Date Name": ["2025-12-31"]})
    before = original.copy(deep=True)
    monkeypatch.setattr(pd, reader, lambda *args, **kwargs: original)
    result = wrapper(path, parse_dates="Date Name")
    assert result.loc[0, "Date Name"] == pd.Timestamp("2025-12-31")
    assert_frame_equal(original, before)


def test_excel_real_roundtrip_when_engine_available(tmp_path):
    pytest.importorskip("openpyxl")
    path = tmp_path / "data.xlsx"
    frame = pd.DataFrame({"Original Name": [1, 2]})
    frame.to_excel(path, index=False, engine="openpyxl")
    assert_frame_equal(load_excel(path, engine="openpyxl"), frame)


def test_parquet_real_roundtrip_when_engine_available(tmp_path):
    pytest.importorskip("pyarrow")
    path = tmp_path / "data.parquet"
    frame = pd.DataFrame({"Original Name": [1, 2]})
    frame.to_parquet(path, engine="pyarrow", index=False)
    assert_frame_equal(load_parquet(path, engine="pyarrow"), frame)


def test_invalid_dates_and_missing_columns():
    frame = pd.DataFrame({"d": ["invalid"]})
    with pytest.raises(ValidationError):
        load_dataset(frame, parse_dates=["d"])
    with pytest.raises(ValidationError):
        load_dataset(frame, parse_dates=["missing"])
    with pytest.raises(ValidationError):
        load_dataset(frame, parse_dates=True)
    with pytest.raises(ValidationError):
        load_dataset(frame, format="csv")


def test_reader_must_return_single_frame(tmp_path, monkeypatch):
    path = tmp_path / "data.xlsx"
    path.touch()
    monkeypatch.setattr(pd, "read_excel", lambda *args, **kwargs: {"sheet": pd.DataFrame()})
    with pytest.raises(DataLoadError, match="single DataFrame"):
        load_excel(path, sheet_name=None)


def test_load_text_and_tsv(tmp_path):
    tsv_path = tmp_path / "data.tsv"
    tsv_path.write_text("a\tb\n1\t2\n3\t4\n")
    df_tsv = load_text(tsv_path)
    assert list(df_tsv.columns) == ["a", "b"]
    assert len(df_tsv) == 2
    assert df_tsv.iloc[0]["a"] == 1

    txt_path = tmp_path / "data.txt"
    txt_path.write_text("col1|col2\nval1|val2\n")
    df_txt = load_text(txt_path, delimiter="|")
    assert list(df_txt.columns) == ["col1", "col2"]
    assert df_txt.iloc[0]["col1"] == "val1"


def test_load_geojson_table(tmp_path):
    import json
    geo_path = tmp_path / "points.geojson"
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Station A", "temp": 28.5},
                "geometry": {"type": "Point", "coordinates": [77.59, 12.97]},
            },
            {
                "type": "Feature",
                "properties": {"name": "Station B", "temp": 30.1},
                "geometry": {"type": "Point", "coordinates": [72.87, 19.07]},
            },
        ],
    }
    geo_path.write_text(json.dumps(data))
    df = load_geojson_table(geo_path)
    assert len(df) == 2
    assert "name" in df.columns
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert df.iloc[0]["latitude"] == 12.97
    assert df.iloc[0]["longitude"] == 77.59


def test_load_netcdf_and_shapefile_optional_guards(tmp_path):
    nc_path = tmp_path / "dummy.nc"
    nc_path.touch()
    try:
        import xarray  # noqa: F401
    except ImportError:
        try:
            import netCDF4  # noqa: F401
        except ImportError:
            with pytest.raises(OptionalDependencyError):
                load_netcdf(nc_path)

    shp_path = tmp_path / "dummy.shp"
    shp_path.touch()
    try:
        import geopandas  # noqa: F401
    except ImportError:
        with pytest.raises(OptionalDependencyError):
            load_shapefile(shp_path)
