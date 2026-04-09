"""Tests for the Source of Truth migration: lineage, audit, production mode."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.pipeline.audit import AuditEntry, PipelineAuditLog
from src.pipeline.bronze import BronzeLayer
from src.pipeline.orchestrator import PipelineOrchestrator
from src.schemas import DataLineage, MeasurementSchema, SourceType, TechnologyType
from src.sources.base import DataSource
from src.sources.crowdsource import CrowdsourceSource
from src.sources.mock_crowdsource import MockCrowdsourceSource
from src.sources.mock_speedtest import MockSpeedtestSource


# ---------------------------------------------------------------------------
# DataLineage
# ---------------------------------------------------------------------------

class TestDataLineage:
    def test_default_lineage(self):
        lineage = DataLineage()
        assert lineage.is_synthetic is False
        assert lineage.ingested_at is None
        assert lineage.transformations == []

    def test_synthetic_flag(self):
        lineage = DataLineage(is_synthetic=True)
        assert lineage.is_synthetic is True

    def test_to_dict(self):
        now = datetime.now(timezone.utc)
        lineage = DataLineage(
            is_synthetic=False,
            ingested_at=now,
            pipeline_run_id="abc123",
            source_file="test.csv",
            source_row=42,
            checksum="deadbeef",
            transformations=["silver:dedup", "silver:h3"],
        )
        d = lineage.to_dict()
        assert d["is_synthetic"] is False
        assert d["pipeline_run_id"] == "abc123"
        assert d["source_file"] == "test.csv"
        assert d["source_row"] == 42
        assert d["checksum"] == "deadbeef"
        assert d["transformations"] == ["silver:dedup", "silver:h3"]

    def test_lineage_in_measurement(self):
        m = MeasurementSchema(
            id="test-1",
            lat=-15.0,
            lon=-47.0,
            timestamp_utc=datetime.now(timezone.utc),
            source=SourceType.MANUAL,
            lineage=DataLineage(is_synthetic=False, source_file="data.csv"),
        )
        assert m.lineage.is_synthetic is False
        assert m.lineage.source_file == "data.csv"
        d = m.to_dict()
        assert d["lineage"]["is_synthetic"] is False

    def test_default_lineage_on_measurement(self):
        m = MeasurementSchema(
            id="test-2",
            lat=-10.0,
            lon=-40.0,
            timestamp_utc=datetime.now(timezone.utc),
            source=SourceType.CROWDSOURCE,
        )
        assert m.lineage.is_synthetic is False


# ---------------------------------------------------------------------------
# Mock sources are marked synthetic
# ---------------------------------------------------------------------------

class TestSyntheticFlag:
    def test_mock_crowdsource_is_synthetic(self):
        src = MockCrowdsourceSource(num_samples=2)
        assert src.is_synthetic is True
        measurements = src.fetch()
        assert len(measurements) == 2
        for m in measurements:
            assert m.lineage.is_synthetic is True

    def test_mock_speedtest_is_synthetic(self):
        src = MockSpeedtestSource(num_samples=2)
        assert src.is_synthetic is True
        measurements = src.fetch()
        for m in measurements:
            assert m.lineage.is_synthetic is True

    def test_crowdsource_source_not_synthetic(self):
        src = CrowdsourceSource()
        assert src.is_synthetic is False


# ---------------------------------------------------------------------------
# Pipeline audit log
# ---------------------------------------------------------------------------

class TestPipelineAuditLog:
    def test_start_and_commit(self, tmp_path):
        audit = PipelineAuditLog(tmp_path)
        entry = audit.start_run(
            mode="production",
            sources=[{"name": "manual_csv", "synthetic": False}],
        )
        entry.record_bronze(100, synthetic=0)
        entry.record_silver(95)
        entry.record_gold({"full_dataset": tmp_path / "dummy.json"})
        audit.commit(entry)

        entries = audit.read_all()
        assert len(entries) == 1
        assert entries[0]["mode"] == "production"
        assert entries[0]["counts"]["bronze"] == 100
        assert entries[0]["counts"]["synthetic"] == 0
        assert entries[0]["counts"]["real"] == 100
        assert entries[0]["counts"]["silver"] == 95

    def test_multiple_runs_append(self, tmp_path):
        audit = PipelineAuditLog(tmp_path)
        for i in range(3):
            entry = audit.start_run(mode="demo", sources=[])
            entry.record_bronze(i * 10)
            audit.commit(entry)

        entries = audit.read_all()
        assert len(entries) == 3

    def test_errors_recorded(self, tmp_path):
        audit = PipelineAuditLog(tmp_path)
        entry = audit.start_run(mode="demo", sources=[])
        entry.add_error("something broke")
        entry.add_warning("suspicious data")
        audit.commit(entry)

        entries = audit.read_all()
        assert entries[0]["errors"] == ["something broke"]
        assert entries[0]["warnings"] == ["suspicious data"]


# ---------------------------------------------------------------------------
# Bronze layer lineage stamping
# ---------------------------------------------------------------------------

class _StubSource(DataSource):
    is_synthetic = False

    def __init__(self):
        super().__init__("stub")

    def fetch(self):
        return [
            MeasurementSchema(
                id="s1",
                lat=-10.0,
                lon=-40.0,
                timestamp_utc=datetime.now(timezone.utc),
                source=SourceType.MANUAL,
                download_mbps=50.0,
            )
        ]


class TestBronzeLineage:
    def test_lineage_stamped_on_ingest(self, tmp_path):
        bronze = BronzeLayer(tmp_path)
        src = _StubSource()
        filepath = bronze.ingest(src, pipeline_run_id="run-xyz")

        with open(filepath) as f:
            data = json.load(f)

        assert data["is_synthetic"] is False
        m = data["measurements"][0]
        assert m["lineage"]["is_synthetic"] is False
        assert m["lineage"]["pipeline_run_id"] == "run-xyz"
        assert m["lineage"]["ingested_at"] is not None

    def test_synthetic_flag_in_bronze(self, tmp_path):
        bronze = BronzeLayer(tmp_path)
        src = MockCrowdsourceSource(num_samples=1)
        filepath = bronze.ingest(src)

        with open(filepath) as f:
            data = json.load(f)

        assert data["is_synthetic"] is True
        assert data["measurements"][0]["lineage"]["is_synthetic"] is True


# ---------------------------------------------------------------------------
# Orchestrator production / demo modes
# ---------------------------------------------------------------------------

class TestOrchestratorMode:
    def test_production_excludes_synthetic(self, tmp_path):
        pipeline = PipelineOrchestrator(data_dir=tmp_path, mode="production")

        mock_src = MockCrowdsourceSource(num_samples=5)
        real_src = _StubSource()

        # In production mode, mock sources are skipped.
        # The orchestrator prints a warning; real source still runs.
        pipeline.run([mock_src, real_src])

        # Verify only real data lands in bronze
        bronze_dirs = [d.name for d in (tmp_path / "bronze").iterdir() if d.is_dir()]
        assert "stub" in bronze_dirs
        assert "mock_crowdsource" not in bronze_dirs

    def test_demo_includes_synthetic(self, tmp_path):
        pipeline = PipelineOrchestrator(data_dir=tmp_path, mode="demo")
        mock_src = MockCrowdsourceSource(num_samples=3)
        pipeline.run([mock_src])

        bronze_dirs = [d.name for d in (tmp_path / "bronze").iterdir() if d.is_dir()]
        assert "mock_crowdsource" in bronze_dirs

    def test_audit_log_created(self, tmp_path):
        pipeline = PipelineOrchestrator(data_dir=tmp_path, mode="demo")
        pipeline.run([_StubSource()])

        audit_file = tmp_path / "audit" / "pipeline_runs.jsonl"
        assert audit_file.exists()
        entries = json.loads("[" + ",".join(audit_file.read_text().strip().splitlines()) + "]")
        assert len(entries) == 1
        assert entries[0]["mode"] == "demo"
        assert entries[0]["counts"]["bronze"] >= 1


# ---------------------------------------------------------------------------
# CrowdsourceSource reads real submissions
# ---------------------------------------------------------------------------

class TestCrowdsourceSource:
    def test_reads_submissions(self, tmp_path):
        # Write a submission file like the web server would
        submission = {
            "id": "cs-001",
            "lat": -15.5,
            "lon": -47.5,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source": "crowdsource",
            "download_mbps": 25.0,
            "upload_mbps": 5.0,
            "latency_ms": 40.0,
        }
        filepath = tmp_path / "sub_001.json"
        filepath.write_text(json.dumps(submission))

        src = CrowdsourceSource(submissions_dir=tmp_path)
        measurements = src.fetch()
        assert len(measurements) == 1
        assert measurements[0].lineage.is_synthetic is False
        assert measurements[0].download_mbps == 25.0

    def test_skips_already_processed(self, tmp_path):
        submission = {
            "id": "cs-002",
            "lat": -10.0,
            "lon": -40.0,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source": "crowdsource",
            "download_mbps": 10.0,
        }
        filepath = tmp_path / "sub_002.json"
        filepath.write_text(json.dumps(submission))

        src = CrowdsourceSource(submissions_dir=tmp_path)
        first = src.fetch()
        assert len(first) == 1

        # Second call should not re-process
        second = src.fetch()
        assert len(second) == 0


# ---------------------------------------------------------------------------
# SourceType.OOKLA
# ---------------------------------------------------------------------------

class TestOoklaSourceType:
    def test_ookla_source_type_exists(self):
        assert SourceType.OOKLA.value == "ookla"
