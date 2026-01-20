"""Tests for CSV upload script."""

import pytest
import json
import csv
from pathlib import Path
from upload_csv import (
    validate_timestamp,
    validate_coordinate,
    validate_speed,
    validate_optional_numeric,
    validate_row,
    load_and_validate_csv,
    convert_to_json
)


def test_validate_timestamp_valid():
    """Test validation of valid timestamps."""
    assert validate_timestamp("2026-01-15T10:30:00")[0] is True
    assert validate_timestamp("2026-01-01T00:00:00")[0] is True
    assert validate_timestamp("2026-12-31T23:59:59")[0] is True


def test_validate_timestamp_invalid():
    """Test validation of invalid timestamps."""
    assert validate_timestamp("invalid")[0] is False
    assert validate_timestamp("2026/01/15")[0] is False
    assert validate_timestamp("")[0] is False
    assert validate_timestamp("not-a-date")[0] is False


def test_validate_coordinate_latitude_valid():
    """Test validation of valid latitude values."""
    assert validate_coordinate("0", "latitude")[0] is True
    assert validate_coordinate("-23.5505", "latitude")[0] is True
    assert validate_coordinate("90", "latitude")[0] is True
    assert validate_coordinate("-90", "latitude")[0] is True


def test_validate_coordinate_latitude_invalid():
    """Test validation of invalid latitude values."""
    assert validate_coordinate("91", "latitude")[0] is False
    assert validate_coordinate("-91", "latitude")[0] is False
    assert validate_coordinate("invalid", "latitude")[0] is False


def test_validate_coordinate_longitude_valid():
    """Test validation of valid longitude values."""
    assert validate_coordinate("0", "longitude")[0] is True
    assert validate_coordinate("-46.6333", "longitude")[0] is True
    assert validate_coordinate("180", "longitude")[0] is True
    assert validate_coordinate("-180", "longitude")[0] is True


def test_validate_coordinate_longitude_invalid():
    """Test validation of invalid longitude values."""
    assert validate_coordinate("181", "longitude")[0] is False
    assert validate_coordinate("-181", "longitude")[0] is False
    assert validate_coordinate("invalid", "longitude")[0] is False


def test_validate_speed_valid():
    """Test validation of valid speed values."""
    assert validate_speed("100", "download")[0] is True
    assert validate_speed("15.5", "upload")[0] is True
    assert validate_speed("0", "download")[0] is True


def test_validate_speed_invalid():
    """Test validation of invalid speed values."""
    assert validate_speed("-10", "download")[0] is False
    assert validate_speed("invalid", "upload")[0] is False


def test_validate_optional_numeric_valid():
    """Test validation of valid optional numeric fields."""
    assert validate_optional_numeric("30.5", "latency")[0] is True
    assert validate_optional_numeric("", "jitter")[0] is True
    assert validate_optional_numeric("0", "packet_loss")[0] is True


def test_validate_optional_numeric_invalid():
    """Test validation of invalid optional numeric fields."""
    assert validate_optional_numeric("-5", "latency")[0] is False
    assert validate_optional_numeric("invalid", "jitter")[0] is False


def test_validate_row_valid():
    """Test validation of a valid row."""
    row = {
        'timestamp': '2026-01-15T10:30:00',
        'latitude': '-23.5505',
        'longitude': '-46.6333',
        'download': '85.2',
        'upload': '12.5',
        'latency': '45.3'
    }
    is_valid, errors = validate_row(row, 2)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_row_missing_required_field():
    """Test validation of row with missing required field."""
    row = {
        'timestamp': '2026-01-15T10:30:00',
        'latitude': '-23.5505',
        'longitude': '-46.6333',
        'download': '85.2'
        # Missing 'upload'
    }
    is_valid, errors = validate_row(row, 2)
    assert is_valid is False
    assert len(errors) > 0
    assert any('upload' in error.lower() for error in errors)


def test_validate_row_invalid_values():
    """Test validation of row with invalid values."""
    row = {
        'timestamp': 'invalid-date',
        'latitude': '95',  # Out of range
        'longitude': '-46.6333',
        'download': '-10',  # Negative
        'upload': '12.5'
    }
    is_valid, errors = validate_row(row, 2)
    assert is_valid is False
    assert len(errors) >= 3  # At least 3 errors


def test_convert_to_json():
    """Test conversion of CSV rows to JSON format."""
    rows = [
        {
            'timestamp': '2026-01-15T10:30:00',
            'latitude': '-23.5505',
            'longitude': '-46.6333',
            'download': '85.2',
            'upload': '12.5',
            'id': '1',
            'city': 'São Paulo',
            'provider': 'Various',
            'latency': '45.3'
        }
    ]
    
    json_data = convert_to_json(rows)
    
    assert len(json_data) == 1
    assert json_data[0]['timestamp'] == '2026-01-15T10:30:00'
    assert json_data[0]['latitude'] == pytest.approx(-23.5505)
    assert json_data[0]['longitude'] == pytest.approx(-46.6333)
    assert json_data[0]['download'] == pytest.approx(85.2)
    assert json_data[0]['upload'] == pytest.approx(12.5)
    assert json_data[0]['id'] == '1'
    assert json_data[0]['city'] == 'São Paulo'
    assert json_data[0]['latency'] == pytest.approx(45.3)


def test_convert_to_json_minimal():
    """Test conversion with only required fields."""
    rows = [
        {
            'timestamp': '2026-01-15T10:30:00',
            'latitude': '-23.5505',
            'longitude': '-46.6333',
            'download': '85.2',
            'upload': '12.5'
        }
    ]
    
    json_data = convert_to_json(rows)
    
    assert len(json_data) == 1
    assert 'timestamp' in json_data[0]
    assert 'latitude' in json_data[0]
    assert 'longitude' in json_data[0]
    assert 'download' in json_data[0]
    assert 'upload' in json_data[0]
    assert 'id' not in json_data[0]
    assert 'city' not in json_data[0]


def test_load_and_validate_csv(tmp_path):
    """Test loading and validating a CSV file."""
    # Create a valid CSV file
    csv_file = tmp_path / "test.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'latitude', 'longitude', 'download', 'upload'])
        writer.writeheader()
        writer.writerow({
            'timestamp': '2026-01-15T10:30:00',
            'latitude': '-23.5505',
            'longitude': '-46.6333',
            'download': '85.2',
            'upload': '12.5'
        })
    
    valid_rows, errors, stats = load_and_validate_csv(str(csv_file))
    
    assert len(valid_rows) == 1
    assert len(errors) == 0
    assert stats['total_rows'] == 1
    assert stats['valid_rows'] == 1
    assert stats['invalid_rows'] == 0


def test_load_and_validate_csv_with_errors(tmp_path):
    """Test loading and validating a CSV file with errors."""
    # Create a CSV file with errors
    csv_file = tmp_path / "test_errors.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'latitude', 'longitude', 'download', 'upload'])
        writer.writeheader()
        writer.writerow({
            'timestamp': 'invalid',
            'latitude': '95',
            'longitude': '-46.6333',
            'download': '-10',
            'upload': '12.5'
        })
    
    valid_rows, errors, stats = load_and_validate_csv(str(csv_file))
    
    assert len(valid_rows) == 0
    assert len(errors) > 0
    assert stats['total_rows'] == 1
    assert stats['valid_rows'] == 0
    assert stats['invalid_rows'] == 1


def test_load_and_validate_csv_missing_required_columns(tmp_path):
    """Test loading CSV with missing required columns."""
    # Create a CSV file with missing required columns
    csv_file = tmp_path / "test_missing.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'latitude', 'longitude'])
        writer.writeheader()
        writer.writerow({
            'timestamp': '2026-01-15T10:30:00',
            'latitude': '-23.5505',
            'longitude': '-46.6333'
        })
    
    valid_rows, errors, _ = load_and_validate_csv(str(csv_file))
    
    assert len(valid_rows) == 0
    assert len(errors) > 0
    assert any('download' in error.lower() or 'upload' in error.lower() for error in errors)


def test_load_and_validate_csv_file_not_found():
    """Test loading a non-existent CSV file."""
    valid_rows, errors, _ = load_and_validate_csv('/nonexistent/file.csv')
    
    assert len(valid_rows) == 0
    assert len(errors) > 0
    assert any('not found' in error.lower() for error in errors)
