"""Tests for ManualCSVSource connector."""

import csv
import tempfile
from pathlib import Path

from src.schemas import MeasurementSchema, SourceType, TechnologyType
from src.sources.manual_csv import ManualCSVSource


class TestManualCSVSource:
    """Test suite for ManualCSVSource connector."""

    def test_initialization(self):
        """Test source initialization with default parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = ManualCSVSource(watch_dir=Path(tmpdir))

            assert source.source_name == "manual_csv"
            assert source.watch_dir == Path(tmpdir)
            assert source.watch_dir.exists()
            assert source.source_type == SourceType.MANUAL

    def test_custom_initialization(self):
        """Test source initialization with custom parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watch_dir = Path(tmpdir) / "custom"
            source = ManualCSVSource(watch_dir=watch_dir, source_name="anatel_manual", source_type=SourceType.ANATEL)

            assert source.source_name == "anatel_manual"
            assert source.watch_dir == watch_dir
            assert source.watch_dir.exists()
            assert source.source_type == SourceType.ANATEL

    def test_fetch_empty_directory(self):
        """Test fetching from empty directory returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            assert measurements == []

    def test_fetch_basic_csv(self):
        """Test fetching measurements from a basic CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test CSV file
            csv_path = Path(tmpdir) / "test_data.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "id",
                        "latitude",
                        "longitude",
                        "timestamp",
                        "download",
                        "upload",
                        "latency",
                        "provider",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "id": "1",
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "download": "100.0",
                        "upload": "15.0",
                        "latency": "30.0",
                        "provider": "Test ISP",
                    }
                )
                writer.writerow(
                    {
                        "id": "2",
                        "latitude": "-22.9068",
                        "longitude": "-43.1729",
                        "timestamp": "2026-01-15T11:00:00",
                        "download": "85.5",
                        "upload": "12.3",
                        "latency": "45.2",
                        "provider": "Another ISP",
                    }
                )

            # Fetch measurements
            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            # Verify results
            assert len(measurements) == 2

            # Check first measurement
            m1 = measurements[0]
            assert isinstance(m1, MeasurementSchema)
            assert m1.lat == -23.5505
            assert m1.lon == -46.6333
            assert m1.download_mbps == 100.0
            assert m1.upload_mbps == 15.0
            assert m1.latency_ms == 30.0
            assert m1.provider == "Test ISP"
            assert m1.source == SourceType.MANUAL

            # Check second measurement
            m2 = measurements[1]
            assert m2.lat == -22.9068
            assert m2.lon == -43.1729
            assert m2.download_mbps == 85.5

    def test_fetch_duplicate_prevention(self):
        """Test that the same file is not processed twice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test CSV file
            csv_path = Path(tmpdir) / "test_data.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp"])
                writer.writeheader()
                writer.writerow({"latitude": "-23.5505", "longitude": "-46.6333", "timestamp": "2026-01-15T10:00:00"})

            source = ManualCSVSource(watch_dir=Path(tmpdir))

            # First fetch should return measurements
            measurements1 = source.fetch()
            assert len(measurements1) == 1

            # Second fetch should return nothing (file already processed)
            measurements2 = source.fetch()
            assert len(measurements2) == 0

    def test_fetch_multiple_files(self):
        """Test fetching from multiple CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first CSV file
            csv_path1 = Path(tmpdir) / "data1.csv"
            with open(csv_path1, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "download"])
                writer.writeheader()
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "download": "100.0",
                    }
                )

            # Create second CSV file
            csv_path2 = Path(tmpdir) / "data2.csv"
            with open(csv_path2, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "download"])
                writer.writeheader()
                writer.writerow(
                    {
                        "latitude": "-22.9068",
                        "longitude": "-43.1729",
                        "timestamp": "2026-01-15T11:00:00",
                        "download": "85.0",
                    }
                )
                writer.writerow(
                    {
                        "latitude": "-15.7801",
                        "longitude": "-47.9292",
                        "timestamp": "2026-01-15T12:00:00",
                        "download": "150.0",
                    }
                )

            # Fetch measurements
            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            # Should have 3 total measurements from 2 files
            assert len(measurements) == 3

    def test_technology_parsing(self):
        """Test parsing of technology field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "tech_test.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "technology"])
                writer.writeheader()
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "technology": "Fibra Óptica",
                    }
                )
                writer.writerow(
                    {
                        "latitude": "-22.9068",
                        "longitude": "-43.1729",
                        "timestamp": "2026-01-15T11:00:00",
                        "technology": "Starlink",
                    }
                )
                writer.writerow(
                    {
                        "latitude": "-15.7801",
                        "longitude": "-47.9292",
                        "timestamp": "2026-01-15T12:00:00",
                        "technology": "4G",
                    }
                )

            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            assert len(measurements) == 3
            assert measurements[0].technology == TechnologyType.FIBER
            assert measurements[1].technology == TechnologyType.SATELLITE
            assert measurements[2].technology == TechnologyType.MOBILE_4G

    def test_optional_fields(self):
        """Test handling of optional fields in CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "optional.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "download"])
                writer.writeheader()
                # Row with minimal data (only required + download)
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "download": "100.0",
                    }
                )

            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            assert len(measurements) == 1
            m = measurements[0]
            assert m.download_mbps == 100.0
            assert m.upload_mbps is None  # Optional field not provided
            assert m.latency_ms is None
            assert m.provider is None

    def test_invalid_row_handling(self):
        """Test that invalid rows are skipped gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "invalid.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "download"])
                writer.writeheader()
                # Valid row
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "download": "100.0",
                    }
                )
                # Invalid row (bad latitude)
                writer.writerow(
                    {
                        "latitude": "invalid",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T11:00:00",
                        "download": "85.0",
                    }
                )
                # Valid row
                writer.writerow(
                    {
                        "latitude": "-22.9068",
                        "longitude": "-43.1729",
                        "timestamp": "2026-01-15T12:00:00",
                        "download": "90.0",
                    }
                )

            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            # Should get 2 valid measurements, invalid row skipped
            assert len(measurements) == 2

    def test_reset_processed_files(self):
        """Test resetting processed files tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test CSV file
            csv_path = Path(tmpdir) / "test.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp"])
                writer.writeheader()
                writer.writerow({"latitude": "-23.5505", "longitude": "-46.6333", "timestamp": "2026-01-15T10:00:00"})

            source = ManualCSVSource(watch_dir=Path(tmpdir))

            # First fetch
            measurements1 = source.fetch()
            assert len(measurements1) == 1

            # Second fetch (should be empty)
            measurements2 = source.fetch()
            assert len(measurements2) == 0

            # Reset and fetch again
            source.reset_processed_files()
            measurements3 = source.fetch()
            assert len(measurements3) == 1

    def test_metadata_preservation(self):
        """Test that extra fields are preserved in metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "metadata.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "city", "state", "jitter"])
                writer.writeheader()
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "city": "São Paulo",
                        "state": "SP",
                        "jitter": "5.2",
                    }
                )

            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            assert len(measurements) == 1
            m = measurements[0]
            assert m.metadata["city"] == "São Paulo"
            assert m.metadata["state"] == "SP"
            assert m.metadata["jitter"] == "5.2"
            assert "source_file" in m.metadata
            assert "row_number" in m.metadata

    def test_semicolon_delimiter(self):
        """Test parsing CSV files with semicolon delimiter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "semicolon.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "download"], delimiter=";")
                writer.writeheader()
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "download": "100.0",
                    }
                )

            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            assert len(measurements) == 1
            assert measurements[0].download_mbps == 100.0

    def test_processed_files_persistence(self):
        """Test that processed files tracking persists across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test CSV file
            csv_path = Path(tmpdir) / "test.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp"])
                writer.writeheader()
                writer.writerow({"latitude": "-23.5505", "longitude": "-46.6333", "timestamp": "2026-01-15T10:00:00"})

            # First instance processes the file
            source1 = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements1 = source1.fetch()
            assert len(measurements1) == 1

            # Second instance should see the file as already processed
            source2 = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements2 = source2.fetch()
            assert len(measurements2) == 0

    def test_zero_values_handling(self):
        """Test that zero values are correctly parsed, not treated as None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "zeros.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["latitude", "longitude", "timestamp", "download", "upload", "latency"]
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "download": "0",  # Zero should be parsed as 0.0, not None
                        "upload": "0.0",  # Zero should be parsed as 0.0, not None
                        "latency": "0",
                    }
                )

            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            assert len(measurements) == 1
            m = measurements[0]
            assert m.download_mbps == 0.0
            assert m.upload_mbps == 0.0
            assert m.latency_ms == 0.0

    def test_none_values_in_csv(self):
        """Test handling of None values in CSV cells."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "none_values.csv"
            # Create CSV with empty cells (which read as empty strings, not None in csv module)
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "download", "provider"])
                writer.writeheader()
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "download": "",  # Empty cell
                        "provider": "",  # Empty cell
                    }
                )

            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            # Should successfully parse with None for empty fields
            assert len(measurements) == 1
            m = measurements[0]
            assert m.download_mbps is None
            assert m.provider is None

    def test_missing_required_fields(self):
        """Test that rows with missing required fields are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "missing_required.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "timestamp", "download"])
                writer.writeheader()
                # Valid row
                writer.writerow(
                    {
                        "latitude": "-23.5505",
                        "longitude": "-46.6333",
                        "timestamp": "2026-01-15T10:00:00",
                        "download": "100.0",
                    }
                )
                # Missing latitude
                writer.writerow(
                    {"latitude": "", "longitude": "-46.6333", "timestamp": "2026-01-15T11:00:00", "download": "85.0"}
                )
                # Missing longitude
                writer.writerow(
                    {"latitude": "-23.5505", "longitude": "", "timestamp": "2026-01-15T12:00:00", "download": "90.0"}
                )
                # Valid row
                writer.writerow(
                    {
                        "latitude": "-22.9068",
                        "longitude": "-43.1729",
                        "timestamp": "2026-01-15T13:00:00",
                        "download": "95.0",
                    }
                )

            source = ManualCSVSource(watch_dir=Path(tmpdir))
            measurements = source.fetch()

            # Should only get the 2 valid rows
            assert len(measurements) == 2
