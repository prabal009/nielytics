"""JSON-compatible backend boundary for computed indicators, not official warnings."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnalysisResult:
    """An indicator with explicit provenance, limitations, and serializable data.

    ``data`` and ``metadata`` must contain JSON-compatible values. Conversion
    rejects nonfinite numbers and unsupported Python objects rather than
    silently changing scientific values or discarding fields.
    """

    feature: str
    data: dict[str, Any]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    status: str = "success"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent strict-JSON response for a backend serializer."""
        payload = {
            "status": self.status,
            "feature": self.feature,
            "data": self.data,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }
        return json.loads(json.dumps(payload, allow_nan=False))
