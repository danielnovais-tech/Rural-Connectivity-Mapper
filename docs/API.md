# Rural Connectivity Mapper 2026 - API Documentation

## Table of Contents

- [Models](#models)
  - [SpeedTest](#speedtest)
  - [QualityScore](#qualityscore)
  - [ConnectivityPoint](#connectivitypoint)
- [Utilities](#utilities)
  - [Validation](#validation-utils)
  - [Data Management](#data-utils)
  - [Measurement](#measurement-utils)
  - [Geocoding](#geocoding-utils)
  - [Reporting](#report-utils)
  - [Simulation](#simulation-utils)
  - [Mapping](#mapping-utils)
  - [Analysis](#analysis-utils)

---

## Models

### SpeedTest

Represents a speed test measurement with all network metrics.

**Attributes:**

- `download` (float): Download speed in Mbps
- `upload` (float): Upload speed in Mbps
- `latency` (float): Latency in milliseconds
- `jitter` (float): Jitter in milliseconds (default: 0.0)
- `packet_loss` (float): Packet loss percentage (default: 0.0)
- `stability` (float): Connection stability score 0-100 (auto-calculated)

**Methods:**

#### `calculate_stability() -> float`

Calculate connection stability score based on jitter and packet loss.

**Returns:** Stability score from 0 to 100 (higher is better)

#### `to_dict() -> Dict`

Convert SpeedTest to dictionary representation.

**Returns:** Dictionary containing all speed test metrics

#### `from_dict(data: Dict) -> SpeedTest` (classmethod)

Create SpeedTest instance from dictionary.

**Example:**

```python
from src.models import SpeedTest

# Create a speed test
st = SpeedTest(
    download=150.0,
    upload=18.0,
    latency=25.0,
    jitter=3.0,
    packet_loss=0.2
)

print(st.stability)  # Auto-calculated: ~93.0
print(st)  # SpeedTest(download=150.0Mbps, upload=18.0Mbps, latency=25.0ms, stability=93.0)

# Serialize
st_dict = st.to_dict()

# Deserialize
restored_st = SpeedTest.from_dict(st_dict)
```

---

### QualityScore

Represents the quality score of a connectivity point.

**Attributes:**

- `overall_score` (float): Overall quality score (0-100)
- `speed_score` (float): Speed component score (0-100)
- `latency_score` (float): Latency component score (0-100)
- `stability_score` (float): Stability component score (0-100)
- `rating` (str): Quality rating (Excellent/Good/Fair/Poor)

**Class Attributes:**

- `SPEED_WEIGHT = 0.40` (40% weight)
- `LATENCY_WEIGHT = 0.30` (30% weight)
- `STABILITY_WEIGHT = 0.30` (30% weight)
- `TARGET_DOWNLOAD = 200.0` Mbps (Starlink 2026 target)
- `TARGET_UPLOAD = 20.0` Mbps
- `TARGET_LATENCY = 20.0` ms

**Methods:**

#### `calculate(speed_test: SpeedTest) -> QualityScore` (classmethod)

Calculate quality score from speed test results.

**Example:**

```python
from src.models import SpeedTest, QualityScore

st = SpeedTest(download=200.0, upload=20.0, latency=20.0)
qs = QualityScore.calculate(st)

print(qs.overall_score)  # ~95.0
print(qs.rating)  # "Excellent"
```

---

### ConnectivityPoint

Represents a connectivity measurement point with location and quality data.

**Attributes:**

- `latitude` (float): Latitude coordinate
- `longitude` (float): Longitude coordinate
- `provider` (str): Internet service provider name
- `speed_test` (SpeedTest): Speed test measurement results
- `quality_score` (QualityScore): Calculated quality score
- `timestamp` (str): ISO format timestamp (auto-generated)
- `id` (str): Unique identifier (auto-generated UUID)

**Methods:**

#### `to_dict() -> Dict`

Convert ConnectivityPoint to dictionary representation.

#### `from_dict(data: Dict) -> ConnectivityPoint` (classmethod)

Create ConnectivityPoint instance from dictionary.

**Example:**

```python
from src.models import ConnectivityPoint, SpeedTest

st = SpeedTest(download=165.4, upload=22.8, latency=28.5, jitter=3.2, packet_loss=0.1)

point = ConnectivityPoint(
    latitude=-15.7801,
    longitude=-47.9292,
    provider='Starlink',
    speed_test=st
)

print(point.quality_score.rating)  # Auto-calculated
print(point.id)  # Auto-generated UUID

# Serialize for storage
point_dict = point.to_dict()
```

---

## Utilities

### Validation Utils

Functions for validating data integrity.

#### `validate_coordinates(latitude: float, longitude: float) -> bool`

Validate geographic coordinates.

**Parameters:**

- `latitude`: Latitude value (-90 to 90)
- `longitude`: Longitude value (-180 to 180)

**Returns:** `True` if valid, `False` otherwise

**Example:**

```python
from src.utils import validate_coordinates

valid = validate_coordinates(-23.5505, -46.6333)  # True (São Paulo)
invalid = validate_coordinates(100, 200)  # False
```

#### `validate_speed_test(speed_test) -> bool`

Validate speed test measurements.

**Parameters:**

- `speed_test`: SpeedTest object or dict

**Returns:** `True` if all values are positive and required fields exist

#### `validate_provider(provider: str) -> bool`

Validate internet service provider name against known providers.

**Known Providers:** Starlink, Viasat, HughesNet, Claro, Vivo, TIM, Oi, Various, Unknown

---

### Data Utils

Functions for loading, saving, and managing data files.

#### `load_data(filepath: str) -> List[Dict]`

Load JSON data from file.

**Returns:** List of dictionaries (empty list if file doesn't exist)

#### `save_data(filepath: str, data: List[Dict]) -> None`

Save data to JSON file (creates directories if needed).

#### `backup_data(filepath: str) -> str`

Create timestamped backup of a data file.

**Returns:** Path to backup file

**Example:**

```python
from src.utils import load_data, save_data, backup_data

# Load data
data = load_data('src/data/pontos.json')

# Create backup before modification
backup_path = backup_data('src/data/pontos.json')

# Modify and save
data.append(new_point.to_dict())
save_data('src/data/pontos.json', data)
```

---

### Measurement Utils

Functions for network speed testing.

#### `measure_speed() -> Optional[Dict]`

Measure network speed using speedtest-cli.

**Returns:** Dictionary with `download`, `upload`, `latency`, `stability` or `None` if fails

**Example:**

```python
from src.utils import measure_speed

result = measure_speed()
if result:
    print(f"Download: {result['download']} Mbps")
    print(f"Upload: {result['upload']} Mbps")
    print(f"Latency: {result['latency']} ms")
```

---

### Geocoding Utils

Functions for coordinate and address conversion.

#### `geocode_coordinates(latitude: float, longitude: float, timeout: int = 10) -> Optional[str]`

Convert coordinates to address using reverse geocoding.

**Returns:** Address string or `None`

#### `geocode_address(address: str, timeout: int = 10) -> Optional[Tuple[float, float]]`

Convert address to coordinates using forward geocoding.

**Returns:** `(latitude, longitude)` tuple or `None`

**Example:**

```python
from src.utils import geocode_coordinates, geocode_address

# Reverse geocoding
address = geocode_coordinates(-23.5505, -46.6333)
print(address)  # "São Paulo, Brazil"

# Forward geocoding
coords = geocode_address("Brasília, Brazil")
print(coords)  # (-15.7801, -47.9292)
```

---

### Report Utils

Functions for multi-format report generation.

#### `generate_report(data: List[Dict], format: str, output_path: str = None) -> str`

Generate report in specified format.

**Parameters:**

- `data`: List of connectivity point dictionaries
- `format`: Report format ('json', 'csv', 'txt', 'html')
- `output_path`: Optional output file path (auto-generated if None)

**Returns:** Path to generated report file

**Example:**

```python
from src.utils import load_data, generate_report

data = load_data('src/data/pontos.json')

# Generate multiple formats
json_report = generate_report(data, 'json', 'report.json')
csv_report = generate_report(data, 'csv', 'report.csv')
html_report = generate_report(data, 'html', 'report.html')
```

---

### Simulation Utils

Functions for router impact analysis.

#### `simulate_router_impact(data: List[Dict]) -> List[Dict]`

Simulate the impact of router improvements on quality scores.

Applies random improvement of 15-25% to quality scores to simulate router upgrades.

**Returns:** Updated data with improved quality scores

**Example:**

```python
from src.utils import load_data, simulate_router_impact, save_data

data = load_data('src/data/pontos.json')
improved_data = simulate_router_impact(data)

# Save improved data
save_data('src/data/pontos_improved.json', improved_data)
```

---

### Mapping Utils

Functions for interactive map generation.

#### `generate_map(data: List[Dict], output_path: str = None) -> str`

Generate interactive Folium map from connectivity data.

**Features:**

- Color-coded markers by quality score (green/blue/orange/red)
- Popup details with provider, speed test, quality metrics
- Legend for quality ratings
- Auto-centered map based on data points

**Returns:** Path to generated HTML map file

**Example:**

```python
from src.utils import load_data, generate_map

data = load_data('src/data/pontos.json')
map_path = generate_map(data, 'connectivity_map.html')

print(f"Open {map_path} in your browser to view the map")
```

---

### Analysis Utils

Functions for temporal evolution and trends analysis.

#### `analyze_temporal_evolution(data: List[Dict]) -> Dict`

Analyze temporal evolution of connectivity quality.

**Returns:** Dictionary with:

- `total_points`: Total number of points analyzed
- `date_range`: Start date, end date, number of days
- `daily_averages`: Statistics grouped by date
- `trends`: Overall average metrics
- `insights`: List of generated insights
- `provider_stats`: Statistics by provider

**Example:**

```python
from src.utils import load_data, analyze_temporal_evolution

data = load_data('src/data/pontos.json')
analysis = analyze_temporal_evolution(data)

print(f"Average Quality Score: {analysis['trends']['avg_quality_score']}/100")
print(f"Average Download: {analysis['trends']['avg_download']} Mbps")

for insight in analysis['insights']:
    print(f"• {insight}")
```

---

## Complete Workflow Example

```python
#!/usr/bin/env python3
"""Complete workflow example."""

from src.models import ConnectivityPoint, SpeedTest
from src.utils import (
    save_data, load_data, simulate_router_impact,
    generate_report, generate_map, analyze_temporal_evolution
)

# 1. Create connectivity points
points = []

st1 = SpeedTest(download=165.4, upload=22.8, latency=28.5, jitter=3.2, packet_loss=0.1)
point1 = ConnectivityPoint(-15.7801, -47.9292, 'Starlink', st1)
points.append(point1.to_dict())

st2 = SpeedTest(download=85.2, upload=12.5, latency=45.3, jitter=8.2, packet_loss=1.2)
point2 = ConnectivityPoint(-23.5505, -46.6333, 'Various', st2)
points.append(point2.to_dict())

# 2. Save data
save_data('pontos.json', points)

# 3. Load and simulate improvements
data = load_data('pontos.json')
improved_data = simulate_router_impact(data)

# 4. Generate reports
generate_report(improved_data, 'html', 'report.html')
generate_report(improved_data, 'json', 'report.json')

# 5. Create map
generate_map(improved_data, 'map.html')

# 6. Analyze trends
analysis = analyze_temporal_evolution(improved_data)
print(f"Average Quality: {analysis['trends']['avg_quality_score']}/100")

for insight in analysis['insights']:
    print(f"• {insight}")
```

---

## Alternative Data Submission Methods

The Rural Connectivity Mapper 2026 supports multiple methods for submitting connectivity data to accommodate users with different technical skill levels:

### 1. Direct CSV Import (Current)

**Best for:** Bulk data import, automated systems, users comfortable with CSV files

```bash
python main.py --importar src/data/sample_data.csv
```

**CSV Format:**

```csv
id,city,provider,latitude,longitude,download,upload,latency,jitter,packet_loss,timestamp
1,São Paulo,Starlink,-23.5505,-46.6333,165.4,22.8,28.5,3.2,0.1,2026-01-15T10:30:00
```

**Required Fields:**

- `id` - Unique identifier
- `city` - City or location name
- `provider` - ISP name (Starlink, Viasat, HughesNet, Claro, Vivo, TIM, Oi, etc.)
- `latitude` - GPS latitude (-90 to 90)
- `longitude` - GPS longitude (-180 to 180)
- `download` - Download speed in Mbps
- `upload` - Upload speed in Mbps
- `latency` - Latency/ping in milliseconds
- `jitter` - Jitter in milliseconds (optional, default: 0)
- `packet_loss` - Packet loss percentage (optional, default: 0)
- `timestamp` - ISO 8601 format timestamp

### 2. Google Forms Integration (Recommended for Non-Technical Users)

**Best for:** Field data collection, community participation, non-technical users

Google Forms provides an easy-to-use web interface for collecting connectivity data without requiring any programming knowledge or CSV file handling skills.

**Key Features:**

- ✅ **User-Friendly** - Simple web form, no technical skills needed
- ✅ **Mobile Compatible** - Works on smartphones for field data collection
- ✅ **Free** - No cost for basic usage
- ✅ **Automatic Validation** - Built-in field validation and required fields
- ✅ **CSV Export** - Exports to CSV compatible with the mapper
- ✅ **Shareable** - Easy to distribute via link, email, or social media

**Workflow:**

1. Create Google Form with connectivity data fields
2. Share form link with users
3. Collect responses automatically in Google Sheets
4. Export to CSV format
5. Import using standard CSV import command

**Complete Setup Guide:**

See **[docs/GOOGLE_FORMS_INTEGRATION.md](GOOGLE_FORMS_INTEGRATION.md)** for:

- Step-by-step form creation instructions
- Field configuration and validation rules
- Data export and formatting procedures
- Import instructions and troubleshooting
- Sample form template

**Example:**

```bash
# After exporting from Google Forms
python main.py --importar google_forms_responses.csv --map --relatorio html
```

### 3. REST API (Future - Planned for v1.2.0)

**Best for:** Real-time data submission, mobile apps, automated systems

A REST API is planned for later in 2026 (v1.2.0 release) that will allow:

- Real-time data submission
- Real-time data retrieval
- Programmatic data retrieval
- Programmatic data submission
- Real-time data submission via HTTP POST
- JSON-based data format
- Authentication and rate limiting
- Webhooks for data updates
- Integration with mobile apps and IoT devices

**Planned Endpoints:**

- `POST /api/v1/points` - Submit new connectivity point
- `GET /api/v1/points` - Retrieve connectivity points
- `GET /api/v1/analysis` - Get analysis results

---

## CLI Usage

See README.md for complete CLI documentation.

```bash
# Import CSV data
python main.py --debug --importar src/data/sample_data.csv

# Import Google Forms export
python main.py --importar google_forms_export.csv

# Generate reports
python main.py --relatorio json
python main.py --relatorio html

# Simulate router impact
python main.py --simulate

# Generate map
python main.py --map

# Analyze temporal evolution
python main.py --analyze

# Combined workflow
python main.py --debug --importar src/data/sample_data.csv --simulate --map --analyze --relatorio html
```

---

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```
