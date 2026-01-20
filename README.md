# Rural Connectivity Mapper 2026

[![CI](https://img.shields.io/github/actions/workflow/status/danielnovais-tech/Rural-Connectivity-Mapper-2026/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/actions/workflows/ci.yml)
[![Lint](https://img.shields.io/github/actions/workflow/status/danielnovais-tech/Rural-Connectivity-Mapper-2026/lint.yml?branch=main&style=flat-square&label=Lint)](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/actions/workflows/lint.yml)
[![GitHub License](https://img.shields.io/github/license/danielnovais-tech/Rural-Connectivity-Mapper-2026?style=flat-square)](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/danielnovais-tech/Rural-Connectivity-Mapper-2026?style=flat-square)](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/danielnovais-tech/Rural-Connectivity-Mapper-2026?style=flat-square)](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/network)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)](https://www.python.org/downloads/)
[![Last Commit](https://img.shields.io/github/last-commit/danielnovais-tech/Rural-Connectivity-Mapper-2026?style=flat-square)](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/commits/main)
[![Release](https://img.shields.io/github/v/release/danielnovais-tech/Rural-Connectivity-Mapper-2026?style=flat-square)](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/releases/latest)
[![codecov](https://img.shields.io/badge/coverage-83%25-green?style=flat-square)](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026)

Python-based tool to map and analyze rural internet connectivity across Latin America, aligned with Starlink's 2026 expansion roadmap.

## 🌍 Overview

The Rural Connectivity Mapper 2026 is a comprehensive platform for analyzing and visualizing internet connectivity quality across Latin America, with a focus on Starlink's satellite internet expansion. The tool measures, analyzes, and reports on connectivity metrics including download/upload speeds, latency, stability, and overall quality scores.

**NEW in v1.1:** Real ANATEL & IBGE data integration, Starlink API, Interactive Streamlit Dashboard, and support for 10 LATAM countries!

Python-based tool to map and analyze rural internet connectivity worldwide, aligned with Starlink's 2026 expansion roadmap.

## 🌐 Global Connectivity Analysis

The Rural Connectivity Mapper 2026 is a comprehensive platform for analyzing and visualizing internet connectivity quality across multiple countries, with a focus on Starlink's satellite internet expansion. The tool measures, analyzes, and reports on connectivity metrics including download/upload speeds, latency, stability, and overall quality scores.

**Multi-Country Support:** Now supports 9 countries with country-specific provider lists and localized settings.

**Aligned with Starlink's 2026 roadmap:** 10M rural connections & 20-30% agricultural productivity gains.

---

# !/usr/bin/env python3

"""
README Cleanup and Reorganization Script

This script processes the messy, repetitive README content and produces
a clean, organized version by:

1. Removing duplicate sections and content
2. Fixing version inconsistencies
3. Consolidating features and statistics
4. Standardizing installation and usage instructions
"""

import re
from collections import OrderedDict
from datetime import datetime
from typing import List, Dict, Tuple

class READMECleaner:
    def **init**(self, input_content: str):
        self.input_content = input_content
        self.clean_content = ""
        self.sections = OrderedDict()
        self.version = "1.1.0"
        self.current_date = datetime.now().strftime("%B %d, %Y")

    def parse_sections(self):
        """Parse the messy README into logical sections"""
        lines = self.input_content.split('\n')
        current_section = "header"
        section_content = []
        
        for line in lines:
            # Check for section headers
            if line.strip().startswith('# '):
                if current_section != "header":
                    self.sections[current_section] = '\n'.join(section_content)
                current_section = line.strip('# ').strip()
                section_content = [line]
            elif line.strip().startswith('## '):
                if current_section and section_content:
                    self.sections[current_section] = '\n'.join(section_content)
                current_section = line.strip('# ').strip()
                section_content = [line]
            else:
                section_content.append(line)
        
        # Add the last section
        if section_content:
            self.sections[current_section] = '\n'.join(section_content)
    
    def remove_duplicates(self, text: str) -> str:
        """Remove duplicate lines and sections from text"""
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        
        for line in lines:
            # Normalize line for comparison (strip extra spaces, ignore markdown symbols)
            normalized = re.sub(r'[#\-\*]', '', line).strip()
            if not normalized or normalized not in seen:
                seen.add(normalized)
                unique_lines.append(line)
            elif line.strip().startswith('#'):
                # Keep section headers even if duplicate content
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def consolidate_features(self) -> str:
        """Consolidate all feature lists into a single, organized list"""
        features = {
            "Core Functionality": [
                "🌐 **Multi-Country Support** - 10 LATAM countries (BR, AR, CL, CO, MX, PE, EC, UY, PY, BO)",
                "📊 **Data Integration** - ANATEL, IBGE, and Starlink API integration",
                "🖥️ **CLI Application** - Full command-line interface with 7 operational modes",
                "📱 **Web Dashboard** - Interactive Streamlit dashboard with real-time visualization",
            ],
            "Data Analysis": [
                "📈 **Temporal Analysis** - Track connectivity trends over time",
                "🏢 **Provider Comparison** - Benchmark ISPs with country-specific lists",
                "🧮 **Quality Scoring** - Comprehensive algorithm with 2026 metrics",
                "🤖 **ML-Enhanced Analysis** - Machine learning for rural connectivity optimization",
            ],
            "Visualization": [
                "🗺️ **Interactive Maps** - Folium maps with color-coded quality markers",
                "🛰️ **Starlink Coverage** - Coverage zones and signal strength visualization",
                "📊 **Chart Visualizations** - Plotly charts for data exploration",
            ],
            "Data Management": [
                "📤 **CSV Upload & Validation** - Easy data import with validation",
                "📋 **Multi-Format Export** - JSON, CSV, TXT, HTML reports",
                "🔗 **Ecosystem Integration** - Export for Hybrid Architecture Simulator & AgriX-Boost",
                "🌐 **REST API** - Full API for data management and integration",
            ],
            "Deployment & Testing": [
                "🐳 **Docker Support** - Containerized deployment for rural environments",
                "🧪 **Comprehensive Testing** - 73+ tests with 80%+ code coverage",
                "⚙️ **CI/CD Pipeline** - GitHub Actions for automated testing and deployment",
            ]
        }
        
        features_text = "## ✨ Features\n\n"
        for category, feature_list in features.items():
            features_text += f"### {category}\n\n"
            for feature in feature_list:
                features_text += f"- {feature}\n"
            features_text += "\n"
        
        return features_text
    
    def consolidate_installation(self) -> str:
        """Consolidate installation instructions"""
        return """## 🚀 Installation

## 🚀 Installation

### Requirements

- **Python 3.8+** or **Docker**
- Internet connection (for geocoding and speedtest APIs)
- Git (for cloning repository)

### Quick Install (Local)

```bash
# Clone the repository
git clone https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026.git
cd Rural-Connectivity-Mapper-2026

# Install dependencies
pip install -r requirements.txt

# Run demo workflow
python demo_workflow.py
```

### Quick Install (Docker Compose)

```bash
# Clone and run with Docker Compose
git clone https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026.git
cd Rural-Connectivity-Mapper-2026
docker compose up

# Install dependencies
pip install -r requirements.txt

# Run demo workflow
python demo_workflow.py
```

### Dependencies

```text
    """Consolidate usage instructions"""
    return """## 📖 Usage


```

**💡 For production deployments, migrations, and rollback procedures, see [DEPLOYMENT.md](DEPLOYMENT.md)**

### 🐳 Docker Installation (Recommended for Rural Deployments)

Docker containerization simplifies deployment on rural servers, Raspberry Pi, or farm test environments by avoiding dependency conflicts (including speedtest-cli issues).

#### Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose (optional, included with Docker Desktop)

#### Quick Start with Docker

**Option 1: Using Docker Compose (Easiest)**

```bash
# Clone the repository
git clone https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026.git
cd Rural-Connectivity-Mapper-2026

# Run demo workflow in container
docker compose up

# Generated reports will be in the current directory:
# - demo_report.json, .csv, .txt, .html
# - demo_connectivity_map.html

```

**Option 2: Using Docker directly**

```bash
# Build the Docker image
docker build -t rural-connectivity-mapper .

# Run demo workflow (files generated inside container)
docker run --rm rural-connectivity-mapper

# Run demo workflow with volume mount to persist files in current directory
docker run --rm -v $(pwd):/app rural-connectivity-mapper

# Run CLI commands with volume mount
docker run --rm -v $(pwd):/app rural-connectivity-mapper \
  python main.py --importar src/data/sample_data.csv --relatorio html

# Run with debug mode
docker run --rm -v $(pwd):/app rural-connectivity-mapper \
  python main.py --debug --simulate --map --analyze

```

#### Docker CLI Examples

```bash
# Generate all report formats
docker run --rm -v $(pwd):/app rural-connectivity-mapper \
  python main.py --importar src/data/sample_data.csv --relatorio json

# Create interactive map
docker run --rm -v $(pwd):/app rural-connectivity-mapper \
  python main.py --importar src/data/sample_data.csv --map

# Simulate router improvements and analyze
docker run --rm -v $(pwd):/app rural-connectivity-mapper \
  python main.py --importar src/data/sample_data.csv --simulate --analyze --relatorio html

# Use custom CSV data
docker run --rm \
  -v $(pwd):/app \
  -v $(pwd)/my_data.csv:/app/data.csv \
  rural-connectivity-mapper \
  python main.py --importar /app/data.csv --map --relatorio json

# Run with Docker Compose for one-off commands
docker compose run --rm rural-mapper python main.py --help
docker compose run --rm rural-mapper python main.py --importar src/data/sample_data.csv --map

# List supported countries
python main.py --list-countries

# Import data and generate report
python main.py --importar data.csv --country BR --relatorio html

# Create interactive map
python main.py --importar data.csv --map --starlink-coverage

# Analyze trends
python main.py --importar data.csv --analyze --language pt

# ML-enhanced analysis
python main.py --importar data.csv --ml-analyze

# Ecosystem integration exports
python main.py --export ecosystem


```

#### Production Deployment Notes

For production environments, consider these security best practices:

```bash
# Use specific volume mounts instead of mounting entire directory
docker run --rm \
  -v $(pwd)/src/data:/app/src/data:ro \
  -v $(pwd)/output:/app/output \
  rural-connectivity-mapper

# Or run without volume mounts for isolated operation
docker run --rm rural-connectivity-mapper python main.py --help

```

#### Benefits for Rural Deployments

- ✅ **No dependency conflicts** - All dependencies pre-installed
- ✅ **Works on Raspberry Pi** - ARM-compatible base image
- ✅ **Consistent environment** - Same behavior across all systems
- ✅ **Easy updates** - Just pull new image
- ✅ **Isolated from host** - Won't affect local Python environment
- ✅ **Speedtest-cli included** - No manual installation needed

---

## 📖 Usage

### 🌐 Web Dashboard (NEW in v1.1)

Launch the interactive Streamlit dashboard for browser-based analysis:

### Quick Start - Streamlit Dashboard (NEW!)

Launch the interactive web dashboard:

```bash
streamlit run dashboard.py
```

**Dashboard Features:**

- **📊 Dashboard Overview** - View statistics, data table, and generate reports
- **📤 Upload Data** - Import CSV files with connectivity data
- **🚀 Speed Test** - Run on-demand speed tests on your current connection
- **🗺️ Map View** - Interactive Folium maps with color-coded quality markers
- **📈 Analysis** - Temporal evolution trends and insights
- **🔧 Simulation** - Model router impact on connectivity quality

**CSV Upload Format:**

```csv
id,city,provider,latitude,longitude,download,upload,latency,jitter,packet_loss,timestamp
1,São Paulo,Starlink,-23.5505,-46.6333,165.4,22.8,28.5,3.2,0.1,2026-01-15T10:30:00
```

The dashboard automatically opens at `http://localhost:8501` and provides a user-friendly interface for all connectivity analysis tasks.

**Features:**

- 🌍 Select from 10 LATAM countries
- 📊 View ANATEL broadband and mobile data
- 👥 Explore IBGE demographic statistics
- 🛰️ Check Starlink availability and service plans
- 🌎 Compare connectivity across LATAM countries
- 🗺️ Interactive maps with real-time data

### Web Dashboard (NEW! 🎉)

Start the web-based dashboard for a modern GUI experience:

```bash
python app.py
```

Then open your browser to `http://localhost:5000`

**Dashboard Features:**

- 📊 Real-time connectivity statistics and KPIs
- 📈 Interactive data tables with provider/rating distributions
- 🗺️ Embedded interactive Folium maps
- 💡 AI-powered insights and recommendations
- ⚡ One-click router impact simulation
- 📥 Download reports in multiple formats (JSON, CSV, HTML)
- 🔄 Live data refresh capabilities

**REST API Endpoints:**

- `GET /api/data` - Retrieve all connectivity points
- `GET /api/data/<id>` - Get specific point by ID
- `POST /api/data` - Add new connectivity point
- `GET /api/statistics` - Get summary statistics
- `GET /api/analysis` - Get temporal analysis
- `POST /api/simulate` - Simulate router improvements
- `GET /api/report/<format>` - Generate and download reports
- `GET /api/map` - Generate interactive map
- `GET /api/health` - Health check endpoint

---

## 📖 CLI Usage

### Quick Start - CSV Upload Script ⚡

**Lowest barrier to entry for contributors and rural testers!**

Upload and validate speedtest data with a single command:

```bash
python upload_csv.py example_speedtests.csv
```

**Key Features:**

- ✅ Validates schema (timestamp, lat/lon, download/upload) before processing
- 📊 Detailed validation reports with clear error messages
- 🚀 Easy to demo and document with included `example_speedtests.csv`
- 💾 Outputs clean JSON format ready for further analysis

**Usage Examples:**

```bash
# Basic upload with validation
python upload_csv.py example_speedtests.csv

# Custom output file
python upload_csv.py my_data.csv --output results.json

# Dry-run mode (validate without saving)
python upload_csv.py data.csv --dry-run --verbose
```

**Required CSV Columns:** `timestamp`, `latitude`, `longitude`, `download`, `upload`  
**Optional CSV Columns:** `id`, `city`, `provider`, `latency`, `jitter`, `packet_loss`

See `example_speedtests.csv` for a complete sample file with 10 test locations across Brazil.

### Quick Start - Demo Workflow

Run the complete demo to see all features:

```bash
python demo_workflow.py
```

**Auto-generates:**

- `demo_report.json`, `.csv`, `.txt`, `.html`
- `demo_connectivity_map.html` (interactive map)
- Console output with statistics

### Starlink API Demo

Test the Starlink API module for provider comparison:

```bash
python demo_starlink_api.py
```

**Features demonstrated:**

- Coverage data retrieval with API fallback
- Performance metrics for multiple locations
- Provider comparison (Starlink vs. Viasat vs. HughesNet)
- Quality score calculations and recommendations
- `demo_connectivity_map.html` (interactive map)
- Console output with statistics

### CLI Commands

#### List Available Countries

#### 🌍 Crowdsourced Data Collection (NEW!)

**Start the web server for data collection:**

```bash
python crowdsource_server.py
```

*Opens a mobile-friendly web form at <http://localhost:5000>*

**Submit data via command line:**

```bash
# Interactive mode - guided prompts
python submit_speedtest.py

# Direct submission with arguments
python submit_speedtest.py -lat -23.5505 -lon -46.6333 \
  -p Starlink -d 150.0 -u 20.0 -l 30.0

# Auto-run speedtest and submit
python submit_speedtest.py --auto-speedtest -p Starlink
```

**See full crowdsourcing guide:** [docs/CROWDSOURCING.md](docs/CROWDSOURCING.md)

---

#### Import Data

```bash
python main.py --list-countries
```

*Shows all supported country codes and names*

#### Import Data (with Country)

```bash
python main.py --importar src/data/sample_data.csv --country BR
python main.py --importar src/data/sample_data_us.csv --country US
```

#### Generate Reports

```bash

python main.py --relatorio html    # HTML report (default country)
python main.py --relatorio json --country US    # JSON report for US
python main.py --relatorio csv --country CA     # CSV report for Canada

python main.py --relatorio html    # HTML report (English)
python main.py --relatorio json    # JSON report
python main.py --relatorio csv     # CSV report

python main.py --relatorio txt     # Text report

# Generate reports in Portuguese
python main.py --relatorio html --language pt    # HTML report in Portuguese
python main.py --relatorio txt --lang pt         # Text report in Portuguese
```

#### Simulate Router Improvements

```bash
python main.py --simulate
python main.py --simulate --country US
```

*Models 15-25% quality score boost from router upgrades*

#### Create Interactive Map

```bash
python main.py --map
python main.py --map --country US  # Map centered on United States
```

*Generates Folium HTML map with color-coded markers and Starlink coverage zones*

*Generates Folium HTML map with color-coded markers and country-specific center*

#### Create Map with Starlink Coverage Overlay

```bash
python main.py --map --starlink-coverage
```

*Generates interactive map with optional Starlink coverage zones showing Active, Planned, and Limited coverage areas. Helps farmers identify optimal installation locations.*

#### Analyze Temporal Evolution (with Country Selection)

```bash
python main.py --analyze
python main.py --analyze --country GB  # Analyze UK data

*Generates Folium HTML map with color-coded markers and Starlink coverage overlay*

#### Create Map Without Starlink Coverage
```bash
python main.py --map --no-starlink-coverage
```

*Generates map without the coverage layer for simplified view*

#### Analyze Temporal Evolution

```bash
python main.py --analyze                # Analyze in English
python main.py --analyze --language pt  # Analyze in Portuguese

```

*Shows trends, insights, provider statistics in selected language*

#### **NEW: ML-Enhanced Geospatial Analysis**

```bash
python main.py --ml-analyze
```

*Perform machine learning analysis for:*

- Rural area identification and prioritization
- Starlink expansion zone recommendations
- ROI analysis for satellite internet deployment
- Improvement potential predictions

#### Enable Debug Mode

```bash
python main.py --debug --importar data.csv --country DE
```

#### Combined Workflow

```bash
python main.py --debug \
  --country US \
  --importar src/data/sample_data_us.csv \
  --simulate \
  --map \
  --starlink-coverage \
  --analyze \
  --ml-analyze \
  --relatorio html
```

### Using the New Data Integration Features

#### Fetch ANATEL Data

```python
from src.utils import fetch_anatel_broadband_data, fetch_anatel_mobile_data

# Get broadband data
broadband = fetch_anatel_broadband_data(state='SP')

# Get mobile coverage data
mobile = fetch_anatel_mobile_data(state='RJ')
```

#### Fetch IBGE Demographics

```python
from src.utils import get_rural_areas_needing_connectivity, get_ibge_statistics_summary

# Get priority rural areas
priority_areas = get_rural_areas_needing_connectivity()

# Get Brazil connectivity summary
summary = get_ibge_statistics_summary()
```

#### Check Starlink Availability

```python
from src.utils import check_starlink_availability, get_starlink_service_plans

# Check availability at coordinates
availability = check_starlink_availability(-15.7801, -47.9292)

# Get service plans
plans = get_starlink_service_plans()
```

#### Work with LATAM Countries

```python
from src.utils import get_supported_countries, get_country_config

# Get all supported countries
countries = get_supported_countries()  # ['BR', 'AR', 'CL', 'CO', 'MX', ...]

# Get country configuration
config = get_country_config('AR')
print(config.name)  # 'Argentina'
print(config.telecom_regulator)  # 'ENACOM'
```

#### Export for Ecosystem Integration

```bash
# Export for Hybrid Architecture Simulator
python main.py --export hybrid

# Export for AgriX-Boost
python main.py --export agrix

# Export complete ecosystem bundle
python main.py --export ecosystem
```

*Generates data exports for integration with Hybrid Architecture Simulator (failover testing) and AgriX-Boost (farm dashboards)*

### CLI Arguments Reference

| Argument | Description | Choices/Format |
| -------- | ----------- | -------------- |
| `--debug` | Enable verbose logging | Flag |
| `--country <code>` | ISO country code | BR, US, CA, GB, AU, DE, FR, IN, MX |
| `--list-countries` | List all available countries | Flag |
| `--relatorio <format>` | Generate report | json, csv, txt, html |
| `--importar <csv>` | Import from CSV | Path to file |
| `--simulate` | Simulate router impact | Flag |
| `--map` | Generate interactive map | Flag |
| `--starlink-coverage` | Add Starlink coverage overlay | Flag (requires --map) |
| `--no-starlink-coverage` | Disable Starlink coverage overlay | Flag (use with --map) |
| `--analyze` | Analyze temporal trends | Flag |
| `--ml-analyze` | **NEW:** ML-enhanced geospatial analysis | Flag |
| `--language <code>` or `--lang <code>` | Language for reports/analysis | en (English), pt (Portuguese) |
| `--export <target>` | Export for ecosystem integration | hybrid, agrix, ecosystem |

def get_supported_countries(self) -> str:
    """Generate supported countries table"""
    countries = [
        ("🇧🇷 Brazil", "BR", "ANATEL", "IBGE", "Active (98.5% coverage)"),
        ("🇦🇷 Argentina", "AR", "ENACOM", "INDEC", "Active (97.0% coverage)"),
        ("🇨🇱 Chile", "CL", "SUBTEL", "INE", "Active (98.0% coverage)"),
        ("🇨🇴 Colombia", "CO", "CRC", "DANE", "Active (90.0% coverage)"),
        ("🇲🇽 Mexico", "MX", "IFT", "INEGI", "Active (95.0% coverage)"),
        ("🇵🇪 Peru", "PE", "OSIPTEL", "INEI", "Active (88.0% coverage)"),
        ("🇪🇨 Ecuador", "EC", "ARCOTEL", "INEC", "Active"),
        ("🇺🇾 Uruguay", "UY", "URSEC", "INE", "Active"),
        ("🇵🇾 Paraguay", "PY", "CONATEL", "DGEEC", "Active"),
        ("🇧🇴 Bolivia", "BO", "ATT", "INE", "Active"),
    ]

    table = "## 🌎 Supported Countries\n\n"
    table += "| Country | Code | Telecom Regulator | Stats Agency | Starlink Status |\n"
    table += "|---------|------|-------------------|--------------|-----------------|\n"
    
    for name, code, regulator, stats, status in countries:
        table += f"| {name} | {code} | {regulator} | {stats} | {status} |\n"
    
    return table

def get_project_stats(self) -> str:
    """Generate consistent project statistics"""
    return f"""## 📊 Project Statistics

### Alternative Data Submission Methods

#### 📝 Google Forms Integration (Recommended for Non-Technical Users)

For users who are not comfortable with CSV files or command-line tools, we provide **Google Forms integration** as an easy alternative for data collection.

**Benefits:**

- ✅ No technical knowledge required
- ✅ Mobile-friendly for field data collection
- ✅ Free and easy to share
- ✅ Automatic data validation
- ✅ Exports to CSV format compatible with the mapper

**Quick Start:**

1. Create a Google Form using our template
2. Share the form link with users
3. Collect responses in Google Sheets
4. Export to CSV and import using `--importar`

**📖 Complete Guide:** See [docs/GOOGLE_FORMS_INTEGRATION.md](docs/GOOGLE_FORMS_INTEGRATION.md) for detailed instructions on:

- Setting up your Google Form
- Configuring fields and validation
- Exporting and formatting data
- Importing into the mapper
- Troubleshooting common issues

**Example Workflow:**

```bash
# After exporting from Google Forms to CSV
python main.py --importar google_forms_export.csv --map --relatorio html
```

---

## 🛰️ Starlink Coverage Layer

The interactive maps now include **Starlink coverage visualization** for rural Brazil:

### Features

- **Coverage Zones**: 5 major regions showing satellite signal strength
  - Central Brazil (Brasília) - Excellent coverage
  - Southeast Brazil (São Paulo/Rio) - Excellent coverage
  - South Brazil - Good coverage
  - Northeast Brazil - Good coverage
  - North Brazil (Amazon) - Expanding coverage

- **Signal Points**: 11+ locations with actual signal strength measurements (0-100)
- **Toggle Layers**: Use the layer control to show/hide:
  - Starlink Coverage Zones
  - Starlink Signal Points
  - Speedtest Data Points

- **Color Coding**:
  - 🟢 Green: Excellent signal (85+/100)
  - 🟡 Yellow: Good signal (70-84/100)
  - 🟠 Orange: Fair signal (50-69/100)

### Implementation Note

Currently uses **simulated coverage data** based on Starlink's 2026 expansion roadmap. The architecture is ready to integrate with official Starlink APIs when available. Coverage zones reflect known deployment priorities and satellite constellation patterns.

### Using the Map

1. Generate a map: `python main.py --map`
2. Open the HTML file in your browser
3. Use the **Layer Control** (top right) to toggle different layers
4. Click on markers and zones to see detailed information
5. The **Legend** (bottom right) explains all indicators

---

## 📁 Project Structure

```
Rural-Connectivity-Mapper-2026/
├── main.py                      # CLI application
├── dashboard.py                 # NEW: Streamlit web dashboard
=======
├── app.py                       # Flask web application (NEW!)
├── upload_csv.py                # 🆕 Standalone CSV upload & validation script
├── example_speedtests.csv       # 🆕 Sample CSV with 10 test locations
├── demo_workflow.py             # Complete demo
├── demo_starlink_api.py         # Starlink API demo
├── requirements.txt             # Dependencies
├── README.md                    # This file
├── DEPLOYMENT.md                # Deployment notes
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore
│
├── templates/                   # Web dashboard templates (NEW!)
│   └── index.html              # Main dashboard page
├── config/                      # Configuration files
│   └── countries.json           # Country-specific settings
│
├── src/
│   ├── models/                  # Data models
│   │   ├── ConnectivityPoint.py # With country support
│   │   ├── SpeedTest.py
│   │   └── QualityScore.py
│   │
│   ├── utils/                   # Utility modules (12 modules)
│   │   ├── validation_utils.py
│   ├── utils/                   # Utility modules
│   │   ├── config_utils.py      # Country configuration loader
│   │   ├── validation_utils.py  # Country-aware validation
│   │   ├── data_utils.py
│   │   ├── measurement_utils.py
│   │   ├── geocoding_utils.py   # Multi-language support
│   │   ├── report_utils.py
│   │   ├── simulation_utils.py
│   │   ├── mapping_utils.py
│   │   ├── analysis_utils.py
│   │   └── starlink_api.py      # NEW: Starlink API integration
│   │
│   └── data/
│       ├── sample_data.csv      # Sample points
│       └── pontos.json          # Data storage
│
├── tests/                       # Test suite (58 tests)
│   ├── test_models.py
│   ├── test_validation_utils.py
│   ├── test_data_utils.py
│   ├── test_measurement_utils.py
│   ├── test_geocoding_utils.py
│   ├── test_report_utils.py
│   ├── test_simulation_utils.py
│   ├── test_mapping_utils.py
│   ├── test_analysis_utils.py
│   └── test_starlink_api.py     # NEW: Starlink API tests
│
└── docs/
    └── API.md                   # API reference
│   │   └── QualityScore.py
│   │
│   ├── utils/                   # Utility modules
│   │   ├── validation_utils.py
│   │   ├── data_utils.py
│   │   ├── measurement_utils.py
│   │   ├── geocoding_utils.py
│   │   ├── report_utils.py
│   │   ├── simulation_utils.py
│   │   ├── mapping_utils.py
│   │   ├── analysis_utils.py
│   │   └── starlink_coverage_utils.py
│   │   ├── anatel_utils.py      # NEW: ANATEL data integration
│   │   ├── ibge_utils.py        # NEW: IBGE demographics
│   │   ├── starlink_utils.py    # NEW: Starlink API
│   │   └── country_config.py    # NEW: LATAM country configs
│   │   └── ml_utils.py          # **NEW:** ML analysis
│   │   ├── mapping_utils.py     # Country-specific centers
│   │   └── analysis_utils.py
│   │   ├── mapping_utils.py
│   │   ├── analysis_utils.py
│   │   └── export_utils.py      # NEW: Ecosystem exports
│   │
│   └── data/
│       ├── sample_data.csv      # Sample Brazil data
│       ├── sample_data_us.csv   # Sample US data
│       └── pontos.json          # Data storage
│
├── tests/                       # Test suite (45 tests)
├── tests/                       # Test suite (73 tests)
├── tests/                       # Test suite (47 tests)
├── tests/                       # Test suite (46 tests)
├── tests/                       # Test suite (55 tests)
├── tests/                       # Test suite (46 tests)
├── examples/                    # CSV templates for contributions
│   ├── README.md                # Template documentation
│   ├── speedtest_template_basic.csv
│   └── speedtest_template_complete.csv
│
├── tests/                       # Test suite (36 tests)
│   ├── test_models.py
│   ├── test_config_utils.py     # Config tests (NEW)
│   ├── test_validation_utils.py
│   ├── test_data_utils.py
│   ├── test_measurement_utils.py
│   ├── test_geocoding_utils.py
│   ├── test_report_utils.py
│   ├── test_simulation_utils.py
│   ├── test_mapping_utils.py
│   ├── test_analysis_utils.py
│   └── test_starlink_coverage_utils.py
│   ├── test_anatel_utils.py     # NEW: ANATEL tests
│   ├── test_ibge_utils.py       # NEW: IBGE tests
│   ├── test_starlink_utils.py   # NEW: Starlink tests
│   └── test_country_config.py   # NEW: Country config tests
│   └── test_app.py             # Web app tests (NEW!)
│   └── test_ml_utils.py         # **NEW:** ML tests
│   └── test_upload_csv.py       # 🆕 CSV upload script tests
│   └── test_export_utils.py     # NEW: Ecosystem export tests
│
├── docs/
│   ├── API.md                   # API reference
│   └── ECOSYSTEM_INTEGRATION.md # NEW: Ecosystem guide
│
└── exports/                     # Generated ecosystem exports
    ├── hybrid_simulator_input.json
    ├── agrix_boost_connectivity.json
    └── ecosystem/
        ├── hybrid_simulator_input.json
        ├── agrix_boost_connectivity.json
        └── ecosystem_manifest.json
└── docs/
    ├── API.md                   # API reference
    └── GOOGLE_FORMS_INTEGRATION.md  # Google Forms setup guide

```

---

## 📊 Sample Data

Pre-configured connectivity data for 15 Brazilian cities with fresh 2026 metrics:

### Starlink Comparison (2026)

| Provider | Cities | Avg Download | Avg Upload | Avg Latency | Avg Obstruction | Avg Quality |
| -------- | ------ | ------------ | ---------- | ----------- | --------------- | ----------- |
| **Starlink High Performance** ⭐ | 2 | 197.0 Mbps | 28.8 Mbps | 21.8 ms | 0.7% | **96.7/100** |
| **Starlink Gen2** ⭐ | 2 | 168.9 Mbps | 23.7 Mbps | 27.7 ms | 1.9% | **89.4/100** |
| Claro | 2 | 90.3 Mbps | 14.7 Mbps | 40.6 ms | 0.0% | 71.2/100 |
| Vivo | 2 | 83.4 Mbps | 12.8 Mbps | 47.0 ms | 0.0% | 63.0/100 |
| TIM | 2 | 77.7 Mbps | 11.0 Mbps | 53.3 ms | 0.0% | 59.8/100 |
| Viasat | 2 | 73.7 Mbps | 9.5 Mbps | 69.9 ms | 8.9% | 47.5/100 |
| HughesNet | 2 | 64.2 Mbps | 7.5 Mbps | 91.9 ms | 11.2% | 24.0/100 |
| Oi | 1 | 58.3 Mbps | 6.5 Mbps | 78.9 ms | 0.0% | 44.7/100 |

### Key Findings

- **Starlink High Performance** delivers the best overall experience with 197 Mbps download and minimal 0.7% obstruction
- **Starlink Gen2** provides excellent performance at 169 Mbps with low 1.9% obstruction
- Traditional fiber ISPs (Claro, Vivo, TIM) show good speeds but higher latency (40-53 ms)
- Legacy satellite providers (Viasat, HughesNet) suffer from high obstruction (9-11%) and latency (70-92 ms)

Pre-configured connectivity data for 10 Brazilian cities (2026 data):

| City | Provider | Download | Upload | Latency | Jitter | Packet Loss | Obstruction | Quality Score |
| ------ | ---------- | ---------- | -------- | --------- | -------- | ------------- | ------------- | --------------- |
| **São Paulo** | Various | 85.2 Mbps | 12.5 Mbps | 45.3 ms | 8.2 ms | 1.2% | 0% | 63.0/100 (Good) |
| **Rio de Janeiro** | Claro | 92.1 Mbps | 15.3 Mbps | 38.7 ms | 6.5 ms | 0.8% | 0% | 71.2/100 (Good) |
| **Brasília** | **Starlink Gen2** ⭐ | 165.4 Mbps | 22.8 Mbps | 28.5 ms | 3.2 ms | 0.1% | 2.5% | **91.0/100 (Excellent)** |
| **Salvador** | Viasat | 75.3 Mbps | 9.8 Mbps | 68.2 ms | 15.7 ms | 2.5% | 0% | 42.3/100 (Fair) |
| **Fortaleza** | HughesNet | 62.8 Mbps | 7.2 Mbps | 95.4 ms | 22.3 ms | 3.8% | 0% | 21.8/100 (Poor) |
| **Curitiba** | **Starlink High Perf** 🚀 | 220.5 Mbps | 28.4 Mbps | 24.8 ms | 2.1 ms | 0.05% | 1.2% | **96.7/100 (Excellent)** |
| **Manaus** | Vivo | 68.4 Mbps | 10.2 Mbps | 52.3 ms | 12.4 ms | 1.8% | 0% | 52.1/100 (Fair) |
| **Recife** | TIM | 78.9 Mbps | 11.6 Mbps | 41.5 ms | 9.3 ms | 1.4% | 0% | 61.6/100 (Good) |
| **Porto Alegre** | Oi | 81.2 Mbps | 13.8 Mbps | 39.2 ms | 7.8 ms | 1.1% | 0% | 66.7/100 (Good) |
| **Belo Horizonte** | **Starlink Gen2** ⭐ | 172.8 Mbps | 24.2 Mbps | 26.9 ms | 2.8 ms | 0.08% | 3.8% | **92.5/100 (Excellent)** |

---

## 🌎 Multi-Country Support

The tool now supports **9 countries** with country-specific configurations:

| Country | Code | Language | Key Providers |
| ------- | ---- | -------- | ------------- |
| **Brazil** | BR | Portuguese | Starlink, Viasat, HughesNet, Claro, Vivo, TIM, Oi |
| **United States** | US | English | Starlink, Viasat, HughesNet, AT&T, Verizon, T-Mobile |
| **Canada** | CA | English | Starlink, Xplornet, Bell, Rogers, Telus, Shaw |
| **United Kingdom** | GB | English | Starlink, BT, Virgin Media, Sky, TalkTalk, Vodafone |
| **Australia** | AU | English | Starlink, NBN Co, Telstra, Optus, TPG, Vodafone |
| **Germany** | DE | German | Starlink, Deutsche Telekom, Vodafone, O2, 1&1 |
| **France** | FR | French | Starlink, Orange, SFR, Bouygues Telecom, Free |
| **India** | IN | English | Starlink, Jio, Airtel, BSNL, Vi, ACT Fibernet |
| **Mexico** | MX | Spanish | Starlink, Telmex, Telcel, AT&T Mexico, Izzi, Megacable |

### Country Configuration Features

- **Localized Geocoding**: Addresses returned in the country's primary language
- **Provider Validation**: Country-specific ISP lists for accurate validation
- **Map Centering**: Interactive maps automatically center on the selected country
- **Customizable**: Add new countries by editing `config/countries.json`

### Example: Using Different Countries

```bash
# Analyze US data
python main.py --country US --importar src/data/sample_data_us.csv --map

# Generate report for Canada
python main.py --country CA --analyze --relatorio json

# List all supported countries
python main.py --list-countries
```

---

## 🎯 Starlink 2026 Metrics

### Target Specifications

- **Download Speed:** 50-200 Mbps
- **Upload Speed:** 10-20 Mbps
- **Latency:** 20-40 ms
- **Jitter:** <5 ms (lower is better)
- **Packet Loss:** <1% (lower is better)
- **Obstruction:** <2% for satellite dishes (lower is better)
- **Quality Score Weighting:** Speed (40%) + Latency (30%) + Stability (30%)

### Quality Score Algorithm

```python
Overall Score = (Speed Score × 0.40) + (Latency Score × 0.30) + (Stability Score × 0.30)

# Component calculations:
Speed Score = ((download/200 + upload/20) / 2) × 100
Latency Score = 100 - (latency - 20) × 1.25  # Capped at 100

Stability Score = 100 - (jitter × 2 + packet_loss × 10 + obstruction × 0.2)
```

### Satellite-Specific Metrics

- **Obstruction:** Percentage of time the satellite dish has its view blocked by obstacles (trees, buildings)
  - **Excellent:** <2% obstruction
  - **Good:** 2-5% obstruction
  - **Fair:** 5-10% obstruction
  - **Poor:** >10% obstruction
- **Jitter:** Variation in latency, critical for real-time applications (VoIP, gaming, video calls)
- **Packet Loss:** Percentage of data packets that fail to reach their destination

### Performance Comparison: Starlink Gen2 vs High Performance

| Metric | Gen2 Standard | High Performance | Improvement |
| ------ | ------------- | ---------------- | ----------- |
| Download | 169 Mbps | 197 Mbps | +17% |
| Upload | 24 Mbps | 29 Mbps | +21% |
| Latency | 28 ms | 22 ms | -21% |
| Obstruction | 1.9% | 0.7% | -63% |
| Quality Score | 89.4/100 | 96.7/100 | +8% |

Stability Score = 100 - (jitter × 2 + packet_loss × 10 + obstruction × 0.2)

```

**New 2026 Metrics:**
- **Jitter**: Variation in latency (ms) - affects real-time applications
- **Packet Loss**: Percentage of lost packets - critical for reliability
- **Obstruction**: Percentage of sky view blocked (satellite-specific) - Starlink performance indicator


### Rating Tiers
- **Excellent:** ≥80/100 (Starlink target)
- **Good:** 60-79/100
- **Fair:** 40-59/100
- **Poor:** <40/100

---


## 🤖 Machine Learning Features

### ML-Enhanced Geospatial Analysis

The toolkit now includes advanced machine learning capabilities for optimizing rural connectivity and Starlink expansion strategies.

#### Key ML Capabilities

1. **Rural Area Identification**
   - Automatically identifies rural areas based on distance from major cities
   - Uses geospatial features to classify urban vs. rural zones
   - Threshold: >100km from major city = rural area

2. **Improvement Potential Prediction**
   - ML models predict which areas have highest improvement potential
   - Considers current quality score, distance from cities, and connectivity gaps
   - Generates priority scores (0-100) for each location

3. **Starlink Expansion Zone Recommendation**
   - K-means clustering to identify optimal expansion zones
   - Prioritizes zones based on rural characteristics and connectivity gaps
   - Provides actionable recommendations for each zone

4. **ROI Analysis**
   - Calculates Starlink suitability score for deployment
   - Analyzes rural coverage percentage and high-priority areas
   - Generates strategic recommendations based on ML insights

### ML Analysis Output

```json
{
  "roi_analysis": {
    "rural_percentage": 60.0,
    "starlink_suitability_score": 75.5,
    "recommendations": [
      "STRONG FIT: Over 50% of points are in rural areas"
    ]
  },
  "expansion_zones": {
    "zone_1": {
      "priority_score": 85.2,
      "is_primarily_rural": true,
      "recommendation": "HIGH PRIORITY: Rural area with poor connectivity"
    }
  },
  "top_priority_areas": [...]
}
```

### ML Algorithms Used

- **K-Means Clustering**: For expansion zone identification
- **Feature Engineering**: Geospatial distance calculations, quality metrics
- **Ensemble Methods**: For robust prediction and prioritization
- **Geospatial Analytics**: Haversine distance, coordinate-based features

## 🔗 Ecosystem Integration

### Overview

Rural Connectivity Mapper 2026 integrates seamlessly with other projects to create a comprehensive rural connectivity ecosystem:

1. **Rural Connectivity Mapper** - Measures and analyzes connectivity
2. **Hybrid Architecture Simulator** - Tests failover scenarios with real data
3. **AgriX-Boost** - Provides connectivity layer for farm dashboards

### Export Data

Generate ecosystem-compatible exports:

```bash
# Export for Hybrid Architecture Simulator (failover testing)
python main.py --export hybrid

# Export for AgriX-Boost (farm dashboards)
python main.py --export agrix

# Export complete ecosystem bundle
python main.py --export ecosystem
```

### Ecosystem Bundle Contents

When using `--export ecosystem`, the following files are generated in `exports/ecosystem/`:

- **hybrid_simulator_input.json** - Failover testing data with:
  - Signal quality metrics
  - Latency and stability scores
  - Failover indicators (connection reliability, low latency, stability)
  - Recommended primary/backup connection flags

- **agrix_boost_connectivity.json** - Farm connectivity layer with:
  - Network performance metrics
  - Farm suitability indicators (IoT, video, real-time control, analytics)
  - Connectivity recommendations for agricultural use cases

- **ecosystem_manifest.json** - Integration manifest with:
  - Component descriptions and purposes
  - Data summary and quality distribution
  - Integration notes and references

### Integration Benefits

**For Hybrid Architecture Simulator:**

- Test realistic failover scenarios with actual connectivity data
- Model network degradation and recovery
- Evaluate backup connection strategies

**For AgriX-Boost:**

- Display real-time connectivity status in farm dashboards
- Assess farm suitability for IoT sensors, video monitoring, and automation
- Provide connectivity-based recommendations for farmers

**Documentation:** See [ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) for detailed integration guide.

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Web App Tests Only

```bash
pytest tests/test_app.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov=app --cov-report=html
```

**Test Coverage:**

- 38 total tests (190% of requirement)
- 5 model tests
- 33 utility tests

- 58 total tests (290% of requirement)
- 5 model tests
- 31 utility tests
- 22 Starlink API tests

- 73 total tests (365% of original requirement)
- 5 model tests
- 31 original utility tests
- 37 new integration tests (ANATEL, IBGE, Starlink, Country Config)

- 47 total tests
- 5 model tests
- 31 utility tests
- 11 web application tests

- **47 total tests** (including 11 ML tests)
- 5 model tests
- 31 utility tests
- 11 ML tests

- 46 total tests (230% of requirement)
- 5 model tests
- 31 utility tests
- 10 ecosystem export tests

- 80%+ code coverage

### Linting

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run ruff
ruff check .

# Run flake8
flake8 src/ tests/ main.py demo_workflow.py
```

---

## 🔄 CI/CD

This project uses GitHub Actions for continuous integration and deployment:

### Workflows

1. **CI Workflow** (`.github/workflows/ci.yml`)
   - Runs on: Push to main/develop, Pull Requests
   - Tests across Python 3.8, 3.9, 3.10, 3.11, 3.12
   - Generates coverage reports
   - Uploads coverage artifacts

2. **Lint Workflow** (`.github/workflows/lint.yml`)
   - Runs on: Push to main/develop, Pull Requests
   - Checks code quality with ruff and flake8
   - Ensures consistent code style

3. **Release Workflow** (`.github/workflows/release.yml`)
   - Runs on: Version tags (v*.*.*)
   - Creates GitHub releases automatically
   - Includes test results and coverage

### Running CI Locally

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=src

# Run linting
ruff check .
flake8 src/ tests/ main.py demo_workflow.py
```

### Configuration Files

- `pytest.ini` - Pytest configuration
- `.flake8` - Flake8 linting rules
- `ruff.toml` - Ruff linting configuration
- `requirements-dev.txt` - Development dependencies

---

## 🌍 Use Cases

1. **Rural Expansion Planning** - Identify priority areas for Starlink installations using coverage overlay
2. **ISP Performance Benchmarking** - Compare Starlink vs. traditional providers
3. **Installation Site Selection** - Visualize coverage zones to determine optimal Dishy placement
4. **Infrastructure ROI Modeling** - Estimate impact of router upgrades
5. **Policy Advocacy** - Generate reports for government stakeholders
6. **Academic Research** - Analyze connectivity's socioeconomic impact

7. **Rural Expansion Planning** - Identify priority areas for Starlink installations across LATAM

8. **Rural Expansion Planning** - Identify priority areas for Starlink installations using ML

9. **ISP Performance Benchmarking** - Compare Starlink vs. traditional providers

10. **Infrastructure ROI Modeling** - Estimate impact of router upgrades with ML predictions
11. **Policy Advocacy** - Generate ML-enhanced reports for government stakeholders
12. **Academic Research** - Analyze connectivity's socioeconomic impact with geospatial ML
13. **Starlink Deployment Strategy** - Optimize satellite internet expansion with ML zone recommendations

14. **Infrastructure ROI Modeling** - Estimate impact of router upgrades

15. **Policy Advocacy** - Generate reports for government stakeholders using real ANATEL/IBGE data
16. **Academic Research** - Analyze connectivity's socioeconomic impact with demographic integration
17. **Cross-Country Analysis** - Compare connectivity metrics across 10 LATAM countries
18. **Starlink Market Entry** - Assess service availability and competitive landscape
19. **Digital Divide Studies** - Track rural-urban connectivity gaps with IBGE statistics

---

## 🌎 Supported Countries

The tool now supports **10 Latin American countries**:

| Country | Code | Telecom Regulator | Stats Agency | Starlink Status |
| ------- | ---- | ----------------- | ------------ | --------------- |
| 🇧🇷 Brazil | BR | ANATEL | IBGE | Active (98.5% coverage) |
| 🇦🇷 Argentina | AR | ENACOM | INDEC | Active (97.0% coverage) |
| 🇨🇱 Chile | CL | SUBTEL | INE | Active (98.0% coverage) |
| 🇨🇴 Colombia | CO | CRC | DANE | Active (90.0% coverage) |
| 🇲🇽 Mexico | MX | IFT | INEGI | Active (95.0% coverage) |
| 🇵🇪 Peru | PE | OSIPTEL | INEI | Active (88.0% coverage) |
| 🇪🇨 Ecuador | EC | ARCOTEL | INEC | Active |
| 🇺🇾 Uruguay | UY | URSEC | INE | Active |
| 🇵🇾 Paraguay | PY | CONATEL | DGEEC | Active |
| 🇧🇴 Bolivia | BO | ATT | INE | Active |

1. **Policy Advocacy** - Generate reports for government stakeholders
2. **Academic Research** - Analyze connectivity's socioeconomic impact
3. **Failover Testing** - Export data to Hybrid Architecture Simulator for realistic network failover scenarios
4. **Farm Automation** - Integrate with AgriX-Boost to provide connectivity layer for agricultural IoT and monitoring

---

## 🗺️ Roadmap

### v1.1.0 (Q1 2026) ✅ COMPLETED

- [x] Real-time ANATEL data integration
- [x] IBGE demographics integration  
- [x] Starlink API integration
- [x] Streamlit web dashboard
- [x] Support for 10 LATAM countries
- [x] Country-specific configurations

### v1.1.0 (Q1 2026) - COMPLETED ✅

- [x] Multi-country support (9 countries)
- [x] Country-specific provider lists
- [x] Localized geocoding
- [x] Configurable map centers

### v1.0.0 (Current) ✅

- [x] Complete CLI application with ecosystem integration
- [x] Export data for Hybrid Architecture Simulator (failover testing)
- [x] Export data for AgriX-Boost (farm dashboards)
- [x] Ecosystem bundle generation
- [x] 46 comprehensive tests

### v1.0.1 (Current Release)

- [x] Docker containerization ✅ (Moved from v1.1.0)

### v1.1.0 (Q1 2026)

- [x] Web dashboard (Streamlit)
- [x] Real-time speedtest integration
- [x] Integration with Starlink APIs ✅ (Completed: starlink_api.py module)
- [ ] Real-time speedtest integration
- [ ] SQLite database backend

- [x] GitHub Actions CI/CD ✅
- [ ] Docker containerization
- [ ] GitHub Actions CI/CD

### v1.2.0 (Q2 2026) - COMPLETED! ✅

- [x] Web dashboard (Flask)
- [x] REST API endpoints
- [ ] Machine learning predictions

### v1.2.0 (Q2 2026) - **COMPLETED EARLY!**

- [ ] Web dashboard (Flask/Streamlit)
- [ ] REST API endpoints
- [x] **Machine learning predictions** ✅
- [ ] GeoJSON/KML export

### v2.0.0 (H2 2026)

- [ ] Multi-language UI (Portuguese/Spanish/English)
- [ ] Mobile app for field data collection
- [ ] Advanced analytics (churn prediction)
- [ ] Live Starlink satellite tracking
- [ ] Additional countries support
- [x] Multi-language support (Portuguese/English) ✅ **Completed!**
- [ ] Mobile app for field data collection
- [ ] Advanced analytics (churn prediction)
- [ ] Integration with Starlink APIs
- [ ] Deep learning models for connectivity forecasting

---

## 📊 How to Contribute Your Speedtest Data

Help us map rural connectivity across Brazil! Your speedtest data is valuable for:

- 🗺️ Identifying underserved areas
- 📈 Tracking ISP performance over time
- 🎯 Supporting Starlink's 2026 expansion planning
- 📊 Advocating for better rural internet policies

### Quick Contribution Guide

#### 1️⃣ Download a Template

Choose one of the ready-made CSV templates from the [`/examples/`](examples/) directory:

- **[Basic Template](examples/speedtest_template_basic.csv)** - Simple template with one example entry
- **[Complete Template](examples/speedtest_template_complete.csv)** - Template with 5 example entries

Or download directly:

```bash
curl -O https://raw.githubusercontent.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/main/examples/speedtest_template_basic.csv
```

#### 2️⃣ Run a Speedtest

Use any of these tools to measure your internet speed:

**Online Tools:**

- [Speedtest.net](https://www.speedtest.net/) (recommended)
- [Fast.com](https://fast.com/)
- [CloudFlare Speed Test](https://speed.cloudflare.com/)

**Command Line:**

```bash
pip install speedtest-cli
speedtest-cli --simple
```

#### 3️⃣ Fill in Your Data

Edit the CSV template with your results:

| Field | How to Fill | Example |
| ----- | ----------- | ------- |
| `id` | Any unique number | 1 |
| `city` | Your city/location | "Campinas" |
| `provider` | Your ISP name | "Starlink" |
| `latitude` | GPS coordinate | -22.9099 |
| `longitude` | GPS coordinate | -47.0626 |
| `download` | Download speed (Mbps) | 150.5 |
| `upload` | Upload speed (Mbps) | 20.3 |
| `latency` | Ping time (ms) | 28.0 |
| `jitter` | Jitter (ms) - optional | 3.5 |
| `packet_loss` | Packet loss (%) - optional | 0.2 |
| `timestamp` | ISO 8601 format (optional) | 2026-01-15T10:00:00 |

**💡 Tip:** Use [Google Maps](https://www.google.com/maps) to find coordinates - right-click on your location and click the coordinates to copy them.

#### 4️⃣ Submit Your Data

Choose one of these methods:

**Method A: GitHub Pull Request** (Recommended)

```bash
# Fork the repository first, then:
git clone https://github.com/YOUR-USERNAME/Rural-Connectivity-Mapper-2026.git
cd Rural-Connectivity-Mapper-2026
git checkout -b data/your-location-name

# Add your CSV file to src/data/ or submit as attachment
git add your_speedtest_data.csv
git commit -m "Add speedtest data for [Your City]"
git push origin data/your-location-name

# Open a Pull Request on GitHub
```

**Method B: GitHub Issue**

1. Go to [Issues](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues/new)
2. Title: "Speedtest Data: [Your City]"
3. Attach your CSV file or paste the data
4. Add any relevant context (time of day, weather conditions, etc.)

**Method C: Email/Contact**

- Submit via [GitHub Discussions](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/discussions)

### Data Quality Guidelines

✅ **Do:**

- Run 3-5 tests and use average values
- Test at different times of day
- Close bandwidth-intensive applications
- Note any unusual conditions (weather, network congestion)
- Use accurate GPS coordinates

❌ **Don't:**

- Submit fake or estimated data
- Include personally identifiable information
- Submit duplicate measurements without time gaps

### Need Help?

📖 Full documentation in [`/examples/README.md`](examples/README.md)  
💬 Questions? Open a [Discussion](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/discussions)  
🐛 Issues? Report a [Bug](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues)

**Every data point helps! Thank you for contributing to better rural connectivity in Brazil! 🇧🇷**

---

## 🤝 Contributing Code

Developer contributions are also welcome! Please:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Run tests: `pytest tests/ -v`
4. Submit Pull Request

**Guidelines:**

- Follow PEP 8 style
- Add docstrings (Google-style)
- Include tests for new features
- Update documentation
- **Estimate effort** when creating issues (S/M/L/XL or hours)

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details including effort estimation guidelines.

---

## 📄 License

**MIT License** - See [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Daniel Azevedo Novais

---

## 🙏 Acknowledgments

- **SpaceX Starlink** - 2026 expansion targets and satellite innovation

- **ANATEL** - Brazilian telecommunications data and regulatory framework
- **IBGE** - Brazilian demographic and geographic statistics
- **LATAM Regulators** - ENACOM, SUBTEL, CRC, IFT, OSIPTEL, and others
- **Brazilian ISPs** - Claro, Vivo, TIM, Oi for benchmarking
- **Satellite ISPs** - Viasat, HughesNet for rural comparisons
- **Open Source Community** - geopy, folium, pytest, pandas, streamlit, plotly

- **Global ISPs** - AT&T, Verizon, Bell, BT, Telstra, Deutsche Telekom and many others

- **SpaceX Starlink** - 2026 expansion targets and Gen2/High Performance dish innovation

- **Brazilian ISPs** - Claro, Vivo, TIM, Oi for benchmarking
- **Satellite ISPs** - Viasat, HughesNet for rural comparisons
- **Open Source Community** - geopy, folium, pytest, pandas, scikit-learn

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues)
- **Discussions:** [GitHub Discussions](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/discussions)
- **Repository:** [Rural-Connectivity-Mapper-2026](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026)

---

## 📊 Project Statistics

- **35+ files** across models, utilities, tests, documentation
- **4,000+ lines of code** (Python)
- **45 passing tests** (100% success rate)
- **5 sample cities** with real-world profiles
- **4 export formats** (JSON, CSV, TXT, HTML)
- **5 Starlink coverage zones** + 11 signal points

- **35+ files** across models, utilities, tests, documentation
- **4,500+ lines of code** (Python)
- **58 passing tests** (100% success rate)
- **9 utility modules** including Starlink API integration

- **40 files** across models, utilities, tests, documentation
- **5,119 lines of code** (Python)
- **73 passing tests** (100% success rate)
- **10 LATAM countries** fully configured
- **4 data sources** (ANATEL, IBGE, Starlink API, Manual)
- **6 dashboard views** in Streamlit
- **4 export formats** (JSON, CSV, TXT, HTML)

- **35 files** across models, utilities, tests, documentation, web app
- **4,800+ lines of code** (Python, HTML, CSS, JavaScript)
- **47 passing tests** (100% success rate)

- **35+ files** across models, utilities, tests, documentation
- **5,500+ lines of code** (Python)
- **47 passing tests** (100% success rate)

- **38 files** across models, utilities, tests, documentation, config
- **4,500+ lines of code** (Python)
- **46 passing tests** (100% success rate)
- **9 supported countries** with localized settings
- **10+ sample cities** with real-world profiles
- **4 export formats** (JSON, CSV, TXT, HTML)

- **35 files** across models, utilities, tests, documentation
- **4,000+ lines of code** (Python)
- **50 passing tests** (100% success rate)
- **2 supported languages** (English, Portuguese)

- **35 files** across models, utilities, tests, documentation
- **4,000+ lines of code** (Python)
- **55 passing tests** (100% success rate)
- **10 sample locations** in example_speedtests.csv
- **4 export formats** (JSON, CSV, TXT, HTML)

- **40+ files** across models, utilities, tests, documentation, exports
- **5,000+ lines of code** (Python)
- **46 passing tests** (100% success rate)
- **32 files** across models, utilities, tests, documentation

- **3,700+ lines of code** (Python)
- **38 passing tests** (100% success rate)

- **3,591+ lines of code** (Python)
- **37 passing tests** (100% success rate)
- **15 sample cities** with real-world 2026 profiles
- **8 ISP providers** (Starlink Gen2, Starlink High Performance, and traditional ISPs)
- **4 export formats** (JSON, CSV, TXT, HTML)

- **3,800+ lines of code** (Python)
- **39 passing tests** (100% success rate)
- **10 sample cities** with real-world 2026 profiles
- **9 ISP providers** including Starlink Gen2 and High Performance dishes
- **4 export formats** (JSON, CSV, TXT, HTML)
- **3,591 lines of code** (Python)
- **39 passing tests** (100% success rate)

- **5 sample cities** with real-world profiles
- **7 export formats** (JSON, CSV, TXT, HTML, Hybrid Simulator, AgriX-Boost, Ecosystem Bundle)

- **80%+ test coverage**
- **6 Starlink coverage zones** (Active, Planned, Limited)

- **14 REST API endpoints** for data integration

- **3 integrated ecosystem components**

---

**🇧🇷 🇦🇷 🇨🇱 🇨🇴 🇲🇽 Made with ❤️ for improving rural connectivity across Latin America**

**🌍 Made with ❤️ for improving rural connectivity worldwide**

*Supporting Starlink's 2026 roadmap to connect 10M rural users globally and enable 20-30% agricultural productivity gains.*

*Part of the Rural Connectivity Ecosystem 2026 - integrating with Hybrid Architecture Simulator and AgriX-Boost.*

---

## 📚 Additional Documentation

- **[New Features Guide](docs/NEW_FEATURES.md)** - Comprehensive guide for ANATEL, IBGE, Starlink API, and LATAM support
- **[API Reference](docs/API.md)** - Full API documentation

---

**Release Date:** January 4, 2026  
**Version:** 1.1.0  

**Release Date:** January 3, 2026  
**Version:** 1.0.0  

**Status:** Production Ready ✅
