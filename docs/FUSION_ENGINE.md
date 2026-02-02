# Fusion Engine Documentation

## Overview

The **Fusion Engine** is a critical component of the Rural Connectivity Mapper data pipeline that bridges the gap between the Bronze (raw data) and Silver (normalized, validated) layers. It is responsible for:

1. **Reading processed data** from the Bronze layer (supports both JSON and Parquet formats)
2. **Unifying data** from multiple sources (official APIs, crowdsourcing, etc.)
3. **Calculating the Rural Connectivity Index (ICR)** for each measurement
4. **Preparing unified data** for Silver layer processing

## Architecture

The Fusion Engine fits into the data pipeline as follows:

```
Data Sources → Bronze Layer → Fusion Engine → Silver Layer → Gold Layer
               (Raw Data)     (Unify & ICR)   (Validate)    (Aggregate)
```

## Rural Connectivity Index (ICR)

### What is ICR?

The **Índice de Conectividade Rural (ICR)** is a composite metric that evaluates the quality of rural connectivity. It provides a single score from 0-100 that reflects the overall connectivity quality at a given location.

### ICR Calculation

The ICR is calculated using a weighted formula based on four components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Download Speed | 40% | Download bandwidth (0-100+ Mbps) |
| Upload Speed | 30% | Upload bandwidth (0-50+ Mbps) |
| Latency | 20% | Round-trip time, inverted (lower is better) |
| Availability | 10% | Data completeness (all metrics present) |

**Formula:**
```
ICR = (download_score × 0.40) + (upload_score × 0.30) + 
      (latency_score × 0.20) + (availability_score × 0.10)
```

### ICR Classification

| ICR Range | Classification | Description |
|-----------|---------------|-------------|
| 76-100 | Excellent | High-quality connectivity, suitable for all applications |
| 51-75 | Good | Adequate connectivity for most applications |
| 26-50 | Fair | Basic connectivity, may struggle with bandwidth-intensive apps |
| 0-25 | Poor | Minimal connectivity, significant limitations |

### Component Scoring

**Download Speed:**
- 0 Mbps = 0 points
- 100+ Mbps = 100 points
- Linear scaling between 0-100 Mbps

**Upload Speed:**
- 0 Mbps = 0 points
- 50+ Mbps = 100 points
- Linear scaling between 0-50 Mbps

**Latency (inverted):**
- 0-50 ms = 100 points
- 500+ ms = 0 points
- Linear scaling (lower latency = higher score)

**Availability:**
- All 3 metrics present = 100 points
- 2 metrics present = 66.67 points
- 1 metric present = 33.33 points
- No metrics = 0 points

## Usage

### Basic Usage

```python
from pathlib import Path
from src.pipeline import FusionEngine

# Initialize fusion engine
bronze_dir = Path("data/bronze")
fusion = FusionEngine(bronze_dir)

# Process Bronze layer data (auto-detect format)
enriched_measurements = fusion.process(format="auto")

# Each measurement now has ICR in metadata
for measurement in enriched_measurements:
    icr = measurement.metadata['icr']
    classification = measurement.metadata['icr_classification']
    print(f"ICR: {icr:.2f} ({classification})")
```

### Reading Specific Formats

```python
# Read only JSON files
measurements = fusion.read_bronze_json()

# Read only Parquet files (requires pandas)
measurements = fusion.read_bronze_parquet()

# Read from specific source
measurements = fusion.read_bronze_json(source_name="anatel")
```

### Standalone ICR Calculation

```python
from src.pipeline import FusionEngine

# Initialize (bronze_dir can be any path for standalone use)
fusion = FusionEngine(Path("/tmp"))

# Calculate ICR for measurements you already have
measurements = [...]  # Your list of MeasurementSchema objects
enriched = fusion.calculate_icr(measurements)

# Access ICR data
for m in enriched:
    print(f"ICR: {m.metadata['icr']}")
    print(f"Components: {m.metadata['icr_components']}")
    print(f"Classification: {m.metadata['icr_classification']}")
```

### Integration with Pipeline

The Fusion Engine is automatically integrated with the `PipelineOrchestrator`:

```python
from src.pipeline import PipelineOrchestrator
from src.sources import MockCrowdsourceSource, MockSpeedtestSource

# Initialize pipeline (fusion enabled by default)
pipeline = PipelineOrchestrator(use_fusion=True)

# Run pipeline
sources = [
    MockCrowdsourceSource(num_samples=50),
    MockSpeedtestSource(num_samples=30),
]
pipeline.run(sources)

# ICR is automatically calculated and added to all measurements
```

To disable fusion:
```python
pipeline = PipelineOrchestrator(use_fusion=False)
```

## Output Format

After fusion processing, each measurement includes:

```json
{
  "id": "measurement_123",
  "lat": -15.7801,
  "lon": -47.9292,
  "download_mbps": 100.0,
  "upload_mbps": 50.0,
  "latency_ms": 20.0,
  "source": "anatel",
  "metadata": {
    "fusion_metadata": {
      "unified_at": "2026-01-24T17:57:30.065269+00:00",
      "source": "anatel"
    },
    "icr": 92.34,
    "icr_components": {
      "download_score": 100.0,
      "upload_score": 100.0,
      "latency_score": 96.0,
      "availability_score": 100.0
    },
    "icr_classification": "excellent"
  }
}
```

## File Format Support

### JSON (Default)

The Fusion Engine natively supports JSON files from the Bronze layer:
- No additional dependencies required
- Standard format used by BronzeLayer
- Files follow pattern: `{source_name}_{timestamp}.json`

### Parquet (Optional)

Parquet support requires pandas and pyarrow:

```bash
pip install pandas pyarrow
```

Files should follow pattern: `{source_name}_{timestamp}.parquet`

## Testing

Run the fusion engine tests:

```bash
# Run all fusion engine tests
pytest tests/test_fusion_engine.py -v

# Run specific test
pytest tests/test_fusion_engine.py::TestFusionEngine::test_calculate_icr -v
```

## Demonstration

Try the fusion engine demo:

```bash
python demo_fusion_engine.py
```

This will:
1. Generate sample data if needed
2. Demonstrate fusion engine capabilities
3. Show ICR calculations and classifications
4. Display statistics and sample measurements

## Technical Details

### Performance

- **Memory efficient**: Processes measurements in streaming fashion
- **Fast**: Leverages Pydantic for validation
- **Scalable**: Can handle large datasets with millions of measurements

### Error Handling

The Fusion Engine gracefully handles:
- Missing or corrupt files
- Invalid JSON/Parquet data
- Missing metrics (assigns neutral scores)
- Empty Bronze layer (returns empty list)

### Logging

Enable logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Best Practices

1. **Run fusion before Silver layer**: Fusion should always run before Silver layer processing to ensure ICR is calculated

2. **Use auto-detection**: Let the engine auto-detect file formats unless you have a specific reason to specify

3. **Monitor ICR distributions**: Track ICR classifications over time to identify trends

4. **Validate results**: Spot-check ICR calculations against raw metrics to ensure accuracy

5. **Update weights as needed**: The ICR weights (40/30/20/10) can be adjusted in `fusion_engine.py` if your use case requires different priorities

## Future Enhancements

Potential improvements for future versions:

- [ ] Support for additional file formats (CSV, Avro)
- [ ] Configurable ICR weights
- [ ] Time-series ICR trends
- [ ] Geographic ICR heatmaps
- [ ] Automated ICR threshold alerts
- [ ] Machine learning-based ICR predictions

## See Also

- [Data Architecture](ARCHITECTURE_DATA.md) - Overall pipeline architecture
- [README](../README.md) - Project overview and quick start guide
