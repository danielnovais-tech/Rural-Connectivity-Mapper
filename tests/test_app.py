"""Tests for the Flask web application."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pytest
from unittest.mock import patch, MagicMock

from app import app
from src.utils import save_data


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_data():
    """Create sample connectivity data for testing."""
    return [
        {
            "id": "test1",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "provider": "Starlink",
            "speed_test": {
                "download": 165.4,
                "upload": 22.8,
                "latency": 28.5,
                "jitter": 3.2,
                "packet_loss": 0.1,
                "stability": 92.6
            },
            "quality_score": {
                "overall_score": 100,
                "speed_score": 100,
                "latency_score": 100,
                "stability_score": 100,
                "rating": "Excellent"
            },
            "timestamp": "2026-01-15T10:30:00"
        }
    ]


def test_index_route(client):
    """Test the main dashboard route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Rural Connectivity Mapper 2026' in response.data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['status'] == 'healthy'
    assert 'timestamp' in data


def test_get_data(client, sample_data, tmp_path):
    """Test getting all connectivity data."""
    # Save sample data to temporary file
    data_file = tmp_path / 'test_pontos.json'
    save_data(str(data_file), sample_data)
    
    # Override the data path in the app
    import app as app_module
    original_path = app_module.DATA_PATH
    app_module.DATA_PATH = str(data_file)
    
    try:
        response = client.get('/api/data')
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['total'] == 1
        assert len(result['data']) == 1
        assert result['data'][0]['provider'] == 'Starlink'
    finally:
        app_module.DATA_PATH = original_path


def test_get_statistics(client, sample_data, tmp_path):
    """Test getting connectivity statistics."""
    data_file = tmp_path / 'test_pontos.json'
    save_data(str(data_file), sample_data)
    
    import app as app_module
    original_path = app_module.DATA_PATH
    app_module.DATA_PATH = str(data_file)
    
    try:
        response = client.get('/api/statistics')
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        stats = result['statistics']
        assert stats['total_points'] == 1
        assert stats['avg_quality_score'] == 100
        assert stats['avg_download'] == pytest.approx(165.4)
        assert 'Starlink' in stats['providers']
        assert 'Excellent' in stats['ratings']
    finally:
        app_module.DATA_PATH = original_path


def test_get_analysis(client, sample_data, tmp_path):
    """Test getting temporal analysis."""
    data_file = tmp_path / 'test_pontos.json'
    save_data(str(data_file), sample_data)
    
    import app as app_module
    original_path = app_module.DATA_PATH
    app_module.DATA_PATH = str(data_file)
    
    try:
        response = client.get('/api/analysis')
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'analysis' in result
        assert 'total_points' in result['analysis']
    finally:
        app_module.DATA_PATH = original_path


def test_add_data_point(client, tmp_path):
    """Test adding a new connectivity data point."""
    data_file = tmp_path / 'test_pontos.json'
    save_data(str(data_file), [])
    
    import app as app_module
    original_path = app_module.DATA_PATH
    app_module.DATA_PATH = str(data_file)
    
    try:
        new_point = {
            'latitude': -22.9068,
            'longitude': -43.1729,
            'provider': 'Claro',
            'download': 92.1,
            'upload': 15.3,
            'latency': 38.7,
            'jitter': 6.5,
            'packet_loss': 0.8
        }
        
        response = client.post('/api/data', 
                              data=json.dumps(new_point),
                              content_type='application/json')
        assert response.status_code == 201
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['data']['provider'] == 'Claro'
        assert 'quality_score' in result['data']
    finally:
        app_module.DATA_PATH = original_path


def test_add_data_point_invalid_coordinates(client):
    """Test adding a data point with invalid coordinates."""
    invalid_point = {
        'latitude': 999,  # Invalid latitude
        'longitude': -43.1729,
        'provider': 'Claro',
        'download': 92.1,
        'upload': 15.3,
        'latency': 38.7
    }
    
    response = client.post('/api/data', 
                          data=json.dumps(invalid_point),
                          content_type='application/json')
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert result['success'] is False
    assert 'Invalid coordinates' in result['error']


def test_add_data_point_missing_fields(client):
    """Test adding a data point with missing required fields."""
    incomplete_point = {
        'latitude': -22.9068,
        'longitude': -43.1729,
        # Missing provider, download, upload, latency
    }
    
    response = client.post('/api/data', 
                          data=json.dumps(incomplete_point),
                          content_type='application/json')
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert result['success'] is False
    assert 'Missing required field' in result['error']


def test_simulate_improvement(client, sample_data, tmp_path):
    """Test router impact simulation."""
    data_file = tmp_path / 'test_pontos.json'
    save_data(str(data_file), sample_data)
    
    import app as app_module
    original_path = app_module.DATA_PATH
    app_module.DATA_PATH = str(data_file)
    
    try:
        response = client.post('/api/simulate')
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'data' in result
    finally:
        app_module.DATA_PATH = original_path


def test_get_data_point(client, sample_data, tmp_path):
    """Test getting a specific data point by ID."""
    data_file = tmp_path / 'test_pontos.json'
    save_data(str(data_file), sample_data)
    
    import app as app_module
    original_path = app_module.DATA_PATH
    app_module.DATA_PATH = str(data_file)
    
    try:
        response = client.get('/api/data/test1')
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['data']['id'] == 'test1'
        assert result['data']['provider'] == 'Starlink'
    finally:
        app_module.DATA_PATH = original_path


def test_get_nonexistent_data_point(client, sample_data, tmp_path):
    """Test getting a non-existent data point."""
    data_file = tmp_path / 'test_pontos.json'
    save_data(str(data_file), sample_data)
    
    import app as app_module
    original_path = app_module.DATA_PATH
    app_module.DATA_PATH = str(data_file)
    
    try:
        response = client.get('/api/data/nonexistent')
        assert response.status_code == 404
        
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'not found' in result['error']
    finally:
        app_module.DATA_PATH = original_path


# ============================================================================
# Tests for /api/v2/recommendation endpoint
# ============================================================================

def test_recommendation_endpoint_success(client, tmp_path, monkeypatch):
    """Test successful recommendation request."""
    # Mock analytics to avoid creating files
    import src.utils.analytics as analytics_module
    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir()
    monkeypatch.setattr(analytics_module, 'ANALYTICS_DIR', analytics_dir)
    monkeypatch.setattr(analytics_module, 'EVENTS_FILE', analytics_dir / "events.jsonl")
    
    request_data = {
        'latitude': -15.7801,
        'longitude': -47.9292,
        'use_case': 'rural_home'
    }
    
    response = client.post('/api/v2/recommendation',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result['success'] is True
    assert 'recommendation' in result
    assert 'providers' in result
    assert 'location' in result
    assert 'response_time_ms' in result
    assert result['recommendation']['best_provider'] is not None


def test_recommendation_endpoint_missing_latitude(client):
    """Test recommendation request with missing latitude."""
    request_data = {
        'longitude': -47.9292
    }
    
    response = client.post('/api/v2/recommendation',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert result['success'] is False
    assert 'Missing required fields' in result['error']


def test_recommendation_endpoint_missing_longitude(client):
    """Test recommendation request with missing longitude."""
    request_data = {
        'latitude': -15.7801
    }
    
    response = client.post('/api/v2/recommendation',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert result['success'] is False
    assert 'Missing required fields' in result['error']


def test_recommendation_endpoint_invalid_coordinates(client):
    """Test recommendation request with invalid coordinates."""
    request_data = {
        'latitude': 999,  # Invalid
        'longitude': -47.9292
    }
    
    response = client.post('/api/v2/recommendation',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert result['success'] is False
    assert 'Invalid coordinates' in result['error']


def test_recommendation_endpoint_with_session_id(client, tmp_path, monkeypatch):
    """Test recommendation request with custom session ID."""
    # Mock analytics to avoid creating files
    import src.utils.analytics as analytics_module
    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir()
    monkeypatch.setattr(analytics_module, 'ANALYTICS_DIR', analytics_dir)
    monkeypatch.setattr(analytics_module, 'EVENTS_FILE', analytics_dir / "events.jsonl")
    
    request_data = {
        'latitude': -23.5505,
        'longitude': -46.6333
    }
    
    custom_session_id = 'test-session-123'
    
    response = client.post('/api/v2/recommendation',
                          data=json.dumps(request_data),
                          content_type='application/json',
                          headers={'X-Session-ID': custom_session_id})
    
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result['success'] is True
    
    # Verify session ID was used in analytics
    events_file = analytics_dir / "events.jsonl"
    if events_file.exists():
        with open(events_file, 'r') as f:
            events = [json.loads(line) for line in f if line.strip()]
            # At least one event should have our custom session ID
            session_ids = [e['session_id'] for e in events]
            assert custom_session_id in session_ids


def test_recommendation_endpoint_tracks_analytics(client, tmp_path, monkeypatch):
    """Test that recommendation endpoint tracks analytics events."""
    # Mock analytics to avoid creating files in default location
    import src.utils.analytics as analytics_module
    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir()
    events_file = analytics_dir / "events.jsonl"
    monkeypatch.setattr(analytics_module, 'ANALYTICS_DIR', analytics_dir)
    monkeypatch.setattr(analytics_module, 'EVENTS_FILE', events_file)
    
    request_data = {
        'latitude': -15.7801,
        'longitude': -47.9292
    }
    
    response = client.post('/api/v2/recommendation',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    
    # Verify analytics events were tracked
    assert events_file.exists()
    
    with open(events_file, 'r') as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    # Should have at least 2 events: api_called and api_succeeded
    assert len(events) >= 2
    
    event_names = [e['event_name'] for e in events]
    assert 'recommendation_api_called' in event_names
    assert 'recommendation_api_succeeded' in event_names
    
    # Check that geo data is privacy-safe (rounded)
    for event in events:
        if 'geo' in event:
            # Coordinates should be rounded to 2 decimal places
            lat_str = str(event['geo']['lat'])
            lon_str = str(event['geo']['lon'])
            # Check that they don't have more than 2 decimal places
            if '.' in lat_str:
                assert len(lat_str.split('.')[1]) <= 2
            if '.' in lon_str:
                assert len(lon_str.split('.')[1]) <= 2


def test_recommendation_endpoint_empty_body(client):
    """Test recommendation request with empty body."""
    response = client.post('/api/v2/recommendation',
                          data='',
                          content_type='application/json')
    
    assert response.status_code == 400


def test_recommendation_endpoint_invalid_json(client):
    """Test recommendation request with invalid JSON."""
    response = client.post('/api/v2/recommendation',
                          data='not valid json',
                          content_type='application/json')
    
    # Flask should return 400 for invalid JSON
    assert response.status_code in [400, 500]
