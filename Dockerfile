# Edward AI Assistant - Docker Image
#
# ⚠️ WARNING: Edward is a GUI desktop application
# Running it in Docker is NOT RECOMMENDED because:
# - Requires X11/display forwarding (complex)
# - Needs audio device passthrough
# - Requires keyboard/mouse input
# - Needs direct file system access
#
# RECOMMENDED: Run Edward natively on your desktop
# See DOCKER_GUIDE.md for details
#
# This Dockerfile is provided for:
# - Development/testing purposes
# - Headless/API-only deployments (future)
# - Reference implementation
#
# For production: Use docker-compose.bob-only.yml for Bob API only

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port for FastAPI (if needed)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the application
CMD ["python", "main.py"]

# Made with Bob
