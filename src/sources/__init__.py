"""Data source connectors for the pipeline."""

from .anatel_parquet import AnatelParquetSource
from .base import DataSource
from .manual_csv import ManualCSVSource
from .mock_crowdsource import MockCrowdsourceSource
from .mock_speedtest import MockSpeedtestSource

__all__ = [
    "DataSource",
    "AnatelParquetSource",
    "MockCrowdsourceSource",
    "MockSpeedtestSource",
    "ManualCSVSource",
]
