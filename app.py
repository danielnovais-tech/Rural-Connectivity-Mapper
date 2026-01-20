#!/usr/bin/env python3
"""Flask web application for Rural Connectivity Mapper 2026"""

import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
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

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data file path
DATA_PATH = 'src/data/pontos.json'


@app.route('/')
def index():
    """Render main dashboard page."""
    return render_template('index.html')


@app.route('/api/data', methods=['GET'])
def get_data():
    """Get all connectivity data points.

    Returns:
        JSON: List of connectivity points
    """
    try:
        data = load_data(DATA_PATH)
        return jsonify({
            'success': True,
            'data': data,
            'total': len(data)
        })
    except (ValueError, KeyError, OSError) as e:
        logger.error("Error loading data: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/data/<point_id>', methods=['GET'])
def get_data_point(point_id):
    """Get a specific connectivity data point.

    Args:
        point_id: ID of the data point

    Returns:
        JSON: Connectivity point data
    """
    try:
        data = load_data(DATA_PATH)
        point = next((p for p in data if p.get('id') == point_id), None)

        if point:
            return jsonify({
                'success': True,
                'data': point
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data point not found'
            }), 404
    except (ValueError, KeyError, OSError) as e:
        logger.error("Error loading data point: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/data', methods=['POST'])
def add_data_point():
    """Add a new connectivity data point.

    Returns:
        JSON: Success status and created point
    """
    try:
        data_json = request.get_json()

        # Validate required fields
        required_fields = ['latitude', 'longitude', 'provider', 'download', 'upload', 'latency']
        for field in required_fields:
            if field not in data_json:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Validate coordinates
        lat = float(data_json['latitude'])
        lon = float(data_json['longitude'])

        if not validate_coordinates(lat, lon):
            return jsonify({
                'success': False,
                'error': 'Invalid coordinates'
            }), 400

        # Create SpeedTest
        speed_test = SpeedTest(
            download=float(data_json['download']),
            upload=float(data_json['upload']),
            latency=float(data_json['latency']),
            jitter=float(data_json.get('jitter', 0)),
            packet_loss=float(data_json.get('packet_loss', 0))
        )

        # Create ConnectivityPoint
        point = ConnectivityPoint(
            latitude=lat,
            longitude=lon,
            provider=data_json['provider'],
            speed_test=speed_test,
            timestamp=data_json.get('timestamp', datetime.now().isoformat()),
            point_id=data_json.get('id')
        )

        # Load existing data and append new point
        data = load_data(DATA_PATH)
        data.append(point.to_dict())
        save_data(DATA_PATH, data)

        return jsonify({
            'success': True,
            'data': point.to_dict(),
            'message': 'Data point added successfully'
        }), 201

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid value: {str(e)}'
        }), 400
    except (KeyError, TypeError, OSError, IOError) as e:
        logger.error("Error adding data point: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get overall connectivity statistics.

    Returns:
        JSON: Statistics summary
    """
    try:
        data = load_data(DATA_PATH)

        if not data:
            return jsonify({
                'success': True,
                'statistics': {
                    'total_points': 0,
                    'avg_quality_score': 0,
                    'avg_download': 0,
                    'avg_upload': 0,
                    'avg_latency': 0
                }
            })

        # Calculate statistics
        total_points = len(data)
        avg_quality_score = sum(p['quality_score']['overall_score'] for p in data) / total_points
        avg_download = sum(p['speed_test']['download'] for p in data) / total_points
        avg_upload = sum(p['speed_test']['upload'] for p in data) / total_points
        avg_latency = sum(p['speed_test']['latency'] for p in data) / total_points

        # Count by rating
        ratings = {}
        for point in data:
            rating = point['quality_score']['rating']
            ratings[rating] = ratings.get(rating, 0) + 1

        # Count by provider
        providers = {}
        for point in data:
            provider = point['provider']
            providers[provider] = providers.get(provider, 0) + 1

        return jsonify({
            'success': True,
            'statistics': {
                'total_points': total_points,
                'avg_quality_score': round(avg_quality_score, 2),
                'avg_download': round(avg_download, 2),
                'avg_upload': round(avg_upload, 2),
                'avg_latency': round(avg_latency, 2),
                'ratings': ratings,
                'providers': providers
            }
        })
    except (ValueError, KeyError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error("Error calculating statistics: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """Get temporal analysis of connectivity data.

    Returns:
        JSON: Temporal analysis results
    """
    try:
        data = load_data(DATA_PATH)
        analysis = analyze_temporal_evolution(data)

        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.error("Error performing analysis: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/simulate', methods=['POST'])
def simulate_improvement():
    """Simulate router impact on quality scores.

    Returns:
        JSON: Success status and message
    """
    try:
        data = load_data(DATA_PATH)
        improved_data = simulate_router_impact(data)
        save_data(DATA_PATH, improved_data)

        return jsonify({
            'success': True,
            'message': 'Router impact simulation completed',
            'data': improved_data
        })
    except (ValueError, KeyError, OSError, TypeError) as e:
        logger.error("Error simulating improvement: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/report/<report_format>', methods=['GET'])
def generate_report_api(report_format):
    """Generate report in specified format.

    Args:
        report_format: Report format (json, csv, txt, html)

    Returns:
        File download or JSON response
    """
    try:
        if report_format not in ['json', 'csv', 'txt', 'html']:
            return jsonify({
                'success': False,
                'error': 'Invalid format. Choose from: json, csv, txt, html'
            }), 400

        data = load_data(DATA_PATH)
        report_path = generate_report(data, report_format, f'report.{report_format}')

        return send_file(
            report_path,
            as_attachment=True,
            download_name=f'connectivity_report.{report_format}'
        )
    except (ValueError, KeyError, OSError, IOError, TypeError) as e:
        logger.error("Error generating report: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/map', methods=['GET'])
def get_map():
    """Generate interactive connectivity map.

    Returns:
        HTML: Interactive Folium map
    """
    try:
        data = load_data(DATA_PATH)

        # Create a temporary file for the map
        fd, temp_path = tempfile.mkstemp(suffix='.html', prefix='connectivity_map_')
        os.close(fd)

        map_path = generate_map(data, temp_path)

        # Send file and delete after sending
        response = send_file(map_path, mimetype='text/html')

        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except OSError:
                pass

        return response
    except (ValueError, KeyError, OSError, IOError, TypeError, ImportError) as e:
        logger.error("Error generating map: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint.

    Returns:
        JSON: Health status
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    # Ensure data directory exists
    Path('src/data').mkdir(parents=True, exist_ok=True)

    # Run Flask development server
    # Debug mode is only enabled in development (when FLASK_ENV is not set to production)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
