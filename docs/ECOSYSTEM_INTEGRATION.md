# Ecosystem Integration Guide

## Overview

The Rural Connectivity Mapper 2026 is designed to seamlessly integrate with other projects in the rural connectivity ecosystem, providing real-world connectivity data for enhanced testing and application development.

## Ecosystem Components

### 1. Rural Connectivity Mapper 2026

**Repository:** [Rural-Connectivity-Mapper-2026](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026)

**Purpose:** Map and analyze rural internet connectivity across Brazil, measuring signal quality, latency, download/upload speeds, and stability metrics.

**Key Features:**

- Connectivity measurement and mapping
- Quality score calculation
- Provider comparison
- Temporal analysis
- Multi-format reporting

### 2. Hybrid Architecture Simulator

**Repository:** [Hybrid-Architecture-Simulator](https://github.com/danielnovais-tech/Hybrid-Architecture-Simulator)
**Purpose:** Test realistic failover scenarios using real-world connectivity data.

**Integration Benefits:**

- Use actual connectivity metrics for realistic simulation
- Test failover behavior based on signal quality
- Model network degradation scenarios
- Evaluate backup connection strategies

### 3. AgriX-Boost

**Repository:** [AgriX-Boost](https://github.com/danielnovais-tech/AgriX-Boost)
**Purpose:** Connectivity layer for agricultural monitoring and farm dashboards.

**Integration Benefits:**

- Real-time connectivity status for farm locations
- Farm suitability assessments for different use cases
- IoT sensor network planning
- Video monitoring capability checks

## Export Formats

### Ecosystem Bundle

Export complete integration data for all components:

```bash
python main.py --importar data.csv --export ecosystem
```

**Outputs:**

- `exports/ecosystem/hybrid_simulator_input.json` - Failover testing data
- `exports/ecosystem/agrix_boost_connectivity.json` - Farm connectivity layer
- `exports/ecosystem/ecosystem_manifest.json` - Integration manifest

### Individual Exports

#### Hybrid Architecture Simulator

```bash
python main.py --export hybrid
```

**Output:** `exports/hybrid_simulator_input.json`

**Data Structure:**

```json
{
  "metadata": {
    "export_timestamp": "2026-01-03T12:00:00",
    "source": "Rural Connectivity Mapper 2026",
    "total_points": 5,
    "format_version": "1.0",
    "purpose": "failover_testing"
  },
  "connectivity_points": [
    {
      "point_id": "uuid",
      "location": {
        "latitude": -23.5505,
        "longitude": -46.6333
      },
      "provider": "Starlink",
      "timestamp": "2026-01-15T10:30:00",
      "metrics": {
        "signal_quality": 100.0,
        "latency_ms": 28.5,
        "download_mbps": 165.4,
        "upload_mbps": 22.8,
        "stability_score": 96.6,
        "jitter_ms": 3.2,
        "packet_loss_pct": 0.1
      },
      "quality_breakdown": {
        "overall_score": 100.0,
        "speed_score": 95.0,
        "latency_score": 89.4,
        "stability_score": 96.6,
        "rating": "Excellent"
      },
      "failover_indicators": {
        "connection_reliable": true,
        "low_latency": true,
        "stable_connection": true,
        "recommended_primary": true
      }
    }
  ]
}
```

**Failover Indicators:**

- `connection_reliable`: Quality score >= 60 (suitable for general use)
- `low_latency`: Latency < 100ms (suitable for real-time applications)
- `stable_connection`: Stability score >= 70 (minimal packet loss/jitter)
- `recommended_primary`: Overall score >= 80 (excellent quality)

#### AgriX-Boost

```bash
python main.py --export agrix
```

**Output:** `exports/agrix_boost_connectivity.json`

**Data Structure:**

```json
{
  "metadata": {
    "export_timestamp": "2026-01-03T12:00:00",
    "source": "Rural Connectivity Mapper 2026",
    "total_locations": 5,
    "format_version": "1.0",
    "purpose": "farm_connectivity_layer"
  },
  "connectivity_layer": [
    {
      "location_id": "uuid",
      "coordinates": {
        "lat": -23.5505,
        "lon": -46.6333
      },
      "isp_provider": "Starlink",
      "measurement_time": "2026-01-15T10:30:00",
      "connectivity_status": {
        "quality_rating": "Excellent",
        "quality_score": 100.0,
        "is_operational": true,
        "is_optimal": true
      },
      "network_performance": {
        "download_speed_mbps": 165.4,
        "upload_speed_mbps": 22.8,
        "latency_ms": 28.5,
        "stability_pct": 96.6,
        "jitter_ms": 3.2,
        "packet_loss_pct": 0.1
      },
      "farm_suitability": {
        "iot_sensors_supported": true,
        "video_monitoring_supported": true,
        "real_time_control_supported": true,
        "data_analytics_supported": true
      },
      "recommendations": [
        "Excellent connectivity - Suitable for all farm automation systems",
        "Ideal for precision agriculture and autonomous equipment",
        "Supports video monitoring and remote surveillance",
        "Suitable for real-time sensor networks"
      ]
    }
  ]
}
```

**Farm Suitability Indicators:**

- `iot_sensors_supported`: Latency < 200ms AND quality >= 40 (basic IoT operation)
- `video_monitoring_supported`: Download >= 25 Mbps AND quality >= 60 (HD video streaming)
- `real_time_control_supported`: Latency < 50ms AND quality >= 80 (autonomous equipment)
- `data_analytics_supported`: Download >= 10 Mbps AND quality >= 40 (data transmission)

## Integration Workflow

### Complete Ecosystem Export

1. **Collect connectivity data:**

   ```bash
   python main.py --importar src/data/sample_data.csv
   ```

2. **Generate ecosystem bundle:**

   ```bash
   python main.py --export ecosystem
   ```

3. **Use exported data:**
   - Copy `exports/ecosystem/hybrid_simulator_input.json` to Hybrid Architecture Simulator
   - Copy `exports/ecosystem/agrix_boost_connectivity.json` to AgriX-Boost
   - Reference `exports/ecosystem/ecosystem_manifest.json` for integration metadata

### Automated Pipeline Example

```bash
# Full workflow with all features
python main.py \
  --importar src/data/sample_data.csv \
  --simulate \
  --analyze \
  --map \
  --relatorio json \
  --export ecosystem
```

This generates:

- Connectivity map (`connectivity_map_*.html`)
- JSON report (`report_*.json`)
- Complete ecosystem bundle (`exports/ecosystem/`)

## Use Cases

### 1. Failover Testing

Use Hybrid Architecture Simulator integration to:

- Test network failover with realistic latency profiles
- Simulate connection degradation scenarios
- Evaluate backup connection strategies
- Model satellite-to-terrestrial handoff

**Example Scenario:**

```bash
Primary: Starlink (28.5ms latency, 100.0 quality)
Backup: 4G LTE (68.2ms latency, 50.6 quality)
→ Test failover trigger at quality < 60
```

### 2. Farm Dashboard Integration

Use AgriX-Boost integration to:

- Display real-time connectivity status
- Show farm suitability for different applications
- Provide connectivity recommendations
- Plan IoT sensor deployment

**Example Farm Dashboard:**

```bash
Location: Rural Farm A
Provider: Starlink
Status: ✓ Operational
Quality: Excellent (100/100)

Supported Applications:
✓ IoT Sensors
✓ Video Monitoring
✓ Real-time Control
✓ Data Analytics
```

### 3. Research & Development

Use ecosystem data to:

- Study connectivity patterns in rural areas
- Correlate connectivity with agricultural productivity
- Test new agricultural IoT solutions
- Develop hybrid network architectures

## Data Quality & Reliability

### Quality Ratings

- **Excellent** (80-100): All applications supported
- **Good** (60-79): Most applications supported
- **Fair** (40-59): Basic applications supported
- **Poor** (<40): Limited functionality

### Update Frequency

- Real-time: Live measurements during data collection
- Batch: Import from CSV files
- Historical: Temporal analysis over time periods

### Validation

- Data undergoes validation checks during import and export
- Cross-checked with multiple measurements
- Anomalies flagged for review
All exported data includes:
- Timestamp of measurement
- Data source attribution
- Format version for compatibility
- Quality score breakdown

## API Integration (Future)

### Planned Features

- REST API endpoints for live data access
- WebSocket streaming for real-time updates
- GraphQL queries for flexible data retrieval
- OAuth authentication for secure access

### Example API Call (Future)

```bash
# Get connectivity data for location
curl -X GET https://api.rural-connectivity.io/v1/points \
  -H "Authorization: Bearer TOKEN" \
  -d "lat=-23.5505&lon=-46.6333"
```

## Support & Contribution

### Documentation

- **Main README:** [README.md](../README.md)
- **API Reference:** [API.md](API.md)
- **Ecosystem Guide:** This document

### Issues & Feedback

Report integration issues or request features:

- [GitHub Issues](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues)
- [GitHub Discussions](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/discussions)

### Contributing

We welcome contributions to improve ecosystem integration:

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit Pull Request

## Roadmap

### v1.1.0 (Q1 2026)

- [ ] Real-time data streaming
- [ ] SQLite database backend
- [ ] Enhanced export formats

### v1.2.0 (Q2 2026)

- [ ] REST API endpoints
- [ ] WebSocket integration
- [ ] GeoJSON/KML export

### v2.0.0 (H2 2026)

- [ ] GraphQL API
- [ ] Multi-project dashboard
- [ ] Advanced analytics integration

---

**Created:** January 2026  
**Version:** 1.0.0  
**Status:** Production Ready ✅
