"""Tests for the analytics module."""

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.analytics import (
    APP_VERSION,
    compute_analytics_summary,
    ensure_analytics_directory,
    generate_anonymous_user_id,
    read_events,
    safe_geo,
    timed_event,
    track_event,
)


@pytest.fixture
def temp_analytics_dir(tmp_path):
    """Create a temporary analytics directory for testing."""
    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir()
    return analytics_dir


@pytest.fixture
def mock_analytics_path(temp_analytics_dir, monkeypatch):
    """Mock the analytics directory path."""
    events_file = temp_analytics_dir / "events.jsonl"
    
    # Patch the module-level constants
    import src.utils.analytics as analytics_module
    monkeypatch.setattr(analytics_module, 'ANALYTICS_DIR', temp_analytics_dir)
    monkeypatch.setattr(analytics_module, 'EVENTS_FILE', events_file)
    
    return events_file


class TestSafeGeo:
    """Tests for the safe_geo function."""
    
    def test_safe_geo_rounds_coordinates(self):
        """Test that coordinates are rounded to 2 decimal places."""
        result = safe_geo(-23.5505199, -46.6333094)
        
        assert result is not None
        assert result['lat'] == -23.55
        assert result['lon'] == -46.63
    
    def test_safe_geo_handles_none(self):
        """Test that None inputs return None."""
        assert safe_geo(None, -46.63) is None
        assert safe_geo(-23.55, None) is None
        assert safe_geo(None, None) is None
    
    def test_safe_geo_preserves_rounded_values(self):
        """Test that already rounded values stay the same."""
        result = safe_geo(-15.78, -47.93)
        
        assert result['lat'] == -15.78
        assert result['lon'] == -47.93
    
    def test_safe_geo_handles_edge_cases(self):
        """Test edge cases like 0, negative, and extreme values."""
        # Zero
        result = safe_geo(0.0, 0.0)
        assert result['lat'] == 0.0
        assert result['lon'] == 0.0
        
        # Extreme values
        result = safe_geo(89.999999, -179.999999)
        assert result['lat'] == 90.0
        assert result['lon'] == -180.0


class TestAnonymousUserId:
    """Tests for anonymous user ID generation."""
    
    def test_generate_anonymous_user_id(self):
        """Test that anonymous user ID is generated correctly."""
        session_id = str(uuid.uuid4())
        anon_id = generate_anonymous_user_id(session_id)
        
        assert anon_id.startswith('anon_')
        assert len(anon_id) == 17  # 'anon_' + 12 chars
    
    def test_anonymous_user_id_is_consistent(self):
        """Test that the same session ID produces the same anonymous ID."""
        session_id = str(uuid.uuid4())
        anon_id1 = generate_anonymous_user_id(session_id)
        anon_id2 = generate_anonymous_user_id(session_id)
        
        assert anon_id1 == anon_id2
    
    def test_different_sessions_produce_different_ids(self):
        """Test that different session IDs produce different anonymous IDs."""
        session_id1 = str(uuid.uuid4())
        session_id2 = str(uuid.uuid4())
        
        anon_id1 = generate_anonymous_user_id(session_id1)
        anon_id2 = generate_anonymous_user_id(session_id2)
        
        assert anon_id1 != anon_id2


class TestTrackEvent:
    """Tests for the track_event function."""
    
    def test_track_event_creates_file(self, mock_analytics_path):
        """Test that track_event creates the events file."""
        session_id = str(uuid.uuid4())
        
        track_event('test_event', session_id)
        
        assert mock_analytics_path.exists()
    
    def test_track_event_writes_valid_json(self, mock_analytics_path):
        """Test that tracked events are valid JSON."""
        session_id = str(uuid.uuid4())
        
        track_event('test_event', session_id)
        
        with open(mock_analytics_path, 'r') as f:
            line = f.readline()
            event = json.loads(line)
        
        assert event['event_name'] == 'test_event'
        assert event['session_id'] == session_id
        assert 'ts' in event
        assert 'anonymous_user_id' in event
        assert event['app_version'] == APP_VERSION
    
    def test_track_event_with_all_parameters(self, mock_analytics_path):
        """Test track_event with all optional parameters."""
        session_id = str(uuid.uuid4())
        context = {'page': 'test_page', 'step': 'step1'}
        metrics = {'duration_ms': 123.45}
        properties = {'button': 'submit'}
        geo = {'lat': -23.55, 'lon': -46.63}
        
        track_event(
            event_name='full_event',
            session_id=session_id,
            context=context,
            metrics=metrics,
            properties=properties,
            geo=geo
        )
        
        with open(mock_analytics_path, 'r') as f:
            event = json.loads(f.readline())
        
        assert event['context'] == context
        assert event['metrics'] == metrics
        assert event['properties'] == properties
        assert event['geo'] == geo
    
    def test_track_event_appends_multiple_events(self, mock_analytics_path):
        """Test that multiple events are appended to the file."""
        session_id = str(uuid.uuid4())
        
        track_event('event1', session_id)
        track_event('event2', session_id)
        track_event('event3', session_id)
        
        with open(mock_analytics_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        assert json.loads(lines[0])['event_name'] == 'event1'
        assert json.loads(lines[1])['event_name'] == 'event2'
        assert json.loads(lines[2])['event_name'] == 'event3'
    
    def test_track_event_handles_errors_gracefully(self, mock_analytics_path, monkeypatch):
        """Test that errors in tracking don't crash the application."""
        session_id = str(uuid.uuid4())
        
        # Mock open to raise an exception
        original_open = open
        def mock_open(*args, **kwargs):
            if 'events.jsonl' in str(args[0]):
                raise IOError("Mock error")
            return original_open(*args, **kwargs)
        
        monkeypatch.setattr('builtins.open', mock_open)
        
        # Should not raise an exception
        track_event('test_event', session_id)


class TestTimedEvent:
    """Tests for the timed_event context manager."""
    
    def test_timed_event_tracks_duration(self, mock_analytics_path):
        """Test that timed_event tracks the duration."""
        import time
        session_id = str(uuid.uuid4())
        
        with timed_event('timed_test', session_id):
            time.sleep(0.05)  # Sleep for 50ms
        
        with open(mock_analytics_path, 'r') as f:
            event = json.loads(f.readline())
        
        assert event['event_name'] == 'timed_test'
        assert 'duration_ms' in event['metrics']
        assert event['metrics']['duration_ms'] >= 40  # Allow some margin
    
    def test_timed_event_with_exception(self, mock_analytics_path):
        """Test that timed_event tracks errors."""
        session_id = str(uuid.uuid4())
        
        try:
            with timed_event('error_test', session_id):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        with open(mock_analytics_path, 'r') as f:
            event = json.loads(f.readline())
        
        assert event['event_name'] == 'error_test'
        assert event['properties'].get('error') is True
        assert 'duration_ms' in event['metrics']
    
    def test_timed_event_with_context_and_properties(self, mock_analytics_path):
        """Test timed_event with additional parameters."""
        session_id = str(uuid.uuid4())
        context = {'page': 'test'}
        properties = {'action': 'click'}
        geo = {'lat': -23.55, 'lon': -46.63}
        
        with timed_event('complex_timed', session_id, context=context, 
                        properties=properties, geo=geo):
            pass
        
        with open(mock_analytics_path, 'r') as f:
            event = json.loads(f.readline())
        
        assert event['context'] == context
        assert 'action' in event['properties']
        assert event['geo'] == geo


class TestReadEvents:
    """Tests for the read_events function."""
    
    def test_read_events_empty_file(self, mock_analytics_path):
        """Test reading from non-existent file returns empty list."""
        events = read_events()
        assert events == []
    
    def test_read_events_returns_all_events(self, mock_analytics_path):
        """Test that read_events returns all events."""
        session_id = str(uuid.uuid4())
        
        track_event('event1', session_id)
        track_event('event2', session_id)
        track_event('event3', session_id)
        
        events = read_events()
        
        assert len(events) == 3
        # Events should be returned in reverse order (most recent first)
        assert events[0]['event_name'] == 'event3'
        assert events[1]['event_name'] == 'event2'
        assert events[2]['event_name'] == 'event1'
    
    def test_read_events_with_limit(self, mock_analytics_path):
        """Test that read_events respects the limit parameter."""
        session_id = str(uuid.uuid4())
        
        for i in range(10):
            track_event(f'event{i}', session_id)
        
        events = read_events(limit=3)
        
        assert len(events) == 3
        assert events[0]['event_name'] == 'event9'  # Most recent


class TestComputeAnalyticsSummary:
    """Tests for the compute_analytics_summary function."""
    
    def test_compute_analytics_summary_empty(self, mock_analytics_path):
        """Test summary with no events."""
        summary = compute_analytics_summary()
        
        assert summary['total_events'] == 0
        assert summary['unique_sessions'] == 0
        assert summary['event_counts'] == {}
    
    def test_compute_analytics_summary_with_events(self, mock_analytics_path):
        """Test summary with various events."""
        session_id1 = str(uuid.uuid4())
        session_id2 = str(uuid.uuid4())
        
        # Track various events
        track_event('app_loaded', session_id1)
        track_event('page_selected', session_id1)
        track_event('app_loaded', session_id2)
        track_event('page_selected', session_id2)
        track_event('page_selected', session_id2)
        
        summary = compute_analytics_summary()
        
        assert summary['total_events'] == 5
        assert summary['unique_sessions'] == 2
        assert summary['event_counts']['app_loaded'] == 2
        assert summary['event_counts']['page_selected'] == 3
    
    def test_compute_analytics_summary_time_to_recommendation(self, mock_analytics_path):
        """Test time-to-recommendation metrics."""
        session_id = str(uuid.uuid4())
        
        # Track recommendation events with durations
        track_event('recommendation_requested', session_id, 
                   metrics={'duration_ms': 100})
        track_event('recommendation_requested', session_id, 
                   metrics={'duration_ms': 200})
        track_event('recommendation_requested', session_id, 
                   metrics={'duration_ms': 300})
        
        summary = compute_analytics_summary()
        
        assert 'time_to_recommendation' in summary
        assert summary['time_to_recommendation']['median_ms'] == 200
        assert summary['time_to_recommendation']['count'] == 3
    
    def test_compute_analytics_summary_ctr(self, mock_analytics_path):
        """Test CTR calculation."""
        session_id = str(uuid.uuid4())
        
        # Track CTA clicks and recommendations
        track_event('recommendation_rendered', session_id)
        track_event('recommendation_rendered', session_id)
        track_event('recommendation_rendered', session_id)
        track_event('recommendation_rendered', session_id)
        track_event('cta_clicked', session_id)
        track_event('cta_clicked', session_id)
        
        summary = compute_analytics_summary()
        
        assert 'ctr' in summary
        assert summary['ctr']['recommendation_rendered'] == 4
        assert summary['ctr']['cta_clicked'] == 2
        assert summary['ctr']['rate'] == 50.0


class TestEnsureAnalyticsDirectory:
    """Tests for the ensure_analytics_directory function."""
    
    def test_ensure_analytics_directory_creates_dir(self, tmp_path, monkeypatch):
        """Test that directory is created if it doesn't exist."""
        import src.utils.analytics as analytics_module
        
        analytics_dir = tmp_path / "new_analytics"
        monkeypatch.setattr(analytics_module, 'ANALYTICS_DIR', analytics_dir)
        
        assert not analytics_dir.exists()
        
        ensure_analytics_directory()
        
        assert analytics_dir.exists()
        assert analytics_dir.is_dir()
    
    def test_ensure_analytics_directory_idempotent(self, temp_analytics_dir, monkeypatch):
        """Test that calling multiple times doesn't cause errors."""
        import src.utils.analytics as analytics_module
        monkeypatch.setattr(analytics_module, 'ANALYTICS_DIR', temp_analytics_dir)
        
        # Should not raise an error
        ensure_analytics_directory()
        ensure_analytics_directory()
        ensure_analytics_directory()
