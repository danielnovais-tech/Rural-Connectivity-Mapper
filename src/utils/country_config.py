"""Country configuration for LATAM support.

This module provides country-specific configurations and data sources
for Latin American countries.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CountryConfig:
    """Configuration for a country."""

    code: str
    name: str
    official_language: str
    currency: str
    telecom_regulator: str
    stats_agency: str
    coordinates_center: tuple[float, float]  # (latitude, longitude)
    supported_providers: list[str]
    data_sources: dict[str, str]


# LATAM country configurations
LATAM_COUNTRIES = {
    "BR": CountryConfig(
        code="BR",
        name="Brazil",
        official_language="Portuguese",
        currency="BRL",
        telecom_regulator="ANATEL",
        stats_agency="IBGE",
        coordinates_center=(-15.7801, -47.9292),
        supported_providers=["Starlink", "Vivo", "Claro", "TIM", "Oi", "Viasat", "HughesNet"],
        data_sources={
            "telecom": "https://informacoes.anatel.gov.br/paineis/acessos",
            "demographics": "https://servicodados.ibge.gov.br/api/v1",
            "connectivity": "https://cetic.br/",
        },
    ),
    "AR": CountryConfig(
        code="AR",
        name="Argentina",
        official_language="Spanish",
        currency="ARS",
        telecom_regulator="ENACOM",
        stats_agency="INDEC",
        coordinates_center=(-34.6037, -58.3816),
        supported_providers=["Starlink", "Telecom Argentina", "Claro", "Movistar", "Personal", "HughesNet"],
        data_sources={
            "telecom": "https://www.enacom.gob.ar/datos-abiertos",
            "demographics": "https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos",
            "connectivity": "https://datosabiertos.enacom.gob.ar/",
        },
    ),
    "CL": CountryConfig(
        code="CL",
        name="Chile",
        official_language="Spanish",
        currency="CLP",
        telecom_regulator="SUBTEL",
        stats_agency="INE",
        coordinates_center=(-33.4489, -70.6693),
        supported_providers=["Starlink", "Movistar", "Entel", "Claro", "WOM", "VTR"],
        data_sources={
            "telecom": "https://www.subtel.gob.cl/estudios-y-estadisticas/",
            "demographics": "https://www.ine.gob.cl/",
            "connectivity": "https://www.subtel.gob.cl/",
        },
    ),
    "CO": CountryConfig(
        code="CO",
        name="Colombia",
        official_language="Spanish",
        currency="COP",
        telecom_regulator="CRC",
        stats_agency="DANE",
        coordinates_center=(4.7110, -74.0721),
        supported_providers=["Starlink", "Claro", "Movistar", "Tigo", "ETB", "DirecTV"],
        data_sources={
            "telecom": "https://www.crcom.gov.co/es/pagina/datos-abiertos",
            "demographics": "https://www.dane.gov.co/",
            "connectivity": "https://colombiatic.mintic.gov.co/",
        },
    ),
    "MX": CountryConfig(
        code="MX",
        name="Mexico",
        official_language="Spanish",
        currency="MXN",
        telecom_regulator="IFT",
        stats_agency="INEGI",
        coordinates_center=(19.4326, -99.1332),
        supported_providers=["Starlink", "Telcel", "Movistar", "AT&T", "Izzi", "Megacable"],
        data_sources={
            "telecom": "http://www.ift.org.mx/estadisticas",
            "demographics": "https://www.inegi.org.mx/",
            "connectivity": "http://www.ift.org.mx/",
        },
    ),
    "PE": CountryConfig(
        code="PE",
        name="Peru",
        official_language="Spanish",
        currency="PEN",
        telecom_regulator="OSIPTEL",
        stats_agency="INEI",
        coordinates_center=(-12.0464, -77.0428),
        supported_providers=["Starlink", "Movistar", "Claro", "Entel", "Bitel"],
        data_sources={
            "telecom": "https://www.osiptel.gob.pe/categoria/indicadores-del-sector",
            "demographics": "https://www.inei.gob.pe/",
            "connectivity": "https://www.osiptel.gob.pe/",
        },
    ),
    "EC": CountryConfig(
        code="EC",
        name="Ecuador",
        official_language="Spanish",
        currency="USD",
        telecom_regulator="ARCOTEL",
        stats_agency="INEC",
        coordinates_center=(-0.1807, -78.4678),
        supported_providers=["Starlink", "Claro", "Movistar", "CNT", "Tuenti"],
        data_sources={
            "telecom": "https://www.arcotel.gob.ec/indicadores/",
            "demographics": "https://www.ecuadorencifras.gob.ec/",
            "connectivity": "https://www.arcotel.gob.ec/",
        },
    ),
    "UY": CountryConfig(
        code="UY",
        name="Uruguay",
        official_language="Spanish",
        currency="UYU",
        telecom_regulator="URSEC",
        stats_agency="INE",
        coordinates_center=(-34.9011, -56.1645),
        supported_providers=["Starlink", "Antel", "Movistar", "Claro"],
        data_sources={
            "telecom": "https://www.ursec.gub.uy/inicio/datos-abiertos",
            "demographics": "http://www.ine.gub.uy/",
            "connectivity": "https://www.gub.uy/agesic/",
        },
    ),
    "PY": CountryConfig(
        code="PY",
        name="Paraguay",
        official_language="Spanish",
        currency="PYG",
        telecom_regulator="CONATEL",
        stats_agency="DGEEC",
        coordinates_center=(-25.2637, -57.5759),
        supported_providers=["Starlink", "Tigo", "Claro", "Personal", "Copaco"],
        data_sources={
            "telecom": "https://www.conatel.gov.py/estadisticas/",
            "demographics": "https://www.ine.gov.py/",
            "connectivity": "https://www.conatel.gov.py/",
        },
    ),
    "BO": CountryConfig(
        code="BO",
        name="Bolivia",
        official_language="Spanish",
        currency="BOB",
        telecom_regulator="ATT",
        stats_agency="INE",
        coordinates_center=(-16.5000, -68.1500),
        supported_providers=["Starlink", "Entel", "Tigo", "Viva"],
        data_sources={
            "telecom": "https://att.gob.bo/",
            "demographics": "https://www.ine.gob.bo/",
            "connectivity": "https://att.gob.bo/",
        },
    ),
}


def get_country_config(country_code: str) -> CountryConfig | None:
    """Get configuration for a specific country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        CountryConfig: Country configuration or None if not supported
    """
    config = LATAM_COUNTRIES.get(country_code.upper())
    if config:
        logger.info(f"Retrieved configuration for {config.name}")
    else:
        logger.warning(f"Country {country_code} not supported")
    return config


def get_supported_countries() -> list[str]:
    """Get list of supported country codes.

    Returns:
        List[str]: List of supported country codes
    """
    countries = list(LATAM_COUNTRIES.keys())
    logger.info(f"Retrieved {len(countries)} supported countries")
    return countries


def get_country_providers(country_code: str) -> list[str]:
    """Get list of supported providers for a country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        List[str]: List of provider names
    """
    config = get_country_config(country_code)
    if config:
        return config.supported_providers
    return []


def get_country_data_sources(country_code: str) -> dict[str, str]:
    """Get data source URLs for a country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        Dict[str, str]: Dictionary of data source types to URLs
    """
    config = get_country_config(country_code)
    if config:
        return config.data_sources
    return {}


def get_latam_summary() -> dict:
    """Get summary of LATAM coverage and statistics.

    Returns:
        Dict: Summary statistics for all LATAM countries
    """
    logger.info("Generating LATAM summary statistics")

    summary = {
        "total_countries": len(LATAM_COUNTRIES),
        "countries": {},
        "total_providers": set(),
        "languages": set(),
        "currencies": set(),
    }

    for code, config in LATAM_COUNTRIES.items():
        summary["countries"][code] = {
            "name": config.name,
            "language": config.official_language,
            "currency": config.currency,
            "providers_count": len(config.supported_providers),
        }
        summary["total_providers"].update(config.supported_providers)
        summary["languages"].add(config.official_language)
        summary["currencies"].add(config.currency)

    # Convert sets to lists for JSON serialization
    summary["total_providers"] = sorted(summary["total_providers"])
    summary["languages"] = sorted(summary["languages"])
    summary["currencies"] = sorted(summary["currencies"])
    summary["unique_providers_count"] = len(summary["total_providers"])

    logger.info(f"Generated summary for {summary['total_countries']} LATAM countries")
    return summary


def translate_field_names(country_code: str) -> dict[str, str]:
    """Get field name translations for a country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        Dict[str, str]: Dictionary mapping English field names to local language
    """
    config = get_country_config(country_code)

    # English to Portuguese translations for Brazil
    pt_translations = {
        "download": "download",
        "upload": "upload",
        "latency": "latência",
        "provider": "provedor",
        "quality_score": "pontuação de qualidade",
        "excellent": "excelente",
        "good": "bom",
        "fair": "razoável",
        "poor": "ruim",
        "municipality": "município",
        "state": "estado",
        "coverage": "cobertura",
        "rural": "rural",
        "urban": "urbano",
    }

    # English to Spanish translations for Spanish-speaking countries
    es_translations = {
        "download": "descarga",
        "upload": "subida",
        "latency": "latencia",
        "provider": "proveedor",
        "quality_score": "puntuación de calidad",
        "excellent": "excelente",
        "good": "bueno",
        "fair": "regular",
        "poor": "pobre",
        "municipality": "municipio",
        "state": "estado",
        "coverage": "cobertura",
        "rural": "rural",
        "urban": "urbano",
    }

    if config:
        if config.official_language == "Portuguese":
            return pt_translations
        elif config.official_language == "Spanish":
            return es_translations

    # Default to English (no translation)
    return {}
