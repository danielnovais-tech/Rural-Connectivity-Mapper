"""OpenAPI 3.1.0 specification for the Rural Connectivity Mapper API.

Serves as the single source of truth for the public API surface.  Generated
programmatically so it stays in sync with Flask routes.

Usage::

    from src.api.openapi_spec import OPENAPI_SPEC
    # Returns a Python dict matching the OpenAPI 3.1.0 schema

Or from the running app:

    GET /api/openapi.json   → machine-readable spec
    GET /api/docs           → Swagger UI
"""

from __future__ import annotations

OPENAPI_SPEC: dict = {
    "openapi": "3.1.0",
    "info": {
        "title": "Rural Connectivity Mapper API",
        "version": "2.0.0",
        "description": (
            "Open API for rural connectivity data collection, analysis, "
            "ML-powered coverage-gap forecasting, and prescriptive "
            "infrastructure recommendations.  Designed as a central "
            "connectivity data hub with standardised open-data exports "
            "(GeoJSON, CSV, ecosystem bundles)."
        ),
        "contact": {"name": "Rural Connectivity Mapper", "url": "https://github.com/novais-tech/Rural-Connectivity-Mapper"},
        "license": {"name": "MIT", "identifier": "MIT"},
    },
    "servers": [
        {"url": "/", "description": "Current server"},
    ],
    "tags": [
        {"name": "Data", "description": "CRUD operations on connectivity measurements"},
        {"name": "Statistics", "description": "Aggregated statistics and temporal analysis"},
        {"name": "ML", "description": "Machine-learning coverage-gap forecasts and RL recommendations"},
        {"name": "Open Data", "description": "Standardised open-data exports (GeoJSON, CSV, ecosystem)"},
        {"name": "Reports", "description": "Formatted report generation and map visualisation"},
        {"name": "Recommendations", "description": "Provider comparison and location-based advice"},
        {"name": "System", "description": "Health checks and API metadata"},
    ],
    "paths": {
        # ── Data ──────────────────────────────────────────────────────
        "/api/data": {
            "get": {
                "operationId": "listData",
                "tags": ["Data"],
                "summary": "List all connectivity data points",
                "responses": {
                    "200": {
                        "description": "Array of connectivity points",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/DataListResponse"}}},
                    },
                },
            },
            "post": {
                "operationId": "addDataPoint",
                "tags": ["Data"],
                "summary": "Add a new connectivity measurement",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/NewDataPoint"}}},
                },
                "responses": {
                    "201": {
                        "description": "Measurement created",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/DataPointResponse"}}},
                    },
                    "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                },
            },
        },
        "/api/data/{pointId}": {
            "get": {
                "operationId": "getDataPoint",
                "tags": ["Data"],
                "summary": "Get a single connectivity data point",
                "parameters": [
                    {"name": "pointId", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {"description": "Single data point", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/DataPointResponse"}}}},
                    "404": {"description": "Not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                },
            },
        },
        # ── Statistics ────────────────────────────────────────────────
        "/api/statistics": {
            "get": {
                "operationId": "getStatistics",
                "tags": ["Statistics"],
                "summary": "Get overall connectivity statistics",
                "responses": {
                    "200": {"description": "Statistics summary", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/StatisticsResponse"}}}},
                },
            },
        },
        "/api/analysis": {
            "get": {
                "operationId": "getTemporalAnalysis",
                "tags": ["Statistics"],
                "summary": "Temporal evolution analysis of connectivity data",
                "responses": {
                    "200": {"description": "Temporal analysis", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SuccessResponse"}}}},
                },
            },
        },
        # ── ML / RL ──────────────────────────────────────────────────
        "/api/v2/ml/analysis": {
            "get": {
                "operationId": "mlAnalysis",
                "tags": ["ML"],
                "summary": "Combined ML + RL analysis",
                "description": "Runs coverage-gap forecasting (Gradient Boosting) and prescriptive recommendations (Q-learning) on all data.",
                "responses": {
                    "200": {"description": "Combined ML report", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MLAnalysisResponse"}}}},
                },
            },
        },
        "/api/v2/ml/coverage-gaps": {
            "get": {
                "operationId": "coverageGaps",
                "tags": ["ML"],
                "summary": "Coverage-gap forecasting",
                "description": "Predicts which H3 cells are at risk of quality degradation.",
                "responses": {
                    "200": {"description": "Gap forecasts", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CoverageGapResponse"}}}},
                },
            },
        },
        "/api/v2/ml/recommendations": {
            "get": {
                "operationId": "prescriptiveRecommendations",
                "tags": ["ML"],
                "summary": "Prescriptive infrastructure recommendations",
                "description": "RL-based optimal intervention policy per H3 cell.",
                "responses": {
                    "200": {"description": "Ranked recommendations", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PrescriptiveResponse"}}}},
                },
            },
        },
        # ── Open Data ────────────────────────────────────────────────
        "/api/v2/export/geojson": {
            "get": {
                "operationId": "exportGeoJSON",
                "tags": ["Open Data"],
                "summary": "Export data as GeoJSON FeatureCollection",
                "description": "RFC 7946 GeoJSON with connectivity properties per feature.",
                "responses": {
                    "200": {
                        "description": "GeoJSON FeatureCollection",
                        "content": {"application/geo+json": {"schema": {"$ref": "#/components/schemas/GeoJSONFeatureCollection"}}},
                    },
                },
            },
        },
        "/api/v2/export/csv": {
            "get": {
                "operationId": "exportCSV",
                "tags": ["Open Data"],
                "summary": "Export data as CSV",
                "description": "Flat CSV with standardised column names for interoperability.",
                "responses": {
                    "200": {
                        "description": "CSV file download",
                        "content": {"text/csv": {"schema": {"type": "string"}}},
                    },
                },
            },
        },
        "/api/v2/export/ecosystem": {
            "get": {
                "operationId": "exportEcosystem",
                "tags": ["Open Data"],
                "summary": "Export ecosystem integration bundle",
                "description": "JSON bundle with Hybrid Simulator + AgriX-Boost + manifest.",
                "responses": {
                    "200": {"description": "Ecosystem bundle", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SuccessResponse"}}}},
                },
            },
        },
        "/api/v2/export/measurement-schema": {
            "get": {
                "operationId": "getMeasurementSchema",
                "tags": ["Open Data"],
                "summary": "Canonical MeasurementSchema (JSON Schema)",
                "description": "Returns the Pydantic-generated JSON Schema for the canonical measurement format.",
                "responses": {
                    "200": {"description": "JSON Schema", "content": {"application/schema+json": {"schema": {"type": "object"}}}},
                },
            },
        },
        # ── Recommendations ──────────────────────────────────────────
        "/api/v2/recommendation": {
            "post": {
                "operationId": "getRecommendation",
                "tags": ["Recommendations"],
                "summary": "Get connectivity recommendation for a location",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["latitude", "longitude"],
                                "properties": {
                                    "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                                    "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                                    "use_case": {"type": "string", "default": "general"},
                                },
                            },
                        },
                    },
                },
                "responses": {
                    "200": {"description": "Provider recommendation", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RecommendationResponse"}}}},
                    "400": {"description": "Invalid coordinates", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                },
            },
        },
        # ── Reports ──────────────────────────────────────────────────
        "/api/report/{format}": {
            "get": {
                "operationId": "generateReport",
                "tags": ["Reports"],
                "summary": "Generate a report in the specified format",
                "parameters": [
                    {
                        "name": "format",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "enum": ["json", "csv", "txt", "html"]},
                    },
                ],
                "responses": {
                    "200": {"description": "Report file download"},
                    "400": {"description": "Invalid format"},
                },
            },
        },
        "/api/map": {
            "get": {
                "operationId": "getMap",
                "tags": ["Reports"],
                "summary": "Generate interactive Folium map",
                "responses": {
                    "200": {"description": "HTML map page", "content": {"text/html": {"schema": {"type": "string"}}}},
                },
            },
        },
        "/api/simulate": {
            "post": {
                "operationId": "simulateImprovement",
                "tags": ["Reports"],
                "summary": "Simulate router impact on quality scores",
                "responses": {
                    "200": {"description": "Simulation results", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SuccessResponse"}}}},
                },
            },
        },
        # ── System ───────────────────────────────────────────────────
        "/api/health": {
            "get": {
                "operationId": "healthCheck",
                "tags": ["System"],
                "summary": "Health check",
                "responses": {
                    "200": {
                        "description": "Healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "status": {"type": "string"},
                                        "timestamp": {"type": "string", "format": "date-time"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "/api/openapi.json": {
            "get": {
                "operationId": "getOpenAPISpec",
                "tags": ["System"],
                "summary": "OpenAPI 3.1 specification (this document)",
                "responses": {
                    "200": {"description": "OpenAPI JSON", "content": {"application/json": {"schema": {"type": "object"}}}},
                },
            },
        },
    },
    # ── Components ───────────────────────────────────────────────────
    "components": {
        "schemas": {
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "const": False},
                    "error": {"type": "string"},
                },
            },
            "SuccessResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {},
                },
            },
            # ── Data ──────────────────────────────────────────────
            "SpeedTest": {
                "type": "object",
                "properties": {
                    "download": {"type": "number", "description": "Download speed in Mbps"},
                    "upload": {"type": "number", "description": "Upload speed in Mbps"},
                    "latency": {"type": "number", "description": "Latency in ms"},
                    "jitter": {"type": "number"},
                    "packet_loss": {"type": "number"},
                    "stability": {"type": "number", "minimum": 0, "maximum": 100},
                },
            },
            "QualityScore": {
                "type": "object",
                "properties": {
                    "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
                    "speed_score": {"type": "number"},
                    "latency_score": {"type": "number"},
                    "stability_score": {"type": "number"},
                    "rating": {"type": "string", "enum": ["Excellent", "Good", "Fair", "Poor"]},
                },
            },
            "ConnectivityPoint": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                    "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                    "provider": {"type": "string"},
                    "country": {"type": "string", "pattern": "^[A-Z]{2}$"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "speed_test": {"$ref": "#/components/schemas/SpeedTest"},
                    "quality_score": {"$ref": "#/components/schemas/QualityScore"},
                },
            },
            "NewDataPoint": {
                "type": "object",
                "required": ["latitude", "longitude", "provider", "download", "upload", "latency"],
                "properties": {
                    "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                    "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                    "provider": {"type": "string"},
                    "download": {"type": "number", "minimum": 0, "description": "Mbps"},
                    "upload": {"type": "number", "minimum": 0, "description": "Mbps"},
                    "latency": {"type": "number", "minimum": 0, "description": "ms"},
                    "jitter": {"type": "number", "default": 0},
                    "packet_loss": {"type": "number", "default": 0},
                },
            },
            "DataListResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {"type": "array", "items": {"$ref": "#/components/schemas/ConnectivityPoint"}},
                    "total": {"type": "integer"},
                },
            },
            "DataPointResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {"$ref": "#/components/schemas/ConnectivityPoint"},
                    "message": {"type": "string"},
                },
            },
            # ── Statistics ────────────────────────────────────────
            "StatisticsResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "statistics": {
                        "type": "object",
                        "properties": {
                            "total_points": {"type": "integer"},
                            "avg_quality_score": {"type": "number"},
                            "avg_download": {"type": "number"},
                            "avg_upload": {"type": "number"},
                            "avg_latency": {"type": "number"},
                            "ratings": {"type": "object", "additionalProperties": {"type": "integer"}},
                            "providers": {"type": "object", "additionalProperties": {"type": "integer"}},
                        },
                    },
                },
            },
            # ── ML ───────────────────────────────────────────────
            "GapForecast": {
                "type": "object",
                "properties": {
                    "h3_index": {"type": "string"},
                    "current_quality": {"type": "number"},
                    "predicted_quality": {"type": "number"},
                    "quality_delta": {"type": "number"},
                    "time_to_gap_days": {"type": ["integer", "null"]},
                    "risk_level": {"type": "string", "enum": ["critical", "high", "moderate", "low"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "dominant_technology": {"type": "string"},
                    "is_rural": {"type": "boolean"},
                },
            },
            "CoverageGapResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "generated_at": {"type": "string", "format": "date-time"},
                            "total_cells_analyzed": {"type": "integer"},
                            "cells_at_risk": {"type": "integer"},
                            "cells_critical": {"type": "integer"},
                            "model_r2_score": {"type": "number"},
                            "forecasts": {"type": "array", "items": {"$ref": "#/components/schemas/GapForecast"}},
                            "summary": {"type": "object"},
                        },
                    },
                },
            },
            "Recommendation": {
                "type": "object",
                "properties": {
                    "h3_index": {"type": "string"},
                    "action": {
                        "type": "string",
                        "enum": [
                            "deploy_satellite", "upgrade_fiber", "add_4g_tower",
                            "add_5g_small_cell", "add_fixed_wireless",
                            "community_wifi", "maintain",
                        ],
                    },
                    "expected_quality_after": {"type": "number"},
                    "expected_uplift": {"type": "number"},
                    "estimated_cost_normalised": {"type": "number"},
                    "roi_score": {"type": "number"},
                    "priority_rank": {"type": "integer"},
                    "rationale": {"type": "string"},
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "is_rural": {"type": "boolean"},
                    "current_quality": {"type": "number"},
                },
            },
            "PrescriptiveResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "generated_at": {"type": "string", "format": "date-time"},
                            "total_cells": {"type": "integer"},
                            "cells_with_actions": {"type": "integer"},
                            "total_episodes_trained": {"type": "integer"},
                            "recommendations": {"type": "array", "items": {"$ref": "#/components/schemas/Recommendation"}},
                            "policy_summary": {"type": "object"},
                        },
                    },
                },
            },
            "MLAnalysisResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "generated_at": {"type": "string", "format": "date-time"},
                            "data_points_used": {"type": "integer"},
                            "h3_cells_analyzed": {"type": "integer"},
                            "coverage_gap_forecast": {"type": "object"},
                            "prescriptive_recommendations": {"type": "object"},
                        },
                    },
                },
            },
            # ── Open Data ────────────────────────────────────────
            "GeoJSONFeatureCollection": {
                "type": "object",
                "required": ["type", "features"],
                "properties": {
                    "type": {"type": "string", "const": "FeatureCollection"},
                    "features": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type", "geometry", "properties"],
                            "properties": {
                                "type": {"type": "string", "const": "Feature"},
                                "geometry": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string", "const": "Point"},
                                        "coordinates": {
                                            "type": "array",
                                            "items": {"type": "number"},
                                            "minItems": 2,
                                            "maxItems": 2,
                                        },
                                    },
                                },
                                "properties": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "provider": {"type": "string"},
                                        "download_mbps": {"type": "number"},
                                        "upload_mbps": {"type": "number"},
                                        "latency_ms": {"type": "number"},
                                        "quality_score": {"type": "number"},
                                        "rating": {"type": "string"},
                                        "timestamp": {"type": "string", "format": "date-time"},
                                        "technology": {"type": "string"},
                                        "country": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "generated_at": {"type": "string", "format": "date-time"},
                            "total_features": {"type": "integer"},
                            "source": {"type": "string"},
                            "license": {"type": "string"},
                        },
                    },
                },
            },
            # ── Recommendations ──────────────────────────────────
            "RecommendationResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "recommendation": {
                        "type": "object",
                        "properties": {
                            "best_provider": {"type": "string"},
                            "alternatives": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "providers": {"type": "object"},
                    "location": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lon": {"type": "number"},
                        },
                    },
                    "response_time_ms": {"type": "number"},
                },
            },
        },
    },
}
