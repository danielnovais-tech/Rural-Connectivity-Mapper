"""Tests for validation utilities."""

import pytest

from src.utils.validation_utils import (
    validate_coordinates,
    validate_speed_test,
    validate_provider,
    validate_csv_row
)
from src.models import SpeedTest


def test_validate_coordinates_valid():
    """Test validation of valid coordinates."""
    # Valid coordinates
    assert validate_coordinates(0, 0) is True
    assert validate_coordinates(-23.5505, -46.6333) is True  # São Paulo
    assert validate_coordinates(90, 180) is True  # Max valid
    assert validate_coordinates(-90, -180) is True  # Min valid


def test_validate_coordinates_invalid():
    """Test validation of invalid coordinates."""
    # Invalid latitude
    assert validate_coordinates(91, 0) is False
    assert validate_coordinates(-91, 0) is False

    # Invalid longitude
    assert validate_coordinates(0, 181) is False
    assert validate_coordinates(0, -181) is False

    # Both invalid
    assert validate_coordinates(100, 200) is False


def test_validate_speed_test_valid():
    """Test validation of valid speed test data."""
    speed_test = SpeedTest(
        download=100.0,
        upload=15.0,
        latency=30.0,
        jitter=5.0,
        packet_loss=0.5
    )

    assert validate_speed_test(speed_test) is True

    # Test with dict
    speed_dict = {
        'download': 100.0,
        'upload': 15.0,
        'latency': 30.0
    }

    assert validate_speed_test(speed_dict) is True


def test_validate_speed_test_invalid():
    """Test validation of invalid speed test data."""
    # Negative values
    invalid_dict = {
        'download': -10.0,
        'upload': 15.0,
        'latency': 30.0
    }

    assert validate_speed_test(invalid_dict) is False

    # Missing required fields
    incomplete_dict = {
        'download': 100.0
    }

    assert validate_speed_test(incomplete_dict) is False


def test_validate_speed_test_bounds():
    """Test validation with bounds checking."""
    # Out of bounds download speed
    invalid_dict = {
        'download': 2000.0,  # Too high
        'upload': 15.0,
        'latency': 30.0
    }
    assert validate_speed_test(invalid_dict, check_bounds=True) is False

    # Out of bounds latency
    invalid_dict = {
        'download': 100.0,
        'upload': 15.0,
        'latency': 5000.0  # Too high
    }
    assert validate_speed_test(invalid_dict, check_bounds=True) is False

    # Valid within bounds
    valid_dict = {
        'download': 100.0,
        'upload': 15.0,
        'latency': 30.0
    }
    assert validate_speed_test(valid_dict, check_bounds=True) is True


def test_validate_provider_valid():
    """Test validation of valid provider names."""
    assert validate_provider('Starlink') is True
    assert validate_provider('Viasat') is True
    assert validate_provider('HughesNet') is True
    assert validate_provider('Claro') is True


def test_validate_provider_invalid():
    """Test validation of invalid provider names."""
    assert validate_provider('Unknown Provider') is False
    assert validate_provider('') is False
    assert validate_provider(None) is False


def test_validate_csv_row_valid():
    """Test validation of valid CSV row."""
    row = {
        'latitude': '-23.5505',
        'longitude': '-46.6333',
        'provider': 'Starlink',
        'download': '100.0',
        'upload': '15.0',
        'latency': '30.0',
        'jitter': '5.0',
        'packet_loss': '0.5'
    }

    is_valid, error_msg = validate_csv_row(row, 1)
    assert is_valid is True
    assert error_msg == ""


def test_validate_csv_row_missing_fields():
    """Test validation with missing required fields."""
    row = {
        'latitude': '-23.5505',
        'provider': 'Starlink',
        'download': '100.0'
    }

    is_valid, error_msg = validate_csv_row(row, 1)
    assert is_valid is False
    assert "Missing required fields" in error_msg


def test_validate_csv_row_invalid_numeric():
    """Test validation with invalid numeric values."""
    row = {
        'latitude': 'invalid',
        'longitude': '-46.6333',
        'provider': 'Starlink',
        'download': '100.0',
        'upload': '15.0',
        'latency': '30.0'
    }

    is_valid, error_msg = validate_csv_row(row, 1)
    assert is_valid is False
    assert "Invalid numeric value" in error_msg


def test_validate_csv_row_out_of_range_coordinates():
    """Test validation with out of range coordinates."""
    row = {
        'latitude': '95.0',  # Invalid
        'longitude': '-46.6333',
        'provider': 'Starlink',
        'download': '100.0',
        'upload': '15.0',
        'latency': '30.0'
    }

    is_valid, error_msg = validate_csv_row(row, 1)
    assert is_valid is False
    assert "Invalid latitude" in error_msg


def test_validate_csv_row_out_of_range_speed():
    """Test validation with out of range speed values."""
    row = {
        'latitude': '-23.5505',
        'longitude': '-46.6333',
        'provider': 'Starlink',
        'download': '5000.0',  # Too high
        'upload': '15.0',
        'latency': '30.0'
    }

    is_valid, error_msg = validate_csv_row(row, 1)
    assert is_valid is False
    assert "Invalid download" in error_msg
