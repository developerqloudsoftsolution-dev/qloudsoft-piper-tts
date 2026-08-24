import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Security, Depends, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.piper_service import get_tts_service, TTSService
from app.ui import get_dashboard_html

# Configure structured logging to stdout for Render logs
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("tts_api")

security = HTTPBearer(auto_error=False)


# --- Request & Response Models ---

class TTSRequest(BaseModel):
    text: str = Field(
        ...,
        description="The text to synthesize into speech (supports Hindi, Hinglish, English).",
        examples=["नमस्ते! आपका स्वागत है। How can I help you today?"]
    )
    voice: Optional[str] = Field(
        default=None,
        description="Voice ID to use (e.g. 'hi-IN-SwaraNeural' for ultra-realistic Hindi female, 'hi-IN-MadhurNeural' for Hindi male).",
        examples=["hi-IN-SwaraNeural"]
    )
    rate: Optional[str] = Field(
        default="+0%",
        description="Speech rate speed adjustment (e.g. '+0%', '+15%', '-10%').",
        examples=["+0%"]
    )
    pitch: Optional[str] = Field(
        default="+0Hz",
        description="Speech pitch adjustment (e.g. '+0Hz', '+2Hz').",
        examples=["+0Hz"]
    )
    format: Optional[str] = Field(
        default="mp3",
        description="Output audio format ('mp3' or 'wav').",
        examples=["mp3"]
    )


class TTSBase64Response(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded audio data.")
    format: str = Field(default="mp3", description="Audio format (mp3 or wav).")
    voice: str = Field(..., description="Voice model used.")


class HealthResponse(BaseModel):
    status: str = "ok"
    default_voice: str
    engine: str
    sample_rate: int


# --- Authentication Dependency ---

async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> bool:
    """
    Validates Bearer token authentication against settings.API_KEY.
    If API_KEY is not configured in the environment, authentication is bypassed.
    """
    if not settings.API_KEY:
        return True

    if not credentials or not credentials.credentials:
        logger.warning("Unauthorized access attempt: Missing Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.API_KEY:
        logger.warning("Unauthorized access attempt: Invalid API key provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


# --- Lifespan Management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager:
    Initializes the unified TTS Service on startup.
    """
    logger.info("==================================================")
    logger.info(" Starting Neural & High-Fidelity TTS Microservice")
    logger.info(f" Default Voice Model    : {settings.DEFAULT_VOICE}")
    logger.info(f" Max Text Length        : {settings.MAX_TEXT_LENGTH} chars")
    logger.info(f" Default Audio Format   : {settings.DEFAULT_FORMAT}")
    logger.info(f" Authentication         : {'Enabled (Bearer API_KEY)' if settings.API_KEY else 'Disabled (Open Access)'}")
    logger.info("==================================================")

    tts_service = get_tts_service()
    logger.info(f"TTS Service initialized. Ready for requests on {settings.HOST}:{settings.PORT}")

    yield

    logger.info("Shutting down TTS Microservice...")


# --- FastAPI Application ---

app = FastAPI(
    title="Realistic Hindi Neural TTS Microservice",
    description="High-definition, studio-grade Hindi, Hinglish, and Indian English Text-to-Speech API.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for web apps & dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global Exception Handlers ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catches unhandled exceptions and logs them without leaking stack traces."""
    logger.error(f"Unhandled error processing request '{request.url.path}': {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing your speech request."}
    )


# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse, tags=["Dashboard"], include_in_schema=False)
async def dashboard_ui():
    """
    Interactive web UI & Speech Playground for testing realistic Hindi voice synthesis.
    """
    tts_service = get_tts_service()
    return HTMLResponse(
        content=get_dashboard_html(
            model_name=tts_service.default_voice,
            sample_rate=tts_service.sample_rate,
            max_length=settings.MAX_TEXT_LENGTH,
            auth_enabled=bool(settings.API_KEY)
        )
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Public health check endpoint for uptime monitoring and readiness.
    """
    tts_service = get_tts_service()
    return {
        "status": "ok",
        "default_voice": tts_service.default_voice,
        "engine": "neural_azure_hd",
        "sample_rate": tts_service.sample_rate
    }


@app.get("/voices", response_model=List[Dict[str, Any]], tags=["Voices"])
async def list_voices():
    """
    Lists all available realistic Neural and offline voice models with metadata.
    """
    tts_service = get_tts_service()
    return tts_service.get_available_voices()


@app.post(
    "/tts",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/mpeg": {}, "audio/wav": {}},
            "description": "Returns raw audio stream (MP3 or WAV)."
        },
        400: {"description": "Validation error (empty or oversized text)"},
        401: {"description": "Unauthorized"},
        500: {"description": "Synthesis error"}
    },
    tags=["TTS"]
)
async def generate_tts_post(
    request: TTSRequest,
    _authenticated: bool = Depends(verify_api_key)
):
    """
    Synthesizes input text into a realistic human-grade speech audio stream (MP3/WAV).
    Default voice: `hi-IN-SwaraNeural` (Ultra-realistic Hindi/Hinglish Female).
    """
    text = request.text.strip() if request.text else ""

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty."
        )

    if len(text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text length ({len(text)} chars) exceeds maximum limit of {settings.MAX_TEXT_LENGTH}."
        )

    tts_service = get_tts_service()

    try:
        audio_bytes, mime_type = await tts_service.synthesize(
            text=text,
            voice=request.voice,
            rate=request.rate,
            pitch=request.pitch,
            output_format=request.format
        )
        extension = "mp3" if "mpeg" in mime_type else "wav"
        return Response(
            content=audio_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename=speech.{extension}",
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"TTS synthesis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech synthesis failed."
        )


@app.get(
    "/tts",
    response_class=Response,
    tags=["TTS"]
)
async def generate_tts_get(
    text: str = Query(..., description="Text to synthesize into speech"),
    voice: Optional[str] = Query(None, description="Voice ID (e.g. hi-IN-SwaraNeural)"),
    rate: Optional[str] = Query("+0%", description="Speed adjustment rate"),
    pitch: Optional[str] = Query("+0Hz", description="Pitch adjustment"),
    format: Optional[str] = Query("mp3", description="Audio format (mp3 or wav)"),
    _authenticated: bool = Depends(verify_api_key)
):
    """
    Direct GET streaming endpoint for HTML5 `<audio>` tags and WhatsApp direct audio URLs.
    """
    clean_text = text.strip()
    if not clean_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text parameter is required.")

    tts_service = get_tts_service()
    try:
        audio_bytes, mime_type = await tts_service.synthesize(
            text=clean_text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            output_format=format
        )
        extension = "mp3" if "mpeg" in mime_type else "wav"
        return Response(
            content=audio_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename=speech.{extension}",
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        logger.error(f"TTS GET stream error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="TTS stream failed.")


@app.post(
    "/tts/base64",
    response_model=TTSBase64Response,
    tags=["TTS"]
)
async def generate_tts_base64(
    request: TTSRequest,
    _authenticated: bool = Depends(verify_api_key)
):
    """
    Synthesizes input text and returns a Base64-encoded audio string in JSON.
    Ideal for webhook integrations and JSON clients.
    """
    text = request.text.strip() if request.text else ""

    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty.")

    if len(text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text length exceeds {settings.MAX_TEXT_LENGTH} chars limit."
        )

    tts_service = get_tts_service()

    try:
        b64_str, fmt = await tts_service.synthesize_base64(
            text=text,
            voice=request.voice,
            rate=request.rate,
            pitch=request.pitch,
            output_format=request.format
        )
        resolved_voice, _ = tts_service._resolve_voice_engine(request.voice)
        return TTSBase64Response(
            audio_base64=b64_str,
            format=fmt,
            voice=resolved_voice
        )
    except Exception as e:
        logger.error(f"TTS base64 error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Speech synthesis failed.")

