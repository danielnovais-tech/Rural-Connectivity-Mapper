"""Tests for geocoding utilities."""

import pytest
from unittest.mock import Mock, patch

from src.utils.geocoding_utils import geocode_coordinates, geocode_address
from geopy.exc import GeocoderTimedOut, GeocoderQuotaExceeded, GeocoderUnavailable


def test_geocoding_coordinates():
    """Test reverse geocoding from coordinates to address."""
    with patch('src.utils.geocoding_utils.geolocator.reverse') as mock_reverse:
        # Setup mock
        mock_location = Mock()
        mock_location.address = "São Paulo, Brazil"
        mock_reverse.return_value = mock_location
        
        # Test geocoding
        address = geocode_coordinates(-23.5505, -46.6333)
        
        assert address == "São Paulo, Brazil"
        mock_reverse.assert_called_once()


def test_geocoding_address():
    """Test forward geocoding from address to coordinates."""
    with patch('src.utils.geocoding_utils.geolocator.geocode') as mock_geocode:
        # Setup mock
        mock_location = Mock()
        mock_location.latitude = -23.5505
        mock_location.longitude = -46.6333
        mock_geocode.return_value = mock_location
        
        # Test geocoding
        coords = geocode_address("São Paulo, Brazil")
        
        assert coords is not None
        assert coords[0] == -23.5505
        assert coords[1] == -46.6333
        mock_geocode.assert_called_once()


def test_geocoding_coordinates_invalid_coords():
    """Test geocoding with invalid coordinates."""
    # Invalid latitude
    address = geocode_coordinates(95.0, -46.6333)
    assert address is None
    
    # Invalid longitude
    address = geocode_coordinates(-23.5505, 200.0)
    assert address is None


def test_geocoding_address_invalid_input():
    """Test geocoding with invalid address input."""
    # Empty address
    coords = geocode_address("")
    assert coords is None
    
    # None address
    coords = geocode_address(None)  # type: ignore
    assert coords is None


def test_geocoding_coordinates_timeout_retry():
    """Test retry logic on timeout."""
    with patch('src.utils.geocoding_utils.geolocator.reverse') as mock_reverse:
        # First call times out, second succeeds
        mock_location = Mock()
        mock_location.address = "São Paulo, Brazil"
        mock_reverse.side_effect = [
            GeocoderTimedOut("Timeout"),
            mock_location
        ]
        
        with patch('src.utils.geocoding_utils.time.sleep'):  # Skip actual sleep
            address = geocode_coordinates(-23.5505, -46.6333, max_retries=2)
        
        assert address == "São Paulo, Brazil"
        assert mock_reverse.call_count == 2


def test_geocoding_coordinates_timeout_exhausted():
    """Test retry logic when all retries timeout."""
    with patch('src.utils.geocoding_utils.geolocator.reverse') as mock_reverse:
        mock_reverse.side_effect = GeocoderTimedOut("Timeout")
        
        with patch('src.utils.geocoding_utils.time.sleep'):  # Skip actual sleep
            address = geocode_coordinates(-23.5505, -46.6333, max_retries=3)
        
        assert address is None
        assert mock_reverse.call_count == 3


def test_geocoding_quota_exceeded():
    """Test handling of quota exceeded error."""
    with patch('src.utils.geocoding_utils.geolocator.reverse') as mock_reverse:
        mock_reverse.side_effect = GeocoderQuotaExceeded("Quota exceeded")
        
        address = geocode_coordinates(-23.5505, -46.6333)
        
        assert address is None
        assert mock_reverse.call_count == 1  # Should not retry on quota exceeded


def test_geocoding_service_unavailable_retry():
    """Test retry logic when service is unavailable."""
    with patch('src.utils.geocoding_utils.geolocator.geocode') as mock_geocode:
        # First call unavailable, second succeeds
        mock_location = Mock()
        mock_location.latitude = -23.5505
        mock_location.longitude = -46.6333
        mock_geocode.side_effect = [
            GeocoderUnavailable("Service unavailable"),
            mock_location
        ]
        
        with patch('src.utils.geocoding_utils.time.sleep'):  # Skip actual sleep
            coords = geocode_address("São Paulo, Brazil", max_retries=2)
        
        assert coords is not None
        assert coords[0] == -23.5505
        assert mock_geocode.call_count == 2


def test_geocoding_no_results():
    """Test handling when geocoding returns no results."""
    with patch('src.utils.geocoding_utils.geolocator.reverse') as mock_reverse:
        mock_reverse.return_value = None
        
        address = geocode_coordinates(-23.5505, -46.6333)
        
        assert address is None
