"""India-specific hazard aggregation, spatial hotspot detection, and GeoJSON formatting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from nielytics.exceptions import ValidationError
from nielytics.models.schemas import AnalysisResult

from .boundaries import haversine_distance_km
from .india_names import normalize_district_name, normalize_state_name


def aggregate_hazards_by_region(
    data: pd.DataFrame,
    region_type: str = "state",
    region_column: str | None = None,
    hazard_column: str = "hazard",
    value_column: str = "value",
    date_column: str = "date",
) -> AnalysisResult:
    """Aggregate hazard events and metrics by Indian State or District.

    Normalizes region names, calculates event frequency, summary statistics,
    and temporal bounds. Returns a strictly JSON-serializable AnalysisResult.
    """
    if not isinstance(data, pd.DataFrame):
        raise ValidationError("data must be a pandas DataFrame.")
    if region_type not in ("state", "district"):
        raise ValidationError("region_type must be 'state' or 'district'.")

    col = region_column or ("state" if region_type == "state" else "district")
    if col not in data.columns:
        raise ValidationError(f"Region column {col!r} not found in DataFrame.")

    df = data.copy(deep=True)
    if region_type == "state":
        df["_norm_region"] = df[col].apply(lambda x: normalize_state_name(str(x)) if pd.notna(x) else None)
    else:
        state_col = "state" if "state" in df.columns else None
        df["_norm_region"] = df.apply(
            lambda r: normalize_district_name(
                str(r[col]),
                state=str(r[state_col]) if state_col and pd.notna(r[state_col]) else None,
            )
            if pd.notna(r[col]) else None,
            axis=1,
        )

    valid = df.dropna(subset=["_norm_region"])
    groups: dict[str, Any] = {}

    for region_name, grp in valid.groupby("_norm_region"):
        event_count = len(grp)
        hazards_present = sorted(grp[hazard_column].dropna().astype(str).unique().tolist()) if hazard_column in grp.columns else []

        val_stats = {}
        if value_column in grp.columns:
            vals = grp[value_column].dropna().astype(float)
            if len(vals) > 0:
                val_stats = {
                    "mean": float(round(vals.mean(), 4)),
                    "min": float(vals.min()),
                    "max": float(vals.max()),
                }

        date_bounds = None
        if date_column in grp.columns:
            dt_series = pd.to_datetime(grp[date_column], errors="coerce").dropna()
            if len(dt_series) > 0:
                date_bounds = [
                    dt_series.min().strftime("%Y-%m-%d"),
                    dt_series.max().strftime("%Y-%m-%d"),
                ]

        groups[str(region_name)] = {
            "event_count": int(event_count),
            "hazards": hazards_present,
            "metrics": val_stats,
            "date_range": date_bounds,
        }

    return AnalysisResult(
        feature="regional_hazard_aggregation",
        data={
            "region_type": region_type,
            "total_regions": len(groups),
            "regions": groups,
        },
        metadata={
            "region_column": col,
            "hazard_column": hazard_column,
            "value_column": value_column,
        },
    )


def get_state_hazard_summary(
    data: pd.DataFrame,
    state: str,
    state_column: str = "state",
    hazard_column: str = "hazard",
    value_column: str = "value",
    date_column: str = "date",
) -> AnalysisResult:
    """Retrieve filtered hazard summary for a specific Indian State."""
    norm_state = normalize_state_name(state)
    if not norm_state:
        raise ValidationError(f"Unrecognized Indian State name: {state!r}")

    res = aggregate_hazards_by_region(
        data,
        region_type="state",
        region_column=state_column,
        hazard_column=hazard_column,
        value_column=value_column,
        date_column=date_column,
    )
    state_data = res.data["regions"].get(norm_state, {
        "event_count": 0,
        "hazards": [],
        "metrics": {},
        "date_range": None,
    })

    return AnalysisResult(
        feature="state_hazard_summary",
        data={
            "state": norm_state,
            "summary": state_data,
        },
        metadata={"queried_name": state},
    )


def get_district_hazard_summary(
    data: pd.DataFrame,
    district: str,
    state: str | None = None,
    district_column: str = "district",
    hazard_column: str = "hazard",
    value_column: str = "value",
    date_column: str = "date",
) -> AnalysisResult:
    """Retrieve filtered hazard summary for a specific Indian District."""
    norm_dist = normalize_district_name(district, state=state)
    if not norm_dist:
        raise ValidationError(f"Unrecognized Indian District name: {district!r}")

    res = aggregate_hazards_by_region(
        data,
        region_type="district",
        region_column=district_column,
        hazard_column=hazard_column,
        value_column=value_column,
        date_column=date_column,
    )
    dist_data = res.data["regions"].get(norm_dist, {
        "event_count": 0,
        "hazards": [],
        "metrics": {},
        "date_range": None,
    })

    return AnalysisResult(
        feature="district_hazard_summary",
        data={
            "district": norm_dist,
            "state": state,
            "summary": dist_data,
        },
        metadata={"queried_district": district},
    )


def detect_hazard_hotspots(
    data: pd.DataFrame,
    latitude_column: str = "latitude",
    longitude_column: str = "longitude",
    min_events: int = 3,
    radius_km: float = 50.0,
) -> AnalysisResult:
    """Detect spatial clustering of hazard events within a geographical radius.

    Uses pairwise Haversine distances to cluster adjacent occurrences.
    """
    if latitude_column not in data.columns or longitude_column not in data.columns:
        raise ValidationError("Latitude and longitude columns required for hotspot detection.")

    valid = data.dropna(subset=[latitude_column, longitude_column]).copy()
    coords = valid[[latitude_column, longitude_column]].to_numpy(dtype=float)

    n = len(coords)
    visited = np.zeros(n, dtype=bool)
    hotspots: list[dict[str, Any]] = []

    for i in range(n):
        if visited[i]:
            continue
        lat_i, lon_i = coords[i]
        cluster_indices = [i]
        for j in range(i + 1, n):
            if visited[j]:
                continue
            lat_j, lon_j = coords[j]
            dist = haversine_distance_km(lat_i, lon_i, lat_j, lon_j)
            if dist <= radius_km:
                cluster_indices.append(j)

        if len(cluster_indices) >= min_events:
            for idx in cluster_indices:
                visited[idx] = True
            c_coords = coords[cluster_indices]
            center_lat = float(round(float(np.mean(c_coords[:, 0])), 5))
            center_lon = float(round(float(np.mean(c_coords[:, 1])), 5))
            hotspots.append({
                "center_latitude": center_lat,
                "center_longitude": center_lon,
                "event_count": len(cluster_indices),
                "radius_km": float(radius_km),
            })

    return AnalysisResult(
        feature="hazard_hotspots",
        data={
            "hotspot_count": len(hotspots),
            "radius_km": float(radius_km),
            "min_events": int(min_events),
            "hotspots": hotspots,
        },
        metadata={"total_inspected_events": n},
    )


def compare_hazard_regions(
    data: pd.DataFrame,
    regions: list[str],
    region_type: str = "state",
    region_column: str | None = None,
    hazard_column: str = "hazard",
    value_column: str = "value",
) -> AnalysisResult:
    """Side-by-side comparison of hazard metrics across multiple Indian regions."""
    agg = aggregate_hazards_by_region(
        data,
        region_type=region_type,
        region_column=region_column,
        hazard_column=hazard_column,
        value_column=value_column,
    )
    all_regions = agg.data["regions"]
    comparison: dict[str, Any] = {}

    for r in regions:
        norm = normalize_state_name(r) if region_type == "state" else normalize_district_name(r)
        if norm and norm in all_regions:
            comparison[norm] = all_regions[norm]
        else:
            comparison[norm or r] = {
                "event_count": 0,
                "hazards": [],
                "metrics": {},
                "date_range": None,
                "status": "no_data_or_unrecognized",
            }

    return AnalysisResult(
        feature="regional_hazard_comparison",
        data={
            "region_type": region_type,
            "comparison": comparison,
        },
        metadata={"queried_regions": regions},
    )


def generate_hazard_geojson(
    data: pd.DataFrame,
    latitude_column: str = "latitude",
    longitude_column: str = "longitude",
    properties: list[str] | None = None,
) -> dict[str, Any]:
    """Generate strict RFC 7946 GeoJSON FeatureCollection formatted for Leaflet, Mapbox, and deck.gl."""
    if latitude_column not in data.columns or longitude_column not in data.columns:
        raise ValidationError("Latitude and longitude columns required for GeoJSON generation.")

    features: list[dict[str, Any]] = []
    prop_cols = properties if properties is not None else [
        c for c in data.columns if c not in (latitude_column, longitude_column)
    ]

    for _, row in data.iterrows():
        lat_val = row[latitude_column]
        lon_val = row[longitude_column]
        if pd.isna(lat_val) or pd.isna(lon_val):
            continue
        try:
            f_lat = float(lat_val)
            f_lon = float(lon_val)
            if not (-90.0 <= f_lat <= 90.0 and -180.0 <= f_lon <= 180.0):
                continue
        except (ValueError, TypeError):
            continue

        props_dict: dict[str, Any] = {}
        for p in prop_cols:
            if p in row:
                val = row[p]
                if pd.isna(val):
                    props_dict[p] = None
                elif isinstance(val, (int, float, str, bool)):
                    props_dict[p] = val
                else:
                    props_dict[p] = str(val)

        feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(round(f_lon, 6)), float(round(f_lat, 6))],
            },
            "properties": props_dict,
        }
        features.append(feat)

    return {
        "type": "FeatureCollection",
        "features": features,
    }
