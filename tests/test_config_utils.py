"""Tests for configuration utilities."""

import pytest

from src.utils.config_utils import (
    get_country_info,
    get_default_country,
    get_language,
    get_map_center,
    get_providers,
    get_zoom_level,
    list_available_countries,
    load_country_config,
)


def test_load_country_config():
    """Test loading country configuration."""
    config = load_country_config()

    assert "countries" in config
    assert "default_country" in config
    assert isinstance(config["countries"], dict)
    assert len(config["countries"]) > 0


def test_get_default_country():
    """Test getting default country code."""
    default = get_default_country()

    assert isinstance(default, str)
    assert len(default) == 2
    assert default.isupper()


def test_get_country_info():
    """Test getting country information."""
    # Test Brazil
    br_info = get_country_info("BR")

    assert "name" in br_info
    assert "language" in br_info
    assert "default_center" in br_info
    assert "providers" in br_info
    assert br_info["name"] == "Brazil"
    assert br_info["language"] == "pt"

    # Test US
    us_info = get_country_info("US")

    assert us_info["name"] == "United States"
    assert us_info["language"] == "en"


def test_get_country_info_invalid():
    """Test getting country information with invalid code."""
    with pytest.raises(ValueError) as exc_info:
        get_country_info("XX")

    assert "not found" in str(exc_info.value).lower()


def test_get_providers():
    """Test getting providers for a country."""
    # Test Brazil
    br_providers = get_providers("BR")

    assert isinstance(br_providers, list)
    assert len(br_providers) > 0
    assert "Starlink" in br_providers
    assert "Unknown" in br_providers

    # Test US
    us_providers = get_providers("US")

    assert isinstance(us_providers, list)
    assert "Verizon" in us_providers
    assert "AT&T" in us_providers


def test_get_language():
    """Test getting language for a country."""
    assert get_language("BR") == "pt"
    assert get_language("US") == "en"
    assert get_language("CA") == "en"
    assert get_language("DE") == "de"
    assert get_language("FR") == "fr"


def test_get_map_center():
    """Test getting map center coordinates."""
    br_center = get_map_center("BR")

    assert isinstance(br_center, tuple)
    assert len(br_center) == 2
    assert isinstance(br_center[0], (int, float))
    assert isinstance(br_center[1], (int, float))
    # Brazil should be in southern hemisphere
    assert br_center[0] < 0

    us_center = get_map_center("US")
    # US should be in northern hemisphere
    assert us_center[0] > 0


def test_get_zoom_level():
    """Test getting zoom level for a country."""
    br_zoom = get_zoom_level("BR")

    assert isinstance(br_zoom, int)
    assert br_zoom > 0
    assert br_zoom <= 20


def test_list_available_countries():
    """Test listing available countries."""
    countries = list_available_countries()

    assert isinstance(countries, list)
    assert len(countries) > 0
    assert "BR" in countries
    assert "US" in countries
    assert all(len(code) == 2 for code in countries)


def test_case_insensitive_country_code():
    """Test that country codes work case-insensitively."""
    # Should work with lowercase
    info_lower = get_country_info("br")
    info_upper = get_country_info("BR")

    assert info_lower == info_upper
