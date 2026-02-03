# Rural Connectivity Mapper 2026 - Dockerfile
# Optimized for rural servers, Raspberry Pi, and farm deployments

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including speedtest-cli
# Using slim image to keep size down for rural/limited bandwidth deployments
RUN apt-get update && apt-get install -y --no-install-recommends \
    speedtest-cli \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
# Note: --trusted-host flags may be needed in some restricted network environments
# Remove these flags if building in a standard environment with proper SSL certificates
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for output files
RUN mkdir -p /app/output

# Set environment variable to avoid Python buffering issues
ENV PYTHONUNBUFFERED=1

# Default command runs the demo workflow
CMD ["python", "demo_workflow.py"]
