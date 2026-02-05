"""Tests for export utilities."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from src.utils.export_utils import (
    _generate_farm_recommendations,
    _get_quality_distribution,
    export_ecosystem_bundle,
    export_for_agrix_boost,
    export_for_hybrid_simulator,
)


@pytest.fixture
def sample_data():
    """Create sample connectivity data for testing."""
    return [
        {
            "id": "test-1",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "provider": "Starlink",
            "timestamp": "2026-01-15T10:30:00",
            "speed_test": {
                "download": 165.4,
                "upload": 22.8,
                "latency": 28.5,
                "jitter": 3.2,
                "packet_loss": 0.1,
                "stability": 96.6,
            },
            "quality_score": {
                "overall_score": 100.0,
                "speed_score": 95.0,
                "latency_score": 89.4,
                "stability_score": 96.6,
                "rating": "Excellent",
            },
        },
        {
            "id": "test-2",
            "latitude": -22.9068,
            "longitude": -43.1729,
            "provider": "Claro",
            "timestamp": "2026-01-15T11:00:00",
            "speed_test": {
                "download": 92.1,
                "upload": 15.3,
                "latency": 38.7,
                "jitter": 6.5,
                "packet_loss": 0.8,
                "stability": 85.0,
            },
            "quality_score": {
                "overall_score": 82.2,
                "speed_score": 75.0,
                "latency_score": 76.6,
                "stability_score": 85.0,
                "rating": "Excellent",
            },
        },
        {
            "id": "test-3",
            "latitude": -12.9714,
            "longitude": -38.5014,
            "provider": "Viasat",
            "timestamp": "2026-01-15T12:00:00",
            "speed_test": {
                "download": 75.3,
                "upload": 9.8,
                "latency": 68.2,
                "jitter": 15.7,
                "packet_loss": 2.5,
                "stability": 43.6,
            },
            "quality_score": {
                "overall_score": 50.6,
                "speed_score": 60.0,
                "latency_score": 39.8,
                "stability_score": 43.6,
                "rating": "Fair",
            },
        },
    ]


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_export_for_hybrid_simulator(sample_data, temp_output_dir):
    """Test export for Hybrid Architecture Simulator."""
    output_path = str(Path(temp_output_dir) / "hybrid_test.json")

    result = export_for_hybrid_simulator(sample_data, output_path)

    # Verify file was created
    assert Path(result).exists()
    assert result == output_path

    # Load and verify content
    with open(result) as f:
        data = json.load(f)

    # Check metadata
    assert "metadata" in data
    assert data["metadata"]["source"] == "Rural Connectivity Mapper 2026"
    assert data["metadata"]["total_points"] == 3
    assert data["metadata"]["purpose"] == "failover_testing"
    assert "export_timestamp" in data["metadata"]

    # Check connectivity points
    assert "connectivity_points" in data
    assert len(data["connectivity_points"]) == 3

    # Verify first point structure
    point = data["connectivity_points"][0]
    assert point["point_id"] == "test-1"
    assert point["provider"] == "Starlink"
    assert point["location"]["latitude"] == -23.5505
    assert point["location"]["longitude"] == -46.6333

    # Check metrics
    assert point["metrics"]["signal_quality"] == pytest.approx(100.0)
    assert point["metrics"]["latency_ms"] == pytest.approx(28.5)
    assert point["metrics"]["download_mbps"] == pytest.approx(165.4)
    assert point["metrics"]["upload_mbps"] == pytest.approx(22.8)
    assert point["metrics"]["stability_score"] == pytest.approx(96.6)

    # Check quality breakdown
    assert point["quality_breakdown"]["overall_score"] == pytest.approx(100.0)
    assert point["quality_breakdown"]["rating"] == "Excellent"

    # Check failover indicators
    assert point["failover_indicators"]["connection_reliable"] is True
    assert point["failover_indicators"]["low_latency"] is True
    assert point["failover_indicators"]["stable_connection"] is True
    assert point["failover_indicators"]["recommended_primary"] is True


def test_export_for_agrix_boost(sample_data, temp_output_dir):
    """Test export for AgriX-Boost."""
    output_path = str(Path(temp_output_dir) / "agrix_test.json")

    result = export_for_agrix_boost(sample_data, output_path)

    # Verify file was created
    assert Path(result).exists()
    assert result == output_path

    # Load and verify content
    with open(result) as f:
        data = json.load(f)

    # Check metadata
    assert "metadata" in data
    assert data["metadata"]["source"] == "Rural Connectivity Mapper 2026"
    assert data["metadata"]["total_locations"] == 3
    assert data["metadata"]["purpose"] == "farm_connectivity_layer"

    # Check connectivity layer
    assert "connectivity_layer" in data
    assert len(data["connectivity_layer"]) == 3

    # Verify first point structure
    point = data["connectivity_layer"][0]
    assert point["location_id"] == "test-1"
    assert point["isp_provider"] == "Starlink"
    assert point["coordinates"]["lat"] == -23.5505
    assert point["coordinates"]["lon"] == -46.6333

    # Check connectivity status
    assert point["connectivity_status"]["quality_rating"] == "Excellent"
    assert point["connectivity_status"]["quality_score"] == pytest.approx(100.0)
    assert point["connectivity_status"]["is_operational"] is True
    assert point["connectivity_status"]["is_optimal"] is True

    # Check network performance
    assert point["network_performance"]["download_speed_mbps"] == pytest.approx(165.4)
    assert point["network_performance"]["upload_speed_mbps"] == pytest.approx(22.8)
    assert point["network_performance"]["latency_ms"] == pytest.approx(28.5)

    # Check farm suitability
    assert point["farm_suitability"]["iot_sensors_supported"] is True
    assert point["farm_suitability"]["video_monitoring_supported"] is True
    assert point["farm_suitability"]["real_time_control_supported"] is True
    assert point["farm_suitability"]["data_analytics_supported"] is True

    # Check recommendations exist
    assert "recommendations" in point
    assert isinstance(point["recommendations"], list)
    assert len(point["recommendations"]) > 0


def test_export_ecosystem_bundle(sample_data, temp_output_dir):
    """Test export of complete ecosystem bundle."""
    output_dir = str(Path(temp_output_dir) / "ecosystem_bundle")

    result = export_ecosystem_bundle(sample_data, output_dir)

    # Verify all files were created
    assert "hybrid_simulator" in result
    assert "agrix_boost" in result
    assert "manifest" in result

    assert Path(result["hybrid_simulator"]).exists()
    assert Path(result["agrix_boost"]).exists()
    assert Path(result["manifest"]).exists()

    # Load and verify manifest
    with open(result['manifest'], 'r') as f:
        manifest = json.load(f)

    assert manifest["ecosystem"] == "Rural Connectivity Ecosystem 2026"
    assert "components" in manifest
    assert "rural_connectivity_mapper" in manifest["components"]
    assert "hybrid_architecture_simulator" in manifest["components"]
    assert "agrix_boost" in manifest["components"]

    # Check data summary
    assert manifest["data_summary"]["total_points"] == 3
    assert "providers" in manifest["data_summary"]
    assert "Starlink" in manifest["data_summary"]["providers"]

    # Check quality distribution
    quality_dist = manifest["data_summary"]["quality_distribution"]
    assert quality_dist["Excellent"] == 2
    assert quality_dist["Fair"] == 1


def test_generate_farm_recommendations_excellent():
    """Test farm recommendations for excellent connectivity."""
    speed_test = {"download": 165.4, "upload": 22.8, "latency": 28.5, "stability": 96.6}
    quality_score = {"overall_score": 100.0}

    recommendations = _generate_farm_recommendations(speed_test, quality_score)

    assert len(recommendations) > 0
    assert any("Excellent connectivity" in rec for rec in recommendations)
    assert any("precision agriculture" in rec for rec in recommendations)
    assert any("video monitoring" in rec for rec in recommendations)


def test_generate_farm_recommendations_poor():
    """Test farm recommendations for poor connectivity."""
    speed_test = {"download": 15.0, "upload": 2.0, "latency": 150.0, "stability": 50.0}
    quality_score = {"overall_score": 30.0}

    recommendations = _generate_farm_recommendations(speed_test, quality_score)

    assert len(recommendations) > 0
    assert any("Poor connectivity" in rec for rec in recommendations)
    assert any("High latency" in rec for rec in recommendations)


def test_generate_farm_recommendations_fair():
    """Test farm recommendations for fair connectivity."""
    speed_test = {"download": 30.0, "upload": 8.0, "latency": 80.0, "stability": 65.0}
    quality_score = {"overall_score": 50.0}

    recommendations = _generate_farm_recommendations(speed_test, quality_score)

    assert len(recommendations) > 0
    assert any("Fair connectivity" in rec for rec in recommendations)


def test_get_quality_distribution(sample_data):
    """Test quality distribution calculation."""
    distribution = _get_quality_distribution(sample_data)

    assert distribution["Excellent"] == 2
    assert distribution["Good"] == 0
    assert distribution["Fair"] == 1
    assert distribution["Poor"] == 0


def test_export_empty_data(temp_output_dir):
    """Test export with empty data."""
    output_path = str(Path(temp_output_dir) / "empty_test.json")

    result = export_for_hybrid_simulator([], output_path)

    assert Path(result).exists()
    
    with open(result, 'r') as f:
        data = json.load(f)

    assert data["metadata"]["total_points"] == 0
    assert len(data["connectivity_points"]) == 0


def test_failover_indicators_thresholds(sample_data, temp_output_dir):
    """Test that failover indicators use correct thresholds."""
    output_path = str(Path(temp_output_dir) / "failover_test.json")

    result = export_for_hybrid_simulator(sample_data, output_path)
    
    with open(result, 'r') as f:
        data = json.load(f)

    # Check Fair quality point (index 2)
    fair_point = data["connectivity_points"][2]

    # Fair quality (50.6) is below threshold (< 60), so not recommended as primary
    assert fair_point["failover_indicators"]["recommended_primary"] is False
    # Fair quality (50.6) is below reliable threshold (< 60)
    assert fair_point["failover_indicators"]["connection_reliable"] is False
    # Latency 68.2ms is < 100, so low_latency should be True
    assert fair_point["failover_indicators"]["low_latency"] is True
    # Stability 43.6 is < 70, so stable_connection should be False
    assert fair_point["failover_indicators"]["stable_connection"] is False


def test_farm_suitability_thresholds(sample_data, temp_output_dir):
    """Test that farm suitability indicators use correct thresholds."""
    output_path = str(Path(temp_output_dir) / "suitability_test.json")

    result = export_for_agrix_boost(sample_data, output_path)
    
    with open(result, 'r') as f:
        data = json.load(f)

    # Check Fair quality point (index 2)
    fair_point = data["connectivity_layer"][2]
    suitability = fair_point["farm_suitability"]

    # Latency 68.2 < 200 and overall 50.6 >= 40, so IoT should be supported
    assert suitability["iot_sensors_supported"] is True

    # Download 75.3 >= 25 and overall 50.6 >= 60 is False, so video should NOT be supported
    assert suitability["video_monitoring_supported"] is False

    # Latency 68.2 is not < 50, so real-time control NOT supported
    assert suitability["real_time_control_supported"] is False

    # Download 75.3 >= 10 and overall 50.6 >= 40, so data analytics should be supported
    assert suitability["data_analytics_supported"] is True
