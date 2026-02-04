"""Tests for the fusion engine."""

import json
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.pipeline.fusion_engine import FusionEngine
from src.schemas import MeasurementSchema, SourceType, TechnologyType


@pytest.fixture
def temp_bronze_dir():
    """Create a temporary bronze directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_measurements():
    """Create sample measurements for testing."""
    return [
        MeasurementSchema(
            id="test_001",
            lat=-15.7801,
            lon=-47.9292,
            timestamp_utc=datetime.now(UTC) - timedelta(days=1),
            download_mbps=100.0,
            upload_mbps=50.0,
            latency_ms=20.0,
            technology=TechnologyType.FIBER,
            source=SourceType.ANATEL,
            provider="Test ISP",
            country="BR",
        ),
        MeasurementSchema(
            id="test_002",
            lat=-15.7901,
            lon=-47.9392,
            timestamp_utc=datetime.now(UTC) - timedelta(days=2),
            download_mbps=25.0,
            upload_mbps=10.0,
            latency_ms=50.0,
            technology=TechnologyType.MOBILE_4G,
            source=SourceType.CROWDSOURCE,
            provider="Mobile Carrier",
            country="BR",
        ),
        MeasurementSchema(
            id="test_003",
            lat=-15.8001,
            lon=-47.9492,
            timestamp_utc=datetime.now(UTC) - timedelta(days=3),
            download_mbps=5.0,
            upload_mbps=1.0,
            latency_ms=200.0,
            technology=TechnologyType.SATELLITE,
            source=SourceType.CROWDSOURCE,
            provider="Satellite ISP",
            country="BR",
        ),
    ]


@pytest.fixture
def bronze_with_json(temp_bronze_dir, sample_measurements):
    """Create bronze layer with JSON files."""
    # Create source directories
    anatel_dir = temp_bronze_dir / "anatel"
    crowdsource_dir = temp_bronze_dir / "mock_crowdsource"
    anatel_dir.mkdir(parents=True)
    crowdsource_dir.mkdir(parents=True)
    
    # Save ANATEL data
    anatel_data = {
        "source": "anatel",
        "ingestion_timestamp": datetime.now(UTC).isoformat(),
        "count": 1,
        "measurements": [sample_measurements[0].to_dict()]
    }
    with open(anatel_dir / "anatel_20260124_120000.json", 'w') as f:
        json.dump(anatel_data, f)
    
    # Save crowdsource data
    crowdsource_data = {
        "source": "mock_crowdsource",
        "ingestion_timestamp": datetime.now(UTC).isoformat(),
        "count": 2,
        "measurements": [m.to_dict() for m in sample_measurements[1:]]
    }
    with open(crowdsource_dir / "mock_crowdsource_20260124_120000.json", 'w') as f:
        json.dump(crowdsource_data, f)
    
    return temp_bronze_dir


class TestFusionEngine:
    """Test suite for FusionEngine."""
    
    def test_init(self, temp_bronze_dir):
        """Test fusion engine initialization."""
        engine = FusionEngine(temp_bronze_dir)
        assert engine.bronze_dir == temp_bronze_dir
        assert engine.silver_dir is None
    
    def test_read_bronze_json(self, bronze_with_json, sample_measurements):
        """Test reading JSON files from bronze layer."""
        engine = FusionEngine(bronze_with_json)
        measurements = engine.read_bronze_json()
        
        assert len(measurements) == 3
        assert all(isinstance(m, MeasurementSchema) for m in measurements)
    
    def test_read_bronze_json_by_source(self, bronze_with_json):
        """Test reading JSON files from a specific source."""
        engine = FusionEngine(bronze_with_json)
        
        # Read only ANATEL data
        anatel_measurements = engine.read_bronze_json("anatel")
        assert len(anatel_measurements) == 1
        assert anatel_measurements[0].source == SourceType.ANATEL
        
        # Read only crowdsource data
        crowdsource_measurements = engine.read_bronze_json("mock_crowdsource")
        assert len(crowdsource_measurements) == 2
        assert all(m.source == SourceType.CROWDSOURCE for m in crowdsource_measurements)
    
    def test_read_bronze_data_auto(self, bronze_with_json):
        """Test auto-detection of file format."""
        engine = FusionEngine(bronze_with_json)
        measurements = engine.read_bronze_data(format="auto")
        
        assert len(measurements) == 3
    
    def test_unify_sources(self, sample_measurements):
        """Test source unification."""
        engine = FusionEngine(Path("/tmp"))
        unified = engine.unify_sources(sample_measurements)
        
        assert len(unified) == 3
        # Check that fusion metadata was added
        for measurement in unified:
            assert 'fusion_metadata' in measurement.metadata
            assert 'unified_at' in measurement.metadata['fusion_metadata']
            assert 'source' in measurement.metadata['fusion_metadata']
    
    def test_calculate_icr(self, sample_measurements):
        """Test ICR calculation."""
        engine = FusionEngine(Path("/tmp"))
        enriched = engine.calculate_icr(sample_measurements)
        
        assert len(enriched) == 3
        
        # Check that ICR was added to all measurements
        for measurement in enriched:
            assert 'icr' in measurement.metadata
            assert 'icr_components' in measurement.metadata
            assert 'icr_classification' in measurement.metadata
            
            # Check ICR is in valid range
            icr = measurement.metadata['icr']
            assert 0 <= icr <= 100
            
            # Check components
            components = measurement.metadata['icr_components']
            assert 'download_score' in components
            assert 'upload_score' in components
            assert 'latency_score' in components
            assert 'availability_score' in components
    
    def test_icr_classification(self, sample_measurements):
        """Test ICR classification levels."""
        engine = FusionEngine(Path("/tmp"))
        enriched = engine.calculate_icr(sample_measurements)
        
        # First measurement (fiber, high speeds) should be excellent or good
        icr_1 = enriched[0].metadata['icr']
        classification_1 = enriched[0].metadata['icr_classification']
        assert icr_1 >= 51  # Should be at least "good"
        assert classification_1 in ["good", "excellent"]
        
        # Third measurement (satellite, low speeds) should be lower
        icr_3 = enriched[2].metadata['icr']
        classification_3 = enriched[2].metadata['icr_classification']
        assert icr_3 < icr_1  # Should be lower than fiber
        assert classification_3 in ["poor", "fair", "good"]
    
    def test_icr_components_weights(self):
        """Test that ICR components are properly weighted."""
        engine = FusionEngine(Path("/tmp"))
        
        # Create a measurement with perfect metrics
        perfect_measurement = MeasurementSchema(
            id="perfect",
            lat=-15.7801,
            lon=-47.9292,
            timestamp_utc=datetime.now(UTC),
            download_mbps=100.0,  # Perfect score
            upload_mbps=50.0,     # Perfect score
            latency_ms=0.0,       # Perfect score
            technology=TechnologyType.FIBER,
            source=SourceType.ANATEL,
            country="BR",
        )
        
        enriched = engine.calculate_icr([perfect_measurement])
        components = enriched[0].metadata['icr_components']
        
        # Check that all component scores are calculated
        assert components['download_score'] == 100.0
        assert components['upload_score'] == 100.0
        assert components['latency_score'] == 100.0
        assert components['availability_score'] == 100.0
        
        # ICR should be 100 for perfect metrics
        assert enriched[0].metadata['icr'] == 100.0
    
    def test_icr_with_missing_metrics(self):
        """Test ICR calculation with missing metrics."""
        engine = FusionEngine(Path("/tmp"))
        
        # Create a measurement with some missing metrics
        incomplete_measurement = MeasurementSchema(
            id="incomplete",
            lat=-15.7801,
            lon=-47.9292,
            timestamp_utc=datetime.now(UTC),
            download_mbps=50.0,
            upload_mbps=None,  # Missing
            latency_ms=None,   # Missing
            technology=TechnologyType.MOBILE_4G,
            source=SourceType.CROWDSOURCE,
            country="BR",
        )
        
        enriched = engine.calculate_icr([incomplete_measurement])
        components = enriched[0].metadata['icr_components']
        
        # Check that missing metrics get zero scores (except latency which gets neutral)
        assert components['download_score'] == 50.0  # 50 Mbps = 50%
        assert components['upload_score'] == 0.0     # Missing
        assert components['latency_score'] == 50.0   # Neutral
        assert components['availability_score'] < 100.0  # Not all metrics present
        
        # ICR should still be calculated
        assert 'icr' in enriched[0].metadata
        assert 0 <= enriched[0].metadata['icr'] <= 100
    
    def test_process_integration(self, bronze_with_json):
        """Test the complete fusion engine process."""
        engine = FusionEngine(bronze_with_json)
        processed = engine.process()
        
        assert len(processed) == 3
        
        # Check that all enrichments were applied
        for measurement in processed:
            # Fusion metadata
            assert 'fusion_metadata' in measurement.metadata
            
            # ICR
            assert 'icr' in measurement.metadata
            assert 'icr_components' in measurement.metadata
            assert 'icr_classification' in measurement.metadata
    
    def test_empty_bronze_layer(self, temp_bronze_dir):
        """Test handling of empty bronze layer."""
        engine = FusionEngine(temp_bronze_dir)
        measurements = engine.read_bronze_json()
        
        assert measurements == []
    
    def test_invalid_json_handling(self, temp_bronze_dir):
        """Test handling of invalid JSON files."""
        # Create a source directory with invalid JSON
        invalid_dir = temp_bronze_dir / "invalid_source"
        invalid_dir.mkdir(parents=True)
        
        with open(invalid_dir / "invalid.json", 'w') as f:
            f.write("{ invalid json }")
        
        engine = FusionEngine(temp_bronze_dir)
        measurements = engine.read_bronze_json()
        
        # Should handle error gracefully and return empty list
        assert measurements == []
