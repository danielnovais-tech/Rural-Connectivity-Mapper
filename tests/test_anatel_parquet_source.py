from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from src.schemas import SourceType
from src.sources import AnatelParquetSource


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_anatel_parquet_source_backhaul_best_effort(tmp_path: Path):
    parquet_dir = tmp_path / "bronze" / "anatel"
    ts = datetime(2026, 2, 1, 12, 0, 0, tzinfo=UTC).isoformat()

    df = pd.DataFrame(
        [
            {
                "id": "BH-001",
                "municipio": "Brasilia",
                "uf": "DF",
                "operadora": "Claro",
                "latitude": -15.7801,
                "longitude": -47.9292,
                "frequencia": "2.4GHz",
                "capacidade_mbps": 150.0,
                "_processamento_data": ts,
                "_dataset_tipo": "backhaul",
                "_confidence_score": 0.9,
            }
        ]
    )

    parquet_path = parquet_dir / "anatel_backhaul_20260201_120000_deadbeef.parquet"
    _write_parquet(df, parquet_path)

    source = AnatelParquetSource(parquet_dir=parquet_dir, mode="best-effort")
    measurements = source.fetch()

    assert len(measurements) == 1
    m = measurements[0]
    assert m.source == SourceType.ANATEL
    assert m.lat == pytest.approx(-15.7801)
    assert m.lon == pytest.approx(-47.9292)
    assert m.download_mbps == pytest.approx(150.0)
    assert m.upload_mbps is None
    assert m.latency_ms is None
    assert m.provider == "Claro"
    assert m.country == "BR"
    assert m.region == "DF"
    assert m.metadata["dataset_type"] == "backhaul"
    assert m.metadata["source_file"] == parquet_path.name

    # Second fetch should not re-emit the same file (dedupe by file hash)
    measurements2 = source.fetch()
    assert measurements2 == []


def test_anatel_parquet_source_strict_missing_required_raises(tmp_path: Path):
    parquet_dir = tmp_path / "bronze" / "anatel"
    df = pd.DataFrame(
        [
            {
                "id": "BH-002",
                # missing latitude/longitude
                "operadora": "Vivo",
                "capacidade_mbps": 200.0,
                "_processamento_data": datetime.now(UTC).isoformat(),
                "_dataset_tipo": "backhaul",
            }
        ]
    )
    parquet_path = parquet_dir / "anatel_backhaul_20260201_120001_deadbeef.parquet"
    _write_parquet(df, parquet_path)

    source = AnatelParquetSource(parquet_dir=parquet_dir, mode="strict")
    with pytest.raises(ValueError):
        source.fetch()


def test_anatel_parquet_source_best_effort_skips_unsupported_dataset(tmp_path: Path):
    parquet_dir = tmp_path / "bronze" / "anatel"
    df = pd.DataFrame(
        [
            {
                "municipio": "X",
                "uf": "SP",
                "quantidade": 10,
                "velocidade": "50 Mbps",
                "tecnologia": "Fibra",
                "_processamento_data": datetime.now(UTC).isoformat(),
                "_dataset_tipo": "acesso_fixo",
            }
        ]
    )
    parquet_path = parquet_dir / "anatel_acesso_fixo_20260201_120002_deadbeef.parquet"
    _write_parquet(df, parquet_path)

    source = AnatelParquetSource(
        parquet_dir=parquet_dir,
        mode="best-effort",
        dataset_types=["acesso_fixo"],
    )
    assert source.fetch() == []
