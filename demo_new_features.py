#!/usr/bin/env python3
"""Demo script to test new features: ANATEL, IBGE, Starlink, and LATAM support."""

import logging

from src.utils import (
    check_starlink_availability,
    fetch_anatel_broadband_data,
    fetch_anatel_mobile_data,
    get_anatel_provider_stats,
    get_country_config,
    get_ibge_statistics_summary,
    get_latam_summary,
    get_rural_areas_needing_connectivity,
    get_starlink_coverage_map,
    get_starlink_service_plans,
    get_supported_countries,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_anatel_integration():
    """Test ANATEL data integration."""
    print("\n" + "=" * 80)
    print("ANATEL INTEGRATION TEST")
    print("=" * 80)

    # Test broadband data
    broadband = fetch_anatel_broadband_data(state="SP")
    print(f"\n✓ Fetched {len(broadband)} ANATEL broadband records for São Paulo")
    if broadband:
        sample = broadband[0]
        print(f"  Sample: {sample['municipality']} - {sample['provider']} - {sample['avg_speed_mbps']} Mbps")

    # Test mobile data
    mobile = fetch_anatel_mobile_data()
    print(f"\n✓ Fetched {len(mobile)} ANATEL mobile coverage records")

    # Test provider stats
    stats = get_anatel_provider_stats()
    print(f"\n✓ Retrieved stats for {len(stats)} providers")
    print(f"  Starlink market share: {stats['Starlink']['market_share']}%")
    print(f"  Starlink avg speed: {stats['Starlink']['avg_speed_mbps']} Mbps")


def test_ibge_integration():
    """Test IBGE data integration."""
    print("\n" + "=" * 80)
    print("IBGE INTEGRATION TEST")
    print("=" * 80)

    # Test rural areas
    priority_areas = get_rural_areas_needing_connectivity()
    print(f"\n✓ Found {len(priority_areas)} priority rural areas")
    if priority_areas:
        top_area = priority_areas[0]
        print(f"  Top priority: {top_area['municipality']}, {top_area['state']}")
        print(f"    Rural population: {top_area['rural_population']:,}")
        print(f"    Internet coverage: {top_area['internet_coverage']}%")
        print(f"    Priority score: {top_area['priority_score']}")

    # Test statistics summary
    summary = get_ibge_statistics_summary()
    print("\n✓ IBGE Statistics Summary:")
    print(f"  Total municipalities: {summary['total_municipalities']:,}")
    print(f"  Rural population: {summary['rural_population']:,}")
    print(f"  Rural internet access: {summary['rural_households_with_internet']}%")
    print(f"  Digital divide: {summary['urban_rural_digital_divide_percentage']}%")


def test_starlink_integration():
    """Test Starlink API integration."""
    print("\n" + "=" * 80)
    print("STARLINK INTEGRATION TEST")
    print("=" * 80)

    # Test availability check
    lat, lon = -15.7801, -47.9292  # Brasília
    availability = check_starlink_availability(lat, lon)
    print(f"\n✓ Starlink availability at Brasília ({lat}, {lon}):")
    print(f"  Service available: {availability['service_available']}")
    print(f"  Status: {availability['status']}")
    print(f"  Expected speeds: {availability['expected_speeds']['download_mbps']}")
    print(f"  Latency: {availability['expected_speeds']['latency_ms']}")

    # Test service plans
    plans = get_starlink_service_plans()
    print(f"\n✓ Retrieved {len(plans)} Starlink service plans:")
    for plan in plans:
        print(f"  - {plan['name']}: R${plan['price_brl_monthly']}/month")
        print(f"    Speed: {plan['download_speed']}, Latency: {plan['latency']}")

    # Test coverage map
    coverage = get_starlink_coverage_map("BR")
    print(f"\n✓ Starlink coverage in {coverage['country_name']}:")
    print(f"  Coverage: {coverage['coverage_percentage']}%")
    print(f"  Active users: {coverage['active_users']:,}")
    print(f"  Ground stations: {coverage['ground_stations']}")


def test_latam_support():
    """Test LATAM country support."""
    print("\n" + "=" * 80)
    print("LATAM COUNTRY SUPPORT TEST")
    print("=" * 80)

    # Test supported countries
    countries = get_supported_countries()
    print(f"\n✓ Supported countries: {len(countries)}")
    print(f"  {', '.join(countries)}")

    # Test country configs
    print("\n✓ Country configurations:")
    for code in ["BR", "AR", "CL", "MX"]:
        config = get_country_config(code)
        print(f"  {config.name} ({code}):")
        print(f"    Regulator: {config.telecom_regulator}")
        print(f"    Providers: {len(config.supported_providers)}")
        print(f"    Currency: {config.currency}")

    # Test LATAM summary
    summary = get_latam_summary()
    print("\n✓ LATAM Summary:")
    print(f"  Total countries: {summary['total_countries']}")
    print(f"  Unique providers: {summary['unique_providers_count']}")
    print(f"  Languages: {', '.join(summary['languages'])}")
    print(f"  Top providers: {', '.join(summary['total_providers'][:5])}")


def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("RURAL CONNECTIVITY MAPPER 2026 - NEW FEATURES DEMO")
    print("Testing: ANATEL, IBGE, Starlink API, and LATAM Support")
    print("=" * 80)

    try:
        test_anatel_integration()
        test_ibge_integration()
        test_starlink_integration()
        test_latam_support()

        print("\n" + "=" * 80)
        print("✓ ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNext Steps:")
        print("  1. Run the Streamlit dashboard: streamlit run dashboard.py")
        print("  2. Try the CLI with: python main.py --help")
        print("  3. Run the test suite: pytest tests/ -v")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
