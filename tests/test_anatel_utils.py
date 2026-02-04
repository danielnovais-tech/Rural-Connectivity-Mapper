"""Tests for ANATEL utilities."""

import pytest

pytest.importorskip("pandas", exc_type=ImportError)
from src.utils.anatel_utils import (
    convert_anatel_to_connectivity_points,
    fetch_anatel_broadband_data,
    fetch_anatel_mobile_data,
    get_anatel_provider_stats,
)


def test_fetch_anatel_broadband_data():
    """Test fetching ANATEL broadband data."""
    data = fetch_anatel_broadband_data()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check data structure
    first_record = data[0]
    assert 'state' in first_record
    assert 'municipality' in first_record
    assert 'provider' in first_record
    assert 'technology' in first_record
    assert 'avg_speed_mbps' in first_record
    assert 'coverage_percentage' in first_record


def test_fetch_anatel_broadband_data_with_state_filter():
    """Test fetching ANATEL broadband data with state filter."""
    data = fetch_anatel_broadband_data(state='SP')
    
    assert isinstance(data, list)
    # All records should be from SP
    for record in data:
        assert record['state'] == 'SP'


def test_fetch_anatel_mobile_data():
    """Test fetching ANATEL mobile data."""
    data = fetch_anatel_mobile_data()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check data structure
    first_record = data[0]
    assert 'state' in first_record
    assert 'municipality' in first_record
    assert 'provider' in first_record
    assert 'technology' in first_record
    assert 'coverage_4g_percentage' in first_record
    assert 'avg_speed_mbps' in first_record


def test_get_anatel_provider_stats():
    """Test getting ANATEL provider statistics."""
    stats = get_anatel_provider_stats()
    
    assert isinstance(stats, dict)
    assert len(stats) > 0
    
    # Check known providers
    assert 'Starlink' in stats
    assert 'Claro' in stats
    
    # Check structure
    starlink_stats = stats['Starlink']
    assert 'market_share' in starlink_stats
    assert 'total_subscribers' in starlink_stats
    assert 'avg_speed_mbps' in starlink_stats
    assert 'technology' in starlink_stats


def test_get_anatel_provider_stats_filtered():
    """Test getting ANATEL provider statistics for specific provider."""
    stats = get_anatel_provider_stats(provider='Starlink')
    
    assert isinstance(stats, dict)
    assert 'Starlink' in stats
    assert len(stats) == 1


def test_convert_anatel_to_connectivity_points():
    """Test converting ANATEL data to connectivity points."""
    anatel_data = fetch_anatel_broadband_data()
    connectivity_points = convert_anatel_to_connectivity_points(anatel_data)
    
    assert isinstance(connectivity_points, list)
    assert len(connectivity_points) == len(anatel_data)
    
    # Check structure
    first_point = connectivity_points[0]
    assert 'latitude' in first_point
    assert 'longitude' in first_point
    assert 'provider' in first_point
    assert 'speed_test' in first_point
    assert 'metadata' in first_point
    
    # Check metadata
    assert first_point['metadata']['source'] == 'ANATEL'
    assert 'state' in first_point['metadata']
    assert 'municipality' in first_point['metadata']


def test_convert_empty_anatel_data():
    """Test converting empty ANATEL data."""
    connectivity_points = convert_anatel_to_connectivity_points([])
    
    assert isinstance(connectivity_points, list)
    assert len(connectivity_points) == 0
