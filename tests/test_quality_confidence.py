"""Unit tests for quality and confidence scoring."""

from datetime import UTC, datetime, timedelta
from typing import Any

from src.quality import ConfidenceCalculator, SourceReliabilityWeights
from src.schemas import MeasurementSchema, SourceType, TechnologyType


class TestSourceReliabilityWeights:
    """Tests for source reliability weights."""

    def test_weights_defined_for_all_sources(self):
        """Ensure weights are defined for all source types."""
        for source_type in SourceType:
            weight = SourceReliabilityWeights.get_weight(source_type)
            assert 0.0 <= weight <= 1.0

    def test_anatel_highest_weight(self):
        """ANATEL should have highest reliability weight."""
        anatel_weight = SourceReliabilityWeights.get_weight(SourceType.ANATEL)

        for source_type in SourceType:
            if source_type != SourceType.ANATEL:
                weight = SourceReliabilityWeights.get_weight(source_type)
                assert anatel_weight >= weight

    def test_crowdsource_lower_than_official(self):
        """Crowdsource should have lower weight than official sources."""
        crowdsource_weight = SourceReliabilityWeights.get_weight(SourceType.CROWDSOURCE)
        anatel_weight = SourceReliabilityWeights.get_weight(SourceType.ANATEL)
        ibge_weight = SourceReliabilityWeights.get_weight(SourceType.IBGE)

        assert crowdsource_weight < anatel_weight
        assert crowdsource_weight < ibge_weight


class TestConfidenceCalculator:
    """Tests for confidence score calculation."""

    def create_measurement(
        self,
        days_old: int = 0,
        source: SourceType = SourceType.ANATEL,
        download: float | None = 100.0,
        upload: float | None = 20.0,
        latency: float | None = 25.0,
        technology: TechnologyType = TechnologyType.FIBER,
        provider: str | None = "Test Provider",
        metadata: dict[str, Any] | None = None,
    ) -> MeasurementSchema:
        """Helper to create test measurements."""
        timestamp = datetime.now(UTC) - timedelta(days=days_old)

        return MeasurementSchema(
            id=f"test_{days_old}",
            lat=-15.7801,
            lon=-47.9292,
            timestamp_utc=timestamp,
            download_mbps=download,
            upload_mbps=upload,
            latency_ms=latency,
            technology=technology,
            source=source,
            provider=provider,
            confidence_score=None,
            confidence_breakdown=None,
            metadata=metadata or {},
            country="BR",
            region="BR",
            h3_index="test_h3",
        )

    def test_fresh_data_high_recency_score(self):
        """Fresh data (< 7 days) should get 100% recency score."""
        measurement = self.create_measurement(days_old=3)
        score, breakdown = ConfidenceCalculator.calculate(measurement)

        assert breakdown.recency_score == 100.0

    def test_old_data_low_recency_score(self):
        """Old data (> 365 days) should get 0% recency score."""
        measurement = self.create_measurement(days_old=400)
        score, breakdown = ConfidenceCalculator.calculate(measurement)

        assert breakdown.recency_score == 0.0

    def test_medium_age_data_decaying_score(self):
        """Medium age data should have linearly decaying score."""
        measurement_30d = self.create_measurement(days_old=30)
        measurement_180d = self.create_measurement(days_old=180)

        _, breakdown_30d = ConfidenceCalculator.calculate(measurement_30d)
        _, breakdown_180d = ConfidenceCalculator.calculate(measurement_180d)

        assert 0 < breakdown_180d.recency_score < 100
        assert breakdown_30d.recency_score > breakdown_180d.recency_score

    def test_source_reliability_scores(self):
        """Different sources should have different reliability scores."""
        anatel = self.create_measurement(source=SourceType.ANATEL)
        crowdsource = self.create_measurement(source=SourceType.CROWDSOURCE)

        _, anatel_breakdown = ConfidenceCalculator.calculate(anatel)
        _, crowdsource_breakdown = ConfidenceCalculator.calculate(crowdsource)

        assert anatel_breakdown.source_reliability_score > crowdsource_breakdown.source_reliability_score

    def test_valid_metrics_high_consistency_score(self):
        """Valid metrics within normal ranges should get high consistency score."""
        measurement = self.create_measurement(download=100.0, upload=20.0, latency=25.0)

        _, breakdown = ConfidenceCalculator.calculate(measurement)

        assert breakdown.consistency_score >= 80.0

    def test_outlier_metrics_low_consistency_score(self):
        """Outlier metrics should reduce consistency score."""
        measurement = self.create_measurement(
            download=15000.0,  # Unrealistically high
            upload=20.0,
            latency=25.0,
        )

        _, breakdown = ConfidenceCalculator.calculate(measurement)

        assert breakdown.consistency_score < 80.0

    def test_suspicious_ratio_reduces_consistency(self):
        """Upload > Download * 2 should reduce consistency score."""
        measurement = self.create_measurement(
            download=10.0,
            upload=50.0,  # Suspicious ratio
            latency=25.0,
        )

        _, breakdown = ConfidenceCalculator.calculate(measurement)

        assert breakdown.consistency_score < 100.0

    def test_complete_metadata_high_completeness_score(self):
        """Measurements with complete metadata should score higher."""
        complete = self.create_measurement(provider="Test Provider", metadata={"test": "data", "extra": "info"})

        incomplete = self.create_measurement(provider=None, metadata={})

        _, complete_breakdown = ConfidenceCalculator.calculate(complete)
        _, incomplete_breakdown = ConfidenceCalculator.calculate(incomplete)

        assert complete_breakdown.completeness_score > incomplete_breakdown.completeness_score

    def test_overall_score_range(self):
        """Overall score should always be between 0 and 100."""
        # Test various scenarios
        scenarios = [
            self.create_measurement(days_old=0),
            self.create_measurement(days_old=180),
            self.create_measurement(days_old=500),
            self.create_measurement(source=SourceType.CROWDSOURCE),
            self.create_measurement(download=15000.0),  # Outlier
        ]

        for measurement in scenarios:
            score, _ = ConfidenceCalculator.calculate(measurement)
            assert 0.0 <= score <= 100.0

    def test_overall_score_is_weighted_average(self):
        """Overall score should be weighted average of components."""
        measurement = self.create_measurement()
        score, breakdown = ConfidenceCalculator.calculate(measurement)

        expected_score = (
            breakdown.recency_score * ConfidenceCalculator.RECENCY_WEIGHT
            + breakdown.source_reliability_score * ConfidenceCalculator.SOURCE_WEIGHT
            + breakdown.consistency_score * ConfidenceCalculator.CONSISTENCY_WEIGHT
            + breakdown.completeness_score * ConfidenceCalculator.COMPLETENESS_WEIGHT
        )

        assert abs(score - expected_score) < 0.01

    def test_high_quality_measurement_high_score(self):
        """High quality measurement should get high overall score."""
        measurement = self.create_measurement(
            days_old=1,  # Fresh
            source=SourceType.ANATEL,  # Reliable
            download=100.0,  # Valid
            upload=20.0,  # Valid
            latency=25.0,  # Valid
            provider="Test Provider",
            metadata={"quality": "high"},
        )

        score, _ = ConfidenceCalculator.calculate(measurement)

        assert score >= 80.0

    def test_low_quality_measurement_low_score(self):
        """Low quality measurement should get low overall score."""
        measurement = self.create_measurement(
            days_old=400,  # Very old
            source=SourceType.OTHER,  # Unreliable
            download=None,  # Missing
            upload=None,  # Missing
            latency=3000.0,  # Outlier
            provider=None,
            metadata={},
        )

        score, _ = ConfidenceCalculator.calculate(measurement)

        assert score < 40.0

    def test_future_timestamp_low_recency(self):
        """Future timestamps should get low recency score."""
        future_time = datetime.now(UTC) + timedelta(days=10)
        measurement = MeasurementSchema(
            id="future_test",
            lat=-15.7801,
            lon=-47.9292,
            timestamp_utc=future_time,
            download_mbps=100.0,
            upload_mbps=20.0,
            latency_ms=25.0,
            source=SourceType.ANATEL,
            provider="Test Provider",
            confidence_score=None,
            confidence_breakdown=None,
            country="BR",
            region="BR",
            h3_index="test_h3",
        )

        _, breakdown = ConfidenceCalculator.calculate(measurement)

        assert breakdown.recency_score < 20.0


class TestConfidenceBreakdown:
    """Tests for confidence breakdown structure."""

    def test_breakdown_to_dict(self):
        """Test breakdown conversion to dictionary."""
        measurement = MeasurementSchema(
            id="test",
            lat=-15.7801,
            lon=-47.9292,
            timestamp_utc=datetime.now(UTC),
            download_mbps=100.0,
            upload_mbps=20.0,
            latency_ms=25.0,
            source=SourceType.ANATEL,
            provider="Test Provider",
            confidence_score=None,
            confidence_breakdown=None,
            country="BR",
            region="BR",
            h3_index="test_h3",
        )

        _, breakdown = ConfidenceCalculator.calculate(measurement)
        breakdown_dict = breakdown.to_dict()

        assert "recency_score" in breakdown_dict
        assert "source_reliability_score" in breakdown_dict
        assert "consistency_score" in breakdown_dict
        assert "completeness_score" in breakdown_dict

        for score in breakdown_dict.values():
            assert 0.0 <= score <= 100.0
