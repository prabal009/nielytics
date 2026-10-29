"""NOAA IBTrACS v04r01 North Indian Ocean historical best-track CSV."""

from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from datetime import UTC, datetime

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._http import HTTPClient, ResponseError, coordinates, date_range

IBTRACS_URL = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv"
_REQUIRED = {"SID": "", "SEASON": "Year", "BASIN": "", "ISO_TIME": "", "LAT": "degrees_north", "LON": "degrees_east", "WMO_WIND": "kts", "USA_WIND": "kts"}


def _optional_number(value: str | None, name: str) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ResponseError(f"Invalid IBTrACS numeric {name}: {value!r}") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ResponseError(f"Invalid IBTrACS numeric {name}: {value!r}")
    return parsed


def load_ibtracs(
    *,
    year: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    storm_id: str | None = None,
    basin: str = "NI",
    bbox: tuple[float, float, float, float] | None = None,
    client: HTTPClient | None = None,
) -> AnalysisResult:
    """Download/filter NI CSV; preserve UTC timestamps, storm IDs and wind provenance.

    ``bbox`` uses ``(west, south, east, north)`` WGS84; this filters
    *observations*, not storm occurrence/landfall. Dates are inclusive UTC
    calendar dates. Missing CSV wind/position cells remain None; storm records
    without coordinates are retained but cannot form map geometry.
    """
    if (start_date is None) != (end_date is None):
        raise ValidationError("start_date and end_date must be supplied together")
    if start_date is not None:
        date_range(start_date, end_date)
    if isinstance(year, bool) or (year is not None and (not isinstance(year, int) or year < 1800 or year > datetime.now(UTC).year)):
        raise ValidationError("year must be a valid integer year")
    if not isinstance(basin, str) or basin != "NI":
        raise ValidationError("This verified IBTrACS file only supports basin='NI'")
    if storm_id is not None and (not isinstance(storm_id, str) or not storm_id.strip()):
        raise ValidationError("storm_id must be a nonempty string")
    if bbox is not None:
        if not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
            raise ValidationError("bbox must be (west, south, east, north)")
        west, south, east, north = bbox
        coordinates(south, west)
        coordinates(north, east)
        if west > east or south > north:
            raise ValidationError("bbox boundaries must be ordered; antimeridian crossing unsupported")
    body, provenance = (client or HTTPClient()).get(IBTRACS_URL)
    try:
        reader = csv.reader(io.StringIO(body.decode("utf-8-sig"), newline=""))
        headings = next(reader)
        unit_row = next(reader)
    except (UnicodeDecodeError, StopIteration, csv.Error) as exc:
        raise ResponseError("IBTrACS CSV must contain UTF-8 header and units row") from exc
    if len(headings) != len(unit_row) or len(set(headings)) != len(headings) or any(name not in headings or unit_row[headings.index(name)].strip() != expected for name, expected in _REQUIRED.items()):
        raise ResponseError("IBTrACS CSV required headers or declared column units differ from v04r01")
    index = {name: headings.index(name) for name in (*_REQUIRED, "NAME", "TRACK_TYPE") if name in headings}
    records = []
    for line in reader:
        if not line or all(not cell.strip() for cell in line):
            continue
        if len(line) != len(headings):
            raise ResponseError("IBTrACS CSV has an inconsistent number of columns")
        def get(name: str, row: list[str] = line) -> str:
            return row[index[name]].strip() if name in index else ""
        sid, season, row_basin = get("SID"), get("SEASON"), get("BASIN")
        if not sid or not season.isdigit() or len(season) != 4 or not row_basin:
            raise ResponseError("IBTrACS record has missing SID, SEASON or BASIN")
        try:
            timestamp = datetime.strptime(get("ISO_TIME"), "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ResponseError("IBTrACS record has invalid UTC ISO_TIME") from exc
        if year is not None and int(season) != year or row_basin != basin or storm_id is not None and sid != storm_id:
            continue
        if start_date is not None and not start_date <= timestamp.date().isoformat() <= end_date:
            continue
        lat_text, lon_text = get("LAT"), get("LON")
        if bool(lat_text) != bool(lon_text):
            raise ResponseError("IBTrACS LAT/LON must be present together")
        lat = lon = None
        if lat_text:
            try:
                lat, lon = float(lat_text), float(lon_text)
                coordinates(lat, lon)
            except (ValueError, ValidationError) as exc:
                raise ResponseError("IBTrACS record has invalid LAT/LON") from exc
        if bbox is not None and (lat is None or not west <= lon <= east or not south <= lat <= north):
            continue
        records.append({"sid": sid, "season": int(season), "basin": row_basin, "name": get("NAME") or None,
                        "time": timestamp.replace(tzinfo=UTC).isoformat(), "latitude": lat, "longitude": lon,
                        "wmo_wind_kts": _optional_number(get("WMO_WIND"), "WMO_WIND"),
                        "usa_wind_kts": _optional_number(get("USA_WIND"), "USA_WIND"),
                        "track_type": get("TRACK_TYPE") or None})
    records.sort(key=lambda row: (row["sid"], row["time"]))
    return AnalysisResult(feature="ibtracs_observations", data={"records": records}, metadata={
        "source": "NOAA NCEI IBTrACS", "source_dataset": "v04r01 NI CSV", "data_type": "historical_best_track",
        "coverage": {"start": min((row["time"] for row in records), default=None),
                     "end": max((row["time"] for row in records), default=None)},
        "units": {"latitude": "degrees_north", "longitude": "degrees_east", "wmo_wind_kts": "kts", "usa_wind_kts": "kts"},
        "missing_value": "Blank CSV cells normalized to null", "timezone": "UTC",
        "limitations": ["Best-track and provisional data are not a live warning feed.",
                        "WMO agency wind averaging periods differ; WMO_WIND and USA_WIND must not be compared as identical measurements.",
                        "Track intersections with coastlines do not verify landfall; preliminary tracks may be revised."],
        "attribution": "NOAA NCEI IBTrACS v04r01 doi:10.25921/82ty-9e16; cite Knapp et al. 2010 and Gahtan et al. 2024", **provenance,
    })


def get_cyclone_tracks(result: AnalysisResult) -> AnalysisResult:
    """Group observations by SID in chronological order.

    Records without coordinates are retained; GeoJSON LineStrings require
    at least two distinct positions. Duplicate timestamps are retained.
    """
    if result.feature != "ibtracs_observations":
        raise ValidationError("An ibtracs_observations result is required")
    storms: dict[str, list[dict]] = defaultdict(list)
    for record in result.data["records"]:
        storms[record["sid"]].append(record)
    return AnalysisResult(feature="cyclone_tracks", data={"tracks": [
        {"sid": sid, "observations": sorted(rows, key=lambda row: row["time"])} for sid, rows in sorted(storms.items())
    ]}, metadata=result.metadata)


def cyclone_frequency(result: AnalysisResult) -> AnalysisResult:
    """Count unique storm SIDs by IBTrACS SEASON, excluding spur-only tracks."""
    tracks = get_cyclone_tracks(result)
    counts: dict[int, set[str]] = defaultdict(set)
    for storm in tracks.data["tracks"]:
        for season in {row["season"] for row in storm["observations"]
                       if "spur" not in (row["track_type"] or "").lower()}:
            counts[season].add(storm["sid"])
    return AnalysisResult(feature="cyclone_frequency", data={"seasons": [
        {"season": year, "storm_count": len(sids)} for year, sids in sorted(counts.items())
    ]}, metadata={**result.metadata, "method": "unique IBTrACS SID per SEASON among filtered observations, excluding spur-only tracks"})


def get_cyclone_intensity(result: AnalysisResult) -> AnalysisResult:
    """Return observed WMO and USA wind maxima separately in knots per storm."""
    tracks = get_cyclone_tracks(result)
    return AnalysisResult(feature="cyclone_intensity", data={"storms": [
        {"sid": storm["sid"], "wmo_wind_max_kts": max((row["wmo_wind_kts"] for row in storm["observations"] if row["wmo_wind_kts"] is not None), default=None),
         "usa_wind_max_kts": max((row["usa_wind_kts"] for row in storm["observations"] if row["usa_wind_kts"] is not None), default=None)}
        for storm in tracks.data["tracks"]
    ]}, metadata={**result.metadata, "method": "per-storm maximum of available source wind values (different averaging periods)"})


def cyclone_tracks_to_geojson(result: AnalysisResult) -> dict:
    """Build map-ready lines for storms with >=2 geolocated observations.

    Zero/one-point tracks are omitted (not extended or fabricated); use the
    source result for single-point events. Coordinates use longitude, latitude.
    """
    from nielytics.geospatial.geojson import tracks_to_geojson

    tracks = get_cyclone_tracks(result)
    lines = []
    for storm in tracks.data["tracks"]:
        rows = [row for row in storm["observations"] if row["latitude"] is not None]
        if len(rows) < 2 or len({(row["longitude"], row["latitude"]) for row in rows}) < 2:
            continue
        lines.append({"coordinates": [[row["longitude"], row["latitude"]] for row in rows],
                      "properties": {"sid": storm["sid"], "times_utc": [row["time"] for row in rows],
                                     "name": rows[0]["name"]},
                      "provenance": {"source_url": result.metadata["source_url"],
                                     "retrieved_at": result.metadata["retrieved_at"],
                                     "cached": result.metadata["cached"]}})
    return tracks_to_geojson(lines, crs="EPSG:4326", source=result.metadata["source"],
                             period=str(result.metadata["coverage"]), units="degrees WGS84",
                             method="chronological IBTrACS SID observation positions",
                             limitations=[*result.metadata["limitations"], "Tracks with fewer than two distinct geolocated points are omitted."])
