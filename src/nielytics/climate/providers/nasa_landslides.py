"""NASA's one-time Global Landslide Catalog CSV export (not live warnings)."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._http import HTTPClient, ResponseError, coordinates

CATALOG_URL = "https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv"
CATALOG_PAGE = "https://data.nasa.gov/dataset/global-landslide-catalog-export"
_REQUIRED = {"event_id", "event_date", "longitude", "latitude", "country_code", "landslide_trigger"}
_LIMITATIONS = [
    "NASA labels this a one-time export current as of March 7, 2016, although the published CSV contains later-dated rows; not a live warning feed.",
    "Media and other reports are incomplete and location/date accuracy varies by event.",
    "NASA requests agreement to catalog terms and citation of Kirschbaum et al. (2010, 2015) for exports.",
]


def _parse_catalog(body: bytes, provenance: dict) -> AnalysisResult:
    try:
        reader = csv.DictReader(io.StringIO(body.decode("utf-8-sig"), newline=""))
        if not reader.fieldnames or not _REQUIRED.issubset(reader.fieldnames) or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ResponseError("NASA GLC CSV is missing required columns or has duplicate headers")
        records = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ResponseError("NASA GLC CSV contains a row with an inconsistent number of columns")
            if all(not value for value in row.values()):
                continue
            event_id = row["event_id"].strip()
            if not event_id:
                raise ResponseError("NASA GLC CSV contains an event without event_id")
            raw_date = row["event_date"].strip()
            try:
                event_date = datetime.strptime(raw_date, "%m/%d/%Y %I:%M:%S %p").date().isoformat() if raw_date else None
            except ValueError as exc:
                raise ResponseError(f"NASA GLC event {event_id} has invalid event_date") from exc
            lon_text, lat_text = row["longitude"].strip(), row["latitude"].strip()
            longitude = latitude = None
            if lon_text and lat_text:
                try:
                    longitude, latitude = float(lon_text), float(lat_text)
                    coordinates(latitude, longitude)
                except (ValueError, ValidationError) as exc:
                    raise ResponseError(f"NASA GLC event {event_id} has invalid coordinates") from exc
            records.append({"event_id": event_id, "date": event_date, "event_date_raw": raw_date or None,
                            "longitude": longitude, "latitude": latitude,
                            "country_code": row["country_code"].strip() or None,
                            "landslide_trigger": row["landslide_trigger"].strip() or None,
                            "location_accuracy": row.get("location_accuracy", "").strip() or None})
    except (UnicodeDecodeError, csv.Error, AttributeError) as exc:
        raise ResponseError("NASA GLC catalog is not a valid UTF-8 CSV export") from exc
    if not records:
        raise ResponseError("NASA GLC catalog contains no events")
    dated = [record["date"] for record in records if record["date"] is not None]
    return AnalysisResult(feature="landslide_events", data={"records": records}, metadata={
        "source": "NASA Global Landslide Catalog (GLC) one-time export",
        "source_dataset": CATALOG_PAGE, "data_type": "historical_catalog",
        "coverage": {"start": min(dated, default=None), "end": max(dated, default=None)},
        "units": {"longitude": "degrees_east", "latitude": "degrees_north"},
        "missing_value": "Blank cells normalized to null; a missing coordinate suppresses both coordinates",
        "event_time_standard": "Catalog times are preserved as supplied; UTC offset is not specified",
        "attribution": "NASA GLC; cite Kirschbaum et al. (2010) doi:10.1007/s11069-009-9401-4 and Kirschbaum et al. (2015) doi:10.1016/j.geomorph.2015.03.016",
        "license": "Not specified on NASA Open Data resource page; review catalog terms before use",
        "limitations": _LIMITATIONS.copy(), **provenance,
    })


def fetch_landslide_events(*, accept_terms: bool = False, client: HTTPClient | None = None) -> AnalysisResult:
    """Download the verified historic CSV only after user accepts NASA catalog terms."""
    if accept_terms is not True:
        raise ValidationError(f"Review {CATALOG_PAGE} and explicitly accept its export terms before downloading")
    body, provenance = (client or HTTPClient()).get(CATALOG_URL)
    return _parse_catalog(body, provenance)


def load_landslide_catalog(path: str | Path) -> AnalysisResult:
    """Load a previously downloaded GLC CSV locally without contacting NASA."""
    try:
        data = Path(path).read_bytes()
    except (OSError, TypeError, ValueError) as exc:
        raise ValidationError(f"Cannot read local GLC catalog: {path}") from exc
    return _parse_catalog(data, {"source_url": CATALOG_URL, "retrieved_at": None,
                                 "cached": False, "cache_expired": None, "local_file": str(path)})


def filter_landslides_by_region(
    result: AnalysisResult, *, bbox: tuple[float, float, float, float] | None = None,
    country_code: str | None = None,
) -> AnalysisResult:
    """Filter geolocated catalog events by WGS84 bbox and/or recorded country code."""
    if result.feature != "landslide_events":
        raise ValidationError("A landslide_events result is required")
    if bbox is None and country_code is None:
        raise ValidationError("Specify bbox and/or country_code")
    if country_code is not None and (not isinstance(country_code, str) or len(country_code) != 2 or not country_code.isalpha()):
        raise ValidationError("country_code must be a two-letter ISO code")
    if bbox is not None:
        if not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
            raise ValidationError("bbox must be (west, south, east, north)")
        west, south, east, north = bbox
        coordinates(south, west)
        coordinates(north, east)
        if west > east or south > north:
            raise ValidationError("bbox boundaries must be ordered")
    records = [record for record in result.data["records"] if
               (country_code is None or record["country_code"] == country_code.upper()) and
               (bbox is None or (record["longitude"] is not None and west <= record["longitude"] <= east
                              and south <= record["latitude"] <= north))]
    dated = [record["date"] for record in records if record["date"] is not None]
    return AnalysisResult(feature="landslide_events", data={"records": records}, metadata={
        **result.metadata, "coverage": {"start": min(dated, default=None), "end": max(dated, default=None)},
        "region_filter": {"bbox": list(bbox) if bbox is not None else None,
                          "country_code": country_code.upper() if country_code else None},
    })


def landslide_events_to_geojson(result: AnalysisResult) -> dict:
    """Export only valid catalog point positions; missing positions are omitted."""
    from nielytics.geospatial.geojson import points_to_geojson

    if result.feature != "landslide_events":
        raise ValidationError("A landslide_events result is required")
    records = result.data["records"]
    points = ({"id": row["event_id"], "longitude": row["longitude"], "latitude": row["latitude"],
               "properties": {"event_date": row["date"], "event_date_raw": row["event_date_raw"],
                              "country_code": row["country_code"],
                              "landslide_trigger": row["landslide_trigger"],
                              "location_accuracy": row["location_accuracy"]},
               "provenance": {"source_url": result.metadata["source_url"],
                              "retrieved_at": result.metadata["retrieved_at"]}}
              for row in records if row["longitude"] is not None and row["latitude"] is not None)
    coverage = result.metadata["coverage"]
    return points_to_geojson(points, crs="EPSG:4326", source=result.metadata["source"],
                             period=f"{coverage['start']} to {coverage['end']}" if coverage["start"] is not None else None,
                             units="WGS84 decimal degrees", method="direct catalog event coordinate export",
                             limitations=[*result.metadata["limitations"],
                                          f"{sum(row['longitude'] is None or row['latitude'] is None for row in records)} records without coordinates omitted."])
