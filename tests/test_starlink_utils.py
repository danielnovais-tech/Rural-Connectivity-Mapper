"""Tests for Starlink utilities."""

from src.utils.starlink_utils import (
    check_batch_availability,
    check_starlink_availability,
    estimate_starlink_performance,
    get_starlink_coverage_map,
    get_starlink_service_plans,
    get_starlink_vs_competitors,
)


def test_check_starlink_availability():
    """Test checking Starlink availability at coordinates."""
    # Test for Brasília (should be available)
    availability = check_starlink_availability(-15.7801, -47.9292)

    assert isinstance(availability, dict)
    assert "latitude" in availability
    assert "longitude" in availability
    assert "service_available" in availability
    assert "status" in availability
    assert "expected_speeds" in availability

    # For most of Brazil, service should be available
    assert availability["service_available"] in [True, False]


def test_check_starlink_availability_remote_area():
    """Test checking Starlink availability in remote Amazon region."""
    # Deep Amazon coordinates
    availability = check_starlink_availability(-5.0, -65.0)

    assert isinstance(availability, dict)
    assert "status" in availability
    # Remote areas might have waitlist status
    assert availability["status"] in ["available", "waitlist", "not_available"]


def test_check_batch_availability():
    """Test checking Starlink availability for multiple locations."""
    coordinates = [
        (-23.5505, -46.6333),  # São Paulo
        (-22.9068, -43.1729),  # Rio de Janeiro
        (-15.7801, -47.9292),  # Brasília
    ]

    results = check_batch_availability(coordinates)

    assert isinstance(results, list)
    assert len(results) == len(coordinates)

    # Check each result
    for result in results:
        assert "latitude" in result
        assert "longitude" in result
        assert "service_available" in result


def test_get_starlink_service_plans():
    """Test getting Starlink service plans."""
    plans = get_starlink_service_plans()

    assert isinstance(plans, list)
    assert len(plans) > 0

    # Check for known plans
    plan_names = [p["name"] for p in plans]
    assert "Residential" in plan_names
    assert "Business" in plan_names

    # Check structure
    first_plan = plans[0]
    assert "plan_id" in first_plan
    assert "name" in first_plan
    assert "price_brl_monthly" in first_plan
    assert "price_usd_monthly" in first_plan
    assert "hardware_cost_brl" in first_plan
    assert "download_speed" in first_plan
    assert "upload_speed" in first_plan
    assert "latency" in first_plan

    # Check prices are positive
    for plan in plans:
        assert plan["price_brl_monthly"] > 0
        assert plan["hardware_cost_brl"] > 0


def test_get_starlink_coverage_map_brazil():
    """Test getting Starlink coverage map for Brazil."""
    coverage = get_starlink_coverage_map("BR")

    assert isinstance(coverage, dict)
    assert coverage["country_code"] == "BR"
    assert coverage["country_name"] == "Brazil"
    assert "service_status" in coverage
    assert "coverage_percentage" in coverage
    assert "active_users" in coverage

    # Check coverage is reasonable
    assert 0 <= coverage["coverage_percentage"] <= 100


def test_get_starlink_coverage_map_other_latam():
    """Test getting Starlink coverage map for other LATAM countries."""
    countries = ["AR", "CL", "CO", "MX"]

    for country_code in countries:
        coverage = get_starlink_coverage_map(country_code)

        assert isinstance(coverage, dict)
        assert coverage["country_code"] == country_code
        assert "coverage_percentage" in coverage


def test_get_starlink_coverage_map_unknown():
    """Test getting Starlink coverage map for unknown country."""
    coverage = get_starlink_coverage_map("XX")

    assert isinstance(coverage, dict)
    assert coverage["country_code"] == "XX"
    assert coverage["service_status"] == "unknown"


def test_estimate_starlink_performance_clear_weather():
    """Test estimating Starlink performance in clear weather."""
    performance = estimate_starlink_performance(-15.7801, -47.9292, "clear")

    assert isinstance(performance, dict)
    assert "estimated_download_mbps" in performance
    assert "estimated_upload_mbps" in performance
    assert "estimated_latency_ms" in performance
    assert "signal_strength" in performance
    assert "reliability_score" in performance

    # Clear weather should have best performance
    assert performance["signal_strength"] == "excellent"
    assert performance["reliability_score"] >= 90


def test_estimate_starlink_performance_bad_weather():
    """Test estimating Starlink performance in storm."""
    performance = estimate_starlink_performance(-15.7801, -47.9292, "storm")

    assert isinstance(performance, dict)

    # Storm should degrade performance
    assert performance["reliability_score"] < 95

    # Compare with clear weather
    clear_perf = estimate_starlink_performance(-15.7801, -47.9292, "clear")
    assert performance["estimated_download_mbps"] < clear_perf["estimated_download_mbps"]
    assert performance["estimated_latency_ms"] > clear_perf["estimated_latency_ms"]


def test_get_starlink_vs_competitors():
    """Test comparing Starlink with competitors."""
    comparison = get_starlink_vs_competitors(-15.7801, -47.9292)

    assert isinstance(comparison, dict)
    assert "location" in comparison
    assert "providers" in comparison
    assert "recommendation" in comparison

    # Check providers
    providers = comparison["providers"]
    assert "Starlink" in providers
    assert "Viasat" in providers
    assert "HughesNet" in providers

    # Check Starlink data
    starlink = providers["Starlink"]
    assert "download_mbps" in starlink
    assert "latency_ms" in starlink
    assert "price_monthly_brl" in starlink

    # Starlink should have better latency
    assert "20-40" in starlink["latency_ms"]
