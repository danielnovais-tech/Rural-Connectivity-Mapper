"""Utils package for Rural Connectivity Mapper."""

from .validation_utils import validate_coordinates, validate_speed_test, validate_provider, validate_csv_row
from .data_utils import load_data, save_data, backup_data
from .measurement_utils import measure_speed
from .geocoding_utils import geocode_coordinates, geocode_address
from .report_utils import generate_report
from .simulation_utils import simulate_router_impact
from .mapping_utils import generate_map

from .analysis_utils import (
    analyze_temporal_evolution,
    cluster_connectivity_points,
    forecast_quality_scores
)

from .analysis_utils import analyze_temporal_evolution, compare_providers
from .analysis_utils import analyze_temporal_evolution

from .starlink_coverage_utils import (
    get_starlink_coverage_zones,
    get_starlink_signal_points,
    get_coverage_color,
    get_coverage_rating
)

from .anatel_utils import (
    fetch_anatel_broadband_data,
    fetch_anatel_mobile_data,
    get_anatel_provider_stats,
    convert_anatel_to_connectivity_points
)
from .ibge_utils import (
    fetch_ibge_municipalities,
    get_rural_areas_needing_connectivity,
    get_ibge_statistics_summary
)
from .starlink_utils import (
    check_starlink_availability,
    get_starlink_service_plans,
    get_starlink_coverage_map
)
from .country_config import (
    get_supported_countries,
    get_country_config,
    get_latam_summary
)

from .ml_utils import (
    predict_improvement_potential,
    identify_expansion_zones,
    analyze_starlink_roi,
    generate_ml_report
)

from .config_utils import (
    load_country_config,
    get_country_info,
    get_default_country,
    get_providers,
    get_language,
    get_map_center,
    get_zoom_level,
    list_available_countries
)

from .i18n_utils import get_translation, get_rating_translation, get_supported_languages

from .export_utils import (
    export_for_hybrid_simulator,
    export_for_agrix_boost,
    export_ecosystem_bundle
)






__all__ = [
    'validate_coordinates',
    'validate_speed_test',
    'validate_provider',
    'validate_csv_row',
    'load_data',
    'save_data',
    'backup_data',
    'measure_speed',
    'geocode_coordinates',
    'geocode_address',
    'generate_report',
    'simulate_router_impact',
    'generate_map',
    'analyze_temporal_evolution',
    'get_starlink_coverage_zones',
    'get_starlink_signal_points',
    'get_coverage_color',
    'get_coverage_rating',
    'fetch_anatel_broadband_data',
    'fetch_anatel_mobile_data',
    'get_anatel_provider_stats',
    'convert_anatel_to_connectivity_points',
    'fetch_ibge_municipalities',
    'get_rural_areas_needing_connectivity',
    'get_ibge_statistics_summary',
    'check_starlink_availability',
    'get_starlink_service_plans',
    'get_starlink_coverage_map',
    'get_supported_countries',
    'get_country_config',
    'get_latam_summary',
    'predict_improvement_potential',
    'identify_expansion_zones',
    'analyze_starlink_roi',
    'generate_ml_report',
    'cluster_connectivity_points',
    'forecast_quality_scores',
    'load_country_config',
    'get_country_info',
    'get_default_country',
    'get_providers',
    'get_language',
    'get_map_center',
    'get_zoom_level',
    'list_available_countries',
    'get_translation',
    'get_rating_translation',
    'get_supported_languages',
    'compare_providers',
    'export_for_hybrid_simulator',
    'export_for_agrix_boost',
    'export_ecosystem_bundle'
]
