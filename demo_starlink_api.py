"""Demo script showcasing the Starlink API module for provider comparison.

This script demonstrates how to use the starlink_api module to:
1. Get coverage data for a location
2. Get performance metrics
3. Compare Starlink with competitors (Viasat, HughesNet)
"""

from src.utils.starlink_api import compare_with_competitors, get_coverage_data, get_performance_metrics


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_starlink_api():
    """Run demonstration of Starlink API module."""

    print_section("STARLINK API MODULE DEMONSTRATION")

    # Test locations
    locations = [
        {"name": "Brasília, Brazil", "lat": -15.7801, "lon": -47.9292},
        {"name": "São Paulo, Brazil", "lat": -23.5505, "lon": -46.6333},
        {"name": "Salvador, Brazil", "lat": -12.9714, "lon": -38.5014},
    ]

    for location in locations:
        print_section(f"Location: {location['name']}")
        lat, lon = location["lat"], location["lon"]

        print(f"\nCoordinates: ({lat}, {lon})")

        # 1. Get coverage data
        print("\n1️⃣  Coverage Information:")
        coverage = get_coverage_data(lat, lon)
        print(f"   ✓ Service Available: {coverage.get('available')}")
        print(f"   ✓ Service Tier: {coverage.get('service_tier')}")
        print(f"   ✓ Expected Download: {coverage.get('expected_download_mbps')} Mbps")
        print(f"   ✓ Expected Latency: {coverage.get('expected_latency_ms')} ms")
        print(f"   ✓ Monthly Cost: ${coverage.get('monthly_cost_usd')}")

        # 2. Get performance metrics
        print("\n2️⃣  Performance Metrics:")
        performance = get_performance_metrics(lat, lon)
        print(f"   ✓ Download Speed: {performance.get('download_mbps')} Mbps")
        print(f"   ✓ Upload Speed: {performance.get('upload_mbps')} Mbps")
        print(f"   ✓ Latency: {performance.get('latency_ms')} ms")
        print(f"   ✓ Uptime: {performance.get('uptime_percent')}%")

        # 3. Provider comparison
        print("\n3️⃣  Provider Comparison:")
        comparison = compare_with_competitors(lat, lon)

        print("\n   Provider Rankings:")
        providers = comparison["providers"]
        sorted_providers = sorted(providers.items(), key=lambda x: x[1].get("quality_score", 0), reverse=True)

        for i, (provider, data) in enumerate(sorted_providers, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            print(f"   {emoji} {provider.upper()}")
            print(f"      • Quality Score: {data.get('quality_score')}/100")
            print(f"      • Download: {data.get('download_mbps')} Mbps")
            print(f"      • Upload: {data.get('upload_mbps')} Mbps")
            print(f"      • Latency: {data.get('latency_ms')} ms")
            print(f"      • Monthly Cost: ${data.get('monthly_cost_usd')}")

        print(f"\n   💡 Recommendation: {comparison['recommendation']['best_provider'].upper()}")
        print(f"      Reason: {comparison['recommendation']['reason']}")

    print_section("DEMONSTRATION COMPLETE")
    print("\n✨ The Starlink API module successfully:")
    print("   • Fetches coverage, performance, and availability data")
    print("   • Falls back to simulated data when API is unavailable")
    print("   • Compares Starlink with Viasat and HughesNet")
    print("   • Provides quality scores and recommendations")
    print("\n📝 Note: Currently using simulated data as Starlink API is not publicly accessible.")
    print("   Replace API endpoints with real ones in production environment.\n")


if __name__ == "__main__":
    demo_starlink_api()
