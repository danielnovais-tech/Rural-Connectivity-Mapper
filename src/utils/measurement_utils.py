"""Measurement utilities for network speed testing."""

import logging

logger = logging.getLogger(__name__)


def measure_speed() -> dict | None:
    """Measure network speed using speedtest-cli.

    Returns:
        Optional[Dict]: Dictionary with download, upload, latency, and stability
                       Returns None if measurement fails
    """
    try:
        import speedtest

        logger.info("Starting speed test measurement...")

        # Initialize speedtest client
        st = speedtest.Speedtest()

        # Get best server
        logger.debug("Selecting best server...")
        st.get_best_server()

        # Measure download speed
        logger.debug("Measuring download speed...")
        download = st.download() / 1_000_000  # Convert to Mbps

        # Measure upload speed
        logger.debug("Measuring upload speed...")
        upload = st.upload() / 1_000_000  # Convert to Mbps

        # Get ping/latency
        results = st.results.dict()
        latency = results.get("ping", 0)

        # Calculate stability based on multiple factors
        # In a real implementation, this would involve multiple measurements
        # For now, we'll derive it from latency consistency
        stability = max(0, 100 - (latency / 2))

        result = {
            "download": round(download, 2),
            "upload": round(upload, 2),
            "latency": round(latency, 2),
            "stability": round(stability, 2),
        }

        logger.info(
            f"Speed test complete: {result['download']} Mbps down, "
            f"{result['upload']} Mbps up, {result['latency']} ms latency"
        )

        return result

    except ImportError:
        logger.error("speedtest-cli not installed. Run: pip install speedtest-cli")
        return None
    except Exception as e:
        logger.error(f"Speed test failed: {e}")
        return None
