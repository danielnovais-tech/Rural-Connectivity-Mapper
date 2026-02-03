"""Data source connectors for the pipeline."""

from .base import DataSource
from .anatel_parquet import AnatelParquetSource
from .mock_crowdsource import MockCrowdsourceSource
from .mock_speedtest import MockSpeedtestSource
from .manual_csv import ManualCSVSource

__all__ = [
    "DataSource",
    "AnatelParquetSource",
    "MockCrowdsourceSource",
    "MockSpeedtestSource",
    "ManualCSVSource",
]
