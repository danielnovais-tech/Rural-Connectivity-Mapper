"""Tests for crowdsourcing server endpoints."""

import io
import json
import shutil

# Import the Flask app
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import crowdsource_server
from crowdsource_server import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    
    # Use a temporary data file for testing
    temp_dir = tempfile.mkdtemp()
    test_data_file = str(Path(temp_dir) / 'test_pontos.json')
    
    # Override the DATA_FILE in the module
    original_data_file = crowdsource_server.DATA_FILE
    crowdsource_server.DATA_FILE = test_data_file
    
    with app.test_client() as client:
        yield client
    
    # Restore original DATA_FILE
    crowdsource_server.DATA_FILE = original_data_file
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_submission():
    """Sample speedtest submission data."""
    return {
        'latitude': -23.5505,
        'longitude': -46.6333,
        'provider': 'Starlink',
        'download': 150.0,
        'upload': 20.0,
        'latency': 30.0,
        'jitter': 5.0,
        'packet_loss': 0.5
    }


def test_index_page(client):
    """Test that the main form page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Rural Connectivity Mapper' in response.data
    assert b'speedtest-form' in response.data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data


def test_submit_valid_data(client, sample_submission):
    """Test submitting valid speedtest data."""
    response = client.post(
        '/api/submit',
        data=json.dumps(sample_submission),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'point_id' in data
    assert 'quality_score' in data
    assert 'rating' in data


def test_submit_missing_fields(client):
    """Test submitting data with missing required fields."""
    incomplete_data = {
        'latitude': -23.5505,
        'longitude': -46.6333,
        # Missing provider, download, upload, latency
    }
    
    response = client.post(
        '/api/submit',
        data=json.dumps(incomplete_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Missing required fields' in data['error']


def test_submit_invalid_coordinates(client, sample_submission):
    """Test submitting data with invalid coordinates."""
    invalid_data = sample_submission.copy()
    invalid_data['latitude'] = 999  # Invalid latitude
    
    response = client.post(
        '/api/submit',
        data=json.dumps(invalid_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid coordinates' in data['error']


def test_submit_negative_speeds(client, sample_submission):
    """Test submitting data with negative speed values."""
    invalid_data = sample_submission.copy()
    invalid_data['download'] = -10.0  # Negative speed
    
    response = client.post(
        '/api/submit',
        data=json.dumps(invalid_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data


def test_submit_invalid_numeric_type(client, sample_submission):
    """Test submitting data with invalid numeric types."""
    invalid_data = sample_submission.copy()
    invalid_data['download'] = 'not_a_number'
    
    response = client.post(
        '/api/submit',
        data=json.dumps(invalid_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data


def test_download_template(client):
    """Test downloading CSV template."""
    response = client.get('/api/template')
    
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert b'latitude,longitude,provider' in response.data


def test_upload_csv_valid(client):
    """Test uploading valid CSV file."""
    csv_content = """latitude,longitude,provider,download,upload,latency,jitter,packet_loss
-23.5505,-46.6333,Starlink,150.0,20.0,30.0,5.0,0.5
-15.7801,-47.9292,Vivo,85.0,12.0,45.0,8.0,1.2"""
    
    data = {
        'file': (io.BytesIO(csv_content.encode()), 'test.csv')
    }
    
    response = client.post(
        '/api/upload-csv',
        data=data,
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 201
    
    result = json.loads(response.data)
    assert result['success'] is True
    assert result['imported'] == 2


def test_upload_csv_no_file(client):
    """Test CSV upload with no file provided."""
    response = client.post('/api/upload-csv')
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data
    assert 'No file provided' in data['error']


def test_upload_csv_invalid_extension(client):
    """Test CSV upload with non-CSV file."""
    data = {
        'file': (io.BytesIO(b'test content'), 'test.txt')
    }
    
    response = client.post(
        '/api/upload-csv',
        data=data,
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert 'error' in result
    assert 'must be a CSV' in result['error']


def test_upload_csv_missing_columns(client):
    """Test CSV upload with missing required columns."""
    csv_content = """latitude,longitude,provider
-23.5505,-46.6333,Starlink"""
    
    data = {
        'file': (io.BytesIO(csv_content.encode()), 'test.csv')
    }
    
    response = client.post(
        '/api/upload-csv',
        data=data,
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert 'error' in result


def test_upload_csv_invalid_data(client):
    """Test CSV upload with some invalid rows."""
    csv_content = """latitude,longitude,provider,download,upload,latency
-23.5505,-46.6333,Starlink,150.0,20.0,30.0
999,999,Invalid,100,10,40
-15.7801,-47.9292,Vivo,85.0,12.0,45.0"""
    
    data = {
        'file': (io.BytesIO(csv_content.encode()), 'test.csv')
    }
    
    response = client.post(
        '/api/upload-csv',
        data=data,
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 201
    
    result = json.loads(response.data)
    assert result['success'] is True
    assert result['imported'] == 2  # Only 2 valid rows
    assert 'warnings' in result


def test_multiple_submissions(client, sample_submission):
    """Test multiple consecutive submissions."""
    # Submit first point
    response1 = client.post(
        '/api/submit',
        data=json.dumps(sample_submission),
        content_type='application/json'
    )
    assert response1.status_code == 201
    
    # Submit second point with different location
    submission2 = sample_submission.copy()
    submission2['latitude'] = -15.7801
    submission2['longitude'] = -47.9292
    submission2['provider'] = 'Vivo'
    
    response2 = client.post(
        '/api/submit',
        data=json.dumps(submission2),
        content_type='application/json'
    )
    assert response2.status_code == 201
    
    # Verify they have different IDs
    data1 = json.loads(response1.data)
    data2 = json.loads(response2.data)
    assert data1['point_id'] != data2['point_id']


def test_submit_with_optional_fields_omitted(client):
    """Test submitting data without optional fields."""
    minimal_data = {
        'latitude': -23.5505,
        'longitude': -46.6333,
        'provider': 'Starlink',
        'download': 150.0,
        'upload': 20.0,
        'latency': 30.0
        # jitter and packet_loss omitted
    }
    
    response = client.post(
        '/api/submit',
        data=json.dumps(minimal_data),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert data['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
