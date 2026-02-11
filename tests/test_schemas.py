"""Unit tests for schema validation and normalization."""

from datetime import datetime, timezone

UTC = timezone.utc

import pytest
from pydantic import ValidationError

from src.schemas import ConfidenceBreakdown, MeasurementSchema, SourceType, TechnologyType


class TestMeasurementSchema:
    """Tests for the canonical measurement schema."""

    def test_valid_measurement_creation(self):
        """Test creating a valid measurement."""
        measurement = MeasurementSchema(
            id="test123",
            lat=-15.7801,
            lon=-47.9292,
            timestamp_utc=datetime.now(UTC),
            download_mbps=100.0,
            upload_mbps=20.0,
            latency_ms=25.0,
            technology=TechnologyType.FIBER,
            source=SourceType.ANATEL,
            provider="Test Provider",
            country="BR",
        )

        assert measurement.id == "test123"
        assert measurement.lat == -15.7801
        assert measurement.lon == -47.9292
        assert measurement.download_mbps == 100.0
        assert measurement.upload_mbps == 20.0
        assert measurement.latency_ms == 25.0
        assert measurement.technology == TechnologyType.FIBER
        assert measurement.source == SourceType.ANATEL

    def test_latitude_range_validation(self):
        """Test that latitude must be in valid range."""
        # Valid latitude
        MeasurementSchema(
            id="test",
            lat=45.0,
            lon=0.0,
            timestamp_utc=datetime.now(UTC),
            source=SourceType.ANATEL,
        )

        # Invalid: too high
        with pytest.raises(ValidationError):
            MeasurementSchema(
                id="test",
                lat=91.0,
                lon=0.0,
                timestamp_utc=datetime.now(UTC),
                source=SourceType.ANATEL,
            )

        # Invalid: too low
        with pytest.raises(ValidationError):
            MeasurementSchema(
                id="test",
                lat=-91.0,
                lon=0.0,
                timestamp_utc=datetime.now(UTC),
                source=SourceType.ANATEL,
            )

    def test_longitude_range_validation(self):
        """Test that longitude must be in valid range."""
        # Valid longitude
        MeasurementSchema(
            id="test",
            lat=0.0,
            lon=120.0,
            timestamp_utc=datetime.now(UTC),
            source=SourceType.ANATEL,
        )

        # Invalid: too high
        with pytest.raises(ValidationError):
            MeasurementSchema(
                id="test",
                lat=0.0,
                lon=181.0,
                timestamp_utc=datetime.now(UTC),
                source=SourceType.ANATEL,
            )

        # Invalid: too low
        with pytest.raises(ValidationError):
            MeasurementSchema(
                id="test",
                lat=0.0,
                lon=-181.0,
                timestamp_utc=datetime.now(UTC),
                source=SourceType.ANATEL,
            )

    def test_speed_metrics_non_negative(self):
        """Test that speed metrics cannot be negative."""
        # Valid speeds
        MeasurementSchema(
            id="test",
            lat=0.0,
            lon=0.0,
            timestamp_utc=datetime.now(UTC),
            download_mbps=100.0,
            upload_mbps=20.0,
            latency_ms=25.0,
            source=SourceType.ANATEL,
        )

        # Invalid: negative download
        with pytest.raises(ValidationError):
            MeasurementSchema(
                id="test",
                lat=0.0,
                lon=0.0,
                timestamp_utc=datetime.now(UTC),
                download_mbps=-10.0,
                source=SourceType.ANATEL,
            )

    def test_optional_fields(self):
        """Test that optional fields can be None."""
        measurement = MeasurementSchema(
            id="test",
            lat=0.0,
            lon=0.0,
            timestamp_utc=datetime.now(UTC),
            source=SourceType.ANATEL,
            # All metrics optional
            download_mbps=None,
            upload_mbps=None,
            latency_ms=None,
            provider=None,
        )

        assert measurement.download_mbps is None
        assert measurement.upload_mbps is None
        assert measurement.latency_ms is None
        assert measurement.provider is None

    def test_default_technology(self):
        """Test that technology defaults to UNKNOWN."""
        measurement = MeasurementSchema(
            id="test",
            lat=0.0,
            lon=0.0,
            timestamp_utc=datetime.now(UTC),
            source=SourceType.ANATEL,
        )

        assert measurement.technology == TechnologyType.UNKNOWN

    def test_metadata_default_empty_dict(self):
        """Test that metadata defaults to empty dict."""
        measurement = MeasurementSchema(
            id="test",
            lat=0.0,
            lon=0.0,
            timestamp_utc=datetime.now(UTC),
            source=SourceType.ANATEL,
        )

        assert measurement.metadata == {}

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        timestamp = datetime.now(UTC)
        measurement = MeasurementSchema(
            id="test123",
            lat=-15.7801,
            lon=-47.9292,
            timestamp_utc=timestamp,
            download_mbps=100.0,
            upload_mbps=20.0,
            latency_ms=25.0,
            technology=TechnologyType.FIBER,
            source=SourceType.ANATEL,
            provider="Test Provider",
            metadata={"key": "value"},
        )

        data = measurement.to_dict()

        assert data["id"] == "test123"
        assert data["lat"] == -15.7801
        assert data["lon"] == -47.9292
        assert data["download_mbps"] == 100.0
        assert data["technology"] == "fiber"
        assert data["source"] == "anatel"
        assert "timestamp_utc" in data
        assert data["metadata"] == {"key": "value"}

    def test_from_dict_conversion(self):
        """Test creation from dictionary."""
        data = {
            "id": "test123",
            "lat": -15.7801,
            "lon": -47.9292,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "download_mbps": 100.0,
            "upload_mbps": 20.0,
            "latency_ms": 25.0,
            "technology": "fiber",
            "source": "anatel",
            "provider": "Test Provider",
            "metadata": {"key": "value"},
        }

        measurement = MeasurementSchema.from_dict(data)

        assert measurement.id == "test123"
        assert measurement.download_mbps == 100.0
        assert measurement.technology == TechnologyType.FIBER
        assert measurement.source == SourceType.ANATEL
        assert measurement.metadata == {"key": "value"}

    def test_timestamp_parsing_iso_format(self):
        """Test parsing ISO format timestamps."""
        # ISO format with Z
        measurement = MeasurementSchema(
            id="test",
            lat=0.0,
            lon=0.0,
            timestamp_utc="2024-01-15T10:30:00Z",
            source=SourceType.ANATEL,
        )
        assert isinstance(measurement.timestamp_utc, datetime)

        # ISO format without Z
        measurement = MeasurementSchema(
            id="test",
            lat=0.0,
            lon=0.0,
            timestamp_utc="2024-01-15T10:30:00",
            source=SourceType.ANATEL,
        )
        assert isinstance(measurement.timestamp_utc, datetime)

    def test_confidence_score_range(self):
        """Test that confidence score must be 0-100."""
        # Valid
        measurement = MeasurementSchema(
            id="test",
            lat=0.0,
            lon=0.0,
            timestamp_utc=datetime.now(UTC),
            source=SourceType.ANATEL,
            confidence_score=85.5,
        )
        assert measurement.confidence_score == 85.5

        # Invalid: too high
        with pytest.raises(ValidationError):
            MeasurementSchema(
                id="test",
                lat=0.0,
                lon=0.0,
                timestamp_utc=datetime.now(UTC),
                source=SourceType.ANATEL,
                confidence_score=101.0,
            )

        # Invalid: negative
        with pytest.raises(ValidationError):
            MeasurementSchema(
                id="test",
                lat=0.0,
                lon=0.0,
                timestamp_utc=datetime.now(UTC),
                source=SourceType.ANATEL,
                confidence_score=-5.0,
            )


class TestConfidenceBreakdown:
    """Tests for confidence breakdown schema."""

    def test_valid_breakdown_creation(self):
        """Test creating a valid confidence breakdown."""
        breakdown = ConfidenceBreakdown(
            recency_score=90.0,
            source_reliability_score=85.0,
            consistency_score=95.0,
            completeness_score=80.0,
        )

        assert breakdown.recency_score == 90.0
        assert breakdown.source_reliability_score == 85.0
        assert breakdown.consistency_score == 95.0
        assert breakdown.completeness_score == 80.0

    def test_breakdown_score_range_validation(self):
        """Test that breakdown scores must be 0-100."""
        # Valid
        ConfidenceBreakdown(
            recency_score=0.0,
            source_reliability_score=50.0,
            consistency_score=100.0,
            completeness_score=75.5,
        )

        # Invalid: too high
        with pytest.raises(ValidationError):
            ConfidenceBreakdown(
                recency_score=101.0,
                source_reliability_score=50.0,
                consistency_score=50.0,
                completeness_score=50.0,
            )

        # Invalid: negative
        with pytest.raises(ValidationError):
            ConfidenceBreakdown(
                recency_score=50.0,
                source_reliability_score=-10.0,
                consistency_score=50.0,
                completeness_score=50.0,
            )

    def test_breakdown_to_dict(self):
        """Test breakdown to dictionary conversion."""
        breakdown = ConfidenceBreakdown(
            recency_score=90.0,
            source_reliability_score=85.0,
            consistency_score=95.0,
            completeness_score=80.0,
        )

        data = breakdown.to_dict()

        assert data["recency_score"] == 90.0
        assert data["source_reliability_score"] == 85.0
        assert data["consistency_score"] == 95.0
        assert data["completeness_score"] == 80.0


class TestEnumerations:
    """Tests for enum types."""

    def test_source_type_values(self):
        """Test that all expected source types exist."""
        expected_sources = ["crowdsource", "anatel", "ibge", "starlink", "speedtest", "manual", "other"]

        actual_sources = [s.value for s in SourceType]

        for expected in expected_sources:
            assert expected in actual_sources

    def test_technology_type_values(self):
        """Test that all expected technology types exist."""
        expected_techs = [
            "fiber",
            "cable",
            "dsl",
            "satellite",
            "mobile_4g",
            "mobile_5g",
            "fixed_wireless",
            "other",
            "unknown",
        ]

        actual_techs = [t.value for t in TechnologyType]

        for expected in expected_techs:
            assert expected in actual_techs
