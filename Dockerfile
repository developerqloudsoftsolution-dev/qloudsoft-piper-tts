# ==============================================================================
# Ultra-Lightweight Meta MMS-TTS Hindi REST API for Render Free Tier (512MB RAM Limit)
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DEFAULT_VOICE=facebook/mms-tts-hin \
    MMS_MODEL_ID=facebook/mms-tts-hin \
    MAX_TEXT_LENGTH=1000 \
    OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2

WORKDIR /app

# Install minimal OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first to keep Docker image small and avoid CUDA overhead
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Meta MMS Hindi model weights during docker build for instant zero-delay container startup
RUN python -c "from transformers import VitsModel, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/mms-tts-hin'); VitsModel.from_pretrained('facebook/mms-tts-hin')"

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
