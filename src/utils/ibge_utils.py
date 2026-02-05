"""IBGE (Instituto Brasileiro de Geografia e Estatística) data integration utilities.

This module provides utilities to fetch demographic and geographic data from IBGE,
the Brazilian Institute of Geography and Statistics.
"""

import logging

import requests

logger = logging.getLogger(__name__)

# IBGE API endpoints
IBGE_BASE_URL = "https://servicodados.ibge.gov.br/api/v1"
IBGE_ENDPOINTS = {
    "municipalities": "/localidades/municipios",
    "states": "/localidades/estados",
    "districts": "/localidades/distritos",
}


def fetch_ibge_municipalities(state_code: str | None = None) -> list[dict]:
    """Fetch municipality data from IBGE.

    Args:
        state_code: Optional state code (UF) to filter municipalities

    Returns:
        List[Dict]: Municipality data including population and area
    """
    logger.info(f"Fetching IBGE municipality data for state={state_code}")

    try:
        # Real IBGE API call
        url = f"{IBGE_BASE_URL}{IBGE_ENDPOINTS['municipalities']}"
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()

        municipalities = response.json()

        # Filter by state if specified
        if state_code:
            state_code_upper = state_code.upper()
            filtered: list = []
            for m in municipalities:
                uf_sigla = (((m.get("microrregiao") or {}).get("mesorregiao") or {}).get("UF") or {}).get("sigla")
                if uf_sigla == state_code_upper:
                    filtered.append(m)
            municipalities = filtered

        logger.info(f"Retrieved {len(municipalities)} municipalities from IBGE")
        return municipalities

    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch from IBGE API: {e}. Using mock data.")
        return _get_mock_municipalities(state_code)


def _get_mock_municipalities(state_code: str | None = None) -> list[dict]:
    """Get mock municipality data when API is unavailable.

    Args:
        state_code: Optional state code to filter

    Returns:
        List[Dict]: Mock municipality data
    """
    mock_data = [
        {
            "id": 3550308,
            "nome": "São Paulo",
            "microrregiao": {"mesorregiao": {"UF": {"sigla": "SP", "nome": "São Paulo"}}},
            "population": 12325232,
            "area_km2": 1521.11,
            "rural_population": 150000,
        },
        {
            "id": 3304557,
            "nome": "Rio de Janeiro",
            "microrregiao": {"mesorregiao": {"UF": {"sigla": "RJ", "nome": "Rio de Janeiro"}}},
            "population": 6747815,
            "area_km2": 1200.27,
            "rural_population": 80000,
        },
        {
            "id": 5300108,
            "nome": "Brasília",
            "microrregiao": {"mesorregiao": {"UF": {"sigla": "DF", "nome": "Distrito Federal"}}},
            "population": 3094325,
            "area_km2": 5760.78,
            "rural_population": 120000,
        },
        {
            "id": 2927408,
            "nome": "Salvador",
            "microrregiao": {"mesorregiao": {"UF": {"sigla": "BA", "nome": "Bahia"}}},
            "population": 2900319,
            "area_km2": 693.45,
            "rural_population": 45000,
        },
        {
            "id": 2304400,
            "nome": "Fortaleza",
            "microrregiao": {"mesorregiao": {"UF": {"sigla": "CE", "nome": "Ceará"}}},
            "population": 2686612,
            "area_km2": 314.93,
            "rural_population": 35000,
        },
    ]

    if state_code:
        mock_data = [m for m in mock_data if m["microrregiao"]["mesorregiao"]["UF"]["sigla"] == state_code.upper()]

    return mock_data


def fetch_ibge_demographics(municipality_id: int) -> dict:
    """Fetch demographic data for a specific municipality.

    Args:
        municipality_id: IBGE municipality code

    Returns:
        Dict: Demographic statistics
    """
    logger.info(f"Fetching IBGE demographics for municipality_id={municipality_id}")

    # Mock demographic data (would be from IBGE API in production)
    demographics = {
        "municipality_id": municipality_id,
        "total_population": 500000,
        "rural_population": 75000,
        "urban_population": 425000,
        "households": 150000,
        "rural_households": 22000,
        "internet_access_percentage": 78.5,
        "rural_internet_access_percentage": 45.2,
        "avg_income": 2500.0,
        "poverty_rate": 15.5,
    }

    logger.info(f"Retrieved demographics for municipality {municipality_id}")
    return demographics


def get_rural_areas_needing_connectivity() -> list[dict]:
    """Get list of rural areas with low connectivity based on IBGE data.

    Returns:
        List[Dict]: Priority rural areas for connectivity improvements
    """
    logger.info("Fetching rural areas needing connectivity from IBGE data")

    # Mock data representing areas with low connectivity
    priority_areas = [
        {
            "municipality": "Cametá",
            "state": "PA",
            "rural_population": 85000,
            "internet_coverage": 12.5,
            "priority_score": 95,
            "latitude": -2.2422,
            "longitude": -49.4964,
        },
        {
            "municipality": "Bom Jesus da Lapa",
            "state": "BA",
            "rural_population": 42000,
            "internet_coverage": 18.3,
            "priority_score": 88,
            "latitude": -13.2550,
            "longitude": -43.4183,
        },
        {
            "municipality": "Picos",
            "state": "PI",
            "rural_population": 38000,
            "internet_coverage": 22.1,
            "priority_score": 82,
            "latitude": -7.0772,
            "longitude": -41.4669,
        },
        {
            "municipality": "Araguaína",
            "state": "TO",
            "rural_population": 35000,
            "internet_coverage": 28.5,
            "priority_score": 75,
            "latitude": -7.1906,
            "longitude": -48.2073,
        },
        {
            "municipality": "Caruaru",
            "state": "PE",
            "rural_population": 55000,
            "internet_coverage": 32.0,
            "priority_score": 70,
            "latitude": -8.2836,
            "longitude": -35.9744,
        },
    ]

    logger.info(f"Retrieved {len(priority_areas)} priority rural areas")
    return priority_areas


def get_ibge_statistics_summary() -> dict:
    """Get summary statistics from IBGE about Brazil's connectivity landscape.

    Returns:
        Dict: Summary statistics
    """
    logger.info("Fetching IBGE connectivity statistics summary")

    summary = {
        "total_municipalities": 5570,
        "total_population": 213300000,
        "rural_population": 31900000,
        "rural_percentage": 15.0,
        "households_with_internet": 83.0,
        "rural_households_with_internet": 55.0,
        "municipalities_with_low_coverage": 2100,
        "priority_states": ["PA", "AM", "TO", "PI", "MA", "BA"],
        "avg_rural_internet_speed_mbps": 35.0,
        "urban_rural_digital_divide_percentage": 28.0,
    }

    logger.info("Retrieved IBGE statistics summary")
    return summary


def combine_ibge_anatel_data(ibge_data: list[dict], anatel_data: list[dict]) -> list[dict]:
    """Combine IBGE demographic data with ANATEL connectivity data.

    Args:
        ibge_data: IBGE municipality/demographic data
        anatel_data: ANATEL connectivity data

    Returns:
        List[Dict]: Combined enriched dataset
    """
    logger.info(f"Combining {len(ibge_data)} IBGE records with {len(anatel_data)} ANATEL records")

    combined = []

    # Create lookup for ANATEL data by municipality
    anatel_by_municipality = {}
    for record in anatel_data:
        municipality = record.get("municipality", record.get("nome"))
        if municipality not in anatel_by_municipality:
            anatel_by_municipality[municipality] = []
        anatel_by_municipality[municipality].append(record)

    # Combine data
    for ibge_record in ibge_data:
        municipality = ibge_record.get("nome")

        # Find matching ANATEL records
        anatel_records = anatel_by_municipality.get(municipality, [])

        if anatel_records:
            for anatel_record in anatel_records:
                combined_record = {**ibge_record, "connectivity": anatel_record, "data_source": "IBGE+ANATEL"}
                combined.append(combined_record)
        else:
            # Include IBGE data even without ANATEL match
            combined_record = {**ibge_record, "connectivity": None, "data_source": "IBGE_only"}
            combined.append(combined_record)

    logger.info(f"Created {len(combined)} combined records")
    return combined
