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
        # ── Lite UI ─────────────────────────────────────────────
        "site_title": "Rural Connectivity Mapper",
        "nav_dashboard": "Dashboard",
        "nav_submit": "Submit Data",
        "nav_map": "Map",
        "nav_language": "Português",
        "hero_heading": "Rural Connectivity",
        "hero_sub": "Real-time connectivity data for underserved communities",
        "stat_points": "Measurements",
        "stat_download": "Avg Download",
        "stat_upload": "Avg Upload",
        "stat_latency": "Avg Latency",
        "stat_quality": "Avg Quality",
        "section_providers": "Providers",
        "section_ratings": "Quality Ratings",
        "section_data": "Recent Measurements",
        "section_insights": "Insights",
        "col_provider": "Provider",
        "col_count": "Count",
        "col_quality": "Quality",
        "col_download": "Download",
        "col_upload": "Upload",
        "col_latency": "Latency",
        "no_data": "No data available yet. Submit your first measurement!",
        "submit_heading": "Contribute Your Data",
        "submit_sub": "Help map rural connectivity by sharing your speed test results",
        "field_lat": "Latitude",
        "field_lon": "Longitude",
        "field_provider": "Internet Provider",
        "field_download": "Download (Mbps)",
        "field_upload": "Upload (Mbps)",
        "field_latency": "Latency (ms)",
        "btn_locate": "Use My Location",
        "btn_submit": "Submit",
        "btn_load_map": "Load Map",
        "map_heading": "Connectivity Map",
        "map_sub": "Visualize connectivity across rural areas",
        "map_note": "The map loads on demand to save bandwidth.",
        "map_nojs": "JavaScript is required to display the map. Data is shown as a table below.",
        "map_load_prompt": "Click to load the interactive connectivity map.",
        "map_size_warning": "~180 KB will be downloaded (Leaflet tiles).",
        "msg_loading": "Loading…",
        "msg_success": "Data submitted successfully!",
        "msg_error": "Something went wrong. Please try again.",
        "col_lat": "Latitude",
        "col_lon": "Longitude",
        "msg_locating": "Getting your location…",
        "msg_no_geo": "Geolocation is not supported by your browser.",
        "footer_text": "Rural Connectivity Mapper 2026 — Open Source",
        "offline_banner": "You are offline. Showing cached data.",
        "select_provider": "Select…",
        "help_speedtest": "Run a test at fast.com or speedtest.net first.",
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
        # ── Lite UI ─────────────────────────────────────────────
        "site_title": "Mapeador de Conectividade Rural",
        "nav_dashboard": "Painel",
        "nav_submit": "Enviar Dados",
        "nav_map": "Mapa",
        "nav_language": "English",
        "hero_heading": "Conectividade Rural",
        "hero_sub": "Dados de conectividade em tempo real para comunidades carentes",
        "stat_points": "Medições",
        "stat_download": "Download Médio",
        "stat_upload": "Upload Médio",
        "stat_latency": "Latência Média",
        "stat_quality": "Qualidade Média",
        "section_providers": "Provedores",
        "section_ratings": "Classificações de Qualidade",
        "section_data": "Medições Recentes",
        "section_insights": "Análises",
        "col_provider": "Provedor",
        "col_count": "Qtd",
        "col_quality": "Qualidade",
        "col_download": "Download",
        "col_upload": "Upload",
        "col_latency": "Latência",
        "no_data": "Nenhum dado disponível ainda. Envie sua primeira medição!",
        "submit_heading": "Contribua com seus Dados",
        "submit_sub": "Ajude a mapear a conectividade rural compartilhando seus testes de velocidade",
        "field_lat": "Latitude",
        "field_lon": "Longitude",
        "field_provider": "Provedor de Internet",
        "field_download": "Download (Mbps)",
        "field_upload": "Upload (Mbps)",
        "field_latency": "Latência (ms)",
        "btn_locate": "Usar Minha Localização",
        "btn_submit": "Enviar",
        "btn_load_map": "Carregar Mapa",
        "map_heading": "Mapa de Conectividade",
        "map_sub": "Visualize a conectividade nas áreas rurais",
        "map_note": "O mapa é carregado sob demanda para economizar dados.",
        "map_nojs": "JavaScript é necessário para exibir o mapa. Os dados estão na tabela abaixo.",
        "map_load_prompt": "Clique para carregar o mapa interativo de conectividade.",
        "map_size_warning": "~180 KB serão baixados (tiles do Leaflet).",
        "msg_loading": "Carregando…",
        "msg_success": "Dados enviados com sucesso!",
        "msg_error": "Algo deu errado. Tente novamente.",
        "col_lat": "Latitude",
        "col_lon": "Longitude",
        "msg_locating": "Obtendo sua localização…",
        "msg_no_geo": "Geolocalização não é suportada pelo seu navegador.",
        "footer_text": "Mapeador de Conectividade Rural 2026 — Código Aberto",
        "offline_banner": "Você está offline. Exibindo dados em cache.",
        "select_provider": "Selecione…",
        "help_speedtest": "Execute um teste em fast.com ou speedtest.net primeiro.",
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
