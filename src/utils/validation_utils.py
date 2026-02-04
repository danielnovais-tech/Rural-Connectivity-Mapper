"""Validation utilities for data integrity checks."""

import logging
from typing import Any

from .config_utils import get_default_country, get_providers

logger = logging.getLogger(__name__)


# Known providers in Brazil
KNOWN_PROVIDERS = ["Starlink", "Viasat", "HughesNet", "Claro", "Vivo", "TIM", "Oi", "Various", "Unknown"]

# Realistic bounds for speed test values
SPEED_TEST_BOUNDS = {
    "download": (0.0, 1000.0),  # Mbps - max for satellite/fiber
    "upload": (0.0, 500.0),  # Mbps
    "latency": (0.0, 2000.0),  # ms - max for satellite
    "jitter": (0.0, 500.0),  # ms
    "packet_loss": (0.0, 100.0),  # percentage
}


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate geographic coordinates.

    Args:
        latitude: Latitude value to validate
        longitude: Longitude value to validate

    Returns:
        bool: True if coordinates are valid, False otherwise
    """
    try:
        lat = float(latitude)
        lon = float(longitude)

        if lat < -90 or lat > 90:
            logger.warning(f"Invalid latitude: {lat}. Must be between -90 and 90.")
            return False

        if lon < -180 or lon > 180:
            logger.warning(f"Invalid longitude: {lon}. Must be between -180 and 180.")
            return False

        return True
    except (ValueError, TypeError) as e:
        logger.error(f"Error validating coordinates: {e}")
        return False


def _validate_speed_field(field: str, value: Any, check_bounds: bool) -> bool:
    """Validate a single speed test field.

    Args:
        field: Name of the field being validated
        value: Value to validate
        check_bounds: If True, validate values are within realistic bounds

    Returns:
        bool: True if field is valid, False otherwise
    """
    if not isinstance(value, (int, float)):
        logger.warning(f"Field {field} must be numeric, got {type(value)}")
        return False

    if value < 0:
        logger.warning(f"Field {field} must be positive, got {value}")
        return False

    # Check realistic bounds if enabled
    if check_bounds and field in SPEED_TEST_BOUNDS:
        min_val, max_val = SPEED_TEST_BOUNDS[field]
        if value < min_val or value > max_val:
            logger.warning(f"Field {field} value {value} is outside realistic bounds [{min_val}, {max_val}]")
            return False

    return True


def _get_speed_test_data(speed_test: Any) -> dict[str, Any]:
    """Extract data from SpeedTest object or dict."""
    if hasattr(speed_test, "to_dict"):
        return speed_test.to_dict()
    return speed_test


def validate_speed_test(speed_test: Any, check_bounds: bool = True) -> bool:
    """Validate speed test measurements.

    Args:
        speed_test: SpeedTest object or dict to validate
        check_bounds: If True, validate values are within realistic bounds

    Returns:
        bool: True if speed test data is valid, False otherwise
    """
    try:
        data = _get_speed_test_data(speed_test)

        # Check required fields exist and are valid
        required_fields = ["download", "upload", "latency"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False

            if not _validate_speed_field(field, data[field], check_bounds):
                return False

        # Validate optional fields if present
        optional_fields = ["jitter", "packet_loss", "stability"]
        for field in optional_fields:
            if field in data and not _validate_speed_field(field, data[field], check_bounds):
                return False

        return True
    except Exception as e:
        logger.error(f"Error validating speed test: {e}")
        return False


def validate_provider(provider: str, country_code: str | None = None) -> bool:
    """Validate internet service provider name.

    Args:
        provider: Provider name to validate
        country_code: ISO country code for provider list (default: uses default country)

    Returns:
        bool: True if provider is known, False otherwise
    """
    if not provider or not isinstance(provider, str):
        logger.warning(f"Invalid provider: {provider}")
        return False

    # Get providers for the specified country
    if country_code is None:
        country_code = get_default_country()

    known_providers = get_providers(country_code)

    if provider not in known_providers:
        logger.warning(
            f"Unknown provider: {provider}. Known providers for {country_code}: {', '.join(known_providers)}"
        )
        return False

    return True


def _validate_numeric_field_value(field: str, value: float, row_num: int) -> tuple[bool, str]:
    """Validate a numeric field value against its constraints.

    Args:
        field: Name of the field
        value: Numeric value to validate
        row_num: Row number for error reporting

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if field == "latitude":
        if value < -90 or value > 90:
            return False, f"Row {row_num}: Invalid latitude {value} (must be between -90 and 90)"
    elif field == "longitude":
        if value < -180 or value > 180:
            return False, f"Row {row_num}: Invalid longitude {value} (must be between -180 and 180)"
    elif field in SPEED_TEST_BOUNDS:
        min_val, max_val = SPEED_TEST_BOUNDS[field]
        if value < min_val or value > max_val:
            return False, f"Row {row_num}: Invalid {field} {value} (must be between {min_val} and {max_val})"

    return True, ""


def _validate_numeric_fields(row: dict[str, str], row_num: int) -> tuple[bool, str]:
    """Validate all numeric fields in a CSV row.

    Args:
        row: Dictionary representing a CSV row
        row_num: Row number for error reporting

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    numeric_fields = ["latitude", "longitude", "download", "upload", "latency", "jitter", "packet_loss"]

    for field in numeric_fields:
        if field in row and row[field]:
            try:
                value = float(row[field])
                is_valid, error_msg = _validate_numeric_field_value(field, value, row_num)
                if not is_valid:
                    return False, error_msg
            except (ValueError, TypeError) as e:
                return False, (f"Row {row_num}: Invalid numeric value for {field}: {row[field]} (error: {e})")

    return True, ""


def validate_csv_row(row: dict[str, str], row_num: int) -> tuple[bool, str]:
    """Validate a CSV row for required fields and data types.

    Args:
        row: Dictionary representing a CSV row
        row_num: Row number for error reporting

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    required_fields = ["latitude", "longitude", "provider", "download", "upload", "latency"]

    # Check for missing fields
    missing_fields = [field for field in required_fields if field not in row or not row[field]]
    if missing_fields:
        return False, f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}"

    # Validate numeric fields
    is_valid, error_msg = _validate_numeric_fields(row, row_num)
    if not is_valid:
        return False, error_msg

    # Validate provider
    if row["provider"] not in KNOWN_PROVIDERS:
        logger.warning(f"Row {row_num}: Unknown provider '{row['provider']}' will be accepted but logged")

    return True, ""
