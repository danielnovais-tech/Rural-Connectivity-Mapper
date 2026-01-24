"""Tests for ANATEL Static Connector."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import json

# Add the parent directory to the path to import the connector
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_pipeline.connectors.anatel_static_connector import ANATELStaticConnector


@pytest.fixture
def temp_dirs():
    """Create temporary input and output directories."""
    temp_input = tempfile.mkdtemp()
    temp_output = tempfile.mkdtemp()
    
    yield temp_input, temp_output
    
    # Cleanup
    shutil.rmtree(temp_input, ignore_errors=True)
    shutil.rmtree(temp_output, ignore_errors=True)


@pytest.fixture
def sample_csv(temp_dirs):
    """Create a sample CSV file."""
    temp_input, _ = temp_dirs
    csv_path = Path(temp_input) / "test_data.csv"
    
    # Create sample data
    data = {
        'id': ['test-001', 'test-002', 'test-003'],
        'latitude': [-23.5505, -22.9068, -19.9167],
        'longitude': [-46.6333, -43.1729, -43.9345],
        'technology': ['Fiber', 'Cable', 'DSL'],
        'capacity_mbps': [1000, 500, 100],
        'provider': ['Provider A', 'Provider B', 'Provider C']
    }
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    return csv_path


def test_connector_initialization(temp_dirs):
    """Test connector initializes correctly."""
    temp_input, temp_output = temp_dirs
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    assert connector.input_dir == Path(temp_input)
    assert connector.output_dir == Path(temp_output)
    assert Path(temp_output).exists()  # Should create output dir
    assert connector.report is not None


def test_find_csv_files(temp_dirs, sample_csv):
    """Test finding CSV files in input directory."""
    temp_input, temp_output = temp_dirs
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    csv_files = connector.find_csv_files()
    
    assert len(csv_files) == 1
    assert csv_files[0].name == "test_data.csv"


def test_validate_dataframe_valid(temp_dirs):
    """Test validation of a valid DataFrame."""
    temp_input, temp_output = temp_dirs
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    # Create valid DataFrame
    df = pd.DataFrame({
        'latitude': [-23.5505, -22.9068],
        'longitude': [-46.6333, -43.1729],
        'speed': [100, 200]
    })
    
    is_valid, errors = connector.validate_dataframe(df, "test.csv")
    
    assert is_valid is True
    assert len(errors) == 0


def test_validate_dataframe_missing_fields(temp_dirs):
    """Test validation fails with missing required fields."""
    temp_input, temp_output = temp_dirs
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    # Create DataFrame missing required fields
    df = pd.DataFrame({
        'latitude': [-23.5505, -22.9068],
        'speed': [100, 200]
    })
    
    is_valid, errors = connector.validate_dataframe(df, "test.csv")
    
    assert is_valid is False
    assert len(errors) > 0
    assert any('longitude' in str(error).lower() for error in errors)


def test_validate_dataframe_empty(temp_dirs):
    """Test validation fails with empty DataFrame."""
    temp_input, temp_output = temp_dirs
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    df = pd.DataFrame()
    
    is_valid, errors = connector.validate_dataframe(df, "test.csv")
    
    assert is_valid is False
    assert len(errors) > 0


def test_process_csv_file_success(temp_dirs, sample_csv):
    """Test successful processing of a CSV file."""
    temp_input, temp_output = temp_dirs
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    result = connector.process_csv_file(sample_csv)
    
    assert result['status'] == 'success'
    assert result['records_processed'] == 3
    assert result['output_file'] is not None
    assert len(result['errors']) == 0
    
    # Verify parquet file was created
    output_file = Path(result['output_file'])
    assert output_file.exists()
    assert output_file.suffix == '.parquet'
    
    # Verify parquet file is readable and contains correct data
    df = pd.read_parquet(output_file)
    assert len(df) == 3
    assert 'latitude' in df.columns
    assert 'longitude' in df.columns


def test_process_all_files(temp_dirs, sample_csv):
    """Test processing all CSV files."""
    temp_input, temp_output = temp_dirs
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    report = connector.process_all()
    
    assert report['summary']['total_files'] == 1
    assert report['summary']['successful'] == 1
    assert report['summary']['failed'] == 0
    assert report['summary']['total_records'] == 3
    assert len(report['files_processed']) == 1
    
    # Verify report JSON was created
    report_files = list(Path(temp_output).glob("anatel_processing_report_*.json"))
    assert len(report_files) == 1
    
    # Verify report JSON is valid
    with open(report_files[0], 'r') as f:
        report_data = json.load(f)
    
    assert 'connector' in report_data
    assert report_data['connector'] == 'ANATEL Static Connector'
    assert 'summary' in report_data


def test_process_no_files(temp_dirs):
    """Test processing when no CSV files exist."""
    temp_input, temp_output = temp_dirs
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    report = connector.process_all()
    
    assert report['summary']['total_files'] == 0
    assert report['summary']['successful'] == 0
    assert report['summary']['failed'] == 0


def test_process_invalid_csv(temp_dirs):
    """Test processing an invalid CSV file."""
    temp_input, temp_output = temp_dirs
    csv_path = Path(temp_input) / "invalid.csv"
    
    # Create CSV without required fields
    df = pd.DataFrame({
        'name': ['A', 'B', 'C'],
        'value': [1, 2, 3]
    })
    df.to_csv(csv_path, index=False)
    
    connector = ANATELStaticConnector(
        input_dir=temp_input,
        output_dir=temp_output
    )
    
    report = connector.process_all()
    
    assert report['summary']['total_files'] == 1
    assert report['summary']['successful'] == 0
    assert report['summary']['failed'] == 1
    assert len(report['errors']) > 0


def test_integration_with_real_sample():
    """Integration test with real sample data."""
    # Use the actual sample CSV if it exists
    sample_csv_path = Path(__file__).parent.parent / "data" / "manual" / "anatel_backhaul.csv"
    
    if not sample_csv_path.exists():
        pytest.skip("Sample CSV not found, skipping integration test")
    
    # Create temporary output directory
    temp_output = tempfile.mkdtemp()
    
    try:
        connector = ANATELStaticConnector(
            input_dir=str(sample_csv_path.parent),
            output_dir=temp_output
        )
        
        report = connector.process_all()
        
        assert report['summary']['successful'] > 0
        assert report['summary']['total_records'] > 0
        
        # Verify parquet files were created
        parquet_files = list(Path(temp_output).glob("*.parquet"))
        assert len(parquet_files) > 0
        
        # Verify at least one parquet file is readable
        df = pd.read_parquet(parquet_files[0])
        assert len(df) > 0
        assert 'latitude' in df.columns
        assert 'longitude' in df.columns
        
    finally:
        shutil.rmtree(temp_output, ignore_errors=True)
