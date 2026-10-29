"""NIElytics: one backend-safe public package for analytics and indicators."""

from .core.visualization import (
    plot_bar,
    plot_box,
    plot_correlation,
    plot_distribution,
    plot_geographic,
    plot_histogram,
    plot_line,
    plot_scatter,
    plot_seasonal,
    plot_timeseries,
)
from .dataset import Dataset
from .exceptions import (
    DataLoadError,
    NIElyticsError,
    OptionalDependencyError,
    UnsupportedFormatError,
    ValidationError,
)
from .hazards import (
    CycloneAnalyzer,
    DroughtAnalyzer,
    FloodAnalyzer,
    HeatwaveAnalyzer,
    LandslideAnalyzer,
)
from .models import AnalysisResult

__version__ = "0.1.0"
__all__ = [
    "AnalysisResult",
    "CycloneAnalyzer",
    "DataLoadError",
    "Dataset",
    "DroughtAnalyzer",
    "FloodAnalyzer",
    "HeatwaveAnalyzer",
    "LandslideAnalyzer",
    "NIElyticsError",
    "OptionalDependencyError",
    "UnsupportedFormatError",
    "ValidationError",
    "plot_bar",
    "plot_box",
    "plot_correlation",
    "plot_distribution",
    "plot_geographic",
    "plot_histogram",
    "plot_line",
    "plot_scatter",
    "plot_seasonal",
    "plot_timeseries",
]
