# CSV Upload Script Documentation

## Overview

The CSV Upload Script is a standalone tool for validating and uploading speedtest data to the Rural Connectivity Mapper 2026 system. It provides the **lowest barrier to entry** for contributors and rural testers to submit connectivity measurements.

## Features

- ✅ **Schema Validation**: Validates all required fields (timestamp, lat/lon, download/upload)
- 📊 **Detailed Error Reporting**: Clear, actionable error messages for invalid data
- 🚀 **Easy to Use**: Single command to validate and convert CSV to JSON
- 💾 **Flexible Output**: Save to custom file paths or validate without saving
- 🔍 **Dry-Run Mode**: Validate CSV without creating output files
- 📈 **Statistics**: Shows validation summary with row counts and missing fields

## Quick Start

### Basic Usage

```bash
# Validate and convert example file
python upload_csv.py example_speedtests.csv

# Output: speedtest_data.json (default)
```

### Custom Output

```bash
# Specify custom output file
python upload_csv.py my_data.csv --output results.json
```

### Validation Only (Dry-Run)

```bash
# Validate without creating output file
python upload_csv.py data.csv --dry-run

# Show detailed error messages
python upload_csv.py data.csv --dry-run --verbose
```

## CSV Format

### Required Columns

All CSV files **must** include these columns:

| Column | Type | Description | Example |
| -------- | ------- | ------------- | --------- |
| `timestamp` | ISO 8601 DateTime | When the test was performed | `2026-01-15T10:30:00` |
| `latitude` | Float (-90 to 90) | Latitude coordinate | `-23.5505` |
| `longitude` | Float (-180 to 180) | Longitude coordinate | `-46.6333` |
| `download` | Float (≥ 0) | Download speed in Mbps | `85.2` |
| `upload` | Float (≥ 0) | Upload speed in Mbps | `12.5` |

### Optional Columns

These columns are optional but recommended:

| Column | Type | Description | Example |
| -------- | ------- | ------------- | --------- |
| `id` | String | Unique identifier | `1` or `test-001` |
| `city` | String | City name | `São Paulo` |
| `provider` | String | Internet service provider | `Starlink`, `Claro` |
| `latency` | Float (≥ 0) | Latency in milliseconds | `45.3` |
| `jitter` | Float (≥ 0) | Jitter in milliseconds | `8.2` |
| `packet_loss` | Float (≥ 0) | Packet loss percentage | `1.2` |

## Example CSV Files

### Minimal Example (Required Fields Only)

```csv
timestamp,latitude,longitude,download,upload
2026-01-20T14:00:00,-23.5505,-46.6333,100.5,15.2
2026-01-20T14:15:00,-22.9068,-43.1729,85.3,12.8
2026-01-20T14:30:00,-15.7801,-47.9292,120.7,18.5
```

### Basic Template (Recommended Starting Point)

Copy/paste this as your CSV header + first row:

```csv
id,city,provider,latitude,longitude,download,upload,latency,jitter,packet_loss,timestamp
1,Your City Name,Your ISP Name,-23.5505,-46.6333,100.0,15.0,30.0,5.0,0.5,2026-01-15T10:00:00
```

### Complete Template (Example Dataset)

```csv
id,city,provider,latitude,longitude,download,upload,latency,jitter,packet_loss,timestamp
1,São Paulo,Starlink,-23.5505,-46.6333,165.4,22.8,28.5,3.2,0.1,2026-01-15T10:30:00
2,Belo Horizonte,Claro,-19.9167,-43.9345,92.1,15.3,38.7,6.5,0.8,2026-01-15T11:00:00
3,Curitiba,Vivo,-25.4284,-49.2733,110.5,18.2,32.1,4.8,0.3,2026-01-15T11:30:00
4,Porto Alegre,TIM,-30.0346,-51.2177,88.7,14.1,42.3,7.2,1.1,2026-01-15T12:00:00
5,Manaus,Viasat,-3.1190,-60.0217,75.3,9.8,68.2,15.7,2.5,2026-01-15T12:30:00
```

### Complete Example (All Fields)

See `example_speedtests.csv` for a complete example with all optional fields included.

## Validation Rules

### Timestamp

- Must be in ISO 8601 format
- Examples: `2026-01-15T10:30:00`, `2026-12-31T23:59:59`
- Invalid: `2026/01/15`, `Jan 15 2026`, `not-a-date`

### Coordinates

- **Latitude**: Must be between -90 and 90
- **Longitude**: Must be between -180 and 180
- Must be numeric values

### Speed Values

- **Download** and **Upload**: Must be positive numbers (≥ 0)
- Measured in Mbps (megabits per second)

### Optional Numeric Fields

- **Latency**, **Jitter**, **Packet Loss**: Must be positive numbers if provided
- Can be left empty or omitted entirely

## Command-Line Options

```bash
usage: upload_csv.py [-h] [--output OUTPUT] [--verbose] [--dry-run] csv_file

positional arguments:
  csv_file              Path to CSV file to upload

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output JSON file path (default: speedtest_data.json)
  --verbose, -v         Show detailed validation error messages
  --dry-run             Validate CSV without saving output file
```

## Output Format

The script converts CSV data to JSON format:

```json
[
  {
    "timestamp": "2026-01-15T10:30:00",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "download": 85.2,
    "upload": 12.5,
    "id": "1",
    "city": "São Paulo",
    "provider": "Various",
    "latency": 45.3,
    "jitter": 8.2,
    "packet_loss": 1.2
  }
]
```

## Error Handling

### Common Errors

**Missing Required Field**

```bash
Row 2: Missing required field 'latitude'
```

→ Add the missing column to your CSV file

**Invalid Timestamp**

```bash
Row 3: Invalid timestamp format: '2026/01/15'. Expected ISO format (e.g., 2026-01-15T10:30:00)
```

→ Use ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`

**Out of Range Coordinate**

```bash
Row 4: Latitude must be between -90 and 90, got 95.0
```

→ Check your coordinate values

**Negative Speed**

```bash
Row 5: Download speed must be positive, got -10.5
```

→ Speed values cannot be negative

### Validation Report

After processing, you'll see a validation report:

```bash
--------------------------------------------------------------------------------
CSV VALIDATION REPORT
--------------------------------------------------------------------------------

Total rows processed: 10
Valid rows: 10 ✓
Invalid rows: 0 ✗

Optional fields summary:
  • city: missing in 2 row(s)
  • latency: missing in 3 row(s)
--------------------------------------------------------------------------------
```

## Use Cases

### 1. Rural Tester Data Collection

Rural testers can create simple CSV files with speedtest results:

```bash
# Collect data in the field
# Create speedtest_results.csv with required fields
python upload_csv.py speedtest_results.csv --output my_area_data.json
```

### 2. Bulk Data Import

Import large datasets from other sources:

```bash
# Validate first
python upload_csv.py large_dataset.csv --dry-run --verbose

# If validation passes, convert
python upload_csv.py large_dataset.csv --output converted_data.json
```

### 3. Data Quality Check

Verify data quality before integration:

```bash
# Check for errors without creating files
python upload_csv.py suspicious_data.csv --dry-run --verbose
```

## Integration with Main Application

After creating a JSON file with the upload script, you can import it into the main application:

```bash
# Use the main.py CLI to work with the data
python main.py --importar speedtest_data.json --map --relatorio html
```

## Troubleshooting

### File Not Found

```bash
File not found: /path/to/file.csv
```

→ Check the file path and ensure the file exists

### Empty CSV

```bash
CSV file is empty or has no header
```

→ Ensure your CSV has a header row with column names

### Missing Required Columns

```bash
CSV header missing required fields: download, upload
```

→ Add the required columns to your CSV header

## Best Practices

1. **Start with the Example**: Use `example_speedtests.csv` as a template
2. **Validate First**: Always use `--dry-run` for initial validation
3. **Include Optional Fields**: More data = better insights
4. **Use ISO Timestamps**: Consistent datetime format prevents errors
5. **Check Coordinates**: Verify lat/lon values are correct for your location

## Performance

- Processes ~1,000 rows per second on typical hardware
- Memory efficient: streams CSV data instead of loading all at once
- Suitable for files with thousands of speedtest records

## Support

For issues or questions:

- Check error messages carefully - they indicate exactly what needs fixing
- Review `example_speedtests.csv` for proper format
- Use `--verbose` flag for detailed error information
- Open an issue on GitHub if you need help

---
