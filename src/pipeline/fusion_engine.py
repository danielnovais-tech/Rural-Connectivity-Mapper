"""Fusion Engine: Unifies data from multiple sources and calculates ICR.

This module is responsible for:
1. Reading processed Parquet/JSON files from the Bronze layer
2. Unifying data from multiple sources (official APIs + crowdsourcing)
3. Calculating the Rural Connectivity Index (ICR)
4. Generating the unified Silver layer
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from src.schemas import MeasurementSchema

logger = logging.getLogger(__name__)


class FusionEngine:
    """Fusion engine for unifying multi-source data and calculating ICR.

    The fusion engine bridges the gap between Bronze (raw data) and Silver
    (normalized, validated data) by:
    - Reading data from multiple sources
    - Calculating the Rural Connectivity Index (ICR)
    - Preparing unified data for Silver layer processing
    """

    def __init__(self, bronze_dir: Path, silver_dir: Path | None = None):
        """Initialize fusion engine.

        Args:
            bronze_dir: Path to bronze data directory
            silver_dir: Optional path to silver directory (for compatibility)
        """
        self.bronze_dir = Path(bronze_dir)
        self.silver_dir = Path(silver_dir) if silver_dir else None

    def read_bronze_json(self, source_name: str | None = None) -> list[MeasurementSchema]:
        """Read JSON files from Bronze layer.

        Args:
            source_name: Optional source name to filter by. If None, reads all sources.

        Returns:
            List of measurements from Bronze layer
        """
        measurements = []

        if source_name:
            # Read from specific source directory
            source_dir = self.bronze_dir / source_name
            if source_dir.exists():
                for filepath in sorted(source_dir.glob("*.json")):
                    measurements.extend(self._read_json_file(filepath))
        else:
            # Read from all source directories
            for source_dir in self.bronze_dir.iterdir():
                if not source_dir.is_dir():
                    continue
                for filepath in sorted(source_dir.glob("*.json")):
                    measurements.extend(self._read_json_file(filepath))

        logger.info(f"Read {len(measurements)} measurements from Bronze layer")
        return measurements

    def read_bronze_parquet(self, source_name: str | None = None) -> list[MeasurementSchema]:
        """Read Parquet files from Bronze layer.

        Args:
            source_name: Optional source name to filter by. If None, reads all sources.

        Returns:
            List of measurements from Bronze layer

        Raises:
            ImportError: If pandas is not installed
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required to read Parquet files. Install with: pip install pandas pyarrow")

        measurements = []

        if source_name:
            # Read from specific source directory
            source_dir = self.bronze_dir / source_name
            if source_dir.exists():
                for filepath in sorted(source_dir.glob("*.parquet")):
                    measurements.extend(self._read_parquet_file(filepath))
        else:
            # Read from all source directories
            for source_dir in self.bronze_dir.iterdir():
                if not source_dir.is_dir():
                    continue
                for filepath in sorted(source_dir.glob("*.parquet")):
                    measurements.extend(self._read_parquet_file(filepath))

        logger.info(f"Read {len(measurements)} measurements from Bronze Parquet files")
        return measurements

    def read_bronze_data(self, source_name: str | None = None, format: str = "auto") -> list[MeasurementSchema]:
        """Read data from Bronze layer (auto-detect or specify format).

        Args:
            source_name: Optional source name to filter by
            format: Format to read ("json", "parquet", or "auto" to try both)

        Returns:
            List of measurements from Bronze layer
        """
        measurements = []

        if format == "auto":
            # Try JSON first (default format)
            measurements = self.read_bronze_json(source_name)

            # If no JSON files found and pandas is available, try Parquet
            if not measurements and PANDAS_AVAILABLE:
                try:
                    measurements = self.read_bronze_parquet(source_name)
                except Exception as e:
                    logger.warning(f"Failed to read Parquet files: {e}")
        elif format == "json":
            measurements = self.read_bronze_json(source_name)
        elif format == "parquet":
            measurements = self.read_bronze_parquet(source_name)
        else:
            raise ValueError(f"Unknown format: {format}. Use 'json', 'parquet', or 'auto'")

        return measurements

    def unify_sources(self, measurements: list[MeasurementSchema]) -> list[MeasurementSchema]:
        """Unify measurements from multiple sources.

        This method prepares data from different sources (official APIs, crowdsourcing, etc.)
        for unified processing. Currently, it ensures all measurements are in the canonical
        schema format and enriches them with metadata for fusion.

        Args:
            measurements: List of measurements from various sources

        Returns:
            Unified list of measurements ready for Silver layer processing
        """
        unified: list[MeasurementSchema] = []
        source_counts: dict[str, int] = {}

        for measurement in measurements:
            # Track source counts
            source = measurement.source.value
            source_counts[source] = source_counts.get(source, 0) + 1

            # Add fusion metadata
            if "fusion_metadata" not in measurement.metadata:
                measurement.metadata["fusion_metadata"] = {
                    "unified_at": datetime.now(timezone.utc).isoformat(),
                    "source": source,
                }

            unified.append(measurement)

        logger.info(f"Unified {len(unified)} measurements from {len(source_counts)} sources:")
        for source, count in sorted(source_counts.items()):
            logger.info(f"  - {source}: {count} measurements")

        return unified

    def calculate_icr(self, measurements: list[MeasurementSchema]) -> list[MeasurementSchema]:
        """Calculate Rural Connectivity Index (ICR) for measurements.

        The ICR is a composite metric that evaluates the quality of rural connectivity
        based on multiple factors:
        - Download speed (40% weight)
        - Upload speed (30% weight)
        - Latency (20% weight)
        - Availability/consistency (10% weight)

        The index ranges from 0-100, where:
        - 0-25: Poor connectivity
        - 26-50: Fair connectivity
        - 51-75: Good connectivity
        - 76-100: Excellent connectivity

        Args:
            measurements: List of measurements to calculate ICR for

        Returns:
            Measurements with ICR added to metadata
        """
        for measurement in measurements:
            icr_components = {}

            # Download speed component (0-100 scale)
            # Scale: 0 Mbps = 0, 100+ Mbps = 100
            if measurement.download_mbps is not None:
                download_score = min(100, measurement.download_mbps)
                icr_components["download_score"] = round(download_score, 2)
            else:
                icr_components["download_score"] = 0.0

            # Upload speed component (0-100 scale)
            # Scale: 0 Mbps = 0, 50+ Mbps = 100
            if measurement.upload_mbps is not None:
                upload_score = min(100, measurement.upload_mbps * 2)
                icr_components["upload_score"] = round(upload_score, 2)
            else:
                icr_components["upload_score"] = 0.0

            # Latency component (0-100 scale, inverted - lower is better)
            # Scale: 0-50ms = 100, 500+ms = 0
            if measurement.latency_ms is not None:
                latency_score = max(0, 100 - (measurement.latency_ms / 5.0))
                icr_components["latency_score"] = round(latency_score, 2)
            else:
                icr_components["latency_score"] = 50.0  # Neutral score if missing

            # Availability component (based on data completeness)
            # Having all three metrics = 100, missing some = lower
            metrics_count = sum(
                [
                    measurement.download_mbps is not None,
                    measurement.upload_mbps is not None,
                    measurement.latency_ms is not None,
                ]
            )
            availability_score = (metrics_count / 3.0) * 100
            icr_components["availability_score"] = round(availability_score, 2)

            # Calculate weighted ICR
            icr = (
                icr_components["download_score"] * 0.40
                + icr_components["upload_score"] * 0.30
                + icr_components["latency_score"] * 0.20
                + icr_components["availability_score"] * 0.10
            )

            # Add ICR to measurement metadata
            measurement.metadata["icr"] = round(icr, 2)
            measurement.metadata["icr_components"] = icr_components

            # Add ICR classification
            if icr >= 76:
                classification = "excellent"
            elif icr >= 51:
                classification = "good"
            elif icr >= 26:
                classification = "fair"
            else:
                classification = "poor"
            measurement.metadata["icr_classification"] = classification

        logger.info(f"Calculated ICR for {len(measurements)} measurements")
        return measurements

    def process(self, format: str = "auto") -> list[MeasurementSchema]:
        """Process Bronze layer data through fusion engine.

        This is the main entry point that:
        1. Reads data from Bronze layer
        2. Unifies data from multiple sources
        3. Calculates ICR
        4. Returns data ready for Silver layer processing

        Args:
            format: Format to read ("json", "parquet", or "auto")

        Returns:
            Processed measurements ready for Silver layer
        """
        print("\n🔄 FUSION ENGINE: Processing Bronze layer data...")

        # Step 1: Read Bronze layer data
        print("  → Reading Bronze layer data...")
        measurements = self.read_bronze_data(format=format)
        print(f"    ✓ Loaded {len(measurements)} measurements")

        # Step 2: Unify data from multiple sources
        print("  → Unifying data from multiple sources...")
        unified = self.unify_sources(measurements)
        print(f"    ✓ Unified {len(unified)} measurements")

        # Step 3: Calculate ICR
        print("  → Calculating Rural Connectivity Index (ICR)...")
        enriched = self.calculate_icr(unified)
        print(f"    ✓ Calculated ICR for {len(enriched)} measurements")

        print("✅ Fusion engine processing complete\n")

        return enriched

    def _read_json_file(self, filepath: Path) -> list[MeasurementSchema]:
        """Read a single JSON file and extract measurements.

        Args:
            filepath: Path to JSON file

        Returns:
            List of measurements from the file
        """
        try:
            with open(filepath) as f:
                data = json.load(f)

            # Extract measurements from the file structure
            measurements = []
            if "measurements" in data:
                for m in data["measurements"]:
                    try:
                        measurements.append(MeasurementSchema.from_dict(m))
                    except Exception as e:
                        logger.warning(f"Failed to parse measurement: {e}")

            return measurements
        except Exception as e:
            logger.error(f"Failed to read JSON file {filepath}: {e}")
            return []

    def _read_parquet_file(self, filepath: Path) -> list[MeasurementSchema]:
        """Read a single Parquet file and extract measurements.

        Args:
            filepath: Path to Parquet file

        Returns:
            List of measurements from the file
        """
        try:
            df = pd.read_parquet(filepath)

            # Convert DataFrame to measurements
            measurements = []
            for _, row in df.iterrows():
                try:
                    # Convert row to dict and create measurement
                    data = row.to_dict()
                    measurements.append(MeasurementSchema.from_dict(data))
                except Exception as e:
                    logger.warning(f"Failed to parse measurement from Parquet: {e}")

            return measurements
        except Exception as e:
            logger.error(f"Failed to read Parquet file {filepath}: {e}")
            return []
