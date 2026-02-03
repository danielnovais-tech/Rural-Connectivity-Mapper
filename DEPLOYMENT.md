# 🚀 Deployment Notes - Rural Connectivity Mapper 2026

This document provides comprehensive deployment instructions, configuration details, and best practices for deploying the Rural Connectivity Mapper 2026 application.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Dependencies](#dependencies)
4. [Pre-Deployment Checklist](#pre-deployment-checklist)
5. [Deployment Steps](#deployment-steps)
6. [Data Migration](#data-migration)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)
10. [Performance Considerations](#performance-considerations)
11. [Security Notes](#security-notes)
12. [Feature Flags](#feature-flags)
13. [Monitoring and Logging](#monitoring-and-logging)
14. [Support and Escalation](#support-and-escalation)
15. [Version History](#version-history)
16. [Next Release Preview](#next-release-preview)
17. [Checklist: First-Time Deployment](#checklist-first-time-deployment)

---

## Prerequisites

### System Requirements

- **Operating System:** Linux, macOS, or Windows (with Python support)
- **Python Version:** 3.12+
- **Memory:** Minimum 512 MB RAM (1 GB+ recommended for large datasets)
- **Disk Space:** Minimum 100 MB free space
- **Internet Connection:** Required for:
  - Geocoding services (Nominatim OpenStreetMap)
  - Speed test measurements (speedtest-cli)
  - Package installation

### Required Access

- **Network Access:** Outbound HTTPS connections for:
  - `nominatim.openstreetmap.org` (geocoding)
  - `speedtest.net` servers (speed measurements)
  - `pypi.org` (package installation)

### Tools

- `pip` package manager (version 20.0+)
- `git` (for version control and deployment)
- Optional: `virtualenv` or `venv` for isolated environments

---

## Environment Variables

### Optional Configuration

Currently, the application does not require mandatory environment variables. However, you may configure the following for advanced setups:

#### Geocoding Configuration

```bash
# Optional: Custom geocoding timeout (default: 10 seconds)
export GEOCODING_TIMEOUT=15

# Optional: Custom user agent for geocoding requests
export GEOCODING_USER_AGENT="rural-connectivity-mapper-2026"
```

#### Logging Configuration

```bash
# Optional: Set logging level (DEBUG, INFO, WARNING, ERROR)
export LOG_LEVEL=INFO

# Optional: Log file path (default: console output only)
export LOG_FILE=/var/log/rural-connectivity-mapper.log
```

#### Data Storage

```bash
# Optional: Custom data directory (default: src/data/)
export DATA_DIR=/path/to/data

# Optional: Custom output directory for reports and maps
export OUTPUT_DIR=/path/to/output
```

### Production Environment Setup

For production deployments, create a `.env` file (not tracked in git):

```bash
# .env file (create manually, not included in repository)
LOG_LEVEL=INFO
DATA_DIR=/opt/rural-connectivity-mapper/data
OUTPUT_DIR=/opt/rural-connectivity-mapper/output
GEOCODING_TIMEOUT=15
```

**Note:** The application currently reads these from environment variables. If using `.env` files, you'll need to add `python-dotenv` to requirements and load them in `main.py`.

---

## Dependencies

### Python Packages

All dependencies are specified in `requirements.txt`:

```txt
speedtest-cli>=2.1.3   # Network speed testing
geopy>=2.3.0           # Geocoding services  
pytest>=7.4.0          # Testing framework
pytest-cov>=4.1.0      # Code coverage
colorama>=0.4.6        # Colored console output
pandas>=2.0.0          # Data manipulation
requests>=2.31.0       # HTTP client
folium>=0.14.0         # Interactive maps
matplotlib>=3.7.0      # Data visualization
```

### Dependency Installation

```bash
# Standard installation
pip install -r requirements.txt

# For production (with exact versions)
pip install -r requirements.txt --no-cache-dir

# Verify installation
pip list | grep -E "speedtest|geopy|pytest|colorama|pandas|folium|matplotlib"
```

### Known Compatibility Issues

- **speedtest-cli 2.1.3:** Some network configurations may require firewall rules for speedtest servers
- **geopy 2.3.0+:** Rate limiting on Nominatim API (1 request/second recommended)
- **pandas 2.0.0+:** Requires numpy 1.20.0+ (automatically installed)
- **folium 0.14.0:** JavaScript dependencies embedded in HTML output

---

## Pre-Deployment Checklist

### Code Preparation

- [ ] Pull latest code from main branch
- [ ] Review CHANGELOG or release notes for version changes
- [ ] Verify Python version compatibility (`python --version`)
- [ ] Run tests to ensure code quality (`pytest tests/ -v`)
- [ ] Check test coverage (`pytest tests/ --cov=src --cov-report=term`)

### Environment Setup

- [ ] Create/activate virtual environment
- [ ] Install/update dependencies (`pip install -r requirements.txt`)
- [ ] Verify all imports work (`python -c "import src"`)
- [ ] Check disk space for data storage
- [ ] Verify network connectivity to external services

### Data Preparation

- [ ] Backup existing `src/data/pontos.json` (if exists)
- [ ] Prepare any new CSV import files
- [ ] Validate CSV format matches expected schema
- [ ] Test import on sample data first

### Configuration Review

- [ ] Review and set environment variables (if needed)
- [ ] Check file permissions for data directories
- [ ] Verify log file paths are writable
- [ ] Configure firewall rules for external API access

---

## Deployment Steps

### Standard Deployment (Development/Testing)

```bash
# 1. Clone or update repository
git clone https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026.git
cd Rural-Connectivity-Mapper-2026

# Or update existing installation
git pull origin main

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verify installation
python -c "from src.models import ConnectivityPoint; print('✓ Models loaded')"
python -c "from src.utils import load_data; print('✓ Utils loaded')"

# 5. Run demo workflow to verify
python demo_workflow.py

# 6. Check outputs
ls -la demo_*.* demo_connectivity_map.html
```

### Production Deployment

```bash
# 1. Set up production directory
sudo mkdir -p /opt/rural-connectivity-mapper
sudo chown $(whoami):$(whoami) /opt/rural-connectivity-mapper
cd /opt/rural-connectivity-mapper

# 2. Clone repository
git clone https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026.git .
git checkout tags/v1.0.1  # Use specific version tag (check latest: git tag -l)

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# 5. Set up data directories
mkdir -p data output logs
chmod 755 data output logs

# 6. Run verification tests
pytest tests/ -v --tb=short

# 7. Test CLI functionality
python main.py --help

# 8. Import initial data (if applicable)
python main.py --importar src/data/sample_data.csv

# 9. Generate initial reports
python main.py --relatorio json
python main.py --map
```

### Docker Deployment (Future - v1.1.0)

**Note:** Docker support planned for v1.1.0. For now, use standard deployment.

```bash
# Placeholder for future Docker deployment
# docker build -t rural-connectivity-mapper:v1.0.1 .
# docker run -d -v /data:/app/data rural-connectivity-mapper:v1.0.1
```

---

## Data Migration

### File-Based Data Storage

The application uses JSON file storage (`src/data/pontos.json`). No database migrations required.

### Migrating from v1.0.0 to v1.0.1

```bash
# 1. Backup existing data
cp src/data/pontos.json src/data/pontos.json.backup.$(date +%Y%m%d)

# 2. Update code
git pull origin main

# 3. Reinstall dependencies (if changed)
pip install -r requirements.txt --upgrade

# 4. Verify data integrity
python -c "from src.utils import load_data; points = load_data(); print(f'✓ Loaded {len(points)} points')"
```

### Importing Legacy CSV Data

```bash
# Validate CSV format first
head -5 legacy_data.csv

# Expected format:
# latitude,longitude,download_speed,upload_speed,latency,provider,city,timestamp,tags

# Import with logging
python main.py --debug --importar legacy_data.csv

# Verify import
python -c "from src.utils import load_data; print(f'Total points: {len(load_data())}')"
```

### Data Backup Strategy

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=/backup/rural-connectivity-mapper
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp src/data/pontos.json $BACKUP_DIR/pontos_$DATE.json

# Keep last 7 days
find $BACKUP_DIR -name "pontos_*.json" -mtime +7 -delete
```

---

## Post-Deployment Verification

### Functional Tests

```bash
# 1. Verify CLI help works
python main.py --help

# 2. Test data import
python main.py --importar src/data/sample_data.csv

# 3. Generate all report formats
python main.py --relatorio json
python main.py --relatorio csv
python main.py --relatorio txt
python main.py --relatorio html

# 4. Test map generation
python main.py --map

# 5. Test simulation
python main.py --simulate

# 6. Test analysis
python main.py --analyze

# 7. Verify outputs exist
ls -lh demo_*.* connectivity_map.html simulated_*.json
```

### Integration Tests

```bash
# Test complete workflow
python main.py --debug \
  --importar src/data/sample_data.csv \
  --simulate \
  --map \
  --analyze \
  --relatorio html

# Verify:
# - No errors in console output
# - All files generated successfully
# - Map opens in browser correctly
# - Reports contain expected data
```

### External Service Tests

```bash
# Test geocoding service
python -c "
from src.utils import geocode_coordinates
result = geocode_coordinates(-23.5505, -46.6333)
assert result is not None, 'Geocoding failed'
print('✓ Geocoding service working')
"

# Test speedtest (optional, takes ~30 seconds)
python -c "
from src.utils import measure_speed
result = measure_speed()
if result:
    print(f'✓ Speedtest working: {result}')
else:
    print('⚠ Speedtest failed (may be network/firewall)')
"
```

### Performance Benchmarks

```bash
# Benchmark import performance
time python main.py --importar src/data/sample_data.csv

# Expected: < 5 seconds for 5 sample points
# Expected: ~1-2 seconds per 100 points for larger datasets

# Benchmark report generation
time python main.py --relatorio html

# Expected: < 2 seconds for small datasets (< 100 points)
```

---

## Rollback Procedures

### Quick Rollback

```bash
# 1. Identify previous working version
git tag -l

# 2. Checkout previous version
git checkout tags/v1.0.0  # or previous working tag

# 3. Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 4. Restore data backup
cp src/data/pontos.json.backup src/data/pontos.json

# 5. Verify functionality
python demo_workflow.py
```

### Full System Rollback

```bash
# 1. Stop any running processes
pkill -f "python main.py"

# 2. Backup current state
mv /opt/rural-connectivity-mapper /opt/rural-connectivity-mapper.failed.$(date +%Y%m%d)

# 3. Restore from backup
cp -r /backup/rural-connectivity-mapper.v1.0.0 /opt/rural-connectivity-mapper

# 4. Activate and verify
cd /opt/rural-connectivity-mapper
source venv/bin/activate
python main.py --help
```

### Data-Only Rollback

```bash
# If only data is corrupted
cp /backup/pontos_20260103.json src/data/pontos.json

# Verify data integrity
python -c "
from src.utils import load_data
points = load_data()
print(f'✓ Restored {len(points)} connectivity points')
"
```

---

## Troubleshooting

### Common Issues

#### Issue: Import Error - Module Not Found

```bash
# Symptom
ImportError: No module named 'speedtest'

# Solution
pip install -r requirements.txt
# Or individual package
pip install speedtest-cli
```

#### Issue: Geocoding Timeout

```bash
# Symptom
GeocoderTimedOut: Service timed out

# Solution 1: Increase timeout
export GEOCODING_TIMEOUT=30

# Solution 2: Check network connectivity
curl -I https://nominatim.openstreetmap.org

# Solution 3: Rate limiting (wait between requests)
# The app already implements delays, but external rate limits may apply
```

#### Issue: Permission Denied on Data Files

```bash
# Symptom
PermissionError: [Errno 13] Permission denied: 'src/data/pontos.json'

# Solution
chmod 644 src/data/pontos.json
chmod 755 src/data/
```

#### Issue: Invalid CSV Format

```bash
# Symptom
KeyError: 'latitude' or similar

# Solution: Check CSV headers
head -1 your_data.csv

# Expected headers:
# latitude,longitude,download_speed,upload_speed,latency,provider,city,timestamp,tags

# Validate with sample
cat > test.csv << EOF
latitude,longitude,download_speed,upload_speed,latency,provider,city,timestamp,tags
-23.5505,-46.6333,100.0,15.0,30.0,Starlink,São Paulo,2026-01-03T10:00:00,urban
EOF

python main.py --importar test.csv
```

#### Issue: Map Not Displaying

```bash
# Symptom
HTML file generated but map doesn't show

# Solution 1: Check file size
ls -lh connectivity_map.html
# Should be > 100 KB

# Solution 2: Verify data loaded
python -c "from src.utils import load_data; print(len(load_data()))"

# Solution 3: Check browser console (F12)
# Look for JavaScript errors

# Solution 4: Regenerate map
rm connectivity_map.html
python main.py --map
```

### Debug Mode

```bash
# Enable detailed logging
python main.py --debug --importar src/data/sample_data.csv

# Check for ERROR or WARNING messages
# All operations should log their progress
```

### System Diagnostics

```bash
# Check Python version
python --version  # Should be 3.12+

# Check installed packages
pip list

# Check package versions match requirements
pip check

# Verify network connectivity
ping -c 3 nominatim.openstreetmap.org
ping -c 3 speedtest.net

# Check disk space
df -h .

# Check file permissions
ls -la src/data/
```

---

## Performance Considerations

### Geocoding Rate Limits

- **Nominatim API:** Max 1 request per second (enforced by service)
- **Solution:** Application already includes delays between requests
- **Large datasets:** Expect ~1 hour for 3600 points (geocoding only)

### Speed Test Duration

- **Single test:** 20-60 seconds depending on connection
- **Recommendation:** Use simulated data for testing instead of live measurements
- **Production:** Schedule batch speed tests during off-peak hours

### Memory Usage

- **Small datasets (< 1000 points):** < 100 MB RAM
- **Large datasets (> 10,000 points):** Up to 500 MB RAM
- **Map generation:** Folium can use significant memory for large datasets

### Optimization Tips

```bash
# 1. Process data in batches for large imports
split -l 1000 large_dataset.csv batch_

# 2. Use --simulate instead of live speed tests for development
python main.py --simulate

# 3. Disable geocoding for existing coordinates
# (Coordinates are already in CSV, no reverse geocoding needed)

# 4. Generate maps for subsets
# Use filtering in future versions or manually subset CSV
```

---

## Security Notes

### API Key Management

**Current Status:** No API keys required for v1.0.1

**Future Versions (v1.2.0+):**
- Starlink API integration may require authentication
- Use environment variables for sensitive data
- **Never commit API keys to git**

```bash
# Future: Use .env file (not tracked in git)
echo "STARLINK_API_KEY=your_key_here" >> .env
echo ".env" >> .gitignore
```

### Data Privacy

- **No PII Collection:** Sample data contains only aggregated metrics
- **Location Data:** Coordinates are city-level, not individual addresses
- **Recommendation:** Anonymize any user-specific data before import

### Network Security

```bash
# Firewall rules for production (example)
# Allow outbound HTTPS for API calls
sudo ufw allow out 443/tcp

# Restrict inbound if running as service
sudo ufw default deny incoming
```

### File Permissions

```bash
# Recommended permissions
chmod 755 /opt/rural-connectivity-mapper
chmod 644 /opt/rural-connectivity-mapper/src/data/pontos.json
chmod 700 /opt/rural-connectivity-mapper/logs  # If using log files
```

### Dependency Security

```bash
# Check for known vulnerabilities
pip install safety
safety check -r requirements.txt

# Keep dependencies updated
pip list --outdated

# Update specific packages
pip install --upgrade speedtest-cli geopy
```

---

## Feature Flags

**Current Status:** No feature flags implemented in v1.0.1

**Future Versions:** Feature flags may be added for:
- Real-time speed testing (vs. simulated)
- Different geocoding providers
- Database backends (JSON vs. SQLite)
- Advanced analytics features

**Recommendation:** Use environment variables for feature toggles:

```bash
# Example for future use
export ENABLE_REALTIME_SPEEDTEST=false
export ENABLE_ADVANCED_ANALYTICS=true
export DATABASE_BACKEND=json  # or 'sqlite'
```

---

## Monitoring and Logging

### Application Logs

```bash
# View real-time logs (if using log file)
tail -f /var/log/rural-connectivity-mapper.log

# Search for errors
grep ERROR /var/log/rural-connectivity-mapper.log

# Check recent activity
tail -100 /var/log/rural-connectivity-mapper.log
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "=== Rural Connectivity Mapper Health Check ==="

# Check Python
python --version > /dev/null 2>&1 && echo "✓ Python OK" || echo "✗ Python FAILED"

# Check dependencies
pip show speedtest-cli > /dev/null 2>&1 && echo "✓ speedtest-cli OK" || echo "✗ speedtest-cli FAILED"
pip show geopy > /dev/null 2>&1 && echo "✓ geopy OK" || echo "✗ geopy FAILED"
pip show folium > /dev/null 2>&1 && echo "✓ folium OK" || echo "✗ folium FAILED"

# Check data file
[ -f src/data/pontos.json ] && echo "✓ Data file exists" || echo "✗ Data file missing"

# Check CLI
python main.py --help > /dev/null 2>&1 && echo "✓ CLI works" || echo "✗ CLI FAILED"

echo "=== Health Check Complete ==="
```

---

## Support and Escalation

### Getting Help

1. **Check Documentation:** README.md, API.md, this DEPLOYMENT.md
2. **Review Issues:** [GitHub Issues](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues)
3. **Enable Debug Mode:** `python main.py --debug ...`
4. **Run Tests:** `pytest tests/ -v` to identify broken functionality

### Reporting Deployment Issues

When reporting issues, include:

```bash
# System information
python --version
pip list | grep -E "speedtest|geopy|pytest|colorama|pandas|folium|matplotlib"
uname -a

# Error logs
python main.py --debug [your command] 2>&1 | tee deployment_error.log

# Attach deployment_error.log to GitHub issue
```

---

## Version History

| Version | Release Date | Deployment Notes |
|---------|--------------|------------------|
| v1.0.1  | Dec 28, 2025 | Enhanced documentation, no breaking changes |
| v1.0.0  | Dec 28, 2025 | Initial production release |

---

## Next Release Preview (v1.1.0 - Q1 2026)

**Planned Changes:**
- SQLite database backend (migration from JSON required)
- Docker containerization (new deployment method)
- GitHub Actions CI/CD (automated testing)
- Real-time speedtest integration (new API dependencies)

**Migration Impact:**
- **Breaking:** Data migration from JSON to SQLite required
- **New Dependencies:** `sqlite3` (built-in), `docker` (optional)
- **Environment Variables:** `DATABASE_URL` for custom DB paths

---

## Checklist: First-Time Deployment

Use this checklist for new deployments:

- [ ] System meets prerequisites (Python 3.12+, network access)
- [ ] Virtual environment created and activated
- [ ] Dependencies installed from requirements.txt
- [ ] Import successful with sample data
- [ ] All report formats generate successfully
- [ ] Map generation works and opens in browser
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Backup strategy configured
- [ ] Monitoring/logging set up (if needed)
- [ ] Documentation reviewed by team
- [ ] Rollback procedure tested
- [ ] Health check script runs successfully

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Maintained By:** Rural Connectivity Mapper Team  

For questions or updates to this document, please open a GitHub issue or discussion.
