"""Live speedtest data source using the speedtest-cli library.

This connector runs an actual Ookla speed test from the host machine
and returns a single real-time MeasurementSchema.
"""

import logging
import uuid
from datetime import datetime, timezone

from src.schemas import DataLineage, MeasurementSchema, SourceType, TechnologyType

from .base import DataSource

logger = logging.getLogger(__name__)

try:
    import speedtest as _speedtest_lib

    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False


class LiveSpeedtestSource(DataSource):
    """Run a real Ookla speed test and return the measurement.

    Requires the ``speedtest-cli`` package (``pip install speedtest-cli``).
    The source performs a single test per ``fetch()`` call.
    """

    is_synthetic = False

    def __init__(self, country: str = "BR", region: str | None = None, technology: TechnologyType = TechnologyType.OTHER):
        super().__init__("live_speedtest")
        self.country = country
        self.region = region
        self.technology = technology

    def fetch(self) -> list[MeasurementSchema]:
        if not SPEEDTEST_AVAILABLE:
            logger.warning("speedtest-cli not installed – skipping LiveSpeedtestSource")
            return []

        logger.info("Running live speed test …")
        try:
            st = _speedtest_lib.Speedtest()
            st.get_best_server()
            st.download()
            st.upload()
            results = st.results.dict()
        except Exception as exc:
            logger.error("Live speed test failed: %s", exc)
            return []

        download_mbps = round(results.get("download", 0) / 1_000_000, 2)
        upload_mbps = round(results.get("upload", 0) / 1_000_000, 2)
        latency_ms = results.get("ping")

        server = results.get("server", {})
        lat = server.get("lat")
        lon = server.get("lon")
        provider = results.get("client", {}).get("isp")

        if lat is None or lon is None:
            logger.warning("Speed test returned no geolocation – skipping")
            return []

        measurement = MeasurementSchema(
            id=f"live_speedtest_{uuid.uuid4().hex[:12]}",
            lat=float(lat),
            lon=float(lon),
            timestamp_utc=datetime.now(timezone.utc),
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            latency_ms=latency_ms,
            technology=self.technology,
            source=SourceType.SPEEDTEST,
            provider=provider,
            country=self.country,
            region=self.region,
            lineage=DataLineage(
                is_synthetic=False,
                ingested_at=datetime.now(timezone.utc),
                source_file="ookla_speedtest_cli",
            ),
            metadata={
                "server_name": server.get("name"),
                "server_country": server.get("country"),
                "server_id": server.get("id"),
                "bytes_sent": results.get("bytes_sent"),
                "bytes_received": results.get("bytes_received"),
            },
        )

        logger.info(
            "Live speed test: %.1f Mbps down / %.1f Mbps up / %.0f ms latency",
            download_mbps,
            upload_mbps,
            latency_ms or 0,
        )
        return [measurement]
