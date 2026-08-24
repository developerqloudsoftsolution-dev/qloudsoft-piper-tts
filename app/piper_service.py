import io
import re
import wave
import base64
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from app.config import settings

logger = logging.getLogger("tts_service")

# Check Edge-TTS availability
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts package is not installed. Neural Azure voices will not be available.")

# Check Piper availability
try:
    from piper.voice import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    logger.warning("piper-tts package is not installed. Offline ONNX voices will not be available.")


# Comprehensive Voice Catalog with Indian & Neural Voices prioritized
VOICE_METADATA: Dict[str, Dict[str, Any]] = {
    # --- Top Realistic Neural Indian Voices (Primary) ---
    "hi-IN-SwaraNeural": {
        "id": "hi-IN-SwaraNeural",
        "name": "Swara (Human HD)",
        "language": "Hindi / Hinglish",
        "locale": "hi_IN",
        "gender": "Female",
        "quality": "Neural HD (Ultra-Realistic)",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": True,
        "description": "Ultra-realistic natural Indian Hindi & Hinglish female voice. Expressive, warm, and human-grade tone."
    },
    "hi-IN-MadhurNeural": {
        "id": "hi-IN-MadhurNeural",
        "name": "Madhur (Human HD)",
        "language": "Hindi / Hinglish",
        "locale": "hi_IN",
        "gender": "Male",
        "quality": "Neural HD (Ultra-Realistic)",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": True,
        "description": "Studio-quality realistic Indian Hindi & Hinglish male voice with confident and clear diction."
    },
    "en-IN-NeerjaNeural": {
        "id": "en-IN-NeerjaNeural",
        "name": "Neerja (Indian English)",
        "language": "English (India)",
        "locale": "en_IN",
        "gender": "Female",
        "quality": "Neural HD (Fluent)",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": False,
        "description": "Natural Indian-accented English female voice for professional customer communication."
    },
    "en-IN-PrabhatNeural": {
        "id": "en-IN-PrabhatNeural",
        "name": "Prabhat (Indian English)",
        "language": "English (India)",
        "locale": "en_IN",
        "gender": "Male",
        "quality": "Neural HD (Fluent)",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": False,
        "description": "Natural Indian-accented English male voice for corporate notifications and updates."
    },
    "mr-IN-AarohiNeural": {
        "id": "mr-IN-AarohiNeural",
        "name": "Aarohi (Marathi)",
        "language": "Marathi",
        "locale": "mr_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": False,
        "description": "Realistic Marathi female neural voice."
    },
    "gu-IN-DhwaniNeural": {
        "id": "gu-IN-DhwaniNeural",
        "name": "Dhwani (Gujarati)",
        "language": "Gujarati",
        "locale": "gu_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": False,
        "description": "Realistic Gujarati female neural voice."
    },
    "bn-IN-TanishaaNeural": {
        "id": "bn-IN-TanishaaNeural",
        "name": "Tanishaa (Bengali)",
        "language": "Bengali",
        "locale": "bn_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": False,
        "description": "Realistic Bengali female neural voice."
    },
    "ta-IN-PallaviNeural": {
        "id": "ta-IN-PallaviNeural",
        "name": "Pallavi (Tamil)",
        "language": "Tamil",
        "locale": "ta_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": False,
        "description": "Realistic Tamil female neural voice."
    },
    "te-IN-ShrutiNeural": {
        "id": "te-IN-ShrutiNeural",
        "name": "Shruti (Telugu)",
        "language": "Telugu",
        "locale": "te_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": False,
        "description": "Realistic Telugu female neural voice."
    },
    "ur-IN-GulNeural": {
        "id": "ur-IN-GulNeural",
        "name": "Gul (Urdu)",
        "language": "Urdu (India)",
        "locale": "ur_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural",
        "is_star": False,
        "description": "Realistic Urdu female neural voice."
    },
    # --- Offline Piper Models ---
    "hi_IN-priyamvada-medium": {
        "id": "hi_IN-priyamvada-medium",
        "name": "Priyamvada (Offline Piper)",
        "language": "Hindi (Piper)",
        "locale": "hi_IN",
        "gender": "Female",
        "quality": "Medium (Offline)",
        "flag": "🇮🇳",
        "engine": "piper",
        "is_star": False,
        "description": "Offline Piper ONNX Hindi female voice model."
    },
    "hi_IN-rohan-medium": {
        "id": "hi_IN-rohan-medium",
        "name": "Rohan (Offline Piper)",
        "language": "Hindi (Piper)",
        "locale": "hi_IN",
        "gender": "Male",
        "quality": "Medium (Offline)",
        "flag": "🇮🇳",
        "engine": "piper",
        "is_star": False,
        "description": "Offline Piper ONNX Hindi male voice model."
    },
    "en_GB-jenny_dioco-medium": {
        "id": "en_GB-jenny_dioco-medium",
        "name": "Jenny Dioco (Offline Piper)",
        "language": "English (UK)",
        "locale": "en_GB",
        "gender": "Female",
        "quality": "Medium (Offline)",
        "flag": "🇬🇧",
        "engine": "piper",
        "is_star": False,
        "description": "Offline British English female Piper voice."
    },
    "en_US-amy-low": {
        "id": "en_US-amy-low",
        "name": "Amy (Offline Piper Low)",
        "language": "English (US)",
        "locale": "en_US",
        "gender": "Female",
        "quality": "Low (Offline)",
        "flag": "🇺🇸",
        "engine": "piper",
        "is_star": False,
        "description": "Lightweight offline US English Piper voice."
    }
}


def clean_speech_text(text: str) -> str:
    """
    Cleans text for optimal TTS natural pronunciation:
    - Removes WhatsApp markdown (*bold*, _italic_, ~strike~, `code`)
    - Removes bullet points and unpronounceable characters
    - Normalizes multiple spaces and line breaks
    """
    if not text:
        return ""
    # Remove markdown bold/italic/strike
    t = re.sub(r'[*_~`#>]', '', text)
    # Remove bullet markers
    t = re.sub(r'^\s*[-•*]\s+', '', t, flags=re.MULTILINE)
    # Replace URLs with "link"
    t = re.sub(r'https?://\S+', 'link', t)
    # Replace multiple spaces/newlines with a single space
    t = re.sub(r'\s+', ' ', t).strip()
    return t


class TTSService:
    """
    Unified High-Fidelity Speech Synthesis Service.
    Supports Neural Azure Voices (hi-IN-SwaraNeural, hi-IN-MadhurNeural, etc.)
    with automatic offline Piper ONNX fallback.
    """

    _instance: Optional["TTSService"] = None

    def __init__(self):
        self._default_voice: str = settings.DEFAULT_VOICE
        self._piper_voices: Dict[str, Any] = {}
        self._sample_rates: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._is_loaded: bool = True

    @classmethod
    def get_instance(cls) -> "TTSService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def default_voice(self) -> str:
        return self._default_voice

    @property
    def sample_rate(self) -> int:
        return 24000  # Default 24kHz for HD Neural voices

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Returns metadata for all supported neural and offline voices."""
        voice_list = []
        for voice_id, meta in VOICE_METADATA.items():
            voice_list.append({
                "id": voice_id,
                "name": meta["name"],
                "language": meta["language"],
                "locale": meta["locale"],
                "gender": meta["gender"],
                "quality": meta["quality"],
                "flag": meta["flag"],
                "engine": meta["engine"],
                "is_star": meta.get("is_star", False),
                "is_default": voice_id == self._default_voice,
                "description": meta["description"]
            })
        return voice_list

    def _resolve_voice_engine(self, voice_name: Optional[str]) -> Tuple[str, str]:
        """
        Determines the engine ('neural' or 'piper') and canonical voice name.
        """
        v = (voice_name or self._default_voice).strip()
        
        # Check alias
        if v.lower() in ("swara", "hindi_female", "female_hindi", "hi_female"):
            return "hi-IN-SwaraNeural", "neural"
        if v.lower() in ("madhur", "hindi_male", "male_hindi", "hi_male"):
            return "hi-IN-MadhurNeural", "neural"
        if v.lower() in ("neerja", "indian_english", "en_in"):
            return "en-IN-NeerjaNeural", "neural"
        if v.lower() in ("prabhat", "indian_male"):
            return "en-IN-PrabhatNeural", "neural"

        # Check if voice is in metadata registry
        if v in VOICE_METADATA:
            return v, VOICE_METADATA[v]["engine"]

        # If voice name contains "Neural", treat as Neural voice
        if "neural" in v.lower():
            return v, "neural"

        # Otherwise treat as Piper ONNX model
        return v, "piper"

    # --- Neural TTS Synthesis (Edge-TTS Azure) ---
    async def _synthesize_neural(
        self,
        text: str,
        voice_name: str,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> bytes:
        """
        Synthesizes speech using Microsoft Azure Neural voices (Ultra-Realistic).
        """
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError("edge-tts library is required for neural voice synthesis.")

        clean_text = clean_speech_text(text)
        if not clean_text:
            raise ValueError("Input text is empty after cleaning.")

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=voice_name,
            rate=rate,
            pitch=pitch
        )

        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        audio_bytes = audio_buffer.getvalue()
        if len(audio_bytes) < 100:
            raise RuntimeError("Neural TTS generated an empty or incomplete audio stream.")

        return audio_bytes

    # --- Piper ONNX Synthesis (Offline Fallback) ---
    def _load_piper_model(self, model_name: str) -> Any:
        """Loads a Piper ONNX model into memory."""
        target = model_name.replace(".onnx", "").replace(".json", "")
        if target in self._piper_voices:
            return self._piper_voices[target]

        if not PIPER_AVAILABLE:
            raise RuntimeError("piper-tts is not available for offline ONNX models.")

        onnx_file = settings.MODEL_DIR / f"{target}.onnx"
        config_file = settings.MODEL_DIR / f"{target}.onnx.json"

        if not onnx_file.exists():
            # Try auto-download
            from download_model import ensure_model_files
            ensure_model_files(target, settings.MODEL_DIR)

        voice = PiperVoice.load(str(onnx_file), config_path=str(config_file) if config_file.exists() else None)
        self._piper_voices[target] = voice
        return voice

    def _sync_piper_synthesize(self, text: str, voice_name: str) -> bytes:
        """Piper ONNX offline worker."""
        clean_text = clean_speech_text(text)
        voice = self._load_piper_model(voice_name)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            if hasattr(voice, "synthesize_wav"):
                voice.synthesize_wav(clean_text, wav_file)
            else:
                first = True
                for chunk in voice.synthesize(clean_text):
                    if first:
                        wav_file.setframerate(chunk.sample_rate)
                        wav_file.setsampwidth(chunk.sample_width)
                        wav_file.setnchannels(chunk.sample_channels)
                        first = False
                    wav_file.writeframes(chunk.audio_int16_bytes)

        return buffer.getvalue()

    # --- Public Synthesis API ---
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        Synthesizes text into high quality audio.
        Returns (audio_bytes, mime_type).
        """
        clean_text = clean_speech_text(text)
        if not clean_text:
            raise ValueError("Input text cannot be empty.")

        resolved_voice, engine = self._resolve_voice_engine(voice)
        rate_val = rate or settings.DEFAULT_RATE
        pitch_val = pitch or settings.DEFAULT_PITCH
        format_val = (output_format or settings.DEFAULT_FORMAT).lower()

        logger.info(f"Synthesizing [{len(clean_text)} chars] with voice '{resolved_voice}' (engine: {engine})")

        if engine == "neural":
            try:
                audio_bytes = await self._synthesize_neural(
                    clean_text,
                    voice_name=resolved_voice,
                    rate=rate_val,
                    pitch=pitch_val
                )
                # Neural returns MP3 audio stream
                return audio_bytes, "audio/mpeg"
            except Exception as e:
                logger.warning(f"Neural TTS failed for '{resolved_voice}': {e}. Trying offline Piper fallback...")
                if PIPER_AVAILABLE:
                    try:
                        wav_bytes = await asyncio.to_thread(self._sync_piper_synthesize, clean_text, settings.PIPER_MODEL)
                        return wav_bytes, "audio/wav"
                    except Exception as pe:
                        logger.error(f"Piper fallback also failed: {pe}")
                raise e
        else:
            # Piper ONNX model
            wav_bytes = await asyncio.to_thread(self._sync_piper_synthesize, clean_text, resolved_voice)
            return wav_bytes, "audio/wav"

    async def synthesize_wav(self, text: str, voice_name: Optional[str] = None) -> bytes:
        """Legacy helper returning audio stream."""
        audio_bytes, _ = await self.synthesize(text, voice=voice_name, output_format="wav")
        return audio_bytes

    async def synthesize_base64(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> Tuple[str, str]:
        """Returns (base64_string, format_type)."""
        audio_bytes, mime_type = await self.synthesize(
            text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            output_format=output_format
        )
        b64_str = base64.b64encode(audio_bytes).decode("utf-8")
        fmt = "mp3" if "mpeg" in mime_type else "wav"
        return b64_str, fmt


# Singleton Accessor
def get_piper_service() -> TTSService:
    return TTSService.get_instance()

def get_tts_service() -> TTSService:
    return TTSService.get_instance()

