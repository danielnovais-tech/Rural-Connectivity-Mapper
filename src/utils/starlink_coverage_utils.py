"""Starlink coverage utilities for Brazil rural areas.

This module provides functionality to generate Starlink coverage data for Brazil.
Currently uses simulated/placeholder data based on known Starlink deployment patterns.
Ready to be replaced with official API when available.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_starlink_coverage_zones() -> list[dict[str, Any]]:
    """Get Starlink coverage zones for Brazil.

    This is currently a placeholder implementation that returns simulated coverage
    data based on Starlink's known 2026 expansion roadmap for Brazil. The zones
    represent areas with strong, medium, and developing Starlink satellite coverage.

    Returns:
        List[Dict]: List of coverage zone dictionaries containing:
            - name: Zone name
            - coordinates: List of [lat, lon] boundary points
            - signal_strength: Coverage strength ('excellent', 'good', 'fair')
            - color: Display color for the zone
            - opacity: Zone opacity for visualization

    Note:
        This will be replaced with real Starlink API data when officially available.
        Current zones are based on:
        - Starlink 2026 expansion targets (10M rural connections)
        - Satellite constellation coverage patterns
        - Known deployment priorities in Brazil
    """
    coverage_zones = [
        {
            "name": "Central Brazil - High Coverage",
            "coordinates": [[-15.0, -50.0], [-15.0, -45.0], [-17.0, -45.0], [-17.0, -50.0], [-15.0, -50.0]],
            "signal_strength": "excellent",
            "color": "#00ff00",
            "opacity": 0.3,
            "description": "Primary coverage zone including Brasília region with optimal satellite visibility",
        },
        {
            "name": "Southeast Brazil - High Coverage",
            "coordinates": [[-20.0, -48.0], [-20.0, -42.0], [-24.0, -42.0], [-24.0, -48.0], [-20.0, -48.0]],
            "signal_strength": "excellent",
            "color": "#00ff00",
            "opacity": 0.3,
            "description": "São Paulo and Rio de Janeiro region with strong satellite coverage",
        },
        {
            "name": "South Brazil - Good Coverage",
            "coordinates": [[-24.0, -54.0], [-24.0, -48.0], [-30.0, -48.0], [-30.0, -54.0], [-24.0, -54.0]],
            "signal_strength": "good",
            "color": "#ffff00",
            "opacity": 0.25,
            "description": "Southern states with reliable coverage (Paraná, Santa Catarina, Rio Grande do Sul)",
        },
        {
            "name": "Northeast Brazil - Developing Coverage",
            "coordinates": [[-3.0, -42.0], [-3.0, -35.0], [-13.0, -35.0], [-13.0, -42.0], [-3.0, -42.0]],
            "signal_strength": "good",
            "color": "#ffff00",
            "opacity": 0.25,
            "description": "Northeast coastal region with expanding coverage (Fortaleza, Salvador areas)",
        },
        {
            "name": "North Brazil - Expanding Coverage",
            "coordinates": [[2.0, -62.0], [2.0, -50.0], [-8.0, -50.0], [-8.0, -62.0], [2.0, -62.0]],
            "signal_strength": "fair",
            "color": "#ffa500",
            "opacity": 0.2,
            "description": "Amazon region - coverage expanding as part of 2026 rural connectivity initiative",
        },
    ]

    logger.info(f"Generated {len(coverage_zones)} Starlink coverage zones for Brazil")
    return coverage_zones


def get_starlink_signal_points() -> list[dict[str, Any]]:
    """Get Starlink signal strength points for rural Brazil.

    Returns simulated signal strength data points across rural Brazil.
    These represent typical satellite signal measurements that would be obtained
    from actual Starlink terminals or coverage API.

    Returns:
        List[Dict]: List of signal point dictionaries containing:
            - latitude: Point latitude
            - longitude: Point longitude
            - signal_strength: Signal quality (0-100)
            - coverage_type: Type of coverage ('primary', 'secondary', 'edge')

    Note:
        This is placeholder data. Replace with real API when available.
    """
    # Simulate signal strength points across Brazil's rural areas
    signal_points = [
        # Central Brazil - Strong signals
        {"latitude": -15.7801, "longitude": -47.9292, "signal_strength": 95, "coverage_type": "primary"},
        {"latitude": -16.0, "longitude": -48.0, "signal_strength": 92, "coverage_type": "primary"},
        {"latitude": -15.5, "longitude": -47.5, "signal_strength": 90, "coverage_type": "primary"},
        # Southeast - Strong signals
        {"latitude": -23.5505, "longitude": -46.6333, "signal_strength": 88, "coverage_type": "primary"},
        {"latitude": -22.9068, "longitude": -43.1729, "signal_strength": 85, "coverage_type": "primary"},
        # South - Good signals
        {"latitude": -25.4284, "longitude": -49.2733, "signal_strength": 82, "coverage_type": "secondary"},
        {"latitude": -30.0346, "longitude": -51.2177, "signal_strength": 80, "coverage_type": "secondary"},
        # Northeast - Medium signals
        {"latitude": -12.9714, "longitude": -38.5014, "signal_strength": 75, "coverage_type": "secondary"},
        {"latitude": -3.7172, "longitude": -38.5433, "signal_strength": 72, "coverage_type": "secondary"},
        # North/Amazon - Developing signals
        {"latitude": -3.1190, "longitude": -60.0217, "signal_strength": 68, "coverage_type": "edge"},
        {"latitude": -1.4558, "longitude": -48.4902, "signal_strength": 65, "coverage_type": "edge"},
    ]

    logger.info(f"Generated {len(signal_points)} Starlink signal strength points")
    return signal_points


def get_coverage_color(signal_strength: float) -> str:
    """Get color representation for signal strength.

    Args:
        signal_strength: Signal strength value (0-100)

    Returns:
        str: Hex color code for the signal strength
    """
    if signal_strength >= 85:
        return "#00ff00"  # Green - Excellent
    elif signal_strength >= 70:
        return "#ffff00"  # Yellow - Good
    elif signal_strength >= 50:
        return "#ffa500"  # Orange - Fair
    else:
        return "#ff0000"  # Red - Poor


def get_coverage_rating(signal_strength: float) -> str:
    """Get human-readable rating for signal strength.

    Args:
        signal_strength: Signal strength value (0-100)

    Returns:
        str: Rating text ('Excellent', 'Good', 'Fair', 'Poor')
    """
    if signal_strength >= 85:
        return "Excellent"
    elif signal_strength >= 70:
        return "Good"
    elif signal_strength >= 50:
        return "Fair"
    else:
        return "Poor"
