#!/usr/bin/env python3
"""Crowdsourcing web server for rural connectivity data collection.

This server provides:
1. A mobile-friendly web form for submitting speedtest data
2. An API endpoint for programmatic submissions
3. A CSV upload endpoint for bulk data import
"""

import csv
import io
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_file

from src.config import DATA_FILE_PATH
from src.models import ConnectivityPoint, SpeedTest
from src.utils import load_data, save_data, validate_coordinates

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = DATA_FILE_PATH

# Mobile-friendly HTML form template
FORM_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rural Connectivity Mapper - Contribuir Dados</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }
        input, select, button {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:active {
            transform: translateY(0);
        }
        .helper-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .success {
            background: #4caf50;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }
        .error {
            background: #f44336;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }
        .location-btn {
            background: #2196F3;
            margin-bottom: 20px;
        }
        .required::after {
            content: " *";
            color: #f44336;
        }
        @media (max-width: 600px) {
            .container { padding: 20px; }
            h1 { font-size: 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 Rural Connectivity Mapper</h1>
        <p class="subtitle">Ajude a mapear a conectividade rural no Brasil</p>

        <button class="location-btn" onclick="getLocation()">📍 Obter Minha Localização</button>

        <form id="speedtest-form">
            <div class="form-group">
                <label class="required">Latitude</label>
                <input type="number" step="0.000001" name="latitude" id="latitude" required>
                <p class="helper-text">Ex: -15.7801 (Brasília)</p>
            </div>

            <div class="form-group">
                <label class="required">Longitude</label>
                <input type="number" step="0.000001" name="longitude" id="longitude" required>
                <p class="helper-text">Ex: -47.9292 (Brasília)</p>
            </div>

            <div class="form-group">
                <label class="required">Provedor de Internet</label>
                <select name="provider" required>
                    <option value="">Selecione...</option>
                    <option value="Starlink">Starlink</option>
                    <option value="Viasat">Viasat</option>
                    <option value="HughesNet">HughesNet</option>
                    <option value="Claro">Claro</option>
                    <option value="Vivo">Vivo</option>
                    <option value="TIM">TIM</option>
                    <option value="Oi">Oi</option>
                    <option value="Outro">Outro</option>
                </select>
            </div>

            <div class="form-group">
                <label class="required">Velocidade Download (Mbps)</label>
                <input type="number" step="0.1" name="download" required>
                <p class="helper-text">Execute um teste em fast.com ou speedtest.net</p>
            </div>

            <div class="form-group">
                <label class="required">Velocidade Upload (Mbps)</label>
                <input type="number" step="0.1" name="upload" required>
            </div>

            <div class="form-group">
                <label class="required">Latência (ms)</label>
                <input type="number" step="0.1" name="latency" required>
                <p class="helper-text">Ping em milissegundos</p>
            </div>

            <div class="form-group">
                <label>Jitter (ms) - Opcional</label>
                <input type="number" step="0.1" name="jitter" value="0">
            </div>

            <div class="form-group">
                <label>Perda de Pacotes (%) - Opcional</label>
                <input type="number" step="0.1" name="packet_loss" value="0">
            </div>

            <button type="submit">📤 Enviar Dados</button>
        </form>

        <div class="success" id="success-msg"></div>
        <div class="error" id="error-msg"></div>
    </div>

    <script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        document.getElementById('latitude').value = position.coords.latitude.toFixed(6);
                        document.getElementById('longitude').value = position.coords.longitude.toFixed(6);
                        showSuccess('Localização obtida com sucesso!');
                    },
                    error => {
                        showError('Erro ao obter localização: ' + error.message);
                    }
                );
            } else {
                showError('Geolocalização não é suportada pelo seu navegador');
            }
        }

        document.getElementById('speedtest-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);

            try {
                const response = await fetch('/api/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    showSuccess('Dados enviados com sucesso! Obrigado por contribuir!');
                    e.target.reset();
                } else {
                    showError(result.error || 'Erro ao enviar dados');
                }
            } catch (error) {
                showError('Erro de conexão: ' + error.message);
            }
        });

        function showSuccess(msg) {
            const successDiv = document.getElementById('success-msg');
            const errorDiv = document.getElementById('error-msg');
            successDiv.textContent = msg;
            successDiv.style.display = 'block';
            errorDiv.style.display = 'none';
            setTimeout(() => { successDiv.style.display = 'none'; }, 5000);
        }

        function showError(msg) {
            const successDiv = document.getElementById('success-msg');
            const errorDiv = document.getElementById('error-msg');
            errorDiv.textContent = msg;
            errorDiv.style.display = 'block';
            successDiv.style.display = 'none';
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve the mobile-friendly submission form."""
    return render_template_string(FORM_HTML)


@app.route('/api/submit', methods=['POST'])
def submit_data():
    """API endpoint to submit speedtest data.

    Expects JSON with fields:
    - latitude (float): required
    - longitude (float): required
    - provider (str): required
    - download (float): required
    - upload (float): required
    - latency (float): required
    - jitter (float): optional, default 0
    - packet_loss (float): optional, default 0

    Returns:
        JSON response with success status and point ID
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['latitude', 'longitude', 'provider', 'download', 'upload', 'latency']
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Convert string values to appropriate types
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            download = float(data['download'])
            upload = float(data['upload'])
            latency = float(data['latency'])
            jitter = float(data.get('jitter', 0))
            packet_loss = float(data.get('packet_loss', 0))
        except ValueError as e:
            return jsonify({'error': f'Invalid numeric value: {str(e)}'}), 400

        # Validate coordinates
        if not validate_coordinates(latitude, longitude):
            return jsonify({'error': 'Invalid coordinates'}), 400

        # Validate speed test values
        if download < 0 or upload < 0 or latency < 0:
            return jsonify({'error': 'Speed test values must be non-negative'}), 400

        if jitter < 0 or packet_loss < 0:
            return jsonify({'error': 'Jitter and packet loss must be non-negative'}), 400

        # Create speed test and connectivity point
        speed_test = SpeedTest(
            download=download,
            upload=upload,
            latency=latency,
            jitter=jitter,
            packet_loss=packet_loss
        )

        point = ConnectivityPoint(
            latitude=latitude,
            longitude=longitude,
            provider=data['provider'],
            speed_test=speed_test,
            timestamp=datetime.now().isoformat()
        )

        # Load existing data, append new point, and save
        existing_data = load_data(DATA_FILE)
        existing_data.append(point.to_dict())
        save_data(DATA_FILE, existing_data)

        logger.info(
            "New data point submitted: %s from provider %s", point.id, point.provider
        )

        return jsonify({
            'success': True,
            'message': 'Data submitted successfully',
            'point_id': point.id,
            'quality_score': round(point.quality_score.overall_score, 2),
            'rating': point.quality_score.rating
        }), 201

    except OSError as e:
        logger.error("Error processing submission: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """API endpoint to upload CSV file with multiple speedtest entries.

    Expects CSV file with columns:
    - latitude, longitude, provider, download, upload, latency
    - Optional: jitter, packet_loss, timestamp

    Returns:
        JSON response with count of successfully imported points
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if not file.filename or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400

        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        # Validate CSV has required columns
        required_cols = {'latitude', 'longitude', 'provider', 'download', 'upload', 'latency'}
        fieldnames = csv_reader.fieldnames if csv_reader.fieldnames is not None else []
        if not required_cols.issubset(set(fieldnames)):
            return jsonify({
                'error': f'CSV must contain columns: {", ".join(required_cols)}'
            }), 400

        # Process each row
        points = []
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (after header)
            try:
                latitude = float(row['latitude'])
                longitude = float(row['longitude'])

                if not validate_coordinates(latitude, longitude):
                    errors.append(f'Row {row_num}: Invalid coordinates')
                    continue

                speed_test = SpeedTest(
                    download=float(row['download']),
                    upload=float(row['upload']),
                    latency=float(row['latency']),
                    jitter=float(row.get('jitter', 0)),
                    packet_loss=float(row.get('packet_loss', 0))
                )

                point = ConnectivityPoint(
                    latitude=latitude,
                    longitude=longitude,
                    provider=row['provider'],
                    speed_test=speed_test,
                    timestamp=row.get('timestamp', datetime.now().isoformat())
                )

                points.append(point.to_dict())

            except (ValueError, KeyError) as e:
                errors.append(f'Row {row_num}: {str(e)}')
                continue

        if not points:
            return jsonify({
                'error': 'No valid data points in CSV',
                'errors': errors
            }), 400

        # Append to existing data
        existing_data = load_data(DATA_FILE)
        existing_data.extend(points)
        save_data(DATA_FILE, existing_data)

        logger.info("CSV upload: %s points imported, %s errors", len(points), len(errors))

        response = {
            'success': True,
            'imported': len(points),
            'message': f'Successfully imported {len(points)} data points'
        }

        if errors:
            response['warnings'] = errors

        return jsonify(response), 201

    except (UnicodeDecodeError, csv.Error) as e:
        logger.error("Error processing CSV file: %s", str(e))
        return jsonify({'error': f'Invalid CSV file: {str(e)}'}), 400
    except OSError as e:
        logger.error("File I/O error during CSV upload: %s", str(e))
        return jsonify({'error': 'Error reading or writing data file'}), 500


@app.route('/api/template')
def download_template():
    """Download CSV template for bulk upload."""
    template_data = """latitude,longitude,provider,download,upload,latency,jitter,packet_loss,timestamp
-23.5505,-46.6333,Starlink,150.0,20.0,30.0,5.0,0.5,2026-01-15T10:30:00
-15.7801,-47.9292,Vivo,85.0,12.0,45.0,8.0,1.2,2026-01-15T11:00:00"""  # noqa: E501

    output = io.BytesIO()
    output.write(template_data.encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='speedtest_template.csv'
    )


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    import os

    # Ensure data directory exists
    Path(DATA_FILE).parent.mkdir(parents=True, exist_ok=True)

    # Check if running in development mode (default to False for security)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

    # Run server
    print("\n" + "=" * 70)
    print("🌍 Rural Connectivity Mapper - Crowdsourcing Server")
    print("=" * 70)
    print("\n📱 Open in your browser:")
    print("   http://localhost:5000")
    print("\n📊 API Endpoints:")
    print("   POST /api/submit        - Submit single speedtest")
    print("   POST /api/upload-csv    - Upload CSV file")
    print("   GET  /api/template      - Download CSV template")
    print("   GET  /health            - Health check")

    if debug_mode:
        print("\n⚠️  WARNING: Running in DEBUG mode - NOT for production!")
    else:
        print("\n✓ Running in production mode")
        print("  To enable debug mode, set: export FLASK_DEBUG=True")

    print("\n" + "=" * 70 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
