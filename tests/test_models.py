"""Tests for data models."""

import pytest

from src.models import ConnectivityPoint, QualityScore, SpeedTest


def test_connectivity_point_creation():
    """Test ConnectivityPoint creation and basic properties."""
    speed_test = SpeedTest(download=100.0, upload=15.0, latency=30.0, jitter=5.0, packet_loss=0.5)

    point = ConnectivityPoint(latitude=-23.5505, longitude=-46.6333, provider="Starlink", speed_test=speed_test)

    assert point.latitude == -23.5505
    assert point.longitude == -46.6333
    assert point.provider == "Starlink"
    assert point.speed_test == speed_test
    assert point.quality_score is not None
    assert point.id is not None
    assert point.timestamp is not None


def test_speed_test_stability_calculation():
    """Test SpeedTest stability calculation."""
    # Test with low jitter and packet loss (high stability)
    speed_test_good = SpeedTest(download=100.0, upload=15.0, latency=30.0, jitter=2.0, packet_loss=0.1)

    assert speed_test_good.stability > 90

    # Test with high jitter and packet loss (low stability)
    speed_test_poor = SpeedTest(download=100.0, upload=15.0, latency=30.0, jitter=20.0, packet_loss=5.0)

    assert speed_test_poor.stability <= 20

    # Test with obstruction (satellite-specific metric)
    speed_test_obstructed = SpeedTest(
        download=150.0,
        upload=18.0,
        latency=25.0,
        jitter=3.0,
        packet_loss=0.1,
        obstruction=10.0,  # 10% obstruction
    )

    # With 10% obstruction, penalty should be 10 * 5 = 50 points
    # Base: 100 - jitter(6) - packet_loss(1) - obstruction(50) = 43
    assert 40 <= speed_test_obstructed.stability <= 45


def test_quality_score_calculation():
    """Test QualityScore calculation from SpeedTest."""
    # Test excellent quality (high speed, low latency)
    speed_test_excellent = SpeedTest(
        download=200.0,  # At target
        upload=20.0,  # At target
        latency=20.0,  # At target
        jitter=1.0,
        packet_loss=0.0,
    )

    quality_excellent = QualityScore.calculate(speed_test_excellent)

    assert quality_excellent.overall_score >= 80
    assert quality_excellent.rating == "Excellent"

    # Test poor quality (low speed, high latency)
    speed_test_poor = SpeedTest(download=20.0, upload=2.0, latency=150.0, jitter=25.0, packet_loss=5.0)

    quality_poor = QualityScore.calculate(speed_test_poor)

    assert quality_poor.overall_score < 40
    assert quality_poor.rating == "Poor"


def test_model_serialization():
    """Test model to_dict and from_dict serialization."""
    # Create original point
    speed_test = SpeedTest(download=150.0, upload=18.0, latency=25.0, jitter=3.0, packet_loss=0.2)

    original_point = ConnectivityPoint(
        latitude=-15.7801, longitude=-47.9292, provider="Starlink", speed_test=speed_test, point_id="test-123"
    )

    # Serialize to dict
    point_dict = original_point.to_dict()

    assert "id" in point_dict
    assert "latitude" in point_dict
    assert "speed_test" in point_dict
    assert "quality_score" in point_dict

    # Deserialize from dict
    restored_point = ConnectivityPoint.from_dict(point_dict)

    assert restored_point.id == original_point.id
    assert restored_point.latitude == original_point.latitude
    assert restored_point.longitude == original_point.longitude
    assert restored_point.provider == original_point.provider
    assert restored_point.speed_test.download == original_point.speed_test.download


def test_model_validation():
    """Test model validation and error handling."""
    # Test SpeedTest with valid data
    valid_speed_test = SpeedTest(download=100.0, upload=15.0, latency=30.0)

    assert valid_speed_test.download == pytest.approx(100.0)
    assert valid_speed_test.jitter == pytest.approx(0.0)  # Default value
    assert valid_speed_test.packet_loss == pytest.approx(0.0)  # Default value
    assert valid_speed_test.obstruction == pytest.approx(0.0)  # Default value

    # Test SpeedTest to_dict
    st_dict = valid_speed_test.to_dict()
    assert st_dict["download"] == pytest.approx(100.0)
    assert "stability" in st_dict
    assert "obstruction" in st_dict

    # Test from_dict with partial data
    partial_dict = {"download": 50.0, "upload": 5.0, "latency": 60.0}

    restored_st = SpeedTest.from_dict(partial_dict)
    assert restored_st.download == pytest.approx(50.0)
    assert restored_st.jitter == pytest.approx(0.0)
    assert restored_st.obstruction == pytest.approx(0.0)


def test_speed_test_obstruction_calculation():
    """Test SpeedTest stability calculation with obstruction metric."""
    # Test with no obstruction (non-satellite connection)
    speed_test_no_obstruction = SpeedTest(
        download=100.0, upload=15.0, latency=30.0, jitter=2.0, packet_loss=0.1, obstruction=0.0
    )

    # Stability should be high with low jitter and packet loss
    assert speed_test_no_obstruction.stability > 90

    # Test with moderate obstruction (satellite connection)
    speed_test_with_obstruction = SpeedTest(
        download=150.0,
        upload=20.0,
        latency=25.0,
        jitter=3.0,
        packet_loss=0.1,
        obstruction=5.0,  # 5% obstruction
    )

    # Obstruction should reduce stability score
    # Base 100 - jitter(3*2=6) - packet_loss(0.1*10=1) - obstruction(5*5=25) = 68
    assert 65 <= speed_test_with_obstruction.stability <= 70

    # Test with high obstruction (poor satellite line of sight)
    speed_test_high_obstruction = SpeedTest(
        download=100.0,
        upload=15.0,
        latency=30.0,
        jitter=5.0,
        packet_loss=1.0,
        obstruction=10.0,  # 10% obstruction
    )

    # High obstruction should significantly reduce stability
    # Base 100 - jitter(10) - packet_loss(10) - obstruction(10*5=50) = 30
    assert 28 <= speed_test_high_obstruction.stability <= 32
