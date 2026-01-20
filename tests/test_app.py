"""Tests for the Flask web application."""

import json
import pytest
from pathlib import Path

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
