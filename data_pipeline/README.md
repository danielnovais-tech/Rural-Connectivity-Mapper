# ANATEL Static Connector

## Overview

The ANATEL Static Connector is a data pipeline component that processes CSV files containing ANATEL (Brazilian National Telecommunications Agency) connectivity data and converts them to the more efficient Parquet format for storage and analysis.

## Features

- ✅ Reads CSV files from the manual data directory
- ✅ Validates data structure and required fields
- ✅ Converts to Parquet format for efficient storage
- ✅ Generates detailed JSON processing reports
- ✅ Handles multiple CSV files in batch
- ✅ Provides clear error reporting and validation

## Directory Structure

```
data_pipeline/
└── connectors/
    └── anatel_static_connector.py    # Main connector script

data/
├── manual/                            # Input directory (CSV files)
│   └── anatel_backhaul.csv           # Sample ANATEL data
└── bronze/
    └── anatel/                        # Output directory
        ├── *.parquet                  # Converted data files
        └── anatel_processing_report_*.json  # Processing reports
```

## Usage

### Basic Usage

```bash
# Place CSV files in data/manual/
# Run the connector
python data_pipeline/connectors/anatel_static_connector.py
```

### Expected Output

```
======================================================================
🚀 ANATEL Static Connector - Starting Processing
======================================================================
📁 Found 1 CSV file(s) in data/manual

📄 Processing: anatel_backhaul.csv
   ✓ Read 20 records
   ✓ Columns: ['id', 'uf', 'municipio', 'latitude', 'longitude', ...]
   ✓ Validation passed
   ✓ Saved to: data/bronze/anatel/anatel_backhaul_20260124_175248.parquet

======================================================================
📊 Processing Summary
======================================================================
Total files: 1
Successful: 1
Failed: 0
Total records processed: 20

📋 Report saved to: data/bronze/anatel/anatel_processing_report_20260124_175248.json
======================================================================

✅ All files processed successfully!
```

## Input Data Format

CSV files should contain ANATEL connectivity data with at minimum:

**Required fields:**
- `latitude` - Location latitude (decimal degrees)
- `longitude` - Location longitude (decimal degrees)

**Recommended fields:**
- `id` - Unique identifier
- `uf` - Brazilian state code (e.g., "SP", "RJ")
- `municipio` - Municipality name
- `technology` - Connection technology type
- `capacity_mbps` - Connection capacity in Mbps
- `provider` - Service provider name
- `timestamp_utc` - Data timestamp in UTC
- `source` - Data source identifier

## Output Files

### Parquet Files
- Compressed binary format for efficient storage
- Preserves all data types and schema
- Optimized for analytical queries
- Filename pattern: `{csv_name}_{timestamp}.parquet`

### Processing Reports
JSON files containing:
- Execution timestamp
- Files processed with status
- Statistics (record counts, columns)
- Validation errors (if any)
- Sample record from each file

Example report structure:
```json
{
  "connector": "ANATEL Static Connector",
  "execution_timestamp": "2026-01-24T17:52:48.123456Z",
  "files_processed": [
    {
      "filename": "anatel_backhaul.csv",
      "status": "success",
      "records_processed": 20,
      "output_file": "data/bronze/anatel/anatel_backhaul_20260124_175248.parquet",
      "statistics": {
        "total_records": 20,
        "columns": ["id", "uf", "municipio", ...],
        "sample_record": {...}
      }
    }
  ],
  "summary": {
    "total_files": 1,
    "successful": 1,
    "failed": 0,
    "total_records": 20
  }
}
```

## Validation

The connector performs the following validations:

1. **File existence check** - Ensures input directory exists
2. **DataFrame validation** - Checks for empty DataFrames
3. **Required fields check** - Validates presence of `latitude` and `longitude`
4. **Null value detection** - Identifies missing values in critical fields

Failed validations are logged in the processing report.

## Dependencies

- `pandas>=2.0.0` - Data manipulation
- `pyarrow>=11.0.0` - Parquet file format support

Install with:
```bash
pip install pandas pyarrow
```

## Integration with Existing Pipeline

This connector produces data in the **Bronze Layer** format, which is the first stage of the data pipeline:

```
Sources (CSV files)
    ↓
Bronze Layer (Raw Parquet - this connector)
    ↓
Silver Layer (Normalized, Validated)
    ↓
Gold Layer (Aggregated, Analysis-Ready)
```

## Sample Data

A sample ANATEL backhaul dataset is included at `data/manual/anatel_backhaul.csv` for testing and demonstration purposes. This dataset contains 20 records from major Brazilian cities with backhaul infrastructure information.

## Troubleshooting

**No CSV files found:**
- Ensure CSV files are placed in the `data/manual/` directory
- Check file extensions (must be `.csv`)

**Validation errors:**
- Verify CSV contains `latitude` and `longitude` columns
- Check for proper CSV formatting
- Review the processing report for specific error details

**Import errors:**
- Install required dependencies: `pip install pandas pyarrow`
- Verify Python version compatibility (3.8+)

## Future Enhancements

- [ ] Support for direct API integration with ANATEL
- [ ] Data schema validation against canonical schemas
- [ ] Automatic data quality scoring
- [ ] Integration with Silver layer processing
- [ ] Support for incremental updates
- [ ] Compression options for Parquet files
