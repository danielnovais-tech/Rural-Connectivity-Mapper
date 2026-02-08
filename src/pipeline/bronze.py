"""Bronze layer: raw data ingestion and immutable storage."""

import json
from datetime import UTC, datetime
from pathlib import Path

from src.schemas import MeasurementSchema
from src.sources import DataSource


class BronzeLayer:
    """Bronze layer handles raw data ingestion from sources.

    Raw data is stored in immutable JSON files, organized by source and
    ingestion timestamp. No transformations are applied at this stage.
    """

    def __init__(self, bronze_dir: Path):
        """Initialize bronze layer.

        Args:
            bronze_dir: Path to bronze data directory
        """
        self.bronze_dir = Path(bronze_dir)
        self.bronze_dir.mkdir(parents=True, exist_ok=True)

    def ingest(self, source: DataSource) -> Path:
        """Ingest data from a source into bronze layer.

        Args:
            source: DataSource instance to fetch from

        Returns:
            Path to the created bronze file
        """
        # Fetch data from source
        measurements = source.fetch()

        # Create source-specific directory
        source_dir = self.bronze_dir / source.source_name
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with timestamp
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{source.source_name}_{timestamp}.json"
        filepath = source_dir / filename

        # Convert measurements to dictionaries
        data = {
            "source": source.source_name,
            "ingestion_timestamp": datetime.now(UTC).isoformat(),
            "count": len(measurements),
            "measurements": [m.to_dict() for m in measurements],
        }

        # Write to file (immutable)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"✓ Ingested {len(measurements)} measurements from {source.source_name}")
        print(f"  → {filepath}")

        return filepath

    def read_latest(self, source_name: str) -> list[MeasurementSchema]:
        """Read latest data file for a source.

        Args:
            source_name: Name of the source

        Returns:
            List of measurements from the latest file
        """
        source_dir = self.bronze_dir / source_name
        if not source_dir.exists():
            return []

        # Find latest file
        files = sorted(source_dir.glob(f"{source_name}_*.json"), reverse=True)
        if not files:
            return []

        # Read and parse
        with open(files[0]) as f:
            data = json.load(f)

        measurements = [MeasurementSchema.from_dict(m) for m in data.get("measurements", [])]

        return measurements

    def read_all(self) -> list[MeasurementSchema]:
        """Read all bronze data from all sources.

        Returns:
            List of all measurements across all sources
        """
        all_measurements = []

        # Iterate through all source directories
        for source_dir in self.bronze_dir.iterdir():
            if not source_dir.is_dir():
                continue

            # Read all files in source directory
            for filepath in sorted(source_dir.glob("*.json")):
                with open(filepath) as f:
                    data = json.load(f)

                measurements = [MeasurementSchema.from_dict(m) for m in data.get("measurements", [])]
                all_measurements.extend(measurements)

        return all_measurements
