#!/usr/bin/env python3
"""
Multi-Country Demo for Rural Connectivity Mapper 2026
Demonstrates the new country-specific configuration features.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import ConnectivityPoint, SpeedTest
from src.utils import (
    get_country_info,
    get_language,
    get_map_center,
    get_providers,
    get_zoom_level,
    list_available_countries,
)


def main():
    """Run multi-country demonstration."""
    print("=" * 80)
    print("RURAL CONNECTIVITY MAPPER 2026 - MULTI-COUNTRY DEMO")
    print("=" * 80)
    print()

    # List available countries
    print("📍 Available Countries:")
    print("-" * 80)
    countries = list_available_countries()
    for code in sorted(countries):
        info = get_country_info(code)
        print(f"  {code}: {info['name']:<20} (Language: {info['language']})")
    print()

    # Show configuration for a few countries
    demo_countries = ["BR", "US", "CA", "GB", "AU"]

    print("🌍 Country-Specific Configurations:")
    print("-" * 80)
    for code in demo_countries:
        info = get_country_info(code)
        center = get_map_center(code)
        zoom = get_zoom_level(code)
        providers = get_providers(code)
        language = get_language(code)

        print(f"\n{code} - {info['name']}:")
        print(f"  Language: {language}")
        print(f"  Map Center: ({center[0]:.4f}, {center[1]:.4f})")
        print(f"  Zoom Level: {zoom}")
        print(f"  Providers: {', '.join(providers[:5])}...")
    print()

    # Create sample connectivity points for different countries
    print("📊 Sample Connectivity Points:")
    print("-" * 80)

    # Brazil sample
    br_speed = SpeedTest(download=165.4, upload=22.8, latency=28.5, jitter=3.2, packet_loss=0.1)
    br_point = ConnectivityPoint(
        latitude=-15.7801, longitude=-47.9292, provider="Starlink", speed_test=br_speed, country="BR"
    )
    print("\nBrazil (Brasília):")
    print(f"  Provider: {br_point.provider}")
    print(f"  Quality Score: {br_point.quality_score.overall_score:.1f}/100 ({br_point.quality_score.rating})")
    print(f"  Download: {br_point.speed_test.download} Mbps")
    print(f"  Country: {br_point.country}")

    # US sample
    us_speed = SpeedTest(download=180.5, upload=25.3, latency=22.1, jitter=2.8, packet_loss=0.05)
    us_point = ConnectivityPoint(
        latitude=30.2672, longitude=-97.7431, provider="Starlink", speed_test=us_speed, country="US"
    )
    print("\nUnited States (Austin):")
    print(f"  Provider: {us_point.provider}")
    print(f"  Quality Score: {us_point.quality_score.overall_score:.1f}/100 ({us_point.quality_score.rating})")
    print(f"  Download: {us_point.speed_test.download} Mbps")
    print(f"  Country: {us_point.country}")

    # UK sample
    uk_speed = SpeedTest(download=145.2, upload=19.5, latency=32.4, jitter=4.1, packet_loss=0.2)
    uk_point = ConnectivityPoint(
        latitude=51.5074,
        longitude=-0.1278,
        provider="BT",
        speed_test=uk_speed,
        country="GB"
    )
    print(f"\nUnited Kingdom (London):")
    print(f"  Provider: {uk_point.provider}")
    print(f"  Quality Score: {uk_point.quality_score.overall_score:.1f}/100 ({uk_point.quality_score.rating})")
    print(f"  Download: {uk_point.speed_test.download} Mbps")
    print(f"  Country: {uk_point.country}")

    print()
    print("=" * 80)
    print("✅ Multi-Country Support Successfully Demonstrated!")
    print("=" * 80)
    print()
    print("Try these commands:")
    print("  • python main.py --list-countries")
    print("  • python main.py --country US --importar src/data/sample_data_us.csv --map")
    print("  • python main.py --country BR --analyze --relatorio json")
    print()


if __name__ == "__main__":
    main()
