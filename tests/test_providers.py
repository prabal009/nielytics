"""Offline contract fixtures modeled on verified provider JSON/CSV responses."""

import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from nielytics.climate.providers import (
    HTTPClient,
    OfflineCacheError,
    ProviderError,
    ResponseError,
    analyze_discharge_anomalies,
    cyclone_frequency,
    cyclone_tracks_to_geojson,
    fetch_historical_weather,
    fetch_landslide_events,
    fetch_nasa_power_data,
    fetch_river_discharge,
    filter_landslides_by_region,
    get_cyclone_intensity,
    get_cyclone_tracks,
    landslide_events_to_geojson,
    load_ibtracs,
    load_landslide_catalog,
)
from nielytics.exceptions import ValidationError


class Reply(io.BytesIO):
    status = 200


class Stub:
    def __init__(self, payload):
        self.payload = payload
        self.urls = []

    def __call__(self, request, timeout):
        self.urls.append((request.full_url, timeout))
        if isinstance(self.payload, Exception):
            raise self.payload
        if callable(self.payload):
            return self.payload(request, timeout)
        return Reply(self.payload if isinstance(self.payload, bytes) else json.dumps(self.payload).encode())


def client(payload):
    return HTTPClient(opener=Stub(payload), retries=0)


WEATHER = {"latitude": 12.267136, "longitude": 76.62162, "timezone": "Asia/Kolkata",
           "daily_units": {"time": "iso8601", "temperature_2m_max": "°C", "precipitation_sum": "mm"},
           "daily": {"time": ["2025-01-01", "2025-01-02"], "temperature_2m_max": [28.6, None],
                     "precipitation_sum": [0, 12.1]}}
FLOOD = {"latitude": 12.275002, "longitude": 76.625, "timezone": "GMT",
         "daily_units": {"time": "iso8601", "river_discharge": "m³/s"},
         "daily": {"time": ["2025-01-01", "2025-01-02", "2025-01-03"], "river_discharge": [0.06, None, 0.12]}}
POWER = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [76.639, 12.296, 714.58]},
         "properties": {"parameter": {"PRECTOTCORR": {"20250101": 0, "20250102": -999},
                                      "T2M_MAX": {"20250101": 29.04, "20250102": 28.75}}},
         "header": {"fill_value": -999, "time_standard": "LST", "sources": ["MERRA2", "POWER"]},
         "parameters": {"PRECTOTCORR": {"units": "mm/day"}, "T2M_MAX": {"units": "C"}}}
CSV = ("SID,SEASON,BASIN,NAME,ISO_TIME,LAT,LON,WMO_WIND,USA_WIND,TRACK_TYPE\n"
       " ,Year, , , ,degrees_north,degrees_east,kts,kts, \n"
       "2025001N10080,2025,NI,TEST,2025-01-02 12:00:00,12,79,50,55,main\n"
       "2025001N10080,2025,NI,TEST,2025-01-01 06:00:00,11,80, ,45,main\n"
       "2025001N10080,2025,NI,TEST,2025-01-03 06:00:00, , , , ,main\n"
       "2025002N12081,2025,NI,OTHER,2025-01-05 06:00:00,13,81,60, ,main\n")

GLC = ("event_id,event_date,longitude,latitude,country_code,landslide_trigger\n"
       "42,07/22/2009 12:00:00 AM,88.3143,26.8572,IN,downpour\n"
       "43,07/23/2009 12:00:00 AM,,26.8572,IN,rain\n"
       "44,,81.708,28.8378,NP,monsoon\n")


def test_open_meteo_response_and_units():
    stub = Stub(WEATHER)
    result = fetch_historical_weather(12.2958, 76.6394, "2025-01-01", "2025-01-02",
                                      daily=("temperature_2m_max", "precipitation_sum"), client=HTTPClient(opener=stub))
    assert result.data["records"][1]["temperature_2m_max"] is None
    assert result.metadata["grid_cell"]["latitude"] == 12.267136
    assert result.metadata["units"]["precipitation_sum"] == "mm"
    assert result.metadata["cached"] is False
    assert result.to_dict()["status"] == "success"
    params = parse_qs(urlsplit(stub.urls[0][0]).query)
    assert params["timezone"] == ["Asia/Kolkata"] and params["precipitation_unit"] == ["mm"]


@pytest.mark.parametrize("bad", [
    {**WEATHER, "daily_units": {"temperature_2m_max": "°F", "precipitation_sum": "mm"}},
    {**WEATHER, "daily": {"time": ["2025-01-01"], "temperature_2m_max": [25, 26], "precipitation_sum": [2]}},
    {**WEATHER, "daily": {"time": ["2025-01-02", "2025-01-01"], "temperature_2m_max": [25, 26], "precipitation_sum": [2, 1]}},
    {"error": True, "reason": "bad date"}, {},
])
def test_weather_bad_response(bad):
    with pytest.raises(ResponseError):
        fetch_historical_weather(12, 77, "2025-01-01", "2025-01-02", daily=("temperature_2m_max", "precipitation_sum"), client=client(bad))


def test_weather_rejects_missing_time_units_and_invalid_values():
    bad_units = json.loads(json.dumps(WEATHER))
    bad_units["daily_units"].pop("time")
    with pytest.raises(ResponseError, match="daily.time"):
        fetch_historical_weather(12, 77, "2025-01-01", "2025-01-02",
                                 daily=("temperature_2m_max", "precipitation_sum"), client=client(bad_units))
    bad_precipitation = json.loads(json.dumps(WEATHER))
    bad_precipitation["daily"]["precipitation_sum"][0] = -1
    with pytest.raises(ResponseError, match="Invalid Open-Meteo"):
        fetch_historical_weather(12, 77, "2025-01-01", "2025-01-02",
                                 daily=("temperature_2m_max", "precipitation_sum"), client=client(bad_precipitation))


def test_flood_historical_not_confirmed_and_anomaly():
    result = fetch_river_discharge(12, 77, "2025-01-01", "2025-01-03", client=client(FLOOD))
    assert result.metadata["units"]["river_discharge"] == "m³/s"
    assert "modeled" in result.metadata["data_type"]
    anomaly = analyze_discharge_anomalies(result, baseline_start="2025-01-01", baseline_end="2025-01-03")
    assert anomaly.data["records"][0]["anomaly_percent"] == pytest.approx(-33.3333333)
    assert anomaly.data["records"][1]["anomaly_percent"] is None
    with pytest.raises(ValidationError):
        analyze_discharge_anomalies(result, baseline_start="2025-01-01", baseline_end="2025-01-02")
    with pytest.raises(ValidationError):
        fetch_river_discharge(12, 77, "2025-01-01", "2099-01-03", client=client(FLOOD))

def test_flood_rejects_units_and_incomplete_coverage():
    wrong = json.loads(json.dumps(FLOOD))
    wrong["daily_units"]["river_discharge"] = "mm"
    with pytest.raises(ResponseError):
        fetch_river_discharge(12, 77, "2025-01-01", "2025-01-03", client=client(wrong))
    wrong = json.loads(json.dumps(FLOOD))
    wrong["daily"]["time"].pop(1)
    wrong["daily"]["river_discharge"].pop(1)
    with pytest.raises(ResponseError, match="incomplete"):
        fetch_river_discharge(12, 77, "2025-01-01", "2025-01-03", client=client(wrong))


def test_power_fill_and_time_standard():
    stub = Stub(POWER)
    result = fetch_nasa_power_data(12.2958, 76.6394, "2025-01-01", "2025-01-02", client=HTTPClient(opener=stub))
    assert result.data["records"][1]["PRECTOTCORR"] is None
    assert result.data["records"][0]["T2M_MAX"] == 29.04
    assert result.metadata["missing_value"] == "header.fill_value (-999) normalized to null"
    assert parse_qs(urlsplit(stub.urls[0][0]).query)["time-standard"] == ["LST"]


@pytest.mark.parametrize("change", [
    lambda p: p["header"].pop("fill_value"),
    lambda p: p["parameters"]["PRECTOTCORR"].update(units="inch/day"),
    lambda p: p["properties"]["parameter"]["PRECTOTCORR"].update({"20250201": 2}),
    lambda p: p["properties"]["parameter"]["PRECTOTCORR"].update({"20250101": -10}),
])
def test_power_invalid_response(change):
    payload = json.loads(json.dumps(POWER))
    change(payload)
    with pytest.raises(ResponseError):
        fetch_nasa_power_data(12, 77, "2025-01-01", "2025-01-02", client=client(payload))


def test_ibtracs_source_units_filters_tracks_and_frequency():
    result = load_ibtracs(client=client(CSV.encode()), storm_id="2025001N10080")
    records = result.data["records"]
    assert len(records) == 3 and records[0]["time"] == "2025-01-01T06:00:00+00:00"
    assert records[0]["wmo_wind_kts"] is None and records[-1]["latitude"] is None
    assert result.metadata["units"]["wmo_wind_kts"] == "kts"
    assert cyclone_frequency(result).data["seasons"] == [{"season": 2025, "storm_count": 1}]
    assert get_cyclone_intensity(result).data["storms"][0]["usa_wind_max_kts"] == 55
    assert len(get_cyclone_tracks(result).data["tracks"][0]["observations"]) == 3
    assert len(load_ibtracs(client=client(CSV.encode()), bbox=(79, 11, 80, 12)).data["records"]) == 2
    layer = cyclone_tracks_to_geojson(result)
    assert layer["type"] == "FeatureCollection"
    assert layer["features"][0]["geometry"]["coordinates"] == [[80.0, 11.0], [79.0, 12.0]]


def test_ibtracs_rejects_missing_units_bad_rows_and_other_basins():
    for bad in (CSV.replace("degrees_east", "radians"), CSV.replace("2025-01-02 12:00:00", "bad-time"), ""):
        with pytest.raises(ResponseError):
            load_ibtracs(client=client(bad.encode()))
    with pytest.raises(ValidationError):
        load_ibtracs(client=client(CSV.encode()), basin="WP")

def test_ibtracs_spur_only_track_not_counted():
    source = CSV.replace("2025002N12081,2025,NI,OTHER,2025-01-05 06:00:00,13,81,60, ,main",
                         "2025002N12081,2025,NI,OTHER,2025-01-05 06:00:00,13,81,60, ,spur")
    result = load_ibtracs(client=client(source.encode()), storm_id="2025002N12081")
    assert cyclone_frequency(result).data["seasons"] == []


def test_transport_timeout_retry_and_rate_limit():
    calls = []

    def intermittent(request, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            raise HTTPError(request.full_url, 429, "slow", {"Retry-After": "3"}, None)
        return Reply(b"ok")

    delays = []
    body, _ = HTTPClient(opener=intermittent, retries=1, sleep=delays.append).get("https://example.invalid/public")
    assert body == b"ok" and calls == [20, 20] and delays == [3]
    with pytest.raises(ProviderError, match="Could not retrieve"):
        HTTPClient(opener=Stub(URLError("timeout")), retries=0).get("https://example.invalid/public")
    with pytest.raises(ProviderError, match="HTTP 429"):
        HTTPClient(opener=Stub(HTTPError("https://example.invalid", 429, "slow", {}, None)), retries=0).get("https://example.invalid/public")


def test_explicit_cache_offline_expiry_and_no_network(tmp_path):
    now = [1000000]
    stub = Stub(WEATHER)
    config = {"cache_dir": tmp_path, "ttl_seconds": 10, "clock": lambda: now[0]}
    arguments = (12, 77, "2025-01-01", "2025-01-02")
    opts = {"daily": ("temperature_2m_max", "precipitation_sum")}
    fetch_historical_weather(*arguments, **opts, client=HTTPClient(opener=stub, **config))
    assert len(stub.urls) == 1
    offline = HTTPClient(offline=True, opener=Stub(AssertionError("network used")), **config)
    assert fetch_historical_weather(*arguments, **opts, client=offline).metadata["cached"] is True
    now[0] += 10
    with pytest.raises(OfflineCacheError):
        fetch_historical_weather(*arguments, **opts, client=offline)
    stale = HTTPClient(offline=True, allow_expired_offline=True, **config)
    assert fetch_historical_weather(*arguments, **opts, client=stale).metadata["cache_expired"] is True
    now[0] += 10
    assert fetch_historical_weather(*arguments, **opts, client=HTTPClient(opener=stub, **config)).metadata["cached"] is False
    assert len(stub.urls) == 2


@pytest.mark.parametrize("latitude,longitude", [(91, 77), (12, 181), (float("nan"), 77)])
def test_invalid_coordinates_rejected_before_transport(latitude, longitude):
    with pytest.raises(ValidationError):
        fetch_river_discharge(latitude, longitude, "2025-01-01", "2025-01-02", client=client(FLOOD))

def test_glc_catalog_requires_explicit_terms_before_network():
    stub = Stub(AssertionError("network used before terms acceptance"))
    with pytest.raises(ValidationError, match="export terms"):
        fetch_landslide_events(client=HTTPClient(opener=stub))
    assert stub.urls == []


def test_glc_csv_parse_filter_offline_local_and_geojson(tmp_path):
    stub = Stub(GLC.encode())
    result = fetch_landslide_events(accept_terms=True, client=HTTPClient(opener=stub))
    assert result.data["records"][0]["date"] == "2009-07-22"
    assert result.data["records"][1]["latitude"] is None
    assert result.metadata["coverage"] == {"start": "2009-07-22", "end": "2009-07-23"}
    assert "Global_Landslide_Catalog_Export_rows.csv" in stub.urls[0][0]
    india = filter_landslides_by_region(result, bbox=(80, 20, 90, 30), country_code="in")
    assert [r["event_id"] for r in india.data["records"]] == ["42"]
    layer = landslide_events_to_geojson(result)
    assert [feature["id"] for feature in layer["features"]] == ["42", "44"]
    assert layer["features"][0]["geometry"]["coordinates"] == [88.3143, 26.8572]
    assert "1 records without coordinates omitted." in layer["metadata"]["limitations"]
    local = tmp_path / "glc.csv"
    local.write_text(GLC, encoding="utf-8")
    assert load_landslide_catalog(local).metadata["retrieved_at"] is None
    assert load_landslide_catalog(local).data == result.data


@pytest.mark.parametrize("body", [
    b"", b"event_id,date,latitude,longitude\n42,2020-01-01,20,80\n",
    GLC.replace("88.3143", "nan").encode(),
    GLC.replace("07/22/2009 12:00:00 AM", "unparseable").encode(),
    GLC.replace("IN,downpour", "IN").encode(),
])
def test_glc_rejects_invalid_csv(body):
    with pytest.raises(ResponseError):
        fetch_landslide_events(accept_terms=True, client=client(body))


def test_glc_invalid_region_and_unavailable_local_file(tmp_path):
    result = fetch_landslide_events(accept_terms=True, client=client(GLC.encode()))
    with pytest.raises(ValidationError):
        filter_landslides_by_region(result, bbox=(90, 20, 80, 30))
    with pytest.raises(ValidationError):
        filter_landslides_by_region(result, country_code="IND")
    with pytest.raises(ValidationError, match="Cannot read"):
        load_landslide_catalog(tmp_path / "absent.csv")


def test_transport_retries_nonraising_429_response():
    class RateLimited(Reply):
        status = 429
        headers: dict[str, str]

        def __init__(self, body: bytes) -> None:
            super().__init__(body)
            self.headers = {"Retry-After": "2"}

    calls = []
    delays = []

    def opener(request, timeout):
        calls.append(request.full_url)
        return RateLimited(b"blocked") if len(calls) == 1 else Reply(b"ok")

    body, _ = HTTPClient(opener=opener, retries=1, sleep=delays.append).get("https://example.invalid/public")
    assert body == b"ok" and len(calls) == 2 and delays == [2]


@pytest.mark.parametrize("daily,parameters", [([[]], None), (None, [["PRECTOTCORR"]])])
def test_invalid_variable_selection_raises_validation_error(daily, parameters):
    if daily is not None:
        with pytest.raises(ValidationError):
            fetch_historical_weather(12, 77, "2025-01-01", "2025-01-02", daily=daily, client=client(WEATHER))
    if parameters is not None:
        with pytest.raises(ValidationError):
            fetch_nasa_power_data(12, 77, "2025-01-01", "2025-01-02", parameters=parameters, client=client(POWER))
