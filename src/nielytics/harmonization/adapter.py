"""Harmonization adapter transforming multi-source datasets into standard ClimateLens records."""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd

from nielytics.core import cleaner
from nielytics.core.loader import load_dataset
from nielytics.exceptions import ValidationError
from nielytics.geospatial.india_names import normalize_district_name, normalize_state_name
from nielytics.models.schemas import AnalysisResult
from .schema import (
    VALID_DATA_QUALITIES,
    VALID_HAZARDS,
    VALID_OBSERVATION_TYPES,
    HarmonizationSchema,
    StandardClimateRecord,
)


class DatasetHarmonizer:
    """Orchestrates ingestion, cleaning, normalization, and harmonization across climate datasets."""

    def __init__(self, schema: HarmonizationSchema | None = None) -> None:
        self.schema = schema or HarmonizationSchema()

    def harmonize(
        self,
        data: pd.DataFrame | str | os.PathLike[str],
        schema: HarmonizationSchema | None = None,
        **loader_kwargs: Any,
    ) -> AnalysisResult:
        """Harmonize input dataset into StandardClimateRecord objects and return an AnalysisResult."""
        cfg = schema or self.schema

        if cfg.hazard not in VALID_HAZARDS:
            raise ValidationError(f"Invalid hazard: {cfg.hazard!r}. Must be one of {sorted(VALID_HAZARDS)}")
        if cfg.data_quality not in VALID_DATA_QUALITIES:
            raise ValidationError(f"Invalid data_quality: {cfg.data_quality!r}")
        if cfg.observation_type not in VALID_OBSERVATION_TYPES:
            raise ValidationError(f"Invalid observation_type: {cfg.observation_type!r}")

        # Ingest
        if isinstance(data, pd.DataFrame):
            frame = data.copy(deep=True)
        else:
            frame = load_dataset(data, **loader_kwargs)

        # Apply column mapping if provided
        if cfg.column_mapping:
            frame = frame.rename(columns=cfg.column_mapping)

        # Verify required columns exist
        if cfg.date_column not in frame.columns:
            raise ValidationError(f"Required date column {cfg.date_column!r} not found in input data.")
        if cfg.value_column not in frame.columns:
            raise ValidationError(f"Required value column {cfg.value_column!r} not found in input data.")

        total_input_rows = len(frame)
        drop_reasons: dict[str, int] = {}
        conversions_applied: list[str] = []
        warnings: list[str] = []

        # Unit conversion if needed
        if cfg.source_unit != cfg.target_unit:
            try:
                frame = cleaner.convert_units(
                    frame,
                    column=cfg.value_column,
                    from_unit=cfg.source_unit,
                    to_unit=cfg.target_unit,
                )
                conversions_applied.append(f"{cfg.metric}: {cfg.source_unit} -> {cfg.target_unit}")
            except Exception as exc:
                raise ValidationError(f"Unit conversion failed: {exc}") from exc

        records: list[StandardClimateRecord] = []
        valid_dates: list[str] = []
        unique_states: set[str] = set()
        unique_districts: set[str] = set()

        for idx, row in frame.iterrows():
            # Date validation
            raw_date = row[cfg.date_column]
            if pd.isna(raw_date):
                drop_reasons["missing_date"] = drop_reasons.get("missing_date", 0) + 1
                continue
            try:
                parsed_date = pd.to_datetime(raw_date)
                if cfg.temporal_resolution == "daily":
                    date_str = parsed_date.strftime("%Y-%m-%d")
                elif cfg.temporal_resolution == "monthly":
                    date_str = parsed_date.strftime("%Y-%m-01")
                elif cfg.temporal_resolution == "annual":
                    date_str = parsed_date.strftime("%Y-01-01")
                else:  # event
                    date_str = parsed_date.strftime("%Y-%m-%d")
            except Exception:
                drop_reasons["unparseable_date"] = drop_reasons.get("unparseable_date", 0) + 1
                continue

            # Value validation
            val = row[cfg.value_column]
            try:
                f_val = float(val)
                if not np.isfinite(f_val):
                    drop_reasons["non_finite_value"] = drop_reasons.get("non_finite_value", 0) + 1
                    continue
            except (ValueError, TypeError):
                drop_reasons["non_numeric_value"] = drop_reasons.get("non_numeric_value", 0) + 1
                continue

            # State & District normalization
            state_val = None
            if cfg.state_column and cfg.state_column in frame.columns:
                raw_state = row[cfg.state_column]
                if pd.notna(raw_state):
                    state_val = normalize_state_name(str(raw_state))
                    if state_val:
                        unique_states.add(state_val)

            district_val = None
            if cfg.district_column and cfg.district_column in frame.columns:
                raw_district = row[cfg.district_column]
                if pd.notna(raw_district):
                    district_val = normalize_district_name(str(raw_district), state=state_val)
                    if district_val:
                        unique_districts.add(district_val)

            # Coordinates validation
            lat_val = None
            if cfg.latitude_column and cfg.latitude_column in frame.columns:
                raw_lat = row[cfg.latitude_column]
                if pd.notna(raw_lat):
                    try:
                        f_lat = float(raw_lat)
                        if -90.0 <= f_lat <= 90.0:
                            lat_val = f_lat
                        else:
                            drop_reasons["latitude_out_of_bounds"] = drop_reasons.get("latitude_out_of_bounds", 0) + 1
                            continue
                    except (ValueError, TypeError):
                        pass

            lon_val = None
            if cfg.longitude_column and cfg.longitude_column in frame.columns:
                raw_lon = row[cfg.longitude_column]
                if pd.notna(raw_lon):
                    try:
                        f_lon = float(raw_lon)
                        if -180.0 <= f_lon <= 180.0:
                            lon_val = f_lon
                        else:
                            drop_reasons["longitude_out_of_bounds"] = drop_reasons.get("longitude_out_of_bounds", 0) + 1
                            continue
                    except (ValueError, TypeError):
                        pass

            # Gather extra unmapped fields
            mapped_cols = {
                cfg.date_column,
                cfg.value_column,
                cfg.state_column,
                cfg.district_column,
                cfg.latitude_column,
                cfg.longitude_column,
            }
            extra_data = {
                str(k): (None if pd.isna(v) else (v if isinstance(v, (int, float, str, bool)) else str(v)))
                for k, v in row.items()
                if k not in mapped_cols
            }

            rec = StandardClimateRecord(
                date=date_str,
                state=state_val,
                district=district_val,
                latitude=lat_val,
                longitude=lon_val,
                hazard=cfg.hazard,
                metric=cfg.metric,
                value=f_val,
                unit=cfg.target_unit,
                source=cfg.source,
                data_quality=cfg.data_quality,
                observation_type=cfg.observation_type,
                extra=extra_data,
            )
            records.append(rec)
            valid_dates.append(date_str)

        dropped_rows = total_input_rows - len(records)
        date_min = min(valid_dates) if valid_dates else None
        date_max = max(valid_dates) if valid_dates else None

        report = {
            "total_input_rows": total_input_rows,
            "harmonized_rows": len(records),
            "dropped_rows": dropped_rows,
            "drop_reasons": drop_reasons,
            "conversions_applied": conversions_applied,
            "date_range": [date_min, date_max] if date_min and date_max else None,
            "unique_states": sorted(unique_states),
            "unique_districts_count": len(unique_districts),
        }

        if dropped_rows > 0:
            warnings.append(f"Harmonization dropped {dropped_rows} rows due to validation failures: {drop_reasons}")

        return AnalysisResult(
            feature="dataset_harmonization",
            data={
                "records": [r.to_dict() for r in records],
                "report": report,
            },
            metadata={
                "hazard": cfg.hazard,
                "metric": cfg.metric,
                "target_unit": cfg.target_unit,
                "source": cfg.source,
                "temporal_resolution": cfg.temporal_resolution,
            },
            warnings=warnings,
        )

    @staticmethod
    def to_dataframe(analysis_result: AnalysisResult) -> pd.DataFrame:
        """Convert harmonized AnalysisResult records back to a pandas DataFrame."""
        records = analysis_result.data.get("records", [])
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)
