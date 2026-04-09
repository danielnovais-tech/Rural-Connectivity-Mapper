"""Tests for OpenAPI spec, open-data exports (GeoJSON/CSV/ecosystem), and API endpoints."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime

import pytest


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _sample_point(
    pid: str = "pt-1",
    lat: float = -15.78,
    lon: float = -47.93,
    download: float = 50.0,
    upload: float = 15.0,
    latency: float = 35.0,
    quality: float = 72.0,
    rating: str = "Good",
    provider: str = "Starlink",
) -> dict:
    return {
        "id": pid,
        "latitude": lat,
        "longitude": lon,
        "provider": provider,
        "country": "BR",
        "timestamp": datetime.now().isoformat(),
        "speed_test": {
            "download": download,
            "upload": upload,
            "latency": latency,
            "jitter": 2.0,
            "packet_loss": 0.1,
            "stability": 88.0,
        },
        "quality_score": {
            "overall_score": quality,
            "speed_score": 65.0,
            "latency_score": 80.0,
            "stability_score": 88.0,
            "rating": rating,
        },
        "technology": "satellite",
        "h3_index": "870000000000001",
    }


def _sample_data(n: int = 5) -> list[dict]:
    return [
        _sample_point("pt-1", -15.78, -47.93, 50, 15, 35, 72, "Good", "Starlink"),
        _sample_point("pt-2", -23.55, -46.63, 120, 40, 12, 90, "Excellent", "Vivo"),
        _sample_point("pt-3", -3.12, -60.02, 5, 1, 120, 25, "Poor", "HughesNet"),
        _sample_point("pt-4", -22.91, -43.17, 80, 30, 20, 78, "Good", "Claro"),
        _sample_point("pt-5", -8.05, -34.88, 12, 3, 80, 35, "Poor", "TIM"),
    ][:n]


# ══════════════════════════════════════════════════════════════════════════════
# OpenAPI Spec Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestOpenAPISpec:

    def test_spec_structure(self):
        from src.api.openapi_spec import OPENAPI_SPEC

        assert OPENAPI_SPEC["openapi"] == "3.1.0"
        assert "info" in OPENAPI_SPEC
        assert OPENAPI_SPEC["info"]["title"] == "Rural Connectivity Mapper API"
        assert "paths" in OPENAPI_SPEC
        assert "components" in OPENAPI_SPEC

    def test_all_main_paths_present(self):
        from src.api.openapi_spec import OPENAPI_SPEC

        paths = OPENAPI_SPEC["paths"]
        required_paths = [
            "/api/data",
            "/api/data/{pointId}",
            "/api/statistics",
            "/api/analysis",
            "/api/health",
            "/api/v2/recommendation",
            "/api/v2/ml/analysis",
            "/api/v2/ml/coverage-gaps",
            "/api/v2/ml/recommendations",
            "/api/v2/export/geojson",
            "/api/v2/export/csv",
            "/api/v2/export/ecosystem",
            "/api/v2/export/measurement-schema",
            "/api/openapi.json",
        ]
        for p in required_paths:
            assert p in paths, f"Missing path: {p}"

    def test_tags_defined(self):
        from src.api.openapi_spec import OPENAPI_SPEC

        tag_names = {t["name"] for t in OPENAPI_SPEC["tags"]}
        assert {"Data", "Statistics", "ML", "Open Data", "System"}.issubset(tag_names)

    def test_schemas_defined(self):
        from src.api.openapi_spec import OPENAPI_SPEC

        schemas = OPENAPI_SPEC["components"]["schemas"]
        required_schemas = [
            "ConnectivityPoint",
            "SpeedTest",
            "QualityScore",
            "NewDataPoint",
            "GapForecast",
            "Recommendation",
            "GeoJSONFeatureCollection",
            "ErrorResponse",
        ]
        for s in required_schemas:
            assert s in schemas, f"Missing schema: {s}"

    def test_spec_is_valid_json(self):
        from src.api.openapi_spec import OPENAPI_SPEC

        # Must be serialisable
        dumped = json.dumps(OPENAPI_SPEC)
        loaded = json.loads(dumped)
        assert loaded["openapi"] == "3.1.0"

    def test_data_path_has_get_and_post(self):
        from src.api.openapi_spec import OPENAPI_SPEC

        data_path = OPENAPI_SPEC["paths"]["/api/data"]
        assert "get" in data_path
        assert "post" in data_path
        assert data_path["post"]["requestBody"]["required"] is True

    def test_export_paths_are_get(self):
        from src.api.openapi_spec import OPENAPI_SPEC

        for path in ["/api/v2/export/geojson", "/api/v2/export/csv", "/api/v2/export/ecosystem"]:
            assert "get" in OPENAPI_SPEC["paths"][path]


# ══════════════════════════════════════════════════════════════════════════════
# GeoJSON Export Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestGeoJSON:

    def test_basic_feature_collection(self):
        from src.api.open_data import to_geojson

        data = _sample_data(3)
        geojson = to_geojson(data)

        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 3
        assert "metadata" in geojson
        assert geojson["metadata"]["total_features"] == 3
        assert geojson["metadata"]["license"] == "MIT"

    def test_feature_geometry(self):
        from src.api.open_data import to_geojson

        data = _sample_data(1)
        feature = to_geojson(data)["features"][0]

        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        coords = feature["geometry"]["coordinates"]
        assert len(coords) == 2
        # GeoJSON is [lon, lat]
        assert coords[0] == pytest.approx(-47.93, abs=0.01)
        assert coords[1] == pytest.approx(-15.78, abs=0.01)

    def test_feature_properties(self):
        from src.api.open_data import to_geojson

        data = _sample_data(1)
        props = to_geojson(data)["features"][0]["properties"]

        assert props["provider"] == "Starlink"
        assert props["download_mbps"] == 50.0
        assert props["quality_score"] == 72.0
        assert props["country"] == "BR"

    def test_empty_data(self):
        from src.api.open_data import to_geojson

        geojson = to_geojson([])
        assert geojson["type"] == "FeatureCollection"
        assert geojson["features"] == []
        assert geojson["metadata"]["total_features"] == 0

    def test_geojson_is_serialisable(self):
        from src.api.open_data import to_geojson

        data = _sample_data(5)
        dumped = json.dumps(to_geojson(data))
        assert len(dumped) > 100


# ══════════════════════════════════════════════════════════════════════════════
# CSV Export Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestCSV:

    def test_basic_csv(self):
        from src.api.open_data import to_csv, CSV_COLUMNS

        data = _sample_data(3)
        csv_str = to_csv(data)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)

        assert len(rows) == 3
        assert set(reader.fieldnames) == set(CSV_COLUMNS)

    def test_csv_values(self):
        from src.api.open_data import to_csv

        data = _sample_data(1)
        csv_str = to_csv(data)
        reader = csv.DictReader(io.StringIO(csv_str))
        row = next(reader)

        assert row["provider"] == "Starlink"
        assert float(row["download_mbps"]) == 50.0
        assert float(row["quality_score"]) == 72.0

    def test_empty_csv(self):
        from src.api.open_data import to_csv, CSV_COLUMNS

        csv_str = to_csv([])
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert rows == []
        assert set(reader.fieldnames) == set(CSV_COLUMNS)


# ══════════════════════════════════════════════════════════════════════════════
# Ecosystem Bundle Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestEcosystemBundle:

    def test_bundle_structure(self):
        from src.api.open_data import to_ecosystem_bundle

        data = _sample_data(3)
        bundle = to_ecosystem_bundle(data)

        assert "metadata" in bundle
        assert "hybrid_simulator" in bundle
        assert "agrix_boost" in bundle
        assert "manifest" in bundle
        assert bundle["metadata"]["total_points"] == 3

    def test_simulator_payload(self):
        from src.api.open_data import to_ecosystem_bundle

        data = _sample_data(2)
        sim = to_ecosystem_bundle(data)["hybrid_simulator"]

        assert sim["purpose"] == "failover_testing"
        assert sim["total_points"] == 2
        pt = sim["connectivity_points"][0]
        assert "failover_indicators" in pt
        assert "metrics" in pt

    def test_agrix_payload(self):
        from src.api.open_data import to_ecosystem_bundle

        data = _sample_data(2)
        agrix = to_ecosystem_bundle(data)["agrix_boost"]

        assert agrix["purpose"] == "farm_connectivity_layer"
        loc = agrix["connectivity_layer"][0]
        assert "farm_suitability" in loc
        assert "connectivity_status" in loc

    def test_farm_suitability_flags(self):
        from src.api.open_data import to_ecosystem_bundle

        # High quality point
        data = [_sample_point(download=120, upload=40, latency=12, quality=90)]
        agrix = to_ecosystem_bundle(data)["agrix_boost"]
        suit = agrix["connectivity_layer"][0]["farm_suitability"]

        assert suit["iot_sensors_supported"] is True
        assert suit["video_monitoring_supported"] is True
        assert suit["real_time_control_supported"] is True
        assert suit["data_analytics_supported"] is True

    def test_farm_suitability_poor(self):
        from src.api.open_data import to_ecosystem_bundle

        # Poor quality point
        data = [_sample_point(download=3, upload=0.5, latency=200, quality=20)]
        agrix = to_ecosystem_bundle(data)["agrix_boost"]
        suit = agrix["connectivity_layer"][0]["farm_suitability"]

        assert suit["video_monitoring_supported"] is False
        assert suit["real_time_control_supported"] is False

    def test_manifest_components(self):
        from src.api.open_data import to_ecosystem_bundle

        bundle = to_ecosystem_bundle(_sample_data(1))
        roles = {c["role"] for c in bundle["manifest"]["components"]}
        assert "data_hub" in roles
        assert "failover_testing" in roles
        assert "farm_dashboards" in roles


# ══════════════════════════════════════════════════════════════════════════════
# Measurement JSON Schema Test
# ══════════════════════════════════════════════════════════════════════════════

class TestMeasurementSchema:

    def test_schema_generation(self):
        from src.api.open_data import measurement_json_schema

        schema = measurement_json_schema()
        assert "properties" in schema
        assert "lat" in schema["properties"]
        assert "lon" in schema["properties"]
        assert "download_mbps" in schema["properties"]
        assert schema["properties"]["lat"]["type"] == "number"

    def test_schema_title(self):
        from src.api.open_data import measurement_json_schema

        schema = measurement_json_schema()
        assert schema.get("title") == "MeasurementSchema"

    def test_schema_enums(self):
        from src.api.open_data import measurement_json_schema

        schema = measurement_json_schema()
        # SourceType enum should appear in $defs
        defs = schema.get("$defs", {})
        assert "SourceType" in defs
        assert "TechnologyType" in defs
