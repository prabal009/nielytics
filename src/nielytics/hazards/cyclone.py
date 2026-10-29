"""Historical cyclone-track observations; no inferred landfall or damage."""
from __future__ import annotations

from itertools import pairwise
from math import asin, cos, radians, sin, sqrt

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from ._common import dates, frame, numeric, result, threshold

_CAVEAT = "Historical track proximity and observed intensity do not establish landfall, damage, or a live warning."
_EARTH_RADIUS_KM = 6371.0088


def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle surface distance (haversine, spherical Earth)."""
    a = sin(radians(lat2 - lat1) / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * asin(min(1.0, sqrt(a)))


class CycloneAnalyzer:
    """Analyze explicit storm track observations, wind in km/h and pressure in hPa."""

    def __init__(self, data: pd.DataFrame, *, storm_id_column: str = "storm_id",
                 time_column: str = "time", latitude_column: str = "latitude",
                 longitude_column: str = "longitude", wind_column: str = "wind",
                 pressure_column: str = "pressure", wind_unit: str,
                 pressure_unit: str) -> None:
        if wind_unit != "km/h" or pressure_unit != "hPa":
            raise ValidationError("supported wind_unit='km/h' and pressure_unit='hPa' only")
        columns = (storm_id_column, time_column, latitude_column, longitude_column,
                   wind_column, pressure_column)
        track = frame(data, columns)
        ids = track[storm_id_column]
        if not ids.map(lambda value: isinstance(value, str) and bool(value.strip())).all():
            raise ValidationError("storm IDs must be nonempty strings")
        track[time_column] = dates(track[time_column], daily=False)
        if track.duplicated([storm_id_column, time_column]).any():
            raise ValidationError("duplicate timestamp within a storm")
        for name, low, high in ((latitude_column, -90, 90), (longitude_column, -180, 180),
                                (wind_column, 0, None), (pressure_column, 0, None)):
            if name in (wind_column, pressure_column) and track[name].isna().all():
                track[name] = track[name].astype(float)
            track[name] = numeric(track[name], name, minimum=low, maximum=high)
        if (track[pressure_column].dropna() == 0).any():
            raise ValidationError("pressure must exceed zero hPa")
        if track[[latitude_column, longitude_column]].isna().any().any():
            raise ValidationError("track coordinates cannot be missing")
        self.storm_id_column, self.time_column = storm_id_column, time_column
        self.latitude_column, self.longitude_column = latitude_column, longitude_column
        self.wind_column, self.pressure_column = wind_column, pressure_column
        self._data = track.sort_values([storm_id_column, time_column]).reset_index(drop=True)

    def _meta(self, **details: object) -> dict:
        return {"kind": "historical_track_observations", "period": {
            "start": self._data[self.time_column].min().isoformat(),
            "end": self._data[self.time_column].max().isoformat()},
            "units": {"distance": "km", "wind": "km/h", "pressure": "hPa"}, **details}

    def _warnings(self) -> list[str]:
        if self._data[[self.wind_column, self.pressure_column]].isna().any().any():
            return ["Missing wind/pressure observations are omitted from intensity extrema, not set to zero."]
        return []

    def track_distance(self) -> AnalysisResult:
        """Great-circle distances between successive timestamps, by storm."""
        tracks = []
        for storm, points in self._data.groupby(self.storm_id_column, sort=False):
            segments = []
            coordinates = points[[self.latitude_column, self.longitude_column]].to_numpy()
            for (lat1, lon1), (lat2, lon2) in pairwise(coordinates):
                segments.append(_distance(float(lat1), float(lon1), float(lat2), float(lon2)))
            tracks.append({"storm_id": storm, "distance_km": float(sum(segments)),
                           "segments_km": segments, "observation_count": len(points)})
        return result("track_distance", {"storms": tracks},
                      self._meta(method="successive great-circle distances on spherical Earth"),
                      self._warnings(), _CAVEAT)

    def cyclone_intensity(self) -> AnalysisResult:
        """Maximum observed wind and minimum observed pressure per storm."""
        rows = []
        for storm, points in self._data.groupby(self.storm_id_column, sort=False):
            winds, pressures = points[self.wind_column], points[self.pressure_column]
            rows.append({"storm_id": storm, "max_wind_kmh": float(winds.max()) if winds.notna().any() else None,
                         "min_pressure_hpa": float(pressures.min()) if pressures.notna().any() else None,
                         "observation_count": len(points)})
        return result("cyclone_intensity", {"storms": rows}, self._meta(), self._warnings(), _CAVEAT)

    def cyclone_frequency(self) -> AnalysisResult:
        """Count unique storms by year of first observation (not landfall)."""
        initial = self._data.groupby(self.storm_id_column)[self.time_column].min()
        counts = initial.dt.year.value_counts().sort_index()
        return result("cyclone_frequency", {"years": [{"year": int(year), "storms": int(count)}
                                                       for year, count in counts.items()]},
                      self._meta(method="year of first available observation"), self._warnings(), _CAVEAT)

    def proximity(self, *, latitude: float, longitude: float, radius_km: float) -> AnalysisResult:
        """Closest sampled track point per storm to a coordinate, not landfall.

        Sparse sampled tracks may pass closer between observations; this method
        does not interpolate or infer coastline intersections.
        """
        lat = threshold(latitude, "latitude")
        lon = threshold(longitude, "longitude")
        radius = threshold(radius_km, "radius_km", minimum=0)
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValidationError("latitude/longitude out of range")
        rows = []
        for storm, points in self._data.groupby(self.storm_id_column, sort=False):
            distances = [_distance(lat, lon, float(p_lat), float(p_lon)) for p_lat, p_lon
                         in points[[self.latitude_column, self.longitude_column]].itertuples(index=False, name=None)]
            nearest = int(np.argmin(distances))
            rows.append({"storm_id": storm, "closest_observed_km": distances[nearest],
                         "closest_observed_time": points[self.time_column].iloc[nearest].isoformat(),
                         "within_radius": distances[nearest] <= radius})
        return result("cyclone_proximity", {"storms": rows},
                      self._meta(latitude=lat, longitude=lon, radius_km=radius,
                                 method="nearest sampled track point; no track interpolation"),
                      self._warnings(), _CAVEAT)
