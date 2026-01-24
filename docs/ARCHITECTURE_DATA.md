# Data Architecture Documentation

## Overview

This document describes the data architecture for the Rural Connectivity Mapper's "Source of Truth" (Pilar 1). The architecture implements a robust data pipeline with quality scoring, data contracts, and reproducibility.

## Architecture Principles

1. **Immutability**: Raw data (bronze layer) is never modified
2. **Traceability**: Every transformation is documented and reproducible
3. **Quality First**: All data includes confidence scores and quality metrics
4. **Extensibility**: Easy to add new data sources and transformations

## Pipeline Architecture

### Three-Layer Medallion Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       DATA SOURCES                          │
│  Crowdsource | Speedtest | ANATEL | IBGE | Starlink | ...  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    BRONZE LAYER (Raw)                        │
│  - Immutable source data                                     │
│  - Organized by source and ingestion timestamp               │
│  - No transformations applied                                │
│  - JSON format: data/bronze/{source}/{source}_{timestamp}.json│
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  SILVER LAYER (Normalized)                   │
│  - Deduplicated data                                         │
│  - Validated and normalized schema                           │
│  - Confidence scores calculated                              │
│  - H3 geospatial indexing added                              │
│  - JSON format: data/silver/silver_{timestamp}.json          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   GOLD LAYER (Aggregated)                    │
│  - Geographic aggregations (H3 cells)                        │
│  - Source aggregations                                       │
│  - Ready for consumption by applications                     │
│  - JSON format: data/gold/{aggregation}_{timestamp}.json    │
└─────────────────────────────────────────────────────────────┘
```

## Canonical Schema

### MeasurementSchema

The canonical schema represents the "source of truth" for all connectivity measurements:

```python
{
  # Identity
  "id": "unique_identifier",
  
  # Location (required)
  "lat": -15.7801,        # Latitude (-90 to 90)
  "lon": -47.9292,        # Longitude (-180 to 180)
  
  # Temporal
  "timestamp_utc": "2024-01-15T10:30:00Z",
  
  # Connectivity Metrics
  "download_mbps": 100.5,  # Optional, >= 0
  "upload_mbps": 20.3,     # Optional, >= 0
  "latency_ms": 25.1,      # Optional, >= 0
  
  # Technology & Source
  "technology": "fiber",    # Enum: fiber, cable, dsl, satellite, mobile_4g, mobile_5g, fixed_wireless, other, unknown
  "source": "anatel",      # Enum: crowdsource, anatel, ibge, starlink, speedtest, manual, other
  "provider": "Vivo",      # Optional
  
  # Quality & Confidence (added in silver layer)
  "confidence_score": 87.5,           # 0-100
  "confidence_breakdown": {
    "recency_score": 100.0,           # 0-100
    "source_reliability_score": 95.0, # 0-100
    "consistency_score": 85.0,        # 0-100
    "completeness_score": 70.0        # 0-100
  },
  
  # Geographic Indexing (added in silver layer)
  "h3_index": "87283082bffffff",     # H3 cell for aggregation
  
  # Additional Metadata
  "country": "BR",         # ISO 3166-1 alpha-2
  "region": "DF",          # Optional
  "metadata": {            # Optional, source-specific
    "key": "value"
  }
}
```

## Confidence Scoring

### Overview

Every measurement in the silver and gold layers includes a **confidence score** (0-100) that indicates the reliability of the data. Higher scores mean more trustworthy data.

### Calculation Method

The confidence score is a weighted average of four components:

| Component | Weight | Description |
|-----------|--------|-------------|
| **Recency** | 40% | How recent is the measurement |
| **Source Reliability** | 30% | How trustworthy is the data source |
| **Consistency** | 20% | Outlier detection and validation |
| **Completeness** | 10% | How complete is the metadata |

### Component Details

#### 1. Recency Score (40%)

Measures how fresh the data is:

- **Fresh (< 7 days)**: 100% score
- **Stale (> 365 days)**: 0% score
- **Medium**: Linear decay between fresh and stale
- **Future timestamps**: 10% score (suspicious)

#### 2. Source Reliability Score (30%)

Based on the trustworthiness of the data source:

| Source | Weight | Justification |
|--------|--------|---------------|
| ANATEL | 95% | Official regulatory data |
| IBGE | 90% | Government statistical data |
| Starlink | 85% | Direct from provider |
| Speedtest | 75% | Established testing platform |
| Crowdsource | 60% | Community data, variable quality |
| Manual | 50% | Manual entry, needs verification |
| Other | 40% | Unknown source |

These weights are configurable in `src/quality/confidence.py`.

#### 3. Consistency Score (20%)

Validates that measurements are within reasonable ranges:

- **Download speed**: 0.1 - 10,000 Mbps
- **Upload speed**: 0.1 - 5,000 Mbps
- **Latency**: 1 - 2,000 ms
- **Ratio check**: Upload shouldn't exceed download * 2 (except special cases)

Penalties:
- Out-of-range values: -30 points per metric
- Suspicious ratios: -15 points

#### 4. Completeness Score (10%)

Measures how complete the measurement is:

- **Core fields**: Base score for required fields (id, lat, lon, timestamp, source)
- **Metrics**: +20 points for each metric (download, upload, latency)
- **Metadata**: +10 points for each additional field (technology, provider, country, region)
- **Extra metadata**: +10 points for additional metadata

Normalized to 0-100 scale.

### Example Scores

**High Quality Measurement** (Score: ~90):
- Fresh data (2 days old) → Recency: 100
- ANATEL source → Reliability: 95
- Valid metrics → Consistency: 100
- Complete metadata → Completeness: 85

**Medium Quality Measurement** (Score: ~60):
- Older data (90 days) → Recency: 75
- Crowdsource → Reliability: 60
- Valid metrics → Consistency: 100
- Partial metadata → Completeness: 50

**Low Quality Measurement** (Score: ~30):
- Very old (400 days) → Recency: 0
- Unknown source → Reliability: 40
- Outlier values → Consistency: 70
- Minimal metadata → Completeness: 30

## Deduplication Strategy

Measurements are considered duplicates if they have:
1. Same location (rounded to 4 decimal places ≈ 11 meters)
2. Same timestamp hour

When duplicates are found, we keep the measurement with the most complete data.

## Geographic Aggregation

### H3 Indexing

We use Uber's [H3 hexagonal hierarchical spatial index](https://h3geo.org/) for geographic aggregation:

- **Resolution**: 7 (≈ 5 km² per cell)
- **Benefits**: 
  - Uniform cell sizes
  - Efficient aggregation
  - Hierarchical analysis support

Each measurement in the silver layer receives an `h3_index` field.

### Gold Layer Aggregations

The gold layer provides aggregated views:

#### 1. Geographic Aggregation (`geographic_h3_{timestamp}.json`)

For each H3 cell:
- Average download/upload/latency
- Measurement count
- Average confidence score
- Technology distribution

#### 2. Source Aggregation (`by_source_{timestamp}.json`)

For each data source:
- Measurement count
- Average confidence score
- List of measurement IDs

#### 3. Full Dataset (`full_dataset_{timestamp}.json`)

Complete enriched dataset with all measurements and their confidence scores.

## Data Sources

### Current Sources

#### 1. Mock Crowdsource Source
- **Purpose**: Simulates community-submitted measurements
- **Coverage**: Rural Brazil
- **Sample Size**: Configurable (default: 50)
- **Characteristics**:
  - Various technologies (4G, satellite, DSL, fixed wireless)
  - 10-20% missing data (realistic)
  - Time range: Last 90 days

#### 2. Mock Speedtest Source
- **Purpose**: Simulates professional speed test platforms
- **Coverage**: Rural United States
- **Sample Size**: Configurable (default: 30)
- **Characteristics**:
  - Better technologies (fiber, cable, 5G)
  - Higher data completeness (95%+)
  - Time range: Last 30 days

### Adding New Sources

To add a new data source:

1. Create a new class in `src/sources/` inheriting from `DataSource`
2. Implement the `fetch()` method returning `List[MeasurementSchema]`
3. Add the source to `PipelineOrchestrator` in your script

Example:

```python
from src.sources import DataSource
from src.schemas import MeasurementSchema

class MyCustomSource(DataSource):
    def __init__(self):
        super().__init__("my_custom_source")
    
    def fetch(self) -> List[MeasurementSchema]:
        # Implement data fetching logic
        measurements = []
        # ... fetch and transform data ...
        return measurements
```

## Running the Pipeline

### Prerequisites

```bash
# Install dependencies
make install
```

### Execute Pipeline

```bash
# Run complete pipeline (bronze → silver → gold)
make data-build
```

This will:
1. Ingest data from all configured sources into bronze layer
2. Process and enrich data into silver layer
3. Aggregate data into gold layer
4. Output summary statistics

### Output Structure

```
data/
├── bronze/
│   ├── mock_crowdsource/
│   │   └── mock_crowdsource_20240115_103000.json
│   └── mock_speedtest/
│       └── mock_speedtest_20240115_103000.json
├── silver/
│   └── silver_20240115_103030.json
└── gold/
    ├── geographic_h3_20240115_103045.json
    ├── by_source_20240115_103045.json
    └── full_dataset_20240115_103045.json
```

## Validation & Testing

### Running Tests

```bash
# Run all tests
make test

# Run only quality/confidence tests
make test-quality
```

### Test Coverage

- **Schema Validation**: Ensures data contracts are enforced
- **Confidence Scoring**: Validates all scoring components
- **Range Validation**: Checks coordinate and metric ranges
- **Normalization**: Tests data transformations

## API & Programmatic Access

### Python API

```python
from src.pipeline import PipelineOrchestrator
from src.sources import MockCrowdsourceSource, MockSpeedtestSource

# Initialize sources
sources = [
    MockCrowdsourceSource(num_samples=100),
    MockSpeedtestSource(num_samples=50),
]

# Run pipeline
pipeline = PipelineOrchestrator()
pipeline.run(sources)

# Access data
from src.pipeline import SilverLayer, GoldLayer

silver = SilverLayer("data/silver")
measurements = silver.read_latest()

gold = GoldLayer("data/gold")
geo_data = gold.read_latest("geographic_h3")
```

## Performance Considerations

### Scalability

Current implementation is optimized for:
- **Volume**: Up to 100K measurements per run
- **Frequency**: Hourly or daily runs
- **Storage**: JSON files for simplicity and reproducibility

For larger scale:
- Consider Parquet format for better compression
- Implement incremental processing
- Add database backend (PostgreSQL with PostGIS)

### Optimization Tips

1. **Deduplication**: Use hash-based lookups for large datasets
2. **H3 Indexing**: Pre-calculate H3 cells in bronze layer if needed
3. **Parallel Processing**: Sources can be ingested in parallel
4. **Incremental Updates**: Process only new bronze files

## Future Enhancements

### Planned Improvements

1. **Real Data Sources**
   - ANATEL API integration
   - IBGE data connector
   - Starlink coverage API
   - Public speedtest platforms

2. **Advanced Quality**
   - ML-based outlier detection
   - Cross-validation between sources
   - Temporal consistency checks
   - Geographic consistency validation

3. **Performance**
   - Parquet storage format
   - Incremental processing
   - Distributed processing (Spark/Dask)

4. **Monitoring**
   - Data quality dashboards
   - Pipeline execution metrics
   - Alerting on quality degradation

## Troubleshooting

### Common Issues

**Issue**: Pipeline fails with import errors
```bash
# Solution: Ensure dependencies are installed
make install
```

**Issue**: No data in gold layer
```bash
# Solution: Check that sources are returning data
python -c "from src.sources import MockCrowdsourceSource; print(len(MockCrowdsourceSource().fetch()))"
```

**Issue**: Low confidence scores
- Check data recency (old data gets low scores)
- Verify source reliability weights
- Ensure metrics are in valid ranges

## References

- [H3 Hexagonal Hierarchical Spatial Index](https://h3geo.org/)
- [Pydantic Data Validation](https://docs.pydantic.dev/)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)

## Contact & Support

For questions or issues with the data architecture:
1. Check this documentation
2. Run tests to verify setup: `make test`
3. Review example outputs in `data/` directories
4. Consult the code documentation in `src/`
