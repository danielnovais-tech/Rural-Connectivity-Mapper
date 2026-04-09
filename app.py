#!/usr/bin/env python3
"""Flask web application for Rural Connectivity Mapper 2026"""

import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from time import time

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from flask_cors import CORS  # type: ignore

from src.models import ConnectivityPoint, SpeedTest
from src.utils import (
    analyze_temporal_evolution,
    generate_map,
    generate_report,
    load_data,
    save_data,
    simulate_router_impact,
    validate_coordinates,
)
from src.utils.analytics import safe_geo, track_event
from src.utils.i18n_utils import get_translation
from src.utils.starlink_api import compare_with_competitors

# Known providers for the submit form
KNOWN_PROVIDERS = [
    "Starlink", "Vivo", "Claro", "TIM", "Oi", "Brisanet",
    "Hughes", "Viasat", "Other",
]

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Data file path
DATA_PATH = "src/data/pontos.json"


@app.route("/")
def index():
    """Render main dashboard page."""
    return render_template("index.html")


@app.route("/api/data", methods=["GET"])
def get_data():
    """Get all connectivity data points.

    Returns:
        JSON: List of connectivity points
    """
    try:
        data = load_data(DATA_PATH)
        return jsonify({"success": True, "data": data, "total": len(data)})
    except (ValueError, KeyError, OSError) as e:
        logger.error("Error loading data: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/data/<point_id>", methods=["GET"])
def get_data_point(point_id):
    """Get a specific connectivity data point.

    Args:
        point_id: ID of the data point

    Returns:
        JSON: Connectivity point data
    """
    try:
        data = load_data(DATA_PATH)
        point = next((p for p in data if p.get("id") == point_id), None)

        if point:
            return jsonify({"success": True, "data": point})
        else:
            return jsonify({"success": False, "error": "Data point not found"}), 404
    except (ValueError, KeyError, OSError) as e:
        logger.error("Error loading data point: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/data", methods=["POST"])
def add_data_point():
    """Add a new connectivity data point.

    Returns:
        JSON: Success status and created point
    """
    try:
        data_json = request.get_json()

        # Validate required fields
        required_fields = ["latitude", "longitude", "provider", "download", "upload", "latency"]
        for field in required_fields:
            if field not in data_json:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400

        # Validate coordinates
        lat = float(data_json["latitude"])
        lon = float(data_json["longitude"])

        if not validate_coordinates(lat, lon):
            return jsonify({"success": False, "error": "Invalid coordinates"}), 400

        # Create SpeedTest
        speed_test = SpeedTest(
            download=float(data_json["download"]),
            upload=float(data_json["upload"]),
            latency=float(data_json["latency"]),
            jitter=float(data_json.get("jitter", 0)),
            packet_loss=float(data_json.get("packet_loss", 0)),
        )

        # Create ConnectivityPoint
        point = ConnectivityPoint(
            latitude=lat,
            longitude=lon,
            provider=data_json["provider"],
            speed_test=speed_test,
            timestamp=data_json.get("timestamp", datetime.now().isoformat()),
            point_id=data_json.get("id"),
        )

        # Load existing data and append new point
        data = load_data(DATA_PATH)
        data.append(point.to_dict())
        save_data(DATA_PATH, data)

        return jsonify({"success": True, "data": point.to_dict(), "message": "Data point added successfully"}), 201

    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid value: {str(e)}"}), 400
    except (KeyError, TypeError, OSError) as e:
        logger.error("Error adding data point: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/statistics", methods=["GET"])
def get_statistics():
    """Get overall connectivity statistics.

    Returns:
        JSON: Statistics summary
    """
    try:
        data = load_data(DATA_PATH)

        if not data:
            return jsonify(
                {
                    "success": True,
                    "statistics": {
                        "total_points": 0,
                        "avg_quality_score": 0,
                        "avg_download": 0,
                        "avg_upload": 0,
                        "avg_latency": 0,
                    },
                }
            )

        # Calculate statistics
        total_points = len(data)
        avg_quality_score = sum(p["quality_score"]["overall_score"] for p in data) / total_points
        avg_download = sum(p["speed_test"]["download"] for p in data) / total_points
        avg_upload = sum(p["speed_test"]["upload"] for p in data) / total_points
        avg_latency = sum(p["speed_test"]["latency"] for p in data) / total_points

        # Count by rating
        ratings = {}
        for point in data:
            rating = point["quality_score"]["rating"]
            ratings[rating] = ratings.get(rating, 0) + 1

        # Count by provider
        providers = {}
        for point in data:
            provider = point["provider"]
            providers[provider] = providers.get(provider, 0) + 1

        return jsonify(
            {
                "success": True,
                "statistics": {
                    "total_points": total_points,
                    "avg_quality_score": round(avg_quality_score, 2),
                    "avg_download": round(avg_download, 2),
                    "avg_upload": round(avg_upload, 2),
                    "avg_latency": round(avg_latency, 2),
                    "ratings": ratings,
                    "providers": providers,
                },
            }
        )
    except (ValueError, KeyError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error("Error calculating statistics: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analysis", methods=["GET"])
def get_analysis():
    """Get temporal analysis of connectivity data.

    Returns:
        JSON: Temporal analysis results
    """
    try:
        data = load_data(DATA_PATH)
        analysis = analyze_temporal_evolution(data)

        return jsonify({"success": True, "analysis": analysis})
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.error("Error performing analysis: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/simulate", methods=["POST"])
def simulate_improvement():
    """Simulate router impact on quality scores.

    Returns:
        JSON: Success status and message
    """
    try:
        data = load_data(DATA_PATH)
        improved_data = simulate_router_impact(data)
        save_data(DATA_PATH, improved_data)

        return jsonify({"success": True, "message": "Router impact simulation completed", "data": improved_data})
    except (ValueError, KeyError, OSError, TypeError) as e:
        logger.error("Error simulating improvement: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/report/<report_format>", methods=["GET"])
def generate_report_api(report_format):
    """Generate report in specified format.

    Args:
        report_format: Report format (json, csv, txt, html)

    Returns:
        File download or JSON response
    """
    try:
        if report_format not in ["json", "csv", "txt", "html"]:
            return jsonify({"success": False, "error": "Invalid format. Choose from: json, csv, txt, html"}), 400

        data = load_data(DATA_PATH)
        report_path = generate_report(data, report_format, f"report.{report_format}")

        return send_file(report_path, as_attachment=True, download_name=f"connectivity_report.{report_format}")
    except (ValueError, KeyError, OSError, TypeError) as e:
        logger.error("Error generating report: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/map", methods=["GET"])
def get_map():
    """Generate interactive connectivity map.

    Returns:
        HTML: Interactive Folium map
    """
    try:
        data = load_data(DATA_PATH)

        # Create a temporary file for the map
        fd, temp_path = tempfile.mkstemp(suffix=".html", prefix="connectivity_map_")
        os.close(fd)

        map_path = generate_map(data, temp_path)

        # Send file and delete after sending
        response = send_file(map_path, mimetype="text/html")

        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except OSError:
                pass

        return response
    except (ValueError, KeyError, OSError, TypeError, ImportError) as e:
        logger.error("Error generating map: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint.

    Returns:
        JSON: Health status
    """
    return jsonify({"success": True, "status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/api/v2/recommendation", methods=["POST"])
def get_recommendation():
    """Get connectivity recommendation for a location.

    Analyzes available providers at a given location and returns
    the best recommendation based on speed, coverage, and cost.

    Request body:
        {
            "latitude": float,
            "longitude": float,
            "use_case": string (optional)
        }

    Returns:
        JSON: Recommendation with provider comparison
    """
    # Get or generate session ID from request
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    start_time = time()

    try:
        data = request.get_json()

        # Validate required fields
        if not data or "latitude" not in data or "longitude" not in data:
            track_event(
                event_name="recommendation_api_failed",
                session_id=session_id,
                properties={"error_code": "missing_required_fields"},
            )
            return jsonify({"success": False, "error": "Missing required fields: latitude, longitude"}), 400

        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        use_case = data.get("use_case", "general")

        # Validate coordinates
        if not validate_coordinates(latitude, longitude):
            track_event(
                event_name="recommendation_api_failed",
                session_id=session_id,
                properties={"error_code": "invalid_coordinates"},
            )
            return jsonify({"success": False, "error": "Invalid coordinates"}), 400

        # Track API call
        track_event(
            event_name="recommendation_api_called",
            session_id=session_id,
            context={"use_case": use_case},
            geo=safe_geo(latitude, longitude),
        )

        # Get recommendation using existing utility
        comparison = compare_with_competitors(latitude, longitude)

        # Calculate response time
        response_time_ms = (time() - start_time) * 1000

        # Track success
        track_event(
            event_name="recommendation_api_succeeded",
            session_id=session_id,
            context={"use_case": use_case},
            metrics={"response_time_ms": round(response_time_ms, 2)},
            properties={"recommended_provider": comparison["recommendation"]["best_provider"]},
            geo=safe_geo(latitude, longitude),
        )

        return jsonify(
            {
                "success": True,
                "recommendation": comparison["recommendation"],
                "providers": comparison["providers"],
                "location": comparison["location"],
                "response_time_ms": round(response_time_ms, 2),
            }
        )

    except ValueError as e:
        response_time_ms = (time() - start_time) * 1000
        track_event(
            event_name="recommendation_api_failed",
            session_id=session_id,
            metrics={"response_time_ms": round(response_time_ms, 2)},
            properties={"error_code": "value_error", "error_message": str(e)},
        )
        return jsonify({"success": False, "error": f"Invalid value: {str(e)}"}), 400

    except Exception as e:
        response_time_ms = (time() - start_time) * 1000
        logger.error(f"Error generating recommendation: {e}")
        track_event(
            event_name="recommendation_api_failed",
            session_id=session_id,
            metrics={"response_time_ms": round(response_time_ms, 2)},
            properties={"error_code": "internal_error", "error_message": str(e)},
        )
        return jsonify({"success": False, "error": "Internal server error"}), 500


# ── ML / RL API endpoints ───────────────────────────────────────────────────


@app.route("/api/v2/ml/analysis", methods=["GET"])
def ml_analysis():
    """Run combined ML + RL analysis on current connectivity data.

    Returns coverage-gap forecasts and prescriptive infrastructure recommendations.
    """
    try:
        from src.models.ml_engine import MLEngine

        data = load_data(DATA_PATH)
        if not data:
            return jsonify({"success": True, "data": {"message": "No data available for analysis"}}), 200

        engine = MLEngine()
        report = engine.run(data)
        return jsonify({"success": True, "data": report.to_dict()})
    except Exception as e:
        logger.error("ML analysis error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/v2/ml/coverage-gaps", methods=["GET"])
def coverage_gaps():
    """Forecast coverage gaps — which H3 cells are at risk of quality degradation."""
    try:
        from src.models.coverage_gap_model import CoverageGapForecaster, snapshots_from_gold

        data = load_data(DATA_PATH)
        if not data:
            return jsonify({"success": True, "data": {"forecasts": []}}), 200

        snapshots = snapshots_from_gold(data)
        forecaster = CoverageGapForecaster()
        if len(snapshots) >= 5:
            forecaster.fit(snapshots)
        report = forecaster.predict(snapshots)
        return jsonify({"success": True, "data": report.to_dict()})
    except Exception as e:
        logger.error("Coverage gap forecast error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/v2/ml/recommendations", methods=["GET"])
def prescriptive_recommendations():
    """Get prescriptive infrastructure recommendations (RL-based)."""
    try:
        from src.models.prescriptive_rl import PrescriptiveAgent, cell_states_from_gold

        data = load_data(DATA_PATH)
        if not data:
            return jsonify({"success": True, "data": {"recommendations": []}}), 200

        cell_states = cell_states_from_gold(data)
        agent = PrescriptiveAgent()
        if cell_states:
            agent.train(cell_states)
        report = agent.recommend(cell_states)
        return jsonify({"success": True, "data": report.to_dict()})
    except Exception as e:
        logger.error("Prescriptive recommendations error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ── OpenAPI / Open-Data endpoints ───────────────────────────────────────────


@app.route("/api/openapi.json", methods=["GET"])
def openapi_spec():
    """Serve the OpenAPI 3.1 specification."""
    from src.api.openapi_spec import OPENAPI_SPEC

    return jsonify(OPENAPI_SPEC)


@app.route("/api/docs")
def swagger_ui():
    """Render Swagger UI for interactive API exploration."""
    return render_template("swagger_ui.html")


@app.route("/api/v2/export/geojson", methods=["GET"])
def export_geojson():
    """Export all connectivity data as GeoJSON (RFC 7946)."""
    try:
        from src.api.open_data import to_geojson

        data = load_data(DATA_PATH)
        geojson = to_geojson(data)
        response = app.response_class(
            json.dumps(geojson, ensure_ascii=False),
            mimetype="application/geo+json",
        )
        response.headers["Content-Disposition"] = "attachment; filename=connectivity.geojson"
        return response
    except (ValueError, KeyError, OSError) as e:
        logger.error("GeoJSON export error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/v2/export/csv", methods=["GET"])
def export_csv():
    """Export all connectivity data as CSV."""
    try:
        from src.api.open_data import to_csv

        data = load_data(DATA_PATH)
        csv_str = to_csv(data)
        response = app.response_class(csv_str, mimetype="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=connectivity.csv"
        return response
    except (ValueError, KeyError, OSError) as e:
        logger.error("CSV export error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/v2/export/ecosystem", methods=["GET"])
def export_ecosystem():
    """Export ecosystem integration bundle (Hybrid Simulator + AgriX-Boost)."""
    try:
        from src.api.open_data import to_ecosystem_bundle

        data = load_data(DATA_PATH)
        bundle = to_ecosystem_bundle(data)
        return jsonify({"success": True, "data": bundle})
    except (ValueError, KeyError, OSError) as e:
        logger.error("Ecosystem export error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/v2/export/measurement-schema", methods=["GET"])
def export_measurement_schema():
    """Return the canonical MeasurementSchema as JSON Schema."""
    try:
        from src.api.open_data import measurement_json_schema

        schema = measurement_json_schema()
        response = app.response_class(
            json.dumps(schema, ensure_ascii=False, indent=2),
            mimetype="application/schema+json",
        )
        return response
    except Exception as e:
        logger.error("Schema export error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ── Lite UI routes (lightweight, works on slow connections) ──────────────


def _lite_ctx(lang: str) -> dict:
    """Build shared template context for lite pages."""
    return {
        "t": lambda key, **kw: get_translation(key, language=lang, **kw),
        "lang": lang,
    }


def _lang() -> str:
    """Get language from query param, default 'pt'."""
    raw = request.args.get("lang", "pt")
    return raw if raw in ("en", "pt") else "pt"


@app.route("/lite/")
def lite_dashboard():
    """Lightweight server-rendered dashboard."""
    lang = _lang()
    ctx = _lite_ctx(lang)

    data = load_data(DATA_PATH)
    total = len(data)

    if total:
        avg_dl = sum(p["speed_test"]["download"] for p in data) / total
        avg_ul = sum(p["speed_test"]["upload"] for p in data) / total
        avg_lat = sum(p["speed_test"]["latency"] for p in data) / total
        avg_q = sum(p["quality_score"]["overall_score"] for p in data) / total
    else:
        avg_dl = avg_ul = avg_lat = avg_q = 0

    providers: dict[str, dict] = {}
    ratings: dict[str, int] = {}
    for p in data:
        prov = p["provider"]
        if prov not in providers:
            providers[prov] = {"count": 0, "quality_sum": 0}
        providers[prov]["count"] += 1
        providers[prov]["quality_sum"] += p["quality_score"]["overall_score"]
        r = p["quality_score"]["rating"]
        ratings[r] = ratings.get(r, 0) + 1

    providers_list = [
        {"name": k, "count": v["count"], "avg_quality": round(v["quality_sum"] / v["count"], 1)}
        for k, v in providers.items()
    ]

    stats = {
        "total": total,
        "avg_download": round(avg_dl, 1),
        "avg_upload": round(avg_ul, 1),
        "avg_latency": round(avg_lat, 1),
        "avg_quality": round(avg_q, 1),
    }

    return render_template(
        "lite/dashboard.html",
        **ctx,
        stats=stats,
        providers=providers_list,
        ratings=ratings,
        data=data[:20],
    )


@app.route("/lite/submit", methods=["GET", "POST"])
def lite_submit():
    """Lightweight submit form — works as plain HTML POST."""
    lang = _lang()
    ctx = _lite_ctx(lang)
    form: dict = {}
    msg_ok = msg_err = None

    if request.method == "POST":
        form = dict(request.form)
        try:
            lat = float(form.get("latitude", ""))
            lon = float(form.get("longitude", ""))
            dl = float(form.get("download", ""))
            ul = float(form.get("upload", ""))
            latency = float(form.get("latency", ""))
            provider = form.get("provider", "")

            if not validate_coordinates(lat, lon):
                raise ValueError("Invalid coordinates")
            if not provider:
                raise ValueError("Provider is required")

            speed_test = SpeedTest(
                download=dl, upload=ul, latency=latency, jitter=0, packet_loss=0,
            )
            point = ConnectivityPoint(
                latitude=lat, longitude=lon, provider=provider, speed_test=speed_test,
            )

            data = load_data(DATA_PATH)
            data.append(point.to_dict())
            save_data(DATA_PATH, data)

            msg_ok = ctx["t"]("msg_success")
            form = {}  # clear form on success
        except (ValueError, TypeError, OSError) as exc:
            logger.warning("Lite submit error: %s", exc)
            msg_err = ctx["t"]("msg_error")

    return render_template(
        "lite/submit.html",
        **ctx,
        form=form,
        providers=KNOWN_PROVIDERS,
        msg_ok=msg_ok,
        msg_err=msg_err,
    )


@app.route("/lite/map")
def lite_map():
    """Lightweight map page — lazy-loads Leaflet on demand."""
    lang = _lang()
    ctx = _lite_ctx(lang)

    data = load_data(DATA_PATH)
    points = [
        {
            "latitude": p["latitude"],
            "longitude": p["longitude"],
            "provider": p["provider"],
            "download_speed": p["speed_test"]["download"],
            "upload_speed": p["speed_test"]["upload"],
            "latency": p["speed_test"]["latency"],
        }
        for p in data
    ]

    return render_template(
        "lite/map.html",
        **ctx,
        points=points,
        points_json=json.dumps(points),
    )


if __name__ == "__main__":
    # Ensure data directory exists
    Path("src/data").mkdir(parents=True, exist_ok=True)

    # Run Flask development server
    # Debug mode temporarily disabled due to auto-reload issues
    port = int(os.environ.get("PORT", 5000))
    debug_mode = False  # Temporarily disabled
    app.run(host="0.0.0.0", port=port, debug=debug_mode, use_reloader=False)
