"""Tests for measurement utilities."""

from unittest.mock import Mock, patch

import pytest

from src.utils.measurement_utils import measure_speed


def test_measure_speed():
    """Test speed measurement with mocked speedtest."""
    with patch('speedtest.Speedtest') as mock_speedtest:
        # Setup mock
        mock_st = Mock()
        mock_st.download.return_value = 100_000_000  # 100 Mbps in bits
        mock_st.upload.return_value = 15_000_000     # 15 Mbps in bits
        mock_st.results.dict.return_value = {'ping': 30.0}
        
        mock_speedtest.return_value = mock_st
        
        # Test measurement
        result = measure_speed()
        
        assert result is not None
        assert 'download' in result
        assert 'upload' in result
        assert 'latency' in result
        assert 'stability' in result
        
        assert result['download'] == pytest.approx(100.0)
        assert result['upload'] == pytest.approx(15.0)
        assert result['latency'] == pytest.approx(30.0)
        assert 0 <= result['stability'] <= 100
        
        # Verify speedtest was called
        mock_st.get_best_server.assert_called_once()
        mock_st.download.assert_called_once()
        mock_st.upload.assert_called_once()


def test_measure_speed_returns_none_when_speedtest_missing():
    """Test ImportError branch when speedtest-cli isn't available."""
    import builtins

    original_import = builtins.__import__

    def import_side_effect(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'speedtest':
            raise ImportError("No module named 'speedtest'")
        return original_import(name, globals, locals, fromlist, level)

    with patch('builtins.__import__', side_effect=import_side_effect):
        assert measure_speed() is None


def test_measure_speed_returns_none_on_runtime_error():
    """Test generic exception branch when speedtest raises at runtime."""
    with patch('speedtest.Speedtest', side_effect=RuntimeError('boom')):
        assert measure_speed() is None
