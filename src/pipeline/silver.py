"""Silver layer: normalized, validated, and deduplicated data."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import List

import h3

from src.quality import ConfidenceCalculator
from src.schemas import MeasurementSchema


class SilverLayer:
    """Silver layer handles data normalization, validation, and enrichment.

    Applies:
    - Deduplication
    - Validation (range checks, null handling)
    - Confidence scoring
    - H3 geospatial indexing
    """

    def __init__(self, silver_dir: Path):
        """Initialize silver layer.

        Args:
            silver_dir: Path to silver data directory
        """
        self.silver_dir = Path(silver_dir)
        self.silver_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, bronze_measurements: List[MeasurementSchema]) -> List[MeasurementSchema]:
        """Process bronze data into silver layer.

        Args:
            bronze_measurements: Raw measurements from bronze layer

        Returns:
            Processed measurements with quality scores
        """
        print(f"\n📊 Processing {len(bronze_measurements)} measurements into silver layer...")

        # Step 1: Deduplicate
        deduplicated = self._deduplicate(bronze_measurements)
        print(f"  ✓ Deduplicated: {len(bronze_measurements)} → {len(deduplicated)}")

        # Step 2: Validate and filter
        validated = self._validate(deduplicated)
        print(f"  ✓ Validated: {len(deduplicated)} → {len(validated)}")

        # Step 3: Enrich with confidence scores and H3 index
        enriched = self._enrich(validated)
        print(f"  ✓ Enriched with confidence scores and H3 indexing")
        
        # Step 4: Save to silver
        self._save(enriched)

        return enriched
    
    def _deduplicate(self, measurements: List[MeasurementSchema]) -> List[MeasurementSchema]:
        """Remove duplicate measurements.

        Deduplication strategy:
        - Consider measurements duplicate if they have same location (rounded to 4 decimals)
          and timestamp within same hour
        - Keep the one with most complete data
        """
        seen: set[str] = set()
        deduplicated = []

        # Sort by completeness (measurements with more data first)
        sorted_measurements = sorted(
            measurements,
            key=lambda m: (bool(m.download_mbps) + bool(m.upload_mbps) + bool(m.latency_ms) + bool(m.provider)),
            reverse=True,
        )

        for measurement in sorted_measurements:
            # Create dedup key: location + hour
            lat_key = round(measurement.lat, 4)
            lon_key = round(measurement.lon, 4)
            time_key = measurement.timestamp_utc.strftime("%Y%m%d%H")
            dedup_key = f"{lat_key}_{lon_key}_{time_key}"

            if dedup_key not in seen:
                seen.add(dedup_key)
                deduplicated.append(measurement)

        return deduplicated
    
    def _validate(self, measurements: List[MeasurementSchema]) -> List[MeasurementSchema]:
        """Validate measurements and filter invalid ones.

        Validation rules:
        - Must have valid coordinates
        - Must have at least one metric (download, upload, or latency)
        - Metrics must be in reasonable ranges (handled by Pydantic)
        """
        validated = []

        for measurement in measurements:
            # Check for at least one metric
            has_metric = any(
                [
                    measurement.download_mbps is not None,
                    measurement.upload_mbps is not None,
                    measurement.latency_ms is not None,
                ]
            )

            if not has_metric:
                continue  # Skip measurements with no metrics

            # Pydantic already validates ranges, so if we got here, it's valid
            validated.append(measurement)

        return validated
    
    def _enrich(self, measurements: List[MeasurementSchema]) -> List[MeasurementSchema]:
        """Enrich measurements with confidence scores and H3 indexing.

        Args:
            measurements: Validated measurements

        Returns:
            Enriched measurements with confidence scores and H3 index
        """
        enriched = []

        for measurement in measurements:
            # Calculate confidence score
            score, breakdown = ConfidenceCalculator.calculate(measurement)
            measurement.confidence_score = score
            measurement.confidence_breakdown = breakdown

            # Add H3 index for geospatial aggregation (resolution 7 ≈ 5km²)
            try:
                h3_index = h3.latlng_to_cell(measurement.lat, measurement.lon, 7)
                measurement.h3_index = h3_index
            except Exception:
                # Invalid coordinates, skip H3
                pass

            enriched.append(measurement)

        return enriched
    
    def _save(self, measurements: List[MeasurementSchema]) -> Path:
        """Save enriched measurements to silver layer.

        Args:
            measurements: Enriched measurements

        Returns:
            Path to saved file
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"silver_{timestamp}.json"
        filepath = self.silver_dir / filename

        data = {
            "processed_timestamp": datetime.now(UTC).isoformat(),
            "count": len(measurements),
            "measurements": [m.to_dict() for m in measurements],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"  → {filepath}")

        return filepath
    
    def read_latest(self) -> List[MeasurementSchema]:
        """Read latest silver data.

        Returns:
            List of measurements from latest silver file
        """
        files = sorted(self.silver_dir.glob("silver_*.json"), reverse=True)
        if not files:
            return []
        
        with open(files[0], 'r') as f:
            data = json.load(f)

        measurements = [MeasurementSchema.from_dict(m) for m in data.get("measurements", [])]

        return measurements
