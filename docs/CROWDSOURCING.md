# Crowdsourced Data Collection Guide

## 🌍 Overview

The Rural Connectivity Mapper now supports **crowdsourced data collection**, allowing people across Brazil to easily submit their internet speedtest results. This feature helps expand the dataset beyond the initial 5 cities to provide a comprehensive view of rural connectivity nationwide.

## 📱 Three Ways to Contribute

### 1. Web Form (Easiest - Mobile Friendly)

**Perfect for:** Mobile users, quick submissions, non-technical users

#### Steps

1. **Start the crowdsourcing server:**

   ```bash
   python crowdsource_server.py
   ```

2. **Open in your browser:**
   - Desktop: http://localhost:5000
   - Mobile: http://YOUR_IP_ADDRESS:5000

3. **Submit your data:**
   - Click "📍 Obter Minha Localização" to auto-fill coordinates
   - Or manually enter latitude/longitude (find on Google Maps)
   - Select your internet provider
   - Run a speedtest at [fast.com](https://fast.com) or [speedtest.net](https://speedtest.net)
   - Enter the results (download, upload, latency)
   - Click "📤 Enviar Dados"

#### Features

- ✅ Mobile-responsive design
- ✅ Automatic geolocation (with permission)
- ✅ Real-time validation
- ✅ Portuguese interface
- ✅ Success/error feedback

---

### 2. Command-Line Script

**Perfect for:** Terminal users, automation, batch submissions

#### Interactive Mode

```bash
python submit_speedtest.py
```

The script will guide you through each step:

- Auto-detect location (optional)
- Select provider from list
- Option to run automatic speedtest
- Manual entry of speedtest results
- Review and confirm before submission

#### Direct Submission

```bash
python submit_speedtest.py \
  --latitude -23.5505 \
  --longitude -46.6333 \
  --provider Starlink \
  --download 150.0 \
  --upload 20.0 \
  --latency 30.0 \
  --jitter 5.0 \
  --packet-loss 0.5
```

#### Auto Speedtest

```bash
python submit_speedtest.py --auto-speedtest --provider Starlink
```

This will:

1. Auto-detect your location via IP
2. Run a real speedtest
3. Submit the results automatically

---

### 3. CSV Bulk Upload

**Perfect for:** Organizations, bulk data collection, offline data entry

#### Using the Web Interface

1. **Download the CSV template:**
   - Visit http://localhost:5000/api/template
   - Or use curl: `curl -O http://localhost:5000/api/template`

2. **Fill in your data:**

   ```csv
   latitude,longitude,provider,download,upload,latency,jitter,packet_loss,timestamp
   -23.5505,-46.6333,Starlink,150.0,20.0,30.0,5.0,0.5,2026-01-15T10:30:00
   -15.7801,-47.9292,Vivo,85.0,12.0,45.0,8.0,1.2,2026-01-15T11:00:00
   ```

3. **Upload via web form or API:**

   ```bash
   curl -X POST http://localhost:5000/api/upload-csv \
     -F "file=@my_speedtests.csv"
   ```

#### Using the CLI (existing functionality)

```bash
python main.py --importar my_speedtests.csv
```

---

## 🔌 API Reference

### Submit Single Data Point

```bash
POST /api/submit
Content-Type: application/json

{
  "latitude": -23.5505,
  "longitude": -46.6333,
  "provider": "Starlink",
  "download": 150.0,
  "upload": 20.0,
  "latency": 30.0,
  "jitter": 5.0,
  "packet_loss": 0.5
}
```

**Response:**

```json
{
  "success": true,
  "message": "Data submitted successfully",
  "point_id": "550e8400-e29b-41d4-a716-446655440000",
  "quality_score": 85.2,
  "rating": "Excellent"
}
```

### Upload CSV File

```bash
POST /api/upload-csv
Content-Type: multipart/form-data

file: <CSV file>
```

**Response:**

```json
{
  "success": true,
  "imported": 25,
  "message": "Successfully imported 25 data points",
  "warnings": ["Row 3: Invalid coordinates"]
}
```

### Download CSV Template

```bash
GET /api/template
```

Returns a pre-formatted CSV file with example data.

### Health Check

```bash
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:00"
}
```

---

## 📊 Data Format

### Required Fields

- `latitude` (float): -90 to 90
- `longitude` (float): -180 to 180  
- `provider` (string): Internet service provider name
- `download` (float): Download speed in Mbps
- `upload` (float): Upload speed in Mbps
- `latency` (float): Latency/ping in milliseconds

### Optional Fields

- `jitter` (float): Jitter in milliseconds (default: 0)
- `packet_loss` (float): Packet loss percentage (default: 0)
- `timestamp` (string): ISO 8601 format (auto-generated if omitted)

### Provider Options

Recommended providers:

- Starlink
- Viasat
- HughesNet
- Claro
- Vivo
- TIM
- Oi
- Other/Unknown

---

## 🚀 Deployment for Public Access

### Local Network (Home/Office)

```bash
# Start server on all network interfaces
python crowdsource_server.py
```

Access from any device on your network at:

- http://YOUR_LOCAL_IP:5000

Find your IP:

- Windows: `ipconfig`
- Linux/Mac: `ifconfig` or `ip addr`

### Cloud Deployment (Production)

#### Using a Cloud Provider (Recommended for public access)

**Option 1: Deploy to Heroku**

```bash
# Install Heroku CLI, then:
heroku create rural-connectivity-mapper
git push heroku main
```

**Option 2: Deploy to Google Cloud Run**

```bash
gcloud run deploy rural-connectivity-mapper \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Option 3: Deploy to AWS Elastic Beanstalk**

```bash
eb init -p python-3.8 rural-connectivity-mapper
eb create rural-connectivity-env
eb deploy
```

### Reverse Proxy (Advanced)

Use nginx as a reverse proxy for production:

```nginx
server {
    listen 80;
    server_name connectivity.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔒 Security Considerations

### For Public Deployment

1. **Enable rate limiting:**

   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, default_limits=["100 per hour"])
   ```

2. **Add CORS headers** (if needed):

   ```python
   from flask_cors import CORS
   CORS(app)
   ```

3. **Validate all inputs** (already implemented)

4. **Use HTTPS** (via reverse proxy like nginx)

5. **Set up authentication** (for admin endpoints)

6. **Monitor submissions** (check logs regularly)

---

## 📈 Scaling the Dataset

### Campaign Ideas

1. **Social Media:**
   - Share the submission form link
   - Create hashtag: #MapeamentoRuralBrasil
   - Post QR codes linking to the form

2. **Community Partnerships:**
   - Partner with rural cooperatives
   - Reach out to agricultural associations
   - Contact rural schools/libraries

3. **Incentives:**
   - Gamification: leaderboard for most submissions by region
   - Monthly reports showing their area's connectivity
   - Recognition for top contributors

4. **Offline Collection:**
   - Distribute printed CSV templates
   - Collect at community events
   - Batch upload via CSV endpoint

### Expected Growth

Starting with 5 cities, crowdsourcing can:

- **Week 1:** 50-100 new data points
- **Month 1:** 500-1000 data points
- **Month 3:** 5000+ data points across all Brazilian states
- **Year 1:** 50,000+ data points providing comprehensive coverage

---

## 🧪 Testing

### Test the Web Form

```bash
1. Start server: `python crowdsource_server.py`
2. Navigate to http://localhost:5000
3. Fill in test data
4. Verify submission in `src/data/pontos.json`

### Test the CLI Script
```bash
# Interactive mode
python submit_speedtest.py

# Direct submission
python submit_speedtest.py -lat -23.5505 -lon -46.6333 \
  -p Starlink -d 150 -u 20 -l 30
```

### Test CSV Upload

```bash
# Download template
curl http://localhost:5000/api/template -o test.csv

# Upload
curl -X POST http://localhost:5000/api/upload-csv -F "file=@test.csv"
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Submit data
curl -X POST http://localhost:5000/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -23.5505,
    "longitude": -46.6333,
    "provider": "Starlink",
    "download": 150.0,
    "upload": 20.0,
    "latency": 30.0
  }'
```

---

## 📱 Mobile App Integration (Future)

The API is designed to be mobile-app-friendly:

```javascript
// React Native / Flutter example
const submitSpeedtest = async (data) => {
  const response = await fetch('http://api.example.com/api/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude: location.coords.latitude,
      longitude: location.coords.longitude,
      provider: selectedProvider,
      download: speedtest.download,
      upload: speedtest.upload,
      latency: speedtest.latency
    })
  });
  
  return response.json();
};
```

---

## 🆘 Troubleshooting

### Server won't start

- Check if port 5000 is available: `lsof -i :5000`
- Install Flask: `pip install flask>=3.0.0`

### Form doesn't show location button

- Enable location services in browser settings
- Must use HTTPS for production (HTTP only works on localhost)

### CSV upload fails

- Verify CSV has required columns
- Check for encoding issues (must be UTF-8)
- Validate numeric values (no text in number fields)

### Auto-speedtest not working

- Install speedtest-cli: `pip install speedtest-cli`
- Check internet connection
- Some networks block speedtest servers

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues)
- **Questions:** Use interactive mode for guidance
- **Bulk submissions:** Contact for assistance with large datasets

---

**🇧🇷 Together, we can map connectivity across all of rural Brazil!**
