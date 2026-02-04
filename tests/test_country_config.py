"""Tests for country configuration utilities."""

from src.utils.country_config import (
    get_country_config,
    get_country_data_sources,
    get_country_providers,
    get_latam_summary,
    get_supported_countries,
    translate_field_names,
)


def test_get_supported_countries():
    """Test getting list of supported countries."""
    countries = get_supported_countries()
    
    assert isinstance(countries, list)
    assert len(countries) >= 10  # Should have at least 10 LATAM countries
    
    # Check for key countries
    assert 'BR' in countries
    assert 'AR' in countries
    assert 'CL' in countries
    assert 'MX' in countries


def test_get_country_config_brazil():
    """Test getting country config for Brazil."""
    config = get_country_config('BR')
    
    assert config is not None
    assert config.code == 'BR'
    assert config.name == 'Brazil'
    assert config.official_language == 'Portuguese'
    assert config.currency == 'BRL'
    assert config.telecom_regulator == 'ANATEL'
    assert config.stats_agency == 'IBGE'
    assert config.coordinates_center == (-15.7801, -47.9292)
    assert 'Starlink' in config.supported_providers
    assert len(config.data_sources) > 0


def test_get_country_config_case_insensitive():
    """Test that country code is case insensitive."""
    config_upper = get_country_config('BR')
    config_lower = get_country_config('br')
    
    assert config_upper is not None
    assert config_lower is not None
    assert config_upper.code == config_lower.code


def test_get_country_config_unknown():
    """Test getting config for unknown country."""
    config = get_country_config('XX')
    
    assert config is None


def test_get_country_providers():
    """Test getting providers for a country."""
    providers = get_country_providers('BR')
    
    assert isinstance(providers, list)
    assert len(providers) > 0
    assert 'Starlink' in providers
    assert 'Claro' in providers


def test_get_country_providers_different_countries():
    """Test that different countries have different provider lists."""
    br_providers = get_country_providers('BR')
    ar_providers = get_country_providers('AR')
    
    # Both should have Starlink
    assert 'Starlink' in br_providers
    assert 'Starlink' in ar_providers
    
    # But might have different local providers
    assert isinstance(br_providers, list)
    assert isinstance(ar_providers, list)


def test_get_country_data_sources():
    """Test getting data sources for a country."""
    sources = get_country_data_sources('BR')
    
    assert isinstance(sources, dict)
    assert 'telecom' in sources
    assert 'demographics' in sources
    assert 'connectivity' in sources
    
    # Check URLs are valid
    for _source_type, url in sources.items():
        assert url.startswith('http')


def test_get_latam_summary():
    """Test getting LATAM summary."""
    summary = get_latam_summary()
    
    assert isinstance(summary, dict)
    assert 'total_countries' in summary
    assert 'countries' in summary
    assert 'total_providers' in summary
    assert 'languages' in summary
    assert 'currencies' in summary
    assert 'unique_providers_count' in summary
    
    # Check counts
    assert summary['total_countries'] >= 10
    assert summary['unique_providers_count'] > 0
    
    # Check Brazil is included
    assert 'BR' in summary['countries']
    
    # Check provider list
    assert 'Starlink' in summary['total_providers']


def test_translate_field_names_portuguese():
    """Test field name translation for Portuguese."""
    translations = translate_field_names('BR')
    
    assert isinstance(translations, dict)
    assert 'download' in translations
    assert translations['latency'] == 'latência'
    assert translations['provider'] == 'provedor'
    assert translations['excellent'] == 'excelente'


def test_translate_field_names_spanish():
    """Test field name translation for Spanish."""
    translations = translate_field_names('AR')
    
    assert isinstance(translations, dict)
    assert 'download' in translations
    assert translations['latency'] == 'latencia'
    assert translations['provider'] == 'proveedor'
    assert translations['excellent'] == 'excelente'


def test_translate_field_names_unknown():
    """Test field name translation for unknown country."""
    translations = translate_field_names('XX')
    
    # Should return empty dict for unknown country
    assert isinstance(translations, dict)
    assert len(translations) == 0


def test_all_countries_have_starlink():
    """Test that all LATAM countries include Starlink."""
    countries = get_supported_countries()
    
    for country_code in countries:
        providers = get_country_providers(country_code)
        assert 'Starlink' in providers, f"Starlink not found in {country_code}"


def test_all_countries_have_valid_config():
    """Test that all countries have valid configuration."""
    countries = get_supported_countries()
    
    for country_code in countries:
        config = get_country_config(country_code)
        
        assert config is not None
        assert config.code == country_code
        assert config.name
        assert config.official_language
        assert config.currency
        assert config.telecom_regulator
        assert config.stats_agency
        assert len(config.coordinates_center) == 2
        assert len(config.supported_providers) > 0
        assert len(config.data_sources) > 0
