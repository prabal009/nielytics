"""Standardized ClimateLens schemas and record definitions for harmonization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

VALID_HAZARDS = frozenset({"heatwave", "flood", "drought", "landslide", "cyclone"})
VALID_DATA_QUALITIES = frozenset({"verified", "unverified", "modeled", "proxy"})
VALID_OBSERVATION_TYPES = frozenset({"ground_station", "reanalysis", "nwp_forecast", "event_catalog"})


@dataclass(frozen=True)
class StandardClimateRecord:
    """Canonical harmonized climate record adhering to the ClimateLens India schema."""

    date: str  # ISO YYYY-MM-DD
    state: str | None
    district: str | None
    latitude: float | None
    longitude: float | None
    hazard: str
    metric: str
    value: float
    unit: str
    source: str
    data_quality: str = "verified"
    observation_type: str = "ground_station"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert record to strictly JSON-compliant dictionary."""
        d = asdict(self)
        # Ensure clean floats or None
        if self.latitude is not None:
            d["latitude"] = float(round(self.latitude, 6))
        if self.longitude is not None:
            d["longitude"] = float(round(self.longitude, 6))
        d["value"] = float(self.value)
        return d


@dataclass
class HarmonizationSchema:
    """Configurable schema mapping heterogeneous inputs into StandardClimateRecord format."""

    date_column: str = "date"
    value_column: str = "value"
    state_column: str | None = None
    district_column: str | None = None
    latitude_column: str | None = None
    longitude_column: str | None = None
    hazard: str = "heatwave"
    metric: str = "tmax"
    source_unit: str = "C"
    target_unit: str = "C"
    source: str = "unknown"
    data_quality: str = "verified"
    observation_type: str = "ground_station"
    temporal_resolution: str = "daily"  # daily, monthly, annual, event
    column_mapping: dict[str, str] = field(default_factory=dict)
