"""Historical cyclone-track observations; no inferred landfall or damage."""
from __future__ import annotations

from itertools import pairwise
from math import asin, cos, radians, sin, sqrt
from typing import Any

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

    def imd_cyclone_classification(self) -> AnalysisResult:
        """Classify storm peak intensity according to official India Meteorological Department (IMD) scale.

        Scale:
        - Low Pressure Area (< 31 km/h)
        - Depression (31 – 49 km/h)
        - Deep Depression (50 – 61 km/h)
        - Cyclonic Storm (62 – 88 km/h)
        - Severe Cyclonic Storm (89 – 117 km/h)
        - Very Severe Cyclonic Storm (118 – 167 km/h)
        - Extremely Severe Cyclonic Storm (168 – 221 km/h)
        - Super Cyclonic Storm (>= 222 km/h)
        """
        storm_classifications: list[dict[str, Any]] = []
        counts = {
            "Low Pressure Area": 0,
            "Depression": 0,
            "Deep Depression": 0,
            "Cyclonic Storm": 0,
            "Severe Cyclonic Storm": 0,
            "Very Severe Cyclonic Storm": 0,
            "Extremely Severe Cyclonic Storm": 0,
            "Super Cyclonic Storm": 0,
        }

        for storm_id, points in self._data.groupby(self.storm_id_column, sort=False):
            winds = points[self.wind_column].dropna().astype(float)
            if len(winds) == 0:
                continue
            max_wind = float(winds.max())
            min_press = float(points[self.pressure_column].dropna().min()) if points[self.pressure_column].notna().any() else None

            if max_wind < 31.0:
                cat = "Low Pressure Area"
            elif max_wind <= 49.0:
                cat = "Depression"
            elif max_wind <= 61.0:
                cat = "Deep Depression"
            elif max_wind <= 88.0:
                cat = "Cyclonic Storm"
            elif max_wind <= 117.0:
                cat = "Severe Cyclonic Storm"
            elif max_wind <= 167.0:
                cat = "Very Severe Cyclonic Storm"
            elif max_wind <= 221.0:
                cat = "Extremely Severe Cyclonic Storm"
            else:
                cat = "Super Cyclonic Storm"

            counts[cat] += 1
            storm_classifications.append({
                "storm_id": storm_id,
                "peak_wind_kmh": float(round(max_wind, 2)),
                "min_pressure_hpa": float(round(min_press, 2)) if min_press is not None else None,
                "category": cat,
            })

        warning = "IMD cyclone classifications reflect 3-minute sustained wind observations; satellite Dvorak estimates have inherent uncertainty."
        return result(
            "imd_cyclone_classification",
            {
                "total_storms": len(storm_classifications),
                "category_counts": counts,
                "storms": storm_classifications,
            },
            self._meta(standard="India Meteorological Department (IMD)"),
            [warning, *self._warnings()],
            _CAVEAT,
        )

    def convert_wind_units(self, from_unit: str = "km/h", to_unit: str = "knots") -> pd.DataFrame:
        """Return a copy of track data with converted wind speeds."""
        from nielytics.core.cleaner import convert_units
        return convert_units(self._data, self.wind_column, from_unit=from_unit, to_unit=to_unit)

    def landfall_analysis(
        self,
        coastline_points: list[tuple[float, float]] | None = None,
        proximity_threshold_km: float = 50.0,
    ) -> AnalysisResult:
        """Detect track crossing or closest proximity of storm tracks to Indian coastline reference coordinates."""
        # Representative Indian coastline sample points (lat, lon)
        default_coast = [
            (8.08, 77.55), (10.76, 79.84), (13.08, 80.27), (15.91, 80.47),
            (17.68, 83.21), (19.81, 85.83), (21.62, 87.52), (21.70, 88.08),
            (18.92, 72.83), (15.49, 73.82), (12.87, 74.88), (9.93, 76.26),
        ]
        coast = coastline_points or default_coast
        landfall_candidates: list[dict[str, Any]] = []

        for storm_id, points in self._data.groupby(self.storm_id_column, sort=False):
            min_dist = float("inf")
            best_time = None
            best_lat, best_lon = None, None

            for _, pt in points.iterrows():
                pt_lat, pt_lon = float(pt[self.latitude_column]), float(pt[self.longitude_column])
                for c_lat, c_lon in coast:
                    d = _distance(pt_lat, pt_lon, c_lat, c_lon)
                    if d < min_dist:
                        min_dist = d
                        best_time = pt[self.time_column].isoformat()
                        best_lat, best_lon = pt_lat, pt_lon

            landfall_candidates.append({
                "storm_id": storm_id,
                "closest_coast_distance_km": float(round(min_dist, 2)),
                "closest_time": best_time,
                "location": {"latitude": best_lat, "longitude": best_lon},
                "potential_landfall": bool(min_dist <= proximity_threshold_km),
            })

        return result(
            "cyclone_landfall_analysis",
            {
                "proximity_threshold_km": proximity_threshold_km,
                "storms": landfall_candidates,
            },
            self._meta(method="minimum distance to reference coastline points"),
            self._warnings(),
            _CAVEAT,
        )

    def regional_cyclone_exposure(
        self,
        target_lat: float,
        target_lon: float,
        radius_km: float = 300.0,
    ) -> AnalysisResult:
        """Identify cyclones passing within a given radius of a target Indian region coordinate."""
        prox = self.proximity(latitude=target_lat, longitude=target_lon, radius_km=radius_km)
        exposed = [s for s in prox.data["storms"] if s["within_radius"]]
        return result(
            "regional_cyclone_exposure",
            {
                "target_coordinates": {"latitude": target_lat, "longitude": target_lon},
                "radius_km": radius_km,
                "total_exposed_storms": len(exposed),
                "exposed_storms": exposed,
            },
            self._meta(target_latitude=target_lat, target_longitude=target_lon, radius_km=radius_km),
            self._warnings(),
            _CAVEAT,
        )

    def seasonal_cyclone_trend(self) -> AnalysisResult:
        """Compare cyclone frequency across Pre-Monsoon (Apr–May) and Post-Monsoon (Oct–Dec) seasons."""
        df = self._data.copy()
        df["month"] = df[self.time_column].dt.month
        df["year"] = df[self.time_column].dt.year

        pre_monsoon_storms = set()
        post_monsoon_storms = set()
        monsoon_storms = set()

        for storm_id, grp in df.groupby(self.storm_id_column):
            months = set(grp["month"].unique())
            if any(m in (4, 5) for m in months):
                pre_monsoon_storms.add(storm_id)
            elif any(m in (10, 11, 12) for m in months):
                post_monsoon_storms.add(storm_id)
            elif any(m in (6, 7, 8, 9) for m in months):
                monsoon_storms.add(storm_id)

        return result(
            "seasonal_cyclone_trend",
            {
                "pre_monsoon_april_may_count": len(pre_monsoon_storms),
                "post_monsoon_oct_dec_count": len(post_monsoon_storms),
                "monsoon_june_sept_count": len(monsoon_storms),
                "post_to_pre_ratio": float(round(len(post_monsoon_storms) / len(pre_monsoon_storms), 2)) if len(pre_monsoon_storms) > 0 else None,
            },
            self._meta(method="season of storm activity by calendar month"),
            self._warnings(),
            _CAVEAT,
        )
