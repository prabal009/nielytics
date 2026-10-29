"""Open-Meteo historical daily reanalysis (not station observations or warnings)."""

from __future__ import annotations

import math
from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._http import HTTPClient, ResponseError, coordinates, date_range, parse_json

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_DAILY_UNITS = {"temperature_2m_max": "°C", "temperature_2m_min": "°C", "precipitation_sum": "mm"}


def _daily(payload: dict, variables: tuple[str, ...], start: str, end: str, expected_units: dict[str, str] = _DAILY_UNITS) -> tuple[list[dict], dict, dict]:
    daily, units = payload.get("daily"), payload.get("daily_units")
    if not isinstance(daily, dict) or not isinstance(units, dict):
        raise ResponseError("Open-Meteo response missing daily values or daily_units")
    times = daily.get("time")
    if units.get("time") != "iso8601" or not isinstance(times, list) or not times:
        raise ResponseError("Open-Meteo daily.time must be a nonempty ISO date list")
    for variable in variables:
        if units.get(variable) != expected_units.get(variable) or not isinstance(daily.get(variable), list) or len(daily[variable]) != len(times):
            raise ResponseError(f"Open-Meteo missing/invalid units or values for {variable}")
    records = []
    previous = None
    for index, raw_date in enumerate(times):
        try:
            parsed = date.fromisoformat(raw_date)
            if raw_date != parsed.isoformat() or not start <= raw_date <= end or (previous is not None and parsed <= previous):
                raise ValueError
        except (ValueError, TypeError) as exc:
            raise ResponseError("Open-Meteo dates must be unique ordered ISO dates within requested period") from exc
        previous = parsed
        row = {"date": raw_date}
        for variable in variables:
            value = daily[variable][index]
            if value is not None and (isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or (variable in ("precipitation_sum", "river_discharge") and value < 0)):
                raise ResponseError(f"Invalid Open-Meteo value for {variable} on {raw_date}")
            row[variable] = value
        records.append(row)
    if records[0]["date"] != start or records[-1]["date"] != end or len(records) != (date.fromisoformat(end) - date.fromisoformat(start)).days + 1:
        raise ResponseError("Open-Meteo returned incomplete daily date coverage")
    location = {"latitude": payload.get("latitude"), "longitude": payload.get("longitude")}
    try:
        coordinates(**location)
    except (ValidationError, TypeError) as exc:
        raise ResponseError("Open-Meteo response has invalid grid-cell coordinates") from exc
    return records, {variable: units[variable] for variable in variables}, location


def fetch_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    *,
    daily: tuple[str, ...] = ("temperature_2m_max", "temperature_2m_min", "precipitation_sum"),
    timezone: str = "Asia/Kolkata",
    client: HTTPClient | None = None,
) -> AnalysisResult:
    """Fetch daily historical reanalysis; null measurements remain None.

    ``daily`` accepts only the three verified variables. ``client`` injects
    transport/cache/offline policy; default is online with no disk cache.
    Commercial Open-Meteo API access requires separate contractual terms.
    """
    coordinates(latitude, longitude)
    date_range(start_date, end_date)
    if start_date < "1940-01-01" or date.fromisoformat(end_date) >= date.today():
        raise ValidationError("Open-Meteo historical requests require dates from 1940-01-01 through yesterday; selected model may have shorter coverage")
    if (not isinstance(daily, (tuple, list)) or not daily or
            any(not isinstance(item, str) for item in daily) or
            len(set(daily)) != len(daily) or any(item not in _DAILY_UNITS for item in daily)):
        raise ValidationError(f"daily must contain unique variables from {tuple(_DAILY_UNITS)}")
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, TypeError, ValueError) as exc:
        raise ValidationError("timezone must be an IANA time zone") from exc
    params = {"latitude": str(latitude), "longitude": str(longitude), "start_date": start_date,
              "end_date": end_date, "daily": ",".join(daily), "timezone": timezone,
              "temperature_unit": "celsius", "precipitation_unit": "mm"}
    body, provenance = (client or HTTPClient()).get(ARCHIVE_URL, params)
    payload = parse_json(body)
    records, units, grid_cell = _daily(payload, daily, start_date, end_date)
    if payload.get("timezone") != timezone:
        raise ResponseError("Open-Meteo returned a different time zone")
    return AnalysisResult(feature="historical_weather", data={"records": records}, metadata={
        "source": "Open-Meteo Historical Weather API", "source_dataset": "Historical reanalysis (model varies with availability)",
        "data_type": "historical_reanalysis", "requested_location": {"latitude": latitude, "longitude": longitude},
        "grid_cell": grid_cell, "timezone": payload["timezone"], "units": units,
        "coverage": {"start": records[0]["date"], "end": records[-1]["date"]},
        "missing_value": "JSON null", "limitations": ["Reanalysis grid-cell estimates, not station observations or official hazard declarations.", "Available date ranges vary by model."],
        "attribution": "Open-Meteo; free API non-commercial CC BY 4.0 with provider attribution", **provenance,
    })


def fetch_temperature_data(latitude: float, longitude: float, start_date: str, end_date: str, *, timezone: str = "Asia/Kolkata", client: HTTPClient | None = None) -> AnalysisResult:
    """Fetch daily maximum/minimum 2m air temperature in °C."""
    return fetch_historical_weather(latitude, longitude, start_date, end_date, daily=("temperature_2m_max", "temperature_2m_min"), timezone=timezone, client=client)


def fetch_rainfall_data(latitude: float, longitude: float, start_date: str, end_date: str, *, timezone: str = "Asia/Kolkata", client: HTTPClient | None = None) -> AnalysisResult:
    """Fetch daily precipitation sum (all precipitation, including snow) in mm."""
    return fetch_historical_weather(latitude, longitude, start_date, end_date, daily=("precipitation_sum",), timezone=timezone, client=client)
