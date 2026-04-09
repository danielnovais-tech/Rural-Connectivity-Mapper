"""Models package for Rural Connectivity Mapper."""

from .ConnectivityPoint import ConnectivityPoint
from .QualityScore import QualityScore
from .SpeedTest import SpeedTest

__all__ = [
    "SpeedTest",
    "QualityScore",
    "ConnectivityPoint",
    # ML / RL models are imported lazily to avoid hard numpy dependency at
    # package import time.  Use:
    #   from src.models.coverage_gap_model import CoverageGapForecaster
    #   from src.models.prescriptive_rl import PrescriptiveAgent
    #   from src.models.ml_engine import MLEngine
]
