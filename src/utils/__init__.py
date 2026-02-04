"""Utils package for Rural Connectivity Mapper.

This package intentionally avoids importing heavy optional dependencies at
import-time (e.g. numpy/pandas/sklearn). Many modules import `src.utils` for a
small subset of helpers; eager imports would crash module import when those
optional dependencies aren't available (or when wheels are incompatible).

Exports are provided lazily via `__getattr__`.
"""

from __future__ import annotations

import importlib
from typing import Any

_EXPORTS: dict[str, tuple[str, str]] = {
    # validation_utils
    'validate_coordinates': ('validation_utils', 'validate_coordinates'),
    'validate_speed_test': ('validation_utils', 'validate_speed_test'),
    'validate_provider': ('validation_utils', 'validate_provider'),
    'validate_csv_row': ('validation_utils', 'validate_csv_row'),

    # data_utils
    'load_data': ('data_utils', 'load_data'),
    'save_data': ('data_utils', 'save_data'),
    'backup_data': ('data_utils', 'backup_data'),

    # measurement_utils
    'measure_speed': ('measurement_utils', 'measure_speed'),

    # geocoding_utils
    'geocode_coordinates': ('geocoding_utils', 'geocode_coordinates'),
    'geocode_address': ('geocoding_utils', 'geocode_address'),

    # report_utils
    'generate_report': ('report_utils', 'generate_report'),

    # simulation_utils
    'simulate_router_impact': ('simulation_utils', 'simulate_router_impact'),

    # mapping_utils
    'generate_map': ('mapping_utils', 'generate_map'),

    # analysis_utils
    'analyze_temporal_evolution': ('analysis_utils', 'analyze_temporal_evolution'),
    'cluster_connectivity_points': ('analysis_utils', 'cluster_connectivity_points'),
    'forecast_quality_scores': ('analysis_utils', 'forecast_quality_scores'),
    'compare_providers': ('analysis_utils', 'compare_providers'),

    # starlink_coverage_utils
    'get_starlink_coverage_zones': ('starlink_coverage_utils', 'get_starlink_coverage_zones'),
    'get_starlink_signal_points': ('starlink_coverage_utils', 'get_starlink_signal_points'),
    'get_coverage_color': ('starlink_coverage_utils', 'get_coverage_color'),
    'get_coverage_rating': ('starlink_coverage_utils', 'get_coverage_rating'),

    # anatel_utils
    'fetch_anatel_broadband_data': ('anatel_utils', 'fetch_anatel_broadband_data'),
    'fetch_anatel_mobile_data': ('anatel_utils', 'fetch_anatel_mobile_data'),
    'get_anatel_provider_stats': ('anatel_utils', 'get_anatel_provider_stats'),
    'convert_anatel_to_connectivity_points': ('anatel_utils', 'convert_anatel_to_connectivity_points'),

    # ibge_utils
    'fetch_ibge_municipalities': ('ibge_utils', 'fetch_ibge_municipalities'),
    'get_rural_areas_needing_connectivity': ('ibge_utils', 'get_rural_areas_needing_connectivity'),
    'get_ibge_statistics_summary': ('ibge_utils', 'get_ibge_statistics_summary'),

    # starlink_utils
    'check_starlink_availability': ('starlink_utils', 'check_starlink_availability'),
    'get_starlink_service_plans': ('starlink_utils', 'get_starlink_service_plans'),
    'get_starlink_coverage_map': ('starlink_utils', 'get_starlink_coverage_map'),

    # country_config
    'get_supported_countries': ('country_config', 'get_supported_countries'),
    'get_country_config': ('country_config', 'get_country_config'),
    'get_latam_summary': ('country_config', 'get_latam_summary'),

    # ml_utils
    'predict_improvement_potential': ('ml_utils', 'predict_improvement_potential'),
    'identify_expansion_zones': ('ml_utils', 'identify_expansion_zones'),
    'analyze_starlink_roi': ('ml_utils', 'analyze_starlink_roi'),
    'generate_ml_report': ('ml_utils', 'generate_ml_report'),

    # config_utils
    'load_country_config': ('config_utils', 'load_country_config'),
    'get_country_info': ('config_utils', 'get_country_info'),
    'get_default_country': ('config_utils', 'get_default_country'),
    'get_providers': ('config_utils', 'get_providers'),
    'get_language': ('config_utils', 'get_language'),
    'get_map_center': ('config_utils', 'get_map_center'),
    'get_zoom_level': ('config_utils', 'get_zoom_level'),
    'list_available_countries': ('config_utils', 'list_available_countries'),

    # i18n_utils
    'get_translation': ('i18n_utils', 'get_translation'),
    'get_rating_translation': ('i18n_utils', 'get_rating_translation'),
    'get_supported_languages': ('i18n_utils', 'get_supported_languages'),

    # export_utils
    'export_for_hybrid_simulator': ('export_utils', 'export_for_hybrid_simulator'),
    'export_for_agrix_boost': ('export_utils', 'export_for_agrix_boost'),
    'export_ecosystem_bundle': ('export_utils', 'export_ecosystem_bundle'),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_name, attr_name = _EXPORTS[name]
    module = importlib.import_module(f".{module_name}", __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_EXPORTS.keys()))


__all__ = list(_EXPORTS.keys())
