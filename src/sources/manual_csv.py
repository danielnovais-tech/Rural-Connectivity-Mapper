"""Manual CSV data source connector for ANATEL and other data.

This connector monitors a directory for manually downloaded CSV files and processes them
into the unified data model. It provides:
- File monitoring and versioning
- CSV validation and parsing
- Duplicate prevention
- Integration with the pipeline
"""

import csv
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.schemas import MeasurementSchema, SourceType, TechnologyType

from .base import DataSource

logger = logging.getLogger(__name__)


class ManualCSVSource(DataSource):
    """Data source for manually downloaded CSV files.

    This connector monitors a specified directory for CSV files and processes them
    into the unified measurement schema. It tracks processed files to prevent duplicates
    and validates data quality.

    Expected CSV format (flexible column order):
    - Required: latitude, longitude, timestamp
    - Optional: download, upload, latency, provider, technology, city, id, etc.
    """

    def __init__(
        self,
        watch_dir: Path | None = None,
        source_name: str = "manual_csv",
        source_type: SourceType | None = None,
        processed_files_log: Path | None = None,
    ):
        """Initialize manual CSV source.

        Args:
            watch_dir: Directory to monitor for CSV files (default: data/bronze/manual/)
            source_name: Identifier for this data source
            source_type: Type of source (default: MANUAL)
            processed_files_log: Path to file tracking processed CSVs
        """
        super().__init__(source_name)

        # Set up watch directory
        if watch_dir is None:
            # Default to data/bronze/manual/
            base_dir = Path(__file__).parent.parent.parent / "data" / "bronze" / "manual"
            self.watch_dir = base_dir
        else:
            self.watch_dir = Path(watch_dir)

        self.watch_dir.mkdir(parents=True, exist_ok=True)

        # Set up processed files tracking
        if processed_files_log is None:
            self.processed_files_log = self.watch_dir / ".processed_files.json"
        else:
            self.processed_files_log = Path(processed_files_log)

        self.source_type = SourceType.MANUAL if source_type is None else source_type
        self._processed_files: set[str] = self._load_processed_files()

        logger.info(f"Initialized ManualCSVSource watching {self.watch_dir}")

    def _load_processed_files(self) -> set[str]:
        """Load the set of already processed file hashes.

        Returns:
            Set of file hashes that have been processed
        """
        if not self.processed_files_log.exists():
            return set()

        try:
            with open(self.processed_files_log) as f:
                data = json.load(f)
            return set(data.get("processed_hashes", []))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load processed files log: {e}")
            return set()

    def _save_processed_files(self) -> None:
        """Save the set of processed file hashes to disk."""
        data = {"processed_hashes": list(self._processed_files), "last_updated": datetime.now(timezone.utc).isoformat()}

        try:
            with open(self.processed_files_log, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error(f"Could not save processed files log: {e}")

    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate hash of file contents for duplicate detection.

        Args:
            filepath: Path to the file

        Returns:
            SHA256 hash of the file contents
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read in chunks for large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _parse_technology(self, tech_str: str | None) -> TechnologyType:
        """Parse technology string to TechnologyType enum.

        Args:
            tech_str: Technology string from CSV

        Returns:
            TechnologyType enum value
        """
        if not tech_str:
            # Some schema implementations expose UNKNOWN as a raw string literal;
            # wrap via the type to ensure the return type is TechnologyType.
            return TechnologyType(TechnologyType.UNKNOWN)

        tech_lower = tech_str.lower()

        # Map common variations to technology types
        if any(x in tech_lower for x in ["fibr", "fiber", "ftth", "fttc"]):
            return TechnologyType(TechnologyType.FIBER)
        elif any(x in tech_lower for x in ["cable", "coax"]):
            return TechnologyType(TechnologyType.CABLE)
        elif any(x in tech_lower for x in ["dsl", "adsl", "vdsl"]):
            return TechnologyType(TechnologyType.DSL)
        elif any(x in tech_lower for x in ["satélite", "satellite", "starlink", "viasat", "hughesnet"]):
            return TechnologyType(TechnologyType.SATELLITE)
        elif any(x in tech_lower for x in ["5g", "mobile_5g"]):
            return TechnologyType(TechnologyType.MOBILE_5G)
        elif any(x in tech_lower for x in ["4g", "lte", "mobile_4g"]):
            return TechnologyType(TechnologyType.MOBILE_4G)
        elif any(x in tech_lower for x in ["wireless", "radio", "wisp"]):
            return TechnologyType(TechnologyType.FIXED_WIRELESS)
        else:
            return TechnologyType(TechnologyType.OTHER)

    def _parse_csv_row(self, row: dict[str, str], row_num: int, filename: str) -> MeasurementSchema | None:
        """Parse a single CSV row into a MeasurementSchema.

        Args:
            row: Dictionary of CSV row data
            row_num: Row number for error reporting
            filename: Source filename for tracking

        Returns:
            MeasurementSchema instance or None if invalid
        """
        try:
            # Normalize column names (handle case variations)
            # Handle None values before stripping
            row_lower = {k.lower().strip(): (v.strip() if v is not None else "") for k, v in row.items()}

            # Required fields - check for empty strings before converting
            lat_str = row_lower.get("latitude", row_lower.get("lat", ""))
            lon_str = row_lower.get("longitude", row_lower.get("lon", row_lower.get("lng", "")))

            if not lat_str or not lon_str:
                logger.warning(f"Row {row_num} in {filename}: Missing required latitude or longitude")
                return None

            lat = float(lat_str)
            lon = float(lon_str)

            # Parse timestamp
            timestamp_str = row_lower.get("timestamp", row_lower.get("timestamp_utc", row_lower.get("date", "")))
            if timestamp_str:
                # Try parsing with various formats
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except ValueError:
                    # Try other common formats
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"]:
                        try:
                            timestamp = datetime.strptime(timestamp_str, fmt)
                            # Make timezone-aware if not already
                            if timestamp.tzinfo is None:
                                timestamp = timestamp.replace(tzinfo=timezone.utc)
                            break
                        except ValueError:
                            continue
                    else:
                        logger.warning(
                            f"Row {row_num}: Could not parse timestamp '{timestamp_str}', using current time"
                        )
                        timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)

            # Optional fields - handle '0' and '0.0' as valid values
            download_str = row_lower.get("download", row_lower.get("download_mbps", "")).strip()
            download = float(download_str) if download_str else None

            upload_str = row_lower.get("upload", row_lower.get("upload_mbps", "")).strip()
            upload = float(upload_str) if upload_str else None

            latency_str = row_lower.get("latency", row_lower.get("latency_ms", row_lower.get("ping", ""))).strip()
            latency = float(latency_str) if latency_str else None

            provider = row_lower.get("provider", row_lower.get("isp", "")) or None

            technology_str = row_lower.get("technology", row_lower.get("tech", ""))
            technology = self._parse_technology(technology_str)

            # Generate ID if not provided
            id_str = row_lower.get("id", "")
            if id_str:
                measurement_id = f"{self.source_name}_{id_str}"
            else:
                measurement_id = f"{self.source_name}_{uuid.uuid4().hex[:12]}"

            # Additional metadata
            metadata = {
                "source_file": filename,
                "row_number": row_num,
            }

            # Include any extra fields
            extra_fields = ["city", "municipality", "state", "uf", "jitter", "packet_loss"]
            for field in extra_fields:
                if field in row_lower and row_lower[field]:
                    metadata[field] = row_lower[field]

            # Create measurement
            measurement = MeasurementSchema(
                id=measurement_id,
                lat=lat,
                lon=lon,
                timestamp_utc=timestamp,
                download_mbps=download,
                upload_mbps=upload,
                latency_ms=latency,
                technology=technology,
                source=self.source_type,
                provider=provider,
                country=row_lower.get("country", "BR"),  # Default to Brazil
                confidence_score=None,
                confidence_breakdown=None,
                region=None,
                h3_index=None,
                metadata=metadata,
            )

            return measurement

        except (ValueError, KeyError) as e:
            logger.warning(f"Row {row_num} in {filename}: Invalid data - {e}")
            return None

    def _process_csv_file(self, filepath: Path) -> list[MeasurementSchema]:
        """Process a single CSV file into measurements.

        Args:
            filepath: Path to the CSV file

        Returns:
            List of MeasurementSchema instances
        """
        measurements = []

        logger.info(f"Processing CSV file: {filepath}")

        try:
            # Try common encodings for Brazilian CSV exports.
            encodings_to_try = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
            last_error: Exception | None = None

            for encoding in encodings_to_try:
                try:
                    with open(filepath, encoding=encoding) as f:
                        # Detect delimiter (support both comma and semicolon)
                        sample = f.read(1024)
                        f.seek(0)

                        delimiter = "," if sample.count(",") > sample.count(";") else ";"

                        reader = csv.DictReader(f, delimiter=delimiter)

                        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                            measurement = self._parse_csv_row(row, row_num, filepath.name)
                            if measurement:
                                measurements.append(measurement)

                    # If we successfully read the file, stop trying other encodings.
                    last_error = None
                    break
                except UnicodeDecodeError as e:
                    last_error = e
                    continue

            if last_error is not None:
                raise last_error

            logger.info(f"Successfully parsed {len(measurements)} measurements from {filepath.name}")

        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")

        return measurements

    def fetch(self) -> list[MeasurementSchema]:
        """Fetch measurements from unprocessed CSV files in the watch directory.

        Scans the watch directory for new CSV files, processes them, and marks them
        as processed to prevent duplicates.

        Returns:
            List of MeasurementSchema instances from all new CSV files
        """
        all_measurements = []
        new_files_processed = 0

        # Find all CSV files in watch directory
        csv_files = list(self.watch_dir.glob("*.csv"))

        if not csv_files:
            logger.info(f"No CSV files found in {self.watch_dir}")
            return []

        logger.info(f"Found {len(csv_files)} CSV file(s) in {self.watch_dir}")

        for csv_file in csv_files:
            # Calculate file hash
            file_hash = self._get_file_hash(csv_file)

            # Skip if already processed
            if file_hash in self._processed_files:
                logger.info(f"Skipping already processed file: {csv_file.name}")
                continue

            # Process the file
            measurements = self._process_csv_file(csv_file)
            all_measurements.extend(measurements)

            # Mark as processed
            self._processed_files.add(file_hash)
            new_files_processed += 1

            logger.info(f"✓ Processed {csv_file.name}: {len(measurements)} measurements")

        # Save processed files log
        if new_files_processed > 0:
            self._save_processed_files()
            logger.info(f"Processed {new_files_processed} new file(s), total {len(all_measurements)} measurements")
        else:
            logger.info("No new files to process")

        return all_measurements

    def reset_processed_files(self) -> None:
        """Reset the processed files tracking (useful for testing or reprocessing).

        Warning: This will cause all files to be reprocessed on next fetch().
        """
        self._processed_files.clear()
        self._save_processed_files()
        logger.info("Reset processed files tracking")
