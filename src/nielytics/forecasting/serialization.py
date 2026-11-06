"""Safe JSON-based model persistence; zero pickle/joblib dependency."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from nielytics.exceptions import DataLoadError, ValidationError


def save_forecaster_artifacts(
    artifacts: dict[str, Any],
    filepath: str | os.PathLike[str],
) -> None:
    """Save trained forecaster weights, baselines, and configuration to safe JSON file."""
    path = Path(filepath).expanduser()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure clean serialization
        clean_json = json.dumps(artifacts, indent=2, allow_nan=False)
        path.write_text(clean_json, encoding="utf-8")
    except Exception as exc:
        raise ValidationError(f"Could not persist forecaster artifacts to {path}: {exc}") from exc


def load_forecaster_artifacts(
    filepath: str | os.PathLike[str],
) -> dict[str, Any]:
    """Load forecaster artifacts from safe JSON file."""
    path = Path(filepath).expanduser()
    if not path.is_file():
        raise DataLoadError(f"Forecaster artifact file not found: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValidationError("Forecaster artifact JSON root must be an object.")
        return data
    except Exception as exc:
        raise DataLoadError(f"Could not load forecaster artifacts from {path}: {exc}") from exc
