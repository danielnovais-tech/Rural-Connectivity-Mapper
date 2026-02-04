#!/usr/bin/env python3
"""Demo workflow for Rural Connectivity Mapper 2026."""

import logging
import sys

from src.models import ConnectivityPoint, SpeedTest
from src.utils import (
    analyze_temporal_evolution,
    compare_providers,
    generate_map,
    generate_ml_report,
    generate_report,
    load_data,
    save_data,
    simulate_router_impact,
    validate_csv_row,
)


def setup_logging():
    """Configure logging for demo."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )


def main():
    """Execute complete demo workflow."""
    setup_logging()
    logger = logging.getLogger(__name__)

    print("\n" + "=" * 80)
    print("RURAL CONNECTIVITY MAPPER 2026 - DEMO WORKFLOW")
    print("Demonstrating Starlink's 2026 expansion analysis in Brazil")
    print("=" * 80 + "\n")

    try:
        # Step 1: Import CSV data
        logger.info("Step 1: Importing sample data from CSV...")
        import csv
        from datetime import datetime

        csv_path = "src/data/sample_data.csv"
        data_path = "src/data/pontos.json"

        points = []
        skipped_count = 0

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                # Validate row
                is_valid, error_msg = validate_csv_row(row, row_num)
                if not is_valid:
                    logger.warning(error_msg)
                    skipped_count += 1
                    continue

                try:
                    speed_test = SpeedTest(
                        download=float(row["download"]),
                        upload=float(row["upload"]),
                        latency=float(row["latency"]),
                        jitter=float(row.get("jitter", 0)),
                        packet_loss=float(row.get("packet_loss", 0)),
                        obstruction=float(row.get("obstruction", 0)),
                    )

                    point = ConnectivityPoint(
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                        provider=row["provider"],
                        speed_test=speed_test,
                        timestamp=row.get("timestamp", datetime.now().isoformat()),
                        point_id=row.get("id"),
                    )

                    points.append(point.to_dict())
                except (ValueError, TypeError) as e:
                    logger.warning(f"Row {row_num}: Error creating point - {e}")
                    skipped_count += 1
                    continue

        if not points:
            logger.error("No valid data points found in CSV")
            sys.exit(1)

        save_data(data_path, points)
        print(f"✓ Imported {len(points)} connectivity points from CSV")
        if skipped_count > 0:
            print(f"  (Skipped {skipped_count} invalid rows)")

        # Step 2: Load data
        logger.info("Step 2: Loading data...")
        data = load_data(data_path)
        print(f"✓ Loaded {len(data)} points from database")

        # Step 3: Display initial statistics
        print("\n" + "-" * 80)
        print("INITIAL CONNECTIVITY STATISTICS")
        print("-" * 80)
        for point in data:
            provider = point["provider"]
            qs = point["quality_score"]
            st = point["speed_test"]
            print(
                f"{provider:15} | Score: {qs['overall_score']:5.1f}/100 ({qs['rating']:9}) | "
                f"Download: {st['download']:6.1f} Mbps | Latency: {st['latency']:5.1f} ms"
            )
        print("-" * 80 + "\n")

        # Step 4: Simulate router impact
        logger.info("Step 3: Simulating router impact (15-25% improvement)...")
        improved_data = simulate_router_impact(data)
        save_data(data_path, improved_data)
        print("✓ Router impact simulation completed")

        # Step 5: Display improved statistics
        print("\n" + "-" * 80)
        print("POST-SIMULATION CONNECTIVITY STATISTICS")
        print("-" * 80)
        for i, point in enumerate(improved_data):
            provider = point["provider"]
            qs = point["quality_score"]
            st = point["speed_test"]
            original_score = data[i]["quality_score"]["overall_score"]
            improvement = qs["overall_score"] - original_score
            print(
                f"{provider:15} | Score: {qs['overall_score']:5.1f}/100 ({qs['rating']:9}) | "
                f"Improvement: +{improvement:4.1f} | Download: {st['download']:6.1f} Mbps"
            )
        print("-" * 80 + "\n")

        # Step 6: Analyze temporal evolution
        logger.info("Step 4: Analyzing temporal evolution...")
        analysis = analyze_temporal_evolution(improved_data)

        print("\n" + "-" * 80)
        print("TEMPORAL ANALYSIS")
        print("-" * 80)
        print(f"Total Points Analyzed: {analysis['total_points']}")
        print(f"Average Quality Score: {analysis['trends']['avg_quality_score']}/100")
        print(f"Average Download Speed: {analysis['trends']['avg_download']} Mbps")
        print(f"Average Latency: {analysis['trends']['avg_latency']} ms")
        print("\nKey Insights:")
        for insight in analysis["insights"]:
            print(f"  • {insight}")
        print("-" * 80 + "\n")

        # Step 7: ML-Enhanced Geospatial Analysis
        logger.info("Step 5: Performing ML-enhanced geospatial analysis...")
        print("\n" + "-" * 80)
        print("ML-ENHANCED ANALYSIS FOR RURAL CONNECTIVITY & STARLINK EXPANSION")
        print("-" * 80)

        ml_report = generate_ml_report(improved_data)

        # Display ROI Analysis
        roi = ml_report["roi_analysis"]
        print("\n💰 Starlink ROI Analysis:")
        print(f"  • Rural Coverage: {roi['rural_percentage']:.1f}% of points")
        print(f"  • Starlink Suitability Score: {roi['starlink_suitability_score']:.1f}/100")
        print(f"  • High Priority Areas: {roi['high_priority_points']} zones")
        print(f"  • Key Recommendation: {roi['recommendations'][0]}")

        # Display Expansion Zones
        zones = ml_report["expansion_zones"]
        print(f"\n🗺️  Identified {zones['total_zones']} Expansion Zones:")
        for zone_id, zone_data in zones["zones"].items():
            print(
                f"  • {zone_id}: Priority {zone_data['priority_score']:.0f}/100 - "
                f"{zone_data['point_count']} points, "
                f"{'Rural' if zone_data['is_primarily_rural'] else 'Urban'}"
            )

        # Save ML report
        import json

        ml_report_path = "demo_ml_analysis.json"
        with open(ml_report_path, "w", encoding="utf-8") as f:
            json.dump(ml_report, f, indent=2, ensure_ascii=False)
        print(f"\n✓ ML analysis saved: {ml_report_path}")
        print("-" * 80 + "\n")

        # Step 8: Generate reports in multiple formats
        logger.info("Step 6: Generating multi-format reports...")

        # Step 6.5: Compare providers
        logger.info("Step 4.5: Comparing provider performance...")
        provider_comparison = compare_providers(improved_data)

        print("\n" + "-" * 80)
        print("PROVIDER COMPARISON (2026 Data)")
        print("-" * 80)
        print(f"Total Providers: {provider_comparison['total_providers']}")
        print(f"Satellite Providers: {', '.join(provider_comparison['satellite_providers'])}")
        print("\nProvider Performance Summary:")

        # Sort providers by average quality score
        sorted_providers = sorted(
            provider_comparison["providers"].items(), key=lambda x: x[1]["quality_score"]["avg"], reverse=True
        )

        for provider, metrics in sorted_providers:
            is_satellite = provider in provider_comparison["satellite_providers"]
            sat_marker = "🛰️ " if is_satellite else "🌐 "

            print(f"\n{sat_marker}{provider}:")
            print(
                f"  Quality Score: {metrics['quality_score']['avg']}/100 "
                f"(min: {metrics['quality_score']['min']}, max: {metrics['quality_score']['max']})"
            )
            print(
                f"  Download: {metrics['download']['avg']} Mbps "
                f"(min: {metrics['download']['min']}, max: {metrics['download']['max']})"
            )
            print(f"  Upload: {metrics['upload']['avg']} Mbps")
            print(f"  Latency: {metrics['latency']['avg']} ms")
            print(f"  Jitter: {metrics['jitter']['avg']} ms")
            print(f"  Packet Loss: {metrics['packet_loss']['avg']}%")
            if is_satellite and metrics["obstruction"]["avg"] > 0:
                print(f"  Obstruction: {metrics['obstruction']['avg']}%")
            print(f"  Stability: {metrics['stability']['avg']}/100")

        print("\nKey Provider Insights:")
        for insight in provider_comparison["insights"]:
            print(f"  • {insight}")
        print("-" * 80 + "\n")

        # Step 7: Generate reports in multiple formats
        logger.info("Step 5: Generating multi-format reports...")

        formats = ["json", "csv", "txt", "html"]
        for fmt in formats:
            report_path = generate_report(improved_data, fmt, f"demo_report.{fmt}")
            print(f"✓ Generated {fmt.upper()} report: {report_path}")

        # Step 9: Generate interactive map
        logger.info("Step 7: Generating interactive map...")
        map_path = generate_map(improved_data, "demo_connectivity_map.html")
        print(f"✓ Generated interactive map: {map_path}")

        # Step 9: Generate map with Starlink coverage overlay
        logger.info("Step 8: Generating map with Starlink coverage overlay...")
        coverage_map_path = generate_map(
            improved_data, "demo_connectivity_map_with_coverage.html", include_starlink_coverage=True
        )
        print(f"✓ Generated map with Starlink coverage: {coverage_map_path}")

        # Final summary
        print("\n" + "=" * 80)
        print("DEMO WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nGenerated Files:")
        print("  • demo_report.json - JSON format report")
        print("  • demo_report.csv - CSV format report")
        print("  • demo_report.txt - Text format report")
        print("  • demo_report.html - HTML format report")
        print("  • demo_connectivity_map.html - Interactive Folium map")

        print("  • demo_connectivity_map_with_coverage.html - Map with Starlink coverage overlay")
        print("\nNext Steps:")
        print("  1. Open demo_connectivity_map_with_coverage.html to view the Starlink coverage zones")
        print("  2. Toggle the coverage layer on/off using the layer control in the map")
        print("  3. Review the generated reports for detailed connectivity analysis")
        print("  4. Use main.py with different flags for custom analysis")
        print("\nExample: python main.py --debug --importar src/data/sample_data.csv --map --starlink-coverage")
        print("  • demo_ml_analysis.json - ML-enhanced geospatial analysis")
        print("\nNext Steps:")
        print("  1. Open demo_connectivity_map.html in your browser to view the interactive map")
        print("  2. Review demo_ml_analysis.json for ML-powered insights")
        print("  3. Review the generated reports for detailed connectivity analysis")
        print("  4. Use main.py with different flags for custom analysis")
        print("\nExample: python main.py --debug --importar src/data/sample_data.csv --ml-analyze")
        print("=" * 80 + "\n")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\n❌ Error: Required file not found - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo workflow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
