"""Tests for Starlink API utilities."""

from unittest.mock import Mock, patch

import pytest
import requests

from src.utils.starlink_api import (
    _calculate_provider_score,
    _get_recommendation_reason,
    _get_simulated_availability,
    _get_simulated_coverage,
    _get_simulated_performance,
    compare_with_competitors,
    get_availability_status,
    get_coverage_data,
    get_performance_metrics,
)


class TestCoverageData:
    """Test suite for get_coverage_data function."""

    def test_get_coverage_data_api_success(self):
        """Test successful API call for coverage data."""
        with patch("requests.get") as mock_get:
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "available": True,
                "service_tier": "residential",
                "expected_download_mbps": 150.0,
                "monthly_cost_usd": 120,
            }
            mock_get.return_value = mock_response

            result = get_coverage_data(-15.7801, -47.9292)

            assert result is not None
            assert result["available"] is True
            assert result["service_tier"] == "residential"
            assert result["expected_download_mbps"] == pytest.approx(150.0)

            # Verify API was called with correct params
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[1]["params"]["latitude"] == -15.7801
            assert call_args[1]["params"]["longitude"] == -47.9292

    def test_get_coverage_data_api_failure_fallback(self):
        """Test fallback to simulated data when API fails."""
        with patch("requests.get") as mock_get:
            # Mock API failure
            mock_get.side_effect = requests.exceptions.RequestException("API unavailable")

            result = get_coverage_data(-15.7801, -47.9292)

            assert result is not None
            assert "data_source" in result
            assert result["data_source"] == "simulated"
            assert isinstance(result["available"], bool)

    def test_get_coverage_data_timeout_fallback(self):
        """Test fallback when API times out."""
        with patch("requests.get") as mock_get:
            # Mock timeout
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

            result = get_coverage_data(-15.7801, -47.9292)

            assert result is not None
            assert result["data_source"] == "simulated"


class TestPerformanceMetrics:
    """Test suite for get_performance_metrics function."""

    def test_get_performance_metrics_api_success(self):
        """Test successful API call for performance metrics."""
        with patch("requests.get") as mock_get:
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "download_mbps": 165.0,
                "upload_mbps": 22.0,
                "latency_ms": 28.0,
                "uptime_percent": 99.5,
            }
            mock_get.return_value = mock_response

            result = get_performance_metrics(-15.7801, -47.9292)

            assert result is not None
            assert result["download_mbps"] == pytest.approx(165.0)
            assert result["upload_mbps"] == pytest.approx(22.0)
            assert result["latency_ms"] == pytest.approx(28.0)

    def test_get_performance_metrics_api_failure_fallback(self):
        """Test fallback to simulated data when API fails."""
        with patch("requests.get") as mock_get:
            # Mock API failure
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            result = get_performance_metrics(-15.7801, -47.9292)

            assert result is not None
            assert result["data_source"] == "simulated"
            assert "download_mbps" in result
            assert "upload_mbps" in result
            assert "latency_ms" in result


class TestAvailabilityStatus:
    """Test suite for get_availability_status function."""

    def test_get_availability_status_api_success(self):
        """Test successful API call for availability status."""
        with patch("requests.get") as mock_get:
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"service_available": True, "status": "active", "can_order_now": True}
            mock_get.return_value = mock_response

            result = get_availability_status(-15.7801, -47.9292)

            assert result is not None
            assert result["service_available"] is True
            assert result["status"] == "active"

    def test_get_availability_status_api_failure_fallback(self):
        """Test fallback to simulated data when API fails."""
        with patch("requests.get") as mock_get:
            # Mock API failure
            mock_get.side_effect = requests.exceptions.HTTPError("500 Server Error")

            result = get_availability_status(-15.7801, -47.9292)

            assert result is not None
            assert result["data_source"] == "simulated"
            assert "service_available" in result


class TestCompareWithCompetitors:
    """Test suite for compare_with_competitors function."""

    def test_compare_with_competitors_success(self):
        """Test provider comparison with all data."""
        with (
            patch("src.utils.starlink_api.get_performance_metrics") as mock_perf,
            patch("src.utils.starlink_api.get_coverage_data") as mock_cov,
        ):
            # Mock Starlink data
            mock_perf.return_value = {
                "download_mbps": 165.0,
                "upload_mbps": 22.0,
                "latency_ms": 28.0,
                "jitter_ms": 5.0,
                "packet_loss_percent": 0.1,
                "data_source": "simulated",
            }
            mock_cov.return_value = {"available": True, "monthly_cost_usd": 120, "data_source": "simulated"}

            result = compare_with_competitors(-15.7801, -47.9292)

            assert result is not None
            assert "location" in result
            assert "providers" in result
            assert "recommendation" in result

            assert "starlink" in result["providers"]
            assert "viasat" in result["providers"]
            assert "hughesnet" in result["providers"]

            assert result["location"]["latitude"] == -15.7801
            assert result["location"]["longitude"] == -47.9292

            # Starlink should generally have best quality score
            assert result["providers"]["starlink"]["quality_score"] > 0

    def test_compare_with_competitors_recommendation(self):
        """Test that recommendation is provided."""
        result = compare_with_competitors(-15.7801, -47.9292)

        assert "recommendation" in result
        assert "best_provider" in result["recommendation"]
        assert "score" in result["recommendation"]
        assert "reason" in result["recommendation"]

        # Best provider should be one of the three
        assert result["recommendation"]["best_provider"] in ["starlink", "viasat", "hughesnet"]


class TestSimulatedData:
    """Test suite for simulated data functions."""

    def test_simulated_coverage_brazil_location(self):
        """Test simulated coverage for location in Brazil."""
        result = _get_simulated_coverage(-15.7801, -47.9292)  # Brasília

        assert result is not None
        assert result["available"] is True
        assert result["data_source"] == "simulated"
        assert result["expected_download_mbps"] > 0
        assert result["monthly_cost_usd"] is not None

    def test_simulated_coverage_outside_brazil(self):
        """Test simulated coverage for location outside Brazil."""
        result = _get_simulated_coverage(40.7128, -74.0060)  # New York

        assert result is not None
        assert result["available"] is False
        assert result["data_source"] == "simulated"
        assert result["expected_download_mbps"] == 0

    def test_simulated_performance_returns_valid_data(self):
        """Test simulated performance returns realistic metrics."""
        result = _get_simulated_performance(-15.7801, -47.9292)

        assert result is not None
        assert result["data_source"] == "simulated"
        assert result["download_mbps"] > 0
        assert result["upload_mbps"] > 0
        assert result["latency_ms"] > 0
        assert 0 <= result["uptime_percent"] <= 100

    def test_simulated_availability_brazil_location(self):
        """Test simulated availability for Brazil location."""
        result = _get_simulated_availability(-15.7801, -47.9292)

        assert result is not None
        assert result["service_available"] is True
        assert result["status"] == "active"
        assert result["can_order_now"] is True


class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_calculate_provider_score_excellent(self):
        """Test score calculation for excellent performance."""
        performance_data = {
            "download_mbps": 200.0,
            "upload_mbps": 20.0,
            "latency_ms": 20.0,
            "jitter_ms": 2.0,
            "packet_loss_percent": 0.1,
        }

        score = _calculate_provider_score(performance_data)

        assert score > 90  # Should be excellent
        assert 0 <= score <= 100

    def test_calculate_provider_score_poor(self):
        """Test score calculation for poor performance."""
        performance_data = {
            "download_mbps": 25.0,
            "upload_mbps": 3.0,
            "latency_ms": 700.0,
            "jitter_ms": 50.0,
            "packet_loss_percent": 2.0,
        }

        score = _calculate_provider_score(performance_data)

        assert score < 60  # Should be poor/fair
        assert 0 <= score <= 100

    def test_calculate_provider_score_missing_data(self):
        """Test score calculation with missing data defaults to 0 values."""
        performance_data = {}

        score = _calculate_provider_score(performance_data)

        # With all missing data (defaults to 0), score should still be valid
        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_get_recommendation_reason_starlink(self):
        """Test recommendation reason for Starlink."""
        reason = _get_recommendation_reason("starlink", {"quality_score": 95})

        assert "starlink" in reason.lower() or "leo" in reason.lower()
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_get_recommendation_reason_viasat(self):
        """Test recommendation reason for Viasat."""
        reason = _get_recommendation_reason("viasat", {"quality_score": 50})

        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_get_recommendation_reason_hughesnet(self):
        """Test recommendation reason for HughesNet."""
        reason = _get_recommendation_reason("hughesnet", {"quality_score": 35})

        assert isinstance(reason, str)
        assert len(reason) > 0


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_coverage_data_with_extreme_coordinates(self):
        """Test coverage data with extreme latitude/longitude."""
        # Should not crash with extreme coordinates
        result = get_coverage_data(-90.0, -180.0)

        assert result is not None
        assert "data_source" in result

    def test_performance_metrics_with_zero_coordinates(self):
        """Test performance metrics with zero coordinates."""
        result = get_performance_metrics(0.0, 0.0)

        assert result is not None
        assert "download_mbps" in result

    def test_compare_providers_consistent_structure(self):
        """Test that provider comparison always returns consistent structure."""
        result = compare_with_competitors(-15.7801, -47.9292)

        # Verify structure is always present
        assert "location" in result
        assert "providers" in result
        assert "recommendation" in result

        # Each provider should have consistent fields
        for provider_name, provider_data in result["providers"].items():
            assert "available" in provider_data
            assert "download_mbps" in provider_data
            assert "upload_mbps" in provider_data
            assert "latency_ms" in provider_data
            assert "quality_score" in provider_data
