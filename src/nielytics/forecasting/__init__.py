"""Temperature forecasting, chronological backtesting, and climate projection engine."""

from .baselines import (
    PersistenceBaseline,
    SeasonalClimatologyBaseline,
    TrendSeasonalityBaseline,
)
from .climate_projections import ClimateProjectionEngine
from .evaluation import compute_metrics, compute_skill_score, run_chronological_backtest
from .models import ClosedFormRidgeRegressor, DirectMultiStepForecaster
from .providers import OperationalForecastAdapter
from .serialization import load_forecaster_artifacts, save_forecaster_artifacts
from .temperature import TemperatureForecaster

__all__ = [
    "ClimateProjectionEngine",
    "ClosedFormRidgeRegressor",
    "DirectMultiStepForecaster",
    "OperationalForecastAdapter",
    "PersistenceBaseline",
    "SeasonalClimatologyBaseline",
    "TemperatureForecaster",
    "TrendSeasonalityBaseline",
    "compute_metrics",
    "compute_skill_score",
    "load_forecaster_artifacts",
    "run_chronological_backtest",
    "save_forecaster_artifacts",
]
