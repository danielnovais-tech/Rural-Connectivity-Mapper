"""Geocoding utilities for coordinate and address conversion."""

import logging
import time
from typing import Any, cast

from geopy.exc import GeocoderQuotaExceeded, GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim
from geopy.location import Location

logger = logging.getLogger(__name__)

# Initialize geocoder with user agent
geolocator = Nominatim(user_agent="rural-connectivity-mapper-2026")

# Rate limiting configuration (Nominatim allows 1 request per second)
RATE_LIMIT_DELAY = 1.0  # seconds between requests
_last_request_time = 0


def _wait_for_rate_limit():
    """Ensure we respect the rate limit by waiting if necessary."""
    global _last_request_time
    current_time = time.time()
    time_since_last_request = current_time - _last_request_time

    if time_since_last_request < RATE_LIMIT_DELAY:
        sleep_time = RATE_LIMIT_DELAY - time_since_last_request
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)

    _last_request_time = time.time()


def _validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate coordinate values.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        lat = float(latitude)
        lon = float(longitude)

        if not (-90 <= lat <= 90):
            logger.error(f"Invalid latitude: {lat} (must be between -90 and 90)")
            return False

        if not (-180 <= lon <= 180):
            logger.error(f"Invalid longitude: {lon} (must be between -180 and 180)")
            return False

        return True
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid coordinate values: {e}")
        return False


def geocode_coordinates(latitude: float, longitude: float, timeout: Any = 10, max_retries: int = 3) -> str | None:
    """Convert coordinates to a human-readable address (reverse geocoding).

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        Optional[str]: Address string if successful, None otherwise
    """
    if not _validate_coordinates(latitude, longitude):
        return None

    coords = f"{latitude}, {longitude}"

    for attempt in range(max_retries):
        try:
            _wait_for_rate_limit()

            location = cast(Location | None, geolocator.reverse(coords, timeout=timeout, exactly_one=True))

            if location and location.address:
                logger.info(f"Reverse geocoded {coords} to: {location.address}")
                return location.address
            else:
                logger.warning(f"No address found for coordinates: {coords}")
                return None

        except GeocoderTimedOut:
            if attempt < max_retries - 1:
                logger.warning(f"Geocoding timeout for {coords}, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2**attempt)  # Exponential backoff
                continue
            else:
                logger.error(f"Geocoding timeout for {coords} after {max_retries} attempts")
                return None

        except GeocoderQuotaExceeded:
            logger.error(f"Geocoding quota exceeded for {coords}")
            return None

        except (GeocoderServiceError, GeocoderUnavailable) as e:
            logger.error(f"Geocoding service error for {coords}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error during reverse geocoding {coords}: {e}")
            return None

    return None


def geocode_address(address: str, timeout: Any = 10, max_retries: int = 3) -> tuple[float, float] | None:
    """Convert an address to coordinates (forward geocoding).

    Args:
        address: Address string to geocode
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        Optional[Tuple[float, float]]: (latitude, longitude) if successful, None otherwise
    """
    if not address or not address.strip():
        logger.error("Empty address provided for geocoding")
        return None

    address = address.strip()

    for attempt in range(max_retries):
        try:
            _wait_for_rate_limit()

            location = cast(Location | None, geolocator.geocode(address, timeout=timeout, exactly_one=True))

            if location:
                coords = (location.latitude, location.longitude)
                logger.info(f"Geocoded '{address}' to: {coords}")
                return coords
            else:
                logger.warning(f"No coordinates found for address: {address}")
                return None

        except GeocoderTimedOut:
            if attempt < max_retries - 1:
                logger.warning(f"Geocoding timeout for '{address}', retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2**attempt)  # Exponential backoff
                continue
            else:
                logger.error(f"Geocoding timeout for '{address}' after {max_retries} attempts")
                return None

        except GeocoderQuotaExceeded:
            logger.error(f"Geocoding quota exceeded for '{address}'")
            return None

        except (GeocoderServiceError, GeocoderUnavailable) as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Geocoding service unavailable for '{address}', retrying... (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(2**attempt)
                continue
            logger.error(f"Geocoding service error for '{address}': {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error during geocoding '{address}': {e}")
            return None

    return None
