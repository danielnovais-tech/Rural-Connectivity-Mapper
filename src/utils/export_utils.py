"""Export utilities for ecosystem integration with Hybrid Architecture Simulator and AgriX-Boost."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)

# Failover indicator thresholds
FAILOVER_RELIABLE_THRESHOLD = 60  # Minimum quality score for reliable connection
FAILOVER_LOW_LATENCY_THRESHOLD = 100  # Maximum latency (ms) for low latency classification
FAILOVER_STABLE_THRESHOLD = 70  # Minimum stability score for stable connection
FAILOVER_PRIMARY_THRESHOLD = 80  # Minimum quality score for primary connection recommendation

# Farm suitability thresholds
FARM_IOT_LATENCY_THRESHOLD = 200  # Maximum latency (ms) for IoT sensors
FARM_IOT_QUALITY_THRESHOLD = 40  # Minimum quality score for IoT sensors
FARM_VIDEO_DOWNLOAD_THRESHOLD = 25  # Minimum download speed (Mbps) for video monitoring
FARM_VIDEO_QUALITY_THRESHOLD = 60  # Minimum quality score for video monitoring
FARM_CONTROL_LATENCY_THRESHOLD = 50  # Maximum latency (ms) for real-time control
FARM_CONTROL_QUALITY_THRESHOLD = 80  # Minimum quality score for real-time control
FARM_ANALYTICS_DOWNLOAD_THRESHOLD = 10  # Minimum download speed (Mbps) for data analytics
FARM_ANALYTICS_QUALITY_THRESHOLD = 40  # Minimum quality score for data analytics


def export_for_hybrid_simulator(
    data: list[dict[str, Any]],
    output_path: str = "exports/hybrid_simulator_input.json",
) -> str:
    """Export connectivity data for Hybrid Architecture Simulator failover testing.

    Formats data to include signal quality, latency, and stability metrics required for
    testing realistic failover scenarios.
    """
    logger.info("Exporting data for Hybrid Architecture Simulator to %s", output_path)

    simulator_data: dict[str, Any] = {
        "metadata": {
            "export_timestamp": datetime.now().isoformat(),
            "source": "Rural Connectivity Mapper 2026",
            "total_points": len(data),
            "format_version": "1.0",
            "purpose": "failover_testing",
        },
        "connectivity_points": [],
    }

    for point in data:
        speed_test = cast(dict[str, Any], point.get("speed_test", {}))
        quality_score = cast(dict[str, Any], point.get("quality_score", {}))

        simulator_point: dict[str, Any] = {
            "point_id": point.get("id"),
            "location": {"latitude": point.get("latitude"), "longitude": point.get("longitude")},
            "provider": point.get("provider"),
            "timestamp": point.get("timestamp"),
            "metrics": {
                "signal_quality": quality_score.get("overall_score", 0.0),
                "latency_ms": speed_test.get("latency", 0.0),
                "download_mbps": speed_test.get("download", 0.0),
                "upload_mbps": speed_test.get("upload", 0.0),
                "stability_score": speed_test.get("stability", 0.0),
                "jitter_ms": speed_test.get("jitter", 0.0),
                "packet_loss_pct": speed_test.get("packet_loss", 0.0),
            },
            "quality_breakdown": {
                "overall_score": quality_score.get("overall_score", 0.0),
                "speed_score": quality_score.get("speed_score", 0.0),
                "latency_score": quality_score.get("latency_score", 0.0),
                "stability_score": quality_score.get("stability_score", 0.0),
                "rating": quality_score.get("rating", "Unknown"),
            },
            "failover_indicators": {
                "connection_reliable": quality_score.get("overall_score", 0.0) >= FAILOVER_RELIABLE_THRESHOLD,
                "low_latency": speed_test.get("latency", 999) < FAILOVER_LOW_LATENCY_THRESHOLD,
                "stable_connection": speed_test.get("stability", 0.0) >= FAILOVER_STABLE_THRESHOLD,
                "recommended_primary": quality_score.get("overall_score", 0.0) >= FAILOVER_PRIMARY_THRESHOLD,
            },
        }

        cast(list[dict[str, Any]], simulator_data["connectivity_points"]).append(simulator_point)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(simulator_data, file, indent=2, ensure_ascii=False)

    logger.info("Successfully exported %s points for Hybrid Architecture Simulator", len(data))
    return str(output_file)


def export_for_agrix_boost(
    data: list[dict[str, Any]],
    output_path: str = "exports/agrix_boost_connectivity.json",
) -> str:
    """Export connectivity data for AgriX-Boost farm dashboards."""
    logger.info("Exporting data for AgriX-Boost to %s", output_path)

    agrix_data: dict[str, Any] = {
        "metadata": {
            "export_timestamp": datetime.now().isoformat(),
            "source": "Rural Connectivity Mapper 2026",
            "total_locations": len(data),
            "format_version": "1.0",
            "purpose": "farm_connectivity_layer",
        },
        "connectivity_layer": [],
    }

    for point in data:
        speed_test = cast(dict[str, Any], point.get("speed_test", {}))
        quality_score = cast(dict[str, Any], point.get("quality_score", {}))

        agrix_point: dict[str, Any] = {
            "location_id": point.get("id"),
            "coordinates": {"lat": point.get("latitude"), "lon": point.get("longitude")},
            "isp_provider": point.get("provider"),
            "measurement_time": point.get("timestamp"),
            "connectivity_status": {
                "quality_rating": quality_score.get("rating", "Unknown"),
                "quality_score": quality_score.get("overall_score", 0.0),
                "is_operational": quality_score.get("overall_score", 0.0) >= 40,
                "is_optimal": quality_score.get("overall_score", 0.0) >= 80,
            },
            "network_performance": {
                "download_speed_mbps": speed_test.get("download", 0.0),
                "upload_speed_mbps": speed_test.get("upload", 0.0),
                "latency_ms": speed_test.get("latency", 0.0),
                "stability_pct": speed_test.get("stability", 0.0),
                "jitter_ms": speed_test.get("jitter", 0.0),
                "packet_loss_pct": speed_test.get("packet_loss", 0.0),
            },
            "farm_suitability": {
                "iot_sensors_supported": speed_test.get("latency", 999) < FARM_IOT_LATENCY_THRESHOLD
                and quality_score.get("overall_score", 0.0) >= FARM_IOT_QUALITY_THRESHOLD,
                "video_monitoring_supported": speed_test.get("download", 0.0) >= FARM_VIDEO_DOWNLOAD_THRESHOLD
                and quality_score.get("overall_score", 0.0) >= FARM_VIDEO_QUALITY_THRESHOLD,
                "real_time_control_supported": speed_test.get("latency", 999) < FARM_CONTROL_LATENCY_THRESHOLD
                and quality_score.get("overall_score", 0.0) >= FARM_CONTROL_QUALITY_THRESHOLD,
                "data_analytics_supported": speed_test.get("download", 0.0) >= FARM_ANALYTICS_DOWNLOAD_THRESHOLD
                and quality_score.get("overall_score", 0.0) >= FARM_ANALYTICS_QUALITY_THRESHOLD,
            },
            "recommendations": _generate_farm_recommendations(speed_test, quality_score),
        }

        cast(list[dict[str, Any]], agrix_data["connectivity_layer"]).append(agrix_point)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(agrix_data, file, indent=2, ensure_ascii=False)

    logger.info("Successfully exported %s points for AgriX-Boost", len(data))
    return str(output_file)


def _generate_farm_recommendations(
    speed_test: dict[str, Any],
    quality_score: dict[str, Any],
) -> list[str]:
    """Generate recommendations for farm connectivity based on metrics."""
    recommendations: list[str] = []

    overall = quality_score.get("overall_score", 0.0)
    download = speed_test.get("download", 0.0)
    latency = speed_test.get("latency", 999)
    stability = speed_test.get("stability", 0.0)

    if overall >= 80:
        recommendations.append("Excellent connectivity - Suitable for all farm automation systems")
    elif overall >= 60:
        recommendations.append("Good connectivity - Suitable for most farm applications")
    elif overall >= 40:
        recommendations.append("Fair connectivity - Basic IoT and monitoring supported")
    else:
        recommendations.append("Poor connectivity - Consider upgrading or adding backup connection")

    if download >= 50 and latency < 50:
        recommendations.append("Ideal for precision agriculture and autonomous equipment")

    if download >= 25:
        recommendations.append("Supports video monitoring and remote surveillance")

    if latency < 100 and stability >= 70:
        recommendations.append("Suitable for real-time sensor networks")

    if stability < 70:
        recommendations.append("Consider improving connection stability for critical operations")

    if latency > 100:
        recommendations.append("High latency - May impact real-time control systems")

    return recommendations


def export_ecosystem_bundle(
    data: list[dict[str, Any]],
    output_dir: str = "exports/ecosystem",
) -> dict[str, str]:
    """Export complete ecosystem bundle for all integrated projects."""
    logger.info("Creating ecosystem bundle in %s", output_dir)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    simulator_path = export_for_hybrid_simulator(data, str(output_path / "hybrid_simulator_input.json"))
    agrix_path = export_for_agrix_boost(data, str(output_path / "agrix_boost_connectivity.json"))

    manifest: dict[str, Any] = {
        "ecosystem": "Rural Connectivity Ecosystem 2026",
        "version": "1.0.0",
        "created": datetime.now().isoformat(),
        "components": {
            "rural_connectivity_mapper": {
                "description": "Map and analyze rural internet connectivity",
                "repository": "https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026",
                "data_points": len(data),
            },
            "hybrid_architecture_simulator": {
                "description": "Test realistic failover scenarios",
                "input_file": "hybrid_simulator_input.json",
                "purpose": "Failover testing with real connectivity data",
            },
            "agrix_boost": {
                "description": "Connectivity layer for farm dashboards",
                "input_file": "agrix_boost_connectivity.json",
                "purpose": "Agricultural monitoring and farm management",
            },
        },
        "integration_notes": [
            "Rural Connectivity Mapper provides real-world connectivity data",
            "Hybrid Architecture Simulator uses data for failover scenario testing",
            "AgriX-Boost integrates connectivity layer into farm dashboards",
            "All three projects share common data formats for seamless integration",
        ],
        "data_summary": {
            "total_points": len(data),
            "providers": list({p.get("provider", "Unknown") for p in data}),
            "quality_distribution": _get_quality_distribution(data),
        },
    }

    manifest_path = output_path / "ecosystem_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2, ensure_ascii=False)

    logger.info("Ecosystem bundle created successfully")
    return {"hybrid_simulator": simulator_path, "agrix_boost": agrix_path, "manifest": str(manifest_path)}


def _get_quality_distribution(data: list[dict[str, Any]]) -> dict[str, int]:
    """Calculate distribution of quality ratings."""
    distribution: dict[str, int] = {"Excellent": 0, "Good": 0, "Fair": 0, "Poor": 0, "Unknown": 0}

    for point in data:
        quality_score = cast(dict[str, Any], point.get("quality_score", {}))
        rating = quality_score.get("rating", "Unknown")
        if rating in distribution:
            distribution[rating] += 1
        else:
            distribution["Unknown"] += 1

    return distribution
