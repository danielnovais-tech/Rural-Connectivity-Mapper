# Example CSV Templates

This directory contains ready-to-use CSV templates for contributing speedtest data to the Rural Connectivity Mapper 2026 project.

## 📋 Available Templates

### 1. Basic Template (`speedtest_template_basic.csv`)

A minimal template with one example entry. Perfect for getting started quickly.

**Use this if:** You want a simple template to fill in your own data.

### 2. Complete Template (`speedtest_template_complete.csv`)

A comprehensive template with 5 example entries from different Brazilian cities and ISPs.

**Use this if:** You want to see multiple examples of properly formatted data.

## 📝 CSV Field Descriptions

| Field | Required | Type | Description | Example |
| ----- | -------- | ---- | ----------- | ------- |
| `id` | Yes | Integer | Unique identifier for the measurement | 1, 2, 3... |
| `city` | Yes | String | City or location name | "São Paulo", "Rio de Janeiro" |
| `provider` | Yes | String | Internet Service Provider name | "Starlink", "Claro", "Vivo" |
| `latitude` | Yes | Float | Latitude coordinate (-90 to 90) | -23.5505 |
| `longitude` | Yes | Float | Longitude coordinate (-180 to 180) | -46.6333 |
| `download` | Yes | Float | Download speed in Mbps | 165.4 |
| `upload` | Yes | Float | Upload speed in Mbps | 22.8 |
| `latency` | Yes | Float | Latency (ping) in milliseconds | 28.5 |
| `jitter` | No | Float | Jitter in milliseconds (defaults to 0) | 3.2 |
| `packet_loss` | No | Float | Packet loss percentage (defaults to 0) | 0.1 |
| `timestamp` | No | ISO 8601 | Measurement timestamp (auto-generated if missing) | 2026-01-15T10:30:00 |

## 🚀 Quick Start

1. **Download a template:**

   ```bash
   # Download the basic template
   curl -O https://raw.githubusercontent.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/main/examples/speedtest_template_basic.csv
   ```

2. **Edit the template:**
   - Open the CSV file in Excel, Google Sheets, or a text editor
   - Replace the example data with your speedtest results
   - Make sure coordinates are accurate (use Google Maps to find them)

3. **Validate your data:**
   - Ensure all required fields are filled
   - Check that latitude is between -90 and 90
   - Check that longitude is between -180 and 180
   - Verify speedtest values are positive numbers

4. **Submit your data:**
   - See the main [README.md](../README.md) for contribution instructions
   - Create a Pull Request or open an Issue with your data

## 🌐 Finding Coordinates

**Google Maps Method:**

1. Open [Google Maps](https://www.google.com/maps)
2. Right-click on your location
3. Click on the coordinates to copy them
4. Format: `latitude,longitude` (e.g., `-23.5505,-46.6333`)

**GPS Device/Smartphone:**

- Use GPS apps that display decimal degree coordinates
- Ensure format is in decimal degrees, not degrees/minutes/seconds

## 🧪 Running a Speedtest

### Online Speedtest Tools

- [Speedtest.net](https://www.speedtest.net/) by Ookla
- [Fast.com](https://fast.com/) by Netflix
- [CloudFlare Speed Test](https://speed.cloudflare.com/)

### Command Line (Linux/Mac)

```bash
# Install speedtest-cli
pip install speedtest-cli

# Run test
speedtest-cli --simple
```

### Recording Your Results

After running a speedtest, note down:

- **Download speed** (Mbps)
- **Upload speed** (Mbps)
- **Latency/Ping** (ms)
- **Jitter** (ms) - if available
- **Packet loss** (%) - if available

## ✅ Data Quality Tips

1. **Run multiple tests:** Take 3-5 measurements and use the average
2. **Test at different times:** Morning, afternoon, and evening
3. **Close other applications:** Ensure accurate measurements
4. **Use wired connection:** If possible, test via Ethernet (WiFi adds latency)
5. **Document conditions:** Note weather, time of day, network load

## 🤝 Contributing

Your speedtest data helps map rural connectivity across Brazil and supports Starlink's 2026 expansion planning!

Every contribution matters, whether it's:

- ✅ A single speedtest from your location
- ✅ Multiple measurements over time
- ✅ Comparative tests (before/after provider change)
- ✅ Coverage gaps in underserved areas

Thank you for helping improve rural internet connectivity! 🇧🇷
