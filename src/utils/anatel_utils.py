"""ANATEL (Agência Nacional de Telecomunicações) data integration utilities.

This module provides utilities to fetch real connectivity and telecom data from ANATEL,
the Brazilian National Telecommunications Agency.
"""

import json
import logging
import os

import requests
import urllib3

# Disable SSL warnings when verify=False is used (for testing only)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# ANATEL Open Data API endpoints
ANATEL_BASE_URL = "https://informacoes.anatel.gov.br/paineis/acessos"
ANATEL_ENDPOINTS = {
    'banda_larga': '/dados-abertos/banda-larga-fixa',
    'telefonia_movel': '/dados-abertos/telefonia-movel',
    'cobertura': '/dados-abertos/cobertura-movel'
}

# ANATEL CKAN API endpoints for backhaul data
ANATEL_CKAN_BASE_URL = "https://dadosabertos.anatel.gov.br/api/3/action"

# Backup data file path
ANATEL_BACKUP_BACKHAUL_FILE = "data/backup/anatel_backhaul_sample.json"


def fetch_anatel_broadband_data(state: str | None = None, year: int | None = 2026) -> list[dict]:
    """Fetch broadband coverage data from ANATEL.

    Args:
        state: Optional Brazilian state code (e.g., 'SP', 'RJ')
        year: Year for data (default: 2026)

    Returns:
        List[Dict]: Broadband data points with provider and coverage info
    """
    logger.info(f"Fetching ANATEL broadband data for state={state}, year={year}")

    # Mock data for demonstration (real API would be called here)
    # In production, this would call the actual ANATEL API
    mock_data = [
        {
            'state': 'SP',
            'municipality': 'São Paulo',
            'provider': 'Claro',
            'technology': 'Fibra',
            'subscribers': 150000,
            'avg_speed_mbps': 100.0,
            'coverage_percentage': 85.5
        },
        {
            'state': 'RJ',
            'municipality': 'Rio de Janeiro',
            'provider': 'Vivo',
            'technology': 'Fibra',
            'subscribers': 120000,
            'avg_speed_mbps': 90.0,
            'coverage_percentage': 80.0
        },
        {
            'state': 'MG',
            'municipality': 'Belo Horizonte',
            'provider': 'Oi',
            'technology': 'ADSL',
            'subscribers': 80000,
            'avg_speed_mbps': 35.0,
            'coverage_percentage': 70.0
        },
        {
            'state': 'BA',
            'municipality': 'Salvador',
            'provider': 'TIM',
            'technology': '4G',
            'subscribers': 60000,
            'avg_speed_mbps': 25.0,
            'coverage_percentage': 60.0
        },
        {
            'state': 'CE',
            'municipality': 'Fortaleza',
            'provider': 'Viasat',
            'technology': 'Satélite',
            'subscribers': 15000,
            'avg_speed_mbps': 50.0,
            'coverage_percentage': 40.0
        }
    ]

    # Filter by state if specified
    if state:
        mock_data = [d for d in mock_data if d['state'] == state.upper()]

    logger.info(f"Retrieved {len(mock_data)} ANATEL broadband records")
    return mock_data


def fetch_anatel_mobile_data(state: str | None = None) -> list[dict]:
    """Fetch mobile coverage data from ANATEL.

    Args:
        state: Optional Brazilian state code (e.g., 'SP', 'RJ')

    Returns:
        List[Dict]: Mobile coverage data points
    """
    logger.info(f"Fetching ANATEL mobile data for state={state}")

    # Mock data for demonstration
    mock_data = [
        {
            'state': 'SP',
            'municipality': 'São Paulo',
            'provider': 'Claro',
            'technology': '5G',
            'coverage_4g_percentage': 95.0,
            'coverage_5g_percentage': 45.0,
            'avg_speed_mbps': 85.0
        },
        {
            'state': 'RJ',
            'municipality': 'Rio de Janeiro',
            'provider': 'Vivo',
            'technology': '5G',
            'coverage_4g_percentage': 93.0,
            'coverage_5g_percentage': 40.0,
            'avg_speed_mbps': 80.0
        },
        {
            'state': 'DF',
            'municipality': 'Brasília',
            'provider': 'TIM',
            'technology': '5G',
            'coverage_4g_percentage': 90.0,
            'coverage_5g_percentage': 35.0,
            'avg_speed_mbps': 75.0
        }
    ]

    # Filter by state if specified
    if state:
        mock_data = [d for d in mock_data if d['state'] == state.upper()]

    logger.info(f"Retrieved {len(mock_data)} ANATEL mobile records")
    return mock_data


def get_anatel_provider_stats(provider: str | None = None) -> dict:
    """Get aggregated statistics for telecom providers from ANATEL.

    Args:
        provider: Optional provider name to filter

    Returns:
        Dict: Provider statistics including market share and coverage
    """
    logger.info(f"Fetching ANATEL provider stats for provider={provider}")

    # Mock aggregated data
    all_stats = {
        'Claro': {
            'market_share': 28.5,
            'total_subscribers': 4500000,
            'avg_speed_mbps': 95.0,
            'coverage_municipalities': 3200,
            'technology': ['Fibra', '5G', '4G']
        },
        'Vivo': {
            'market_share': 26.0,
            'total_subscribers': 4100000,
            'avg_speed_mbps': 90.0,
            'coverage_municipalities': 3100,
            'technology': ['Fibra', '5G', '4G']
        },
        'TIM': {
            'market_share': 22.0,
            'total_subscribers': 3400000,
            'avg_speed_mbps': 85.0,
            'coverage_municipalities': 2900,
            'technology': ['Fibra', '5G', '4G']
        },
        'Oi': {
            'market_share': 15.0,
            'total_subscribers': 2300000,
            'avg_speed_mbps': 60.0,
            'coverage_municipalities': 2500,
            'technology': ['ADSL', '4G']
        },
        'Starlink': {
            'market_share': 3.5,
            'total_subscribers': 550000,
            'avg_speed_mbps': 150.0,
            'coverage_municipalities': 5570,  # All municipalities
            'technology': ['Satélite']
        }
    }

    if provider:
        return {provider: all_stats.get(provider, {})}

    logger.info(f"Retrieved stats for {len(all_stats)} providers")
    return all_stats


def convert_anatel_to_connectivity_points(anatel_data: list[dict]) -> list[dict]:
    """Convert ANATEL data format to ConnectivityPoint format.

    Args:
        anatel_data: List of ANATEL data records

    Returns:
        List[Dict]: Data in ConnectivityPoint-compatible format
    """
    logger.info(f"Converting {len(anatel_data)} ANATEL records to connectivity points")

    # Brazilian state capitals coordinates (for mapping)
    coordinates = {
        'São Paulo': (-23.5505, -46.6333),
        'Rio de Janeiro': (-22.9068, -43.1729),
        'Belo Horizonte': (-19.9167, -43.9345),
        'Salvador': (-12.9714, -38.5014),
        'Fortaleza': (-3.7172, -38.5433),
        'Brasília': (-15.7801, -47.9292)
    }

    connectivity_points = []

    for record in anatel_data:
        municipality = record.get('municipality')
        coords = coordinates.get(municipality, (0.0, 0.0))

        point = {
            'latitude': coords[0],
            'longitude': coords[1],
            'provider': record.get('provider', 'Unknown'),
            'speed_test': {
                'download': record.get('avg_speed_mbps', 0.0),
                'upload': record.get('avg_speed_mbps', 0.0) * 0.15,  # Estimate upload
                'latency': 45.0,  # Default latency
                'jitter': 8.0,
                'packet_loss': 1.0
            },
            'metadata': {
                'source': 'ANATEL',
                'state': record.get('state'),
                'municipality': municipality,
                'technology': record.get('technology'),
                'coverage_percentage': record.get('coverage_percentage', 0.0),
                'subscribers': record.get('subscribers', 0)
            }
        }

        connectivity_points.append(point)

    logger.info(f"Converted {len(connectivity_points)} connectivity points")
    return connectivity_points


def load_anatel_backhaul_backup(path: str = ANATEL_BACKUP_BACKHAUL_FILE) -> list[dict]:
    """Load ANATEL backhaul data from backup JSON file.

    Args:
        path: Path to the backup JSON file (default: ANATEL_BACKUP_BACKHAUL_FILE)

    Returns:
        List[Dict]: List of backhaul data records, empty list if file missing or invalid
    """
    logger.info(f"Loading ANATEL backhaul backup from {path}")

    # Check if file exists
    if not os.path.exists(path):
        logger.warning(f"Backup file not found: {path}")
        return []

    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        # Validate top-level structure
        if not isinstance(data, dict):
            logger.warning(f"Invalid backup file structure: expected dict, got {type(data)}")
            return []

        if 'data' not in data:
            logger.warning("Backup file missing 'data' key")
            return []

        records = data['data']
        if not isinstance(records, list):
            logger.warning(f"Invalid data structure: expected list, got {type(records)}")
            return []

        # Validate required fields in each record
        required_fields = [
            'uf',
            'municipio',
            'latitude',
            'longitude',
            'technology',
            'capacity_mbps',
            'provider',
            'timestamp_utc',
            'id',
            'source',
        ]

        valid_records = []
        for idx, record in enumerate(records):
            if not isinstance(record, dict):
                logger.warning(f"Record {idx} is not a dict, skipping")
                continue

            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                logger.warning(f"Record {idx} missing required fields: {missing_fields}, skipping")
                continue

            valid_records.append(record)

        logger.info(f"Loaded {len(valid_records)} valid backhaul records from backup")
        return valid_records

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from {path}: {e}")
        return []
    except Exception as e:
        logger.warning(f"Error loading backup file {path}: {e}")
        return []


def fetch_anatel_backhaul_data(limit: int = 1000, use_backup_on_failure: bool = True) -> list[dict]:
    """Fetch ANATEL backhaul infrastructure data.

    This function attempts to fetch backhaul data from the ANATEL CKAN API.
    If the API is not configured or fails, it falls back to the backup sample data.

    Args:
        limit: Maximum number of records to return (default: 1000)
        use_backup_on_failure: Whether to use backup data if API fails (default: True)

    Returns:
        List[Dict]: List of backhaul data records
    """
    logger.info(f"Fetching ANATEL backhaul data (limit={limit})")

    # Placeholder for future API implementation
    # TODO: Configure ANATEL backhaul resource_id when available
    # Future implementation will call: {ANATEL_CKAN_BASE_URL}/datastore_search
    resource_id = None

    if resource_id:
        try:
            # Attempt to fetch from CKAN API with timeout and SSL handling
            url = f"{ANATEL_CKAN_BASE_URL}/datastore_search"
            params = {
                'resource_id': resource_id,
                'limit': limit
            }

            logger.info(f"Attempting to fetch from CKAN API: {url}")
            response = requests.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()

            data = response.json()

            # Validate response structure
            if 'success' not in data or not data['success']:
                logger.warning("CKAN API returned unsuccessful response")
                raise ValueError("API returned unsuccessful response")

            if 'result' not in data or 'records' not in data['result']:
                logger.warning("CKAN API response missing expected data structure")
                raise ValueError("API response missing expected structure")

            records = data['result']['records']
            logger.info(f"Successfully fetched {len(records)} records from CKAN API")
            return records[:limit]

        except requests.exceptions.Timeout as e:
            logger.warning(f"CKAN API timeout (30s exceeded): {e}")
            if use_backup_on_failure:
                logger.info("Falling back to backup data due to timeout")
                return load_anatel_backhaul_backup()[:limit]
            return []
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL certificate error with CKAN API: {e}")
            if use_backup_on_failure:
                logger.info("Falling back to backup data due to SSL error")
                return load_anatel_backhaul_backup()[:limit]
            return []
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            logger.warning(f"Failed to fetch from ANATEL CKAN API: {e}")
            if use_backup_on_failure:
                logger.info("Falling back to backup data due to API inconsistency")
                return load_anatel_backhaul_backup()[:limit]
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching from CKAN API: {e}")
            if use_backup_on_failure:
                logger.info("Falling back to backup data")
                return load_anatel_backhaul_backup()[:limit]
            return []
    else:
        # No resource_id configured, use backup directly
        logger.info("No ANATEL API resource_id configured, using backup data")
        return load_anatel_backhaul_backup()[:limit]

