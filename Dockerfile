# ==============================================================================
# Ultra-Lightweight Piper TTS REST API for Render Free Tier (512MB RAM Limit)
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DEFAULT_VOICE=hi-IN-SwaraNeural \
    PIPER_MODEL=hi_IN-priyamvada-medium \
    MAX_TEXT_LENGTH=1000 \
    MODEL_DIR=/app/models

WORKDIR /app

# Install minimal OS dependencies for TTS (espeak-ng, ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    ca-certificates \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory
RUN mkdir -p /app/models

# Copy model downloader and pre-download the fallback voice model
COPY download_model.py .
RUN python download_model.py hi_IN-priyamvada-medium --dir /app/models

# Copy application source code
COPY app/ /app/app/

# Create a non-privileged user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (Render sets $PORT dynamically)
EXPOSE 8000

# Start Uvicorn bound to Render dynamic PORT
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
