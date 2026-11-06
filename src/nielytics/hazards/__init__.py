"""Historical hazard observations and scientifically labeled proxy indicators."""

from .cyclone import CycloneAnalyzer
from .drought import DroughtAnalyzer
from .flood import FloodAnalyzer
from .heatwave import HeatwaveAnalyzer
from .landslide import LandslideAnalyzer
from .multi_hazard import MultiHazardAnalyzer

__all__ = [
    "CycloneAnalyzer",
    "DroughtAnalyzer",
    "FloodAnalyzer",
    "HeatwaveAnalyzer",
    "LandslideAnalyzer",
    "MultiHazardAnalyzer",
]
