# Data Pipeline - ANATEL Static Connector

This directory contains the data pipeline infrastructure for processing telecommunication data from various sources.

## Overview

The ANATEL Static Connector is designed to process CSV files manually downloaded from the Brazilian telecommunications regulatory agency (ANATEL).

## Directory Structure

```
data_pipeline/
├── connectors/
│   ├── anatel_static_connector.py  # Main connector for processing ANATEL CSVs
│   ├── data_schemas.py            # Data schema definitions
│   └── __init__.py
└── __init__.py

data/
├── manual/                         # Place downloaded CSV files here
│   └── processados/               # Processed files are moved here
├── bronze/anatel/                 # Processed data in Parquet format
├── silver/                        # (Future) Unified and cleaned data
└── gold/                          # (Future) Final indicators
```

## Usage

### 1. Download CSV Files from ANATEL

Follow the instructions in: `scripts/fetch_anatel_instructions.md`

Key steps:
1. Visit: https://dadosabertos.anatel.gov.br/
2. Search for:
   - "Backhaul" (transport infrastructure)
   - "Estações de Telecomunicações" (telecom stations)
   - "Acessos Fixos" (fixed broadband access)
3. Download CSV files
4. Place them in `data/manual/` directory

### 2. Run the Connector

```bash
# From the repository root
python data_pipeline/connectors/anatel_static_connector.py
```

Or import and use programmatically:

```python
from data_pipeline.connectors import AnatelStaticConnector

# Create connector instance
connector = AnatelStaticConnector()

# Process all CSV files in data/manual/
results = connector.run()

# Check results
for result in results:
    if result['status'] == 'success':
        print(f"✅ Processed: {result['stats']['arquivo_origem']}")
        print(f"   Type: {result['stats']['dataset_tipo']}")
        print(f"   Records: {result['stats']['registros_processados']}")
    else:
        print(f"❌ Error: {result['file']} - {result['error']}")
```

### 3. Access Processed Data

Processed data is saved in Parquet format in `data/bronze/anatel/`:

```python
import pandas as pd
from pathlib import Path

# List processed files
bronze_dir = Path("data/bronze/anatel")
parquet_files = list(bronze_dir.glob("*.parquet"))

# Read a file
df = pd.read_parquet(parquet_files[0])
print(df.head())
```

## Supported Dataset Types

The connector automatically identifies and processes three types of ANATEL datasets:

### 1. Backhaul Infrastructure
- **Expected columns**: id, municipio, uf, operadora, latitude, longitude, frequencia, capacidade_mbps
- **Description**: Transport infrastructure data

### 2. Telecom Stations (Estações)
- **Expected columns**: id, municipio, uf, operadora, tecnologia, latitude, longitude
- **Description**: Telecommunications station data

### 3. Fixed Access (Acesso Fixo)
- **Expected columns**: municipio, uf, quantidade, velocidade, tecnologia
- **Description**: Fixed broadband access data

## Features

### Automatic Processing
- **Encoding Detection**: Tries UTF-8, Latin-1, and CP1252
- **Type Inference**: Identifies dataset type by filename and columns
- **Data Validation**: Validates geographic coordinates (Brazil bounds)
- **Data Cleaning**: Normalizes strings, converts types, removes invalid records

### Metadata Addition
Each processed record includes:
- `_processamento_data`: Processing timestamp
- `_dataset_tipo`: Dataset type
- `_confidence_score`: Data quality score (0.9 for official data)

### File Organization
- Original CSV files are moved to `data/manual/processados/`
- Processed data saved as Parquet in `data/bronze/anatel/`
- Processing report generated as JSON

## Dependencies

Required Python packages:
- pandas >= 2.0.0
- pyarrow >= 10.0.0
- geohash2 >= 1.1 (optional, for geographic hashing)

Install with:
```bash
pip install pandas pyarrow geohash2
```

## Testing

Run the test suite:

```bash
pytest tests/test_anatel_static_connector.py -v
```

## Troubleshooting

### "No files found"
- Ensure CSV files are in `data/manual/` directory
- Check file extension is `.csv` or `.CSV`

### "Unable to decode file"
- File may be corrupted
- Try opening in a text editor to verify content

### "Unknown dataset type"
- File doesn't match known schemas
- Verify column names match expected schemas

## Next Steps

After processing ANATEL data:
1. Run the fusion engine to combine with other data sources
2. Generate unified views in `data/silver/`
3. Create final indicators in `data/gold/`

## Support

For issues or questions:
- Check the user guide: `scripts/fetch_anatel_instructions.md`
- Review test examples: `tests/test_anatel_static_connector.py`
- Open an issue on the project repository
