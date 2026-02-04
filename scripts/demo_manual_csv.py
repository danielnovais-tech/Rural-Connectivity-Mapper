#!/usr/bin/env python3
"""Demo script for manual CSV data pipeline.

This script demonstrates the manual CSV pipeline workflow:
1. Monitor data/bronze/manual/ for CSV files
2. Process and validate the data
3. Integrate into the bronze/silver/gold pipeline
"""

import shutil
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineOrchestrator
from src.sources import ManualCSVSource


def main():
    """Run the manual CSV pipeline demo."""
    print("=" * 70)
    print("MANUAL CSV DATA PIPELINE DEMO")
    print("=" * 70)
    print()
    print("This demo shows how to process manually downloaded CSV files.")
    print()

    # Set up paths
    manual_dir = Path("data/bronze/manual")
    sample_csv = Path("examples/anatel_sample_manual.csv")

    # Ensure manual directory exists
    manual_dir.mkdir(parents=True, exist_ok=True)

    # Check if sample CSV exists and copy it to manual directory if not already there
    target_csv = manual_dir / "anatel_sample_manual.csv"
    if sample_csv.exists():
        if not target_csv.exists():
            print(f"📂 Copying sample CSV to {manual_dir}/")
            shutil.copy(sample_csv, target_csv)
            print(f"   ✓ {target_csv.name} ready for processing")
        else:
            print(f"📂 Sample CSV already in {manual_dir}/")
            print("   Note: File has been processed before (will be skipped)")
    else:
        print(f"⚠️  Sample CSV not found: {sample_csv}")
        print(f"   Please place CSV files in {manual_dir}/ manually")

    print()
    print("-" * 70)
    print()

    # Initialize manual CSV source
    print("🔍 Initializing Manual CSV Source...")
    manual_source = ManualCSVSource(watch_dir=manual_dir, source_name="anatel_manual")
    print(f"   ✓ Watching directory: {manual_dir}")
    print()

    # Initialize pipeline
    print("🚀 Running pipeline with Manual CSV source...")
    pipeline = PipelineOrchestrator()

    # Run pipeline with manual source
    sources = [manual_source]
    pipeline.run(sources)

    print()
    print("=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print()
    print("📖 What happened:")
    print("  1. ManualCSVSource scanned data/bronze/manual/ for CSV files")
    print("  2. New CSV files were parsed and validated")
    print("  3. Data was processed through Bronze → Silver → Gold layers")
    print("  4. File hashes were recorded to prevent duplicate processing")
    print()
    print("💡 Next steps:")
    print("  - Place more CSV files in data/bronze/manual/")
    print("  - Run this script again - only new files will be processed")
    print("  - Check data/gold/ for aggregated output")
    print()
    print("🔄 To reprocess all files:")
    print("  - Delete data/bronze/manual/.processed_files.json")
    print("  - Run this script again")
    print()


if __name__ == "__main__":
    main()
