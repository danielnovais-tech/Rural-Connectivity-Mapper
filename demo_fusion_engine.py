#!/usr/bin/env python3
"""Demonstration of the Fusion Engine functionality.

This script demonstrates:
1. Reading Bronze layer data
2. Unifying data from multiple sources
3. Calculating the Rural Connectivity Index (ICR)
4. Viewing ICR classifications
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import FusionEngine, BronzeLayer
from src.sources import MockCrowdsourceSource, MockSpeedtestSource


def main():
    """Demonstrate fusion engine functionality."""
    
    print("=" * 70)
    print("🔄 FUSION ENGINE DEMONSTRATION")
    print("=" * 70)
    
    # Setup
    data_dir = Path(__file__).parent.parent / "data"
    bronze_dir = data_dir / "bronze"
    
    # Step 1: Generate some sample data if bronze layer is empty
    print("\n📥 Step 1: Preparing Bronze layer data...")
    bronze = BronzeLayer(bronze_dir)
    
    # Check if we have data
    existing_data = bronze.read_all()
    if not existing_data:
        print("  No existing data found. Generating sample data...")
        sources = [
            MockCrowdsourceSource(num_samples=30),
            MockSpeedtestSource(num_samples=20),
        ]
        for source in sources:
            bronze.ingest(source)
    else:
        print(f"  Found {len(existing_data)} existing measurements in Bronze layer")
    
    # Step 2: Initialize Fusion Engine
    print("\n🔧 Step 2: Initializing Fusion Engine...")
    fusion = FusionEngine(bronze_dir)
    print("  ✓ Fusion Engine initialized")
    
    # Step 3: Read Bronze layer data
    print("\n📖 Step 3: Reading Bronze layer data...")
    measurements = fusion.read_bronze_data(format="auto")
    print(f"  ✓ Loaded {len(measurements)} measurements")
    
    # Show source distribution
    from collections import Counter
    source_counts = Counter(m.source.value for m in measurements)
    print("\n  Source distribution:")
    for source, count in sorted(source_counts.items()):
        print(f"    - {source}: {count} measurements")
    
    # Step 4: Unify sources
    print("\n🔀 Step 4: Unifying data from multiple sources...")
    unified = fusion.unify_sources(measurements)
    print(f"  ✓ Unified {len(unified)} measurements")
    
    # Step 5: Calculate ICR
    print("\n📊 Step 5: Calculating Rural Connectivity Index (ICR)...")
    enriched = fusion.calculate_icr(unified)
    print(f"  ✓ Calculated ICR for {len(enriched)} measurements")
    
    # Step 6: Analyze ICR results
    print("\n📈 Step 6: Analyzing ICR results...")
    
    # ICR classification distribution
    classifications = Counter(m.metadata['icr_classification'] for m in enriched)
    print("\n  ICR Classification Distribution:")
    for classification, count in sorted(classifications.items()):
        percentage = (count / len(enriched)) * 100
        print(f"    - {classification.capitalize()}: {count} ({percentage:.1f}%)")
    
    # ICR statistics
    icr_values = [m.metadata['icr'] for m in enriched]
    avg_icr = sum(icr_values) / len(icr_values)
    min_icr = min(icr_values)
    max_icr = max(icr_values)
    
    print(f"\n  ICR Statistics:")
    print(f"    - Average: {avg_icr:.2f}")
    print(f"    - Minimum: {min_icr:.2f}")
    print(f"    - Maximum: {max_icr:.2f}")
    
    # Show sample measurements with ICR
    print("\n📋 Sample Measurements with ICR:")
    print("-" * 70)
    
    # Show best, average, and worst connectivity
    sorted_by_icr = sorted(enriched, key=lambda m: m.metadata['icr'], reverse=True)
    
    samples = [
        ("Best", sorted_by_icr[0]),
        ("Median", sorted_by_icr[len(sorted_by_icr) // 2]),
        ("Worst", sorted_by_icr[-1]),
    ]
    
    for label, measurement in samples:
        icr = measurement.metadata['icr']
        classification = measurement.metadata['icr_classification']
        components = measurement.metadata['icr_components']
        
        print(f"\n{label} Connectivity (ICR: {icr:.2f} - {classification.upper()}):")
        print(f"  Location: ({measurement.lat:.4f}, {measurement.lon:.4f})")
        print(f"  Source: {measurement.source.value}")
        print(f"  Technology: {measurement.technology.value}")
        print(f"  Download: {measurement.download_mbps:.2f} Mbps" if measurement.download_mbps else "  Download: N/A")
        print(f"  Upload: {measurement.upload_mbps:.2f} Mbps" if measurement.upload_mbps else "  Upload: N/A")
        print(f"  Latency: {measurement.latency_ms:.2f} ms" if measurement.latency_ms else "  Latency: N/A")
        print(f"  ICR Components:")
        print(f"    - Download Score: {components['download_score']:.2f}")
        print(f"    - Upload Score: {components['upload_score']:.2f}")
        print(f"    - Latency Score: {components['latency_score']:.2f}")
        print(f"    - Availability Score: {components['availability_score']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ FUSION ENGINE DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Insights:")
    print("1. The Fusion Engine successfully unified data from multiple sources")
    print("2. ICR (Rural Connectivity Index) was calculated for all measurements")
    print("3. ICR provides a composite score (0-100) based on:")
    print("   - Download speed (40% weight)")
    print("   - Upload speed (30% weight)")
    print("   - Latency (20% weight)")
    print("   - Availability (10% weight)")
    print("4. Classifications help identify areas needing connectivity improvements")
    print()


if __name__ == "__main__":
    main()
