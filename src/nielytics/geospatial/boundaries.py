"""Lightweight reference coordinates, bounding boxes, and point-in-polygon logic for India."""

from __future__ import annotations

import math
from typing import Any

from .india_names import normalize_state_name

# Reference centroids (latitude, longitude) and bounding boxes (min_lon, min_lat, max_lon, max_lat)
# for all 36 Indian States and Union Territories.
INDIA_STATE_REFERENCES: dict[str, dict[str, Any]] = {
    "Andhra Pradesh": {"centroid": (15.9129, 79.7400), "bbox": (76.76, 12.62, 84.77, 19.92)},
    "Arunachal Pradesh": {"centroid": (28.2180, 94.7278), "bbox": (91.50, 26.65, 97.42, 29.50)},
    "Assam": {"centroid": (26.2006, 92.9376), "bbox": (89.70, 24.13, 96.02, 27.97)},
    "Bihar": {"centroid": (25.0961, 85.3131), "bbox": (83.33, 24.28, 88.30, 27.52)},
    "Chhattisgarh": {"centroid": (21.2787, 81.8661), "bbox": (80.25, 17.78, 84.40, 24.10)},
    "Goa": {"centroid": (15.2993, 74.1240), "bbox": (73.68, 14.90, 74.34, 15.80)},
    "Gujarat": {"centroid": (22.2587, 71.1924), "bbox": (68.10, 20.10, 74.47, 24.71)},
    "Haryana": {"centroid": (29.0588, 76.0856), "bbox": (74.45, 27.65, 77.60, 30.92)},
    "Himachal Pradesh": {"centroid": (31.1048, 77.1734), "bbox": (75.58, 30.38, 79.07, 33.37)},
    "Jharkhand": {"centroid": (23.6102, 85.2799), "bbox": (83.32, 21.97, 87.95, 25.35)},
    "Karnataka": {"centroid": (15.3173, 75.7139), "bbox": (74.05, 11.59, 78.59, 18.45)},
    "Kerala": {"centroid": (10.8505, 76.2711), "bbox": (74.86, 8.30, 77.42, 12.80)},
    "Madhya Pradesh": {"centroid": (22.9734, 78.6569), "bbox": (74.04, 21.08, 82.81, 26.87)},
    "Maharashtra": {"centroid": (19.7515, 75.7139), "bbox": (72.60, 15.60, 80.90, 22.03)},
    "Manipur": {"centroid": (24.6637, 93.9063), "bbox": (92.98, 23.83, 94.78, 25.68)},
    "Meghalaya": {"centroid": (25.4670, 91.3662), "bbox": (89.82, 25.03, 92.80, 26.12)},
    "Mizoram": {"centroid": (23.1645, 92.9376), "bbox": (92.25, 21.97, 93.43, 24.52)},
    "Nagaland": {"centroid": (26.1584, 94.5624), "bbox": (93.33, 25.10, 95.25, 27.03)},
    "Odisha": {"centroid": (20.9517, 85.0985), "bbox": (81.38, 17.78, 87.52, 22.57)},
    "Punjab": {"centroid": (31.1471, 75.3412), "bbox": (73.88, 29.53, 76.93, 32.50)},
    "Rajasthan": {"centroid": (27.0238, 74.2179), "bbox": (69.50, 23.05, 78.28, 30.20)},
    "Sikkim": {"centroid": (27.5330, 88.5122), "bbox": (88.01, 27.07, 88.92, 28.13)},
    "Tamil Nadu": {"centroid": (11.1271, 78.6569), "bbox": (76.23, 8.08, 80.35, 13.58)},
    "Telangana": {"centroid": (18.1124, 79.0193), "bbox": (77.23, 15.83, 81.32, 19.92)},
    "Tripura": {"centroid": (23.9408, 91.9882), "bbox": (91.15, 22.93, 92.33, 24.53)},
    "Uttar Pradesh": {"centroid": (26.8467, 80.9462), "bbox": (77.08, 23.87, 84.63, 30.40)},
    "Uttarakhand": {"centroid": (30.0668, 79.0193), "bbox": (77.58, 28.72, 81.03, 31.45)},
    "West Bengal": {"centroid": (22.9868, 87.8550), "bbox": (85.82, 21.52, 89.88, 27.22)},
    # 8 Union Territories
    "Andaman and Nicobar Islands": {"centroid": (11.7401, 92.6586), "bbox": (92.20, 6.75, 94.00, 13.70)},
    "Chandigarh": {"centroid": (30.7333, 76.7794), "bbox": (76.70, 30.68, 76.85, 30.80)},
    "Dadra and Nagar Haveli and Daman and Diu": {"centroid": (20.3974, 72.8328), "bbox": (70.85, 20.00, 73.25, 20.75)},
    "Delhi": {"centroid": (28.7041, 77.1025), "bbox": (76.84, 28.40, 77.35, 28.88)},
    "Jammu and Kashmir": {"centroid": (33.7782, 76.5762), "bbox": (73.75, 32.28, 77.55, 36.50)},
    "Ladakh": {"centroid": (34.1526, 77.5771), "bbox": (75.50, 32.50, 80.50, 36.00)},
    "Lakshadweep": {"centroid": (10.5667, 72.6417), "bbox": (71.50, 8.00, 74.00, 12.50)},
    "Puducherry": {"centroid": (11.9416, 79.8083), "bbox": (79.60, 11.75, 79.95, 12.10)},
}


def get_state_reference(state_name: str) -> dict[str, Any] | None:
    """Retrieve reference centroid and bounding box for a normalized state name."""
    norm = normalize_state_name(state_name)
    if not norm:
        return None
    return INDIA_STATE_REFERENCES.get(norm)


def point_in_bbox(lon: float, lat: float, bbox: tuple[float, float, float, float]) -> bool:
    """Check if point (lon, lat) lies within bounding box (min_lon, min_lat, max_lon, max_lat)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def point_in_polygon(
    lon: float,
    lat: float,
    polygon: list[tuple[float, float]] | list[list[float]],
) -> bool:
    """Pure-Python ray-casting point-in-polygon algorithm with Shapely acceleration if available."""
    try:
        from shapely.geometry import Point as SPoint, Polygon as SPolygon
        return bool(SPolygon(polygon).contains(SPoint(lon, lat)))
    except ImportError:
        pass

    # Ray casting algorithm
    n = len(polygon)
    inside = False
    p1_lon, p1_lat = polygon[0][0], polygon[0][1]
    for i in range(1, n + 1):
        p2_lon, p2_lat = polygon[i % n][0], polygon[i % n][1]
        if lat > min(p1_lat, p2_lat):
            if lat <= max(p1_lat, p2_lat):
                if lon <= max(p1_lon, p2_lon):
                    if p1_lat != p2_lat:
                        x_inters = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                    if p1_lon == p2_lon or lon <= x_inters:
                        inside = not inside
        p1_lon, p1_lat = p2_lon, p2_lat
    return inside


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two coordinates in kilometers using Haversine formula."""
    r = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def find_nearest_state(lat: float, lon: float) -> str | None:
    """Find the nearest Indian State/UT for given coordinates using centroid distance."""
    best_state: str | None = None
    min_dist = float("inf")
    for state, ref in INDIA_STATE_REFERENCES.items():
        c_lat, c_lon = ref["centroid"]
        dist = haversine_distance_km(lat, lon, c_lat, c_lon)
        if dist < min_dist:
            min_dist = dist
            best_state = state
    return best_state
