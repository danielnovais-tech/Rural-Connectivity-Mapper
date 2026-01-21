"""Tests for internationalization utilities."""

import pytest
from unittest.mock import patch
from src.utils.i18n_utils import (
    get_translation, 
    get_rating_translation, 
    get_supported_languages
)


def test_get_supported_languages():
    """Test getting supported languages."""
    languages = get_supported_languages()
    assert 'en' in languages
    assert 'pt' in languages
    assert len(languages) >= 2


def test_get_translation_english():
    """Test English translations."""
    assert get_translation('report_title', 'en') == 'RURAL CONNECTIVITY MAPPER 2026 - REPORT'
    assert get_translation('provider', 'en') == 'Provider'
    assert get_translation('download', 'en') == 'Download'
    assert get_translation('excellent', 'en') == 'Excellent'


def test_get_translation_portuguese():
    """Test Portuguese translations."""
    assert get_translation('report_title', 'pt') == 'MAPEADOR DE CONECTIVIDADE RURAL 2026 - RELATÓRIO'
    assert get_translation('provider', 'pt') == 'Provedor'
    assert get_translation('download', 'pt') == 'Download'
    assert get_translation('excellent', 'pt') == 'Excelente'


def test_get_translation_default_language():
    """Test default language fallback."""
    # When no language specified, should default to English
    assert get_translation('provider') == 'Provider'


def test_get_translation_unsupported_language():
    """Test fallback for unsupported language."""
    # Should fall back to English
    result = get_translation('provider', 'fr')
    assert result == 'Provider'


def test_get_translation_missing_key():
    """Test behavior with missing translation key."""
    # Should return the key itself if not found
    result = get_translation('nonexistent_key', 'en')
    assert result == 'nonexistent_key'


def test_get_translation_with_formatting():
    """Test translation with format parameters."""
    result = get_translation('insight_best_provider', 'en', 
                           provider='Starlink', score='95.0')
    assert 'Starlink' in result
    assert '95.0' in result
    
    result_pt = get_translation('insight_best_provider', 'pt', 
                              provider='Starlink', score='95.0')
    assert 'Starlink' in result_pt
    assert '95.0' in result_pt


def test_get_translation_language_normalization_and_truncation():
    """Test language normalization: case/whitespace + truncation to 2 chars."""
    assert get_translation('provider', ' PT ') == 'Provedor'
    assert get_translation('provider', 'pt-BR') == 'Provedor'


def test_get_translation_missing_format_parameter_logs_warning():
    """Test that missing format params do not raise and log a warning."""
    with patch('src.utils.i18n_utils.logger.warning') as warn:
        result = get_translation('insight_best_provider', 'en', provider='Starlink')

    # Because a required param is missing, formatting is skipped and placeholders remain.
    assert result == '{provider} shows the best average quality score ({score}/100)'
    assert warn.call_count >= 1


def test_get_rating_translation_english():
    """Test rating translations in English."""
    assert get_rating_translation('Excellent', 'en') == 'Excellent'
    assert get_rating_translation('Good', 'en') == 'Good'
    assert get_rating_translation('Fair', 'en') == 'Fair'
    assert get_rating_translation('Poor', 'en') == 'Poor'


def test_get_rating_translation_portuguese():
    """Test rating translations in Portuguese."""
    assert get_rating_translation('Excellent', 'pt') == 'Excelente'
    assert get_rating_translation('Good', 'pt') == 'Bom'
    assert get_rating_translation('Fair', 'pt') == 'Razoável'
    assert get_rating_translation('Poor', 'pt') == 'Ruim'


def test_get_rating_translation_case_insensitive():
    """Test that rating translation handles different cases."""
    assert get_rating_translation('EXCELLENT', 'pt') == 'Excelente'
    assert get_rating_translation('good', 'pt') == 'Bom'
    assert get_rating_translation('FaIr', 'pt') == 'Razoável'


def test_insights_translations():
    """Test insights message translations."""
    # English insights
    assert 'excellent' in get_translation('insight_excellent_quality', 'en').lower()
    assert 'starlink' in get_translation('insight_download_excellent', 'en').lower()
    
    # Portuguese insights
    assert 'excelente' in get_translation('insight_excellent_quality', 'pt').lower()
    assert 'starlink' in get_translation('insight_download_excellent', 'pt').lower()
