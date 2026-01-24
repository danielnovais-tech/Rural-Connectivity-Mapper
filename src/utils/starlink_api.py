"""Starlink API utilities for fetching satellite connectivity data.

This module provides functions to interact with Starlink's API endpoints
to retrieve coverage, performance, and availability data. It includes
automatic fallback to simulated data when the API is unavailable.
"""

import logging
import random

import requests
import urllib3

# Disable SSL warnings when verify=False is used (for testing only)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Starlink API endpoints (placeholder URLs - not real/functional endpoints)
# In production, replace with actual Starlink API URLs
STARLINK_COVERAGE_API = "https://api.starlink.example/v1/coverage"
STARLINK_PERFORMANCE_API = "https://api.starlink.example/v1/performance"
STARLINK_AVAILABILITY_API = "https://api.starlink.example/v1/availability"

# Request timeout in seconds
REQUEST_TIMEOUT = 30

# Geographic boundaries for Brazil coverage (for simulated data)
BRAZIL_LAT_MIN = -33.0
BRAZIL_LAT_MAX = 5.0
BRAZIL_LON_MIN = -74.0
BRAZIL_LON_MAX = -34.0


def get_coverage_data(latitude: float, longitude: float) -> dict | None:
    """Fetch Starlink coverage data for a specific location.

    Attempts to retrieve coverage information from Starlink's API. Falls back
    to simulated data if the API is unavailable or returns an error.

    Args:
        latitude: Latitude coordinate of the location
        longitude: Longitude coordinate of the location

    Returns:
        Optional[Dict]: Coverage data including availability status, expected speeds,
                       and service tier. Returns None only on critical errors.

    Example:
        >>> data = get_coverage_data(-15.7801, -47.9292)
        >>> print(data['available'])
        True
    """
    try:
        logger.info(f"Fetching Starlink coverage data for ({latitude}, {longitude})")

        # Attempt to call Starlink API
        params = {
            'latitude': latitude,
            'longitude': longitude
        }

        response = requests.get(
            STARLINK_COVERAGE_API,
            params=params,
            timeout=REQUEST_TIMEOUT,
            verify=False
        )

        response.raise_for_status()
        data = response.json()

        logger.info("Successfully retrieved coverage data from Starlink API")
        return data

    except requests.exceptions.RequestException as e:
        logger.warning(f"Starlink API unavailable: {e}. Falling back to simulated data.")
        return _get_simulated_coverage(latitude, longitude)
    except Exception as e:
        logger.error(f"Error fetching coverage data: {e}")
        return _get_simulated_coverage(latitude, longitude)


def get_performance_metrics(latitude: float, longitude: float) -> dict | None:
    """Fetch Starlink performance metrics for a specific location.

    Retrieves current performance data including download/upload speeds,
    latency, and network statistics. Falls back to simulated data if unavailable.

    Args:
        latitude: Latitude coordinate of the location
        longitude: Longitude coordinate of the location

    Returns:
        Optional[Dict]: Performance metrics including speeds, latency, uptime.
                       Returns None only on critical errors.
    """
    try:
        logger.info(f"Fetching Starlink performance metrics for ({latitude}, {longitude})")

        params = {
            'latitude': latitude,
            'longitude': longitude
        }

        response = requests.get(
            STARLINK_PERFORMANCE_API,
            params=params,
            timeout=REQUEST_TIMEOUT,
            verify=False
        )

        response.raise_for_status()
        data = response.json()

        logger.info("Successfully retrieved performance metrics from Starlink API")
        return data

    except requests.exceptions.RequestException as e:
        logger.warning(f"Starlink API unavailable: {e}. Falling back to simulated data.")
        return _get_simulated_performance(latitude, longitude)
    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}")
        return _get_simulated_performance(latitude, longitude)


def get_availability_status(latitude: float, longitude: float) -> dict | None:
    """Fetch Starlink availability status for a specific location.

    Checks if Starlink service is currently available at the given coordinates,
    including waitlist status and estimated availability date.

    Args:
        latitude: Latitude coordinate of the location
        longitude: Longitude coordinate of the location

    Returns:
        Optional[Dict]: Availability status including service status, waitlist info.
                       Returns None only on critical errors.
    """
    try:
        logger.info(f"Fetching Starlink availability for ({latitude}, {longitude})")

        params = {
            'latitude': latitude,
            'longitude': longitude
        }

        response = requests.get(
            STARLINK_AVAILABILITY_API,
            params=params,
            timeout=REQUEST_TIMEOUT,
            verify=False
        )

        response.raise_for_status()
        data = response.json()

        logger.info("Successfully retrieved availability status from Starlink API")
        return data

    except requests.exceptions.RequestException as e:
        logger.warning(f"Starlink API unavailable: {e}. Falling back to simulated data.")
        return _get_simulated_availability(latitude, longitude)
    except Exception as e:
        logger.error(f"Error fetching availability status: {e}")
        return _get_simulated_availability(latitude, longitude)


def compare_with_competitors(latitude: float, longitude: float) -> dict:
    """Compare Starlink with competitors (Viasat, HughesNet) at a location.

    Provides a comparison of Starlink's expected performance against other
    satellite internet providers for the given location.

    Args:
        latitude: Latitude coordinate of the location
        longitude: Longitude coordinate of the location

    Returns:
        Dict: Comparison data for Starlink, Viasat, and HughesNet including
              speeds, latency, pricing estimates, and quality scores.
    """
    try:
        logger.info(f"Comparing providers for location ({latitude}, {longitude})")

        # Get Starlink data
        starlink_perf = get_performance_metrics(latitude, longitude)
        starlink_coverage = get_coverage_data(latitude, longitude)

        # Simulate competitor data (in production, these might be real APIs)
        comparison = {
            'location': {
                'latitude': latitude,
                'longitude': longitude
            },
            'providers': {
                'starlink': {
                    'available': starlink_coverage.get('available', False) if starlink_coverage else False,
                    'download_mbps': starlink_perf.get('download_mbps', 0) if starlink_perf else 0,
                    'upload_mbps': starlink_perf.get('upload_mbps', 0) if starlink_perf else 0,
                    'latency_ms': starlink_perf.get('latency_ms', 0) if starlink_perf else 0,
                    'monthly_cost_usd': starlink_coverage.get('monthly_cost_usd', 120) if starlink_coverage else 120,
                    'quality_score': _calculate_provider_score(starlink_perf or {})
                },
                'viasat': _get_viasat_data(),
                'hughesnet': _get_hughesnet_data()
            }
        }

        # Determine the best provider
        best_provider = max(
            comparison['providers'].items(),
            key=lambda x: x[1].get('quality_score', 0)
        )

        comparison['recommendation'] = {
            'best_provider': best_provider[0],
            'score': best_provider[1].get('quality_score', 0),
            'reason': _get_recommendation_reason(best_provider[0], best_provider[1])
        }

        logger.info(f"Provider comparison complete. Best: {best_provider[0]}")
        return comparison

    except Exception as e:
        logger.error(f"Error comparing providers: {e}")
        # Return minimal comparison on error
        return {
            'location': {'latitude': latitude, 'longitude': longitude},
            'providers': {},
            'recommendation': {'best_provider': 'starlink', 'score': 0, 'reason': 'Error occurred'}
        }


# ============================================================================
# PRIVATE HELPER FUNCTIONS - Simulated Data Fallbacks
# ============================================================================

def _get_simulated_coverage(latitude: float, longitude: float) -> dict:
    """Generate simulated Starlink coverage data.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Dict: Simulated coverage information
    """
    # Brazil is within Starlink's coverage area as of 2026
    in_brazil = (BRAZIL_LAT_MIN <= latitude <= BRAZIL_LAT_MAX and
                 BRAZIL_LON_MIN <= longitude <= BRAZIL_LON_MAX)

    return {
        'available': in_brazil,
        'service_tier': 'residential' if in_brazil else 'unavailable',
        'expected_download_mbps': 150.0 if in_brazil else 0,
        'expected_upload_mbps': 20.0 if in_brazil else 0,
        'expected_latency_ms': 30.0 if in_brazil else 0,
        'monthly_cost_usd': 120 if in_brazil else None,
        'installation_cost_usd': 599 if in_brazil else None,
        'waitlist_months': 0 if in_brazil else 6,
        'data_source': 'simulated'
    }


def _get_simulated_performance(latitude: float, longitude: float) -> dict:
    """Generate simulated Starlink performance metrics.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Dict: Simulated performance data
    """
    # Vary performance slightly based on location
    random.seed(int((latitude + 90) * 1000 + (longitude + 180) * 1000))

    download_base = 150.0
    download_variation = random.uniform(-20, 30)

    return {
        'download_mbps': round(download_base + download_variation, 1),
        'upload_mbps': round(20.0 + random.uniform(-2, 5), 1),
        'latency_ms': round(30.0 + random.uniform(-5, 10), 1),
        'jitter_ms': round(random.uniform(2, 8), 1),
        'packet_loss_percent': round(random.uniform(0, 0.5), 2),
        'uptime_percent': round(random.uniform(98.5, 99.9), 2),
        'data_source': 'simulated'
    }


def _get_simulated_availability(latitude: float, longitude: float) -> dict:
    """Generate simulated Starlink availability status.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Dict: Simulated availability information
    """
    in_brazil = (BRAZIL_LAT_MIN <= latitude <= BRAZIL_LAT_MAX and
                 BRAZIL_LON_MIN <= longitude <= BRAZIL_LON_MAX)

    return {
        'service_available': in_brazil,
        'status': 'active' if in_brazil else 'waitlist',
        'estimated_wait_months': 0 if in_brazil else 6,
        'can_order_now': in_brazil,
        'capacity_status': 'available' if in_brazil else 'at_capacity',
        'data_source': 'simulated'
    }


def _get_viasat_data() -> dict:
    """Generate simulated Viasat competitor data.

    Returns:
        Dict: Simulated Viasat performance and pricing
    """
    return {
        'available': True,
        'download_mbps': 75.0,
        'upload_mbps': 10.0,
        'latency_ms': 650.0,  # Geostationary satellite has high latency
        'monthly_cost_usd': 70,
        'quality_score': 50.0,
        'data_cap_gb': 150,
        'data_source': 'simulated'
    }


def _get_hughesnet_data() -> dict:
    """Generate simulated HughesNet competitor data.

    Returns:
        Dict: Simulated HughesNet performance and pricing
    """
    return {
        'available': True,
        'download_mbps': 25.0,
        'upload_mbps': 3.0,
        'latency_ms': 700.0,  # Geostationary satellite has high latency
        'monthly_cost_usd': 65,
        'quality_score': 35.0,
        'data_cap_gb': 100,
        'data_source': 'simulated'
    }


def _calculate_provider_score(performance_data: dict) -> float:
    """Calculate quality score for a provider based on performance metrics.

    Uses the same algorithm as QualityScore model:
    Speed (40%) + Latency (30%) + Stability (30%)

    Note: This is a simplified version adapted for raw performance dictionaries
    rather than SpeedTest objects. The core algorithm matches QualityScore.calculate()
    to ensure consistent scoring across the application.

    Args:
        performance_data: Dictionary with download, upload, latency metrics

    Returns:
        float: Quality score from 0-100
    """
    try:
        download = performance_data.get('download_mbps', 0)
        upload = performance_data.get('upload_mbps', 0)
        latency = performance_data.get('latency_ms', 0)
        packet_loss = performance_data.get('packet_loss_percent', 0)
        jitter = performance_data.get('jitter_ms', 0)

        # Speed score (40%) - matches QualityScore.TARGET_DOWNLOAD/UPLOAD
        speed_score = ((download / 200.0) + (upload / 20.0)) / 2 * 100
        speed_score = min(100, speed_score)

        # Latency score (30%) - matches QualityScore latency calculation
        latency_score = max(0, 100 - (latency - 20) * 1.25)
        latency_score = min(100, latency_score)

        # Stability score (30%) - adapted for jitter and packet_loss metrics
        stability_score = 100 - (jitter * 2 + packet_loss * 10)
        stability_score = max(0, min(100, stability_score))

        # Overall score - matches QualityScore weight distribution
        overall_score = (speed_score * 0.4) + (latency_score * 0.3) + (stability_score * 0.3)

        return round(overall_score, 1)

    except Exception as e:
        logger.error(f"Error calculating provider score: {e}")
        return 0.0


def _get_recommendation_reason(provider: str, data: dict) -> str:
    """Generate recommendation reason for the best provider.

    Args:
        provider: Name of the recommended provider
        data: Provider data dictionary

    Returns:
        str: Human-readable recommendation reason
    """
    score = data.get('quality_score', 0)

    if provider == 'starlink':
        if score >= 90:
            return "Best speeds and lowest latency with Starlink's LEO satellite network"
        else:
            return "Good performance with Starlink despite some limitations"
    elif provider == 'viasat':
        return "Viasat offers acceptable speeds but higher latency"
    elif provider == 'hughesnet':
        return "HughesNet is available but has lower performance metrics"
    else:
        return f"{provider} recommended based on quality score"
