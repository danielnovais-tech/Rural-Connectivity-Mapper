import csv
from pathlib import Path

import pytest

from data_pipeline.connectors.anatel_static_connector import ANATELStaticConnector
from src.sources.anatel_parquet import AnatelParquetMode, AnatelParquetSource


def _write_backhaul_csv(path: Path) -> None:
    rows = [
        {
            "id": "1",
            "municipio": "Brasilia",
            "uf": "DF",
            "operadora": "Vivo",
            "latitude": "-15.7801",
            "longitude": "-47.9292",
            "frequencia": "700",
            "capacidade_mbps": "100.0",
        },
        {
            "id": "2",
            "municipio": "Brasilia",
            "uf": "DF",
            "operadora": "Claro",
            "latitude": "-15.7802",
            "longitude": "-47.9293",
            "frequencia": "700",
            # Partial row: capacity missing
            "capacidade_mbps": "",
        },
    ]

    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _find_backhaul_parquet(output_dir: Path) -> Path:
    matches = sorted(output_dir.glob("anatel_backhaul_*.parquet"))
    assert matches, f"No backhaul parquet output found in {output_dir}"
    return matches[0]


def test_anatel_connector_to_source_best_effort(tmp_path: Path) -> None:
    manual_dir = tmp_path / "manual"
    output_dir = tmp_path / "bronze" / "anatel"

    csv_path = manual_dir / "backhaul_sample.csv"
    _write_backhaul_csv(csv_path)

    connector = ANATELStaticConnector(manual_dir=manual_dir, output_dir=output_dir)
    results = connector.run()

    assert results
    assert all(r.get("status") == "success" for r in results)

    parquet_path = _find_backhaul_parquet(output_dir)
    assert parquet_path.exists()

    source = AnatelParquetSource(
        parquet_dir=output_dir,
        mode=AnatelParquetMode.BEST_EFFORT,
        dataset_types=("backhaul",),
    )
    measurements = source.fetch()

    assert len(measurements) == 2
    assert sum(1 for m in measurements if m.download_mbps is None) == 1
    assert all(m.lat is not None and m.lon is not None for m in measurements)
    assert all(m.source.value == "anatel" for m in measurements)


def test_anatel_connector_to_source_strict_raises_on_missing_capacity(tmp_path: Path) -> None:
    manual_dir = tmp_path / "manual"
    output_dir = tmp_path / "bronze" / "anatel"

    csv_path = manual_dir / "backhaul_sample.csv"
    _write_backhaul_csv(csv_path)

    connector = ANATELStaticConnector(manual_dir=manual_dir, output_dir=output_dir)
    results = connector.run()
    assert results

    _find_backhaul_parquet(output_dir)

    source = AnatelParquetSource(
        parquet_dir=output_dir,
        mode=AnatelParquetMode.STRICT,
        dataset_types=("backhaul",),
    )

    with pytest.raises(ValueError):
        source.fetch()
