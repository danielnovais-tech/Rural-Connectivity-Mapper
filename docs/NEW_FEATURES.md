# New Features Guide - Rural Connectivity Mapper 2026 v1.1

## Overview

Version 1.1 introduces major enhancements to the Rural Connectivity Mapper 2026:

1. **ANATEL Data Integration** - Real Brazilian telecom data
2. **IBGE Demographics** - Population and connectivity statistics
3. **Starlink API** - Service availability and coverage maps
4. **LATAM Support** - 10 Latin American countries
5. **Streamlit Dashboard** - Interactive web interface

---

## 1. ANATEL Data Integration

### What is ANATEL?

ANATEL (Agência Nacional de Telecomunicações) is Brazil's National Telecommunications Agency, responsible for regulating telecom services.

### Features

- Fetch broadband fixed internet data
- Get mobile coverage statistics  
- Provider market share analysis
- Technology penetration (Fiber, 4G, 5G, Satellite)

### Usage Examples

```python
from src.utils import (
    fetch_anatel_broadband_data,
    fetch_anatel_mobile_data,
    get_anatel_provider_stats,
    convert_anatel_to_connectivity_points
)

# Get broadband data for all Brazil
broadband = fetch_anatel_broadband_data()

# Filter by state (São Paulo)
sp_broadband = fetch_anatel_broadband_data(state='SP')

# Get mobile coverage data
mobile = fetch_anatel_mobile_data(state='RJ')

# Get provider statistics
stats = get_anatel_provider_stats()
starlink_stats = get_anatel_provider_stats(provider='Starlink')

# Convert to ConnectivityPoint format
points = convert_anatel_to_connectivity_points(broadband)
```

### Data Fields

**Broadband Data:**

- `state`: State abbreviation (SP, RJ, MG, etc.)
- `municipality`: City name
- `provider`: ISP name
- `technology`: Connection type (Fibra, ADSL, Satélite, etc.)
- `subscribers`: Number of subscribers
- `avg_speed_mbps`: Average download speed
- `coverage_percentage`: Population coverage

**Mobile Data:**

- `state`, `municipality`, `provider`
- `technology`: Network type (5G, 4G)
- `coverage_4g_percentage`: 4G coverage
- `coverage_5g_percentage`: 5G coverage
- `avg_speed_mbps`: Average mobile speed

---

## 2. IBGE Demographics Integration

### What is IBGE?

IBGE (Instituto Brasileiro de Geografia e Estatística) is Brazil's national statistics agency, providing demographic and geographic data.

### Features

- Municipality population data
- Rural vs. urban statistics
- Internet access percentages
- Priority areas identification

### Usage Examples

```python
from src.utils import (
    fetch_ibge_municipalities,
    get_rural_areas_needing_connectivity,
    get_ibge_statistics_summary,
    combine_ibge_anatel_data
)

# Get all municipalities
municipalities = fetch_ibge_municipalities()

# Filter by state
sp_municipalities = fetch_ibge_municipalities(state_code='SP')

# Get priority rural areas (low connectivity)
priority_areas = get_rural_areas_needing_connectivity()

# Get national statistics summary
summary = get_ibge_statistics_summary()
print(f"Rural population: {summary['rural_population']:,}")
print(f"Rural internet access: {summary['rural_households_with_internet']}%")

# Combine IBGE + ANATEL data
from src.utils import fetch_anatel_broadband_data
anatel_data = fetch_anatel_broadband_data()
combined = combine_ibge_anatel_data(municipalities, anatel_data)
```

### Priority Areas Analysis

The system identifies rural areas with:

- High rural population
- Low internet coverage
- High priority score (based on population and coverage gap)

Example output:

```python
priority_areas = get_rural_areas_needing_connectivity()
# [
#   {
#     'municipality': 'Cametá',
#     'state': 'PA',
#     'rural_population': 85000,
#     'internet_coverage': 12.5,
#     'priority_score': 95
#   },
#   ...
# ]
```

---

## 3. Starlink API Integration

### Features

- Service availability checker
- Coverage maps by country
- Service plans and pricing
- Performance estimation
- Provider comparison

### Usage Examples

```python
from src.utils import (
    check_starlink_availability,
    check_batch_availability,
    get_starlink_service_plans,
    get_starlink_coverage_map,
    estimate_starlink_performance,
    get_starlink_vs_competitors
)

# Check availability at specific coordinates
availability = check_starlink_availability(-15.7801, -47.9292)
print(f"Available: {availability['service_available']}")
print(f"Status: {availability['status']}")
print(f"Expected speeds: {availability['expected_speeds']}")

# Check multiple locations at once
locations = [
    (-23.5505, -46.6333),  # São Paulo
    (-22.9068, -43.1729),  # Rio de Janeiro
    (-15.7801, -47.9292)   # Brasília
]
results = check_batch_availability(locations)

# Get service plans
plans = get_starlink_service_plans()
for plan in plans:
    print(f"{plan['name']}: R${plan['price_brl_monthly']}/month")
    print(f"  Hardware: R${plan['hardware_cost_brl']}")
    print(f"  Speed: {plan['download_speed']}")

# Get coverage map for a country
coverage = get_starlink_coverage_map('BR')
print(f"Coverage: {coverage['coverage_percentage']}%")
print(f"Active users: {coverage['active_users']:,}")

# Estimate performance with weather conditions
performance = estimate_starlink_performance(
    -15.7801, -47.9292,
    weather_condition='clear'
)

# Compare with competitors
comparison = get_starlink_vs_competitors(-15.7801, -47.9292)
print(f"Recommended: {comparison['recommendation']}")
```

### Service Plans

Available plans (2026):

1. **Residential** - R$299/month, 50-200 Mbps
2. **Business** - R$999/month, 100-350 Mbps
3. **Roam (Mobile)** - R$499/month, 50-150 Mbps
4. **Maritime** - R$4,999/month, 100-350 Mbps

---

## 4. LATAM Country Support

### Supported Countries

10 Latin American countries with full configuration:

| Code | Country | Regulator | Stats Agency |
| ---- | ------- | --------- | ------------ |
| BR | Brazil | ANATEL | IBGE |
| AR | Argentina | ENACOM | INDEC |
| CL | Chile | SUBTEL | INE |
| CO | Colombia | CRC | DANE |
| MX | Mexico | IFT | INEGI |
| PE | Peru | OSIPTEL | INEI |
| EC | Ecuador | ARCOTEL | INEC |
| UY | Uruguay | URSEC | INE |
| PY | Paraguay | CONATEL | DGEEC |
| BO | Bolivia | ATT | INE |

### Usage Examples

```python
from src.utils import (
    get_supported_countries,
    get_country_config,
    get_country_providers,
    get_latam_summary,
    translate_field_names
)

# List all supported countries
countries = get_supported_countries()
# ['BR', 'AR', 'CL', 'CO', 'MX', 'PE', 'EC', 'UY', 'PY', 'BO']

# Get country configuration
config = get_country_config('AR')
print(f"Name: {config.name}")
print(f"Currency: {config.currency}")
print(f"Regulator: {config.telecom_regulator}")
print(f"Stats Agency: {config.stats_agency}")
print(f"Providers: {config.supported_providers}")

# Get providers for a country
providers = get_country_providers('CL')
# ['Starlink', 'Movistar', 'Entel', 'Claro', 'WOM', 'VTR']

# Get LATAM summary
summary = get_latam_summary()
print(f"Total countries: {summary['total_countries']}")
print(f"Unique providers: {summary['unique_providers_count']}")

# Get field translations
pt_trans = translate_field_names('BR')  # Portuguese
es_trans = translate_field_names('AR')  # Spanish
```

### Country-Specific Features

Each country has:

- Official language (Portuguese/Spanish)
- Currency code
- Telecom regulatory agency
- National statistics institute
- Center coordinates for mapping
- List of major ISPs
- Data source URLs

---

## 5. Streamlit Dashboard

### Launching the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Dashboard Features

#### 1. Overview Tab

- Key connectivity metrics
- Provider market share pie chart
- Speed comparison bar charts
- IBGE statistics summary

#### 2. ANATEL Data Tab

- Broadband data table and visualizations
- Mobile coverage statistics
- State filtering
- Subscriber distribution charts

#### 3. IBGE Demographics Tab

- Population distribution maps  
- Rural vs urban population charts
- Internet access percentages
- Priority rural areas table
- Coverage vs priority score scatter plot
- Download data as CSV
- Population statistics

#### 4. Starlink Availability Tab

- Coverage map by country
- Active users and ground stations metrics
- Service plans comparison table
- Interactive availability checker (enter lat/lon)

#### 5. LATAM Comparison Tab

- Compare all 10 countries
- Starlink coverage bar chart
- Provider distribution
- Country details table

#### 6. Interactive Map Tab

- Full-screen interactive map
- Markers with provider details
- Click for connectivity info
- Color-coded by quality

### Dashboard Controls

**Sidebar:**

- Country selector (10 LATAM countries)
- View selector (6 different views)
- Country info panel
- Last updated timestamp

**Main Area:**

- Summary statistics
- Visualizations (charts with Plotly)
- Interactive charts (Plotly)
- Data tables (Streamlit)
- Maps (Folium)
- Download buttons

---

## 6. Integration Examples

### Example 1: Complete Country Analysis

```python
from src.utils import *

# Analyze Brazil
country_code = 'BR'

# 1. Get ANATEL data
broadband = fetch_anatel_broadband_data()
mobile = fetch_anatel_mobile_data()
provider_stats = get_anatel_provider_stats()

# 2. Get IBGE demographics
priority_areas = get_rural_areas_needing_connectivity()
ibge_summary = get_ibge_statistics_summary()

# 3. Check Starlink coverage
coverage = get_starlink_coverage_map(country_code)

# 4. Generate report
print(f"\n{config.name} Connectivity Report")
print(f"{'=' * 50}")
print(f"Total municipalities: {ibge_summary['total_municipalities']:,}")
print(f"Rural population: {ibge_summary['rural_population']:,}")
print(f"Rural internet access: {ibge_summary['rural_households_with_internet']}%")
print(f"\nStarlink Coverage: {coverage['coverage_percentage']}%")
print(f"Starlink Users: {coverage['active_users']:,}")
print(f"\nPriority Areas: {len(priority_areas)}")
```

### Example 2: Multi-Country Comparison

```python
from src.utils import *

# Compare Starlink across LATAM
countries = ['BR', 'AR', 'CL', 'MX', 'CO']

for code in countries:
    config = get_country_config(code)
    coverage = get_starlink_coverage_map(code)
    
    print(f"{config.name}:")
    print(f"  Coverage: {coverage['coverage_percentage']}%")
    print(f"  Users: {coverage['active_users']:,}")
    print(f"  Ground Stations: {coverage['ground_stations']}")
```

### Example 3: Priority Area Investment Analysis

```python
from src.utils import *

# Get priority areas
priority_areas = get_rural_areas_needing_connectivity()

# Calculate investment opportunity
total_population = sum(area['rural_population'] for area in priority_areas)
avg_coverage_gap = 100 - sum(area['internet_coverage'] for area in priority_areas) / len(priority_areas)

print(f"Investment Opportunity Analysis:")
print(f"Total unserved rural population: {total_population:,}")
print(f"Average coverage gap: {avg_coverage_gap:.1f}%")

# Check Starlink availability
for area in priority_areas[:5]:
    availability = check_starlink_availability(
        area['latitude'],
        area['longitude']
    )
    print(f"\n{area['municipality']}, {area['state']}:")
    print(f"  Starlink: {availability['status']}")
    print(f"  Priority Score: {area['priority_score']}")
```

---

## 7. Testing

All new features are fully tested:

```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_anatel_utils.py -v
pytest tests/test_ibge_utils.py -v
pytest tests/test_starlink_utils.py -v
pytest tests/test_country_config.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

**Test Coverage:**

- 73 total tests
- 7 ANATEL tests
- 8 IBGE tests
- 10 Starlink tests
- 13 Country config tests
- 80%+ code coverage

---

## 8. Data Sources

### Official APIs

**Brazil:**

- ANATEL: https://informacoes.anatel.gov.br/paineis/acessos
- IBGE: https://servicodados.ibge.gov.br/api/v1

**Argentina:**

- ENACOM: https://www.enacom.gob.ar/datos-abiertos
- INDEC: https://www.indec.gob.ar

**Chile:**

- SUBTEL: https://www.subtel.gob.cl/estudios-y-estadisticas/
- INE: https://www.ine.gob.cl/

*(Other countries have similar official sources listed in country_config.py)*

### Mock Data

For development and testing, the system uses mock data that mirrors the structure of real API responses. In production, these can be replaced with actual API calls.

---

## 9. Troubleshooting

### Common Issues

**1. Import errors**

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
```

**2. Streamlit not found**

```bash
pip install streamlit streamlit-folium plotly
```

**3. API timeouts**

- The IBGE API fetch has fallback to mock data if the real API is unavailable
- Check internet connection
- Verify API endpoints are accessible

**4. Test failures**

```bash
# Clear pytest cache
pytest --cache-clear

# Run tests with verbose output
pytest tests/ -vv
```

---

## 10. Future Enhancements

Planned features:

- Real-time ANATEL API integration
- Live Starlink satellite tracking
- Machine learning predictions
- Export to GeoJSON/KML
- Mobile app for field data collection
- Advanced analytics dashboard

---

For more information, see the main [README.md](../README.md) or run:

```bash
python demo_new_features.py
```
