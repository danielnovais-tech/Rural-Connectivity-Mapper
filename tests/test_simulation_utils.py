"""Tests for simulation utilities."""

import pytest

from src.utils.simulation_utils import simulate_router_impact


@pytest.fixture
def sample_data():
    """Sample connectivity data for testing."""
    return [
        {
            "id": "test-1",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "provider": "Starlink",
            "quality_score": {
                "overall_score": 70.0,
                "speed_score": 75.0,
                "latency_score": 65.0,
                "stability_score": 70.0,
                "rating": "Good",
            },
        },
        {
            "id": "test-2",
            "latitude": -22.9068,
            "longitude": -43.1729,
            "provider": "Claro",
            "quality_score": {
                "overall_score": 50.0,
                "speed_score": 55.0,
                "latency_score": 45.0,
                "stability_score": 50.0,
                "rating": "Fair",
            },
        },
    ]


def test_simulate_router_impact(sample_data):
    """Test router impact simulation improves scores."""
    improved_data = simulate_router_impact(sample_data)

    # Verify data length unchanged
    assert len(improved_data) == len(sample_data)

    # Verify scores improved
    for i, point in enumerate(improved_data):
        original_score = sample_data[i]["quality_score"]["overall_score"]
        new_score = point["quality_score"]["overall_score"]

        # Score should be improved but not exceed 100
        assert new_score > original_score
        assert new_score <= 100


def test_simulate_improvement_range(sample_data):
    """Test that improvement is within expected 15-25% range."""
    # Run simulation multiple times to check range
    for _ in range(10):
        improved_data = simulate_router_impact(sample_data)

        for i, point in enumerate(improved_data):
            original_score = sample_data[i]["quality_score"]["overall_score"]
            new_score = point["quality_score"]["overall_score"]

            # Calculate improvement factor
            improvement_factor = new_score / original_score if original_score > 0 else 1

            # Improvement should be between 15% and 25% (factor 1.15 to 1.25)
            # Allow small margin for rounding
            assert improvement_factor >= 1.14
            assert improvement_factor <= 1.26


def test_simulate_rating_update(sample_data):
    """Test that rating is updated based on new score."""
    improved_data = simulate_router_impact(sample_data)

    for point in improved_data:
        score = point["quality_score"]["overall_score"]
        rating = point["quality_score"]["rating"]

        # Verify rating matches score
        if score >= 80:
            assert rating == "Excellent"
        elif score >= 60:
            assert rating == "Good"
        elif score >= 40:
            assert rating == "Fair"
        else:
            assert rating == "Poor"


def test_simulate_preserves_other_fields(sample_data):
    """Test that simulation preserves non-quality fields."""
    improved_data = simulate_router_impact(sample_data)

    for i, point in enumerate(improved_data):
        # Original fields should be preserved
        assert point["id"] == sample_data[i]["id"]
        assert point["latitude"] == sample_data[i]["latitude"]
        assert point["longitude"] == sample_data[i]["longitude"]
        assert point["provider"] == sample_data[i]["provider"]
