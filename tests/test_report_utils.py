"""Tests for report generation utilities."""

import pytest
import json
import csv
from pathlib import Path

from src.utils.report_utils import generate_report, getCustomExcludes, getCombinedExcludes


@pytest.fixture
def sample_data():
    """Sample connectivity data for testing."""
    return [
        {
            'id': 'test-1',
            'latitude': -23.5505,
            'longitude': -46.6333,
            'provider': 'Starlink',
            'timestamp': '2026-01-15T10:30:00',
            'speed_test': {
                'download': 150.0,
                'upload': 18.0,
                'latency': 25.0,
                'jitter': 3.0,
                'packet_loss': 0.2,
                'stability': 95.0
            },
            'quality_score': {
                'overall_score': 85.5,
                'speed_score': 88.0,
                'latency_score': 90.0,
                'stability_score': 95.0,
                'rating': 'Excellent'
            }
        },
        {
            'id': 'test-2',
            'latitude': -22.9068,
            'longitude': -43.1729,
            'provider': 'Claro',
            'timestamp': '2026-01-15T11:00:00',
            'speed_test': {
                'download': 92.1,
                'upload': 15.3,
                'latency': 38.7,
                'jitter': 6.5,
                'packet_loss': 0.8,
                'stability': 85.0
            },
            'quality_score': {
                'overall_score': 72.0,
                'speed_score': 70.0,
                'latency_score': 75.0,
                'stability_score': 85.0,
                'rating': 'Good'
            }
        }
    ]


def test_generate_json_report(sample_data, tmp_path):
    """Test JSON report generation."""
    output_path = tmp_path / "test_report.json"
    
    result_path = generate_report(sample_data, 'json', str(output_path))
    
    assert Path(result_path).exists()
    
    # Verify JSON content
    with open(result_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]['id'] == 'test-1'
    assert data[1]['provider'] == 'Claro'


def test_generate_csv_report(sample_data, tmp_path):
    """Test CSV report generation."""
    output_path = tmp_path / "test_report.csv"
    
    result_path = generate_report(sample_data, 'csv', str(output_path))
    
    assert Path(result_path).exists()
    
    # Verify CSV content
    with open(result_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert 'provider' in rows[0]
    assert rows[0]['provider'] == 'Starlink'
    assert 'overall_score' in rows[0]


def test_generate_html_report(sample_data, tmp_path):
    """Test HTML report generation."""
    output_path = tmp_path / "test_report.html"
    
    result_path = generate_report(sample_data, 'html', str(output_path))
    
    assert Path(result_path).exists()
    
    # Verify HTML content
    with open(result_path, 'r') as f:
        content = f.read()
    
    assert '<!DOCTYPE html>' in content
    assert 'Starlink' in content
    assert 'Claro' in content
    assert 'Excellent' in content


def test_generate_html_report_portuguese(sample_data, tmp_path):
    """Test HTML report generation in Portuguese."""
    output_path = tmp_path / "test_report_pt.html"
    
    result_path = generate_report(sample_data, 'html', str(output_path), language='pt')
    
    assert Path(result_path).exists()
    
    # Verify Portuguese content
    with open(result_path, 'r') as f:
        content = f.read()
    
    assert '<!DOCTYPE html>' in content
    assert 'Provedor' in content
    assert 'Excelente' in content
    assert 'MAPEADOR DE CONECTIVIDADE RURAL' in content


def test_generate_txt_report(sample_data, tmp_path):
    """Test TXT report generation."""
    output_path = tmp_path / "test_report.txt"
    
    result_path = generate_report(sample_data, 'txt', str(output_path))
    
    assert Path(result_path).exists()
    
    # Verify TXT content
    with open(result_path, 'r') as f:
        content = f.read()
    
    assert 'RURAL CONNECTIVITY MAPPER 2026' in content
    assert 'Starlink' in content
    assert 'Total Points: 2' in content


def test_generate_txt_report_portuguese(sample_data, tmp_path):
    """Test TXT report generation in Portuguese."""
    output_path = tmp_path / "test_report_pt.txt"
    
    result_path = generate_report(sample_data, 'txt', str(output_path), language='pt')
    
    assert Path(result_path).exists()
    
    # Verify Portuguese TXT content
    with open(result_path, 'r') as f:
        content = f.read()
    
    assert 'MAPEADOR DE CONECTIVIDADE RURAL' in content
    assert 'Provedor' in content
    assert 'Total de Pontos: 2' in content
    assert 'Excelente' in content


def test_generate_report_invalid_format(sample_data):
    """Test error handling for invalid format."""
    with pytest.raises(ValueError):
        generate_report(sample_data, 'invalid_format')


def test_get_custom_excludes_missing_file(tmp_path):
    """Missing settings.json should return empty excludes."""
    missing = tmp_path / "missing_settings.json"
    assert getCustomExcludes(config_path=str(missing)) == []


def test_get_custom_excludes_invalid_json(tmp_path):
    """Invalid JSON should be handled gracefully."""
    bad = tmp_path / "settings.json"
    bad.write_text("{not-json}", encoding="utf-8")
    assert getCustomExcludes(config_path=str(bad)) == []


def test_get_custom_excludes_valid_json(tmp_path):
    """Valid settings.json should return globalExcludes list."""
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps({"globalExcludes": ["dist/", "build/", "__pycache__/", "*.pyc"]}),
        encoding="utf-8",
    )
    assert getCustomExcludes(config_path=str(settings)) == ["dist/", "build/", "__pycache__/", "*.pyc"]


def test_get_combined_excludes_merges_and_dedupes(tmp_path):
    """Combined excludes should include built-ins + project + global, without duplicates."""
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps({"globalExcludes": ["dist/", "node_modules/", "*.pyc"]}),
        encoding="utf-8",
    )

    combined = getCombinedExcludes(
        project_excludes=["build/", ".git/"],
        config_path=str(settings),
    )

    # Built-ins
    assert ".git/" in combined
    assert "node_modules/" in combined
    assert "__pycache__/" in combined
    assert "*.pyc" in combined

    # Project + global
    assert "build/" in combined
    assert "dist/" in combined

    # De-dupe
    assert combined.count("node_modules/") == 1
    assert combined.count(".git/") == 1
    assert combined.count("*.pyc") == 1
