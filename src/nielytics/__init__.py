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
from .facade import ClimateAnalytics
from .forecasting import (
    ClimateProjectionEngine,
    TemperatureForecaster,
)
from .harmonization import (
    DatasetHarmonizer,
    HarmonizationSchema,
    StandardClimateRecord,
)
from .hazards import (
    CycloneAnalyzer,
    DroughtAnalyzer,
    FloodAnalyzer,
    HeatwaveAnalyzer,
    LandslideAnalyzer,
    MultiHazardAnalyzer,
)
from .insights import (
    Insight,
    InsightEngine,
)
from .models import AnalysisResult

__version__ = "0.2.0.dev1"
__all__ = [
    "AnalysisResult",
    "ClimateAnalytics",
    "ClimateProjectionEngine",
    "CycloneAnalyzer",
    "DataLoadError",
    "Dataset",
    "DatasetHarmonizer",
    "DroughtAnalyzer",
    "FloodAnalyzer",
    "HarmonizationSchema",
    "HeatwaveAnalyzer",
    "Insight",
    "InsightEngine",
    "LandslideAnalyzer",
    "MultiHazardAnalyzer",
    "NIElyticsError",
    "OptionalDependencyError",
    "StandardClimateRecord",
    "TemperatureForecaster",
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
