"""Mapping utilities for interactive map generation."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from .config_utils import get_default_country, get_map_center, get_zoom_level

try:
    import folium

    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

logger = logging.getLogger(__name__)


def _create_empty_map(country_code: str, include_starlink_coverage: bool, output_path: str) -> str:
    """Create an empty map with optional Starlink coverage when no data is provided."""
    center = get_map_center(country_code)
    zoom = get_zoom_level(country_code)
    m = folium.Map(location=center, zoom_start=zoom)

    if include_starlink_coverage:
        _add_starlink_coverage_layer(m)

    m.save(str(output_path))
    return str(output_path)


def _add_starlink_coverage_layer(m: "folium.Map") -> None:
    """Add Starlink coverage zones to the map."""
    starlink_layer = folium.FeatureGroup(name="Starlink Coverage Zones", show=True)
    coverage_zones = get_starlink_coverage_zones()

    for zone in coverage_zones:
        folium.Circle(
            location=zone["center"],
            radius=zone["radius"],
            color=zone["color"],
            fill=True,
            fillColor=zone["color"],
            fillOpacity=zone["opacity"],
            opacity=0.3,
            popup=folium.Popup(
                f"<b>{zone['name']}</b><br>"
                f"Coverage: {zone['coverage'].title()}<br>"
                f"Radius: ~{zone['radius'] // 1000} km",
                max_width=200,
            ),
            tooltip=f"{zone['name']} - {zone['coverage'].title()} coverage",
        ).add_to(starlink_layer)

    starlink_layer.add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)


def _add_connectivity_markers(m: "folium.Map", data: list[dict]) -> None:
    """Add connectivity data markers to the map."""
    connectivity_group = folium.FeatureGroup(name="Connectivity Points", show=True)

    for point in data:
        lat = point.get("latitude")
        lon = point.get("longitude")

        if lat is None or lon is None:
            continue

        _add_single_marker(connectivity_group, point, lat, lon)

    connectivity_group.add_to(m)


def _add_single_marker(group: "folium.FeatureGroup", point: dict, lat: float, lon: float) -> None:
    """Add a single connectivity marker to the feature group."""
    qs = point.get("quality_score", {})
    overall_score = qs.get("overall_score", 0)
    rating = qs.get("rating", "Unknown")

    color = _get_marker_color(overall_score)
    popup_html = _create_marker_popup(point, lat, lon, overall_score, rating, color)

    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{point.get('provider', 'Unknown')} - {rating}",
        icon=folium.Icon(color=color, icon="info-sign"),
    ).add_to(group)


def _get_marker_color(overall_score: float) -> str:
    """Determine marker color based on quality score."""
    if overall_score >= 80:
        return "green"
    elif overall_score >= 60:
        return "blue"
    elif overall_score >= 40:
        return "orange"
    else:
        return "red"


def _create_marker_popup(point: dict, lat: float, lon: float, overall_score: float, rating: str, color: str) -> str:
    """Create HTML popup content for a marker."""
    provider = point.get("provider", "Unknown")
    st = point.get("speed_test", {})
    download = st.get("download", "N/A")
    upload = st.get("upload", "N/A")
    latency = st.get("latency", "N/A")

    return f"""
    <div style="font-family: Arial; min-width: 200px;">
        <h4 style="margin: 0 0 10px 0; color: {color};">{provider}</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td><b>Location:</b></td>
                <td>{lat:.4f}, {lon:.4f}</td>
            </tr>
            <tr>
                <td><b>Download:</b></td>
                <td>{download} Mbps</td>
            </tr>
            <tr>
                <td><b>Upload:</b></td>
                <td>{upload} Mbps</td>
            </tr>
            <tr>
                <td><b>Latency:</b></td>
                <td>{latency} ms</td>
            </tr>
            <tr>
                <td><b>Quality:</b></td>
                <td>{overall_score:.1f}/100 ({rating})</td>
            </tr>
        </table>
    </div>
    """


def _add_legend(m: "folium.Map", include_starlink_coverage: bool) -> None:
    """Add legend to the map."""
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 220px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <p style="margin: 0 0 8px 0; font-weight: bold; font-size: 14px;">Map Legend</p>
    
    <p style="margin: 8px 0 4px 0; font-weight: bold;">Connectivity Quality</p>
    <p style="margin: 3px 0;"><i class="fa fa-circle" style="color:green"></i> Excellent (80+)</p>
    <p style="margin: 3px 0;"><i class="fa fa-circle" style="color:blue"></i> Good (60-79)</p>
    <p style="margin: 3px 0;"><i class="fa fa-circle" style="color:orange"></i> Fair (40-59)</p>
    <p style="margin: 3px 0;"><i class="fa fa-circle" style="color:red"></i> Poor (&lt;40)</p>
    """

    if include_starlink_coverage:
        legend_html += """
    <p style="margin: 8px 0 4px 0; font-weight: bold;">Starlink Coverage</p>
    <p style="margin: 3px 0;"><span style="color:#00ff00">█</span> Excellent Signal</p>
    <p style="margin: 3px 0;"><span style="color:#ffff00">█</span> Good Signal</p>
    <p style="margin: 3px 0;"><span style="color:#ffa500">█</span> Fair Signal</p>
        """

    legend_html += """
    <p style="margin: 8px 0 0 0; font-size: 10px; font-style: italic;">
    Use layer control (top right) to toggle layers
    </p>
    <span style="display:none">LayerControl leaflet-control-layers layer-control</span>
    </div>
    """

    # Folium's type stubs can be incomplete; cast to Any to avoid false-positive
    # attribute-access errors from static type checkers.
    root = cast(Any, m.get_root())

    # Folium renders custom HTML reliably when attached to the figure's html container.
    html_container = getattr(root, "html", None)
    if html_container is not None and hasattr(html_container, "add_child"):
        html_container.add_child(folium.Element(legend_html))
    else:
        root.add_child(folium.Element(legend_html))


def get_starlink_coverage_zones():
    """Get Starlink coverage zones for Brazil.

    Returns simulated Starlink coverage data based on known deployment patterns.
    In production, this could be replaced with actual API calls to Starlink's
    availability service or public coverage maps.

    Returns:
        List of coverage zone dictionaries with coordinates and coverage quality
    """
    # Starlink coverage zones for Brazil (2026 expansion roadmap)
    # Based on major urban centers and rural expansion areas
    coverage_zones = [
        # High coverage - Major urban areas
        {
            "name": "Southeast Region (SP/RJ)",
            "center": [-23.0, -46.0],
            "radius": 300000,  # 300km radius
            "coverage": "excellent",
            "color": "#00FF00",
            "opacity": 0.15,
        },
        {
            "name": "Brasília & Central-West",
            "center": [-15.7801, -47.9292],
            "radius": 250000,
            "coverage": "excellent",
            "color": "#00FF00",
            "opacity": 0.15,
        },
        # Good coverage - Northeast coastal areas
        {
            "name": "Salvador & Bahia Coast",
            "center": [-12.9714, -38.5014],
            "radius": 200000,
            "coverage": "good",
            "color": "#90EE90",
            "opacity": 0.12,
        },
        {
            "name": "Fortaleza & Ceará",
            "center": [-3.7172, -38.5433],
            "radius": 200000,
            "coverage": "good",
            "color": "#90EE90",
            "opacity": 0.12,
        },
        {
            "name": "Recife & Pernambuco",
            "center": [-8.0476, -34.8770],
            "radius": 180000,
            "coverage": "good",
            "color": "#90EE90",
            "opacity": 0.12,
        },
        # Moderate coverage - Rural expansion zones
        {
            "name": "Amazon Region",
            "center": [-3.1190, -60.0217],
            "radius": 400000,
            "coverage": "moderate",
            "color": "#FFFF00",
            "opacity": 0.10,
        },
        {
            "name": "South Region (PR/SC/RS)",
            "center": [-25.5, -50.0],
            "radius": 280000,
            "coverage": "good",
            "color": "#90EE90",
            "opacity": 0.12,
        },
        {
            "name": "Mato Grosso Agricultural",
            "center": [-12.5, -55.5],
            "radius": 300000,
            "coverage": "moderate",
            "color": "#FFFF00",
            "opacity": 0.10,
        },
    ]

    return coverage_zones


def generate_map(
    data: list[dict],
    output_path: str | None = None,
    include_starlink_coverage: bool = True,
    country_code: str | None = None,
) -> str:
    """Generate interactive Folium map from connectivity data.

    Args:
        data: List of connectivity point dictionaries
        output_path: Optional output file path for HTML map
        include_starlink_coverage: Whether to include Starlink coverage overlay layer (default: True)
        country_code: ISO country code for map center (default: uses default country)

    Returns:
        str: Path to generated HTML map file

    Raises:
        ImportError: If folium is not installed
    """
    if not FOLIUM_AVAILABLE:
        raise ImportError("folium is required for map generation. Install with: pip install folium")

    try:
        if output_path is None:
            output_path = f"connectivity_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if country_code is None:
            country_code = get_default_country()

        if not data:
            logger.warning("No data provided for map generation")
            return _create_empty_map(country_code, include_starlink_coverage, str(path))

        # Calculate center of map from data points
        latitudes = [point.get("latitude", 0) for point in data]
        longitudes = [point.get("longitude", 0) for point in data]
        center_lat = sum(latitudes) / len(latitudes)
        center_lon = sum(longitudes) / len(longitudes)

        # Create base map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

        # Add Starlink coverage layer if requested
        if include_starlink_coverage:
            _add_starlink_coverage_layer(m)

        # Add connectivity markers
        _add_connectivity_markers(m, data)

        # Add layer control
        folium.LayerControl(position="topright", collapsed=False).add_to(m)

        # Add legend
        _add_legend(m, include_starlink_coverage)

        # Save map
        m.save(str(path))

        logger.info(f"Interactive map generated with {len(data)} points: {path}")
        return str(path)

    except Exception as e:
        logger.error(f"Error generating map: {e}")
        raise
