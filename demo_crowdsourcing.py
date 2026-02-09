#!/usr/bin/env python3
"""
Demonstration of crowdsourced data collection features.

This script demonstrates all three methods of submitting speedtest data:
1. CLI submission script
2. CSV bulk upload
3. API endpoint (simulated)
"""

import json
import subprocess
import time
from pathlib import Path

from src.utils import load_data

print("\n" + "=" * 80)
print("🌍 Rural Connectivity Mapper - Crowdsourcing Demo")
print("=" * 80 + "\n")

# Clean data for demo
data_file = Path("src/data/pontos.json")
if data_file.exists():
    backup = Path(f"src/data/pontos_backup_{int(time.time())}.json")
    subprocess.run(["cp", str(data_file), str(backup)])
    print(f"✓ Backed up existing data to {backup}")

# Write initial empty state
with open(data_file, "w") as f:
    json.dump([], f)
print("✓ Reset data file\n")

print("=" * 80)
print("Method 1: CLI Submission Script")
print("=" * 80)
print("\n📍 Submitting data from São Paulo...\n")

result = subprocess.run(
    [
        "python",
        "submit_speedtest.py",
        "-lat",
        "-23.5505",
        "-lon",
        "-46.6333",
        "-p",
        "Starlink",
        "-d",
        "165.4",
        "-u",
        "22.8",
        "-l",
        "28.5",
        "-j",
        "3.2",
        "--packet-loss",
        "0.1",
    ],
    capture_output=True,
    text=True,
)

print(result.stdout)
if result.returncode != 0:
    print(f"Error: {result.stderr}")

print("=" * 80)
print("Method 2: CSV Bulk Upload")
print("=" * 80)
print("\n📊 Uploading CSV with multiple cities...\n")

# Create sample CSV
csv_content = """latitude,longitude,provider,download,upload,latency,jitter,packet_loss
-15.7801,-47.9292,Vivo,85.2,12.5,45.3,8.2,1.2
-12.9714,-38.5014,Viasat,75.3,9.8,68.2,15.7,2.5
-3.7172,-38.5433,HughesNet,62.8,7.2,95.4,22.3,3.8
-22.9068,-43.1729,Claro,92.1,15.3,38.7,6.5,0.8"""

csv_file = Path("/tmp/demo_speedtests.csv")
with open(csv_file, "w") as f:
    f.write(csv_content)

result = subprocess.run(["python", "main.py", "--importar", str(csv_file)], capture_output=True, text=True)

print(result.stdout)
if result.returncode != 0:
    print(f"Error: {result.stderr}")

print("\n" + "=" * 80)
print("Results Summary")
print("=" * 80 + "\n")

# Load and display all data
data = load_data("src/data/pontos.json")

print(f"📊 Total data points collected: {len(data)}\n")
print("Provider Distribution:")

providers = {}
for point in data:
    provider = point["provider"]
    providers[provider] = providers.get(provider, 0) + 1

for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
    print(f"  • {provider}: {count} point(s)")

print("\nQuality Score Distribution:")

ratings = {"Excellent": 0, "Good": 0, "Fair": 0, "Poor": 0}
total_score = 0

for point in data:
    rating = point["quality_score"]["rating"]
    ratings[rating] = ratings.get(rating, 0) + 1
    total_score += point["quality_score"]["overall_score"]

for rating in ["Excellent", "Good", "Fair", "Poor"]:
    count = ratings[rating]
    if count > 0:
        print(f"  • {rating}: {count} point(s)")

avg_score = total_score / len(data) if data else 0
print(f"\nAverage Quality Score: {avg_score:.1f}/100")

print("\n" + "=" * 80)
print("API Endpoints Available")
print("=" * 80 + "\n")

print("To use the web form and API, run:")
print("  python crowdsource_server.py")
print("\nThen access:")
print("  • Web Form:  http://localhost:5000")
print("  • API:       http://localhost:5000/api/submit")
print("  • Template:  http://localhost:5000/api/template")
print("  • Upload:    http://localhost:5000/api/upload-csv")

print("\n" + "=" * 80)
print("Next Steps")
print("=" * 80 + "\n")

print("1. Generate a map of the collected data:")
print("   python main.py --map")
print("\n2. Generate a report:")
print("   python main.py --relatorio html")
print("\n3. Analyze temporal evolution:")
print("   python main.py --analyze")
print("\n4. Start crowdsourcing server for public submissions:")
print("   python crowdsource_server.py")

print("\n" + "=" * 80)
print("✅ Demo Complete!")
print("=" * 80 + "\n")

print("📖 For full documentation, see: docs/CROWDSOURCING.md\n")
