"""Configuration utilities for country-specific settings."""

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache for loaded configuration
_config_cache: dict | None = None


def load_country_config(config_path: str | Path | None = None) -> dict:
    """Load country configuration from JSON file.

    Args:
        config_path: Optional path to config file. Uses default if None.

    Returns:
        Dict: Configuration dictionary with country settings
    """
    global _config_cache

    original_config_path = config_path

    # Return cached config if available
    if _config_cache is not None and original_config_path is None:
        return _config_cache

    if config_path is None:
        # Use default config path
        # When frozen by PyInstaller, sys._MEIPASS points to the extracted bundle root.
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent.parent))
        config_path = base_dir / "config" / "countries.json"

    config_file = config_path if isinstance(config_path, Path) else Path(config_path)

    try:
        with open(config_file, encoding="utf-8") as f:
            config = json.load(f)

        # Cache the config
        if original_config_path is None or str(config_file).endswith("countries.json"):
            _config_cache = config

        logger.debug(f"Loaded country configuration from {config_file}")
        return config

    except FileNotFoundError:
        logger.error(f"Country configuration file not found: {config_file}")
        # Return minimal default config
        return {
            "countries": {
                "BR": {
                    "name": "Brazil",
                    "language": "pt",
                    "default_center": {"latitude": -15.7801, "longitude": -47.9292},
                    "zoom_level": 4,
                    "providers": ["Starlink", "Various", "Unknown"],
                }
            },
            "default_country": "BR",
        }

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing country configuration: {e}")
        raise


def get_country_info(country_code: str, config: dict | None = None) -> dict:
    """Get configuration for a specific country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'BR', 'US')
        config: Optional configuration dict. Loads default if None.

    Returns:
        Dict: Country-specific configuration

    Raises:
        ValueError: If country code is not found in configuration
    """
    if config is None:
        config = load_country_config()

    country_code = country_code.upper()

    if country_code not in config.get("countries", {}):
        available = ", ".join(config.get("countries", {}).keys())
        raise ValueError(f"Country code '{country_code}' not found in configuration. Available countries: {available}")

    return config["countries"][country_code]


def get_default_country(config: dict | None = None) -> str:
    """Get the default country code from configuration.

    Args:
        config: Optional configuration dict. Loads default if None.

    Returns:
        str: Default country code
    """
    if config is None:
        config = load_country_config()

    return config.get("default_country", "BR")


def get_providers(country_code: str, config: dict | None = None) -> list[str]:
    """Get list of providers for a specific country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code
        config: Optional configuration dict. Loads default if None.

    Returns:
        List[str]: List of provider names
    """
    country_info = get_country_info(country_code, config)
    return country_info.get("providers", ["Unknown"])


def get_language(country_code: str, config: dict | None = None) -> str:
    """Get the language code for a specific country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code
        config: Optional configuration dict. Loads default if None.

    Returns:
        str: Language code (e.g., 'en', 'pt', 'es')
    """
    country_info = get_country_info(country_code, config)
    return country_info.get("language", "en")


def get_map_center(country_code: str, config: dict | None = None) -> tuple:
    """Get the default map center coordinates for a specific country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code
        config: Optional configuration dict. Loads default if None.

    Returns:
        tuple: (latitude, longitude) for map center
    """
    country_info = get_country_info(country_code, config)
    center = country_info.get("default_center", {"latitude": 0, "longitude": 0})
    return (center["latitude"], center["longitude"])


def get_zoom_level(country_code: str, config: dict | None = None) -> int:
    """Get the default zoom level for a specific country's map.

    Args:
        country_code: ISO 3166-1 alpha-2 country code
        config: Optional configuration dict. Loads default if None.

    Returns:
        int: Default zoom level
    """
    country_info = get_country_info(country_code, config)
    return country_info.get("zoom_level", 4)


def list_available_countries(config: dict | None = None) -> list[str]:
    """Get list of all available country codes in configuration.

    Args:
        config: Optional configuration dict. Loads default if None.

    Returns:
        List[str]: List of country codes
    """
    if config is None:
        config = load_country_config()

    return list(config.get("countries", {}).keys())
