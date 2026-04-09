"""Data source connectors for the pipeline."""

from .anatel_parquet import AnatelParquetSource
from .base import DataSource
from .crowdsource import CrowdsourceSource
from .live_speedtest import LiveSpeedtestSource
from .manual_csv import ManualCSVSource
from .mock_crowdsource import MockCrowdsourceSource
from .mock_speedtest import MockSpeedtestSource

__all__ = [
    "DataSource",
    "AnatelParquetSource",
    "CrowdsourceSource",
    "LiveSpeedtestSource",
    "MockCrowdsourceSource",
    "MockSpeedtestSource",
    "ManualCSVSource",
]
