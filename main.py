#!/usr/bin/env python3
"""Main CLI application for Rural Connectivity Mapper 2026."""

import argparse
import csv
import logging
import sys
from datetime import datetime

from src.models import ConnectivityPoint, SpeedTest
from src.utils import (
    analyze_temporal_evolution,
    export_ecosystem_bundle,
    export_for_agrix_boost,
    export_for_hybrid_simulator,
    generate_map,
    generate_ml_report,
    generate_report,
    get_default_country,
    list_available_countries,
    load_data,
    save_data,
    simulate_router_impact,
    validate_coordinates,
    validate_csv_row,
)


def setup_logging(debug: bool = False) -> None:
    """Configure logging settings.
    
    Args:
        debug: Enable debug level logging if True
    """
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def import_csv(csv_path: str, output_path: str = 'src/data/pontos.json', country_code: str = None) -> None:
    """Import connectivity data from CSV file.
    
    Args:
        csv_path: Path to CSV file
        output_path: Path to save JSON data
        country_code: ISO country code for the data (default: uses default country)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Importing data from {csv_path}...")
    
    if country_code is None:
        country_code = get_default_country()
    
    try:
        points = []
        errors = []
        skipped_count = 0
        
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate CSV has required columns
            if reader.fieldnames is None:
                logger.error("CSV file is empty or has no header row")
                sys.exit(1)
            
            required_cols = ['latitude', 'longitude', 'provider', 'download', 'upload', 'latency']
            missing_cols = [col for col in required_cols if col not in reader.fieldnames]
            if missing_cols:
                logger.error(f"CSV is missing required columns: {', '.join(missing_cols)}")
                logger.error(f"Found columns: {', '.join(reader.fieldnames)}")
                sys.exit(1)
            
            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                # Validate row before processing
                is_valid, error_msg = validate_csv_row(row, row_num)
                if not is_valid:
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    skipped_count += 1
                    continue
                

                try:
                    # Convert numeric fields with error handling
                    lat = float(row['latitude'])
                    lon = float(row['longitude'])
                    download = float(row['download'])
                    upload = float(row['upload'])
                    latency = float(row['latency'])
                    jitter = float(row.get('jitter', 0))
                    packet_loss = float(row.get('packet_loss', 0))
                    obstruction = float(row.get('obstruction', 0))
                    
                    # Additional validation for coordinates
                    if not validate_coordinates(lat, lon):
                        logger.warning(f"Row {row_num}: Invalid coordinates ({lat}, {lon}), skipping")
                        skipped_count += 1
                        continue
                    
                    # Create SpeedTest
                    speed_test = SpeedTest(
                        download=download,
                        upload=upload,
                        latency=latency,
                        jitter=jitter,
                        packet_loss=packet_loss,
                        obstruction=obstruction,
                    )
                    
                    # Create ConnectivityPoint
                    point = ConnectivityPoint(
                        latitude=lat,
                        longitude=lon,
                        provider=row['provider'],
                        speed_test=speed_test,
                        timestamp=row.get('timestamp', datetime.now().isoformat()),
                        point_id=row.get('id'),
                        country=row.get('country', country_code),
                    )
                    
                    points.append(point.to_dict())
                    logger.debug(f"Imported point: {point}")
                    
                except ValueError as e:
                    error_msg = f"Row {row_num}: Invalid numeric value - {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    skipped_count += 1
                    continue
                except Exception as e:
                    error_msg = f"Row {row_num}: Unexpected error - {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    skipped_count += 1
                    continue

        
        # Save to JSON
        if points:
            save_data(output_path, points)
            logger.info(f"Successfully imported {len(points)} points to {output_path}")
            
            if skipped_count > 0:
                logger.warning(f"Skipped {skipped_count} invalid rows")
                logger.info("Run with --debug flag to see details of skipped rows")
        else:
            logger.error("No valid data points found in CSV file")
            if errors:
                logger.error("Errors encountered:")
                for error in errors[:10]:  # Show first 10 errors
                    logger.error(f"  {error}")
                if len(errors) > 10:
                    logger.error(f"  ... and {len(errors) - 10} more errors")
            sys.exit(1)
    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error importing CSV: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Rural Connectivity Mapper 2026 - Analyze rural connectivity worldwide',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --debug --importar src/data/sample_data.csv --relatorio json
  %(prog)s --simulate --map --country US
  %(prog)s --analyze --relatorio html --country CA
  %(prog)s --list-countries
        """
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose logging'
    )
    
    parser.add_argument(
        '--country',
        metavar='CODE',
        help='ISO country code (e.g., BR, US, CA, GB). Use --list-countries to see all available.'
    )
    
    parser.add_argument(
        '--list-countries',
        action='store_true',
        help='List all available country codes and exit'
    )
    
    parser.add_argument(
        '--relatorio',
        choices=['json', 'csv', 'txt', 'html'],
        help='Generate report in specified format'
    )
    
    parser.add_argument(
        '--importar',
        metavar='CSV',
        help='Import data from CSV file'
    )
    
    parser.add_argument(
        '--simulate',
        action='store_true',
        help='Simulate router impact on quality scores'
    )
    
    parser.add_argument(
        '--map',
        action='store_true',
        help='Generate interactive Folium map'
    )
    
    parser.add_argument(
        '--starlink-coverage',
        action='store_true',
        help='Add Starlink coverage overlay to the map (requires --map)'
    )

    parser.add_argument(
        '--no-starlink-coverage',
        action='store_true',
        help='Disable Starlink coverage overlay on the map'
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze temporal evolution'
    )
    
    parser.add_argument(
        '--ml-analyze',
        action='store_true',
        help='Perform ML-enhanced geospatial analysis for rural connectivity and Starlink expansion'
    )

    parser.add_argument(
        '--language',
        '--lang',
        choices=['en', 'pt'],
        default='en',
        help='Language for reports and analysis output (en=English, pt=Portuguese)'
    )

    parser.add_argument(
        '--export',
        choices=['hybrid', 'agrix', 'ecosystem'],
        help='Export data for ecosystem integration (hybrid=Hybrid Architecture Simulator, agrix=AgriX-Boost, ecosystem=Full bundle)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Handle list-countries command
    if args.list_countries:
        countries = list_available_countries()
        print("\nAvailable country codes:")
        print("=" * 50)
        from src.utils.config_utils import get_country_info
        for code in sorted(countries):
            info = get_country_info(code)
            print(f"  {code}: {info['name']}")
        print("=" * 50)
        sys.exit(0)
    
    logger.info("Rural Connectivity Mapper 2026 - Starting")
    
    # Get country code
    country_code = args.country if args.country else get_default_country()
    logger.info(f"Using country: {country_code}")

    # Validate country code early to provide clear feedback
    available_countries = list_available_countries()
    if country_code not in available_countries:
        logger.error(f"Invalid country code: {country_code}")
        print(f"Error: '{country_code}' is not a valid country code.")
        print("Use --list-countries to see all available country codes.")
        sys.exit(1)
    
    # Check if any action was specified

    if args.starlink_coverage and args.no_starlink_coverage:
        logger.error("Cannot use both --starlink-coverage and --no-starlink-coverage")
        print("Error: choose either --starlink-coverage or --no-starlink-coverage (not both).")
        sys.exit(2)

    if not any([
        args.importar,
        args.relatorio,
        args.simulate,
        args.map,
        args.analyze,
        args.ml_analyze,
        args.export,
    ]):
        parser.print_help()
        sys.exit(0)
    
    data_path = 'src/data/pontos.json'
    
    # Import CSV data
    if args.importar:
        import_csv(args.importar, data_path, country_code)
    
    # Load existing data
    data = load_data(data_path)
    
    if not data:
        logger.warning("No data available. Import data first with --importar")
        if not args.importar:
            sys.exit(1)
    
    # Simulate router impact
    if args.simulate:
        logger.info("Simulating router impact...")
        data = simulate_router_impact(data)
        save_data(data_path, data)
        logger.info("Router impact simulation completed and saved")
    
    # Analyze temporal evolution
    if args.analyze:
        logger.info("Analyzing temporal evolution...")
        analysis = analyze_temporal_evolution(data, args.language)
        
        print("\n" + "=" * 80)
        print("TEMPORAL ANALYSIS RESULTS")
        print("=" * 80)
        print(f"\nTotal Points: {analysis['total_points']}")
        print(f"Date Range: {analysis['date_range'].get('start', 'N/A')} to {analysis['date_range'].get('end', 'N/A')}")
        print("\nOverall Trends:")
        print(f"  Average Quality Score: {analysis['trends']['avg_quality_score']}/100")
        print(f"  Average Download: {analysis['trends']['avg_download']} Mbps")
        print(f"  Average Latency: {analysis['trends']['avg_latency']} ms")
        print("\nInsights:")
        for insight in analysis['insights']:
            print(f"  • {insight}")
        print("=" * 80 + "\n")
    
    # ML-enhanced geospatial analysis
    if args.ml_analyze:
        logger.info("Performing ML-enhanced geospatial analysis...")
        ml_report = generate_ml_report(data)
        
        print("\n" + "=" * 80)
        print("ML-ENHANCED GEOSPATIAL ANALYSIS FOR RURAL CONNECTIVITY")
        print("=" * 80)
        print("\n📊 SUMMARY")
        print(f"  Total Points Analyzed: {ml_report['summary']['total_points_analyzed']}")
        print(f"  ML Model Version: {ml_report['summary']['ml_model_version']}")
        
        print("\n💰 STARLINK ROI ANALYSIS")
        roi = ml_report['roi_analysis']
        print(f"  Rural Coverage: {roi['rural_percentage']:.1f}% ({roi['rural_points']}/{roi['total_points']} points)")
        print(f"  High Priority Areas: {roi['high_priority_points']} points need immediate attention")
        print(f"  Current Avg Quality: {roi['avg_current_quality']:.1f}/100")
        print(f"  Starlink Suitability Score: {roi['starlink_suitability_score']:.1f}/100")
        print("\n  Recommendations:")
        for rec in roi['recommendations']:
            print(f"    • {rec}")
        
        print("\n🗺️  EXPANSION ZONES")
        zones = ml_report['expansion_zones']
        print(f"  Identified {zones['total_zones']} optimal expansion zones")
        print(f"  Top Priority: {zones['top_priority_zone']}")
        print("\n  Zone Details:")
        for zone_id, zone_data in zones['zones'].items():
            print(f"\n  {zone_id.upper()}:")
            print(f"    Location: ({zone_data['center']['latitude']:.4f}, {zone_data['center']['longitude']:.4f})")
            print(f"    Points: {zone_data['point_count']}")
            print(f"    Avg Quality: {zone_data['avg_quality_score']:.1f}/100")
            print(f"    Distance from City: {zone_data['avg_distance_from_city_km']:.1f} km")
            print(f"    Rural Area: {'Yes' if zone_data['is_primarily_rural'] else 'No'}")
            print(f"    Priority Score: {zone_data['priority_score']:.1f}")
            print(f"    → {zone_data['recommendation']}")
        
        print("\n🎯 TOP 5 PRIORITY AREAS FOR IMPROVEMENT")
        for i, area in enumerate(ml_report['top_priority_areas'], 1):
            print(f"\n  #{i} - {area['provider']}")
            print(f"    Location: ({area['latitude']:.4f}, {area['longitude']:.4f})")
            print(f"    Current Quality: {area['current_quality']:.1f}/100")
            print(f"    Priority Score: {area['priority_score']:.1f}/100")
            print(f"    Distance from City: {area['distance_from_city_km']:.1f} km")
            print(f"    Rural: {'Yes' if area['is_rural'] else 'No'}")
        
        print("\n" + "=" * 80 + "\n")
        
        # Save ML analysis to JSON
        import json
        ml_output_path = 'ml_analysis_report.json'
        with open(ml_output_path, 'w', encoding='utf-8') as f:
            json.dump(ml_report, f, indent=2, ensure_ascii=False)
        logger.info(f"ML analysis saved to {ml_output_path}")
        print(f"✓ ML analysis report saved to {ml_output_path}\n")
    
    # Generate report
    if args.relatorio:
        logger.info(f"Generating {args.relatorio.upper()} report...")
        report_path = generate_report(data, args.relatorio, language=args.language)
        logger.info(f"Report generated: {report_path}")
    
    # Generate map
    # Note: Map generation does not currently support multilingual features
    if args.map:
        logger.info("Generating interactive map...")

        include_coverage = args.starlink_coverage or not args.no_starlink_coverage
        map_path = generate_map(
            data,
            include_starlink_coverage=include_coverage,
            country_code=country_code,
        )

        if include_coverage:
            logger.info("Including Starlink coverage overlay layer")

        logger.info(f"Map generated: {map_path}")
        if args.starlink_coverage:
            logger.info("Starlink coverage overlay enabled")
    
    # Export for ecosystem integration
    if args.export:
        logger.info(f"Exporting data for ecosystem integration ({args.export})...")
        
        if args.export == 'hybrid':
            export_path = export_for_hybrid_simulator(data)
            logger.info(f"Exported for Hybrid Architecture Simulator: {export_path}")
            print(f"\n✓ Data exported for Hybrid Architecture Simulator: {export_path}")
        
        elif args.export == 'agrix':
            export_path = export_for_agrix_boost(data)
            logger.info(f"Exported for AgriX-Boost: {export_path}")
            print(f"\n✓ Data exported for AgriX-Boost: {export_path}")
        
        elif args.export == 'ecosystem':
            export_paths = export_ecosystem_bundle(data)
            logger.info("Exported complete ecosystem bundle")
            print("\n" + "=" * 80)
            print("ECOSYSTEM BUNDLE EXPORTED")
            print("=" * 80)
            print(f"  Hybrid Architecture Simulator: {export_paths['hybrid_simulator']}")
            print(f"  AgriX-Boost: {export_paths['agrix_boost']}")
            print(f"  Ecosystem Manifest: {export_paths['manifest']}")
            print("=" * 80 + "\n")
    
    logger.info("Rural Connectivity Mapper 2026 - Completed successfully")


if __name__ == '__main__':
    main()
