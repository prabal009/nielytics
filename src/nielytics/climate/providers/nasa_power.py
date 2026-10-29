"""NASA POWER modeled daily point precipitation and air temperature."""

from __future__ import annotations

import math
from datetime import date, datetime

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._http import HTTPClient, ResponseError, coordinates, date_range, parse_json

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
_PARAMETERS = {"PRECTOTCORR": "mm/day", "T2M_MAX": "C"}


def fetch_nasa_power_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    *,
    parameters: tuple[str, ...] = ("PRECTOTCORR", "T2M_MAX"),
    client: HTTPClient | None = None,
) -> AnalysisResult:
    """Fetch verified AG daily parameters in Local Solar Time (LST).

    POWER ``header.fill_value`` is converted to None; returned parameter
    units must match the documented values. No arbitrary parameter schema is
    assumed. Historic data are modeled/gridded, not gauge declarations.
    """
    coordinates(latitude, longitude)
    date_range(start_date, end_date)
    if start_date < "1981-01-01" or date.fromisoformat(end_date) >= date.today():
        raise ValidationError("POWER daily historical dates must be from 1981-01-01 through yesterday")
    if (not isinstance(parameters, (tuple, list)) or not parameters or
            any(not isinstance(parameter, str) for parameter in parameters) or
            len(set(parameters)) != len(parameters) or any(parameter not in _PARAMETERS for parameter in parameters)):
        raise ValidationError(f"parameters must be unique values from {tuple(_PARAMETERS)}")
    params = {"parameters": ",".join(parameters), "community": "AG", "longitude": str(longitude),
              "latitude": str(latitude), "start": start_date.replace("-", ""), "end": end_date.replace("-", ""),
              "format": "JSON", "time-standard": "LST"}
    body, provenance = (client or HTTPClient()).get(POWER_URL, params)
    payload = parse_json(body)
    header, props, units_meta = payload.get("header"), payload.get("properties"), payload.get("parameters")
    if not isinstance(header, dict) or not isinstance(props, dict) or not isinstance(units_meta, dict) or not isinstance(props.get("parameter"), dict):
        raise ResponseError("POWER response missing header, properties.parameter, or parameters units")
    if header.get("time_standard") != "LST":
        raise ResponseError("POWER returned an unexpected time standard")
    fill = header.get("fill_value")
    if isinstance(fill, bool) or not isinstance(fill, (int, float)) or not math.isfinite(fill):
        raise ResponseError("POWER header.fill_value is missing or invalid")
    values = props["parameter"]
    dates: set[str] | None = None
    for parameter in parameters:
        if not isinstance(values.get(parameter), dict) or not isinstance(units_meta.get(parameter), dict) or units_meta[parameter].get("units") != _PARAMETERS[parameter]:
            raise ResponseError(f"POWER missing/invalid parameter {parameter} or units")
        these_dates = set(values[parameter])
        if dates is not None and dates != these_dates:
            raise ResponseError("POWER parameter date coverage is inconsistent")
        dates = these_dates
    if not dates:
        raise ResponseError("POWER response contains no daily observations")
    records = []
    for raw_date in sorted(dates):
        try:
            parsed = datetime.strptime(raw_date, "%Y%m%d").date()
            if parsed.strftime("%Y%m%d") != raw_date or not start_date <= parsed.isoformat() <= end_date:
                raise ValueError
        except (ValueError, TypeError) as exc:
            raise ResponseError("POWER returned an invalid or out-of-range observation date") from exc
        row = {"date": parsed.isoformat()}
        for parameter in parameters:
            value = values[parameter][raw_date]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ResponseError(f"POWER returned invalid value for {parameter} on {raw_date}")
            if parameter == "PRECTOTCORR" and value < 0 and value != fill:
                raise ResponseError("POWER precipitation cannot be negative except declared fill")
            row[parameter] = None if value == fill else value
        records.append(row)
    if records[0]["date"] != start_date or records[-1]["date"] != end_date or len(records) != (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1:
        raise ResponseError("POWER returned incomplete daily date coverage")
    geometry = payload.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point" or not isinstance(geometry.get("coordinates"), list) or len(geometry["coordinates"]) < 2:
        raise ResponseError("POWER response missing Point geometry")
    lon, lat = geometry["coordinates"][:2]
    try:
        coordinates(lat, lon)
    except ValidationError as exc:
        raise ResponseError("POWER response has invalid point coordinates") from exc
    return AnalysisResult(feature="nasa_power_daily", data={"records": records}, metadata={
        "source": "NASA POWER Daily Point API", "source_dataset": "POWER daily meteorology",
        "data_type": "historical_modeled", "requested_location": {"latitude": latitude, "longitude": longitude},
        "grid_cell": {"latitude": lat, "longitude": lon}, "time_standard": "LST",
        "units": {parameter: _PARAMETERS[parameter] for parameter in parameters},
        "coverage": {"start": records[0]["date"], "end": records[-1]["date"]},
        "missing_value": f"header.fill_value ({fill}) normalized to null", "provider_sources": header.get("sources", []),
        "service_version": header.get("api", {}).get("version") if isinstance(header.get("api"), dict) else None,
        "limitations": ["Gridded modeled daily values, not station records or disaster declarations.",
                        "POWER LST days differ from UTC and civil timezone boundaries.",
                        "Meteorological parameters generally have 2–3 days of publication latency."],
        "attribution": "NASA POWER; cite POWER project and Daily service version and accessed date", **provenance,
    })


def fetch_nasa_precipitation(latitude: float, longitude: float, start_date: str, end_date: str, *, client: HTTPClient | None = None) -> AnalysisResult:
    """Fetch POWER corrected daily precipitation PRECTOTCORR in mm/day."""
    return fetch_nasa_power_data(latitude, longitude, start_date, end_date, parameters=("PRECTOTCORR",), client=client)
