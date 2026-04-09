"""Pipeline audit log — immutable record of every pipeline run.

Each pipeline execution writes an audit entry that captures:
- unique run ID
- start / end timestamps
- sources used (with synthetic flag)
- record counts per layer (bronze, silver, gold)
- any errors or warnings
- SHA-256 digest of the gold output for tamper detection

The log is append-only JSON-Lines (one JSON object per line) stored at
``data/audit/pipeline_runs.jsonl``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PipelineAuditLog:
    """Append-only audit trail for pipeline runs."""

    def __init__(self, audit_dir: Path | None = None):
        if audit_dir is None:
            audit_dir = Path(__file__).parent.parent.parent / "data" / "audit"
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.audit_dir / "pipeline_runs.jsonl"

    def start_run(self, *, mode: str, sources: list[dict[str, Any]]) -> AuditEntry:
        return AuditEntry(mode=mode, sources=sources)

    def commit(self, entry: AuditEntry) -> None:
        record = entry.finalise()
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")
        logger.info("Audit entry %s written → %s", record["run_id"], self.log_path)

    def read_all(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        entries: list[dict[str, Any]] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
        return entries


class AuditEntry:
    """In-flight record for a single pipeline execution."""

    def __init__(self, *, mode: str, sources: list[dict[str, Any]]):
        self.run_id = uuid.uuid4().hex
        self.mode = mode
        self.started_at = datetime.now(timezone.utc)
        self.sources = sources
        self.bronze_count: int = 0
        self.silver_count: int = 0
        self.gold_files: list[str] = []
        self.synthetic_count: int = 0
        self.real_count: int = 0
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.gold_checksum: str | None = None

    def record_bronze(self, count: int, *, synthetic: int = 0) -> None:
        self.bronze_count = count
        self.synthetic_count = synthetic
        self.real_count = count - synthetic

    def record_silver(self, count: int) -> None:
        self.silver_count = count

    def record_gold(self, files: dict[str, Path]) -> None:
        self.gold_files = [str(p) for p in files.values()]
        # Checksum gold full dataset if present
        full = files.get("full_dataset")
        if full and Path(full).exists():
            sha = hashlib.sha256()
            with open(full, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha.update(chunk)
            self.gold_checksum = sha.hexdigest()

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def finalise(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "started_at": self.started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_s": round((datetime.now(timezone.utc) - self.started_at).total_seconds(), 2),
            "sources": self.sources,
            "counts": {
                "bronze": self.bronze_count,
                "silver": self.silver_count,
                "gold_files": len(self.gold_files),
                "synthetic": self.synthetic_count,
                "real": self.real_count,
            },
            "gold_checksum": self.gold_checksum,
            "gold_files": self.gold_files,
            "warnings": self.warnings,
            "errors": self.errors,
        }
