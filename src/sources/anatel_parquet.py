"""ANATEL Parquet data source.

This source reads Parquet datasets produced by the ANATEL connectors
(`data_pipeline/connectors/anatel_static_connector.py`) under `data/bronze/anatel/`
and maps rows to the canonical `MeasurementSchema` used by the medallion pipeline.

Notes
-----
The ANATEL connector outputs are *dataset-level* (e.g. backhaul, stations). Some
datasets do not contain per-measurement metrics (download/upload/latency) or even
coordinates. This source supports:

- best-effort: skip invalid/unsupported rows/files
- strict: raise on missing required columns/values
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

from src.schemas import MeasurementSchema, SourceType, TechnologyType

from .base import DataSource

logger = logging.getLogger(__name__)


class AnatelParquetMode(str, Enum):
    BEST_EFFORT = "best-effort"
    STRICT = "strict"


@dataclass(frozen=True)
class AnatelParquetSourceConfig:
    parquet_dir: Path
    mode: AnatelParquetMode = AnatelParquetMode.BEST_EFFORT
    dataset_types: tuple[str, ...] = ("backhaul",)
    source_name: str = "anatel_parquet"
    processed_files_log: Path | None = None
    country: str = "BR"
    include_metricless: bool = False


class AnatelParquetSource(DataSource):
    """DataSource that reads ANATEL Parquet datasets from disk."""

    def __init__(
        self,
        parquet_dir: Path | None = None,
        mode: AnatelParquetMode | str = AnatelParquetMode.BEST_EFFORT,
        dataset_types: Iterable[str] | None = None,
        processed_files_log: Path | None = None,
        include_metricless: bool = False,
        source_name: str = "anatel_parquet",
        country: str = "BR",
    ):
        super().__init__(source_name)

        if parquet_dir is None:
            parquet_dir = Path(__file__).parent.parent.parent / "data" / "bronze" / "anatel"
        parquet_dir = Path(parquet_dir)
        parquet_dir.mkdir(parents=True, exist_ok=True)

        parsed_mode = AnatelParquetMode(mode) if not isinstance(mode, AnatelParquetMode) else mode

        if dataset_types is None:
            dataset_types_tuple: tuple[str, ...] = ("backhaul",)
        else:
            dataset_types_tuple = tuple(str(x).strip() for x in dataset_types if str(x).strip())

        if processed_files_log is None:
            processed_files_log = parquet_dir / ".processed_parquets.json"

        self.config = AnatelParquetSourceConfig(
            parquet_dir=parquet_dir,
            mode=parsed_mode,
            dataset_types=dataset_types_tuple,
            source_name=source_name,
            processed_files_log=Path(processed_files_log),
            country=country,
            include_metricless=include_metricless,
        )

        self._processed_hashes: set[str] = self._load_processed_hashes()

        logger.info(
            "Initialized AnatelParquetSource dir=%s mode=%s dataset_types=%s",
            self.config.parquet_dir,
            self.config.mode,
            self.config.dataset_types,
        )

    def _load_processed_hashes(self) -> set[str]:
        log_path = self.config.processed_files_log
        if log_path is None or not log_path.exists():
            return set()

        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
            return set(data.get("processed_hashes", []))
        except Exception as exc:
            logger.warning("Could not load processed parquets log (%s): %s", log_path, exc)
            return set()

    def _save_processed_hashes(self) -> None:
        log_path = self.config.processed_files_log
        if log_path is None:
            return

        payload = {
            "processed_hashes": sorted(self._processed_hashes),
            "last_updated": datetime.now(UTC).isoformat(),
        }
        log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _file_hash(filepath: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def _infer_dataset_type_from_filename(filepath: Path) -> str | None:
        # Expected format: anatel_{dataset_type}_{timestamp}_{hash}.parquet
        stem = filepath.stem
        parts = stem.split("_")
        if len(parts) >= 2 and parts[0].lower() == "anatel":
            return parts[1].lower()
        return None

    @staticmethod
    def _parse_technology(value: Any) -> TechnologyType:
        if value is None:
            return TechnologyType.UNKNOWN

        text = str(value).strip().lower()
        if not text or text in {"nan", "none"}:
            return TechnologyType.UNKNOWN

        if any(x in text for x in ["fibr", "fiber", "ftth", "fttc"]):
            return TechnologyType.FIBER
        if any(x in text for x in ["cable", "coax"]):
            return TechnologyType.CABLE
        if any(x in text for x in ["dsl", "adsl", "vdsl"]):
            return TechnologyType.DSL
        if any(x in text for x in ["sat", "starlink", "viasat", "hughes"]):
            return TechnologyType.SATELLITE
        if "5g" in text:
            return TechnologyType.MOBILE_5G
        if any(x in text for x in ["4g", "lte"]):
            return TechnologyType.MOBILE_4G
        if any(x in text for x in ["wireless", "radio", "wisp"]):
            return TechnologyType.FIXED_WIRELESS

        return TechnologyType.OTHER

    @staticmethod
    def _coerce_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        try:
            return float(value)
        except Exception:
            return None

    def _pick_timestamp(self, row: pd.Series) -> datetime:
        # Prefer processing timestamp injected by the connector.
        for key in ("_processamento_data", "timestamp", "timestamp_utc", "data", "data_instalacao"):
            if key in row and row[key] is not None and not (isinstance(row[key], float) and pd.isna(row[key])):
                return MeasurementSchema.parse_timestamp(row[key])
        return datetime.now(UTC)

    def _map_backhaul_row(
        self,
        row: pd.Series,
        *,
        dataset_type: str,
        file_hash8: str,
        source_file: str,
        row_index: int,
    ) -> MeasurementSchema | None:
        lat = self._coerce_float(row.get("latitude"))
        lon = self._coerce_float(row.get("longitude"))
        if lat is None or lon is None:
            if self.config.mode == AnatelParquetMode.STRICT:
                raise ValueError("Missing latitude/longitude")
            return None

        download = self._coerce_float(row.get("capacidade_mbps"))
        if download is None and self.config.mode == AnatelParquetMode.STRICT:
            raise ValueError("Missing capacidade_mbps for backhaul")

        provider = row.get("operadora")
        provider_str = str(provider).strip() if provider is not None and not pd.isna(provider) else None

        technology = self._parse_technology(row.get("tecnologia"))

        raw_id = row.get("id")
        raw_id_str = str(raw_id).strip() if raw_id is not None and not pd.isna(raw_id) else str(row_index)
        measurement_id = f"{self.source_name}_{dataset_type}_{file_hash8}_{raw_id_str}"

        metadata: dict[str, Any] = {
            "dataset_type": dataset_type,
            "source_file": source_file,
            "anatel_id": raw_id_str,
        }
        for key in ("municipio", "uf", "frequencia", "capacidade_mbps"):
            if key in row and row[key] is not None and not pd.isna(row[key]):
                metadata[key] = row[key]

        return MeasurementSchema(
            id=measurement_id,
            lat=lat,
            lon=lon,
            timestamp_utc=self._pick_timestamp(row),
            download_mbps=download,
            upload_mbps=None,
            latency_ms=None,
            technology=technology,
            source=SourceType.ANATEL,
            provider=provider_str,
            country=self.config.country,
            region=str(row.get("uf")).strip() if row.get("uf") is not None and not pd.isna(row.get("uf")) else None,
            metadata=metadata,
        )

    def _map_estacoes_row(
        self,
        row: pd.Series,
        *,
        dataset_type: str,
        file_hash8: str,
        source_file: str,
        row_index: int,
    ) -> MeasurementSchema | None:
        if not self.config.include_metricless:
            return None

        lat = self._coerce_float(row.get("latitude"))
        lon = self._coerce_float(row.get("longitude"))
        if lat is None or lon is None:
            if self.config.mode == AnatelParquetMode.STRICT:
                raise ValueError("Missing latitude/longitude")
            return None

        provider = row.get("operadora")
        provider_str = str(provider).strip() if provider is not None and not pd.isna(provider) else None
        technology = self._parse_technology(row.get("tecnologia"))

        raw_id = row.get("id")
        raw_id_str = str(raw_id).strip() if raw_id is not None and not pd.isna(raw_id) else str(row_index)
        measurement_id = f"{self.source_name}_{dataset_type}_{file_hash8}_{raw_id_str}"

        metadata: dict[str, Any] = {
            "dataset_type": dataset_type,
            "source_file": source_file,
            "anatel_id": raw_id_str,
        }
        for key in ("municipio", "uf", "geohash"):
            if key in row and row[key] is not None and not pd.isna(row[key]):
                metadata[key] = row[key]

        # Keep metrics None (these will be filtered in Silver by default).
        return MeasurementSchema(
            id=measurement_id,
            lat=lat,
            lon=lon,
            timestamp_utc=self._pick_timestamp(row),
            download_mbps=None,
            upload_mbps=None,
            latency_ms=None,
            technology=technology,
            source=SourceType.ANATEL,
            provider=provider_str,
            country=self.config.country,
            region=str(row.get("uf")).strip() if row.get("uf") is not None and not pd.isna(row.get("uf")) else None,
            metadata=metadata,
        )

    def _map_dataframe(
        self,
        df: pd.DataFrame,
        *,
        dataset_type: str,
        file_hash8: str,
        source_file: str,
    ) -> list[MeasurementSchema]:
        measurements: list[MeasurementSchema] = []

        if dataset_type == "backhaul":
            required = {"latitude", "longitude"}
            if self.config.mode == AnatelParquetMode.STRICT:
                required |= {"capacidade_mbps"}
            missing = sorted(required - set(df.columns))
            if missing:
                raise ValueError(f"Missing required columns for backhaul: {missing}")

            for i, row in enumerate(df.itertuples(index=False), start=0):
                series = pd.Series(row._asdict())
                mapped = self._map_backhaul_row(
                    series,
                    dataset_type=dataset_type,
                    file_hash8=file_hash8,
                    source_file=source_file,
                    row_index=i,
                )
                if mapped is not None:
                    measurements.append(mapped)
            return measurements

        if dataset_type == "estacoes":
            required = {"latitude", "longitude"}
            missing = sorted(required - set(df.columns))
            if missing and self.config.mode == AnatelParquetMode.STRICT:
                raise ValueError(f"Missing required columns for estacoes: {missing}")

            for i, row in enumerate(df.itertuples(index=False), start=0):
                series = pd.Series(row._asdict())
                mapped = self._map_estacoes_row(
                    series,
                    dataset_type=dataset_type,
                    file_hash8=file_hash8,
                    source_file=source_file,
                    row_index=i,
                )
                if mapped is not None:
                    measurements.append(mapped)
            return measurements

        # Unsupported dataset types (e.g., acesso_fixo has no coordinates).
        if self.config.mode == AnatelParquetMode.STRICT:
            raise ValueError(f"Unsupported ANATEL dataset_type: {dataset_type}")
        return []

    def fetch(self) -> list[MeasurementSchema]:
        parquet_files = sorted(self.config.parquet_dir.glob("anatel_*.parquet"))
        if not parquet_files:
            logger.info("No ANATEL parquet files found in %s", self.config.parquet_dir)
            return []

        all_measurements: list[MeasurementSchema] = []
        newly_processed = 0

        for filepath in parquet_files:
            file_hash = self._file_hash(filepath)
            if file_hash in self._processed_hashes:
                continue

            dataset_type = self._infer_dataset_type_from_filename(filepath)
            if dataset_type is None:
                if self.config.mode == AnatelParquetMode.STRICT:
                    raise ValueError(f"Unable to infer dataset_type from filename: {filepath.name}")
                continue

            if dataset_type not in set(self.config.dataset_types):
                continue

            try:
                df = pd.read_parquet(filepath)
                file_hash8 = file_hash[:8]
                measurements = self._map_dataframe(
                    df,
                    dataset_type=dataset_type,
                    file_hash8=file_hash8,
                    source_file=filepath.name,
                )
                all_measurements.extend(measurements)
                self._processed_hashes.add(file_hash)
                newly_processed += 1
            except Exception:
                logger.exception("Failed to process %s", filepath.name)
                if self.config.mode == AnatelParquetMode.STRICT:
                    raise
                # best-effort: skip the file
                continue

        if newly_processed > 0:
            self._save_processed_hashes()

        logger.info(
            "AnatelParquetSource processed %d new file(s), emitted %d measurement(s)",
            newly_processed,
            len(all_measurements),
        )
        return all_measurements
