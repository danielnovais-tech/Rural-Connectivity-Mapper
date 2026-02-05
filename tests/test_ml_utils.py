"""Tests for ML utilities."""

import pytest

pytest.importorskip("numpy", exc_type=ImportError)
pytest.importorskip("sklearn", exc_type=ImportError)

from src.utils.ml_utils import (
    analyze_starlink_roi,
    calculate_distance_from_major_city,
    extract_geospatial_features,
    generate_ml_report,
    identify_expansion_zones,
    predict_improvement_potential,
)


def create_sample_point(lat, lon, quality_score, download, upload, latency, provider="Test ISP"):
    """Create a sample connectivity point for testing."""
    return {
        "latitude": lat,
        "longitude": lon,
        "provider": provider,
        "quality_score": {"overall_score": quality_score, "rating": "Good" if quality_score >= 60 else "Poor"},
        "speed_test": {"download": download, "upload": upload, "latency": latency, "jitter": 5.0, "packet_loss": 0.1},
        "timestamp": "2026-01-01T00:00:00",
    }


def test_calculate_distance_from_major_city():
    """Test distance calculation from major cities."""
    # São Paulo coordinates
    distance = calculate_distance_from_major_city(-23.5505, -46.6333)
    assert distance >= 0
    assert distance < 10  # Should be very close to São Paulo itself

    # Remote area far from cities
    distance_remote = calculate_distance_from_major_city(-10.0, -50.0)
    assert distance_remote > 100  # Should be far from major cities


def test_extract_geospatial_features():
    """Test geospatial feature extraction."""
    data = [
        create_sample_point(-23.5505, -46.6333, 80, 100, 20, 30, "Starlink"),
        create_sample_point(-22.9068, -43.1729, 70, 85, 15, 40, "Claro"),
    ]

    features = extract_geospatial_features(data)

    assert features.shape == (2, 7)  # 2 points, 7 features each
    assert features[0, 0] == -23.5505  # Latitude
    assert features[0, 1] == -46.6333  # Longitude
    assert features[0, 3] == 80  # Quality score
    assert features[0, 4] == 100  # Download speed


def test_predict_improvement_potential():
    """Test ML improvement potential prediction."""
    data = [
        create_sample_point(-23.5505, -46.6333, 80, 100, 20, 30, "Starlink"),
        create_sample_point(-10.0, -50.0, 40, 50, 8, 80, "HughesNet"),
        create_sample_point(-15.7939, -47.8828, 90, 150, 25, 25, "Starlink"),
    ]

    enriched_data = predict_improvement_potential(data)

    assert len(enriched_data) == 3
    assert all("ml_analysis" in point for point in enriched_data)

    # Check ML analysis fields
    ml = enriched_data[0]["ml_analysis"]
    assert "improvement_potential" in ml
    assert "distance_from_city_km" in ml
    assert "is_rural" in ml
    assert "priority_score" in ml

    # Rural area with poor connectivity should have high priority
    rural_poor = [p for p in enriched_data if p["provider"] == "HughesNet"][0]
    assert rural_poor["ml_analysis"]["is_rural"] is True
    assert rural_poor["ml_analysis"]["improvement_potential"] > 0


def test_predict_improvement_potential_insufficient_data():
    """Test ML prediction with insufficient data."""
    data = [create_sample_point(-23.5505, -46.6333, 80, 100, 20, 30, "Starlink")]

    # Should handle gracefully with minimal data
    result = predict_improvement_potential(data)
    assert len(result) == 1


def test_identify_expansion_zones():
    """Test expansion zone identification."""
    data = [
        create_sample_point(-23.5505, -46.6333, 80, 100, 20, 30, "Starlink"),
        create_sample_point(-22.9068, -43.1729, 70, 85, 15, 40, "Claro"),
        create_sample_point(-10.0, -50.0, 40, 50, 8, 80, "HughesNet"),
        create_sample_point(-15.7939, -47.8828, 90, 150, 25, 25, "Starlink"),
        create_sample_point(-12.9714, -38.5014, 55, 60, 10, 70, "Viasat"),
    ]

    zones = identify_expansion_zones(data, n_zones=3)

    assert "total_zones" in zones
    assert "zones" in zones
    assert "top_priority_zone" in zones
    assert zones["total_zones"] <= 3

    # Check zone structure
    for _zone_key, zone_data in zones['zones'].items():
        assert 'center' in zone_data
        assert 'latitude' in zone_data['center']
        assert 'longitude' in zone_data['center']
        assert 'point_count' in zone_data
        assert 'avg_quality_score' in zone_data
        assert 'avg_distance_from_city_km' in zone_data
        assert 'priority_score' in zone_data
        assert 'recommendation' in zone_data


def test_identify_expansion_zones_insufficient_data():
    """Test expansion zones with fewer points than zones."""
    data = [
        create_sample_point(-23.5505, -46.6333, 80, 100, 20, 30, "Starlink"),
        create_sample_point(-22.9068, -43.1729, 70, 85, 15, 40, "Claro"),
    ]

    zones = identify_expansion_zones(data, n_zones=5)

    assert zones["total_zones"] <= len(data)


def test_analyze_starlink_roi():
    """Test Starlink ROI analysis."""
    data = [
        create_sample_point(-23.5505, -46.6333, 80, 100, 20, 30, "Starlink"),
        create_sample_point(-10.0, -50.0, 40, 50, 8, 80, "HughesNet"),
        create_sample_point(-12.0, -52.0, 35, 45, 7, 90, "Viasat"),
        create_sample_point(-15.7939, -47.8828, 90, 150, 25, 25, "Starlink"),
    ]

    roi = analyze_starlink_roi(data)

    assert "total_points" in roi
    assert "rural_points" in roi
    assert "rural_percentage" in roi
    assert "high_priority_points" in roi
    assert "avg_current_quality" in roi
    assert "total_improvement_potential" in roi
    assert "avg_improvement_potential" in roi
    assert "recommendations" in roi
    assert "starlink_suitability_score" in roi

    assert roi["total_points"] == 4
    assert roi["rural_percentage"] >= 0
    assert roi["rural_percentage"] <= 100
    assert roi["starlink_suitability_score"] >= 0
    assert roi["starlink_suitability_score"] <= 100
    assert isinstance(roi["recommendations"], list)
    assert len(roi["recommendations"]) > 0


def test_analyze_starlink_roi_empty_data():
    """Test ROI analysis with empty data."""
    roi = analyze_starlink_roi([])

    assert roi["total_points"] == 0
    assert roi["rural_points"] == 0
    assert roi["high_priority_points"] == 0


def test_generate_ml_report():
    """Test comprehensive ML report generation."""
    data = [
        create_sample_point(-23.5505, -46.6333, 80, 100, 20, 30, "Starlink"),
        create_sample_point(-10.0, -50.0, 40, 50, 8, 80, "HughesNet"),
        create_sample_point(-12.0, -52.0, 35, 45, 7, 90, "Viasat"),
        create_sample_point(-15.7939, -47.8828, 90, 150, 25, 25, "Starlink"),
        create_sample_point(-22.9068, -43.1729, 70, 85, 15, 40, "Claro"),
    ]

    report = generate_ml_report(data)

    assert "summary" in report
    assert "roi_analysis" in report
    assert "expansion_zones" in report
    assert "top_priority_areas" in report
    assert "enriched_data" in report

    # Check summary
    assert report["summary"]["total_points_analyzed"] == 5
    assert "ml_model_version" in report["summary"]

    # Check top priority areas
    assert len(report["top_priority_areas"]) <= 5
    for priority_area in report["top_priority_areas"]:
        assert "provider" in priority_area
        assert "latitude" in priority_area
        assert "longitude" in priority_area
        assert "current_quality" in priority_area
        assert "priority_score" in priority_area
        assert "distance_from_city_km" in priority_area
        assert "is_rural" in priority_area

    # Check enriched data
    assert len(report["enriched_data"]) == 5
    assert all("ml_analysis" in point for point in report["enriched_data"])


def test_rural_identification():
    """Test that rural areas are correctly identified."""
    # Urban area (near São Paulo)
    urban_data = [create_sample_point(-23.5505, -46.6333, 80, 100, 20, 30, "Starlink")]
    enriched = predict_improvement_potential(urban_data)
    assert enriched[0]["ml_analysis"]["is_rural"] is False

    # Rural area (far from major cities)
    rural_data = [create_sample_point(-10.0, -55.0, 40, 50, 8, 80, "HughesNet")]
    enriched = predict_improvement_potential(rural_data)
    assert enriched[0]["ml_analysis"]["is_rural"] is True


def test_priority_scoring():
    """Test that priority scoring works correctly."""
    data = [
        # Poor quality, rural - should have high priority
        create_sample_point(-10.0, -55.0, 30, 40, 6, 100, "HughesNet"),
        # Good quality, urban - should have low priority
        create_sample_point(-23.5505, -46.6333, 90, 150, 25, 25, "Starlink"),
    ]

    enriched = predict_improvement_potential(data)

    # Rural poor should have higher priority than urban good
    rural_poor_priority = enriched[0]["ml_analysis"]["priority_score"]
    urban_good_priority = enriched[1]["ml_analysis"]["priority_score"]

    assert rural_poor_priority > urban_good_priority
