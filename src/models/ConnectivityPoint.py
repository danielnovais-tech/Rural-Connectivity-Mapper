"""ConnectivityPoint model for location-based connectivity data."""

import uuid
from datetime import datetime

from .QualityScore import QualityScore
from .SpeedTest import SpeedTest


class ConnectivityPoint:
    """Represents a connectivity measurement point with location and quality data.

    Attributes:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        provider (str): Internet service provider name
        speed_test (SpeedTest): Speed test measurement results
        quality_score (QualityScore): Calculated quality score
        timestamp (str): ISO format timestamp of measurement
        id (str): Unique identifier for the point
        country (str): ISO 3166-1 alpha-2 country code (e.g., 'BR', 'US')
    """

    def __init__(
        self,
        latitude: float,
        longitude: float,
        provider: str,
        speed_test: SpeedTest,
        quality_score: QualityScore | None = None,
        timestamp: str | None = None,
        point_id: str | None = None,
        country: str = "BR"
    ):
        """Initialize ConnectivityPoint instance.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            provider: Internet service provider name
            speed_test: SpeedTest instance with measurements
            quality_score: QualityScore instance, auto-calculated if None
            timestamp: ISO format timestamp, auto-generated if None
            point_id: Unique identifier, auto-generated if None
            country: ISO 3166-1 alpha-2 country code (default: 'BR')
        """
        self.latitude = latitude
        self.longitude = longitude
        self.provider = provider
        self.speed_test = speed_test
        self.quality_score = quality_score if quality_score else QualityScore.calculate(speed_test)
        self.timestamp = timestamp if timestamp else datetime.now().isoformat()
        self.id = point_id if point_id else str(uuid.uuid4())
        self.country = country.upper() if country else "BR"
    
    def to_dict(self) -> dict:
        """Convert ConnectivityPoint to dictionary representation.

        Returns:
            Dict: Dictionary containing all connectivity point data
        """
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "provider": self.provider,
            "speed_test": self.speed_test.to_dict(),
            "quality_score": self.quality_score.to_dict(),
            "timestamp": self.timestamp,
            "country": self.country,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConnectivityPoint':
        """Create ConnectivityPoint instance from dictionary.

        Args:
            data: Dictionary containing connectivity point data

        Returns:
            ConnectivityPoint: New ConnectivityPoint instance
        """
        speed_test = SpeedTest.from_dict(data.get("speed_test", {}))

        # If quality_score exists in dict, use it; otherwise it will be auto-calculated
        quality_score = None
        if "quality_score" in data:
            qs_data = data["quality_score"]
            quality_score = QualityScore(
                overall_score=qs_data.get("overall_score", 0.0),
                speed_score=qs_data.get("speed_score", 0.0),
                latency_score=qs_data.get("latency_score", 0.0),
                stability_score=qs_data.get("stability_score", 0.0),
            )

        return cls(
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
            provider=data.get("provider", "Unknown"),
            speed_test=speed_test,
            quality_score=quality_score,
            timestamp=data.get("timestamp"),
            point_id=data.get("id"),
            country=data.get("country", "BR"),
        )

    def __repr__(self) -> str:
        """String representation of ConnectivityPoint.

        Returns:
            str: Formatted string representation
        """
        return (
            f"ConnectivityPoint(id={self.id[:8]}..., "
            f"provider={self.provider}, "
            f"location=({self.latitude:.4f}, {self.longitude:.4f}), "
            f"quality={self.quality_score.rating})"
        )
