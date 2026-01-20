# Web Dashboard Quick Start Guide

## 🚀 Getting Started

### Prerequisites

- Clone the repository:

  ```bash
  git clone https://github.com/yourusername/Rural-Connectivity-Mapper-2026.git
  ```

- Python 3.8+
- pip package manager
- All dependencies installed (`pip install -r requirements.txt`)

### Starting the Web Dashboard

1. **Navigate to the project directory:**

   ```bash
   cd Rural-Connectivity-Mapper-2026
   ```

2. **Start the Flask application:**

   ```bash
   python app.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5000`

The dashboard will automatically load and display connectivity data from `src/data/pontos.json`.

---

## 📊 Dashboard Features

### Main Statistics Cards

- **Total Points** - Number of connectivity measurement points
- **Avg Quality Score** - Overall quality rating (0-100)
- **Avg Download** - Average download speed in Mbps
- **Avg Latency** - Average latency in milliseconds

### Data Panels

#### Connectivity Data Table

Displays all measurement points with:

- Provider name
- Quality score and rating (Excellent/Good/Fair/Poor)
- Download/Upload speeds
- Latency measurements

Color-coded by quality rating:

- 🟢 **Excellent** (≥80) - Green
- 🔵 **Good** (60-79) - Blue
- 🟡 **Fair** (40-59) - Orange
- 🔴 **Poor** (<40) - Red

#### Provider Distribution

Shows count of measurement points per ISP provider

#### Rating Distribution

Breakdown of quality ratings across all points

#### Key Insights

AI-powered analysis and recommendations based on the data

---

## 🗺️ Interactive Map

Click the **"Load Map"** button to view an interactive Folium map showing:

- Geographic distribution of measurement points
- Color-coded markers based on quality scores
- Popup details for each location

---

## ⚡ Actions

### Refresh Data

Reloads all statistics and tables from the current data file

### Simulate Router Impact

Applies a 15-25% quality improvement simulation to all data points, modeling the effect of router upgrades

### Download Reports

Generate and download reports in multiple formats:

- **JSON** - Structured data format
- **CSV** - Spreadsheet compatible
- **HTML** - Formatted web page

---

## 🔌 REST API Endpoints

The web dashboard is backed by a full REST API that can be accessed programmatically:

### Data Management

- `GET /api/data` - Get all connectivity points
- `GET /api/data/<id>` - Get specific point by ID
- `POST /api/data` - Add new connectivity point

### Analytics

- `GET /api/statistics` - Get summary statistics
- `GET /api/analysis` - Get temporal analysis

### Operations

- `POST /api/simulate` - Simulate router improvements
- `GET /api/report/<format>` - Generate report (json/csv/txt/html)
- `GET /api/map` - Generate interactive map

### Utility

- `GET /api/health` - Health check

---

## 📝 Adding Data via API

Example using curl:

```bash
curl -X POST http://localhost:5000/api/data \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -23.5505,
    "longitude": -46.6333,
    "provider": "Starlink",
    "download": 165.4,
    "upload": 22.8,
    "latency": 28.5,
    "jitter": 3.2,
    "packet_loss": 0.1
  }'
```

Example using Python:

```python
import requests

data = {
    "latitude": -23.5505,
    "longitude": -46.6333,
    "provider": "Starlink",
    "download": 165.4,
    "upload": 22.8,
    "latency": 28.5,
    "jitter": 3.2,
    "packet_loss": 0.1
}

response = requests.post('http://localhost:5000/api/data', json=data)
print(response.json())
```

---

## 🛠️ Troubleshooting

### Port Already in Use

If port 5000 is already in use, set a different port:

```bash
PORT=8000 python app.py
```

### Data Not Loading

Ensure `src/data/pontos.json` exists and contains valid data. Run the demo workflow first:

```bash
python demo_workflow.py
```

### Map Not Displaying

The map requires internet access to load external resources (Leaflet, etc.). If offline, map functionality may be limited.

---

## 🔒 Production Deployment

**Important:** The built-in Flask server is for development only. For production deployment:

1. Use a production WSGI server like Gunicorn:

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. Set up a reverse proxy (nginx/Apache)

3. Enable HTTPS/SSL

4. Configure proper authentication/authorization

5. Set environment variables:

   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secret-key
   ```

---

## 📚 Additional Resources

- [Main README](../README.md) - Full project documentation
- [API Documentation](../docs/API.md) - Detailed API reference
- [GitHub Repository](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026)

---

**Made with ❤️ for improving rural connectivity in Brazil**
