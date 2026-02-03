"""Tests for Starlink coverage utilities."""

from src.utils.starlink_coverage_utils import (
    get_coverage_color,
    get_coverage_rating,
    get_starlink_coverage_zones,
    get_starlink_signal_points,
)


def test_get_starlink_coverage_zones():
    """Test getting Starlink coverage zones for Brazil."""
    zones = get_starlink_coverage_zones()

    assert isinstance(zones, list)
    assert len(zones) > 0

    # Check first zone structure
    zone = zones[0]
    assert "name" in zone
    assert "coordinates" in zone
    assert "signal_strength" in zone
    assert "color" in zone
    assert "opacity" in zone
    assert "description" in zone

    # Verify coordinates are valid
    assert isinstance(zone["coordinates"], list)
    assert len(zone["coordinates"]) >= 3  # At least 3 points for polygon

    # Verify signal strength is valid
    assert zone["signal_strength"] in ["excellent", "good", "fair", "poor"]


def test_get_starlink_signal_points():
    """Test getting Starlink signal strength points."""
    points = get_starlink_signal_points()

    assert isinstance(points, list)
    assert len(points) > 0

    # Check first point structure
    point = points[0]
    assert "latitude" in point
    assert "longitude" in point
    assert "signal_strength" in point
    assert "coverage_type" in point

    # Verify signal strength is in valid range
    assert 0 <= point["signal_strength"] <= 100

    # Verify coverage type is valid
    assert point["coverage_type"] in ["primary", "secondary", "edge"]


def test_get_coverage_color():
    """Test coverage color mapping."""
    # Excellent signal - green
    assert get_coverage_color(95) == "#00ff00"
    assert get_coverage_color(85) == "#00ff00"

    # Good signal - yellow
    assert get_coverage_color(80) == "#ffff00"
    assert get_coverage_color(70) == "#ffff00"

    # Fair signal - orange
    assert get_coverage_color(65) == "#ffa500"
    assert get_coverage_color(50) == "#ffa500"

    # Poor signal - red
    assert get_coverage_color(45) == "#ff0000"
    assert get_coverage_color(30) == "#ff0000"

    # Edge cases
    assert get_coverage_color(100) == "#00ff00"
    assert get_coverage_color(0) == "#ff0000"


def test_get_coverage_rating():
    """Test coverage rating mapping."""
    # Excellent
    assert get_coverage_rating(100) == "Excellent"
    assert get_coverage_rating(85) == "Excellent"

    # Good
    assert get_coverage_rating(84) == "Good"
    assert get_coverage_rating(70) == "Good"

    # Fair
    assert get_coverage_rating(69) == "Fair"
    assert get_coverage_rating(50) == "Fair"

    # Poor
    assert get_coverage_rating(49) == "Poor"
    assert get_coverage_rating(0) == "Poor"


def test_coverage_zones_cover_brazil():
    """Test that coverage zones cover major regions of Brazil."""
    zones = get_starlink_coverage_zones()
    zone_names = [zone["name"].lower() for zone in zones]

    # Check that major regions are covered
    assert any("central" in name for name in zone_names)
    assert any("southeast" in name for name in zone_names)
    assert any("south" in name for name in zone_names)
    assert any("northeast" in name for name in zone_names)
    assert any("north" in name for name in zone_names)


def test_signal_points_have_valid_coordinates():
    """Test that all signal points have valid Brazilian coordinates."""
    points = get_starlink_signal_points()

    for point in points:
        lat = point["latitude"]
        lon = point["longitude"]

        # Brazil latitude range: approximately +5 to -34
        assert -34 <= lat <= 5

        # Brazil longitude range: approximately -73 to -34
        assert -74 <= lon <= -34


def test_coverage_zones_have_closed_polygons():
    """Test that coverage zones have properly closed polygons."""
    zones = get_starlink_coverage_zones()

    for zone in zones:
        coords = zone["coordinates"]
        # First and last coordinate should be the same for closed polygon
        assert coords[0] == coords[-1], f"Zone '{zone['name']}' polygon is not closed"


def test_signal_strength_distribution():
    """Test that signal points have realistic strength distribution."""
    points = get_starlink_signal_points()
    strengths = [p["signal_strength"] for p in points]

    # Should have variation in signal strength
    assert min(strengths) < 80  # Some weaker signals
    assert max(strengths) >= 85  # Some strong signals
    assert len(set(strengths)) > 1  # Not all the same
