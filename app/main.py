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
logger = logging.getLogger("mms_tts_api")

security = HTTPBearer(auto_error=False)


# --- Request & Response Models ---

class TTSRequest(BaseModel):
    text: str = Field(
        ...,
        description="The text to synthesize into speech (Devanagari Hindi or cleaned input text).",
        examples=["नमस्ते, आप कैसे हैं?"]
    )
    voice: Optional[str] = Field(
        default=None,
        description="Voice Model ID (default: 'facebook/mms-tts-hin').",
        examples=["facebook/mms-tts-hin"]
    )
    rate: Optional[str] = Field(
        default="+0%",
        description="Speed adjustment rate parameter.",
        examples=["+0%"]
    )
    pitch: Optional[str] = Field(
        default="+0Hz",
        description="Pitch adjustment parameter.",
        examples=["+0Hz"]
    )
    format: Optional[str] = Field(
        default="wav",
        description="Output audio format (default: 'wav').",
        examples=["wav"]
    )


class TTSBase64Response(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded audio data.")
    format: str = Field(default="wav", description="Audio format (wav).")
    voice: str = Field(..., description="Voice model used.")


class HealthResponse(BaseModel):
    status: str = "ok"
    engine: str
    default_voice: str
    is_loaded: bool
    sample_rate: int
    error: Optional[str] = None


# --- Authentication Dependency ---

async def verify_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> bool:
    """
    Validates token authentication against settings.API_KEY.
    Supports:
    1. Bearer token in 'Authorization: Bearer <API_KEY>' header
    2. 'X-API-Key' / 'api-key' custom header
    3. '?api_key=<API_KEY>' or '?token=<API_KEY>' query parameters (crucial for HTML5 <audio> streaming)
    
    If settings.API_KEY is empty/unconfigured, authentication is bypassed (Open Access).
    """
    configured_key = settings.API_KEY.strip() if settings.API_KEY else ""
    if not configured_key:
        return True

    token: Optional[str] = None

    # 1. Bearer token in Authorization header
    if credentials and credentials.credentials:
        token = credentials.credentials.strip()

    # 2. X-API-Key or api-key header
    if not token:
        raw_header = request.headers.get("x-api-key") or request.headers.get("api-key")
        if raw_header:
            token = raw_header.strip()

    # 3. Query parameter ?api_key= or ?token=
    if not token:
        raw_param = request.query_params.get("api_key") or request.query_params.get("token")
        if raw_param:
            token = raw_param.strip()

    if not token:
        logger.warning(f"Unauthorized access to '{request.url.path}': Missing Authorization header or api_key parameter.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid Bearer token. Please provide your API key via 'Authorization: Bearer <API_KEY>' header, 'X-API-Key' header, or '?api_key=<API_KEY>' query parameter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token != configured_key:
        logger.warning(f"Unauthorized access to '{request.url.path}': Invalid API key provided.")
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
    Initializes and loads Meta MMS-TTS Hindi model on startup.
    """
    logger.info("==================================================")
    logger.info(" Starting Meta MMS-TTS Hindi Microservice")
    logger.info(f" Default Model ID       : {settings.DEFAULT_VOICE}")
    logger.info(f" Max Text Length        : {settings.MAX_TEXT_LENGTH} chars")
    logger.info(f" Default Audio Format   : {settings.DEFAULT_FORMAT}")
    logger.info(f" Authentication         : {'Enabled (Bearer API_KEY)' if settings.API_KEY else 'Disabled (Open Access)'}")
    logger.info("==================================================")

    tts_service = get_tts_service()
    if tts_service.is_loaded:
        logger.info(f"MMS-TTS Service ready on {settings.HOST}:{settings.PORT} (Sample rate: {tts_service.sample_rate}Hz)")
    else:
        logger.warning(f"MMS-TTS Service initialized with error: {tts_service.load_error}")

    yield

    logger.info("Shutting down MMS-TTS Microservice...")


# --- FastAPI Application ---

app = FastAPI(
    title="Meta MMS-TTS Hindi Microservice",
    description="High-quality, low-memory Meta MMS Hindi (facebook/mms-tts-hin) VITS Text-to-Speech API for CPU & Render Free.",
    version="2.1.0",
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
    Interactive web UI & Speech Playground for testing Meta MMS Hindi voice synthesis.
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
    Public health check endpoint reporting MMS-TTS engine status and readiness.
    """
    tts_service = get_tts_service()
    return {
        "status": "ok" if tts_service.is_loaded else "error",
        "engine": "mms-tts-hin",
        "default_voice": tts_service.default_voice,
        "is_loaded": tts_service.is_loaded,
        "sample_rate": tts_service.sample_rate,
        "error": tts_service.load_error
    }


@app.get("/voices", response_model=List[Dict[str, Any]], tags=["Voices"])
async def list_voices():
    """
    Lists available Meta MMS Hindi voice models and aliases.
    """
    tts_service = get_tts_service()
    return tts_service.get_available_voices()


@app.post(
    "/tts",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/wav": {}, "audio/mpeg": {}},
            "description": "Returns raw WAV audio stream."
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
    Synthesizes input text into a Meta MMS Hindi speech audio stream (WAV).
    Default model: `facebook/mms-tts-hin`.
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
        extension = "wav" if "wav" in mime_type else "mp3"
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
            detail=f"Speech synthesis failed: {e}"
        )


@app.get(
    "/tts",
    response_class=Response,
    tags=["TTS"]
)
async def generate_tts_get(
    text: str = Query(..., description="Hindi text to synthesize into speech"),
    voice: Optional[str] = Query(None, description="Voice ID (default: facebook/mms-tts-hin)"),
    rate: Optional[str] = Query("+0%", description="Speed adjustment rate"),
    pitch: Optional[str] = Query("+0Hz", description="Pitch adjustment"),
    format: Optional[str] = Query("wav", description="Audio format (wav)"),
    _authenticated: bool = Depends(verify_api_key)
):
    """
    Direct GET streaming endpoint for HTML5 `<audio>` tags and web audio players.
    """
    clean_text = text.strip()
    if not clean_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query parameter 'text' cannot be empty.")

    if len(clean_text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text exceeds maximum limit of {settings.MAX_TEXT_LENGTH} characters."
        )

    tts_service = get_tts_service()

    try:
        audio_bytes, mime_type = await tts_service.synthesize(
            text=clean_text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            output_format=format
        )
        extension = "wav" if "wav" in mime_type else "mp3"
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
        logger.error(f"GET /tts synthesis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {e}"
        )


@app.post(
    "/tts/base64",
    response_model=TTSBase64Response,
    responses={
        200: {"description": "Returns JSON with base64-encoded audio string."},
        400: {"description": "Validation error"},
        401: {"description": "Unauthorized"},
        500: {"description": "Synthesis error"}
    },
    tags=["TTS"]
)
async def generate_tts_base64(
    request: TTSRequest,
    _authenticated: bool = Depends(verify_api_key)
):
    """
    Synthesizes speech and returns base64-encoded audio inside a JSON payload.
    Ideal for direct embedding in JSON-based microservices and webhooks.
    """
    text = request.text.strip() if request.text else ""
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty.")

    if len(text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text length ({len(text)} chars) exceeds maximum limit of {settings.MAX_TEXT_LENGTH}."
        )

    tts_service = get_tts_service()

    try:
        b64_audio, fmt = await tts_service.synthesize_base64(
            text=text,
            voice=request.voice,
            rate=request.rate,
            pitch=request.pitch,
            output_format=request.format
        )
        return {
            "audio_base64": b64_audio,
            "format": fmt,
            "voice": request.voice or tts_service.default_voice
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Base64 synthesis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {e}"
        )
