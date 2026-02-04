#!/usr/bin/env python3
"""CLI script to run the data pipeline."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineOrchestrator
from src.sources import AnatelParquetSource, ManualCSVSource, MockCrowdsourceSource, MockSpeedtestSource


def _parse_csv_list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def main():
    """Run the data pipeline with all available sources."""
    parser = argparse.ArgumentParser(description="Run the Rural Connectivity Mapper data pipeline")
    parser.add_argument(
        "--include-anatel-parquet",
        action="store_true",
        help="Include ANATEL Parquet datasets from data/bronze/anatel/ as a DataSource",
    )
    parser.add_argument(
        "--anatel-parquet-dir",
        default=str(Path("data") / "bronze" / "anatel"),
        help="Directory containing ANATEL Parquet files (default: data/bronze/anatel)",
    )
    parser.add_argument(
        "--anatel-parquet-mode",
        choices=["best-effort", "strict"],
        default="best-effort",
        help="Mapping/validation mode for ANATEL Parquet ingestion",
    )
    parser.add_argument(
        "--anatel-parquet-dataset-types",
        default="backhaul",
        help="Comma-separated dataset types to ingest (default: backhaul)",
    )
    parser.add_argument(
        "--anatel-include-metricless",
        action="store_true",
        help="Also emit metric-less ANATEL rows (e.g., estacoes). These are filtered by Silver by default.",
    )
    args = parser.parse_args()

    # Initialize sources
    sources = [ManualCSVSource()]  # Process measurement-level CSVs in data/bronze/manual/

    if args.include_anatel_parquet:
        sources.append(
            AnatelParquetSource(
                parquet_dir=Path(args.anatel_parquet_dir),
                mode=args.anatel_parquet_mode,
                dataset_types=_parse_csv_list(args.anatel_parquet_dataset_types),
                include_metricless=args.anatel_include_metricless,
            )
        )

    sources.extend(
        [
            MockCrowdsourceSource(num_samples=50),
            MockSpeedtestSource(num_samples=30),
        ]
    )
    
    # Initialize and run pipeline
    pipeline = PipelineOrchestrator()
    pipeline.run(sources)
    
    print("✅ Pipeline execution completed successfully!")
    print("\nYou can now find the processed data in:")
    print("  - Bronze (raw): data/bronze/")
    print("  - Silver (enriched): data/silver/")
    print("  - Gold (aggregated): data/gold/")


if __name__ == "__main__":
    main()
