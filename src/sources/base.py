"""Base interface for data sources."""

from abc import ABC, abstractmethod

from src.schemas import MeasurementSchema


class DataSource(ABC):
    """Abstract base class for data sources.

    All data source connectors should inherit from this class and implement
    the fetch() method to retrieve measurements from their respective sources.
    """

    def __init__(self, source_name: str):
        """Initialize data source.

        Args:
            source_name: Identifier for this data source
        """
        self.source_name = source_name

    @abstractmethod
    def fetch(self) -> list[MeasurementSchema]:
        """Fetch measurements from the data source.

        Returns:
            List of MeasurementSchema instances
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source_name='{self.source_name}')"
