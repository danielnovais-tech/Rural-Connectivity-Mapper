# Multi-Country Support Example

This document demonstrates how to use the Rural Connectivity Mapper 2026 with different countries.

## Supported Countries

The tool supports 9 countries with country-specific configurations:

- **BR** - Brazil (Portuguese)
- **US** - United States (English)
- **CA** - Canada (English)
- **GB** - United Kingdom (English)
- **AU** - Australia (English)
- **DE** - Germany (German)
- **FR** - France (French)
- **IN** - India (English)
- **MX** - Mexico (Spanish)

## List Available Countries

```bash
python main.py --list-countries
```

Output:

```bash
Available country codes:
==================================================
  AU: Australia
  BR: Brazil
  CA: Canada
  DE: Germany
  FR: France
  GB: United Kingdom
  IN: India
  MX: Mexico
  US: United States
==================================================
```

## Using Different Countries

### Example 1: Import and Map US Data

```bash
python main.py --country US --importar src/data/sample_data_us.csv --map
```

This will:

- Import US connectivity data
- Validate providers against US provider list (AT&T, Verizon, Starlink, etc.)
- Generate a map centered on the United States
- Use English for any geocoding operations

### Example 2: Analyze Canadian Data

```bash
python main.py --country CA --analyze --relatorio json
```

This will:

- Use Canadian country settings
- Validate providers against Canadian provider list (Bell, Rogers, Telus, etc.)
- Generate analysis and JSON report

### Example 3: Germany with Full Workflow

```bash
python main.py --country DE \
  --debug \
  --importar data_germany.csv \
  --simulate \
  --map \
  --analyze \
  --relatorio html
```

This will:

- Use German language for geocoding
- Validate German providers (Deutsche Telekom, Vodafone, etc.)
- Center map on Germany
- Run complete workflow with all features

## CSV Format with Country Field

You can include a `country` column in your CSV file:

```csv
id,city,provider,latitude,longitude,download,upload,latency,jitter,packet_loss,timestamp,country
1,Austin,Starlink,30.2672,-97.7431,180.5,25.3,22.1,2.8,0.05,2026-01-15T10:00:00,US
2,Toronto,Bell,43.6532,-79.3832,150.2,20.1,28.5,4.2,0.3,2026-01-15T11:00:00,CA
```

If the country column is not present, the `--country` argument will be used as default.

## Country Configuration File

The country settings are stored in `config/countries.json`:

```json
{
  "countries": {
    "US": {
      "name": "United States",
      "language": "en",
      "default_center": {
        "latitude": 39.8283,
        "longitude": -98.5795
      },
      "zoom_level": 4,
      "providers": [
        "Starlink",
        "Viasat",
        "HughesNet",
        "AT&T",
        "Verizon",
        "T-Mobile",
        "CenturyLink",
        "Frontier",
        "Various",
        "Unknown"
      ]
    }
  }
}
```

## Adding a New Country

To add support for a new country:

1. Edit `config/countries.json`
2. Add a new entry with the ISO country code
3. Specify:
   - `name`: Full country name
   - `language`: ISO language code for geocoding
   - `default_center`: Latitude/longitude for map center
   - `zoom_level`: Default map zoom (1-20)
   - `providers`: List of ISPs in that country

Example for Japan:

```json
"JP": {
  "name": "Japan",
  "language": "ja",
  "default_center": {
    "latitude": 36.2048,
    "longitude": 138.2529
  },
  "zoom_level": 5,
  "providers": [
    "Starlink",
    "NTT",
    "KDDI",
    "SoftBank",
    "Various",
    "Unknown"
  ]
}
```

## Features by Country

Each country has:

1. **Localized Geocoding**: Addresses are returned in the country's language
2. **Provider Validation**: Only providers in the country's list are valid
3. **Map Centering**: Maps automatically center on the country
4. **Zoom Level**: Appropriate zoom based on country size

## Backward Compatibility

The default country is Brazil (BR), so existing workflows without the `--country` argument will continue to work as before.
