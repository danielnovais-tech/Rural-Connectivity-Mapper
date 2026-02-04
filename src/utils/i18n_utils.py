"""Internationalization utilities for multilingual support."""

import logging

logger = logging.getLogger(__name__)

# Translation dictionaries
TRANSLATIONS = {
    "en": {
        # Report headers
        "report_title": "RURAL CONNECTIVITY MAPPER 2026 - REPORT",
        "generated": "Generated",
        "total_points": "Total Points",
        "point": "Point",
        "location": "Location",
        "provider": "Provider",
        "timestamp": "Timestamp",
        # Speed test fields
        "speed_test": "Speed Test",
        "download": "Download",
        "upload": "Upload",
        "latency": "Latency",
        "jitter": "Jitter",
        "packet_loss": "Packet Loss",
        "stability": "Stability",
        # Quality score fields
        "quality_score": "Quality Score",
        "overall": "Overall",
        "overall_score": "Overall Score",
        "speed_score": "Speed Score",
        "latency_score": "Latency Score",
        "stability_score": "Stability Score",
        "rating": "Rating",
        # Ratings
        "excellent": "Excellent",
        "good": "Good",
        "fair": "Fair",
        "poor": "Poor",
        # Units
        "mbps": "Mbps",
        "ms": "ms",
        # Analysis insights
        "insight_excellent_quality": "Overall connectivity quality is excellent across all points",
        "insight_good_quality": "Overall connectivity quality is good with room for improvement",
        "insight_poor_quality": "Overall connectivity quality needs significant improvement",
        "insight_download_excellent": "Download speeds meet Starlink 2026 target expectations",
        "insight_download_good": "Download speeds are acceptable but below optimal targets",
        "insight_download_poor": "Download speeds are below target thresholds",
        "insight_latency_good": "Latency is within Starlink 2026 target range",
        "insight_latency_poor": "Latency exceeds target thresholds and needs optimization",
        "insight_best_provider": "{provider} shows the best average quality score ({score}/100)",
    },
    "pt": {
        # Report headers
        "report_title": "MAPEADOR DE CONECTIVIDADE RURAL 2026 - RELATÓRIO",
        "generated": "Gerado em",
        "total_points": "Total de Pontos",
        "point": "Ponto",
        "location": "Localização",
        "provider": "Provedor",
        "timestamp": "Data/Hora",
        # Speed test fields
        "speed_test": "Teste de Velocidade",
        "download": "Download",
        "upload": "Upload",
        "latency": "Latência",
        "jitter": "Jitter",
        "packet_loss": "Perda de Pacotes",
        "stability": "Estabilidade",
        # Quality score fields
        "quality_score": "Pontuação de Qualidade",
        "overall": "Geral",
        "overall_score": "Pontuação Geral",
        "speed_score": "Pontuação de Velocidade",
        "latency_score": "Pontuação de Latência",
        "stability_score": "Pontuação de Estabilidade",
        "rating": "Classificação",
        # Ratings
        "excellent": "Excelente",
        "good": "Bom",
        "fair": "Razoável",
        "poor": "Ruim",
        # Units
        "mbps": "Mbps",
        "ms": "ms",
        # Analysis insights
        "insight_excellent_quality": "A qualidade geral da conectividade é excelente em todos os pontos",
        "insight_good_quality": "A qualidade geral da conectividade é boa com margem para melhoria",
        "insight_poor_quality": "A qualidade geral da conectividade precisa de melhorias significativas",
        "insight_download_excellent": "As velocidades de download atendem às expectativas do Starlink 2026",
        "insight_download_good": "As velocidades de download são aceitáveis mas abaixo das metas ideais",
        "insight_download_poor": "As velocidades de download estão abaixo dos limites esperados",
        "insight_latency_good": "A latência está dentro da faixa esperada do Starlink 2026",
        "insight_latency_poor": "A latência excede os limites esperados e precisa de otimização",
        "insight_best_provider": "{provider} apresenta a melhor pontuação média de qualidade ({score}/100)",
    },
}

# Default language
DEFAULT_LANGUAGE = "en"


def get_translation(key: str, language: str | None = None, **kwargs) -> str:
    """Get translation for a key in specified language.

    Args:
        key: Translation key
        language: Language code (en, pt). Defaults to DEFAULT_LANGUAGE
        **kwargs: Format parameters for the translation string

    Returns:
        str: Translated string
    """
    if language is None:
        language = DEFAULT_LANGUAGE

    # Normalize and validate language code
    language = str(language).lower().strip()
    if len(language) > 2:
        language = language[:2]

    # Fall back to English if language not supported
    if language not in TRANSLATIONS:
        logger.warning(f"Language '{language}' not supported, falling back to '{DEFAULT_LANGUAGE}'")
        language = DEFAULT_LANGUAGE

    # Get translation
    translation = TRANSLATIONS[language].get(key, key)

    # Apply formatting if kwargs provided
    if kwargs:
        try:
            translation = translation.format(**kwargs)
        except KeyError as e:
            # Extract the missing parameter name from the exception
            missing_param = str(e).strip("'\"")
            logger.warning(f"Missing format parameter '{missing_param}' for translation key '{key}'")

    return translation


def get_rating_translation(rating: str, language: str | None = None) -> str:
    """Get translation for a quality rating.

    Args:
        rating: Original rating string (Excellent, Good, Fair, Poor)
        language: Language code (en, pt)

    Returns:
        str: Translated rating
    """
    if language is None:
        language = DEFAULT_LANGUAGE

    # Normalize rating to lowercase for lookup
    rating_key = rating.lower()

    return get_translation(rating_key, language)


def get_supported_languages() -> list:
    """Get list of supported language codes.

    Returns:
        list: List of supported language codes
    """
    return list(TRANSLATIONS.keys())
