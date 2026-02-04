"""Tests for data utilities."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.data_utils import backup_data, load_data, save_data


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return [
        {"id": "test-1", "latitude": -23.5505, "longitude": -46.6333, "provider": "Starlink"},
        {"id": "test-2", "latitude": -22.9068, "longitude": -43.1729, "provider": "Claro"},
    ]


def test_load_save_data(tmp_path, sample_data):
    """Test saving and loading JSON data."""
    test_file = tmp_path / "test_data.json"

    # Save data
    save_data(str(test_file), sample_data)

    assert test_file.exists()

    # Load data
    loaded_data = load_data(str(test_file))

    assert len(loaded_data) == 2
    assert loaded_data[0]["id"] == "test-1"
    assert loaded_data[1]["provider"] == "Claro"


def test_backup_data(tmp_path, sample_data):
    """Test creating backup of data file."""
    test_file = tmp_path / "test_data.json"

    # Create original file
    save_data(str(test_file), sample_data)

    # Create backup
    backup_path = backup_data(str(test_file))

    assert Path(backup_path).exists()
    assert "backup" in backup_path

    # Verify backup content matches original
    original_data = load_data(str(test_file))
    backup_data_content = load_data(backup_path)

    assert original_data == backup_data_content


def test_load_nonexistent_file(tmp_path):
    """Test loading from non-existent file."""
    test_file = tmp_path / "nonexistent.json"

    # Should return empty list without error
    data = load_data(str(test_file))

    assert data == []


def test_backup_nonexistent_file(tmp_path):
    """Test backup of non-existent file raises error."""
    test_file = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError):
        backup_data(str(test_file))


def test_save_creates_directory(tmp_path, sample_data):
    """Test that save_data creates parent directories."""
    test_file = tmp_path / "subdir" / "nested" / "test_data.json"

    # Should create directories automatically
    save_data(str(test_file), sample_data)

    assert test_file.exists()

    # Verify data
    loaded_data = load_data(str(test_file))
    assert len(loaded_data) == 2


def test_load_invalid_json_raises(tmp_path):
    """Test that invalid JSON triggers JSONDecodeError."""
    test_file = tmp_path / "invalid.json"
    test_file.write_text("{ not valid json ]", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_data(str(test_file))


def test_save_data_raises_on_write_error(tmp_path, sample_data):
    """Test that save_data propagates IO errors (e.g., permission issues)."""
    test_file = tmp_path / "test_data.json"

    with patch("src.utils.data_utils.open", side_effect=OSError("nope")):
        with pytest.raises(OSError):
            save_data(str(test_file), sample_data)


def test_load_data_raises_on_read_error(tmp_path):
    """Test that load_data propagates unexpected read errors."""
    test_file = tmp_path / "test_data.json"
    test_file.write_text("[]", encoding="utf-8")

    with patch("src.utils.data_utils.open", side_effect=OSError("read fail")):
        with pytest.raises(OSError):
            load_data(str(test_file))
