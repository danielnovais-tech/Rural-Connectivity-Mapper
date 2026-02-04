"""Mock crowdsource data source connector."""

import random
import uuid
from datetime import UTC, datetime, timedelta

from src.schemas import MeasurementSchema, SourceType, TechnologyType

from .base import DataSource


class MockCrowdsourceSource(DataSource):
    """Mock crowdsource data source for testing and demonstration.

    Generates realistic sample data that simulates crowdsourced connectivity
    measurements from various rural locations.
    """

    def __init__(self, num_samples: int = 50):
        """Initialize mock crowdsource source.

        Args:
            num_samples: Number of sample measurements to generate
        """
        super().__init__("mock_crowdsource")
        self.num_samples = num_samples

    def fetch(self) -> list[MeasurementSchema]:
        """Fetch mock crowdsource measurements.

        Generates realistic sample data with various quality levels,
        locations, and time ranges.

        Returns:
            List of MeasurementSchema instances
        """
        measurements = []

        # Simulate measurements from rural Brazil
        # Using realistic coordinate ranges for rural areas
        lat_range = (-33.0, -5.0)  # Southern to Northern Brazil
        lon_range = (-73.0, -35.0)  # Western to Eastern Brazil

        for i in range(self.num_samples):
            # Generate random location
            lat = random.uniform(*lat_range)
            lon = random.uniform(*lon_range)

            # Generate random timestamp within last 90 days
            days_ago = random.randint(0, 90)
            timestamp = datetime.now(UTC) - timedelta(days=days_ago)

            # Generate realistic speed measurements
            # Simulating various connection types in rural areas
            tech_choice = random.choice(
                [
                    TechnologyType.MOBILE_4G,
                    TechnologyType.SATELLITE,
                    TechnologyType.DSL,
                    TechnologyType.FIXED_WIRELESS,
                ]
            )

            download: float | None = 0.0
            upload: float | None = 0.0
            latency: float | None = 0.0

            # Speed ranges based on technology
            if tech_choice == TechnologyType.SATELLITE:
                download = random.uniform(10.0, 150.0)
                upload = random.uniform(3.0, 20.0)
                latency = random.uniform(500.0, 800.0)
            elif tech_choice == TechnologyType.MOBILE_4G:
                download = random.uniform(5.0, 50.0)
                upload = random.uniform(2.0, 15.0)
                latency = random.uniform(30.0, 100.0)
            elif tech_choice == TechnologyType.DSL:
                download = random.uniform(1.0, 25.0)
                upload = random.uniform(0.5, 5.0)
                latency = random.uniform(20.0, 80.0)
            else:  # Fixed wireless
                download = random.uniform(3.0, 30.0)
                upload = random.uniform(1.0, 10.0)
                latency = random.uniform(15.0, 60.0)

            # Some entries may have incomplete data (simulating real-world)
            if random.random() < 0.1:  # 10% missing download
                download = None
            if random.random() < 0.15:  # 15% missing upload
                upload = None
            if random.random() < 0.2:  # 20% missing latency
                latency = None

            # Random providers
            providers = ["Vivo", "TIM", "Claro", "Oi", "Starlink", "Local ISP", "Community Network", None]
            provider = random.choice(providers)

            # Create measurement
            measurement = MeasurementSchema(
                id=f"crowdsource_{uuid.uuid4().hex[:12]}",
                lat=round(lat, 6),
                lon=round(lon, 6),
                timestamp_utc=timestamp,
                download_mbps=round(download, 2) if download is not None else None,
                upload_mbps=round(upload, 2) if upload is not None else None,
                latency_ms=round(latency, 2) if latency is not None else None,
                technology=tech_choice,
                source=SourceType.CROWDSOURCE,
                provider=provider,
                confidence_score=None,
                confidence_breakdown=None,
                country="BR",
                region="BR",
                h3_index=None,
                metadata={
                    "device_type": random.choice(["android", "ios", "web"]),
                    "app_version": "1.0.0",
                    "submitted_by": f"user_{i % 20}",  # Simulate multiple users
                },
            )

            measurements.append(measurement)

        return measurements
