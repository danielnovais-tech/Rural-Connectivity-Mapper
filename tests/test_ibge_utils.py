"""Tests for IBGE utilities."""

import pytest

pytest.importorskip("pandas", exc_type=ImportError)
from src.utils.ibge_utils import (
    combine_ibge_anatel_data,
    fetch_ibge_demographics,
    fetch_ibge_municipalities,
    get_ibge_statistics_summary,
    get_rural_areas_needing_connectivity,
)


def test_fetch_ibge_municipalities():
    """Test fetching IBGE municipalities."""
    municipalities = fetch_ibge_municipalities()

    assert isinstance(municipalities, list)
    assert len(municipalities) > 0

    # Check structure
    first_municipality = municipalities[0]
    assert "nome" in first_municipality or "id" in first_municipality


def test_fetch_ibge_municipalities_with_state_filter():
    """Test fetching IBGE municipalities with state filter."""
    municipalities = fetch_ibge_municipalities(state_code="SP")

    assert isinstance(municipalities, list)
    # All municipalities should be from SP
    for municipality in municipalities:
        uf = municipality.get("microrregiao", {}).get("mesorregiao", {}).get("UF", {}).get("sigla")
        if uf:
            assert uf == "SP"


def test_fetch_ibge_demographics():
    """Test fetching IBGE demographics."""
    demographics = fetch_ibge_demographics(3550308)  # São Paulo

    assert isinstance(demographics, dict)
    assert "municipality_id" in demographics
    assert "total_population" in demographics
    assert "rural_population" in demographics
    assert "internet_access_percentage" in demographics


def test_get_rural_areas_needing_connectivity():
    """Test getting rural areas needing connectivity."""
    priority_areas = get_rural_areas_needing_connectivity()

    assert isinstance(priority_areas, list)
    assert len(priority_areas) > 0

    # Check structure
    first_area = priority_areas[0]
    assert "municipality" in first_area
    assert "state" in first_area
    assert "rural_population" in first_area
    assert "internet_coverage" in first_area
    assert "priority_score" in first_area
    assert "latitude" in first_area
    assert "longitude" in first_area

    # Check priority scores are valid
    for area in priority_areas:
        assert 0 <= area["priority_score"] <= 100


def test_get_ibge_statistics_summary():
    """Test getting IBGE statistics summary."""
    summary = get_ibge_statistics_summary()

    assert isinstance(summary, dict)
    assert "total_municipalities" in summary
    assert "total_population" in summary
    assert "rural_population" in summary
    assert "rural_percentage" in summary
    assert "households_with_internet" in summary
    assert "rural_households_with_internet" in summary

    # Check values are reasonable
    assert summary["total_municipalities"] > 5000
    assert summary["total_population"] > 200000000
    assert 0 < summary["rural_percentage"] < 100


def test_combine_ibge_anatel_data():
    """Test combining IBGE and ANATEL data."""
    ibge_data = [{"nome": "São Paulo", "id": 3550308}, {"nome": "Rio de Janeiro", "id": 3304557}]
    anatel_data = [
        {"municipality": "São Paulo", "provider": "Claro", "avg_speed_mbps": 100},
        {"municipality": "São Paulo", "provider": "Vivo", "avg_speed_mbps": 95},
    ]

    combined = combine_ibge_anatel_data(ibge_data, anatel_data)

    assert isinstance(combined, list)
    assert len(combined) > 0

    # Check that São Paulo has connectivity data
    sp_records = [r for r in combined if r.get("nome") == "São Paulo"]
    assert len(sp_records) > 0

    # Check Rio has record (without ANATEL match)
    rj_records = [r for r in combined if r.get("nome") == "Rio de Janeiro"]
    assert len(rj_records) > 0


def test_combine_empty_data():
    """Test combining empty data."""
    combined = combine_ibge_anatel_data([], [])

    assert isinstance(combined, list)
    assert len(combined) == 0
