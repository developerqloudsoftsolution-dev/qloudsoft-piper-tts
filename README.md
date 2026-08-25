# 🎙️ Meta MMS-TTS Hindi Microservice • Qloudflow

A lightweight, production-ready **Text-to-Speech (TTS) REST API** powered by **Meta's Massively Multilingual Speech (MMS) Hindi Model** (`facebook/mms-tts-hin`) via Hugging Face Transformers. Specifically engineered for **low-memory, CPU-only environments** such as the Render Free tier (512MB RAM).

---

## ✨ Key Features

* **🇮🇳 Meta MMS Hindi (`facebook/mms-tts-hin`)**: Official VITS end-to-end neural Text-to-Speech model trained on native Hindi speech datasets.
* **⚡ Ultra-Low Memory Footprint (< 512MB RAM)**: 
  * Uses CPU-only PyTorch builds (~150MB instead of 2GB+ CUDA).
  * Limits PyTorch thread concurrency (`OMP_NUM_THREADS=2`) to prevent CPU/RAM thrashing.
  * Discards intermediate PyTorch tensors immediately upon inference completion with explicit garbage collection.
* **🚀 Single Startup Model Loading**: Loads model weights and tokenizer once into memory at application lifespan startup (singleton pattern).
* **🔊 Standard WAV Audio Output**: Returns 16kHz 16-bit mono PCM WAV audio directly compatible with HTML5 `<audio>`, browser Web Audio API, and telephony voice engines.
* **🔤 Clean Input Preprocessing**: Accepts standard Devanagari Hindi Unicode text (`नमस्ते, आप कैसे हैं?`) and handles Roman Hindi/Hinglish text gracefully.
* **📴 Piper Code Rollback Ready**: Retains legacy Piper code structures for rollback capability without initializing or consuming memory.
* **🎨 Web Dashboard & Playground**: Interactive UI at `http://localhost:8000/` for instant speech testing and parameter tuning.
* **🔒 Optional API Key Security**: Bearer token authentication via `Authorization: Bearer <API_KEY>` header.

---

## 📁 Project Structure

```text
piper-tts/
├── app/
│   ├── __init__.py           # Package marker
│   ├── config.py             # MMS Model & Server configuration
│   ├── main.py               # FastAPI application & REST endpoints
│   ├── piper_service.py      # Meta MMS-TTS Hindi VITS Service Layer
│   └── ui.py                 # Interactive web dashboard
├── models/
│   └── .gitkeep              # Directory for cached models
├── requirements.txt          # Python dependencies (FastAPI, PyTorch CPU, Transformers)
├── Dockerfile                # CPU-optimized Dockerfile for Render Free
├── render.yaml               # Render Blueprint specification
└── README.md                 # Technical documentation
```

---

## ⚙️ Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `MMS_MODEL_ID` | `facebook/mms-tts-hin` | Hugging Face MMS Hindi model identifier. |
| `DEFAULT_VOICE` | `facebook/mms-tts-hin` | Default voice model name used in synthesis requests. |
| `MAX_TEXT_LENGTH` | `1000` | Maximum character length per request to protect memory. |
| `DEFAULT_FORMAT` | `wav` | Default audio format (`wav`). |
| `API_KEY` | *(empty)* | Optional Bearer token for authentication (empty = open access). |
| `PORT` | `8000` | Server binding port (Render sets `$PORT` dynamically). |
| `HOST` | `0.0.0.0` | Server binding host. |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 🚀 Local Development Setup

### 1. Prerequisites
* Python 3.10+ (or Python 3.11/3.12)
* `pip` and virtual environment support

### 2. Setup Virtual Environment
```bash
cd piper-tts
python -m venv venv

# On Linux / macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies (CPU-Optimized)
```bash
# Install PyTorch CPU build
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt
```

### 4. Run the Local Microservice
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://127.0.0.1:8000`** in your browser to access the interactive web playground.

---

## ☁️ Render Deployment (Free Tier 512MB RAM)

### 1. Memory Optimization Strategy
Render's free tier imposes a strict **512MB RAM** ceiling. To guarantee stability:
1. **CPU PyTorch Build**: `Dockerfile` installs `torch` directly from `https://download.pytorch.org/whl/cpu`, avoiding ~2.5GB of unused CUDA binaries.
2. **Pre-Cached Weights**: The Docker build pre-caches `facebook/mms-tts-hin` (~145MB) during image construction, eliminating download lag and memory spikes on container cold start.
3. **Thread Limiting**: `OMP_NUM_THREADS=2` and `MKL_NUM_THREADS=2` prevent PyTorch from spawning excessive threads on Render's shared vCPUs.

### 2. Deploy via Render Blueprint
1. Push this repository to GitHub/GitLab.
2. In the Render Dashboard, click **New +** → **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](./render.yaml).
4. Click **Apply** to deploy.

---

## 🧪 REST API Reference

### 1. Health & Status Check
```http
GET /health
```
**Response (200 OK):**
```json
{
  "status": "ok",
  "engine": "mms-tts-hin",
  "default_voice": "facebook/mms-tts-hin",
  "is_loaded": true,
  "sample_rate": 16000,
  "error": null
}
```

---

### 2. Generate Speech (Binary WAV Stream)
```http
POST /tts
Content-Type: application/json

{
  "text": "नमस्ते, आप कैसे हैं?",
  "voice": "facebook/mms-tts-hin",
  "format": "wav"
}
```
**Response (200 OK):** Returns raw `audio/wav` binary stream.

---

### 3. Direct Streaming GET Endpoint (for HTML5 Audio)
```http
GET /tts?text=नमस्ते,%20आप%20कैसे%20हैं?&format=wav
```
**Response (200 OK):** Returns streamable `audio/wav`.

---

### 4. Base64 JSON Audio Endpoint
```http
POST /tts/base64
Content-Type: application/json

{
  "text": "नमस्ते! क्लाउडसॉफ्ट सॉल्यूशंस में आपका स्वागत है।"
}
```
**Response (200 OK):**
```json
{
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
  "format": "wav",
  "voice": "facebook/mms-tts-hin"
}
```

---

## ⚡ Laravel Voice Agent Integration

To connect this MMS-TTS microservice to the Laravel Voice Calling Agent:
1. Update `laravel-whatsapp-manager/.env`:
   ```env
   TTS_ENGINE=mms_hindi
   PIPER_TTS_URL=http://127.0.0.1:8000
   ```
2. The Voice Agent automatically streams WAV audio generated by `facebook/mms-tts-hin`.
