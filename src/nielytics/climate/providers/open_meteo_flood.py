"""Open-Meteo/GloFAS modeled daily river discharge, never confirmed flooding."""

from __future__ import annotations

from datetime import date
from statistics import mean

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._http import HTTPClient, ResponseError, coordinates, date_range, parse_json
from .open_meteo import _daily

FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"


def fetch_river_discharge(
    latitude: float, longitude: float, start_date: str, end_date: str, *, client: HTTPClient | None = None
) -> AnalysisResult:
    """Fetch historical modeled river discharge for a grid cell (m³/s).

    Only past dates are accepted; never classify modeled discharge as observed
    flooding. The 5-km river selected may differ from the intended river.
    """
    coordinates(latitude, longitude)
    date_range(start_date, end_date)
    if start_date < "1984-01-01" or date.fromisoformat(end_date) >= date.today():
        raise ValidationError("Historical GloFAS requests require dates from 1984-01-01 through yesterday; no forecast data")
    params = {"latitude": str(latitude), "longitude": str(longitude), "daily": "river_discharge",
              "start_date": start_date, "end_date": end_date, "timezone": "GMT"}
    body, provenance = (client or HTTPClient()).get(FLOOD_URL, params)
    payload = parse_json(body)
    records, units, grid_cell = _daily(payload, ("river_discharge",), start_date, end_date, {"river_discharge": "m³/s"})
    if payload.get("timezone") != "GMT":
        raise ResponseError("Flood model returned unexpected timezone; model dates require GMT")
    return AnalysisResult(feature="river_discharge", data={"records": records}, metadata={
        "source": "Open-Meteo Flood API (GloFAS)", "source_dataset": "GloFAS modeled discharge (reanalysis and/or historical forecast)",
        "data_type": "historical_modeled_discharge", "requested_location": {"latitude": latitude, "longitude": longitude},
        "grid_cell": grid_cell, "timezone": "GMT", "units": units,
        "coverage": {"start": records[0]["date"], "end": records[-1]["date"]},
        "missing_value": "JSON null", "limitations": ["Modeled discharge is not a confirmed flood event or inundation extent.",
        "GloFAS grid resolution is ~5 km; nearest river may differ from intended river.",
        "Data after July 2022 may originate from operational forecasts; this response does not expose per-day model lineage."],
        "attribution": "Open-Meteo; free API non-commercial CC BY 4.0 with provider attribution", **provenance,
    })


def analyze_discharge_anomalies(discharge: AnalysisResult, *, baseline_start: str, baseline_end: str) -> AnalysisResult:
    """Calculate departures from mean baseline discharge using supplied records.

    Baseline dates must lie inside retrieved period with >=2 nonmissing samples.
    This simple baseline is not an estimated flood return period.
    """
    date_range(baseline_start, baseline_end)
    if discharge.feature != "river_discharge" or discharge.metadata.get("units", {}).get("river_discharge") != "m³/s":
        raise ValidationError("A river_discharge result with m³/s units is required")
    records = discharge.data.get("records", [])
    baseline = [row["river_discharge"] for row in records if baseline_start <= row["date"] <= baseline_end and row["river_discharge"] is not None]
    if len(baseline) < 2:
        raise ValidationError("At least two nonmissing baseline observations are required")
    baseline_mean = mean(baseline)
    return AnalysisResult(feature="discharge_anomaly", data={"records": [
        {"date": row["date"], "river_discharge": row["river_discharge"],
         "anomaly_m3_per_s": None if row["river_discharge"] is None else row["river_discharge"] - baseline_mean,
         "anomaly_percent": None if row["river_discharge"] is None or baseline_mean == 0 else 100 * (row["river_discharge"] - baseline_mean) / baseline_mean}
        for row in records
    ]}, metadata={**discharge.metadata, "method": "value minus arithmetic mean of selected baseline records",
                 "baseline": {"start": baseline_start, "end": baseline_end, "n": len(baseline), "mean_m3_per_s": baseline_mean},
                 "units": {"river_discharge": "m³/s", "anomaly_m3_per_s": "m³/s", "anomaly_percent": "%"},
                 "limitations": [*discharge.metadata.get("limitations", []), "Baseline uses only retrieved data, not a climatological or flood threshold."]})
