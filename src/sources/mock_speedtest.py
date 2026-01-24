"""Mock speedtest data source connector."""

from datetime import datetime, timezone, timedelta
from typing import List
import uuid
import random

from src.schemas import MeasurementSchema, SourceType, TechnologyType
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
    
    def fetch(self) -> List[MeasurementSchema]:
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
        lat_range = (30.0, 48.0)   # Southern to Northern US (excluding Alaska)
        lon_range = (-120.0, -75.0)  # Western to Eastern US
        
        for i in range(self.num_samples):
            # Generate random location
            lat = random.uniform(*lat_range)
            lon = random.uniform(*lon_range)
            
            # Generate random timestamp within last 30 days
            # Speedtest data is typically fresher
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.now(timezone.utc) - timedelta(
                days=days_ago, hours=hours_ago
            )
            
            # Generate realistic speed measurements
            # Speedtest platform typically has better connection types
            tech_choice = random.choice([
                TechnologyType.FIBER,
                TechnologyType.CABLE,
                TechnologyType.MOBILE_5G,
                TechnologyType.SATELLITE,
                TechnologyType.FIXED_WIRELESS,
            ])
            
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
            providers = [
                "AT&T", "Verizon", "Comcast", "CenturyLink",
                "Starlink", "HughesNet", "T-Mobile", "Spectrum"
            ]
            provider = random.choice(providers)
            
            # Determine region/state
            if lat > 42:
                region = random.choice(["WA", "MT", "ND", "MN", "WI", "MI"])
            elif lat < 35:
                region = random.choice(["TX", "LA", "MS", "AL", "GA", "SC"])
            else:
                region = random.choice(["CO", "NE", "KS", "MO", "IL", "IN"])
            
            # Create measurement
            measurement = MeasurementSchema(
                id=f"speedtest_{uuid.uuid4().hex[:12]}",
                lat=round(lat, 6),
                lon=round(lon, 6),
                timestamp_utc=timestamp,
                download_mbps=round(download, 2),
                upload_mbps=round(upload, 2) if upload else None,
                latency_ms=round(latency, 2) if latency else None,
                technology=tech_choice,
                source=SourceType.SPEEDTEST,
                provider=provider,
                country="US",
                region=region,
                metadata={
                    "server_id": f"server_{random.randint(1000, 9999)}",
                    "test_id": f"test_{uuid.uuid4().hex[:16]}",
                    "client_ip": f"{random.randint(1, 255)}.{random.randint(1, 255)}.xxx.xxx",
                }
            )
            
            measurements.append(measurement)
        
        return measurements
