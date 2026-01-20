# Ecosystem Export Examples

This document provides detailed examples of the ecosystem export formats.

## Table of Contents

1. [Ecosystem Bundle Overview](#ecosystem-bundle-overview)
2. [Hybrid Architecture Simulator Export](#hybrid-architecture-simulator-export)
3. [AgriX-Boost Export](#agrix-boost-export)
4. [Ecosystem Manifest](#ecosystem-manifest)

---

## Ecosystem Bundle Overview

The ecosystem bundle provides all necessary data for integration with Hybrid Architecture Simulator and AgriX-Boost in a single export command.

### Generate Ecosystem Bundle

```bash
python main.py --importar src/data/sample_data.csv --export ecosystem
```

### Output Files

Three files are generated in `exports/ecosystem/`:

1. **hybrid_simulator_input.json** - Failover testing data
2. **agrix_boost_connectivity.json** - Farm connectivity layer
3. **ecosystem_manifest.json** - Integration manifest

---

## Hybrid Architecture Simulator Export

### Purpose

Provides connectivity data formatted for realistic network failover testing and simulation.

### Key Features

- Signal quality metrics for failover decision-making
- Latency and stability scores for performance modeling
- Failover indicators for connection reliability
- Recommended primary/backup connection flags

### Example Export

```json
{
  "metadata": {
    "export_timestamp": "2026-01-04T00:03:17.879596",
    "source": "Rural Connectivity Mapper 2026",
    "total_points": 5,
    "format_version": "1.0",
    "purpose": "failover_testing"
  },
  "connectivity_points": [
    {
      "point_id": "3",
      "location": {
        "latitude": -15.7801,
        "longitude": -47.9292
      },
      "provider": "Starlink",
      "timestamp": "2026-01-15T11:30:00",
      "metrics": {
        "signal_quality": 100.0,
        "latency_ms": 28.5,
        "download_mbps": 165.4,
        "upload_mbps": 22.8,
        "stability_score": 92.6,
        "jitter_ms": 3.2,
        "packet_loss_pct": 0.1
      },
      "quality_breakdown": {
        "overall_score": 100.0,
        "speed_score": 100.0,
        "latency_score": 100.0,
        "stability_score": 100.0,
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

### Failover Indicators Explained

| Indicator | Threshold | Description |
| --------- | --------- | ----------- |
| `connection_reliable` | Quality ≥ 60 | Connection suitable for general use |
| `low_latency` | Latency < 100ms | Suitable for real-time applications |
| `stable_connection` | Stability ≥ 70 | Minimal packet loss and jitter |
| `recommended_primary` | Overall ≥ 80 | Excellent quality, recommended as primary |

### Use Case Example

**Scenario:** Testing failover between Starlink and 4G LTE

```bash# Hybrid Simulator Input Example
{
  "location_id": "3",
  "coordinates": {
    "lat": -15.7801,
    "lon": -47.9292
  },      
Primary Connection: Starlink
- Signal Quality: 100.0
- Latency: 28.5ms
- Recommended Primary: ✓

Backup Connection: 4G LTE  
- Signal Quality: 50.6
- Latency: 68.2ms
- Recommended Primary: ✗

Failover Trigger: When primary quality drops below 60
```

---

## AgriX-Boost Export

### Purpose

Provides connectivity layer data for agricultural monitoring and farm dashboard integration.

### Key Features

- Network performance metrics for farm operations
- Farm suitability indicators for specific use cases
- Connectivity recommendations for farmers
- Status flags for operational readiness

### Example Export

```json
{
  "metadata": {
    "export_timestamp": "2026-01-04T00:03:17.880089",
    "source": "Rural Connectivity Mapper 2026",
    "total_locations": 5,
    "format_version": "1.0",
    "purpose": "farm_connectivity_layer"
  },
  "connectivity_layer": [
    {
      "location_id": "3",
      "coordinates": {
        "lat": -15.7801,
        "lon": -47.9292
      },
      "isp_provider": "Starlink",
      "measurement_time": "2026-01-15T11:30:00",
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
        "stability_pct": 92.6,
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

### Farm Suitability Indicators Explained

| Use Case | Requirements | Description |
| -------- | ----------- | ----------- |
| **IoT Sensors** | Latency < 200ms, Quality ≥ 40 | Basic sensor data collection and transmission |
| **Video Monitoring** | Download ≥ 25 Mbps, Quality ≥ 60 | HD video streaming for surveillance |
| **Real-time Control** | Latency < 50ms, Quality ≥ 80 | Autonomous equipment and precision agriculture |
| **Data Analytics** | Download ≥ 10 Mbps, Quality ≥ 40 | Large dataset transmission and cloud processing |

### Farm Dashboard Integration Example

**Visual Representation:**

```bash
╔════════════════════════════════════════════════╗
║         Farm Connectivity Dashboard            ║
╠════════════════════════════════════════════════╣
║ Location: Brasília Farm                        ║
║ Provider: Starlink                             ║
║ Status: ✓ Operational (Optimal)                ║
║ Quality: Excellent (100/100)                   ║
╠════════════════════════════════════════════════╣
║ Network Performance:                           ║
║   Download: 165.4 Mbps                         ║
║   Upload: 22.8 Mbps                            ║
║   Latency: 28.5 ms                             ║
║   Stability: 92.6%                             ║
╠════════════════════════════════════════════════╣
║ Supported Farm Applications:                   ║
║   ✓ IoT Sensors                                ║
║   ✓ Video Monitoring                           ║
║   ✓ Real-time Control                          ║
║   ✓ Data Analytics                             ║
╠════════════════════════════════════════════════╣
║ Recommendations:                               ║
║   • Excellent connectivity - All systems go!   ║
║   • Ideal for precision agriculture            ║
║   • Supports autonomous equipment              ║
╚════════════════════════════════════════════════╝
```

---

## Ecosystem Manifest

### Purpose

Provides metadata and integration information for the entire ecosystem.

### Example Manifest

```json
{
  "ecosystem": "Rural Connectivity Ecosystem 2026",
  "version": "1.0.0",
  "created": "2026-01-04T00:03:17.880342",
  "components": {
    "rural_connectivity_mapper": {
      "description": "Map and analyze rural internet connectivity",
      "repository": "https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026",
      "data_points": 5
    },
    "hybrid_architecture_simulator": {
      "description": "Test realistic failover scenarios",
      "input_file": "hybrid_simulator_input.json",
      "purpose": "Failover testing with real connectivity data"
    },
    "agrix_boost": {
      "description": "Connectivity layer for farm dashboards",
      "input_file": "agrix_boost_connectivity.json",
      "purpose": "Agricultural monitoring and farm management"
    }
  },
  "integration_notes": [
    "Rural Connectivity Mapper provides real-world connectivity data",
    "Hybrid Architecture Simulator uses data for failover scenario testing",
    "AgriX-Boost integrates connectivity layer into farm dashboards",
    "All three projects share common data formats for seamless integration"
  ],
  "data_summary": {
    "total_points": 5,
    "providers": [
      "Starlink",
      "Claro",
      "Viasat",
      "HughesNet",
      "Various"
    ],
    "quality_distribution": {
      "Excellent": 2,
      "Good": 1,
      "Fair": 1,
      "Poor": 1,
      "Unknown": 0
    }
  }
}
```

### Manifest Fields Explained

| Field | Description |
| ------- | ----------- |
| `ecosystem` | Name of the ecosystem |
| `version` | Ecosystem format version |
| `created` | Export timestamp |
| `components` | All integrated projects |
| `integration_notes` | Integration guidelines |
| `data_summary` | Overview of exported data |

---

## Integration Workflow

### Complete Example

```bash
# Step 1: Import data
python main.py --importar src/data/sample_data.csv

# Step 2: Simulate improvements (optional)
python main.py --simulate

# Step 3: Generate ecosystem bundle
python main.py --export ecosystem

# Step 4: Use exported files
# - Copy exports/ecosystem/hybrid_simulator_input.json to Hybrid Architecture Simulator
# - Copy exports/ecosystem/agrix_boost_connectivity.json to AgriX-Boost
# - Reference exports/ecosystem/ecosystem_manifest.json for metadata
```

### Individual Exports

```bash
# Export only for Hybrid Architecture Simulator
python main.py --export hybrid
# Output: exports/hybrid_simulator_input.json

# Export only for AgriX-Boost
python main.py --export agrix
# Output: exports/agrix_boost_connectivity.json
```

---

## Quality Ratings Reference

| Rating | Score Range | Hybrid Simulator | AgriX-Boost |
| ------- | ----------- | ---------------- | ----------- |
| **Excellent** | 80-100 | Recommended primary | All applications supported |
| **Good** | 60-79 | Connection reliable | Most applications supported |
| **Fair** | 40-59 | Backup only | Basic applications only |
| **Poor** | 0-39 | Not recommended | Limited functionality |

---

**Last Updated:** January 4, 2026  
**Format Version:** 1.0
