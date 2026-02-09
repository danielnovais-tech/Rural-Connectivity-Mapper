#!/usr/bin/env python3
"""CLI script to run the data pipeline."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineOrchestrator
from src.sources import MockCrowdsourceSource, MockSpeedtestSource


def main():
    """Run the data pipeline with mock sources."""
    # Initialize sources
    sources = [
        MockCrowdsourceSource(num_samples=50),
        MockSpeedtestSource(num_samples=30),
    ]

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
