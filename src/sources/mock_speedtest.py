"""Mock speedtest data source connector."""

import random
import uuid
from datetime import datetime, timedelta, timezone

from src.schemas import ConfidenceBreakdown, MeasurementSchema, SourceType, TechnologyType

from .base import DataSource


class MockSpeedtestSource(DataSource):
    """Mock speedtest platform data source for testing and demonstration.

    Generates realistic sample data that simulates speed test measurements
    from established testing platforms.
    """

    def __init__(self, num_samples: int = 30):
        """Initialize mock speedtest source.

        Args:
            num_samples: Number of sample measurements to generate
        """
        super().__init__("mock_speedtest")
        self.num_samples = num_samples

    def fetch(self) -> list[MeasurementSchema]:
        """Fetch mock speedtest measurements.

        Generates realistic sample data with higher quality and completeness
        compared to crowdsource data, simulating data from established
        testing platforms.

        Returns:
            List of MeasurementSchema instances
        """
        measurements = []

        # Simulate measurements from rural US
        # Using realistic coordinate ranges for rural areas
        lat_range = (30.0, 48.0)  # Southern to Northern US (excluding Alaska)
        lon_range = (-120.0, -75.0)  # Western to Eastern US

        for _i in range(self.num_samples):
            # Generate random location
            lat = random.uniform(*lat_range)
            lon = random.uniform(*lon_range)

            # Generate random timestamp within last 30 days
            # Speedtest data is typically fresher
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)

            # Generate realistic speed measurements
            # Speedtest platform typically has better connection types
            tech_choice = random.choice(
                [
                    TechnologyType.FIBER,
                    TechnologyType.CABLE,
                    TechnologyType.MOBILE_5G,
                    TechnologyType.SATELLITE,
                    TechnologyType.FIXED_WIRELESS,
                ]
            )

            download: float = 0.0
            upload: float | None = 0.0
            latency: float | None = 0.0

            # Speed ranges based on technology (generally better than crowdsource)
            if tech_choice == TechnologyType.FIBER:
                download = random.uniform(100.0, 1000.0)
                upload = random.uniform(50.0, 500.0)
                latency = random.uniform(5.0, 20.0)
            elif tech_choice == TechnologyType.CABLE:
                download = random.uniform(50.0, 400.0)
                upload = random.uniform(10.0, 50.0)
                latency = random.uniform(10.0, 30.0)
            elif tech_choice == TechnologyType.MOBILE_5G:
                download = random.uniform(100.0, 500.0)
                upload = random.uniform(20.0, 100.0)
                latency = random.uniform(15.0, 40.0)
            elif tech_choice == TechnologyType.SATELLITE:
                download = random.uniform(50.0, 200.0)
                upload = random.uniform(10.0, 30.0)
                latency = random.uniform(400.0, 700.0)
            else:  # Fixed wireless
                download = random.uniform(25.0, 100.0)
                upload = random.uniform(5.0, 25.0)
                latency = random.uniform(20.0, 50.0)

            # Speedtest data is typically more complete
            # Only 5% chance of missing data
            if random.random() < 0.05:
                upload = None
            if random.random() < 0.03:
                latency = None

            # US providers
            providers = ["AT&T", "Verizon", "Comcast", "CenturyLink", "Starlink", "HughesNet", "T-Mobile", "Spectrum"]
            provider = random.choice(providers)

            # Determine region/state
            if lat > 42:
                region = random.choice(["WA", "MT", "ND", "MN", "WI", "MI"])
            elif lat < 35:
                region = random.choice(["TX", "LA", "MS", "AL", "GA", "SC"])
            else:
                region = random.choice(["CO", "NE", "KS", "MO", "IL", "IN"])

            # Confidence/quality metadata (optional in schema but included for completeness)
            completeness = (
                (1.0 if download is not None else 0.0)
                + (1.0 if upload is not None else 0.0)
                + (1.0 if latency is not None else 0.0)
            ) / 3.0
            recency = max(0.0, 1.0 - (days_ago / 30.0))
            # Speedtest platform is generally reliable
            source_reliability = 0.9
            confidence_score = round(((0.4 * completeness) + (0.4 * recency) + (0.2 * source_reliability)) * 100.0, 2)
            confidence_breakdown = ConfidenceBreakdown(
                recency_score=round(recency * 100.0, 2),
                source_reliability_score=round(source_reliability * 100.0, 2),
                consistency_score=90.0,
                completeness_score=round(completeness * 100.0, 2),
            )

            h3_index = f"mock_h3_{round(lat, 3)}_{round(lon, 3)}"

            # Create measurement
            measurement = MeasurementSchema(
                id=f"speedtest_{uuid.uuid4().hex[:12]}",
                lat=round(lat, 6),
                lon=round(lon, 6),
                timestamp_utc=timestamp,
                download_mbps=round(download, 2),
                upload_mbps=round(upload, 2) if upload is not None else None,
                latency_ms=round(latency, 2) if latency is not None else None,
                confidence_score=confidence_score,
                confidence_breakdown=confidence_breakdown,
                technology=tech_choice,
                source=SourceType.SPEEDTEST,
                provider=provider,
                country="US",
                region=region,
                h3_index=h3_index,
                metadata={
                    "server_id": f"server_{random.randint(1000, 9999)}",
                    "test_id": f"test_{uuid.uuid4().hex[:16]}",
                    "client_ip": f"{random.randint(1, 255)}.{random.randint(1, 255)}.xxx.xxx",
                },
            )

            measurements.append(measurement)

        return measurements
