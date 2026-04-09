"""Crowdsource data source that reads real community submissions.

This connector reads measurements that were submitted through the crowdsource
web form (crowdsource_server.py) and persisted to the data directory.

Unlike MockCrowdsourceSource, this reads *real* user-submitted data.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.schemas import DataLineage, MeasurementSchema, SourceType

from .base import DataSource

logger = logging.getLogger(__name__)


class CrowdsourceSource(DataSource):
    """Read real crowdsourced measurements submitted via the web form or API.

    Monitors ``data/bronze/crowdsource/`` for JSON files produced by
    ``crowdsource_server.py`` and yields validated ``MeasurementSchema``
    instances with full lineage.
    """

    is_synthetic = False

    def __init__(self, submissions_dir: Path | None = None):
        super().__init__("crowdsource")
        if submissions_dir is None:
            submissions_dir = Path(__file__).parent.parent.parent / "data" / "bronze" / "crowdsource"
        self.submissions_dir = Path(submissions_dir)
        self.submissions_dir.mkdir(parents=True, exist_ok=True)

        self._processed_log = self.submissions_dir / ".processed_submissions.json"
        self._processed_hashes: set[str] = self._load_processed()

    def _load_processed(self) -> set[str]:
        if not self._processed_log.exists():
            return set()
        try:
            data = json.loads(self._processed_log.read_text(encoding="utf-8"))
            return set(data.get("processed_hashes", []))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not load processed submissions log: %s", exc)
            return set()

    def _save_processed(self) -> None:
        payload = {
            "processed_hashes": sorted(self._processed_hashes),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self._processed_log.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _file_hash(filepath: Path) -> str:
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def fetch(self) -> list[MeasurementSchema]:
        measurements: list[MeasurementSchema] = []
        new_hashes: list[str] = []

        for filepath in sorted(self.submissions_dir.glob("*.json")):
            if filepath.name.startswith("."):
                continue

            fhash = self._file_hash(filepath)
            if fhash in self._processed_hashes:
                continue

            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Skipping unreadable file %s: %s", filepath, exc)
                continue

            records = data.get("measurements", [data] if "lat" in data else [])
            for idx, record in enumerate(records):
                try:
                    record.setdefault("lineage", {})
                    record["lineage"]["is_synthetic"] = False
                    record["lineage"]["ingested_at"] = datetime.now(timezone.utc).isoformat()
                    record["lineage"]["source_file"] = str(filepath.name)
                    record["lineage"]["source_row"] = idx
                    record["lineage"]["checksum"] = hashlib.sha256(
                        json.dumps(record, sort_keys=True, default=str).encode()
                    ).hexdigest()

                    m = MeasurementSchema.from_dict(record)
                    measurements.append(m)
                except Exception as exc:
                    logger.warning("Row %d in %s failed validation: %s", idx, filepath.name, exc)

            new_hashes.append(fhash)

        if new_hashes:
            self._processed_hashes.update(new_hashes)
            self._save_processed()
            logger.info("Ingested %d crowdsource measurements from %d new files", len(measurements), len(new_hashes))
        else:
            logger.info("No new crowdsource submissions found")

        return measurements
