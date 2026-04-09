"""Mock crowdsource data source connector."""

import random
import uuid
from datetime import datetime, timedelta, timezone

from src.schemas import ConfidenceBreakdown, DataLineage, MeasurementSchema, SourceType, TechnologyType

from .base import DataSource


class MockCrowdsourceSource(DataSource):
    """Mock crowdsource data source for testing and demonstration.

    Generates realistic sample data that simulates crowdsourced connectivity
    measurements from various rural locations.
    """

    is_synthetic = True

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
            timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago)

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

            # Confidence/quality metadata (required by schema)
            completeness = (
                (1.0 if download is not None else 0.0)
                + (1.0 if upload is not None else 0.0)
                + (1.0 if latency is not None else 0.0)
            ) / 3.0
            recency = max(0.0, 1.0 - (days_ago / 90.0))
            tech_weight = {
                TechnologyType.FIXED_WIRELESS: 0.75,
                TechnologyType.MOBILE_4G: 0.7,
                TechnologyType.DSL: 0.6,
                TechnologyType.SATELLITE: 0.5,
            }.get(tech_choice, 0.6)
            confidence_score = round(((0.5 * completeness) + (0.3 * recency) + (0.2 * tech_weight)) * 100.0, 2)
            # Map our internal components onto the canonical ConfidenceBreakdown schema.
            confidence_breakdown = ConfidenceBreakdown(
                recency_score=round(recency * 100.0, 2),
                source_reliability_score=round(tech_weight * 100.0, 2),
                consistency_score=80.0,
                completeness_score=round(completeness * 100.0, 2),
            )

            # Region/H3 placeholders for mock data (required by schema)
            region = "BR"
            h3_index = f"mock_h3_{round(lat, 3)}_{round(lon, 3)}"

            # Create measurement
            measurement = MeasurementSchema(
                id=f"crowdsource_{uuid.uuid4().hex[:12]}",
                lat=round(lat, 6),
                lon=round(lon, 6),
                timestamp_utc=timestamp,
                download_mbps=round(download, 2) if download is not None else None,
                upload_mbps=round(upload, 2) if upload is not None else None,
                latency_ms=round(latency, 2) if latency is not None else None,
                confidence_score=confidence_score,
                confidence_breakdown=confidence_breakdown,
                technology=tech_choice,
                source=SourceType.CROWDSOURCE,
                provider=provider,
                country="BR",
                region=region,
                h3_index=h3_index,
                lineage=DataLineage(is_synthetic=True),
                metadata={
                    "device_type": random.choice(["android", "ios", "web"]),
                    "app_version": "1.0.0",
                    "submitted_by": f"user_{i % 20}",  # Simulate multiple users
                },
            )

            measurements.append(measurement)

        return measurements
