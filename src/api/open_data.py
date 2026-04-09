"""Open-data export helpers — GeoJSON, CSV, ecosystem bundle.

Produces standardised, machine-readable formats so external systems
(GIS tools, data portals, partner APIs) can consume Rural Connectivity
Mapper data without custom parsing.

All exports include metadata headers (source, license, timestamp) to
comply with open-data best practices.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

_SOURCE = "Rural Connectivity Mapper 2026"
_LICENSE = "MIT"

# Canonical CSV column order (flat, GIS-friendly)
CSV_COLUMNS = [
    "id",
    "latitude",
    "longitude",
    "provider",
    "country",
    "timestamp",
    "download_mbps",
    "upload_mbps",
    "latency_ms",
    "jitter_ms",
    "packet_loss_pct",
    "stability",
    "quality_score",
    "rating",
    "technology",
    "h3_index",
]


# ── GeoJSON (RFC 7946) ──────────────────────────────────────────────────────

def to_geojson(data: list[dict]) -> dict:
    """Convert a list of connectivity-point dicts to a GeoJSON FeatureCollection.

    Each point becomes a GeoJSON Feature with a Point geometry and flat
    ``properties`` that any GIS tool can consume.
    """
    features: list[dict] = []
    for pt in data:
        lat = pt.get("latitude", pt.get("lat", 0))
        lon = pt.get("longitude", pt.get("lon", 0))
        speed = pt.get("speed_test", {})
        quality = pt.get("quality_score", {})

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(lon, 6), round(lat, 6)],  # GeoJSON is [lon, lat]
            },
            "properties": {
                "id": pt.get("id", ""),
                "provider": pt.get("provider", ""),
                "download_mbps": speed.get("download", pt.get("download_mbps")),
                "upload_mbps": speed.get("upload", pt.get("upload_mbps")),
                "latency_ms": speed.get("latency", pt.get("latency_ms")),
                "quality_score": quality.get("overall_score", pt.get("confidence_score")),
                "rating": quality.get("rating", ""),
                "timestamp": pt.get("timestamp", pt.get("timestamp_utc", "")),
                "technology": pt.get("technology", ""),
                "country": pt.get("country", "BR"),
                "h3_index": pt.get("h3_index", ""),
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_features": len(features),
            "source": _SOURCE,
            "license": _LICENSE,
        },
    }


# ── CSV ──────────────────────────────────────────────────────────────────────

def to_csv(data: list[dict]) -> str:
    """Produce a CSV string with standardised column names."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()

    for pt in data:
        speed = pt.get("speed_test", {})
        quality = pt.get("quality_score", {})
        writer.writerow({
            "id": pt.get("id", ""),
            "latitude": pt.get("latitude", pt.get("lat", "")),
            "longitude": pt.get("longitude", pt.get("lon", "")),
            "provider": pt.get("provider", ""),
            "country": pt.get("country", "BR"),
            "timestamp": pt.get("timestamp", pt.get("timestamp_utc", "")),
            "download_mbps": speed.get("download", pt.get("download_mbps", "")),
            "upload_mbps": speed.get("upload", pt.get("upload_mbps", "")),
            "latency_ms": speed.get("latency", pt.get("latency_ms", "")),
            "jitter_ms": speed.get("jitter", ""),
            "packet_loss_pct": speed.get("packet_loss", ""),
            "stability": speed.get("stability", ""),
            "quality_score": quality.get("overall_score", pt.get("confidence_score", "")),
            "rating": quality.get("rating", ""),
            "technology": pt.get("technology", ""),
            "h3_index": pt.get("h3_index", ""),
        })

    return buf.getvalue()


# ── Ecosystem bundle ─────────────────────────────────────────────────────────

def to_ecosystem_bundle(data: list[dict]) -> dict:
    """Produce a JSON ecosystem-integration bundle.

    Includes:
    * Hybrid Architecture Simulator input (failover indicators)
    * AgriX-Boost connectivity layer (farm suitability)
    * Ecosystem manifest
    """
    from src.utils.export_utils import (
        export_for_agrix_boost,
        export_for_hybrid_simulator,
    )

    # Use existing exporters but capture output as dicts
    import tempfile, os

    bundle: dict = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": _SOURCE,
            "license": _LICENSE,
            "total_points": len(data),
            "format_version": "2.0.0",
        },
        "hybrid_simulator": _build_simulator_payload(data),
        "agrix_boost": _build_agrix_payload(data),
        "manifest": {
            "ecosystem_name": "Rural Connectivity Ecosystem",
            "components": [
                {"name": "Rural Connectivity Mapper", "role": "data_hub"},
                {"name": "Hybrid Architecture Simulator", "role": "failover_testing"},
                {"name": "AgriX-Boost", "role": "farm_dashboards"},
            ],
        },
    }
    return bundle


def _build_simulator_payload(data: list[dict]) -> dict:
    """Hybrid Architecture Simulator compatible payload."""
    points = []
    for pt in data:
        speed = pt.get("speed_test", {})
        quality = pt.get("quality_score", {})
        qs = quality.get("overall_score", 0)
        lat_val = speed.get("latency", 0)
        stab = speed.get("stability", 0)

        points.append({
            "point_id": pt.get("id", ""),
            "location": {
                "latitude": pt.get("latitude", pt.get("lat", 0)),
                "longitude": pt.get("longitude", pt.get("lon", 0)),
            },
            "provider": pt.get("provider", ""),
            "metrics": {
                "signal_quality": qs,
                "latency_ms": lat_val,
                "download_mbps": speed.get("download", 0),
                "upload_mbps": speed.get("upload", 0),
                "stability_score": stab,
            },
            "failover_indicators": {
                "connection_reliable": qs >= 60,
                "low_latency": lat_val < 100,
                "stable_connection": stab >= 70,
                "recommended_primary": qs >= 80,
            },
        })
    return {
        "format_version": "1.0",
        "purpose": "failover_testing",
        "total_points": len(points),
        "connectivity_points": points,
    }


def _build_agrix_payload(data: list[dict]) -> dict:
    """AgriX-Boost compatible connectivity layer."""
    locations = []
    for pt in data:
        speed = pt.get("speed_test", {})
        quality = pt.get("quality_score", {})
        qs = quality.get("overall_score", 0)
        dl = speed.get("download", 0)
        lat_val = speed.get("latency", 0)

        locations.append({
            "location_id": pt.get("id", ""),
            "coordinates": {
                "latitude": pt.get("latitude", pt.get("lat", 0)),
                "longitude": pt.get("longitude", pt.get("lon", 0)),
            },
            "isp_provider": pt.get("provider", ""),
            "connectivity_status": {
                "quality_score": qs,
                "quality_rating": quality.get("rating", ""),
                "is_operational": qs >= 40,
            },
            "farm_suitability": {
                "iot_sensors_supported": lat_val < 200 and qs >= 40,
                "video_monitoring_supported": dl >= 25 and qs >= 60,
                "real_time_control_supported": lat_val < 50 and qs >= 80,
                "data_analytics_supported": dl >= 10 and qs >= 40,
            },
        })
    return {
        "format_version": "1.0",
        "purpose": "farm_connectivity_layer",
        "total_locations": len(locations),
        "connectivity_layer": locations,
    }


# ── Measurement JSON Schema ─────────────────────────────────────────────────

def measurement_json_schema() -> dict:
    """Return the Pydantic-generated JSON Schema for MeasurementSchema."""
    from src.schemas.measurement import MeasurementSchema

    return MeasurementSchema.model_json_schema()
