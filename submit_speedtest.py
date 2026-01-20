#!/usr/bin/env python3
"""Simple command-line script to submit speedtest data to Rural Connectivity Mapper.

This script allows users to easily submit their connectivity data either:
1. Interactively by answering prompts
2. Via command-line arguments
3. By running an actual speedtest
"""

import argparse
import sys
from datetime import datetime
from typing import cast

from src.config import DATA_FILE_PATH
from src.models import ConnectivityPoint, SpeedTest
from src.utils import load_data, save_data, validate_coordinates

# Try to import optional speedtest module
try:
    import speedtest
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False
    speedtest = None  # type: ignore[assignment]


def get_location():
    """Try to get user's location using IP geolocation."""
    try:
        import requests
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.ok:
            data = response.json()
            return data.get('lat'), data.get('lon'), data.get('city', 'Unknown')
    except Exception:
        pass
    return None, None, None


def run_speedtest() -> dict[str, float] | None:
    """Run an actual speedtest and return results."""
    if not SPEEDTEST_AVAILABLE:
        print("⚠️  speedtest-cli not available. Install it with: pip install speedtest-cli")
        return None

    print("\n🔄 Running speedtest... This may take a minute...")

    try:
        st = speedtest.Speedtest()  # type: ignore[reportPossiblyUnboundVariable]
        st.get_best_server()  # type: ignore[reportUnknownMemberType]

        print("📥 Testing download speed...")
        download: float = float(st.download()) / 1_000_000  # type: ignore[reportUnknownMemberType]  # Convert to Mbps

        print("📤 Testing upload speed...")
        upload: float = float(st.upload()) / 1_000_000  # type: ignore[reportUnknownMemberType]  # Convert to Mbps

        print("📡 Measuring latency...")
        latency: float = float(getattr(st.results, 'ping', 0))  # type: ignore[reportUnknownMemberType]

        return {
            'download': round(download, 2),
            'upload': round(upload, 2),
            'latency': round(latency, 2)
        }
    except (speedtest.SpeedtestException, OSError, ValueError) as e:  # type: ignore[union-attr]
        print(f"❌ Error running speedtest: {e}")
        return None


def interactive_submit():
    """Interactive mode - prompt user for all information."""
    print("\n" + "=" * 70)
    print("🌍 Rural Connectivity Mapper - Submit Your Data")
    print("=" * 70 + "\n")

    # Try to get location automatically
    auto_lat, auto_lon, city = get_location()

    if auto_lat and auto_lon:
        print(f"📍 Detected location: {city or 'Unknown'}")
        print(f"   Latitude: {auto_lat}, Longitude: {auto_lon}")
        use_auto = input("\nUse this location? (y/n) [y]: ").strip().lower()

        if use_auto in ('', 'y', 'yes'):
            latitude = auto_lat
            longitude = auto_lon
        else:
            latitude = float(input("Enter latitude: "))
            longitude = float(input("Enter longitude: "))
    else:
        print("Enter your location (use Google Maps to find coordinates):")
        latitude = float(input("Latitude: "))
        longitude = float(input("Longitude: "))

    if not validate_coordinates(latitude, longitude):
        print("❌ Invalid coordinates. Please check and try again.")
        sys.exit(1)

    # Provider
    print("\nInternet Provider Options:")
    providers = ['Starlink', 'Viasat', 'HughesNet', 'Claro', 'Vivo', 'TIM', 'Oi', 'Other']
    for i, p in enumerate(providers, 1):
        print(f"  {i}. {p}")

    provider_choice = input("\nSelect provider (1-8) or type name: ").strip()

    if provider_choice.isdigit() and 1 <= int(provider_choice) <= len(providers):
        provider = providers[int(provider_choice) - 1]
    else:
        provider = provider_choice if provider_choice else 'Unknown'

    # Speed test option
    print("\nSpeed Test Data:")
    print("  1. Run automatic speedtest (requires speedtest-cli)")
    print("  2. Enter manual values (from fast.com, speedtest.net, etc.)")

    choice = input("\nChoice (1/2) [2]: ").strip()

    # Initialize variables
    download = 0.0
    upload = 0.0
    latency = 0.0
    jitter = 0.0
    packet_loss = 0.0

    if choice == '1' and SPEEDTEST_AVAILABLE:
        results = run_speedtest()
        if results:
            download = results['download']
            upload = results['upload']
            latency = results['latency']
            jitter = 0.0
            packet_loss = 0.0
        else:
            print("Falling back to manual entry...")
            choice = '2'

    if choice != '1' or not SPEEDTEST_AVAILABLE:
        print("\nEnter your speedtest results:")
        download = float(input("Download speed (Mbps): "))
        upload = float(input("Upload speed (Mbps): "))
        latency = float(input("Latency/Ping (ms): "))

        jitter_input = input("Jitter (ms) [0]: ").strip()
        jitter = float(jitter_input) if jitter_input else 0.0

        packet_input = input("Packet loss (%) [0]: ").strip()
        packet_loss = float(packet_input) if packet_input else 0.0

    # Confirm submission
    print("\n" + "=" * 70)
    print("📋 Review Your Submission:")
    print("=" * 70)
    print(f"Location: {latitude}, {longitude}")
    print(f"Provider: {provider}")
    print(f"Download: {download} Mbps")
    print(f"Upload: {upload} Mbps")
    print(f"Latency: {latency} ms")
    print(f"Jitter: {jitter} ms")
    print(f"Packet Loss: {packet_loss}%")
    print("=" * 70 + "\n")

    confirm = input("Submit this data? (y/n) [y]: ").strip().lower()

    if confirm not in ('', 'y', 'yes'):
        print("❌ Submission cancelled.")
        sys.exit(0)

    # Create and save point
    speed_test = SpeedTest(
        download=download,
        upload=upload,
        latency=latency,
        jitter=jitter,
        packet_loss=packet_loss
    )

    point = ConnectivityPoint(
        latitude=latitude,
        longitude=longitude,
        provider=provider,
        speed_test=speed_test,
        timestamp=datetime.now().isoformat()
    )

    # Save to data file
    existing_data = cast(list[dict[str, object]], load_data(DATA_FILE_PATH))
    point_dict: dict[str, object] = point.to_dict()  # type: ignore[reportUnknownMemberType]
    existing_data.append(point_dict)
    save_data(DATA_FILE_PATH, existing_data)

    print("\n✅ Success! Your data has been submitted.")
    print(f"   Point ID: {point.id}")
    print(f"   Quality Score: {point.quality_score.overall_score:.1f}/100 ({point.quality_score.rating})")
    print("\nThank you for contributing to Rural Connectivity Mapper! 🙏\n")


def handle_location(args: argparse.Namespace) -> tuple[float, float]:
    """Handle location retrieval from args or auto-detection."""
    if args.auto_speedtest and (args.latitude is None or args.longitude is None):
        lat, lon, city = get_location()
        if lat and lon:
            print(f"📍 Detected location: {city or 'Unknown'} ({lat}, {lon})")
            return lat, lon
        else:
            print("❌ Could not auto-detect location. Please provide --latitude and --longitude")
            sys.exit(1)
    else:
        return args.latitude, args.longitude


def handle_speedtest_data(args: argparse.Namespace) -> tuple[float, float, float, float, float, str]:
    """Handle speedtest data retrieval from args or auto-test."""
    if args.auto_speedtest:
        results = run_speedtest()
        if not results:
            print("❌ Speedtest failed.")
            sys.exit(1)

        return (
            results['download'],
            results['upload'],
            results['latency'],
            float(args.jitter) if args.jitter is not None else 0.0,
            float(args.packet_loss) if args.packet_loss is not None else 0.0,
            str(args.provider) if args.provider else 'Unknown'
        )

    return (
        float(args.download),
        float(args.upload),
        float(args.latency),
        float(args.jitter) if args.jitter is not None else 0.0,
        float(args.packet_loss) if args.packet_loss is not None else 0.0,
        str(args.provider) if args.provider else 'Unknown'
    )


def main():
    """Main entry point for the submission script."""
    parser = argparse.ArgumentParser(
        description='Submit speedtest data to Rural Connectivity Mapper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python submit_speedtest.py

  # Manual entry with all arguments
  python submit_speedtest.py -lat -23.5505 -lon -46.6333 \\
    -p Starlink -d 150.0 -u 20.0 -l 30.0

  # Run actual speedtest
  python submit_speedtest.py --auto-speedtest -p Starlink
        """
    )

    parser.add_argument(
        '-lat', '--latitude',
        type=float,
        help='Latitude coordinate'
    )

    parser.add_argument(
        '-lon', '--longitude',
        type=float,
        help='Longitude coordinate'
    )

    parser.add_argument(
        '-p', '--provider',
        help='Internet service provider name'
    )

    parser.add_argument(
        '-d', '--download',
        type=float,
        help='Download speed in Mbps'
    )

    parser.add_argument(
        '-u', '--upload',
        type=float,
        help='Upload speed in Mbps'
    )

    parser.add_argument(
        '-l', '--latency',
        type=float,
        help='Latency in milliseconds'
    )

    parser.add_argument(
        '-j', '--jitter',
        type=float,
        default=0.0,
        help='Jitter in milliseconds (default: 0)'
    )

    parser.add_argument(
        '--packet-loss',
        type=float,
        default=0.0,
        help='Packet loss percentage (default: 0)'
    )

    parser.add_argument(
        '--auto-speedtest',
        action='store_true',
        help='Run automatic speedtest (requires speedtest-cli)'
    )

    args = parser.parse_args()

    # If no arguments provided, use interactive mode
    if len(sys.argv) == 1:
        interactive_submit()
        return

    # Validate required arguments if not using auto speedtest
    if not args.auto_speedtest:
        required = ['latitude', 'longitude', 'provider', 'download', 'upload', 'latency']
        missing = [r for r in required if getattr(args, r) is None]

        if missing:
            print(f"❌ Error: Missing required arguments: {', '.join(missing)}")
            print("Use -h for help or run without arguments for interactive mode.")
            sys.exit(1)

    # Get location
    latitude, longitude = handle_location(args)

    if not validate_coordinates(latitude, longitude):
        print("❌ Invalid coordinates.")
        sys.exit(1)

    # Get speedtest data
    download, upload, latency, jitter, packet_loss, provider = handle_speedtest_data(args)

    # Create and save point
    speed_test = SpeedTest(
        download=download,
        upload=upload,
        latency=latency,
        jitter=jitter,
        packet_loss=packet_loss
    )

    point = ConnectivityPoint(
        latitude=latitude,
        longitude=longitude,
        provider=provider,
        speed_test=speed_test,
        timestamp=datetime.now().isoformat()
    )

    # Save to data file
    existing_data = cast(list[dict[str, object]], load_data(DATA_FILE_PATH))
    point_dict: dict[str, object] = point.to_dict()  # type: ignore[reportUnknownMemberType]
    existing_data.append(point_dict)
    save_data(DATA_FILE_PATH, existing_data)

    print(f"\n✅ Success! Data submitted (ID: {point.id})")
    print(f"   Quality Score: {point.quality_score.overall_score:.1f}/100 ({point.quality_score.rating})\n")


if __name__ == '__main__':
    main()
