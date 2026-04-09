"""Bronze layer: raw data ingestion and immutable storage."""

import json
from datetime import datetime, timezone
from pathlib import Path

from src.schemas import DataLineage, MeasurementSchema
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

    def ingest(self, source: DataSource, *, pipeline_run_id: str | None = None) -> Path:
        """Ingest data from a source into bronze layer.

        Every measurement is stamped with lineage metadata before persistence.

        Args:
            source: DataSource instance to fetch from
            pipeline_run_id: Optional run ID to embed in lineage

        Returns:
            Path to the created bronze file
        """
        # Fetch data from source
        measurements = source.fetch()
        now = datetime.now(timezone.utc)

        # Stamp lineage on each measurement
        for m in measurements:
            if m.lineage is None:
                m.lineage = DataLineage()
            m.lineage.is_synthetic = source.is_synthetic
            if m.lineage.ingested_at is None:
                m.lineage.ingested_at = now
            if pipeline_run_id:
                m.lineage.pipeline_run_id = pipeline_run_id

        # Create source-specific directory
        source_dir = self.bronze_dir / source.source_name
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with timestamp
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"{source.source_name}_{timestamp}.json"
        filepath = source_dir / filename

        # Convert measurements to dictionaries
        data = {
            "source": source.source_name,
            "ingestion_timestamp": now.isoformat(),
            "is_synthetic": source.is_synthetic,
            "count": len(measurements),
            "measurements": [m.to_dict() for m in measurements],
        }

        # Write to file (immutable)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"✓ Ingested {len(measurements)} measurements from {source.source_name}" +
              (" [synthetic]" if source.is_synthetic else ""))
        print(f"  → {filepath}")

        return filepath

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
